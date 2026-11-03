"""Chapter 3 card 1 (scene chapter-3): the illustrator's c3s1 animation brought in as they made it (Demetre, 2026-11-03).

    python3 chapters/ch3/scripts/ch3_c3s1_import.py --write

Reads their file (Rive file 2668591, read only; the copy in .cache/illustrator/), artboard NYT_YIG_c3s1, animation "Ball" (420
frames), and writes it into the room's Loop key for key: the same frames, values and easing (cubic, value-eased and elastic keys
included), on the same pieces. Their ball comes in as their art (Ball_Move, Ball_01 and its parts; the Solo becomes a node and its
hidden Ball_02 is left out). Their joystick rig comes in as what it does to the ball, sampled on every frame from their own keys and
rig animations (Ball_Scale: the ball's size, 0.7 to 2 times; Ball_Squash: its squash), the way every other room's rig came in.
Their "Loop" animation (the bird's blink) is already the room's Small Loop.

Only what is needed to play it in this room is changed: the ball sits in the room's floor plane where their artboard drew it (behind
the picture's front frame and hill, in front of the disco ball), with the room's Floor Clip standing in for their front floor; during
the intro it holds their first frame, riding the picture's drop; the Loop is their 420 frames, starting when the intro ends.
Not applied, because the disco ball is kept as it is: their keys on the disco ball's hanging group, its ball, its Line and Burst_01.

Run it on the room as it was before the rebuilt journey (.cache/scratch.nosync/ch3/ch3-scene-before-c3s1.rml) with the saved disco ball
put back (chapters/ch3/scripts/ch3_disco.py restore). It is not safe to run twice.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
import copy
import re
import sys
import xml.etree.ElementTree as ET

from import_room import ILLUSTRATOR, Rig, read_keys, value_at
from rml_edit import Doc, bake, num
from rml_read import Scene, chapter_dir

SCENE = chapter_dir("ch3") / "scene.rml"
ROOM = "Chapter 3"
INTRO = 192
PIC_PIVOT = (606.25, 581.25)
PICTURE_6 = "9:879"
DISCO_WRAP = "9:689"
STAND_IN = "9:2100"
FLOOR_CLIP = "9:3108"
SKIPPED = {"1:22094": "the disco ball's hanging group (rotation, a swing)", "1:22100": "the disco ball (y, a bob)",
           "1:22907": "the disco ball's Line (a vertex: bends)", "1:22901": "the disco ball's Line (a vertex: moves)",
           "1:22073": "Burst_01 (its path's scale: the burst)"}
OURS = {"1:20728": "9:691", "1:19341": "9:741", "1:21295": "9:1386", "1:21270": "9:1422", "1:21913": "9:1144",
        "1:23095": "9:1321", "1:98237": "9:1328"}
BARS = ("Bar_01", "Bar_02", "Bar_03")


def source():
    root = ET.parse(ILLUSTRATOR).getroot()
    ab = next(a for a in root.iter("Artboard") if a.get("name") == "NYT_YIG_c3s1")
    anims = {a.get("id"): a for a in ab.iter("LinearAnimation")}
    ball = next(a for a in anims.values() if a.get("name") == "Ball")
    return ab, anims, ball


def element_lines(e, level, ids, idmap):
    """RML lines for a copy of element e with fresh ids (idmap: old id -> new id), indented `level` spaces."""
    attrs = dict(e.attrib)
    if "id" in attrs:
        idmap[attrs["id"]] = attrs["id"] = ids()
    a = "".join(f' {k}="{v}"' for k, v in attrs.items())
    kids = list(e)
    if not kids:
        return [f"{' ' * level}<{e.tag}{a}/>"]
    out = [f"{' ' * level}<{e.tag}{a}>"]
    for c in kids:
        out += element_lines(c, level + 4, ids, idmap)
    return out + [f"{' ' * level}</{e.tag}>"]


def main():
    ab, anims, ball = source()
    by_id = {e.get("id"): e for e in ab.iter() if e.get("id")}
    solo = by_id["1:17655"]
    joystick = next(ab.iter("Joystick"))
    rig = Rig(joystick, anims)
    sc = Scene(SCENE)
    doc = Doc(SCENE)
    names = {e.get("id"): e.get("name") for e in sc.root.iter() if e.get("id")}
    for theirs, ours in OURS.items():
        assert by_id[theirs].get("name") == names[ours], (theirs, by_id[theirs].get("name"), ours, names[ours])
    mobile = next(e for e in sc.root.iter() if e.get("id") == OURS["1:21913"])
    for b in BARS:
        theirs = next(c for c in by_id["1:21913"] if c.get("name") == b)
        OURS[theirs.get("id")] = next(c for c in mobile if c.get("name") == b).get("id")

    # ---- the stand-in ball goes: its node and its keys
    for an in (f"{ROOM} Intro", f"{ROOM} Waiting", f"{ROOM} Built", f"{ROOM} Loop"):
        doc.drop_object(an, STAND_IN)
    i = doc.idx(STAND_IN)
    del doc.lines[i:doc.end(i) + 1]

    # ---- their ball: Ball_Move (a node now) with Ball_01; the rig's first frame set on the art
    jkeys = {kp.get("property"): read_keys(kp) for ko in ball.findall("KeyedObject") if ko.get("objectId") == joystick.get("id")
             for kp in ko.findall("KeyedProperty")}
    jx = lambda f: value_at(jkeys["x"], f) if "x" in jkeys else float(joystick.get("x", 0))
    jy = lambda f: value_at(jkeys["y"], f) if "y" in jkeys else float(joystick.get("y", 0))
    pose0 = rig.sample(jx(0), jy(0))
    node = ET.Element("Node", {"x": solo.get("x"), "y": solo.get("y"), "name": "Ball_Move", "id": solo.get("id")})
    b01 = copy.deepcopy(by_id[solo.get("activeComponentId")])
    for e in b01.iter():
        for (oid, prop), v in pose0.items():
            if e.get("id") == oid:
                e.set(prop, num(v))
    node.append(b01)
    # the room's Floor Clip on the ball's shapes, standing in for their front floor (it hid the ball below y 711)
    for sh in b01.iter("Shape"):
        ET.SubElement(sh, "ClippingShape", {"sourceId": FLOOR_CLIP, "name": "Floor Clip", "id": "x"})
    idmap = {}
    t = doc.idx(DISCO_WRAP)
    level = len(doc.lines[t]) - len(doc.lines[t].lstrip())
    doc.lines[t:t] = element_lines(node, level, doc.new_id, idmap)
    for theirs in list(idmap):
        OURS.setdefault(theirs, idmap[theirs])

    # ---- the Loop: their 420 frames, key for key; the rig sampled on every frame
    loop = f"{ROOM} Loop"
    doc.set_duration(loop, int(ball.get("duration")))
    n = int(ball.get("duration"))
    a, b = doc.anim(loop)
    new, skipped = [], []
    for ko in ball.findall("KeyedObject"):
        oid = ko.get("objectId")
        if oid in SKIPPED:
            skipped.append(oid)
            continue
        if oid == joystick.get("id"):
            continue
        ko2 = copy.deepcopy(ko)
        ko2.set("objectId", OURS[oid])
        new += element_lines(ko2, 12, doc.new_id, {})
    doc.lines[b:b] = new
    for (oid, prop) in rig.targets:
        vals = {f: rig.sample(jx(f), jy(f))[(oid, prop)] for f in range(n + 1)}
        if max(vals.values()) - min(vals.values()) < 1e-6:
            continue
        doc.set_prop(loop, OURS[oid], prop, bake(vals, range(n + 1)))

    # ---- the intro holds their first frame, riding the picture's drop and squash; the poses follow the intro
    from rooms_sheet import Sheet
    k6 = Sheet(sc).anim_keys(sc.animations[f"{ROOM} Intro"])[PICTURE_6]
    bm = {kp.get("property"): read_keys(kp) for ko in ball.findall("KeyedObject") if ko.get("objectId") == "1:17655" for kp in ko.findall("KeyedProperty")}
    x0, y0 = value_at(bm["x"], 0), value_at(bm["y"], 0)
    s0 = pose0[("1:17674", "scaleX")]
    xs, ys, sxs, sys_ = {}, {}, {}, {}
    for f in range(INTRO):
        dy, sx, sy = k6["y"].at(f) - PIC_PIVOT[1], k6["scaleX"].at(f), k6["scaleY"].at(f)
        xs[f] = PIC_PIVOT[0] + (x0 - PIC_PIVOT[0]) * sx
        ys[f] = PIC_PIVOT[1] + (y0 - PIC_PIVOT[1]) * sy + dy
        sxs[f], sys_[f] = s0 * sx, s0 * sy
    intro = f"{ROOM} Intro"
    for oid, prop, vals in ((OURS["1:17655"], "x", xs), (OURS["1:17655"], "y", ys), (OURS["1:17674"], "scaleX", sxs), (OURS["1:17674"], "scaleY", sys_)):
        k = bake(vals, range(INTRO))
        doc.set_prop(intro, oid, prop, k)
        doc.set_prop(f"{ROOM} Waiting", oid, prop, [(0, k[0][1], "hold")])
        doc.set_prop(f"{ROOM} Built", oid, prop, [(0, k[-1][1], "hold")])
    doc.save()
    # the join: every property the Loop keys is held by the Intro at the Loop's first frame (and so by Waiting and Built), so the
    # room arrives on their frame 0 and comes back to it
    sc2 = Scene(SCENE)
    sh2 = Sheet(sc2)
    lk, ik = sh2.anim_keys(sc2.animations[loop]), sh2.anim_keys(sc2.animations[intro])
    disco = set(re.findall(r'\bid="([^"]+)"', "\n".join(doc.lines[doc.idx(DISCO_WRAP):doc.end(doc.idx(DISCO_WRAP)) + 1])))
    doc = Doc(SCENE)
    joined = 0
    for oid, props in lk.items():
        if oid in disco:
            continue
        for prop, k in props.items():
            if prop in ik.get(oid, {}):
                continue
            v = k.at(0)
            doc.set_prop(intro, oid, prop, [(0, v, "hold"), (INTRO - 1, v, "hold")])
            doc.set_prop(f"{ROOM} Waiting", oid, prop, [(0, v, "hold")])
            doc.set_prop(f"{ROOM} Built", oid, prop, [(0, v, "hold")])
            joined += 1
    doc.save()
    print(f"joined {joined} properties to the intro (held at the Loop's first frame)")
    print(f"wrote {SCENE}: their Ball animation ({n} frames) into {loop}; not applied (the disco ball): "
          + "; ".join(SKIPPED[o] for o in skipped))


if __name__ == "__main__":
    if "--write" not in sys.argv:
        raise SystemExit(__doc__)
    main()
