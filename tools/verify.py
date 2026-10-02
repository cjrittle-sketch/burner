#!/usr/bin/env python3
"""Behaviour checks a bench can't see. Run after every speed change.

    python3 tools/verify.py           # all checks
    python3 tools/verify.py scroll    # just one (names below)
    python3 tools/verify.py --json

Each check drives the phone through Android's own Settings screens (present
on every phone) and prints PASS, FAIL or SKIP. Exit 1 if anything failed.
Every one of these broke at least once during the Oct 2 speed loop:

  scroll     one `scroll down` moves the list about half a screen, and a
             dump taken straight after it shows the new content
  rowtap     `tap --xy 0.5,0.5` on Settings home is not refused
  dialog     with a dialog open, a tap on a label behind it is refused
  landscape  a labelled tap lands correctly with the screen rotated
  shot       `shot --out DIR` writes a fresh, non-empty file each time

The phone is left on Settings, rotation is put back, and dialogs are closed.
"""
import argparse
import json
import os
import statistics
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BURNER = os.path.join(ROOT, "bin", "burner")


def _adb_path():
    ws = os.environ.get("BURNER_WORKSPACE") or ROOT
    p = os.path.join(ws, ".android-tools", "platform-tools", "adb")
    return p if os.path.exists(p) else "adb"


def _target():
    port = "15555"
    try:
        with open(os.path.join(ROOT, "config.env")) as f:
            for line in f:
                if line.strip().startswith("LOCAL_PORT="):
                    port = line.split("=", 1)[1].strip().strip('"')
    except OSError:
        pass
    return "127.0.0.1:" + port


def adb_shell(cmd):
    return subprocess.run([_adb_path(), "-s", _target(), "shell", cmd],
                          capture_output=True, text=True, timeout=30).stdout.strip()


def burner(*argv, timeout=90):
    r = subprocess.run([sys.executable, BURNER] + list(argv),
                       capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout, r.stderr


def dump():
    rc, out, _ = burner("dump", "--json", "--all")
    try:
        return json.loads(out)["nodes"]
    except (ValueError, KeyError):
        return []


def open_settings(action="android.settings.SETTINGS"):
    adb_shell("am start -W -a {}".format(action))
    time.sleep(1.5)


def screen_height(nodes):
    hs = []
    for n in nodes:
        b = n.get("bounds", "")
        try:
            hs.append(int(b.split("][")[1].rstrip("]").split(",")[1]))
        except (IndexError, ValueError):
            pass
    return max(hs) if hs else 0


def labelled(nodes):
    """{label: y} for nodes with a unique label."""
    seen, out = set(), {}
    for n in nodes:
        lab = n.get("text") or n.get("desc")
        if not lab or "y" not in n:
            continue
        if lab in seen:
            out.pop(lab, None)
        else:
            out[lab] = n["y"]
        seen.add(lab)
    return out


def movement(before, after, h):
    """Fraction of the screen height the list moved, from labels on both
    dumps. None when nothing is on both (moved more than a screen). Pure."""
    a, b = labelled(before), labelled(after)
    common = [k for k in a if k in b]
    if not common or not h:
        return None
    return abs(statistics.median(a[k] - b[k] for k in common)) / h


# ------------------------------------------------------------------ checks

def check_scroll():
    open_settings("android.settings.MANAGE_ALL_APPLICATIONS_SETTINGS")
    d0 = dump()
    if len(labelled(d0)) < 6:
        return "SKIP", "the all-apps list is too short to scroll"
    rc, _, err = burner("scroll", "down")
    if rc != 0:
        return "FAIL", "scroll down exited {}: {}".format(rc, err.strip()[-120:])
    d1 = dump()
    time.sleep(1.0)
    d2 = dump()
    burner("scroll", "top")
    if labelled(d1) != labelled(d2):
        return "FAIL", "a dump right after the scroll showed old or moving content"
    moved = movement(d0, d1, screen_height(d0))
    if moved is not None and moved < 0.3:
        return "FAIL", "one scroll moved the list {:.0%} of the screen (want ~50%)".format(moved)
    return "PASS", "moved {}".format("over a screen" if moved is None else "{:.0%}".format(moved))


def check_rowtap():
    open_settings()
    rc, out, err = burner("tap", "--xy", "0.5,0.5")
    burner("press", "BACK")
    if rc != 0:
        return "FAIL", "refused: {}".format((err or out).strip()[-160:])
    return "PASS", "accepted"


def check_dialog():
    open_settings("android.settings.DEVICE_INFO_SETTINGS")
    before = dump()
    labels = list(labelled(before))
    if "Device name" not in labels:
        return "SKIP", "no 'Device name' row on this phone's About screen"
    behind = next((l for l in labels if l not in ("Device name", "About phone")
                   and len(l) > 3), None)
    burner("tap", "Device name")
    time.sleep(1.0)
    during = dump()
    if labelled(during) == labelled(before):
        return "SKIP", "the Device name dialog didn't open"
    rc, out, err = burner("tap", behind)
    burner("press", "BACK")
    if rc == 0:
        return "FAIL", "tap on '{}' behind the dialog went through".format(behind)
    return "PASS", "tap on '{}' behind the dialog refused".format(behind)


def check_landscape():
    acc = adb_shell("settings get system accelerometer_rotation")
    rot = adb_shell("settings get system user_rotation")
    try:
        adb_shell("settings put system accelerometer_rotation 0; "
                  "settings put system user_rotation 1")
        open_settings()
        time.sleep(1.0)
        rc, out, err = burner("tap", "Search settings || Search")
        if rc != 0:
            return "SKIP" if "no match" in err + out else "FAIL", \
                (err or out).strip()[-160:]
        time.sleep(1.0)
        if not any("EditText" in (n.get("class") or "") for n in dump()):
            return "FAIL", "tap returned ok but the search screen didn't open"
        return "PASS", "search opened in landscape"
    finally:
        burner("press", "BACK")
        adb_shell("settings put system user_rotation {}; "
                  "settings put system accelerometer_rotation {}".format(
                      rot if rot.isdigit() else 0, acc if acc.isdigit() else 1))


def check_shot():
    d = tempfile.mkdtemp(prefix="burner-verify-")
    for _ in range(2):
        rc, out, err = burner("shot", "--out", d)
        if rc != 0:
            return "FAIL", "shot exited {}: {}".format(rc, err.strip()[-120:])
    files = [os.path.join(d, f) for f in os.listdir(d)]
    if len(files) != 2:
        return "FAIL", "two shots made {} file(s); names must not repeat".format(len(files))
    if any(os.path.getsize(f) < 1000 for f in files):
        return "FAIL", "a screenshot file is empty or tiny"
    return "PASS", "2 new files"


CHECKS = [("scroll", check_scroll), ("rowtap", check_rowtap),
          ("dialog", check_dialog), ("landscape", check_landscape),
          ("shot", check_shot)]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("only", nargs="*", help="check names to run")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    results = []
    for name, fn in CHECKS:
        if args.only and name not in args.only:
            continue
        try:
            status, detail = fn()
        except Exception as e:  # a check must never leave the loop hanging
            status, detail = "FAIL", "{}: {}".format(type(e).__name__, e)
        results.append({"check": name, "status": status, "detail": detail})
        if not args.json:
            print("{:<5} {:<10} {}".format(status, name, detail), flush=True)
    if args.json:
        print(json.dumps(results))
    return 1 if any(r["status"] == "FAIL" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
