"""End (scene end): one more ball joins the left pile during the intro (Demetre, 2026-11-03).

    python3 chapters/ch3/scripts/ch3_end_ball.py --write      once, on the scene as committed in fa89b06

The standard ball (Chapter 1 card 3's art and dot, End's red), 0.9 times its size, rides in with the room's front plane and rolls
along the floor line from the room's left as the pan starts, slowing steadily, its dot turning one turn per circumference. At 1.60 s it
meets the loose ball at the left pile's edge and stops in front of the pile's edge at 1.67 s; the loose ball gives 4 units and settles
back 1, and the pile's edge ball gives a little and settles, all still by 1.93 s, before the copy at 2.0 s. It is drawn in front of the
pile. After the intro it is part of the pile: the loop does not move it, and the Built pose has it settled.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
from ball_motion import smooth
from rml_edit import Doc, bake, num
from rml_read import chapter_dir

SCENE = chapter_dir("ch3") / "scene.rml"
ROOM = "End"
INTRO = 192
R, SIZE, FLOOR = 17.678, 0.9, 712.0
FRONT = "9:31249"
LOOSE, EDGE = "9:27872", "9:27860"          # the loose ball beside the left pile (x 658.9, r 11.2) and the pile's edge ball (x 620)
LOOSE_X, EDGE_X = 211.957, 173.043          # their own x (inside the pile's group)
START, MEET, STOP = 3, 96, 100              # the roll starts with the pan; meets the loose ball at 1.60 s; stops at 1.67 s
V_START, V_MEET = 9.0, 1.0                  # units a frame
CONTACT_X = 658.9 - 11.2 - R * SIZE         # the new ball's centre when it touches the loose ball


def main():
    a = (V_START - V_MEET) / (MEET - START)
    dist = (V_START + V_MEET) / 2 * (MEET - START)
    x0 = CONTACT_X - dist
    xs = {}
    for f in range(INTRO):
        if f <= START:
            xs[f] = x0
        elif f <= MEET:
            t = f - START
            xs[f] = x0 + V_START * t - 0.5 * a * t * t
        elif f <= STOP:                         # gives up its last speed to the loose ball: slows to rest in 4 frames
            t = f - MEET
            T = STOP - MEET
            xs[f] = CONTACT_X + V_MEET * (t - t * t / (2 * T))
        else:
            xs[f] = xs[STOP]
    r = R * SIZE
    th = {0: 0.0}
    for f in range(1, INTRO):
        th[f] = th[f - 1] + (xs[f] - xs[f - 1]) / r
    loose = {f: LOOSE_X + 4.0 * smooth(min(max((f - MEET) / 10, 0), 1)) - 1.0 * smooth(min(max((f - 106) / 10, 0), 1)) for f in range(INTRO)}
    edge = {f: EDGE_X - 1.5 * (smooth(min(max((f - 98) / 6, 0), 1)) - smooth(min(max((f - 104) / 10, 0), 1))) for f in range(INTRO)}

    doc = Doc(SCENE)
    n = doc.new_id
    ball, b01, b01s, spin, spinart, hl, base = (n() for _ in range(7))
    fi = doc.idx(FRONT)
    p = " " * (len(doc.lines[fi]) - len(doc.lines[fi].lstrip()) + 4)
    art = [f'{p}<Node x="{num(xs[INTRO - 1])}" y="{num(FLOOR)}" name="{ROOM} Ball" id="{ball}">',
           f'{p}    <Node scaleX="{SIZE}" scaleY="{SIZE}" name="Ball_01" id="{b01}">',
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
           f'{p}                </Node>', f'{p}            </Node>', f'{p}        </Node>', f'{p}    </Node>', f'{p}</Node>']
    doc.lines[fi + 1:fi + 1] = art           # the front plane's first child: drawn in front of the pile
    fr = range(INTRO)
    for oid, prop, vals in ((ball, "x", xs), (spin, "rotation", th), (LOOSE, "x", loose), (EDGE, "x", edge)):
        k = bake(vals, fr)
        doc.set_prop(f"{ROOM} Intro", oid, prop, k)
        doc.set_prop(f"{ROOM} Waiting", oid, prop, [(0, vals[0], "hold")])
        doc.set_prop(f"{ROOM} Built", oid, prop, [(0, vals[INTRO - 1], "hold")])
    doc.save()
    print(f"wrote {SCENE}: {ROOM} Ball rolls from x {x0:.0f} (room) at {START / 60:.2f} s, meets the loose ball at {MEET / 60:.2f} s, "
          f"rests at x {xs[STOP]:.1f} at {STOP / 60:.2f} s ({th[INTRO - 1] / 6.2832:.2f} turns); slowing {a:.3f} a frame squared")


if __name__ == "__main__":
    if "--write" not in sys.argv:
        raise SystemExit(__doc__)
    main()
