"""Write each file's named pieces as a tree, read from the three scene.rml files, as JSON (for the Finesse panel's pin comments).

    python3 tools/room_pieces.py

Keys are the file numbers ("1", "2", "3"). Each value is the artboard's tree of nodes and shapes that the web runtime can find by
name, which needs a name used only once on the artboard: [{"n": name, "c": [children]}]. A node without a usable name (unnamed,
or a name used twice, such as "Ball_01_Scale") is left out and its children take its place, so every name in the tree is one
`artboard.transformComponent(name)` finds. The panel hides one of these at a time and redraws, and the pieces whose hiding
changes the pixels around a pin are the pieces under it (the same test as tools/safe_area.py, in the browser).
"""
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rml_read import Scene, chapter_dir  # noqa: E402

KINDS = ("Node", "Shape")


def tree(element, usable):
    out = []
    for child in element:
        if child.tag not in KINDS:
            continue
        kids = tree(child, usable)
        name = child.get("name")
        if name in usable:
            out.append({"n": name, "c": kids})
        else:
            out.extend(kids)
    return out


def main():
    out = {}
    for file_no, ch in enumerate(("ch1", "ch2", "ch3"), 1):
        scene = Scene(chapter_dir(ch) / "scene.rml")
        counts = collections.Counter(e.get("name") for e in scene.artboard.iter() if e.tag in KINDS and e.get("name"))
        usable = {n for n, c in counts.items() if c == 1}
        out[str(file_no)] = tree(scene.artboard, usable)
    print(json.dumps(out, separators=(",", ":")))


if __name__ == "__main__":
    main()
