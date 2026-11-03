"""Chapter 3 card 1: Demetre's decisions on the c3s1 conflicts (2026-11-03), applied to the faithful import (ch3_c3s1_import.py).

    python3 chapters/ch3/scripts/ch3_c3s1_decisions.py --write      on the scene as committed in a757356; not safe to run twice

1. c3s1 starts at 1.95 s (intro frame 117), behind the hill; the intro plays its first 75 frames and the Loop picks up there.
4. The ring box lid falls shut and the ring lowers while the ball rests hidden in the box; the mobile's last key matches its first.
5. Every property ends where it starts: the front copies switch back while the ball is in the box (the ball's own jump back to the
   picture happens there too, hidden at both ends), so the Loop's first and last frames are the same.
6. The bird's blink loop is as long as the Loop (416 frames, after 12).
8. The rig's squash rises take 6 frames (they took 2), each still peaking on its contact.
9. The ball is the standard ball (Chapter 1 card 3's art and dot), with c3s1's motion, sizes and depth; the dot turns one turn per
   circumference of travel at the ball's size of the moment; the leftover to whole turns goes while it is hidden in the box. Their
   squash (it bent the base path) is the same flattening on Ball_01's scale, about the contact point, so it does not turn with the dot.
11. The disco ball's swing and the contact sparkle (Sparkle 5) move to the new hit (c3s1 frame 279).
12. Four frames of the ball's rest in the box are cut: the Loop is 416 frames, the disco spin's length.
Everything else, and the disco ball's drop, spin, sparkles and Line, is untouched.
"""
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
from import_room import ILLUSTRATOR, read_keys, value_at
from rml_edit import Doc, bake, num
from rml_read import Scene, chapter_dir
from rooms_sheet import Sheet

SCENE = chapter_dir("ch3") / "scene.rml"
SCRATCH = chapter_dir("ch3").parent.parent / ".cache" / "scratch.nosync" / "ch3"
ROOM = "Chapter 3"
INTRO, L, T0 = 192, 416, 117
PHASE0 = INTRO - 1 - T0                 # the Loop's first frame is c3s1 frame 74
R = 17.678
SQUASH = (1.131, 0.854)                 # their full squash: width and height (Ball_Squash at its far end), about the contact point
DISCO_WRAP, FLOOR_CLIP, DISCO_SWING = "9:689", "9:3108", "9:2"
OLD_HIT, NEW_HIT = 57, 279 - PHASE0     # the disco reactions' Loop frames: answered the rebuilt journey's hit; c3s1's hit
NAMES = ("Picture_Frame_F", "Picture_Land_F", "Ring_lid", "Jem", "Mobile", "Bar_01", "Bar_02", "Bar_03", "Bird", "Leg")


def joystick_x():
    """Their joystick's x keys with each squash rise stretched to 6 frames (the low key before a peak moved back to it)."""
    ab = next(a for a in ET.parse(ILLUSTRATOR).getroot().iter("Artboard") if a.get("name") == "NYT_YIG_c3s1")
    ball = next(a for a in ab.iter("LinearAnimation") if a.get("name") == "Ball")
    kp = next(kp for ko in ball.findall("KeyedObject") if ko.get("objectId") == "1:17385" for kp in ko.findall("KeyedProperty") if kp.get("property") == "x")
    keys = read_keys(kp)
    out = list(keys)
    for i in range(1, len(keys)):
        f, v = keys[i][0], keys[i][1]
        if v > 0 and keys[i - 1][1] < v and f - keys[i - 1][0] < 6:
            assert i < 2 or keys[i - 2][0] <= f - 6, f
            out[i - 1] = (f - 6,) + tuple(keys[i - 1][1:])
    return out


def main():
    doc = Doc(SCENE)
    sc = Scene(SCENE)
    by_name = {}
    room_node = next(e for e in sc.root.iter("Node") if e.get("name") == f"{ROOM} Room")
    for e in room_node.iter():
        if e.get("name") in NAMES + ("Ball_Move", "Ball_01", "Chapter 3 Sparkle 5"):
            by_name.setdefault(e.get("name"), e)
    ids = {n: by_name[n].get("id") for n in NAMES}
    loop, intro = f"{ROOM} Loop", f"{ROOM} Intro"
    # 4. the mobile's last key matches its first (it settles back on its tilt)
    a, b = doc.anim(loop)
    oi = next(i for i in range(a, b) if f'objectId="{ids["Mobile"]}"' in doc.lines[i])
    last = max((i for i in range(oi, doc.end(oi)) if "<KeyFrameDouble" in doc.lines[i]), key=lambda i: int(re.search(r'frame="(\d+)"', doc.lines[i]).group(1)))
    assert 'frame="338"' in doc.lines[last] and "value=" not in doc.lines[last], doc.lines[last]
    doc.lines[last] = doc.lines[last].replace("<KeyFrameDouble ", '<KeyFrameDouble value="-0.06981317" ', 1)
    tmp = SCRATCH / "decisions-step.rml"
    tmp.write_text("\n".join(doc.lines))
    sc = Scene(tmp)
    sh = Sheet(sc)
    lk, ik = sh.anim_keys(sc.animations[loop]), sh.anim_keys(sc.animations[intro])
    c3 = lambda oid, prop, f: lk[oid][prop].at(f)
    ball_move, ball_01 = by_name["Ball_Move"].get("id"), by_name["Ball_01"].get("id")

    # ---- c3s1 per frame, 0..415 (12: four frames of the rest in the box cut; nothing moves there)
    F = range(L)
    jx = joystick_x()
    v = {}
    for n in NAMES:
        oid = ids[n]
        for prop in lk.get(oid, {}):
            v[(oid, prop)] = {f: c3(oid, prop, f) for f in F}
    lid, jem = ids["Ring_lid"], ids["Jem"]
    for f in F:                                                       # 4. the lid falls shut and the ring lowers, out of the ball's sight
        if f >= 350:
            v[(jem, "y")][f] = -6.25 + 3.25 * (0.5 - 0.5 * math.cos(math.pi * min((f - 350) / 16, 1.0)))
        if f >= 356:
            u = min((f - 356) / 24, 1.0)
            v[(lid, "rotation")][f] = -0.9948377 * (1 - u * u)
    for n in ("Picture_Frame_F", "Picture_Land_F"):                   # 5. switched back while the ball is in the box
        for f in F:
            if f >= 345:
                v[(ids[n], "opacity")][f] = 1.0
    bx = {f: c3(ball_move, "x", f) for f in F}
    by = {f: c3(ball_move, "y", f) for f in F}
    size = {f: c3(ball_01, "scaleX", f) for f in F}
    sq = {f: (value_at(jx, f) + 1) / 2 for f in F}
    sx = {f: size[f] * (1 + (SQUASH[0] - 1) * sq[f]) for f in F}
    sy = {f: size[f] * (1 + (SQUASH[1] - 1) * sq[f]) for f in F}
    # 9. the dot turns with the travel, one turn per circumference at the size of the moment; the leftover goes in the box
    th = [0.0]
    for f in range(L):
        dx = bx[(f + 1) % L] - bx[f]
        th.append(th[-1] + (dx / (R * size[f]) if abs(dx) < 30 else 0.0))
    resid = th[L] - 2 * math.pi * round(th[L] / (2 * math.pi))
    a0, z0 = 342, 410
    sm = lambda t: t * t * (3 - 2 * t)
    th = [t - resid * (sm(min(max((f - a0) / (z0 - a0), 0.0), 1.0))) for f, t in enumerate(th)]
    turns = th[L] - th[0]
    # the ball before the hop rides the picture's drop (the import's intro keys); after it, c3s1
    pre = {k: {f: ik[o][p].at(f) for f in range(T0)} for k, (o, p) in {"x": (ball_move, "x"), "y": (ball_move, "y"), "s": (ball_01, "scaleX")}.items()}

    # ---- their ball goes; the standard ball comes in its place, with the room's Floor Clip
    i = doc.idx(ball_move)
    j = doc.end(i)
    gone = set(re.findall(r'\bid="([^"]+)"', "\n".join(doc.lines[i:j + 1])))
    level = len(doc.lines[i]) - len(doc.lines[i].lstrip())
    del doc.lines[i:j + 1]
    for an in (intro, loop, f"{ROOM} Waiting", f"{ROOM} Built"):
        for oid in gone:
            doc.drop_object(an, oid)
    n = doc.new_id
    ballid, b01, b01s, spin, spinart, hl, base = (n() for _ in range(7))
    p = " " * level
    art = [f'{p}<Node x="{num(bx[0])}" y="{num(by[0])}" name="{ROOM} Ball" id="{ballid}">',
           f'{p}    <Node name="Ball_01" id="{b01}">',
           f'{p}        <Node x="-0.072021484" y="0.096008301" name="Ball_01_Scale" id="{b01s}">',
           f'{p}            <Node y="-17.572" name="{ROOM} Ball Spin" id="{spin}">',
           f'{p}                <Node y="17.572" name="{ROOM} Ball Spin Art" id="{spinart}">',
           f'{p}                    <Shape x="6.3640137" y="-23.834076" rotation="-0.77726489" name="Ball_01_Highlight" id="{hl}">',
           f'{p}                        <Ellipse width="7.5" height="9.6440001" x="-1.0000001" scaleY="1.174" scaleX="1.174" id="{n()}"/>',
           f'{p}                        <Fill id="{n()}">', f'{p}                            <SolidColor colorValue="FFFFFFFF" id="{n()}"/>', f'{p}                        </Fill>',
           f'{p}                        <Stroke thickness="1.5" cap="round" join="round" transformAffectsStroke="false" id="{n()}">',
           f'{p}                            <SolidColor colorValue="FF1F1F1F" id="{n()}"/>', f'{p}                        </Stroke>',
           f'{p}                        <ClippingShape sourceId="{FLOOR_CLIP}" name="Floor Clip" id="{n()}"/>',
           f'{p}                    </Shape>',
           f'{p}                    <Shape y="-17.571991" name="Ball_01_Base" id="{base}">',
           f'{p}                        <PointsPath isClosed="true" name="Path" id="{n()}">',
           f'{p}                            <CubicDetachedVertex inRotation="3.1415927" inDistance="9.7632895" outDistance="9.7632895" y="-17.677999" id="{n()}"/>',
           f'{p}                            <CubicDetachedVertex inRotation="-1.5707964" inDistance="9.7632895" outRotation="1.5707964" outDistance="9.7632895" x="17.677999" id="{n()}"/>',
           f'{p}                            <CubicDetachedVertex inDistance="9.7632895" outRotation="3.1415927" outDistance="9.7632895" y="17.677999" id="{n()}"/>',
           f'{p}                            <CubicDetachedVertex inRotation="1.5707964" inDistance="9.7632895" outRotation="-1.5707964" outDistance="9.7632895" x="-17.677999" id="{n()}"/>',
           f'{p}                        </PointsPath>',
           f'{p}                        <Fill id="{n()}">', f'{p}                            <SolidColor colorValue="FFFF5959" id="{n()}"/>', f'{p}                        </Fill>',
           f'{p}                        <Stroke thickness="1.5" cap="round" join="round" transformAffectsStroke="false" id="{n()}">',
           f'{p}                            <SolidColor colorValue="FF1F1F1F" id="{n()}"/>', f'{p}                        </Stroke>',
           f'{p}                        <ClippingShape sourceId="{FLOOR_CLIP}" name="Floor Clip" id="{n()}"/>',
           f'{p}                    </Shape>',
           f'{p}                </Node>', f'{p}            </Node>', f'{p}        </Node>', f'{p}    </Node>', f'{p}</Node>']
    doc.lines[i:i] = art

    # ---- write: intro (before the hop: the picture's drop, or c3s1's first frame; after: c3s1), loop (c3s1 from frame 74, round)
    def ser_intro(c3v, before):
        return {f: (before(f) if f < T0 else c3v[f - T0]) for f in range(INTRO)}

    def ser_loop(c3v, extra=None):
        return {k: c3v[(PHASE0 + k) % L] + (extra(k) if extra else 0.0) for k in range(L + 1)}

    tracks = [((ballid, "x"), bx, lambda f: pre["x"][f]), ((ballid, "y"), by, lambda f: pre["y"][f]),
              ((b01, "scaleX"), sx, lambda f: pre["s"][f]), ((b01, "scaleY"), sy, lambda f: pre["s"][f] * ik[ball_01]["scaleY"].at(f) / ik[ball_01]["scaleX"].at(f)),
              ((spin, "rotation"), {f: th[f] for f in F}, lambda f: th[0])]
    for key, c3v in v.items():
        tracks.append((key, c3v, lambda f, c3v=c3v: c3v[0]))
    doc.set_duration(loop, L)
    doc.set_duration(f"{ROOM} Small Loop", L)
    for (oid, prop), c3v, before in tracks:
        iv = ser_intro(c3v, before)
        lv = ser_loop(c3v, (lambda k: turns * ((PHASE0 + k) // L)) if prop == "rotation" and oid == spin else None)
        if prop == "opacity":                                          # switches, as hold keys
            hold = lambda s, fr: [(f, s[f], "hold") for f in fr if f == fr[0] or f == fr[-1] or s[f] != s[f - 1]]
            ik_, lk_ = hold(iv, list(range(INTRO))), hold(lv, list(range(L + 1)))
        else:
            ik_, lk_ = bake(iv, range(INTRO)), bake(lv, range(L + 1))
        doc.set_prop(intro, oid, prop, ik_)
        doc.set_prop(loop, oid, prop, lk_)
        doc.set_prop(f"{ROOM} Waiting", oid, prop, [(0, iv[0], "hold")])
        doc.set_prop(f"{ROOM} Built", oid, prop, [(0, iv[INTRO - 1], "hold")])

    # ---- 11. the disco ball's swing and the contact sparkle move to the new hit (shifted round the Loop)
    shift = NEW_HIT - OLD_HIT
    s5 = by_name["Chapter 3 Sparkle 5"]
    s5_path = next(c for c in s5 if c.tag == "PointsPath").get("id")
    moved = [(DISCO_SWING, "rotation"), (s5_path, "scaleX"), (s5_path, "scaleY"), (s5.get("id"), "opacity")]
    old_len = 416
    for oid, prop in moved:
        k = lk[oid][prop]
        vals = {f: k.at((f - shift) % old_len) for f in range(L + 1)}
        if oid == DISCO_SWING:                                         # its last 0.001 rad would cross the seam: it ends there
            vals = {f: (0.0 if f < NEW_HIT or f == L else x) for f, x in vals.items()}
        if prop == "opacity":
            doc.set_prop(loop, oid, prop, [(f, vals[f], "hold") for f in range(L + 1) if f in (0, L) or vals[f] != vals[f - 1]])
        else:
            doc.set_prop(loop, oid, prop, bake(vals, range(L + 1)))
    doc.save()
    print(f"wrote {SCENE}: c3s1 from intro frame {T0} ({T0 / 60:.2f} s), Loop {L} frames from c3s1 frame {PHASE0}; the ball turns "
          f"{turns / (2 * math.pi):.0f} times a loop (leftover {resid:+.2f} rad in the box); the disco reactions moved to Loop frame {NEW_HIT} "
          f"({3.2 + NEW_HIT / 60:.2f} s)")


if __name__ == "__main__":
    if "--write" not in sys.argv:
        raise SystemExit(__doc__)
    main()
