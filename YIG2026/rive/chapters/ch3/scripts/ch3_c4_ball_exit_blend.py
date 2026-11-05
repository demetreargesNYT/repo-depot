"""Chapter 4 ball: a Back mid roll-in no longer stops the ball dead for a frame (Demetre, 2026-11-04).

    python3 chapters/ch3/scripts/ch3_c4_ball_exit_blend.py --write [--scene PATH]      once, on a scene with the ball's layers

The transitions into "Chapter 4 Ball Leaving" blended for 100 ms; the Leaving animation does not key x or the turn, so the ball's
own x froze when the blend ended, a hard stop from up to 9 units a frame, while the exit wrapper started from rest. The blend now
lasts as long as the exit (1 s): the outgoing Arrive or Idle keeps playing under a fading weight, so the ball's own speed dies away
smoothly from where it is while the wrapper takes it left; its height and squash blend to the floor over the same second.
The Leaving animation shrinks from 62 to 6 frames, so blend plus Leaving (66 frames) still ends just before the exit wrapper is parked
(68 frames): a Next tapped during the exit never shows the ball back on stage before it is hidden.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ch3_c4_city import scene_path
from rml_edit import Doc

BLEND_MS = 1000
LEAVING_FRAMES = 6


def main():
    path = scene_path()
    lines = path.read_text().split("\n")
    layer = next(i for i, l in enumerate(lines) if 'name="Chapter 4 Ball Motion"' in l)
    end = next(i for i in range(layer, len(lines)) if lines[i].strip() == "</StateMachineLayer>")
    leaving = next(re.search(r'id="([^"]+)"', l).group(1) for l in lines[layer:end] if "<AnimationState" in l and
                   re.search(r'animationId="([^"]+)"', l).group(1) == re.search(r'<LinearAnimation[^>]*name="Chapter 4 Ball Leaving" id="([^"]+)"', "\n".join(lines)).group(1))
    changed = 0
    for i in range(layer, end):
        if f'stateToId="{leaving}"' in lines[i] and 'duration="100"' in lines[i]:
            lines[i] = lines[i].replace('duration="100"', f'duration="{BLEND_MS}"')
            changed += 1
    assert changed, "no transition into Leaving with a 100 ms blend"
    path.write_text("\n".join(lines))
    doc = Doc(path)
    doc.set_duration("Chapter 4 Ball Leaving", LEAVING_FRAMES)
    doc.save()
    print(f"wrote {path}: {changed} transitions into Leaving now blend for {BLEND_MS} ms")


if __name__ == "__main__":
    if "--write" not in sys.argv:
        raise SystemExit(__doc__)
    main()
