"""Chapter 4, card 1: the Crossword tower builds itself, row by row, like a grid being solved (Demetre, 2026-11-04).

    python3 chapters/ch3/scripts/ch3_c4_build_tower.py --write [--scene PATH]      once; refuses if the layer is already there

Pieces: every square (one Shape, 12.5 units, dark 1F1F1F or light DFDBD7) that shows above the floor line, in Crossword_F (9:4620, the
hidden copy, node opacity 0) and Crossword_B (9:7705). Both copies get the same keys, frame for frame (matched by absolute x, y within 0.3).
Build: rows rise from the base; a row starts 4 frames after the one below it, and each square starts 0 to 6 frames after the row's
start (a seeded shuffle, the same in both copies). First square at frame 66; each square fades in over 6 frames while dropping 16 to 28
units into place with one small overshoot (back.out.small, 22 frames). Loop and calm: no motion (one flat track).
"""
import random
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ch3_c4_city import add_building, scene_path        # noqa: E402  (also adds the extra eases)
from rml_edit import Doc                                # noqa: E402

NAME = "Tower"
TOWERS = {"F": "9:4620", "B": "9:7705"}
START, ROW_STEP, JITTER, SETTLE, FADE = 66, 4, 6, 22, 6
BASE_Y = 705.0          # absolute y of row 0's centre (its bottom edge sits on the floor line 712)
STEP = 12.5
SHOWS_UNTIL = 718.0     # centre y; the squares below this are under the floor


def squares(root):
    """{letter: {(abs x, abs y): (shape id, local y)}} for the squares that show above the floor."""
    out = {}
    for letter, tid in TOWERS.items():
        tower = next(e for e in root.iter("Node") if e.get("id") == tid)
        d = {}

        def walk(n, ax, ay):
            for c in n:
                if c.tag == "Node":
                    walk(c, ax + float(c.get("x", 0)), ay + float(c.get("y", 0)))
                elif c.tag == "Shape":
                    x, y = ax + float(c.get("x", 0)), ay + float(c.get("y", 0))
                    if y <= SHOWS_UNTIL:
                        assert (round(x, 2), round(y, 2)) not in d, "two squares on one spot"
                        d[(round(x, 2), round(y, 2))] = (c.get("id"), float(c.get("y", 0)))
        walk(tower, float(tower.get("x", 0)), float(tower.get("y", 0)))
        out[letter] = d
    # the copies differ by 0.25 units on 6 squares of the top block: pair each B square with the F square within 0.3
    paired = {}
    for pos, v in out["B"].items():
        near = [q for q in out["F"] if abs(q[0] - pos[0]) < 0.3 and abs(q[1] - pos[1]) < 0.3]
        assert len(near) == 1, pos
        paired[pos] = out["F"][near[0]]
    assert len(paired) == len(out["F"]), "the two copies have different squares"
    out["F"] = paired
    return out


def main():
    path = scene_path()
    assert f"Chapter 4 City {NAME}" not in Path(path).read_text(), "the Tower layer is already in this scene"
    sq = squares(ET.parse(path).getroot())
    rng = random.Random(4620)
    build, first, last = {}, 999, 0
    for pos in sorted(sq["B"], key=lambda p: (-p[1], p[0])):
        row = round((BASE_Y - pos[1]) / STEP)
        s = START + (row + 1) * ROW_STEP + rng.randint(0, JITTER)
        drop = rng.randint(16, 28)
        first, last = min(first, s), max(last, s + SETTLE)
        for letter in TOWERS:
            oid, y = sq[letter][pos]
            build[(oid, "y")] = [(0, y - drop, "hold"), (s, y - drop, "back.out.small"), (s + SETTLE, y, "hold"), (192, y, "hold")]
            build[(oid, "opacity")] = [(0, 0, "hold"), (s, 0, "power1.out"), (s + FADE, 1, "hold"), (192, 1, "hold")]
    assert last <= 190, last
    some = sq["B"][min(sq["B"])][0]
    tracks = {"build": build, "loop": {(some, "opacity"): [(0, 1, "hold"), (600, 1, "hold")]}}
    doc = Doc(path)
    add_building(doc, NAME, tracks)
    doc.save()
    print(f"wrote {path}: {len(sq['B'])} squares x 2 copies, first visible frame {first}, last settle {last}, {len(build)} build tracks")


if __name__ == "__main__":
    if "--write" not in sys.argv:
        raise SystemExit(__doc__)
    main()
