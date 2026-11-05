"""Chapter 3 pin 2 (Demetre, 2026-11-05): the flash of a ball at frame 342 of the 416 frame loop (5.70 s).

    python3 chapters/ch3/scripts/ch3_ball_return_hold.py [--write]

While the ball is out of sight (frames 265 to 341) it sits by the box at x 1030; at frame 342 its keys put it back in the picture
at x 596. Those two keys are one frame apart and linear, so any render between frames (a 120 Hz screen, the Finesse panel's
sub-frame clock) draws the ball streaking across the stage for an instant. Every ball key at frame 341 becomes a hold, so the
jump happens exactly on frame 342, while the ball is behind the gifts.
"""
import re
import sys
from pathlib import Path

SCENE = Path(__file__).resolve().parents[1] / "scene.rml"
lines = SCENE.read_text().split("\n")
start = next(i for i, l in enumerate(lines) if 'name="Chapter 3 Loop"' in l and "<LinearAnimation" in l)
end = next(i for i in range(start, len(lines)) if "</LinearAnimation>" in lines[i])
BALL = {"9:41640", "9:41641", "9:41642", "9:41643", "9:41644"}
changed = []
obj = None
for i in range(start, end):
    m = re.search(r'<KeyedObject objectId="([^"]+)"', lines[i])
    if m:
        obj = m.group(1)
    if obj in BALL and "<KeyFrameDouble" in lines[i] and 'frame="341"' in lines[i]:
        changed.append(i)
        if "--write" in sys.argv:
            assert 'interpolationType="linear"' in lines[i], lines[i]
            lines[i] = lines[i].replace('interpolationType="linear"', 'interpolationType="hold"')
print(len(changed), "keys")
if "--write" in sys.argv:
    SCENE.write_text("\n".join(lines))
