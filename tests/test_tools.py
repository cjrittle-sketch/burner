"""The dev tools in tools/ (bench compare, trace summary, verify, offburner),
tested offline on canned data.

Run from the repo root:  python3 -m unittest discover -s tests
"""
import importlib.util
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name):
    spec = importlib.util.spec_from_file_location(
        "tool_" + name, os.path.join(ROOT, "tools", name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


benchcmp, tracesum, verify, offburner = (
    load("benchcmp"), load("tracesum"), load("verify"), load("offburner"))


def run(**medians):
    return {"results": {k: {"median": v, "exit": 0} for k, v in medians.items()}}


class BenchCmpTests(unittest.TestCase):
    def flags(self, base, head):
        return {r[0]: r[4] for r in benchcmp.compare(base, head)}

    def test_start_timeout_regression_is_flagged(self):  # 1.2s -> 10s, Oct 2
        self.assertEqual(self.flags(run(start=1183), run(start=10204))["start"], "SLOWER")

    def test_small_or_relative_only_changes_are_noise(self):
        f = self.flags(run(back=110, tap=1000), run(back=200, tap=1250))
        self.assertEqual(f, {"back": "", "tap": ""})

    def test_new_failure_is_flagged(self):
        head = run(shot=1500)
        head["results"]["shot"]["exit"] = 1
        self.assertEqual(self.flags(run(shot=1500), head)["shot"], "FAILS NOW")

    def test_big_win_is_marked(self):
        self.assertEqual(self.flags(run(notifications=12709), run(notifications=1817))
                         ["notifications"], "faster")


class TraceSumTests(unittest.TestCase):
    def test_u2_spans_land_in_their_command(self):
        spans = [
            {"src": "burner", "run": "a", "cmd": "tap X", "step": "adb shell", "ms": 300, "t": 100.4},
            {"src": "u2mux", "step": "dump rpc", "ms": 840, "t": 100.9},
            {"src": "burner", "run": "a", "cmd": "tap X", "step": "total", "ms": 1500, "t": 101.0},
            {"src": "u2mux", "step": "tap rpc", "ms": 450, "t": 105.0},
        ]
        runs = tracesum.group(spans)
        steps = [s["step"] for s in runs["a"]["spans"]]
        self.assertEqual(steps, ["adb shell", "u2 dump rpc"])
        text = tracesum.render(runs["a"])
        self.assertIn("1200ms  unaccounted", text)  # u2 RPCs aren't double-counted


class VerifyTests(unittest.TestCase):
    def test_movement_from_shared_labels(self):
        before = [{"text": "A", "y": 1000}, {"text": "B", "y": 1200}]
        after = [{"text": "A", "y": 0}, {"text": "B", "y": 200}]
        self.assertAlmostEqual(verify.movement(before, after, 2000), 0.5)

    def test_one_row_scroll_is_small(self):  # the 240px scroll, Oct 2
        before = [{"text": "A", "y": 1000}, {"text": "B", "y": 1200}]
        after = [{"text": "A", "y": 760}, {"text": "B", "y": 960}]
        self.assertLess(verify.movement(before, after, 2400), 0.3)

    def test_fixed_chrome_doesnt_hide_a_scroll(self):  # Pixel 7a All apps
        bar = [{"text": t, "y": 191} for t in ("Navigate up", "All apps", "Search")]
        before = bar + [{"text": "A", "y": 1720}, {"text": "B", "y": 1914}]
        after = bar + [{"text": "A", "y": 301}, {"text": "B", "y": 495}]
        self.assertAlmostEqual(verify.movement(before, after, 2400), 1419 / 2400)

    def test_nothing_moved_is_zero(self):
        same = [{"text": "A", "y": 500}]
        self.assertEqual(verify.movement(same, same, 2400), 0.0)

    def test_nothing_shared_means_moved_a_screen(self):
        self.assertIsNone(verify.movement([{"text": "A", "y": 1}], [{"text": "Z", "y": 1}], 2400))


class OffBurnerTests(unittest.TestCase):
    def test_flags_going_around_burner(self):
        text = "\n".join([
            "$ ~/burner/bin/burner tap \"Apps\"",
            "adb shell dumpsys account",
            "export PATH=$HOME/burner/bin:$PATH",
            "cat > ~/burner/recipes/about.burner",
            "burner scroll down",
        ])
        whys = [h[1].split(" ")[0] for h in offburner.scan(text)]
        self.assertEqual(whys, ["dumpsys", "PATH", "recipe"])


if __name__ == "__main__":
    unittest.main()
