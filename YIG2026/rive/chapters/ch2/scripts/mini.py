"""The Mini, "the trick" (loop reworked 2026-11-05): a magic trick with clear moves and real pauses, 18.9 s.

Every cube, still or moving, is drawn by the 3D cube method (cube3d.py), from one viewpoint, every face one solid colour. The arrival
(the intro, 3.2 s) is unchanged and everything is still until it ends: the ball is hidden in the top cube U and the first move starts on
the loop's first frame. Moves never overlap (asserted for the lids and the turn; the ball's hops and rolls are sequential by
construction), and every lid and tip is eased: no linear moves.

Timeline (scene clock, the Finesse panel's; the loop starts at 3.20 s):
   1.83- 3.20 rest   the hide: nothing moves; the ball is in U (and, unseen, in L)
 THE LID TRICK (two lid opens: L, then U)
   3.20- 3.90 move   L's lid opens: the cube presses down 1.4, the lid dips 1.8 degrees, lifts (eased out) to 96 and settles to 92
   3.90- 4.20 rest
   4.20- 4.63 move   the ball rises out of L (eased lift 39 px) and glances at U
   4.63- 4.93 rest
   4.93- 5.63 move   U's lid opens (the same feel)
   5.63- 5.93 rest
   5.93- 6.90 move   the ball hops from L into U (parabola at 0.40, 52 frames) and settles out of sight
   6.90- 7.20 rest
   7.20- 7.67 move   L's lid falls shut (constant acceleration, 0.27 s), then two taps (2.4 and 0.9 degrees; the lid reopens a hair and a
                     thin dark gap shows inside the cube's outline, never outside it) and lies flush
   7.67- 7.97 rest
   7.97- 8.43 move   U's lid falls shut, two taps
   8.43- 8.77 rest   the hide: the ball is in U, every lid shut
 THE REVEAL
   8.77- 9.47 move   U turns 90 degrees (the keeper turn, unchanged: 0.5 s, 3 degree overshoot, settle): its right face is an open face, dark,
                     and as the front swings away the ball is there, sitting in it
   9.47- 9.77 rest
   9.77-10.43 move   the ball rolls out of the open face onto the right stack's top (eased in and out, the dot turning with it)
  10.43-12.27 REST 1 the ball on the right stack in plain view, nothing moves (1.83 s)
 THE LAUNCH
  12.27-13.87 move   the ball gathers (5 percent), hops over U (parabola, apex y 459) onto the rear left of the front cube's black top, lands (squash
                     5 percent, back within 0.2 s) and its settle roll carries it onto its spot
  13.87-14.27 rest
  14.27-16.13 move   the front cube rocks back 3 degrees and tips forward (slow start, fast middle) to 34 plus 4 of follow-through; the ball rides its
                     top and is flicked up and over U (a fling, leaves at 13.9 px per frame, the hop landed at 14.0) onto the right stack
                     (stretch 3 percent, landing squash 5 percent, settle roll)
  16.13-16.47 rest   the front cube stays tipped, its black top showing
  16.47-17.17 move   the front cube tips back upright (heavy; one small rock back, 2 degrees)
  17.17-19.00 REST 2 the ball on the right stack in plain view, nothing moves (1.83 s)
 BACK TO THE START
  19.00-19.63 move   the ball rolls back into U's open face
  19.63-19.93 rest
  19.93-20.63 move   U turns back: its front covers the ball
  20.63-20.77 rest   the hide (the seam): every cube on its drawn pose, the ball out of sight in U
The ball is out of sight for at most 2.5 s (the seam, through the first lid and the pause after it) and in plain view for every other rest.
The tip is 34 degrees, not a quarter turn: a 90 degree tip puts the cube's new front face wholly below the phone frame, and the rear
corners of the top drop after about 22 degrees (see TIP below).
"""
import math
import os
import re
import xml.etree.ElementTree as ET

import cube3d as c3
from cube3d import Cube, Face, LIGHT, DARK
from common import CENTER_IN_SCALE, BallArt, Cycle, _set_attrs, emit, plane_x, prepare_ball, smooth

ROOM = "The Mini"
T0 = 110                                   # 1.83 s: the tops have landed (their squash is over at 1.82 s)
A = (747.5, 711.5)                         # the scale's anchor: the room's middle, on the floor line
K = 0.85
PLANES = {"Front": "9:5695", "Floor": "9:5694"}
CUBES = ("9:5206", "9:5208", "9:5210", "9:5212")    # the four drop-ins
ART = {"c1": "9:5207", "c3": "9:5211", "c4": "9:5213"}    # their Art nodes (their space is the planes' own space)
BALL_SCALE = 1.7
G = 0.40
R_BALL = 17.678 * BALL_SCALE               # the ball's radius on the screen (30.05)
RC_PLANE = 17.2 * BALL_SCALE / K           # the ball's centre to what it rests on, in the planes' units
COPY_Y = 425.0                             # the ball's top and every moving piece stay at or below this
CROP = (560.0, 935.0)

# ---- the cubes (the planes' own space, before the 0.85) ---------------------------------------------------------------------
# One viewpoint for all four: the depth goes up and to the LEFT, (-38.332, -44.682) for a 95.829 cube.
D3 = (-38.332, -44.682)
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

# every face one solid colour, as the illustration drew it. U's right face, which the art never drew, is the cube's open face: dark,
# seen only when the cube has turned to bring it to the front.
COL = {
    (U, "front"): LIGHT, (U, "left"): LIGHT, (U, "back"): LIGHT, (U, "lid"): DARK, (U, "open"): DARK,
    (R, "front"): DARK, (R, "left"): LIGHT, (R, "top"): LIGHT,
    (F, "front"): LIGHT, (F, "left"): LIGHT, (F, "top"): DARK,
    (L, "front"): LIGHT, (L, "left"): DARK, (L, "lid"): LIGHT,
}

# ---- tempo (frames at 60/s) -------------------------------------------------------------------------------------------------
# A lid opening: a press (the cube dips 1.4 and the lid 1.8 degrees closed-ward), the lid lifts (eased out) a few degrees past open,
# and settles back. Shutting is quicker: it falls under its own weight (constant acceleration), lands, and taps twice.
OPEN_TOP, OVERSWING = math.radians(92), math.radians(4)    # past about 98 the free edge dips back and reads as a wobble
PRESS, PRESS_N, DIP = math.radians(1.8), 8, 1.4
LIFT_N, LSETTLE_N = 22, 12
OPEN_N = PRESS_N + LIFT_N + LSETTLE_N      # 42: 0.7 s
FALL_N, BUMP1_N, BUMP2_N = 16, 7, 5        # the fall 0.27 s, then two taps
BUMP1, BUMP2 = math.radians(2.4), math.radians(0.9)
SHUT_N = FALL_N + BUMP1_N + BUMP2_N        # 28: 0.47 s
TURN_N, SETTLE_N, OVER = 30, 12, math.radians(3)            # the top cube's turn: the keeper (0.5 s, a 3 degree overshoot that settles)
TURN_TOTAL = TURN_N + SETTLE_N
# the front cube's tip: it rocks back 3 degrees, tips forward (slow start, fast middle) a few degrees past 48 and settles; the way back
# is heavy too and ends with a small rock back. The rear corners of the top rise until the tip reaches about 22 degrees and drop after it;
# the further past that, the more that drop looks like a second swing to the jitter check (a buzz), and past about 50 degrees the front
# edge leaves the phone frame. 34 degrees (38 with the follow-through) is the biggest tip that passes, and shows the black top fully
TIP, TIP_OVER, TIP_ANT = math.radians(34), math.radians(4), math.radians(3)
TIP_ANT_N, TIP_FWD_N, TIP_SETTLE_N = 10, 32, 12
TIP_UP_N = TIP_ANT_N + TIP_FWD_N + TIP_SETTLE_N            # 54
TIP_REL = TIP_ANT_N + TIP_FWD_N // 2                       # the ball leaves at the fastest moment of the tip
TIPBACK_N, TIPBACK_SETTLE_N, TIPBACK_OVER = 32, 10, math.radians(2)
TIP_DOWN_N = TIPBACK_N + TIPBACK_SETTLE_N                  # 42
PEEK_N, PEEK_RISE = 16, 39.2               # the peek's lift (39.2 px in 0.27 s)
GL = math.radians(12)                      # a glance
DUR = {"open": OPEN_N, "shut": SHUT_N}


def S(p):
    return (A[0] + K * (p[0] - A[0]), A[1] + K * (p[1] - A[1]))


def ease_io(u):
    u = min(1.0, max(0.0, u))
    return 4 * u ** 3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2


def lift_ease(u):
    """Eases out (most of the swing early) from a standing start, and arrives with no speed."""
    s = smooth(u)
    return 1 - (1 - s) ** 2


# ---- the moves: an angle per cycle frame ------------------------------------------------------------------------------------------
def lid_angles(events, n):
    """events: [(frame, "open" | "shut")] -> (lid angle, cube dip) per frame. A shut lid is exactly 0 from the end of its move."""
    a, dip = [0.0] * (n + 1), [0.0] * (n + 1)
    evs = sorted(events)
    for (fa, ka), (fb, kb) in zip(evs, evs[1:]):
        assert fb - fa >= DUR[ka], ("a lid move starts before the one before it has finished", fa, ka, fb, kb)
    for k, (f0, kind) in enumerate(evs):
        f1 = evs[k + 1][0] if k + 1 < len(evs) else n + 1
        for g in range(f0, f1):
            t = g - f0
            if kind == "open":
                if t < PRESS_N:
                    a[g] = -PRESS * smooth(t / PRESS_N)
                    dip[g] = DIP * math.sin(math.pi * t / PRESS_N)
                elif t < PRESS_N + LIFT_N:
                    a[g] = -PRESS + (OPEN_TOP + OVERSWING + PRESS) * lift_ease((t - PRESS_N) / LIFT_N)
                elif t < OPEN_N:
                    a[g] = OPEN_TOP + OVERSWING * (1 - smooth((t - PRESS_N - LIFT_N) / LSETTLE_N))
                else:
                    a[g] = OPEN_TOP
            else:
                if t < FALL_N:
                    a[g] = OPEN_TOP * (1 - (t / FALL_N) ** 2)
                elif t < FALL_N + BUMP1_N:
                    a[g] = BUMP1 * math.sin(math.pi * (t - FALL_N) / BUMP1_N)
                elif t < SHUT_N:
                    a[g] = BUMP2 * math.sin(math.pi * (t - FALL_N - BUMP1_N) / BUMP2_N)
                else:
                    a[g] = 0.0
    return a, dip


def turn_angles(events, n):
    """events: [(frame, ("turn", target))]: the keeper turn, 0.5 s with a small overshoot that settles."""
    a = [0.0] * (n + 1)
    evs = sorted(events, key=lambda e: e[0])
    for (fa, ka), (fb, kb) in zip(evs, evs[1:]):
        assert fb - fa >= TURN_TOTAL, ("a turn starts before the one before it has settled", fa, fb)
    for k, (f0, kind) in enumerate(evs):
        f1 = evs[k + 1][0] if k + 1 < len(evs) else n + 1
        a0 = a[f0 - 1] if f0 > 0 else 0.0
        target = kind[1]
        over = math.copysign(OVER, target - a0)
        for g in range(f0, f1):
            t = g - f0
            if t < TURN_N:
                a[g] = a0 + (target + over - a0) * ease_io(t / TURN_N)
            elif t < TURN_TOTAL:
                a[g] = target + over * (1 - smooth((t - TURN_N) / SETTLE_N))
            else:
                a[g] = target
    return a


def tip_up(t):
    """The tip forward, t frames after it starts."""
    if t < TIP_ANT_N:
        return -TIP_ANT * smooth(t / TIP_ANT_N)
    if t < TIP_ANT_N + TIP_FWD_N:
        return -TIP_ANT + (TIP + TIP_OVER + TIP_ANT) * ease_io((t - TIP_ANT_N) / TIP_FWD_N)
    if t < TIP_UP_N:
        return TIP + TIP_OVER * (1 - smooth((t - TIP_ANT_N - TIP_FWD_N) / TIP_SETTLE_N))
    return TIP


def tip_down(t):
    """The way back, heavy, ending with one small rock back that settles."""
    if t < TIPBACK_N:
        return TIP + (-TIPBACK_OVER - TIP) * ease_io(t / TIPBACK_N)
    if t < TIP_DOWN_N:
        return -TIPBACK_OVER * (1 - smooth((t - TIPBACK_N) / TIPBACK_SETTLE_N))
    return 0.0


def tip_angles(events, n):
    """events: [(frame, "up" | "down")] -> the tip angle per frame."""
    a = [0.0] * (n + 1)
    evs = sorted(events)
    for (fa, ka), (fb, kb) in zip(evs, evs[1:]):
        assert fb - fa >= (TIP_UP_N if ka == "up" else TIP_DOWN_N), ("a tip starts before the one before it has settled", fa, fb)
    for k, (f0, kind) in enumerate(evs):
        f1 = evs[k + 1][0] if k + 1 < len(evs) else n + 1
        for g in range(f0, f1):
            a[g] = tip_up(g - f0) if kind == "up" else tip_down(g - f0)
    return a


# ---- the ball's timeline ----------------------------------------------------------------------------------------------------
class Path:
    """The ball frame by frame: centre, mode ("hidden" wholly out of sight in a box, "air", "roll", "rest"), the turn it adds per frame
    (rolling and the spin it keeps in the air), a glance (the turn of its dot in place) and a squash (signed: down is negative, volume kept)."""

    def __init__(self):
        self.p, self.mode, self.w, self.glance, self.sq = [], [], [], [], []
        self.notes = []

    @property
    def now(self):
        return len(self.p)

    def put(self, p, mode, w=0.0, gl=0.0, sq=0.0):
        self.p.append(p)
        self.mode.append(mode)
        self.w.append(w)
        self.glance.append(gl)
        self.sq.append(sq)

    def rest(self, p, n, mode="hidden"):
        for _ in range(n):
            self.put(p, mode)

    def peek(self, p, rise_at, keys, end_at):
        """The ball's lift out of a box: from frame rise_at an eased lift of PEEK_RISE in PEEK_N frames (arriving softly), then it stays up
        until end_at, its glance (the turn of its dot) eased between the keys [(frame, angle)]; where two keys have the same angle it
        keeps a faint eased roll of about a degree. Returns the position it ends at."""
        assert self.now == rise_at, (self.now, rise_at)

        def glance(f):
            if f <= keys[0][0]:
                return keys[0][1]
            for (f0, a0), (f1, a1) in zip(keys, keys[1:]):
                if f0 <= f <= f1:
                    u = (f - f0) / (f1 - f0)
                    return a0 + (a1 - a0) * ease_io(u) + (math.radians(1.1) * math.sin(math.pi * u) if abs(a1 - a0) < 1e-9 and a0 != 0 else 0.0)
            return keys[-1][1]
        for t in range(1, PEEK_N + 1):
            self.put((p[0], p[1] - PEEK_RISE * smooth(t / PEEK_N)), "air", gl=glance(rise_at + t - 1))
        top = (p[0], p[1] - PEEK_RISE)
        for f in range(rise_at + PEEK_N, end_at):
            self.put(top, "rest", gl=glance(f))
        return top

    def fly(self, p0, p1, catch_y, T):
        """From rest at p0 into a box: a parabola at 0.40 that is T frames from launch to the frame its centre is at catch_y (out of
        sight), then 6 frames settling to p1. Returns (launch frame, the frame it is out of sight, v)."""
        vy = (catch_y - p0[1]) / T - 0.5 * G * T
        assert vy < 0, ("the flight cannot rise", vy)
        vx = (p1[0] - p0[0]) / T
        f_go = self.now
        w = 0.25 * vx / R_BALL
        for t in range(1, T + 1):
            q = (p0[0] + vx * t, p0[1] + vy * t + 0.5 * G * t * t)
            self.put(q, "air" if t < T else "hidden", w=w)
        f_in = self.now - 1
        for k in range(1, 7):
            s_ = smooth(k / 6)
            self.put((q[0] + (p1[0] - q[0]) * s_, q[1] + (p1[1] - q[1]) * s_), "hidden")
        apex = min(y for _, y in self.p[f_go:f_in])
        self.notes.append(("into a box", f_go, f_in, apex, (vx, vy)))
        return f_go, f_in, (vx, vy)

    def gather(self, p, n, a):
        """A gather before a hop: the ball presses down by a (a fraction) over n frames."""
        for t in range(1, n + 1):
            self.put(p, "rest", sq=-a * smooth(t / n))

    def arc(self, p0, p1, T, gather=0.0, stretch=0.0, label="hop"):
        """A hop from rest at p0 to a landing on a surface at p1, T frames, at 0.40. It leaves from the gather and stretches by
        `stretch` while it is fast. Returns (vx, vy at launch, vy at landing)."""
        vy = (p1[1] - p0[1]) / T - 0.5 * G * T
        assert vy < 0, ("the hop cannot rise", vy)
        vx = (p1[0] - p0[0]) / T
        f_go = self.now
        w = 0.25 * vx / R_BALL
        for t in range(1, T + 1):
            q = (p0[0] + vx * t, p0[1] + vy * t + 0.5 * G * t * t)
            u = smooth(min(1.0, t / 3))
            sq = -gather * (1 - u) + stretch * u * (1 - smooth((t - 3) / 13))
            self.put(q, "air" if t < T else "roll", w=w if t < T else 0.0, sq=sq)
        apex = min(y for _, y in self.p[f_go:])
        self.notes.append((label, f_go, self.now - 1, apex, (vx, vy)))
        return vx, vy, vy + G * T

    def land(self, p, vk, n, amp):
        """After a landing at p: it keeps vk of the speed along the surface and rolls to a stop over n frames (the speed falling to zero), with a
        squash of amp that springs back within 12 frames. Returns where it stops."""
        x0, prev = p[0], p[0]
        for t in range(1, n + 1):
            x = x0 + vk * n / 2 * (1 - (1 - t / n) ** 2)
            sq = -amp * math.sin(math.pi * min(1.0, t / 12)) ** 2 if t < 12 else 0.0
            self.put((x, p[1]), "roll", w=(x - prev) / R_BALL, sq=sq)
            prev = x
        return (x0 + vk * n / 2, p[1])

    def roll(self, p0, p1, n):
        """A roll from rest to rest, eased in and out, the dot turning with the distance."""
        prev = p0[0]
        for t in range(1, n + 1):
            s_ = smooth(t / n)
            q = (p0[0] + (p1[0] - p0[0]) * s_, p0[1] + (p1[1] - p0[1]) * s_)
            self.put(q, "roll", w=(q[0] - prev) / R_BALL)
            prev = q[0]


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
    return pose.get("lid", 0) > 1e-9


def ball_on_top(cube, pose, u, v):
    """The ball's centre on the screen when it rests on the cube's top face at (u across, v from the back edge to the front edge)."""
    a, b, c, d = cube.quad3("top", None, pose)
    contact = c3.add(a, c3.add(c3.mul(c3.sub(b, a), u), c3.mul(c3.sub(d, a), v)))
    e1, e2 = c3.sub(b, a), c3.sub(d, a)
    nx = (e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0])
    ln = math.sqrt(sum(x * x for x in nx))
    n_out = tuple(-x / ln for x in nx)                  # the outward normal (up for a top face)
    centre3 = c3.add(contact, c3.mul(n_out, RC_PLANE))
    return S(cube.cam.project(centre3))


# ---- the hidden check -------------------------------------------------------------------------------------------------------
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
    move_before(doc, "9:5206", "9:5212")            # Cubes 1 (U's and F's tops) above Cubes 4 (R's top): U's lid sits in front of R's
    arts = scale_room(doc)

    # ---------------------------------------------------------------- the ball
    art = BallArt(scene, ROOM)
    _set_attrs(doc, art.b01, {"scaleX": BALL_SCALE, "scaleY": BALL_SCALE})
    art.k = BALL_SCALE
    art.R, art.Rc = R_BALL, 17.2 * art.k
    sx, sy = -0.072021484, 0.096008301
    art.dc = (art.ox + art.k * (sx + CENTER_IN_SCALE[0]), art.oy + art.k * (sy + CENTER_IN_SCALE[1]))
    spin = prepare_ball(doc, art)

    cub = {"U": U, "R": R, "F": F, "L": L}
    top_y = lambda cube: S((0.0, cube.centre[1] - cube.hy))[1]            # the front face's top edge on the screen
    IN = {k: (round(S(c.cam.project(c.centre))[0], 1), round(top_y(c) + 36, 1)) for k, c in cub.items()}    # at rest in a box: wholly behind its front and side
    CATCH = {k: round(top_y(c) + 32, 1) for k, c in cub.items()}          # a centre this low is wholly out of sight
    R_REST = (902.0, 622.5)                                                # on the right stack's top, in plain view (its centre 30 inside the crop)
    F_UV = (0.10, 0.25)                                                    # where on the front cube's top it sits
    F_REST = ball_on_top(F, {}, *F_UV)

    P = Path()
    lids = {"U": [], "L": []}
    turn, tips, log = [], [], []

    def seg(kind, label, n0):
        log.append((n0, P.now, kind, label))

    # ================================================================ the hide, then the lid trick (two lid opens)
    n0 = P.now
    P.rest(IN["U"], 62)                                   # still: the ball is in U (the arrival)
    P.rest(IN["L"], 20)                                   # ... and, unseen, in L
    seg("rest", "the hide: the ball is out of sight (in U, then unseen in L)", n0)
    n0 = P.now
    lids["L"].append((P.now, "open"))                     # lid open 1
    P.rest(IN["L"], OPEN_N)
    seg("move", "L's lid opens (press, lift, swing past, settle)", n0)
    n0 = P.now
    P.rest(IN["L"], 18)
    seg("rest", "pause (the mouth of L is open and dark)", n0)
    n0 = P.now
    rise = P.now
    top_L = P.peek(IN["L"], rise, [(rise, 0), (rise + PEEK_N + 2, GL), (rise + PEEK_N + 10, GL)], rise + PEEK_N + 10)
    seg("move", "the ball rises out of L and glances at U", n0)
    n0 = P.now
    P.rest(top_L, 18, "rest")
    seg("rest", "pause (the ball in plain view above L)", n0)
    n0 = P.now
    lids["U"].append((P.now, "open"))                     # lid open 2
    P.rest(top_L, OPEN_N, "rest")
    seg("move", "U's lid opens", n0)
    n0 = P.now
    P.rest(top_L, 18, "rest")
    seg("rest", "pause (both lids open, the ball up)", n0)
    n0 = P.now
    P.fly(top_L, IN["U"], CATCH["U"], 52)
    seg("move", "the ball hops from L into U and is out of sight", n0)
    hop_in = P.notes[-1]
    n0 = P.now
    P.rest(IN["U"], 18)
    seg("rest", "pause (the ball is in U)", n0)
    n0 = P.now
    lids["L"].append((P.now, "shut"))
    P.rest(IN["U"], SHUT_N)
    seg("move", "L's lid falls shut, two taps", n0)
    n0 = P.now
    P.rest(IN["U"], 18)
    seg("rest", "pause", n0)
    n0 = P.now
    lids["U"].append((P.now, "shut"))
    P.rest(IN["U"], SHUT_N)
    seg("move", "U's lid falls shut, two taps", n0)
    n0 = P.now
    P.rest(IN["U"], 20)
    seg("rest", "the hide: the ball is in U, every lid shut", n0)

    # ================================================================ the reveal: U turns and the ball is there
    n0 = P.now
    turn.append((P.now, ("turn", math.pi / 2)))
    P.rest(IN["U"], TURN_TOTAL, "rest")
    seg("move", "U turns 90 degrees (the keeper): its open face comes round and the ball is revealed sitting there", n0)
    n0 = P.now
    P.rest(IN["U"], 18, "rest")
    seg("rest", "pause (the ball in the open face)", n0)
    n0 = P.now
    P.roll(IN["U"], R_REST, 40)
    seg("move", "the ball rolls out of U onto the right stack's top", n0)
    n0 = P.now
    P.rest(R_REST, 110, "rest")
    seg("rest", "REST 1: the ball on the right stack, in plain view", n0)

    # ================================================================ the launch
    T_HOP, LAND_N, LAND_AMP, KEEP = 63, 24, 0.05, 0.8
    n0 = P.now
    P.gather(R_REST, 9, 0.05)
    vx_h = (F_REST[0] - R_REST[0]) / (T_HOP + KEEP * LAND_N / 2)       # lands to the right of its spot and rolls left onto it
    land_F = (F_REST[0] - KEEP * vx_h * LAND_N / 2, F_REST[1])
    _, vy_h, vy_land = P.arc(R_REST, land_F, T_HOP, gather=0.05, stretch=0.02, label="hop onto the front cube")
    P.land(land_F, KEEP * vx_h, LAND_N, LAND_AMP)
    seg("move", "the ball hops over U onto the front cube's top (gather 5%, landing squash 5%, settle roll)", n0)
    hop_F = P.notes[-1]
    v_in = math.hypot(vx_h * KEEP, vy_land)
    n0 = P.now
    P.rest(F_REST, 24, "rest")
    seg("rest", "pause (the ball on the front cube)", n0)
    n0 = P.now
    tip_at = P.now
    tips.append((tip_at, "up"))
    for t in range(TIP_REL):                              # it rides the top as the cube rocks back and tips
        P.put(ball_on_top(F, {"tip": tip_up(t)}, *F_UV), "rest")
    p_rel = ball_on_top(F, {"tip": tip_up(TIP_REL)}, *F_UV)
    T_FL = 62
    vx_f = (R_REST[0] - p_rel[0]) / (T_FL + KEEP * LAND_N / 2)
    land_R = (R_REST[0] - KEEP * vx_f * LAND_N / 2, R_REST[1])
    vx_f2, vy_f, vy_fl = P.arc(p_rel, land_R, T_FL, stretch=0.03, label="fling off the front cube")
    P.land(land_R, KEEP * vx_f2, LAND_N, LAND_AMP)
    seg("move", "the front cube tips forward (black top showing) and flicks the ball up and over U onto the right stack (squash 5%, settle roll)", n0)
    fling = P.notes[-1]
    v_out = math.hypot(vx_f2, vy_f)
    assert tip_at + TIP_UP_N <= P.now
    n0 = P.now
    P.rest(R_REST, 20, "rest")
    seg("rest", "pause (the front cube stays tipped, black top showing)", n0)
    n0 = P.now
    tips.append((P.now, "down"))
    P.rest(R_REST, TIP_DOWN_N, "rest")
    seg("move", "the front cube tips back upright (heavy, one small rock back)", n0)
    n0 = P.now
    P.rest(R_REST, 110, "rest")
    seg("rest", "REST 2: the ball on the right stack, in plain view", n0)

    # ================================================================ back to the start
    n0 = P.now
    P.roll(R_REST, IN["U"], 38)
    seg("move", "the ball rolls back into U's open face", n0)
    n0 = P.now
    P.rest(IN["U"], 18, "rest")
    seg("rest", "pause (the ball in the open face)", n0)
    n0 = P.now
    turn.append((P.now, ("turn", 0.0)))
    P.rest(IN["U"], TURN_TOTAL, "rest")
    seg("move", "U turns back: the ball is out of sight again", n0)
    n0 = P.now
    TAIL = 8
    P.rest(IN["U"], TAIL)
    seg("rest", "the hide (the loop's seam)", n0)
    Lc = P.now                                            # frame Lc is frame 0 again
    P.put(IN["U"], "hidden")

    # ---------------------------------------------------------------- the pieces' poses, frame by frame
    a_lidU, dipU = lid_angles(lids["U"], Lc)
    a_lidL, dipL = lid_angles(lids["L"], Lc)
    a_turn = turn_angles(turn, Lc)
    a_tip = tip_angles(tips, Lc)
    for arr in (a_lidU, a_lidL, a_turn, a_tip, dipU, dipL):
        assert abs(arr[0]) < 1e-9 and abs(arr[Lc]) < 1e-9
    poses = {
        "U": [{"turn": a_turn[g], "lid": a_lidU[g], "dip": dipU[g]} for g in range(Lc + 1)],
        "L": [{"lid": a_lidL[g], "dip": dipL[g]} for g in range(Lc + 1)],
        "F": [{"tip": a_tip[g]} for g in range(Lc + 1)],
        "R": [{} for g in range(Lc + 1)],
    }
    # moves never overlap: no two of the pieces move on the same frame (the ball's hops and rolls count; the front cube's tail of
    # settling while the ball is in the air is the same move)
    moving = [[abs(arr[g + 1] - arr[g]) > 1e-9 for arr in (a_lidU, a_lidL, a_turn)] for g in range(Lc)]
    assert all(sum(m) <= 1 for m in moving), "two moves at once"
    # U never turns with its lid open
    for g in range(Lc + 1):
        if abs(a_turn[g]) > 1e-6 and abs(a_turn[g] - math.pi / 2) > 1e-6:
            assert abs(a_lidU[g]) < 1e-9, ("U turns with its lid open", g)

    # ---------------------------------------------------------------- the faces
    faces = {
        "front": [Face(U, "front", fill=COL[(U, "front")], name=f"{U.name} Front"),
                  Face(U, "left", fill=COL[(U, "left")]), Face(U, "back", fill=COL[(U, "back")]),
                  Face(L, "front", fill=COL[(L, "front")]), Face(L, "left", fill=COL[(L, "left")]),
                  Face(F, "front", fill=COL[(F, "front")]), Face(F, "left", fill=COL[(F, "left")])],
        "c3": [Face(R, "front", fill=COL[(R, "front")])],
        "floor": [Face(U, "right", fill=COL[(U, "open")], name=f"{U.name} Open Face")],
        "c1": [Face(U, "top", "lid", fill=COL[(U, "lid")], name=f"{U.name} Lid"), Face(U, "top", "lid", flip=True, name=f"{U.name} Lid Inside"),
               Face(U, "top", fill=DARK, name=f"{U.name} Opening", fixed={}, show=lid_off),
               Face(F, "top", fill=COL[(F, "top")], name=f"{F.name} Top"),
               Face(L, "top", "lid", fill=COL[(L, "lid")], name=f"{L.name} Lid", two_sided=True),
               Face(L, "top", fill=DARK, name=f"{L.name} Opening", fixed={}, show=lid_off)],
        "c4": [Face(R, "top", fill=COL[(R, "top")], name=f"{R.name} Top")],
        "floor_end": [Face(R, "left", fill=COL[(R, "left")])],
    }
    key_of = {U: "U", R: "R", F: "F", L: "L"}
    rest = lambda f: poses[key_of[f.cube]][0]
    ident = lambda p: p
    where = {"front": (arts["Front"], insert_first), "c3": (ART["c3"], insert_first), "floor": (arts["Floor"], insert_first),
             "c1": (ART["c1"], insert_first), "c4": (ART["c4"], insert_first), "floor_end": (arts["Floor"], insert_last)}
    for grp in faces:                               # a face no pose ever shows is not drawn at all (U's back)
        faces[grp] = [f for f in faces[grp] if any(f.visible(poses[key_of[f.cube]][g]) for g in range(Lc + 1))]
    for grp, fs in faces.items():
        parent, put = where[grp]
        pad = pad_in(doc, parent)
        lines = []
        for f in fs:
            lines += f.lines(doc, pad, rest(f), ident)
        put(doc, parent, lines)

    # every face's tracks; only the ones that move are keyed
    pieces, vertex_ids, moving_tracks = [], [], 0
    for grp, fs in faces.items():
        for f in fs:
            ps = poses[key_of[f.cube]]
            for (oid, prop), vals in f.tracks(ps, ident).items():
                if max(vals) - min(vals) < 1e-6:
                    continue
                assert abs(vals[0] - vals[Lc]) < 1e-6, (f.name, oid, prop)
                pieces.append((oid, prop, (lambda g, a=vals: a[g]), None))
                if prop != "opacity":
                    vertex_ids.append(oid)
                    moving_tracks += 1

    # ---------------------------------------------------------------- the checks on the screen
    front_faces = [f for f in faces["front"]] + faces["c3"]
    ball_top = min(p[1] for p in P.p) - R_BALL
    assert ball_top >= COPY_Y, ("the ball crosses the copy", ball_top)
    piece_top = min(S(q)[1] for grp in faces.values() for f in grp for g in range(0, Lc + 1, 2)
                    for q in f.outline(poses[key_of[f.cube]][g]) if f.visible(poses[key_of[f.cube]][g]))
    assert piece_top >= COPY_Y, ("a piece crosses the copy", piece_top)
    seen_hidden, behind, reveal_cover = [], {}, []
    for g in range(Lc + 1):
        covers = [(f.cube, [S(q) for q in f.outline(poses[key_of[f.cube]][g])]) for f in front_faces if f.visible(poses[key_of[f.cube]][g])]
        if P.mode[g] != "hidden":
            assert CROP[0] <= P.p[g][0] - R_BALL and P.p[g][0] + R_BALL <= CROP[1], ("the ball leaves the phone crop", g, P.p[g])
            pts = disc(P.p[g], R_BALL)
            if P.mode[g] == "air":                      # in the air it passes only in front of, or into the top of, the boxes
                for cube, poly in covers:
                    n_in = sum(inside(q, poly) for q in pts)
                    if n_in:
                        behind.setdefault(cube.name, []).append((g, n_in))
            if turn[0][0] <= g <= turn[0][0] + TURN_TOTAL:
                reveal_cover.append((g, round(sum(any(inside(q, c) for _, c in covers) for q in pts) / len(pts), 2)))
            continue
        bad = [q for q in disc(P.p[g], R_BALL - 0.8) if not any(inside(q, c) for _, c in covers)]
        if bad:
            seen_hidden.append((g, len(bad)))
    assert not seen_hidden, ("the ball shows when it should be hidden", seen_hidden[:8], [P.p[g] for g, _ in seen_hidden[:3]], [a_turn[g] for g, _ in seen_hidden[:3]])
    nothing_moves = sum(
        not (any(abs(arr[g + 1] - arr[g]) > 1e-9 for arr in (a_lidU, a_lidL, a_turn, a_tip)) or math.dist(P.p[g], P.p[g + 1]) > 0.02
             or abs(P.sq[g + 1] - P.sq[g]) > 1e-6 or abs(P.glance[g + 1] - P.glance[g]) > 1e-6)
        for g in range(Lc))
    longest, run = 0, 0
    for g in list(range(Lc)) * 2:
        run = run + 1 if P.mode[g] == "hidden" else 0
        longest = max(longest, run)
    if os.environ.get("MINI_DEBUG"):
        for name, spans_ in behind.items():
            fr = sorted({g for g, _ in spans_})
            runs, start = [], fr[0]
            for a_, b_ in zip(fr, fr[1:] + [None]):
                if b_ != a_ + 1:
                    runs.append((start, a_, max(n for g, n in spans_ if start <= g <= a_)))
                    start = b_
            print("  ball in front-plane of", name, "frames (from, to, most disc points covered):", runs)
        print("  reveal coverage (frame, covered share):", reveal_cover[::3])
        print("  ball rest on F", F_REST, "released at", p_rel, "lands on R at", land_R)

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
    total = th[Lc]
    want = round(total / (2 * math.pi)) * 2 * math.pi
    a0 = Lc - TAIL                                   # the closing hide takes up what is left over to a whole number of turns
    for g in range(a0, Lc + 1):
        th[g] += (want - total) * smooth((g - a0) / (Lc - a0))
    th = [th[g] + P.glance[g] for g in range(Lc + 1)]
    px = plane_x(scene, sheet, ROOM, "Front")

    def pre(f):
        return (IN["U"][0] + px(f), IN["U"][1]), 1.0, 1.0
    emit(doc, art, spin, cyc, th, T0, pre, pieces)

    # thin the vertex keys, but keep the edge of every rest exact so a shut lid lies exactly on its cube
    phase0 = 192 - 1 - T0
    pkey = {k: [tuple(round(v, 9) for v in p.values()) for p in ps] for k, ps in poses.items()}
    edges = set()
    for k, keys_ in pkey.items():
        for g in range(Lc + 1):
            prev_same = g > 0 and keys_[g] == keys_[g - 1]
            next_same = g < Lc and keys_[g] == keys_[g + 1]
            if (next_same and not prev_same) or (prev_same and not next_same):
                edges.add(g)
    protect_loop = {(g - phase0) % Lc + j for g in edges for j in (0, Lc) if (g - phase0) % Lc + j <= Lc}
    protect_intro = {T0 + g for g in edges if T0 + g < 192}
    wl, wi = {}, {}
    for oid, prop, fn, _own in pieces:
        if prop in ("x", "y"):
            wl[(oid, prop)] = {k: fn((phase0 + k) % Lc) for k in protect_loop}
            wi[(oid, prop)] = {f: fn(f - T0) for f in protect_intro}
    c3.ensure_keys(doc, f"{ROOM} Loop", wl)
    c3.ensure_keys(doc, f"{ROOM} Intro", wi)
    ball_thinned = 0                                 # the ball's spin and sideways travel are straight lines in a flight: a key a frame is not needed
    for an in ("Intro", "Loop"):
        ball_thinned += c3.thin_keys(doc, f"{ROOM} {an}", [spin], tol=0.003, props=("rotation",))
        ball_thinned += c3.thin_keys(doc, f"{ROOM} {an}", [art.id], tol=0.1, props=("x",))
    thinned = c3.thin_keys(doc, f"{ROOM} Intro", vertex_ids, protect=protect_intro) + c3.thin_keys(doc, f"{ROOM} Loop", vertex_ids, protect=protect_loop)

    # a shut lid is exactly its cube's still top: read the keys back and compare, on every frame it rests shut
    flush, flush_at = 0.0, None
    lid_faces = [f for grp in faces.values() for f in grp if getattr(f, "part", None) == "lid" and not f.flip]
    ids_ = [vid for f in lid_faces for vid in f.shapes[0][1]]
    series = [(c3.key_values(doc, f"{ROOM} Loop", ids_), lambda g: (g - phase0) % Lc, Lc),
              (c3.key_values(doc, f"{ROOM} Intro", ids_), lambda g: T0 + g, 191)]
    for f in lid_faces:
        ps = poses[key_of[f.cube]]
        shut = [g for g in range(1, Lc) if ps[g] == ps[g - 1] == ps[g + 1] and ps[g]["lid"] == 0]
        for g in shut:
            ref = f.cube.quad(f.face, None, ps[g])
            for rows, frame_of, last in series:
                for fr in {frame_of(g), frame_of(g) + (Lc if frame_of(g) == (g - phase0) % Lc else 0)}:
                    if fr > last:
                        continue
                    for vid, (rx, ry) in zip(f.shapes[0][1], ref):
                        for prop, ref_v in (("x", rx), ("y", ry)):
                            r_ = rows.get((vid, prop))
                            if r_ is not None:
                                d_ = abs(c3.value_at(r_, fr) - ref_v) * K
                                if d_ > flush:
                                    flush, flush_at = d_, (f.name, g, fr, prop)
    assert flush < 0.05, ("a shut lid is not flush with its cube", flush, flush_at)

    # ---------------------------------------------------------------- the report
    sec = lambda g: f"{(T0 + g) / 60:.2f}"
    table = "\n".join(f"  {sec(a):>6}-{sec(b):<6} {k:4s} {t}" for a, b, k, t in log)
    move_frames = sum(b - a for a, b, k, _ in log if k == "move")
    rest_frames = sum(b - a for a, b, k, _ in log if k == "rest")
    flights = "; ".join(f"{lab} {sec(a)}-{sec(b)} s apex y {apex:.0f} (ball top {apex - R_BALL:.0f}) v ({vv[0]:.2f}, {vv[1]:.2f})" for lab, a, b, apex, vv in P.notes)
    return (f"{ROOM}: loop {Lc / 60:.2f} s ({Lc} frames), loop starts at 3.20 s; moves {move_frames / Lc:.0%}, rests and pauses {rest_frames / Lc:.0%}"
            f" (on {nothing_moves / Lc:.0%} of the frames nothing at all moves)\n{table}\n"
            f"  3D cubes (perspective {c3.PERSPECTIVE}, rest pose within {worst:.3f} of the drawing), {moving_tracks} vertex tracks keyed "
            f"({thinned} keys thinned, {ball_thinned} on the ball); shut lids flush within {flush:.3f} px\n"
            f"  flights: {flights}\n"
            f"  hop onto F lands at speed {v_in:.1f} (vy {vy_land:.1f}); fling leaves F at {v_out:.1f} (vx {vx_f2:.1f}, vy {vy_f:.1f}), lands at vy {vy_fl:.1f}\n"
            f"  ball top {ball_top:.0f}, pieces top {piece_top:.0f}; longest hidden {longest} frames ({longest / 60:.2f} s)")
