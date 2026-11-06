"""Chapter 4 finesse notes 3 and 4 (Demetre, 2026-11-06).

    python3 chapters/ch3/scripts/ch3_c4_notes_3_4.py [--scene PATH] [--write]

Note 3: in each of the two hexagon plate stacks of SpB_02 (the stack of plates with the small spinning hexes, and the one beside it) a larger
        ring (the 22.9 unit one) does the same flat coin spin as the small hex, later in the loop and at a different time from it: the first
        stack's at frame 330 and the other's at frame 440 of the 600 frame loop (the small hexes spin at 186 to 222). Each ring gets a dark
        hollow copy behind it, like the small hexes have, so the flip shows depth. The Calm loop (card 2) spins to 0.5 as its small hexes do.
Note 4: the tower (Crossword_B, the visible copy) swaps a few blocks between white and black through the loop: five moments (frames 40, 140,
        240, 340, 440), three blocks each (two white to black, one black to white), each fading over 12 frames, holding, and fading back
        140 frames later (120 for the last), so the loop closes and at most nine blocks are swapped at once. The Calm loop swaps two blocks per
        moment and fades over 20 frames.
Run once; it asserts on a second run.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rml_edit import Doc  # noqa: E402
from rml_read import chapter_dir  # noqa: E402
from ch3_loop_pauses import put, scene_path  # noqa: E402

LOOP = 600
HEX_ANIMS = ("Chapter 4 City Hex", "Chapter 4 City Hex Calm")
RINGS = {"9:10513": 330, "9:10719": 440}          # the 22.9 unit rings: stack one's plate 2, the second stack's top plate; their spin start
SPIN = 36


def spin_curve(doc, anim, plate="9:66983", start=186):
    """{offset: scaleX} of the small hex's coin spin in `anim` (its window starts at frame `start`)."""
    a, b = doc.anim(anim)
    i, j = doc._object(a, b, plate)
    out = {}
    cur = None
    for l in doc.lines[i:j + 1]:
        m = re.search(r'<KeyedProperty property="(\w+)"', l)
        if m:
            cur = m.group(1)
        m = re.search(r'<KeyFrameDouble value="([^"]+)".*?frame="(\d+)"', l)
        if cur == "scaleX" and m:
            f = int(m.group(2))
            if start <= f <= start + SPIN:
                out[f - start] = float(m.group(1))
    out[0] = out.get(0, 1.0)
    return out


def clone_keyed(doc, anim, src, dst):
    """Copy the KeyedObject of `src` in `anim` (if any) as the KeyedObject of `dst`, with new ids."""
    a, b = doc.anim(anim)
    i = doc._object(a, b, src)
    if i is None:
        return False
    blk = doc.lines[i[0]:i[1] + 1]
    blk = [re.sub(r'\bid="[^"]+"', lambda m: f'id="{doc.new_id()}"', l) for l in blk]
    blk[0] = re.sub(r'objectId="[^"]+"', f'objectId="{dst}"', blk[0])
    doc.lines[b:b] = blk
    return True


def add_ring_spins(doc):
    n = doc.new_id
    curves = {anim: spin_curve(doc, anim) for anim in HEX_ANIMS}
    for ring, start in RINGS.items():
        i = doc.idx(ring)
        j = doc.end(i)
        shape = doc.lines[i:j + 1]
        hollow = [re.sub(r'\bid="[^"]+"', lambda m: f'id="{n()}"', l) for l in shape]
        hid = re.search(r'\bid="([^"]+)"', hollow[0]).group(1)
        hollow[0] = re.sub(r' name="[^"]*"', "", hollow[0]).replace("<Shape", '<Shape name="Hex Ring Hollow"', 1)
        k = next(x for x, l in enumerate(hollow) if "<Fill" in l)
        hollow[k + 1] = re.sub(r'colorValue="[^"]+"', 'colorValue="FF1F1F1F"', hollow[k + 1])
        doc.lines[j + 1:j + 1] = hollow
        for anim in ("Chapter 4 City Hex Rest", "Chapter 4 City Hex Build", "Chapter 4 City Hex", "Chapter 4 City Hex Calm"):
            clone_keyed(doc, anim, ring, hid)
        for anim in HEX_ANIMS:
            c = curves[anim]
            keys = [(0, 1.0, "hold"), (start, 1.0, "linear")]
            keys += [(start + off, v, "linear") for off, v in sorted(c.items()) if off > 0]
            keys += [(start + SPIN + 1, 1.0, "linear"), (LOOP, 1.0, "hold")]
            doc.set_prop(anim, ring, "scaleX", keys)
        doc.set_prop("Chapter 4 City Hex Rest", ring, "scaleX", [(0, 1.0, "hold")])


def add_tower_swaps(doc):
    from xml.etree import ElementTree as ET
    root = ET.parse(doc.path).getroot()
    ids = {e.get("id"): e for e in root.iter() if e.get("id")}
    grid = {}

    def walk(e, ox, oy):
        for c in e:
            if c.tag == "Node":
                walk(c, ox + float(c.get("x", 0)), oy + float(c.get("y", 0)))
            elif c.tag == "Shape":
                f = [x for x in c if x.tag == "Fill"]
                if not f:
                    continue
                sc = next(f[0].iter("SolidColor"))
                grid[(round((ox + float(c.get("x", 0)) - 44.5) / 12.5), round((382 - (oy + float(c.get("y", 0)))) / 12.5))] = (sc.get("colorValue"), sc.get("id"))
    walk(ids["9:7705"], 0, 0)                     # Crossword_B: the visible copy (Crossword_F is hidden)
    used = set()

    def pick(colour, r0, want_col):
        for dr in range(0, 6):
            for dc in range(0, 4):
                for c in ((want_col + dc) % 4 - 1, (want_col - dc) % 4 - 1):
                    for r in (r0 + dr, r0 - dr):
                        cell = grid.get((c, r))
                        if cell and cell[0] == colour and (c, r) not in used and -1 <= c <= 2 and 3 <= r <= 24:
                            used.add((c, r))
                            return (c, r), cell
        raise SystemExit("no cell")
    events = [(40, 140), (140, 140), (240, 140), (340, 140), (440, 120)]
    plan = []
    for i, (e, d) in enumerate(events):
        r0 = 5 + 4 * i
        plan.append((e, d, [pick("FFDFDBD7", r0, i * 2), pick("FF1F1F1F", r0 + 1, i * 2 + 1), pick("FFDFDBD7", r0 + 2, i * 2 + 2)]))
    WHITE, BLACK = "FFDFDBD7", "FF1F1F1F"
    for anim, per_event, fade in (("Chapter 4 City Tower", 3, 12), ("Chapter 4 City Tower Calm", 2, 20)):
        for e, d, chosen in plan:
            for (pos, (col, scid)) in chosen[:per_event]:
                other = BLACK if col == WHITE else WHITE
                keys = [(0, col), (e, col), (e + fade, other), (e + d, other), (e + d + fade, col), (LOOP, col)]
                put(doc, anim, scid, "colorValue", "color", keys, set())
    for e, d, chosen in plan:
        for pos, (col, scid) in chosen:
            put(doc, "Chapter 4 City Tower Rest", scid, "colorValue", "color", [(0, col)], set())
    return plan


def main():
    argv = sys.argv
    path = scene_path(argv)
    doc = Doc(path)
    assert not any('name="Hex Ring Hollow"' in l for l in doc.lines), "already applied"
    add_ring_spins(doc)
    plan = add_tower_swaps(doc)
    print([(e, d, [p for p, _ in ch]) for e, d, ch in plan])
    if "--write" in argv:
        doc.save()
        print("written", path)


if __name__ == "__main__":
    main()
