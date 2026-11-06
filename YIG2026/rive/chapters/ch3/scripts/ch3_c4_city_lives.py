"""Chapter 4 city pass, the "lives" phase (Demetre, 2026-11-06): every building gets a quiet base motion plus at most one small moment per loop.

    python3 chapters/ch3/scripts/ch3_c4_city_lives.py --scene PATH [--write]        once; it asserts on a second run

This edits the scene in place (it does not regenerate a room). The arrival, the build sequence and the ball are not touched.
Only the Loop and Calm animations of each city layer change (Rest gets a key for every property they key), plus these new things:
- cleanup: Coss_F (an exact visible duplicate of Coss_B, drawn on top of it), Crossword_F and SpB_02_F (hidden at opacity 0, never shown),
  and the second plate stack's ring hollow, are deleted with every key that pointed at them;
- the Connections stack's cell lights (lighter rectangles clipped to a slab's body), the glint bands on the blue Coss tiles, the Hex
  stack's ring hollows, the Dome centre's hollow, and "Chapter 4 Clouds" (ten shapes behind the city) with two layers of their own.
Everything is keyed with a few keys and eases (smooth drifts are cubic Hermite keys every 50 frames).
"""
import math
import random
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rml_edit import Doc, EASES, num  # noqa: E402
from rml_read import Scene, chapter_dir  # noqa: E402
import ch3_c4_city as city  # noqa: E402,F401  (importing it adds the extra eases)
import svg_to_rml  # noqa: E402

LOOP = 600
ROOM = "Chapter 4"
WHITE, BLACK = "FFDFDBD7", "FF1F1F1F"
CLOUD_FILL, LINE = "FFEBF4F3", "FF1F1F1F"
FLOOR_CLIP = "9:20855"
SCRATCH_SVG = Path(__file__).resolve().parents[3] / "chapters/ch3/refs/clouds.svg"


# ---- a faster, batch writer for one animation ---------------------------------------------------------------------------------------
class Anim:
    """Reads one animation's KeyedObjects once, lets you replace properties, and writes the animation back once."""

    def __init__(self, doc, name):
        self.doc, self.name = doc, name
        self.a, self.b = doc.anim(name)
        body = doc.lines[self.a + 1:self.b]
        self.objs = {}                    # oid -> {"id": line id, "props": {prop: [lines]}}, insertion ordered
        i = 0
        while i < len(body):
            m = re.match(r'^\s*<KeyedObject objectId="([^"]+)" id="([^"]+)">\s*$', body[i])
            assert m, (name, body[i][:100])
            oid, kid = m.groups()
            j = i + 1
            props = {}
            while not body[j].strip().startswith("</KeyedObject>"):
                mp = re.match(r'^(\s*)<KeyedProperty property="(\w+)"', body[j])
                assert mp, (name, body[j][:100])
                k = j
                while not (body[k].startswith(mp.group(1) + "</KeyedProperty>")):
                    k += 1
                props[mp.group(2)] = body[j:k + 1]
                j = k + 1
            self.objs[oid] = {"id": kid, "props": props}
            i = j + 1

    def has(self, oid, prop=None):
        return oid in self.objs and (prop is None or prop in self.objs[oid]["props"])

    def drop_object(self, oid):
        self.objs.pop(oid, None)

    def drop_prop(self, oid, prop):
        if self.has(oid, prop):
            del self.objs[oid]["props"][prop]
            if not self.objs[oid]["props"]:
                del self.objs[oid]

    def put(self, oid, prop, lines):
        self.objs.setdefault(oid, {"id": self.doc.new_id(), "props": {}})["props"][prop] = lines

    def set(self, oid, prop, keys):
        """keys: [(frame, number, how)] with how 'hold', 'linear', an ease name or an (x1, y1, x2, y2) tuple."""
        pad = " " * 20
        self.put(oid, prop, [f'{" " * 16}<KeyedProperty property="{prop}" id="{self.doc.new_id()}">']
                 + key_lines(self.doc, keys, pad) + [f'{" " * 16}</KeyedProperty>'])

    def set_color(self, oid, keys):
        pad = " " * 20
        self.put(oid, "colorValue", [f'{" " * 16}<KeyedProperty property="colorValue" id="{self.doc.new_id()}">']
                 + color_lines(self.doc, keys, pad) + [f'{" " * 16}</KeyedProperty>'])

    def first_value(self, oid, prop):
        for l in self.objs[oid]["props"][prop]:
            m = re.search(r'<KeyFrame(?:Double|Color)(?: value="([^"]*)")?', l)
            if m:
                v = m.group(1)
                return v if (v and not re.fullmatch(r"-?[\d.eE+-]+", v)) else float(v or 0)
        raise KeyError((oid, prop))

    def last_value(self, oid, prop):
        last = None
        for l in self.objs[oid]["props"][prop]:
            m = re.search(r'<KeyFrame(?:Double|Color)(?: value="([^"]*)")?', l)
            if m:
                v = m.group(1)
                last = v if (v and not re.fullmatch(r"-?[\d.eE+-]+", v)) else float(v or 0)
        return last

    def commit(self):
        out = []
        for oid, o in self.objs.items():
            out.append(f'            <KeyedObject objectId="{oid}" id="{o["id"]}">')
            for lines in o["props"].values():
                out += lines
            out.append("            </KeyedObject>")
        a, b = self.doc.anim(self.name)          # other animations were committed since this one was read: find it again
        self.doc.lines[a + 1:b] = out


def key_lines(doc, keys, pad):
    out = []
    for frame, value, how in keys:
        v = f' value="{num(value)}"' if num(value) != "0" else ""
        fr = f' frame="{frame}"' if frame else ""
        if how == "hold":
            out.append(f'{pad}<KeyFrameDouble{v}{fr} id="{doc.new_id()}"/>')
        elif how == "linear":
            out.append(f'{pad}<KeyFrameDouble{v} interpolationType="linear"{fr} id="{doc.new_id()}"/>')
        else:
            x1, y1, x2, y2 = how if isinstance(how, tuple) else EASES[how]
            out.append(f'{pad}<KeyFrameDouble{v} interpolationType="cubic"{fr} id="{doc.new_id()}">')
            out.append(f'{pad}    <CubicEaseInterpolator x1="{round(x1, 4)}" y1="{round(y1, 4)}" x2="{round(x2, 4)}" y2="{round(y2, 4)}" id="{doc.new_id()}"/>')
            out.append(f"{pad}</KeyFrameDouble>")
    return out


def color_lines(doc, keys, pad):
    out = []
    for frame, value, how in keys:
        fr = f' frame="{frame}"' if frame else ""
        if how == "hold":
            out.append(f'{pad}<KeyFrameColor value="{value}"{fr} id="{doc.new_id()}"/>')
        else:
            x1, y1, x2, y2 = EASES[how]
            out.append(f'{pad}<KeyFrameColor value="{value}" interpolationType="cubic"{fr} id="{doc.new_id()}">')
            out.append(f'{pad}    <CubicEaseInterpolator x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" id="{doc.new_id()}"/>')
            out.append(f"{pad}</KeyFrameColor>")
    return out


def hermite(fn, frames):
    """Keys for a smooth function fn(frame): cubic Hermite segments (a cubic ease whose handles carry the slopes) between the knots."""
    vals = [fn(f) for f in frames]
    h = 0.01
    slopes = [(fn(f + h) - fn(f - h)) / (2 * h) for f in frames]
    keys = []
    for i, f in enumerate(frames):
        if i == len(frames) - 1:
            keys.append((f, vals[i], "hold"))
            break
        dt, dv = frames[i + 1] - f, vals[i + 1] - vals[i]
        if abs(dv) < 1e-6:
            keys.append((f, vals[i], "hold" if abs(slopes[i]) < 1e-6 and abs(slopes[i + 1]) < 1e-6 else "linear"))
            continue
        keys.append((f, vals[i], (1 / 3, slopes[i] * dt / 3 / dv, 2 / 3, 1 - slopes[i + 1] * dt / 3 / dv)))
    return keys


KNOTS = list(range(0, LOOP + 1, 50))


def mix(c, other="FFFFFFFF", t=0.5):
    a = [int(c[i:i + 2], 16) for i in (2, 4, 6)]
    b = [int(other[i:i + 2], 16) for i in (2, 4, 6)]
    return "FF" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(a, b))


# ---- reading ------------------------------------------------------------------------------------------------------------------------
class Reader:
    """Built values and static attributes, read from the scene as it was before this script edited it."""

    def __init__(self, path):
        self.sc = Scene(path)
        self.keys = {}
        for nm in ("Hex", "Dome", "Connections", "Strands", "Coss", "Tower"):
            self.keys[nm] = self.sc.keys(self.sc.animations[f"{ROOM} City {nm} Build"])

    def static(self, oid, prop):
        e = self.sc.by_id[oid]
        default = {"scaleX": 1.0, "scaleY": 1.0, "opacity": 1.0}.get(prop, 0.0)
        return float(e.get(prop, default))

    def built(self, building, oid, prop):
        ks = self.keys[building].get((self.sc.label(oid), prop))
        # labels are names where an object has one; fall back to the id itself
        if ks is None:
            ks = self.keys[building].get((oid, prop))
        return ks[-1][1] if ks else self.static(oid, prop)


# ---- cleanup ------------------------------------------------------------------------------------------------------------------------
def delete_elements_and_keys(doc, element_ids):
    """Delete the elements with these ids (subtrees included) and every KeyedObject that points into them."""
    sc = Scene(doc.path)
    gone = set()
    for eid in element_ids:
        gone |= {e.get("id") for e in sc.by_id[eid].iter() if e.get("id")}
    before = len(doc.lines)
    for eid in element_ids:
        i = doc.idx(eid)
        del doc.lines[i:doc.end(i) + 1]
    keyed_removed = 0
    i = 0
    out = []
    lines = doc.lines
    n = len(lines)
    pat = re.compile(r'^\s*<KeyedObject objectId="([^"]+)"')
    while i < n:
        m = pat.match(lines[i])
        if m and m.group(1) in gone:
            j = i
            while not lines[j].strip().startswith("</KeyedObject>"):
                j += 1
            keyed_removed += 1
            i = j + 1
            continue
        out.append(lines[i])
        i += 1
    doc.lines[:] = out
    return before - len(doc.lines), keyed_removed, len(gone)


# ---- the tower (Crossword_B): face flips, words and waves -----------------------------------------------------------------------------
def tower_grid(sc):
    ids = sc.by_id
    grid = {}

    def walk(e, ox, oy):
        for c in e:
            if c.tag == "Node":
                walk(c, ox + float(c.get("x", 0)), oy + float(c.get("y", 0)))
            elif c.tag == "Shape":
                f = [x for x in c if x.tag == "Fill"]
                if not f:
                    continue
                sc_ = next(f[0].iter("SolidColor"))
                key = (round((ox + float(c.get("x", 0)) - 44.5) / 12.5), round((382 - (oy + float(c.get("y", 0)))) / 12.5))
                grid.setdefault(key, []).append((sc_.get("colorValue"), sc_.get("id")))
    walk(ids["9:7705"], 0, 0)
    return {k: v[0] for k, v in grid.items() if len(v) == 1}          # a cell drawn twice is left alone


class Cells:
    """Each cell's flip events; refuses an event that overlaps another on the same cell."""

    def __init__(self, grid):
        self.grid, self.events = grid, {}

    def free(self, cell, a, d, margin=6):
        return all(d + margin < a2 or a - margin > d2 for a2, d2 in [(e[0], e[3]) for e in self.events.get(cell, [])])

    def add(self, cell, a, fade, hold, back_fade):
        b, c = a + fade, a + fade + hold
        d = c + back_fade
        assert d < LOOP - 2, (cell, a, d)
        self.events.setdefault(cell, []).append((a, b, c, d))

    def tracks(self):
        out = {}
        for cell, evs in self.events.items():
            c0 = self.grid[cell][0]
            c1 = BLACK if c0 == WHITE else WHITE
            keys = [] if evs[0][0] == 0 else [(0, c0, "hold")]
            for a, b, c, d in sorted(evs):
                keys += [(a, c0, "power1.inOut"), (b, c1, "hold"), (c, c1, "power1.inOut"), (d, c0, "hold")]
            keys.append((LOOP, c0, "hold"))
            out[self.grid[cell][1]] = keys
        return out


def tower_runs(grid):
    """All 3 to 5 cell runs across (a row) and down (a column) in the rows that show clear of the dome (15 and up)."""
    runs = []
    for (c, r) in grid:
        if r < 15:
            continue
        for L in (3, 4, 5):
            across = [(c + i, r) for i in range(L)]
            down = [(c, r - i) for i in range(L)]
            for kind, cells in (("across", across), ("down", down)):
                if all(x in grid and x[1] >= 15 for x in cells):
                    runs.append((kind, cells))
    return runs


def tower_motion(grid, calm, rng):
    cells = Cells(grid)
    runs = tower_runs(grid)
    step, hold, fade_back = (30, 50, 24) if calm else (20, 40, 16)
    lengths = [3, 4, 3, 4, 3] if calm else [4, 3, 5, 4, 3, 5, 3]
    t = 8 if calm else 6
    last_centre = None
    for k, L in enumerate(lengths):
        pool = [r for r in runs if len(r[1]) == L and r[0] == ("across" if k % 2 == 0 else "down")]
        rng.shuffle(pool)
        pick = None
        for kind, cs in pool:
            cx = sum(c for c, r in cs) / L
            cy = sum(r for c, r in cs) / L
            if last_centre and math.hypot(cx - last_centre[0], (cy - last_centre[1]) * 0.9) < 3.2:
                continue
            if all(cells.free(x, t + i * step, t + i * step + 40 + hold + fade_back + step * (L - 1 - i)) for i, x in enumerate(cs)):
                pick = (cs, cx, cy)
                break
        assert pick, "no word fits"
        cs, cx, cy = pick
        last_centre = (cx, cy)
        end = t + step * (L - 1)                          # the last cell starts to flip here
        for i, x in enumerate(cs):
            a = t + step * i
            fade = 12 if not calm else 18
            # all cells of a word revert together, `hold` frames after the last one has finished flipping
            revert_from = end + fade + hold
            cells.add(x, a, fade, revert_from - (a + fade), fade_back)
        t += step * L
    if calm:
        return cells
    # the moment: twice per loop a wave runs the tower a row at a time (about 1 s): bottom up, then top down
    rows = list(range(15, 31))
    for start, order in ((236, rows), (498, rows[::-1])):
        for k, r in enumerate(order):
            a0 = start + round(k * 60 / (len(rows) - 1))
            avail = [(c, rr) for (c, rr) in grid if rr == r and cells.free((c, rr), a0, a0 + 30)]
            rng.shuffle(avail)
            chosen = []
            for cell in avail:
                if all(abs(cell[0] - o[0]) > 1 for o in chosen):
                    chosen.append(cell)
                if len(chosen) == 3:
                    break
            for cell in chosen:
                cells.add(cell, a0, 8, 10, 8)
    return cells


def do_tower(doc, rd, loop, calm, rest):
    sc = rd.sc
    grid = tower_grid(sc)
    old = [i for i in loop.objs if i in {v[1] for v in grid.values()}]
    for a in (loop, calm, rest):
        for oid in old:
            a.drop_object(oid)
    out = {}
    for anim, is_calm, seed in ((loop, False, 11), (calm, True, 12)):
        cells = tower_motion(grid, is_calm, random.Random(seed))
        tr = cells.tracks()
        out[is_calm] = tr
        for scid, keys in tr.items():
            anim.set_color(scid, keys)
    # Loop and Calm key the same cells (a cell flipped in one and unkeyed in the other would stay flipped across the blend)
    for scid in set(out[False]) | set(out[True]):
        for anim, is_calm in ((loop, False), (calm, True)):
            if scid not in out[is_calm]:
                c0 = next(v[0] for v in grid.values() if v[1] == scid)
                anim.set_color(scid, [(0, c0, "hold"), (LOOP, c0, "hold")])
        c0 = next(v[0] for v in grid.values() if v[1] == scid)
        rest.set_color(scid, [(0, c0, "hold")])
    return {"cells loop": len(out[False]), "cells calm": len(out[True])}


# ---- the Spelling Bee hex stacks: independent coin spinners --------------------------------------------------------------------------
# plate -> rings from the inside out: (shape or wrapper-node id, is a wrapper node, hollow id or None)
HEX_PLATES = {
    1: [("9:66955", True, "9:66957"), ("9:10477", False, None), ("9:10489", False, None), ("9:10597", False, None)],
    2: [("9:66969", True, "9:66971"), ("9:10513", False, "9:93651"), ("9:10525", False, None), ("9:10585", False, None)],
    3: [("9:66983", True, "9:66985"), ("9:10549", False, None), ("9:10561", False, None), ("9:10573", False, None)],
}
HEX_DEAD = ("9:10719", "9:93780")                 # the back stack's spinning ring and its hollow: "little or nothing" there
HEX_EXTRA_RING_SPINS = ("9:10513",)               # already has a scaleX key from note 3 (re-keyed here)


def clone_hollow(doc, ring_id, name="Hex Ring Hollow"):
    """A dark copy of a ring, right behind it (the next line after the ring) with the same fill and stroke geometry."""
    i = doc.idx(ring_id)
    j = doc.end(i)
    new_id = None
    copy = []
    for l in doc.lines[i:j + 1]:
        copy.append(re.sub(r'\bid="[^"]+"', lambda m: f'id="{doc.new_id()}"', l))
    new_id = re.search(r'\bid="([^"]+)"', copy[0]).group(1)
    copy[0] = re.sub(r' name="[^"]*"', "", copy[0]).replace("<Shape", f'<Shape name="{name}"', 1)
    k = next(x for x, l in enumerate(copy) if "<Fill" in l)
    copy[k + 1] = re.sub(r'colorValue="[^"]+"', f'colorValue="{BLACK}"', copy[k + 1])
    doc.lines[j + 1:j + 1] = copy
    return new_id


def clone_keyed_object(anim, src, dst):
    """The KeyedObject of `src` repeated for `dst` with new ids (so the hollow builds and rests with its ring)."""
    if not anim.has(src):
        return
    d = anim.doc
    props = {}
    for prop, lines in anim.objs[src]["props"].items():
        props[prop] = [re.sub(r'\bid="[^"]+"', lambda m: f'id="{d.new_id()}"', l) for l in lines]
    anim.objs[dst] = {"id": d.new_id(), "props": props}


def hex_schedule(rng):
    rings = [(p, r) for p in HEX_PLATES for r in range(4)]
    starts = [10, 64, 118, 160, 200, 262, 314, 356, 410, 438, 500, 552]       # never 2 s (120 frames) without one; two overlaps
    while True:
        order = rings[:]
        rng.shuffle(order)
        if all(a[0] != b[0] for a, b in zip(order, order[1:])):
            break
    return [(s, pick, "full" if i in (3, 8) else rng.choice(("half", "half", "full"))) for i, (s, pick) in enumerate(zip(starts, order))]


def spin_keys(start, kind, depth):
    d = 26 if kind == "half" else 48
    half = d // 2
    if kind == "half":
        return [(start, 1.0, "sine.in"), (start + half, depth, "sine.out"), (start + d, 1.0, "hold")]
    q = d // 4
    return [(start, 1.0, "sine.in"), (start + q, depth, "sine.out"), (start + 2 * q, 1.0, "sine.in"), (start + 3 * q, depth, "sine.out"), (start + d, 1.0, "hold")]


def do_hex(doc, rd, loop, calm, rest, build, hollows):
    # the back stack's spin and the F copies are gone; the old small-hex curves are replaced
    for a in (loop, calm, rest):
        for oid in list(a.objs):
            for prop in ("scaleX",):
                nm = rd.sc.names.get(oid, "")
                if nm.startswith("Hex Plate B") or oid in {r[0] for pl in HEX_PLATES.values() for r in pl} or oid in HEX_DEAD:
                    a.drop_prop(oid, prop)
    ring_ids = [(r[0]) for pl in HEX_PLATES.values() for r in pl]
    # hollows for the rings that have none yet (cloned once, behind their ring, building and resting with it)
    for p, rings in HEX_PLATES.items():
        for idx, (rid, wrapped, hid) in enumerate(rings):
            if hid is None:
                hid = hollows.get(rid) or clone_hollow(doc, rid)
                hollows[rid] = hid
                rings[idx] = (rid, wrapped, hid)
                for a in (rest, build, loop, calm):
                    clone_keyed_object(a, rid, hid)
    seq = hex_schedule(random.Random(5))
    per_ring = {}
    for s, (p, r), kind in seq:
        per_ring.setdefault(HEX_PLATES[p][r][0], []).append((s, kind))
    for anim, depth in ((loop, 0.07), (calm, 0.45)):
        for rid, evs in per_ring.items():
            keys = [(0, 1.0, "hold")]
            for s, kind in sorted(evs):
                ks = spin_keys(s, kind, depth)
                if keys[-1][0] == ks[0][0]:
                    keys.pop()
                keys += ks
            keys.append((LOOP, 1.0, "hold"))
            anim.set(rid, "scaleX", keys)
    for rid in per_ring:
        rest.set(rid, "scaleX", [(0, 1.0, "hold")])
    return {"spins": len(seq), "rings": len(per_ring), "schedule": [(s, p, r, k) for s, (p, r), k in seq]}


# ---- Strands: the molecule breathes --------------------------------------------------------------------------------------------------
STR_NODES = {"A": "9:4018", "B": "9:4024", "C": "9:4043", "D": "9:4012", "E": "9:4049"}
STR_BASE = {"A": (78.25, 20.75), "B": (108.25, 73.25), "C": (48.25, 73.25), "D": (20.75, 125.75), "E": (135.75, 125.75)}
STR_LIGHTS = {"9:4006": ("A", (0.0, -10.0)), "9:3994": ("B", (0.0, -11.667)), "9:4000": ("C", (0.0, -11.667))}
STR_BARS = {"9:4030": ("A", "B"), "9:4055": ("C", "D"), "9:4068": ("B", "E"), "9:4081": ("A", "C"), "9:4094": ("C", "E"),
            "9:4107": ("B", "D"), "9:4120": ("D", "E")}
# per node: (cycles in x, cycles in y, amplitude x, amplitude y, phase x, phase y)
STR_DRIFT = {"A": (1, 2, 2.6, 2.2, 0.3, 1.9), "B": (2, 1, 2.8, 2.4, 2.2, 0.6), "C": (1, 1, 2.4, 2.8, 4.0, 2.9),
             "D": (2, 2, 3.0, 2.0, 1.1, 5.0), "E": (1, 2, 2.2, 2.6, 5.2, 3.7)}
SWELL = 0.025
SWELL_CYCLES = 2


def str_state(t, amp):
    c = (sum(b[0] for b in STR_BASE.values()) / 5, sum(b[1] for b in STR_BASE.values()) / 5)
    d = {}
    for n, (kx, ky, ax, ay, px, py) in STR_DRIFT.items():
        d[n] = (amp * ax * math.sin(2 * math.pi * kx * t / LOOP + px), amp * ay * math.sin(2 * math.pi * ky * t / LOOP + py))
    mean = (sum(v[0] for v in d.values()) / 5, sum(v[1] for v in d.values()) / 5)
    s = 1 + amp * SWELL * (1 - math.cos(2 * math.pi * SWELL_CYCLES * t / LOOP)) / 2
    # the swell is about the centre; the drifts are shifted so their average never moves it
    pos = {n: (c[0] + (STR_BASE[n][0] + d[n][0] - mean[0] - c[0]) * s, c[1] + (STR_BASE[n][1] + d[n][1] - mean[1] - c[1]) * s) for n in d}
    return pos, s


def str_bar_geometry(sc):
    """For each bar: the angle and length of its end-to-end line at rest, and which vertex sits at its second end."""
    out = {}
    for bid, (a, b) in STR_BARS.items():
        pa, pb = STR_BASE[a], STR_BASE[b]
        out[bid] = (math.atan2(pb[1] - pa[1], pb[0] - pa[0]), math.hypot(pb[0] - pa[0], pb[1] - pa[1]))
    return out


def straighten_bars(doc, sc):
    """Redraw each bar as a straight line along its own x axis, its node turned to the rest angle: same picture, but the line can now be
    stretched and turned by two keys (rotation, scaleX) instead of by four vertices."""
    geo = str_bar_geometry(sc)
    for bid, (ang, length) in geo.items():
        bar = sc.by_id[bid]
        a, b = STR_BARS[bid]
        i = doc.idx(bid)
        j = doc.end(i)
        # the first vertex of each shape is the one at the second end b (mid + half), as the art was drawn: check and fix
        for shape in bar.findall("Shape"):
            path = shape.find("PointsPath")
            v1, v2 = list(path)
            pa, pb = STR_BASE[a], STR_BASE[b]
            mid = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
            end_b = (pb[0] - mid[0], pb[1] - mid[1])
            first_is_b = abs(float(v1.get("x", 0)) - end_b[0]) < 0.01 and abs(float(v1.get("y", 0)) - end_b[1]) < 0.01
            new = [(+length / 2, 0.0), (-length / 2, 0.0)] if first_is_b else [(-length / 2, 0.0), (+length / 2, 0.0)]
            for v, (x, y) in zip((v1, v2), new):
                k = doc.idx(v.get("id"))
                attrs = (f' x="{num(x)}"' if abs(x) > 1e-9 else "") + (f' y="{num(y)}"' if abs(y) > 1e-9 else "")
                doc.lines[k] = re.sub(r'<StraightVertex[^>]*?(\s*id=)', lambda m: f"<StraightVertex{attrs}{m.group(1)}", doc.lines[k], count=1)
        # the bar's own turn, in radians, so it draws as before
        line = doc.lines[doc.idx(bid)]
        assert "rotation=" not in line
        doc.lines[doc.idx(bid)] = line.replace("<Node ", f'<Node rotation="{num(ang)}" ', 1) if "rotation=" not in line else line


def do_strands(doc, rd, loop, calm, rest):
    sc = rd.sc
    geo = str_bar_geometry(sc)
    summary = {}
    for anim, amp in ((loop, 1.0), (calm, 0.55)):
        for a in (anim,):
            for oid in list(a.objs):
                if oid in set(STR_NODES.values()) | set(STR_LIGHTS) | set(STR_BARS):
                    a.drop_object(oid)
        for n, oid in STR_NODES.items():
            for prop, fn in (("x", lambda t, n=n: str_state(t, amp)[0][n][0]), ("y", lambda t, n=n: str_state(t, amp)[0][n][1]),
                             ("scaleX", lambda t: str_state(t, amp)[1]), ("scaleY", lambda t: str_state(t, amp)[1])):
                anim.set(oid, prop, hermite(fn, KNOTS))
        for oid, (n, off) in STR_LIGHTS.items():
            for prop, fn in (("x", lambda t, n=n, off=off: str_state(t, amp)[0][n][0] + off[0] * str_state(t, amp)[1]),
                             ("y", lambda t, n=n, off=off: str_state(t, amp)[0][n][1] + off[1] * str_state(t, amp)[1]),
                             ("scaleX", lambda t: str_state(t, amp)[1]), ("scaleY", lambda t: str_state(t, amp)[1])):
                anim.set(oid, prop, hermite(fn, KNOTS))
        for bid, (a, b) in STR_BARS.items():
            ang0, len0 = geo[bid]

            def mid(t, k, a=a, b=b):
                p = str_state(t, amp)[0]
                return (p[a][k] + p[b][k]) / 2

            def angle(t, a=a, b=b):
                p = str_state(t, amp)[0]
                return math.atan2(p[b][1] - p[a][1], p[b][0] - p[a][0])

            def stretch(t, a=a, b=b, len0=len0):
                p = str_state(t, amp)[0]
                return math.hypot(p[b][0] - p[a][0], p[b][1] - p[a][1]) / len0
            anim.set(bid, "x", hermite(lambda t: mid(t, 0), KNOTS))
            anim.set(bid, "y", hermite(lambda t: mid(t, 1), KNOTS))
            anim.set(bid, "rotation", hermite(angle, KNOTS))
            anim.set(bid, "scaleX", hermite(stretch, KNOTS))
            anim.set(bid, "scaleY", [(0, 1.0, "hold"), (LOOP, 1.0, "hold")])
            anim.set(bid, "opacity", [(0, 1.0, "hold"), (LOOP, 1.0, "hold")])
    for oid in set(STR_NODES.values()) | set(STR_LIGHTS) | set(STR_BARS):
        if loop.has(oid):
            for prop in loop.objs[oid]["props"]:
                rest.set(oid, prop, [(0, loop.first_value(oid, prop), "hold")])
    return {"props": sum(len(o["props"]) for o in loop.objs.values())}


# ---- Coss: the roaming glint -------------------------------------------------------------------------------------------------------
GLINTS = [("9:10217", 70), ("9:10311", 270), ("9:9933", 470)]          # tile (the blue shape), start frame
GLINT_FRAMES = 24


def tile_info(sc, tile_id):
    tile = sc.by_id[tile_id]
    parent = sc.parent[tile]
    return tile, parent


def make_glints(doc, sc):
    """One white band per glint, inserted as the first child of its tile's node (so it draws over the tile), clipped to the tile."""
    out = []
    ln = math.hypot(25, 27.5)
    dx, dy = 25 / ln, 27.5 / ln                      # along the tile's diagonal
    nx, ny = dy, -dx                                 # across it, towards the upper right
    half_len, thick = 32.0, 9.0
    pts = [(-half_len * dx - thick / 2 * nx, -half_len * dy - thick / 2 * ny), (half_len * dx - thick / 2 * nx, half_len * dy - thick / 2 * ny),
           (half_len * dx + thick / 2 * nx, half_len * dy + thick / 2 * ny), (-half_len * dx + thick / 2 * nx, -half_len * dy + thick / 2 * ny)]
    reach = 12.5 * abs(nx) + 13.75 * abs(ny) + thick / 2 + 1.5
    for tile_id, start in GLINTS:
        tile, parent = tile_info(sc, tile_id)
        tx, ty = float(tile.get("x", 0)), float(tile.get("y", 0))
        # the parent node's first child line
        pi = doc.idx(parent.get("id"))
        ind = " " * (len(doc.lines[pi]) - len(doc.lines[pi].lstrip()) + 4)
        gid = doc.new_id()
        s0 = -reach
        x0, y0 = tx + s0 * nx, ty + s0 * ny
        verts = "\n".join(f'{ind}        <StraightVertex x="{num(px)}" y="{num(py)}" id="{doc.new_id()}"/>' for px, py in pts)
        block = [f'{ind}<Shape x="{num(x0)}" y="{num(y0)}" opacity="0" name="Glint" id="{gid}">',
                 f'{ind}    <PointsPath isClosed="true" id="{doc.new_id()}">', verts,
                 f'{ind}    </PointsPath>',
                 f'{ind}    <Fill id="{doc.new_id()}">', f'{ind}        <SolidColor colorValue="FFFFFFFF" id="{doc.new_id()}"/>', f'{ind}    </Fill>',
                 f'{ind}    <Stroke thickness="1.5" cap="round" join="round" transformAffectsStroke="false" id="{doc.new_id()}">',
                 f'{ind}        <SolidColor colorValue="{LINE}" id="{doc.new_id()}"/>', f'{ind}    </Stroke>',
                 f'{ind}    <ClippingShape sourceId="{tile_id}" name="Tile Clip" id="{doc.new_id()}"/>',
                 f'{ind}</Shape>']
        pi = doc.idx(parent.get("id"))
        doc.lines[pi + 1:pi + 1] = block
        out.append({"id": gid, "start": start, "x0": x0, "y0": y0, "x1": tx - s0 * nx, "y1": ty - s0 * ny})
    return out


def do_coss(doc, rd, loop, calm, rest, glints):
    for anim, keep in ((loop, 3), (calm, 2)):
        for k, g in enumerate(glints):
            t = g["start"]
            on = k < keep
            for prop, a, b in (("x", g["x0"], g["x1"]), ("y", g["y0"], g["y1"])):
                if on:
                    anim.set(g["id"], prop, [(0, a, "hold"), (t, a, "power1.inOut"), (t + GLINT_FRAMES, b, "hold"), (t + GLINT_FRAMES + 1, a, "hold"), (LOOP, a, "hold")])
                else:
                    anim.set(g["id"], prop, [(0, a, "hold"), (LOOP, a, "hold")])
            if on:
                anim.set(g["id"], "opacity", [(0, 0.0, "hold"), (t, 1.0, "hold"), (t + GLINT_FRAMES + 1, 0.0, "hold"), (LOOP, 0.0, "hold")])
            else:
                anim.set(g["id"], "opacity", [(0, 0.0, "hold"), (LOOP, 0.0, "hold")])
    for g in glints:
        rest.set(g["id"], "x", [(0, g["x0"], "hold")])
        rest.set(g["id"], "y", [(0, g["y0"], "hold")])
        rest.set(g["id"], "opacity", [(0, 0.0, "hold")])
    return {"glints": len(glints)}


# ---- the dome (SpB_01): pops, a coin spin, a pangram ripple ------------------------------------------------------------------------------
DOME_CELLS = {"top": ["9:4464", "9:4584"], "tr": ["9:4452", "9:4560"], "lr": ["9:4416", "9:4572"], "bottom": ["9:4596"],
              "ll": ["9:4428", "9:4548"], "tl": ["9:4440", "9:4536"], "centre": ["9:4476", "9:4488", "9:4608"]}
DOME_AROUND = ["top", "tr", "lr", "bottom", "ll", "tl"]          # clockwise, the pangram order, the centre last
DOME_CENTRE_OUTER = "9:4608"


def pulse_keys(t, amp, up=10, down=14):
    return [(t, 1.0, "power2.out"), (t + up, 1.0 + amp, "power2.inOut"), (t + up + down, 1.0, "hold")]


def do_dome(doc, rd, loop, calm, rest, hollow):
    pops_loop = [(38, "tr"), (104, "ll"), (170, "top"), (236, "lr"), (302, "tl"), (454, "bottom"), (520, "tr")]
    pops_calm = [(104, "ll"), (236, "lr"), (454, "bottom")]
    for anim, pops, amp, ripple, spins in ((loop, pops_loop, 0.05, 372, [(90, "half"), (478, "full")]),
                                           (calm, pops_calm, 0.04, 372, [(300, "half")])):
        events = {}        # (shape id, prop) -> [(frame, keys)]
        for t, cell in pops:
            for sid in DOME_CELLS[cell]:
                for prop in ("scaleX", "scaleY"):
                    events.setdefault((sid, prop), []).append(pulse_keys(t, amp))
        ramp = amp * 1.0
        order = DOME_AROUND + ["centre"]
        if anim is loop:
            for k, cell in enumerate(order):
                for sid in DOME_CELLS[cell]:
                    for prop in ("scaleX", "scaleY"):
                        events.setdefault((sid, prop), []).append(pulse_keys(ripple + k * 7, ramp, 9, 12))
        for t, kind in spins:
            for sid in DOME_CELLS["centre"]:
                events.setdefault((sid, "scaleX"), []).append(spin_keys(t, kind, 0.07 if anim is loop else 0.45))
        for (sid, prop), evs in events.items():
            keys = [(0, 1.0, "hold")]
            for ks in sorted(evs):
                if keys[-1][0] == ks[0][0]:
                    keys.pop()
                assert keys[-1][0] < ks[0][0], (sid, prop, keys[-1], ks[0])
                keys += ks
            keys.append((LOOP, 1.0, "hold"))
            anim.set(sid, prop, keys)
    # Loop and Calm key the same properties
    for anim, other in ((loop, calm), (calm, loop)):
        for oid, o in list(other.objs.items()):
            for prop in o["props"]:
                if not anim.has(oid, prop):
                    anim.set(oid, prop, [(0, 1.0, "hold"), (LOOP, 1.0, "hold")])
    return {"pops": len(pops_loop)}


# ---- the Connections stack: cell lights, rise and settle, the purple slab's proud lift ----------------------------------------------------
SLABS = {"lime": ("9:4134", "9:4397", "9:4207"), "purple": ("9:4292", "9:4403", "9:4335"), "green": ("9:4351", None, "9:4376"), "blue": ("9:4223", "9:4409", None)}
LIGHT_RUNS = [("lime", 1, 0, 5, 14), ("purple", 0, 1, 4, 98), ("green", 1, 0, 4, 168), ("lime", 3, 2, 5, 232), ("purple", 2, 0, 5, 306),
              ("lime", 0, 1, 4, 392), ("green", 0, 1, 3, 452), ("purple", 1, 2, 4, 508)]
LIGHT_FADE_IN, LIGHT_HOLD, LIGHT_FADE_OUT, LIGHT_STEP = 8, 24, 14, 12


def slab_cells(sc, slab):
    node_id, side_id, body_id = SLABS[slab]
    node = sc.by_id[node_id]
    body = sc.by_id[body_id]
    rect = body.find("Rectangle")
    if rect is not None:
        bx, bw, bh = float(body.get("x", 0)), float(rect.get("width")), float(rect.get("height"))
    else:                       # the green slab's front is the olive rectangle too (9:4376)
        raise KeyError(body_id)
    vx, hy = [], []
    for sh in node.findall("Shape"):
        p = sh.find("PointsPath")
        if p is None or sh.find("Fill") is not None and len(list(p)) > 2:
            continue
        v = list(p)
        if len(v) != 2:
            continue
        x0, y0, x1, y1 = (float(v[0].get("x", 0)), float(v[0].get("y", 0)), float(v[1].get("x", 0)), float(v[1].get("y", 0)))
        if abs(x0 - x1) < 1e-6:
            vx.append(float(sh.get("x", 0)))
        elif abs(y0 - y1) < 1e-6:
            hy.append(float(sh.get("y", 0)))
    cols = sorted({bx - bw / 2, bx + bw / 2, *[x for x in vx if bx - bw / 2 < x < bx + bw / 2]})
    rows = sorted({-bh / 2, bh / 2, *[y for y in hy if -bh / 2 < y < bh / 2]})
    return cols, rows


def make_lights(doc, sc):
    """Overlay rectangles for the cells the runs use, one lighter shade of the slab, clipped to the slab body, right under the grid lines."""
    cells = {}
    shades = {}
    for slab, row, c0, L, start in LIGHT_RUNS:
        cols, rows = slab_cells(sc, slab)
        for k in range(L):
            key = (slab, row, c0 + k)
            assert key[2] < len(cols) - 1 and row < len(rows) - 1, (slab, row, c0, L, len(cols), len(rows))
            cells.setdefault(key, None)
    made = {}
    for slab in SLABS:
        want = sorted(k for k in cells if k[0] == slab)
        if not want:
            continue
        node_id, side_id, body_id = SLABS[slab]
        node = sc.by_id[node_id]
        body = sc.by_id[body_id]
        body_fill = next(next(f.iter("SolidColor")) for f in body if f.tag == "Fill").get("colorValue")
        shade = mix(body_fill, "FFFFFFFF", 0.55)
        cols, rows = slab_cells(sc, slab)
        ni = doc.idx(node_id)
        ind = " " * (len(doc.lines[ni]) - len(doc.lines[ni].lstrip()) + 4)
        bi = doc.idx(body_id)
        block = []
        for (_, row, col) in want:
            x0, x1, y0, y1 = cols[col], cols[col + 1], rows[row], rows[row + 1]
            sid = doc.new_id()
            made[(slab, row, col)] = sid
            block += [f'{ind}<Shape x="{num((x0 + x1) / 2)}" y="{num((y0 + y1) / 2)}" opacity="0" name="Cell Light" id="{sid}">',
                      f'{ind}    <Rectangle width="{num(x1 - x0)}" height="{num(y1 - y0)}" id="{doc.new_id()}"/>',
                      f'{ind}    <Fill id="{doc.new_id()}">', f'{ind}        <SolidColor colorValue="{shade}" id="{doc.new_id()}"/>', f'{ind}    </Fill>',
                      f'{ind}    <ClippingShape sourceId="{body_id}" name="Slab Clip" id="{doc.new_id()}"/>', f'{ind}</Shape>']
        bi = doc.idx(body_id)
        doc.lines[bi:bi] = block
    return made


def slab_y_events(slab, calm):
    """The slab's rise-and-settle windows (frame, up, down, amplitude) and its place in the purple lift."""
    base = {"green": [(20, 90, 110, 1.2), (430, 70, 90, 0.9)], "lime": [(100, 100, 100, 1.5), (470, 60, 70, 1.0)],
            "purple": [(40, 90, 100, 1.6), (440, 70, 70, 1.0)], "blue": [(180, 110, 120, 0.8)]}[slab]
    if calm:
        base = [(a, u + 20, d + 20, amp * 0.6) for a, u, d, amp in base[:1]]
    moment = {"purple": (330, 14, 22, 3.2), "lime": (338, 14, 22, 1.9), "green": (346, 14, 22, 1.2)}.get(slab)
    return base, (None if calm else moment)


def y_keys(y0, base, moment):
    keys = [(0, y0, "hold")]
    evs = [(a, u, d, amp) for a, u, d, amp in base] + ([moment] if moment else [])
    for a, u, d, amp in sorted(evs):
        if keys[-1][0] == a:
            keys.pop()
        assert keys[-1][0] < a, (keys[-1], a)
        keys += [(a, y0, "sine.inOut" if (a, u, d, amp) in base else "power2.out"), (a + u, y0 - amp, "sine.inOut" if (a, u, d, amp) in base else "power2.inOut"), (a + u + d, y0, "hold")]
    keys.append((LOOP, y0, "hold"))
    return keys


def do_connections(doc, rd, loop, calm, rest, lights):
    sc = rd.sc
    # the old slide-and-lock goes; the slabs only breathe
    for anim, runs in ((loop, LIGHT_RUNS), (calm, LIGHT_RUNS[::2])):
        calm_ = anim is calm
        for slab, (node_id, side_id, body_id) in SLABS.items():
            base, moment = slab_y_events(slab, calm_)
            y0 = rd.static(node_id, "y")
            ys = y_keys(y0, base, moment)
            anim.set(node_id, "y", ys)
            if side_id:
                anim.set(side_id, "y", [(f, v + (rd.static(side_id, "y") - y0), h) for f, v, h in ys])
        for sid in lights.values():
            anim.set(sid, "opacity", [(0, 0.0, "hold"), (LOOP, 0.0, "hold")])
        for slab, row, c0, L, start in runs:
            per = {}
            for k in range(L):
                sid = lights[(slab, row, c0 + k)]
                a = start + k * LIGHT_STEP
                per[sid] = [(0, 0.0, "hold"), (a, 0.0, "power1.inOut"), (a + LIGHT_FADE_IN, 1.0, "hold"), (a + LIGHT_FADE_IN + LIGHT_HOLD, 1.0, "power1.inOut"),
                            (a + LIGHT_FADE_IN + LIGHT_HOLD + LIGHT_FADE_OUT, 0.0, "hold"), (LOOP, 0.0, "hold")]
            for sid, keys in per.items():
                anim.set(sid, "opacity", keys)
    for anim in (loop, calm):
        for oid in anim.objs:
            for prop in anim.objs[oid]["props"]:
                if not rest.has(oid, prop):
                    rest.set(oid, prop, [(0, anim.first_value(oid, prop), "hold")])
    return {"lights": len(lights)}


# ---- the clouds ---------------------------------------------------------------------------------------------------------------------
CLOUD_SVG_OFFSET = (494.25, 420.531)          # the cloud SVG's artboard origin in the city frame
CLOUD_CLASS = {"Vector": "cloud", "Vector_2": "cloud", "Vector_3": "cloud", "Vector_9": "cloud", "Vector_10": "cloud",
               "Vector_4": "dot", "Vector_5": "dot", "Vector_6": "dot", "Vector_7": "pill", "Vector_8": "pill"}
# whole-second periods that divide the 120 s loop: 8.57 .. 13.33 s for the clouds, 4 to 6 s for the small ones
CLOUD_CYCLES_LOOP = 7200
CLOUD_X = {"Vector": (13, 4.0, 0.7), "Vector_2": (11, 3.4, 2.4), "Vector_3": (10, 4.6, 4.1), "Vector_9": (9, 3.0, 5.5), "Vector_10": (14, 3.8, 1.2)}
CLOUD_Y = {"Vector": (17, 1.1, 1.0), "Vector_2": (19, 1.4, 3.2), "Vector_3": (15, 1.0, 5.1), "Vector_9": (21, 1.3, 0.3), "Vector_10": (18, 1.2, 4.4)}
SMALL_Y = {"Vector_4": (25, 1.8, 0.4), "Vector_5": (30, 1.5, 2.6), "Vector_6": (20, 1.6, 4.9), "Vector_7": (24, 1.2, 1.7), "Vector_8": (30, 1.4, 3.9)}


def cloud_shapes(doc):
    svg = SCRATCH_SVG.read_text()
    root = ET.fromstring(svg)
    shapes = []
    for el in root.iter("{http://www.w3.org/2000/svg}path"):
        pid = el.get("id")
        if pid not in CLOUD_CLASS:
            continue
        subs = svg_to_rml.parse_path(el.get("d"))
        ox, oy = CLOUD_SVG_OFFSET
        for sub, _ in subs:
            for v in sub:
                v.x += ox
                v.y += oy
        shapes.append((pid, subs))
    return shapes


def cloud_xml(doc, pid, subs, ind):
    x = svg_to_rml.shape_xml(CLOUD_FILL, subs, doc.new_id)
    stroke = f'<Stroke thickness="1.5" cap="round" join="round" transformAffectsStroke="false" id="{doc.new_id()}"><SolidColor colorValue="{LINE}" id="{doc.new_id()}"/></Stroke>'
    x = x.replace("</Shape>", stroke + "</Shape>")
    x = x.replace("<Shape", f'<Shape name="Chapter 4 Cloud {pid.replace("Vector", "").strip("_") or "1"}"', 1)
    from xml.dom import minidom
    pretty = minidom.parseString(x).documentElement.toprettyxml(indent="    ")
    return [ind + l for l in pretty.split("\n") if l.strip()], re.search(r'\bx="([^"]+)"', x).group(1) if re.search(r'<Shape name="[^"]*" x="', x) else None


def sine_keys(period_frames, amp, phase, centre):
    """Keys at each extreme of centre + amp * sin(2 pi t / period + phase), over the whole 7200 frame loop, eased with sine.inOut."""
    f = lambda t: centre + amp * math.sin(2 * math.pi * t / period_frames + phase)
    # extremes at t where the phase is a quarter turn
    ts = []
    k = math.ceil((-phase - math.pi / 2) / math.pi)
    while True:
        t = (k * math.pi + math.pi / 2 - phase) * period_frames / (2 * math.pi)
        if t > CLOUD_CYCLES_LOOP:
            break
        if t >= 0:
            ts.append(t)
        k += 1
    keys = [(0, f(0), "hold")]
    # between the start and the first extreme the curve is a part of a half wave: use the ease, close enough at an amplitude of a few units
    for t in ts:
        keys.append((round(t), f(t), "sine.inOut"))
    keys.append((CLOUD_CYCLES_LOOP, f(CLOUD_CYCLES_LOOP), "hold"))
    # remove duplicate frames, set the interpolation of each key to leave it
    out = []
    for fr, v, how in keys:
        if out and out[-1][0] == fr:
            out.pop()
        out.append((fr, v, how))
    return out


def add_clouds(doc, sc):
    shapes = cloud_shapes(doc)
    fp = doc.idx("9:20848")
    fp_end = doc.end(fp)
    ind_fp = " " * (len(doc.lines[fp]) - len(doc.lines[fp].lstrip()))
    gid = doc.new_id()
    ind = ind_fp + "    "
    block = [f'{ind}<Node name="Chapter 4 Clouds" id="{gid}">']
    sids = {}
    for pid, subs in shapes:
        lines, _ = cloud_xml(doc, pid, subs, ind + "    ")
        sid = re.search(r'\bid="([^"]+)"', lines[0]).group(1)
        sids[pid] = (sid, float(re.search(r'<Shape[^>]*? x="([^"]+)"', lines[0]).group(1)) if re.search(r'<Shape[^>]*? x="([^"]+)"', lines[0]) else 0.0,
                     float(re.search(r'<Shape[^>]*? y="([^"]+)"', lines[0]).group(1)) if re.search(r'<Shape[^>]*? y="([^"]+)"', lines[0]) else 0.0)
        block += lines
    block.append(f"{ind}</Node>")
    # last child of the floor plane = drawn behind every building
    doc.lines[fp_end:fp_end] = block
    return gid, sids


def add_cloud_layers(doc, gid, sids):
    n = doc.new_id
    anim = f"{ROOM} Clouds Drift"
    aid = n()
    # the drift animation: 7200 frames (120 s) so every period closes exactly
    lines = [f'        <LinearAnimation fps="60" duration="{CLOUD_CYCLES_LOOP}" loopValue="loop" name="{anim}" id="{aid}">']
    body = []
    for pid, (sid, x, y) in sids.items():
        body.append(f'            <KeyedObject objectId="{sid}" id="{n()}">')
        if pid in CLOUD_X:
            cyc, amp, ph = CLOUD_X[pid]
            keys = sine_keys(CLOUD_CYCLES_LOOP / cyc, amp, ph, x)
            body.append(f'                <KeyedProperty property="x" id="{n()}">')
            body += key_lines(doc, keys, " " * 20)
            body.append("                </KeyedProperty>")
        cyc, amp, ph = (CLOUD_Y.get(pid) or SMALL_Y[pid])
        keys = sine_keys(CLOUD_CYCLES_LOOP / cyc, amp, ph, y)
        body.append(f'                <KeyedProperty property="y" id="{n()}">')
        body += key_lines(doc, keys, " " * 20)
        body.append("                </KeyedProperty>")
        body.append("            </KeyedObject>")
    lines += body + ["        </LinearAnimation>"]
    shown, hidden = n(), n()
    fade_show = [f'        <LinearAnimation fps="60" duration="1" name="{ROOM} Clouds Shown" id="{shown}">',
                 f'            <KeyedObject objectId="{gid}" id="{n()}">', f'                <KeyedProperty property="opacity" id="{n()}">',
                 f'                    <KeyFrameDouble value="1" id="{n()}"/>', "                </KeyedProperty>", "            </KeyedObject>", "        </LinearAnimation>"]
    fade_hide = [f'        <LinearAnimation fps="60" duration="1" name="{ROOM} Clouds Hidden" id="{hidden}">',
                 f'            <KeyedObject objectId="{gid}" id="{n()}">', f'                <KeyedProperty property="opacity" id="{n()}">',
                 f'                    <KeyFrameDouble id="{n()}"/>', "                </KeyedProperty>", "            </KeyedObject>", "        </LinearAnimation>"]
    sc = Scene(doc.path)
    loop_anim = next(e for e in sc.root.iter("LinearAnimation") if e.get("name") == f"{ROOM} Loop")
    li = doc.idx(loop_anim.get("id"))
    doc.lines[li:li] = lines + fade_show + fade_hide
    # state machine layers
    rev = lambda v: city._cond_bool(n, city.REVEAL_P, v)
    pad = " " * 16

    def tr(to, conds=(), ms=0):
        attrs = f' stateToId="{to}" duration="{ms}"' + (' interpolationType="cubic"' if ms else "")
        head = f"<StateTransition{attrs} id=\"{n()}\">"
        out = [head] + (["    " + f'<CubicEaseInterpolator x1="0.45" y1="0" x2="0.55" y2="1" id="{n()}"/>'] if ms else [])
        out += ["    " + l for c in conds for l in c] + ["</StateTransition>"]
        return out
    # layer 1: the drift
    ds = n()
    drift = [f'            <StateMachineLayer name="{ROOM} Clouds Drift" id="{n()}">', f'{pad}<AnyState x="160" y="200" id="{n()}"/>',
             f'{pad}<ExitState x="720" y="200" id="{n()}"/>', f'{pad}<EntryState x="0" y="0" id="{n()}">',
             f'{pad}    <StateTransition stateToId="{ds}" id="{n()}"/>', f'{pad}</EntryState>',
             f'{pad}<AnimationState animationId="{aid}" x="160" y="0" id="{ds}"/>', "            </StateMachineLayer>"]
    # layer 2: shown / hidden on reveal (the boolean the fireworks play on), no new setting
    start, sh, hd = n(), n(), n()
    fade = [f'            <StateMachineLayer name="{ROOM} Clouds Fade" id="{n()}">', f'{pad}<AnyState x="160" y="200" id="{n()}"/>',
            f'{pad}<ExitState x="720" y="200" id="{n()}"/>', f'{pad}<EntryState x="0" y="0" id="{n()}">',
            f'{pad}    <StateTransition stateToId="{start}" id="{n()}"/>', f'{pad}</EntryState>']
    fade += [f'{pad}<AnimationState animationId="{shown}" x="160" y="0" id="{start}">']
    fade += [pad + "    " + l for l in tr(hd, (rev("true"),)) + tr(sh, (rev("false"),))] + [f"{pad}</AnimationState>"]
    fade += [f'{pad}<AnimationState animationId="{shown}" x="360" y="0" id="{sh}">'] + [pad + "    " + l for l in tr(hd, (rev("true"),), 500)] + [f"{pad}</AnimationState>"]
    fade += [f'{pad}<AnimationState animationId="{hidden}" x="560" y="0" id="{hd}">'] + [pad + "    " + l for l in tr(sh, (rev("false"),), 500)] + [f"{pad}</AnimationState>"]
    fade.append("            </StateMachineLayer>")
    si = max(i for i, l in enumerate(doc.lines) if l.strip() == "</StateMachine>")
    doc.lines[si:si] = drift + fade


# ---- the main pass -----------------------------------------------------------------------------------------------------------------------
def main():
    argv = sys.argv
    path = Path(argv[argv.index("--scene") + 1]) if "--scene" in argv else chapter_dir("ch3") / "scene.rml"
    write = "--write" in argv
    doc = Doc(path)
    assert not any('name="Chapter 4 Clouds"' in l for l in doc.lines), "already applied"
    rd = Reader(path)
    sc = rd.sc
    report = {}

    # 1. cleanup
    dead = ["9:4620", "9:6834", "9:7340", HEX_DEAD[1]]
    removed_lines, removed_keys, removed_ids = delete_elements_and_keys(doc, dead)
    report["cleanup"] = {"lines": removed_lines, "keyed objects": removed_keys, "elements": removed_ids}
    if "--cleanup-only" in argv:          # to measure what the cleanup alone saves
        print(report)
        if write:
            doc.save()
        return

    # structural inserts first (they move lines), then the animations
    hollows = {}
    for p, rings in HEX_PLATES.items():
        for idx, (rid, wrapped, hid) in enumerate(rings):
            if hid is None:
                hid = clone_hollow(doc, rid)
                hollows[rid] = hid
                rings[idx] = (rid, wrapped, hid)
    sc_now = Scene(doc.path) if False else sc
    glints = make_glints(doc, sc)
    lights = make_lights(doc, sc)
    # the dome centre's hollow (behind the outer ring)
    dome_hollow = clone_hollow(doc, DOME_CENTRE_OUTER, "Dome Centre Hollow")
    cloud_gid, cloud_ids = add_clouds(doc, sc)
    straighten_bars(doc, sc)

    names = {"Tower": f"{ROOM} City Tower", "Hex": f"{ROOM} City Hex", "Strands": f"{ROOM} City Strands", "Coss": f"{ROOM} City Coss",
             "Dome": f"{ROOM} City Dome", "Connections": f"{ROOM} City Connections"}

    def open_anims(b):
        n = names[b]
        return Anim(doc, n), Anim(doc, n + " Calm"), Anim(doc, n + " Rest"), Anim(doc, n + " Build")

    def commit(*anims):
        for a in anims:
            a.commit()

    # the Hex hollows need to be present in Rest/Build/Loop/Calm before the spins are written
    loop, calm, rest, build = open_anims("Hex")
    for rid, hid in hollows.items():
        for a in (rest, build, loop, calm):
            clone_keyed_object(a, rid, hid)
    report["hex"] = do_hex(doc, rd, loop, calm, rest, build, hollows)
    # the dead ring's keys: its scaleX is dropped in do_hex; its hollow was deleted with all its keys
    commit(loop, calm, rest, build)

    loop, calm, rest, build = open_anims("Tower")
    report["tower"] = do_tower(doc, rd, loop, calm, rest)
    commit(loop, calm, rest, build)

    loop, calm, rest, build = open_anims("Strands")
    report["strands"] = do_strands(doc, rd, loop, calm, rest)
    commit(loop, calm, rest, build)

    loop, calm, rest, build = open_anims("Coss")
    report["coss"] = do_coss(doc, rd, loop, calm, rest, glints)
    commit(loop, calm, rest, build)

    loop, calm, rest, build = open_anims("Dome")
    # the dome centre's hollow builds, rests and holds with its outer ring
    for a in (rest, build, loop, calm):
        clone_keyed_object(a, DOME_CENTRE_OUTER, dome_hollow)
    report["dome"] = do_dome(doc, rd, loop, calm, rest, dome_hollow)
    commit(loop, calm, rest, build)

    loop, calm, rest, build = open_anims("Connections")
    report["connections"] = do_connections(doc, rd, loop, calm, rest, lights)
    commit(loop, calm, rest, build)

    add_cloud_layers(doc, cloud_gid, cloud_ids)
    report["clouds"] = {"shapes": len(cloud_ids)}
    for k, v in report.items():
        print(k, v)
    if write:
        doc.save()
        print("written", path)
    else:
        print("dry run: nothing written")


if __name__ == "__main__":
    main()
