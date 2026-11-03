"""Strands: the ball comes out of the right sneaker and drops back into it.

The sneakers are drawn in two layers around the ball (their fronts in the Front Plane, above it; their insides and backs in the
Floor Plane, below it), so a ball low in the right shoe is hidden by the shoe's front and a ball coming out shows over the dark
opening: no clip is needed. The journey (one gravity, every contact keeps 85 to 92 percent of its speed): it pops out of the shoe
as soon as the room has panned in, lands on the bottom string (which sags and springs it on), hits the frame's upright bar and
comes back, bounces twice along the string, comes down on the string's left knob, which kicks it left, and drops into the shoe's
opening. Out of sight it settles in the shoe, waits, and pops out again. The room's own Floor Clip stays on the ball (it only cuts
below the floor line, where the ball is inside the shoe anyway).
"""
import math

from common import BallArt, Cycle, dip, emit, plane_x, prepare_ball, smooth
from sim import World

ROOM = "Strands"
T0 = 118                                   # 1.97 s: the yellow frame it bounces on lands at 1.65 s and its squash is over at 1.97 s
IN_SHOE = (689.5, 722.0)                   # the ball's centre low in the right shoe: wholly behind its front
POP = (3.2, -9.5)
CATCH = 6                                  # frames from the opening to rest inside the shoe (out of sight)
PAUSE = 28                                 # frames in the shoe before the next pop
KR = 17.85                                 # the white knobs' radius, stroke included
STRING_Y = 9.0                             # (local units) how far the string's middle point sags per unit of landing speed / 10


def surfaces(w):
    rod_a, rod_b = (604 + 7.5 * 0.751, 567 - 7.5 * 0.66), (665.6 + 7.5 * 0.751, 637.1 - 7.5 * 0.66)
    return [
        w.seg(rod_a, rod_b, name="rod", e=0.8, kt=0.95),
        w.circ((604, 567), KR, name="rod top knob", e=0.8),
        w.circ((665.6, 637.1), KR, name="rod low knob", e=0.8),
        w.seg((766, 666.2), (891.1, 666.2), name="bottom string", e=0.9, kt=0.97),       # the strings are 15-wide strokes
        w.circ((766, 673.7), KR, name="bottom left knob", e=0.8),
        w.circ((891.1, 673.7), KR, name="bottom right knob", e=0.8),
        w.seg((811.4, 559.2), (891.1, 559.2), name="top string", e=0.9, kt=0.97),
        w.circ((811.5, 567), KR, name="top left knob", e=0.8),
        w.circ((891.1, 567), KR, name="top right knob", e=0.8),
        w.seg((883.6, 567), (883.6, 673.7), name="bar", e=0.8, n=(-1, 0)),
        w.seg((740, 711.8), (935, 711.8), name="floor", e=0.75),                       # (none where the shoes stand)
    ]


def build(doc, scene, sheet):
    art = BallArt(scene, ROOM)
    spin = prepare_ball(doc, art)
    for oid in ("9:3332", "9:3291"):         # the old journey's top-string sag and blue-strand bend
        doc.drop_object(f"{ROOM} Loop", oid)
    w = World(art.Rc)
    ev, path = w.run(IN_SHOE, POP, surfaces(w), frames=220, max_events=9, t_max=600)
    s = w.s
    hits = [(e[1], e[2].name, (e[4][0] / s, e[4][1] / s), (e[5][0] / s, e[5][1] / s)) for e in ev if e[0] == "hit"]
    names = [h[1] for h in hits]
    assert "floor" not in names and names[-1] == "bottom left knob", names
    # the frame it is in the opening: the centre passes y 696 going down after the last contact
    f_in = next(f for f in range(int(hits[-1][0]) + 1, 220) if path[f][0][1] >= 696)
    assert abs(path[f_in][0][0] - IN_SHOE[0]) < 2.5, path[f_in]
    # it falls on until it is low in the shoe (centre y 716: the checker's out-of-sight line, a contact point below y 731), then the
    # shoe catches it out of sight
    f_last = next(f for f in range(f_in, 220) if path[f][0][1] >= 716)
    cyc_frames = {f: (path[f][0], "air" if f else "hidden") for f in range(f_last + 1)}
    p1 = path[f_last][0]
    for u in range(1, CATCH + 1):
        k = smooth(u / CATCH)
        cyc_frames[f_last + u] = ((p1[0] + (IN_SHOE[0] - p1[0]) * k, p1[1] + (IN_SHOE[1] - p1[1]) * k), "hidden")
    f_rest = f_last + CATCH
    L = f_rest + PAUSE
    cyc = Cycle(L)
    for g in range(L + 1):
        cyc.put(g, *cyc_frames.get(g, (IN_SHOE, "hidden")))
    cyc.put(L, IN_SHOE, "hidden")
    for t, name, vin, vout in hits:
        if name == "bar":
            continue                                                # a side hit: a vertical squash would read wrong
        cyc.squash(round(t), min(0.12, 0.016 * abs(vin[1]) + 0.01) if "string" in name else 0.04, T=12)
    # turn: in the air it keeps the turn it had when it left a surface (it grips at each contact); out of the shoe, a little
    r = art.R
    contact_w = {round(t): vout[0] / r for t, name, vin, vout in hits}
    th = [0.0]
    w_now = 0.0
    for g in range(L):
        dx = cyc.c[g + 1][0] - cyc.c[g][0]
        if g in contact_w:
            w_now = contact_w[g]
        elif g == 0:
            w_now = 0.25 * dx / r
        if cyc.mode[g] != "air" and g > f_last:
            w_now = 0.0
        th.append(th[-1] + w_now)
    total = th[-1]
    want = round(total / (2 * math.pi)) * 2 * math.pi
    for g in range(f_last + 1, L + 1):
        th[g] += (want - total) * smooth((g - f_last) / (f_rest - f_last))
    # the bottom string sags under each landing and springs back (one smooth dip); the upright bar gives a little when hit
    string_hits = [(t, abs(vin[1])) for t, name, vin, vout in hits if name == "bottom string"]
    # one clear sag on the first, hardest landing; the two after it only stir the string (three equal sags in a row read as a buzz)
    sags = [(t, STRING_Y * v / 10 if i == 0 else 1.4 * v / string_hits[1][1], 22 if i == 0 else 16) for i, (t, v) in enumerate(string_hits)]
    string_y = lambda g: 0.364 + sum(dip(g - t, d, T) for t, d, T in sags)
    t_bar = next(t for t, name, *_ in hits if name == "bar")
    bar_x = lambda g: 2.515 + dip(g - t_bar, 2.5, 12)
    px = plane_x(scene, sheet, ROOM, "Front")

    def pre(f):
        return (IN_SHOE[0] + px(f), IN_SHOE[1]), 1.0, 1.0
    pieces = [("9:3355", "y", string_y, None), ("9:3355", "x", lambda g: 2.515, None), ("9:3323", "x", bar_x, None)]
    emit(doc, art, spin, cyc, th, T0, pre, pieces)
    sec = lambda g: f"{(T0 + g) / 60:.2f} s"
    times = ", ".join(f"{name} {sec(t)}" for t, name, *_ in hits)
    return (f"{ROOM}: pops out of the right shoe at {sec(0)}; {times}; drops into the shoe at {sec(f_in)}; "
            f"out again {(L - f_in) / 60:.2f} s later; loop {L / 60:.2f} s")
