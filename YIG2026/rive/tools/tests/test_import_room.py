"""Tests for tools/import_room.py. Run: python3 -m unittest discover -s tools/tests

The illustrator's side is a small synthetic artboard built here, so each behaviour has a known right answer. The
chapter side is the real chapters/ch2/scene.rml (read, never written), since the importer copies Wordle's structure.
"""
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import import_room as I

CHAPTER = Path(__file__).resolve().parents[2] / "chapters" / "ch2" / "scene.rml"

# A room with a wall and floor (left out), a hidden group (left out), a drop-in piece, a piece that overhangs the
# frame, and a ball rig: a Solo whose active child's scaleX follows the joystick's x axis and whose y follows its y
# axis. The loop keys the joystick, the Solo's position, and the piece (whose loop does not close).
SOURCE = """<Rive version="1" kind="fragment">
<Artboard width="1495" height="1067" name="TEST_room" id="0:1">
  <Node x="700" y="600" name="Piece" id="0:10">
    <Shape id="0:11"><PointsPath isClosed="true" id="0:12">
      <StraightVertex x="-20" y="-20" id="0:13"/><StraightVertex x="20" y="-20" id="0:14"/>
      <StraightVertex x="20" y="20" id="0:15"/><StraightVertex x="-20" y="20" id="0:16"/>
    </PointsPath><Fill id="0:17"><SolidColor colorValue="FF00FF00" id="0:18"/></Fill></Shape>
    <Node hidden="true" name="Hidden Bit" id="0:19"/>
  </Node>
  <Solo activeComponentId="0:31" x="500" y="700" name="Ball_Move" id="0:30">
    <Node name="Ball_A" id="0:31">
      <Shape name="Ball_Base" id="0:32"><PointsPath isClosed="true" id="0:33">
        <StraightVertex x="-10" y="-10" id="0:34"/><StraightVertex x="10" y="-10" id="0:35"/>
        <StraightVertex x="10" y="10" id="0:36"/><StraightVertex x="-10" y="10" id="0:37"/>
      </PointsPath><Fill id="0:38"><SolidColor colorValue="FFFF0000" id="0:39"/></Fill></Shape>
    </Node>
    <Node name="Ball_B" id="0:40"/>
  </Solo>
  <Node x="1480" y="650" name="Overhang" id="0:50">
    <Shape id="0:51"><PointsPath isClosed="true" id="0:52">
      <StraightVertex x="-5" y="-5" id="0:53"/><StraightVertex x="40" y="-5" id="0:54"/>
      <StraightVertex x="40" y="5" id="0:55"/><StraightVertex x="-5" y="5" id="0:56"/>
    </PointsPath><Fill id="0:57"><SolidColor colorValue="FF0000FF" id="0:58"/></Fill></Shape>
  </Node>
  <Joystick x="-1" xId="0:70" yId="0:80" id="0:60"/>
  <Node y="710" name="Floor 9" id="0:90"/>
  <Node name="Wall 9" id="0:91"/>
  <LinearAnimation name="Squash" id="0:70">
    <KeyedObject objectId="0:31" id="0:71"><KeyedProperty property="scaleX" id="0:72">
      <KeyFrameDouble value="1" interpolationType="linear" id="0:73"/><KeyFrameDouble value="2" frame="60" id="0:74"/>
    </KeyedProperty></KeyedObject>
  </LinearAnimation>
  <LinearAnimation name="Lift" id="0:80">
    <KeyedObject objectId="0:31" id="0:81"><KeyedProperty property="y" id="0:82">
      <KeyFrameDouble value="-4" interpolationType="linear" id="0:83"/><KeyFrameDouble value="4" frame="60" id="0:84"/>
    </KeyedProperty></KeyedObject>
  </LinearAnimation>
  <LinearAnimation duration="120" loopValue="loop" name="Loop" id="0:100">
    <KeyedObject objectId="0:60" id="0:101">
      <KeyedProperty property="x" id="0:102">
        <KeyFrameDouble value="-1" interpolationType="linear" id="0:103"/>
        <KeyFrameDouble value="1" interpolationType="linear" frame="60" id="0:104"/>
        <KeyFrameDouble value="-1" frame="120" id="0:105"/>
      </KeyedProperty>
    </KeyedObject>
    <KeyedObject objectId="0:30" id="0:110">
      <KeyedProperty property="x" id="0:111">
        <KeyFrameDouble value="500" interpolationType="cubic" id="0:112"><CubicEaseInterpolator x1="0.3" x2="0.7" y2="1" id="0:113"/></KeyFrameDouble>
        <KeyFrameDouble value="560" interpolationType="elastic" frame="60" id="0:114"/>
        <KeyFrameDouble value="500" frame="120" id="0:115"/>
      </KeyedProperty>
      <KeyedProperty property="y" id="0:116">
        <KeyFrameDouble value="700" id="0:117"/>
      </KeyedProperty>
    </KeyedObject>
    <KeyedObject objectId="0:10" id="0:120">
      <KeyedProperty property="x" id="0:121">
        <KeyFrameDouble value="700" interpolationType="linear" id="0:122"/>
        <KeyFrameDouble value="706" frame="120" id="0:123"/>
      </KeyedProperty>
    </KeyedObject>
  </LinearAnimation>
</Artboard>
</Rive>"""

CONFIG = {
    "room": "Test Room", "scene": 9, "artboard": "TEST_room", "loop": "Loop", "ball": "Ball_Move",
    "wall": "FF123456", "floor": "FF654321", "lockup": "art/ch2/originals/spelling-bee-lockup.svg",
    "intro": {"plane": [0.05, 1.55], "drops": [{"name": "Piece", "ids": ["0:10"], "from": 1.0, "to": 1.5}],
              "ball": {"roll": [1.15, 1.9], "land": [1.9, 2.05]}},
}


def build_room():
    text = CHAPTER.read_text()
    b = I.Build(CONFIG, text, ET.fromstring(SOURCE))
    pieces = b.build()
    return b, pieces, text


class Sampling(unittest.TestCase):
    def test_value_at(self):
        keys = [(0, 0.0, "linear", None), (10, 10.0, "hold", None), (20, 20.0, "hold", None)]
        cases = [(-5, 0.0), (0, 0.0), (5, 5.0), (10, 10.0), (15, 10.0), (25, 20.0)]
        for f, want in cases:
            with self.subTest(frame=f):
                self.assertAlmostEqual(I.value_at(keys, f), want)

    def test_cubic_ease_ends_and_middle(self):
        for ctrl, t, want in [((0.42, 0, 0.58, 1), 0.0, 0.0), ((0.42, 0, 0.58, 1), 1.0, 1.0), ((0.42, 0, 0.58, 1), 0.5, 0.5),
                              ((0, 0, 1, 1), 0.25, 0.25)]:
            with self.subTest(ctrl=ctrl, t=t):
                self.assertAlmostEqual(I.bezier_ease(*ctrl, t), want, 4)

    def test_thin_is_exact_on_lines_and_keeps_corners(self):
        line = [(f, 2.0 * f) for f in range(11)]
        self.assertEqual(I.thin(line), [(0, 0.0), (10, 20.0)])
        vee = [(f, abs(f - 5.0)) for f in range(11)]
        self.assertEqual([f for f, _ in I.thin(vee)], [0, 5, 10])

    def test_rig_maps_joystick_to_axis_frames(self):
        src = ET.fromstring(SOURCE).find("Artboard")
        rig = I.Rig(src.find("Joystick"), {a.get("id"): a for a in src.findall("LinearAnimation")})
        for jx, jy, scale, y in [(-1, -1, 1.0, -4.0), (1, 1, 2.0, 4.0), (0, 0, 1.5, 0.0)]:
            with self.subTest(jx=jx, jy=jy):
                s = rig.sample(jx, jy)
                self.assertAlmostEqual(s[("0:31", "scaleX")], scale)
                self.assertAlmostEqual(s[("0:31", "y")], y)


class Build(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b, cls.pieces, cls.text = build_room()
        cls.room = cls.pieces["room"]
        cls.anims = {a.get("name"): a for a in cls.pieces["animations"]}

    def names(self):
        return [e.get("name") for e in self.room.iter() if e.get("name")]

    def test_backdrop_rig_and_hidden_nodes_are_left_out(self):
        tags = {e.tag for e in self.room.iter()}
        self.assertNotIn("Joystick", tags)
        self.assertNotIn("Solo", tags)
        for gone in ("Floor 9", "Wall 9", "Hidden Bit", "Ball_B"):
            self.assertNotIn(gone, self.names())
        self.assertIn("Test Room Ball", self.names())
        self.assertIn("Ball_A", self.names())

    def test_loop_is_copied_key_for_key(self):
        loop = self.anims["Test Room Loop"]
        self.assertEqual(loop.get("duration"), "120")
        self.assertEqual(loop.get("loopValue"), "loop")
        ball = next(e for e in self.room.iter() if e.get("name") == "Test Room Ball")
        ko = next(k for k in loop.findall("KeyedObject") if k.get("objectId") == ball.get("id"))
        xs = next(kp for kp in ko.findall("KeyedProperty") if kp.get("property") == "x")
        got = [(k.get("frame", "0"), k.get("value"), k.get("interpolationType")) for k in xs]
        self.assertEqual(got, [("0", "500", "cubic"), ("60", "560", "elastic"), ("120", "500", None)])
        ease = xs[0].find("CubicEaseInterpolator")
        self.assertEqual((ease.get("x1"), ease.get("x2"), ease.get("y2")), ("0.3", "0.7", "1"))

    def test_baked_rig_reproduces_the_rig(self):
        loop = self.anims["Test Room Loop"]
        art = next(e for e in self.room.iter() if e.get("name") == "Ball_A")
        ko = next(k for k in loop.findall("KeyedObject") if k.get("objectId") == art.get("id"))
        keys = {kp.get("property"): I.read_keys(kp) for kp in ko.findall("KeyedProperty")}
        self.assertIn("scaleX", keys)                       # the joystick's x moves, so scaleX is keyed
        self.assertNotIn("y", keys)                         # its y never moves, so y is set on the art
        self.assertIsNone(art.get("y"))                     # held at 0, the default, so nothing is written
        for f, want in [(0, 1.0), (30, 1.5), (60, 2.0), (90, 1.5), (119, 1 + 1 / 60)]:
            with self.subTest(frame=f):
                self.assertAlmostEqual(I.value_at(keys["scaleX"], f), want, 6)

    def test_a_loop_that_does_not_close_is_closed_and_recorded(self):
        self.assertEqual(len(self.b.fixes), 1)
        what, was, now = self.b.fixes[0]
        self.assertIn("Piece x", what)
        self.assertEqual((was, now), (706.0, 700.0))

    def test_intro_is_3_2_s_and_ends_on_the_loop_start(self):
        intro, waiting = self.anims["Test Room Intro"], self.anims["Test Room Waiting"]
        self.assertEqual(intro.get("duration"), "192")
        first = {(ko.get("objectId"), kp.get("property")): I.read_keys(kp)[0][1]
                 for ko in intro.findall("KeyedObject") for kp in ko.findall("KeyedProperty")}
        held = {(ko.get("objectId"), kp.get("property")): I.read_keys(kp)[0][1]
                for ko in waiting.findall("KeyedObject") for kp in ko.findall("KeyedProperty")}
        self.assertEqual(first.keys(), held.keys())
        for k in first:
            self.assertAlmostEqual(first[k], held[k])
        loop = self.anims["Test Room Loop"]
        ends = {(ko.get("objectId"), kp.get("property")): I.read_keys(kp)[-1][1]
                for ko in intro.findall("KeyedObject") for kp in ko.findall("KeyedProperty")}
        for ko in loop.findall("KeyedObject"):
            for kp in ko.findall("KeyedProperty"):
                key = (ko.get("objectId"), kp.get("property"))
                if key in ends and kp.get("property") in ("x", "y", "scaleX", "scaleY"):
                    with self.subTest(key=key):
                        self.assertAlmostEqual(ends[key], I.read_keys(kp)[0][1], 4)

    def test_overhang_is_reported(self):
        self.assertTrue(any("OVERHANG" in n and "Overhang" in n for n in self.b.notes))

    def test_lockup_and_layers(self):
        self.assertIn("Test Room Lockup Gate", self.names())
        self.assertEqual(sorted(l.get("name") for l in self.pieces["layers"]),
                         ["Test Room", "Test Room Draw", "Test Room Exit", "Test Room Lockup"])
        values = {c.get("value") for l in self.pieces["layers"] for c in l.iter("TransitionValueNumberComparator")}
        self.assertIn("9", values)
        self.assertNotIn("1", values, "no layer still waits for Wordle's scene")

    def test_splice_builds_and_adds_only(self):
        out = I.splice(self.text, self.pieces)
        ET.fromstring(out)                                    # still well-formed
        old_lines, new_lines = self.text.splitlines(), out.splitlines()
        self.assertGreater(len(new_lines), len(old_lines))
        import difflib
        removed = [l for l in difflib.ndiff(old_lines, new_lines) if l.startswith("- ")]
        self.assertEqual(removed, [], "splice only adds lines")

    def test_importing_the_same_room_twice_is_refused(self):
        out = I.splice(self.text, self.pieces)
        with self.assertRaises(SystemExit):
            I.Build(CONFIG, out, ET.fromstring(SOURCE))


if __name__ == "__main__":
    unittest.main()
