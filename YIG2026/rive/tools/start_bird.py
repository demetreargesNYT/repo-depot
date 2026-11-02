"""One time (2026-11-02, history like loading_start.py): Start's bird lands as one bounce with the ball (finesse round, Start).

    python3 tools/start_bird.py            dry run: prints the new times, writes nothing
    python3 tools/start_bird.py --write    rewrite chapters/ch1/scene.rml

Before: the bird rode the ball up (loop frames 60 to 78), then kept rising while the ball came down, hung near the top for
about 0.3 s and fell for about 0.7 s, landing at frame 134, 0.43 s after the ball touched down (frame 108). It went up like
it was thrown and came down like a feather.
After (loop frames at 60 per second):
  * it rides the ball up until frame 72 as before, then lifts 17 px off the ball's top and tops out at frame 93 (a short
    ease-out), with a hang of about 0.14 s within 2 px of the top
  * it falls with a gravity ease (slow at the top, fastest at the end) for 21 frames, 0.35 s, as long as the rise
  * it lands at frame 114, 6 frames (0.1 s) after the ball touches down, with its landing squash, and then the small
    rebound it already had; the stretch on the way up and down is moved with it
The dip before the jump (48 to 66), the 4.5 s loop and the blinks (the small loop) are untouched.
"""
import math
import sys

from ball_easing import Patcher
from rml_read import chapter_dir
from rooms_sheet import Sheet

EASE = {"sine.inOut": (0.37, 0, 0.63, 1), "power2.out": (0.33, 1, 0.68, 1), "back.out": (0.34, 1.56, 0.64, 1)}
S, T, LAND = 72, 93, 114        # the bird leaves the ball's top; the top of its arc; it lands (loop frames)
PEAK_ABOVE = 17.0               # px it lifts above the ball's top at frame S
SHARP = 1.5                     # how sharply the rise stops at the top (2 is a plain ease-out; lower hangs less)


def main(argv):
    pt = Patcher(chapter_dir("ch1") / "scene.rml")
    s, sh = pt.scene, Sheet(pt.scene)
    keys = sh.anim_keys(s.animations["Start Loop"])
    get = lambda n: next(o for o in keys if s.by_id[o].get("name") == n)
    bird, ball, car = get("Start Bird"), get("Start Ball"), get("Start Bird Carrier")
    ball_y, car_y = keys[ball]["y"], keys[car]["y"]
    seat = lambda f: ball_y.at(f) + car_y.at(f) - 58.0          # the bird's world y while it sits on the ball
    rest = seat(0)
    r0 = seat(S)
    peak = r0 - PEAK_ABOVE

    def world(f):
        if f <= S:
            return seat(f)
        if f <= T:
            u = (f - S) / (T - S)
            return r0 + (peak - r0) * (1 - (1 - u) ** SHARP)      # ease-out: slows to nothing at the top
        if f <= LAND:
            u = (f - T) / (LAND - T)
            return peak + (rest - peak) * u ** 2                  # gravity: slow at the top, fastest at the end
        return rest

    local = {f: world(f) - ball_y.at(f) - car_y.at(f) for f in range(S, LAND + 1)}
    # never inside the ball: the bird's world y must stay at or above (less than) the seat
    inside = [f for f in range(S, LAND + 1) if world(f) > seat(f) + 0.01]
    top_frames = [f for f in range(S, LAND + 1) if world(f) <= peak + 2.0]
    print(f"bird leaves the ball's top at frame {S} ({S / 60:.2f} s into the loop), tops out at {T} ({T / 60:.2f} s), lands at {LAND} ({LAND / 60:.2f} s); "
          f"was: tops out about frame 90, lands 134 ({134 / 60:.2f} s)")
    print(f"within 2 px of the top: frames {top_frames[0]} to {top_frames[-1]} ({(top_frames[-1] - top_frames[0] + 1) / 60:.2f} s); fall {LAND - T} frames ({(LAND - T) / 60:.2f} s); "
          f"ball touches down at frame 108, bird {LAND - 108} frames ({(LAND - 108) / 60:.2f} s) later; frames inside the ball: {inside}")
    print("speed per frame (px) frames 70 to 116:", " ".join(f"{abs(world(f + 1) - world(f)):.1f}" for f in range(70, 116, 2)))
    if "--write" not in argv:
        return 0

    def ease_xml(name):
        x1, y1, x2, y2 = EASE[name]
        return f'<CubicEaseInterpolator x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" id="{pt.new_id()}"/>'

    def key(frame, value, how="hold"):
        fr = f' frame="{frame}"' if frame else ""
        if how == "hold":
            return (frame, f'<KeyFrameDouble value="{value!r}"{fr} id="{pt.new_id()}"/>')
        if how == "linear":
            return (frame, f'<KeyFrameDouble value="{value!r}" interpolationType="linear"{fr} id="{pt.new_id()}"/>')
        return (frame, f'<KeyFrameDouble value="{value!r}" interpolationType="cubic"{fr} id="{pt.new_id()}">{ease_xml(how)}</KeyFrameDouble>')

    # Bird y (local to the carrier): -58 until the bird leaves, one linear key per frame while it flies, then the rebound it had
    ents = [key(0, -58.0), key(S - 1, -58.0)]
    ents += [key(f, round(local[f], 4), "linear") for f in range(S, LAND + 1)]
    ents += [key(LAND + 1, -58.0), key(120, -58.0), key(120 + 0, -60.5, "power2.out"), key(131, -58.0), key(270, -58.0)]
    ents = [e for e in ents if True]
    # the rebound pair replaces the old (140: -60.5 power2.out, 151: -58) shifted 20 frames earlier; drop the duplicate frame-120 hold
    seen, clean = set(), []
    for f, t in ents:
        if f == 120 and "hold" and 'interpolationType' not in t:
            continue
        if f in seen:
            continue
        seen.add(f)
        clean.append((f, t))
    p, e = pt.block("Start", bird, "y")
    head, _ = pt.entries(p, e)
    pt.write_entries(p, e, head, clean)

    # Bird scale: stretch on the way up and down, the landing squash at the new contact, back to 1 by frame 134
    def scale(prop, up, down, squash):
        rows = [key(0, 1.0), key(70, 1.0, "sine.inOut"), key(80, up, "sine.inOut"), key(90, 1.0), key(100, 1.0, "sine.inOut"),
                key(113, down, "power2.out"), key(118, squash, "back.out"), key(134, 1.0), key(270, 1.0)]
        p, e = pt.block("Start", bird, prop)
        head, _ = pt.entries(p, e)
        pt.write_entries(p, e, head, rows)
    scale("scaleX", 0.97, 0.97, 1.12)
    scale("scaleY", 1.06, 1.05, 0.84)
    pt.path.write_text(pt.text)
    print("wrote", pt.path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
