"""Regenerates the whole Chapter 4 ball journey from the illustrator's file: refuses chapters/ch3/scene.rml once it has changed since commit d65c7ea (tools/regen_guard.py).

Chapter 4 (scene chapter-4): the illustrator's ball journey brought in as they made it, with our standard ball (Demetre, 2026-11-03).

    python3 chapters/ch3/scripts/ch3_c4s1_import.py --write      once, on the scene as committed in d65c7ea

Their file (Rive file 2668591, read only; the copy in .cache/illustrator/), artboard NYT_YIG_c4s1_Wordle (the room's own source; the
other four c4s1 artboards have their own variants of it), animation "Ball" (420 frames), goes into the room's Loop key for key: the
same frames, values and easing, on the same pieces (the stack's reactions and its front and back copies). The ball is our standard ball
(Chapter 1 card 3's art and dot) on their ball's path, at their sizes (their Ball_Scale_c4: 0.7 to 5.19 times) and squash (their
Ball_Squash, as the same flattening on Ball_01's scale about the contact point), at their depth (between SpB_02_F and Crossword_B);
its dot turns one turn per circumference of travel at the size of the moment. The room's Floor Clip stands in for their front floor,
which hid the ball below the floor line. The Loop is their 420 frames from the end of the intro, and the intro holds their first frame.
The fireworks are untouched.
"""
import copy
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
from import_room import ILLUSTRATOR, Rig, read_keys, value_at
from rml_edit import Doc, bake, num
import regen_guard
WRITTEN_AGAINST = "d65c7ea"     # the scene this was run on, once (see above)
from rml_read import Scene, chapter_dir
from rooms_sheet import Sheet

SCENE = chapter_dir("ch3") / "scene.rml"
ROOM = "Chapter 4"
INTRO = 192
R = 17.678
SQUASH = (1.131, 0.854)                 # their full squash, width and height, about the contact point (as in c3s1)
STAND_IN = "9:13991"
BEFORE = "Crossword_B"                  # their ball is drawn just above it


def element_lines(e, level, ids):
    attrs = dict(e.attrib)
    if "id" in attrs:
        attrs["id"] = ids()
    a = "".join(f' {k}="{v}"' for k, v in attrs.items())
    kids = list(e)
    if not kids:
        return [f"{' ' * level}<{e.tag}{a}/>"]
    out = [f"{' ' * level}<{e.tag}{a}>"]
    for c in kids:
        out += element_lines(c, level + 4, ids)
    return out + [f"{' ' * level}</{e.tag}>"]


def find_ours(src_parent, src_el, ours_root, top_names):
    """Our element for one of theirs: walk down from the same-named top piece, matching each step by tag, name and position."""
    chain = []
    e = src_el
    while e is not None and e not in top_names:
        chain.append(e)
        e = src_parent.get(e)
    top = e
    o = next(c for c in ours_root if c.get("name") == top.get("name"))
    key = lambda c: (c.tag, c.get("name"), round(float(c.get("x", 0)), 2), round(float(c.get("y", 0)), 2))
    for s in reversed(chain):
        hits = [c for c in o if key(c) == key(s)]
        assert len(hits) == 1, (top.get("name"), key(s), len(hits))
        o = hits[0]
    return o


def main():
    root = ET.parse(ILLUSTRATOR).getroot()
    ab = next(a for a in root.iter("Artboard") if a.get("name") == "NYT_YIG_c4s1_Wordle")
    src_parent = {c: p for p in ab.iter() for c in p}
    anims = {a.get("id"): a for a in ab.iter("LinearAnimation")}
    ball = next(a for a in anims.values() if a.get("name") == "Ball")
    by_id = {e.get("id"): e for e in ab.iter() if e.get("id")}
    joystick = next(ab.iter("Joystick"))
    solo = next(e for e in ab.iter("Solo") if e.get("name") == "Ball_Move")
    b01_src = by_id[solo.get("activeComponentId")]
    rig = Rig(joystick, anims)
    n = int(ball.get("duration"))
    sc = Scene(SCENE)
    room = next(e for e in sc.root.iter("Node") if e.get("name") == f"{ROOM} Room")
    plane = next(c for c in room if c.get("name") == f"{ROOM} Floor Plane")
    floor_clip = next(e for e in room if e.get("name") == f"{ROOM} Floor Clip").get("id")
    tops = set(ab)
    loop, intro = f"{ROOM} Loop", f"{ROOM} Intro"
    poses = (intro, f"{ROOM} Waiting", f"{ROOM} Built", loop)

    doc = Doc(SCENE)
    # ---- the stand-in goes; the standard ball comes in at their depth
    for an in poses:
        doc.drop_object(an, STAND_IN)
    i = doc.idx(STAND_IN)
    del doc.lines[i:doc.end(i) + 1]
    nid = doc.new_id
    ballid, b01, b01s, spin, spinart, hl, base = (nid() for _ in range(7))
    t = doc.idx(next(c for c in plane if c.get("name") == BEFORE).get("id"))
    p = " " * (len(doc.lines[t]) - len(doc.lines[t].lstrip()))
    clip = lambda: f'<ClippingShape sourceId="{floor_clip}" name="Floor Clip" id="{nid()}"/>'
    art = [f'{p}<Node x="{solo.get("x")}" y="{solo.get("y")}" name="{ROOM} Ball" id="{ballid}">',
           f'{p}    <Node y="{b01_src.get("y", "0")}" name="Ball_01" id="{b01}">',
           f'{p}        <Node x="-0.072021484" y="0.096008301" name="Ball_01_Scale" id="{b01s}">',
           f'{p}            <Node y="-17.572" name="{ROOM} Ball Spin" id="{spin}">',
           f'{p}                <Node y="17.572" name="{ROOM} Ball Spin Art" id="{spinart}">',
           f'{p}                    <Shape x="6.3640137" y="-23.834076" rotation="-0.77726489" name="Ball_01_Highlight" id="{hl}">',
           f'{p}                        <Ellipse width="7.5" height="9.6440001" x="-1.0000001" scaleY="1.174" scaleX="1.174" id="{nid()}"/>',
           f'{p}                        <Fill id="{nid()}">', f'{p}                            <SolidColor colorValue="FFFFFFFF" id="{nid()}"/>', f'{p}                        </Fill>',
           f'{p}                        <Stroke thickness="1.5" cap="round" join="round" transformAffectsStroke="false" id="{nid()}">',
           f'{p}                            <SolidColor colorValue="FF1F1F1F" id="{nid()}"/>', f'{p}                        </Stroke>',
           f'{p}                        {clip()}', f'{p}                    </Shape>',
           f'{p}                    <Shape y="-17.571991" name="Ball_01_Base" id="{base}">',
           f'{p}                        <PointsPath isClosed="true" name="Path" id="{nid()}">',
           f'{p}                            <CubicDetachedVertex inRotation="3.1415927" inDistance="9.7632895" outDistance="9.7632895" y="-17.677999" id="{nid()}"/>',
           f'{p}                            <CubicDetachedVertex inRotation="-1.5707964" inDistance="9.7632895" outRotation="1.5707964" outDistance="9.7632895" x="17.677999" id="{nid()}"/>',
           f'{p}                            <CubicDetachedVertex inDistance="9.7632895" outRotation="3.1415927" outDistance="9.7632895" y="17.677999" id="{nid()}"/>',
           f'{p}                            <CubicDetachedVertex inRotation="1.5707964" inDistance="9.7632895" outRotation="-1.5707964" outDistance="9.7632895" x="-17.677999" id="{nid()}"/>',
           f'{p}                        </PointsPath>',
           f'{p}                        <Fill id="{nid()}">', f'{p}                            <SolidColor colorValue="FFFF5959" id="{nid()}"/>', f'{p}                        </Fill>',
           f'{p}                        <Stroke thickness="1.5" cap="round" join="round" transformAffectsStroke="false" id="{nid()}">',
           f'{p}                            <SolidColor colorValue="FF1F1F1F" id="{nid()}"/>', f'{p}                        </Stroke>',
           f'{p}                        {clip()}', f'{p}                    </Shape>',
           f'{p}                </Node>', f'{p}            </Node>', f'{p}        </Node>', f'{p}    </Node>', f'{p}</Node>']
    doc.lines[t:t] = art

    # ---- the Loop: their keys, key for key (the ball's path on our ball's node), their length
    doc.clear(loop)
    doc.set_duration(loop, n)
    a, b = doc.anim(loop)
    new, mapped = [], []
    for ko in ball.findall("KeyedObject"):
        oid = ko.get("objectId")
        if oid == joystick.get("id"):
            continue
        ours = ballid if oid == solo.get("id") else find_ours(src_parent, by_id[oid], plane, tops).get("id")
        mapped.append((by_id[oid].get("name"), ours))
        ko2 = copy.deepcopy(ko)
        ko2.set("objectId", ours)
        new += element_lines(ko2, 12, nid)
    doc.lines[b:b] = new
    regen_guard.save(doc, WRITTEN_AGAINST, __file__)

    # ---- the rig (size and squash) and the dot's turn, on every frame
    jk = {kp.get("property"): read_keys(kp) for ko in ball.findall("KeyedObject") if ko.get("objectId") == joystick.get("id") for kp in ko.findall("KeyedProperty")}
    jx = lambda f: value_at(jk["x"], f) if "x" in jk else float(joystick.get("x", 0))
    jy = lambda f: value_at(jk["y"], f) if "y" in jk else float(joystick.get("y", 0))
    size = {f: rig.sample(jx(f), jy(f))[(b01_src.get("id"), "scaleX")] for f in range(n + 1)}
    sq = {f: (jx(f) + 1) / 2 for f in range(n + 1)}
    sc2 = Scene(SCENE)
    lk = Sheet(sc2).anim_keys(sc2.animations[loop])
    bx = {f: lk[ballid]["x"].at(f) for f in range(n + 1)}
    th = {0: 0.0}
    for f in range(n):
        dx = bx[f + 1] - bx[f]
        th[f + 1] = th[f] + dx / (R * size[f])
    doc = Doc(SCENE)
    doc.set_prop(loop, b01, "scaleX", bake({f: size[f] * (1 + (SQUASH[0] - 1) * sq[f]) for f in range(n + 1)}, range(n + 1)))
    doc.set_prop(loop, b01, "scaleY", bake({f: size[f] * (1 + (SQUASH[1] - 1) * sq[f]) for f in range(n + 1)}, range(n + 1)))
    doc.set_prop(loop, spin, "rotation", bake(th, range(n + 1)))
    regen_guard.save(doc, WRITTEN_AGAINST, __file__)

    # ---- the join: the intro (and so Waiting and Built) holds every Loop property at the Loop's first frame
    sc3 = Scene(SCENE)
    sh3 = Sheet(sc3)
    lk, ik = sh3.anim_keys(sc3.animations[loop]), sh3.anim_keys(sc3.animations[intro])
    doc = Doc(SCENE)
    for oid, props in lk.items():
        for prop, k in props.items():
            if prop in ik.get(oid, {}):
                continue
            v = k.at(0)
            doc.set_prop(intro, oid, prop, [(0, v, "hold"), (INTRO - 1, v, "hold")])
            doc.set_prop(f"{ROOM} Waiting", oid, prop, [(0, v, "hold")])
            doc.set_prop(f"{ROOM} Built", oid, prop, [(0, v, "hold")])
    regen_guard.save(doc, WRITTEN_AGAINST, __file__)
    turns = th[n] / (2 * math.pi)
    print(f"wrote {SCENE}: {ROOM} Loop is their Ball ({n} frames) on: " + ", ".join(f"{a} -> {b}" for a, b in mapped)
          + f"; the dot turns {turns:.2f} times a loop")


if __name__ == "__main__":
    if "--write" not in sys.argv:
        raise SystemExit(__doc__)
    main()
