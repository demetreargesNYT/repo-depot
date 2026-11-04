"""Measure Chapter 4's fireworks: every piece's world-space box at every frame of "Chapter 4 Fireworks Loop".

    python3 chapters/ch3/scripts/ch3_c4_fireworks_measure.py [--scene PATH]

Per gate it prints the highest point any visible piece reaches (smallest y, with the stroke) among the pieces whose box touches
x 540..955 (the phone column plus a little), the frame it happens and which piece, and the same for the whole artboard width.
Pieces with opacity 0 (their own or an ancestor's) are skipped; a Solo draws only its active child; a piece whose scale is 0
but has a stroke is reported as a dot (a non-scaling stroke still draws one).
"""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
from import_room import affine, compose
from rml_read import Scene, chapter_dir
from rooms_sheet import Sheet

ANIM = "Chapter 4 Fireworks Loop"
GATES = ("Wordle", "Connections", "Strands", "Spelling Bee", "Crossword")
COLUMN = (540.0, 955.0)
LIMIT_Y = 440.0
PAD = 1.0                       # half the 1.5 stroke plus a little for the round joins
GEOM = ("Node", "Shape", "Solo")


def num(e, k, d, vals):
    v = vals.get(e.get("id"), {}).get(k)
    return v if v is not None else float(e.get(k, d))


def node_matrix(e, vals, f):
    r, sx, sy = num(e, "rotation", 0, vals), num(e, "scaleX", 1, vals), num(e, "scaleY", 1, vals)
    cs, sn = math.cos(r), math.sin(r)
    return (cs * sx, sn * sx, -sn * sy, cs * sy, num(e, "x", 0, vals), num(e, "y", 0, vals))


def path_points(p, vals):
    pts = []
    for v in p:
        if v.tag in ("StraightVertex", "CubicDetachedVertex", "CubicAsymmetricVertex", "CubicMirroredVertex"):
            x, y = num(v, "x", 0, vals), num(v, "y", 0, vals)
            pts.append((x, y))
            for key in ("in", "out"):
                d = float(v.get(f"{key}Distance", 0))
                if d:
                    r = float(v.get(f"{key}Rotation", 0))
                    pts.append((x + d * math.cos(r), y + d * math.sin(r)))
    return pts


def geometry_points(shape, vals):
    """The shape's own path points in the shape's space (each path's transform applied)."""
    out = []
    for g in shape:
        if g.tag == "PointsPath":
            m = affine(g)
            for x, y in path_points(g, vals):
                out.append((m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5]))
        elif g.tag in ("Rectangle", "Ellipse"):
            w, h = float(g.get("width", 0)), float(g.get("height", 0))
            ox, oy = float(g.get("originX", .5)), float(g.get("originY", .5))
            m = affine(g)
            for x, y in ((-w * ox, -h * oy), (w * (1 - ox), -h * oy), (w * (1 - ox), h * (1 - oy)), (-w * ox, h * (1 - oy))):
                out.append((m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5]))
    return out


class Gate:
    def __init__(self, scene, gate_name):
        self.scene = scene
        self.node = scene.node(f"Chapter 4 Fireworks {gate_name} Gate")
        self.name = gate_name
        anim = scene.animations[ANIM]
        sheet = Sheet(scene)
        ids = {e.get("id") for e in self.node.iter() if e.get("id")}
        self.keys = {o: p for o, p in sheet.anim_keys(anim).items() if o in ids}
        self.solo = {}
        for ko in anim.findall("KeyedObject"):
            for kp in ko.findall("KeyedProperty"):
                if kp.get("property") == "activeComponentId" and ko.get("objectId") in ids:
                    self.solo[ko.get("objectId")] = sorted(((int(k.get("frame", 0)), k.get("value")) for k in kp))
        self.parent = {c: p for p in self.node.iter() for c in p}
        self.units = self.find_units()
        # matrices above the gate, at rest
        m = (1, 0, 0, 1, 0, 0)
        chain, p = [], scene.parent[self.node]
        while p is not None and p.tag in ("Node", "Shape"):
            chain.append(p)
            p = scene.parent.get(p)
        for x in reversed(chain):
            m = compose(m, affine(x))
        self.base = m

    def find_units(self):
        """The movable bursts: one node per burst (a burst's whole look hangs below it), in document order."""
        kids = lambda e: [c for c in e if c.tag in ("Node", "Shape")]
        out = []
        if self.name == "Strands":
            return kids(self.node)
        for container in kids(self.node):
            for c in kids(container):
                if self.name == "Spelling Bee" and c.get("name") == "Small":
                    out += kids(c)
                else:
                    out.append(c)
        return out

    def values(self, f):
        return {o: {p: k.at(f) for p, k in props.items()} for o, props in self.keys.items()}

    def active(self, solo, f):
        cur = solo.get("activeComponentId")
        for fr, v in self.solo.get(solo.get("id"), []):
            if fr <= f:
                cur = v
        return cur

    def pieces(self, f):
        """[(name path, [x0, y0, x1, y1], dot, unit id, ids of the chain from the gate's child down to the shape)] for the visible shapes at frame f (a dot: scale 0 but a stroke still draws).
        self.origin[unit id] is set to the unit's world origin (x, y) at this frame."""
        vals = self.values(f)
        out = []
        unit_ids = {u.get("id") for u in self.units}
        self.origin = {}

        def walk(e, m, names, uid=None, ids=()):
            op = num(e, "opacity", 1, vals)
            if op <= 0:
                return
            m = compose(m, node_matrix(e, vals, f))
            names = names + [e.get("name") or e.tag]
            ids = ids + (e.get("id"),)
            if e.get("id") in unit_ids:
                uid = e.get("id")
                self.origin[uid] = (m[4], m[5])
            if e.tag == "Shape":
                has_stroke = e.find("Stroke") is not None
                has_fill = e.find("Fill") is not None
                pts = geometry_points(e, vals)
                if pts and (has_stroke or has_fill):
                    xs, ys = [], []
                    for x, y in pts:
                        xs.append(m[0] * x + m[2] * y + m[4])
                        ys.append(m[1] * x + m[3] * y + m[5])
                    pad = PAD if has_stroke else 0
                    box = [min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad]
                    dot = has_stroke and (max(xs) - min(xs) < 1e-3 and max(ys) - min(ys) < 1e-3)
                    out.append(("/".join(names[-4:]), box, dot, uid, ids))
            for c in e:
                if c.tag in GEOM:
                    if e.tag == "Solo":
                        d = dict(e.attrib)
                        if c.get("id") != self.active(d, f):
                            continue
                    walk(c, m, names, uid, ids)

        for c in self.node:
            if c.tag in GEOM:
                walk(c, self.base, [])
        return out


def measure(scene, gate_name, frames=range(300)):
    g = Gate(scene, gate_name)
    best = None          # (y, frame, piece, box) among pieces touching the column
    best_all = None
    dots = {}
    for f in frames:
        for name, box, dot, *_ in g.pieces(f):
            if dot:
                dots.setdefault(name, []).append(f)
            if best_all is None or box[1] < best_all[0]:
                best_all = (box[1], f, name, box)
            if box[2] >= COLUMN[0] and box[0] <= COLUMN[1]:
                if best is None or box[1] < best[0]:
                    best = (box[1], f, name, box)
    return best, best_all, dots


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene")
    a = ap.parse_args()
    scene = Scene(a.scene or chapter_dir("ch3") / "scene.rml")
    for name in GATES:
        best, best_all, dots = measure(scene, name)
        print(f"{name:13s} column highest y {best[0]:7.1f} at frame {best[1]:3d}  {best[2]}   (whole width {best_all[0]:7.1f} at {best_all[1]})"
              if best else f"{name}: nothing in the column")
        if dots:
            print(f"    dots (scale 0 with a stroke): {len(dots)} pieces, e.g. {next(iter(dots))} frames {dots[next(iter(dots))][:3]}...")


if __name__ == "__main__":
    main()
