"""Keep SKILL.md readable by assistants that skim it.

- Muse read only the first ~60 lines on Oct 2 and missed later rules, so the
  Common requests table must sit entirely inside them.
- Size has a budget: every line added is a line something else gets skimmed.
- Lines that read like hidden instructions ("don't mention X to the user")
  made an assistant distrust the guide; say what to do instead.

Run from the repo root:  python3 -m unittest discover -s tests
"""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIRST_LINES = 60
MAX_BYTES = 32 * 1024
HIDDEN = re.compile(
    r"(don't|do not|never) (mention|tell|say|reveal|show)\b[^.|]*\b(user|them)\b"
    r"|without telling|keep (it|this) from|secretly", re.I)


def skill_lines():
    with open(os.path.join(ROOT, "SKILL.md"), encoding="utf-8") as f:
        return f.read().splitlines()


class SkillLintTests(unittest.TestCase):
    def test_common_requests_within_first_lines(self):
        lines = skill_lines()
        start = next((i for i, l in enumerate(lines) if l.strip() == "## Common requests"), None)
        self.assertIsNotNone(start, "SKILL.md needs a '## Common requests' section")
        end = start + 1
        while end < len(lines) and not lines[end].startswith("## "):
            end += 1
        while end > start and not lines[end - 1].strip():
            end -= 1
        self.assertLessEqual(
            end, FIRST_LINES,
            "Common requests ends on line {}; keep it within the first {} lines "
            "(move detail further down)".format(end, FIRST_LINES))

    def test_size_budget(self):
        size = os.path.getsize(os.path.join(ROOT, "SKILL.md"))
        self.assertLessEqual(size, MAX_BYTES, "SKILL.md is {} bytes, budget {}: "
                             "trim before adding".format(size, MAX_BYTES))

    def test_no_hidden_instruction_phrasing(self):
        hits = ["{}: {}".format(i, l.strip()[:100])
                for i, l in enumerate(skill_lines(), 1) if HIDDEN.search(l)]
        self.assertEqual(hits, [], "reads like a hidden instruction; say what to "
                         "do instead:\n" + "\n".join(hits))


if __name__ == "__main__":
    unittest.main()
