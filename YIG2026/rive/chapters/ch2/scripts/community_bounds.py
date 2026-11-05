"""Bounds of an art subtree in a scene file, read with a real XML parser: the geometry the Community room's pieces are measured and
placed by (Chapter 2 has no way to render a copy of a project, so the layout is done by numbers).

    bounds(element)  ->  (x0, y0, x1, y1) in the element's PARENT space (its own x, y, rotation and scale applied), stroke included.
"""
import math


def _mat(e):
    x, y = float(e.get("x", 0)), float(e.get("y", 0))
    r = float(e.get("rotation", 0))
    sx, sy = float(e.get("scaleX", 1)), float(e.get("scaleY", 1))
    c, s = math.cos(r), math.sin(r)
    return (c * sx, s * sx, -s * sy, c * sy, x, y)


def _mul(m, n):
    a, b, c, d, e, f = m
    A, B, C, D, E, F = n
    return (a * A + c * B, b * A + d * B, a * C + c * D, b * C + d * D, a * E + c * F + e, b * E + d * F + f)


def _pt(m, p):
    return (m[0] * p[0] + m[2] * p[1] + m[4], m[1] * p[0] + m[3] * p[1] + m[5])


def _bez(p0, p1, p2, p3, n=12):
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        yield (u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
               u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1])


def _handles(v):
    p = (float(v.get("x", 0)), float(v.get("y", 0)))
    if v.tag == "StraightVertex":
        return p, p, p
    if v.tag == "CubicAsymmetricVertex":
        r = float(v.get("rotation", 0))
        i_r, o_r = r + math.pi, r
        i_d, o_d = float(v.get("inDistance", 0)), float(v.get("outDistance", 0))
    else:
        i_r, o_r = float(v.get("inRotation", 0)), float(v.get("outRotation", 0))
        i_d, o_d = float(v.get("inDistance", 0)), float(v.get("outDistance", 0))
    return (p[0] + i_d * math.cos(i_r), p[1] + i_d * math.sin(i_r)), p, (p[0] + o_d * math.cos(o_r), p[1] + o_d * math.sin(o_r))


def _path_points(path):
    vs = [v for v in path if v.tag.endswith("Vertex")]
    pts = []
    n = len(vs)
    closed = path.get("isClosed") == "true"
    for i in range(n if closed else n - 1):
        a, b = vs[i], vs[(i + 1) % n]
        _, pa, oa = _handles(a)
        ib, pb, _ = _handles(b)
        pts += list(_bez(pa, oa, ib, pb))
    if n == 1:
        pts.append(_handles(vs[0])[1])
    return pts


def _walk(e, m, out):
    mm = _mul(m, _mat(e)) if e.tag in ("Node", "Shape") else m
    if e.tag == "Shape":
        stroke = e.find("Stroke")
        half = float(stroke.get("thickness", 1)) / 2 if stroke is not None else 0.0
        scales = stroke is None or stroke.get("transformAffectsStroke", "true") != "false"
        k = (abs(mm[0] * mm[3] - mm[1] * mm[2])) ** 0.5 if scales else 1.0
        local = []
        for child in e:
            if child.tag == "PointsPath":
                local += _path_points(child)
            elif child.tag == "Ellipse":
                w, h = float(child.get("width", 0)), float(child.get("height", 0))
                cx, cy = float(child.get("x", 0)), float(child.get("y", 0))
                local += [(cx + w / 2 * math.cos(t / 12 * 2 * math.pi), cy + h / 2 * math.sin(t / 12 * 2 * math.pi)) for t in range(12)]
            elif child.tag == "Rectangle":
                w, h = float(child.get("width", 0)), float(child.get("height", 0))
                ox, oy = float(child.get("originX", 0)), float(child.get("originY", 0))
                local += [(-ox * w, -oy * h), ((1 - ox) * w, -oy * h), ((1 - ox) * w, (1 - oy) * h), (-ox * w, (1 - oy) * h)]
        for p in local:
            q = _pt(mm, p)
            sk = half * (k if scales else 1.0)
            out.append((q[0] - sk, q[1] - sk, q[0] + sk, q[1] + sk))
    for child in e:
        if child.tag in ("Node", "Shape"):
            _walk(child, mm, out)


def bounds(e):
    out = []
    mm = _mat(e)
    inner = (1, 0, 0, 1, 0, 0)
    for child in ([e] if e.tag == "Shape" else list(e)):
        if child is e:
            _walk(e, (1, 0, 0, 1, 0, 0), out)
        elif child.tag in ("Node", "Shape"):
            _walk(child, mm, out)
    xs0, ys0 = min(b[0] for b in out), min(b[1] for b in out)
    xs1, ys1 = max(b[2] for b in out), max(b[3] for b in out)
    return xs0, ys0, xs1, ys1
