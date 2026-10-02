#!/usr/bin/env python3
"""Show where each burner command's time went.

    BURNER_TRACE=json burner tap "Search settings"
    python3 tools/tracesum.py            # waterfall for every command traced
    python3 tools/tracesum.py --last 1   # only the latest command
    python3 tools/tracesum.py --clear    # empty the trace (stops u2mux tracing)

burner writes its steps (adb calls, sleeps, scroll steps, total) to
run/trace.jsonl. While that file exists the UI helper (u2mux) adds its RPC
spans there too; they are placed inside the command whose time window they
fall in. "unaccounted" is the command's total minus the spans listed, which
is mostly Python work and anything not traced yet (a step that wraps
other traced steps, like a scroll step around its sleep, can count twice).
"""
import argparse
import json
import os
import sys
from collections import OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACE = os.path.join(ROOT, "run", "trace.jsonl")


def load(path):
    try:
        with open(path) as f:
            return [json.loads(l) for l in f if l.strip()]
    except FileNotFoundError:
        return []


def group(spans):
    """{run_id: {"cmd", "total", "start", "end", "spans": [...]}}, with u2mux
    spans attached to the run whose window contains them. Pure: testable."""
    runs = OrderedDict()
    for s in spans:
        if s.get("src") != "burner":
            continue
        r = runs.setdefault(s["run"], {"cmd": s.get("cmd", ""), "total": None,
                                       "spans": [], "end": s["t"]})
        r["end"] = max(r["end"], s["t"])
        if s["step"] == "total":
            r["total"] = s["ms"]
        else:
            r["spans"].append(s)
    for r in runs.values():
        r["start"] = r["end"] - (r["total"] or 0) / 1000.0
    for s in spans:
        if s.get("src") == "u2mux":
            for r in runs.values():
                if r["total"] is not None and r["start"] <= s["t"] <= r["end"] + 0.05:
                    r["spans"].append(dict(s, step="u2 " + s["step"]))
                    break
    for r in runs.values():
        r["spans"].sort(key=lambda s: s["t"])
    return runs


def render(run):
    lines = ["{}  total {}ms".format(run["cmd"] or "(command)",
                                     "?" if run["total"] is None else int(run["total"]))]
    timed = 0.0
    for s in run["spans"]:
        ms = s.get("ms")
        # u2 RPCs run inside the caller's own spans (e.g. a dump), so they
        # are shown but not added to the sum.
        if ms is not None and not s["step"].startswith("u2 "):
            timed += ms
        lines.append("  {:>7}  {}".format("" if ms is None else "{}ms".format(int(ms)),
                                         s["step"]))
    if run["total"] is not None:
        lines.append("  {:>7}  unaccounted".format("{}ms".format(int(run["total"] - timed))))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--last", type=int, help="only the last N commands")
    ap.add_argument("--clear", action="store_true", help="delete the trace file")
    ap.add_argument("--file", default=TRACE)
    args = ap.parse_args()
    if args.clear:
        try:
            os.remove(args.file)
        except FileNotFoundError:
            pass
        return 0
    runs = list(group(load(args.file)).values())
    if not runs:
        print("no trace yet: run a command with BURNER_TRACE=json first")
        return 0
    if args.last:
        runs = runs[-args.last:]
    print("\n\n".join(render(r) for r in runs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
