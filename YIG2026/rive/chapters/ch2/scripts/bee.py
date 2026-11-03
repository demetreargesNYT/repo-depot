"""Spelling Bee: the ball comes out of the #1 mug and goes back behind it.

The mug is drawn in two halves around the ball (Mug 1, its front wall, above; Mug 2, its inside and back, below), so a ball sitting
low in it is hidden by the front wall and a ball rising out of it shows over the dark inside. The journey: it pops up out of the mug
(1.83 s, once the mug has landed and settled), hops left along the floor line, lands on the corner of the left brick step, which kicks
it back to the right, and it rolls right and comes to rest behind the mug, where a slot the shape of the mug's outline hides it (on
only from its first landing until it is back inside the mug). Out of sight it drops back into the mug, waits, and pops out again.
"""
import math

from common import INTRO, BallArt, Cycle, dip, emit, intro_series, plane_x, prepare_ball, add_hole
from sim import World
import ball_physics as bp

ROOM = "Spelling Bee"
T0 = 110                                   # 1.83 s: the mug landed at 1.50 s and its squash is over at 1.82 s
IN_MUG = (807.0, 710.0)                    # the ball's centre low in the mug: wholly behind its front wall
REST_X = 807.0                             # where it stops behind the mug
POP = (-1.6, -9.0)
ROOM_ID = "9:2399"
PAUSE = 20                                 # frames in the mug before the next pop (it has been out of sight behind the mug ~1 s already)


def build(doc, scene, sheet):
    art = BallArt(scene, ROOM)
    spin = prepare_ball(doc, art)
    for oid in ("9:506", "9:467"):        # the old loop's hex drifts (reactions to the old journey)
        doc.drop_object(f"{ROOM} Loop", oid)
    Rc = art.Rc
    w = World(Rc)
    floor = w.seg((623.1, 711.8), (960, 711.8), name="floor", e=0.75)
    step = w.seg((593.1, 694.2), (623.1, 694.2), name="step top")
    corner = w.circ((623.1, 694.2), 0.5, name="corner", e=0.85, kt=0.97)
    ev, path = w.run(IN_MUG, POP, [floor, step, corner], max_events=12, t_max=400)
    s = w.s
    hits = [(e[1], e[2].name, (e[3][0] / s, e[3][1] / s), (e[5][0] / s, e[5][1] / s), (e[4][0] / s, e[4][1] / s)) for e in ev if e[0] == "hit"]
    i_corner = next(i for i, h in enumerate(hits) if h[1] == "corner")
    t_back, _, p_back, v_back, _ = hits[i_corner + 1]           # the little hop after the corner lands: from here it rolls
    t_back_f = math.ceil(t_back)
    fy = 711.8 - Rc
    x0 = p_back[0] + v_back[0] * (t_back_f - t_back)
    v0 = v_back[0]
    a = v0 * v0 / (2 * (REST_X - x0))
    t_stop = v0 / a
    cyc_frames = {}
    for f in range(t_back_f):
        cyc_frames[f] = (path[f][0], "air" if f else "hidden")
    f = t_back_f
    while True:
        u = f - t_back_f
        if u >= t_stop:
            break
        cyc_frames[f] = ((x0 + v0 * u - 0.5 * a * u * u, fy), "roll")
        f += 1
    f_rest = f
    cyc_frames[f_rest] = ((REST_X, fy), "rest")
    f_in = f_rest + 1                                              # out of sight: down into the mug
    L = f_in + PAUSE
    cyc = Cycle(L)
    for g in range(L + 1):
        if g in cyc_frames:
            cyc.put(g, *cyc_frames[g])
        else:
            cyc.put(g, IN_MUG, "hidden")
    cyc.put(L, IN_MUG, "hidden")
    # squash on every landing, in proportion to the fall
    for t, name, p, vout, vin in hits[: i_corner + 2]:
        cyc.squash(round(t), min(0.14, 0.016 * abs(vin[1]) + 0.01), T=12)
    # turn: rolling turns with the distance, in the air it keeps the turn it had when it left a surface (grips at each contact)
    r = art.R
    contact_w = {round(t): vout[0] / r for t, name, p, vout, vin in hits}
    th = [0.0]
    w_now = 0.0
    for g in range(L):
        m = cyc.mode[g]
        dx = cyc.c[g + 1][0] - cyc.c[g][0]
        if g in contact_w:
            w_now = contact_w[g]
        if m == "roll":
            w_now = dx / r
        elif m == "air":
            if g == 0:
                w_now = 0.25 * dx / r
        else:
            w_now = 0.0
        th.append(th[-1] + w_now)
    total = th[-1]
    want = round(total / (2 * math.pi)) * 2 * math.pi
    for g in range(f_in, L + 1):
        th[g] += (want - total) * min(1.0, (g - f_in) / 20)
    # the slot: on from the first landing (well clear of the mug) until the ball is back inside, out of sight
    t_land1 = round(hits[0][0])
    hole = add_hole(doc, art, ROOM_ID, f"{ROOM} Mug Slot", poly=mug_outline(), x=1500)      # in the room, so it leaves with it
    hole_x = lambda g: 0.0 if t_land1 <= g < f_in + 1 else 1500.0
    # the left brick step gives a little where the ball hits it
    t_c = hits[i_corner][0]
    bricks_x = lambda g: 60.419998 + dip(g - t_c, -1.6, 16)
    # before T0 the ball sits low in the mug and rides it in (the pan, the drop and the landing squash)
    px = plane_x(scene, sheet, ROOM, "Front")
    my = intro_series(scene, sheet, ROOM, "9:463", "y")
    msx = intro_series(scene, sheet, ROOM, "9:463", "scaleX")
    msy = intro_series(scene, sheet, ROOM, "9:463", "scaleY")
    piv = (747.501, 575.111)

    def pre(f):
        dy = my(f) - piv[1]
        cx = piv[0] + msx(f) * (IN_MUG[0] - piv[0]) + px(f)
        cy = piv[1] + dy + msy(f) * (IN_MUG[1] - piv[1])
        return (cx, cy), 1.0, 1.0
    pieces = [(hole, "x", hole_x, None), ("9:556", "x", bricks_x, None)]
    emit(doc, art, spin, cyc, th, T0, pre, pieces)
    times = ", ".join(f"{name} {INTRO_S(t)}" for t, name, *_ in hits[: i_corner + 2])
    return (f"{ROOM}: pops out of the mug at {INTRO_S(0)}; {times}; rolls back and stops behind the mug at {INTRO_S(f_rest)}; "
            f"back in the mug (unseen) and out again {PAUSE / 60:.2f} s later; loop {L / 60:.2f} s")


def INTRO_S(g):
    return f"{(T0 + g) / 60:.2f} s"


def mug_outline():
    import geom
    return geom.sampled(geom.BYID["9:433"], 8)
