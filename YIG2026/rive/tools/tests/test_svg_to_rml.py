"""Tests for tools/svg_to_rml.py. Run: python3 -m unittest discover -s tools/tests"""
import math
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import svg_to_rml as S

ORIGINALS = Path(__file__).resolve().parents[2] / "art" / "ch2" / "originals"
LOCKUPS = ["wordle", "connections", "strands", "spelling-bee", "mini", "midi", "daily-crossword"]


def counter():
    n = [0]

    def ids():
        n[0] += 1
        return f"9:{n[0]}"
    return ids


def absolute_vertices(shape_xml):
    """[[(x, y, in handle point or None, out handle point or None)]] per subpath, in the shape's parent space."""
    shape = ET.fromstring(shape_xml)
    sx, sy = float(shape.get("x", 0)), float(shape.get("y", 0))
    out = []
    for p in shape.findall("PointsPath"):
        verts = []
        for v in p:
            x, y = sx + float(v.get("x", 0)), sy + float(v.get("y", 0))
            hs = []
            for key in ("in", "out"):
                d = float(v.get(f"{key}Distance", 0))
                r = float(v.get(f"{key}Rotation", 0))
                hs.append((x + d * math.cos(r), y + d * math.sin(r)) if d else None)
            verts.append((x, y, hs[0], hs[1]))
        out.append(verts)
    return out


class ParsePath(unittest.TestCase):
    def test_commands(self):
        cases = [
            ("absolute square", "M0 0H10V10H0Z", 4, True),
            ("relative square", "m1 1h2v2h-2z", 4, True),
            ("path back to its start merges the two vertices", "M0 0L10 0L10 10L0 0Z", 3, True),
            ("open path", "M0 0L5 5", 2, False),
            ("two subpaths", "M0 0H1V1Z M5 5H6V6Z", None, True),
        ]
        for label, d, count, closed in cases:
            with self.subTest(label):
                subs = S.parse_path(d)
                if count is not None:
                    self.assertEqual(len(subs[0][0]), count)
                self.assertEqual(subs[0][1], closed)
        self.assertEqual(len(S.parse_path("M0 0H1V1Z M5 5H6V6Z")), 2)

    def test_cubic_handles_sit_on_their_vertices(self):
        (verts, closed), = S.parse_path("M0 0C0 5 5 10 10 10")
        self.assertEqual(verts[0].out, (0, 5))
        self.assertEqual(verts[1].into, (5 - 10, 10 - 10))
        self.assertFalse(closed)

    def test_merging_a_closing_cubic_keeps_its_in_handle(self):
        (verts, closed), = S.parse_path("M0 0L10 0C10 5 5 10 0 0Z")
        self.assertEqual(len(verts), 2)
        self.assertEqual(verts[0].into, (5, 10))

    def test_commands_the_lockups_never_use_are_refused(self):
        with self.assertRaises(ValueError):
            S.parse_path("M0 0A5 5 0 0 1 10 0")


class ShapeXml(unittest.TestCase):
    def test_round_trip_keeps_every_vertex_and_handle(self):
        d = "M10 10C10 20 20 30 30 30L40 30V50H10Z M15 15H20V20H15Z"
        shape = S.shape_xml("FF112233", S.parse_path(d), counter())
        got = absolute_vertices(shape)
        want = S.parse_path(d)
        self.assertEqual(len(got), len(want))
        for g, (w, _) in zip(got, want):
            self.assertEqual(len(g), len(w))
            for (x, y, hin, hout), v in zip(g, w):
                self.assertAlmostEqual(x, v.x, 5)
                self.assertAlmostEqual(y, v.y, 5)
                for h, rel in ((hin, v.into), (hout, v.out)):
                    if rel is None:
                        self.assertIsNone(h)
                    else:
                        self.assertAlmostEqual(h[0], v.x + rel[0], 5)
                        self.assertAlmostEqual(h[1], v.y + rel[1], 5)

    def test_hole_is_counter_clockwise(self):
        shape = ET.fromstring(S.shape_xml("FF000000", S.parse_path("M0 0H10V10H0Z M2 2V8H8V2Z"), counter()))
        flags = [p.get("isClockwise") for p in shape.findall("PointsPath")]
        self.assertEqual(flags, [None, "false"])

    def test_offset_centres_the_shape(self):
        shape = ET.fromstring(S.shape_xml("FF000000", S.parse_path("M100 100H110V110H100Z"), counter(), offset=(100, 100)))
        self.assertAlmostEqual(float(shape.get("x")), 5)
        self.assertAlmostEqual(float(shape.get("y")), 5)


class RealLockups(unittest.TestCase):
    def test_every_lockup_converts_into_icon_and_word(self):
        for name in LOCKUPS:
            with self.subTest(name):
                paths = S.svg_paths((ORIGINALS / f"{name}-lockup.svg").read_text())
                self.assertTrue(paths)
                centres = [(S.bounds(S.points(subs))[1] + S.bounds(S.points(subs))[3]) / 2 for _, subs in paths]
                self.assertTrue(any(c <= 92 for c in centres), "an icon")
                self.assertTrue(any(c > 92 for c in centres), "a word")
                for colour, subs in paths:
                    ET.fromstring(S.shape_xml(colour, subs, counter()))   # well-formed


if __name__ == "__main__":
    unittest.main()
