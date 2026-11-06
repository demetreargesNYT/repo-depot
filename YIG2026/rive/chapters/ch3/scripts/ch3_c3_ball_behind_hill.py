"""Chapter 3 finesse note 1 of the 2026-11-06 14:13 send: the ball lives half behind the green hill; it never bounces on the hill, and it bounces out from behind it.

    python3 chapters/ch3/scripts/ch3_c3_ball_behind_hill.py --scene PATH [--write]       once; it asserts on a second run

The ball's rest pose in the painting moves from sitting on the crest (foot y 551.68) to half behind the hill (foot y 570.5, so its centre is about 1.7 above the
crest line y 556 and the front hill, drawn over it, hides about half). That pose is where the Intro ends, the Built pose sits, and the loop
starts and ends, so all four agree:
- Intro, frames 121 to 191: the ball rises out of hiding to the half-behind pose (29 frames, eased out, growing from 0.7 to 0.9182) and then
  hangs there with a 1.2 unit breath (the foot lifts and settles, back on 570.5 at frame 191). No overshoot above the crest, no landing.
- Loop, frames 583 to 636 (the return): it pops up from hiding (foot 583.5, scale 0.75, the dot looking down) to the half-behind pose in 16
  frames, then stays there peeking for 37 frames (0.6 s): the dot comes round slowly to the front and the foot breathes 1 unit. No dip, no landing
  on the crest, no prep hop.
- Loop, frames 0 to 22 (the bounce out): the same gather and spring as before but shallower: the foot sinks 3.5 units (570.5 to 574, the ball is
  still about 40 percent visible) instead of 29 (to 581, hidden), the squash keeps 70 percent of its depth, and the spring joins the old arc at frame 23 (a 7
  percent gentler push). Everything from frame 23 on is untouched.
"""
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rml_edit import Doc  # noqa: E402
from rml_read import chapter_dir  # noqa: E402
from ch3_c4_city_lives import Anim  # noqa: E402

BALL, ART, SPIN = None, None, None
Y_OLD, Y_HALF, Y_SINK = 551.6769, 570.5, 574.0
SQUASH = 0.7                    # the gather squash keeps 70 percent of its old depth, so the ball stays about 40 percent visible
S_REST = 0.9182
ROT_REST = -0.0153


def smooth(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def out3(u):
    u = min(max(u, 0.0), 1.0)
    return 1 - (1 - u) ** 3


def parse(lines):
    root = ET.fromstring("<r>" + "\n".join(lines) + "</r>")
    keys = []
    for k in root.iter("KeyFrameDouble"):
        keys.append((int(k.get("frame", 0)), float(k.get("value", 0)), k.get("interpolationType", "hold")))
    return sorted(keys)


def sample(keys, f):
    if f <= keys[0][0]:
        return keys[0][1]
    for (a, va, ta), (b, vb, tb) in zip(keys, keys[1:]):
        if a <= f < b:
            return va if ta == "hold" else va + (vb - va) * (f - a) / (b - a)
    return keys[-1][1]


def replaced(keys, lo, hi, values):
    """Keys with the frames lo..hi (inclusive) replaced by one linear key a frame holding `values` (a function of the frame)."""
    kept = [k for k in keys if not lo <= k[0] <= hi]
    return sorted(kept + [(f, values(f), "linear") for f in range(lo, hi + 1)])


def put(anim, oid, prop, keys):
    anim.set(oid, prop, [(f, v, t) for f, v, t in keys])


def main():
    argv = sys.argv
    path = Path(argv[argv.index("--scene") + 1]) if "--scene" in argv else chapter_dir("ch3") / "scene.rml"
    doc = Doc(path)
    from rml_read import Scene
    sc = Scene(path)
    node = sc.node("Chapter 3 Ball")
    ball = node.get("id")
    art = next(e for e in node.iter("Node") if e.get("name") == "Ball_01").get("id")
    spin = next(e for e in node.iter("Node") if e.get("name") == "Chapter 3 Ball Spin").get("id")

    # ---- the loop
    loop = Anim(doc, "Chapter 3 Loop")
    ky = parse(loop.objs[ball]["props"]["y"])
    assert abs(sample(ky, 0) - Y_OLD) < 1e-3 and abs(sample(ky, 636) - Y_OLD) < 1e-3, "already applied (the loop does not start on the old rest pose)"
    y_old = lambda f: sample(ky, f)
    k1 = (Y_SINK - Y_HALF) / (581.0 - Y_OLD)                     # the sink before the spring: 3.5 units instead of 29.3
    k2 = (514.0382 - Y_SINK) / (514.0382 - 581.0)                # the spring: joins the old arc at frame 23
    assert abs(y_old(12) - 581.0) < 1e-6 and abs(y_old(23) - 514.0382) < 1e-3

    def y_start(f):
        if f <= 12:
            return Y_HALF + (y_old(f) - Y_OLD) * k1
        return 514.0382 + (y_old(f) - 514.0382) * k2
    ky = replaced(ky, 0, 22, y_start)

    def y_return(f):
        if f <= 599:
            return 583.5 + (Y_HALF - 583.5) * out3((f - 583) / 16)
        return Y_HALF - 1.0 * math.sin(math.pi * (f - 599) / (636 - 599))
    ky = replaced(ky, 583, 636, y_return)
    put(loop, ball, "y", ky)
    for prop in ("scaleX", "scaleY"):
        ks = parse(loop.objs[art]["props"][prop])
        old_s = lambda f, ks0=ks: sample(ks0, f)
        ks = replaced(ks, 5, 22, lambda f: S_REST + SQUASH * (old_s(f) - S_REST))
        ks = replaced(ks, 583, 636, lambda f: 0.75 + (S_REST - 0.75) * out3((f - 583) / 16) if f <= 599 else S_REST)
        put(loop, art, prop, ks)
    kr = parse(loop.objs[spin]["props"]["rotation"])
    kr = replaced(kr, 583, 636, lambda f: 2.1847 + (ROT_REST - 2.1847) * smooth((f - 583) / 45))
    put(loop, spin, "rotation", kr)
    loop.commit()

    # ---- the intro
    intro = Anim(doc, "Chapter 3 Intro")
    iy = parse(intro.objs[ball]["props"]["y"])
    assert abs(sample(iy, 191) - Y_OLD) < 1e-3
    iy = replaced(iy, 121, 191, lambda f: 581.0 - (581.0 - Y_HALF) * out3((f - 121) / 29) if f <= 150 else Y_HALF - 1.2 * math.sin(math.pi * (f - 150) / 41))
    put(intro, ball, "y", iy)
    for prop in ("scaleX", "scaleY"):
        ks = parse(intro.objs[art]["props"][prop])
        ks = replaced(ks, 121, 191, lambda f: 0.7 + (S_REST - 0.7) * out3((f - 121) / 29))
        put(intro, art, prop, ks)
    intro.commit()

    # ---- the built pose
    built = Anim(doc, "Chapter 3 Built")
    built.set(ball, "y", [(0, Y_HALF, "hold")])
    built.commit()
    print(f"loop start/end foot {Y_HALF}; sink {Y_SINK}; intro rise from frame 121; return from frame 583")
    if "--write" in argv:
        doc.save()
        print("written", path)
    else:
        print("dry run")


if __name__ == "__main__":
    main()
