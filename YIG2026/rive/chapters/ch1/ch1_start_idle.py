"""Regenerates the whole Start room's loop: refuses chapters/ch1/scene.rml once it has changed since commit 7e137b4 (tools/regen_guard.py).

One time (2026-11-04): Start's bouncing-ball-and-bird loop replaced by Chapter 3 card 2's ball, bird and idle loop.

    python3 chapters/ch1/ch1_start_idle.py            dry run: what it would copy
    python3 chapters/ch1/ch1_start_idle.py --write    rewrite chapters/ch1/scene.rml

Chapter 3's file is only read (chapters/ch3/scene.rml, room "Bird on Ball", scene chapter-3-bird); nothing is written there and File 1 keeps no
reference to it. What is copied, key for key:
  * the idle loop's ball sway (Ball x, 301 keys) and the ball's roll (its Spin rotation, 239 keys): the ball sways 5 units each way along the
    floor line and its dot rolls with it, 300 frames (5 s), first and last frame the same;
  * the bird's counter-tilt about its feet (Bird rotation, 127 keys);
  * the bird's blink (its Small Loop, 300 frames), written onto Start's bird, which is the same drawing (checked: the shapes match).
Start's ball is already Chapter 3's ball (35.36 across at scale 2, 1.5 across with its stroke, the floor line at 712, x 748), and its bird already
rests at the same place on it (feet at y 641.29), so nothing is rescaled or moved. The one thing added is the bird's pivot: a "Start Bird Tilt"
node at the ball's top (the pattern CLAUDE.md asks for: its own position on the pivot, an inner Art group offset back) so the bird turns
about its feet; the ball's art turns about its own centre (Start Ball Art's origin) and needs no pivot.
Start's intro (the ball finishing its bounce, the bird dropping on it) and its exit (the whole room pans left) are untouched. The loading
scene's bounce is untouched.
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

RIVE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RIVE_ROOT / "tools"))
from rml_edit import Doc, num                                    # noqa: E402
import regen_guard                                               # noqa: E402
WRITTEN_AGAINST = "7e137b4"     # the file before this script's commit (125b175)

SCENE = RIVE_ROOT / "chapters" / "ch1" / "scene.rml"
CH3 = RIVE_ROOT / "chapters" / "ch3" / "scene.rml"               # read only
BALL, BALL_ART, BIRD, CARRIER = "9:13166", "9:13067", "9:13163", "9:13164"
START_BIRD_SHAPE = "9:13080"                                     # "Bird": the drawing the blink moves
CH3_BIRD_SHAPE, CH3_LOOP, CH3_SMALL = "9:32384", "Bird on Ball Loop", "Bird on Ball Small Loop"
CH3_BALL, CH3_SPIN, CH3_BIRD = "9:44918", "9:44921", "9:44925"
BALL_TOP = 712.0 - 70.712                                        # 641.288: where the bird's feet are, as in Chapter 3
PIVOT = (0.0, round(BALL_TOP - 712.0 + 17.68, 3))                # in the carrier's frame (the carrier sits 17.68 above the ball's origin)
LOOP = 300
INTRO = 192
ROOM = "Start"


def keys_of(root, anim, oid, prop):
    an = next(a for a in root.iter("LinearAnimation") if a.get("name") == anim)
    ko = next(k for k in an.findall("KeyedObject") if k.get("objectId") == oid)
    kp = next(p for p in ko.findall("KeyedProperty") if p.get("property") == prop)
    return [(int(k.get("frame", 0)), float(k.get("value", 0)), k.get("interpolationType")) for k in kp]


def ser(e, ind):
    pad = " " * ind
    attrs = "".join(f' {k}="{v}"' for k, v in e.attrib.items())
    kids = list(e)
    if not kids:
        return [f"{pad}<{e.tag}{attrs}/>"]
    out = [f"{pad}<{e.tag}{attrs}>"]
    for c in kids:
        out += ser(c, ind + 4)
    return out + [f"{pad}</{e.tag}>"]


def verts(root, oid):
    node = next(e for e in root.iter() if e.get("id") == oid)
    return [v.get("id") for v in node.iter() if v.tag == "CubicDetachedVertex"]


def main(argv):
    write = "--write" in argv
    doc = Doc(SCENE)
    if any('name="Start Bird Tilt"' in l for l in doc.lines):
        raise SystemExit("already applied (Start Bird Tilt exists)")
    ch3 = ET.parse(CH3).getroot()
    scene = ET.fromstring("\n".join(doc.lines))

    sway = keys_of(ch3, CH3_LOOP, CH3_BALL, "x")
    roll = keys_of(ch3, CH3_LOOP, CH3_SPIN, "rotation")
    tilt = keys_of(ch3, CH3_LOOP, CH3_BIRD, "rotation")
    assert sway[0][1] == sway[-1][1] == 748.0 and roll[0][1] == roll[-1][1] == 0 and tilt[0][1] == tilt[-1][1] == 0, "the idle loop must close"
    assert sway[-1][0] == roll[-1][0] == tilt[-1][0] == LOOP
    assert all(how == "linear" for _, _, how in sway + roll + tilt)
    print(f"ch3 idle loop: ball x {len(sway)} keys ({min(v for _, v, _ in sway):.1f} to {max(v for _, v, _ in sway):.1f}), roll {len(roll)} keys "
          f"(+-{max(abs(v) for _, v, _ in roll):.4f} rad), bird tilt {len(tilt)} keys (+-{max(abs(v) for _, v, _ in tilt):.4f} rad), {LOOP} frames")

    # the blink: Chapter 3's vertices -> Start's, by their place in the (identical) drawing
    cv, sv = verts(ch3, CH3_BIRD_SHAPE), verts(scene, START_BIRD_SHAPE)
    assert len(cv) == len(sv) == 19
    vmap = dict(zip(cv, sv))
    small = next(a for a in ch3.iter("LinearAnimation") if a.get("name") == CH3_SMALL)
    assert small.get("duration") == str(LOOP)
    print(f"ch3 blink: {len(small.findall('KeyedObject'))} vertices keyed, written onto Start's bird")
    if not write:
        return 0

    # ---- the bird's pivot at the ball's top ----
    pid, aid = doc.wrap(BIRD, "Start Bird Tilt", *PIVOT)

    # ---- Start Loop: the idle loop, 300 frames ----
    a, _ = doc.anim("Start Loop")
    doc.clear("Start Loop")
    doc.set_duration("Start Loop", LOOP)
    lin = lambda ks: [(f, v, "linear") for f, v, _ in ks]
    doc.set_prop("Start Loop", BALL, "x", lin(sway))
    doc.set_prop("Start Loop", BALL_ART, "rotation", lin(roll))
    doc.set_prop("Start Loop", pid, "rotation", lin(tilt))

    # the intro, Waiting and Built also set what the loop keys (the rule checks require it): rest, no turn, no tilt
    for obj in (BALL_ART, pid):
        doc.set_prop("Start Intro", obj, "rotation", [(0, 0, "linear"), (INTRO, 0, "linear")])
        doc.set_prop("Start Waiting", obj, "rotation", [(0, 0, "hold")])
        doc.set_prop("Start Built", obj, "rotation", [(0, 0, "hold")])

    # ---- Start Small Loop: Chapter 3's blink, 300 frames ----
    doc.clear("Start Small Loop")
    doc.set_duration("Start Small Loop", LOOP)
    i, j = doc.anim("Start Small Loop")
    out = []
    for ko in small.findall("KeyedObject"):
        new = ET.fromstring(ET.tostring(ko))
        for e in new.iter():
            if e.get("id"):
                e.set("id", doc.new_id())
        new.set("objectId", vmap[ko.get("objectId")])
        out += ser(new, 12)
    doc.lines[j:j] = out
    regen_guard.save(doc, WRITTEN_AGAINST, __file__)
    print(f"wrote {SCENE}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
