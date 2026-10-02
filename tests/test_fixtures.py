"""Replay saved phone screens through burner's tap planner, offline.

Each case in tests/fixtures/cases.json names a screen (a raw dump saved
with `burner dump --save tests/fixtures/<name>.xml`), a tap (a label, or
"xy" as 0-1 fractions like --xy) and the decision burner must make: tap,
refused, ambiguous or nomatch. "at" pins the pixel the tap lands on.

When a tap is wrongly refused or lands wrong on the phone: save that screen,
add a case with the right answer, watch it fail, then fix bin/burner.

Run from the repo root:  python3 -m unittest discover -s tests
"""
import importlib.util
import json
import os
import sys
import unittest
import xml.etree.ElementTree as ET
from importlib.machinery import SourceFileLoader

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
_loader = SourceFileLoader("burner_fixtures", os.path.join(
    os.path.dirname(HERE), "bin", "burner"))
_spec = importlib.util.spec_from_loader("burner_fixtures", _loader)
burner = importlib.util.module_from_spec(_spec)
sys.modules["burner_fixtures"] = burner
_loader.exec_module(burner)


def load_cases():
    with open(os.path.join(FIXTURES, "cases.json")) as f:
        return json.load(f)


def plan(case):
    root = ET.parse(os.path.join(FIXTURES, case["screen"])).getroot()
    burner._update_screen_from_dump(root)
    nodes = burner.walk(root)
    w, h = burner.screen_dims()
    if "xy" in case:
        nx, ny = case["xy"]
        return burner.plan_tap(nodes, w, h, xy=(int(nx * w), int(ny * h)))
    return burner.plan_tap(nodes, w, h, text=case["tap"])


class FixtureTapTests(unittest.TestCase):
    def test_cases(self):
        for case in load_cases():
            with self.subTest(screen=case["screen"],
                              tap=case.get("tap") or case.get("xy")):
                p = plan(case)
                self.assertEqual(p["action"], case["expect"], case.get("why", ""))
                if "at" in case:
                    self.assertEqual(list(p["xy"]), case["at"])

    def test_every_screen_has_a_case(self):
        used = {c["screen"] for c in load_cases()}
        screens = {n for n in os.listdir(FIXTURES) if n.endswith(".xml")}
        self.assertEqual(screens - used, set(), "screens with no case in cases.json")


if __name__ == "__main__":
    unittest.main()
