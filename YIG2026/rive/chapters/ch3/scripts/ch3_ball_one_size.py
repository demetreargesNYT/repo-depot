"""Chapter 3 pin 1 (Demetre, 2026-11-05): once the ball jumps out of the picture it stays one size for the rest of the loop.

    python3 chapters/ch3/scripts/ch3_ball_one_size.py [--write]

The illustrator scaled the ball from 0.92 up to 2.05 and back as it travelled (a depth cue). In "Chapter 3 Loop" the Ball_01
scaleX/scaleY keys now keep the squash and stretch (the ratio sx:sy) but hold the overall size (sqrt(sx*sy)) at 0.9182, the size the
intro ends on and the loop starts and ends on. The ball coming back into view (frames 342 on) still grows from 0.7, and stops at 0.9182.
Run once; it asserts on a second run.
"""
import math
import re
import sys
from pathlib import Path

SCENE = Path(__file__).resolve().parents[1] / "scene.rml"
B = 0.9182
lines = SCENE.read_text().split("\n")

start = next(i for i, l in enumerate(lines) if 'name="Chapter 3 Loop"' in l and "<LinearAnimation" in l)
end = next(i for i in range(start, len(lines)) if "</LinearAnimation>" in lines[i])
ko = next(i for i in range(start, end) if 'objectId="9:41641"' in lines[i] and "<KeyedObject" in lines[i])
ko_end = next(i for i in range(ko, end) if "</KeyedObject>" in lines[i])

keys = {"scaleX": {}, "scaleY": {}}
cur = None
for i in range(ko, ko_end):
    m = re.search(r'<KeyedProperty property="(\w+)"', lines[i])
    if m:
        cur = m.group(1)
    m = re.search(r'<KeyFrameDouble value="([^"]+)"', lines[i])
    if m and cur in keys:
        f = re.search(r'frame="(\d+)"', lines[i])
        keys[cur][int(f.group(1)) if f else 0] = (i, float(m.group(1)))

assert keys["scaleX"].keys() == keys["scaleY"].keys()
out = {}
for f in sorted(keys["scaleX"]):
    (ix, sx), (iy, sy) = keys["scaleX"][f], keys["scaleY"][f]
    g = math.sqrt(sx * sy)
    gn = B if f < 342 else min(g, B)
    k = gn / g
    out[ix] = (sx * k, f)
    out[iy] = (sy * k, f)

if "--write" not in sys.argv:
    for f in (0, 8, 40, 64, 100, 184, 224, 264, 341, 342, 360, 380, 408, 416):
        if f in keys["scaleX"]:
            print(f, round(keys["scaleX"][f][1], 3), round(keys["scaleY"][f][1], 3), "->", round(out[keys["scaleX"][f][0]][0], 3), round(out[keys["scaleY"][f][0]][0], 3))
    sys.exit()

assert abs(keys["scaleX"][40][1] - 1.4107) < 1e-3, "already applied"
for i, (v, f) in out.items():
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    lines[i] = re.sub(r'value="[^"]+"', f'value="{s}"', lines[i], count=1)
SCENE.write_text("\n".join(lines))
print("written")
