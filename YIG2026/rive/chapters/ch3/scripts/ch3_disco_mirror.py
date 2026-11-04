"""Chapter 3: the disco ball's swing and contact sparkle mirrored for c3s1's hit on its upper right (Demetre, 2026-11-03).

    python3 chapters/ch3/scripts/ch3_disco_mirror.py --write      once, on the scene as committed in 840880e

The swing's values change sign (it leans left, away from a hit on the right); Sparkle 5 moves to the mirror of its spot, the upper
right of the ball where the ball strikes (x 35.5, 27.7 above the centre), with its turn mirrored. Nothing else changes.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
from rml_edit import Doc, bake, num
from rml_read import Scene, chapter_dir
from rooms_sheet import Sheet

SCENE = chapter_dir("ch3") / "scene.rml"
SWING, LOOP = "9:2", "Chapter 3 Loop"


def main():
    sc = Scene(SCENE)
    k = Sheet(sc).anim_keys(sc.animations[LOOP])[SWING]["rotation"]
    n = sc.duration(sc.animations[LOOP])
    doc = Doc(SCENE)
    doc.set_prop(LOOP, SWING, "rotation", bake({f: -k.at(f) for f in range(n + 1)}, range(n + 1)))
    i = next(i for i, l in enumerate(doc.lines) if 'name="Chapter 3 Sparkle 5"' in l)
    line = doc.lines[i]
    x = float(re.search(r' x="([^"]+)"', line).group(1))
    rot = float(re.search(r' rotation="([^"]+)"', line).group(1))
    assert x < 0, line
    line = re.sub(r' x="[^"]+"', f' x="{num(-x)}"', line, count=1)
    doc.lines[i] = re.sub(r' rotation="[^"]+"', f' rotation="{num(-rot)}"', line, count=1)
    doc.save()
    print(f"mirrored the swing ({n + 1} frames) and moved Sparkle 5 to x {-x:g}")


if __name__ == "__main__":
    if "--write" not in sys.argv:
        raise SystemExit(__doc__)
    main()
