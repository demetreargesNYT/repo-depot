"""The Crossword: the ball rolls out of the floating bar and back behind the open crate.

The floating bar is a box drawn in two layers around the ball: its dark back (Floor Plane) below the ball and its white front panels
(Front Boxes 1, Doors) above it, so the ball inside is hidden. Its right-hand panel slides (9:8472 x: 6.92 closed, -15 open) to open
the bar's right end. The journey: once the front boxes have landed and settled (1.83 s), the panel slides open and the ball rolls out
of the open end, drops to the floor line, bounces into the middle stack's lower step, which turns it round, and hops and rolls back
left behind the open crate at bottom left, where a slot the shape of the crate's outline hides it (on only from just before it gets
there until it is back in the bar). Out of sight it goes back into the bar, the panel has shut, and it waits before the next roll.

The old journey's keys are dropped: Ball_01's moves (the ball is moved by its own node now), the stair cube's door (8434, 8435), the
copy of the middle cube used to cover the old return (Group 2's opacity) and the bar panel's old timing.
"""
import math
import re

from common import INTRO, BallArt, Cycle, emit, intro_series, plane_x, prepare_ball, add_hole, num
from sim import World

ROOM = "The Crossword"
ROOM_ID = "9:9626"
T0 = 116                                   # 1.93 s: the front boxes (the bar's panels) landed at 1.50 s, their squash is over at 1.82 s;
                                           # six frames on, so the intro-to-loop seam falls on a rising hop, not at its top
FLOOR = 711.9
BAR_FLOOR = 627.8                          # the bar's inside floor (the bottom of its panels)
BAR_END = 667.5                            # the bar's open right end
PANEL = "9:8472"
PANEL_SHUT, PANEL_OPEN = 6.92, -15.0
OPEN_T, SHUT_T = 10, 10                    # frames the panel takes to slide open and shut
ROLL_V = 2.1                               # the ball's speed as it leaves the bar
PAUSE = 30                                 # frames in the bar before the panel opens again
CRATE = [(570.2, 681.8), (659.2, 681.8), (675.0, 702.6), (675.0, 732.2), (586.0, 732.2), (570.2, 711.5)]


def ease(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def build(doc, scene, sheet):
    art = BallArt(scene, ROOM)
    spin = prepare_ball(doc, art)
    for a in ("Intro", "Loop", "Waiting", "Built"):
        doc.drop_object(f"{ROOM} {a}", art.b01)
    for oid in ("9:8513", "9:8434", "9:8435"):
        doc.drop_object(f"{ROOM} Loop", oid)
    doc.drop_object(f"{ROOM} Loop", PANEL)
    i = doc.idx(doc_anim_id(doc, f"{ROOM} Loop"))
    doc.lines[i] = re.sub(r' work(Start|End)="[^"]*"', "", doc.lines[i])

    Rc = art.Rc
    in_bar = (627.0, BAR_FLOOR - Rc)
    fy = FLOOR - Rc
    # 1. the panel opens; the ball starts rolling once the end is half open and reaches ROLL_V at the end of the bar
    f_go = 5
    d = BAR_END - in_bar[0]
    acc = ROLL_V * ROLL_V / (2 * d)
    n_roll = math.ceil(ROLL_V / acc)
    frames = {}
    for g in range(f_go + 1):
        frames[g] = (in_bar, "hidden" if g == 0 else "rest")
    for u in range(1, n_roll + 1):
        frames[f_go + u] = ((in_bar[0] + 0.5 * acc * u * u, in_bar[1]), "roll")
    f_edge = f_go + n_roll
    p_edge, v_edge = frames[f_edge][0], (acc * n_roll, 0.0)
    # 2. off the end, onto the floor line, into the step, back left behind the crate
    w = World(Rc)
    floor = w.seg((560.0, FLOOR), (722.5, FLOOR), name="floor", e=0.8)
    face = w.circ((722.5 + 2000.0, 697.0), 2000.0, name="step face", e=0.46, kt=0.97)       # the flat face as a huge circle (a contact on it never turns into a roll); a glancing knock
    top = w.seg((722.5, 682.3), (781.8, 682.3), name="step top")
    ev, path = w.run(p_edge, v_edge, [floor, face, top], max_events=14, t_max=300, frames=300, roll_below=1.8)
    s = w.s
    hits = [(e[1], e[2].name, (e[3][0] / s, e[3][1] / s), (e[5][0] / s, e[5][1] / s), (e[4][0] / s, e[4][1] / s)) for e in ev if e[0] == "hit"]
    rolls = [e for e in ev if e[0] == "roll"]
    assert rolls, "never settles into a roll"
    t_roll = rolls[0][1]
    t_roll_f = math.ceil(t_roll)
    for u in range(t_roll_f + 1):
        frames[f_edge + u] = (path[u][0], "air" if path[u][1] == "air" else "roll")
    # 3. the last roll, left along the floor line behind the crate, slows to a stop well inside the crate's outline
    x0 = path[t_roll_f][0][0]
    v0 = (path[t_roll_f][0][0] - path[t_roll_f - 1][0][0])
    x_rest = x0 - min(12.0, x0 - 590.0)                 # a short roll, ending well inside the crate's outline (centre 585 to 661)
    assert v0 < 0 and x0 > x_rest >= 590.0 and x0 < 661.0, (x0, v0)
    a = v0 * v0 / (2 * (x0 - x_rest))
    t_stop = abs(v0) / a
    g = f_edge + t_roll_f
    u = 0
    while u + 1 < t_stop:
        u += 1
        frames[g + u] = ((x0 + v0 * u + 0.5 * a * u * u, fy), "roll")
    f_rest = g + u + 1
    frames[f_rest] = ((x_rest, fy), "rest")
    f_in = f_rest + 1                                     # out of sight: back into the bar
    L = f_in + PAUSE
    cyc = Cycle(L)
    for k in range(L + 1):
        cyc.put(k, *(frames[k] if k in frames else (in_bar, "hidden")))
    cyc.put(L, in_bar, "hidden")
    # squash: one clear squash on the drop from the bar, lighter ones on the hops that follow; none on the step (a side knock)
    landings = [(t, vin) for t, name, p, vout, vin in hits if name == "floor"]
    for n, (t, vin) in enumerate(landings):
        amt = 0.13 if n == 0 else min(0.06, 0.012 * abs(vin[1]))
        if amt > 0.015:
            cyc.squash(f_edge + round(t), amt, T=12)
    # turn: grips at each contact, turns with the distance while rolling, keeps its turn in the air, still at rest
    r = art.R
    contact_w = {f_edge + round(t): vout[0] / r for t, name, p, vout, vin in hits}
    th = [0.0]
    w_now = 0.0
    for k in range(L):
        m = cyc.mode[k]
        dx = cyc.c[k + 1][0] - cyc.c[k][0]
        if k in contact_w:
            w_now = contact_w[k]
        if m == "roll":
            w_now = dx / r
        elif m != "air":
            w_now = 0.0
        th.append(th[-1] + w_now)
    total = th[-1]
    want = round(total / (2 * math.pi)) * 2 * math.pi
    for k in range(f_in, L + 1):
        th[k] += (want - total) * min(1.0, (k - f_in) / 20)
    # the panel: opens at the start of the cycle, shuts once the ball is out and has dropped clear of the bar
    f_shut = f_edge + 24
    panel = lambda k: (PANEL_SHUT + (PANEL_OPEN - PANEL_SHUT) * ease(k / OPEN_T) if k < f_shut
                       else PANEL_OPEN + (PANEL_SHUT - PANEL_OPEN) * ease((k - f_shut) / SHUT_T))
    # the slot: on from the first landing (the ball is clear of the crate) until it is back in the bar
    f_land1 = f_edge + round(landings[0][0])
    hole = add_hole(doc, art, ROOM_ID, f"{ROOM} Crate Slot", poly=CRATE, x=1500)
    hole_x = lambda k: 0.0 if f_land1 <= k < f_in + 1 else 1500.0
    # before T0 the ball sits in the bar and rides in with the front boxes (the pan, their drop and their landing squash)
    px = plane_x(scene, sheet, ROOM, "Front")
    by = intro_series(scene, sheet, ROOM, "9:8534", "y")
    bsx = intro_series(scene, sheet, ROOM, "9:8534", "scaleX")
    bsy = intro_series(scene, sheet, ROOM, "9:8534", "scaleY")
    piv = (760.094, 747.921)

    def pre(f):
        cx = piv[0] + bsx(f) * (in_bar[0] - piv[0]) + px(f)
        cy = by(f) + bsy(f) * (in_bar[1] - piv[1])
        return (cx, cy), 1.0, 1.0
    pieces = [(hole, "x", hole_x, None), (PANEL, "x", panel, None)]
    emit(doc, art, spin, cyc, th, T0, pre, pieces)
    S = lambda k: f"{(T0 + k) / 60:.2f} s"
    hit_txt = ", ".join(f"{name} {S(f_edge + round(t))}" for t, name, *_ in hits)
    return (f"{ROOM}: panel opens {S(0)}, ball rolls out of the bar {S(f_go)} to {S(f_edge)}; {hit_txt}; stops behind the crate "
            f"at x {x_rest:.0f} {S(f_rest)}; back in the bar unseen, panel shut, next roll {PAUSE / 60:.2f} s later; loop {L / 60:.2f} s")


def doc_anim_id(doc, name):
    i, _ = doc.anim(name)
    return re.search(r'\bid="([^"]+)"', doc.lines[i]).group(1)
