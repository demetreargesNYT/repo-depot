"""Chapter 4, Connections flip: the moving faces keep square corners through the turn (Demetre, 2026-11-04).

    python3 chapters/ch3/scripts/ch3_c4_connections_corners.py --write [--scene PATH]      once, on a scene with the Connections flip

The eight flip faces (Connections Tile 1 to 4, Old and New) were rounded rectangles on the outer corners; squeezing one on scaleY
squashed its corner radius, so a thinning face showed a rounded, oval end mid-flip. Now every face is a plain rectangle with square
corners, and one hidden shape, "Connections Corner Clip" (the top row's outline, inset half a stroke, top corners rounded like the
bar), clips them all: the faces' corners stay square while they turn and the bar's own outline shows through where it curves.
At rest a face covers exactly what the rounded one did.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ch3_c4_city import scene_path
from rml_edit import Doc, num

XS = [-38.2355, -24.4855, -9.4855, 5.5145, 23.0145]      # the top row's tile edges, in the bar's coordinates (as in ch3_c4_city_connections.py)
TOP, BOTTOM, RAD, INSET = -16.25, -1.25, 6.78, 0.75
CLIP_NAME = "Connections Corner Clip"


def main():
    path = scene_path()
    assert CLIP_NAME not in path.read_text(), f"{CLIP_NAME} is already in {path}"
    doc = Doc(path)
    first = next(i for i, l in enumerate(doc.lines) if 'name="Connections Tile 1 Old"' in l)
    clip, fill, color, rect = (doc.new_id() for _ in range(4))
    a, b = XS[0] + INSET, XS[4] - INSET
    top = TOP + INSET
    pad = " " * 28
    lines = [f'{pad}<Shape x="{num((a + b) / 2)}" y="{num(top)}" opacity="0" name="{CLIP_NAME}" id="{clip}">',
             f'{pad}    <Rectangle linkCornerRadius="false" cornerRadiusTL="{num(RAD - INSET)}" cornerRadiusTR="{num(RAD - INSET)}" originY="0" '
             f'width="{num(b - a)}" height="{num(BOTTOM - top)}" id="{rect}"/>',
             f'{pad}    <Fill id="{fill}">', f'{pad}        <SolidColor colorValue="FF000000" id="{color}"/>', f'{pad}    </Fill>', f'{pad}</Shape>']
    doc.lines[first:first] = lines
    done = 0
    for i, l in enumerate(doc.lines):
        m = re.search(r'name="Connections Tile (\d) (Old|New)"', l)
        if not m:
            continue
        j = doc.end(i)
        for k in range(i, j + 1):
            if "<Rectangle" in doc.lines[k]:
                doc.lines[k] = re.sub(r' linkCornerRadius="false"| cornerRadiusT[LR]="[^"]*"', "", doc.lines[k])
            if "<ClippingShape" in doc.lines[k]:
                doc.lines[k] = re.sub(r'sourceId="[^"]*" name="Floor Clip"', f'sourceId="{clip}" name="Corner Clip"', doc.lines[k])
        done += 1
    assert done == 8, done
    doc.save()
    print(f"wrote {path}: 8 faces square-cornered, clipped by {CLIP_NAME}")


if __name__ == "__main__":
    if "--write" not in sys.argv:
        raise SystemExit(__doc__)
    main()
