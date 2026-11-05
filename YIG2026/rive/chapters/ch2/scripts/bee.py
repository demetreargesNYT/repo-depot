"""Spelling Bee, "the fidget toy" (Demetre's brief, 2026-11-04): about 13 s, all in the middle of the phone frame, around the mug,
the upright hex block (Right Hex, 9:553) and the coaster. The lily pad (Left Hex) and the coaster's big hex keep their drawing: the
ball never uses the pad, and the big hex never moves.

  1  the pop: the mug squashes a hair (98 percent tall, 101 wide, 0.12 s, planted on its base) and springs back with one overshoot
     under 1 percent as the ball leaves; the ball hops out and lands on the block's top (landing squash), rolling on a touch
  2  curious: 0.2 s after the landing the block's inner plate turns once like a coin (width |cos t|, 0.6 s, eased, the dark hollow
     behind it); the ball rolls a touch so its dot looks down at it, and holds
  3  eager: three quick little hops in place, each with a small gather; the plate flips on each landing, a little faster each time
  4  showing off: a deeper gather and a slight lean, one bigger hop, a proud landing; the plate spins like a top, slowing to a stop on
     its starting face, while the ball watches with a faint, eased roll
  5  bounce down: the ball hops down onto the coaster's big hex and bounces off it (keeping about 75 to 80 percent), up and left into the lily
     pad's lower right face (drawn at 107 degrees), which knocks it back up and right (88 percent kept); the pad gives a little
  6  home: that ricochet carries it in front of the block's lower-left corner (overlapping it: depth) and over the mug's left rim; it
     drops in (the hidden reset), and the mug gives one small proud wobble

One gravity (0.40), every flight a whole-frame parabola. Squash and stretch about the ball's bottom (Ball_01_Scale), volume constant;
a lean is a turn of Ball_01_Scale about the contact point, with the spin pivot turned back by the same angle so the dot only turns with
the ball's travel. The block and the lily pad are behind the ball in depth (it passes in front of their faces); the paths still keep
clear of their outlines, and of the mug's rim.
"""
import math

from bee_art import BLOCK_C, add_plate_spin, block_outline
from common import BallArt, Cycle, dip, emit, intro_series, plane_x, prepare_ball, smooth

ROOM = "Spelling Bee"
T0 = 110                                   # 1.83 s: the mug landed at 1.50 s and its squash is over at 1.82 s
G = 0.40
IN_MUG = (807.0, 710.0)                    # low in the mug, wholly behind its front wall
HIDE_Y = 699.0                             # a centre below this is wholly behind the mug's front wall
MUG_PIVOT = (747.501, 575.111)
MUG_BASE = (807.25, 738.0)                 # the mug's base centre, where it stays planted
BLOCK_TOP = 553.75                         # the block's top: the line y 553.75 from x 774 to 846.6
FACE_Y = 743.0                             # where the ball touches the coaster's big hex (its face spans x 646 to 765 at this depth)
PAD = [(641.83, 595.25), (599.38, 595.25), (589.6, 627.09), (622.26, 658.93), (664.72, 658.93), (674.5, 627.09)]
RIM = [(767.25, 669.54)] + [(767.25, float(y)) for y in range(672, 740, 4)] + [(846.0, 663.0), (847.25, 669.54)]
COPY_Y = 425.0                             # the ball's top stays at or below this

# the schedule, in cycle frames (the cycle starts with the gather in the mug; the ball leaves at GO)
GO, N1, X_BLOCK = 9, 46, 788.0             # the pop: 46 frames to the block's top
SETTLE1 = 16
FLIP1_AT, FLIP1 = 12, 36                   # 0.2 s after the landing; 0.6 s
GLANCE_AT, GLANCE_N, GLANCE_DX, GLANCE_HOLD = 17, 16, 10.0, 30
HOPS = [(0.35, 17, 28), (-0.40, 16, 24), (0.35, 15, 20)]   # (vx, flight frames, the flip's frames on its landing)
HOP_DWELL = 20                             # landing to the next launch: the landing squash (12), then the gather (8)
CALM1, CALM1_DX = 60, -3.0                 # after the hops: a faint roll back
BIG_GATHER, BIG_VX, BIG_T, BIG_LEAN = 18, -0.25, 36, math.radians(-3.0)
TOP_AT, TOP_N, TOP_TURNS = 2, 150, 8       # the top spin: 8 half turns (4 whole) over 2.5 s, slowing to a stop
WATCH_AT, WATCH_N, WATCH_DX = 22, 134, 5.0     # it watches until the top has stopped
CALM2, CALM2_DX = 56, -5.0
DOWN_GATHER = 9
PAD_FACES = {"the lily pad's upper right slant": (PAD[0], PAD[5]), "the lily pad's lower right face": (PAD[5], PAD[4]),
             "the lily pad's bottom": (PAD[4], PAD[3])}
PAD_NODE = (627.625, 658.929)              # the lily pad's node (it turns about it)
PAD_GIVE, PAD_TILT = 3.2, math.radians(1.6)   # how far the hit pushes the pad (along the hit), and its tilt
HOME_BEAT = 84                             # hidden in the mug after the catch before the loop starts again

# squash and stretch (maximums from CLAUDE.md: gather 5, landing 6, big landing 8, flight stretch 3 on the fastest moves only)
SQ = dict(mug_gather=0.04, land1=0.05, hop_gather=0.02, hop_land=0.03, big_gather=0.045, proud=0.075, down_gather=0.03,
          coaster=0.06, pad_hit=0.03)

ease = lambda u: 0.0 if u <= 0 else 1.0 if u >= 1 else (4 * u ** 3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2)
sine = lambda u: 0.0 if u <= 0 else 1.0 if u >= 1 else 0.5 - 0.5 * math.cos(math.pi * u)


def seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy)))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def poly_segs(pts):
    return [(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))]


BLOCK_SEGS, PAD_SEGS = poly_segs(block_outline()), poly_segs(PAD)


def clearance(p, block=True, pad=True, rim=True):
    d = [99.0]
    if block:
        d += [seg_dist(p, a, b) for a, b in BLOCK_SEGS]
    if pad:
        d += [seg_dist(p, a, b) for a, b in PAD_SEGS]
    if rim:
        d += [math.dist(p, q) for q in RIM]
    return min(d)


class Track:
    """The ball's centre frame by frame, and the turn from each frame to the next."""

    def __init__(self, p0, R):
        self.pos, self.w, self.R = [p0], [], R
        self.flights, self.landings = [], []        # (launch, T, vx, vy0); (frame, kind, speed in)

    @property
    def f(self):
        return len(self.pos) - 1

    def put(self, p, w):
        self.pos.append(p)
        self.w.append(w)

    def still(self, n):
        for _ in range(n):
            self.put(self.pos[-1], 0.0)

    def roll_sine(self, dx, n):
        """A faint, eased roll along the surface it is on (in and out), turning with the distance."""
        x0, y = self.pos[-1]
        prev = x0
        for t in range(1, n + 1):
            x = x0 + dx * sine(t / n)
            self.put((x, y), (x - prev) / self.R)
            prev = x

    def roll_out(self, v0, n):
        """Rolling on from a landing at the speed it kept sideways, easing to a stop over n frames."""
        x0, y = self.pos[-1]
        prev = x0
        for t in range(1, n + 1):
            x = x0 + v0 * t - v0 * t * t / (2 * n)
            self.put((x, y), (x - prev) / self.R)
            prev = x

    def hop(self, vx, T, y1, kind, w_air=None, vy0=None):
        x0, y0 = self.pos[-1]
        if vy0 is None:
            vy0 = (y1 - y0 - 0.2 * T * T) / T
        w = self.w[-1] if w_air is None and self.w else (w_air or 0.0)
        launch = self.f
        for t in range(1, T + 1):
            self.put((x0 + vx * t, y0 + vy0 * t + 0.2 * t * t), w)
        self.flights.append((launch, T, vx, vy0))
        vin = math.hypot(vx, vy0 + 0.2 * (2 * T - 1))
        self.landings.append((self.f, kind, vin))
        return launch, self.f


def land_pulse(u, a, down=3, back=6, after=3, ov=0.12):
    """A landing squash: down to a, back up through 1 to one tiny overshoot (stretch) and settled, 12 frames in all."""
    if u < 0 or u > down + back + after:
        return 0.0
    if u <= down:
        return a * smooth(u / down)
    if u <= down + back:
        return a + (-ov * a - a) * smooth((u - down) / back)
    return -ov * a * (1 - smooth((u - down - back) / after))


def gather_pulse(g, start, launch, a, release=3):
    """An anticipation gather: in from `start`, held, out in the last `release` frames before the launch."""
    if g < start or g > launch:
        return 0.0
    if g >= launch - release:
        return a * (1 - smooth((g - launch + release) / release))
    return a * smooth((g - start) / max(1, launch - release - start))


def mug_pose(c, c_catch):
    """The mug's squash (sx, sy), wobble (rotation), and the node position that keeps its base planted."""
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
    c_, s_ = math.cos(rho), math.sin(rho)
    rx, ry = sx * bx, sy * by
    return sx, sy, rho, (MUG_BASE[0] - (rx * c_ - ry * s_), MUG_BASE[1] - (rx * s_ + ry * c_))


def settle(u, A, T=24, ov=0.22):
    """A give of A under a hit, one small overshoot back the other way, still at T frames (0.4 s)."""
    if u <= 0 or u >= T:
        return 0.0
    T1 = 0.55 * T
    return A * math.sin(math.pi * u / T1) if u < T1 else -ov * A * math.sin(math.pi * (u - T1) / (T - T1))


def first_pad_hit(p, v, Rc, tmax=70.0):
    """The first contact of a flight (from p with velocity v) with the lily pad's right-hand faces: (time, centre, face, normal),
    or None if it misses them or meets a corner instead of a face."""
    t, step = 0.0, 0.25
    while t < tmax:
        t += step
        q = (p[0] + v[0] * t, p[1] + v[1] * t + 0.2 * t * t)
        if min(seg_dist(q, a, b) for a, b in PAD_FACES.values()) <= Rc:
            lo, hi = t - step, t
            for _ in range(40):
                m = (lo + hi) / 2
                qm = (p[0] + v[0] * m, p[1] + v[1] * m + 0.2 * m * m)
                if min(seg_dist(qm, a, b) for a, b in PAD_FACES.values()) <= Rc:
                    hi = m
                else:
                    lo = m
            qh = (p[0] + v[0] * hi, p[1] + v[1] * hi + 0.2 * hi * hi)
            name, (a, b) = min(PAD_FACES.items(), key=lambda kv: seg_dist(qh, *kv[1]))
            dx, dy = b[0] - a[0], b[1] - a[1]
            u = ((qh[0] - a[0]) * dx + (qh[1] - a[1]) * dy) / (dx * dx + dy * dy)
            if not 0.08 <= u <= 0.92:
                return None
            n = (dy / math.hypot(dx, dy), -dx / math.hypot(dx, dy))
            if (qh[0] - a[0]) * n[0] + (qh[1] - a[1]) * n[1] < 0:
                n = (-n[0], -n[1])
            return hi, qh, name, n
        if q[1] - 23.865 < COPY_Y:
            return None
    return None


def plan_bounces(x_s, BT, YC, Rc):
    """The hop down from the block (from x_s) onto the coaster's big hex, the bounce off it into the lily pad's face, and the
    ricochet from there into the mug, chosen together: the hop down keeps clear of the block's side and the pad; each contact keeps 72
    to 90 percent of its speed; the ricochet keeps clear of the pad and the mug's rim, passes in front of the block's corner clearly
    overlapping it or clearly apart (never a near-miss), crosses the rim's line inside the opening and is hidden before the far wall."""
    best = None
    for T in range(34, 56):
        for xl2 in range(1400, 1500):
            xl = xl2 / 2
            vx = (xl - x_s) / T
            vy0 = (YC - BT - 0.2 * T * T) / T
            if not -5.5 <= vy0 <= -1.5:
                continue
            c_down = 99.0
            for k in range(1, 2 * T):
                t = k / 2
                q = (x_s + vx * t, BT + vy0 * t + 0.2 * t * t)
                c_down = min(c_down, clearance(q, block=t >= 3))
            if c_down < 24.4:
                continue
            vin = (vx, vy0 + 0.2 * (2 * T - 1))
            for ec in (0.72, 0.74, 0.76, 0.78, 0.80, 0.84, 0.88):
                for ktc in (0.85, 0.92, 1.0):
                    vo = (vin[0] * ktc, -vin[1] * ec)
                    kc = math.hypot(*vo) / math.hypot(*vin)
                    if not 0.72 <= kc <= 0.9:
                        continue
                    h = first_pad_hit((xl, YC), (vo[0], vo[1] + 0.2), Rc)
                    if not h:
                        continue
                    tc, qc, face, n = h
                    vc = (vo[0], vo[1] + 0.2 + 0.4 * tc)
                    vn = vc[0] * n[0] + vc[1] * n[1]
                    if vn >= 0:
                        continue
                    vt = (vc[0] - vn * n[0], vc[1] - vn * n[1])
                    for ep in (0.75, 0.8, 0.85, 0.9):
                        for ktp in (0.85, 0.92):
                            w = (ktp * vt[0] - ep * vn * n[0], ktp * vt[1] - ep * vn * n[1])
                            kp = math.hypot(*w) / math.hypot(*vc)
                            if not 0.72 <= kp <= 0.9 or w[0] <= 0:
                                continue
                            c_rim, cross, deep, cpad, t, ok = 99.0, None, -99.0, 99.0, 0.0, True
                            while True:
                                t += 0.5
                                q = (qc[0] + w[0] * t, qc[1] + w[1] * t + 0.2 * t * t)
                                if q[1] - 23.865 < COPY_Y or t > 90:
                                    ok = False
                                    break
                                down = w[1] + 0.4 * t > 0
                                if down and q[1] >= 668 and cross is None:
                                    cross = q[0]
                                if down and q[1] >= HIDE_Y:
                                    break
                                c_rim = min(c_rim, min(math.dist(q, r) for r in RIM))
                                deep = max(deep, 23.865 - block_signed(q))
                                if t > 1.5:
                                    cpad = min(cpad, min(seg_dist(q, a, b) for a, b in PAD_FACES.values()))
                            if not ok or cross is None or not 796 <= cross <= 810 or q[0] > 818:
                                continue
                            if c_rim < 25.5 or cpad < Rc + 2 or not (deep <= -3 or OVERLAP[0] <= deep <= OVERLAP[1]):
                                continue
                            score = min(c_rim - 25.5, c_down - 24.4)
                            if best is None or score > best[0]:
                                best = (score, dict(T=T, xl=xl, vx=vx, vy0=vy0, vo=vo, kc=kc, tc=tc, qc=qc, face=face, n=n, w=w, kp=kp,
                                                    cross=cross, deep=deep, c_rim=c_rim, c_down=c_down))
    assert best, "no bounce chain from the block to the big hex, the lily pad and the mug works"
    return best[1]


OVERLAP = (9.0, 16.0)                      # how deep the ball's outline crosses into the block's corner on the way into the mug (px)


def q_top(x0, y0, vy0):
    return y0 - vy0 * vy0 / 0.8 - 23.865


def block_signed(p):
    """The distance from p to the block's outline, negative inside it."""
    d = min(seg_dist(p, a, b) for a, b in BLOCK_SEGS)
    pts = block_outline()
    inside = False
    for (x1, y1), (x2, y2) in BLOCK_SEGS:
        if (y1 > p[1]) != (y2 > p[1]) and p[0] < x1 + (p[1] - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return -d if inside else d


def build(doc, scene, sheet):
    art = BallArt(scene, ROOM)
    spin = prepare_ball(doc, art)
    for oid in ("9:506", "9:467"):        # the old loop's hex drifts
        doc.drop_object(f"{ROOM} Loop", oid)
    RC, R = art.Rc, art.R
    BT, YC = BLOCK_TOP - RC, FACE_Y - RC

    tr = Track(IN_MUG, R)
    tr.still(GO)                                          # the gather in the mug (out of sight) and the mug's squash
    go, c_land1 = tr.hop((X_BLOCK - IN_MUG[0]) / N1, N1, BT, "the block's top", w_air=0.0)
    pop_frames = range(go, c_land1)
    tr.roll_out((X_BLOCK - IN_MUG[0]) / N1, SETTLE1)
    while tr.f < c_land1 + GLANCE_AT:
        tr.roll_sine(0.0, 1)
    c_gl = tr.f
    tr.roll_sine(GLANCE_DX, GLANCE_N)                     # the glance: a touch of roll so the dot looks down at the plate
    c_gl_end = tr.f
    tr.still(GLANCE_HOLD)
    # the eager hops: a small gather (a faint roll with it), a quick hop, a landing; the plate flips on each landing
    flips = [(c_land1 + FLIP1_AT, FLIP1)]
    gathers = []
    tr.roll_sine(1.0, 9)
    gathers.append((tr.f - 9, tr.f, SQ["hop_gather"]))
    hop_lands = []
    for k, (vx, T, flip_n) in enumerate(HOPS):
        _, land = tr.hop(vx, T, BT, "the block's top", w_air=0.0)
        hop_lands.append(land)
        flips.append((land, flip_n))
        tr.roll_out(vx, HOP_DWELL if k < len(HOPS) - 1 else 22)
        if k < len(HOPS) - 1:
            gathers.append((tr.f - 8, tr.f, SQ["hop_gather"]))
    tr.roll_sine(CALM1_DX, CALM1)
    c_big = tr.f
    tr.still(BIG_GATHER)                                  # the deeper gather and the lean: full stillness, on purpose
    gathers.append((c_big, tr.f, SQ["big_gather"]))
    leans = [(c_big, tr.f, BIG_LEAN, 8)]
    big_go, c_proud = tr.hop(BIG_VX, BIG_T, BT, "the block's top (proud)", w_air=0.0)
    tr.roll_out(BIG_VX, 20)
    top = (c_proud + TOP_AT, TOP_N)
    while tr.f < c_proud + WATCH_AT:
        tr.roll_sine(0.0, 1)
    tr.roll_sine(WATCH_DX, WATCH_N)                       # the ball watches the top with a faint roll
    tr.roll_sine(CALM2_DX, CALM2)
    tr.roll_sine(-1.0, DOWN_GATHER)
    gathers.append((tr.f - DOWN_GATHER, tr.f, SQ["down_gather"]))
    x_s = tr.pos[-1][0]
    P = plan_bounces(x_s, BT, YC, RC)
    c_go_down, c_coaster = tr.hop(P["vx"], P["T"], YC, "the coaster's big hex", w_air=0.25 * P["vx"] / R, vy0=P["vy0"])
    # off the big hex (it grips: the turn follows its sideways speed), into the pad's face, and off that into the mug
    (x0, y0), vo, tc, qc, n, w = tr.pos[-1], P["vo"], P["tc"], P["qc"], P["n"], P["w"]
    w_air = vo[0] / R
    tang = (-n[1], n[0])
    w_pad = 0.5 * w_air + 0.5 * (w[0] * tang[0] + w[1] * tang[1]) / R
    k, c_catch = 0, None
    while True:
        k += 1
        if k < tc:
            p = (x0 + vo[0] * k, y0 + (vo[1] + 0.2) * k + 0.2 * k * k)
            tr.put(p, w_air)
        else:
            u = k - tc
            p = (qc[0] + w[0] * u, qc[1] + w[1] * u + 0.2 * u * u)
            tr.put(p, w_pad)
        if c_catch is None and k > tc and p[1] >= 668 and w[1] + 0.4 * (k - tc) > 0:
            c_catch, cross = tr.f, p
        if k > tc and p[1] >= HIDE_Y and w[1] + 0.4 * (k - tc) > 0:
            c_hid = tr.f
            break
    c_pad = c_coaster + math.ceil(tc)
    tr.landings.append((c_pad, P["face"], math.hypot(vo[0], vo[1] + 0.4 * tc)))
    tr.flights.append((c_coaster, math.floor(tc), vo[0], vo[1] + 0.2))
    tr.flights.append((c_pad, c_hid - c_pad, w[0], w[1] + 0.4 * (c_pad - c_coaster - tc)))
    # hidden in the mug: it keeps falling to the bottom, the mug catches it, then it settles back to its starting place
    vxh, vyh = tr.pos[-1][0] - tr.pos[-2][0], tr.pos[-1][1] - tr.pos[-2][1]
    hx, hy = tr.pos[-1]
    while hy < IN_MUG[1]:
        vyh += G
        hx = min(820.0, max(796.0, hx + vxh))
        vxh *= 0.8
        hy = min(IN_MUG[1], hy + vyh)
        tr.put((hx, hy), 0.0)
    f_bottom = tr.f
    for k in range(1, 13):
        tr.put((hx + (IN_MUG[0] - hx) * smooth(k / 12), IN_MUG[1]), 0.0)
    L = c_catch + HOME_BEAT
    while tr.f < L:
        tr.put(IN_MUG, 0.0)
    assert tr.f == L and 720 <= L <= 840, L
    pos = tr.pos

    # ------------------------------------------------------------------ the turn
    # the pop's spin (out of the mug, out of sight when it starts) is chosen so that, after the landing's roll and the glance, the dot
    # points at the plate's centre
    th = [0.0]
    for g in range(L):
        th.append(th[-1] + tr.w[g])
    cx_g = pos[c_gl_end][0]
    to_plate = math.degrees(math.atan2(-(BLOCK_C[1] - pos[c_gl_end][1]), BLOCK_C[0] - cx_g))
    want = math.radians(43.9 - to_plate)                  # the dot sits 43.9 degrees above "right" when the turn is 0
    have = th[c_gl_end] - th[c_land1]
    need = (want - have) % (2 * math.pi)
    w_pop = need / len(pop_frames)
    for g in pop_frames:
        tr.w[g] = w_pop
    th = [0.0]
    for g in range(L):
        th.append(th[-1] + tr.w[g])
    total = th[L]
    whole = round(total / (2 * math.pi)) * 2 * math.pi
    for g in range(f_bottom, L + 1):
        th[g] += (whole - total) * min(1.0, (g - f_bottom) / 20)

    # ------------------------------------------------------------------ squash, stretch and lean
    s = [0.0] * (L + 1)
    lean = [0.0] * (L + 1)
    for g in range(L + 1):
        v = s[g]
        v += gather_pulse(g, 0, GO, SQ["mug_gather"])
        for a, b, amt in gathers:
            v += gather_pulse(g, a, b, amt)
        v += land_pulse(g - c_land1, SQ["land1"])
        for land in hop_lands:
            v += land_pulse(g - land, SQ["hop_land"])
        v += land_pulse(g - c_proud, SQ["proud"], down=4, back=7, after=4)
        v += land_pulse(g - c_coaster, SQ["coaster"])
        s[g] = v
        for a, b, ang, back in leans:
            if a <= g <= b:
                lean[g] = ang * smooth((g - a) / (b - a))
            elif b < g <= b + back:
                lean[g] = ang * (1 - smooth((g - b) / back))
    # the flight stretch, along the travel (here: up and down), only on the fastest moves
    for launch, T, vx, vy0 in tr.flights:
        for k in range(1, T):
            g = launch + k
            vy = vy0 + 0.4 * k
            sp = math.hypot(vx, vy)
            amt = 0.03 * min(1.0, max(0.0, (sp - 6.0) / 6.5)) * (vy * vy / (sp * sp)) * min(1.0, k / 2, (T - k) / 3)
            if g <= L and amt > 0 and pos[g][1] < HIDE_Y:
                s[g] = min(s[g], -amt) if s[g] <= 0 else s[g] - amt
    assert max(s) <= 0.08 + 1e-9 and min(s) >= -0.03 - 1e-9, (max(s), min(s))
    assert abs(s[0] - s[L]) < 1e-9 and abs(lean[0] - lean[L]) < 1e-9
    cyc = Cycle(L)
    hs = [land_pulse(g - c_pad, SQ["pad_hit"], down=2, back=6, after=2) for g in range(L + 1)]   # the hit on the pad's face: across
    for g in range(L + 1):
        cyc.put(g, pos[g], "air")
        cyc.sy[g] = (1 - s[g]) / (1 - hs[g])
        cyc.sx[g] = (1 - hs[g]) / (1 - s[g])               # volume constant
    th_spin = [th[g] - lean[g] for g in range(L + 1)]      # the dot turns only with the travel, not with the lean

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
    pieces.append((art.scale, "rotation", ser(lambda g: lean[g]), None))
    # the lily pad gives under the hit: pushed along the hit a little, tilted a little, one small overshoot, still in 0.4 s
    pieces.append(("9:504", "x", ser(lambda g: PAD_NODE[0] - n[0] * settle(g - c_pad, PAD_GIVE)), None))
    pieces.append(("9:504", "y", ser(lambda g: PAD_NODE[1] - n[1] * settle(g - c_pad, PAD_GIVE)), intro_series(scene, sheet, ROOM, "9:504", "y")))
    pieces.append(("9:504", "rotation", ser(lambda g: settle(g - c_pad, PAD_TILT)), None))

    # the plate: one coin turn per flip (half a turn of |cos|: it ends on the face it started on), then the top's spin, slowing down
    for (a, n), (b, _) in zip(flips, flips[1:] + [top]):
        assert a + n < b, ("two turns of the plate overlap", a, b)

    def plate_angle(c):
        for a, n in flips:
            if a <= c <= a + n:
                return math.pi * ease((c - a) / n)
        a, n = top
        if a <= c <= a + n:
            u = (c - a) / n
            return TOP_TURNS * math.pi * (1 - (1 - u) ** 2)
        return 0.0
    plate = add_plate_spin(doc, ROOM)
    pieces.append((plate, "scaleX", ser(lambda g: max(0.07, abs(math.cos(plate_angle(g))))), None))

    def pre(f):
        px = plane_x(scene, sheet, ROOM, "Front")
        my = intro_series(scene, sheet, ROOM, "9:463", "y")
        msx = intro_series(scene, sheet, ROOM, "9:463", "scaleX")
        msy = intro_series(scene, sheet, ROOM, "9:463", "scaleY")
        dy = my(f) - MUG_PIVOT[1]
        return ((MUG_PIVOT[0] + msx(f) * (IN_MUG[0] - MUG_PIVOT[0]) + px(f), MUG_PIVOT[1] + dy + msy(f) * (IN_MUG[1] - MUG_PIVOT[1])), 1.0, 1.0)

    emit(doc, art, spin, cyc, th_spin, T0, pre, pieces)

    # ------------------------------------------------------------------ the checks
    launches = {f[0] for f in tr.flights}
    near = {c + d for c, _, _ in tr.landings for d in (-1, 0, 1, 2)} | {x + d for x in launches for d in (0, 1, 2)}
    near |= set(range(c_hid, L + 1))
    bad = []
    for g in range(2, L + 1):
        if g in near:
            continue
        a = (pos[g][0] - 2 * pos[g - 1][0] + pos[g - 2][0], pos[g][1] - 2 * pos[g - 1][1] + pos[g - 2][1])
        if math.hypot(*a) > 0.9:
            bad.append((g, round(math.hypot(*a), 2)))
    assert not bad, ("the ball jumps", bad[:6])
    for g in range(L + 1):
        assert pos[g][1] - 23.865 >= COPY_Y - 1e-6, ("the ball's top above the copy line", g, pos[g])
        if pos[g][1] < HIDE_Y:
            assert 560 <= pos[g][0] <= 935, ("outside the phone frame", g)
    on_top = [pos[g][0] for g in range(c_land1, c_go_down) if abs(pos[g][1] - BT) < 1e-6]
    assert min(on_top) >= 782 and max(on_top) <= 838, ("rolling off the block's top", min(on_top), max(on_top))
    assert 793 <= cross[0] <= 821, ("the ball misses the mug's opening", cross)

    sec = lambda g: f"{(T0 + g) / 60:.2f} s"
    beats = [f"pop {sec(go)}", f"block {sec(c_land1)}", f"plate turns {sec(flips[0][0])}", f"glance {sec(c_gl)}",
             "hops " + ", ".join(sec(x) for x in hop_lands), f"gather {sec(c_big)}", f"proud landing {sec(c_proud)}",
             f"top spin {sec(top[0])} to {sec(top[0] + top[1])}", f"hop down {sec(c_go_down)}", f"big hex {sec(c_coaster)} ({P['kc']:.0%} kept)",
             f"{P['face']} {sec(c_coaster + tc)} ({P['kp']:.0%} kept)",
             f"into the mug {sec(c_catch)} (crosses x {cross[0]:.0f}; in front of the block's corner, {P['deep']:.1f} px over it; "
             f"{P['c_rim']:.1f} from the rim; hop down {P['c_down']:.1f} clear)"]
    return f"{ROOM}: " + ", ".join(beats) + f"; loop {L / 60:.2f} s ({L} frames)"
