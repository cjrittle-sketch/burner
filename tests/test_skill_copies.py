"""SKILL.md is the one source; its copies must match it.

Run from the repo root:  python3 -m unittest discover -s tests
Fix a failure with:      python3 tools/sync_skill.py
"""
import importlib.util
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location(
    "sync_skill", os.path.join(ROOT, "tools", "sync_skill.py"))
sync_skill = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sync_skill)


class SkillCopiesTest(unittest.TestCase):
    def test_copies_match_skill_md(self):
        for path, text in sync_skill.expected().items():
            with open(path, encoding="utf-8") as f:
                self.assertEqual(
                    f.read(), text,
                    "{} is out of date: run python3 tools/sync_skill.py".format(
                        os.path.relpath(path, ROOT)))

    def test_site_copy_has_no_front_matter(self):
        site = sync_skill.expected()[sync_skill.SITE_COPY]
        self.assertTrue(site.startswith("> Install:"))
        self.assertNotIn("\nname: burner\n", site)


if __name__ == "__main__":
    unittest.main()
