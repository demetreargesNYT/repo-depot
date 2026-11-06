"""Regenerates the whole Chapter 4 ball journey: refuses chapters/ch3/scene.rml once it has changed since commit 101e2a3 (tools/regen_guard.py).

Chapter 4: the player's ball keeps c4s1's journey at a near-normal size, with a small hop for an ending (Demetre, 2026-11-03).

    python3 chapters/ch3/scripts/ch3_c4_ball.py --write      once, on the scene as committed in 101e2a3 (c4s1 imported as drawn)

Changes to the faithful import (ch3_c4s1_import.py):
- it starts at 1.60 s (intro frame 96, hidden below the floor line): the intro plays c4s1's first frames, the Loop picks up there;
- its size, 0.7 to 2.14 times in c4s1 before the leap, is mapped onto 0.9 to 1.2 times;
- the leap (to 5.19 times) is replaced: from the crossword tower's springy top (c4s1 frame 242) it hops off to the right (6.85 a
  frame, under the speed it landed with; gravity 0.40), tops out well below the copy and drops inside the phone frame behind the
  stack's front pieces and below the floor line, where it is out of sight;
- in that hidden stretch the ball's pose, its dot and the stack's front and back copies go back to their first values, so the Loop's
  last frame is its first;
- each depth switch (a front copy on or off) is moved to the nearest frame where the ball is clear of that piece;
- the squash rises take 6 frames (they took 2 to 5), each still peaking on its contact;
- the dot turns one turn per circumference of travel at the size of the moment.
"""
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
from import_room import ILLUSTRATOR, Rig, affine, compose, extent, read_keys, value_at
from rml_edit import Doc, bake, num
import regen_guard
WRITTEN_AGAINST = "101e2a3"     # the scene this was run on, once (see above)
from rml_read import Scene, chapter_dir
from rooms_sheet import Sheet

SCENE = chapter_dir("ch3") / "scene.rml"
SCRATCH = chapter_dir("ch3").parent.parent / ".cache" / "scratch.nosync" / "ch3"
ROOM = "Chapter 4"
INTRO, T0 = 192, 96
PHASE0 = INTRO - 1 - T0
R, G, FLOOR, DROP = 17.678, 0.40, 712.0, 14.5            # DROP: Ball_01 sits this far below the ball's node (their rig)
SQUASH = (1.131, 0.854)
SIZE_IN, SIZE_OUT = (0.7, 2.14), (0.9, 1.2)
LAUNCH, VY0, X_END = 242, -6.0, 760.0                    # the hop off the tower's top
HIDE_RESET = 330                                          # c4s1 frame where, out of sight, everything goes back to its start
COPIES = ("Crossword_F", "Coss_F", "Coss_B", "SpB_02_F")


def source():
    ab = next(a for a in ET.parse(ILLUSTRATOR).getroot().iter("Artboard") if a.get("name") == "NYT_YIG_c4s1_Wordle")
    anims = {a.get("id"): a for a in ab.iter("LinearAnimation")}
    ball = next(a for a in anims.values() if a.get("name") == "Ball")
    joy = next(ab.iter("Joystick"))
    jk = {kp.get("property"): read_keys(kp) for ko in ball.findall("KeyedObject") if ko.get("objectId") == joy.get("id") for kp in ko.findall("KeyedProperty")}
    solo = next(e for e in ab.iter("Solo") if e.get("name") == "Ball_Move")
    b01 = next(e for e in ab.iter() if e.get("id") == solo.get("activeComponentId"))
    return Rig(joy, anims), jk, b01.get("id"), int(ball.get("duration"))


def stretched(keys):
    out = list(keys)
    for i in range(1, len(keys)):
        f, v = keys[i][0], keys[i][1]
        if v > 0 and keys[i - 1][1] < v and f - keys[i - 1][0] < 6:
            out[i - 1] = (f - 6,) + tuple(keys[i - 1][1:])
    return out


def piece_boxes(sc, plane, name):
    """World boxes of a stack piece's children (its silhouette, roughly), with the floor plane at rest."""
    par = {c: p for p in sc.root.iter() for c in p}
    node = next(c for c in plane if c.get("name") == name)
    boxes = []
    def world(e):
        chain, p = [], e
        while p is not None and p.tag != "Artboard":
            chain.append(p)
            p = par.get(p)
        m = (1, 0, 0, 1, 0, 0)
        for x in reversed(chain):
            if x.tag in ("Node", "Shape"):
                m = compose(m, affine(x))
        return m
    for sh in node.iter("Shape"):
        b = extent(sh, compose(world(par[sh]), affine(sh)))
        if b[2] > b[0]:
            boxes.append(b)
    return boxes


def overlaps(c, r, boxes):
    for x0, y0, x1, y1 in boxes:
        dx = max(x0 - c[0], 0, c[0] - x1)
        dy = max(y0 - c[1], 0, c[1] - y1)
        if math.hypot(dx, dy) < r:
            return True
    return False


def main():
    rig, jk, b01_src, n = source()
    sc = Scene(SCENE)
    sh = Sheet(sc)
    room = next(e for e in sc.root.iter("Node") if e.get("name") == f"{ROOM} Room")
    plane = next(c for c in room if c.get("name") == f"{ROOM} Floor Plane")
    by_name = {}
    for e in room.iter():
        by_name.setdefault(e.get("name"), e)
    ball, b01, spin = (by_name[k].get("id") for k in (f"{ROOM} Ball", "Ball_01", f"{ROOM} Ball Spin"))
    loop, intro = f"{ROOM} Loop", f"{ROOM} Intro"
    lk = sh.anim_keys(sc.animations[loop])
    F = range(n + 1)
    vals = {(oid, p): {f: k.at(f) for f in F} for oid, props in lk.items() for p, k in props.items()}

    # ---- size and squash
    jx = stretched(jk["x"])
    jy = lambda f: value_at(jk["y"], f)
    raw = {f: rig.sample(value_at(jx, f), jy(f))[(b01_src, "scaleX")] for f in F}
    lo, hi = SIZE_IN
    size = {f: SIZE_OUT[0] + (SIZE_OUT[1] - SIZE_OUT[0]) * min(max((raw[min(f, LAUNCH)] - lo) / (hi - lo), 0.0), 1.0) for f in F}
    sq = {f: (value_at(jx, f) + 1) / 2 for f in F}
    # ---- the hop off the tower, then out of sight; the reset
    bx, by = vals[(ball, "x")], vals[(ball, "y")]
    x0, y0 = bx[LAUNCH], by[LAUNCH]
    s_hop = size[LAUNCH]
    y_end = FLOOR + 2 * R * s_hop + 3 - DROP                       # the node when the ball's top is below the floor line
    N = math.ceil((-VY0 + math.sqrt(VY0 ** 2 + 2 * G * (y_end - y0))) / G)
    vx = (X_END - x0) / N
    first = {k: v[0] for k, v in vals.items()}
    for f in F:
        if LAUNCH < f <= LAUNCH + N:
            t = f - LAUNCH
            bx[f], by[f] = x0 + vx * t, y0 + VY0 * t + 0.5 * G * t * t
        elif LAUNCH + N < f < HIDE_RESET:
            bx[f], by[f] = bx[LAUNCH + N], by[LAUNCH + N]
        elif f >= HIDE_RESET:
            bx[f], by[f] = first[(ball, "x")], first[(ball, "y")]
    hidden = LAUNCH + N
    sx = {f: size[f] * (1 + (SQUASH[0] - 1) * sq[f]) for f in F}
    sy = {f: size[f] * (1 + (SQUASH[1] - 1) * sq[f]) for f in F}
    for f in F:
        if f >= HIDE_RESET:
            sx[f], sy[f] = sx[0], sy[0]
    th = {0: 0.0}
    for f in range(1, n + 1):
        dx = bx[f] - bx[f - 1]
        th[f] = th[f - 1] + (dx / (R * size[f]) if abs(dx) < 30 else 0.0)
    for f in F:
        if f >= HIDE_RESET:
            th[f] = 0.0
    vals[(ball, "x")], vals[(ball, "y")], vals[(b01, "scaleX")], vals[(b01, "scaleY")], vals[(spin, "rotation")] = bx, by, sx, sy, th
    centre = lambda f: (bx[f], by[f] + DROP - (R - 0.106) * sy[f])
    rad = lambda f: R * size[f] + 0.75
    # ---- the depth switches: the leap's goes (the ball no longer passes there); the rest move to where the ball is clear
    moved = []
    for name in COPIES:
        oid = by_name[name].get("id")
        v = vals[(oid, "opacity")]
        boxes = piece_boxes(sc, plane, name)
        sw = [f for f in range(1, n + 1) if abs(v[f] - v[f - 1]) > 0.5 and f < LAUNCH]
        new = {f: v[0] for f in F}
        state, last = v[0], 0
        for f in sw:
            target = v[f]
            cand = [g for d in range(0, 40) for g in (f - d, f + d) if last < g < LAUNCH and not overlaps(centre(g), rad(g), boxes)]
            g = cand[0] if cand else f
            for h in range(g, n + 1):
                new[h] = target
            moved.append((name, f, g, bool(cand)))
            last = g
        for h in range(HIDE_RESET, n + 1):
            new[h] = v[0]
        vals[(oid, "opacity")] = new
    # everything else the Loop keys ends where it starts, out of sight
    for key, v in vals.items():
        for f in range(HIDE_RESET, n + 1):
            v[f] = v[0] if key[1] != "opacity" else v[f]
    # ---- write: the intro (before the start: c4s1's first frame; after: c4s1), the Loop (c4s1 from frame PHASE0, round)
    doc = Doc(SCENE)
    fr_i, fr_l = range(INTRO), range(n + 1)
    for (oid, prop), v in vals.items():
        iv = {f: v[max(f - T0, 0)] for f in fr_i}
        lv = {k: v[(PHASE0 + k) % n] for k in fr_l}
        if prop == "opacity":
            ik_ = [(f, iv[f], "hold") for f in fr_i if f in (0, INTRO - 1) or iv[f] != iv[f - 1]]
            lk_ = [(k, lv[k], "hold") for k in fr_l if k in (0, n) or lv[k] != lv[k - 1]]
        else:
            ik_, lk_ = bake(iv, fr_i), bake(lv, fr_l)
        doc.set_prop(intro, oid, prop, ik_)
        doc.set_prop(loop, oid, prop, lk_)
        doc.set_prop(f"{ROOM} Waiting", oid, prop, [(0, iv[0], "hold")])
        doc.set_prop(f"{ROOM} Built", oid, prop, [(0, iv[INTRO - 1], "hold")])
    regen_guard.save(doc, WRITTEN_AGAINST, __file__)
    top = min(centre(f)[1] - rad(f) for f in range(LAUNCH, hidden))
    xs = [centre(f)[0] for f in range(12, hidden)]
    print(f"wrote {SCENE}: starts at {T0 / 60:.2f} s; size {min(size.values()):.2f} to {max(size.values()):.2f}; the hop off the tower at "
          f"{(T0 + LAUNCH) / 60:.2f} s, {math.hypot(vx, VY0):.2f} a frame, its top at y {top:.0f}, out of sight at {(T0 + hidden) / 60:.2f} s; "
          f"reset at {(T0 + HIDE_RESET) / 60:.2f} s; x {min(xs) - 21:.0f} to {max(xs) + 21:.0f}")
    for name, f, g, ok in moved:
        print(f"  {name} switch: c4s1 frame {f} -> {g} ({(T0 + g) / 60:.2f} s){'' if ok else ' (NO CLEAR FRAME FOUND)'}")


if __name__ == "__main__":
    if "--write" not in sys.argv:
        raise SystemExit(__doc__)
    main()
