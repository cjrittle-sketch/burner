#!/usr/bin/env python3
"""Find where an assistant went around burner: every shell command in a run
that drove the phone without the `burner` command.

    pbpaste | python3 tools/offburner.py          # a pasted Muse timeline
    python3 tools/offburner.py timeline.txt

Each hit is a missing command or a missing skill row. That is how `status`,
`scroll`, `notifications`, `apps` and `dismiss` came about on Oct 1-2: Muse
improvised with raw adb, dumpsys, HOME plus edge swipes, or by writing
recipe files by hand.
"""
import re
import sys

# Phone access that should have been a burner command. First match wins.
PATTERNS = [
    (r"\bdumpsys\b", "dumpsys (can expose accounts; is a burner command missing?)"),
    (r"\binput (tap|swipe|keyevent|text)\b", "raw input (use burner tap/scroll/press/type)"),
    (r"\buiautomator\b|\bu2ctl\b|\bu2mux\b", "UI helper called directly"),
    (r"\bam start\b|\bmonkey\b", "app launch by hand (burner start/open)"),
    (r"\bsettings (get|put)\b", "phone settings by hand"),
    (r"\bscreencap\b|\bscreenshot\.sh\b", "screenshot by hand (burner shot)"),
    (r"(>|tee)\s*\S*recipes/\S+\.burner", "recipe written by hand (burner save)"),
    (r"export\s+(PATH|BURNER_WORKSPACE)=", "PATH export (call ~/burner/bin/burner)"),
    (r"\bcontent query\b|mmssms|telephony", "message database (open the Messages app)"),
    (r"\badb\b", "raw adb"),  # last: the specific reasons above win
]


def scan(text):
    """[(line_no, why, line)] for lines that look like phone access outside
    burner. Pure: unit-testable."""
    hits = []
    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip().lstrip("$#> ").strip()
        if not s:
            continue
        for pat, why in PATTERNS:
            if re.search(pat, s):
                hits.append((i, why, s[:140]))
                break
    return hits


def main():
    text = open(sys.argv[1]).read() if len(sys.argv) > 1 else sys.stdin.read()
    hits = scan(text)
    for i, why, line in hits:
        print("{:>4}  {}\n      {}".format(i, why, line))
    print("{} place(s) where the assistant went around burner".format(len(hits)))
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
