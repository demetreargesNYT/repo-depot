"""World (room-space) geometry from the scene's setup pose: python3 geom.py <node or shape id> [depth]"""
import math
import sys
import xml.etree.ElementTree as ET
from common import base_text

ROOT = ET.fromstring(base_text())      # the art is the same in every version; read it from the base so a rebuild never depends on the file it writes
PARENT = {c: p for p in ROOT.iter() for c in p}
BYID = {e.get("id"): e for e in ROOT.iter() if e.get("id")}


def local(e):
    x, y = float(e.get("x", 0)), float(e.get("y", 0))
    r = float(e.get("rotation", 0))
    sx, sy = float(e.get("scaleX", 1)), float(e.get("scaleY", 1))
    c, s = math.cos(r), math.sin(r)
    return (c * sx, s * sx, -s * sy, c * sy, x, y)        # a b c d tx ty: (x, y) -> (a x + c y + tx, b x + d y + ty)


def mul(m, n):
    a, b, c, d, tx, ty = m
    a2, b2, c2, d2, tx2, ty2 = n
    return (a * a2 + c * b2, b * a2 + d * b2, a * c2 + c * d2, b * c2 + d * d2, a * tx2 + c * ty2 + tx, b * tx2 + d * ty2 + ty)


def world(e):
    chain = []
    while e is not None and e.tag != "Artboard":
        if e.tag in ("Node", "Shape", "Ellipse", "Rectangle", "PointsPath"):
            chain.append(e)
        e = PARENT.get(e)
    m = (1, 0, 0, 1, 0, 0)
    for n in reversed(chain[:-0 or None]):
        m = mul(m, local(n))
    return m


def apply(m, p):
    a, b, c, d, tx, ty = m
    return (a * p[0] + c * p[1] + tx, b * p[0] + d * p[1] + ty)


def outline(e):
    """Room-space points of a path element (its vertices; an ellipse as 32 points)."""
    m = world(e)
    if e.tag == "Ellipse":
        w, h = float(e.get("width", 0)), float(e.get("height", 0))
        return [apply(m, (w / 2 * math.cos(2 * math.pi * i / 32), h / 2 * math.sin(2 * math.pi * i / 32))) for i in range(32)]
    if e.tag == "Rectangle":
        w, h = float(e.get("width", 0)), float(e.get("height", 0))
        return [apply(m, p) for p in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
    return [apply(m, (float(v.get("x", 0)), float(v.get("y", 0)))) for v in e if v.tag.endswith("Vertex")]


def bbox(pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return (round(min(xs), 1), round(min(ys), 1), round(max(xs), 1), round(max(ys), 1))


def walk(e, depth=0, maxd=9):
    for c in e:
        if c.tag in ("Ellipse", "PointsPath", "Rectangle"):
            fill = None
            sh = PARENT[c]
            f = sh.find("Fill")
            if f is not None and f.find("SolidColor") is not None:
                fill = f.find("SolidColor").get("colorValue")
            print("  " * depth + f"{c.tag} {c.get('id')} in {sh.get('name', '')!r}/{sh.get('id')} fill {fill} bbox {bbox(outline(c))}")
        elif c.tag in ("Node", "Shape") and depth < maxd:
            print("  " * depth + f"{c.tag} {c.get('name', '')!r} {c.get('id')}")
            walk(c, depth + 1, maxd)


if __name__ == "__main__":
    walk(BYID[sys.argv[1]], 0, int(sys.argv[2]) if len(sys.argv) > 2 else 9)


def sampled(e, n=12):
    """Room-space polyline of a PointsPath with its curves (CubicDetachedVertex handles), n points per segment; ellipses as 64 points."""
    m = world(e)
    if e.tag != "PointsPath":
        return outline(e)
    vs = [v for v in e if v.tag.endswith("Vertex")]
    pts = []
    for i, v in enumerate(vs):
        w = vs[(i + 1) % len(vs)]
        p0 = (float(v.get("x", 0)), float(v.get("y", 0)))
        p3 = (float(w.get("x", 0)), float(w.get("y", 0)))
        od, orot = float(v.get("outDistance", 0)), float(v.get("outRotation", 0))
        idd, irot = float(w.get("inDistance", 0)), float(w.get("inRotation", 0))
        p1 = (p0[0] + od * math.cos(orot), p0[1] + od * math.sin(orot))
        p2 = (p3[0] + idd * math.cos(irot), p3[1] + idd * math.sin(irot))
        for k in range(n):
            t = k / n
            q = [(1 - t) ** 3 * p0[j] + 3 * (1 - t) ** 2 * t * p1[j] + 3 * (1 - t) * t * t * p2[j] + t ** 3 * p3[j] for j in (0, 1)]
            pts.append(apply(m, q))
    return pts
