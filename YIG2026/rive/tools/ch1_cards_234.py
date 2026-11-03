"""One time (2026-11-02, history like loading_start.py): new ball loops for Chapter 1 cards 2, 3 and 4 (finesse round).

    python3 tools/ch1_cards_234.py --cards 2            dry run: prints each beat and the clearances, writes nothing
    python3 tools/ch1_cards_234.py --cards 2 --write    rewrite chapters/ch1/scene.rml

Shared by the three rooms: the ball arrives with its room, already at its home spot (no roll-in, no pop), the loop starts the moment
the intro ends, the ball has weight (steady gravity in every flight, a squash on every landing), and the pieces it touches react a
little and settle (a dip with a spring back, a rock, a wobble), each one turning about its own pivot. A reaction starts on the frame
of the contact and the ball rides the piece while it moves. The ball's position is written one key per frame, like the other
rooms' baked arcs. The old roll-in (x -80 at 2.30 to 3.05 s, then the 0.15 s pop) is gone from the intros.

Card 2 was rewritten the same day (finesse round 3): slide down the whole stack, climb back up the right side in small hops; the
eraser launch, the TOTAL spring and the return arc of the first version are gone. Rebuild from the file as it was before the first
version (git show b409b42~1:...scene.rml) to run it: it wraps pieces in pivots and so is not safe to run twice.

Times in the notes are Finesse-panel timecodes: the loop's time plus 3.2 s (the intro).
"""
import math
import sys

from ball_motion import G, Path, arc, bezier, fall_height, gravity, pulse, release, rot, roll_distance, smooth, speed_profile, ease_in, spring
from rml_edit import Doc, bake
from rml_read import Scene, chapter_dir

SCENE = chapter_dir("ch1") / "scene.rml"
INTRO = 192
BALL_CENTER = 16.66          # the ball's centre is this far above its node (the contact point) at full size
R = 17.0                     # centre to the edge of what it rests on
COPY_BOTTOM = 251.0          # lowest line of the card's copy on the 375 x 812 phone frame (measured in the harness, worst card)


def phone_y(y):
    """Artboard y on the phone frame: scale 0.9893 (artboard 1479 px wide for 1495 units), top at -2.45."""
    return 0.9893 * y - 2.45


def plane_x(room):
    """The room's Floor Plane x on every Intro frame (1600 sliding to 0): the ball is not inside the planes, so it rides this."""
    from rooms_sheet import Sheet
    sc = Scene(SCENE)
    sh = Sheet(sc)
    oid = next(e.get("id") for e in sc.root.iter("Node") if e.get("name") == f"{room} Floor Plane")
    k = sh.anim_keys(sc.animations[f"{room} Intro"])[oid]["x"]
    return lambda f: k.at(f)


def series(f0, f1, fn):
    return {f: fn(f) for f in range(f0, f1)}


class Ball:
    """The ball's centre, size, motion mode and spin on every frame, built up from one segment after another.

    Modes (what the ball is doing from this frame to the next): "rest", "roll" (on a surface in the picture: turns with the distance
    it travels along it), "floor" (rolling on the floor plane, where only the sideways part of the travel shows as a turn) and
    "air" (keeps the spin it left the surface with; from rest it gets a little from the push)."""

    def __init__(self, n):
        self.n = n
        self.c = {}
        self.mode = {}
        self.sx = {f: 1.0 for f in range(n)}
        self.sy = {f: 1.0 for f in range(n)}
        self.notes = []
        self.kick = {}

    def put(self, f, c, mode="rest"):
        self.c[f] = c
        self.mode[f] = mode

    def seg(self, f0, f1, pts, mode="air"):
        for i, p in enumerate(pts):
            self.c[f0 + i] = p
            self.mode[f0 + i] = mode
        assert len(pts) == f1 - f0 + 1, (f0, f1, len(pts))

    def squash(self, f, a):
        for k in range(0, 30):
            if f + k < self.n:
                p = pulse(k)
                self.sy[f + k] = 1 - a * p
                self.sx[f + k] = 1 + 0.7 * a * p

    def node(self):
        """x and y of the ball node (the contact point) on every frame."""
        xs = {f: self.c[f][0] for f in self.c}
        ys = {f: self.c[f][1] + BALL_CENTER for f in self.c}
        return xs, ys

    def spin(self, r=16.9, push=0.4):
        """The ball's turn in radians at frames 0 to n (n + 1 values), clockwise positive. Needs c[n] to be the first frame again."""
        th, prev, w_prev, w_air = [0.0], "rest", 0.0, 0.0
        for f in range(self.n):
            m = self.mode.get(f, "rest")
            c0, c1 = self.c[f], self.c[f + 1]
            dx, dy = c1[0] - c0[0], c1[1] - c0[1]
            if m == "roll":
                w = math.copysign(math.hypot(dx, dy), dx) / r if abs(dx) > 1e-9 else 0.0
            elif m == "floor":
                w = dx / r
            elif m == "air":
                if f in self.kick:
                    w_air = self.kick[f]
                elif prev != "air":
                    if prev in ("roll", "floor"):
                        w_air = w_prev
                    else:                                        # off the ground from rest: the push gives it a little
                        k = f
                        while k < self.n and self.mode.get(k) == "air":
                            k += 1
                        k = min(k, f + 12)
                        w_air = push * (self.c[k][0] - self.c[f][0]) / max(k - f, 1) / r
                w = w_air
            else:
                w = 0.0
            th.append(th[-1] + w)
            prev, w_prev = m, w
        return th


def segdist(p, a, b):
    """Distance from point p to the segment a-b."""
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy)))
    return math.dist(p, (ax + t * dx, ay + t * dy))


def round_ball(doc, intro, ids):
    """Hold the ball's shape round for the whole room (the old rooms drew it squashed at rest): key the Intro, drop it from the Loop."""
    loop = intro.replace("Intro", "Loop")
    hold = lambda oid, prop, v: doc.set_prop(intro, oid, prop, [(0, v, "hold"), (INTRO - 1, v, "hold")])
    hl, top, right, left = ids
    hold(hl, "x", 6.364); hold(hl, "y", -23.834); hold(hl, "scaleX", 1.0); hold(hl, "scaleY", 1.0)
    hold(top, "y", -17.678); hold(top, "inDistance", 9.7633); hold(top, "outDistance", 9.7633)
    hold(right, "x", 17.678); hold(right, "y", 0.0)
    hold(left, "x", -17.678); hold(left, "y", 0.0)
    for oid in ids:
        doc.drop_object(loop, oid)


def intro_keys(room, name):
    """The Intro's keys of the named node, by property (read from the scene before it is edited)."""
    from rooms_sheet import Sheet
    sc = Scene(SCENE)
    oid = next(e.get("id") for e in sc.root.iter("Node") if e.get("name") == name)
    return Sheet(sc).anim_keys(sc.animations[f"{room} Intro"])[oid]


def polydist(p, poly):
    """Distance from p to a closed polygon's outline."""
    return min(segdist(p, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))


def card1_spin(doc):
    """Chapter 1 card 1 already turns its ball (Ball Art rotation, rolling and in the air). Audit result (2026-11-02): the turning
    follows the rule everywhere except two windows where the ball rests on the window and on the dog bed (frames 108 to 144 and 270 to
    300) and the rotation wobbled by up to 0.17 radians. The rule says a ball at rest stops turning, so those two windows are held
    still; the keys before and after them are untouched (the rotation is equal at both ends of each window)."""
    from rooms_sheet import Sheet
    sc = Scene(SCENE)
    k = Sheet(sc).anim_keys(sc.animations["Chapter 1 Card 1 Loop"])["9:4806"]["rotation"]
    vals = {f: k.at(f) for f in range(762)}
    assert abs(vals[108] - vals[144]) < 0.01 and abs(vals[270] - vals[300]) < 0.01, (vals[108], vals[144], vals[270], vals[300])
    for f in range(109, 144):
        vals[f] = vals[108]
    for f in range(271, 300):
        vals[f] = vals[270]
    doc.set_prop("Chapter 1 Card 1 Loop", "9:4806", "rotation", bake(vals, range(762)))


def emit_room(doc, room, b, theta, T0, ids, pre, pieces):
    """Write a room whose ball journey starts at intro frame T0 and then repeats as the loop (picked up at the intro's last frame).

    b: the Ball over cycle frames 0 to L - 1 with c[L] = c[0]; theta: its turn at cycle frames 0 to L (the ends a whole number of turns apart);
    ids: dict with ball, scale, spin (node ids); pre(f): (x, y, scaleX, scaleY) of the ball's centre on intro frames before T0;
    pieces: [(object id, property, fn(cycle frame), rest value, extra(intro frame) or None)]. Everything must be at rest on cycle frame 0
    and L - 1, so the loop closes."""
    L = b.n
    assert T0 <= INTRO - 1
    loop, intro = f"{room} Loop", f"{room} Intro"
    phase0 = INTRO - 1 - T0
    px = plane_x(room)
    turns = theta[L] - theta[0]
    assert abs(turns / (2 * math.pi) - round(turns / (2 * math.pi))) < 1e-6, turns
    th_ext = lambda t: theta[t % L] + (t // L) * turns
    fr_i, fr_l = range(INTRO), range(L + 1)
    ix, iy, isx, isy, ith = {}, {}, {}, {}, {}
    for f in fr_i:
        if f < T0:
            x, y, sx, sy = pre(f)
            th = 0.0
        else:
            t = f - T0
            (x, y), sx, sy, th = b.c[t], b.sx[t], b.sy[t], th_ext(t)
        ix[f], iy[f], isx[f], isy[f], ith[f] = x + px(f), y + BALL_CENTER, sx, sy, th
    lx = {k: b.c[(phase0 + k) % L][0] for k in fr_l}
    ly = {k: b.c[(phase0 + k) % L][1] + BALL_CENTER for k in fr_l}
    lsx = {k: b.sx[(phase0 + k) % L] for k in fr_l}
    lsy = {k: b.sy[(phase0 + k) % L] for k in fr_l}
    lth = {k: th_ext(phase0 + k) for k in fr_l}
    doc.set_duration(loop, L + 1)
    for prop, i_ser, l_ser in (("x", ix, lx), ("y", iy, ly)):
        doc.set_prop(intro, ids["ball"], prop, bake(i_ser, fr_i))
        doc.set_prop(loop, ids["ball"], prop, bake(l_ser, fr_l))
    for prop, i_ser, l_ser in (("scaleX", isx, lsx), ("scaleY", isy, lsy)):
        doc.set_prop(intro, ids["scale"], prop, bake(i_ser, fr_i))
        doc.set_prop(loop, ids["scale"], prop, bake(l_ser, fr_l))
    doc.set_prop(intro, ids["spin"], "rotation", bake(ith, fr_i))
    doc.set_prop(loop, ids["spin"], "rotation", bake(lth, fr_l))
    for oid, prop, fn, rest, extra in pieces:
        assert abs(fn(0) - rest) < 1e-6 and abs(fn(L - 1) - rest) < 1e-3, (oid, prop, fn(0), fn(L - 1), rest)
        iser = {f: (fn(max(f - T0, 0)) + (extra(f) if extra else 0.0)) for f in fr_i}
        lser = {k: fn((phase0 + k) % L) for k in fr_l}
        doc.set_prop(intro, oid, prop, bake(iser, fr_i))
        doc.set_prop(loop, oid, prop, bake(lser, fr_l))
    doc.rebuild_waiting(room)


def card2(doc, write):
    """Slide down, climb back up (finesse round 4): the block on top teeters like a seesaw and rolls the ball onto the bar, the ball
    slides down the whole stack and out along the floor, then climbs the right side in small hops."""
    room = "Chapter 1 Card 2"
    # ---- the art (world coordinates measured from the file; every piece here is unscaled) ------------------------------------
    block_top = 444.8                                   # the pink and orange block: flat from x 666.5 to 719.3
    block_poly = [(719.3, 444.8), (722.1, 450.4), (714.9, 460.1), (706.6, 464.3), (653.8, 464.3), (651.0, 458.6), (658.2, 448.9), (666.5, 444.8)]
    block_pivot = (686.5, 464.265)                      # the Top Piece node the intro drops in
    J_top = (682.28, 464.3)                             # the white joint the block sits on: it tips about its top
    home_u = 708.0                                      # where the ball sits on the block (x along the flat top)
    T = (856.1, 711.4)                                  # the pencil's tip
    E = (822.4, 475.3)
    UPRIGHT = math.atan2(T[0] - E[0], T[1] - E[1])
    bar_c, bar_d = (728.27, 517.52), (math.cos(0.22066198), math.sin(0.22066198))
    bar_n = (bar_d[1], -bar_d[0])
    BAR_UP = 7.59 + 16.855
    bar_pivot = (781.5, 538.0)
    j_mid, j_low = (782.02, 555.32), (667.10, 620.37)
    st_a, st_b = (781.7, 555.3), (666.8, 620.4)
    st_len = math.dist(st_a, st_b)
    st_d = ((st_b[0] - st_a[0]) / st_len, (st_b[1] - st_a[1]) / st_len)
    st_n = (st_d[1], -st_d[0])
    ST_UP = 7.25 + 16.855
    total_pivot = (681.0, 711.8)
    total_poly = [(706.7, 711.8), (655.0, 711.8), (649.2, 701.6), (703.7, 608.6), (713.2, 603.2), (764.9, 603.2), (770.7, 613.4), (716.2, 706.4)]
    dom_pivot = (697.0, 572.5)
    c_pivot = (780.2, 711.8)
    c_top = 646.6
    slab_top = 572.7
    floor_c = 711.8 - R
    ramp_p0, ramp_d, ramp_n = (703.7, 608.6), (-0.5056, 0.8627), (-0.8627, -0.5056)

    def bar_pt(p, th):
        c = (bar_c[0] + p * bar_d[0] + BAR_UP * bar_n[0], bar_c[1] + p * bar_d[1] + BAR_UP * bar_n[1])
        return rot(c, bar_pivot, th)

    def bar_p_at(x):
        return (x - bar_c[0] - BAR_UP * bar_n[0]) / bar_d[0]

    def stick_pt(q, th):
        c = (st_a[0] + q * st_d[0] + ST_UP * st_n[0], st_a[1] + q * st_d[1] + ST_UP * st_n[1])
        return rot(c, j_mid, th)

    def ramp_pt(s):
        return (ramp_p0[0] + s * ramp_d[0] + R * ramp_n[0], ramp_p0[1] + s * ramp_d[1] + R * ramp_n[1])

    # ---- the teeter: the block rocks on its joint, tips, and the ball rolls off its right end --------------------------------------
    ctrl = [(0, 0.0), (8, -0.04), (18, 0.05), (26, -0.03), (40, 0.16)]
    TIP = ctrl[-1][1]

    def th_base(t):
        for (t0, v0), (t1, v1) in zip(ctrl, ctrl[1:]):
            if t <= t1:
                return v0 + (v1 - v0) * smooth((t - t0) / (t1 - t0))
        return TIP
    A_ROLL, EDGE_U = 0.9, 720.0
    us, u, v = [], home_u, 0.0
    t_off = None
    for t in range(0, 120):
        us.append(u)
        if u >= EDGE_U:
            t_off = t
            break
        v += A_ROLL * math.sin(th_base(t))
        u += v
    assert t_off, "the ball never rolls off"
    v_off = us[t_off] - us[t_off - 1]
    th_main = lambda t: th_base(t) if t <= t_off else release(t - t_off, TIP, tau=7.0, period=22.0)

    def on_block(u_, th):
        return rot((u_, block_top - R), J_top, th)

    # ---- when things happen (cycle frames; the Finesse timecode is the intro's journey start + frame / 60) ------------------------------
    N_FALL = 22
    F_BAR = t_off + N_FALL
    F_WALL = F_BAR + 9
    F_JOINT = F_WALL + 12
    F_STICK = F_JOINT + 18
    F_LOW = F_STICK + 20
    F_RAMP = F_LOW + 14
    F_RAMP_END = F_RAMP + 9
    D_RUN = 92
    F_FOOT = F_RAMP_END + D_RUN
    F_UP = F_FOOT + 18
    HOP = [(26, 26), (26, 28), (22, 22), (20, 16), (20, 14), (24, None)]
    STAY = 4
    leave, land = [], []
    f = F_UP
    for n, h in HOP:
        leave.append(f)
        land.append(f + n)
        f += n + STAY
    F_TOP = land[-1]
    L = F_TOP + 40
    T0 = max(118, INTRO - F_BAR)

    # ---- positions ----------------------------------------------------------------------------------------------------------------------
    p_off = on_block(us[t_off], th_main(t_off))
    p_prev = on_block(us[t_off - 1], th_main(t_off - 1))
    vx, vy0 = p_off[0] - p_prev[0], p_off[1] - p_prev[1]
    x_land = p_off[0] + vx * N_FALL
    p_bar1 = bar_p_at(x_land)
    land_bar = bar_pt(p_bar1, 0.0)
    h_fall = ((land_bar[1] - p_off[1]) - vy0 * N_FALL) / 4
    p_wall = bar_p_at(792.0)
    shoulder = (j_mid[0] + 34.2 * math.cos(math.radians(-115)), j_mid[1] + 34.2 * math.sin(math.radians(-115)))
    Q0, Q1 = 45.0, 100.0
    s_land, s_end = 66.0, 104.0
    foot = (819.0, floor_c)
    c_land = (790.0, c_top - R)
    slab_land = (806.0, slab_top - R)
    bar_stops = [bar_p_at(x) for x in (794.0, 774.0, 750.0)]
    top_land_u = 714.0
    # the climb's last step: the smallest hop that clears the block's corner
    pos_h5 = bar_pt(bar_stops[2], 0.0)
    top_land = (top_land_u, block_top - R)
    best = None
    for h6 in range(8, 44, 2):
        for xe in (1.0, 1.4, 1.8, 2.2, 2.6):
            pts = arc(pos_h5, top_land, HOP[5][0], h6, xe)
            if min(polydist(p, block_poly) for p in pts[:-3]) >= 16.8:
                best = (h6, xe)
                break
        if best:
            break
    assert best, "no clear last hop"
    h6, xe6 = best
    HOP[5] = (HOP[5][0], h6)

    # ---- reactions (functions of the cycle frame) -------------------------------------------------------------------------------------------
    bar_hits = [(F_BAR, -0.03)] + [(land[i], -0.012) for i in (2, 3, 4)]
    bar = lambda t: sum(spring(t - fl, d, down=4, tau=9.0, period=20.0) for fl, d in bar_hits)
    domino = lambda t: 0.05 * math.exp(-(t - F_BAR - 4) / 14.0) * math.sin(2 * math.pi * (t - F_BAR - 4) / 22.0) if t > F_BAR + 4 else 0.0
    joint_hits = [(F_WALL - 3, 0.10), (F_JOINT, 0.14), (land[1], 0.10)]
    joint_p = lambda t: sum(a * pulse(t - fl, down=3, tau=7.0, period=16.0) for fl, a in joint_hits)
    low_p = lambda t: 0.14 * pulse(t - F_LOW, down=3, tau=7.0, period=16.0)
    stick = lambda t: spring(t - F_STICK, -0.03, down=4, tau=9.0, period=20.0)
    total_dip = lambda t: spring(t - F_RAMP, 0.04, down=4, tau=10.0, period=20.0)
    pencil = lambda t: spring(t - F_WALL, 0.02, down=2, tau=7.0, period=16.0) + spring(t - F_FOOT, 0.012, down=2, tau=7.0, period=16.0)
    slab_dip = lambda t: spring(t - land[1], 2.5, down=3, tau=8.0, period=18.0)
    block_th = lambda t: th_main(t) + spring(t - F_TOP, 0.03, down=3, tau=7.0, period=20.0)

    # ---- the ball -----------------------------------------------------------------------------------------------------------------------------
    b = Ball(L)
    for t in range(0, t_off + 1):
        b.put(t, on_block(us[t], th_main(t)), "roll")
    b.seg(t_off, F_BAR, arc(p_off, land_bar, N_FALL, h_fall))
    # down the bar, speeding up; the joint beneath squashes as the ball crosses it
    v0_bar = vx / bar_d[0]
    D_bar = p_wall - p_bar1
    n_bar = F_WALL - F_BAR
    a_bar = 2 * (D_bar - v0_bar * n_bar) / (n_bar * n_bar)
    assert D_bar > 0 and a_bar >= 0, (D_bar, v0_bar, n_bar, a_bar)
    for i in range(n_bar + 1):
        t = F_BAR + i
        b.put(t, bar_pt(p_bar1 + v0_bar * i + 0.5 * a_bar * i * i, bar(t)), "roll")
    # into the pencil, which gives a little, and back to the joint's shoulder, then off it onto the yellow stick
    b.seg(F_WALL, F_JOINT, arc(b.c[F_WALL], shoulder, F_JOINT - F_WALL, 7))
    b.put(F_JOINT, shoulder)
    b.put(F_JOINT + 1, shoulder)
    b.seg(F_JOINT + 2, F_STICK, arc(shoulder, stick_pt(Q0, 0.0), F_STICK - F_JOINT - 2, 9))
    s_st, _ = roll_distance(F_LOW - F_STICK, 1.8, Q1 - Q0)
    for i, s in enumerate(s_st):
        b.put(F_STICK + i, stick_pt(Q0 + s, stick(F_STICK + i)), "roll")
    b.seg(F_LOW, F_RAMP, arc(b.c[F_LOW], ramp_pt(s_land), F_RAMP - F_LOW, 8))

    def ramp_ride(pt, t):
        return (pt[0], total_pivot[1] + (pt[1] - total_pivot[1]) * (1 - total_dip(t)))
    s_rp, _ = roll_distance(F_RAMP_END - F_RAMP, 3.2, s_end - s_land)
    for i, s in enumerate(s_rp):
        b.put(F_RAMP + i, ramp_ride(ramp_pt(s_land + s), F_RAMP + i), "roll")
    # off the bottom of the slide: it curves round in front of the floor, below TOTAL's base, and heads right toward the C block
    p_exit = ramp_pt(s_end)
    ex = (ramp_d[0], ramp_d[1])
    A = bezier(p_exit, (p_exit[0] + 20 * ex[0], p_exit[1] + 20 * ex[1]), (611.0, 742.0), (648.0, 746.0), 40)
    B = [(648.0 + (712.0 - 648.0) * i / 20, 746.0) for i in range(1, 21)]
    C = bezier((712.0, 746.0), (738.0, 746.0), (765.0, floor_c), (790.0, floor_c), 40)[1:]
    Dd = [(790.0 + (foot[0] - 790.0) * i / 8, floor_c) for i in range(1, 9)]
    path = Path(A + B + C + Dd)
    cum = speed_profile(D_RUN, 4.9, 2.6, 12)
    for i in range(D_RUN + 1):
        b.put(F_RAMP_END + i, path.at(cum[i] * path.length), "floor" if i < D_RUN else "rest")
    f_tap = next(t for t in range(F_RAMP_END, F_FOOT + 1) if b.c[t][0] + 17.0 >= 747.6)
    for t in range(F_FOOT, F_UP + 1):
        b.put(t, foot)
    # the climb
    c_nudge = lambda t: spring(t - f_tap, 0.03, down=3, tau=8.0, period=18.0)
    c_dip = lambda t: spring(t - land[0], 0.04, down=3, tau=8.0, period=18.0)

    def pos_on(i, t):
        if i == 0:
            return (c_land[0], c_pivot[1] + (c_land[1] - c_pivot[1]) * (1 - c_dip(t)))
        if i == 1:
            return slab_land
        if i in (2, 3, 4):
            return bar_pt(bar_stops[i - 2], bar(t))
        return on_block(top_land_u, block_th(t))
    for i, (n, h) in enumerate(HOP):
        a_, z_ = leave[i], land[i]
        if i:
            for t in range(land[i - 1], a_ + 1):
                b.put(t, pos_on(i - 1, t))
        b.seg(a_, z_, arc(b.c[a_], pos_on(i, z_), n, h, xe6 if i == 5 else 1.0))
    # settle on top: it rolls back to its spot as the block rocks and comes to rest
    for t in range(F_TOP, L):
        u_ = top_land_u - (top_land_u - home_u) * smooth((t - F_TOP - 8) / 18.0)
        b.put(t, on_block(u_, block_th(t)), "roll" if F_TOP + 8 <= t <= F_TOP + 26 else "rest")
    b.put(L, b.c[0])
    b.mode[L] = b.mode[0]
    assert math.dist(b.c[L - 1], b.c[0]) < 0.05, (b.c[L - 1], b.c[0])
    for fr, a in ((F_BAR, 0.10), (F_WALL, 0.10), (F_JOINT, 0.12), (F_STICK, 0.10), (F_LOW, 0.12), (F_RAMP, 0.10), (F_FOOT, 0.12)):
        b.squash(fr, a)
    for i, z_ in enumerate(land):
        b.squash(z_, 0.08 if i < 5 else 0.10)
    assert abs(b.sy[L - 1] - 1) < 1e-3, b.sy[L - 1]

    # ---- spin: the turn follows the rule; the leftover (to a whole number of turns) goes into the last hop -------------------------------------
    theta = b.spin()
    resid = theta[L] - 2 * math.pi * round(theta[L] / (2 * math.pi))
    a_, z_ = leave[5], land[5]
    theta = [th - resid * (smooth((t - a_) / (z_ - a_)) if t <= z_ else 1.0) for t, th in enumerate(theta)]
    top = min(c[1] for c in b.c.values()) - 17.6

    # ---- numbers to check -----------------------------------------------------------------------------------------------------------------------
    tc = lambda t: (t + T0) / 60.0           # Finesse timecode of a cycle frame
    names = [("block starts to teeter", 0), ("block tips and the ball rolls off its end", t_off), ("lands on the purple bar", F_BAR),
             ("hits the pencil at the bar's low end", F_WALL), ("touches the right white joint", F_JOINT), ("lands on the yellow stick", F_STICK),
             ("reaches the lower-left white joint", F_LOW), ("lands on TOTAL's left edge", F_RAMP), ("off the bottom of TOTAL, curving right", F_RAMP_END),
             ("goes behind the C block (tap)", f_tap), ("stops against the pencil's foot", F_FOOT)]
    names += [(f"climb hop {i + 1} lands", land[i]) for i in range(6)]
    print(f"{room}: cycle {L} frames ({L / 60:.2f} s), loop {L + 1} frames, journey starts at intro frame {T0} ({T0 / 60:.2f} s); the loop starts at cycle frame {INTRO - 1 - T0}")
    for name, t in names:
        print(f"  cycle {t:3d}  timecode {tc(t):5.2f} s (and +{L / 60:.2f} s each loop)  {name}")
    print(f"  highest point of the ball: y {top:.1f} ({phone_y(top):.0f} px on the phone frame); copy ends at {COPY_BOTTOM:.0f}: clearance {phone_y(top) - COPY_BOTTOM:.0f} px")
    print(f"  x range {min(c[0] for c in b.c.values()) - 17.6:.0f} to {max(c[0] for c in b.c.values()) + 17.6:.0f}, y to {max(c[1] for c in b.c.values()) + 17.6:.0f}")
    sp = lambda fa, fb: max(math.dist(b.c[f_], b.c[f_ + 1]) for f_ in range(fa, fb))
    print(f"  top speeds (px/frame): off the block {v_off:.1f}, bar {sp(F_BAR, F_WALL):.1f}, stick {sp(F_STICK, F_LOW):.1f}, ramp {sp(F_RAMP, F_RAMP_END):.1f}, run {sp(F_RAMP_END, F_FOOT):.1f}")
    print(f"  run: path {path.length:.0f} px; closest the ball's centre gets to TOTAL's outline on the way out: {min(polydist(b.c[t], total_poly) for t in range(F_RAMP_END + 1, F_FOOT)):.1f} (radius 17)")
    print(f"  last hop: {h6} high, x warp {xe6}; closest to the block's outline {min(polydist(b.c[t], block_poly) for t in range(leave[5], land[5] - 2)):.1f}")
    print(f"  spin: {theta[L] / (2 * math.pi):.2f} turns over the cycle (leftover {resid:+.2f} rad put into the last hop)")
    print(f"  gravity: fall off the block {gravity(N_FALL, h_fall):.2f}; climbing hops " + ", ".join(f"{gravity(n, h):.2f}" for n, h in HOP))
    if not write:
        return

    # ---- write ----------------------------------------------------------------------------------------------------------------------------------
    ids = dict(ball="9:8040", scale="9:8042", pencil="9:7760", bar="9:7865", domino="9:7872", total="9:7959", stick="9:7655", jmid="9:7643",
               jlow="9:7649", frontcircle="9:7748", cblock="9:7719", slab="9:7947", blocka="9:7686")
    old = ["9:7659", "9:7748", "9:8049", "9:8043", "9:8054", "9:8052", "9:8051"]
    loop, intro = f"{room} Loop", f"{room} Intro"
    piv = {}
    piv["pencil"], _ = doc.wrap(ids["pencil"], f"{room} Pencil", *T)
    piv["bar"], _ = doc.wrap(ids["bar"], f"{room} Bar", *bar_pivot)
    piv["domino"], _ = doc.wrap(ids["domino"], f"{room} Domino", *dom_pivot)
    piv["total"], _ = doc.wrap(ids["total"], f"{room} Total", *total_pivot)
    piv["stick"], _ = doc.wrap(ids["stick"], f"{room} Yellow Stick", j_mid[0] - 649.0, j_mid[1] - 463.5)      # inside a node at (649, 463.5)
    piv["cblock"], _ = doc.wrap(ids["cblock"], f"{room} C Block", *c_pivot)
    piv["block"], _ = doc.wrap(ids["blocka"], f"{room} Block Seesaw", *J_top)                                  # inside the Top Piece's Art node
    # the ball: turn about its own centre; no floor clip (it now runs in front of the floor); the old vertex and highlight keys go
    spin_id, _ = doc.wrap_run("9:8043", "9:8049", f"{room} Ball Spin", 0.0, -17.572)
    doc.drop_clipping("9:8043")
    doc.drop_clipping("9:8049")
    for oid in old:
        doc.drop_object(loop, oid)
        doc.drop_object(intro, oid)
    doc.set_prop(intro, ids["frontcircle"], "opacity", [(0, 0.0, "hold")])
    ids["spin"] = spin_id

    # the intro: the block drops in with the ball on it; the pencil tips into place last, quickly, with a small bounce
    tp = intro_keys(room, f"{room} Top Piece")
    TIP0, HIT = 117, 135

    def p_intro(fr):
        if fr < TIP0:
            return UPRIGHT
        if fr < HIT:
            return UPRIGHT * (1 - ease_in((fr - TIP0) / (HIT - TIP0)))
        u_ = fr - HIT
        if u_ < 12:
            return 0.025 * math.sin(math.pi * u_ / 12)
        if u_ < 22:
            return 0.006 * math.sin(math.pi * (u_ - 12) / 10)
        return 0.0
    ib = Ball(INTRO)

    def pre(fr):
        sy_t, sx_t = tp["scaleY"].at(fr), tp["scaleX"].at(fr)
        surf_y = tp["y"].at(fr) + sy_t * (block_top - block_pivot[1])
        x = block_pivot[0] + sx_t * (home_u - block_pivot[0])
        return x, surf_y - R, ib.sx[fr], ib.sy[fr]
    ib.squash(98, 0.10)
    pieces = [(piv["pencil"], "rotation", pencil, 0.0, p_intro),
              (piv["bar"], "rotation", bar, 0.0, None), (piv["domino"], "rotation", domino, 0.0, None),
              (piv["stick"], "rotation", stick, 0.0, None),
              (ids["jmid"], "scaleY", lambda t: 1 - joint_p(t) / 0.14 * 0.14, 1.0, None),
              (ids["jmid"], "scaleX", lambda t: 1 + 0.10 * joint_p(t) / 0.14, 1.0, None),
              (ids["jlow"], "scaleY", lambda t: 1 - low_p(t), 1.0, None), (ids["jlow"], "scaleX", lambda t: 1 + 0.7 * low_p(t), 1.0, None),
              (piv["total"], "scaleY", lambda t: 1 - total_dip(t), 1.0, None), (piv["total"], "scaleX", lambda t: 1 + 0.5 * total_dip(t), 1.0, None),
              (piv["cblock"], "rotation", c_nudge, 0.0, None), (piv["cblock"], "scaleY", lambda t: 1 - c_dip(t), 1.0, None),
              (ids["slab"], "y", lambda t: 8.3395 + slab_dip(t), 8.3395, None),
              (piv["block"], "rotation", block_th, 0.0, None)]
    emit_room(doc, room, b, theta, T0, ids, pre, pieces)





def polydist_min(pts, poly):
    return min(polydist(p, poly) for p in pts)



def card3(doc, write):
    """The #1 mug circuit (finesse round 4): mug -> band -> books (ricochet) -> FIRST card (ricochet) -> blue stick -> back into the mug."""
    global BALL_CENTER
    room = "Chapter 1 Card 3"
    BALL_CENTER = 16.78
    Rb = 17.1
    # ---- the art (world coordinates; the shelf, stick, card and mug groups are scaled 0.85 in the file, these are after the scale) ----
    mug_hide = (735.0, 724.0)                       # hidden inside the mug; its front rim is at y 698, so a centre below 715 is out of sight
    posts = [(792.0, 486.0), (862.1, 486.0)]        # radius 14.9
    band_x = 827.0
    band_rest_top = 485.7 - 6.4 + 0.4               # the band is straight at rest: its ends are at y 485.7, 12.75 thick
    band_land = (band_x, band_rest_top - Rb)
    face_a, face_b = (654.6, 473.9), (665.0, 506.2)  # the yellow book's right face (the books lean left against the orange book)
    fn_ = (32.3 / 33.9, -10.4 / 33.9)                # its outward normal, right and a little up
    face_mid = ((face_a[0] + face_b[0]) / 2, (face_a[1] + face_b[1]) / 2)
    book_hit = (face_mid[0] + fn_[0] * Rb, face_mid[1] + fn_[1] * Rb)
    card_edge = [(830.2, 538.6), (820.1, 544.4), (761.6, 644.0), (767.9, 654.9)]     # FIRST card's top and left edge
    ce_d, ce_n = (-0.5065, 0.8624), (-0.8624, -0.5065)
    s_hit = 30.0
    card_hit = (820.1 + s_hit * ce_d[0] + Rb * ce_n[0], 544.4 + s_hit * ce_d[1] + Rb * ce_n[1])
    tip, low = (594.5, 591.0), (671.0, 676.0)        # the blue stick's two white ends (radius 14.9)
    st_len = math.dist(tip, low)
    st_d = ((low[0] - tip[0]) / st_len, (low[1] - tip[1]) / st_len)
    st_n = (st_d[1], -st_d[0])
    ST_UP = 22.6
    stick_pivot, card_pivot, books_pivot, mug_pivot = low, (795.0, 654.9), (650.0, 508.0), (737.0, 745.0)

    def stick_pt(q):
        return (tip[0] + q * st_d[0] + ST_UP * st_n[0], tip[1] + q * st_d[1] + ST_UP * st_n[1])
    stick_land_q = 40.0
    # where the ball meets the lower white joint (centre 32 from it) and rolls over it
    q_join = math.dist(tip, low) - math.sqrt(32.0 ** 2 - ST_UP ** 2)
    jc = low

    # ---- when things happen (cycle frames) --------------------------------------------------------------------------------------------------
    F_POP, N1 = 10, 40                  # hops out of the mug, flight to the band
    F_BAND = F_POP + N1
    BAND_HOLD = 12
    F_UP = F_BAND + BAND_HOLD
    N2 = 34
    F_BOOK = F_UP + N2                  # ricochets off the books
    N3 = 36
    F_CARD = F_BOOK + N3                # ricochets off the FIRST card
    N4 = 34
    F_STK = F_CARD + N4                 # lands on the blue stick
    N_ROLL = 44
    F_JOIN = F_STK + N_ROLL             # reaches the white joint at the stick's low end
    N_ARC = 9
    F_LEAVE = F_JOIN + N_ARC            # rolls off it
    T0 = INTRO - 1 - F_BOOK
    assert T0 >= 90, T0

    # ---- reactions -------------------------------------------------------------------------------------------------------------------------------
    band_dip = lambda t: spring(t - F_BAND, 9.0, down=5, tau=11.0, period=24.0)             # px (world) the band sags
    books = lambda t: spring(t - F_BOOK, -0.03, down=2, tau=7.0, period=16.0)
    card = lambda t: spring(t - F_CARD, 0.04, down=2, tau=9.0, period=20.0)
    stick = lambda t: spring(t - F_STK, -0.015, down=3, tau=8.0, period=18.0)
    # the mug rocks to push the ball out, and wobbles when the ball lands in it (the landing frame is found below)

    # ---- the ball -------------------------------------------------------------------------------------------------------------------------------------
    # off the band: ride the sag until the band is back through straight, going up
    def band_pos(t):
        return (band_land[0], band_land[1] + band_dip(t))
    # the fall into the mug, after rolling over the joint: a plain projectile
    ang0, ang1 = math.atan2(ST_UP * 0 + (-math.sqrt(32.0 ** 2 - ST_UP ** 2)) * 0, 1), 0
    a_start = math.atan2((tip[1] + q_join * st_d[1] + ST_UP * st_n[1]) - jc[1], (tip[0] + q_join * st_d[0] + ST_UP * st_n[0]) - jc[0])
    a_leave = math.radians(-40.0)
    arc_pts = [(jc[0] + 32.0 * math.cos(a_start + (a_leave - a_start) * i / N_ARC), jc[1] + 32.0 * math.sin(a_start + (a_leave - a_start) * i / N_ARC)) for i in range(N_ARC + 1)]
    speed_leave = 2.9
    dirv = (-math.sin(a_leave), math.cos(a_leave))
    vx_, vy_ = dirv[0] * speed_leave, dirv[1] * speed_leave
    fall = [arc_pts[-1]]
    x_, y_ = arc_pts[-1]
    while y_ < mug_hide[1] and len(fall) < 60:
        x_, y_ = x_ + vx_, y_ + vy_
        vy_ += G
        fall.append((x_, y_))
    n_fall = len(fall) - 1
    F_IN = F_LEAVE + n_fall                 # reaches the hidden spot
    F_RIM = F_LEAVE + next(i for i, p in enumerate(fall) if p[1] >= 698.0)
    L = F_IN + 20
    mug_th = lambda t: spring(t - 2, 0.05, down=3, tau=10.0, period=20.0) + spring(t - F_RIM, -0.07, down=3, tau=5.0, period=13.0)

    b = Ball(L)
    for t in range(0, F_POP + 1):
        b.put(t, mug_hide)
    xe1 = 2.4
    # fit the first flight's height so its apex is 20 above the band
    best_h = None
    for h in range(60, 400, 4):
        pts = arc(mug_hide, band_land, N1, h, xe1)
        if min(p[1] for p in pts) <= band_land[1] - 22:
            best_h = h
            break
    assert best_h
    b.seg(F_POP, F_BAND, arc(mug_hide, band_land, N1, best_h, xe1))
    for t in range(F_BAND, F_UP + 1):
        b.put(t, band_pos(t))
    h2 = 30
    b.seg(F_UP, F_BOOK, arc(b.c[F_UP], book_hit, N2, h2))
    h3 = ((card_hit[1] - book_hit[1]) + 1.2 * N3) / 4
    b.seg(F_BOOK, F_CARD, arc(book_hit, card_hit, N3, h3))
    h4 = ((stick_pt(stick_land_q)[1] - card_hit[1]) + 1.5 * N4) / 4
    b.seg(F_CARD, F_STK, arc(card_hit, stick_pt(stick_land_q), N4, h4))
    s_roll, a_roll = roll_distance(F_JOIN - F_STK, 0.6, q_join - stick_land_q)
    for i, s in enumerate(s_roll):
        b.put(F_STK + i, stick_pt(stick_land_q + s), "roll")
    for i, p in enumerate(arc_pts):
        b.put(F_JOIN + i, p, "roll")
    for i, p in enumerate(fall):
        b.put(F_LEAVE + i, p, "air")
    for t in range(F_IN, L):
        u = smooth((t - F_IN) / 6.0)
        b.put(t, (fall[-1][0] + (mug_hide[0] - fall[-1][0]) * u, fall[-1][1] + (mug_hide[1] - fall[-1][1]) * u), "rest")
    b.put(L, b.c[0])
    b.mode[L] = b.mode[0]
    b.kick = {F_BOOK: 0.5 * 3.4 / 16.9, F_CARD: -0.5 * 4.5 / 16.9}
    for fr, a in ((F_BAND, 0.10), (F_BOOK, 0.08), (F_CARD, 0.08), (F_STK, 0.08)):
        b.squash(fr, a)
    # spin: the leftover to a whole number of turns goes into the hidden rest in the mug
    theta = b.spin()
    resid = theta[L] - 2 * math.pi * round(theta[L] / (2 * math.pi))
    a_, z_ = F_IN + 4, L - 1
    theta = [th - resid * (smooth((t - a_) / (z_ - a_)) if t <= z_ else 1.0) for t, th in enumerate(theta)]
    top = min(c[1] for c in b.c.values()) - 17.6

    # ---- numbers to check ------------------------------------------------------------------------------------------------------------------------------
    tc = lambda t: (t + T0) / 60.0
    names = [("mug rocks", 2), ("hops out of the mug", F_POP), ("lands on the band (it sags)", F_BAND), ("springs off the band", F_UP),
             ("ricochets off the books", F_BOOK), ("ricochets off the FIRST card", F_CARD), ("drops onto the blue stick", F_STK),
             ("reaches the white joint at the stick's low end", F_JOIN), ("rolls off it", F_LEAVE), ("drops into the mug (rim)", F_RIM)]
    print(f"{room}: cycle {L} frames ({L / 60:.2f} s), loop {L + 1} frames, journey starts at intro frame {T0} ({T0 / 60:.2f} s); the loop starts at cycle frame {INTRO - 1 - T0}")
    for name, t in names:
        print(f"  cycle {t:3d}  timecode {tc(t):5.2f} s  {name}")
    print(f"  highest point of the ball: y {top:.1f} ({phone_y(top):.0f} px on the phone frame); copy ends at {COPY_BOTTOM:.0f}: clearance {phone_y(top) - COPY_BOTTOM:.0f} px")
    print(f"  x range {min(c[0] for c in b.c.values()) - 17.6:.0f} to {max(c[0] for c in b.c.values()) + 17.6:.0f}")
    edge_d = lambda pts: min(min(segdist(p, card_edge[i], card_edge[i + 1]) for i in range(3)) for p in pts)
    pd_ = lambda pts: min(math.dist(p, q) for p in pts for q in posts)
    print(f"  hop out: {best_h} high, gravity {gravity(N1, best_h):.2f}; closest to FIRST card's edge {edge_d([b.c[t] for t in range(F_POP, F_BAND + 1)]):.1f}, to a post {pd_([b.c[t] for t in range(F_POP, F_BAND + 1)]):.1f} (needs 32)")
    print(f"  band to books: gravity {gravity(N2, h2):.2f}, to a post {pd_([b.c[t] for t in range(F_UP, F_BOOK + 1)]):.1f}; books to FIRST {gravity(N3, h3):.2f}; FIRST to stick {gravity(N4, h4):.2f}, closest to the card's edge {edge_d([b.c[t] for t in range(F_CARD + 3, F_STK + 1)]):.1f}")
    print(f"  fall into the mug: {n_fall} frames; spin: {theta[L] / (2 * math.pi):.2f} turns over the cycle (leftover {resid:+.2f} rad hidden in the mug)")
    if not write:
        return

    # ---- write -----------------------------------------------------------------------------------------------------------------------------------------
    ids = dict(ball="9:9619", scale="9:9621")
    loop, intro = f"{room} Loop", f"{room} Intro"
    piv = {}
    piv["mug"], _ = doc.wrap_run("9:9482", "9:9522", f"{room} Mug", (mug_pivot[0] - 679.0) / 0.85, (mug_pivot[1] - 676.0) / 0.85)      # inside a node at (679, 676) scaled 0.85
    piv["books"], _ = doc.wrap("9:9432", f"{room} Leaning Books", (books_pivot[0] - 581.0) / 0.85, (books_pivot[1] - 460.0) / 0.85)      # inside a node at (581, 460) scaled 0.85
    piv["stick"], _ = doc.wrap("9:9239", f"{room} Blue Stick", *stick_pivot)
    piv["card"], _ = doc.wrap("9:9272", f"{room} First Card Wobble", *card_pivot)
    # the ball hides in the mug behind a clip: everything above the mug's front rim
    clip_id = doc.new_id()
    floor_clip = doc.idx("9:10551")
    doc.lines[floor_clip:floor_clip] = [f'                <Shape y="697" name="{room} Mug Clip" id="{clip_id}">',
                                        f'                    <Rectangle width="9000" height="2000" originX="0.5" originY="1" name="Path" id="{doc.new_id()}"/>',
                                        "                </Shape>"]
    for shape in ("9:9622", "9:9628"):
        i = doc.idx(shape)
        j = doc.end(i)
        doc.lines[j:j] = [f'                                <ClippingShape sourceId="{clip_id}" name="Mug Clip" id="{doc.new_id()}"/>']
    round_ball(doc, intro, ("9:9622", "9:9630", "9:9631", "9:9633"))
    for oid in ("9:9628", "9:9257", "9:9272", "9:9481"):
        doc.drop_object(loop, oid)
    doc.drop_object(intro, "9:9628")
    ids["spin"], _ = doc.wrap_run("9:9622", "9:9628", f"{room} Ball Spin", 0.0, -17.572)
    pre = lambda fr: (mug_hide[0], mug_hide[1], 1.0, 1.0)
    band_vertex = "9:9613"
    pieces = [(piv["mug"], "rotation", mug_th, 0.0, None), (piv["books"], "rotation", books, 0.0, None),
              (piv["stick"], "rotation", stick, 0.0, None), (piv["card"], "rotation", card, 0.0, None),
              (band_vertex, "y", lambda t: band_dip(t) / 0.85, 0.0, None),
              (band_vertex, "x", lambda t: 2.5149 - 0.07 * band_dip(t), 2.5149, None)]
    emit_room(doc, room, b, theta, T0, ids, pre, pieces)


def card3_v1(doc, write):
    global BALL_CENTER
    room = "Chapter 1 Card 3"
    N = 432
    BALL_CENTER = 16.78
    Rb = 17.1
    mug_in = (722.0, 722.0)                 # hidden inside the mug (its front rim is at y 698)
    mug_hide = (737.0, 724.0)
    band_x = 827.0                          # between the two posts (they are at x 792 and 862, radius 14.9)
    band_top = 490.0 - 6.4 + 0.4            # the band's low point is y 490.0 and it is 12.75 thick
    book_land = (645.0, 473.9 - Rb)         # the leaning books' top edge
    shelf_land = (585.0, 509.6 - Rb)        # the left end of the shelf plank
    tip = (594.5, 591.0)
    shoulder = (tip[0] - 32.4 * math.sin(math.radians(22)), tip[1] - 32.4 * math.cos(math.radians(22)))
    low_joint = (671.0, 676.0)
    st_len = math.dist(tip, low_joint)
    st_d = ((low_joint[0] - tip[0]) / st_len, (low_joint[1] - tip[1]) / st_len)
    st_n = (st_d[1], -st_d[0])
    ST_UP = 22.6
    card_tap = (858.0, 538.6 - Rb)
    card_edge = [(830.2, 538.6), (820.1, 544.4), (761.6, 644.0), (767.9, 654.9)]
    books_pivot, stick_pivot, card_pivot, mug_pivot = (650.0, 508.0), low_joint, (795.0, 654.9), (737.0, 745.0)

    def stick_pt(q, th):
        c = (tip[0] + q * st_d[0] + ST_UP * st_n[0], tip[1] + q * st_d[1] + ST_UP * st_n[1])
        return rot(c, stick_pivot, th)

    F_POP, F_BAND, F_UP, F_BOOK, F_BOOK_UP = 34, 104, 114, 164, 172
    F_SHELF, F_EDGE, F_TIP, F_TIP_UP, F_STK, F_STK_END = 206, 214, 240, 246, 262, 306
    F_CARD, F_CARD_UP, F_IN = 354, 356, 406
    Q0, Q1 = 32.0, 104.0

    band = lambda f: spring(f - F_BAND, 9.0, down=5, tau=11.0, period=24.0)          # px the band's middle sags
    books = lambda f: spring(f - F_BOOK, 0.07, down=3, tau=9.0, period=20.0)
    stick = lambda f: spring(f - F_TIP, -0.045, down=4, tau=9.0, period=20.0)
    card = lambda f: spring(f - F_CARD, 0.035, down=3, tau=9.0, period=20.0)
    mug = lambda f: spring(f - F_POP, 0.05, down=3, tau=10.0, period=20.0) + spring(f - F_IN, -0.07, down=3, tau=5.0, period=13.0)

    b = Ball(N)
    for f in range(0, F_POP + 1):
        b.put(f, mug_hide)
    c_band = (band_x, band_top - Rb)
    b.seg(F_POP, F_BAND, arc(mug_hide, c_band, F_BAND - F_POP, 165, 1.8))
    for f in range(F_BAND, F_UP + 1):
        b.put(f, (c_band[0], c_band[1] + 0.85 * band(f)))
    b.seg(F_UP, F_BOOK, arc(b.c[F_UP], book_land, F_BOOK - F_UP, 48))
    for f in range(F_BOOK, F_BOOK_UP + 1):
        b.put(f, rot(book_land, books_pivot, books(f)))
    b.seg(F_BOOK_UP, F_SHELF, arc(b.c[F_BOOK_UP], shelf_land, F_SHELF - F_BOOK_UP, 40))
    for f in range(F_SHELF, F_EDGE + 1):
        t = (f - F_SHELF) / (F_EDGE - F_SHELF)
        b.put(f, (shelf_land[0] - 6.0 * t, shelf_land[1] + 2.0 * t * t))
    b.seg(F_EDGE, F_TIP, arc(b.c[F_EDGE], shoulder, F_TIP - F_EDGE, fall_height(F_TIP - F_EDGE)))
    for f in range(F_TIP, F_TIP_UP + 1):
        b.put(f, rot(shoulder, stick_pivot, stick(f)))
    b.seg(F_TIP_UP, F_STK, arc(b.c[F_TIP_UP], stick_pt(Q0, 0.0), F_STK - F_TIP_UP, 12))
    s_roll, _ = roll_distance(F_STK_END - F_STK, 0.5, Q1 - Q0)
    for i, s in enumerate(s_roll):
        b.put(F_STK + i, stick_pt(Q0 + s, 0.0))
    b.seg(F_STK_END, F_CARD, arc(b.c[F_STK_END], card_tap, F_CARD - F_STK_END, 70))
    for f in range(F_CARD, F_CARD_UP + 1):
        b.put(f, card_tap)
    b.seg(F_CARD_UP, F_IN, arc(card_tap, mug_in, F_IN - F_CARD_UP, 69, 0.55))
    for f in range(F_IN, N):
        b.put(f, mug_in)
    b.seg(N - 1, N - 1, [mug_hide]) if False else None
    # the last frames settle to the hidden spot the loop starts on
    for f in range(F_IN + 6, N):
        t = smooth((f - (F_IN + 6)) / (N - 1 - (F_IN + 6)))
        b.put(f, (mug_in[0] + (mug_hide[0] - mug_in[0]) * t, mug_in[1] + (mug_hide[1] - mug_in[1]) * t))
    for f, a in ((F_BAND, 0.10), (F_BOOK, 0.10), (F_SHELF, 0.10), (F_TIP, 0.10), (F_STK, 0.10), (F_CARD, 0.06)):
        b.squash(f, a)
    xs, ys = b.node()

    top = min(c[1] for c in b.c.values()) - 17.6
    flight1 = [b.c[f] for f in range(F_POP, F_BAND + 1)]
    flight6 = [b.c[f] for f in range(F_CARD_UP, F_IN + 1)]
    flight5 = [b.c[f] for f in range(F_STK_END, F_CARD + 1)]
    edge_d = lambda pts: min(min(segdist(p, card_edge[i], card_edge[i + 1]) for i in range(3)) for p in pts)
    print(f"{room}: loop {N} frames ({N / 60:.2f} s)")
    for name, f in (("ball hops out of the mug", F_POP), ("lands on the yellow band", F_BAND), ("springs off the band", F_UP),
                    ("lands on the leaning books", F_BOOK), ("leaves the books", F_BOOK_UP), ("lands on the shelf's left end", F_SHELF),
                    ("rolls off the shelf's left end", F_EDGE), ("lands on the blue stick's white tip", F_TIP), ("leaves the tip", F_TIP_UP),
                    ("lands on the blue stick", F_STK), ("leaves the stick's low end", F_STK_END), ("taps the FIRST card", F_CARD),
                    ("drops into the mug", F_IN)):
        print(f"  frame {f:3d}  loop {f / 60:5.2f} s  timecode {f / 60 + 3.2:5.2f} s  {name}")
    print(f"  highest point of the ball: y {top:.1f} ({phone_y(top):.0f} px on the phone frame); copy ends at {COPY_BOTTOM:.0f}: clearance {phone_y(top) - COPY_BOTTOM:.0f} px")
    print(f"  closest the ball's centre gets to the FIRST card's left edge: mug to band {edge_d(flight1):.1f}, stick to card {edge_d(flight5):.1f}, card to mug {edge_d(flight6):.1f} (ball radius 17)")
    posts = [(792.0, 486.0), (862.1, 486.0)]
    pd = lambda pts: min(math.dist(p, q) for p in pts for q in posts)
    print(f"  closest to a white post's centre (post radius 14.9 + ball 17 = 32): mug to band {pd(flight1):.1f}; band to books {pd([b.c[f] for f in range(F_UP, F_BOOK + 1)]):.1f}")
    print(f"  gravity: mug to band {gravity(F_BAND - F_POP, 165):.2f}, band to books {gravity(F_BOOK - F_UP, 48):.2f}, books to shelf {gravity(F_SHELF - F_BOOK_UP, 40):.2f}, stick to card {gravity(F_CARD - F_STK_END, 70):.2f}, card to mug {gravity(F_IN - F_CARD_UP, 69):.2f}")
    print(f"  x range {min(c[0] for c in b.c.values()) - 17.6:.0f} to {max(c[0] for c in b.c.values()) + 17.6:.0f}")
    if not write:
        return

    ids = dict(ball="9:9619", scale="9:9621", total_hl="9:9622")
    loop, intro = f"{room} Loop", f"{room} Intro"
    piv = {}
    piv["mug"], _ = doc.wrap_run("9:9482", "9:9522", f"{room} Mug", (mug_pivot[0] - 679.0) / 0.85, (mug_pivot[1] - 676.0) / 0.85)      # inside a node at (679, 676) scaled 0.85
    piv["books"], _ = doc.wrap("9:9432", f"{room} Leaning Books", (books_pivot[0] - 581.0) / 0.85, (books_pivot[1] - 460.0) / 0.85)      # inside a node at (581, 460) scaled 0.85
    piv["stick"], _ = doc.wrap("9:9239", f"{room} Blue Stick", *stick_pivot)
    piv["card"], _ = doc.wrap("9:9272", f"{room} First Card Wobble", *card_pivot)
    # the ball hides in the mug behind a clip: everything above the mug's front rim
    clip_id = doc.new_id()
    floor_clip = doc.idx("9:10551")
    doc.lines[floor_clip:floor_clip] = [f'                <Shape y="697" name="{room} Mug Clip" id="{clip_id}">',
                                        f'                    <Rectangle width="9000" height="2000" originX="0.5" originY="1" name="Path" id="{doc.new_id()}"/>',
                                        "                </Shape>"]
    for shape in ("9:9622", "9:9628"):
        i = doc.idx(shape)
        j = doc.end(i)
        doc.lines[j:j] = [f'                                <ClippingShape sourceId="{clip_id}" name="Mug Clip" id="{doc.new_id()}"/>']
    round_ball(doc, intro, ("9:9622", "9:9630", "9:9631", "9:9633"))
    for oid in ("9:9628", "9:9257", "9:9272", "9:9481"):
        doc.drop_object(loop, oid)
    doc.drop_object(intro, "9:9628")
    doc.set_duration(loop, N)
    fr_i, fr_l = range(INTRO), range(N)
    hide_x, hide_y = mug_hide[0], mug_hide[1] + BALL_CENTER
    px = plane_x(room)
    doc.set_prop(intro, ids["ball"], "x", bake({f: hide_x + px(f) for f in fr_i}, fr_i))
    doc.set_prop(intro, ids["ball"], "y", [(0, hide_y, "hold")])
    doc.set_prop(loop, ids["ball"], "x", bake(xs, fr_l))
    doc.set_prop(loop, ids["ball"], "y", bake(ys, fr_l))
    for prop, ser in (("scaleX", b.sx), ("scaleY", b.sy)):
        doc.set_prop(intro, ids["scale"], prop, [(0, 1.0, "hold"), (INTRO - 1, 1.0, "hold")])
        doc.set_prop(loop, ids["scale"], prop, bake(ser, fr_l))

    def both(oid, prop, fn, rest):
        doc.set_prop(loop, oid, prop, bake(series(0, N, fn), fr_l))
        doc.set_prop(intro, oid, prop, [(0, rest, "hold"), (INTRO - 1, rest, "hold")])
    both(piv["mug"], "rotation", mug, 0.0)
    both(piv["books"], "rotation", books, 0.0)
    both(piv["stick"], "rotation", stick, 0.0)
    both(piv["card"], "rotation", card, 0.0)
    # the band's middle vertex sags under the ball (it was already keyed this way by the old loop)
    band_vertex = "9:9613"
    doc.set_prop(loop, band_vertex, "y", bake(series(0, N, lambda f: 5.0702 + band(f) / 0.85), fr_l))
    doc.set_prop(loop, band_vertex, "x", bake(series(0, N, lambda f: 2.5149 - 0.07 * band(f)), fr_l))
    doc.rebuild_waiting(room)



def card4_v1(doc, write):
    global BALL_CENTER
    room = "Chapter 1 Card 4"
    N = 400
    BALL_CENTER = 16.78
    Rb = 17.1
    A = (721.0, 511.2 - Rb)           # the crossword flower's checker head
    B = (786.0, 532.2 - Rb)           # the yellow S hexagon's flat top
    C = (680.0, 548.2 - Rb)           # the purple leaf's top edge
    base_y = 634.2                    # where the stems meet the pot's rim
    pivots = dict(cross=(720.9, base_y), hexa=(765.5, base_y), leaf=(714.5, 633.0))
    HOP, STAY = 40, 4                 # frames in the air, frames on the flower before the next hop: a steady beat of 44
    F_GO = 72
    legs = [("cross", A, "hexa", B, 38), ("hexa", B, "leaf", C, 68), ("leaf", C, "cross", A, 26)]
    sched = []                       # (frame landed, flower)
    f = F_GO
    takeoffs = []
    for rnd in range(2):
        for src, ps, dst, pd_, h in legs:
            takeoffs.append((f, f + HOP, src, pd_, h, dst))
            sched.append((f + HOP, dst))
            f += HOP + STAY
    F_END = takeoffs[-1][1]

    dip = {"cross": 0.04, "hexa": 0.04, "leaf": 0.04}
    land = {}
    for fl, who in sched:
        land.setdefault(who, []).append(fl)
    def react(who, fr):
        return sum(spring(fr - fl, 1.0, down=3, tau=8.0, period=16.0) for fl in land.get(who, []))
    sway = lambda fr: 0.014 * (1 - math.cos(2 * math.pi * fr / 48)) / 2 if fr < F_GO - 24 else (
        0.014 * (1 - math.cos(2 * math.pi * (F_GO - 24) / 48)) / 2 * (1 - smooth((fr - (F_GO - 24)) / 24)) if fr < F_GO else 0.0)
    scale_y = {w: (lambda fr, w=w: 1 - dip[w] * react(w, fr)) for w in dip}
    rotation = {"cross": lambda fr: sway(fr) + 0.02 * react("cross", fr), "hexa": lambda fr: 0.025 * react("hexa", fr), "leaf": lambda fr: -0.025 * react("leaf", fr)}

    b = Ball(N)
    pos = {"cross": A, "hexa": B, "leaf": C}
    contact_y = {"cross": 511.2, "hexa": 532.2, "leaf": 548.2}
    def ride(who, fr):
        p = pos[who]
        sy = scale_y[who](fr)
        return (p[0], p[1] + (1 - sy) * (base_y - contact_y[who]))
    cur = "cross"
    fr = 0
    for (fl, fland, ps, pd_, h, dst) in takeoffs:
        for g in range(fr, fl + 1):
            b.put(g, ride(cur, g))
        pts = arc(b.c[fl], ride(dst, fland), fland - fl, h)
        b.seg(fl, fland, pts)
        cur = dst
        fr = fland
    for g in range(fr, N):
        b.put(g, ride(cur, g))
    for fl, who in sched:
        b.squash(fl, 0.10)
    xs, ys = b.node()

    top = min(c[1] for c in b.c.values()) - 17.6
    print(f"{room}: loop {N} frames ({N / 60:.2f} s)")
    names = {"cross": "crossword flower", "hexa": "yellow S hexagon", "leaf": "purple leaf"}
    print(f"  rest on the crossword flower until frame {F_GO}")
    for fl, fland, ps, pd_, h, dst in takeoffs:
        print(f"  frame {fl:3d} hop off the {names[ps]}; frame {fland:3d} lands on the {names[dst]}  (loop {fland / 60:5.2f} s, timecode {fland / 60 + 3.2:5.2f} s; arc {h} high, gravity {gravity(HOP, h):.2f})")
    print(f"  highest point of the ball: y {top:.1f} ({phone_y(top):.0f} px on the phone frame); copy ends at {COPY_BOTTOM:.0f}: clearance {phone_y(top) - COPY_BOTTOM:.0f} px")
    head_top = 511.2
    cl = min(c[1] for f_, c in b.c.items() if 701.8 - 17 < c[0] < 740 + 17)
    over = [(f_, c) for f_, c in b.c.items() if 701.8 - 14 < c[0] < 740 + 14 and c[1] + 17 > head_top + 0.5 and not (abs(c[0] - A[0]) < 1 and abs(c[1] - A[1]) < 6)]
    print(f"  frames where the ball is in the checker head (should be none): {[f_ for f_, _ in over][:5]}")
    print(f"  x range {min(c[0] for c in b.c.values()) - 17.6:.0f} to {max(c[0] for c in b.c.values()) + 17.6:.0f}")
    if not write:
        return

    loop, intro = f"{room} Loop", f"{room} Intro"
    ball_id, scale_id = "9:11187", "9:11189"
    piv = {}
    piv["cross"], _ = doc.wrap("9:11138", f"{room} Crossword Flower", pivots["cross"][0] - 669.0, pivots["cross"][1] - 489.0)
    piv["hexa"], _ = doc.wrap("9:10996", f"{room} S Flower", pivots["hexa"][0] - 669.0, pivots["hexa"][1] - 489.0)
    piv["leaf"], _ = doc.wrap("9:11075", f"{room} Purple Leaf", pivots["leaf"][0] - 669.0, pivots["leaf"][1] - 489.0)
    round_ball(doc, intro, ("9:11190", "9:11198", "9:11199", "9:11201"))
    doc.drop_object(loop, "9:11138")
    doc.set_duration(loop, N)
    fr_i, fr_l = range(INTRO), range(N)
    px = plane_x(room)
    hx, hy = A[0], A[1] + BALL_CENTER
    doc.set_prop(intro, ball_id, "x", bake({f_: hx + px(f_) for f_ in fr_i}, fr_i))
    doc.set_prop(intro, ball_id, "y", [(0, hy, "hold")])
    doc.set_prop(loop, ball_id, "x", bake(xs, fr_l))
    doc.set_prop(loop, ball_id, "y", bake(ys, fr_l))
    for prop, ser in (("scaleX", b.sx), ("scaleY", b.sy)):
        doc.set_prop(intro, scale_id, prop, [(0, 1.0, "hold"), (INTRO - 1, 1.0, "hold")])
        doc.set_prop(loop, scale_id, prop, bake(ser, fr_l))

    def both(oid, prop, fn, rest):
        doc.set_prop(loop, oid, prop, bake(series(0, N, fn), fr_l))
        doc.set_prop(intro, oid, prop, [(0, rest, "hold"), (INTRO - 1, rest, "hold")])
    for w in ("cross", "hexa", "leaf"):
        both(piv[w], "scaleY", scale_y[w], 1.0)
        both(piv[w], "rotation", rotation[w], 0.0)
    doc.rebuild_waiting(room)


def main(argv):
    cards = [int(c) for c in argv[argv.index("--cards") + 1].split(",")] if "--cards" in argv else [2, 3, 4]
    doc = Doc(SCENE)
    if "--write" in argv:
        card1_spin(doc)
    for c in cards:
        {2: card2, 3: card3, 4: card4_v1}[c](doc, "--write" in argv)
    if "--write" in argv:
        doc.save()
        print("wrote", SCENE)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
