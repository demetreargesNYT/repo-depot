"""Chapter 4 card 1, the city builds itself: the yellow honeycomb dome (SpB_01, 9:4415) pops in cell by cell from the middle out.

    python3 chapters/ch3/scripts/ch3_c4_build_dome.py --write --scene PATH

The dome is front layer and finishes last. Each of its 18 shapes keys its own scale (about its own centre: the vertices are centred on the
shape's x/y) and opacity: 0.5 -> 1 with one small overshoot over 18 frames, opacity 0 -> 1 over the first 6. Hidden pieces sit at opacity 0
(no stroke dots) and every stroke is made non-scaling (line weight stays 1.5). The centre hex and its small inner hex start at frame 130,
then the pieces by distance from the centre, 3 to 5 frames apart, the last settling at 186. Loop and calm: flat (one opacity hold).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ch3_c4_city import LOOP, BUILD, add_building, scene_path
from rml_edit import Doc
from rml_read import Scene

DOME, CENTRE, SMALL = "9:4415", "9:4488", "9:4476"
POP, FADE, FROM = 18, 6, 0.5
START, STEP = 130, 4          # first pop; frames between rings of pieces


def main():
    path = scene_path()
    sc = Scene(path)
    doc = Doc(path)
    assert "Chapter 4 City Dome" not in {e.get("name") for e in sc.root.iter("StateMachineLayer")}, "layer exists"
    byid = {e.get("id"): e for e in sc.root.iter() if e.get("id")}
    dome = byid[DOME]
    assert dome.get("name") == "SpB_01"
    shapes = [c for c in dome if c.tag == "Shape"]
    assert len(shapes) == 18, len(shapes)
    cx, cy = float(byid[CENTRE].get("x")), float(byid[CENTRE].get("y"))
    dist = {s.get("id"): ((float(s.get("x")) - cx) ** 2 + (float(s.get("y")) - cy) ** 2) ** 0.5 for s in shapes}
    order = sorted(dist, key=lambda i: (i not in (CENTRE, SMALL), dist[i]))
    # the centre pair first; the rest outward in pairs, a ring's pieces ordered around the circle, STEP frames between pairs
    import math
    starts = {CENTRE: START, SMALL: START}
    rest = [o for o in order if o not in starts]
    rest.sort(key=lambda o: (round(dist[o] / 3), math.atan2(float(byid[o].get("y")) - cy, float(byid[o].get("x")) - cx)))
    for k, oid in enumerate(rest):
        starts[oid] = START + 3 + (k // 2) * STEP - (1 if k % 2 else 0) * -1
    assert max(starts.values()) + POP <= 186, starts
    for oid in order:           # strokes stay 1.5 when scaled
        i = doc.idx(oid)
        for k in range(i, doc.end(i) + 1):
            if doc.lines[k].lstrip().startswith("<Stroke ") and "transformAffectsStroke" not in doc.lines[k]:
                doc.lines[k] = doc.lines[k].replace("<Stroke ", '<Stroke transformAffectsStroke="false" ', 1)
        # opacity attribute for the pose when no animation runs is the built value; the layer's Rest pose hides it
    build = {}
    for oid in order:
        s = starts[oid]
        for p in ("scaleX", "scaleY"):
            build[(oid, p)] = [(0, FROM, "hold"), (s, FROM, "back.out.small"), (s + POP, 1, "hold"), (BUILD, 1, "hold")]
        build[(oid, "opacity")] = [(0, 0, "hold"), (s, 0, "power2.out"), (s + FADE, 1, "hold"), (BUILD, 1, "hold")]
    loop = {(CENTRE, "opacity"): [(0, 1, "hold"), (LOOP, 1, "hold")]}
    add_building(doc, "Dome", {"build": build, "loop": loop, "calm": loop})
    print({i: (starts[i], round(dist[i], 1)) for i in order})
    if "--write" in sys.argv:
        doc.save()
        print("wrote", path)


main()
