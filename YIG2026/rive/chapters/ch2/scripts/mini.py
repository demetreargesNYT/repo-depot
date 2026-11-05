"""The Mini, "the magic trick" (Demetre's brief, 2026-11-05): the ball is a curious, slightly cheeky character and the cubes are the
props. Two moves, two rests. The full timeline (Finesse-panel times) is printed by build() and recorded in the commit that made it.

Every cube, still or moving, is drawn by the 3D cube method (cube3d.py), from one viewpoint, every face one solid colour. The
arrival (the intro, 3.2 s) is unchanged: the ball is out of sight in the top cube U and nothing moves. The cycle starts on the
intro's last frame, so the first thing after the arrival is the reveal; from then on the loop runs in the brief's order:

  1 curiosity   the ball on the floor glances (leans) at the left box L, hops once in place, rolls to L
  2 lid trick   L's lid opens (press, eased lift, swing past open, settle), the ball peeks, hops in; the lid falls shut (one soft bump);
                a 0.4 s beat with the box shut
  3 reveal      U, lid shut, rolls forward a full 90 degrees about its own centre: its back face (hidden) comes up as the new top and
                the ball, which was behind it, rides up on it into view; one small "ta-da" bounce
  4 rest 1      the ball on U's new top, one slow settle roll
  5 ride        U rolls a full 90 degrees to the left (in the picture plane) with the ball on top; the ball rolls a little down the
                tilting face, leaves it, and lands on the floor as U's next face comes flat (squash, settle roll)
  6 rest 2      the ball leans back towards U while U rolls back twice (left roll undone, then the forward roll), then it rolls to its
                starting spot

The cube moves are complete 90 degree rolls that land on a flat face (heavy: an eased slow start, a few degrees of follow-through, a
settle). U rolls in place because it is the only cube a full roll keeps inside the phone crop: a roll over an edge would carry it off
R (right) or into the air (left), L's left side is cut by the crop and F's front is cut at the bottom. U has no lid any more; L's
lid is the only lid and it never moves while a cube rolls. L's lid is hinged on its left rim, so open it stands at the box's left side
(mostly outside the crop): a lid hinged on the back edge stands right above the opening, and the ball could not drop in without
crossing it. The hop in is checked in L's own 3D space (it starts on the floor line, at the wall behind the box, and comes forward over
the right wall into the box), and on the screen it never touches the open lid.

Draw order (the room's own masks): U's front, left and top, L's and F's front and left faces and R's front are in the Front Plane, over
the ball; U's back (the face the ball rides) and right face, every lid and opening, F's top and R's top and left are in the Floor
Plane, under it. U's top is two shapes: the drop-in's copy (under the ball, in the Cubes 1 drop) shows until the drop has landed, then
the loop's copy (over the ball) takes over on a frame where the two are the same picture.

On the floor the ball sits on the floor line (y 712). Between L and U the floor line runs 2 px above the back edge of F's black top,
so on the floor the ball sits just behind that edge (0.5 px clear of its stroke).
"""
import math
import os
import re
import xml.etree.ElementTree as ET

import cube3d as c3
from cube3d import Cube, Face, LIGHT, DARK
from common import CENTER_IN_SCALE, BallArt, Cycle, _set_attrs, emit, plane_x, prepare_ball, smooth

ROOM = "The Mini"
T0 = 191                                   # the cycle starts on the intro's last frame (the arrival is the ball hidden, nothing moving)
SWAP = 115                                 # U's top changes copy here: the drop-in has landed (its squash is over at 1.82 s)
A = (747.5, 711.5)                         # the scale's anchor: the room's middle, on the floor line
K = 0.85
PLANES = {"Front": "9:5695", "Floor": "9:5694"}
CUBES = ("9:5206", "9:5208", "9:5210", "9:5212")    # the four drop-ins
ART = {"c1": "9:5207", "c3": "9:5211", "c4": "9:5213"}    # their Art nodes (their space is the planes' own space)
BALL_SCALE = 1.7
G = 0.40
G_P = G / K                                # gravity in the planes' units
R_BALL = 17.678 * BALL_SCALE               # the ball's radius on the screen (30.05)
RC_PLANE = 17.2 * BALL_SCALE / K           # the ball's centre to what it rests on, in the planes' units
FLOOR_Y = 712.0
YF = FLOOR_Y - 17.2 * BALL_SCALE           # the ball's centre when it sits on the floor line
COPY_Y = 425.0                             # the ball's top and every moving piece stay at or below this
CROP = (560.0, 935.0)
CLEAR = R_BALL + 0.75                      # the ball's centre to any edge it must not touch (its outline plus the edge's half stroke)
HID_R = (R_BALL + 0.6) / 0.98            # out of sight means the whole outline, stroke and all, is covered (disc() samples its edge at 0.98)

# ---- the cubes (the planes' own space, before the 0.85) ---------------------------------------------------------------------
D3 = (-38.332, -44.682)                    # one viewpoint for all four: the depth goes up and to the left
U = Cube("The Mini Top Cube", (795.667, 568.582, 891.496, 664.328), D3)
R = Cube("The Mini Right Stack", (891.498, 664.330, 987.327, 760.076), D3)
F = Cube("The Mini Front Cube", (679.85, 756.178, 775.679, 851.924), D3)
L = Cube("The Mini Left Box", (536.008, 664.330, 631.837, 760.076), D3)
ART_CORNERS = {                            # the drawing's own corners, for the check at PERSPECTIVE 0 (the two cubes the art draws this way)
    (U, "left"): [(757.338, 523.894), (795.67, 568.576), (795.67, 664.322), (757.338, 619.64)],
    (U, "top"): [(757.266, 523.894), (853.095, 523.894), (891.427, 568.576), (795.597, 568.576)],
    (R, "top"): [(853.097, 619.646), (948.926, 619.646), (987.257, 664.328), (891.428, 664.328)],
    (R, "left"): [(853.166, 619.646), (891.497, 664.328), (891.497, 760.074), (853.166, 715.392)],
}

# ---- tempo (frames at 60/s) -------------------------------------------------------------------------------------------------
# L's lid: a press (the box dips 1.4 and the lid 1.8 degrees closed-ward), an eased lift a few degrees past open, a settle. It shuts
# quicker: it falls under its own weight (constant acceleration) and lands with one soft bump.
OPEN_TOP, OVERSWING = math.radians(92), math.radians(4)    # past about 98 the free edge dips back and reads as a wobble
PRESS, PRESS_N, DIP = math.radians(1.8), 7, 1.4
LIFT_N, LSETTLE_N = 18, 9
OPEN_N = PRESS_N + LIFT_N + LSETTLE_N      # 35: 0.58 s
FALL_N, BUMP_N, BUMP = 14, 7, math.radians(1.5)
SHUT_N = FALL_N + BUMP_N                   # 21: 0.35 s
# U's rolls: heavy (an eased slow start, a fast middle), a few degrees of follow-through, a settle
ROLL_N, ROLL_SETTLE, OVER = 44, 14, math.radians(3.5)      # the reveal and the ride: 0.73 s + 0.23 s
RIDE_N = 66                                                # the ride's roll carries the ball: slower, 1.1 s + 0.23 s
BACK_N, BACK_SETTLE = 38, 12                               # the two rolls back: 0.63 s + 0.2 s
HALF = math.pi / 2


def S(p):
    return (A[0] + K * (p[0] - A[0]), A[1] + K * (p[1] - A[1]))


def ease_io(u):
    u = min(1.0, max(0.0, u))
    return 4 * u ** 3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2


def lift_ease(u):
    """Eases out (most of the swing early) from a standing start, and arrives with no speed."""
    s = smooth(u)
    return 1 - (1 - s) ** 2


# ---- the moves: a value per cycle frame -------------------------------------------------------------------------------------------
def lid_angle(events, g):
    """events: [(frame, "open" | "shut")] -> (lid angle, box dip) on frame g. A shut lid is exactly 0 from the end of its move."""
    a, dip = 0.0, 0.0
    for f0, kind in sorted(events):
        if g < f0:
            break
        t = g - f0
        if kind == "open":
            if t < PRESS_N:
                a, dip = -PRESS * smooth(t / PRESS_N), DIP * math.sin(math.pi * t / PRESS_N)
            elif t < PRESS_N + LIFT_N:
                a, dip = -PRESS + (OPEN_TOP + OVERSWING + PRESS) * lift_ease((t - PRESS_N) / LIFT_N), 0.0
            elif t < OPEN_N:
                a, dip = OPEN_TOP + OVERSWING * (1 - smooth((t - PRESS_N - LIFT_N) / LSETTLE_N)), 0.0
            else:
                a, dip = OPEN_TOP, 0.0
        else:
            dip = 0.0
            if t < FALL_N:
                a = OPEN_TOP * (1 - (t / FALL_N) ** 2)
            elif t < SHUT_N:
                a = BUMP * math.sin(math.pi * (t - FALL_N) / BUMP_N)
            else:
                a = 0.0
    return a, dip


def roll_angle(events, g):
    """events: [(frame, target, turn frames, settle frames)] -> the angle on frame g: eased in and out to a few degrees past the
    target, then settling onto it. Each roll starts from where the one before settled (asserted when they are made)."""
    a = 0.0
    for f0, target, tn, sn in sorted(events):
        if g < f0:
            break
        t = g - f0
        a0 = _settled(events, f0)
        over = math.copysign(OVER, target - a0)
        if t < tn:
            a = a0 + (target + over - a0) * ease_io(t / tn)
        elif t < tn + sn:
            a = target + over * (1 - smooth((t - tn) / sn))
        else:
            a = target
    return a


def _settled(events, f0):
    prev = [e for e in sorted(events) if e[0] < f0]
    return prev[-1][1] if prev else 0.0


def rx(a):
    """Rolled forward about the left-right axis through the centre: the top goes to the front (the back comes up)."""
    c, s = math.cos(a), math.sin(a)
    return ((1, 0, 0), (0, c, -s), (0, s, c))


def rz(a):
    """Rolled in the picture plane about the front-back axis through the centre: the top goes to the left (on the screen)."""
    c, s = math.cos(a), math.sin(a)
    return ((c, s, 0), (-s, c, 0), (0, 0, 1))


def matmul(a, b):
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)) for i in range(3))


def flat(m):
    return tuple(round(v, 12) for row in m for v in row)


# ---- the ball's timeline ----------------------------------------------------------------------------------------------------
class Path:
    """The ball frame by frame: centre, mode ("hidden", "air", "roll", "rest"), the turn it adds on that frame, a glance (a turn of its
    dot in place), a squash (signed: down is negative, volume kept), and what it may touch (its state, for the overlap check)."""

    def __init__(self):
        self.p, self.mode, self.w, self.glance, self.sq, self.state = [], [], [], [], [], []
        self.notes = []

    @property
    def now(self):
        return len(self.p)

    def put(self, p, mode, state, w=0.0, gl=None, sq=0.0):
        self.p.append(p)
        self.mode.append(mode)
        self.w.append(w)
        self.glance.append(self.glance[-1] if gl is None and self.glance else (gl or 0.0))
        self.sq.append(sq)
        self.state.append(state)

    def hold(self, n, mode="rest", state="free"):
        for _ in range(n):
            self.put(self.p[-1], mode, state)

    def roll(self, p1, n, state="free", ease=None):
        """A roll from rest to rest along the floor (or any level surface), eased in and out, the dot turning with the distance."""
        p0 = self.p[-1]
        prev = p0[0]
        for t in range(1, n + 1):
            s_ = (ease or smooth)(t / n)
            q = (p0[0] + (p1[0] - p0[0]) * s_, p0[1] + (p1[1] - p0[1]) * s_)
            self.put(q, "roll", state, w=(q[0] - prev) / R_BALL)
            prev = q[0]

    def squash_to(self, a, n, state="free"):
        """Eases the squash from where it is to a (negative: a gather; positive: a stretch) over n frames, in place."""
        s0 = self.sq[-1]
        for t in range(1, n + 1):
            self.put(self.p[-1], "rest", state, sq=s0 + (a - s0) * smooth(t / n))

    def glance_to(self, a, n, state="free"):
        g0 = self.glance[-1]
        for t in range(1, n + 1):
            self.put(self.p[-1], "rest", state, gl=g0 + (a - g0) * ease_io(t / n), sq=self.sq[-1])

    def hop(self, p1, T, gather, stretch=0.0, state="free", label="hop"):
        """From rest (squashed by `gather`) to a landing at p1, T frames, a parabola at 0.40. Returns (vx, vy at launch, vy at landing)."""
        p0 = self.p[-1]
        vy = (p1[1] - p0[1]) / T - 0.5 * G * T
        vx = (p1[0] - p0[0]) / T
        f_go = self.now
        w = 0.25 * vx / R_BALL
        for t in range(1, T + 1):
            q = (p0[0] + vx * t, p0[1] + vy * t + 0.5 * G * t * t)
            u = smooth(min(1.0, t / 3))
            sq = -gather * (1 - u) + stretch * u * (1 - smooth((t - 3) / 10))
            self.put(q, "air" if t < T else "roll", state, w=w if t < T else 0.0, sq=sq if t < T else 0.0)
        apex = min(y for _, y in self.p[f_go:])
        self.notes.append((label, f_go, self.now - 1, apex, (vx, vy)))
        return vx, vy, vy + G * T

    def land(self, vk, n, amp, state="free"):
        """After a landing on the floor: it keeps vk of its sideways speed and rolls to a stop over n frames, with one squash of amp that
        springs back within 12 frames. Returns where it stops."""
        p = self.p[-1]
        x0, prev = p[0], p[0]
        for t in range(1, n + 1):
            x = x0 + vk * n / 2 * (1 - (1 - t / n) ** 2)
            sq = -amp * math.sin(math.pi * min(1.0, t / 12)) ** 2 if t < 12 else 0.0
            self.put((x, p[1]), "roll", state, w=(x - prev) / R_BALL, sq=sq)
            prev = x
        return self.p[-1]


# ---- the art ----------------------------------------------------------------------------------------------------------------
def parse(doc):
    return ET.fromstring("\n".join(doc.lines))


def delete(doc, oid):
    i = doc.idx(oid)
    del doc.lines[i:doc.end(i) + 1]


def move_before(doc, oid, before_id):
    """Cut an element and put it just before another (same indent assumed)."""
    i = doc.idx(oid)
    block = doc.lines[i:doc.end(i) + 1]
    del doc.lines[i:doc.end(i) + 1]
    j = doc.idx(before_id)
    doc.lines[j:j] = block


def scale_room(doc):
    """The planes' pieces into 0.85 pivots, the drop-ins' falls compensated. Returns {plane: the pivot's Art node id}."""
    root = parse(doc)
    byid = {e.get("id"): e for e in root.iter() if e.get("id")}
    arts = {}
    for name, pid in PLANES.items():
        kids = [c for c in byid[pid] if c.tag in ("Node", "Shape")]
        piv, art = doc.wrap_run(kids[0].get("id"), kids[-1].get("id"), f"{ROOM} {name} Scale", *A)
        _set_attrs(doc, piv, {"scaleX": K, "scaleY": K})
        arts[name] = art
    a, b = doc.anim(f"{ROOM} Intro")
    for cid in CUBES:                       # the first y key of each drop: as far above its rest on screen as before
        i = next(j for j in range(a, b) if f'objectId="{cid}"' in doc.lines[j])
        j = next(j for j in range(i, doc.end(i)) if 'property="y"' in doc.lines[j])
        ks = [m for m in range(j, doc.end(j)) if "<KeyFrameDouble" in doc.lines[m]]
        val = lambda m: float(re.search(r' value="([^"]+)"', doc.lines[m]).group(1)) if ' value="' in doc.lines[m] else 0.0
        v0, v1 = val(ks[0]), val(ks[-1])
        doc.lines[ks[0]] = re.sub(r' value="[^"]+"', f' value="{v1 + (v0 - v1) / K:.4f}"', doc.lines[ks[0]])
    return arts


def insert_first(doc, parent_id, lines):
    i = doc.idx(parent_id)
    doc.lines[i + 1:i + 1] = lines


def insert_last(doc, parent_id, lines):
    j = doc.end(doc.idx(parent_id))
    doc.lines[j:j] = lines


def pad_in(doc, parent_id):
    l = doc.lines[doc.idx(parent_id)]
    return " " * (len(l) - len(l.lstrip()) + 4)


def check_rest_projection():
    """At PERSPECTIVE 0 every cube at rest is the drawing: the front faces exactly, the rest within the drawing's own 0.07 slack."""
    worst = 0.0
    for cube in (U, R, F, L):
        k0 = cube.cam.k
        cube.cam.k = 0.0
        x0, y0 = cube.centre[0] - cube.hx, cube.centre[1] - cube.hy
        x1, y1 = cube.centre[0] + cube.hx, cube.centre[1] + cube.hy
        for p, q in zip(cube.quad("front"), [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]):
            assert math.dist(p, q) < 1e-9, (cube.name, "front", p, q)
        for (c, face), pts in ART_CORNERS.items():
            if c is cube:
                got = cube.quad(face)
                for p in pts:
                    d = min(math.dist(p, g) for g in got)
                    worst = max(worst, d)
                    assert d < 0.1, (cube.name, face, p, d)
        cube.cam.k = k0
    return worst


def lid_off(pose):
    return pose.get("lidl", 0) > 1e-9


def pose_key(p):
    return tuple(round(x, 9) for v in p.values() for x in (v if isinstance(v, tuple) else (v,)))


# ---- geometry on the screen -------------------------------------------------------------------------------------------------
def inside(pt, poly):
    s = None
    for i in range(len(poly)):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % len(poly)]
        c = (x1 - x0) * (pt[1] - y0) - (y1 - y0) * (pt[0] - x0)
        if abs(c) < 1e-9:
            continue
        if s is None:
            s = c > 0
        elif (c > 0) != s:
            return False
    return True


def seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    l2 = dx * dx + dy * dy
    t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def poly_dist(p, poly):
    """How far the point is outside the polygon (negative: inside)."""
    d = min(seg_dist(p, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))
    return -d if inside(p, poly) else d


def disc(c, r):
    pts = [c]
    for rr in (0.35 * r, 0.7 * r, 0.98 * r):
        for k in range(28):
            a = 2 * math.pi * k / 28
            pts.append((c[0] + rr * math.cos(a), c[1] + rr * math.sin(a)))
    return pts


def build(doc, scene, sheet):
    worst = check_rest_projection()

    # ---------------------------------------------------------------- the old art out
    olds = ["9:5214", "9:5176", "9:5186", "9:5196", "9:5155"]        # the 'a' groups (U front, side, F, R side, L), R's top, front, inner top, the tops
    root = parse(doc)
    gone = {e.get("id") for o in olds for e in next(x for x in root.iter() if x.get("id") == o).iter() if e.get("id")}
    for o in olds:
        delete(doc, o)
    for an in ("Intro", "Waiting", "Built", "Loop"):
        a, b = doc.anim(f"{ROOM} {an}")
        for oid in sorted({m.group(1) for l in doc.lines[a:b] for m in [re.search(r'<KeyedObject objectId="([^"]+)"', l)] if m and m.group(1) in gone}):
            doc.drop_object(f"{ROOM} {an}", oid)
    move_before(doc, "9:5206", "9:5212")            # Cubes 1 (U's and F's tops) above Cubes 4 (R's top)
    arts = scale_room(doc)

    # ---------------------------------------------------------------- the ball
    art = BallArt(scene, ROOM)
    _set_attrs(doc, art.b01, {"scaleX": BALL_SCALE, "scaleY": BALL_SCALE})
    art.k = BALL_SCALE
    art.R, art.Rc = R_BALL, 17.2 * art.k
    sx, sy = -0.072021484, 0.096008301
    art.dc = (art.ox + art.k * (sx + CENTER_IN_SCALE[0]), art.oy + art.k * (sy + CENTER_IN_SCALE[1]))
    spin = prepare_ball(doc, art)

    # ---------------------------------------------------------------- the faces (made first: the path is checked against them)
    faces = {
        "front": [Face(U, "front", fill=LIGHT, name=f"{U.name} Front"), Face(U, "left", fill=LIGHT),
                  Face(U, "top", fill=DARK, name=f"{U.name} Lid"),
                  Face(L, "front", fill=LIGHT), Face(L, "left", fill=DARK),
                  Face(F, "front", fill=LIGHT), Face(F, "left", fill=LIGHT)],
        "c3": [Face(R, "front", fill=DARK)],
        "floor": [Face(U, "back", fill=LIGHT, name=f"{U.name} Back"), Face(U, "right", fill=LIGHT)],
        "c1": [Face(U, "top", fill=DARK, name=f"{U.name} Lid Drop", fixed={}),
               Face(F, "top", fill=DARK, name=f"{F.name} Top"),
               Face(L, "top", "lidl", fill=LIGHT, name=f"{L.name} Lid", two_sided=True),
               Face(L, "top", fill=DARK, name=f"{L.name} Opening", fixed={}, show=lid_off)],
        "c4": [Face(R, "top", fill=LIGHT, name=f"{R.name} Top")],
        "floor_end": [Face(R, "left", fill=LIGHT)],
    }
    over_groups, under_groups = ("front", "c3"), ("floor", "c1", "c4", "floor_end")
    drop_copy = faces["c1"][0]
    U_OVER = {f"{U.name} Front", f"{U.name} Left", f"{U.name} Lid"}
    U_BACK = f"{U.name} Back"
    L_IN = {f"{L.name} Front", f"{L.name} Left", f"{L.name} Opening"}

    # ---------------------------------------------------------------- the pieces' moves (filled in as the path is made)
    ax_ev, az_ev, lid_ev = [], [], []

    def upose(g):
        m = matmul(rz(roll_angle(az_ev, g)), rx(roll_angle(ax_ev, g)))
        return {"rot": flat(m)}

    def lpose(g):
        a, d = lid_angle(lid_ev, g)
        return {"lidl": a, "dip": d}

    def pose_of(cube, g):
        return upose(g) if cube is U else lpose(g) if cube is L else {}

    def on_u(pose, s, t, lift=0.0):
        """The ball's centre on the screen when it sits on U's back face at (s across, t down it), lifted off it by `lift`."""
        return S(U.cam.project(U.world((s, t, U.hz + RC_PLANE + lift), None, pose)))

    def shown(g, groups, skip=()):
        """[(face, polygon on the screen)] for the faces of these groups that show on frame g."""
        out = []
        for grp in groups:
            for f in faces[grp]:
                if f is drop_copy or f.name in skip:
                    continue
                ps = pose_of(f.cube, g)
                if f.visible(ps):
                    out.append((f, [S(q) for q in f.outline(ps)]))
        return out

    def clearance(g, c, allowed=()):
        """The smallest margin (centre distance minus CLEAR) from the ball at c to any showing face it may not touch on frame g."""
        worst_, at = float("inf"), None
        for f, poly in shown(g, over_groups + under_groups, skip=allowed):
            d = poly_dist(c, poly) - CLEAR
            if d < worst_:
                worst_, at = d, f.name
        return worst_, at

    l_top = [S(q) for q in L.quad("top")]           # back left, back right, front right, front left
    l_front = [S(q) for q in L.quad("front")]       # top left, top right, bottom right, bottom left
    RC = RC_PLANE

    def l_local(c, Z):
        """The ball's centre in L's own 3D space (x, y, z from the box's centre) from where it is drawn and how deep it is (Z, from the
        box's front face)."""
        cam = L.cam
        p = (A[0] + (c[0] - A[0]) / K, A[1] + (c[1] - A[1]) / K)
        w = 1 + cam.k * Z / cam.S
        qx, qy = cam.F[0] + (p[0] - cam.F[0]) * w, cam.F[1] + (p[1] - cam.F[1]) * w
        X, Y = qx - Z * cam.d[0], qy - Z * cam.d[1]
        return (X - L.centre[0], Y - L.centre[1], Z - L.hz)

    def l_floor_depth(c):
        """How deep (Z) a ball drawn at c must be to rest on the floor (the plane of L's bottom)."""
        lo, hi = -200.0, 400.0
        for _ in range(60):
            mid = (lo + hi) / 2
            if l_local(c, mid)[1] < L.hy - RC:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2

    LID_TOP = -L.hy - 2 * L.hy * math.sin(OPEN_TOP) - 2.0     # the open lid's top edge (its height above the hinge), a little over

    def l_fit(b, lid_open):
        """How well the ball at b (L's own 3D space) clears the box, in the planes' units (negative: it would be inside a wall, or
        behind the open lid where it is drawn in front of it). It is clear when it is wholly to the right of the box, wholly above its
        rim, or wholly inside it; with the lid open, over the box and below the lid's top it must also be in front of the lid."""
        x, y, z = b
        right = x - RC - L.hx
        above = -L.hy - (y + RC)
        inner = min(L.hx - RC - abs(x), L.hz - RC - abs(z), L.hy - RC - y)
        fit = max(right, above, inner)
        if lid_open and x - RC < -L.hx + 1.0 and y + RC > LID_TOP:
            fit = min(fit, LID_TOP - (y + RC))
        return fit

    P = Path()
    log = []

    def seg(kind, label, n0):
        log.append((n0, P.now, kind, label))

    # ================================================================ 3 the reveal (the cycle starts here, on the intro's last frame)
    S0 = (21.6, 6.5)                       # where on U's back face the ball waits: wholly behind U's front, left and top
    n0 = P.now
    ax_ev.append((0, HALF, ROLL_N, ROLL_SETTLE))
    for g in range(ROLL_N + ROLL_SETTLE):
        P.put(on_u(upose(g), *S0), "rest", "reveal")
    seg("move", "U rolls forward 90 degrees: its back face comes up as the new top and the ball rides up on it into view", n0)
    n0 = P.now
    P.hold(6, state="onU")
    T_TADA, H_TADA = 14, 10.0 / K                   # a pop of 10 px, no gather: the one squash is the landing
    v0 = G_P * T_TADA / 2
    pose1 = upose(P.now)
    for t in range(1, T_TADA + 1):
        P.put(on_u(pose1, *S0, lift=v0 * t - 0.5 * G_P * t * t), "air" if t < T_TADA else "rest", "onU")
    for t in range(1, 13):
        P.put(P.p[-1], "rest", "onU", sq=-0.05 * math.sin(math.pi * t / 12) ** 2)
    seg("move", "ta-da: one small bounce on the new top (squash 5 percent, once)", n0)

    # ================================================================ 4 rest 1
    n0 = P.now
    P.hold(16, state="onU")
    s_, prev = S0[0], P.p[-1][0]
    S1_U = S0[0] + 6.0                              # one slow settle roll of 5 px (about 10 degrees of turn)
    for t in range(1, 55):
        s_ = S0[0] + (S1_U - S0[0]) * smooth(t / 54)
        q = on_u(pose1, s_, S0[1])
        P.put(q, "roll", "onU", w=(q[0] - prev) / R_BALL)
        prev = q[0]
    P.hold(50, state="onU")
    seg("rest", "REST 1: on U's new top in plain view, one slow settle roll", n0)

    # ================================================================ 5 the ride
    # Slower than the reveal (it carries the ball): the ball rolls down the tilting top and leaves it at 60 degrees, with the speed
    # the face and its own roll give it (no push), and falls clear of U (tried in .cache/scratch.nosync/ch2/try/ride_probe.py)
    RIDE_REL = math.radians(60)
    n0 = P.now
    ride0 = P.now
    az_ev.append((ride0, HALF, RIDE_N, ROLL_SETTLE))
    s_, vs, prev_phi = S1_U, 0.0, 0.0
    rel = None
    for g in range(ride0, ride0 + RIDE_N + ROLL_SETTLE):
        assert g == P.now
        phi = roll_angle(az_ev, g)
        vs += -G_P * math.sin(phi)                  # it rolls down the tilting face (gravity along the slope)
        s_ += vs
        b3 = U.world((s_, S0[1], U.hz + RC_PLANE), None, upose(g))
        q = S(U.cam.project(b3))
        P.put(q, "roll", "onU", w=-(phi - prev_phi) + vs / RC_PLANE)
        prev_phi = phi
        if phi >= RIDE_REL:
            rel = g
            break
    assert rel is not None
    Z_REL = b3[2]                                  # it falls at the depth it left from
    w_air = P.w[-1]
    v = (P.p[-1][0] - P.p[-2][0], P.p[-1][1] - P.p[-2][1])
    p_rel = P.p[-1]
    t = 0
    fall = {}
    while True:
        t += 1
        q = (p_rel[0] + v[0] * t, p_rel[1] + v[1] * t + 0.5 * G * t * t)
        if q[1] >= YF:
            P.put((q[0], YF), "roll", "release")
            fall[P.now - 1] = Z_REL
            break
        P.put(q, "air", "release", w=w_air)
        fall[P.now - 1] = Z_REL
    vx_land, vy_land = v[0], v[1] + G * t
    P.notes.append(("off U to the floor", rel, P.now - 1, min(y for _, y in P.p[rel:]), v))
    LAND_N, KEEP = 20, 0.55
    P.land(KEEP * vx_land, LAND_N, 0.06)
    seg("move", "the ride: U rolls 90 degrees to the left, the ball rolls down the tilting top, leaves it and lands on the floor (squash 6 percent, settle roll)", n0)
    land_at = P.p[-1]

    # ================================================================ 6 rest 2
    n0 = P.now
    P.hold(max(0, ride0 + RIDE_N + ROLL_SETTLE - P.now) + 3)
    P.roll((land_at[0] + 5.0, YF), 26)              # a lean back towards U
    P.hold(2)
    az_ev.append((P.now, 0.0, BACK_N, BACK_SETTLE))
    P.hold(BACK_N + BACK_SETTLE + 3)
    ax_ev.append((P.now, 0.0, BACK_N, BACK_SETTLE))
    P.hold(BACK_N + BACK_SETTLE + 3)
    seg("rest", "REST 2: the ball on the floor leans back towards U while U rolls back (the left roll, then the forward roll)", n0)
    n0 = P.now
    S1 = (733.0, YF)
    P.roll(S1, 30)
    seg("move", "the ball rolls to its starting spot", n0)

    # ================================================================ 1 curiosity
    n0 = P.now
    P.hold(6)
    P.roll((S1[0] - 5.0, YF), 20)                   # a lean towards L
    P.hold(6)
    P.squash_to(-0.05, 7)
    vx, vy, _ = P.hop((S1[0] - 5.0, YF), 17, 0.05, label="the deciding hop")
    P.land(0.0, 12, 0.04)
    P.roll((P.p[-1][0] - 2.0, YF), 8)               # it settles a touch towards L
    S2 = (683.0, YF)
    P.roll(S2, 26)
    seg("move", "curiosity: a lean towards L, one hop in place (gather 5, squash 4 percent), a roll to L", n0)

    # ================================================================ 2 the lid trick
    n0 = P.now
    lid_ev.append((P.now, "open"))
    P.hold(OPEN_N)
    seg("move", "L's lid opens: press, eased lift, swing past open, settle", n0)
    n0 = P.now
    P.put(P.p[-1], "rest", "free")
    for t in range(1, 11):                          # the peek: up on its toes (3 percent) and a look into the box
        P.put(P.p[-1], "rest", "free", gl=math.radians(-12) * ease_io(t / 10), sq=0.03 * smooth(t / 10))
    for t in range(1, 15):
        P.put(P.p[-1], "rest", "free", gl=math.radians(-12) - math.radians(1.5) * math.sin(math.pi * t / 14), sq=0.03)
    P.squash_to(-0.05, 9)
    # the hop in: the shortest of a few parabolas over the box's right rim and down through the opening, out of sight behind its
    # front, that clears the box's walls (in 3D), the open lid standing on its left rim (on the screen: it is drawn under the ball
    # but stands in front of it) and the crop. The ball sits on the floor line, at the wall, a little behind the box's back; it
    # comes forward as it hops (its depth eases out). The drawn path is the parabola; the depth only decides what it clears.
    Z_S = l_floor_depth(S2)
    lid_open_poly = [S(q) for q in L.quad("top", "lidl", {"lidl": OPEN_TOP})]
    cands = []
    for T in range(26, 60):
        for xc in [x / 2 for x in range(1180, 1226)]:
            for z_i, pw in [(z, p) for z in (30.0, 34.0, 38.0, 44.0) for p in (2, 3, 4, 6)]:
                yc = 704.0
                vy_ = (yc - S2[1]) / T - 0.5 * G * T
                vx_ = (xc - S2[0]) / T
                m = 99.0
                for t in range(1, T + 1):
                    c = (S2[0] + vx_ * t, S2[1] + vy_ * t + 0.5 * G * t * t)
                    Z = Z_S + (z_i - Z_S) * (1 - (1 - t / T) ** pw)
                    m = min(m, l_fit(l_local(c, Z), True) * K, c[0] - R_BALL - CROP[0] - 0.5 if c[1] < 702 else 99,
                            poly_dist(c, lid_open_poly) - CLEAR)
                cands.append((m, T, xc, z_i, pw))
    good = [c for c in cands if c[0] >= 1.0]
    best = min(good, key=lambda c: (c[1], -c[0])) if good else max(cands)
    _, T_IN, XC, Z_I, PW = best
    if os.environ.get("MINI_DEBUG") or best[0] < 0:
        for T in (32, 40, 46):
            for xc in (591.0, 596.0, 601.0, 606.0, 611.0):
                for z_i in (36.0, 48.0):
                    vy_ = (704.0 - S2[1]) / T - 0.5 * G * T
                    vx_ = (xc - S2[0]) / T
                    parts = [99.0, 99.0, 99.0]
                    for t in range(1, T + 1):
                        c = (S2[0] + vx_ * t, S2[1] + vy_ * t + 0.5 * G * t * t)
                        Z = Z_S + (z_i - Z_S) * (1 - (1 - t / T) ** 2)
                        parts = [min(parts[0], l_fit(l_local(c, Z), True) * K),
                                 min(parts[1], c[0] - R_BALL - CROP[0] - 0.5 if c[1] < 702 else 99),
                                 min(parts[2], poly_dist(c, lid_open_poly) - CLEAR)]
                    print("   T", T, "xc", xc, "z", z_i, "3D box", round(parts[0], 1), "crop", round(parts[1], 1), "lid", round(parts[2], 1))
        print("  lid open", [tuple(round(v, 1) for v in q) for q in lid_open_poly])
        print("  the hop into L: best", best, "floor depth", Z_S, "L top", [tuple(round(v, 1) for v in q) for q in l_top])
    assert best[0] >= 0, ("no hop into L clears the box, its lid and the crop", best)
    f_hop = P.now
    P.hop((XC, 704.0), T_IN, 0.05, stretch=0.02, state="enterL", label="the hop into L")
    hop_depth = {f_hop + t - 1: Z_S + (Z_I - Z_S) * (1 - (1 - t / T_IN) ** PW) for t in range(1, T_IN + 1)}
    for i in range(f_hop, P.now):
        P.mode[i] = "air"
    f_catch = P.now - 1
    P.state[f_catch] = "hidden"
    H_L = (XC, 709.0)
    for t in range(1, 7):
        s__ = smooth(t / 6)
        P.put((XC, 704.0 + (H_L[1] - 704.0) * s__), "hidden", "hidden")
        hop_depth[P.now - 1] = Z_I
    seg("move", "the peek (up on its toes, a look in), a gather, the hop into L", n0)
    n0 = P.now
    lid_ev.append((f_catch + 1, "shut"))
    P.hold(max(0, f_catch + 1 + SHUT_N - P.now), "hidden", "hidden")
    seg("move", "L's lid falls shut, one soft bump", n0)
    n0 = P.now
    P.hold(24, "hidden", "hidden")
    seg("rest", "the beat: the box shut, the ball out of sight", n0)
    Lc = P.now                                      # frame Lc is frame 0 again: the ball is behind U (it jumps there out of sight)
    P.put(P.p[0], "hidden", "reveal")

    # ---------------------------------------------------------------- the pieces' poses, frame by frame
    for evs, kind in ((ax_ev, "x"), (az_ev, "z")):
        s_ev = sorted(evs)
        for (fa, _, tn, sn), (fb, _, _, _) in zip(s_ev, s_ev[1:]):
            assert fb - fa >= tn + sn, ("a roll starts before the one before it has settled", kind, fa, fb)
    poses = {"U": [upose(g) for g in range(Lc + 1)], "L": [lpose(g) for g in range(Lc + 1)],
             "F": [{} for _ in range(Lc + 1)], "R": [{} for _ in range(Lc + 1)]}
    for k, ps in poses.items():
        assert pose_key(ps[0]) == pose_key(ps[Lc]), k
    key_of = {U: "U", R: "R", F: "F", L: "L"}
    # moves never overlap: U and the lid never move on the same frame, U's two axes never turn at once, and L's lid is shut whenever U turns
    u_moves = [pose_key(poses["U"][g + 1]) != pose_key(poses["U"][g]) for g in range(Lc)]
    l_moves = [pose_key(poses["L"][g + 1]) != pose_key(poses["L"][g]) for g in range(Lc)]
    assert not any(a_ and b_ for a_, b_ in zip(u_moves, l_moves)), "U and L's lid move at once"
    for g in range(Lc + 1):
        ax_, az_ = roll_angle(ax_ev, g), roll_angle(az_ev, g)
        assert min(abs(ax_), abs(ax_ - HALF)) < 1e-9 or min(abs(az_), abs(az_ - HALF)) < 1e-9, ("U turns on two axes at once", g)
        if u_moves[min(g, Lc - 1)]:
            assert poses["L"][g]["lidl"] == 0.0, ("a lid is open while U turns", g)

    # ---------------------------------------------------------------- the checks on the screen, every frame
    def u_gap(g, c, Z):
        """In 3D, how far the ball drawn at c (at depth Z from U's front) is from U's body, past its radius (planes units)."""
        cam = U.cam
        p = (A[0] + (c[0] - A[0]) / K, A[1] + (c[1] - A[1]) / K)
        w = 1 + cam.k * Z / cam.S
        q = (cam.F[0] + (p[0] - cam.F[0]) * w - Z * cam.d[0], cam.F[1] + (p[1] - cam.F[1]) * w - Z * cam.d[1], Z)
        M = matmul(rz(roll_angle(az_ev, g)), rx(roll_angle(ax_ev, g)))
        b = [q[i] - U.centre[i] for i in range(3)]
        loc = [sum(M[k][i] * b[k] for k in range(3)) for i in range(3)]
        h = (U.hx, U.hy, U.hz)
        return math.sqrt(sum(max(abs(loc[i]) - h[i], 0.0) ** 2 for i in range(3))) - RC_PLANE

    fall_gap = min((u_gap(g, P.p[g], Z), g) for g, Z in fall.items())
    if fall_gap[0] <= 0:
        print("  fall gaps:", [(g, round(u_gap(g, P.p[g], Z), 2), round(P.p[g][0]), round(P.p[g][1])) for g, Z in sorted(fall.items())][:12], "release", rel, "ride0", ride0)
    assert fall_gap[0] > 0, ("the ball goes into U as it falls", fall_gap)
    hidden_frames, overlaps, l_edges = [], [], []
    for g in range(Lc + 1):
        c, st = P.p[g], P.state[g]
        covers = [poly for f, poly in shown(g, over_groups)]
        covered = all(any(inside(q, poly) for poly in covers) for q in disc(c, HID_R))
        if covered:
            hidden_frames.append(g)
        if st == "hidden":
            assert covered, ("the ball shows when it should be out of sight", g, c)
            continue
        if covered:
            continue
        assert CROP[0] <= c[0] - R_BALL and c[0] + R_BALL <= CROP[1], ("the ball leaves the phone crop", g, c)
        allowed = {"free": (), "enterL": L_IN, "reveal": U_OVER | {U_BACK}, "onU": {U_BACK}, "release": {U_BACK, f"{U.name} Right"}}[st]
        m, at = clearance(g, c, allowed)
        if m < 0:
            overlaps.append((g, at, round(m, 2), c))
        if st == "enterL":
            me = l_fit(l_local(c, hop_depth[g]), lpose(g)["lidl"] > 0) * K
            if me < 0:
                l_edges.append((g, round(me, 2)))
    if os.environ.get("MINI_DEBUG"):
        print("  overlaps:", overlaps[:40])
        print("  L edges:", l_edges[:20])
    assert not overlaps, ("the ball touches a cube it should be clear of", len(overlaps), overlaps[:12])
    assert not l_edges, ("the ball goes into a wall of L, or behind its open lid", l_edges[:12])
    # the release: from the frame it leaves U's top it moves away from it
    ball_top = min(p[1] for p in P.p) - R_BALL
    assert ball_top >= COPY_Y, ("the ball crosses the copy", ball_top)
    piece_top = min(poly[i][1] for g in range(0, Lc + 1, 2) for f, poly in shown(g, over_groups + under_groups) for i in range(len(poly)))
    assert piece_top >= COPY_Y, ("a piece crosses the copy", piece_top)
    # the intro: the ball waits out of sight in U (its front and left before the swap, and its top too after it)
    IN_U = (S(U.cam.project(U.centre))[0], S((0.0, U.centre[1] - U.hy))[1] + 36)

    def pre_pos(f):
        if f < SWAP + 2:
            return IN_U
        u = smooth((f - SWAP - 2) / 40)
        return (IN_U[0] + (P.p[0][0] - IN_U[0]) * u, IN_U[1] + (P.p[0][1] - IN_U[1]) * u)
    for f in range(0, T0 + 1, 1):
        groups = [poly for fc, poly in shown(0, ("front",)) if f >= SWAP or fc.name != f"{U.name} Lid"]
        assert all(any(inside(q, poly) for poly in groups) for q in disc(pre_pos(f), HID_R)), ("the ball shows in the arrival", f)
    assert pre_pos(T0) == P.p[0] or math.dist(pre_pos(T0), P.p[0]) < 1e-9

    # stretches: hidden (cyclic), and still while in view outside the two rests
    hid = [g in set(hidden_frames) for g in range(Lc)]
    longest_hidden, run = 0, 0
    for g in list(range(Lc)) * 2:
        run = run + 1 if hid[g] else 0
        longest_hidden = max(longest_hidden, run)
    in_rest = [False] * Lc
    for a_, b_, kind, label in log:
        if label.startswith("REST"):
            for g in range(a_, min(b_, Lc)):
                in_rest[g] = True
    still = [not hid[g] and not in_rest[g] and math.dist(P.p[g], P.p[(g + 1) % Lc]) < 0.02 and abs(P.sq[g] - P.sq[(g + 1) % Lc]) < 1e-6
             and abs(P.glance[g] - P.glance[(g + 1) % Lc]) < 1e-6 for g in range(Lc)]
    longest_still, run, still_at, start = 0, 0, None, 0
    for g in list(range(Lc)) * 2:
        if still[g]:
            if run == 0:
                start = g
            run += 1
            if run > longest_still:
                longest_still, still_at = run, start
        else:
            run = 0
    longest_still = min(longest_still, Lc)

    # ---------------------------------------------------------------- the art in
    rest_pose = lambda f: poses[key_of[f.cube]][0]
    ident = lambda p: p
    where = {"front": (arts["Front"], insert_first), "c3": (ART["c3"], insert_first), "floor": (arts["Floor"], insert_first),
             "c1": (ART["c1"], insert_first), "c4": (ART["c4"], insert_first), "floor_end": (arts["Floor"], insert_last)}
    for grp in faces:                               # a face no pose ever shows is not drawn at all
        faces[grp] = [f for f in faces[grp] if f is drop_copy or any(f.visible(poses[key_of[f.cube]][g]) for g in range(Lc + 1))]
    for grp, fs in faces.items():
        parent, put = where[grp]
        pad = pad_in(doc, parent)
        lines = []
        for f in fs:
            lines += f.lines(doc, pad, rest_pose(f), ident)
        put(doc, parent, lines)

    pieces, vertex_ids, moving_tracks = [], [], 0
    loop_lid = next(f for f in faces["front"] if f.name == f"{U.name} Lid")
    for grp, fs in faces.items():
        for f in fs:
            if f is drop_copy:
                pieces.append((f.shapes[0][0], "opacity", lambda g: 0.0, lambda fr: 1.0 if fr < SWAP else 0.0))
                continue
            ps = poses[key_of[f.cube]]
            for (oid, prop), vals in f.tracks(ps, ident).items():
                own = None
                if f is loop_lid and prop == "opacity":
                    own = lambda fr: 0.0 if fr < SWAP else 1.0
                elif max(vals) - min(vals) < 1e-6:
                    continue
                assert abs(vals[0] - vals[Lc]) < 1e-6, (f.name, oid, prop)
                pieces.append((oid, prop, (lambda g, a=vals: a[g]), own))
                if prop != "opacity":
                    vertex_ids.append(oid)
                    moving_tracks += 1

    # ---------------------------------------------------------------- the ball's keys
    cyc = Cycle(Lc)
    for g in range(Lc + 1):
        cyc.put(g, P.p[g], "air" if P.mode[g] == "air" else "hidden")
        s_ = P.sq[g]
        if s_:
            cyc.sy[g], cyc.sx[g] = 1 + s_, 1 / (1 + s_)
    th = [0.0]
    for g in range(Lc):
        th.append(th[-1] + P.w[g])
    th = [th[g] + P.glance[g] for g in range(Lc + 1)]
    total = th[Lc] - th[0]
    want = round(total / (2 * math.pi)) * 2 * math.pi
    a0 = Lc - 24                                     # the beat (out of sight in L) takes up what is left over to a whole number of turns
    for g in range(a0, Lc + 1):
        th[g] += (want - total) * smooth((g - a0) / (Lc - a0))
    px = plane_x(scene, sheet, ROOM, "Front")

    def pre(f):
        p = pre_pos(f)
        return (p[0] + px(f), p[1]), 1.0, 1.0
    emit(doc, art, spin, cyc, th, T0, pre, pieces)

    # thin the vertex keys, but keep the edge of every rest exact so a shut lid lies exactly on its box
    phase0 = 192 - 1 - T0
    pkey = {k: [pose_key(p) for p in ps] for k, ps in poses.items()}
    edges = set()
    for k, keys_ in pkey.items():
        for g in range(Lc + 1):
            prev_same = g > 0 and keys_[g] == keys_[g - 1]
            next_same = g < Lc and keys_[g] == keys_[g + 1]
            if (next_same and not prev_same) or (prev_same and not next_same):
                edges.add(g)
    protect_loop = {(g - phase0) % Lc + j for g in edges for j in (0, Lc) if (g - phase0) % Lc + j <= Lc}
    wl = {}
    for oid, prop, fn, _own in pieces:
        if prop in ("x", "y"):
            wl[(oid, prop)] = {k: fn((phase0 + k) % Lc) for k in protect_loop}
    c3.ensure_keys(doc, f"{ROOM} Loop", wl)
    ball_thinned = 0
    for an in ("Intro", "Loop"):
        ball_thinned += c3.thin_keys(doc, f"{ROOM} {an}", [spin], tol=0.003, props=("rotation",))
        ball_thinned += c3.thin_keys(doc, f"{ROOM} {an}", [art.id], tol=0.1, props=("x",))
    thinned = c3.thin_keys(doc, f"{ROOM} Loop", vertex_ids, protect=protect_loop)

    # the jump from L to behind U (both out of sight) holds, so no in-between frame ever draws the ball between them
    a, b = doc.anim(f"{ROOM} Loop")
    held = 0
    i = a
    while i < b:
        if f'<KeyedObject objectId="{art.id}"' in doc.lines[i]:
            for j in range(i, doc.end(i)):
                l = doc.lines[j]
                if "<KeyFrameDouble" in l and re.search(rf' frame="{Lc - 1}"', l):
                    doc.lines[j] = l.replace(' interpolationType="linear"', "")
                    held += 1
            break
        i += 1
    assert held == 2, ("the jump's keys", held)

    # a shut lid is exactly its box's still top: read the keys back and compare, on every frame it rests shut
    flush, flush_at = 0.0, None
    lid_faces = [f for grp in faces.values() for f in grp if getattr(f, "part", None) in ("lid", "lidl") and not f.flip]
    ids_ = [vid for f in lid_faces for vid in f.shapes[0][1]]
    rows_l = c3.key_values(doc, f"{ROOM} Loop", ids_)
    for f in lid_faces:
        ps = poses[key_of[f.cube]]
        for g in range(1, Lc):
            if not (pose_key(ps[g]) == pose_key(ps[g - 1]) == pose_key(ps[g + 1]) and ps[g]["lidl"] == 0):
                continue
            ref = f.cube.quad(f.face, None, ps[g])
            for vid, (rx_, ry_) in zip(f.shapes[0][1], ref):
                for prop, ref_v in (("x", rx_), ("y", ry_)):
                    r_ = rows_l.get((vid, prop))
                    if r_ is not None:
                        d_ = abs(c3.value_at(r_, (g - phase0) % Lc) - ref_v) * K
                        if d_ > flush:
                            flush, flush_at = d_, (f.name, g, prop)
    assert flush < 0.05, ("a shut lid is not flush with its box", flush, flush_at)

    # ---------------------------------------------------------------- the report
    sec = lambda g: f"{3.2 + g / 60:.2f}"
    table = "\n".join(f"  {sec(a_):>6}-{sec(b_):<6} {k:4s} {t_}" for a_, b_, k, t_ in log)
    flights = "; ".join(f"{lab} {sec(a_)}-{sec(b_)} s apex y {apex:.0f} (ball top {apex - R_BALL:.0f}) v ({vv[0]:.2f}, {vv[1]:.2f})"
                        for lab, a_, b_, apex, vv in P.notes)
    tight = min((clearance(g, P.p[g], {"free": (), "enterL": L_IN, "reveal": U_OVER | {U_BACK}, "onU": {U_BACK}, "release": {U_BACK, f"{U.name} Right"}}[P.state[g]])[0], g)
                for g in range(0, Lc, 1) if P.state[g] != "hidden" and g not in set(hidden_frames))
    return (f"{ROOM}: loop {Lc / 60:.2f} s ({Lc} frames), the loop starts at 3.20 s on the reveal\n{table}\n"
            f"  3D cubes (perspective {c3.PERSPECTIVE}, rest pose within {worst:.3f} of the drawing), {moving_tracks} vertex tracks keyed "
            f"({thinned} keys thinned, {ball_thinned} on the ball); L's shut lid flush within {flush:.3f} px\n"
            f"  flights: {flights}\n"
            f"  the ride: leaves U's top at {math.degrees(RIDE_REL):.0f} degrees of the roll, v ({v[0]:.2f}, {v[1]:.2f}), lands at x {land_at[0]:.1f} "
            f"(vx {vx_land:.2f}, vy {vy_land:.2f}); the hop into L: {T_IN} frames, rim clearance {best[0]:.1f} px\n"
            f"  ball top {ball_top:.0f}, pieces top {piece_top:.0f}; closest approach to a cube it may not touch: {tight[0]:.2f} px past "
            f"the edge's stroke (frame {tight[1]}, {sec(tight[1])} s)\n"
            f"  longest out of sight {longest_hidden} frames ({longest_hidden / 60:.2f} s); longest still in view outside the rests "
            f"{longest_still} frames ({longest_still / 60:.2f} s, from {sec(still_at) if still_at is not None else '-'} s)")
