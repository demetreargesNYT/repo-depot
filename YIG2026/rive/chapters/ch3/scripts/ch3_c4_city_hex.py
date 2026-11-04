"""Chapter 4 card 1, the city: the Spelling Bee hex column (SpB_02_B and its hidden twin SpB_02_F) pulses from the bottom hex up.

    python3 chapters/ch3/scripts/ch3_c4_city_hex.py --write [--scene PATH]       once; without --write it only checks

The column is three visible hexes (a fourth sits under the floor line) of four nested rings each. Colour can't be keyed, so each
ring gets a "Hex Glow" copy (same outline, pale fill, opacity 0 at rest) written just above that ring in the draw order; the
pulse is its opacity going up and back, inner ring first, then the next out, then the outer edge. The whole column (both
columns of hexes in the copy) sits in a "Hex Lift" pivot at (0, 0) whose y gives the tiny lift. SpB_02_F gets the same, in step.
Loop 600 frames: hex 1 (bottom) 276, hex 2 312, hex 3 348 (4.6 s, 5.2 s, 5.8 s; 36 frames of pulse each, rings 6 frames apart),
lift up 366 to 378 and settle 378 to 396 (6.1 to 6.6 s). Wake: the bottom hex once, 148 to 186. Calm: half the glow, 1 px lift.
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ch3_c4_city import LOOP, WAKE, WAKE_AT, add_building, scene_path
from rml_edit import Doc

PAIRS = {"B": ("9:10426", "9:10427", "9:10670"), "F": ("9:7340", "9:7341", "9:7584")}   # building, first child, last child
HEX_Y = [41.25, -41.25, -123.75]                 # bottom to top; the fourth hex (123.75) is under the floor line
RING_W = [10.1555, 22.8755, 35.3755, 47.8755]    # inner ring to outer edge
GLOW = "FFFFFFE6"
PEAK, PEAK_CALM = 0.8, 0.4
HEX_AT, RING_STEP, RISE, FALL = [276, 312, 348], 6, 8, 12
WAKE_START = WAKE_AT["Hex"] + 3
LIFT, LIFT_CALM = (366, 378, 396), 1.0           # start, peak, settled


def find_rings(path):
    """{building: [[shape ids inner..outer] for each hex]}, read from the scene's XML."""
    root = ET.parse(path).getroot()
    out = {}
    for key, (bid, first, last) in PAIRS.items():
        b = next(e for e in root.iter("Node") if e.get("id") == bid)
        left = next(e for e in b.iter("Node") if e.get("id") == first).find("Node")        # the x -15.4 node, the rings
        hexes = []
        for y in HEX_Y:
            shapes = [s for s in left.findall("Shape") if abs(float(s.get("y")) - y) < 1e-3]
            shapes.sort(key=lambda s: max(abs(float(v.get("x") or 0)) for v in s.iter("StraightVertex")))
            widths = [max(abs(float(v.get("x") or 0)) for v in s.iter("StraightVertex")) for s in shapes]
            assert len(shapes) == 4 and all(abs(a - b) < 1e-3 for a, b in zip(widths, RING_W)), (key, y, widths)
            hexes.append([s.get("id") for s in shapes])
        out[key] = hexes
    return out


def pulse(keys, t0, peak):
    """Append one glow pulse starting at t0: 0 -> peak (power2.out) -> 0 (sine.inOut)."""
    keys += [(t0, 0.0, "power2.out"), (t0 + RISE, peak, "sine.inOut"), (t0 + RISE + FALL, 0.0, "hold")]


def glow_track(hex_starts, peak, end):
    """Opacity keys of one hex's four glow copies: [ring k] -> keys."""
    tracks = []
    for k in range(4):
        keys = [(0, 0.0, "hold")]
        for t in hex_starts:
            pulse(keys, t + k * RING_STEP, peak)
        keys.append((end, 0.0, "hold"))
        tracks.append(keys)
    return tracks


def clone_before(doc, sid, name):
    """A glow copy of the shape written just before it (so it draws just above it). Returns its id."""
    i = doc.idx(sid)
    block = doc.lines[i:doc.end(i) + 1]
    gid = None
    out = []
    for n, line in enumerate(block):
        while 'id="9:' in line:
            a = line.index('id="9:')
            b = line.index('"', a + 4)
            new = doc.new_id()
            if n == 0:
                gid = new
            line = line[:a] + 'id=\x00' + new + '\x00' + line[b + 1:]
        line = line.replace("id=\x00", 'id="').replace("\x00", '"')
        if n == 0:
            line = line.replace(" id=", f' opacity="0" name="{name}" id=', 1)
        out.append(line.replace('colorValue="FFE6FFAA"', f'colorValue="{GLOW}"'))
    doc.lines[i:i] = out
    return gid


def main():
    path = scene_path()
    rings = find_rings(path)
    doc = Doc(path)
    assert not any('name="Chapter 4 City Hex' in l or 'name="Hex Lift' in l for l in doc.lines), "the Hex layer already exists"
    glow, lift = {}, {}
    for key, (bid, first, last) in PAIRS.items():
        glow[key] = [[clone_before(doc, sid, f"Hex Glow {key} {h + 1}.{k + 1}") for k, sid in enumerate(h_ids)]
                     for h, h_ids in enumerate(rings[key])]
        lift[key] = doc.wrap_run(first, last, f"Hex Lift {key}", 0, 0)[0]

    def build(peak, lift_px, starts, end, with_lift):
        tr = {}
        for key in PAIRS:
            for h, st in enumerate(starts):
                for k, keys in enumerate(glow_track(st, peak, end)):
                    tr[(glow[key][h][k], "opacity")] = keys
            if with_lift:
                a, b, c = LIFT
                tr[(lift[key], "y")] = [(0, 0.0, "hold"), (a, 0.0, "power2.out"), (b, -lift_px, "back.out.small"), (c, 0.0, "hold"), (end, 0.0, "hold")]
            else:
                tr[(lift[key], "y")] = [(0, 0.0, "hold"), (end, 0.0, "hold")]
        return tr
    none = [[], [], []]
    loop = build(PEAK, 2.5, [[HEX_AT[0]], [HEX_AT[1]], [HEX_AT[2]]], LOOP, True)
    calm = build(PEAK_CALM, LIFT_CALM, [[HEX_AT[0]], [HEX_AT[1]], [HEX_AT[2]]], LOOP, True)
    wake = build(PEAK_CALM * 1.5, 0, [[WAKE_START], [], []], WAKE, False)     # a soft pulse of the bottom hex only (0.6 of full)
    wake = {k: v for k, v in wake.items() if len(v) > 2 or k[1] == "opacity" and any(x[1] for x in v)}
    add_building(doc, "Hex", {"wake": wake, "loop": loop, "calm": calm})
    if "--write" in sys.argv:
        doc.save()
        print("written", path)
    else:
        print("checked only; pass --write to save")


if __name__ == "__main__":
    main()
