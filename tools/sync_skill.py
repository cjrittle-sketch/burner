#!/usr/bin/env python3
"""Copy SKILL.md to the two places that serve it. Edit only SKILL.md, then run:

    python3 tools/sync_skill.py           # rewrite the copies
    python3 tools/sync_skill.py --check   # exit 1 if a copy is stale

- skills/burner/SKILL.md: an exact copy, for tools that load skills/ folders.
- docs/skill.md: what useburner.si/skill.md serves; the front matter is swapped
  for a one-line install hint at the top.

tests/test_skill_copies.py fails when either copy is out of date.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "SKILL.md")
SKILL_COPY = os.path.join(ROOT, "skills", "burner", "SKILL.md")
SITE_COPY = os.path.join(ROOT, "docs", "skill.md")
SITE_HEADER = ("> Install: curl -fsSL https://useburner.si/install.sh | bash "
               "(full guide below). Skill rev {rev}: if `burner version` "
               "shows a different rev, run `burner update`.\n\n")


def skill_rev(text):
    """Same hash as skill_rev() in bin/burner."""
    import hashlib
    return hashlib.sha256(
        text.replace("\r\n", "\n").encode("utf-8")).hexdigest()[:8]


def strip_front_matter(text):
    if text.startswith("---\n"):
        end = text.index("\n---\n", 4)
        return text[end + len("\n---\n"):].lstrip("\n")
    return text


def expected():
    with open(SOURCE, encoding="utf-8") as f:
        src = f.read()
    header = SITE_HEADER.format(rev=skill_rev(src))
    return {SKILL_COPY: src, SITE_COPY: header + strip_front_matter(src)}


def main():
    if "--check" in sys.argv[1:]:
        stale = []
        for path, text in expected().items():
            with open(path, encoding="utf-8") as f:
                if f.read() != text:
                    stale.append(os.path.relpath(path, ROOT))
        for p in stale:
            print("{} is out of date: run python3 tools/sync_skill.py".format(p))
        return 1 if stale else 0
    for path, text in expected().items():
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print("wrote {}".format(os.path.relpath(path, ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
