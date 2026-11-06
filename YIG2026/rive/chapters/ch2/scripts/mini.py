"""The Mini, "the walkway" (Demetre's brief, 2026-11-06, with the Figma finale frames 13294:110105): the ball is a curious, cheeky
character and six cubes on one grid are its props. The timeline (the Finesse panel's clock) is printed by build().

The grid (Figma frame the-mini-cubes, nodes 13226:109086 and 13234:109515): six cubes drawn from one viewpoint (depth goes up and to the
left), every cube touching the next along a shared face or edge. In cells (column, row from the front, level):
    front-left cube   F1 (0, 0, 0)  lid on its back edge; turns; the ball starts the loop inside it and ends it inside it
    front-right cube  F2 (1, 0, 0)  black front, closed lid: the ball bounces on it
    far-left cube     L0 (-1, 1, 0) black left face; lid on its back edge; turns twice at the end
    middle cube       M  (2, 1, 0)  white front, black left face: still
    right cube        R  (3, 1, 0)  black lid; turns twice (white front to black and back)
    top cube          T  (2, 1, 1)  its left face is a flap hinged on its bottom edge; the ball waits inside it
Cubes are 84 square (the Figma's 83.6 plus the 0.4 gaps its strokes hide); the lattice sits within 0.8 px of every Figma position.
Cubes never move, shake or shift: only lids and the flap move, and F1, R and L0 turn in place (a quarter turn at a time, left to right).

The loop (the clock starts at 3.2 s; build() prints the real times):
    1 out          F1's lid opens (eased, past open, settle); the ball jumps out, bounces once on F2's closed lid and goes up onto T's top;
                   F1's lid closes behind it
    2 idle         it rolls and glances on T's top, Wordle style; F1 turns a quarter (its black left face becomes the front), a split second,
                   a second quarter (the white face is back in front, a black one on the left: the cube is as it began)
    3 across       as the second turn lands the ball bounces from T onto L0's top
    4 in           F1's lid opens, the ball jumps into F1 and the lid shuts at once
    5 R turns      a quarter turn while the ball is hidden: R's white front becomes black; the ball is in R; R's lid cracks open and the ball
                   peeks out (it looks about); the lid shuts; the ball has moved on to T, unseen; R turns a second quarter (white again)
    6 the walkway  T's left face falls open on its bottom edge and lies flat behind F2, revealing the ball; at the same moment F1's lid
                   swings right over and lies flat behind F1: a flat road at the height of the cube tops. The ball rolls out of T, along
                   both lids and stops by L0; L0's lid lifts (hinged at the back), the ball drops in and the lid shuts
    7 reset        as that lid shuts L0 turns two quarters, and the two walkway lids close back onto their cubes; the ball moves unseen
                   to F1 and the loop starts again

Layers: every cube face is under the ball (the Floor Plane) except "cover" copies of the front face of whichever cube the ball is inside
(F1, L0, R and T, whose cover also takes the flap), which switch on only while the ball is out of sight behind that face (the under copy
switches off at the same frame, so no edge is drawn twice). The under copy of a face sits at the top of its cube's stack, so it is stacked
against its neighbours the way its cover is and the swap changes no pixel. The ball is modelled in 3D (the grid's own space); the checks
run on every frame: the ball clears every cube face, edge and lid (sphere against rectangles), every face drawn over or under the ball is
on the right side of it in depth, and when the ball is meant to be out of sight every pixel of it is under a cover.
"""
import math
import os
import re
import xml.etree.ElementTree as ET

import cube3d as c3
from cube3d import Cube, Face, TurnSide, TurnTop, LIGHT, DARK

DARK_IN = "FF131313"                        # the inside of an open cube: a touch darker than the sides, so it has depth (note 4)
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
CROP_TOL = 1.2                              # px the ball's outline may pass the crop's left edge in the drop into L0 (its wall allows no more)
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
OPEN_TOP = math.radians(100)                              # a lid standing open (note 10: a little further back than 92)
OPEN_PLAN = math.radians(107)                             # ... and the most it swings past that: the angle the flights are planned against
FULL = dict(amp=OPEN_TOP, back=1.3, lift_n=30, settle_n=0, fall_n=14, bump_n=7, bump=math.radians(1.5))     # a lid standing open
CRACK = dict(amp=math.radians(38), back=1.3, lift_n=24, settle_n=0, fall_n=10, bump_n=6, bump=math.radians(1.2))   # R's peek
FOLD = dict(amp=math.pi, back=0.0, lift_n=40, settle_n=0, up_n=12, apex=math.radians(100), fall_n=16, bump_n=7,
            bump=math.radians(1.5))                         # F1's lid right over onto the empty cell behind it
FLAP = dict(amp=math.pi / 2, fall_n=26, bump_n=10, bump=math.radians(2.2), n=20, shut_bump_n=7, shut_bump=math.radians(1.5))
TURN_N, SETTLE_N, OVER = 42, 0, 0.0                        # a quarter turn: 0.7 s, eased in and out, onto the face and no further (note 3)
TURN_TOTAL = TURN_N + SETTLE_N
QUARTER = math.pi / 2
GL_UP = math.radians(-12)                  # a glance up and to the left (the dot turns anticlockwise)
FLIP = 0.0                                 # no turn of the dot in a hop: the dot comes back up at every rest
LAYER_TOL = 3.0                            # px of depth the layering check forgives (the ball and a face meeting at a rim)


def ease_io(u):
    u = min(1.0, max(0.0, u))
    return 4 * u ** 3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2


def lift_ease(u):
    s = smooth(u)
    return 1 - (1 - s) ** 2


def back_out(u, c1):
    """Ease-out that swings a little past 1 and settles onto it (c1 sets how far: 1.3 is 6 percent)."""
    u = min(1.0, max(0.0, u)) - 1.0
    return 1.0 + (c1 + 1.0) * u ** 3 + c1 * u ** 2


def bump_at(t, n, amp):
    return amp * math.sin(math.pi * t / n)


def joint_state(events, g):
    """events: [(frame, kind, params)] -> the angle of a lid or the flap on frame g.
    open: an eased lift to a little past open and a settle; shut: a lid dropping shut (kicked up first when it starts flat behind) with
    one soft bump; fall: the flap falling open under gravity, one bump; swing: the flap lifting shut, one soft bump."""
    a = 0.0
    for f0, kind, ev in sorted(events, key=lambda e: e[0]):
        if g < f0:
            break
        t = g - f0
        if kind == "open":
            ln = ev["lift_n"]
            if t < ln:
                u = t / ln
                a = ev["amp"] * back_out(0.5 * u + 0.5 * smooth(u), ev["back"])      # kicked off, swung a little past open, settled
            else:
                a = ev["amp"]
        elif kind == "shut":
            up = ev.get("up_n", 0)
            a0 = ev["apex"] if up else ev["amp"]
            if t < up:
                a = ev["amp"] - (ev["amp"] - a0) * (1 - (1 - t / up) ** 2)
            else:
                t2 = t - up
                if t2 < ev["fall_n"]:
                    a = a0 * (1 - (t2 / ev["fall_n"]) ** 2)
                elif t2 < ev["fall_n"] + ev["bump_n"]:
                    a = bump_at(t2 - ev["fall_n"], ev["bump_n"], ev["bump"])
                else:
                    a = 0.0
        elif kind == "fall":
            if t < ev["fall_n"]:
                a = ev["amp"] * (t / ev["fall_n"]) ** 2
            elif t < ev["fall_n"] + ev["bump_n"]:
                a = ev["amp"] - bump_at(t - ev["fall_n"], ev["bump_n"], ev["bump"])
            else:
                a = ev["amp"]
        elif kind == "swing":
            if t < ev["n"]:
                a = ev["amp"] * (1 - lift_ease(t / ev["n"]))
            elif t < ev["n"] + ev["shut_bump_n"]:
                a = bump_at(t - ev["n"], ev["shut_bump_n"], ev["shut_bump"])
            else:
                a = 0.0
        else:
            raise ValueError(kind)
    return a


def open_n(ev):
    return ev["lift_n"] + ev["settle_n"]


def shut_n(ev):
    return ev.get("up_n", 0) + ev["fall_n"] + ev["bump_n"]


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


def turning(pose):
    t = pose.get("turn", 0.0)
    return abs(t - round(t / QUARTER) * QUARTER) > 1e-6


def at_rest(pose):
    return not turning(pose)


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
LIDDED = ("F1", "L0", "R")


def lid_pose(pose):
    """A lid is only ever open with its cube at rest (a square top is the same square after a quarter turn), and then it is hinged on the
    back edge of the grid, whatever the cube has turned to."""
    return {**pose, "turn": 0.0} if pose.get("lid") else pose


def shell(k, pose):
    """The cube as thin rectangles in the grid's space: its five walls and its top (the lid, for the lidded cubes; the flap is T's left)."""
    cube = CUBE[k]
    out = []
    for f in SHELL_FACES:
        if k == "T" and f == "left":
            out.append((f"{k}.flap", [to_world(k, p) for p in cube.quad3("left", "flap", pose)]))
        else:
            out.append((f"{k}.{f}", [to_world(k, p) for p in cube.quad3(f, None, pose)]))
    if k in LIDDED:
        out.append((f"{k}.lid", [to_world(k, p) for p in cube.quad3("top", "lid", lid_pose(pose))]))
    else:
        out.append((f"{k}.top", [to_world(k, p) for p in cube.quad3("top", None, pose)]))
    return out


STATIC_SHELLS = {k: shell(k, {}) for k in ("F2", "M")}


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


def poly_dist(pt, poly):
    """Distance from a point to a convex polygon on the screen (0 inside)."""
    if inside(pt, poly):
        return 0.0
    best = 1e9
    for i in range(len(poly)):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % len(poly)]
        dx, dy = x1 - x0, y1 - y0
        t = 0.0 if dx == dy == 0 else min(1.0, max(0.0, ((pt[0] - x0) * dx + (pt[1] - y0) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(pt[0] - x0 - t * dx, pt[1] - y0 - t * dy))
    return best


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

    def roll_snap(self, dx, n, gl=None):
        """Wordle's roll: it leaves quickly, eases out a touch past the mark, rocks back and settles (the dot follows the distance)."""
        p0, g0 = self.at, self.gl[-1]
        ov = math.copysign(max(2.0, 0.12 * abs(dx)), dx)
        xs = [p0[0] + (dx + ov) * (1 - (1 - t / n) ** 3) for t in range(1, n + 1)]
        xs += [p0[0] + dx + ov - 1.6 * ov * smooth(t / 12) for t in range(1, 13)]
        xs += [p0[0] + dx - 0.6 * ov + 0.6 * ov * smooth(t / 10) for t in range(1, 11)]
        prev = p0[0]
        for i, x in enumerate(xs):
            s_ = smooth(min(1.0, (i + 1) / n))
            self.put((x, p0[1], p0[2]), "roll", w=(x - prev) / R_BALL, gl=g0 + ((gl if gl is not None else g0) - g0) * s_)
            prev = x

    def truncate(self, n):
        """Drop every frame from n on (a beat that would not fit)."""
        for lst in (self.p, self.mode, self.w, self.gl, self.sq):
            del lst[n:]
        self.notes = [x for x in self.notes if x[1] < n]

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

    def hop(self, p1, T, gather=0.0, stretch=0.0, flip=0.0, glances=(), zp=None, xp=None, xz=False, label="hop"):
        """From rest to a landing at p1: T frames, a parabola at 0.40 in height; X and depth in a straight line, or eased between two
        moments of the flight (xp, zp = (from, to), fractions of the flight; still before and after). It leaves from a gather and stretches
        while it is fast; `flip` adds that many turns of the dot over the second half of the flight; `glances` is [(frame, angle)] eased
        between. Returns (vx, vy, vz, vy at landing)."""
        p0 = self.at
        vy = (p1[1] - p0[1]) / T - 0.5 * G * T
        vx, vz = (p1[0] - p0[0]) / T, (p1[2] - p0[2]) / T
        f_go = self.now
        w = 0.0                                   # leaving a rest, it leaves with no spin and keeps none in the air; its dot only glances
        g0 = self.gl[-1]
        keys = [(0, g0)] + [(int(f), a) for f, a in glances]
        raw = [smooth(min(1.0, max(0.0, (t - 0.45 * T) / (0.5 * T)))) for t in range(0, T + 1)]
        dflip = [raw[t] - raw[t - 1] for t in range(1, T + 1)]
        tot = sum(dflip) or 1.0
        pts = hop_points(p0, p1, T, zp, xp, xz)
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
            if 12 <= t < 20:
                sq = 0.25 * amp * math.sin(math.pi * (t - 12) / 8) ** 2          # one tiny spring past rest, then still
            self.put((x, p[1], p[2]), "roll", w=(x - prev) / R_BALL, sq=sq)
            prev = x
        return self.at


def hop_points(p0, p1, T, zp=None, xp=None, xz=False):
    """The flight: height in a parabola; depth and sideways in a straight line, or each eased between two moments of the flight."""
    vy = (p1[1] - p0[1]) / T - 0.5 * G * T
    out = []
    for t in range(0, T + 1):
        uz = t / T if zp is None else smooth((t / T - zp[0]) / (zp[1] - zp[0]))
        if xp is None:
            ux = uz if xz else t / T
        elif xp[1] >= 1.0:                                      # sideways speed builds up to the landing, never dies away in the air
            ux = max(0.0, (t / T - xp[0]) / (1.0 - xp[0])) ** 2
        else:
            ux = smooth((t / T - xp[0]) / (xp[1] - xp[0]))
        out.append((p0[0] + (p1[0] - p0[0]) * ux, p0[1] + vy * t + 0.5 * G * t * t, p0[2] + (p1[2] - p0[2]) * uz))
    return out


def behind_ok(pts, k, face):
    """The ball never overlaps (on the screen) a face of cube k that is drawn under it while the ball is behind that face."""
    cube = CUBE[k]
    poly = cube.quad(face, None, {})
    cs = [to_world(k, p) for p in cube.quad3(face, None, {})]
    for q in pts:
        sc = screen(q)
        if poly_dist(sc, poly) >= R_BALL + 0.5:
            continue
        for u in disc(sc, R_BALL, rings=(0.4, 0.7, 0.95, 0.999), n=32):
            if not inside(u, poly):
                continue
            zb = sphere_depth(q, u[0], u[1], R_BALL)
            zf = plane_depth(cs, u[0], u[1])
            if zb is not None and zf is not None and zf < zb - LAYER_TOL:
                return False
    return True


def top_ok(pts):
    """The ball and the copy: its top stays a little below the copy's lowest line."""
    return all(screen(q)[1] - R_BALL >= COPY_Y + 6 for q in pts)


def plan_hop(p0, p1, Ts, shells, zps=(None,), xps=(None,), margin=1.5, extra=None):
    """The shortest flight (time, depth profile, sideways profile) that keeps the ball `margin` clear of every rectangle on its way (the
    last two frames are the landing and may touch) and passes `extra(points)`; if none does, the one that clears best.
    Returns (T, zp, xp, how clear, whether it is clear)."""
    best = None
    for T in Ts:
        for zp in zps:
            for xp in xps:
                pts = hop_points(p0, p1, T, zp, xp)
                worst = min(gap(q, shells)[0] for q in pts[1:T - 1])
                end = min(gap(q, shells)[0] for q in pts[T - 1:])
                ok = extra(pts) if extra else True
                if worst >= margin and end >= -0.5 and ok:
                    return T, zp, xp, worst, True
                score = min(worst, end + margin) - (0 if ok else 100)
                if best is None or score > best[3]:
                    best = (T, zp, xp, score, False)
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


class LidFace(Face):
    """A face of a lid: it is only drawn with its cube at rest, and then it sits on the grid's back edge whatever the cube has turned to."""

    def pose_for(self, pose):
        pose = self.fixed if self.fixed is not None else pose
        return {**pose, "turn": 0.0}

    def parts(self, pose):
        return super().parts(self.pose_for(pose))

    def outline(self, pose):
        return super().outline(self.pose_for(pose))


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
    TOPY = Y0                                      # the cube tops' height (the road)
    YB = FLOOR - RC                                # the ball's centre on the floor / on the bottom of a box
    YT = TOPY - RC                                 # on a cube top
    YTT = TOPY - S_ - RC                           # on the top cube's top
    IN_F1 = (722.0, YB, 40.0)
    LAND_F1 = (726.0, YB, 40.0)                    # where the hop in lands (clear of F1's left face on the screen); it settles back to IN_F1                      # inside F1, wholly behind its front square
    ON_F2 = (797.0, YT, 42.0)                      # on F2's top
    ON_T = (872.0, YTT, 126.0)                     # on T's top (it rolls on from the landing)
    ON_L0 = (655.0, YT, 96.0)                     # where the hop to L0 lands; it rolls on to about x 644, clear of F1's open lid
    IN_R = (975.0, YB, 125.0)                      # inside R, against its right wall, hidden behind its front square
    IN_T = (880.0, TOPY - RC, 126.0)               # inside T, wholly behind its front face and its flap
    END_WALK = (717.0, YT, 125.0)                  # the road's end, beside L0 and clear of its lifting lid
    IN_L0 = (637.0, YB, 118.0)                     # inside L0, wholly behind its front square
    RIM = Y0                                       # the front row's front squares' top edge on the screen

    P = Path()
    lid_f1, lid_l0, lid_r, flap_t = [], [], [], []
    turn_f1, turn_r, turn_l0 = [], [], []
    rel = {}
    log = []
    marks = {}

    def seg(kind, label, n0):
        log.append((n0, P.now, kind, label))

    P.put(IN_F1, "rest", gl=0.0, sq=0.0)               # frame 0: inside F1, the lid shut

    def poses_for_plan(**kw):
        d = {"F1": {}, "L0": {}, "R": {}, "T": {}}
        d.update(kw)
        return all_shells(d)

    def run_hop(p1, Ts, shells, zps=(None,), xps=(None,), apex_limit=True, under=(), **kw):
        extra = lambda pts: (top_ok(pts) if apex_limit else True) and all(behind_ok(pts, k_, f_) for k_, f_ in under)
        T, zp, xp, worst, ok = plan_hop(P.at, p1, Ts, shells, zps, xps, extra=extra)
        assert ok, (tuple(round(v) for v in P.at), tuple(round(v) for v in p1), "no clear flight", T, zp, xp, round(worst, 1))
        return T, zp, xp

    # ------------------------------------------------------------ 1 out: F1's lid opens, the ball bounces on F2's lid and up onto T
    n0 = P.now
    lid_f1.append((P.now, "open", FULL))
    P.hold(10)
    P.squash_to(-0.05, 6)                                      # gathers inside as the lid swings up
    seg("move", "F1's lid opens (eased lift, past open, settle); the ball gathers inside", n0)
    n0 = P.now
    sh_open = poses_for_plan(F1={"lid": OPEN_PLAN})
    T1, zp1, xp1 = run_hop(ON_F2, range(30, 56), sh_open, (None,), [(a, 1.0) for a in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5)])
    f_h1 = P.now
    P.hop(ON_F2, T1, gather=0.05, stretch=0.03, zp=zp1, xp=xp1,
          glances=[(0.25 * T1, math.radians(-10)), (0.65 * T1, math.radians(8))], label="out of F1 onto F2's lid")
    marks["h1"] = (f_h1, P.now - 1)
    P.squash_to(-0.07, 4)                                      # the bounce on F2's closed lid: a deep squash and away again
    seg("move", f"the ball jumps out of F1 and bounces on F2's closed lid ({T1} frames in the air)", n0)
    n0 = P.now
    T2, zp2, xp2 = run_hop(ON_T, range(30, 56), sh_open, [None] + [(a, b) for a in (0.0, 0.2, 0.35, 0.5) for b in (0.6, 0.8, 0.95)],
                           [None, (0.0, 1.0), (0.2, 1.0), (0.4, 1.0)])
    f_h2 = P.now
    vx2, *_ = P.hop(ON_T, T2, gather=0.07, stretch=0.03, zp=zp2, xp=xp2,
                    glances=[(0.2 * T2, math.radians(-14)), (0.6 * T2, math.radians(12))], label="up onto T's top")
    marks["h2"] = (f_h2, P.now - 1)
    lid_f1.append((f_h2 + 8, "shut", FULL))                    # F1's lid closes behind it
    P.land(0.6 * vx2, 22, 0.07)
    seg("move", f"it springs on up onto T's top ({T2} frames in the air); F1's lid falls shut behind it, one bump", n0)

    # ------------------------------------------------------------ 2 idle on T's top while F1 turns a quarter, a beat, a quarter
    f_idle0 = P.now
    f_t1 = f_idle0 + 80
    f_t2 = f_t1 + TURN_TOTAL + 14
    f_h3 = f_t2 + 30                                           # the hop to L0 leaves as the second turn lands
    turn_f1 += [(f_t1, -QUARTER), (f_t2, -2 * QUARTER)]
    rel["F1"] = f_t2 + TURN_TOTAL + 8
    assert f_t1 > lid_f1[-1][0] + shut_n(FULL), "F1 turns with its lid still moving"
    x_lo, x_hi = 858.0, 902.0
    ty = YTT

    def beat_pair(dx, n1, n2, gl=None, mid=4):
        """A roll out and the same roll back (the dot is up again), with a beat between."""
        d = dx if x_lo <= P.at[0] + dx <= x_hi else ((x_hi if dx > 0 else x_lo) - P.at[0])
        P.roll_snap(d, n1, gl=gl)
        P.hold(mid, sway=math.radians(1.2), period=12)
        P.roll_snap(-d, n2, gl=0.0)

    def beat_hop(n):
        P.squash_to(-0.04, 4)
        P.hop((P.at[0], ty, P.at[2]), n, gather=0.04, stretch=0.02, label="little hop on T")
        P.squash_to(0.0, 3)

    beats = [lambda: (P.glance_to(math.radians(-10), 7), P.hold(4, sway=math.radians(1.0), period=14)),
             lambda: beat_pair(-24, 13, 14, gl=math.radians(-5)),
             lambda: beat_hop(16),
             lambda: beat_pair(+32, 15, 15, gl=math.radians(8), mid=6),
             lambda: (P.glance_to(math.radians(-6), 7), P.hold(3, sway=math.radians(1.0), period=12)),
             lambda: beat_hop(18),
             lambda: beat_pair(-18, 12, 12)]
    k = 0
    while P.now < f_h3 - 12:
        n_before = P.now
        beats[k % len(beats)]()
        k += 1
        if P.now > f_h3 - 8:                                   # that beat does not fit: leave it out and settle
            P.truncate(n_before)
            break
    P.glance_to(0.0, 6)
    assert P.now <= f_h3, ("the idle runs over", P.now, f_h3)
    P.hold(f_h3 - P.now, sway=math.radians(1.0), period=16)
    seg("move", "it idles on T's top, rolling and glancing; F1 turns a quarter, a beat, a quarter", f_idle0)

    # ------------------------------------------------------------ 3 across to L0
    n0 = P.now
    P.squash_to(-0.05, 4)
    T3, zp3, xp3 = run_hop(ON_L0, range(36, 70, 2), poses_for_plan(), [None, (0.0, 0.5), (0.3, 0.8)], [None, (0.0, 1.0), (0.1, 1.0)])
    f_h3b = P.now
    vx3, *_ = P.hop(ON_L0, T3, gather=0.05, stretch=0.03, zp=zp3, xp=xp3, label="across to L0")
    marks["h3"] = (f_h3b, P.now - 1)
    P.land(0.3 * vx3, 22, 0.07)
    seg("move", f"as the second turn lands it bounces across to L0's top ({T3} frames in the air)", n0)

    # ------------------------------------------------------------ 4 in: F1's lid opens, the ball jumps in, the lid shuts at once
    n0 = P.now
    P.glance_to(GL_UP * 1.6, 10)
    f_open4 = P.now
    lid_f1.append((P.now, "open", FULL))
    P.glance_to(math.radians(6), 12)
    P.squash_to(-0.05, 8)
    P.hold(max(0, open_n(FULL) - 30 + 2))
    seg("move", "L0's top: the ball looks at F1, whose lid opens, and gathers", n0)
    n0 = P.now
    sh4 = poses_for_plan(F1={"lid": OPEN_PLAN})
    T4, zp4, xp4 = run_hop(LAND_F1, range(36, 76, 2), sh4, [None],
                           [(a, 1.0) for a in (0.0, 0.2, 0.35, 0.5, 0.6)], under=(("F1", "left"),))
    f_h4 = P.now
    P.hop(LAND_F1, T4, gather=0.05, stretch=0.03, flip=FLIP, zp=zp4, xp=xp4,
          glances=[(0.40 * T4, math.radians(6)), (0.50 * T4, math.radians(24)), (0.62 * T4, math.radians(6))], label="into F1")
    marks["h4"] = (f_h4, P.now - 1)
    for t in range(1, 7):
        P.put(P.at, "rest", sq=P.sq[-1] * (1 - t / 6))
    P.roll_to(IN_F1[0], 10, gl=0.0)
    f_shut4 = P.now
    lid_f1.append((P.now, "shut", FULL))
    seg("move", f"it hops over the rim into F1 ({T4} frames) and the lid falls shut at once, one bump", n0)

    # ------------------------------------------------------------ 5 R turns; the ball moves on to R and peeks out of its lid
    n0 = P.now
    f_r1 = f_shut4 + shut_n(FULL) + 18                         # the lid has shut, and 0.3 s more
    turn_r.append((f_r1, -QUARTER))
    P.hold(f_r1 - P.now + TURN_TOTAL + 4)
    seg("rest", "hidden in F1; R turns a quarter: its white front becomes black", n0)
    n0 = P.now
    P.jump_to(IN_R)                                            # out of sight in F1, and on the next frame out of sight in R
    f_jr = P.now - 1
    P.hold(3)
    lid_r.append((P.now, "open", CRACK))
    P.hold(10)
    seg("move", "R's black lid cracks open (the ball has moved in unseen)", n0)
    n0 = P.now
    P.squash_to(-0.04, 5)
    P.hop(IN_R, 24, gather=0.04, stretch=0.02, glances=[(8, math.radians(-16)), (15, math.radians(14))], label="peek out of R")
    marks["peek"] = (n0, P.now - 1)
    P.squash_to(0.0, 4)
    P.glance_to(math.radians(-14), 10)
    P.glance_to(math.radians(10), 12)
    P.glance_to(0.0, 8)
    seg("move", "the ball rises into the crack, looks about with its dot, and ducks", n0)
    n0 = P.now
    P.hold(2)
    lid_r.append((P.now, "shut", CRACK))
    P.hold(shut_n(CRACK) + 3)
    f_jt = P.now
    P.jump_to(IN_T)                                            # out of sight in R, and on the next frame out of sight in T
    P.hold(4)
    f_r2 = P.now
    turn_r.append((f_r2, -2 * QUARTER))
    rel["R"] = f_r2 + TURN_TOTAL + 8
    P.hold(TURN_TOTAL + 8)
    seg("rest", "R's lid shuts; the ball moves on to T unseen; R turns a second quarter: white again", n0)

    # ------------------------------------------------------------ 6 the walkway
    n0 = P.now
    f_flap = P.now
    flap_t.append((f_flap, "fall", FLAP))
    lid_f1.append((f_flap, "open", FOLD))
    P.hold(10)
    seg("move", "T's left face falls open and lies flat; F1's lid swings over behind it: a flat road; the ball is revealed inside T", n0)
    n0 = P.now
    P.glance_to(math.radians(-14), 8)
    P.hold(3, sway=math.radians(1.0), period=12)
    P.roll_snap(-26, 14, gl=math.radians(-8))                  # leans out of the opening
    P.hold(5, sway=math.radians(1.2), period=14)
    P.glance_to(math.radians(-16), 8)                           # a look along the road
    P.squash_to(-0.03, 5)
    P.roll_to(786.0, 38, gl=math.radians(-6), sq=0.0)          # off along the flap and over the join
    P.roll_to(END_WALK[0], 40, gl=0.0)                         # on along F1's lid to the end of the road
    P.roll_to(END_WALK[0] + 1.5, 8, gl=0.0)
    seg("move", "the ball rolls out of T, along T's flap and F1's lid, to the end of the road", n0)
    n0 = P.now
    f_lift = P.now
    lid_l0.append((P.now, "open", FULL))
    P.glance_to(GL_UP * 1.4, 10)
    P.glance_to(math.radians(4), 12)
    P.hold(max(0, open_n(FULL) - 22 + 2))                     # the lid is swinging up
    P.roll_to(704.0, 14, gl=0.0)                               # it steps up to the edge
    P.squash_to(-0.05, 8)
    seg("move", "L0's lid lifts (hinged at the back); the ball looks and gathers", n0)
    n0 = P.now
    sh5 = poses_for_plan(L0={"lid": OPEN_PLAN}, F1={"lid": math.pi}, T={"flap": math.pi / 2})
    IN_L0 = (636.0, YB, 120.0)                                 # as far right as a ballistic drop over L0's wall allows
    T5, zp5, xp5 = run_hop(IN_L0, range(40, 100, 2), sh5, [None], [None], apex_limit=True)
    f_h5 = P.now
    P.hop(IN_L0, T5, gather=0.05, stretch=0.03, zp=zp5, xp=xp5, label="into L0")
    marks["h5"] = (f_h5, P.now - 1)
    for t in range(1, 7):
        P.put(P.at, "rest", sq=P.sq[-1] * (1 - t / 6))
    P.glance_to(0.0, 3)
    f_ls = P.now
    lid_l0.append((P.now, "shut", FULL))
    seg("move", f"it drops off the road into L0 ({T5} frames) and the lid shuts", n0)

    # ------------------------------------------------------------ 7 reset: L0 turns twice, the road folds up, the ball goes home unseen
    n0 = P.now
    f_l1 = f_ls + shut_n(FULL) - 1
    turn_l0 += [(f_l1, -QUARTER)]
    f_l2 = f_l1 + TURN_TOTAL + 6
    turn_l0.append((f_l2, -2 * QUARTER))
    rel["L0"] = f_l2 + TURN_TOTAL + 6
    lid_f1.append((f_l1 - 2, "shut", FOLD))
    flap_t.append((f_l1 + 6, "swing", FLAP))
    P.hold(FULL["fall_n"] + FULL["bump_n"] + 2 - 1)
    f_jf = P.now
    P.jump_to(IN_F1)                                           # out of sight in L0 (its lid is shut), and on the next frame out of sight in F1
    f_end = max(rel["L0"] + 2, f_l1 - 2 + shut_n(FOLD) + 2, f_l1 + 6 + FLAP["n"] + FLAP["shut_bump_n"] + 2)
    P.hold(f_end - P.now)
    Lc = P.now
    P.put(IN_F1, "rest", gl=0.0, sq=0.0)                       # frame Lc is frame 0 again
    seg("rest", "L0 turns two quarters, the walkway closes back onto its cubes, and the ball is home in F1", n0)
    assert abs(P.sq[Lc]) < 1e-12 and abs(P.gl[Lc - 1]) < 1e-12 and abs(P.sq[Lc - 1]) < 1e-12 and math.dist(P.p[Lc - 1], IN_F1) < 1e-9, \
        ("the loop does not end where it began", P.sq[Lc - 1], P.gl[Lc - 1], P.p[Lc - 1])

    # ---------------------------------------------------------------- the cubes' poses, frame by frame (geometry first)
    def tp(events, key, g):
        v = turn_state(events, g)
        return v + (math.pi if (key in rel and g >= rel[key]) else 0.0)

    def opening(events, g):
        """The dark opening shows while the lid is up, and one frame either side (under a flush lid it cannot be seen): no gaps."""
        return 1 if any(joint_state(events, g + d) > 1e-9 for d in (-1, 0, 1)) else 0

    geo = []
    for g in range(Lc + 1):
        geo.append({"F1": {"lid": joint_state(lid_f1, g), "turn": tp(turn_f1, "F1", g)},
                    "F2": {}, "M": {},
                    "L0": {"lid": joint_state(lid_l0, g), "turn": tp(turn_l0, "L0", g)},
                    "R": {"lid": joint_state(lid_r, g), "turn": tp(turn_r, "R", g)},
                    "T": {"flap": joint_state(flap_t, g)}})

    # ---------------------------------------------------------------- the faces
    def face(k, f_, part=None, flip=False, fill=LIGHT, name=None, lid=False, **kw):
        cls = LidFace if lid else Face
        return cls(CUBE[k], f_, part, flip=flip, fill=fill, name=name or f"{NAMES[k]} {f_.title()}", **kw)

    def lid_name(k, extra):
        return f"{NAMES[k]} {extra}"

    cvr = lambda p: p.get("cover", 0) > 0
    unc = lambda p: p.get("cover", 0) == 0
    opn = lambda p: p.get("ov", 0) > 0
    f = {}
    for k, light_lid in (("F1", True), ("L0", True), ("R", False)):
        lf = LIGHT if light_lid else DARK
        sides = {"F1": (LIGHT, DARK), "L0": (LIGHT, DARK), "R": (LIGHT, DARK)}[k]
        side = lambda fc_, fill_, **kw: TurnSide(CUBE[k], fc_, fill=fill_, name=f"{NAMES[k]} {fc_.title()}", **kw)
        f[f"{k} front"] = side("front", sides[0], show=unc)
        f[f"{k} back"] = side("back", sides[0], show=unc)
        f[f"{k} left"] = side("left", sides[1], show=unc if k == "R" else None)
        f[f"{k} right"] = side("right", sides[1])
        f[f"{k} turntop"] = TurnTop(CUBE[k], fill=lf, name=lid_name(k, "Top Turning"), show=turning)
        f[f"{k} lid"] = face(k, "top", "lid", fill=lf, name=lid_name(k, "Lid"), lid=True, show=at_rest)
        f[f"{k} lid in"] = face(k, "top", "lid", True, fill=lf, name=lid_name(k, "Lid Inside"), lid=True, show=at_rest)
        f[f"{k} open"] = face(k, "top", fill=DARK_IN, name=lid_name(k, "Opening"), fixed={}, show=opn)
    f["F2 left"] = face("F2", "left", fill=DARK)               # note 1: every cube keeps its left side, even where another cube covers it
    f["F2 front"] = face("F2", "front", fill=DARK)
    f["F2 top"] = face("F2", "top")
    f["M top"] = face("M", "top", fill=DARK)
    f["M left"] = face("M", "left", fill=DARK)
    f["M front"] = face("M", "front")
    f["T top"] = face("T", "top", fill=DARK)
    f["T front"] = face("T", "front", show=lambda p: p.get("cf", 0) == 0)
    f["T flap"] = face("T", "left", "flap", name=f"{NAMES['T']} Flap", show=lambda p: p.get("cp", 0) == 0)
    f["T flap in"] = face("T", "left", "flap", True, name=f"{NAMES['T']} Flap Inside")
    f["T open"] = face("T", "left", fill=DARK_IN, name=f"{NAMES['T']} Opening", fixed={}, show=opn)
    f["F1 cover"] = TurnSide(CUBE["F1"], "front", name=f"{NAMES['F1']} Front Cover", show=cvr)
    f["L0 cover"] = TurnSide(CUBE["L0"], "front", name=f"{NAMES['L0']} Front Cover", show=cvr)
    f["R cover"] = TurnSide(CUBE["R"], "left", fill=DARK, name=f"{NAMES['R']} Front Cover", show=cvr)
    f["T front cover"] = face("T", "front", name=f"{NAMES['T']} Front Cover", show=lambda p: p.get("cf", 0) > 0)
    f["T flap cover"] = face("T", "left", "flap", name=f"{NAMES['T']} Flap Cover", show=lambda p: p.get("cp", 0) > 0)
    key_of = {CUBE[k]: k for k in CELLS}

    # ---------------------------------------------------------------- when each cover is on
    def disc_bottom(g):
        return screen(P.p[g])[1] + R_BALL

    def sc_(g):
        return screen(P.p[g])

    def outline_at(nm, g, **flags):
        k = key_of[f[nm].cube]
        return f[nm].outline({**geo[g][k], **flags})

    # F1's front cover: on from frame 0 until the ball is clear above F1's rim, and again from the frame the lid opens for the way in
    c_f1_off = next(g for g in range(marks["h1"][0] + 1, marks["h1"][1] + 1) if disc_bottom(g - 1) < RIM - 1.0 and P.p[g][2] >= RC - 0.7)
    c_f1_on = f_open4
    c_l0_on, c_l0_off = f_lift, f_jf + 1
    c_r_on, c_r_off = f_jr - 1, f_jt + 1
    # T's front cover: on from the frame in the hop up where the ball has passed behind T's front face and is clear above its top edge
    t_front_top = CUBE["T"].centre[1] - CUBE["T"].hy
    c_tf_on = next(g for g in range(marks["h2"][0], marks["h2"][1] + 1)
                   if P.p[g][2] >= 84.0 + RC - 0.7 and disc_bottom(g) < t_front_top - 1.0 and all(q[2] >= 84 + RC - 0.7 for q in P.p[g:marks["h2"][1] + 1]))
    c_tf_off = Lc - 20
    # T's flap cover: on from before the ball moves into T until the flap has tilted clear of the ball
    c_tp_on = f_jt - 2
    c_tp_off = next(g for g in range(f_flap, f_flap + 60)
                    if poly_dist(sc_(g), f["T flap"].outline(geo[g]["T"])) > R_BALL + 1.0)
    cover = {"F1": lambda g: 1 if (g < c_f1_off or g >= c_f1_on) else 0,
             "L0": lambda g: 1 if c_l0_on <= g < c_l0_off else 0,
             "R": lambda g: 1 if c_r_on <= g < c_r_off else 0,
             "cf": lambda g: 1 if c_tf_on <= g < c_tf_off else 0,
             "cp": lambda g: 1 if c_tp_on <= g < c_tp_off else 0}

    def poses_at(g):
        o = dict(geo[g])
        o["F1"] = {**geo[g]["F1"], "cover": cover["F1"](g), "ov": opening(lid_f1, g)}
        o["L0"] = {**geo[g]["L0"], "cover": cover["L0"](g), "ov": opening(lid_l0, g)}
        o["R"] = {**geo[g]["R"], "cover": cover["R"](g), "ov": opening(lid_r, g)}
        o["T"] = {**geo[g]["T"], "cf": cover["cf"](g), "cp": cover["cp"](g), "ov": opening(flap_t, g)}
        return o
    poses = [poses_at(g) for g in range(Lc + 1)]
    flags = ("cover", "ov", "cf", "cp")
    pk = lambda p: tuple(round(x, 9) for v in p.values() for x in (v if isinstance(v, tuple) else (v,)))
    geom = lambda p: {kk: v for kk, v in p.items() if kk not in flags}
    for k in CELLS:
        assert pk(poses[0][k]) == pk(poses[Lc][k]), ("the loop does not close on", k, poses[0][k], poses[Lc][k])

    # ---------------------------------------------------------------- the rules for the cubes
    for k, ev_ in (("F1", lid_f1), ("L0", lid_l0), ("R", lid_r)):
        for g in range(Lc + 1):
            assert not (poses[g][k]["lid"] > 1e-9 and turning(poses[g][k])), ("a lid is open while its cube turns", k, g)
    turn_win = [(f0, f0 + TURN_TOTAL) for evs in (turn_f1, turn_r, turn_l0) for f0, _ in evs]
    for i_, (a_, b_) in enumerate(turn_win):
        for c_, d_ in turn_win[i_ + 1:]:
            assert b_ <= c_ or d_ <= a_, ("two cubes turn at once", (a_, b_), (c_, d_))

    # ---------------------------------------------------------------- the groups, top first
    groups = {
        "U": ["F2 front", "F2 top", "F1 front", "F1 back", "F1 turntop", "F1 lid", "F1 lid in", "F1 open", "F1 left", "F1 right", "F2 left"],
        "S": ["L0 front", "L0 back", "L0 turntop", "L0 lid", "L0 lid in", "L0 open", "L0 left", "L0 right"],
        "Q": ["T front", "T top", "T flap", "T flap in", "T open"],
        "P": ["M front", "M left", "M top", "R front", "R back", "R turntop", "R lid", "R lid in", "R open", "R left", "R right"],
        "C": ["F1 cover", "L0 cover", "R cover", "T front cover", "T flap cover"],
    }
    for lst in groups.values():
        for nm in list(lst):
            if nm not in f:
                lst.remove(nm)
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
        pose = fc.pose_for(pose) if hasattr(fc, "pose_for") else (fc.fixed if fc.fixed is not None else pose)
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
        if not (CROP[0] - CROP_TOL <= sc[0] - R_BALL and sc[0] + R_BALL <= CROP[1] and sc[1] + R_BALL <= CROP_BOTTOM):
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
                if nm.endswith(" open") or nm.endswith("Opening"):
                    continue                                   # an opening is a hole: the ball is seen through it
                if inside(q, poly):
                    zf = plane_depth(cs, q[0], q[1])
                    if zf is not None and zf < zb - LAYER_TOL:
                        layer_bad.append((g, nm, "face in front of the ball", round(zb - zf, 1)))
    # a cover swaps with its under copy only where the ball is out of sight or clear of its outline
    pops = []
    for key, names in (("F1", ["F1 cover"]), ("L0", ["L0 cover"]), ("R", ["R cover"]), ("T", ["T front cover", "T flap cover"])):
        for nm in names:
            fl = {"F1 cover": "cover", "L0 cover": "cover", "R cover": "cover", "T front cover": "cf", "T flap cover": "cp"}[nm]
            for g in range(1, Lc + 1):
                if poses[g][key].get(fl, 0) != poses[g - 1][key].get(fl, 0):
                    for h in (g - 1, g):
                        if h in hset:
                            continue
                        if poly_dist(sc_(h), f[nm].outline({**poses[h][key], fl: 1})) < R_BALL + 0.3:
                            pops.append((nm, g, h))
    if os.environ.get("MINI_DEBUG"):
        seen = {}
        for g, nm, why, amount in layer_bad:
            seen.setdefault((nm, why), []).append((g, amount))
        for key_, v in seen.items():
            print("  layer:", key_, "frames", [g for g, _ in v][:14], "worst", max(a for _, a in v))
            g0_ = v[0][0]
            print("    ball at", tuple(round(x_, 1) for x_ in P.p[g0_]), P.mode[g0_], "screen", tuple(round(x_, 1) for x_ in screen(P.p[g0_])), "hop4", marks["h4"], "shut4", f_shut4)
        runs = []
        for g, d, at, c in negs:
            if runs and runs[-1][1] == g - 1 and runs[-1][3] == at:
                runs[-1][1], runs[-1][2] = g, min(runs[-1][2], d)
            else:
                runs.append([g, g, d, at, c])
        print("  touching:", runs[:12])
        cr = []
        for g, c in crop_bad:
            if cr and cr[-1][1] == g - 1:
                cr[-1][1] = g
            else:
                cr.append([g, g, c])
        print("  tightest:", tight, " crop runs:", cr[:12], " pops:", pops[:6])
        print("  hop5", f_h5, T5, "ends", f_h5 + T5, "lid shut at", f_ls, "hidden after hop:", [g for g in range(f_h5, f_ls + 8) if g in hset][:3])
        print("  covers: F1 off", c_f1_off, "on", c_f1_on, "; L0", c_l0_on, c_l0_off, "; R", c_r_on, c_r_off, "; T front", c_tf_on, c_tf_off,
              "; T flap", c_tp_on, c_tp_off, "; jumps", sorted(P.jumps))
    assert tight[0] > -0.6, ("the ball touches a cube", tight, negs[:4])
    seen = {}
    for g, nm, why, amount in layer_bad:
        seen.setdefault((nm, why), []).append(g)
    assert not seen, ("the ball is on the wrong side of a face", {k_: (v[0], v[-1], len(v)) for k_, v in seen.items()})
    assert not pops, ("a cover swaps while the ball is beside its outline", pops[:6])
    peek = set(range(marks["peek"][0], marks["peek"][1] + 1))
    crop_other = [c_ for c_ in crop_bad if c_[0] not in peek]
    assert not crop_other, ("the ball leaves the phone crop", crop_other[:6])
    crop_peek = max([sc_(g)[0] + R_BALL - CROP[1] for g, _ in crop_bad if g in peek] + [0.0])
    ball_top = min(screen(p)[1] for p in P.p) - R_BALL
    assert ball_top >= COPY_Y, ("the ball crosses the copy", ball_top)
    lid_top = Y0 + DY - S_ * math.sin(OPEN_TOP)
    assert lid_top >= COPY_Y, ("a lid crosses the copy", lid_top)

    hid = [g in hset for g in range(Lc)]
    longest_hidden, run, run_at = 0, 0, 0
    for g in list(range(Lc)) * 2:
        run = run + 1 if hid[g] else 0
        if run > longest_hidden:
            longest_hidden, run_at = run, g
    hid_runs, run, start = [], 0, 0
    for g in range(2 * Lc):
        if hid[g % Lc]:
            if run == 0:
                start = g
            run += 1
        else:
            if run:
                hid_runs.append((start % Lc, run))
            run = 0
    hid_runs = sorted({(s_, n_) for s_, n_ in hid_runs if n_ < Lc}, key=lambda r: -r[1])[:4]
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
    if os.environ.get("MINI_DEBUG"):
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools"))
        import ball_speed as bs_
        for nm, fc in drawn:
            ps_ = [poses[g][key_of[fc.cube]] for g in range(Lc + 1)]
            for (oid, prop), vals in fc.tracks(ps_, ident).items():
                if prop != "y" or max(vals) - min(vals) < 1.0:
                    continue
                pts_ = bs_.swings(list(vals), 1.5)[1:-1]
                for a_, b_, c_ in zip(pts_, pts_[1:], pts_[2:]):
                    if b_[0] - a_[0] < 20 and c_[0] - b_[0] < 20 and 0.6 * abs(b_[1] - a_[1]) <= abs(c_[1] - b_[1]) <= 1.5 * abs(b_[1] - a_[1]):
                        print("  buzz in", nm, [(round(3.2 + i_ / 60, 2), round(v_, 1)) for i_, v_ in (a_, b_, c_)])
    for nm, fc in drawn:
        ps = [poses[g][key_of[fc.cube]] for g in range(Lc + 1)]
        for (oid, prop), vals in fc.tracks(ps, ident).items():
            kc = key_of[fc.cube]
            if isinstance(fc, TurnSide) and not isinstance(fc, TurnTop) and kc in rel and prop != "opacity":
                vals = list(vals)
                a_end = {"F1": turn_f1, "R": turn_r, "L0": turn_l0}[kc][-1][0] + TURN_TOTAL
                g_r = rel[kc]
                if fc.face in ("front", "left"):                  # out of sight until the hand-over: its corners glide to where it comes back
                    for g_ in range(a_end - 1, g_r):
                        vals[g_] = vals[a_end - 1] + (vals[g_r] - vals[a_end - 1]) * (g_ - a_end + 1) / (g_r - a_end + 1)
                else:                                             # out of sight from the hand-over: its corners glide on to where the seam leaves it
                    last = vals[g_r - 1]
                    for g_ in range(g_r, Lc):
                        vals[g_] = last + (vals[Lc] - last) * (g_ - g_r + 1) / (Lc - g_r + 1)
            if os.environ.get("MINI_DEBUG") and isinstance(fc, TurnSide) and prop == "x":
                jumps_ = [(round(3.2 + g_ / 60, 2), round(vals[g_ + 1] - vals[g_], 1)) for g_ in range(Lc) if abs(vals[g_ + 1] - vals[g_]) > 20]
                if jumps_:
                    print("  jumps", nm, jumps_[:8])
            if max(vals) - min(vals) < 1e-6:
                continue
            assert abs(vals[0] - vals[Lc]) < 1e-6, (nm, oid, prop, vals[0], vals[Lc])
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
    cw = [0.0]
    for g in range(Lc):
        cw.append(cw[-1] + P.w[g])
    wrap = lambda a_: (a_ + math.pi) % (2 * math.pi) - math.pi
    cur = [0.0] * (Lc + 1)                                     # the correction so far, per frame
    dot_fixes = []
    still = lambda g_: g_ < Lc and math.dist(P.p[g_], P.p[g_ + 1]) < 0.05
    g = 0
    while g < Lc:
        if still(g) and not (g > 0 and still(g - 1)):
            b = g
            while still(b + 1):
                b += 1
            r = wrap(cw[g] + cur[g])                           # how far the dot is from up when the ball stops
            if abs(r) > 0.02 and b - g + 1 >= 4:
                m = min(int(min(18, 8 + abs(r) * 7)), b - g + 1)
                for t in range(1, Lc + 1 - g):
                    cur[g + t] += -r * smooth(min(1.0, t / m))
                dot_fixes.append((g, math.degrees(r)))
            g = b + 1
        else:
            g += 1
    th = [cw[g] + cur[g] + P.gl[g] for g in range(Lc + 1)]
    if os.environ.get("MINI_DEBUG"):
        print("  dot fixes (time s, degrees):", [(round(3.2 + g_ / 60, 2), round(d_)) for g_, d_ in dot_fixes])
    total = th[Lc] - th[0]
    want = round(total / (2 * math.pi)) * 2 * math.pi
    # the odd bit of a turn is taken up while the ball is out of sight (the longest hidden stretch after the first jump)
    j_first = min(P.jumps)
    best = None
    g = j_first
    while g < Lc:
        if hid[g]:
            e = g
            while e + 1 < Lc and hid[e + 1]:
                e += 1
            if best is None or e - g > best[1] - best[0]:
                best = (g, e)
            g = e + 1
        else:
            g += 1
    a0, a1 = best[0] + 2, best[1] - 2
    assert a1 - a0 >= 12, ("no hidden stretch to take up the turn", best)
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

    # each jump holds: no frame in between ever draws the ball half way
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
                        if "<KeyFrameDouble" in doc.lines[q] and any(re.search(rf' frame="{jf - 1}"', doc.lines[q]) for jf in P.jumps):
                            doc.lines[q] = doc.lines[q].replace(' interpolationType="linear"', "")
                            held += 1
                    j = pe + 1
                else:
                    j += 1
            break
        i += 1
    moves = sum(abs(screen(P.p[jf])[i_] - screen(P.p[jf - 1])[i_]) > 1e-6 for jf in P.jumps for i_ in (0, 1))      # coordinates that change
    assert held == moves, ("the jumps' keys", held, moves)

    def hold_keys(anim_name, ids, props, frames=None):
        a_, b_ = doc.anim(anim_name)
        ids = set(ids)
        n_ = 0
        i_ = a_
        while i_ < b_:
            m_ = re.search(r'<KeyedObject objectId="([^"]+)"', doc.lines[i_])
            if not m_ or m_.group(1) not in ids:
                i_ += 1
                continue
            e_ = doc.end(i_)
            j_ = i_ + 1
            while j_ < e_:
                pm_ = re.search(r'<KeyedProperty property="([^"]+)"', doc.lines[j_])
                if pm_ and pm_.group(1) in props:
                    pe_ = doc.end(j_)
                    for q_ in range(j_ + 1, pe_):
                        if "<KeyFrameDouble" in doc.lines[q_] and (frames is None or any(re.search(rf' frame="{fr_}"', doc.lines[q_]) for fr_ in frames)):
                            doc.lines[q_] = doc.lines[q_].replace(' interpolationType="linear"', "")
                            n_ += 1
                    j_ = pe_ + 1
                else:
                    j_ += 1
            i_ = e_ + 1
        return n_
    shape_ids = [sid for _, fc in drawn for sid, _ in fc.shapes]
    held_ops = sum(hold_keys(an, shape_ids, ("opacity",)) for an in ("Intro", "Loop") if False) if False else 0
    for an in (f"{ROOM} Intro", f"{ROOM} Loop"):
        held_ops += hold_keys(an, shape_ids, ("opacity",))

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
            ref = fc.cube.quad(fc.face, None, {})
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
    table = "\n".join(f"  {sec(a_):>6}-{sec(b_):<6} {k_:4s} {t_}" for a_, b_, k_, t_ in log)
    flights = "; ".join(f"{lab} {sec(a_)}-{sec(b_)} s ({b_ - a_ + 1} fr) apex y {apex_:.0f}" for lab, a_, b_, apex_, vv in P.notes)
    cube_times = (f"  cubes: F1 lid opens {sec(0)}, shuts {sec(lid_f1[1][0])}; F1 turns {sec(f_t1)} and {sec(f_t2)}; F1 lid again {sec(f_open4)}/"
                  f"{sec(lid_f1[3][0])}; R turns {sec(f_r1)} and {sec(f_r2)}, R lid {sec(lid_r[0][0])}-{sec(lid_r[1][0])}; flap falls {sec(f_flap)}, "
                  f"F1 lid folds over {sec(f_flap)}; L0 lid {sec(f_lift)}-{sec(f_ls)}; L0 turns {sec(f_l1)} and {sec(f_l2)}; flap shuts {sec(flap_t[1][0])}, "
                  f"F1 lid folds back {sec(lid_f1[5][0])}")
    dev = max(math.dist((CUBE[k].centre[0] - CUBE[k].hx, CUBE[k].centre[1] - CUBE[k].hy), FIGMA[k]) for k in CELLS)
    return (f"{ROOM}: loop {Lc / 60:.2f} s ({Lc} frames), the loop starts at 3.20 s with the ball inside F1\n{table}\n{cube_times}\n"
            f"  six cubes on one lattice (every front square within {dev:.2f} px of the Figma), {moving_tracks} vertex tracks keyed "
            f"({thinned} keys thinned, {ball_thinned} on the ball); shut lids flush within {flush:.3f} px\n"
            f"  flights: {flights}\n"
            f"  ball top {ball_top:.0f}, highest lid {lid_top:.0f}; closest to any cube face, edge or lid: {tight[0]:.2f} px (frame {tight[1]}, {sec(tight[1])} s, {tight[2]})\n"
            f"  the peek in R sits {crop_peek:.1f} px past the crop's right edge; the dot is brought back up {len(dot_fixes)} times (largest {max([abs(d_) for _, d_ in dot_fixes] + [0]):.0f} degrees)\n"
            f"  longest out of sight {longest_hidden} frames ({longest_hidden / 60:.2f} s, ending {sec(run_at)} s); the longest stretches (start s, seconds): "
            f"{[(sec(s_), round(n_ / 60, 2)) for s_, n_ in hid_runs]}; longest still in view outside "
            f"the rests {longest_still} frames ({longest_still / 60:.2f} s, from {sec(still_at) if still_at is not None else '-'} s)")
