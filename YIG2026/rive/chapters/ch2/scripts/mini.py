"""The Mini, "the grid trick" (Demetre's brief, 2026-11-05, with the Figma layout; pinned notes 1 to 5 of 2026-11-05 20:45 folded in): the
ball is a curious, cheeky character and six cubes on one grid are its props. The timeline (the Finesse panel's clock) is printed by build().

The grid (Figma frame the-mini-cubes, nodes 13226:109086 and 13234:109515): six cubes drawn from one viewpoint (depth goes up and to the
left), every cube touching the next along a shared face or edge. In cells (column, row from the front, level):
    front-left cube   F1 (0, 0, 0)  lidded (the lid is hinged on its back edge): the ball starts the loop inside it and ends it inside it
    front-right cube  F2 (1, 0, 0)  lidded, black front: the fake-out and the ta-da (it took over from the top cube, note 2)
    far-left cube     L0 (-1, 1, 0) black left face
    middle cube       M  (2, 1, 0)  white front, black left face: the one that spins
    right cube        R  (3, 1, 0)  black top
    top cube          T  (2, 1, 1)  plain, black top: no opening (note 2: the open lid stood too high, close to the copy)
Cubes are 84 square (the Figma's 83.6 plus the 0.4 gaps its strokes hide); the lattice sits within 0.8 px of every Figma position.
The back edge of the row-1 cubes lies on the floor line (y 712). The cubes never leave their cells: only lids lift and M turns in place.

The moves (every cube move is complete; the lids are closed while M turns; only one lid is open at a time; cube moves never overlap):
    1 out             the ball starts inside F1 (hidden through the arrival, lid shut): the lid opens, the ball gathers and bounces out onto the
                      floor in front of the grid (note 1)
    2 size up         it glances up at the open lid and hops twice along the front, counting squares
    3 in              it looks at the mouth, gathers and hops up over the rim (a glance down into the box at the top), a small turn of the dot
                      (note 4) and drops in; the lid falls shut with one bump
    4 misdirection    with the ball hidden, M turns a quarter turn: its black left face comes to the front (white to black); a beat
    5 fake-out        F2's lid lifts halfway, the ball pops up in F2 for a look, the lid drops back; a beat
    6 out of F2       F2's lid opens, the ball springs out onto F2's top (ta-da: one 6 percent squash); it hops down in front of F2 (note 3: an
                      ordinary hop, not a diagonal glide) and F2's lid falls shut behind it
    7 reset           M turns a quarter back (black to white), the ball startles, a pleased settle roll, and it rolls in front of F1
    8 back in         F1's lid opens, the ball hops in as before and the lid falls shut: the loop ends where it began

Layers: every cube face is under the ball (the Floor Plane) except two "cover" copies of F1's and F2's front faces in the Front Plane,
which switch on only while the ball is inside that cube (the under copy switches off at the same frame, so no edge is drawn twice). The
under copy of a front face sits at the top of its cube's stack, so it is stacked against its neighbours the way its cover is and the swap
changes no pixel (note 5). The ball is modelled in 3D (the grid's own space); the checks run on every frame: the ball clears every cube
face, edge and lid (sphere against rectangles), every face drawn over or under the ball is on the right side of it in depth, and when the
ball is meant to be out of sight every pixel of it is under a cover.
"""
import math
import os
import re
import xml.etree.ElementTree as ET

import cube3d as c3
from cube3d import Cube, Face, LIGHT, DARK
from common import CENTER_IN_SCALE, BallArt, Cycle, _set_attrs, emit, plane_x, prepare_ball, smooth

ROOM = "The Mini"
T0 = 191                                   # the cycle starts on the intro's last frame; the ball is inside F1 all through the arrival
LANDED = 126                               # F1's drop-in is over (its squash ends at frame 125): from here the ball and F1's cover are in
G = 0.40
BALL_SCALE = 1.7
R_BALL = 17.678 * BALL_SCALE               # the ball's drawn radius (30.05)
RC = 17.2 * BALL_SCALE                     # its centre to what it rests on (29.24)
COPY_Y = 425.0                             # the ball's top and every moving piece stay at or below this
CROP = (560.0, 935.0)
CROP_BOTTOM = 812.0
WALL = "FFC0D8F8"                          # The Mini's wall (every Mini card), was FF95BEFA
OLD_WALL = "FF95BEFA"

# ---- the grid ---------------------------------------------------------------------------------------------------------------------
S_ = 84.0
DX, DY = -33.63, -39.21                    # a cube's back face is this far from its front face on the screen (up and to the left)
UX, UY = DX / S_, DY / S_                  # the same, per unit of depth
X0, Y0 = 671.6, 706.45                     # the front-left cube's front square, top left
FLOOR = Y0 + S_                            # the floor under the front row, at depth 0
CELLS = {"F1": (0, 0, 0), "F2": (1, 0, 0), "L0": (-1, 1, 0), "M": (2, 1, 0), "R": (3, 1, 0), "T": (2, 1, 1)}
NAMES = {"F1": "The Mini Front Left Cube", "F2": "The Mini Front Right Cube", "L0": "The Mini Far Left Cube", "M": "The Mini Middle Cube",
         "R": "The Mini Right Cube", "T": "The Mini Top Cube"}
FIGMA = {"F1": (671.466, 706.023), "F2": (755.466, 706.027), "L0": (554.466, 667.023), "M": (806.14, 667.57), "R": (890.37, 667.57),
         "T": (806.14, 583.96)}              # the Figma's front squares, top left (stage coordinates), for the report only


def front_rect(c, r, h):
    x, y = X0 + S_ * c + DX * r, Y0 - S_ * h + DY * r
    return (x, y, x + S_, y + S_)


CUBE = {k: Cube(NAMES[k], front_rect(*cell), (DX, DY), perspective=0.0) for k, cell in CELLS.items()}
ZROW = {k: S_ * cell[1] for k, cell in CELLS.items()}


def to_world(k, p):
    """A point in a cube's own space -> the grid's space (X, Y of the front row's plane, Z the depth from the front row)."""
    return (p[0] - ZROW[k] / S_ * DX, p[1] - ZROW[k] / S_ * DY, p[2] + ZROW[k])


def screen(p):
    return (p[0] + p[2] * UX, p[1] + p[2] * UY)


# ---- tempo (frames at 60/s) -------------------------------------------------------------------------------------------------------
OPEN_TOP, OVERSWING = math.radians(92), math.radians(4)    # past about 98 the free edge dips back and reads as a wobble
FULL = dict(amp=OPEN_TOP, over=OVERSWING, press_n=7, lift_n=18, settle_n=9, fall_n=14, bump_n=7, bump=math.radians(1.5))
HALF = dict(amp=math.radians(38), over=math.radians(1.2), press_n=6, lift_n=16, settle_n=8, fall_n=9, bump_n=6, bump=math.radians(1.2))
PRESS, DIP = math.radians(1.8), 1.2
TURN_N, SETTLE_N, OVER = 40, 12, math.radians(3.5)         # a quarter turn of M: 0.67 s, a 3.5 degree follow-through, a 0.2 s settle
TURN_TOTAL = TURN_N + SETTLE_N
QUARTER = math.pi / 2
GL_UP = math.radians(-12)                  # a glance up and to the left (the dot turns anticlockwise)
FLIP = 0.30                                # the turn of the dot in the hop into F1, in turns (note 4: it was a whole turn)
LAYER_TOL = 3.0                            # px of depth the layering check forgives (the ball and a face meeting at a rim)


def open_n(ev):
    return ev["press_n"] + ev["lift_n"] + ev["settle_n"]


def shut_n(ev):
    return ev["fall_n"] + ev["bump_n"]


def ease_io(u):
    u = min(1.0, max(0.0, u))
    return 4 * u ** 3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2


def lift_ease(u):
    s = smooth(u)
    return 1 - (1 - s) ** 2


def lid_state(events, g):
    """events: [(frame, "open" | "shut", params)] -> (lid angle, cube dip) on frame g."""
    a, dip = 0.0, 0.0
    for f0, kind, ev in sorted(events, key=lambda e: e[0]):
        if g < f0:
            break
        t = g - f0
        if kind == "open":
            pn, ln, sn = ev["press_n"], ev["lift_n"], ev["settle_n"]
            if t < pn:
                a, dip = -PRESS * smooth(t / pn), DIP * math.sin(math.pi * t / pn)
            elif t < pn + ln:
                a, dip = -PRESS + (ev["amp"] + ev["over"] + PRESS) * lift_ease((t - pn) / ln), 0.0
            elif t < pn + ln + sn:
                a, dip = ev["amp"] + ev["over"] * (1 - smooth((t - pn - ln) / sn)), 0.0
            else:
                a, dip = ev["amp"], 0.0
        else:
            dip = 0.0
            if t < ev["fall_n"]:
                a = ev["amp"] * (1 - (t / ev["fall_n"]) ** 2)
            elif t < ev["fall_n"] + ev["bump_n"]:
                a = ev["bump"] * math.sin(math.pi * (t - ev["fall_n"]) / ev["bump_n"])
            else:
                a = 0.0
    return a, dip


def turn_state(events, g):
    """events: [(frame, target angle)]: a quarter turn, heavy: eased in and out to a few degrees past, then settling onto the target."""
    a = 0.0
    evs = sorted(events)
    for k, (f0, target) in enumerate(evs):
        if g < f0:
            break
        a0 = evs[k - 1][1] if k else 0.0
        t = g - f0
        over = math.copysign(OVER, target - a0)
        if t < TURN_N:
            a = a0 + (target + over - a0) * ease_io(t / TURN_N)
        elif t < TURN_TOTAL:
            a = target + over * (1 - smooth((t - TURN_N) / SETTLE_N))
        else:
            a = target
    return a


# ---- 3D: the ball against the cubes -------------------------------------------------------------------------------------------------
def sub3(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def dot3(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross3(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def rect_dist(p, rect):
    """Distance from a point to a rectangle in 3D (corners a, b, c, d in order)."""
    a, b, _, d = rect
    u, v, w = sub3(b, a), sub3(d, a), sub3(p, a)
    s = min(1.0, max(0.0, dot3(w, u) / dot3(u, u)))
    t = min(1.0, max(0.0, dot3(w, v) / dot3(v, v)))
    q = (a[0] + u[0] * s + v[0] * t, a[1] + u[1] * s + v[1] * t, a[2] + u[2] * s + v[2] * t)
    return math.dist(p, q)


SHELL_FACES = ("front", "left", "right", "back", "bottom")
LIDDED = ("F1", "F2")


def shell(k, pose):
    """The cube as thin rectangles in the grid's space: its five walls and its top (the lid, for the two lidded cubes)."""
    cube = CUBE[k]
    out = [(f"{k}.{f}", [to_world(k, p) for p in cube.quad3(f, None, pose)]) for f in SHELL_FACES]
    if k in LIDDED:
        out.append((f"{k}.lid", [to_world(k, p) for p in cube.quad3("top", "lid", pose)]))
    else:
        out.append((f"{k}.top", [to_world(k, p) for p in cube.quad3("top", None, pose)]))
    return out


STATIC_SHELLS = {k: shell(k, {}) for k in ("L0", "R", "T")}


def all_shells(poses):
    out = []
    for k in CELLS:
        out += STATIC_SHELLS[k] if k in STATIC_SHELLS else shell(k, poses.get(k, {}))
    return out


def gap(p, shells):
    """The smallest distance from the ball's centre to any rectangle, less what it rests on (so 0 is touching), and which one."""
    best, at = 1e9, None
    for label, rect in shells:
        d = rect_dist(p, rect) - RC
        if d < best:
            best, at = d, label
    return best, at


def sphere_depth(c, u, v, r):
    """The depth where the ray through the screen point (u, v) first meets the sphere at c, or None."""
    a = UX * UX + UY * UY + 1
    b = UX * (u - c[0]) + UY * (v - c[1]) + c[2]
    cc = (u - c[0]) ** 2 + (v - c[1]) ** 2 + c[2] ** 2 - r * r
    disc_ = b * b - a * cc
    if disc_ < 0:
        return None
    return (b - math.sqrt(disc_)) / a


def plane_depth(rect, u, v):
    """The depth where the ray through the screen point (u, v) meets the plane of a rectangle."""
    a = rect[0]
    n = cross3(sub3(rect[1], a), sub3(rect[3], a))
    den = n[2] - n[0] * UX - n[1] * UY
    if abs(den) < 1e-9:
        return None
    return (n[0] * (a[0] - u) + n[1] * (a[1] - v) + n[2] * a[2]) / den


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


def disc(c, r, rings=(0.35, 0.7, 0.98), n=24):
    pts = [c]
    for rr in rings:
        for k in range(n):
            a = 2 * math.pi * k / n
            pts.append((c[0] + rr * r * math.cos(a), c[1] + rr * r * math.sin(a)))
    return pts


HID_R = (R_BALL + 0.6) / 0.98                # out of sight: the outline and its stroke are covered (disc() samples its edge at 0.98)


# ---- the ball's timeline -----------------------------------------------------------------------------------------------------------
class Path:
    """The ball frame by frame in the grid's space: centre (X, Y, Z), mode ("air", "roll", "rest"), the turn it adds on the frame, a glance
    (the dot turning in place) and a squash (signed: down is negative, volume kept)."""

    def __init__(self):
        self.p, self.mode, self.w, self.gl, self.sq = [], [], [], [], []
        self.jumps = set()
        self.notes = []

    @property
    def now(self):
        return len(self.p)

    @property
    def at(self):
        return self.p[-1]

    def put(self, p, mode="rest", w=0.0, gl=None, sq=None):
        self.p.append(p)
        self.mode.append(mode)
        self.w.append(w)
        self.gl.append(self.gl[-1] if (gl is None and self.gl) else (gl or 0.0))
        self.sq.append(self.sq[-1] if (sq is None and self.sq) else (sq or 0.0))

    def roll_to(self, x, n, gl=None, sq=None):
        """A roll along the surface to X, eased in and out, the dot turning with the distance."""
        p0, g0 = self.at, self.gl[-1]
        prev = p0[0]
        for t in range(1, n + 1):
            s_ = smooth(t / n)
            q = (p0[0] + (x - p0[0]) * s_, p0[1], p0[2])
            self.put(q, "roll", w=(q[0] - prev) / R_BALL, gl=g0 + ((gl if gl is not None else g0) - g0) * s_, sq=sq)
            prev = q[0]

    def hold(self, n, sway=0.0, period=40):
        """Stay put; with `sway` the dot drifts a degree or so, so the ball is never exactly still."""
        g0 = self.gl[-1]
        for t in range(1, n + 1):
            self.put(self.at, "rest", gl=g0 + sway * math.sin(2 * math.pi * t / period))

    def squash_to(self, a, n):
        s0 = self.sq[-1]
        for t in range(1, n + 1):
            self.put(self.at, "rest", sq=s0 + (a - s0) * smooth(t / n))

    def glance_to(self, a, n):
        g0 = self.gl[-1]
        for t in range(1, n + 1):
            self.put(self.at, "rest", gl=g0 + (a - g0) * ease_io(t / n))

    def jump_to(self, p):
        """The ball is put somewhere else on one frame, wholly out of sight both before and after."""
        self.jumps.add(self.now)
        self.put(p, "rest")

    def hop(self, p1, T, gather=0.0, stretch=0.0, flip=0.0, glances=(), zp=None, xz=False, label="hop"):
        """From rest to a landing at p1: T frames, a parabola at 0.40 in height; X in a straight line; depth in a straight line, or
        (zp = (from, to), fractions of the flight) eased between those two moments and still before and after. It leaves from a gather
        and stretches while it is fast; `flip` adds that many turns of the dot over the second half of the flight; `glances` is
        [(frame, angle)] eased between. Returns (vx, vy, vz, vy at landing)."""
        p0 = self.at
        vy = (p1[1] - p0[1]) / T - 0.5 * G * T
        vx, vz = (p1[0] - p0[0]) / T, (p1[2] - p0[2]) / T
        f_go = self.now
        w = 0.25 * vx / R_BALL
        g0 = self.gl[-1]
        keys = [(0, g0)] + [(int(f), a) for f, a in glances]
        raw = [smooth(min(1.0, max(0.0, (t - 0.45 * T) / (0.5 * T)))) for t in range(0, T + 1)]
        dflip = [raw[t] - raw[t - 1] for t in range(1, T + 1)]
        tot = sum(dflip) or 1.0
        pts = hop_points(p0, p1, T, zp, xz)
        for t in range(1, T + 1):
            u = smooth(min(1.0, t / 3))
            sq = -gather * (1 - u) + stretch * u * (1 - smooth((t - 3) / 12))
            gl = g0
            for (fa, ga), (fb, gb) in zip(keys, keys[1:]):
                if fa <= t <= fb:
                    gl = ga + (gb - ga) * ease_io((t - fa) / max(1, fb - fa))
                elif t > fb:
                    gl = gb
            self.put(pts[t], "air" if t < T else "roll", w=w + flip * 2 * math.pi * dflip[t - 1] / tot, gl=gl, sq=sq if t < T else 0.0)
        self.notes.append((label, f_go, self.now - 1, min(y for _, y, _ in self.p[f_go:]), (vx, vy, vz)))
        return vx, vy, vz, vy + G * T

    def land(self, vk, n, amp):
        """After a landing: it keeps vk of its sideways speed and rolls to a stop over n frames (the speed falling to zero), with one
        squash of amp that springs back within 12 frames. Returns where it stops."""
        assert n >= 12
        p = self.at
        x0, prev = p[0], p[0]
        for t in range(1, n + 1):
            x = x0 + vk * n / 2 * (1 - (1 - t / n) ** 2)
            sq = -amp * math.sin(math.pi * min(1.0, t / 12)) ** 2 if t < 12 else 0.0
            self.put((x, p[1], p[2]), "roll", w=(x - prev) / R_BALL, sq=sq)
            prev = x
        return self.at


def hop_points(p0, p1, T, zp=None, xz=False):
    """The flight: height in a parabola; depth in a straight line, or eased between two moments of the flight (zp); sideways in a straight
    line, or (xz) together with the depth."""
    vy = (p1[1] - p0[1]) / T - 0.5 * G * T
    out = []
    for t in range(0, T + 1):
        u = t / T if zp is None else smooth((t / T - zp[0]) / (zp[1] - zp[0]))
        out.append((p0[0] + (p1[0] - p0[0]) * (u if xz else t / T), p0[1] + vy * t + 0.5 * G * t * t, p0[2] + (p1[2] - p0[2]) * u))
    return out


def plan_hop(p0, p1, Ts, shells, zps=(None,), margin=1.5, extra=None, xz=False):
    """The shortest flight (time, depth profile) among Ts and zps that keeps the ball `margin` clear of every rectangle on its way (the
    last two frames are the landing and may touch) and passes `extra(points)`; if none does, the one that clears best.
    Returns (T, zp, how clear)."""
    best = None
    for T in Ts:
        for zp in zps:
            pts = hop_points(p0, p1, T, zp, xz)
            worst = min(gap(q, shells)[0] for q in pts[1:T - 1])
            end = min(gap(q, shells)[0] for q in pts[T - 1:])
            ok = extra(pts) if extra else True
            if worst >= margin and end >= -0.5 and ok:
                return T, zp, worst
            score = min(worst, end + margin) - (0 if ok else 100)
            if best is None or score > best[2]:
                best = (T, zp, score)
    return best


# ---- the art ---------------------------------------------------------------------------------------------------------------------------
def parse(doc):
    return ET.fromstring("\n".join(doc.lines))


def delete(doc, oid):
    i = doc.idx(oid)
    del doc.lines[i:doc.end(i) + 1]


def move_before(doc, oid, before_id):
    i = doc.idx(oid)
    block = doc.lines[i:doc.end(i) + 1]
    del doc.lines[i:doc.end(i) + 1]
    j = doc.idx(before_id)
    doc.lines[j:j] = block


def insert_first(doc, parent_id, lines):
    i = doc.idx(parent_id)
    doc.lines[i + 1:i + 1] = lines


def pad_in(doc, parent_id):
    l = doc.lines[doc.idx(parent_id)]
    return " " * (len(l) - len(l.lstrip()) + 4)


def retarget_drop(doc, node, art, px, py):
    """A drop-in group falls from 800 above and squashes about its pivot: put the pivot at the group's base (its art keeps its place)."""
    _set_attrs(doc, node, {"x": px, "y": py})
    _set_attrs(doc, art, {"x": -px, "y": -py})
    a, b = doc.anim(f"{ROOM} Intro")
    i = next(j for j in range(a, b) if f'objectId="{node}"' in doc.lines[j])
    j = next(m for m in range(i, doc.end(i)) if 'property="y"' in doc.lines[m])
    ks = [m for m in range(j, doc.end(j)) if "<KeyFrameDouble" in doc.lines[m]]
    doc.lines[ks[0]] = re.sub(r' value="[^"]+"', f' value="{py - 800:.4f}"', doc.lines[ks[0]])
    doc.lines[ks[-1]] = re.sub(r' value="[^"]+"', f' value="{py:.4f}"', doc.lines[ks[-1]])


def set_wall(doc):
    a, b = doc.anim(f"{ROOM} Colors")
    n = 0
    for i in range(a, b):
        if f'value="{OLD_WALL}"' in doc.lines[i]:
            doc.lines[i] = doc.lines[i].replace(OLD_WALL, WALL)
            n += 1
    assert n == 1, ("the Mini's wall colour was not found once in its Colors pose", n)


def build(doc, scene, sheet):
    # ---------------------------------------------------------------- the old art out, the wall in
    olds = ["9:5214", "9:5176", "9:5186", "9:5196", "9:5155"]        # the 'a' groups and the four old cube shapes
    root = parse(doc)
    gone = {e.get("id") for o in olds for e in next(x for x in root.iter() if x.get("id") == o).iter() if e.get("id")}
    for o in olds:
        delete(doc, o)
    for an in ("Intro", "Waiting", "Built", "Loop"):
        a, b = doc.anim(f"{ROOM} {an}")
        for oid in sorted({m.group(1) for l in doc.lines[a:b] for m in [re.search(r'<KeyedObject objectId="([^"]+)"', l)] if m and m.group(1) in gone}):
            doc.drop_object(f"{ROOM} {an}", oid)
    set_wall(doc)
    # the four drop-in groups all go under the ball, in the order the cubes overlap (top first): front pair, far left, top, middle + right
    move_before(doc, "9:5208", "9:5212")
    move_before(doc, "9:5210", "9:5212")
    P_NODE, S_NODE, U_NODE, Q_NODE = ("9:5206", "9:5207"), ("9:5210", "9:5211"), ("9:5208", "9:5209"), ("9:5212", "9:5213")
    front_bottom = lambda k: CUBE[k].centre[1] + CUBE[k].hy
    mid_x = lambda *ks: sum(CUBE[k].centre[0] for k in ks) / len(ks)
    retarget_drop(doc, *P_NODE, mid_x("M", "R"), front_bottom("M"))        # middle + right: first down
    retarget_drop(doc, *S_NODE, mid_x("L0"), front_bottom("L0"))           # far left
    retarget_drop(doc, *U_NODE, mid_x("F1", "F2"), front_bottom("F1"))     # the front pair
    retarget_drop(doc, *Q_NODE, mid_x("T"), front_bottom("T"))             # the top cube: last, onto the middle one

    # ---------------------------------------------------------------- the ball
    art = BallArt(scene, ROOM)
    _set_attrs(doc, art.b01, {"scaleX": BALL_SCALE, "scaleY": BALL_SCALE})
    art.k = BALL_SCALE
    art.R, art.Rc = R_BALL, 17.2 * art.k
    sx, sy = -0.072021484, 0.096008301
    art.dc = (art.ox + art.k * (sx + CENTER_IN_SCALE[0]), art.oy + art.k * (sy + CENTER_IN_SCALE[1]))
    spin = prepare_ball(doc, art)

    # ================================================================ the timeline
    YB = FLOOR - RC                                # the ball's centre on the floor / on the bottom of a box
    ZF = -31.0                                     # in front of the grid, on the floor (its outline stays inside the crop's bottom edge)
    IN_F1 = (722.0, YB, 40.0)                      # inside F1, wholly behind its front square
    IN_F2 = (806.0, YB, 40.0)                      # inside F2, wholly behind its front square
    ON_F2 = (797.0, Y0 - RC, 42.0)                 # on F2's top
    OUT_F1 = (794.0, YB, ZF)                       # where it lands coming out of F1 (and rolls on to its start spot, about x 800)
    DOWN_F2 = (768.0, YB, ZF)                      # where it lands coming down from F2: straight below where it left, on the screen
    RIM = Y0                                       # the front row's front squares' top edge on the screen

    P = Path()
    lid1, lid2, turns = [], [], []
    log = []
    marks = {}

    def seg(kind, label, n0):
        log.append((n0, P.now, kind, label))

    def enter_ok(pts):
        """Once the ball comes down past the front square's top edge on the screen, it is wholly behind the front wall's plane."""
        ia = min(range(len(pts)), key=lambda t: pts[t][1])
        on = next((t for t in range(ia, len(pts)) if pts[t][2] >= RC - 0.7), None)
        return on is not None and screen(pts[on])[1] + R_BALL < RIM - 0.5 and all(q[2] >= RC - 0.7 for q in pts[on:])

    def exit_ok(pts):
        """Mirror of enter_ok: while the ball is still behind the front wall's plane it is already clear above the edge on the screen."""
        off = max((t for t in range(len(pts)) if pts[t][2] >= RC - 0.7), default=None)
        return off is not None and pts[off][1] <= Y0 - RC + 0.5 and screen(pts[off])[1] + R_BALL < RIM - 0.5 and all(q[2] >= RC - 0.7 for q in pts[:off + 1])

    zps_in = [(a, b) for a in (0.2, 0.3, 0.4) for b in (0.55, 0.65, 0.75, 0.85)]
    zps_out = [(a, b) for a in (0.30, 0.35, 0.4, 0.45) for b in (0.5, 0.55, 0.6, 0.65, 0.7)]

    def lid_trick_in(label_extra=""):
        """The ball looks up at F1's open lid, looks at the mouth, gathers, hops in and the lid falls shut."""
        n0 = P.now
        P.glance_to(GL_UP * 1.6, 10)
        P.glance_to(math.radians(6), 9)
        P.squash_to(-0.05, 9)
        seg("move", "looks up at the lid, then at the mouth, and gathers" + label_extra, n0)
        n0 = P.now
        T_IN, zp_in, _ = plan_hop(P.at, IN_F1, range(36, 60), all_shells(dict(F1={"lid": OPEN_TOP}, F2={})), zps_in, extra=enter_ok)
        f_hop = P.now
        P.hop(IN_F1, T_IN, gather=0.05, stretch=0.03, flip=FLIP, zp=zp_in,
              glances=[(0.40 * T_IN, math.radians(6)), (0.50 * T_IN, math.radians(24)), (0.62 * T_IN, math.radians(6))], label="peek hop into F1")
        marks.setdefault("F1 in", []).append((f_hop, P.now - 1))
        for t in range(1, 7):
            P.put(P.at, "rest", sq=P.sq[-1] * (1 - t / 6))
        seg("move", f"the peek hop: straight up, over the rim (a glance down into the box at the top), a small turn and a drop in ({T_IN} frames)", n0)
        n0 = P.now
        P.hold(4)
        lid1.append((P.now, "shut", FULL))
        P.glance_to(0.0, shut_n(FULL))
        seg("move", "F1's lid falls shut, one bump", n0)

    P.put(IN_F1, "rest", gl=0.0, sq=0.0)               # frame 0: inside F1, the lid shut

    # ------------------------------------------------------------ 1 out (note 1: the ball starts inside the box and bounces out)
    n0 = P.now
    lid1.append((P.now, "open", FULL))
    P.hold(open_n(FULL) - 8)
    P.squash_to(-0.05, 8)                                      # gathers inside
    seg("move", "F1's lid opens (press, eased lift, past open, settle); the ball gathers inside", n0)
    n0 = P.now
    T_OUT1, zp_out1, _ = plan_hop(P.at, OUT_F1, range(36, 66), all_shells(dict(F1={"lid": OPEN_TOP}, F2={})), zps_out, extra=exit_ok, xz=True)
    f_out1 = P.now
    vx_o, *_ = P.hop(OUT_F1, T_OUT1, gather=0.05, stretch=0.03, zp=zp_out1, xz=True, label="bounce out of F1")
    marks["F1 out"] = (f_out1, P.now - 1)
    P.land(0.5 * vx_o, 12, 0.06)
    seg("move", f"the ball bounces out of F1 onto the floor in front ({T_OUT1} frames in the air), squash and a settle roll", n0)

    # ------------------------------------------------------------ 2 size up (the ball counts the squares)
    n0 = P.now
    P.roll_to(P.at[0] - 4.0, 14, gl=GL_UP)                     # settles and glances up at the open lid
    P.squash_to(-0.05, 6)
    vx, *_ = P.hop((P.at[0] - 38.0, YB, ZF), 22, gather=0.05, stretch=0.02, label="count 1")
    P.land(0.55 * vx, 12, 0.06)
    P.squash_to(-0.04, 5)
    vx, *_ = P.hop((P.at[0] - 36.0, YB, ZF), 22, gather=0.04, stretch=0.02, label="count 2")
    P.land(0.55 * vx, 12, 0.05)
    seg("move", "2 size up: settles, glances up at the open lid, two quick hops along the front", n0)

    # ------------------------------------------------------------ 3 in
    lid_trick_in()

    # ------------------------------------------------------------ 4 misdirection
    n0 = P.now
    P.hold(4)
    turns.append((P.now, -QUARTER))
    f_turn1 = P.now
    P.hold(TURN_TOTAL)
    seg("move", "M turns a quarter turn: its black left face comes round to the front (white to black)", n0)
    n0 = P.now
    P.hold(8)
    P.jump_to(IN_F2)                                           # out of sight in F1, and on the next frame out of sight in F2
    P.hold(22)
    seg("rest", "a beat (the ball moves from F1 to F2 unseen)", n0)

    # ------------------------------------------------------------ 5 the fake-out
    n0 = P.now
    lid2.append((P.now, "open", HALF))
    P.hold(HALF["press_n"] + 4)                                # the lid starts to lift; the ball waits a moment
    P.hop(IN_F2, 24, gather=0.04, stretch=0.03, glances=[(7, math.radians(15)), (17, math.radians(-15))], label="pop up in F2")
    P.land(0.0, 12, 0.04)
    seg("move", "F2's lid lifts halfway; the ball pops up for a look (its top over the rim) and drops back in", n0)
    n0 = P.now
    P.hold(3)
    lid2.append((P.now, "shut", HALF))
    P.hold(shut_n(HALF) + 2)
    seg("move", "F2's lid drops back", n0)
    n0 = P.now
    P.hold(22)
    seg("rest", "a beat", n0)

    # ------------------------------------------------------------ 6 out of F2
    n0 = P.now
    lid2.append((P.now, "open", FULL))
    P.hold(open_n(FULL) - 8)
    P.squash_to(-0.05, 8)                                      # gathers inside
    seg("move", "F2's lid opens properly", n0)
    n0 = P.now
    T_OUT2, zp_out2, _ = plan_hop(P.at, ON_F2, range(24, 50), all_shells(dict(F1={}, F2={"lid": OPEN_TOP})))
    f_hop2 = P.now
    P.hop(ON_F2, T_OUT2, gather=0.05, stretch=0.03, zp=zp_out2, label="spring out of F2")
    marks["F2 out"] = (f_hop2, P.now - 1)
    P.land(0.0, 13, 0.06)                                      # ta-da: the one squash
    P.hold(4)
    seg("move", f"the ball springs out onto F2's top and lands: ta-da, one 6 percent squash ({T_OUT2} frames in the air)", n0)
    n0 = P.now
    P.glance_to(math.radians(10), 14)
    P.glance_to(math.radians(-8), 14)
    seg("rest", "ta-da: a proud little glance on top of F2", n0)
    n0 = P.now
    P.squash_to(-0.05, 6)
    T_DOWN, zp_down, _ = plan_hop(P.at, DOWN_F2, range(26, 60), all_shells(dict(F1={}, F2={"lid": OPEN_TOP})),
                                  [(a, b) for a in (0.0, 0.05, 0.1, 0.15, 0.2) for b in (0.3, 0.4, 0.5, 0.6, 0.7)])
    f_down = P.now
    vx3, *_ = P.hop(DOWN_F2, T_DOWN, gather=0.05, stretch=0.02, zp=zp_down, label="hop down in front of F2")
    marks["F2 down"] = (f_down, P.now - 1)
    P.land(0.45 * vx3, 14, 0.06)
    seg("move", f"it hops down in front of F2 ({T_DOWN} frames in the air), squash and a settle roll", n0)

    # ------------------------------------------------------------ 7 reset
    n0 = P.now
    f_turn2 = P.now
    turns.append((P.now, 0.0))
    P.glance_to(math.radians(14), 18)                          # watches the cube
    P.hold(TURN_N - 18 - 4, sway=math.radians(0.8), period=18)
    P.squash_to(0.03, 4)                                       # the startle at the thump: a small hop
    P.hop((P.at[0] - 3.0, YB, ZF), 18, gather=-0.03, label="startle hop")
    P.land(0.0, 12, 0.03)
    P.glance_to(0.0, 8)
    seg("move", "M turns a quarter back (black to white); the ball startles with a small hop", n0)
    n0 = P.now
    P.roll_to(P.at[0] + 5.0, 22, gl=math.radians(-6))          # a pleased settle roll
    P.roll_to(P.at[0] - 1.5, 10, gl=math.radians(3))
    seg("move", "a pleased settle roll", n0)

    # ------------------------------------------------------------ 8 back in (the loop ends where it began)
    n0 = P.now
    P.roll_to(716.0, 34, gl=0.0)                               # in front of F1
    seg("move", "it rolls along the front to F1", n0)
    n0 = P.now
    P.glance_to(GL_UP * 1.6, 10)                               # looks up at the lid before it does it
    lid1.append((P.now, "open", FULL))
    P.glance_to(GL_UP * 2.0, FULL["press_n"] + FULL["lift_n"])
    P.hold(FULL["settle_n"], sway=math.radians(1.0), period=20)
    seg("move", "F1's lid opens (press, eased lift, past open, settle)", n0)
    lid_trick_in(" (the way back in)")
    P.hold(6)                                                  # the lid has settled and the ball is out of sight before the loop wraps
    Lc = P.now
    P.put(IN_F1, "rest", gl=0.0, sq=0.0)                       # frame Lc is frame 0 again
    assert abs(P.sq[Lc]) < 1e-12 and abs(P.gl[Lc - 1]) < 1e-12 and abs(P.sq[Lc - 1]) < 1e-12 and math.dist(P.p[Lc - 1], IN_F1) < 1e-9, \
        ("the loop does not end where it began", P.sq[Lc - 1], P.gl[Lc - 1], P.p[Lc - 1])

    # ---------------------------------------------------------------- when the covers are on, and when F2's lid falls shut
    def disc_bottom(g):
        return screen(P.p[g])[1] + R_BALL

    def apex(rng):
        return min(range(rng[0], rng[1] + 1), key=lambda g: P.p[g][1])
    j1 = min(P.jumps)
    c1a_off = next(g for g in range(marks["F1 out"][0], marks["F1 out"][1] + 1) if P.p[g][2] < RC - 0.7)
    assert disc_bottom(c1a_off) < RIM - 0.5, ("F1's cover would cut the ball as it leaves", c1a_off)
    c1b_on = next(g for g in range(apex(marks["F1 in"][0]), marks["F1 in"][0][1] + 1) if P.p[g][2] >= RC - 0.7)
    c1c_on = next(g for g in range(apex(marks["F1 in"][1]), marks["F1 in"][1][1] + 1) if P.p[g][2] >= RC - 0.7)
    for g in (c1b_on, c1c_on):
        assert disc_bottom(g) < RIM - 0.5, ("F1's cover would cut the ball as it comes in", g)
    c1b_off = j1 + 3
    c2_on = j1 - 2
    c2_off = next(g for g in range(marks["F2 out"][0] + 3, marks["F2 out"][1]) if disc_bottom(g) < RIM - 1.0)
    cover_f1 = lambda g: 1 if (g < c1a_off or c1b_on <= g < c1b_off or g >= c1c_on) else 0
    cover_f2 = lambda g: 1 if c2_on <= g < c2_off else 0
    close_at = None
    for off in range(0, 30):                                   # F2's lid falls shut once the ball's flight has taken it clear of the sweep
        ev_close = f_down + off
        bad = 0
        for g in range(ev_close, ev_close + shut_n(FULL) + 2):
            a, _ = lid_state(lid2 + [(ev_close, "shut", FULL)], g)
            d, _ = gap(P.p[min(g, Lc)], shell("F2", {"lid": a}))
            bad += d < 1.5
        if not bad:
            close_at = ev_close
            break
    assert close_at is not None, "F2's lid cannot shut clear of the ball"
    lid2.append((close_at, "shut", FULL))
    assert close_at + shut_n(FULL) <= f_turn2, ("F2's lid is still moving when M turns back", close_at, f_turn2)

    # ---------------------------------------------------------------- the cubes' poses, frame by frame
    def opening(events, g):
        """The dark opening shows while the lid is up, and one frame either side (under a flush lid it cannot be seen): note 5, no gaps."""
        return 1 if any(lid_state(events, g + d)[0] > 1e-9 for d in (-1, 0, 1)) else 0

    def poses_at(g):
        a1, d1 = lid_state(lid1, g)
        a2, d2 = lid_state(lid2, g)
        return {"F1": {"lid": a1, "dip": d1, "cover": cover_f1(g), "ov": opening(lid1, g)},
                "F2": {"lid": a2, "dip": d2, "cover": cover_f2(g), "ov": opening(lid2, g)},
                "M": {"turn": turn_state(turns, g)}, "L0": {}, "R": {}, "T": {}}
    poses = [poses_at(g) for g in range(Lc + 1)]
    flags = ("cover", "ov")
    pk = lambda p: tuple(round(x, 9) for v in p.values() for x in (v if isinstance(v, tuple) else (v,)))
    geom = lambda p: {kk: v for kk, v in p.items() if kk not in flags}
    for k in CELLS:
        assert pk(poses[0][k]) == pk(poses[Lc][k]), ("the loop does not close on", k)

    # ---------------------------------------------------------------- the rules for the cubes
    moving = [{k for k in CELLS if pk(geom(poses[g + 1][k])) != pk(geom(poses[g][k]))} for g in range(Lc)]
    assert all(len(m) <= 1 for m in moving), ("two cubes move at once", [(g, m) for g, m in enumerate(moving) if len(m) > 1][:6])
    for g in range(Lc + 1):
        assert not (poses[g]["F1"]["lid"] > 1e-9 and poses[g]["F2"]["lid"] > 1e-9), ("two lids open at once", g)
        if "M" in moving[min(g, Lc - 1)]:
            assert poses[g]["F1"]["lid"] == 0.0 and poses[g]["F2"]["lid"] == 0.0, ("a lid is open while M turns", g)
    for g in range(Lc + 1):
        t = poses[g]["M"]["turn"]
        if min(abs(t - 0.0), abs(t + QUARTER)) > 1e-6:
            assert any(g0 <= g <= g0 + TURN_TOTAL for g0, _ in turns), ("M is turned part way and still", g)

    # ---------------------------------------------------------------- the faces
    def face(k, f_, part=None, flip=False, fill=LIGHT, name=None, **kw):
        return Face(CUBE[k], f_, part, flip=flip, fill=fill, name=name or f"{NAMES[k]} {f_.title()}", **kw)

    unc = lambda p: p.get("cover", 0) == 0
    cov = lambda p: p.get("cover", 0) > 0
    opn = lambda p: p.get("ov", 0) > 0
    f = {}
    f["F1 front"] = face("F1", "front", show=unc)
    f["F1 lid"] = face("F1", "top", "lid", name=f"{NAMES['F1']} Lid")
    f["F1 lid in"] = face("F1", "top", "lid", True, name=f"{NAMES['F1']} Lid Inside")
    f["F1 open"] = face("F1", "top", fill=DARK, name=f"{NAMES['F1']} Opening", fixed={}, show=opn)
    f["F1 left"] = face("F1", "left", fill=DARK)
    f["F2 front"] = face("F2", "front", fill=DARK, show=unc)
    f["F2 lid"] = face("F2", "top", "lid", name=f"{NAMES['F2']} Lid")
    f["F2 lid in"] = face("F2", "top", "lid", True, name=f"{NAMES['F2']} Lid Inside")
    f["F2 open"] = face("F2", "top", fill=DARK, name=f"{NAMES['F2']} Opening", fixed={}, show=opn)
    f["L0 top"] = face("L0", "top")
    f["L0 left"] = face("L0", "left", fill=DARK)
    f["L0 front"] = face("L0", "front")
    f["T top"] = face("T", "top", fill=DARK)
    f["T left"] = face("T", "left")
    f["T front"] = face("T", "front")
    f["R top"] = face("R", "top", fill=DARK)
    f["R front"] = face("R", "front")
    f["M top"] = face("M", "top", fill=DARK)
    f["M left"] = face("M", "left", fill=DARK)
    f["M front"] = face("M", "front")
    f["M right"] = face("M", "right")
    f["M back"] = face("M", "back")
    f["R left"] = face("R", "left", name=f"{NAMES['R']} Left Side")
    f["F1 cover"] = face("F1", "front", name=f"{NAMES['F1']} Front Cover", show=cov)
    f["F2 cover"] = face("F2", "front", fill=DARK, name=f"{NAMES['F2']} Front Cover", show=cov)
    groups = {                                             # top first; a front face is at the top of its cube's stack (note 5)
        "U": ["F1 front", "F1 lid", "F1 lid in", "F1 open", "F1 left", "F2 front", "F2 lid", "F2 lid in", "F2 open"],
        "S": ["L0 top", "L0 left", "L0 front"],
        "Q": ["T top", "T left", "T front"],
        "P": ["R top", "R front", "M top", "M left", "M front", "M right", "M back", "R left"],
        "C": ["F1 cover", "F2 cover"],
    }
    key_of = {CUBE[k]: k for k in CELLS}
    for name, fc in f.items():                             # a face no pose ever shows is not drawn at all
        if not any(fc.visible(poses[g][key_of[fc.cube]]) for g in range(Lc + 1)):
            for lst in groups.values():
                if name in lst:
                    lst.remove(name)
    where = {"U": U_NODE[1], "S": S_NODE[1], "Q": Q_NODE[1], "P": P_NODE[1], "C": "9:5695"}      # the covers go over the ball: the Front Plane
    ident = lambda p: p
    for grp, names in groups.items():
        parent = where[grp]
        pad = pad_in(doc, parent)
        lines = []
        for nm in names:
            fc = f[nm]
            lines += fc.lines(doc, pad, poses[0][key_of[fc.cube]], ident)
        insert_first(doc, parent, lines)

    # ---------------------------------------------------------------- the checks, every frame
    def corners(fc, pose):
        pose = fc.fixed if fc.fixed is not None else pose
        return [to_world(key_of[fc.cube], p) for p in fc.cube.quad3(fc.face, fc.part, pose, fc.flip)]
    drawn = [(nm, f[nm]) for grp in groups.values() for nm in grp]
    tight = (1e9, None, None)
    hset, layer_bad, crop_bad, negs = set(), [], [], []
    for g in range(Lc + 1):
        c = P.p[g]
        d, at = gap(c, all_shells({k: poses[g][k] for k in CELLS}))
        if d < tight[0] and g not in P.jumps:
            tight = (d, g, at)
        if d < -0.6 and g not in P.jumps:
            negs.append((g, round(d, 1), at, tuple(round(v, 1) for v in c)))
        sc = screen(c)
        covers_now, under = [], []
        for nm, fc in drawn:
            ps = poses[g][key_of[fc.cube]]
            if fc.visible(ps):
                (covers_now if nm.endswith("cover") else under).append((nm, fc.outline(ps), corners(fc, ps)))
        cpoly = [poly for _, poly, _ in covers_now]
        ring = disc(sc, HID_R)
        if cpoly and all(any(inside(q, poly) for poly in cpoly) for q in ring):
            hset.add(g)
            continue
        if not (CROP[0] <= sc[0] - R_BALL and sc[0] + R_BALL <= CROP[1] and sc[1] + R_BALL <= CROP_BOTTOM):
            crop_bad.append((g, tuple(round(v, 1) for v in sc)))
        for q in disc(sc, R_BALL):
            zb = sphere_depth(c, q[0], q[1], R_BALL)
            if zb is None:
                zb = c[2] - 8.0
            for nm, poly, cs in covers_now:                    # a cover over the ball must be nearer than the ball
                if inside(q, poly):
                    zf = plane_depth(cs, q[0], q[1])
                    if zf is not None and zf > zb + LAYER_TOL:
                        layer_bad.append((g, nm, "cover behind the ball", round(zf - zb, 1)))
            for nm, poly, cs in under:                         # a face under the ball must be farther than the ball
                if nm.endswith(" open"):
                    continue                                   # an opening is a hole: the ball is seen through it
                if inside(q, poly):
                    zf = plane_depth(cs, q[0], q[1])
                    if zf is not None and zf < zb - LAYER_TOL:
                        layer_bad.append((g, nm, "face in front of the ball", round(zb - zf, 1)))
    if os.environ.get("MINI_TOGGLES"):
        for nm, fc in drawn:
            vis = [fc.visible(poses[g][key_of[fc.cube]]) for g in range(Lc + 1)]
            ch = [g for g in range(1, Lc + 1) if vis[g] != vis[g - 1]]
            if ch:
                print("  toggles", nm, ch)
        print("  covers: F1 off", c1a_off, "on", c1b_on, "off", c1b_off, "on", c1c_on, "; F2", c2_on, c2_off, "; jump", j1)
    if os.environ.get("MINI_DEBUG"):
        seen = {}
        for g, nm, why, amount in layer_bad:
            seen.setdefault((nm, why), []).append((g, amount))
        for key, v in seen.items():
            print("  layer:", key, "frames", [g for g, _ in v][:14], "worst", max(a for _, a in v))
        runs = []
        for g, d, at, c in negs:
            if runs and runs[-1][1] == g - 1 and runs[-1][3] == at:
                runs[-1][1], runs[-1][2] = g, min(runs[-1][2], d)
            else:
                runs.append([g, g, d, at, c])
        print("  touching:", runs[:12])
        print("  tightest:", tight, " crop:", crop_bad[:10])
    assert tight[0] > -0.6, ("the ball touches a cube", tight, negs[:4])
    assert not crop_bad, ("the ball leaves the phone crop", crop_bad[:6])
    seen = {}
    for g, nm, why, amount in layer_bad:
        seen.setdefault((nm, why), []).append(g)
    assert not seen, ("the ball is on the wrong side of a face", {k: (v[0], v[-1], len(v)) for k, v in seen.items()})
    ball_top = min(screen(p)[1] for p in P.p) - R_BALL
    assert ball_top >= COPY_Y, ("the ball crosses the copy", ball_top)
    piece_top = min(CUBE[k].centre[1] - CUBE[k].hy for k in CELLS)
    lid_top = Y0 + DY - S_ * math.sin(OPEN_TOP)
    assert lid_top >= COPY_Y, ("a lid crosses the copy", lid_top)

    hid = [g in hset for g in range(Lc)]
    longest_hidden, run, run_at = 0, 0, 0
    for g in list(range(Lc)) * 2:
        run = run + 1 if hid[g] else 0
        if run > longest_hidden:
            longest_hidden, run_at = run, g
    in_rest = [any(a_ <= g < b_ for a_, b_, kind, _ in log if kind == "rest") for g in range(Lc)]
    still = [(not hid[g]) and (not in_rest[g]) and math.dist(P.p[g], P.p[g + 1]) < 0.02 and abs(P.sq[g + 1] - P.sq[g]) < 1e-6
             and abs(P.gl[g + 1] - P.gl[g]) < 1e-6 for g in range(Lc)]
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

    # ---------------------------------------------------------------- the pieces' keys
    pieces, vertex_ids, moving_tracks = [], [], 0
    # through the arrival the ball waits inside F1 (it is not drawn until F1 has landed) and F1's cover is not on until then
    own_opacity = {"F1 front": lambda fr: 1.0 if fr < LANDED else 0.0, "F1 cover": lambda fr: 0.0 if fr < LANDED else 1.0}
    for nm, fc in drawn:
        ps = [poses[g][key_of[fc.cube]] for g in range(Lc + 1)]
        for (oid, prop), vals in fc.tracks(ps, ident).items():
            if max(vals) - min(vals) < 1e-6:
                continue
            assert abs(vals[0] - vals[Lc]) < 1e-6, (nm, oid, prop)
            pieces.append((oid, prop, (lambda g, a=vals: a[g]), own_opacity.get(nm) if prop == "opacity" else None))
            if prop != "opacity":
                vertex_ids.append(oid)
                moving_tracks += 1
    pieces.append((art.id, "opacity", lambda g: 1.0, lambda fr: 0.0 if fr < LANDED else 1.0))

    # ---------------------------------------------------------------- the ball's keys
    cyc = Cycle(Lc)
    for g in range(Lc + 1):
        cyc.put(g, screen(P.p[g]), "air" if P.mode[g] == "air" else "hidden")
        s_ = P.sq[g]
        if s_:
            cyc.sy[g], cyc.sx[g] = 1 + s_, 1 / (1 + s_)
    th = [0.0]
    for g in range(Lc):
        th.append(th[-1] + P.w[g])
    th = [th[g] + P.gl[g] for g in range(Lc + 1)]
    total = th[Lc] - th[0]
    want = round(total / (2 * math.pi)) * 2 * math.pi
    a0, a1 = f_turn1 + TURN_N, f_turn1 + TURN_TOTAL + 10       # while M turns the ball is out of sight, so it takes up the odd bit of a turn here
    assert all(g in hset for g in range(a0, a1 + 1)), "the correcting turn would show"
    for g in range(a0, Lc + 1):
        th[g] += (want - total) * smooth((min(g, a1) - a0) / (a1 - a0))
    px = plane_x(scene, sheet, ROOM, "Front")
    s0 = screen(IN_F1)

    def pre(fr):
        return (s0[0] + px(fr), s0[1]), 1.0, 1.0
    emit(doc, art, spin, cyc, th, T0, pre, pieces)

    # thin the vertex keys, but keep the edge of every rest exact so a shut lid lies exactly on its box
    phase0 = 192 - 1 - T0
    edges = set()
    for k in CELLS:
        keys_ = [pk(geom(poses[g][k])) for g in range(Lc + 1)]
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

    # the jump from F1 to F2 holds: no frame in between ever draws the ball half way
    a, b = doc.anim(f"{ROOM} Loop")
    held = 0
    i = a
    while i < b:
        if f'<KeyedObject objectId="{art.id}"' in doc.lines[i]:
            e = doc.end(i)
            j = i + 1
            while j < e:
                pm = re.search(r'<KeyedProperty property="([^"]+)"', doc.lines[j])
                if pm and pm.group(1) in ("x", "y"):
                    pe = doc.end(j)
                    for q in range(j + 1, pe):
                        if "<KeyFrameDouble" in doc.lines[q] and re.search(rf' frame="{j1 - 1}"', doc.lines[q]):
                            doc.lines[q] = doc.lines[q].replace(' interpolationType="linear"', "")
                            held += 1
                    j = pe + 1
                else:
                    j += 1
            break
        i += 1
    moves = sum(abs(screen(P.p[j1])[i] - screen(P.p[j1 - 1])[i]) > 1e-6 for i in (0, 1))      # x and y of the screen position that change
    assert held == moves, ("the jump's keys", held, moves)

    # a shut lid is exactly its cube's still top
    flush, flush_at = 0.0, None
    lid_faces = [fc for _, fc in drawn if getattr(fc, "part", None) == "lid" and not fc.flip]
    ids_ = [vid for fc in lid_faces for vid in fc.shapes[0][1]]
    rows_l = c3.key_values(doc, f"{ROOM} Loop", ids_)
    for fc in lid_faces:
        ps = [poses[g][key_of[fc.cube]] for g in range(Lc + 1)]
        for g in range(1, Lc):
            if not (pk(geom(ps[g])) == pk(geom(ps[g - 1])) == pk(geom(ps[g + 1])) and ps[g]["lid"] == 0):
                continue
            ref = fc.cube.quad(fc.face, None, {"dip": ps[g].get("dip", 0)})
            for vid, (rx_, ry_) in zip(fc.shapes[0][1], ref):
                for prop, ref_v in (("x", rx_), ("y", ry_)):
                    r_ = rows_l.get((vid, prop))
                    if r_ is not None:
                        d_ = abs(c3.value_at(r_, (g - phase0) % Lc) - ref_v)
                        if d_ > flush:
                            flush, flush_at = d_, (fc.name, g, prop)
    assert flush < 0.05, ("a shut lid is not flush with its cube", flush, flush_at)

    # ---------------------------------------------------------------- the report
    sec = lambda g: f"{3.2 + g / 60:.2f}"
    table = "\n".join(f"  {sec(a_):>6}-{sec(b_):<6} {k:4s} {t_}" for a_, b_, k, t_ in log)
    flights = "; ".join(f"{lab} {sec(a_)}-{sec(b_)} s ({b_ - a_ + 1} fr) apex y {apex_:.0f}" for lab, a_, b_, apex_, vv in P.notes)
    dev = max(math.dist((CUBE[k].centre[0] - CUBE[k].hx, CUBE[k].centre[1] - CUBE[k].hy), FIGMA[k]) for k in CELLS)
    return (f"{ROOM}: loop {Lc / 60:.2f} s ({Lc} frames), the loop starts at 3.20 s with the ball inside F1\n{table}\n"
            f"  six cubes on one lattice (every front square within {dev:.2f} px of the Figma), {moving_tracks} vertex tracks keyed "
            f"({thinned} keys thinned, {ball_thinned} on the ball); shut lids flush within {flush:.3f} px\n"
            f"  flights: {flights}\n"
            f"  ball top {ball_top:.0f}, highest lid {lid_top:.0f}; closest to any cube face, edge or lid: {tight[0]:.2f} px (frame {tight[1]}, {sec(tight[1])} s, {tight[2]})\n"
            f"  longest out of sight {longest_hidden} frames ({longest_hidden / 60:.2f} s, ending {sec(run_at)} s); longest still in view outside "
            f"the rests {longest_still} frames ({longest_still / 60:.2f} s, from {sec(still_at) if still_at is not None else '-'} s)")
