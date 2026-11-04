"""Chapter 4, card 1: the Connections building (the four stacked coloured bars) comes alive (Demetre, 2026-11-04).

    python3 chapters/ch3/scripts/ch3_c4_city_connections.py --write [--scene PATH]      once, on a scene without the layer

The building, bottom to top: blue bar (9:4223), purple bar (9:4292), yellow-green bar (9:4134), olive-green bar (9:4351) with a
green end cap. Each bar is a group of tile lines and rounded rectangles; behind the yellow-green and the purple bar sit their
backing rectangles (9:4397 yellow, 9:4403 dark), which travel with their bar.
Once a loop (6.6 s of the 10 s):
- shuffle 2.6 to 4.0 s: the yellow-green row slides 12 px left and the purple row 12 px right (the explicit exception to the 6 px
  rule: left and right are where the room is free, the tower to the right and the crossword to the left are never touched), a
  small settle, a hold of 0.4 s, then both slide back and lock in with one small bump (a 1.4 px overshoot, then still);
- flip 4.2 to 5.2 s: the olive bar's top row of four tiles turns one quarter turn at a time, left to right, 0.15 s apart, olive to
  a darker green: the old face squeezes up toward its top edge while the new face grows from the bottom edge (two faces that always
  share the cell, no strokes on them, the bar's own grid lines stay on top);
- flip back 8.4 to 9.4 s: the same four tiles turn back, in the same order.
Calm (card 2): slide 6 px, shorter hold, flips on the first three tiles only. Wake (the room's first visit): the first tile flips
over and back inside the Wake, from frame 130 (2.17 s) to 182.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ch3_c4_city import LOOP, WAKE, WAKE_AT, add_building, scene_path
from rml_edit import Doc, num

ROW2, ROW2_BACK, ROW3, ROW3_BACK = "9:4134", "9:4397", "9:4292", "9:4403"
BAR, BAR_RECT = "9:4351", "9:4376"
LAYER = "Chapter 4 City Connections"
OLIVE, DARK = "FFA0C35A", "FF6E9A2E"
# the top row of the olive bar, in the bar's own coordinates: tile edges, row top and bottom (the grid line at y -1.25)
XS = [-38.2355, -24.4855, -9.4855, 5.5145, 23.0145]
TOP, BOTTOM, RAD, INSET = -16.25, -1.25, 6.78, 0.75      # perimeter edges are inset by half a stroke so the bar's outline stays whole
FLIP = 18                                                 # frames for one tile to turn
STAGGER = 9                                               # frames between tiles (0.15 s)
SLIDE = 12.0
OVER = 1.4                                                # the bump when the rows lock in, px


def track(rest, beats, end):
    """Keys from 0 to `end`: beats are (frame, value, how) in order; the track starts and ends on rest."""
    keys = [(0, rest, "hold")] + [b for b in beats if 0 < b[0] < end]
    if keys[-1][0] != end:
        keys.append((end, rest, "hold"))
    return keys


def slide_beats(rest, amount, t0, hold, flipped=False):
    """x of a row: out (power2.inOut) with a tiny settle, hold, back with one bump that lands on rest at t0 + 84 (shuffle 1.4 s)."""
    out_end, back = t0 + 26, t0 + 26 + 6 + hold
    return [(t0, rest, "power2.inOut"), (out_end, rest + amount * 1.07, "sine.inOut"), (out_end + 6, rest + amount, "hold"),
            (back, rest + amount, "power2.inOut"), (back + 21, rest - amount * OVER / SLIDE, "sine.inOut"), (back + 28, rest, "hold")]


def flip_pairs(t, forward, speed=1.0):
    """The old (olive) and new (dark) face keys of one tile for a turn starting at frame t: (old scaleY, old opacity, new scaleY, new opacity)."""
    f = FLIP
    if forward:
        return ([(t, 1, "power2.inOut"), (t + f, 0, "hold")], [(t, 1, "hold"), (t + f, 0, "hold")],
                [(t, 0, "power2.inOut"), (t + f, 1.05, "sine.inOut"), (t + f + 6, 1, "hold")], [(t, 0, "hold"), (t + 1, 1, "hold")])
    # back: the new (dark) face squeezes toward its bottom edge, the old (olive) face grows from the top edge
    return ([(t, 0, "power2.inOut"), (t + f, 1.05, "sine.inOut"), (t + f + 6, 1, "hold")], [(t, 0, "hold"), (t + 1, 1, "hold")],
            [(t, 1, "power2.inOut"), (t + f, 0, "hold")], [(t, 1, "hold"), (t + f, 0, "hold")])


def tile_tracks(tile, starts_fwd, starts_back, end, rest_old=(1, 1), rest_new=(0, 0)):
    """Keys for one tile's four properties. Between the two turns the tile is flipped (old 0/0, new 1/1)."""
    old_s, old_o, new_s, new_o = [], [], [], []
    if starts_fwd is not None:
        a = flip_pairs(starts_fwd, True)
        old_s += a[0]; old_o += a[1]; new_s += a[2]; new_o += a[3]
    if starts_back is not None:
        b = flip_pairs(starts_back, False)
        old_s += b[0]; old_o += b[1]; new_s += b[2]; new_o += b[3]
    out = []
    for (rest, beats) in ((1, old_s), (1, old_o), (0, new_s), (0, new_o)):
        # beats list starts a turn on the value the previous one ended on (hold keys carry it)
        out.append(track(rest, beats, end))
    return out


def tile_xml(doc, i):
    """Two new shapes for tile i of the top row; returns (xml lines, old id, new id)."""
    x0, x1 = XS[i], XS[i + 1]
    left_edge, right_edge = i == 0, i == 3
    a, b = x0 + (INSET if left_edge else 0), x1 - (INSET if right_edge else 0)
    top = TOP + INSET
    w, h = b - a, BOTTOM - top
    pad = " " * 28
    ids = {k: doc.new_id() for k in ("old", "oldr", "oldf", "oldc", "oldfc", "new", "newr", "newf", "newc", "newfc")}
    tl = RAD - INSET if left_edge else 0
    tr = RAD - INSET if right_edge else 0
    lines = []
    for kind, oy, op, sy in (("old", 0, 1, 1), ("new", 1, 0, 0)):
        y = top if kind == "old" else BOTTOM
        col = OLIVE if kind == "old" else DARK
        attrs = f' x="{num((a + b) / 2)}" y="{num(y)}"'
        if kind == "new":
            attrs += ' scaleY="0" opacity="0"'
        # the new face's top corners are rounded like the old one's so it ends as a whole tile
        lines += [f'{pad}<Shape{attrs} name="Connections Tile {i + 1} {kind.capitalize()}" id="{ids[kind]}">',
                  f'{pad}    <Rectangle linkCornerRadius="false" cornerRadiusTL="{num(tl)}" cornerRadiusTR="{num(tr)}" '
                  f'originY="{oy}" width="{num(w)}" height="{num(h)}" id="{ids[kind + "r"]}"/>',
                  f'{pad}    <Fill id="{ids[kind + "f"]}">', f'{pad}        <SolidColor colorValue="{col}" id="{ids[kind + "c"]}"/>',
                  f'{pad}    </Fill>',
                  f'{pad}    <ClippingShape sourceId="9:20855" name="Floor Clip" id="{ids[kind + "fc"]}"/>', f'{pad}</Shape>']
    return lines, ids["old"], ids["new"]


def main():
    path = scene_path()
    text = path.read_text()
    assert LAYER not in text, f"{LAYER} is already in {path}"
    doc = Doc(path)
    shapes, tiles = [], []
    for i in range(4):
        xml, old, new = tile_xml(doc, i)
        shapes += xml
        tiles.append((old, new))
    at = doc.idx(BAR_RECT)
    doc.lines[at:at] = shapes

    rest = {ROW2: 90.75, ROW2_BACK: 98.25, ROW3: 68.875, ROW3_BACK: 70.75}
    full = {"loop": {}, "calm": {}, "wake": {}}
    # row 2 starts at frame 156 (2.6 s), row 3 four frames later with a hold four frames shorter, so both lock in at frame 240 (4.0 s)
    for label, amount, hold in (("loop", SLIDE, 24), ("calm", SLIDE / 2, 16)):
        for oid, sign, t0, h in ((ROW2, -1, 156, hold), (ROW2_BACK, -1, 156, hold), (ROW3, 1, 160, hold - 4), (ROW3_BACK, 1, 160, hold - 4)):
            full[label][(oid, "x")] = track(rest[oid], slide_beats(rest[oid], sign * amount, t0, h), LOOP)
    for k, (old, new) in enumerate(tiles):
        for label, count in (("loop", 4), ("calm", 3)):
            go = 252 + k * STAGGER if k < count else None
            back = 504 + k * 11 if k < count else None
            for prop, kk, face in zip(("scaleY", "opacity", "scaleY", "opacity"), tile_tracks(k, go, back, LOOP), (old, old, new, new)):
                full[label][(face, prop)] = kk
        if k == 0:        # the wake: the first tile turns over at frame 130 and back at 158
            for prop, kk, face in zip(("scaleY", "opacity", "scaleY", "opacity"), tile_tracks(0, 130, 158, WAKE), (old, old, new, new)):
                full["wake"][(face, prop)] = kk
    assert WAKE_AT["Connections"] <= 130 and 158 + FLIP + 6 < WAKE
    add_building(doc, "Connections", full)
    doc.save()
    print(f"wrote {path}")


if __name__ == "__main__":
    if "--write" not in sys.argv:
        raise SystemExit(__doc__)
    main()
