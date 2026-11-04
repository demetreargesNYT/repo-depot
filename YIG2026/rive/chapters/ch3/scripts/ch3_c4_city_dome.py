"""Chapter 4 card 1, the city comes alive: the yellow honeycomb dome (SpB_01, 9:4415) lights its cells one at a time, like a bee.

    python3 chapters/ch3/scripts/ch3_c4_city_dome.py --write --scene PATH

Six white overlay shapes (a copy of a cell's outline at 0.94 size, no stroke, so the 1.5 outlines stay as drawn) sit on top inside
SpB_01, opacity 0. Colour cannot be keyed, so a cell lights by its overlay's opacity: up to 0.6 over 9 frames (0.15 s, power2.out),
back to 0 over 24 frames (0.4 s, sine.inOut). Beats at 0.6, 2.2, 3.9, 5.6, 7.3 and 9.0 s. The path (never two neighbours in a row,
also across the seam): top, bottom right, left, the small centre hex, right, bottom left. Bottom left and right are the slivers of
the lower ring cells that show above the floor line. Wake: the top cell lights once (frame 109). Calm: top, left, small centre, right
at peak 0.4. The overlays carry the floor clip. Nothing moves, so travel and tilt are 0.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2].parent / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ch3_c4_city import LOOP, WAKE, WAKE_AT, add_building, scene_path
from rml_edit import Doc, num
from rml_read import Scene

DOME, FLOOR_CLIP = "9:4415", "9:20855"
# (name, source shape id, which source: inner hex or outer ring hex)
CELLS = [("Top", "9:4464"), ("Bottom Right", "9:4572"), ("Left", "9:4440"), ("Centre", "9:4476"), ("Right", "9:4452"), ("Bottom Left", "9:4548")]
BEATS = [36, 132, 234, 336, 438, 540]            # 0.6, 2.2, 3.9, 5.6, 7.3, 9.0 s
UP, DOWN, PEAK, CALM_PEAK, SHRINK = 9, 24, 0.6, 0.4, 0.94
CALM_SLOTS = [0, 2, 3, 4]


def pulse(start, peak, end):
    return [(start, 0, "power2.out"), (start + UP, peak, "sine.inOut"), (start + UP + DOWN, 0, "hold")]


def track(beats, peak, end):
    keys = [(0, 0, "hold")]
    for b in beats:
        keys += pulse(b, peak, end)
    if keys[-1][0] != end:
        keys.append((end, 0, "hold"))
    return keys


def main():
    path = scene_path()
    sc = Scene(path)
    doc = Doc(path)
    assert "Chapter 4 City Dome" not in {e.get("name") for e in sc.root.iter("StateMachineLayer")}, "layer exists"
    assert sum(1 for e in sc.root.iter() if e.get("name") == "Dome Cell Top") == 0, "overlays exist"
    byid = {e.get("id"): e for e in sc.root.iter() if e.get("id")}
    dome = byid[DOME]
    assert dome.get("name") == "SpB_01" and len(list(dome)) == 18, "the dome is not what the script expects"
    out, ids = [], []
    for name, sid in CELLS:
        src = byid[sid]
        verts = [(float(v.get("x", 0)), float(v.get("y", 0))) for v in src.iter("StraightVertex")]
        assert len(verts) == 6
        oid = doc.new_id()
        ids.append(oid)
        pad = " " * 24
        out += [f'{pad}<Shape x="{src.get("x")}" y="{src.get("y")}" opacity="0" name="Dome Cell {name}" id="{oid}">',
                f'{pad}    <PointsPath isClosed="true" isClockwise="false" id="{doc.new_id()}">']
        out += [f'{pad}        <StraightVertex x="{num(x * SHRINK)}" y="{num(y * SHRINK)}" id="{doc.new_id()}"/>' for x, y in verts]
        out += [f"{pad}    </PointsPath>", f'{pad}    <Fill id="{doc.new_id()}">', f'{pad}        <SolidColor colorValue="FFFFFFFF" id="{doc.new_id()}"/>',
                f"{pad}    </Fill>", f'{pad}    <ClippingShape sourceId="{FLOOR_CLIP}" name="Floor Clip" id="{doc.new_id()}"/>', f"{pad}</Shape>"]
    i = doc.idx(DOME)
    doc.lines[i + 1:i + 1] = out                         # first child draws on top
    loop = {(o, "opacity"): track([BEATS[k]], PEAK, LOOP) for k, o in enumerate(ids)}
    calm = {(ids[k], "opacity"): track([BEATS[k]], CALM_PEAK, LOOP) for k in CALM_SLOTS}
    w0 = WAKE_AT["Dome"]
    wake = {(ids[0], "opacity"): [(0, 0, "hold")] + pulse(w0, PEAK, WAKE)[:3] + [(WAKE, 0, "hold")]}
    add_building(doc, "Dome", {"loop": loop, "calm": calm, "wake": wake})
    if "--write" in sys.argv:
        doc.save()
        print("wrote", path)


main()
