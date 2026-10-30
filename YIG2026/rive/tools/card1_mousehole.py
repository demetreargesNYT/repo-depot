"""One time (2026-10-30, history like card1_refine.py): Chapter 1 card 1's mouse hole gets its red interior back, and the mouse
runs in front of the hole and into it, as in the old YIG Test file (Rive file 2666044, .cache/yig-test/).

    python3 tools/card1_mousehole.py            dry run
    python3 tools/card1_mousehole.py --write

The old file's hole is two parts: a dark arch with a stroke, and a red circle (24 px, FF5959, stroked) drawn over it and clipped
to the arch, so the hole reads as having depth. The mouse is drawn above both and clipped at the arch's right edge, so it
comes out of the hole and goes back in. Here the mask (Chapter 1 Card 1 Mouse Hole Clip, edge at the arch's right edge) was
already right, but the hole was drawn above the mouse and had no red, so the mouse looked as if it ran behind a flat shape.
The circle sits where the old file had it relative to the arch: 7.655 right and 7.355 below the arch's centre.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from import_room import Ids, fnum  # noqa: E402
from rml_read import chapter_dir  # noqa: E402
from xml_fragments import parse, ser  # noqa: E402

OFFSET = (7.655, 7.355)


def main(argv):
    path = chapter_dir("ch1") / "scene.rml"
    text = path.read_text()
    if "Mouse Hole Interior" in text:
        raise SystemExit("already done")
    root = parse(text)
    ids = Ids(text)
    by_id = {e.get("id"): e for e in root.iter() if e.get("id")}
    hole = next(e for e in root.iter("Node") if e.get("name") == "Mouse Hole" and e.get("id") == "9:4782")
    arch = by_id["9:4794"]
    plane = next(e for e in root.iter("Node") if e.get("name") == "Chapter 1 Card 1 Front Plane")
    mouse = next(c for c in plane if c.get("name") == "Chapter 1 Card 1 Mouse")
    x, y = float(arch.get("x", 0)) + OFFSET[0], float(arch.get("y", 0)) + OFFSET[1]
    red = parse(
        f'<Node x="{fnum(x)}" y="{fnum(y)}" name="Mouse Hole Interior" id="{ids()}">'
        f'<Shape id="{ids()}"><Ellipse width="24.04" height="24.04" id="{ids()}"/>'
        f'<Fill id="{ids()}"><SolidColor colorValue="FFFF5959" id="{ids()}"/></Fill>'
        f'<Stroke thickness="1.5" cap="round" join="round" id="{ids()}"><SolidColor colorValue="FF1F1F1F" id="{ids()}"/></Stroke></Shape>'
        f'<ClippingShape sourceId="{arch.get("id")}" name="Hole Arch Clip" id="{ids()}"/></Node>')
    hole.insert(0, red)                                         # first child draws on top: the red circle over the dark arch
    plane.remove(mouse)
    plane.insert(list(plane).index(hole), mouse)                # the mouse in front of the hole, as in the old file
    if "--write" in argv:
        path.write_text(ser(root))
        print("wrote", path)
    else:
        print("dry run: would add the interior at", (round(x, 3), round(y, 3)), "and move the mouse in front of the hole")


if __name__ == "__main__":
    main(sys.argv[1:])
