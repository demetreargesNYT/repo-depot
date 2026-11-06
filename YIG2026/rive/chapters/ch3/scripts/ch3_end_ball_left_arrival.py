"""End finesse note 2, piece 2 (Demetre, 2026-11-06): End's ball arrives from the left, fast: we catch up with the ball that bounced off.

    python3 chapters/ch3/scripts/ch3_end_ball_left_arrival.py --scene PATH [--write]      once; it asserts on a second run

Only the ball's arrival in End's Intro changes (the Intro stays 192 frames, the loop is untouched). On screen, not in the room's plane (the plane
is still sliding in, 1600 to 0 over frames 3 to 93, so the ball's own x is its screen x minus the plane's):
- frames 48 to 64: it comes in from past the left edge (x -30) on a low arc, 14 a frame, dropping 51 units under gravity 0.40, a 3 percent stretch;
- frame 64 (x 194): it lands with a 12 percent squash that springs back with one tiny overshoot by frame 76, keeping 90 percent of its speed;
- frames 64 to 100 (0.6 s): it rolls fast along the floor, 12.6 a frame easing to 11.7, its dot turning one turn per circumference;
- frame 100 (x 631.8): it meets the loose ball at the pile's edge, a small 6 percent squash; the loose ball takes 6.5 units and settles to its old
  final place, the pile's edge ball gives 2; the ball rocks on 4.5 units and settles on its final place (x 633.79, rotation 29.3522) by frame 118;
- everything is still by 2.0 s, when the copy arrives.
Before frame 48 it waits below the stage (y 2400), so nothing pops. The Waiting pose is rebuilt from the Intro, the Built pose gets its y and scale.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rml_edit import Doc  # noqa: E402
from rml_read import chapter_dir  # noqa: E402
from ch3_c4_city_lives import Anim  # noqa: E402
from ch3_c4_ball_exit import hermite_points  # noqa: E402

INTRO = 192
BALL, SPIN, ART, LOOSE, EDGE = "9:46176", "9:46179", "9:46177", "9:27872", "9:27860"
R = 17.678 * 0.9
FLOOR, SCALE = 712.0, 0.9
FINAL_X, FINAL_ROT = 633.7898, 29.3522
CONTACT_X = 658.9 - 11.2 - R                 # where it touches the loose ball (631.79)
START, LAND, CONTACT, DONE = 48, 64, 100, 118
FLY_VX, G = 14.0, 0.40


def plane(f):
    """The Front Plane's x: 1600 to 0 over frames 3 to 93, power2.inOut (0.65, 0, 0.35, 1)."""
    if f <= 3:
        return 1600.0
    if f >= 93:
        return 0.0
    u = (f - 3) / 90
    lo, hi = 0.0, 1.0
    for _ in range(60):
        s = (lo + hi) / 2
        x = 3 * (1 - s) ** 2 * s * 0.65 + 3 * (1 - s) * s * s * 0.35 + s ** 3
        lo, hi = (s, hi) if x < u else (lo, s)
    s = (lo + hi) / 2
    y = 3 * (1 - s) * s * s * 1.0 + s ** 3
    return 1600.0 * (1 - y)


def screen_x():
    """The ball's screen x on every frame from START to DONE."""
    xs = {}
    for f in range(START, LAND + 1):
        xs[f] = -30.0 + FLY_VX * (f - START)
    dist = CONTACT_X - xs[LAND]
    n = CONTACT - LAND
    a = 0.025
    v0 = dist / n + a * n / 2                   # a straight slow-down: the sum of the speeds is the distance
    for f in range(LAND + 1, CONTACT + 1):
        t = f - LAND
        xs[f] = xs[LAND] + v0 * t - 0.5 * a * t * t
    assert abs(xs[CONTACT] - CONTACT_X) < 1e-6
    push, back = 4.5, 2.5
    for f in range(CONTACT + 1, DONE + 1):
        t = f - CONTACT
        if t <= 4:
            e = 1 - (1 - t / 4) ** 2
            xs[f] = CONTACT_X + push * e
        else:
            u = min((t - 4) / (DONE - CONTACT - 4), 1.0)
            e = u * u * (3 - 2 * u)
            xs[f] = CONTACT_X + push - back * e
    assert abs(xs[DONE] - FINAL_X) < 1e-3, xs[DONE]
    return xs, v0


def main():
    argv = sys.argv
    path = Path(argv[argv.index("--scene") + 1]) if "--scene" in argv else chapter_dir("ch3") / "scene.rml"
    doc = Doc(path)
    intro = Anim(doc, "End Intro")
    assert intro.has(BALL, "x") and not intro.has(BALL, "y"), "already applied"
    xs, v0 = screen_x()
    local = {f: xs[f] - plane(f) for f in xs}
    # rotation: one turn per circumference of screen travel, ending on the pose the Built state has
    rot = {DONE: FINAL_ROT}
    for f in range(DONE - 1, START - 1, -1):
        rot[f] = rot[f + 1] - (xs[f + 1] - xs[f]) / R
    x_keys = [(0, local[START], "hold")] + [(f, local[f], "linear") for f in range(START, DONE + 1)] + [(INTRO - 1, FINAL_X, "hold")]
    # the plane's own slide makes the early local x fall; keep a hold at the start, then one linear key a frame
    r_keys = [(0, rot[START], "hold")] + [(f, rot[f], "linear") for f in range(START, DONE + 1)] + [(INTRO - 1, FINAL_ROT, "hold")]
    h = 0.5 * G * (LAND - START) ** 2
    y_fly = hermite_points([(START, FLOOR - h, 0.0), (START + 8, FLOOR - h + 0.5 * G * 64, G * 8), (LAND, FLOOR, G * (LAND - START))])[:-1]
    y_keys = [(0, 2400.0, "hold"), (START - 1, 2400.0, "hold")] + y_fly + [(LAND, FLOOR, "hold"), (INTRO - 1, FLOOR, "hold")]
    sx = [(0, SCALE, "hold"), (START, SCALE / 1.03, "hold"), (LAND - 3, SCALE / 1.03, "power2.inOut"), (LAND, SCALE * 1.12, "power2.out"), (LAND + 3, SCALE * 0.985, "power2.inOut"),
          (LAND + 12, SCALE, "hold"), (CONTACT - 2, SCALE, "power2.out"), (CONTACT, SCALE * 1.06, "power2.inOut"), (CONTACT + 5, SCALE, "hold"), (INTRO - 1, SCALE, "hold")]
    sy = [(0, SCALE, "hold"), (START, SCALE * 1.03, "hold"), (LAND - 3, SCALE * 1.03, "power2.inOut"), (LAND, SCALE * 0.88, "power2.out"), (LAND + 3, SCALE * 1.015, "power2.inOut"),
          (LAND + 12, SCALE, "hold"), (CONTACT - 2, SCALE, "power2.out"), (CONTACT, SCALE * 0.94, "power2.inOut"), (CONTACT + 5, SCALE, "hold"), (INTRO - 1, SCALE, "hold")]
    loose = [(0, 211.957, "hold"), (CONTACT, 211.957, "power2.out"), (CONTACT + 8, 218.457, "power2.inOut"), (CONTACT + 20, 214.957, "hold"), (INTRO - 1, 214.957, "hold")]
    edge = [(0, 173.043, "hold"), (CONTACT + 2, 173.043, "power2.out"), (CONTACT + 8, 171.043, "power2.inOut"), (CONTACT + 18, 173.043, "hold"), (INTRO - 1, 173.043, "hold")]
    for oid, prop, keys in ((BALL, "x", x_keys), (SPIN, "rotation", r_keys), (BALL, "y", y_keys), (ART, "scaleX", sx), (ART, "scaleY", sy), (LOOSE, "x", loose), (EDGE, "x", edge)):
        intro.set(oid, prop, keys)
    intro.commit()

    built = Anim(doc, "End Built")
    built.set(BALL, "y", [(0, FLOOR, "hold")])
    built.set(ART, "scaleX", [(0, SCALE, "hold")])
    built.set(ART, "scaleY", [(0, SCALE, "hold")])
    built.commit()
    doc.rebuild_waiting("End")
    print(f"screen x {xs[START]:.0f} to {xs[DONE]:.1f}; local x {local[START]:.0f} at the start; roll {xs[LAND]:.0f} to {CONTACT_X:.1f} from {v0:.2f} a frame; "
          f"the plane at frame {START} is {plane(START):.0f}")
    if "--write" in argv:
        doc.save()
        print("written", path)
    else:
        print("dry run")


if __name__ == "__main__":
    main()
