"""Chapter 4 card 1, the city: the Spelling Bee hex column (SpB_02_B and its hidden twin SpB_02_F) builds from the bottom up, then
its inner hexes spin like coins in a cascade.

    python3 chapters/ch3/scripts/ch3_c4_build_hex.py --scene PATH [--write]       without --write it only checks

Build (192 frames): the three visible hexes (absolute y 672, 589.5, 507) drop in 30 units from the bottom up and land with one small
settle (rings outer to inner, the inner hex last, the yellow side face with the outer ring); the inner hex then turns once like a
coin (36 frames, power2.inOut, ends on the same face). Landings: frame 96, 126, 156; the last spin ends at 192. The partly hidden back
pair (x about 815) appears with the bottom two hexes. Loop 600: the coin spins at 150, 168, 186 (bottom, middle, top). Calm: the same
timing, each plate only narrows to width 0.5. Nothing else moves. The coin look is Chapter 2's Spelling Bee block (bee_art.py).
"""
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ch3_c4_city import BUILD, LOOP, add_building, scene_path
from rml_edit import Doc, num

PAIRS = {"B": "9:10426", "F": "9:7340"}
HEX_Y = [41.25, -41.25, -123.75]                 # bottom to top (hex centres in the ring node)
LAND = [96, 126, 156]
LOOP_AT = [150, 168, 186]
SPIN = 36
DROP = 30.0
DUR = 18
DARK = "FF1F1F1F"


def ease(u):
    return 2 * u * u if u < 0.5 else 1 - 2 * (1 - u) ** 2


def width(s):
    return max(abs(float(v.get("x") or 0)) for v in s.iter("StraightVertex"))


def find(path):
    """{key: {"hex": [[ring ids outer..inner] per hex], "side": [id per hex], "back": {y: [ids outer..inner]}, "inner_pts": [...]}}"""
    root = ET.parse(path).getroot()
    out = {}
    for key, bid in PAIRS.items():
        b = next(e for e in root.iter("Node") if e.get("id") == bid)
        first = b.findall("Node")[0]
        rings_node, side_node = first.findall("Node")[0], first.findall("Node")[1]
        hexes, sides, pts = [], [], None
        for y in HEX_Y:
            sh = sorted((s for s in rings_node.findall("Shape") if abs(float(s.get("y")) - y) < 1e-3), key=width, reverse=True)
            assert len(sh) == 4, (key, y, len(sh))
            hexes.append([s.get("id") for s in sh])
            sd = [s for s in side_node.findall("Shape") if abs(float(s.get("y")) - y) < 1e-3]
            assert len(sd) == 1
            sides.append(sd[0].get("id"))
            if pts is None:
                pts = [(float(v.get("x") or 0), float(v.get("y") or 0)) for v in sh[-1].iter("StraightVertex")]
        back_node = b.findall("Node")[1]
        back = {}
        for y in (-41.25, -123.75):
            sh = sorted((s for s in back_node.findall("Shape") if abs(float(s.get("y")) - y) < 1e-3), key=width, reverse=True)
            assert len(sh) == 4, (key, "back", y, len(sh))
            back[y] = [s.get("id") for s in sh]
        out[key] = {"hex": hexes, "side": sides, "back": back, "pts": pts}
    return out


def drop_keys(end, y0):
    start = end - DUR
    return ([(0, y0 - DROP, "hold")] if start == 0 else [(0, y0 - DROP, "hold"), (start, y0 - DROP, "back.out.small")]) + [(end, y0, "hold"), (BUILD, y0, "hold")]


def fade_keys(end):
    start = end - DUR
    return [(0, 0.0, "hold"), (start, 0.0, "power2.out"), (start + 8, 1.0, "hold"), (BUILD, 1.0, "hold")]


def spin_keys(starts, floor, end):
    """scaleX of a plate: |cos| of an eased half turn at each start, baked every frame."""
    keys = [(0, 1.0, "hold")]
    for s in starts:
        if s > keys[-1][0]:
            keys.append((s, 1.0, "linear"))
        for f in range(1, SPIN + 1):
            keys.append((s + f, max(floor, abs(math.cos(math.pi * ease(f / SPIN)))), "linear"))
    if keys[-1][0] < end:
        keys.append((end, 1.0, "hold"))
    keys[-1] = (keys[-1][0], 1.0, "hold")
    return keys


def main():
    path = scene_path()
    ids = find(path)
    doc = Doc(path)
    assert not any('name="Chapter 4 City Hex' in l or 'name="Hex Plate' in l for l in doc.lines), "the Hex layer already exists"
    build, loop, calm = {}, {}, {}
    info = {}
    for key in PAIRS:
        d = ids[key]
        for h in range(3):
            y0 = HEX_Y[h]
            land = LAND[h]
            rings = d["hex"][h]                       # outer .. inner
            plate_id = rings[3]
            # the plate goes into a pivot at its centre; the hollow (a dark hexagon of the same size) sits right under it
            i = doc.idx(plate_id)
            j = doc.end(i)
            for k in range(i, j + 1):
                if "<Stroke " in doc.lines[k] and "transformAffectsStroke" not in doc.lines[k]:
                    doc.lines[k] = doc.lines[k].replace("<Stroke ", '<Stroke transformAffectsStroke="false" ', 1)
            pid, _ = doc.wrap(plate_id, f"Hex Plate {key}{h + 1}", 0, y0)
            pj = doc.end(doc.idx(pid))
            pad = " " * (len(doc.lines[pj]) - len(doc.lines[pj].lstrip()))
            p2 = pad + "    "
            hid = doc.new_id()
            body = [f'{pad}<Shape y="{num(y0)}" name="Hex Plate Hollow {key}{h + 1}" id="{hid}">', f'{p2}<PointsPath isClosed="true" id="{doc.new_id()}">']
            body += [f'{p2}    <StraightVertex x="{num(x)}" y="{num(y)}" id="{doc.new_id()}"/>' for x, y in d["pts"]]
            body += [f"{p2}</PointsPath>", f'{p2}<Fill id="{doc.new_id()}">', f'{p2}    <SolidColor colorValue="{DARK}" id="{doc.new_id()}"/>', f"{p2}</Fill>",
                     f'{p2}<Stroke thickness="1.5" cap="round" join="round" transformAffectsStroke="false" id="{doc.new_id()}">',
                     f'{p2}    <SolidColor colorValue="{DARK}" id="{doc.new_id()}"/>', f"{p2}</Stroke>", f"{pad}</Shape>"]
            doc.lines[pj + 1:pj + 1] = body
            ends = [land - 6, land - 4, land - 2, land]            # outer .. inner land; the side face lands with the outer ring
            for sid, e in zip(rings[:3] + [pid, hid], ends + [land]):
                holder = sid
                build[(holder, "y")] = drop_keys(e, y0)
                build[(holder, "opacity")] = fade_keys(e)
            build[(d["side"][h], "y")] = drop_keys(land - 6, y0)
            build[(d["side"][h], "opacity")] = fade_keys(land - 6)
            build[(pid, "scaleX")] = spin_keys([land], 0.07, BUILD)
            loop[(pid, "scaleX")] = spin_keys([LOOP_AT[h]], 0.07, LOOP)
            calm[(pid, "scaleX")] = spin_keys([LOOP_AT[h]], 0.5, LOOP)
            info.setdefault(key, []).append(pid)
        # the back pair appears with the bottom two hexes, outer to inner
        for h, y in ((0, -41.25), (1, -123.75)):
            for r, sid in enumerate(d["back"][y]):
                e = LAND[h] - 6 + 2 * r
                build[(sid, "y")] = drop_keys(e, y)
                build[(sid, "opacity")] = fade_keys(e)
    # shapes got fixed y values; the drop keys above assume each shape's y equals y0 (checked by the unbuilt pose vs the file)
    loop = {k: v for k, v in loop.items()}
    # the loop and calm tracks must also start with every piece at its built value: add_building adds flat holds for the rest
    add_building(doc, "Hex", {"build": build, "loop": loop, "calm": calm})
    first = {k: v[0] for k, v in build.items()}
    vis = sorted(min(f for f, val, _ in v if val > 0) if k[1] == "opacity" else 10**9 for k, v in build.items() if k[1] == "opacity")
    print("pieces:", len(build) // 1, "first visible frame:", vis[0], "last landing:", max(f for k, v in build.items() for f, val, how in v if k[1] == "y" and how == "hold" and f < BUILD))
    if "--write" in sys.argv:
        doc.save()
        print("written", path)
    else:
        print("checked only; pass --write to save")


if __name__ == "__main__":
    main()
