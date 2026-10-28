"""Convert the filled paths of a lockup SVG to Rive shapes, with no loss.

The lockup SVGs hold only filled <path> elements built from M L H V C S Z, in a 175 x 128 frame. Each path becomes one
Shape (one PointsPath per subpath, holes included), its origin at the centre of its points and its vertices relative to
that, which is how the Editor's SVG import writes them. Cubic segments keep their control points exactly: a segment's
out handle sits on its first vertex and its in handle on its last.

    python3 tools/svg_to_rml.py art/ch2/originals/wordle-lockup.svg      print a summary of the shapes
"""
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NUMBER = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
TOKEN = re.compile(r"[MmLlHhVvCcSsZz]|" + NUMBER.pattern)
ARGS = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Z": 0}
NAMED = {"white": "FFFFFFFF", "black": "FF000000"}


class Vertex:
    __slots__ = ("x", "y", "into", "out")

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.into = None      # in handle, relative to the vertex
        self.out = None       # out handle, relative to the vertex


def parse_path(d):
    """[[Vertex]] and a closed flag per subpath: [(vertices, closed)]. Raises on a command the lockups never use."""
    tokens = TOKEN.findall(d)
    subpaths, cur, start = [], None, None
    x = y = 0.0
    prev_c2 = None            # the last cubic's second control point, for S
    i, cmd = 0, None

    def take(n):
        nonlocal i
        vals = [float(t) for t in tokens[i:i + n]]
        if len(vals) != n:
            raise ValueError(f"path ends inside a command: {d[:40]}")
        i += n
        return vals

    while i < len(tokens):
        if re.fullmatch(r"[A-Za-z]", tokens[i]):
            cmd = tokens[i]
            i += 1
            if cmd.upper() not in ARGS:
                raise ValueError(f"unsupported path command {cmd!r}")
        elif cmd is None:
            raise ValueError("path starts with a number")
        rel, up = cmd.islower(), cmd.upper()
        if up == "Z":
            if cur is not None:
                first = cur[0]
                if len(cur) > 1 and abs(cur[-1].x - first.x) < 1e-9 and abs(cur[-1].y - first.y) < 1e-9:
                    first.into = cur[-1].into          # the path already returned to its start: merge the two vertices
                    cur.pop()
                subpaths.append((cur, True))
                x, y = start
                cur = None
            prev_c2 = None
            continue
        a = take(ARGS[up])
        if up == "M":
            if cur is not None:
                subpaths.append((cur, False))
            x, y = (x + a[0], y + a[1]) if rel else (a[0], a[1])
            start, cur = (x, y), [Vertex(x, y)]
            cmd = "l" if rel else "L"               # extra pairs after M are lines
            prev_c2 = None
            continue
        if cur is None:                              # a command after Z starts a new subpath at the old start
            cur = [Vertex(x, y)]
        if up == "L":
            x, y = (x + a[0], y + a[1]) if rel else (a[0], a[1])
            cur.append(Vertex(x, y))
            prev_c2 = None
        elif up == "H":
            x = x + a[0] if rel else a[0]
            cur.append(Vertex(x, y))
            prev_c2 = None
        elif up == "V":
            y = y + a[0] if rel else a[0]
            cur.append(Vertex(x, y))
            prev_c2 = None
        else:
            if up == "C":
                c1 = (x + a[0], y + a[1]) if rel else (a[0], a[1])
                c2 = (x + a[2], y + a[3]) if rel else (a[2], a[3])
                end = (x + a[4], y + a[5]) if rel else (a[4], a[5])
            else:                                    # S: the first control point mirrors the last cubic's second
                c1 = (2 * x - prev_c2[0], 2 * y - prev_c2[1]) if prev_c2 else (x, y)
                c2 = (x + a[0], y + a[1]) if rel else (a[0], a[1])
                end = (x + a[2], y + a[3]) if rel else (a[2], a[3])
            cur[-1].out = (c1[0] - cur[-1].x, c1[1] - cur[-1].y)
            v = Vertex(*end)
            v.into = (c2[0] - end[0], c2[1] - end[1])
            cur.append(v)
            x, y = end
            prev_c2 = c2
    if cur is not None:
        subpaths.append((cur, False))
    return subpaths


def color(value):
    value = value.strip()
    if value in NAMED:
        return NAMED[value]
    if re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        return "FF" + value[1:].upper()
    raise ValueError(f"unsupported fill {value!r}")


def svg_paths(svg_text):
    """[(colour 'AARRGGBB', [(vertices, closed)])] in paint order (first is at the back)."""
    out = []
    for el in ET.fromstring(svg_text).iter("{http://www.w3.org/2000/svg}path"):
        fill = el.get("fill")
        if fill is None or fill == "none":
            raise ValueError("a path without a fill: the lockups hold filled paths only")
        out.append((color(fill), parse_path(el.get("d"))))
    return out


def points(subpaths):
    return [(v.x, v.y) for sub, _ in subpaths for v in sub]


def bounds(pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def area(vertices):
    """Shoelace sum over the vertices (y down): negative is counter-clockwise on screen."""
    return sum(a.x * b.y - b.x * a.y for a, b in zip(vertices, vertices[1:] + vertices[:1])) / 2


def num(v):
    s = f"{v:.6f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def vertex_xml(v, dx, dy, ids):
    x, y = v.x - dx, v.y - dy
    attrs = []
    if v.into is None and v.out is None:
        tag = "StraightVertex"
    else:
        tag = "CubicDetachedVertex"
        for key, h in (("in", v.into), ("out", v.out)):
            if h and math.hypot(*h) > 1e-9:
                rot = math.atan2(h[1], h[0])
                if abs(rot) > 1e-9:
                    attrs.append(f'{key}Rotation="{num(rot)}"')
                attrs.append(f'{key}Distance="{num(math.hypot(*h))}"')
    if abs(x) > 1e-9:
        attrs.append(f'x="{num(x)}"')
    if abs(y) > 1e-9:
        attrs.append(f'y="{num(y)}"')
    return f'<{tag} {" ".join(attrs)} id="{ids()}"/>'.replace(f"<{tag}  ", f"<{tag} ")


def shape_xml(colour, subpaths, ids, offset=(0.0, 0.0)):
    """One Shape. `offset` is subtracted from every coordinate, so the caller can centre a group of shapes."""
    x0, y0, x1, y1 = bounds([(px - offset[0], py - offset[1]) for px, py in points(subpaths)])
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    ox, oy = cx + offset[0], cy + offset[1]
    paths = []
    for sub, closed in subpaths:
        flags = ' isClosed="true"' if closed else ""
        if area(sub) < 0:
            flags += ' isClockwise="false"'
        paths.append(f"<PointsPath{flags} id=\"{ids()}\">" + "".join(vertex_xml(v, ox, oy, ids) for v in sub) + "</PointsPath>")
    pos = (f' x="{num(cx)}"' if abs(cx) > 1e-9 else "") + (f' y="{num(cy)}"' if abs(cy) > 1e-9 else "")
    return (f'<Shape{pos} id="{ids()}">' + "".join(paths)
            + f'<Fill id="{ids()}"><SolidColor colorValue="{colour}" id="{ids()}"/></Fill></Shape>')


def main(argv):
    paths = svg_paths(Path(argv[0]).read_text())
    for i, (colour, subs) in enumerate(paths):
        x0, y0, x1, y1 = bounds(points(subs))
        print(f"{i:2d} {colour} subpaths={len(subs)} vertices={sum(len(s) for s, _ in subs):3d} bbox=({x0:.2f}, {y0:.2f}) to ({x1:.2f}, {y1:.2f})")


if __name__ == "__main__":
    main(sys.argv[1:])
