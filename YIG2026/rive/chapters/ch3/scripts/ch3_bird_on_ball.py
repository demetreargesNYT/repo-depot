"""Regenerates the whole Bird on Ball room (since removed): refuses chapters/ch3/scene.rml once it has changed since commit ff5ca3c (tools/regen_guard.py).

Chapter 3 card 2 (scene chapter-3-bird, room "Bird on Ball"): the standard ball grows under c3s1's bird (Demetre, 2026-11-03).

    python3 chapters/ch3/scripts/ch3_bird_on_ball.py --write      once, on the scene as committed in ff5ca3c

There is no illustrator artboard for this room; the bird is c3s1's (NYT_YIG_c3s1, the one the room already has, with its blink).
Intro: the standard ball (Chapter 1 card 3's art and dot) rides in with the room at its Chapter 3 size, the bird on top; as the pan
ends (1.60 s) it grows to 2 times about its contact point (to 2.20 s, a slight overshoot); the bird hops up as it swells (2.00 s) and
drops back onto its top (2.30 to 2.60 s, one gravity), and the ball gives a little under it. Loop (5 s, the bird's blink's length):
the ball sways 5 units each way along the floor line, its dot rolling with it, and the bird tilts against the sway about its feet.
"""
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
from ball_motion import pulse
from rml_edit import Doc, bake, num
import regen_guard
WRITTEN_AGAINST = "ff5ca3c"     # the scene this was run on, once (see above)
from rml_read import Scene, chapter_dir

SCENE = chapter_dir("ch3") / "scene.rml"
ROOM = "Bird on Ball"
INTRO, L = 192, 300
G, R, FLOOR = 0.40, 17.678, 712.0
X0 = 748.0
OLD_BALL, BIRD, LEG2 = "9:32448", "9:32384", "9:32365"
BIRD_UP = 4.96                           # the bird's own origin sits this far above the ball's top
GROW = (96, 132)                         # 1.60 to 2.20 s
HOP, APEX, LAND = 120, 138, 156          # the bird: hops at 2.00 s, tops out at 2.30 s, lands at 2.60 s
SWAY, TILT = 5.0, 0.012                  # units each way; the bird's counter-tilt in radians per unit


def size(f):
    if f <= GROW[0]:
        return 1.0
    u = min((f - GROW[0]) / (GROW[1] - GROW[0]), 1.0)
    c1, c3 = 1.2, 2.2                    # a back.out with a small overshoot (about 4 percent of the growth)
    e = 1 + c3 * (u - 1) ** 3 + c1 * (u - 1) ** 2
    return 1.0 + e


def squash(f):
    k = f - LAND
    p = pulse(k) if 0 <= k < 30 else 0.0
    return 1 + 0.7 * 0.04 * p, 1 - 0.04 * p


def ball_top(f, sy=1.0):
    return FLOOR - 2 * R * size(f) * sy


def main():
    # the bird's hop: launch speed so it tops out at APEX and lands on the grown ball at LAND under one gravity
    land_y = ball_top(LAND)
    apex_y = land_y - 0.5 * G * (LAND - APEX) ** 2
    hop_y = ball_top(HOP)
    rise = hop_y - apex_y
    v_up = G * (APEX - HOP)
    assert abs(rise - 0.5 * G * (APEX - HOP) ** 2) < 6, (rise, 0.5 * G * (APEX - HOP) ** 2)
    g_up = 2 * rise / (APEX - HOP) ** 2  # the exact gravity of the rise from where the ball's top is at the hop
    bird_y = {}
    for f in range(INTRO):
        sx, sy = squash(f)
        if f <= HOP:
            bird_y[f] = ball_top(f)
        elif f <= APEX:
            t = APEX - f
            bird_y[f] = apex_y + 0.5 * g_up * t * t
        elif f <= LAND:
            t = f - APEX
            bird_y[f] = apex_y + 0.5 * G * t * t
        else:
            bird_y[f] = ball_top(f, sy)
    sc = Scene(SCENE)
    doc = Doc(SCENE)
    intro, loop, waiting, built = (f"{ROOM} {n}" for n in ("Intro", "Loop", "Waiting", "Built"))
    for an in (intro, loop, waiting, built):
        doc.drop_object(an, OLD_BALL)
    # the bird and its second leg go into a node at its feet; the old ball goes; the new ball and the bird go in the floor plane
    bird_lines = []
    for oid in (BIRD, LEG2):
        i = doc.idx(oid)
        j = doc.end(i)
        block = doc.lines[i:j + 1]
        del doc.lines[i:j + 1]
        bird_lines.append(block)
    i = doc.idx(OLD_BALL)
    del doc.lines[i:doc.end(i) + 1]
    plane = next(e for e in sc.root.iter("Node") if e.get("name") == f"{ROOM} Floor Plane").get("id")
    pi = doc.idx(plane)
    assert doc.lines[pi].rstrip().endswith("/>"), "the floor plane is expected to be empty"
    pad = " " * (len(doc.lines[pi]) - len(doc.lines[pi].lstrip()))
    n = doc.new_id
    ball, b01, b01s, spin, spinart, hl, base, birdw, birdart = (n() for _ in range(9))
    p = pad + "    "

    def reindent(block, level):
        d = level - (len(block[0]) - len(block[0].lstrip()))
        return [(" " * d + l) if d >= 0 else l[-d:] for l in block]
    bird_block = [l for blk in bird_lines for l in reindent(blk, len(p) + 8)]
    # inside the wrapper the bird keeps its old place relative to the ball's top: x 6, BIRD_UP above it
    bird_block = [re.sub(r'(name="(Bird|Bird_Leg_2)" id="[^"]+")', r'\1', l) for l in bird_block]
    for k, l in enumerate(bird_block):
        if re.search(r'name="(Bird|Bird_Leg_2)"', l) and len(l) - len(l.lstrip()) == len(p) + 8:
            bird_block[k] = re.sub(r'<Node x="[^"]*" y="[^"]*"', f'<Node x="6" y="{num(-BIRD_UP)}"', l, count=1)
    new = [f'{pad}<Node name="{ROOM} Floor Plane" id="{plane}">',
           f'{p}<Node x="{num(X0)}" y="{num(ball_top(INTRO - 1))}" name="{ROOM} Bird" id="{birdw}">',
           f'{p}    <Node name="{ROOM} Bird Art" id="{birdart}">'] + bird_block + [f'{p}    </Node>', f'{p}</Node>',
           f'{p}<Node x="{num(X0)}" y="{num(FLOOR)}" name="{ROOM} Ball" id="{ball}">',
           f'{p}    <Node scaleX="2" scaleY="2" name="Ball_01" id="{b01}">',
           f'{p}        <Node x="-0.072021484" y="0.096008301" name="Ball_01_Scale" id="{b01s}">',
           f'{p}            <Node y="-17.572" name="{ROOM} Ball Spin" id="{spin}">',
           f'{p}                <Node y="17.572" name="{ROOM} Ball Spin Art" id="{spinart}">',
           f'{p}                    <Shape x="6.3640137" y="-23.834076" rotation="-0.77726489" name="Ball_01_Highlight" id="{hl}">',
           f'{p}                        <Ellipse width="7.5" height="9.6440001" x="-1.0000001" scaleY="1.174" scaleX="1.174" id="{n()}"/>',
           f'{p}                        <Fill id="{n()}">', f'{p}                            <SolidColor colorValue="FFFFFFFF" id="{n()}"/>', f'{p}                        </Fill>',
           f'{p}                        <Stroke thickness="1.5" cap="round" join="round" transformAffectsStroke="false" id="{n()}">',
           f'{p}                            <SolidColor colorValue="FF1F1F1F" id="{n()}"/>', f'{p}                        </Stroke>',
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
           f'{p}                    </Shape>',
           f'{p}                </Node>', f'{p}            </Node>', f'{p}        </Node>', f'{p}    </Node>', f'{p}</Node>',
           f'{pad}</Node>']
    doc.lines[pi:pi + 1] = new
    # ---- keys
    fr_i, fr_l = range(INTRO), range(L + 1)
    sway = {k: SWAY * math.sin(2 * math.pi * k / L) for k in fr_l}
    tracks = {
        (b01, "scaleX"): ({f: size(f) * squash(f)[0] for f in fr_i}, {k: 2.0 for k in fr_l}),
        (b01, "scaleY"): ({f: size(f) * squash(f)[1] for f in fr_i}, {k: 2.0 for k in fr_l}),
        (ball, "x"): ({f: X0 for f in fr_i}, {k: X0 + sway[k] for k in fr_l}),
        (spin, "rotation"): ({f: 0.0 for f in fr_i}, {k: sway[k] / (2 * R) for k in fr_l}),
        (birdw, "x"): ({f: X0 for f in fr_i}, {k: X0 + sway[k] for k in fr_l}),
        (birdw, "y"): (bird_y, {k: ball_top(INTRO - 1) for k in fr_l}),
        (birdw, "rotation"): ({f: 0.0 for f in fr_i}, {k: -TILT * sway[k] for k in fr_l}),
    }
    doc.set_duration(loop, L)
    for (oid, prop), (iv, lv) in tracks.items():
        assert abs(iv[INTRO - 1] - lv[0]) < 1e-6 and abs(lv[0] - lv[L]) < 1e-6, (prop, iv[INTRO - 1], lv[0], lv[L])
        doc.set_prop(intro, oid, prop, bake(iv, fr_i))
        doc.set_prop(loop, oid, prop, bake(lv, fr_l))
        doc.set_prop(waiting, oid, prop, [(0, iv[0], "hold")])
        doc.set_prop(built, oid, prop, [(0, iv[INTRO - 1], "hold")])
    regen_guard.save(doc, WRITTEN_AGAINST, __file__)
    print(f"wrote {SCENE}: {ROOM}: grows {GROW[0] / 60:.2f} to {GROW[1] / 60:.2f} s (peak {max(size(f) for f in fr_i):.3f}); the bird hops at "
          f"{HOP / 60:.2f} s ({v_up:.1f} a frame up, apex y {apex_y:.0f}), lands {LAND / 60:.2f} s on y {land_y:.1f}; the rise's gravity {g_up:.2f}")


if __name__ == "__main__":
    if "--write" not in sys.argv:
        raise SystemExit(__doc__)
    main()
