"""Spelling Bee, "the honeycomb raft" (Demetre's brief, 2026-11-04): a 9 to 10 s loop in the middle of the phone frame.

The pieces: the #1 mug on its coaster, the upright hex block above it (Right Hex, 9:553), the flat floating hex on the left, the lily pad
(Left Hex, 9:504), and the coaster's big front hex on the floor, the raft (9:683, in the group 9:682). Everything stays between x 560
and 935; the ball never uses the brick stacks and never touches the pink floor. Every flight falls at 0.40 and is a whole-frame parabola.

  1  the pop: the mug squashes (height 98 percent, width 101, 0.12 s, planted on the coaster), springs back as the ball leaves
     (one overshoot of 0.9 percent, 0.2 s); the ball hops out of the mug and lands on the block's top, with three small bounces
  2  about 0.2 s after the landing the plate on the block's face turns once like a coin (a 2D squeeze, width |cos t|, 0.6 s, eased)
     with the dark hollow showing behind it
  3  the ball hops up and left over the gap and lands on the lily pad (the pad dips 3.6 px, tilts 1.6 degrees, settles with one overshoot)
  4  the raft lifts out of the comb over 1 s and hovers just below the pad, bobbing 1.4 px
  5  the ball hops off the pad's right edge onto the raft (the raft dips 2.6 px); as it leaves the pad turns 60 degrees in its plane
  6  idle: the raft drifts right (and a little up, to the mug's rim) over 2.8 s; the ball sways on it, glances at the mug and hops once
  7  the block rolls one 60 degree facet (a hexagonal prism turning about its axis)
  8  at the mug the raft tilts 7.5 degrees, the ball rolls off its right corner and drops into the mug (the mug wobbles 1.5 degrees)
  9  hidden in the mug, the ball waits while the raft floats back down into the coaster (0.9 s)
"""
import math

from bee_art import (D, FRONT_C, build_block, block_values, pad_matrix, rot, turn_in_plane)
from common import BallArt, Cycle, dip, emit, intro_series, plane_x, prepare_ball, smooth
from rml_edit import num

ROOM = "Spelling Bee"
T0 = 110                                   # 1.83 s: the mug landed at 1.50 s and its squash is over at 1.82 s
G = 0.40
IN_MUG = (807.0, 710.0)                    # low in the mug, wholly behind its front wall
HIDE_Y = 699.0                             # a centre below this is wholly behind the mug's front wall (its top is under the lip, y 675)
MUG_PIVOT = (747.501, 575.111)
MUG_BASE = (807.25, 738.0)                 # the mug's base centre, where it stays planted
PAD_O = (627.625, 658.929)                 # the lily pad's node
RAFT_O = (705.25, 756.321)                 # the raft's node (centre of its top face is 7.5 above)
FACE_DY = -7.5
BLOCK_TOP, PAD_TOP = 553.8, 595.2
RIM_L, RIM_R = (768.5, 663.0), (846.0, 663.0)
PAD_OUTLINE = [(590.5, 595.2), (641.8, 595.2), (674.5, 627.1), (664.7, 658.9), (613.4, 658.9)]

# the schedule, in cycle frames (the cycle starts with the mug's squash; the ball leaves at GO)
GO = 7
X_BLOCK = 796.0                            # where it lands on the block's top
N1 = 46                                    # the pop's flight
BOUNCES = (21, 17, 14)                     # the small bounces on the block's top (flight times)
C_SPIN = 12                                # the plate's turn starts this long after the landing (0.2 s)
SPIN_N = 36                                # 0.6 s
C_GO2 = 128                                # the hop to the pad (after the plate's turn and a calm beat)
N2 = 34                                    # a flatter, quicker arc: it arrives at 8.9 px/frame and ricochets
PAD_FACE = (640.0, 600.0)                  # where on the pad's face it hits
PAD_NORMAL = (0.348, -0.937)               # the face's lean (20 degrees from flat, tipped up to the right: its dark rim shows on the left)
PAD_E, PAD_KT = 0.82, 0.90                 # the hit keeps 82 percent of the speed along the normal and 90 percent along the face
C_RISE, RISE_N = 106, 66                   # the raft lifts out of the comb (1.1 s) after a 1.5 px press down just before
RAFT_X0 = 696.0                            # the raft's face centre when it hovers (its left corner stays clear of the brick stack)
RAFT_SLIDE = (1.0, 0.6, 0.3, 0.1)
PAD_TURN_N = 48                            # 0.8 s, from the hit
C_SWAY, SWAY_P, SWAY_A = 236, 108, 2.6     # two sways on the raft
C_GLANCE = 270
GLANCE = math.radians(24)
C_BLOCK, BLOCK_N = 350, 30                 # 0.5 s
C_HOP, HOP_V = 410, 2.4                    # the happy hop: 7.2 px high, 12 frames
TILT = math.radians(7.5)
TILT_N = 18
LEAVE_S = 67.5                             # the raft's right corner, from the face centre
DESCENT_N = 54
H0, DH, DX_D = 62.3, 25.7, 24.0            # the raft hovers 62.3 above its place, then drifts 24 right and 25.7 up
DX0 = RAFT_X0 - 705.25                     # the raft's hover, left of its place by 9.25
DRIFT = 2.8

ease = lambda u: 0.0 if u <= 0 else 1.0 if u >= 1 else (4 * u ** 3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2)
sine = lambda u: 0.0 if u <= 0 else 1.0 if u >= 1 else 0.5 - 0.5 * math.cos(math.pi * u)


def settle(u, A, T=24, ov=0.22):
    """A dip of depth A under an impact (down first), one small overshoot back the other way, still at T."""
    if u <= 0 or u >= T:
        return 0.0
    T1 = 0.55 * T
    return A * math.sin(math.pi * u / T1) if u < T1 else -ov * A * math.sin(math.pi * (u - T1) / (T - T1))


class Pad:
    def __init__(self, land):
        self.land = land

    def dy(self, c):
        return settle(c - self.land, 3.6)

    def rot(self, c):
        return settle(c - self.land, math.radians(1.6))

    def at(self, c, local):
        r = rot(self.rot(c), local)
        return (PAD_O[0] + r[0], PAD_O[1] + self.dy(c) + r[1])


class Raft:
    """The raft's offset from its place in the coaster (dx, dy), its tilt, frame by frame.

    The lift: a 1.5 px press down (anticipation), then an ease-out lift (quick off the comb, decelerating into the hover), one overshoot of
    3 px that settles over 28 frames, a 1.8 degree tilt that rises and falls with the lift, then the bob and the drift as single
    smooth-in-out moves. Landings dip it; the descent eases in and out and settles 1.2 px into the comb."""

    def __init__(self, land3, hop_land, drift0, drift1, tilt0):
        self.land3, self.hop_land, self.drift0, self.drift1, self.tilt0 = land3, hop_land, drift0, drift1, tilt0
        self.dn0 = 10 ** 9

    def down(self, c):
        return ease((c - self.dn0) / DESCENT_N)

    @staticmethod
    def lift(c):
        u = (c - C_RISE) / RISE_N
        if u <= 0:
            return 0.0
        if u >= 1:
            return 1.0
        x = u ** 0.7                         # quick off the comb, then decelerating to a stop
        return x * x * (3 - 2 * x)

    def offset(self, c):
        lift, drift = self.lift(c), sine((c - self.drift0) / (self.drift1 - self.drift0))
        k = 1 - self.down(c)
        dx = (DX0 * lift + DX_D * drift) * k
        dy = (-H0 * lift - DH * drift) * k
        if C_RISE - 10 < c < C_RISE:
            dy += 1.5 * math.sin(math.pi * (c - C_RISE + 10) / 10) ** 2
        v = (c - C_RISE - RISE_N) / 28
        if 0 < v < 1:
            dy -= 3.0 * math.sin(math.pi * v) ** 2
        env = smooth((c - (C_RISE + RISE_N + 28)) / 30) * (1 - smooth((c - (self.tilt0 - 10)) / 10)) * k
        dy += 1.4 * env * math.sin(2 * math.pi * (c - C_RISE - RISE_N - 28) / 140)
        dy += settle(c - self.land3, 2.6) + settle(c - self.hop_land, 0.9, 18) + settle(c - self.dn0 - DESCENT_N, 1.2, 16)
        return dx, dy

    def tilt(self, c):
        u = (c - C_RISE) / (RISE_N + 8)
        lt = math.radians(1.8) * math.sin(math.pi * u) ** 2 if 0 < u < 1 else 0.0
        return (lt + TILT * ease((c - self.tilt0) / TILT_N)) * (1 - self.down(c))

    def ball(self, c, s, lift=0.0, rc=23.22):
        dx, dy = self.offset(c)
        r = rot(self.tilt(c), (s, FACE_DY - rc - lift))
        return (RAFT_O[0] + dx + r[0], RAFT_O[1] + dy + r[1])


def seg_dist(p, a, b):
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)


def mug_pose(c, c_catch):
    """The mug's squash (scaleY, scaleX) and wobble (rotation), and the node position that keeps its base planted."""
    if c < 0:
        sy = 1.0
    elif c <= 7:
        sy = 1 - 0.02 * smooth(c / 7)
    elif c <= 19:
        u = (c - 7) / 12
        sy = 0.98 + 0.029 * smooth(u / 0.55) if u < 0.55 else 1.009 - 0.009 * smooth((u - 0.55) / 0.45)
    else:
        sy = 1.0
    sx = 1 - 0.5 * (sy - 1)
    rho = dip(c - c_catch, math.radians(1.5), 24)
    bx, by = MUG_BASE[0] - MUG_PIVOT[0], MUG_BASE[1] - MUG_PIVOT[1]
    r = rot(rho, (sx * bx, sy * by))
    return sx, sy, rho, (MUG_BASE[0] - r[0], MUG_BASE[1] - r[1])


def hold_key(doc, anim, oid, prop, frame):
    """Make the key at `frame` of oid's prop a hold (it stays until the next key), so a corner relabelling is one frame, never a blend."""
    a, b = doc.anim(anim)
    pat = f'objectId="{oid}"'
    for i in range(a, b):
        if pat in doc.lines[i] and "<KeyedObject" in doc.lines[i]:
            e = doc.end(i)
            for j in range(i, e):
                if f'property="{prop}"' in doc.lines[j]:
                    for m in range(j, doc.end(j)):
                        if f' frame="{frame}"' in doc.lines[m]:
                            doc.lines[m] = doc.lines[m].replace(' interpolationType="linear"', "")
                            return True
            return False
    return False


def build(doc, scene, sheet):
    art = BallArt(scene, ROOM)
    spin = prepare_ball(doc, art)
    for oid in ("9:506", "9:467"):        # the old loop's hex drifts
        doc.drop_object(f"{ROOM} Loop", oid)
    RC, R = art.Rc, art.R
    BT, PT = BLOCK_TOP - RC, PAD_TOP - RC

    # ------------------------------------------------------------------ the ball
    pos, w, contacts, notes = [IN_MUG], [], [], {}

    def add(p, wv=0.0):
        pos.append(p)
        w.append(wv)

    def now():
        return len(pos) - 1

    while now() < GO:
        add(IN_MUG)
    x0, y0 = IN_MUG
    vx = (X_BLOCK - x0) / N1
    vy = (BT - y0 - 0.2 * N1 ** 2) / N1
    for t in range(1, N1 + 1):
        add((x0 + vx * t, y0 + vy * t + 0.2 * t * t), 0.25 * vx / R)
    c_land1 = now()
    contacts.append(("the block's top", c_land1, abs(vy + G * N1)))
    for T in BOUNCES:
        vb = -0.2 * T
        for t in range(1, T + 1):
            add((X_BLOCK, BT + vb * t + 0.2 * t * t))
        contacts.append(("the block's top", now(), abs(vb)))
    while now() < C_GO2:
        add((X_BLOCK, BT))
    # the hop to the pad: a quick shallow arc down onto its angled face, where it ricochets towards the raft
    nl = math.hypot(*PAD_NORMAL)
    nrm = (PAD_NORMAL[0] / nl, PAD_NORMAL[1] / nl)
    PC = (PAD_FACE[0] + RC * nrm[0], PAD_FACE[1] + RC * nrm[1])
    vx2 = (PC[0] - X_BLOCK) / N2
    vy2 = (PC[1] - BT - 0.2 * N2 ** 2) / N2
    for t in range(1, N2 + 1):
        add((X_BLOCK + vx2 * t, BT + vy2 * t + 0.2 * t * t), 0.25 * vx2 / R)
    c_b = now()
    v_in = (vx2, vy2 + 0.4 * N2 - 0.2)
    vn = v_in[0] * nrm[0] + v_in[1] * nrm[1]
    assert vn < 0
    vt = (v_in[0] - vn * nrm[0], v_in[1] - vn * nrm[1])
    out = (PAD_KT * vt[0] - PAD_E * vn * nrm[0], PAD_KT * vt[1] - PAD_E * vn * nrm[1])
    contacts.append(("the lily pad", c_b, math.hypot(*v_in)))
    pad = Pad(c_b)
    # the raft, so far as the landing needs it
    c_hop_land = C_HOP + 12
    c_t0 = C_SWAY + 2 * SWAY_P
    raft = Raft(0, c_hop_land, c_t0 + 18 - 175, c_t0 + 18, c_t0)
    best = None
    for T in range(10, 90):
        ty = raft.ball(c_b + T, 0.0, rc=RC)[1]
        y = PC[1] + out[1] * T + 0.2 * T * T
        if T > 15 and y >= ty:
            best = min([T - 1, T], key=lambda q: abs(PC[1] + out[1] * q + 0.2 * q * q - raft.ball(c_b + q, 0.0, rc=RC)[1]))
            break
    N3 = best
    c_land3 = c_b + N3
    raft.land3 = c_land3
    ty = raft.ball(c_land3, 0.0, rc=RC)[1]
    oy = (ty - PC[1] - 0.2 * N3 ** 2) / N3
    ox = out[0]
    ratio = math.hypot(ox, oy) / math.hypot(*v_in)
    assert 0.72 <= ratio <= 0.9, ("the ricochet keeps", ratio)
    S_LAND = PC[0] + ox * N3 - RAFT_X0
    assert 0 <= S_LAND <= 45, ("lands off the raft's face", S_LAND)
    for t in range(1, N3 + 1):
        add((PC[0] + ox * t, PC[1] + oy * t + 0.2 * t * t), 0.25 * ox / R)
    contacts.append(("the raft", c_land3, math.hypot(ox, oy + G * N3)))
    apex = PC[1] - oy * oy / 0.8
    s = S_LAND
    for d in RAFT_SLIDE:
        s += d
        add(raft.ball(now() + 1, s, rc=RC), d / R)
    s_rest = s
    sway = lambda c: SWAY_A * math.sin(2 * math.pi * (c - C_SWAY) / SWAY_P) if C_SWAY <= c <= c_t0 else 0.0
    s_prev = s_rest
    while now() < c_t0:
        c = now() + 1
        s_c = s_rest + sway(c)
        t = c - C_HOP
        if 0 < t < 12:                                     # the happy hop: 7.2 px high, in the air, the ball not rolling
            add(raft.ball(c, s_c, lift=HOP_V * t - 0.2 * t * t, rc=RC), 0.0)
        else:
            add(raft.ball(c, s_c, rc=RC), (s_c - s_prev) / R)
        s_prev = s_c
    # the tilt: it rolls down the raft's face, accelerating by gravity times the sine of the slope, off its right corner
    v_s = 0.0
    s_cur = s_rest
    c_lv = None
    while True:
        c = now() + 1
        v_s += G * math.sin(raft.tilt(c))
        if s_cur + v_s >= LEAVE_S:
            add(raft.ball(c, LEAVE_S, rc=RC), (LEAVE_S - s_cur) / R)
            c_lv = c
            break
        s_cur += v_s
        add(raft.ball(c, s_cur, rc=RC), v_s / R)
    p_a, p_b = pos[-2], pos[-1]
    ux, uy = p_b[0] - p_a[0], p_b[1] - p_a[1]
    uy_ = uy + 0.2
    t = 0
    w_air = v_s / R
    c_catch = None
    rim_min = 1e9
    cross = None
    while True:
        t += 1
        p = (p_b[0] + ux * t, p_b[1] + uy_ * t + 0.2 * t * t)
        add(p, w_air)
        rim_min = min(rim_min, math.hypot(p[0] - RIM_L[0], p[1] - RIM_L[1]), math.hypot(p[0] - RIM_R[0], p[1] - RIM_R[1]))
        if c_catch is None and p[1] >= 668:
            c_catch = now()
            cross = p
        if p[1] >= HIDE_Y:
            break
    c_hid = now()
    assert rim_min >= RC + 1, ("the ball touches the mug's rim", rim_min)
    assert 793 <= cross[0] <= 821, ("the ball misses the mug's opening", cross)
    # hidden in the mug: it keeps falling to the bottom, the mug catches it, then it settles back to its starting place
    vxh = pos[-1][0] - pos[-2][0]
    vyh = pos[-1][1] - pos[-2][1]
    hx, hy = pos[-1]
    while hy < IN_MUG[1]:
        vyh += G
        hx = min(820.0, max(796.0, hx + vxh))
        vxh *= 0.8
        hy = min(IN_MUG[1], hy + vyh)
        add((hx, hy), 0.0)
    f_bottom = now()
    for k in range(1, 13):
        add((hx + (IN_MUG[0] - hx) * smooth(k / 12), IN_MUG[1]), 0.0)
    # the raft floats back down while it is hidden
    raft.dn0 = c_catch + 6
    c_dn1 = raft.dn0 + DESCENT_N
    L = max(c_dn1 + 16, now()) + 8
    while now() < L:
        add(IN_MUG)
    assert now() == L and 540 <= L <= 600, L

    # the turn: the sum of the ball's own rolling and spin, closed to a whole number of turns while it is hidden
    th = [0.0]
    for g in range(L):
        th.append(th[-1] + w[g])
    total = th[L]
    want = round(total / (2 * math.pi)) * 2 * math.pi
    for g in range(f_bottom, L + 1):
        th[g] += (want - total) * min(1.0, (g - f_bottom) / 20)
    glance = lambda c: GLANCE * (ease((c - C_GLANCE) / 12) - ease((c - C_GLANCE - 42) / 12))
    th = [th[g] + glance(g) for g in range(L + 1)]

    cyc = Cycle(L)
    for g in range(L + 1):
        cyc.put(g, pos[g], "air")
    for name, c, vin in contacts:
        cyc.squash(c, min(0.13, 0.011 * vin + 0.005), T=12)
    cyc.squash(C_GO2 - 8, 0.06, T=8)           # the wind-ups

    # ------------------------------------------------------------------ the pieces' keys
    def ser(fn):
        a = [fn(g) for g in range(L + 1)]
        assert abs(a[0] - a[L]) < 1e-6
        return lambda g, a=a: a[g]
    pieces = []
    pose = [mug_pose(g, c_catch) for g in range(L + 1)]
    for mug in ("9:463", "9:465"):
        pieces.append((mug, "x", ser(lambda g: pose[g][3][0]), None))
        pieces.append((mug, "y", ser(lambda g: pose[g][3][1]), intro_series(scene, sheet, ROOM, mug, "y")))
        pieces.append((mug, "scaleX", ser(lambda g: pose[g][0]), intro_series(scene, sheet, ROOM, mug, "scaleX")))
        pieces.append((mug, "scaleY", ser(lambda g: pose[g][1]), intro_series(scene, sheet, ROOM, mug, "scaleY")))
        pieces.append((mug, "rotation", ser(lambda g: pose[g][2]), None))
    pieces.append(("9:504", "y", ser(lambda g: PAD_O[1] + pad.dy(g)), intro_series(scene, sheet, ROOM, "9:504", "y")))
    pieces.append(("9:504", "rotation", ser(lambda g: pad.rot(g)), None))
    ro = [raft.offset(g) for g in range(L + 1)]
    rt = [raft.tilt(g) for g in range(L + 1)]
    pieces.append(("9:683", "x", ser(lambda g: 68.25 + ro[g][0]), None))
    pieces.append(("9:683", "y", ser(lambda g: 101.821 + ro[g][1]), None))
    pieces.append(("9:683", "rotation", ser(lambda g: rt[g]), None))

    # the lily pad's hexagons, turned in their plane (the face and its inner plate, and the dark back face)
    by_id = {e.get("id"): e for e in scene.root.iter() if e.get("id")}
    corners = lambda sid: [(v.get("id"), (float(v.get("x", 0)), float(v.get("y", 0)))) for v in by_id[sid].find("PointsPath")]
    big = corners("9:480")
    M = pad_matrix(big[-1][1], big[-2][1])             # path order is corners 5,4,3,2,1,0
    c_pt0 = c_b
    def pad_angle(c):
        return math.pi / 3 * ease((c - c_pt0) / PAD_TURN_N) if c <= c_pt0 + PAD_TURN_N else 0.0      # one frame after the turn the corners are back
    holds = []
    for sid in ("9:468", "9:480", "9:492"):
        cs = corners(sid)
        n = len(cs)
        for p in [turn_in_plane(M, math.pi / 3, q) for _, q in cs]:   # at 60 degrees each corner sits on another one's place
            assert min(math.hypot(p[0] - r[1][0], p[1] - r[1][1]) for r in cs) < 0.01, ("pad corner", sid)
        for i, (vid, p) in enumerate(cs):
            for k, prop in enumerate(("x", "y")):
                pieces.append((vid, prop, ser(lambda g, p=p, k=k: turn_in_plane(M, pad_angle(g), p)[k]), None))
                holds.append((vid, prop, c_pt0 + PAD_TURN_N))

    # the upright block: its plate's turn, and the roll of the hexagonal prism
    ids = build_block(doc, "9:506", ["9:507", "9:519", "9:529", "9:541"], ROOM)
    c_ps0 = c_land1 + C_SPIN
    sw = lambda c: max(0.07, abs(math.cos(math.pi * ease((c - c_ps0) / SPIN_N))))
    pieces.append((ids["spin"], "scaleX", ser(sw), None))
    block_angle = lambda c: math.pi / 3 * ease((c - C_BLOCK) / BLOCK_N) if c <= C_BLOCK + BLOCK_N else 0.0
    cache = {}
    def bv(c):
        t = block_angle(c)
        if t not in cache:
            cache[t] = block_values(t)
        return cache[t]
    for key in bv(0):
        if key[0] in ("ring", "plate", "hollow"):
            oid, prop = ids[key[0]][key[1]], key[2]
        elif key[0] == "quad":
            _, k, light, n, prop = key
            oid = ids["quads"][k][3 if light else 2][n]
        else:
            _, k, light = key
            oid, prop = ids["quads"][k][1 if light else 0], "opacity"
        pieces.append((oid, prop, ser(lambda g, key=key: bv(g)[key]), None))
        holds.append((oid, prop, C_BLOCK + BLOCK_N))

    def pre(f):
        px = plane_x(scene, sheet, ROOM, "Front")
        my = intro_series(scene, sheet, ROOM, "9:463", "y")
        msx = intro_series(scene, sheet, ROOM, "9:463", "scaleX")
        msy = intro_series(scene, sheet, ROOM, "9:463", "scaleY")
        dy = my(f) - MUG_PIVOT[1]
        return ((MUG_PIVOT[0] + msx(f) * (IN_MUG[0] - MUG_PIVOT[0]) + px(f), MUG_PIVOT[1] + dy + msy(f) * (IN_MUG[1] - MUG_PIVOT[1])), 1.0, 1.0)

    emit(doc, art, spin, cyc, th, T0, pre, pieces)

    # the corners go back to where they were in one frame (a hold, never a blend), in the loop (and the intro, were the turn there)
    phase0 = 192 - 1 - T0
    for oid, prop, cf in holds:
        k = (cf - phase0) % L
        hold_key(doc, f"{ROOM} Loop", oid, prop, k)
        if T0 + cf < 192:
            hold_key(doc, f"{ROOM} Intro", oid, prop, T0 + cf)

    # the checks that no frame jumps further than its speed explains
    bad = []
    near = {c + d for _, c, _ in contacts for d in (-1, 0, 1, 2)} | {c_lv, c_lv + 1, GO, GO + 1, C_GO2, C_GO2 + 1,
                                                                    C_HOP, C_HOP + 1, C_HOP + 2, C_HOP + 12, C_HOP + 13, f_bottom, f_bottom + 1}
    for g in range(2, L):
        if g in near or g > c_hid:
            continue
        a = (pos[g][0] - 2 * pos[g - 1][0] + pos[g - 2][0], pos[g][1] - 2 * pos[g - 1][1] + pos[g - 2][1])
        if math.hypot(*a) > 0.9:
            bad.append((g, round(math.hypot(*a), 2)))
    assert not bad, ("the ball jumps", bad[:6])

    sec = lambda g: f"{(T0 + g) / 60:.2f} s"
    return (f"{ROOM}: squash {sec(0)}, out {sec(GO)}, block {sec(c_land1)} (bounces to {sec(contacts[3][1])}), plate turns {sec(c_ps0)}, "
            f"pad ricochet {sec(c_b)} (keeps {ratio:.0%}, apex y {apex:.0f}), raft rises {sec(C_RISE)}, raft {sec(c_land3)}, pad turns {sec(c_pt0)}, glance {sec(C_GLANCE)}, block rolls {sec(C_BLOCK)}, "
            f"hop {sec(C_HOP)}, tilt {sec(c_t0)}, off the raft {sec(c_lv)}, mug {sec(c_catch)} (rim clearance {rim_min:.1f}, crosses at x {cross[0]:.0f}), "
            f"raft down {sec(c_dn1)}; loop {L / 60:.2f} s ({L} frames)")
