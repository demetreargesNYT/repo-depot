"""Tests for what bringing rooms into a brand-new file needs: the scaffold, a fixed backdrop, a room with no intro,
work-area and tiled loops, and the exact ping-pong reversal. Run: python3 -m unittest discover -s tools/tests"""
import copy
import json
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import import_room as I
import scaffold_chapter as S
from rml_read import REPO

MANIFEST = json.loads((REPO / "chapters" / "ch1" / "chapter.json").read_text())
PLACEHOLDER = REPO / "tools" / "placeholders" / "loading.rml"


def key(frame, value, how=None, ease=None):
    k = ET.Element("KeyFrameDouble", {"frame": str(frame), "value": str(value)})
    if how:
        k.set("interpolationType", how)
    if ease:
        ET.SubElement(k, "CubicEaseInterpolator", {"x1": str(ease[0]), "y1": str(ease[1]), "x2": str(ease[2]), "y2": str(ease[3]), "id": "9:1"})
    return k


class PingPong(unittest.TestCase):
    def test_a_reversed_ease_reversed_again_is_the_original(self):
        c = ET.Element("c", {"x1": "0.66", "y1": "0", "x2": "0.4", "y2": "1"})
        r = I.reversed_ease(c)
        back = I.reversed_ease(ET.Element("c", {k: str(v) for k, v in zip(("x1", "y1", "x2", "y2"), r)}))
        self.assertEqual([round(v, 9) for v in back], [0.66, 0.0, 0.4, 1.0])

    def test_there_and_back_keeps_the_values_and_reverses_the_curve(self):
        a = key(9, 0.25, "cubic", (0.66, 0, 0.4, 1))
        b = key(69, -0.25, "cubic", (0.667, 0, 0.58, 1))           # leaves for a frame past the window, which is cut off
        out = I.pingpong_keys([a, b], 9, 69)
        self.assertEqual([f for f, _ in out], [0, 60, 120])
        self.assertEqual([k.get("value") for _, k in out], ["0.25", "-0.25", "0.25"])
        # the key at the far end now leaves by the reverse of the segment that arrived there
        c = out[1][1].find("CubicEaseInterpolator")
        self.assertEqual([round(float(c.get(n)), 6) for n in ("x1", "y1", "x2", "y2")], [0.6, 0.0, 0.34, 1.0])
        # the way out is the original first key, untouched
        self.assertEqual(out[0][1].find("CubicEaseInterpolator").get("x1"), "0.66")

    def test_only_number_keys_can_be_reversed(self):
        with self.assertRaises(SystemExit):
            I.pingpong_keys([ET.Element("KeyFrameColor", {"frame": "0"})], 0, 10)


def placeholder_build(extra=None):
    """The Loading placeholder brought into a scaffolded File 1 (nothing is written to disk)."""
    text = S.scene_text(MANIFEST)
    cfg = json.loads((REPO / "tools" / "rooms" / "ch1-loading.json").read_text())
    cfg.update(extra or {})
    b = I.Build(cfg, text, ET.parse(PLACEHOLDER).getroot())
    return text, b, b.build()


class NewFile(unittest.TestCase):
    def test_the_scaffold_is_the_shared_picture(self):
        root = ET.fromstring(S.scene_text(MANIFEST))
        ab = root.find("Artboard")
        self.assertEqual((ab.get("width"), ab.get("height"), ab.get("name")), ("1495", "1067", "Start and Chapter 1"))
        self.assertEqual(ab.find("StateMachine").get("name"), "Backdrop")
        self.assertEqual(root.find("ViewModel").get("name"), "Backdrop")
        colours = {sh.get("name"): sh.find("Fill/SolidColor").get("colorValue") for sh in ab.iter("Shape") if sh.find("Fill") is not None and sh.get("name") in ("Wall", "Floor")}
        self.assertEqual(colours, {"Wall": "FFF1ECC0", "Floor": "FFFF811E"})
        self.assertEqual([e.get("name") for e in root.findall("DataEnumCustom")], ["Scene", "Direction"])

    def test_the_first_scene_in_the_manifest_is_the_default(self):
        root = ET.fromstring(S.scene_text(MANIFEST))
        enum = next(e for e in root.findall("DataEnumCustom") if e.get("name") == "Scene")
        default = root.find("ViewModel/ViewModelInstance/ViewModelInstanceEnum").get("propertyValue")
        self.assertEqual(next(v.get("key") for v in enum if v.get("id") == default), "loading")

    def test_a_room_with_no_intro_and_a_fixed_backdrop(self):
        text, b, pieces = placeholder_build()
        names = {a.get("name") for a in pieces["animations"]}
        self.assertNotIn("Loading Intro", names)
        self.assertNotIn("Loading Waiting", names)
        self.assertFalse(any(n.endswith(" Colors") for n in names), "a fixed backdrop has no colour poses")
        self.assertIsNone(pieces["backdrop_transition"])
        self.assertEqual(sorted(l.get("name") for l in pieces["layers"]), ["Loading", "Loading Draw", "Loading Exit"], "no lockup layer without a lockup")

    def test_the_room_the_file_opens_on_starts_in_its_loop(self):
        _, b, pieces = placeholder_build()
        layer = next(l for l in pieces["layers"] if l.get("name") == "Loading")
        loop_id = next(a.get("id") for a in pieces["animations"] if a.get("name") == "Loading Loop")
        states = layer.findall("AnimationState")
        self.assertEqual([s.get("animationId") for s in states], [loop_id], "Waiting and Intro are gone")
        self.assertEqual(layer.find("EntryState/StateTransition").get("stateToId"), states[0].get("id"))

    def test_the_layers_wait_for_the_manifests_scene_and_nothing_else(self):
        _, b, pieces = placeholder_build()
        enum = next(e for e in ET.fromstring(S.scene_text(MANIFEST)).findall("DataEnumCustom") if e.get("name") == "Scene")
        loading = next(v.get("id") for v in enum if v.get("key") == "loading")
        values = {c.get("value") for l in pieces["layers"] for c in l.iter("TransitionValueEnumComparator")}
        self.assertIn(loading, values)

    def test_splice_into_a_file_with_no_rooms_is_well_formed(self):
        text, b, pieces = placeholder_build()
        out = I.splice(text, pieces)
        root = ET.fromstring(out)
        self.assertIsNotNone(root.find(".//Node[@name='Loading Room']"))
        self.assertEqual(len(root.findall(".//StateMachineLayer")), 3)


class Loops(unittest.TestCase):
    def test_a_loop_tiled_to_twice_its_length(self):
        _, b, pieces = placeholder_build({"loops": [{"anim": "Loop", "from": 0, "to": 60}], "loop_frames": 120})
        loop = next(a for a in pieces["animations"] if a.get("name") == "Loading Loop")
        self.assertEqual(loop.get("duration"), "120")
        ys = next(kp for kp in loop.iter("KeyedProperty") if kp.get("property") == "y")
        frames = [int(k.get("frame", 0)) for k in ys]
        self.assertEqual(frames, [0, 18, 36, 60, 78, 96, 120])        # the second tile's keys follow the first; frame 60 is shared
        self.assertEqual(ys[0].get("value"), ys[-1].get("value"), "the loop still closes")

    def test_a_loop_that_does_not_divide_the_length_is_refused(self):
        with self.assertRaises(SystemExit):
            placeholder_build({"loops": [{"anim": "Loop", "from": 0, "to": 60}], "loop_frames": 90})

    def test_two_animations_keying_one_property_are_refused(self):
        with self.assertRaises(SystemExit):
            placeholder_build({"loops": [{"anim": "Loop", "from": 0, "to": 60}, {"anim": "Loop", "from": 0, "to": 60}], "loop_frames": 60})

    def test_a_work_area_the_source_enables_is_its_length(self):
        text = S.scene_text(MANIFEST)
        src = ET.parse(PLACEHOLDER).getroot()
        loop = next(a for a in src.iter("LinearAnimation") if a.get("name") == "Loop")
        loop.set("enableWorkArea", "true")
        loop.set("workStart", "0")
        loop.set("workEnd", "48")
        cfg = json.loads((REPO / "tools" / "rooms" / "ch1-loading.json").read_text())
        b = I.Build(cfg, text, src)
        sources, total = b.loop_sources()
        self.assertEqual(total, 48)
        self.assertFalse(sources[0]["legacy"])


if __name__ == "__main__":
    unittest.main()
