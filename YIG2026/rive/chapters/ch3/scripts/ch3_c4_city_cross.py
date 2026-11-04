"""Chapter 4 card 1: the blue cross towers ("Coss": Coss_F + Coss_B, in step) and the step pyramid ("Cross": Cross_02) come alive.

    python3 chapters/ch3/scripts/ch3_c4_city_cross.py --write [--scene PATH]

Coss (the blue towers, F and B copies moved together):
- tile slide A, 1.2 to 2.25 s: the cross tower's right-hand shaft tile (path 0/1/9) slides 11 px right (0.4 s), holds 0.3 s, clicks back (0.35 s, one overshoot)
- corner fold, 3.0 to 3.5 s: the cross tower's white corner tile folds down flat on its base edge (scaleY to 0.12) and back
- tile slide B, 7.4 to 8.55 s: the L tower's second column tile (path 2/2) slides 11 px left, holds 0.4 s, clicks back
- wake (frame 100): tile A gives a 4 px nudge and back
Cross (the step pyramid, Cross_02): its top cube (dark) does a quarter cube turn to a white face, 9.0 to 9.4 s, and turns back, 9.6 to 10 s
(the loop has to end on the pose it began on); wake (frame 154): the same cube flips and flips back.
Calm: slides 6 px, holds 0.2 s, the corner fold only to 0.55, no cube turn.
"""
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ch3_c4_city import LOOP, WAKE, add_building, scene_path
from rml_edit import Doc

COSS_F, COSS_B, CROSS = "9:6834", "9:9920", "9:3828"
TRI = "9:6900"
TILE_A, TILE_B = "9:7078", "9:7214"
CUBE = "9:3891"
LIGHT = "FFDFDBD7"
H, PO, PI, BK = "hold", "power2.out", "power2.in", "back.out.small"


def kids(e):
    return [c for c in e if c.tag in ("Node", "Shape")]


def path_of(root, target):
    if root is target:
        return []
    for i, c in enumerate(kids(root)):
        p = path_of(c, target)
        if p is not None:
            return [i] + p
    return None


def follow(root, path):
    for i in path:
        root = kids(root)[i]
    return root


def no_stroke_scaling(doc, stroke_id):
    i = doc.idx(stroke_id)
    if "transformAffectsStroke" not in doc.lines[i]:
        doc.lines[i] = re.sub(r' id="', ' transformAffectsStroke="false" id="', doc.lines[i], count=1)


def main(path):
    text = Path(path).read_text()
    assert "Chapter 4 City Coss" not in text and "Chapter 4 City Cross" not in text, "the Coss/Cross layers already exist"
    root = ET.fromstring(text)
    by_id = {e.get("id"): e for e in root.iter() if e.get("id")}
    cf, cb, cr = by_id[COSS_F], by_id[COSS_B], by_id[CROSS]
    pairs = {}
    for name, oid in (("tri", TRI), ("a", TILE_A), ("b", TILE_B)):
        p = path_of(cf, by_id[oid])
        pairs[name] = (by_id[oid], follow(cb, p))
    doc = Doc(path)

    # --- the white corner tile: a pivot on its base edge, in both copies; strokes stay 1.5 when it squashes
    tri_piv = []
    for tri, _ in [(pairs["tri"][0], 0), (pairs["tri"][1], 0)]:
        no_stroke_scaling(doc, tri.find("Stroke").get("id"))
        px, py = float(tri.get("x", 0)), float(tri.get("y", 0)) + 12.5
        tri_piv.append(doc.wrap(tri.get("id"), "Corner Fold", px, py)[0])

    # --- the step pyramid's top cube: the dark face and a white twin, each in a pivot on the cube's centre
    cube = by_id[CUBE]
    no_stroke_scaling(doc, cube.find("Stroke").get("id"))
    i = doc.idx(CUBE)
    j = doc.end(i)
    dup = [re.sub(r' id="9:\d+"', lambda m: f' id="{doc.new_id()}"', l) for l in doc.lines[i:j + 1]]
    k = next(n for n, l in enumerate(dup) if "colorValue" in l)             # the Fill's colour (the first one in the shape)
    dup[k] = re.sub(r'colorValue="\w+"', f'colorValue="{LIGHT}"', dup[k])
    dup_id = re.search(r'id="(9:\d+)"', dup[0]).group(1)
    doc.lines[j + 1:j + 1] = dup
    px, py = float(cube.get("x", 0)), float(cube.get("y", 0))
    dark = doc.wrap(CUBE, "Cube Dark", px, py)[0]
    light = doc.wrap(dup_id, "Cube Light", px, py)[0]
    li = doc.idx(light)
    doc.lines[li] = doc.lines[li].replace(' name=', ' scaleX="0" opacity="0" name=', 1)

    def slide(base, d, out_f, hold, back):
        """x keys for one tile: out, hold, click back (one overshoot)."""
        a = out_f
        return [(0, base, H), (a, base, "power2.inOut"), (a + 24, base + d, H), (a + 24 + hold, base + d, BK), (a + 24 + hold + back, base, H), (LOOP, base, H)]

    def build(d, hold_a, hold_b, fold, cube_on):
        loop, base = {}, {}
        for name in ("a", "b"):
            for tag, el in zip("FB", pairs[name]):
                base[name, tag] = float(el.get("x", 0))
        for tag, f in (("F", 0), ("B", 1)):
            loop[(pairs["a"][f].get("id"), "x")] = slide(base["a", tag], d, 72, hold_a, 21)
            loop[(pairs["b"][f].get("id"), "x")] = slide(base["b", tag], -d, 444, hold_b, 21)
        for p in tri_piv:
            loop[(p, "scaleY")] = [(0, 1, H), (180, 1, PI), (192, fold, H), (196, fold, BK), (210, 1, H), (LOOP, 1, H)]
        return loop, base

    def cube_tracks(on):
        if not on:
            return {(dark, "scaleX"): [(0, 1, H), (LOOP, 1, H)], (dark, "opacity"): [(0, 1, H), (LOOP, 1, H)],
                    (light, "scaleX"): [(0, 0, H), (LOOP, 0, H)], (light, "opacity"): [(0, 0, H), (LOOP, 0, H)]}
        return {(dark, "scaleX"): [(0, 1, H), (540, 1, PI), (552, 0, H), (588, 0, PO), (LOOP, 1, H)],
                (dark, "opacity"): [(0, 1, H), (552, 0, H), (588, 1, H), (LOOP, 1, H)],
                (light, "scaleX"): [(0, 0, H), (552, 0, PO), (564, 1, H), (576, 1, PI), (588, 0, H), (LOOP, 0, H)],
                (light, "opacity"): [(0, 0, H), (552, 1, H), (588, 0, H), (LOOP, 0, H)]}

    full, base = build(11, 18, 24, 0.12, True)
    calm, _ = build(6, 12, 12, 0.55, False)
    wake = {}
    for tag, f in (("F", 0), ("B", 1)):
        b = base["a", tag]
        wake[(pairs["a"][f].get("id"), "x")] = [(0, b, H), (100, b, "power2.inOut"), (112, b + 4, H), (114, b + 4, BK), (128, b, H), (WAKE, b, H)]
    add_building(doc, "Coss", {"wake": wake, "loop": full, "calm": calm})
    wake_cross = {(dark, "scaleX"): [(0, 1, H), (154, 1, PI), (162, 0, H), (172, 0, PO), (180, 1, H), (WAKE, 1, H)],
                  (dark, "opacity"): [(0, 1, H), (162, 0, H), (172, 1, H), (WAKE, 1, H)],
                  (light, "scaleX"): [(0, 0, H), (162, 0, PO), (170, 1, H), (172, 1, PI), (180, 0, H), (WAKE, 0, H)],
                  (light, "opacity"): [(0, 0, H), (162, 1, H), (180, 0, H), (WAKE, 0, H)]}
    add_building(doc, "Cross", {"wake": wake_cross, "loop": cube_tracks(True), "calm": cube_tracks(False)})
    doc.save()
    print(f"wrote {path}: layers Chapter 4 City Coss and Chapter 4 City Cross")


if __name__ == "__main__":
    if "--write" not in sys.argv:
        raise SystemExit(__doc__)
    main(scene_path())
