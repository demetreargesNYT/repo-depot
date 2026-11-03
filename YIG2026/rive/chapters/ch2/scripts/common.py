"""Shared pieces for the Chapter 2 entry redesign (2026-11-03): the ball comes out of an object in its room as part of its loop.

Each room is one cycle of the ball's journey, frame by frame (60 per second). Cycle frame 0 is the moment the ball starts to come
out of its object, at intro frame T0 (as soon as the pieces it touches are in place). The Loop is the same cycle picked up at the
intro's last frame, so it closes on the pose the intro ends on; the cycle's own seam is inside the object, out of sight.

The ball chain in these rooms: "<Room> Ball" (keyed x, y: the room-space position, a direct child of the room, outside the planes),
"Ball_01" (fixed offset and size), "Ball_01_Scale" (keyed scaleX, scaleY: the squash, about the ball's bottom), and a new
"<Room> Ball Spin" pivot at the ball's centre around the highlight and the body (keyed rotation). The body is held round.
"""
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RIVE_DIR = HERE.parents[2]
sys.path.insert(0, str(RIVE_DIR / "tools"))

# the scene as it was before this work (the 2026-11-03 delivery); every rebuild starts from it
BASE_REV = "340b2c7"


def base_text():
    import subprocess
    r = subprocess.run(["git", "show", f"{BASE_REV}:./chapters/ch2/scene.rml"], cwd=RIVE_DIR, capture_output=True, text=True, check=True)
    return r.stdout

from rml_edit import Doc, bake, num  # noqa: E402
from rml_read import Scene  # noqa: E402
from rooms_sheet import Sheet  # noqa: E402
import ball_physics as bp  # noqa: E402

INTRO = 192
G = bp.G
CENTER_IN_SCALE = (0.0, -17.571991)                          # the body's centre in Ball_01_Scale's space


def smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def dip(u, depth, T):
    """One smooth dip u frames after a contact: down to `depth` halfway and back by T, no overshoot (so never a buzz)."""
    return depth * math.sin(math.pi * u / T) ** 2 if 0 < u < T else 0.0


class BallArt:
    """The ids and fixed geometry of one room's ball."""

    def __init__(self, scene, room):
        r = scene.root
        self.room = room
        self.node = next(n for n in r.iter("Node") if n.get("name") == f"{room} Ball")
        b01 = self.node.find("Node")
        sc = b01.find("Node")
        shapes = sc.findall("Shape")
        self.id, self.b01, self.scale = self.node.get("id"), b01.get("id"), sc.get("id")
        self.hl, self.base = shapes[0].get("id"), shapes[1].get("id")
        self.verts = [v.get("id") for v in shapes[1].find("PointsPath").findall("CubicDetachedVertex")]
        self.hl_scale = float(shapes[0].get("scaleX", 1))
        self.ox, self.oy = float(b01.get("x", 0)), float(b01.get("y", 0))
        self.k = float(b01.get("scaleX", 1))
        self.R = 17.678 * self.k                       # the body's radius on the artboard
        self.Rc = 17.2 * self.k                        # centre to what it rests on (the stroke sits a little into the surface)
        cx, cy = CENTER_IN_SCALE
        sx, sy = float(sc.get("x", 0)), float(sc.get("y", 0))
        # node position -> centre: Ball_01's offset, then (scaled by k) Ball_01_Scale's offset and the body's centre in it
        self.dc = (self.ox + self.k * (sx + cx), self.oy + self.k * (sy + cy))

    def node_of(self, c):
        return (c[0] - self.dc[0], c[1] - self.dc[1])


def prepare_ball(doc, art):
    """Wrap the highlight and body in a spin pivot at the body's centre; hold the body round (drop its vertex and highlight keys
    and the body's rotation from every animation of the room). Returns the spin pivot's id."""
    room = art.room
    names = [f"{room} {s}" for s in ("Intro", "Loop", "Waiting", "Built")]
    for a in names:
        for oid in [art.hl, art.base] + art.verts:
            doc.drop_object(a, oid)
    spin, _ = doc.wrap_run(art.hl, art.base, f"{room} Ball Spin", 0.0, -17.571991)
    # the round body and its highlight, as the setup pose (the rooms drew the ball squashed at rest)
    top, right, bottom, left = art.verts
    setv = lambda oid, **kv: _set_attrs(doc, oid, kv)
    setv(top, x=0, y=-17.678, inDistance=9.7633, outDistance=9.7633)
    setv(right, x=17.678, y=0)
    setv(bottom, x=0, y=17.678)
    setv(left, x=-17.678, y=0)
    setv(art.hl, x=6.5 if art.hl_scale != 1 else 6.364, y=-23.834)
    i = doc.idx(art.base)
    doc.lines[i] = re.sub(r' rotation="[^"]*"', "", doc.lines[i])
    return spin


def _set_attrs(doc, oid, kv):
    i = doc.idx(oid)
    line = doc.lines[i]
    for k, v in kv.items():
        if re.search(rf' {k}="[^"]*"', line):
            line = re.sub(rf' {k}="[^"]*"', "" if num(v) == "0" else f' {k}="{num(v)}"', line)
        elif num(v) != "0":
            line = line.replace(f' id="{oid}"', f' {k}="{num(v)}" id="{oid}"')
    doc.lines[i] = line


class Cycle:
    """The ball over cycle frames 0..L (frame L is frame 0 again): centre, squash, mode ("air", "roll", "rest", "hidden")."""

    def __init__(self, L):
        self.L = L
        self.c = {}
        self.mode = {}
        self.sx = {f: 1.0 for f in range(L + 1)}
        self.sy = {f: 1.0 for f in range(L + 1)}
        self.notes = []
        self.roll_r = {}

    def put(self, f, c, mode):
        self.c[f], self.mode[f] = c, mode

    def squash(self, f, a, T=14):
        """A landing squash on frame f: a smooth pulse (down fast, back without overshoot) of amount a over T frames."""
        for u in range(T + 1):
            g = f + u
            if g > self.L:
                break
            p = math.sin(math.pi * min(1.0, u / T)) ** 2 if u else 0.0
            self.sy[g] = min(self.sy[g], 1 - a * p)
            self.sx[g] = max(self.sx[g], 1 + 0.7 * a * p)

    def spin(self, r, closes_in=None):
        """Turn on every frame: rolling turns with the distance along the surface (sign by the sideways travel), in the air it keeps
        the turn rate it left with, at rest and hidden it is still. The hidden frames `closes_in` (a range) take up whatever is left
        over to a whole number of turns, so the cycle closes."""
        th = [0.0]
        w_air, prev, w_prev = 0.0, "rest", 0.0
        for f in range(self.L):
            m = self.mode[f]
            (x0, y0), (x1, y1) = self.c[f], self.c[f + 1]
            if m == "roll":
                w = math.copysign(math.hypot(x1 - x0, y1 - y0), x1 - x0) / r if abs(x1 - x0) > 1e-9 else 0.0
            elif m == "air":
                if prev != "air":
                    w_air = w_prev if prev == "roll" else 0.25 * (x1 - x0) / r
                w = w_air
            else:
                w = 0.0
            th.append(th[-1] + w)
            prev, w_prev = m, w
        if closes_in is not None:
            total = th[-1]
            want = round(total / (2 * math.pi)) * 2 * math.pi
            fr = list(closes_in)
            for f in range(len(th)):
                if f > fr[0]:
                    th[f] += (want - total) * smooth((min(f, fr[-1]) - fr[0]) / (fr[-1] - fr[0]))
        return th


def path_into(cyc, f0, pieces):
    """Write a ball_physics path (pieces [(ta, tb, fn, mode)], times in frames from 0) into the cycle from frame f0; returns the
    frame after the last one written and the last piece's end time."""
    t_end = pieces[-2][1] if len(pieces) > 1 else pieces[-1][1]
    f = f0
    while f - f0 <= t_end:
        p, mode = bp.piece_at(pieces, f - f0)
        cyc.put(f, p, mode)
        f += 1
    return f


def plane_x(scene, sheet, room, plane="Floor"):
    oid = next(e.get("id") for e in scene.root.iter("Node") if e.get("name") == f"{room} {plane} Plane")
    k = sheet.anim_keys(scene.animations[f"{room} Intro"])[oid]["x"]
    return lambda f: k.at(f)


def intro_series(scene, sheet, room, oid, prop):
    keys = sheet.anim_keys(scene.animations[f"{room} Intro"]).get(oid, {})
    return (lambda f: keys[prop].at(f)) if prop in keys else None


def emit(doc, art, spin_id, cyc, theta, T0, pre, pieces):
    """Write the room's Intro and Loop for the ball (x, y on the node, squash on Ball_01_Scale, turn on the spin pivot) and for the
    pieces: [(object id, property, fn(cycle frame) -> value, intro(f) -> value or None)]; before T0 a piece holds intro(f) (its
    own intro move) and fn(0) is added to it as a change from rest (fn must be at rest at the cycle seam).

    pre(f) -> (centre, scaleX, scaleY) on intro frames before T0 (the ball hidden in its object)."""
    L = cyc.L
    room = art.room
    loop, intro = f"{room} Loop", f"{room} Intro"
    phase0 = INTRO - 1 - T0
    assert 0 <= phase0 < L, (phase0, L)
    turns = theta[L] - theta[0]
    assert abs(turns / (2 * math.pi) - round(turns / (2 * math.pi))) < 1e-6, turns
    idx = lambda k: (phase0 + k) % L
    wraps = lambda k: (phase0 + k) // L
    fr_i, fr_l = range(INTRO), range(L + 1)
    ix, iy, isx, isy, ith = {}, {}, {}, {}, {}
    for f in fr_i:
        if f < T0:
            c, sx, sy = pre(f)
            th = theta[0]
        else:
            t = f - T0
            c, sx, sy, th = cyc.c[t], cyc.sx[t], cyc.sy[t], theta[t]
        n = art.node_of(c)
        ix[f], iy[f], isx[f], isy[f], ith[f] = n[0], n[1], sx, sy, th
    lx, ly, lsx, lsy, lth = {}, {}, {}, {}, {}
    for k in fr_l:
        n = art.node_of(cyc.c[idx(k)])
        lx[k], ly[k] = n
        lsx[k], lsy[k] = cyc.sx[idx(k)], cyc.sy[idx(k)]
        lth[k] = theta[idx(k)] + wraps(k) * turns
    doc.set_duration(loop, L + 1)
    for oid, prop, i_ser, l_ser in ((art.id, "x", ix, lx), (art.id, "y", iy, ly), (art.scale, "scaleX", isx, lsx),
                                    (art.scale, "scaleY", isy, lsy), (spin_id, "rotation", ith, lth)):
        doc.set_prop(intro, oid, prop, bake(i_ser, fr_i))
        doc.set_prop(loop, oid, prop, bake(l_ser, fr_l))
    for oid, prop, fn, own in pieces:
        assert abs(fn(0) - fn(L)) < 1e-6, (oid, prop, fn(0), fn(L))
        rest = fn(0)
        iser = {}
        for f in fr_i:
            base = own(f) if own else rest
            iser[f] = base if f < T0 else base + fn(f - T0) - rest
        lser = {k: fn(idx(k)) + ((own(INTRO - 1) - rest) if own else 0.0) for k in fr_l}
        doc.set_prop(intro, oid, prop, bake(iser, fr_i))
        doc.set_prop(loop, oid, prop, bake(lser, fr_l))
    doc.rebuild_waiting(room)
    rebuild_built(doc, room)


def last_values(doc, anim_name):
    import xml.etree.ElementTree as ET
    a, b = doc.anim(anim_name)
    root = ET.fromstring("\n".join(doc.lines[a:b + 1]))
    out = []
    for ko in root.findall("KeyedObject"):
        for kp in ko.findall("KeyedProperty"):
            keys = sorted(kp.findall("KeyFrameDouble"), key=lambda k: int(k.get("frame", 0)))
            if keys:
                out.append((ko.get("objectId"), kp.get("property"), float(keys[-1].get("value", 0))))
    return out


def rebuild_built(doc, room):
    """The room's Built pose (startScene) from its Intro's last keys. Keeps any non-number keys Built already has (none expected)."""
    lasts = last_values(doc, f"{room} Intro")
    doc.clear(f"{room} Built")
    a, b = doc.anim(f"{room} Built")
    by_obj = {}
    for oid, prop, v in lasts:
        by_obj.setdefault(oid, []).append((prop, v))
    new = []
    for oid, props in by_obj.items():
        new.append(f'            <KeyedObject objectId="{oid}" id="{doc.new_id()}">')
        for prop, v in props:
            new.append(f'                <KeyedProperty property="{prop}" id="{doc.new_id()}">')
            new += doc.key_lines([(0, v, "hold")], " " * 20)
            new.append("                </KeyedProperty>")
        new.append("            </KeyedObject>")
    doc.lines[b:b] = new


def add_hole(doc, art, parent_id, name, poly=None, ellipse=None, x=0.0, y=0.0):
    """A clip on the ball: a huge rectangle with one slot cut out (evenOdd), so the ball is hidden only inside the slot. The slot is a
    polygon [(x, y)] or an ellipse (cx, cy, w, h) in the parent's space; the shape is placed first in the parent (drawn on top, not that
    it shows: clip sources are not drawn). Returns the shape's id; key its x to slide the slot away when it is not needed."""
    hid = doc.new_id()
    i = doc.idx(parent_id)
    ind = len(doc.lines[i]) - len(doc.lines[i].lstrip()) + 4
    pad = " " * ind
    body = [f'{pad}<Shape x="{num(x)}" y="{num(y)}" name="{name}" id="{hid}">',
            f'{pad}    <Rectangle width="30000" height="30000" originX="0.5" originY="0.5" name="Path" id="{doc.new_id()}"/>']
    if poly:
        body.append(f'{pad}    <PointsPath isClosed="true" id="{doc.new_id()}">')
        body += [f'{pad}        <StraightVertex x="{num(px)}" y="{num(py)}" id="{doc.new_id()}"/>' for px, py in poly]
        body.append(f"{pad}    </PointsPath>")
    if ellipse:
        cx, cy, w, h = ellipse
        body.append(f'{pad}    <Ellipse x="{num(cx)}" y="{num(cy)}" width="{num(w)}" height="{num(h)}" id="{doc.new_id()}"/>')
    body.append(f"{pad}</Shape>")
    doc.lines[i + 1:i + 1] = body
    for shape in (art.hl, art.base):
        j = doc.end(doc.idx(shape))
        ind2 = len(doc.lines[j]) - len(doc.lines[j].lstrip()) + 4
        doc.lines[j:j] = [f'{" " * ind2}<ClippingShape sourceId="{hid}" fillRule="evenOdd" name="{name}" id="{doc.new_id()}"/>']
    return hid
