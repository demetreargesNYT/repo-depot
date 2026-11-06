"""The 3D cube method for Chapter 2's crossword rooms (The Mini first; The Midi and The Crossword next).

Each moving cube or lid is modelled in 3D, moved (a turn about its vertical axis, a hinge, a slide), and every corner is projected
back onto the drawing every frame. Faces stay plain paths whose vertices are keyed (one key a frame where they move, thinned where a
straight line between keys is within THIN_TOL), so nothing is ever scaled and every line keeps its 1.5 weight
(transformAffectsStroke="false" as well, for the intro's squash). Faces facing away are hidden (opacity 0, switched on the frame the
face is edge-on, so it never flashes), patterns on a face are its own sub-quads projected from their own 3D corners.

The projection (measured from the drawing). The room art draws each cube in an oblique projection: the front face is the true square
(x right, y down) and depth z moves a point by (dx, dy) per unit of depth. In The Mini the back edge of every cube sits (38.332,
-44.682) art units from its front edge for a 95.829 cube, so (dx, dy) = (-0.4000, -0.4663) for the top cube and the right stack (they
show their left side) and (+0.4000, -0.4663) for the front cube (it shows its right side); the left box's back square sits 28.615 to the
left for a 101.494 cube and level with the front, (dx, dy) = (-0.2819, 0): seen at its own height, it shows no top. Each cube keeps the
projection of the art around it, so a moving cube matches the still ones beside it.

Coordinates: p3 = (X, Y, Z), X and Y the drawing's own coordinates in the plane of the cube's front face (Z = 0 at rest), Z the depth
away from the viewer, in the same units.

    oblique      q = (X + Z dx, Y + Z dy)
    perspective  screen = F + (q - F) / (1 + PERSPECTIVE * Z / S)

F is the cube's front-face centre at rest, S its size. With PERSPECTIVE = 0 this is the art's projection exactly; above 0 it is a true
central projection (straight lines stay straight, planes stay planes), near points (Z < 0, a corner swinging forward in a turn) are
drawn a little larger and far ones a little smaller. Its vanishing point is F + (dx, dy) S / PERSPECTIVE, so each cube recedes the way
the art already draws it. The rest pose: the front face sits at Z = 0, where the perspective does nothing, so every front face is the
art's own square at any setting; the receding faces (tops, sides) taper by PERSPECTIVE / (1 + PERSPECTIVE) at their far edge. The still
cubes are drawn by this module too, with the same setting, so still and moving cubes always agree (the art is redrawn to the
projected rest pose; at 0 it is the art exactly, which the room asserts corner by corner).

Culling: every face's corners run clockwise as seen from outside (u x v = -n for its two in-plane axes u, v and outward normal n), so
on the screen (y down) a face faces the viewer exactly when its projected signed area is positive. Within one convex cube the faces
that face the viewer never overlap, so no ordering is needed inside a cube; between pieces the room's planes and drawing order decide.
"""
import math
import re

import common  # noqa: F401  (puts tools on the path)
from rml_edit import num

PERSPECTIVE = 0.06            # 0 = the art's pure oblique; start gentle
THIN_TOL = 0.3                # art units (0.255 px on the screen at the 0.85 scale): a vertex key is dropped where the line between its neighbours is this close
HIDDEN_GLIDE = 40              # frames: a face hidden at least this long glides (a shorter hide keeps its motion, so its
                              # turning points stay where they are and a quick crack never reads as a buzz)
LIGHT, DARK = "FFDFDBD7", "FF1F1F1F"


# ---- 3D ---------------------------------------------------------------------------------------------------------------------
def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def mul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def rotate(p, origin, axis, angle):
    """p turned by angle (radians) about the line through origin along the unit vector axis (Rodrigues)."""
    v = sub(p, origin)
    k = axis
    c, s = math.cos(angle), math.sin(angle)
    kv = k[0] * v[0] + k[1] * v[1] + k[2] * v[2]
    cr = (k[1] * v[2] - k[2] * v[1], k[2] * v[0] - k[0] * v[2], k[0] * v[1] - k[1] * v[0])
    r = tuple(v[i] * c + cr[i] * s + k[i] * kv * (1 - c) for i in range(3))
    return add(origin, r)


def turn_y(p, centre, angle):
    """Turned about the vertical axis through centre: seen from above, positive turns the front to the left (clockwise)."""
    x, z = p[0] - centre[0], p[2] - centre[2]
    c, s = math.cos(angle), math.sin(angle)
    return (centre[0] + x * c + z * s, p[1], centre[2] - x * s + z * c)


def signed_area(poly):
    """Half the shoelace sum on the screen (y down): positive for a clockwise outline, i.e. a face that faces the viewer."""
    s = 0.0
    for i in range(len(poly)):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % len(poly)]
        s += x0 * y1 - x1 * y0
    return s / 2


# ---- the camera and the cube ------------------------------------------------------------------------------------------------
class Camera:
    def __init__(self, anchor, depth, size, perspective=None):
        self.F, self.d, self.S = anchor, depth, size
        self.k = PERSPECTIVE if perspective is None else perspective

    def project(self, p):
        qx, qy = p[0] + p[2] * self.d[0], p[1] + p[2] * self.d[1]
        w = 1 + self.k * p[2] / self.S
        assert w > 0.2, ("a point too close to the viewer", p)
        return (self.F[0] + (qx - self.F[0]) / w, self.F[1] + (qy - self.F[1]) / w)


# each face: outward normal, then its in-plane axes u (along a row) and v (down a column), u x v = -n
FACES = {
    "front": ((0, 0, -1), (1, 0, 0), (0, 1, 0)),
    "back": ((0, 0, 1), (-1, 0, 0), (0, 1, 0)),
    "left": ((-1, 0, 0), (0, 0, -1), (0, 1, 0)),
    "right": ((1, 0, 0), (0, 0, 1), (0, 1, 0)),
    "top": ((0, -1, 0), (1, 0, 0), (0, 0, -1)),
    "bottom": ((0, 1, 0), (1, 0, 0), (0, 0, 1)),
}


class Cube:
    """A box seen in its own camera. front = (x0, y0, x1, y1), its front face at rest in the drawing; depth_px = (dx, dy), how far
    the drawing puts its back face from its front face; depth = its true depth (its width unless given).

    A pose is a dict: turn (radians, about its vertical axis), slide (dX, dY, dZ), lid (radians, the top's hinge on its back edge),
    door (radians, the front face's hinge on its left edge, swinging towards the viewer), tip (radians, the whole cube tipped forward
    about its bottom-front edge, applied before the turn), rot (a row-major 3 x 3 rotation about the cube's centre, applied after the
    tip: a roll in place), dip (the whole cube pressed down by that much). Missing keys are 0."""

    def __init__(self, name, front, depth_px, depth=None, perspective=None):
        x0, y0, x1, y1 = front
        self.name = name
        self.hx, self.hy = (x1 - x0) / 2, (y1 - y0) / 2
        D = depth if depth is not None else x1 - x0
        self.hz = D / 2
        self.centre = ((x0 + x1) / 2, (y0 + y1) / 2, self.hz)
        self.cam = Camera(((x0 + x1) / 2, (y0 + y1) / 2), (depth_px[0] / D, depth_px[1] / D), max(x1 - x0, y1 - y0), perspective)

    # local corners (centre at the origin) of a face, a b c d clockwise from outside, a = its top left
    def local_face(self, face):
        n, u, v = FACES[face]
        h = (self.hx, self.hy, self.hz)
        c = tuple(n[i] * h[i] for i in range(3))
        U = tuple(u[i] * h[i] for i in range(3))
        V = tuple(v[i] * h[i] for i in range(3))
        return [sub(sub(c, U), V), sub(add(c, U), V), add(add(c, U), V), add(sub(c, U), V)]

    def _joint(self, p, part, pose):
        h = (self.hx, self.hy, self.hz)
        if part == "lid" and pose.get("lid"):
            return rotate(p, (0.0, -h[1], h[2]), (1.0, 0.0, 0.0), -pose["lid"])      # the front edge rises
        if part == "lidl" and pose.get("lidl"):
            return rotate(p, (-h[0], -h[1], 0.0), (0.0, 0.0, 1.0), -pose["lidl"])   # hinged on its left edge: the right edge rises
        if part == "flap" and pose.get("flap"):
            # a side face hinged on its bottom edge, falling outwards to the left: the top edge swings out and down
            a = pose["flap"]
            dx, dy = p[0] + h[0], p[1] - h[1]
            return (-h[0] + dx * math.cos(a) + dy * math.sin(a), h[1] - dx * math.sin(a) + dy * math.cos(a), p[2])
        if part == "door" and pose.get("door"):
            return turn_y(p, (-h[0], 0.0, -h[2]), pose["door"])                         # the free edge swings towards the viewer
        return p

    def world(self, p_local, part=None, pose=None):
        pose = pose or {}
        p = self._joint(p_local, part, pose)
        if pose.get("tip"):                                  # tipped forward about the bottom-front edge, the top swinging towards the viewer
            a = pose["tip"]
            yr, zr = p[1] - self.hy, p[2] + self.hz           # from the hinge: y down (negative above it), z away from the viewer
            p = (p[0], self.hy + math.cos(a) * yr - math.sin(a) * zr, -self.hz + math.sin(a) * yr + math.cos(a) * zr)
        if pose.get("rot"):                                  # a whole-cube roll about its own centre: a row-major 3 x 3 matrix
            m = pose["rot"]
            p = (m[0] * p[0] + m[1] * p[1] + m[2] * p[2], m[3] * p[0] + m[4] * p[1] + m[5] * p[2], m[6] * p[0] + m[7] * p[1] + m[8] * p[2])
        p = turn_y(p, (0.0, 0.0, 0.0), pose.get("turn", 0.0))
        s = pose.get("slide", (0.0, 0.0, 0.0))
        d = pose.get("dip", 0.0)                             # the whole cube pressed down by d (a gather before a lid opens)
        t = pose.get("turn", 0.0)
        # A turning cube stays on the floor: its lowest bottom corner (the nearest one, which a turn swings towards the viewer) is held on the
        # floor line the cube rests on, so no corner dips below it at any angle. Exactly nothing at 0 and 90 degrees.
        if t:
            q = abs(t) / (math.pi / 2)
            dq = min(q - math.floor(q), math.ceil(q) - q) * (math.pi / 2)         # how far from the nearest face, 0 to 45 degrees
            m = min(1.0, dq / math.radians(6))                                     # fades out within 6 degrees of a face, so the follow-through is not a second swing
            lift = self.hz * (math.cos(dq) + math.sin(dq) - 1.0) * (-self.cam.d[1]) * m * m * (3 - 2 * m)
        else:
            lift = 0.0
        return (self.centre[0] + p[0] + s[0], self.centre[1] + p[1] + s[1] + d - lift, self.centre[2] + p[2] + s[2])

    def quad3(self, face, part=None, pose=None, flip=False):
        """A face's corners in the world. part: None (the body), "lid" (the top, on its hinge) or "door" (the front, on its hinge);
        flip: the other side of a thin part (a lid's underside), corners reversed so it faces the other way."""
        pts = [self.world(p, part, pose) for p in self.local_face(face)]
        return pts[::-1] if flip else pts

    def project(self, pts3):
        return [self.cam.project(p) for p in pts3]

    def quad(self, face, part=None, pose=None, flip=False):
        return self.project(self.quad3(face, part, pose, flip))

    def cells(self, face, n=3, part=None, pose=None, flip=False):
        """The n x n cells of a face, row by row from its top left, each four projected corners (clockwise from outside)."""
        a, b, c, d = self.quad3(face, part, pose)
        out = []
        for i in range(n):
            for j in range(n):
                P = lambda uu, vv: add(a, add(mul(sub(b, a), uu), mul(sub(d, a), vv)))
                q = [P(j / n, i / n), P((j + 1) / n, i / n), P((j + 1) / n, (i + 1) / n), P(j / n, (i + 1) / n)]
                out.append(self.project(q[::-1] if flip else q))
        return out


def faces_viewer(poly, eps=0.5):
    return signed_area(poly) > eps


# ---- writing the art --------------------------------------------------------------------------------------------------------
def shape_lines(doc, pad, name, pts, fill=LIGHT, stroke=True, closed=True, opacity=1.0):
    """XML for one face: a Shape at 0, 0 with a straight-edged path through pts (in its parent's space), filled and outlined at 1.5
    that never scales. Returns (lines, shape id, vertex ids)."""
    sid = doc.new_id()
    op = f' opacity="{num(opacity)}"' if num(opacity) != "1" else ""
    out = [f'{pad}<Shape{op} name="{name}" id="{sid}">', f'{pad}    <PointsPath isClosed="{"true" if closed else "false"}" id="{doc.new_id()}">']
    vids = []
    for x, y in pts:
        v = doc.new_id()
        vids.append(v)
        out.append(f'{pad}        <StraightVertex x="{num(x)}" y="{num(y)}" id="{v}"/>')
    out.append(f"{pad}    </PointsPath>")
    if fill:
        out += [f'{pad}    <Fill id="{doc.new_id()}">', f'{pad}        <SolidColor colorValue="{fill}" id="{doc.new_id()}"/>', f"{pad}    </Fill>"]
    if stroke:
        out += [f'{pad}    <Stroke thickness="1.5" cap="round" join="round" transformAffectsStroke="false" id="{doc.new_id()}">',
                f'{pad}        <SolidColor colorValue="{DARK}" id="{doc.new_id()}"/>', f"{pad}    </Stroke>"]
    out.append(f"{pad}</Shape>")
    return out, sid, vids


def clip(poly, window):
    """The part of a convex polygon inside a convex window (both clockwise on the screen), Sutherland-Hodgman."""
    out = list(poly)
    for i in range(len(window)):
        a, b = window[i], window[(i + 1) % len(window)]
        side = lambda p: (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
        src, out = out, []
        for k in range(len(src)):
            p, q = src[k], src[(k + 1) % len(src)]
            sp, sq = side(p), side(q)
            if sp >= 0:
                out.append(p)
            if (sp >= 0) != (sq >= 0):
                t = sp / (sp - sq)
                out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
        if not out:
            return []
    return out


def pattern(rows):
    """A crossword pattern from rows of 0 and 1 ("10001 00000 ..."): 1 is a black square."""
    rows = rows.split()
    assert all(len(r) == len(rows) for r in rows), rows
    return tuple(int(c) for r in rows for c in r)


class Face:
    """One drawn face and how to place it on any pose. A plain face is one quad; a pattern face (n x n, 1 = black) is the light
    face, its n - 1 grid lines each way and its black squares, all projected from their own 3D points, so they deform with the face.

    Every shape's vertices are keyed to its corners, and its opacity to whether the face faces the viewer."""

    def __init__(self, cube, face, part=None, flip=False, pattern=None, fill=LIGHT, name=None, show=None, fixed=None, two_sided=False,
                 glide_min=None, wrap_glide=False):
        self.fixed, self.two_sided = fixed, two_sided     # fixed: a pose it is always drawn at (no vertex keys); two_sided: no culling
        self.glide_min, self.wrap_glide = glide_min, wrap_glide    # glide_min: hides this short still glide; wrap_glide: after its last showing it glides to the seam pose
        self.cube, self.face, self.part, self.flip = cube, face, part, flip
        self.pattern, self.fill = pattern, fill
        self.name = name or f"{cube.name} {face.title()}" + (f" {part.title()}" if part else "") + (" Inside" if flip else "")
        self.show = show                     # an extra condition on the pose (e.g. the doorway only while the door is open)
        self.shapes = []                     # [(shape id, [vertex ids])]

    def parts(self, pose):
        """[(name, points, fill or None, closed)] from the top of the drawing down."""
        pose = self.fixed if self.fixed is not None else pose
        quad = self.cube.quad(self.face, self.part, pose, self.flip)
        if self.pattern is None:
            return [(self.name, quad, self.fill, True)]
        n = int(round(len(self.pattern) ** 0.5))
        a, b, c, d = self.cube.quad3(self.face, self.part, pose)
        P = lambda u, v: self.cube.cam.project(add(a, add(mul(sub(b, a), u), mul(sub(d, a), v))))
        out = []
        for k, black in enumerate(self.pattern):
            if black:
                i, j = divmod(k, n)
                q = [P(j / n, i / n), P((j + 1) / n, i / n), P((j + 1) / n, (i + 1) / n), P(j / n, (i + 1) / n)]
                out.append((f"{self.name} Black {k + 1}", q[::-1] if self.flip else q, DARK, True))
        for i in range(1, n):
            out.append((f"{self.name} Line {i}", [P(i / n, 0), P(i / n, 1)], None, False))
            out.append((f"{self.name} Line {n - 1 + i}", [P(0, i / n), P(1, i / n)], None, False))
        out.append((self.name, quad, LIGHT, True))
        return out

    def outline(self, pose):
        pose = self.fixed if self.fixed is not None else pose
        return self.cube.quad(self.face, self.part, pose, self.flip)

    def visible(self, pose):
        if self.show is not None and not self.show(pose):
            return False
        return True if self.two_sided else faces_viewer(self.outline(pose))

    def lines(self, doc, pad, pose, to_local):
        out = []
        op = 1.0 if self.visible(pose) else 0.0
        for nm, pts, fill, closed in self.parts(pose):
            ls, sid, vids = shape_lines(doc, pad, nm, [to_local(p) for p in pts], fill, closed=closed, opacity=op)
            out += ls
            self.shapes.append((sid, vids))
        return out

    def tracks(self, poses, to_local):
        """{(object id, property): [value per frame]} for every frame's pose. While the face is hidden its corners are not drawn,
        so they glide in a straight line from where it went out of sight to where it comes back (two keys instead of one a frame;
        it hides and shows edge-on, so nothing jumps)."""
        out = {}
        per = [self.parts(p) for p in poses]
        vis = [1.0 if self.visible(p) else 0.0 for p in poses]
        n = len(poses)
        shown = [g for g in range(n) if vis[g]]
        for k, (sid, vids) in enumerate(self.shapes):
            out[(sid, "opacity")] = vis
            for m, vid in enumerate(vids):
                pts = [to_local(per[g][k][1][m]) for g in range(n)]
                if shown:
                    for g in range(n):
                        if vis[g]:
                            continue
                        a = max((h for h in shown if h < g), default=None)
                        b = min((h for h in shown if h > g), default=None)
                        gm = HIDDEN_GLIDE if self.glide_min is None else self.glide_min
                        if self.wrap_glide and a is not None and b is None and n - 1 - a >= gm:
                            b = n - 1        # after its last showing it glides on to where the seam leaves it
                            if g == b:
                                continue
                        if a is None or b is None or b - a < gm:
                            continue        # before the first or after the last frame it shows (the seam), or a short hide
                        u = (g - a) / (b - a)
                        pts[g] = (pts[a][0] + (pts[b][0] - pts[a][0]) * u, pts[a][1] + (pts[b][1] - pts[a][1]) * u)
                out[(vid, "x")] = [p[0] for p in pts]
                out[(vid, "y")] = [p[1] for p in pts]
        return out


class Fixed:
    """A still shape shown only on some poses (the inside of a doorway): its points are fixed, only its opacity is keyed."""

    def __init__(self, cube, name, pts, fill, show):
        self.cube, self.name, self.pts, self.fill, self.show = cube, name, pts, fill, show
        self.shapes = []

    def visible(self, pose):
        return self.show(pose)

    def outline(self, pose):
        return self.pts

    def lines(self, doc, pad, pose, to_local):
        ls, sid, vids = shape_lines(doc, pad, self.name, [to_local(p) for p in self.pts], self.fill, opacity=1.0 if self.show(pose) else 0.0)
        self.shapes.append((sid, vids))
        return ls

    def tracks(self, poses, to_local):
        return {(self.shapes[0][0], "opacity"): [1.0 if self.show(p) else 0.0 for p in poses]}


# ---- thinning the baked keys --------------------------------------------------------------------------------------------------
def thin_keys(doc, anim_name, ids, tol=THIN_TOL, protect=(), props=("x", "y")):
    """In one animation, drop the per-frame linear keys of these objects' x and y that a straight line between the kept keys
    reproduces within tol (Douglas-Peucker on each track). The first and last keys always stay, and so does every key on a frame in
    `protect` (the edges of the rests, so a rest is exact and not within tol). Returns how many keys went."""
    a, b = doc.anim(anim_name)
    ids = set(ids)
    dropped = 0
    i = a
    while i < b:
        line = doc.lines[i]
        m = re.search(r'<KeyedObject objectId="([^"]+)"', line)
        if not m or m.group(1) not in ids:
            i += 1
            continue
        e = doc.end(i)
        j = i + 1
        while j < e:
            pm = re.search(r'<KeyedProperty property="([a-zA-Z]+)"', doc.lines[j])
            if not pm or pm.group(1) not in props:
                j += 1
                continue
            pe = doc.end(j)
            rows = []
            for q in range(j + 1, pe):
                l = doc.lines[q]
                if "<KeyFrameDouble" not in l:
                    continue
                assert l.rstrip().endswith("/>"), "thin_keys reads only plain (linear or hold) keys"
                fr = re.search(r' frame="(\d+)"', l)
                v = re.search(r' value="([^"]+)"', l)
                rows.append((q, int(fr.group(1)) if fr else 0, float(v.group(1)) if v else 0.0, "linear" in l))
            keep = [rows[r][1] in protect for r in range(len(rows))]
            keep[0] = keep[-1] = True
            for r, row in enumerate(rows):          # a hold key, and the key after it, stay where they are
                if not row[3]:
                    keep[r] = True
                    if r + 1 < len(rows):
                        keep[r + 1] = True
            stack = [(0, len(rows) - 1)]
            while stack:
                lo, hi = stack.pop()
                if hi - lo < 2:
                    continue
                f0, v0, f1, v1 = rows[lo][1], rows[lo][2], rows[hi][1], rows[hi][2]
                worst, at = -1.0, None
                for r in range(lo + 1, hi):
                    f, v = rows[r][1], rows[r][2]
                    err = abs(v - (v0 + (v1 - v0) * (f - f0) / (f1 - f0)))
                    if keep[r]:
                        err = float("inf")
                    if err > worst:
                        worst, at = err, r
                if worst > tol:
                    keep[at] = True
                    stack += [(lo, at), (at, hi)]
            gone = [rows[r][0] for r in range(len(rows)) if not keep[r]]
            for q in sorted(gone, reverse=True):
                del doc.lines[q]
            dropped += len(gone)
            pe -= len(gone)
            e -= len(gone)
            b -= len(gone)
            j = pe + 1
        i = e + 1
    return dropped


# ---- reading the baked keys back -------------------------------------------------------------------------------------------------
def key_values(doc, anim_name, ids):
    """{(object id, property): [(frame, value, leaves linearly)]} for these objects' x and y keys in one animation."""
    import xml.etree.ElementTree as ET
    a, b = doc.anim(anim_name)
    root = ET.fromstring("\n".join(doc.lines[a:b + 1]))
    ids = set(ids)
    out = {}
    for ko in root.findall("KeyedObject"):
        oid = ko.get("objectId")
        if oid not in ids:
            continue
        for kp in ko.findall("KeyedProperty"):
            if kp.get("property") in ("x", "y"):
                out[(oid, kp.get("property"))] = sorted((int(k.get("frame", 0)), float(k.get("value", 0)), k.get("interpolationType") == "linear")
                                                        for k in kp.findall("KeyFrameDouble"))
    return out


def value_at(rows, frame):
    """The value a key list gives on a frame (linear where the key before leaves linearly, else held)."""
    prev = rows[0]
    for r in rows:
        if r[0] > frame:
            if prev[2]:
                return prev[1] + (r[1] - prev[1]) * (frame - prev[0]) / (r[0] - prev[0])
            return prev[1]
        prev = r
    return prev[1]


def ensure_keys(doc, anim_name, wanted):
    """wanted: {(object id, property): {frame: value}}. Puts a linear key with that exact value on each of those frames that has none
    (emit's bake drops the keys inside a slow start, where the value changes by under 0.001 a frame, so the line from the last key at rest
    would creep before the move really begins). Returns how many keys it added."""
    a, b = doc.anim(anim_name)
    added = 0
    i = a
    while i < b:
        m = re.search(r'<KeyedObject objectId="([^"]+)"', doc.lines[i])
        if not m:
            i += 1
            continue
        e = doc.end(i)
        oid = m.group(1)
        j = i + 1
        while j < e:
            pm = re.search(r'<KeyedProperty property="([^"]+)"', doc.lines[j])
            if not pm:
                j += 1
                continue
            pe = doc.end(j)
            want = wanted.get((oid, pm.group(1)))
            if want:
                rows = []
                for q in range(j + 1, pe):
                    l = doc.lines[q]
                    assert "<KeyFrameDouble" in l and l.rstrip().endswith("/>"), "ensure_keys reads only plain keys"
                    fr = re.search(r' frame="(\d+)"', l)
                    rows.append((int(fr.group(1)) if fr else 0, l))
                have = {f for f, _ in rows}
                pad = " " * (len(doc.lines[j]) - len(doc.lines[j].lstrip()) + 4)
                for f, v in want.items():
                    if f not in have:
                        rows.append((f, doc.key_lines([(f, v, "linear")], pad)[0]))
                        added += 1
                rows.sort(key=lambda r: r[0])
                delta = len(rows) - (pe - j - 1)
                doc.lines[j + 1:pe] = [l for _, l in rows]
                pe += delta
                e += delta
                b += delta
            j = pe + 1
        i = e + 1
    return added
