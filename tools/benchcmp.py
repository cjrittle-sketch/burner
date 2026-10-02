#!/usr/bin/env python3
"""Compare two saved bench runs and flag regressions.

    python3 tools/benchcmp.py            # last saved run vs the one before it
    python3 tools/benchcmp.py abc1234    # last run vs the newest run of that commit
    python3 tools/benchcmp.py --base 0 --head -1   # by position in the history

A command regresses when its median is both 20% and 300ms slower, or when it
now exits non-zero. Exit status is 1 when anything regressed, so a loop can
stop on it.
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY = os.path.join(ROOT, "run", "bench-history.jsonl")
PCT, ABS_MS = 0.20, 300


def load(path):
    try:
        with open(path) as f:
            return [json.loads(l) for l in f if l.strip()]
    except FileNotFoundError:
        return []


def compare(base, head):
    """Rows of (name, base_ms, head_ms, delta_ms, flag). Pure: unit-testable."""
    rows = []
    for name, h in head["results"].items():
        b = base["results"].get(name)
        bm, hm = (b or {}).get("median"), h.get("median")
        flag = ""
        if h.get("exit", 0) != 0 and (b or {}).get("exit", 0) == 0:
            flag = "FAILS NOW"
        elif bm is not None and hm is not None:
            if hm - bm >= ABS_MS and hm >= bm * (1 + PCT):
                flag = "SLOWER"
            elif bm - hm >= ABS_MS and bm >= hm * (1 + PCT):
                flag = "faster"
        rows.append((name, bm, hm, None if bm is None or hm is None else hm - bm, flag))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("commit", nargs="?", help="base: newest run of this commit")
    ap.add_argument("--base", type=int, help="base: index into the history")
    ap.add_argument("--head", type=int, default=-1, help="head: index (default last)")
    ap.add_argument("--file", default=HISTORY)
    args = ap.parse_args()
    hist = load(args.file)
    if len(hist) < 2:
        print("need two saved runs in {} (bench.py --save)".format(args.file))
        return 0
    head = hist[args.head]
    if args.commit:
        cands = [r for r in hist if (r.get("commit") or "").startswith(args.commit)
                 and r is not head]
        if not cands:
            print("no saved run for commit {}".format(args.commit))
            return 2
        base = cands[-1]
    elif args.base is not None:
        base = hist[args.base]
    else:
        base = hist[hist.index(head) - 1] if hist.index(head) > 0 else hist[0]

    print("base {} {}  ->  head {} {}".format(
        (base.get("commit") or "?")[:7], base.get("t"),
        (head.get("commit") or "?")[:7], head.get("t")))
    bad = False
    for name, bm, hm, d, flag in compare(base, head):
        print("{:<16} {:>7} {:>7} {:>8}  {}".format(
            name, "-" if bm is None else "{}ms".format(bm),
            "-" if hm is None else "{}ms".format(hm),
            "" if d is None else "{:+d}ms".format(d), flag))
        bad = bad or flag in ("SLOWER", "FAILS NOW")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
