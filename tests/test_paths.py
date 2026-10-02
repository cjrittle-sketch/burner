"""Shipped code must find everything relative to the burner folder.

A clean install on Oct 2 needed hand patches because scripts assumed an
old ~/workspace layout. This fails on any absolute or personal path in the
files an install ships.

Run from the repo root:  python3 -m unittest discover -s tests
"""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHIPPED = ["bin", "lib", "recipes", "tools"] + [
    f for f in os.listdir(ROOT) if f.endswith(".sh")] + [
    os.path.join("docs", "install.sh")]
BAD = re.compile(r"~/workspace|\$HOME/workspace|/home/\w|/Users/\w|"
                 r"[A-Za-z]:\\\\Users|/root/|\.u2venv")
SKIP_EXT = (".png", ".jpg", ".jar", ".apk", ".zip")


def shipped_files():
    for entry in SHIPPED:
        path = os.path.join(ROOT, entry)
        if os.path.isfile(path):
            yield path
        for d, _, files in os.walk(path):
            for f in files:
                if not f.endswith(SKIP_EXT) and "scrcpy-server" not in f \
                        and "__pycache__" not in d:
                    yield os.path.join(d, f)


class PathTests(unittest.TestCase):
    def test_no_personal_or_absolute_paths(self):
        hits = []
        for path in shipped_files():
            try:
                with open(path, encoding="utf-8") as f:
                    for i, line in enumerate(f, 1):
                        if BAD.search(line):
                            hits.append("{}:{}: {}".format(
                                os.path.relpath(path, ROOT), i, line.strip()[:90]))
            except UnicodeDecodeError:
                continue
        self.assertEqual(hits, [], "paths outside the burner folder:\n" + "\n".join(hits))


if __name__ == "__main__":
    unittest.main()
