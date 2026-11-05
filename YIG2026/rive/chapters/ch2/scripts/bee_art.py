"""Spelling Bee: the upright block as a hexagonal prism (its plate turns like a coin, and the whole block can roll one facet).

The upright block is a hexagonal prism seen in an oblique projection: its front face is a regular hexagon (pointy left and right) and
its back face is the same hexagon moved by D (35.12 px to the right), so the two side faces that show are parallelograms between a front
edge and the same edge moved by D. That is exactly how the old drawing was built (a light band above, a dark band below). The new
block is drawn as that: the front ring, the plate on it (with a dark hollow behind), and six side facets, one per edge of the hexagon.

A roll about the prism's axis is then plain geometry: the front hexagon turns in its own plane, D stays, every facet's four corners
follow, a facet shows only while its outward normal has a positive part along D (its opacity follows that, over a hair of angle, so
nothing pops: a facet that is edge-on has no area), and a facet's shade follows its normal (dark when it faces down, light when it
faces up: a light layer over the dark one fades in). After 60 degrees the hexagon and the facets are where they were with the
corners relabelled, so the picture is identical and the corners go back to their first values in one frame (hold keys).

"""
import math

from rml_edit import num

YEL, DARK = "FFE4E93B", "FF1F1F1F"
R_RING, R_PLATE = 37.4605, 25.5005
FRONT_C = (38.2105, 33.1915)             # the front hexagon's centre in the block's group (9:506)
D = (35.12, 0.0)                         # the block's depth: back face minus front face


def rot(a, p):
    c, s = math.cos(a), math.sin(a)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def hexpt(R, i):
    """Corner i of a regular hexagon of circumradius R, pointy left and right, angles clockwise on the screen from 'right'."""
    a = math.radians(60 * i)
    return (R * math.cos(a), R * math.sin(a))


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def facet_state(k, t):
    """(opacity of the dark facet, opacity of its light layer) for the block's facet k when the front hexagon is turned by t."""
    a = math.radians(60 * k + 30) + t
    nx, ny = math.cos(a), math.sin(a)
    gate = clamp(nx / 0.12)                              # D points right: the facet shows while its normal has a part along D
    shade = clamp((0.2 - ny) / 0.4)                            # 1 facing up (light), 0 facing down (dark)
    return gate, gate * shade


# ---- XML for the block -------------------------------------------------------------------------------------------------------
def _pad(doc, i):
    return " " * (len(doc.lines[i]) - len(doc.lines[i].lstrip()))


def _poly(doc, pad, pts):
    out = [f'{pad}<PointsPath isClosed="true" id="{doc.new_id()}">']
    ids = []
    for x, y in pts:
        v = doc.new_id()
        ids.append(v)
        out.append(f'{pad}    <StraightVertex x="{num(x)}" y="{num(y)}" id="{v}"/>')
    out.append(f"{pad}</PointsPath>")
    return out, ids


def _shape(doc, pad, name, pts, fill, stroke=True, x=0.0, y=0.0, opacity=1.0, fixed_stroke=False):
    sid = doc.new_id()
    at = (f' x="{num(x)}"' if num(x) != "0" else "") + (f' y="{num(y)}"' if num(y) != "0" else "")
    op = f' opacity="{num(opacity)}"' if num(opacity) != "1" else ""
    out = [f'{pad}<Shape{at}{op} name="{name}" id="{sid}">']
    pp, ids = _poly(doc, pad + "    ", pts)
    out += pp
    out += [f'{pad}    <Fill id="{doc.new_id()}">', f'{pad}        <SolidColor colorValue="{fill}" id="{doc.new_id()}"/>', f"{pad}    </Fill>"]
    if stroke:
        fx = ' transformAffectsStroke="false"' if fixed_stroke else ""
        out += [f'{pad}    <Stroke thickness="1.5" cap="round" join="round"{fx} id="{doc.new_id()}">',
                f'{pad}        <SolidColor colorValue="{DARK}" id="{doc.new_id()}"/>', f"{pad}    </Stroke>"]
    out.append(f"{pad}</Shape>")
    return out, sid, ids


def build_block(doc, group_id, old_shape_ids, room):
    """Replace the block's four shapes (in its group `group_id`) with the new construction. Returns a dict of the ids to key:
    plate_spin (node), ring/plate/hollow (vertex ids, path order = corner indices 5,4,3,2,1,0), quads[k] = (dark shape, light shape,
    dark vertex ids, light vertex ids), each quad's corners in order P_k, P_k+1, P_k+1 + D, P_k + D."""
    for sid in old_shape_ids:
        i = doc.idx(sid)
        j = doc.end(i)
        del doc.lines[i:j + 1]
    gi = doc.idx(group_id)
    pad = _pad(doc, gi) + "    "
    order = [5, 4, 3, 2, 1, 0]
    fx, fy = FRONT_C
    lines = []
    # top to bottom: the plate (in its spin node), the hollow, the ring, the light layers, the dark facets
    spin_id = doc.new_id()
    lines.append(f'{pad}<Node x="{num(fx)}" y="{num(fy)}" name="{room} Plate Spin" id="{spin_id}">')
    pl, plate_sid, plate_ids = _shape(doc, pad + "    ", f"{room} Plate", [hexpt(R_PLATE, i) for i in order], YEL, fixed_stroke=True)
    lines += pl + [f"{pad}</Node>"]
    hl, hollow_sid, hollow_ids = _shape(doc, pad, f"{room} Hollow", [hexpt(R_PLATE, i) for i in order], DARK, x=fx, y=fy)
    rl, ring_sid, ring_ids = _shape(doc, pad, f"{room} Ring", [hexpt(R_RING, i) for i in order], YEL, x=fx, y=fy)
    lines += hl + rl
    quads = {}
    lights, darks = [], []
    for k in range(6):
        P = lambda i: hexpt(R_RING, i % 6)
        pts = [P(k), P(k + 1), (P(k + 1)[0] + D[0], P(k + 1)[1] + D[1]), (P(k)[0] + D[0], P(k)[1] + D[1])]
        pts = [(x + fx, y + fy) for x, y in pts]
        g, lt = facet_state(k, 0.0)
        ll, l_sid, l_ids = _shape(doc, pad, f"{room} Facet {k} Light", pts, YEL, opacity=lt)
        dl, d_sid, d_ids = _shape(doc, pad, f"{room} Facet {k}", pts, DARK, opacity=g)
        lights += ll
        darks += dl
        quads[k] = (d_sid, l_sid, d_ids, l_ids)
    lines += lights + darks
    doc.lines[gi + 1:gi + 1] = lines
    return dict(spin=spin_id, ring=ring_ids, plate=plate_ids, hollow=hollow_ids, quads=quads)


def block_values(t, spin=1.0):
    """Every keyed value of the block when its front hexagon is turned by t (radians) and its plate is `spin` wide:
    {('ring', n, 'x'|'y'): v, ('plate', ...), ('hollow', ...), ('quad', k, light?, n, 'x'|'y'): v, ('opacity', k, light?): v}."""
    out = {}
    fx, fy = FRONT_C
    order = [5, 4, 3, 2, 1, 0]
    for name, R in (("ring", R_RING), ("plate", R_PLATE), ("hollow", R_PLATE)):
        for n, i in enumerate(order):
            x, y = rot(t, hexpt(R, i))
            out[(name, n, "x")], out[(name, n, "y")] = x, y
    for k in range(6):
        P = lambda i: rot(t, hexpt(R_RING, i % 6))
        pts = [P(k), P(k + 1), (P(k + 1)[0] + D[0], P(k + 1)[1] + D[1]), (P(k)[0] + D[0], P(k)[1] + D[1])]
        g, lt = facet_state(k, t)
        for light in (False, True):
            for n, (x, y) in enumerate(pts):
                out[("quad", k, light, n, "x")], out[("quad", k, light, n, "y")] = x + fx, y + fy
            out[("opacity", k, light)] = lt if light else g
    return out


BLOCK_C = (754.5 + FRONT_C[0], 553 + FRONT_C[1])   # the block's front hexagon's centre on the artboard
BLOCK_R, BLOCK_D = R_RING, D[0]


def block_outline():
    """The block's silhouette on the artboard, as a closed list of corners (front hexagon's left half, the back face's right half)."""
    cx, cy = BLOCK_C
    h = BLOCK_R * math.sin(math.pi / 3)
    return [(cx - BLOCK_R / 2, cy - h), (cx + BLOCK_R / 2 + BLOCK_D, cy - h), (cx + BLOCK_R + BLOCK_D, cy),
            (cx + BLOCK_R / 2 + BLOCK_D, cy + h), (cx - BLOCK_R / 2, cy + h), (cx - BLOCK_R, cy)]
