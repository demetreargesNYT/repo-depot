"""Chapter 4, card 1: the Crossword tower's squares flip like windows lighting at dusk (Demetre, 2026-11-04).

    python3 chapters/ch3/scripts/ch3_c4_city_tower.py --write [--scene PATH]      once; refuses if the layer is already there

The tower is Crossword_F + Crossword_B (ids 9:4620 / 9:7705): a crossword grid, black squares and light grey squares, drawn as three
stacked blocks (8 x 25 squares, of which 16 rows show above the floor line; 5 x 3; 2 x 3), 12.5 units per square, one Shape each.
Crossword_F is the draw-order copy the Intro shows (opacity 1 until frame 142, in front of Coss; the Wake runs under it), so every
flip is built on both copies and keyed the same, frame for frame.

A flip is the quarter cube turn done in 2D, inside one square: the square keeps its face (the Shape already there) and gets a second
face of the other colour (a copy placed on top of it, folded away at rest: scale 0, opacity 0). Over 15 frames (0.25 s) the old face
narrows towards the square's left edge while the new face widens from the right edge, both with the same power2.inOut, so their widths
always add up to the square: the outline never changes. Strokes stay 1.5 (transformAffectsStroke false on every stroke touched) and a
folded face is hidden (opacity 0), switching while it is zero wide.

Loop (600 frames), flips travel as a ripple, 2 to 3 frames between neighbours (round(2.5 x diagonal steps)):
- wave 1, 0.9 s (frame 54): 12 black squares of the left columns light up (turn light), rising from the base to the right;
  they stay lit.
- wave 2, 6.3 s (frame 378): the same 12 turn black again, the ripple running the other way (from the right, upward and left), and 4
  light squares of the right columns blink dark and back (flip, 8 frames, flip). The loop is back on its first pattern by 7.2 s.
Wake: 6 of the base squares blink (flip, hold, flip back), a ripple from the base, from frame 118. Calm: the same 6 blink once,
slower to settle (20 frame hold) at 1.0 s.
"""
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ch3_c4_city import LOOP, WAKE, WAKE_AT, add_building, scene_path   # noqa: E402  (also adds the extra eases)
from rml_edit import Doc, num                                           # noqa: E402

NAME = "Tower"
TOWERS = {"F": "9:4620", "B": "9:7705"}
DARK, LIGHT = "FF1F1F1F", "FFDFDBD7"
HALF, STEP = 6.25, 12.5
FLIP, EASE = 15, "power2.inOut"
MAIN_X = [-43.75 + STEP * i for i in range(8)]       # column 0..7, left to right (inside the tower's first block)
BASE_Y = 37.5                                        # row 0: the last row whole above the floor line (its edge at 712)
GAP = 8                                              # frames a blinking square stays flipped

# (column, row up from the base): black squares of the left columns, wave 1 lights them and wave 2 puts them out
W1 = [(2, 0), (3, 0), (0, 1), (3, 2), (1, 3), (2, 4), (1, 5), (3, 6), (2, 7), (0, 9), (2, 10), (0, 12)]
BLINK = [(7, 0), (5, 2), (4, 5), (7, 7)]             # light squares of the right columns that blink in wave 2
WAKE_CELLS = [(2, 0), (3, 0), (0, 1), (3, 2), (1, 3), (2, 4)]
WAVE1, WAVE2 = 54, 378


def delay(steps):
    return int(round(2.5 * steps))


def schedule_loop():
    s = {}
    for c, r in W1:
        s[(c, r)] = [WAVE1 + delay(r + c), WAVE2 + delay(r + (3 - c))]
    for c, r in BLINK:
        t = WAVE2 + delay(r + (7 - c))
        s[(c, r)] = [t, t + FLIP + GAP]
    return s


def schedule_wake():
    return {(c, r): [WAKE_AT[NAME] + delay(r + c), WAKE_AT[NAME] + delay(r + c) + FLIP + GAP] for c, r in WAKE_CELLS}


def schedule_calm():
    return {(c, r): [60 + delay(r + c), 60 + delay(r + c) + FLIP + 20] for c, r in WAKE_CELLS}


def cell_xy(c, r):
    return MAIN_X[c], BASE_Y - STEP * r


def find_cells(root):
    """{(column, row): {tower letter: (shape id, fill colour)}} for every square the schedules use."""
    wanted = {cell_xy(c, r): (c, r) for c, r in set(W1) | set(BLINK)}
    out = {}
    for letter, tid in TOWERS.items():
        tower = next(e for e in root.iter("Node") if e.get("id") == tid)
        inner = tower[0]
        assert float(inner.get("x")) == 50.75 and float(inner.get("y")) == 232.0, "the tower's first block moved"
        for s in inner:
            key = (float(s.get("x", 0)), float(s.get("y", 0)))
            if s.tag == "Shape" and key in wanted:
                fill = s.find("Fill").find("SolidColor").get("colorValue")
                out.setdefault(wanted[key], {})[letter] = (s.get("id"), fill)
    for cell in wanted.values():
        assert set(out[cell]) == set(TOWERS), f"square {cell} not found in both copies"
    return out


def make_face(doc, a_id, cx, other_fill):
    """Strokes of the existing face become non-scaling; returns the id of a copy of it on top with the other colour, folded away."""
    i = doc.idx(a_id)
    j = doc.end(i)
    for k in range(i, j + 1):
        if "<Stroke thickness=\"1.5\"" in doc.lines[k] and "transformAffectsStroke" not in doc.lines[k]:
            doc.lines[k] = doc.lines[k].replace('join="round" id=', 'join="round" transformAffectsStroke="false" id=')
    block = list(doc.lines[i:j + 1])
    b_id = doc.new_id()
    block[0] = re.sub(r'\bid="[^"]+"', f'id="{b_id}"', block[0], count=1)
    for k in range(1, len(block)):
        block[k] = re.sub(r'\bid="[^"]+"', lambda m: f'id="{doc.new_id()}"', block[k])
    head = block[0]
    head = re.sub(r'\bx="[^"]*"', "", head, count=1) if re.search(r'<Shape\s+x=', head) else head
    head = head.replace("<Shape ", f'<Shape x="{num(cx + HALF)}" scaleX="0" opacity="0" ', 1)
    block[0] = re.sub(r"\s+", " ", head.strip()).join([" " * (len(doc.lines[i]) - len(doc.lines[i].lstrip())), ""])
    fill_at = next(k for k, l in enumerate(block) if "<SolidColor" in l)          # the Fill's colour comes first
    block[fill_at] = re.sub(r'colorValue="[0-9A-Fa-f]{8}"', f'colorValue="{other_fill}"', block[fill_at])
    doc.lines[i:i] = block
    return b_id


def face_keys(starts, cx, end):
    """Keys of both faces of one square for one animation: {'A': {prop: keys}, 'B': {...}} (A is the face drawn at rest)."""
    k = {"A": {"scaleX": [(0, 1, "hold")], "x": [(0, cx, "hold")], "opacity": [(0, 1, "hold")]},
         "B": {"scaleX": [(0, 0, "hold")], "x": [(0, cx + HALF, "hold")], "opacity": [(0, 0, "hold")]}}
    cur, last = "A", -99
    for s in starts:
        assert s >= last + 2 and s + FLIP + 1 < end, (s, last, end)
        out, inn = cur, "B" if cur == "A" else "A"
        # the face that leaves narrows towards the left edge, the one that arrives widens from the right edge
        k[out]["scaleX"] += [(s, 1, EASE), (s + FLIP, 0, "hold")]
        k[out]["x"] += [(s, cx, EASE), (s + FLIP, cx - HALF, "hold"), (s + FLIP + 1, cx + HALF, "hold")]
        k[out]["opacity"] += [(s + FLIP, 0, "hold")]
        k[inn]["scaleX"] += [(s, 0, EASE), (s + FLIP, 1, "hold")]
        k[inn]["x"] += [(s, cx + HALF, EASE), (s + FLIP, cx, "hold")]
        k[inn]["opacity"] += [(s, 1, "hold")]
        cur, last = inn, s + FLIP + 1
    assert cur == "A", "every square must end on its starting face"
    for face in k.values():
        for prop, keys in face.items():
            assert keys[-1][0] < end
            keys.append((end, keys[0][1], "hold"))
    return k


def main():
    path = scene_path()
    text = Path(path).read_text()
    assert f"Chapter 4 City {NAME}" not in text, "the Tower layer is already in this scene"
    root = ET.parse(path).getroot()
    cells = find_cells(root)
    doc = Doc(path)
    faces = {}                               # (cell, letter) -> (A id, B id, cx)
    for cell in sorted(cells):
        cx = cell_xy(*cell)[0]
        for letter, (a_id, fill) in cells[cell].items():
            b_id = make_face(doc, a_id, cx, LIGHT if fill == DARK else DARK)
            faces[(cell, letter)] = (a_id, b_id, cx)
    tracks = {"loop": {}, "calm": {}, "wake": {}}
    for group, sched, end in (("loop", schedule_loop(), LOOP), ("calm", schedule_calm(), LOOP), ("wake", schedule_wake(), WAKE)):
        for cell, starts in sched.items():
            for letter in TOWERS:
                a_id, b_id, cx = faces[(cell, letter)]
                keys = face_keys(starts, cx, end)
                for face, oid in (("A", a_id), ("B", b_id)):
                    for prop, ks in keys[face].items():
                        tracks[group][(oid, prop)] = ks
    add_building(doc, NAME, tracks)
    doc.save()
    print(f"wrote {path}: {len(cells)} squares flip in both copies ({len(faces)} new faces), "
          f"{len(tracks['loop'])} loop tracks, {len(tracks['calm'])} calm, {len(tracks['wake'])} wake")


if __name__ == "__main__":
    if "--write" not in sys.argv:
        raise SystemExit(__doc__)
    main()
