"""Offline test suite for burner bin/burner.

100% OFFLINE GUARANTEE: every device/network touchpoint is guarded in
OfflineTestCase.setUp -- pc.adb, pc.adb_or_ensure, pc.u2sock, pc.ui_dump,
pc.fast_dump, pc.subprocess, pc.wake/wake_async, pc.tap_center,
pc.u2_invalidate, pc.scrcpy_send, pc.ensure, and socket.socket all raise
AssertionError if called without an explicit mock. Any test that accidentally
attempts live I/O fails loudly instead of hanging on a real connection.

Run from the repo root:  python3 -m unittest discover -s tests
"""
import argparse
import contextlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from importlib.machinery import SourceFileLoader
from types import SimpleNamespace
from unittest import mock

_PC_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bin", "burner")


def _load_pc():
    # bin/burner has no .py extension, so spec_from_file_location can't find a
    # loader -- use SourceFileLoader explicitly.
    loader = SourceFileLoader("pc_under_test", _PC_PATH)
    spec = importlib.util.spec_from_loader("pc_under_test", loader)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["pc_under_test"] = mod
    loader.exec_module(mod)
    return mod


pc = _load_pc()
ROOT = pc.ROOT

SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<hierarchy rotation="0">
  <node index="0" text="" resource-id="" class="android.widget.FrameLayout" package="com.example" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focused="false" focusable="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[0,0][1080,2400]">
    <node index="0" text="Hello" resource-id="com.example:id/title" class="android.widget.TextView" package="com.example" content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focused="false" focusable="false" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[100,200][500,300]"/>
    <node index="1" text="OK" resource-id="com.example:id/ok" class="android.widget.Button" package="com.example" content-desc="" checkable="false" checked="false" clickable="true" enabled="true" focused="false" focusable="true" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[100,400][400,500]"/>
    <node index="2" text="" resource-id="com.example:id/q" class="android.widget.EditText" package="com.example" content-desc="Search" checkable="false" checked="false" clickable="true" enabled="true" focused="true" focusable="true" scrollable="false" long-clickable="false" password="false" selected="false" bounds="[100,600][900,700]"/>
  </node>
</hierarchy>"""

TAP_XML = """<hierarchy rotation="0">
  <node text="" class="android.widget.FrameLayout" bounds="[0,0][1080,2400]" clickable="false" enabled="true" focused="false" checked="false">
    <node text="Not now" class="android.widget.Button" bounds="[100,200][300,400]" clickable="true" enabled="true" focused="false" checked="false"/>
  </node>
</hierarchy>"""

OVERLAY_XML = """<hierarchy rotation="0">
  <node text="" class="android.widget.FrameLayout" bounds="[0,0][1080,2400]" clickable="false" enabled="true" focused="false" checked="false">
    <node text="Hi" class="android.widget.Button" bounds="[100,200][300,400]" clickable="true" enabled="true" focused="false" checked="false"/>
    <node text="Dialog" class="android.widget.FrameLayout" bounds="[500,1100][600,1300]" clickable="false" enabled="true" focused="false" checked="false"/>
  </node>
</hierarchy>"""

TOOLBAR_XML = """<hierarchy rotation="0">
  <node text="" class="android.widget.FrameLayout" bounds="[0,0][1080,2400]" clickable="false" enabled="true" focused="false" checked="false">
    <node text="" class="android.view.ViewGroup" bounds="[0,0][1080,200]" clickable="false" enabled="true" focused="false" checked="false">
      <node text="Search" class="android.widget.EditText" bounds="[100,40][980,160]" clickable="true" enabled="true" focused="false" checked="false"/>
    </node>
  </node>
</hierarchy>"""


def _wnode(text="", desc="", cls="android.widget.TextView", clickable=False,
           enabled=True, bounds="[0,0][10,10]", center=(5, 5)):
    """Build a walk()-style node dict."""
    return {"text": text, "desc": desc, "rid": "", "class": cls,
            "bounds": bounds, "center": center, "clickable": clickable,
            "enabled": enabled, "focused": False, "checked": False,
            "parents": []}


class OfflineTestCase(unittest.TestCase):
    """Installs loud offline guards around every live-I/O entry point."""

    GUARDS = ["subprocess", "u2sock", "adb", "adb_or_ensure", "ui_dump",
              "fast_dump", "wake", "wake_async", "tap_center",
              "u2_invalidate", "scrcpy_send", "ensure"]

    def setUp(self):
        super().setUp()
        self._guards = {}
        for name in self.GUARDS:
            p = mock.patch.object(pc, name)
            m = p.start()
            m.side_effect = AssertionError(
                "OFFLINE GUARD TRIPPED: pc.%s called without a mock "
                "(live I/O attempted)" % name)
            self._guards[name] = p
            self.addCleanup(p.stop)
        p = mock.patch("socket.socket")
        m = p.start()
        m.side_effect = AssertionError(
            "OFFLINE GUARD TRIPPED: socket.socket called (live I/O attempted)")
        self._guards["socket.socket"] = p
        self.addCleanup(p.stop)

    def allow(self, name, **kwargs):
        """Replace the guard on pc.<name> (or plain attribute) with a
        working mock; return it."""
        if name in self._guards:
            self._guards[name].stop()
        p = mock.patch.object(pc, name, **kwargs)
        m = p.start()
        self.addCleanup(p.stop)
        return m

    def parse(self, argv):
        return pc.build_parser().parse_args(argv)

    @contextlib.contextmanager
    def cap(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            yield out, err


# ------------------------------------------------------- 1. compact dump

class CompactDumpTests(OfflineTestCase):
    def test_is_interactive_clickable(self):
        self.assertTrue(pc.is_interactive(_wnode(cls="android.widget.TextView",
                                                 clickable=True)))

    def test_is_interactive_edittext(self):
        self.assertTrue(pc.is_interactive(_wnode(cls="android.widget.EditText",
                                                 clickable=False)))

    def test_is_interactive_button_classes(self):
        for cls in ("Button", "CheckBox", "Switch", "SeekBar"):
            with self.subTest(cls=cls):
                self.assertTrue(pc.is_interactive(
                    _wnode(cls="android.widget." + cls, clickable=False)))

    def test_is_interactive_plain_textview_false(self):
        # A plain TextView with text is NOT interactive per is_interactive
        # (compact_visible shows it because it has text -- tested below).
        self.assertFalse(pc.is_interactive(_wnode(text="Hello",
                                                  cls="android.widget.TextView",
                                                  clickable=False)))

    def test_is_interactive_imagebutton_false(self):
        # Short class name must match exactly; ImageButton is not Button.
        self.assertFalse(pc.is_interactive(_wnode(cls="android.widget.ImageButton",
                                                  clickable=False)))

    def test_compact_bounds_str(self):
        self.assertEqual(pc.compact_bounds_str("[12,34][56,78]"),
                         "12,34-56,78")

    def test_compact_bounds_str_empty(self):
        self.assertEqual(pc.compact_bounds_str(""), "")

    def test_compact_bounds_str_garbage(self):
        self.assertEqual(pc.compact_bounds_str("not-bounds"), "")

    def test_format_compact_shape(self):
        n = _wnode(text="OK", cls="android.widget.Button", clickable=True,
                   bounds="[100,400][300,500]", center=(200, 450))
        self.assertEqual(pc.format_compact(n), "OK (click) [Button] (200,450)")

    def test_format_compact_omits_empty_flags(self):
        n = _wnode(text="Hello", cls="android.widget.TextView",
                   clickable=False, center=(300, 250))
        self.assertEqual(pc.format_compact(n), "Hello [TextView] (300,250)")

    def test_format_compact_disabled_flag(self):
        n = _wnode(text="OK", cls="android.widget.Button", clickable=True,
                   enabled=False, center=(200, 450))
        self.assertEqual(pc.format_compact(n),
                         "OK (click,disabled) [Button] (200,450)")

    def test_format_compact_show_bounds(self):
        n = _wnode(text="OK", cls="android.widget.Button", clickable=True,
                   bounds="[100,400][300,500]", center=(200, 450))
        self.assertEqual(pc.format_compact(n, show_bounds=True),
                         "OK (click) [Button] 100,400-300,500 (200,450)")

    def test_format_compact_missing_center(self):
        n = _wnode(text="X", cls="android.widget.TextView", center=(None, None))
        self.assertEqual(pc.format_compact(n), "X [TextView] (?,?)")

    def test_format_compact_desc_label(self):
        n = _wnode(desc="Search", cls="android.widget.EditText",
                   clickable=True, center=(500, 650))
        self.assertEqual(pc.format_compact(n),
                         "[Search] (click) [EditText] (500,650)")

    def test_node_compact_full(self):
        n = _wnode(text="OK", cls="android.widget.Button", clickable=True,
                   center=(200, 450))
        self.assertEqual(pc.node_compact(n),
                         {"class": "Button", "text": "OK",
                          "x": 200, "y": 450, "clickable": True})

    def test_node_compact_omits_empty_fields(self):
        n = _wnode(cls="android.widget.TextView", enabled=False,
                   center=(None, None))
        self.assertEqual(pc.node_compact(n),
                         {"class": "TextView", "enabled": False})

    def test_compact_visible_include_all(self):
        self.assertTrue(pc.compact_visible(_wnode(), include_all=True))

    def test_compact_visible_interactive(self):
        self.assertTrue(pc.compact_visible(
            _wnode(cls="android.widget.Button", clickable=True),
            include_all=False))

    def test_compact_visible_text(self):
        self.assertTrue(pc.compact_visible(_wnode(text="Hello"),
                                           include_all=False))

    def test_compact_visible_desc(self):
        self.assertTrue(pc.compact_visible(_wnode(desc="Search"),
                                           include_all=False))

    def test_compact_visible_empty_filtered(self):
        self.assertFalse(pc.compact_visible(_wnode(), include_all=False))

    def test_compact_token_reduction(self):
        # 200-node synthetic dump: compact rendering must be <50% of the
        # raw XML dump's char count (the actual token win), and strictly
        # shorter than the --verbose line format.
        parts = ['<hierarchy rotation="0">']
        for i in range(200):
            parts.append(
                '<node text="Item number %d" class="android.widget.TextView" '
                'clickable="false" enabled="true" bounds="[%d,%d][%d,%d]"/>' % (
                    i, i % 100, i // 100, i % 100 + 50, i // 100 + 30))
        parts.append('</hierarchy>')
        raw_xml = "".join(parts)
        nodes = pc.walk(ET.fromstring(raw_xml))
        shown = [n for n in nodes if pc.compact_visible(n, False)]
        self.assertEqual(len(shown), 200)
        compact = "\n".join(pc.format_compact(n) for n in shown)
        verbose = "\n".join(
            "{} [{}] {}".format(pc.node_label(n),
                                n["class"].split(".")[-1], n["bounds"])
            for n in shown)
        self.assertLess(len(compact), len(verbose),
                        "compact should beat --verbose rendering")
        self.assertLess(len(compact), 0.5 * len(raw_xml),
                        "compact=%d raw_xml=%d" % (len(compact), len(raw_xml)))


# ------------------------------------------------- 2. occlusion-aware taps

def _occ_nodes():
    """Doc order: early (before target), target, cover1, cover2 (on top)."""
    early = _wnode(text="early", bounds="[0,0][100,100]")
    target = _wnode(text="target", bounds="[0,0][100,100]")
    cover1 = _wnode(text="cover1", bounds="[10,10][60,60]")
    cover2 = _wnode(text="cover2", bounds="[20,20][50,50]")
    return early, target, cover1, cover2


class OcclusionTests(OfflineTestCase):
    def test_is_point_covered_returns_cover(self):
        early, target, cover1, cover2 = _occ_nodes()
        hit = pc.is_point_covered([early, target, cover1, cover2],
                                  30, 30, target)
        self.assertIsNotNone(hit)
        # cover2 is later in document order -> on top
        self.assertEqual(hit["text"], "cover2")

    def test_is_point_covered_none_when_clear(self):
        early, target, cover1, cover2 = _occ_nodes()
        self.assertIsNone(pc.is_point_covered([early, target, cover1, cover2],
                                              90, 90, target))

    def test_is_point_covered_ignores_earlier_nodes(self):
        # 'early' covers (5,5) but is BEFORE target in doc order -> ignored.
        early, target, cover1, cover2 = _occ_nodes()
        self.assertIsNone(pc.is_point_covered([early, target, cover1, cover2],
                                              5, 5, target))

    def test_is_point_covered_exclude_none_checks_all(self):
        early, target, cover1, cover2 = _occ_nodes()
        hit = pc.is_point_covered([early, target, cover1, cover2],
                                  30, 30, None)
        self.assertIsNotNone(hit)
        self.assertEqual(hit["text"], "cover2")

    def test_find_uncovered_point_alternate(self):
        node = _wnode(bounds="[0,0][100,100]")
        cover = _wnode(text="cover", bounds="[40,40][60,60]")
        nodes = [node, cover]
        pt = pc.find_uncovered_point(node, nodes)
        # center (50,50) covered -> first free sample is (25,50)
        self.assertEqual(pt, (25, 50))

    def test_find_uncovered_point_fully_covered(self):
        node = _wnode(bounds="[0,0][100,100]")
        cover = _wnode(text="cover", bounds="[0,0][100,100]")
        self.assertIsNone(pc.find_uncovered_point(node, [node, cover]))

    def test_find_uncovered_point_bad_bounds(self):
        node = _wnode(bounds="")
        self.assertIsNone(pc.find_uncovered_point(node, [node]))

    def test_parse_normalized_xy_valid(self):
        self.assertEqual(pc.parse_normalized_xy("0.5,0.8"), (0.5, 0.8))

    def test_parse_normalized_xy_boundaries(self):
        self.assertEqual(pc.parse_normalized_xy("0,0"), (0.0, 0.0))
        self.assertEqual(pc.parse_normalized_xy("1,1"), (1.0, 1.0))

    def test_parse_normalized_xy_whitespace(self):
        self.assertEqual(pc.parse_normalized_xy("  0.25 , 0.75  "),
                         (0.25, 0.75))

    def test_parse_normalized_xy_out_of_range(self):
        for bad in ("1.5,0.5", "0.5,1.01", "-0.1,0.5", "0.5,-2"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    pc.parse_normalized_xy(bad)

    def test_parse_normalized_xy_malformed(self):
        for bad in ("abc", "0.5", "0.5,0.8,0.1", "", "0.5,"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    pc.parse_normalized_xy(bad)

    def test_screen_dims_default(self):
        with mock.patch.object(pc, "_screen_wh", "1080 2400"):
            self.assertEqual(pc.screen_dims(), (1080, 2400))

    def test_screen_dims_rotated(self):
        with mock.patch.object(pc, "_screen_wh", "2400 1080"):
            self.assertEqual(pc.screen_dims(), (2400, 1080))

    def test_update_screen_from_dump_rotation(self):
        old = pc._screen_wh
        try:
            pc._update_screen_from_dump(ET.fromstring('<hierarchy rotation="1"/>'))
            self.assertEqual(pc._screen_wh, "2400 1080")
            pc._update_screen_from_dump(ET.fromstring('<hierarchy rotation="0"/>'))
            self.assertEqual(pc._screen_wh, "1080 2400")
            pc._update_screen_from_dump(ET.fromstring('<hierarchy rotation="3"/>'))
            self.assertEqual(pc._screen_wh, "2400 1080")
        finally:
            pc._screen_wh = old


# ------------------------------------------------------------- 3. doctor

class DoctorTests(OfflineTestCase):
    """All 7 doctor checks with mocked dependencies -- never touches adb."""

    CHECK_NAMES = ["adb binary", "adb server", "tunnel target", "u2 daemon",
                   "device state", "dump pipeline", "latency"]
    # fail key -> check name it must break
    FAIL_MAP = {"binary": "adb binary", "server": "adb server",
                "tunnel": "tunnel target", "u2": "u2 daemon",
                "state": "device state", "dump": "dump pipeline",
                "latency": "latency"}

    def _doctor_mocks(self, fail=None, raise_dep=None):
        sub = self.allow("subprocess")
        adb_bin, target = pc.ADB_BIN, pc.TARGET

        def run(cmd, **kw):
            cmd = list(cmd)
            if raise_dep == "subprocess":
                raise RuntimeError("boom")
            if cmd[:2] == [adb_bin, "version"]:
                if fail == "binary":
                    return SimpleNamespace(returncode=1, stdout="",
                                           stderr="oops")
                return SimpleNamespace(
                    returncode=0,
                    stdout="Android Debug Bridge version 1.0.41\n", stderr="")
            if cmd[:2] == [adb_bin, "devices"]:
                if fail == "server":
                    return SimpleNamespace(returncode=1, stdout="",
                                           stderr="oops")
                return SimpleNamespace(returncode=0,
                                       stdout="List of devices attached\n",
                                       stderr="")
            if cmd[:3] == [adb_bin, "connect", target]:
                if fail == "tunnel":
                    return SimpleNamespace(
                        returncode=0,
                        stdout="failed to connect to 'x': refused\n", stderr="")
                return SimpleNamespace(
                    returncode=0,
                    stdout="connected to {}\n".format(target), stderr="")
            raise AssertionError("unexpected subprocess call: %r" % (cmd,))

        sub.run.side_effect = run

        real_exists = os.path.exists
        if raise_dep == "exists":
            ex = mock.patch.object(pc.os.path, "exists",
                                   side_effect=RuntimeError("boom"))
        else:
            def _exists(pth):
                if pth == pc.U2_SOCK:
                    return fail != "u2"
                return real_exists(pth)
            ex = mock.patch.object(pc.os.path, "exists", side_effect=_exists)
        ex.start()
        self.addCleanup(ex.stop)

        def u2(cmd, arg="", timeout=30):
            if raise_dep == "u2sock":
                raise RuntimeError("boom")
            if cmd == "health":
                return "ok"
            if cmd == "dump":
                if fail == "latency":
                    return None
                return '<hierarchy rotation="0"></hierarchy>'
            raise AssertionError("unexpected u2sock cmd: %r" % cmd)

        self.allow("u2sock", side_effect=u2)

        def adb_fn(*a, **kw):
            if raise_dep == "adb":
                raise RuntimeError("boom")
            return SimpleNamespace(
                returncode=0,
                stdout="offline\n" if fail == "state" else "device\n",
                stderr="")

        self.allow("adb", side_effect=adb_fn)

        def fd():
            if raise_dep == "fast_dump":
                raise RuntimeError("boom")
            if fail == "dump":
                return None
            return ET.fromstring(
                '<hierarchy rotation="0">'
                '<node text="x" class="android.widget.TextView" '
                'bounds="[0,0][10,10]"/></hierarchy>')

        self.allow("fast_dump", side_effect=fd)

    def _run_doctor(self, argv, fail=None, raise_dep=None):
        self._doctor_mocks(fail=fail, raise_dep=raise_dep)
        args = self.parse(argv)
        with self.cap() as (out, err):
            rc = pc.cmd_doctor(args)
        return rc, out.getvalue(), err.getvalue()

    def test_doctor_all_pass_exit_0(self):
        rc, out, err = self._run_doctor(["doctor"])
        self.assertEqual(rc, 0)
        self.assertIn("7/7 checks passed", out)

    def test_doctor_all_pass_json(self):
        rc, out, err = self._run_doctor(["doctor", "--json"])
        self.assertEqual(rc, 0)
        data = json.loads(out)
        self.assertTrue(data["ok"])
        self.assertEqual(len(data["checks"]), 7)
        self.assertTrue(all(c["ok"] for c in data["checks"]))
        self.assertIsInstance(data["latency_ms"], int)

    def test_doctor_each_failing_check(self):
        for fail, name in self.FAIL_MAP.items():
            with self.subTest(fail=fail):
                rc, out, err = self._run_doctor(["doctor", "--json"],
                                               fail=fail)
                self.assertEqual(rc, 1, "fail=%s" % fail)
                data = json.loads(out)
                self.assertFalse(data["ok"])
                by_name = {c["name"]: c for c in data["checks"]}
                self.assertFalse(by_name[name]["ok"],
                                 "check %r should be failed" % name)
                others = [c for c in data["checks"] if c["name"] != name]
                self.assertTrue(all(c["ok"] for c in others),
                                "only %r should fail, got %r"
                                % (name, [c["name"] for c in others
                                          if not c["ok"]]))

    def test_doctor_human_marks_failed_check(self):
        rc, out, err = self._run_doctor(["doctor"], fail="tunnel")
        self.assertEqual(rc, 1)
        self.assertIn("[FAIL] tunnel target", out)

    def test_doctor_exception_safe_subprocess(self):
        rc, out, err = self._run_doctor(["doctor"], raise_dep="subprocess")
        self.assertEqual(rc, 1)  # must not raise
        self.assertIn("RuntimeError", out)

    def test_doctor_exception_safe_u2sock(self):
        rc, out, err = self._run_doctor(["doctor"], raise_dep="u2sock")
        self.assertEqual(rc, 1)
        self.assertIn("RuntimeError", out)

    def test_doctor_exception_safe_adb(self):
        rc, out, err = self._run_doctor(["doctor"], raise_dep="adb")
        self.assertEqual(rc, 1)
        self.assertIn("RuntimeError", out)

    def test_doctor_exception_safe_fast_dump(self):
        rc, out, err = self._run_doctor(["doctor"], raise_dep="fast_dump")
        self.assertEqual(rc, 1)
        self.assertIn("RuntimeError", out)

    def test_doctor_exception_safe_exists(self):
        rc, out, err = self._run_doctor(["doctor"], raise_dep="exists")
        self.assertEqual(rc, 1)
        self.assertIn("RuntimeError", out)


# ---------------------------------------------------------- 4. --json output

class JsonOutputTests(OfflineTestCase):
    def _tap_mocks(self, xml):
        self.allow("wake_async")
        self.allow("u2sock", return_value=None)
        self.allow("ui_dump", return_value=ET.fromstring(xml))
        self.allow("tap_center")
        self.allow("u2_invalidate")

    def test_json_flag_position_equivalent(self):
        a1 = self.parse(["--json", "dump"])
        a2 = self.parse(["dump", "--json"])
        a3 = self.parse(["dump"])
        self.assertTrue(pc.as_json(a1))
        self.assertTrue(pc.as_json(a2))
        self.assertFalse(pc.as_json(a3))

    def test_json_dump(self):
        self.allow("ui_dump", return_value=ET.fromstring(SAMPLE_XML))
        args = self.parse(["dump", "--json"])
        with self.cap() as (out, err):
            rc = pc.cmd_dump(args)
        self.assertEqual(rc, 0)
        data = json.loads(out.getvalue())
        self.assertTrue(data["ok"])
        self.assertEqual(len(data["nodes"]), 3)  # Hello, OK, Search field
        self.assertTrue(all("class" in n for n in data["nodes"]))
        self.assertEqual(err.getvalue(), "")

    def test_json_tap_ok(self):
        self._tap_mocks(TAP_XML)
        args = self.parse(["tap", "Not now", "--json"])
        with self.cap() as (out, err):
            rc = pc.cmd_tap(args)
        self.assertEqual(rc, 0)
        data = json.loads(out.getvalue())
        self.assertTrue(data["ok"])
        self.assertEqual(data["tapped"]["text"], "Not now")
        self.assertEqual((data["tapped"]["x"], data["tapped"]["y"]),
                         (200, 300))

    def test_json_tap_no_match_errors_to_stderr(self):
        self._tap_mocks(TAP_XML)
        args = self.parse(["tap", "Nope", "--json"])
        with self.cap() as (out, err):
            rc = pc.cmd_tap(args)
        self.assertEqual(rc, 1)
        data = json.loads(out.getvalue())
        self.assertFalse(data["ok"])
        self.assertIn("error", data)
        self.assertIn('no match for "Nope"', err.getvalue())

    def test_json_tap_xy_refused_by_real_overlay(self):
        self._tap_mocks(OVERLAY_XML)
        args = self.parse(["tap", "--xy", "0.5,0.5", "--json"])
        with self.cap() as (out, err):
            rc = pc.cmd_tap(args)
        self.assertEqual(rc, 1)
        data = json.loads(out.getvalue())
        self.assertFalse(data["ok"])
        self.assertIn("tap refused", err.getvalue())
        self.assertIn("tap refused", data["error"])

    def test_tap_xy_no_false_positive_from_containers(self):
        # BUG (implementation, reported not fixed): with no overlay at all,
        # the --xy occlusion check still refuses because the full-screen
        # root container covers the point (exclude_node=None includes
        # ancestors). Correct behavior: tap proceeds.
        self._tap_mocks(TAP_XML)
        args = self.parse(["tap", "--xy", "0.5,0.5", "--json"])
        with self.cap() as (out, err):
            rc = pc.cmd_tap(args)
        self.assertEqual(rc, 0, "stdout=%r stderr=%r"
                         % (out.getvalue(), err.getvalue()))
        data = json.loads(out.getvalue())
        self.assertTrue(data["ok"])

    def test_tap_xy_toolbar_container_not_blocking(self):
        # Live false positive (2026-09-30): the Amazon search toolbar
        # container covered the tap point and the --xy tap was refused.
        # An edge-to-edge layout container is the tap's natural landing
        # spot, not an obstruction: tap proceeds.
        self._tap_mocks(TOOLBAR_XML)
        args = self.parse(["tap", "--xy", "0.5,0.04", "--json"])
        with self.cap() as (out, err):
            rc = pc.cmd_tap(args)
        self.assertEqual(rc, 0, "stdout=%r stderr=%r"
                         % (out.getvalue(), err.getvalue()))
        data = json.loads(out.getvalue())
        self.assertTrue(data["ok"])

    def test_looks_like_overlay(self):
        w, h = 1080, 2400
        dialog = {"class": "android.widget.FrameLayout",
                  "bounds": "[500,1100][600,1300]"}   # floating box
        toolbar = {"class": "android.view.ViewGroup",
                   "bounds": "[0,0][1080,200]"}       # edge-to-edge
        sheet_cls = {"class": "android.widget.BottomSheet",
                     "bounds": "[0,1800][1080,2400]"}  # class says sheet
        fullscreen = {"class": "android.widget.FrameLayout",
                      "bounds": "[0,0][1080,2400]"}
        self.assertTrue(pc._looks_like_overlay(dialog, w, h))
        self.assertFalse(pc._looks_like_overlay(toolbar, w, h))
        self.assertTrue(pc._looks_like_overlay(sheet_cls, w, h))
        self.assertFalse(pc._looks_like_overlay(fullscreen, w, h))

    def test_json_wait_timeout_errors_to_stderr(self):
        self.allow("u2sock", return_value=pc.U2_NOT_FOUND)
        args = self.parse(["wait", "Never", "--json"])
        with self.cap() as (out, err):
            rc = pc.cmd_wait(args)
        self.assertEqual(rc, 1)
        data = json.loads(out.getvalue())
        self.assertFalse(data["ok"])
        self.assertIn('timeout waiting for "Never"', err.getvalue())

    def test_json_state(self):
        self.allow(
            "adb_or_ensure",
            return_value=SimpleNamespace(
                returncode=0,
                stdout="  mFocusedApp=AppWindowToken{abc} u0 com.example/.Main\n",
                stderr=""))
        self.allow("ui_dump", return_value=ET.fromstring(SAMPLE_XML))
        args = self.parse(["state", "--json"])
        with self.cap() as (out, err):
            rc = pc.cmd_state(args)
        self.assertEqual(rc, 0)
        data = json.loads(out.getvalue())
        self.assertTrue(data["ok"])
        self.assertEqual(data["app"], "com.example/.Main")
        self.assertIn("Hello", data["texts"])


# ------------------------------------------------------------ 5. unicode input

class UnicodeTests(OfflineTestCase):
    def test_needs_unicode_route_ascii(self):
        self.assertFalse(pc.needs_unicode_route("hello"))

    def test_needs_unicode_route_emoji(self):
        self.assertTrue(pc.needs_unicode_route("héllo 🎉"))

    def test_needs_unicode_route_cjk(self):
        self.assertTrue(pc.needs_unicode_route("你好"))

    def test_type_via_adbkeyboard_call_sequence(self):
        calls = []
        self.allow("get_current_ime", return_value="com.example/.Ime")
        m_set = self.allow("set_ime")
        m_bc = self.allow("broadcast_adbkeyboard_text")
        m_tap = self.allow("tap_center")
        m_adb = self.allow("adb_or_ensure")
        with self.cap() as (out, err):
            rc = pc.type_via_adbkeyboard("hi", field_xy=(10, 20),
                                         clear=True, clear_keys=3)
        self.assertEqual(rc, 0)
        # get IME -> set AdbIME -> tap field -> clear -> broadcast -> restore
        m_set.assert_any_call(pc.ADBKEYBOARD_IME)
        m_tap.assert_called_once_with(10, 20)
        self.assertEqual(m_adb.call_count, 3)  # clear_keys=3 DEL keyevents
        m_bc.assert_called_once_with("hi")
        self.assertEqual(m_set.call_args_list[0],
                         mock.call(pc.ADBKEYBOARD_IME))
        self.assertEqual(m_set.call_args_list[-1],
                         mock.call("com.example/.Ime"))
        self.assertIn("adbkeyboard", out.getvalue())

    def test_broadcast_uses_es_msg(self):
        # Real broadcast_adbkeyboard_text, mocked adb: verifies the exact
        # broadcast args (--es msg) with unicode intact. The message is
        # single-quoted for the device shell: `adb shell` joins args with
        # spaces and re-parses them on-device, so an unquoted message with
        # spaces would be split and the text silently lost.
        self.allow("get_current_ime", return_value="com.example/.Ime")
        self.allow("set_ime")
        m_adb = self.allow("adb")
        m_adb.return_value = SimpleNamespace(returncode=0, stdout="",
                                             stderr="")
        pc.broadcast_adbkeyboard_text("héllo 🎉")
        self.assertEqual(
            m_adb.call_args[0],
            ("shell", "am", "broadcast", "-a", "ADB_INPUT_TEXT",
             "--es", "msg", "'héllo 🎉'"))

    def test_broadcast_quotes_single_quotes(self):
        # Embedded single quotes are escaped so the device shell still
        # sees one argument.
        m_adb = self.allow("adb")
        m_adb.return_value = SimpleNamespace(returncode=0, stdout="",
                                             stderr="")
        pc.broadcast_adbkeyboard_text("it's")
        self.assertEqual(
            m_adb.call_args[0][-1], "'it'\\''s'")

    def test_type_via_adbkeyboard_restores_ime_on_exception(self):
        self.allow("get_current_ime", return_value="com.example/.Ime")
        m_set = self.allow("set_ime")
        self.allow("broadcast_adbkeyboard_text",
                   side_effect=RuntimeError("boom"))
        with self.assertRaises(RuntimeError):
            pc.type_via_adbkeyboard("hi")
        # finally block restores even though broadcast raised
        self.assertEqual(m_set.call_args_list,
                         [mock.call(pc.ADBKEYBOARD_IME),
                          mock.call("com.example/.Ime")])

    def test_cmd_type_unicode_flag_forces_adbkeyboard(self):
        m_uni = self.allow("type_via_adbkeyboard", return_value=0)
        self.allow("ui_dump", return_value=ET.fromstring(SAMPLE_XML))
        args = SimpleNamespace(text="hello", field=None, clear=False,
                               clear_keys=20, unicode=True, ascii=False,
                               slow=False)
        with self.cap():
            rc = pc.cmd_type(args)
        self.assertEqual(rc, 0)
        m_uni.assert_called_once()
        self.assertEqual(m_uni.call_args[0][0], "hello")

    def test_cmd_type_ascii_flag_forces_legacy(self):
        m_uni = self.allow("type_via_adbkeyboard", return_value=0)
        m_adb = self.allow("adb_or_ensure")
        m_adb.return_value = SimpleNamespace(returncode=0, stdout="",
                                             stderr="")
        self.allow("u2sock", return_value=None)  # health -> None: skip fast path
        self.allow("u2_invalidate")
        self.allow("ui_dump", return_value=ET.fromstring(SAMPLE_XML))
        args = SimpleNamespace(text="hé", field=None, clear=False,
                               clear_keys=20, unicode=False, ascii=True,
                               slow=False)
        with mock.patch.object(pc.time, "sleep", lambda s: None):
            with self.cap():
                rc = pc.cmd_type(args)
        self.assertEqual(rc, 0)
        m_uni.assert_not_called()
        sent = [c[0] for c in m_adb.call_args_list]
        self.assertIn(("shell", "input", "text", "h"), sent)
        self.assertIn(("shell", "input", "text", "\\é"), sent)


# ----------------------------------------------- 6. existing functionality

class RegressionTests(OfflineTestCase):
    # walk()
    def test_walk_parses_nested_xml(self):
        nodes = pc.walk(ET.fromstring(SAMPLE_XML))
        self.assertEqual(len(nodes), 5)  # hierarchy + frame + 3 children
        texts = [n["text"] for n in nodes]
        self.assertIn("Hello", texts)
        self.assertIn("OK", texts)

    def test_walk_centers_and_parents(self):
        nodes = pc.walk(ET.fromstring(SAMPLE_XML))
        ok = next(n for n in nodes if n["text"] == "OK")
        self.assertEqual(ok["center"], (250, 450))  # [100,400][400,500]
        self.assertEqual(len(ok["parents"]), 2)
        self.assertEqual(ok["parents"][-1].attrib["class"],
                         "android.widget.FrameLayout")
        self.assertTrue(ok["clickable"])
        edit = next(n for n in nodes if n["desc"] == "Search")
        self.assertTrue(edit["focused"])

    # find_nodes()
    def test_find_nodes_exact(self):
        nodes = pc.walk(ET.fromstring(SAMPLE_XML))
        hits = pc.find_nodes(nodes, "OK", exact=True)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["text"], "OK")

    def test_find_nodes_exact_no_substring(self):
        nodes = pc.walk(ET.fromstring(SAMPLE_XML))
        self.assertEqual(pc.find_nodes(nodes, "O", exact=True), [])

    def test_find_nodes_fuzzy(self):
        nodes = pc.walk(ET.fromstring(SAMPLE_XML))
        hits = pc.find_nodes(nodes, "ok", exact=False)
        self.assertEqual([n["text"] for n in hits], ["OK"])

    def test_find_nodes_matches_desc(self):
        nodes = pc.walk(ET.fromstring(SAMPLE_XML))
        hits = pc.find_nodes(nodes, "Search", exact=True)
        self.assertEqual(len(hits), 1)
        self.assertIn("EditText", hits[0]["class"])

    # clickable_target()
    def test_clickable_target_own_center(self):
        n = _wnode(clickable=True, center=(10, 20))
        self.assertEqual(pc.clickable_target(n), (10, 20))

    def test_clickable_target_clickable_ancestor(self):
        parent = ET.fromstring(
            '<node clickable="true" bounds="[0,0][100,100]"/>')
        n = _wnode(clickable=False, center=(None, None))
        n["parents"] = [parent]
        self.assertEqual(pc.clickable_target(n), (50, 50))

    def test_clickable_target_falls_back_to_own(self):
        parent = ET.fromstring(
            '<node clickable="false" bounds="[0,0][100,100]"/>')
        n = _wnode(clickable=False, center=(7, 8))
        n["parents"] = [parent]
        self.assertEqual(pc.clickable_target(n), (7, 8))

    # extract_code()
    def test_extract_code_facebook_style(self):
        self.assertEqual(
            pc.extract_code("42327079 is your Facebook code", ""), "42327079")

    def test_extract_code_enter_this_code(self):
        self.assertEqual(
            pc.extract_code("", "Enter this code: 7392"), "7392")

    def test_extract_code_verification_code(self):
        self.assertEqual(
            pc.extract_code("", "Your verification code is 567812"), "567812")

    def test_extract_code_generic_code(self):
        self.assertEqual(
            pc.extract_code("", "Use code 4242 to verify"), "4242")

    def test_extract_code_fallback_digits(self):
        self.assertEqual(
            pc.extract_code("Welcome aboard",
                            "Your reference number is 987654"), "987654")

    def test_extract_code_subject_first(self):
        self.assertEqual(
            pc.extract_code("111111 is your code", "222222 is your code"),
            "111111")

    def test_extract_code_none(self):
        self.assertIsNone(pc.extract_code("hello", "nothing here"))

    # esc_char()
    def test_esc_char_space(self):
        self.assertEqual(pc.esc_char(" "), "%s")

    def test_esc_char_alnum_passthrough(self):
        for c in "aZ09":
            self.assertEqual(pc.esc_char(c), c)

    def test_esc_char_specials_escaped(self):
        self.assertEqual(pc.esc_char("!"), "\\!")
        self.assertEqual(pc.esc_char("$"), "\\$")
        self.assertEqual(pc.esc_char("&"), "\\&")
        self.assertEqual(pc.esc_char("-"), "\\-")

    # load_config()
    def _write_config(self, d, content):
        p = os.path.join(d, "config.env")
        with open(p, "w") as f:
            f.write(content)
        return p

    def test_load_config_parses_values(self):
        with tempfile.TemporaryDirectory() as d:
            self._write_config(d, 'FOO="bar"\nBAZ=qux\nEQ="a=b"\n')
            with mock.patch.object(pc, "ROOT", d):
                cfg = pc.load_config()
        self.assertEqual(cfg, {"FOO": "bar", "BAZ": "qux", "EQ": "a=b"})

    def test_load_config_ignores_comments_and_blanks(self):
        with tempfile.TemporaryDirectory() as d:
            self._write_config(d, "# comment\n\nFOO=1\n   \n#X=y\n")
            with mock.patch.object(pc, "ROOT", d):
                cfg = pc.load_config()
        self.assertEqual(cfg, {"FOO": "1"})

    def test_load_config_missing_file(self):
        with tempfile.TemporaryDirectory() as d:
            with mock.patch.object(pc, "ROOT", d):
                self.assertEqual(pc.load_config(), {})

    # cmd_do()
    def test_cmd_do_runs_steps(self):
        args = SimpleNamespace(flow="sleep 0; sleep 0")
        with self.cap():
            rc = pc.cmd_do(args)
        self.assertEqual(rc, 0)

    def test_cmd_do_stops_on_failure(self):
        calls = []

        def fake_parse(argv):
            ns = mock.Mock()
            step = " ".join(argv)
            ns.fn = lambda n: calls.append(step) or (
                1 if "fail" in step else 0)
            return ns

        stub = mock.Mock()
        stub.parse_args = fake_parse
        with mock.patch.object(pc, "build_parser", return_value=stub):
            with self.cap():
                rc = pc.cmd_do(SimpleNamespace(
                    flow="step one; fail step; step three"))
        self.assertEqual(rc, 1)
        self.assertEqual(calls, ["step one", "fail step"])

    def test_cmd_do_bad_step(self):
        args = SimpleNamespace(flow="sleep 0; nosuchcommand")
        with self.cap() as (out, err):
            rc = pc.cmd_do(args)
        self.assertEqual(rc, 1)
        self.assertIn("bad step 2", err.getvalue())

    # cmd_recipe()
    def test_cmd_recipe_missing(self):
        with tempfile.TemporaryDirectory() as d:
            with mock.patch.object(pc, "ROOT", d):
                with self.cap() as (out, err):
                    rc = pc.cmd_recipe(SimpleNamespace(name="nope"))
        self.assertEqual(rc, 1)
        self.assertIn("no recipe", err.getvalue())

    def test_cmd_recipe_skips_comments_and_blanks(self):
        with tempfile.TemporaryDirectory() as d:
            rdir = os.path.join(d, "recipes")
            os.makedirs(rdir)
            with open(os.path.join(rdir, "r.burner"), "w") as f:
                f.write("# a comment\n\nsleep 0\n# another\nsleep 0\n")
            with mock.patch.object(pc, "ROOT", d):
                with mock.patch.object(pc, "cmd_do", return_value=0) as m:
                    rc = pc.cmd_recipe(SimpleNamespace(name="r"))
        self.assertEqual(rc, 0)
        self.assertEqual(m.call_args[0][0].flow, "sleep 0; sleep 0")

    def test_cmd_recipe_failing_step(self):
        with tempfile.TemporaryDirectory() as d:
            rdir = os.path.join(d, "recipes")
            os.makedirs(rdir)
            with open(os.path.join(rdir, "r.burner"), "w") as f:
                f.write("sleep 0\nnosuchcmd\n")
            with mock.patch.object(pc, "ROOT", d):
                with self.cap():
                    rc = pc.cmd_recipe(SimpleNamespace(name="r"))
        self.assertEqual(rc, 1)


    # gmail_cli()
    def test_gmail_cli_default(self):
        with mock.patch.dict(pc.CFG, {}, clear=True):
            self.assertEqual(pc.gmail_cli(), ["hatch_gws_cli"])

    def test_gmail_cli_override(self):
        with mock.patch.dict(pc.CFG, {"GMAIL_CLI": "mytool --flag x"}):
            self.assertEqual(pc.gmail_cli(), ["mytool", "--flag", "x"])


# --------------------------------------- 7. docs/implementation consistency

class DocsTests(OfflineTestCase):
    def _readme_commands(self):
        with open(os.path.join(ROOT, "SKILL.md"), encoding="utf-8") as f:
            text = f.read()
        # every "## Command reference ..." section (short and full)
        sections = [s.split("\n## ", 1)[0]
                    for s in text.split("## Command reference")[1:]]
        cmds = {}
        for line in "\n".join(sections).splitlines():
            s = line.strip()
            if not s.startswith("burner "):
                continue
            parts = s.split(None, 2)
            if len(parts) < 2:
                continue
            cmd, rest = parts[1], parts[2] if len(parts) > 2 else ""
            # quoted example text (e.g. pc do '... --timeout 30 ...') holds
            # other commands' flags -- strip quotes first.
            rest = re.sub(r"'[^']*'", "", rest)
            rest = re.sub(r'"[^"]*"', "", rest)
            flags = set(re.findall(r"--([A-Za-z0-9-]+)", rest))
            cmds.setdefault(cmd, set()).update(flags)
        return cmds

    def test_readme_flags_exist_in_argparse(self):
        cmds = self._readme_commands()
        self.assertTrue(cmds, "no commands parsed from SKILL.md")
        ap = pc.build_parser()
        sub = next(a for a in ap._actions
                   if isinstance(a, argparse._SubParsersAction))
        top_opts = set()
        for a in ap._actions:
            top_opts.update(o.lstrip("-") for o in a.option_strings)
        for cmd, flags in sorted(cmds.items()):
            with self.subTest(cmd=cmd):
                self.assertIn(cmd, sub.choices,
                              "SKILL.md documents unknown command")
                parser = sub.choices[cmd]
                opts = set(top_opts)
                for a in parser._actions:
                    opts.update(o.lstrip("-") for o in a.option_strings)
                missing = flags - opts
                self.assertFalse(
                    missing,
                    "SKILL.md flags missing from argparse for %r: %s"
                    % (cmd, sorted(missing)))

    def test_no_muse_phone_string_in_tree(self):
        bad = []
        for dirpath, dirnames, filenames in os.walk(ROOT):
            if ".git" in dirnames:
                dirnames.remove(".git")
            if "tests" in dirnames:
                # this suite itself mentions the string; skip it
                dirnames.remove("tests")
            for fn in filenames:
                p = os.path.join(dirpath, fn)
                if "muse-phone" in fn:
                    bad.append(p)
                    continue
                try:
                    with open(p, "r", encoding="utf-8",
                              errors="strict") as f:
                        content = f.read()
                except (UnicodeDecodeError, OSError):
                    continue
                if "muse-phone" in content:
                    bad.append(p)
        self.assertEqual(bad, [])

    def test_config_example_has_placeholders(self):
        with open(os.path.join(ROOT, "config.env.example")) as f:
            text = f.read()
        assignments = {}
        for line in text.splitlines():
            s = line.strip()
            if s and not s.startswith("#") and "=" in s:
                k, v = s.split("=", 1)
                assignments[k.strip()] = v.strip().strip('"')
        self.assertTrue(assignments)
        ipre = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
        for k, v in assignments.items():
            self.assertFalse(ipre.search(v),
                             "real-looking IP in %s=%r" % (k, v))
        self.assertIn("YOUR_PHONE_TAILSCALE_IP", assignments.values())
        # ADB_PORT is pinned to 5555 by adb-auto-enable (installed during
        # pairing); it is intentionally not a placeholder anymore.
        self.assertEqual(assignments.get("ADB_PORT"), "5555")


# --------------------------------- 8. offline safety + sanity checks

class OfflineSafetyTests(OfflineTestCase):
    def test_guard_blocks_adb(self):
        with self.assertRaises(AssertionError):
            pc.adb("get-state")

    def test_guard_blocks_u2sock(self):
        with self.assertRaises(AssertionError):
            pc.u2sock("dump")

    def test_guard_blocks_socket(self):
        import socket as _socket
        with self.assertRaises(AssertionError):
            _socket.socket(_socket.AF_UNIX)

    def test_bin_burner_compiles(self):
        r = subprocess.run(
            [sys.executable, "-m", "py_compile", os.path.join(ROOT, "bin", "burner")],
            capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_bin_burner_help_offline(self):
        env = dict(os.environ, BURNER_WORKSPACE=ROOT)
        r = subprocess.run(
            [os.path.join(ROOT, "bin", "burner"), "--help"],
            capture_output=True, text=True, timeout=30, env=env, cwd=ROOT)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("phone control CLI", r.stdout)


# --------------------------------- 11. ambiguous taps, snap handles, settle

AMBI_XML = """<hierarchy rotation="0">
  <node text="" class="android.widget.FrameLayout" bounds="[0,0][1080,2400]" clickable="false" enabled="true" focused="false" checked="false">
    <node text="OK" class="android.widget.Button" bounds="[100,400][400,500]" clickable="true" enabled="true" focused="false" checked="false"/>
    <node text="Cancel" class="android.widget.Button" bounds="[500,400][800,500]" clickable="true" enabled="true" focused="false" checked="false"/>
    <node text="OK" class="android.widget.Button" bounds="[100,600][400,700]" clickable="true" enabled="true" focused="false" checked="false"/>
  </node>
</hierarchy>"""

FUZZY_AMBI_XML = """<hierarchy rotation="0">
  <node text="" class="android.widget.FrameLayout" bounds="[0,0][1080,2400]" clickable="false" enabled="true" focused="false" checked="false">
    <node text="Okay" class="android.widget.Button" bounds="[100,400][400,500]" clickable="true" enabled="true" focused="false" checked="false"/>
    <node text="OK fine" class="android.widget.Button" bounds="[100,600][400,700]" clickable="true" enabled="true" focused="false" checked="false"/>
  </node>
</hierarchy>"""

SETTLE_A_XML = """<hierarchy rotation="0">
  <node text="" class="android.widget.FrameLayout" bounds="[0,0][1080,2400]" clickable="false" enabled="true" focused="false" checked="false">
    <node text="Loading" class="android.widget.TextView" bounds="[100,200][500,300]" clickable="false" enabled="true" focused="false" checked="false"/>
  </node>
</hierarchy>"""

SETTLE_B_XML = """<hierarchy rotation="0">
  <node text="" class="android.widget.FrameLayout" bounds="[0,0][1080,2400]" clickable="false" enabled="true" focused="false" checked="false">
    <node text="Results" class="android.widget.TextView" bounds="[100,200][500,300]" clickable="false" enabled="true" focused="false" checked="false"/>
    <node text="Buy" class="android.widget.Button" bounds="[100,400][400,500]" clickable="true" enabled="true" focused="false" checked="false"/>
  </node>
</hierarchy>"""


def _twelve_line_xml():
    kids = "".join(
        '<node text="Row%d" class="android.widget.TextView" '
        'bounds="[%d,200][%d,300]" clickable="false" enabled="true" '
        'focused="false" checked="false"/>' % (i, 100 + i * 10, 500 + i * 10)
        for i in range(12))
    return ('<hierarchy rotation="0"><node text="" '
            'class="android.widget.FrameLayout" bounds="[0,0][1080,2400]" '
            'clickable="false" enabled="true" focused="false" '
            'checked="false">' + kids + "</node></hierarchy>")


class AmbiguousTapTests(OfflineTestCase):
    def _tap(self, argv, xml=AMBI_XML):
        self.allow("wake_async")
        self.allow("ui_dump", return_value=ET.fromstring(xml))
        tc = self.allow("tap_center")
        args = self.parse(argv)
        with self.cap() as (out, err):
            rc = pc.cmd_tap(args)
        return rc, out.getvalue(), err.getvalue(), tc

    def test_ambiguous_tap_refused(self):
        rc, out, err, tc = self._tap(["tap", "OK"])
        self.assertEqual(rc, 1)
        self.assertIn("ambiguous tap", err)
        self.assertIn("2 candidates", err)
        self.assertIn("use --index N or a longer label", err)
        self.assertIn("[0]", err)
        self.assertIn("[1]", err)
        tc.assert_not_called()

    def test_ambiguous_tap_index_selects(self):
        rc, out, err, tc = self._tap(["tap", "OK", "--index", "1"])
        self.assertEqual(rc, 0)
        tc.assert_called_once_with(250, 650)  # second OK button

    def test_single_match_needs_no_index(self):
        rc, out, err, tc = self._tap(["tap", "Cancel"])
        self.assertEqual(rc, 0)
        tc.assert_called_once_with(650, 450)

    def test_fallback_selector_second_label_wins(self):
        rc, out, err, tc = self._tap(["tap", "Nope || Cancel"])
        self.assertEqual(rc, 0)
        tc.assert_called_once_with(650, 450)

    def test_fallback_selector_first_hit_wins(self):
        rc, out, err, tc = self._tap(["tap", "Cancel || OK"])
        self.assertEqual(rc, 0)
        tc.assert_called_once_with(650, 450)  # Cancel matched first

    def test_fallback_all_miss(self):
        rc, out, err, tc = self._tap(["tap", "Nope || Nada"])
        self.assertEqual(rc, 1)
        self.assertIn("no match", err)
        tc.assert_not_called()

    def test_fuzzy_ambiguity_flagged(self):
        rc, out, err, tc = self._tap(["tap", "ok"], xml=FUZZY_AMBI_XML)
        self.assertEqual(rc, 1)
        self.assertIn("ambiguous tap", err)
        self.assertIn("(fuzzy)", err)

    def test_ambiguous_json_shape(self):
        self.allow("wake_async")
        self.allow("ui_dump", return_value=ET.fromstring(AMBI_XML))
        self.allow("tap_center")
        args = self.parse(["tap", "--json", "OK"])
        with self.cap() as (out, err):
            rc = pc.cmd_tap(args)
        self.assertEqual(rc, 1)
        body = json.loads(out.getvalue())
        self.assertFalse(body["ok"])
        self.assertIn("ambiguous tap", body["error"])


class SnapTests(OfflineTestCase):
    def setUp(self):
        super().setUp()
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._dir_patch = mock.patch.object(pc, "SNAP_DIR", self._tmp.name)
        self._dir_patch.start()
        self.addCleanup(self._dir_patch.stop)
        self._snap_patch = mock.patch.object(
            pc, "SNAP_PATH", os.path.join(self._tmp.name, "snap.json"))
        self._snap_patch.start()
        self.addCleanup(self._snap_patch.stop)

    def _save(self, xml=AMBI_XML):
        nodes = pc.walk(ET.fromstring(xml))
        return pc.snap_save(nodes)

    def test_snap_numbers_handles(self):
        numbered = self._save()
        handles = [h for h, _ in numbered]
        # Handles are generation-pinned: @eN~s<gen>
        self.assertTrue(handles[0].startswith("@e1~s"))
        self.assertTrue(all(h.startswith("@e") for h in handles))
        self.assertTrue(all("~s" in h for h in handles))
        # 3 visible nodes: the empty FrameLayout root carries no label
        self.assertEqual(len(numbered), 3)

    def test_snap_file_persists_entries(self):
        self._save()
        with open(os.path.join(self._tmp.name, "snap.json")) as f:
            snap = json.load(f)
        self.assertIn("ts", snap)
        self.assertEqual(snap["entries"]["1"]["x"], 250)

    def test_snap_resolve_roundtrip(self):
        self._save()
        self.assertEqual(pc.snap_resolve("@e1"), (250, 450))
        self.assertEqual(pc.snap_resolve("  @e3 "), (250, 650))

    def test_snap_resolve_no_file(self):
        with self.assertRaisesRegex(ValueError, "run `burner snap` first"):
            pc.snap_resolve("@e1")

    def test_snap_resolve_bad_handle(self):
        with self.assertRaisesRegex(ValueError, "not a snap handle"):
            pc.snap_resolve("OK")

    def test_snap_resolve_expired(self):
        self._save()
        path = os.path.join(self._tmp.name, "snap.json")
        with open(path) as f:
            snap = json.load(f)
        snap["ts"] -= pc.SNAP_TTL + 10
        with open(path, "w") as f:
            json.dump(snap, f)
        with self.assertRaisesRegex(ValueError, "expired"):
            pc.snap_resolve("@e1")

    def test_snap_resolve_missing_entry(self):
        self._save()
        with self.assertRaisesRegex(ValueError, "no such handle"):
            pc.snap_resolve("@e99")

    def test_u2_invalidate_drops_snap(self):
        # Every mutating action funnels through u2_invalidate(); it must
        # delete the snap file so @eN handles never outlive their screen.
        self._save()
        path = os.path.join(self._tmp.name, "snap.json")
        self.assertTrue(os.path.exists(path))
        guard = self._guards["u2_invalidate"]
        with mock.patch.object(pc, "u2_invalidate", guard.temp_original):
            self.allow("u2sock", return_value=None)
            si = self.allow("snap_invalidate")
            pc.u2_invalidate()
            si.assert_called_once_with()

    def test_cmd_snap_output(self):
        self.allow("ui_dump", return_value=ET.fromstring(AMBI_XML))
        args = self.parse(["snap"])
        with self.cap() as (out, err):
            rc = pc.cmd_snap(args)
        self.assertEqual(rc, 0)
        lines = out.getvalue().strip().split("\n")
        # Generation-pinned handle: @e1~s<gen>
        self.assertTrue(lines[0].startswith("@e1~s"))
        self.assertIn("OK", lines[0])

    def test_tap_at_snap_handle(self):
        self._save()
        self.allow("wake_async")
        self.allow("ui_dump", return_value=ET.fromstring(AMBI_XML))
        tc = self.allow("tap_center")
        args = self.parse(["tap", "@e2"])
        with self.cap() as (out, err):
            rc = pc.cmd_tap(args)
        self.assertEqual(rc, 0)
        tc.assert_called_once_with(650, 450)  # Cancel button coords
        self.assertIn("@e2", out.getvalue())

    def test_tap_stale_snap_fails(self):
        args = self.parse(["tap", "@e1"])
        with self.cap() as (out, err):
            rc = pc.cmd_tap(args)
        self.assertEqual(rc, 1)
        self.assertIn("no snap saved", err.getvalue())


class SettleTests(OfflineTestCase):
    def _lines(self, xml):
        return pc.visible_lines(pc.walk(ET.fromstring(xml)))

    def test_settle_unchanged(self):
        root = ET.fromstring(SETTLE_A_XML)
        self.allow("ui_dump", return_value=root)
        added, removed, final_fp = pc.settle_lines(self._lines(SETTLE_A_XML),
                                                   timeout=2, quiet=0.05, poll=0.01)
        self.assertEqual((added, removed), ([], []))
        self.assertIsNotNone(final_fp)

    def test_settle_detects_change(self):
        roots = [ET.fromstring(SETTLE_B_XML)] * 30
        self.allow("ui_dump", side_effect=roots)
        added, removed, final_fp = pc.settle_lines(self._lines(SETTLE_A_XML),
                                                   timeout=2, quiet=0.05, poll=0.01)
        self.assertTrue(any("Results" in l for l in added))
        self.assertTrue(any("Loading" in l for l in removed))

    def test_settle_partial_dump_retried(self):
        full = _twelve_line_xml()
        tiny = SETTLE_A_XML  # 2 lines vs 13: <=20% of a 12+ screen
        roots = [ET.fromstring(tiny)] + [ET.fromstring(full)] * 6
        self.allow("ui_dump", side_effect=roots)
        added, removed, final_fp = pc.settle_lines(self._lines(full),
                                                   timeout=5, quiet=0.05, poll=0.01)
        # The partial read must not surface as a mass disappearance.
        self.assertEqual((added, removed), ([], []))

    def test_tap_settle_reports_unchanged(self):
        self.allow("wake_async")
        self.allow("ui_dump", return_value=ET.fromstring(TAP_XML))
        tc = self.allow("tap_center")
        args = self.parse(["tap", "--settle", "Not now"])
        with self.cap() as (out, err):
            with mock.patch.object(pc, "settle_lines",
                                   return_value=([], [], "rid:test123")) as sl:
                rc = pc.cmd_tap(args)
        self.assertEqual(rc, 0)
        tc.assert_called_once()
        sl.assert_called_once()
        self.assertIn("unchanged", out.getvalue())

    def test_tap_settle_json_shape(self):
        self.allow("wake_async")
        self.allow("ui_dump", return_value=ET.fromstring(TAP_XML))
        self.allow("tap_center")
        args = self.parse(["tap", "--json", "--settle", "Not now"])
        with self.cap() as (out, err):
            with mock.patch.object(
                    pc, "settle_lines",
                    return_value=(["+ Results [TextView] (300,250)"],
                                  ["- Loading [TextView] (300,250)"],
                                  "rid:test123")):
                rc = pc.cmd_tap(args)
        self.assertEqual(rc, 0)
        body = json.loads(out.getvalue())
        self.assertTrue(body["ok"])
        self.assertIn("settled", body)
        self.assertEqual(len(body["settled"]["added"]), 1)

    def test_print_settle_diff_cap(self):
        added = ["line%d" % i for i in range(100)]
        with self.cap() as (out, err):
            pc._print_settle_diff(added, [], cap=80)
        text = out.getvalue()
        self.assertIn("settled: +100 -0", text)
        self.assertIn("... 20 more", text)


# --------------------------------- 12. setup wizard

def _setup_args(**kw):
    base = dict(list_steps=False, step=None, confirm=False, yes=True,
                code=None, ip=None, pair_port=None, connect_port=None)
    base.update(kw)
    return SimpleNamespace(**base)


class SetupWizardTests(OfflineTestCase):
    def setUp(self):
        super().setUp()
        # Redirect the setup state file to a temp dir.
        self.tmp = tempfile.mkdtemp()
        self._sp = mock.patch.object(pc, "SETUP_STATE_PATH",
                                     os.path.join(self.tmp, "setup-state.json"))
        self._sp.start()
        self.addCleanup(self._sp.stop)

    def _adb(self, table):
        """Build a mock for pc.adb from {(cmd tuple): stdout}."""
        def fake(*args, **kwargs):
            key = tuple(str(a) for a in args)
            if key in table:
                return SimpleNamespace(returncode=0, stdout=table[key],
                                       stderr="")
            return SimpleNamespace(returncode=1, stdout="", stderr="no")
        return fake

    def test_step_registry_order_and_kinds(self):
        names = [s["name"] for s in pc.SETUP_STEPS]
        self.assertEqual(names, ["prereqs", "tailscale-phone", "dev-options",
                                 "wireless-debug", "pair",
                                 "install-adb-auto-enable", "self-pair",
                                 "always-on-vpn", "fix-port", "verify"])
        kinds = {s["name"]: s["kind"] for s in pc.SETUP_STEPS}
        self.assertEqual(kinds["prereqs"], "agent")
        self.assertEqual(kinds["tailscale-phone"], "human")
        self.assertEqual(kinds["pair"], "agent")
        self.assertEqual(kinds["self-pair"], "agent")
        # Human steps must carry an instruction and a screenshot path.
        for s in pc.SETUP_STEPS:
            if s["kind"] == "human":
                self.assertTrue(s["instruction"], s["name"])
                self.assertTrue(s["shot"], s["name"])
                self.assertNotIn("\u2014", s["instruction"])  # no em dashes

    def test_list_steps(self):
        m = self.allow("adb")
        m.side_effect = self._adb({("get-state",): "unknown"})
        with self.cap() as (out, err):
            rc = pc.cmd_setup(_setup_args(list_steps=True))
        self.assertEqual(rc, 0)
        text = out.getvalue()
        for name in ("prereqs", "pair", "verify"):
            self.assertIn(name, text)

    def test_human_step_prints_instruction_no_block(self):
        m = self.allow("adb")
        m.side_effect = self._adb({})
        with self.cap() as (out, err):
            rc = pc.cmd_setup(_setup_args(step="tailscale-phone"))
        self.assertEqual(rc, 0)
        text = out.getvalue()
        self.assertIn("Tailscale", text)
        self.assertIn("setup/setup-01-tailscale.png", text)

    def test_confirm_records_human_done(self):
        with self.cap():
            rc = pc.cmd_setup(_setup_args(step="tailscale-phone", confirm=True))
        self.assertEqual(rc, 0)
        st = pc._setup_state_load()
        self.assertIn("tailscale-phone", st["done"])

    def test_read_pair_dialog(self):
        xml = ('<hierarchy><node text="Pair with device" bounds="[0,0][1,1]"/>'
               '<node text="Wi-Fi pairing code" bounds="[0,0][1,1]"/>'
               '<node text="482915" bounds="[0,0][1,1]"/>'
               '<node text="IP address &amp; Port" bounds="[0,0][1,1]"/>'
               '<node text="100.64.1.2:37129" bounds="[0,0][1,1]"/>'
               '</hierarchy>')
        with mock.patch.object(pc, "ui_dump",
                               return_value=pc.ET.fromstring(xml)):
            self.assertEqual(pc._setup_read_pair_dialog(),
                             ("482915", "37129"))

    def test_self_pair_already_paired(self):
        with mock.patch.object(pc, "_setup_app_status",
                               return_value={"isPaired": True}):
            with self.cap() as (out, err):
                rc = pc._run_self_pair(_setup_args())
        self.assertEqual(rc, 0)
        self.assertIn("already paired", out.getvalue())

    def test_unknown_status_falls_back_to_state_file(self):
        pc._setup_state_save("self-pair")
        m = self.allow("adb")
        m.side_effect = self._adb({})
        step = next(s for s in pc.SETUP_STEPS if s["name"] == "self-pair")
        self.assertEqual(pc._setup_step_status(step), "done")

    def test_live_false_beats_state_file(self):
        pc._setup_state_save("wireless-debug")
        m = self.allow("adb")
        m.side_effect = self._adb({("shell", "settings", "get", "global",
                                    "adb_wifi_enabled"): "0"})
        step = next(s for s in pc.SETUP_STEPS if s["name"] == "wireless-debug")
        self.assertEqual(pc._setup_step_status(step), "pending")

    def test_check_wireless_debug_true(self):
        m = self.allow("adb")
        m.side_effect = self._adb({("shell", "settings", "get", "global",
                                    "adb_wifi_enabled"): "1"})
        self.assertTrue(pc._check_wireless_debug())

    def test_check_always_on_vpn(self):
        m = self.allow("adb")
        m.side_effect = self._adb({("shell", "settings", "get", "secure",
                                    "always_on_vpn_app"): "com.tailscale.ipn"})
        self.assertTrue(pc._check_always_on_vpn())

    def test_run_always_on_vpn_refuses_lockdown(self):
        m = self.allow("adb")
        m.side_effect = self._adb({("shell", "settings", "get", "secure",
                                    "always_on_vpn_lockdown"): "1"})
        with self.cap() as (out, err):
            rc = pc._run_always_on_vpn(_setup_args())
        self.assertEqual(rc, 1)
        self.assertIn("lockdown", err.getvalue().lower())

    def test_run_always_on_vpn_success(self):
        calls = []

        def fake_adb(*args, **kwargs):
            calls.append(tuple(str(a) for a in args))
            key = tuple(str(a) for a in args)
            if key == ("shell", "settings", "get", "secure",
                       "always_on_vpn_lockdown"):
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            if key == ("shell", "settings", "put", "secure",
                       "always_on_vpn_app", "com.tailscale.ipn"):
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            if key == ("shell", "settings", "get", "secure",
                       "always_on_vpn_app"):
                return SimpleNamespace(returncode=0, stdout="com.tailscale.ipn",
                                       stderr="")
            return SimpleNamespace(returncode=1, stdout="", stderr="")
        m = self.allow("adb")
        m.side_effect = fake_adb
        with self.cap():
            rc = pc._run_always_on_vpn(_setup_args())
        self.assertEqual(rc, 0)

    def test_pair_needs_code_ip_port(self):
        with self.cap() as (out, err):
            rc = pc.cmd_setup(_setup_args(step="pair"))
        self.assertEqual(rc, 1)
        self.assertIn("--code", err.getvalue())

    def test_pair_rejects_bad_code(self):
        with self.cap():
            rc = pc.cmd_setup(_setup_args(step="pair", code="abc",
                                          ip="100.0.0.1", pair_port="1234"))
        self.assertEqual(rc, 1)

    def test_pair_code_never_written_to_disk(self):
        popen = self.allow("_setup_popen")
        popen.return_value = mock.Mock()
        spawn = self.allow("_setup_spawn")
        spawn.return_value = SimpleNamespace(returncode=0, stdout="paired",
                                             stderr="")
        # get-state: offline until pairing runs, then device.
        states = {"n": 0}

        def fake_adb(*args, **kwargs):
            key = tuple(str(a) for a in args)
            if key == ("get-state",):
                states["n"] += 1
                return SimpleNamespace(
                    returncode=0,
                    stdout="device" if states["n"] > 1 else "offline",
                    stderr="")
            return SimpleNamespace(returncode=1, stdout="", stderr="no")
        m = self.allow("adb")
        m.side_effect = fake_adb
        write_cfg = self.allow("_setup_write_config")
        with self.cap():
            rc = pc.cmd_setup(_setup_args(step="pair", code="482913",
                                          ip="100.99.0.1", pair_port="37001",
                                          connect_port="5555"))
        self.assertEqual(rc, 0)
        # The code went to `adb pair` on stdin, not argv or disk.
        pair_call = [c for c in spawn.call_args_list
                     if c[0][0][:2] == [pc.ADB_BIN, "pair"]]
        self.assertTrue(pair_call)
        self.assertNotIn("482913", " ".join(pair_call[0][0][0]))
        self.assertEqual(pair_call[0][1].get("input_text").strip(), "482913")
        for root, _dirs, files in os.walk(self.tmp):
            for f in files:
                with open(os.path.join(root, f)) as fh:
                    self.assertNotIn("482913", fh.read())
        written = write_cfg.call_args[0][0]
        self.assertNotIn("482913", json.dumps(written))

    def test_setup_not_recorded(self):
        args = self.parse(["setup", "--step", "pair", "--code", "482913"])
        with mock.patch.object(pc.sys, "argv",
                               ["pc", "setup", "--step", "pair",
                                "--code", "482913"]):
            self.assertIsNone(pc.record_command_line(args))

    def test_install_app_downloads_apk(self):
        urlopen = self.allow("_setup_urlopen")
        urlopen.side_effect = [
            json.dumps({"assets": [
                {"name": "adb-auto-enable-v0.3.5.apk",
                 "browser_download_url": "https://example/x.apk"}]}).encode(),
            b"fake-apk-bytes",
        ]
        m = self.allow("adb")
        m.side_effect = self._adb({})
        with mock.patch.object(pc, "WORKSPACE", self.tmp):
            with self.cap():
                path = pc._setup_find_apk()
        self.assertTrue(path and path.endswith(".apk"))
        with open(path, "rb") as f:
            self.assertEqual(f.read(), b"fake-apk-bytes")

    def test_install_app_uses_local_apk_first(self):
        apk = os.path.join(self.tmp, "adb-auto-enable-local.apk")
        with open(apk, "wb") as f:
            f.write(b"x")
        urlopen = self.allow("_setup_urlopen")
        with mock.patch.object(pc, "WORKSPACE", self.tmp):
            path = pc._setup_find_apk()
        self.assertEqual(path, apk)
        urlopen.assert_not_called()

    def test_write_config_preserves_comments(self):
        cfg = os.path.join(self.tmp, "config.env")
        with open(cfg, "w") as f:
            f.write('# comment\nADB_PORT="1234"\nLOCAL_PORT="15555"\n')
        with mock.patch.object(pc, "ROOT", self.tmp):
            pc._setup_write_config({"ADB_PORT": "5555",
                                    "PHONE_TAILSCALE_IP": "100.1.2.3"})
            with open(cfg) as f:
                text = f.read()
        self.assertIn("# comment", text)
        self.assertIn('ADB_PORT="5555"', text)
        self.assertIn('PHONE_TAILSCALE_IP="100.1.2.3"', text)
        self.assertNotIn('"1234"', text)

    def test_verify_reports_red_on_doctor_failure(self):
        with mock.patch.object(pc, "cmd_doctor", return_value=1):
            with self.cap() as (out, err):
                rc = pc._run_verify(_setup_args())
        self.assertEqual(rc, 1)
        self.assertIn("RED", err.getvalue())


if __name__ == "__main__":
    unittest.main()
