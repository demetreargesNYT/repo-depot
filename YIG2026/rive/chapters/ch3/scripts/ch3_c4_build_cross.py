"""Chapter 4 card 1 BUILD for the blue cross towers ("Coss": Coss_F + Coss_B in step) and the step pyramid ("Cross": Cross_02).

    python3 chapters/ch3/scripts/ch3_c4_build_cross.py --write [--scene PATH]

Coss: every tile (a group of dark strip + blue body, or a white corner tile) slides in 20 to 40 px from its side or from above, fades in
over its first 6 frames and clicks into place with one small overshoot (back.out.small). Far left column (outside the phone crop)
builds frames 40 to 118, the right L tower (outside) 50 to 130, the cross tower (inside the crop) 100 to 175, tiles staggered with overlap.
Cross: the pyramid builds row by row from the base, each block dropping 16 px with a scale pop from 0.7 and one small settle, frames 120 to 188.
Loop and calm: flat (one opacity held at its built value).
"""
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ch3_c4_city import add_building, scene_path
from rml_edit import Doc

COSS_F, COSS_B, CROSS = "9:6834", "9:9920", "9:3828"
H, BK, PO = "hold", "back.out.small", "power2.out"
BUILD = 192


def kids(e):
    return [c for c in e if c.tag in ("Node", "Shape")]


def is_tile(e):
    k = kids(e)
    return e.tag == "Node" and bool(k) and all(c.tag == "Shape" for c in k)


def tiles(e, ax=0.0, ay=0.0, out=None, path=()):
    """Every tile (leaf group with shapes) and every lone Shape sitting directly in a wrapper, as (element, abs x, abs y, path)."""
    out = [] if out is None else out
    x, y = ax + float(e.get("x", 0)), ay + float(e.get("y", 0))
    for i, c in enumerate(kids(e)):
        if is_tile(c) or (c.tag == "Shape" and e.tag == "Node"):
            if c.tag == "Shape":
                out.append((c, x + float(c.get("x", 0)), y + float(c.get("y", 0)), path + (i,)))
            else:
                out.append((c, x + float(c.get("x", 0)), y + float(c.get("y", 0)), path + (i,)))
        else:
            tiles(c, x, y, out, path + (i,))
    return out


def follow(root, path):
    for i in path:
        root = kids(root)[i]
    return root


def build_keys(base, off, start, dur, fade=6):
    """Position keys: sit offset (hidden) until start, then one eased move with a small overshoot, then hold."""
    return [(0, base + off, H), (start, base + off, BK), (start + dur, base, H), (BUILD, base, H)]


def fade_keys(start, fade=6):
    return [(0, 0, H), (start, 0, PO), (start + fade, 1, H), (BUILD, 1, H)]


def main(path):
    text = Path(path).read_text()
    assert "Chapter 4 City Coss" not in text and "Chapter 4 City Cross" not in text, "the Coss/Cross layers already exist"
    root = ET.fromstring(text)
    by_id = {e.get("id"): e for e in root.iter() if e.get("id")}
    cf, cb, cr = by_id[COSS_F], by_id[COSS_B], by_id[CROSS]
    doc = Doc(path)
    report = {}

    # ---------------- Coss ----------------
    ts = tiles(cf)
    ts_b = [(follow(cb, p), p) for *_, p in ts]
    # groups by absolute x of the tile centre (artboard x = 427.5 + local, tiles() starts at Coss_F's own origin)
    group = lambda ax: "left" if ax < 560 else ("right" if ax > 935 else "cross")
    cx = sorted(((t, ax, ay, p) for t, ax, ay, p in ts), key=lambda r: (group(r[1]), -r[2]))
    plan = {"left": (40, 98, 22), "right": (50, 108, 22), "cross": (100, 153, 22)}   # first start, last start, duration
    by_g = {}
    for t, ax, ay, p in ts:
        by_g.setdefault(group(ax), []).append((t, ax, ay, p))
    coss = {}
    starts = {}
    for g, items in by_g.items():
        # bottom first (largest y), then toward the middle; the white corner tiles (lone Shapes) come last
        items.sort(key=lambda r: (r[0].tag == "Shape", -r[2], r[1]))
        s0, s1, dur = plan[g]
        for n, (t, ax, ay, p) in enumerate(items):
            start = round(s0 + (s1 - s0) * n / max(1, len(items) - 1))
            starts[(g, t.get("id"))] = start
            gx = ax
            # slide direction: tiles left of their group's centre come from the left, right of it from the right, the shaft from above
            gc = {"left": 464, "right": 1012, "cross": 782}[g]
            if g == "left":
                dx, dy = -28, 0
            elif abs(gx - gc) < 14:
                dx, dy = 0, -34
            else:
                dx, dy = (-26, 0) if gx < gc else (26, 0)
            if t.tag == "Shape":
                dx, dy = 0, -30
            for tag, el in (("F", t), ("B", follow(cb, p))):
                oid = el.get("id")
                bx, by_ = float(el.get("x", 0)), float(el.get("y", 0))
                if dx:
                    coss[(oid, "x")] = build_keys(bx, dx, start, dur)
                if dy:
                    coss[(oid, "y")] = build_keys(by_, dy, start, dur)
                coss[(oid, "opacity")] = fade_keys(start)
    first = ts[0][0]
    loop_c = {(first.get("id"), "opacity"): [(0, 1, H), (600, 1, H)]}

    # ---------------- Cross ----------------
    shapes = [e for e in cr.iter("Shape")]
    cells = []
    def walk(e, ax, ay):
        x, y = ax + float(e.get("x", 0)), ay + float(e.get("y", 0))
        for c in kids(e):
            if c.tag == "Shape":
                cells.append((c, x + float(c.get("x", 0)), y + float(c.get("y", 0))))
            else:
                walk(c, x, y)
    walk(cr, 0, 0)
    rows = sorted({round(cy, 1) for _, cx_, cy in cells}, reverse=True)       # base row first (largest y)
    cross = {}
    cstart = {}
    nrow = len(rows)
    for r, ry in enumerate(rows):
        rc = sorted([c for c in cells if round(c[2], 1) == ry], key=lambda c: c[1])
        base_f = 120 + round(r * 44 / max(1, nrow - 1)) if nrow > 1 else 120
        for n, (sh, ax, ay) in enumerate(rc):
            start = base_f + n * 3
            cstart[sh.get("id")] = start
            sid = sh.get("id")
            stroke = sh.find("Stroke")
            st = stroke.get("id")
            i = doc.idx(st)
            if "transformAffectsStroke" not in doc.lines[i]:
                doc.lines[i] = re.sub(r' id="', ' transformAffectsStroke="false" id="', doc.lines[i], count=1)
            y0 = float(sh.get("y", 0))
            dur = 18
            cross[(sid, "y")] = build_keys(y0, -16, start, dur)
            cross[(sid, "scaleX")] = [(0, 0.7, H), (start, 0.7, BK), (start + dur, 1, H), (BUILD, 1, H)]
            cross[(sid, "scaleY")] = [(0, 0.7, H), (start, 0.7, BK), (start + dur, 1, H), (BUILD, 1, H)]
            cross[(sid, "opacity")] = fade_keys(start)
    assert max(cstart.values()) + 18 <= 188, max(cstart.values())
    loop_x = {(cells[0][0].get("id"), "opacity"): [(0, 1, H), (600, 1, H)]}

    # strokes of the Coss pieces never scale, so nothing to fix there
    add_building(doc, "Coss", {"build": coss, "loop": loop_c})
    add_building(doc, "Cross", {"build": cross, "loop": loop_x})
    doc.save()
    print(f"wrote {path}")
    for g, v in sorted(starts.items()):
        pass
    for g in by_g:
        ss = [v for (gg, _), v in starts.items() if gg == g]
        print(g, len(ss), "tiles; first visible frame", min(ss), "last start", max(ss), "done", max(ss) + plan[g][2])
    print("Cross rows", rows, "cells", len(cells), "first", min(cstart.values()), "last done", max(cstart.values()) + 18)


if __name__ == "__main__":
    if "--write" not in sys.argv:
        raise SystemExit(__doc__)
    main(scene_path())
