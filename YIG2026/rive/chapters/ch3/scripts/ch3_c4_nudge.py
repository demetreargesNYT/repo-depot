"""Chapter 4: the player's ball springs on the yellow block 8 units further right, so its edge stays inside the phone frame (x 560).

    python3 chapters/ch3/scripts/ch3_c4_nudge.py --write      once, on the scene as committed in 65494db

At 1.17x (1.32x squashed) on the block at x 577 its left edge reached x 553 (import policy: nudge it inside). The flight in from
the floor (c4s1 frames 12 to 70) and the flight out to the next block (110 to 140) each take the 8 units as an even change of
horizontal speed, starting and ending on a contact, so both stay parabolas; the spring itself is unchanged, 8 units right. The dot
turns with the extra travel and is back where it was by the next block, so the Loop still ends on its first pose.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
from rml_edit import Doc, bake
from rml_read import Scene, chapter_dir
from rooms_sheet import Sheet

SCENE = chapter_dir("ch3") / "scene.rml"
ROOM = "Chapter 4"
R, SHIFT = 17.678, 8.0
T0, PHASE0, N, INTRO = 96, 95, 420, 192
IN, HOLD, OUT = (12, 70), (70, 110), (110, 140)          # c4s1 frames


def offset(c):
    if c <= IN[0] or c >= OUT[1]:
        return 0.0
    if c < IN[1]:
        return SHIFT * (c - IN[0]) / (IN[1] - IN[0])
    if c <= OUT[0]:
        return SHIFT
    return SHIFT * (1 - (c - OUT[0]) / (OUT[1] - OUT[0]))


def main():
    sc = Scene(SCENE)
    sh = Sheet(sc)
    room = next(e for e in sc.root.iter("Node") if e.get("name") == f"{ROOM} Room")
    bn = next(e for e in room.iter("Node") if e.get("name") == f"{ROOM} Ball")
    ball = bn.get("id")
    b01 = next(e for e in bn.iter() if e.get("name") == "Ball_01").get("id")
    spin = next(e for e in bn.iter() if e.get("name") == f"{ROOM} Ball Spin").get("id")
    loop = sh.anim_keys(sc.animations[f"{ROOM} Loop"])
    intro = sh.anim_keys(sc.animations[f"{ROOM} Intro"])
    lc = lambda k: (k + PHASE0) % N                              # Loop frame -> c4s1 frame
    ic = lambda f: max(f - T0, 0)                                # Intro frame -> c4s1 frame
    size = {lc(k): (loop[b01]["scaleX"].at(k) + loop[b01]["scaleY"].at(k)) / 2 for k in range(N)}
    # the dot's extra turn: in with the extra travel, out scaled so it closes exactly by the next block
    dth = {0: 0.0}
    for c in range(1, N):
        dth[c] = dth[c - 1] + (offset(c) - offset(c - 1)) / (R * size[c])
    gain = dth[OUT[0]]
    lost = dth[OUT[0]] - dth[OUT[1]]
    for c in range(OUT[0] + 1, N):
        if c <= OUT[1]:
            dth[c] = gain * (1 - (gain - dth[c]) / lost)
        else:
            dth[c] = 0.0
    doc = Doc(SCENE)
    fi, fl = range(INTRO), range(N + 1)
    ix = {f: intro[ball]["x"].at(f) + offset(ic(f)) for f in fi}
    ir = {f: intro[spin]["rotation"].at(f) + dth[ic(f)] for f in fi}
    lx = {k: loop[ball]["x"].at(k) + offset(lc(k)) for k in fl}
    lr = {k: loop[spin]["rotation"].at(k) + dth[lc(k)] for k in fl}
    doc.set_prop(f"{ROOM} Intro", ball, "x", bake(ix, fi))
    doc.set_prop(f"{ROOM} Intro", spin, "rotation", bake(ir, fi))
    doc.set_prop(f"{ROOM} Loop", ball, "x", bake(lx, fl))
    doc.set_prop(f"{ROOM} Loop", spin, "rotation", bake(lr, fl))
    doc.set_prop(f"{ROOM} Built", ball, "x", [(0, ix[INTRO - 1], "hold")])
    doc.set_prop(f"{ROOM} Built", spin, "rotation", [(0, ir[INTRO - 1], "hold")])
    doc.save()
    left = min(lx[k] - R * loop[b01]["scaleX"].at(k) - 0.75 for k in fl if loop[ball]["y"].at(k) < 712)
    print(f"wrote {SCENE}: the spring on the yellow block at x {lx[0]:.1f}; the ball's left edge now reaches x {left:.1f}; "
          f"seam x {lx[0]:.2f} / {lx[N]:.2f}, dot {lr[0]:.3f} / {lr[N]:.3f}")


if __name__ == "__main__":
    if "--write" not in sys.argv:
        raise SystemExit(__doc__)
    main()
