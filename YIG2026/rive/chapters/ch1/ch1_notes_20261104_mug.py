"""One time (2026-11-04, sent 08:03, note 1): Chapter 1 card 3's ball comes out of the mug's mouth, not beside it.

    python3 chapters/ch1/ch1_notes_20261104_mug.py            dry run
    python3 chapters/ch1/ch1_notes_20261104_mug.py --write    rewrite chapters/ch1/scene.rml

  * The Mug Clip was a straight line across the stage at y 697, so the ball showed wherever it was above that line, over the mug's
    pink rim beside the mouth too. It is now the mug's mouth: the ball shows above the mouth's front rim inside the opening
    (x 710 to 763, the opening's dark ellipse, centre x 736.5), and anywhere above the mug's top (y 677). The clip's lower edge is the
    front rim curve 2 px above the black, so a thin line of black stays under the ball, like the illustration's other outlines.
  * The ball waited inside the mug at x 717.9, left of the mouth's middle, so it rose with its left edge outside the opening. It now
    waits at x 733 and its hop out is the same flight re-solved from there: it leaves at the same frame and lands on the yellow band
    at the same place and frame (intro frames 108 to 168, loop frames 135 to 195); only its sideways speed changes (1.64 to 1.38 px
    per frame), so it rises through the middle of the mouth (centre x 737 as it clears the rim).
It refuses to run unless the clip and the ball are as they were.
"""
import sys
from pathlib import Path

RIVE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RIVE_ROOT / "tools"))

from ball_motion import smooth                  # noqa: E402
from rml_edit import Doc, bake, num             # noqa: E402
from rml_read import Scene                      # noqa: E402
from rooms_sheet import Sheet                   # noqa: E402

SCENE = RIVE_ROOT / "chapters" / "ch1" / "scene.rml"
ROOM = "Chapter 1 Card 3"
CLIP = "9:17930"
OLD_X, NEW_X = 718.0, 733.1                                       # the ball node (its centre is 0.07 left of it)
CX, RX, CY, BOTTOM, TOP = 736.5, 26.5, 688.5, 695.0, 677.0      # the mouth (from a render), the clip's lower edge, the mug's top
K = 0.5523                                                      # a quarter ellipse's handle length, per radius
FLIGHTS = {"Intro": (108, 168), "Loop": (135, 195)}             # leaves the mug, lands on the band


def main(argv):
    write = "--write" in argv
    s = Scene(SCENE)
    sh = Sheet(s)
    doc = Doc(SCENE)
    ball = next(e.get("id") for e in s.root.iter("Node") if e.get("name") == f"{ROOM} Ball")
    i = doc.idx(CLIP)
    assert '<Rectangle width="9000" height="2000"' in doc.lines[i + 1] and 'y="697"' in doc.lines[i], "the Mug Clip is not the old line"
    new = {}
    for part, (f0, f1) in FLIGHTS.items():
        an = s.animations[f"{ROOM} {part}"]
        n = 192 if part == "Intro" else s.duration(an)
        k = sh.anim_keys(an)[ball]["x"]
        x = {f: k.at(f) for f in range(n)}
        assert abs(x[f0] - OLD_X) < 0.05, (part, x[f0])
        land = x[f1]
        out = dict(x)
        if part == "Intro":                                     # it rides in with the pan inside the mug: the same, 15 px right
            for f in range(0, f0 + 1):
                out[f] = x[f] + (NEW_X - OLD_X)
        else:                                                   # the catch: it slides inside the mug to its new spot (out of sight)
            for f in range(95, 101):
                out[f] = x[95] + (NEW_X - x[95]) * smooth((f - 95) / 5)
            for f in range(101, f0 + 1):
                out[f] = NEW_X
        for f in range(f0, f1 + 1):
            out[f] = NEW_X + (land - NEW_X) * (f - f0) / (f1 - f0)
        new[part] = (out, n)
        print(f"{ROOM} {part}: waits at x {NEW_X} (was {OLD_X}); the hop out, frames {f0} to {f1}, now {(land - NEW_X) / (f1 - f0):.2f} px a "
              f"frame sideways (was {(land - OLD_X) / (f1 - f0):.2f}); centre x {out[f0 + 3]:.1f} as it clears the rim")
    if not write:
        return 0
    for part, (out, n) in new.items():
        doc.set_prop(f"{ROOM} {part}", ball, "x", bake(out, range(n)))
    # the clip: the mug's mouth, and everything above the mug's top
    j = doc.end(i)
    pad = " " * (len(doc.lines[i]) - len(doc.lines[i].lstrip()))
    p = pad + "    "
    v = p + "    "
    nid = doc.new_id
    lines = [f'{pad}<Shape name="{ROOM} Mug Clip" id="{CLIP}">',
             f'{p}<PointsPath isClosed="true" name="Path" id="{nid()}">',
             f'{v}<StraightVertex x="-4000" y="-1400" id="{nid()}"/>',
             f'{v}<StraightVertex x="5500" y="-1400" id="{nid()}"/>',
             f'{v}<StraightVertex x="5500" y="{num(TOP)}" id="{nid()}"/>',
             f'{v}<StraightVertex x="{num(CX + RX)}" y="{num(TOP)}" id="{nid()}"/>',
             f'{v}<CubicDetachedVertex outRotation="1.5707964" outDistance="{num(K * (BOTTOM - CY))}" x="{num(CX + RX)}" y="{num(CY)}" id="{nid()}"/>',
             f'{v}<CubicDetachedVertex inDistance="{num(K * RX)}" outRotation="3.1415927" outDistance="{num(K * RX)}" x="{num(CX)}" y="{num(BOTTOM)}" id="{nid()}"/>',
             f'{v}<CubicDetachedVertex inRotation="1.5707964" inDistance="{num(K * (BOTTOM - CY))}" x="{num(CX - RX)}" y="{num(CY)}" id="{nid()}"/>',
             f'{v}<StraightVertex x="{num(CX - RX)}" y="{num(TOP)}" id="{nid()}"/>',
             f'{v}<StraightVertex x="-4000" y="{num(TOP)}" id="{nid()}"/>',
             f"{p}</PointsPath>",
             f"{pad}</Shape>"]
    doc.lines[i:j + 1] = lines
    doc.rebuild_waiting(ROOM)                                   # the ball waits 15 px right in its Waiting pose too
    doc.save()
    print("wrote", SCENE)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
