"""One time (2026-11-02, history like loading_start.py): new ball loops for Chapter 1 cards 2, 3 and 4 (finesse round 4), and the rest-window fix to card 1's spin.

    python3 tools/ch1_cards_234.py --cards 2            dry run: prints each beat and the clearances, writes nothing
    python3 tools/ch1_cards_234.py --cards 2 --write    rewrite chapters/ch1/scene.rml

Shared by the three rooms: the ball arrives with its room, already at its home spot (no roll-in, no pop), the loop starts the moment
the intro ends, the ball has weight (steady gravity in every flight, a squash on every landing), and the pieces it touches react a
little and settle (a dip with a spring back, a rock, a wobble), each one turning about its own pivot. A reaction starts on the frame
of the contact and the ball rides the piece while it moves. The ball's position is written one key per frame, like the other
rooms' baked arcs. The old roll-in (x -80 at 2.30 to 3.05 s, then the 0.15 s pop) is gone from the intros.

The three rooms were rewritten (rounds 3 and 4) on one framework: each room is a cycle of the ball's journey that starts inside the
intro as soon as the room has landed; the Loop is the same cycle picked up at the intro's last frame (emit_room), so the loop closes on
the pose the intro ends on. The ball turns about its own centre (Ball.spin; "Ball Spin" pivot). Rebuild from the file as it was before
this work (git show b409b42~1:YIG2026/rive/chapters/ch1/scene.rml) to run it: it wraps pieces in pivots and so is not safe to run twice.

Times in the notes are Finesse-panel timecodes: the loop's time plus 3.2 s (the intro).
"""
import math
import sys

from ball_motion import G, Path, arc, bezier, fall_height, gravity, pulse, release, rot, roll_distance, smooth, speed_profile, ease_in, spring
from ball_physics import G as GP
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


def emit_room(doc, room, b, theta, T0, ids, pre, pieces, Ps=0):
    """Write a room whose ball journey starts at intro frame T0 and then repeats as the loop (picked up at the intro's last frame).

    b: the Ball over cycle frames 0 to L - 1 with c[L] = c[Ps]; theta: its turn at cycle frames 0 to L (the periodic part, Ps to L, a whole
    number of turns apart); ids: dict with ball, scale, spin (node ids); pre(f): (x, y, scaleX, scaleY) of the ball's centre on intro frames
    before T0; pieces: [(object id, property, fn(cycle frame), rest value, extra(intro frame) or None)]. Everything must be at rest on cycle
    frames Ps and L - 1, so the loop closes. Ps is where the repeating part of the cycle starts: frames before it (a lead-in that
    only the first visit plays, in the intro) are not part of the loop."""
    L = b.n
    Lp = L - Ps
    assert T0 <= INTRO - 1
    loop, intro = f"{room} Loop", f"{room} Intro"
    phase0 = INTRO - 1 - T0
    assert Ps <= phase0 < L
    px = plane_x(room)
    turns = theta[L] - theta[Ps]
    assert abs(turns / (2 * math.pi) - round(turns / (2 * math.pi))) < 1e-6, turns
    idx = lambda k: Ps + ((phase0 - Ps + k) % Lp)
    wraps = lambda k: (phase0 - Ps + k) // Lp
    fr_i, fr_l = range(INTRO), range(Lp + 1)
    ix, iy, isx, isy, ith = {}, {}, {}, {}, {}
    for f in fr_i:
        if f < T0:
            x, y, sx, sy = pre(f)
            th = 0.0
        else:
            t = f - T0
            (x, y), sx, sy, th = b.c[t], b.sx[t], b.sy[t], theta[t]
        ix[f], iy[f], isx[f], isy[f], ith[f] = x + px(f), y + BALL_CENTER, sx, sy, th
    lx = {k: b.c[idx(k)][0] for k in fr_l}
    ly = {k: b.c[idx(k)][1] + BALL_CENTER for k in fr_l}
    lsx = {k: b.sx[idx(k)] for k in fr_l}
    lsy = {k: b.sy[idx(k)] for k in fr_l}
    lth = {k: theta[idx(k)] + wraps(k) * turns for k in fr_l}
    doc.set_duration(loop, Lp + 1)
    for prop, i_ser, l_ser in (("x", ix, lx), ("y", iy, ly)):
        doc.set_prop(intro, ids["ball"], prop, bake(i_ser, fr_i))
        doc.set_prop(loop, ids["ball"], prop, bake(l_ser, fr_l))
    for prop, i_ser, l_ser in (("scaleX", isx, lsx), ("scaleY", isy, lsy)):
        doc.set_prop(intro, ids["scale"], prop, bake(i_ser, fr_i))
        doc.set_prop(loop, ids["scale"], prop, bake(l_ser, fr_l))
    doc.set_prop(intro, ids["spin"], "rotation", bake(ith, fr_i))
    doc.set_prop(loop, ids["spin"], "rotation", bake(lth, fr_l))
    for oid, prop, fn, rest, extra in pieces:
        assert abs(fn(Ps) - rest) < 1e-6 and abs(fn(L - 1) - rest) < 1e-3, (oid, prop, fn(Ps), fn(L - 1), rest)
        iser = {f: (fn(max(f - T0, 0)) + (extra(f) if extra else 0.0)) for f in fr_i}
        lser = {k: fn(idx(k)) for k in fr_l}
        doc.set_prop(intro, oid, prop, bake(iser, fr_i))
        doc.set_prop(loop, oid, prop, bake(lser, fr_l))
    doc.rebuild_waiting(room)


def dip(t, f0, depth, T):
    """A single smooth dip that starts at frame f0, reaches `depth` halfway and is back at f0 + T: no overshoot, one turning point."""
    u = t - f0
    return depth * math.sin(math.pi * u / T) ** 2 if 0 < u < T else 0.0


smooth_dip = dip


def spring_fade(k, depth, down=3, tau=10.0, period=18.0, T=60.0):
    """spring() without its abrupt cut: the tail dies away smoothly and is gone at T frames after the contact."""
    if k <= 0:
        return 0.0
    if k <= down:
        return depth * math.sin(0.5 * math.pi * k / down)
    u = k - down
    if u >= T:
        return 0.0
    w = 2 * math.pi / period
    v = depth * math.exp(-u / tau) * (math.cos(w * u) + math.sin(w * u) / (w * tau))
    return v * (1 - smooth((u - (T - 12.0)) / 12.0))


def card2(doc, write):
    """Slide down, climb back up, on the physics (finesse round 5). The pencil topples into place and knocks the stack; the top block
    teeters like a seesaw and rolls the ball off onto the purple bar; from there the path is simulated (ball_physics.py): one gravity,
    every contact keeps 70 to 90 percent of its speed, a roll speeds up by G times the slope. The ball lands on the bar, bounces into
    the pencil, falls onto the yellow stick and rolls down it, comes off its low end onto the floor line moving left, rolls a short way
    and stops, pauses, then rolls back right along the floor line (behind TOTAL, behind the C block) to the pencil's foot, and climbs
    back up the right side in hops."""
    from ball_physics import Circ, Seg, build_path, flight, norm, piece_at, simulate, sub, mul
    room = "Chapter 1 Card 2"
    Rb = 17.1
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
    dom_pivot = (697.0, 572.5)
    c_pivot = (780.2, 711.8)
    c_top = 646.6
    slab_top = 572.7
    floor_c = 711.8 - R
    total_poly = [(706.7, 711.8), (655.0, 711.8), (649.2, 701.6), (703.7, 608.6), (713.2, 603.2), (764.9, 603.2), (770.7, 613.4), (716.2, 706.4)]

    def bar_pt(p, th):
        c = (bar_c[0] + p * bar_d[0] + BAR_UP * bar_n[0], bar_c[1] + p * bar_d[1] + BAR_UP * bar_n[1])
        return rot(c, bar_pivot, th)

    def bar_p_at(x):
        return (x - bar_c[0] - BAR_UP * bar_n[0]) / bar_d[0]

    def stick_pt(q, th):
        c = (st_a[0] + q * st_d[0] + ST_UP * st_n[0], st_a[1] + q * st_d[1] + ST_UP * st_n[1])
        return rot(c, j_mid, th)

    # ---- the teeter: the block rocks on its joint, tips, and the ball rolls off its right end (a roll speeds up by G times the slope) ----
    # three swings of a pendulum, eased through cosines (smooth through the middle, still only at the ends): a small rock right, a bigger
    # rock back left, then a third swing right that goes past the balance point and tips; the ball rolls off while it tips
    swings_ = [(19, 0.04), (39, -0.07), (68, 0.40)]
    TIP = swings_[-1][1]

    def th_base(t):
        t0, v0 = 0, 0.0
        for te, ve in swings_:
            if t <= te:
                return v0 + (ve - v0) * (1 - math.cos(math.pi * (t - t0) / (te - t0))) / 2
            t0, v0 = te, ve
        return TIP
    EDGE_U = 720.0
    us, u, v = [], home_u, 0.0
    t_off = None
    for t in range(0, 120):
        us.append(u)
        if u >= EDGE_U:
            t_off = t
            break
        v += GP * math.sin(th_base(t))
        u += v
    assert t_off, "the ball never rolls off"
    T_PEAK = swings_[-1][0]
    assert t_off <= T_PEAK, (t_off, T_PEAK)
    th_main = lambda t: th_base(t) if t <= T_PEAK else release(t - T_PEAK, TIP, tau=10.0, period=30.0)

    def on_block(u_, th):
        return rot((u_, block_top - R), J_top, th)
    p_off = on_block(us[t_off], th_main(t_off))
    p_prev = on_block(us[t_off - 1], th_main(t_off - 1))
    v_off = (p_off[0] - p_prev[0], p_off[1] - p_prev[1])

    # ---- the path after the block, simulated ----------------------------------------------------------------------------------------------
    def seg_c(c0, c1, n, name, e):
        return Seg(sub(c0, mul(n, Rb)), sub(c1, mul(n, Rb)), name, e=e, kt=0.95, n=n)
    s_bar = seg_c(bar_pt(bar_p_at(724.0), 0.0), bar_pt(bar_p_at(792.0), 0.0), (bar_n[0], bar_n[1]), "bar", 0.72)
    pd = unit_((T[0] - E[0], T[1] - E[1]))
    n_wall = (-pd[1], pd[0])
    c_wall = bar_pt(bar_p_at(792.0), 0.0)
    w0 = sub(c_wall, mul(n_wall, Rb))
    s_wall = Seg((w0[0] - 200 * pd[0], w0[1] - 200 * pd[1]), (w0[0] + 200 * pd[0], w0[1] + 200 * pd[1]), "pencil", e=0.8, kt=0.95, n=n_wall)
    s_jmid = Circ(j_mid, 17.35, "joint", e=0.7)
    st_up = (-st_n[0], -st_n[1]) if st_n[1] > 0 else st_n
    s_stick = seg_c(stick_pt(0.0, 0.0), stick_pt(st_len, 0.0), st_up, "stick", 0.2)
    ev1 = simulate(p_off, v_off, 0.0, [s_bar, s_wall], max_events=3)
    k_pen = next(i for i, e in enumerate(ev1) if e[0] == "hit" and e[2].name == "pencil")
    ev1 = ev1[:k_pen + 1]
    ev2 = simulate(ev1[-1][3], ev1[-1][5], ev1[-1][1], [s_wall, s_jmid, s_stick], max_events=5)
    events = ev1 + ev2
    hits = [e for e in events if e[0] == "hit"]
    assert [h[2].name for h in hits][:3] == ["bar", "pencil", "stick"], [h[2].name for h in hits]
    assert events[-1][0] == "leave" and any(e[0] == "roll" for e in events), events[-3:]
    path = build_path(events, p_off, v_off, 0.0)
    t_l, p_l, v_l = events[-1][1], events[-1][2], events[-1][3]            # leaves the stick's low end
    tau = (-v_l[1] + math.sqrt(v_l[1] ** 2 + 2 * GP * (floor_c - p_l[1]))) / GP
    t_fl = t_l + tau                                                          # lands on the floor line (sim time)
    x_fl = p_l[0] + v_l[0] * tau
    vx_roll = 0.80 * v_l[0]                                                   # the floor takes the fall and keeps most of the sideways speed
    MU = 0.50                                                                 # slows and stops on the floor
    tau_s = abs(vx_roll) / MU
    x_stop = x_fl + vx_roll * tau_s / 2

    # ---- when things happen (cycle frames; the Finesse timecode is the intro's journey start + frame / 60) ------------------------------
    T_BAR, T_PEN, T_STK = (t_off + hits[i][1] for i in range(3))
    F_BAR, F_PEN, F_STK = round(T_BAR), round(T_PEN), round(T_STK)
    roll_ev = next(e for e in events if e[0] == "roll")
    F_LOW = round(t_off + roll_ev[2])                                       # off the stick's low end
    tl_c = t_off + t_fl                                                       # landing on the floor (fractional cycle frame)
    F_FL = math.ceil(tl_c)
    F_STOP = math.ceil(tl_c + tau_s)
    PAUSE1, PAUSE2 = 16, 18
    F_GO = F_STOP + PAUSE1
    # rolling back right along the floor line: speeds up, cruises, slows to a stop at the pencil's foot
    foot = (819.0, floor_c)
    A_RUN, V_RUN, MU_RUN = 0.10, 3.6, 0.13
    d_acc, d_dec = V_RUN ** 2 / (2 * A_RUN), V_RUN ** 2 / (2 * MU_RUN)
    D_run = foot[0] - x_stop
    d_cru = D_run - d_acc - d_dec
    assert d_cru > 0, d_cru
    t_acc, t_cru, t_dec = V_RUN / A_RUN, d_cru / V_RUN, V_RUN / MU_RUN

    def run_x(k):
        if k <= 0:
            return x_stop
        if k <= t_acc:
            return x_stop + 0.5 * A_RUN * k * k
        if k <= t_acc + t_cru:
            return x_stop + d_acc + V_RUN * (k - t_acc)
        j = min(k - t_acc - t_cru, t_dec)
        return x_stop + d_acc + d_cru + V_RUN * j - 0.5 * MU_RUN * j * j
    D_RUN = math.ceil(t_acc + t_cru + t_dec)
    F_FOOT = F_GO + D_RUN
    F_UP = F_FOOT + PAUSE2
    f_tap = next(t for t in range(F_GO, F_FOOT + 1) if run_x(t - F_GO) + 17.0 >= 747.6)
    f_hole0 = F_GO - 1
    f_hole1 = next(t for t in range(F_GO, F_FOOT + 1) if run_x(t - F_GO) >= 762.0)

    def parab(p0, p1, ha):
        """A flight at the project gravity from p0 to p1 that peaks ha above the higher of the two: (frames, points)."""
        apex_y = min(p0[1], p1[1]) - ha
        vy0 = -math.sqrt(2 * GP * (p0[1] - apex_y))
        n = round(-vy0 / GP + math.sqrt(2 * (p1[1] - apex_y) / GP))
        vyn = ((p1[1] - p0[1]) - 0.5 * GP * n * n) / n
        return n, [(p0[0] + (p1[0] - p0[0]) * i / n, p0[1] + vyn * i + 0.5 * GP * i * i) for i in range(n + 1)]
    bar_stops = [bar_p_at(x) for x in (794.0, 774.0, 750.0)]
    c_land = (790.0, c_top - R)
    slab_land = (806.0, slab_top - R)
    top_land_u = 714.0
    top_land = (top_land_u, block_top - R)
    pos_h5 = bar_pt(bar_stops[2], 0.0)
    ends = [c_land, slab_land, bar_pt(bar_stops[0], 0.0), bar_pt(bar_stops[1], 0.0), pos_h5, top_land]
    starts = [foot] + ends[:5]
    HA = [26, 26, 22, 20, 20]
    HOP, pts_hop = [], []
    for i in range(5):
        n, pts = parab(starts[i], ends[i], HA[i])
        HOP.append((n, HA[i]))
        pts_hop.append(pts)
    # the climb's last step: the smallest hop that clears the block's corner
    for h6 in range(8, 44, 2):
        n, pts = parab(starts[5], ends[5], h6)
        if min(polydist(p, block_poly) for p in pts[:-3]) >= 16.8:
            break
    else:
        raise AssertionError("no clear last hop")
    HOP.append((n, h6))
    pts_hop.append(pts)
    STAY = 4
    leave, land = [], []
    f = F_UP
    for n, h in HOP:
        leave.append(f)
        land.append(f + n)
        f += n + STAY
    F_TOP = land[-1]
    L = F_TOP + 40
    T0 = INTRO - 1 - F_BAR
    assert T0 >= 107, T0

    # ---- reactions (functions of the cycle frame) -------------------------------------------------------------------------------------------
    bar_hits = [(F_BAR, -0.03)] + [(land[i], -0.012) for i in (2, 3, 4)]
    bar = lambda t: dip(t, F_BAR, -0.03, 36) + sum(dip(t, fl, d, 44) for fl, d in bar_hits[1:])
    domino = lambda t: 0.05 * math.exp(-(t - F_BAR - 4) / 14.0) * math.sin(2 * math.pi * (t - F_BAR - 4) / 22.0) if t > F_BAR + 4 else 0.0
    joint_p = lambda t: 0.10 * pulse(t - land[1], down=3, tau=7.0, period=16.0)
    low_p = lambda t: 0.14 * pulse(t - F_LOW, down=3, tau=7.0, period=16.0)
    stick = lambda t: spring(t - F_STK, -0.03, down=4, tau=9.0, period=20.0)
    pencil = lambda t: dip(t, F_PEN, 0.02, 30) + dip(t, F_FOOT, 0.012, 30)
    slab_dip = lambda t: spring(t - land[1], 2.5, down=3, tau=8.0, period=18.0)
    block_th = lambda t: th_main(t) + dip(t, F_TOP, 0.03, 36)
    hole_x = lambda t: 0.0 if f_hole0 <= t <= f_hole1 else 1500.0

    # ---- the ball -----------------------------------------------------------------------------------------------------------------------------
    b = Ball(L)
    for t in range(0, t_off + 1):
        b.put(t, on_block(us[t], th_main(t)), "roll")
    for t in range(t_off + 1, F_FL):
        p, m = piece_at(path, t - t_off)
        b.put(t, p, m)
    for t in range(F_FL, F_GO + 1):                      # lands on the floor line, rolls a short way left, slows and stops, pauses
        tt = min(t - tl_c, tau_s)
        b.put(t, (x_fl + vx_roll * tt - math.copysign(0.5 * MU * tt * tt, vx_roll), floor_c), "roll" if t <= F_STOP else "rest")
    for t in range(F_GO + 1, F_FOOT + 1):                # rolls back right along the floor line, behind TOTAL and the C block, to the pencil's foot
        b.put(t, (run_x(t - F_GO), floor_c), "roll" if t < F_FOOT else "rest")
    for t in range(F_FOOT, F_UP + 1):
        b.put(t, (run_x(D_RUN + 1), floor_c) if False else foot, "rest")
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
        pts = [(p[0], p[1]) for p in pts_hop[i]]
        pts[-1] = pos_on(i, z_)
        b.seg(a_, z_, pts)
    # settle on top: it rolls back to its spot as the block rocks and comes to rest
    for t in range(F_TOP, L):
        u_ = top_land_u - (top_land_u - home_u) * smooth((t - F_TOP - 8) / 18.0)
        b.put(t, on_block(u_, block_th(t)), "roll" if F_TOP + 8 <= t <= F_TOP + 26 else "rest")
    b.put(L, b.c[0])
    b.mode[L] = b.mode[0]
    assert math.dist(b.c[L - 1], b.c[0]) < 0.05, (b.c[L - 1], b.c[0])
    for fr, a in ((F_BAR, 0.10), (F_PEN, 0.10), (F_STK, 0.10), (F_LOW, 0.10), (F_FL, 0.12), (F_FOOT, 0.12)):
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
    names = [("pencil lands and knocks the stack (intro)", -3), ("block starts to teeter", 0), ("block tips and the ball rolls off its end", t_off),
             ("lands on the purple bar", F_BAR), ("hits the pencil", F_PEN), ("lands on the yellow stick", F_STK), ("off the stick's low end", F_LOW),
             ("lands on the floor line, moving left", F_FL), ("stops", F_STOP), ("starts back right", F_GO),
             ("goes behind the C block (tap)", f_tap), ("stops at the pencil's foot", F_FOOT)]
    names += [(f"climb hop {i + 1} lands", land[i]) for i in range(6)]
    print(f"{room}: cycle {L} frames ({L / 60:.2f} s), loop {L + 1} frames, journey starts at intro frame {T0} ({T0 / 60:.2f} s); the loop starts at cycle frame {INTRO - 1 - T0}")
    for name, t in names:
        print(f"  cycle {t:3d}  timecode {tc(t):5.2f} s (and +{L / 60:.2f} s each loop)  {name}")
    print(f"  highest point of the ball: y {top:.1f} ({phone_y(top):.0f} px on the phone frame); copy ends at {COPY_BOTTOM:.0f}: clearance {phone_y(top) - COPY_BOTTOM:.0f} px")
    print(f"  x range {min(c[0] for c in b.c.values()) - 17.6:.0f} to {max(c[0] for c in b.c.values()) + 17.6:.0f}, y to {max(c[1] for c in b.c.values()) + 17.6:.0f}")
    print(f"  floor: lands at x {x_fl:.0f} moving {vx_roll:.1f} per frame, stops at x {x_stop:.0f} (the ball's left edge {x_stop - 17:.0f}); run back {D_run:.0f} px: {t_acc:.0f} frames speeding up to {V_RUN}, {t_cru:.0f} cruising, {t_dec:.0f} slowing")
    print(f"  hole in the clip (ball behind TOTAL) on frames {f_hole0} to {f_hole1}; TOTAL spans x {min(p[0] for p in total_poly):.0f} to {max(p[0] for p in total_poly):.0f}")
    print(f"  spin: {theta[L] / (2 * math.pi):.2f} turns over the cycle (leftover {resid:+.2f} rad put into the last hop)")
    print("  climb hops (frames, height above the higher end): " + ", ".join(f"{n} / {h}" for n, h in HOP))
    if not write:
        return

    # ---- write ----------------------------------------------------------------------------------------------------------------------------------
    ids = dict(ball="9:8040", scale="9:8042", pencil="9:7760", bar="9:7865", domino="9:7872", stick="9:7655", jmid="9:7643",
               jlow="9:7649", cblock="9:7719", slab="9:7947", blocka="9:7686")
    old = ["9:7659", "9:7748", "9:8049", "9:8043", "9:8054", "9:8052", "9:8051"]
    loop, intro = f"{room} Loop", f"{room} Intro"
    piv = {}
    piv["pencil"], _ = doc.wrap(ids["pencil"], f"{room} Pencil", *T)
    piv["bar"], _ = doc.wrap(ids["bar"], f"{room} Bar", *bar_pivot)
    piv["domino"], _ = doc.wrap(ids["domino"], f"{room} Domino", *dom_pivot)
    piv["stick"], _ = doc.wrap(ids["stick"], f"{room} Yellow Stick", j_mid[0] - 649.0, j_mid[1] - 463.5)      # inside a node at (649, 463.5)
    piv["cblock"], _ = doc.wrap(ids["cblock"], f"{room} C Block", *c_pivot)
    piv["block"], _ = doc.wrap(ids["blocka"], f"{room} Block Seesaw", *J_top)                                  # inside the Top Piece's Art node
    # the ball turns about its own centre; its floor clip stays, and a second clip with TOTAL's outline cut out of it (evenOdd) hides
    # the ball while it runs behind the card; that hole is slid 1500 to the right except for that run
    spin_id, _ = doc.wrap_run("9:8043", "9:8049", f"{room} Ball Spin", 0.0, -17.572)
    hole_id = doc.new_id()
    floor_clip = doc.idx("9:8830")
    verts = [f'                        <StraightVertex x="{num_(p[0])}" y="{num_(p[1])}" id="{doc.new_id()}"/>' for p in total_poly]
    doc.lines[floor_clip:floor_clip] = ([f'                <Shape name="{room} TOTAL Hole" id="{hole_id}">',
                                         f'                    <Rectangle width="30000" height="30000" originX="0.5" originY="0.5" name="Path" id="{doc.new_id()}"/>',
                                         f'                    <PointsPath isClosed="true" id="{doc.new_id()}">'] + verts
                                        + ["                    </PointsPath>", "                </Shape>"])
    for shape in ("9:8043", "9:8049"):
        i = doc.idx(shape)
        j = doc.end(i)
        doc.lines[j:j] = [f'                                <ClippingShape sourceId="{hole_id}" fillRule="evenOdd" name="TOTAL Hole" id="{doc.new_id()}"/>']
    for oid in old:
        doc.drop_object(loop, oid)
        doc.drop_object(intro, oid)
    doc.set_prop(intro, "9:7748", "opacity", [(0, 0.0, "hold")])
    ids["spin"] = spin_id

    # the intro: the block drops in with the ball on it; the pencil tips over into place and knocks the stack three frames before the first rock
    tp = intro_keys(room, f"{room} Top Piece")
    HIT = T0 - 3
    TIP0 = HIT - 11
    assert TIP0 >= 93, TIP0

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
    # the knock: the purple bar and the domino shiver as the pencil lands (cycle frames -3 to the first rock)
    pieces = [(piv["pencil"], "rotation", pencil, 0.0, p_intro),
              (piv["bar"], "rotation", bar, 0.0, lambda f: -0.02 * math.exp(-(f - HIT) / 6.0) * math.sin(2 * math.pi * (f - HIT) / 14.0) if f >= HIT else 0.0),
              (piv["domino"], "rotation", domino, 0.0, None),
              (piv["stick"], "rotation", stick, 0.0, None),
              (ids["jlow"], "scaleY", lambda t: 1 - low_p(t), 1.0, None), (ids["jlow"], "scaleX", lambda t: 1 + 0.7 * low_p(t), 1.0, None),
              (ids["jmid"], "scaleY", lambda t: 1 - joint_p(t), 1.0, None), (ids["jmid"], "scaleX", lambda t: 1 + joint_p(t), 1.0, None),
              (piv["cblock"], "rotation", c_nudge, 0.0, None), (piv["cblock"], "scaleY", lambda t: 1 - c_dip(t), 1.0, None),
              (ids["slab"], "y", lambda t: 8.3395 + slab_dip(t), 8.3395, None),
              (piv["block"], "rotation", block_th, 0.0, None),
              (hole_id, "x", hole_x, 1500.0, None)]
    emit_room(doc, room, b, theta, T0, ids, pre, pieces)


def unit_(a):
    n = math.hypot(a[0], a[1])
    return (a[0] / n, a[1] / n)


def num_(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def polydist_min(pts, poly):
    return min(polydist(p, poly) for p in pts)



def card3(doc, write):
    """The #1 mug circuit on the physics (finesse round 5): mug -> band (a spring) -> books (ricochet) -> FIRST card (ricochet) -> the
    white knob -> down the blue stick -> back into the mug. The path after the band is simulated (ball_physics.py): one gravity, every
    contact keeps 70 to 90 percent of its speed, the roll down the stick speeds up by G times the slope."""
    from ball_physics import Circ, Seg, build_path, flight, norm, piece_at, simulate
    global BALL_CENTER
    room = "Chapter 1 Card 3"
    BALL_CENTER = 16.78
    Rb = 17.1
    # ---- the art (world coordinates; the shelf, stick, card and mug groups are scaled 0.85 in the file, these are after the scale) ----
    mug_hide = (718.0, 724.0)                       # hidden inside the mug; its front rim is at y 698, so a centre below 715 is out of sight
    posts = [(792.0, 486.0), (862.1, 486.0)]        # radius 14.9
    band_rest_top = 485.7 - 6.4 + 0.4               # the band is straight at rest: its ends are at y 485.7, 12.75 thick
    y_band = band_rest_top - Rb                     # the ball's centre on the band
    card_edge = [(830.2, 538.6), (820.1, 544.4), (761.6, 644.0), (767.9, 654.9)]     # FIRST card's top and left edge
    tip, low = (594.5, 591.0), (671.0, 676.0)        # the blue stick's two white ends (radius 14.9)
    st_len = math.dist(tip, low)
    st_d = ((low[0] - tip[0]) / st_len, (low[1] - tip[1]) / st_len)
    st_n = (st_d[1], -st_d[0])
    ST_UP = 22.6
    stick_pivot, card_pivot, books_pivot, mug_pivot = low, (795.0, 654.9), (650.0, 508.0), (737.0, 745.0)
    # surfaces for the simulation, each with how much of the ball's speed it gives back (e) and a little roll-off friction in the tangent
    s_books = Seg((654.6, 473.9), (665.0, 506.2), "books", e=0.85, n=(32.3 / 33.9, -10.4 / 33.9))
    s_card = Seg((830.2, 538.6), (761.6, 644.0), "FIRST", e=0.85, n=(-0.8624, -0.5065))
    s_stick = Seg((tip[0] + (ST_UP - Rb) * st_n[0], tip[1] + (ST_UP - Rb) * st_n[1]), (low[0] + (ST_UP - Rb) * st_n[0], low[1] + (ST_UP - Rb) * st_n[1]), "stick", e=0.3, n=st_n)
    s_knob = Circ(tip, 14.9, "knob", e=0.7)
    s_posts = [Circ(p, 14.9, "post", e=0.5) for p in posts]

    # ---- the hop out of the mug, up to the band (a plain parabola at the project's gravity) ---------------------------------------------------
    F_POP, N1 = 10, 59
    F_BAND = F_POP + N1
    x_land = 815.0                                  # where it lands on the band, left of the middle so the band's left half tilts it left
    p_land = (x_land, y_band)
    v1 = ((x_land - mug_hide[0]) / N1, ((y_band - mug_hide[1]) - 0.5 * GP * N1 * N1) / N1)
    v_in = (v1[0], v1[1] + GP * N1)
    # ---- the band (a spring) throws it left, nearly at the speed it arrived with --------------------------------------------------------------
    RIDE = 6
    F_UP = F_BAND + RIDE
    x_rel, sp_out, ang = 798.0, 7.4, 20.0
    v_out = (-sp_out * math.cos(math.radians(ang)), -sp_out * math.sin(math.radians(ang)))

    def hermite(u, y0, y1, d0, d1):
        h00, h10, h01, h11 = 2 * u ** 3 - 3 * u ** 2 + 1, u ** 3 - 2 * u ** 2 + u, -2 * u ** 3 + 3 * u ** 2, u ** 3 - u ** 2
        return h00 * y0 + h10 * RIDE * d0 + h01 * y1 + h11 * RIDE * d1

    def ride(k):
        u = k / RIDE
        return (hermite(u, x_land, x_rel, v_in[0], v_out[0]), y_band + hermite(u, 0.0, 0.0, v_in[1], v_out[1]))
    band_dip = lambda t: 2.6 * (ride(t - F_BAND)[1] - y_band) if 0 <= t - F_BAND <= RIDE else 0.0
    # ---- the rest of the circuit, simulated ---------------------------------------------------------------------------------------------------
    events = simulate((x_rel, y_band), v_out, 0.0, [s_books, s_card, s_stick, s_knob] + s_posts, max_events=9)
    hits = [e for e in events if e[0] == "hit"]
    assert [h[2].name for h in hits][:3] == ["books", "FIRST", "knob"], [h[2].name for h in hits]
    pieces = build_path(events, (x_rel, y_band), v_out, 0.0)
    # off the stick's low end the stick's spring-back gives the ball lift: it keeps about 70 percent of the speed it arrived with, leaves
    # almost straight up (the angle is found so that it comes down inside the mug's mouth), clears the mug's left rim, and drops in
    assert events[-1][0] == "leave", events[-1]
    t_l, p_l, v_arr = events[-1][1], events[-1][2], events[-1][3]
    sp_launch = 0.72 * norm(v_arr)
    X_MOUTH, Y_RIM = 733.0, 689.0

    def mouth_x(ang):
        vx, vy = sp_launch * math.cos(ang), -sp_launch * math.sin(ang)
        tau = (-vy + math.sqrt(vy * vy + 2 * GP * (Y_RIM - p_l[1]))) / GP
        return p_l[0] + vx * tau
    lo_a, hi_a = math.radians(55.0), math.radians(89.0)
    for _ in range(40):
        mid_a = (lo_a + hi_a) / 2
        if mouth_x(mid_a) > X_MOUTH:
            lo_a = mid_a
        else:
            hi_a = mid_a
    ang_launch = (lo_a + hi_a) / 2
    v_launch = (sp_launch * math.cos(ang_launch), -sp_launch * math.sin(ang_launch))
    pieces[-1] = (t_l, t_l + 400.0, flight(p_l, v_launch, t_l)[0], "air")
    # when the flight off the stick's low end drops below the mug's front rim and out of sight
    t_rim = next(t / 16.0 for t in range(16 * 300) if piece_at(pieces, t / 16.0)[0][1] >= 698.0 and piece_at(pieces, t / 16.0)[1] == "air" and piece_at(pieces, t / 16.0)[0][0] > 680)
    t_hid = next(t / 16.0 for t in range(int(16 * t_rim), 16 * 300) if piece_at(pieces, t / 16.0)[0][1] >= mug_hide[1])
    F_RIM = F_UP + math.ceil(t_rim)
    F_LEAVE = F_UP + round(t_l)
    F_IN = F_UP + math.ceil(t_hid)
    WAIT = 30
    L = F_IN + WAIT
    hit_f = {h[2].name + str(i): F_UP + h[1] for i, h in enumerate(hits)}
    F_BOOK, F_CARD, F_KNOB = (round(F_UP + hits[i][1]) for i in range(3))
    F_STK = round(F_UP + next(h[1] for h in hits if h[2].name == "stick"))
    T0 = INTRO - 1 - F_BOOK
    assert T0 >= 80, T0

    # ---- reactions -------------------------------------------------------------------------------------------------------------------------------
    books = lambda t: spring(t - F_BOOK, -0.11, down=4, tau=12.0, period=18.0)
    card = lambda t: spring(t - F_CARD, 0.04, down=2, tau=9.0, period=20.0)
    stick = lambda t: spring(t - F_STK, -0.08, down=3, tau=9.0, period=18.0) + spring(t - F_KNOB, -0.02, down=3, tau=9.0, period=18.0)
    mug_th = lambda t: spring(t - 2, 0.05, down=3, tau=10.0, period=20.0) + spring(t - F_RIM, -0.045, down=4, tau=7.0, period=20.0)

    # ---- the ball -------------------------------------------------------------------------------------------------------------------------------------
    b = Ball(L)
    for t in range(0, F_POP + 1):
        b.put(t, mug_hide)
    fl1 = flight(mug_hide, v1, F_POP)[0]
    b.seg(F_POP, F_BAND, [fl1(t) for t in range(F_POP, F_BAND + 1)])
    for t in range(F_BAND, F_UP + 1):
        b.put(t, ride(t - F_BAND), "air")
    for t in range(F_UP + 1, F_IN + 1):
        p, m = piece_at(pieces, t - F_UP)
        if m == "roll":                                  # rolling on the stick: it rides the stick as it bends
            p = rot(p, stick_pivot, stick(t))
        b.put(t, p, m)
    last = b.c[F_IN]
    for t in range(F_IN + 1, L):
        u = smooth((t - F_IN) / 5.0)
        b.put(t, (last[0] + (mug_hide[0] - last[0]) * u, last[1] + (mug_hide[1] - last[1]) * u), "rest")
    b.put(L, b.c[0])
    b.mode[L] = b.mode[0]
    b.kick = {F_BOOK: 0.5 * 3.4 / 16.9, F_CARD: -0.5 * 4.5 / 16.9, F_KNOB: 0.3 * 3.0 / 16.9}
    for fr, a in ((F_BAND, 0.10), (F_BOOK, 0.08), (F_CARD, 0.08), (F_KNOB, 0.06), (F_STK, 0.08), (F_LEAVE, 0.08)):
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
             ("ricochets off the books", F_BOOK), ("ricochets off the FIRST card", F_CARD), ("hits the white knob", F_KNOB),
             ("lands on the blue stick", F_STK), ("leaves the stick's low end, lifted", F_LEAVE), ("drops into the mug (rim)", F_RIM), ("out of sight in the mug", F_IN)]
    print(f"{room}: cycle {L} frames ({L / 60:.2f} s), loop {L + 1} frames, journey starts at intro frame {T0} ({T0 / 60:.2f} s); the loop starts at cycle frame {INTRO - 1 - T0}")
    for name, t in names:
        print(f"  cycle {t:3d}  timecode {tc(t):5.2f} s  {name}")
    print(f"  stick end: arrives at {norm(v_arr):.1f}, leaves at {sp_launch:.1f} at {math.degrees(ang_launch):.0f} degrees above horizontal ({v_launch[0]:.1f}, {v_launch[1]:.1f}); comes down at x {mouth_x(ang_launch):.0f} through the rim line")
    print(f"  highest point of the ball: y {top:.1f} ({phone_y(top):.0f} px on the phone frame); copy ends at {COPY_BOTTOM:.0f}: clearance {phone_y(top) - COPY_BOTTOM:.0f} px")
    print(f"  x range {min(c[0] for c in b.c.values()) - 17.6:.0f} to {max(c[0] for c in b.c.values()) + 17.6:.0f}")
    edge_d = lambda pts: min(min(segdist(p, card_edge[i], card_edge[i + 1]) for i in range(3)) for p in pts)
    pd_ = lambda pts: min(math.dist(p, q) for p in pts for q in posts)
    print(f"  hop out: in speed at the band {math.hypot(*v_in):.2f}, out {math.hypot(*v_out):.2f}; closest to FIRST card's edge {edge_d([b.c[t] for t in range(F_POP, F_BAND + 1)]):.1f}, to a post {pd_([b.c[t] for t in range(F_POP, F_UP + 4)]):.1f} (needs 32; the band's left end is under the ball for a moment)")
    print(f"  band sag: ball {max(ride(k)[1] - y_band for k in range(RIDE + 1)):.1f} px, band's middle {max(band_dip(t) for t in range(F_BAND, F_UP + 1)):.1f} px, over {RIDE} frames; spin: {theta[L] / (2 * math.pi):.2f} turns over the cycle (leftover {resid:+.2f} rad hidden in the mug)")
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


def card3_round4(doc, write):
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


def sim_fall(p, v, g, segs, rad, stop_y=None, max_n=90):
    """A ball let go at p with velocity v, falling under gravity g until its centre comes within `rad` of one of the segments
    (list of (a, b)), or reaches stop_y. Returns the positions on each frame (the last is snapped onto the contact) and the segment hit."""
    pts, (x, y), (vx, vy) = [p], p, v
    for _ in range(max_n):
        nx, ny = x + vx, y + vy
        hit = None
        for k in range(1, 9):
            qx, qy = x + (nx - x) * k / 8, y + (ny - y) * k / 8
            for i, (a, b) in enumerate(segs):
                if segdist((qx, qy), a, b) <= rad:
                    hit = (i, (qx, qy))
                    break
            if hit:
                break
            if stop_y is not None and qy >= stop_y:
                hit = (None, (qx, stop_y))
                break
        if hit:
            pts.append(hit[1])
            return pts, hit[0]
        x, y, vy = nx, ny, vy + g
        vx_ = vx
        pts.append((x, y))
    return pts, None


def card4(doc, write):
    """A longer, more varied loop (finesse round 4): balance on the crossword head, a streak of hops, balance, down to the pot through
    the blue leaf, around the rim, and back up the flowers."""
    global BALL_CENTER
    room = "Chapter 1 Card 4"
    BALL_CENTER = 16.78
    Rb = 17.1
    # ---- the art (world coordinates; this room is unscaled) ------------------------------------------------------------------------------
    H = (720.9, 530.4)                      # the crossword head (a checker 38 x 38): flat top at y 511.2
    head_top, head_hw = 511.2, 19.2
    S_top = (786.0, 532.2 - Rb)              # the yellow hexagon's flat top (x 769.1 to 803.1)
    P_top = (681.0, 548.2 - Rb)              # the purple leaf's top edge (x 673.4 to 692.7)
    hex_edge = ((769.1, 532.2), (744.3, 566.1))      # the hexagon's upper-left slope: top end, lower end
    hex_dir = (-0.5890, 0.8081)
    hex_n = (-0.8081, -0.5890)
    leaf_edge = ((745.1, 581.3), (727.0, 607.9))     # the blue leaf's upper-left edge
    leaf_dir = (-0.5620, 0.8271)
    leaf_n = (-0.8271, -0.5620)
    rim_c = 634.2 - Rb                       # the pot's rim
    B1, B2, B3, BL = (720.9, 634.2), (765.5, 634.2), (714.5, 633.0), (729.6, 634.2)      # where the stems meet the pot: crossword, hexagon, purple leaf, blue leaf
    ws = lambda w: (w[0] - 669.0, w[1] - 489.0)       # the flowers sit inside a node at (669, 489)

    # ---- pieces' motion --------------------------------------------------------------------------------------------------------------------
    # event frames (cycle)
    N_H = 34
    STAY = 5
    # balance A: rolls on the head's flat top, with pauses (Wordle's rhythm)
    balA = [(0, 0.0), (8, 0.0), (26, 8.0), (34, 8.0), (58, -8.0), (68, -8.0), (84, 3.0), (98, 3.0)]
    F_H1 = 100                         # the streak: crossword -> hexagon -> purple leaf -> crossword
    leave = [F_H1, F_H1 + N_H + STAY, F_H1 + 2 * (N_H + STAY)]
    land = [l + N_H for l in leave]
    F_C = land[2]                      # back on the crossword head
    balB = [(F_C, 3.0), (F_C + 8, 3.0), (F_C + 22, -6.0), (F_C + 30, -6.0), (F_C + 46, 5.0), (F_C + 54, 5.0), (F_C + 64, 0.0), (F_C + 70, 0.0)]
    F_EDGE0 = F_C + 70                  # starts to roll toward the head's right edge

    def smooth_path(pts, t):
        """Piecewise smooth value through (frame, value) control points (flat between pairs that share a value)."""
        if t <= pts[0][0]:
            return pts[0][1]
        for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
            if t <= t1:
                return v0 + (v1 - v0) * smooth((t - t0) / (t1 - t0))
        return pts[-1][1]

    def u_head(t):
        if t < balA[-1][0] + 1:
            return smooth_path(balA, t)
        if F_C <= t <= balB[-1][0]:
            return smooth_path(balB, t)
        return None

    TILT = 0.06 / 8.0

    # roll off the head's right edge: the head tips like a scale and the ball goes
    F_ROLL = F_EDGE0
    N_ROLL = 22
    u_edge = head_hw
    def u_roll(t):
        return u_edge * ((t - F_ROLL) / N_ROLL) ** 2
    F_OFF = F_ROLL + N_ROLL
    th_roll = lambda t: 0.12 * smooth((t - F_ROLL) / N_ROLL)
    v_off = 2 * u_edge / N_ROLL

    def head_pos(u, th):
        return rot((H[0] + u, head_top - Rb), H, th)

    # the ball leaves the head; falls onto the hexagon's slope; slides down it; falls onto the blue leaf; slides down; falls to the rim
    p_edge = head_pos(u_edge, 0.12)
    pts1, hit1 = sim_fall(p_edge, (v_off * 0.8, 0.15), G, [hex_edge], Rb)
    assert hit1 == 0, "the ball misses the hexagon's slope"
    F_HEX = F_OFF + len(pts1) - 1
    contact1 = pts1[-1]
    # slide: along the slope toward its lower end
    s_from = ((contact1[0] - hex_n[0] * Rb) - hex_edge[0][0]) * hex_dir[0] + ((contact1[1] - hex_n[1] * Rb) - hex_edge[0][1]) * hex_dir[1]
    s_len = math.dist(*hex_edge)
    a_sl = 0.06
    v_in = 1.0
    sl1, s = [], s_from
    v_s = v_in
    while s < s_len:
        P = (hex_edge[0][0] + s * hex_dir[0], hex_edge[0][1] + s * hex_dir[1])
        sl1.append((P[0] + Rb * hex_n[0], P[1] + Rb * hex_n[1]))
        v_s = min(v_s + a_sl, 1.9)
        s += v_s
    F_HEX_END = F_HEX + len(sl1)
    pts2, hit2 = sim_fall(sl1[-1], (hex_dir[0] * v_s, hex_dir[1] * v_s), G, [leaf_edge], Rb)
    assert hit2 == 0, "the ball misses the blue leaf"
    F_LEAF = F_HEX_END + len(pts2) - 1
    contact2 = pts2[-1]
    s_from2 = ((contact2[0] - leaf_n[0] * Rb) - leaf_edge[0][0]) * leaf_dir[0] + ((contact2[1] - leaf_n[1] * Rb) - leaf_edge[0][1]) * leaf_dir[1]
    s_len2 = math.dist(*leaf_edge)
    # the landing hands its speed along the leaf (3 px a frame at most) and the slide eases from it to its old pace, with no stall
    v_arr2 = (pts2[-2][0] - pts2[-3][0]) * leaf_dir[0] + (pts2[-2][1] - pts2[-3][1]) * leaf_dir[1]
    sl2, s, v_s2 = [], s_from2, min(0.9 * v_arr2, 3.6)
    while s < s_len2:
        s += v_s2                                     # the first slide frame already moves (no repeated frame at the landing)
        P = (leaf_edge[0][0] + s * leaf_dir[0], leaf_edge[0][1] + s * leaf_dir[1])
        sl2.append((P[0] + Rb * leaf_n[0], P[1] + Rb * leaf_n[1]))
        v_s2 = 1.5 + (v_s2 - 1.5) * 0.8 if v_s2 > 1.5 else min(v_s2 + 0.08, 1.9)
    F_LEAF_END = F_LEAF + 1 + len(sl2)
    pts3, hit3 = sim_fall(sl2[-1], (leaf_dir[0] * v_s2 * 0.8, leaf_dir[1] * v_s2 * 0.8), G, [], Rb, stop_y=rim_c)
    F_RIM = F_LEAF_END + len(pts3) - 2           # the fall starts on the slide's last frame (no repeated frame)
    rim_x0 = pts3[-1][0]
    # the rim: Wordle-style rolls and pauses
    rim_ctrl = [(0, 0.0), (5, 0.0), (22, 30.0), (30, 30.0), (46, 8.0), (54, 8.0), (68, 28.0), (76, 28.0), (90, 2.0), (92, 2.0)]
    F_RIM_END = F_RIM + rim_ctrl[-1][0]
    # the climb back: rim -> blue leaf (touch) -> hexagon -> crossword head
    leaf_touch = (729.8, 573.5)
    CL = [(24, 22), (30, 34), (30, 22)]
    F_CL0 = max(F_RIM_END + 6, 477)            # the climb starts where it always did
    cl_leave, cl_land = [], []
    f = F_CL0
    for n, h in CL:
        cl_leave.append(f)
        cl_land.append(f + n)
        f += n + STAY
    F_TOPL = cl_land[2]
    L = F_TOPL + 40
    T0 = INTRO - 1 - (balA[-1][0] - 3)       # the loop starts inside balance A's last pause

    # ---- reactions -------------------------------------------------------------------------------------------------------------------------------
    dip = lambda t, evs, depth: sum(spring(t - fl, depth, down=3, tau=10.0, period=18.0) for fl in evs)
    cross_ev = [F_C, F_TOPL]
    hex_ev = [land[0], cl_land[1], F_HEX]
    leaf_ev = [land[1]]
    sy_c = lambda t: 1 - dip(t, [F_C], 0.06) - smooth_dip(t, F_TOPL, 0.06, 28)
    ph_c = lambda t: dip(t, [F_C], 0.03) + smooth_dip(t, F_TOPL, 0.03, 28)
    sy_h = lambda t: 1 - dip(t, hex_ev[:2], 0.06)
    ph_h = lambda t: dip(t, hex_ev[:2], -0.03) + spring(t - F_HEX, 0.05, down=3, tau=9.0, period=18.0)
    sy_l = lambda t: 1 - dip(t, leaf_ev, 0.06)
    ph_l = lambda t: dip(t, leaf_ev, 0.03)
    bleaf = lambda t: spring_fade(t - F_LEAF, -0.14, down=4, tau=10.0, period=20.0) + spring_fade(t - cl_land[0], -0.10, down=3, tau=8.0, period=18.0)

    def th_head(t):
        if t <= F_H1 - 0:
            return TILT * smooth_path(balA, t)
        if t < F_C:
            return release(t - F_H1, TILT * smooth_path(balA, F_H1), tau=7.0, period=18.0)
        if t < F_ROLL:
            return TILT * smooth_path(balB, t) + spring(t - F_C, 0.03, down=3, tau=9.0, period=18.0)
        if t < F_OFF:
            return th_roll(t) + spring(t - F_C, 0.03, down=3, tau=9.0, period=18.0) * (1 - smooth((t - F_ROLL) / N_ROLL))
        if t < F_TOPL:
            return release(t - F_OFF, 0.12, tau=7.0, period=20.0)
        return smooth_dip(t, F_TOPL, 0.03, 28)

    def flower(t, p, base, sy, ph):
        x, y = p[0], base[1] + (p[1] - base[1]) * sy(t)
        return rot((x, y), base, ph(t))

    def head_world(t, u):
        return flower(t, rot((H[0] + u, head_top - Rb), H, th_head(t)), B1, sy_c, ph_c)

    # ---- the ball ------------------------------------------------------------------------------------------------------------------------------------
    b = Ball(L)
    for t in range(0, balA[-1][0] + 1):
        b.put(t, head_world(t, u_head(t)), "roll")
    for t in range(balA[-1][0], F_H1 + 1):
        b.put(t, head_world(t, u_head(balA[-1][0])), "rest")
    hexpos = lambda t: flower(t, S_top, B2, sy_h, ph_h)
    leafpos = lambda t: flower(t, P_top, B3, sy_l, ph_l)
    hops = [("cross", 38, 1.0), ("hexa", 62, 1.0), ("leaf", 24, 1.0)]
    cur = lambda t: None
    for i in range(3):
        a_, z_ = leave[i], land[i]
        start = b.c[a_]
        end = (hexpos(z_) if i == 0 else leafpos(z_) if i == 1 else head_world(z_, balB[0][1]))
        # fit the middle hop's height so the ball clears the crossword head
        h = hops[i][1]
        if i == 1:
            for hh in range(40, 90, 2):
                pts = arc(start, end, N_H, hh, 1.0)
                if min(polydist(p, [(701.8, 511.2), (740.0, 511.2), (740.0, 549.5), (701.8, 549.5)]) for p in pts) >= 17.5:
                    h = hh
                    break
        hops[i] = (hops[i][0], h, hops[i][2])
        b.seg(a_, z_, arc(start, end, N_H, h, 1.0))
        if i < 2:
            for t in range(z_, leave[i + 1] + 1):
                b.put(t, hexpos(t) if i == 0 else leafpos(t), "rest")
    for t in range(F_C, balB[-1][0] + 1):
        b.put(t, head_world(t, u_head(t)), "roll" if t > F_C + 4 else "rest")
    for t in range(balB[-1][0] + 1, F_ROLL):
        b.put(t, head_world(t, 0.0), "rest")
    for t in range(F_ROLL, F_OFF):
        b.put(t, head_world(t, u_roll(t)), "roll")
    for i, p in enumerate(pts1):
        b.put(F_OFF + i, p, "air")
    for i, p in enumerate(sl1):
        b.put(F_HEX + i, p, "roll")
    for i, p in enumerate(pts2):
        b.put(F_HEX_END + i, p, "air")
    for i, p in enumerate(sl2):
        b.put(F_LEAF + 1 + i, p, "roll")
    for i, p in enumerate(pts3):
        b.put(F_LEAF_END + i - 1, p, "air")
    for t in range(F_RIM, F_RIM_END + 1):
        b.put(t, (rim_x0 + smooth_path(rim_ctrl, t - F_RIM), rim_c), "roll")
    rim_end = b.c[F_RIM_END]
    for t in range(F_RIM_END, F_CL0 + 1):
        b.put(t, rim_end, "rest")
    ends = [leaf_touch, hexpos(cl_land[1]), head_world(cl_land[2], 0.0)]
    for i, (n, h) in enumerate(CL):
        a_, z_ = cl_leave[i], cl_land[i]
        start = b.c[a_]
        end = ends[i]
        if i == 1:      # clears the hexagon's top-left corner
            for hh in range(20, 70, 2):
                pts = arc(start, end, n, hh, 1.0)
                if min(math.dist(p, (769.1, 532.2)) for p in pts[:-4]) >= 17.5:
                    h = hh
                    break
        CL[i] = (n, h)
        b.seg(a_, z_, arc(start, end, n, h, 1.0))
        if i < 2:
            for t in range(z_, cl_leave[i + 1] + 1):
                b.put(t, ends[i] if i == 0 else hexpos(t), "rest")
    for t in range(F_TOPL, L):
        b.put(t, head_world(t, 0.0), "rest")
    b.put(L, b.c[0])
    b.mode[L] = b.mode[0]
    assert math.dist(b.c[L - 1], b.c[0]) < 0.1, (b.c[L - 1], b.c[0])
    for fl in [land[0], land[1], F_C, F_HEX, F_LEAF, F_RIM, cl_land[0], cl_land[1], F_TOPL]:
        b.squash(fl, 0.09)
    b.kick = {F_OFF: 0.5 * v_off / 16.9}
    theta = b.spin()
    resid = theta[L] - 2 * math.pi * round(theta[L] / (2 * math.pi))
    a_, z_ = cl_leave[2], cl_land[2]
    theta = [th - resid * (smooth((t - a_) / (z_ - a_)) if t <= z_ else 1.0) for t, th in enumerate(theta)]
    # ---- a lead-in for the first visit: the pot and flowers ride in with the pan, so the ball is already rocking on the crossword head as the
    # room slides into view (calm: 3 px each way, the head tilting like a scale); only the first visit plays it, the loop repeats the cycle above ----
    S = T0                                                       # the cycle above used to start at intro frame S; it still does, the lead-in fills frames 0 to S
    preA = [(0, 0.0), (6, 0.0), (30, 3.0), (40, 3.0), (64, -3.0), (74, -3.0), (S, 0.0)]
    u_pre = lambda t: smooth_path(preA, t)
    th_pre = lambda t: TILT * u_pre(t)
    L_old, L = L, L + S
    b2 = Ball(L)
    for t in range(S):
        b2.put(t, rot((H[0] + u_pre(t), head_top - Rb), H, th_pre(t)), "roll")
    for t in range(L_old):
        b2.c[t + S], b2.mode[t + S], b2.sx[t + S], b2.sy[t + S] = b.c[t], b.mode[t], b.sx[t], b.sy[t]
    b2.c[L], b2.mode[L] = b2.c[S], b2.mode[S]
    b2.kick = {f + S: w for f, w in b.kick.items()}
    b = b2
    theta = b.spin()
    resid = (theta[L] - theta[S]) - 2 * math.pi * round((theta[L] - theta[S]) / (2 * math.pi))
    a_, z_ = cl_leave[2] + S, cl_land[2] + S
    theta = [th - resid * (smooth((t - a_) / (z_ - a_)) if t <= z_ else 1.0) for t, th in enumerate(theta)]
    top = min(c[1] for c in b.c.values()) - 17.6
    T0 = 0

    # ---- numbers to check ---------------------------------------------------------------------------------------------------------------------------
    tc = lambda t: (t + S + T0) / 60.0
    names = [("balance on the crossword head starts", 0), ("hop off the crossword head", leave[0]), ("lands on the yellow S hexagon", land[0]),
             ("lands on the purple leaf", land[1]), ("lands back on the crossword head", land[2]), ("second balance ends, rolls to the edge", F_EDGE0),
             ("leaves the head's right edge", F_OFF), ("lands on the hexagon's slope", F_HEX), ("drops onto the blue leaf (it bends)", F_LEAF),
             ("drops onto the pot's rim", F_RIM), ("rim rolls end", F_RIM_END)]
    names += [("climb: touches the blue leaf", cl_land[0]), ("climb: lands on the hexagon", cl_land[1]), ("climb: lands on the crossword head", cl_land[2])]
    print(f"{room}: cycle {L} frames (lead-in {S} frames, then {L_old} frames that repeat: {L_old / 60:.2f} s), loop {L_old + 1} frames, journey starts at intro frame {T0}; the loop starts at cycle frame {INTRO - 1 - T0}")
    for name, t in sorted(names, key=lambda n: n[1]):
        print(f"  cycle {t:3d}  timecode {tc(t):5.2f} s  {name}")
    print(f"  highest point of the ball: y {top:.1f} ({phone_y(top):.0f} px on the phone frame); copy ends at {COPY_BOTTOM:.0f}: clearance {phone_y(top) - COPY_BOTTOM:.0f} px")
    print(f"  x range {min(c[0] for c in b.c.values()) - 17.6:.0f} to {max(c[0] for c in b.c.values()) + 17.6:.0f}, y to {max(c[1] for c in b.c.values()) + 17.6:.0f}")
    print(f"  lead-in: the ball rolls up to {max(abs(u_pre(t)) for t in range(S)):.1f} px each way on the head from frame 6; hops: {hops}; climb {CL}; spin {(theta[L] - theta[S]) / (2 * math.pi):.2f} turns (leftover {resid:+.2f} rad into the last hop)")
    if not write:
        return

    # ---- write -----------------------------------------------------------------------------------------------------------------------------------------
    ids = dict(ball="9:11187", scale="9:11189")
    loop, intro = f"{room} Loop", f"{room} Intro"
    piv = {}
    piv["head"], _ = doc.wrap("9:11139", f"{room} Crossword Head", H[0] - 720.9, H[1] - 583.5)       # inside the flower node at (720.9, 583.5)
    piv["cross"], _ = doc.wrap("9:11138", f"{room} Crossword Flower", *ws(B1))
    piv["hexa"], _ = doc.wrap("9:10996", f"{room} S Flower", *ws(B2))
    piv["leaf"], _ = doc.wrap("9:11075", f"{room} Purple Leaf", *ws(B3))
    piv["bleaf"], _ = doc.wrap("9:11052", f"{room} Blue Leaf", *ws(BL))
    round_ball(doc, intro, ("9:11190", "9:11198", "9:11199", "9:11201"))
    doc.drop_object(loop, "9:11138")
    ids["spin"], _ = doc.wrap_run("9:11190", "9:11196", f"{room} Ball Spin", 0.0, -17.572)
    pre = lambda fr: (b.c[0][0], b.c[0][1], 1.0, 1.0)
    W = lambda fn, lead: (lambda t: fn(t - S) if t >= S else lead(t))          # a piece's motion on the shifted cycle
    one, zero = (lambda t: 1.0), (lambda t: 0.0)
    pieces = [(piv["head"], "rotation", W(th_head, th_pre), 0.0, None),
              (piv["cross"], "scaleY", W(sy_c, one), 1.0, None), (piv["cross"], "rotation", W(ph_c, zero), 0.0, None),
              (piv["hexa"], "scaleY", W(sy_h, one), 1.0, None), (piv["hexa"], "rotation", W(ph_h, zero), 0.0, None),
              (piv["leaf"], "scaleY", W(sy_l, one), 1.0, None), (piv["leaf"], "rotation", W(ph_l, zero), 0.0, None),
              (piv["bleaf"], "rotation", W(bleaf, zero), 0.0, None)]
    emit_room(doc, room, b, theta, T0, ids, pre, pieces, Ps=S)


def main(argv):
    cards = [int(c) for c in argv[argv.index("--cards") + 1].split(",")] if "--cards" in argv else [2, 3, 4]
    doc = Doc(SCENE)
    if "--write" in argv:
        card1_spin(doc)
    for c in cards:
        {2: card2, 3: card3, 4: card4, 31: card3_round4}[c](doc, "--write" in argv)
    if "--write" in argv:
        doc.save()
        print("wrote", SCENE)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
