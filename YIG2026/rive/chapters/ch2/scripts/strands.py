"""Strands: the ball comes out of the right sneaker, plays on the yellow frame, and drops back into the shoe.

The sneakers are drawn in two layers around the ball (their fronts in the Front Plane, above it; their insides and backs in the
Floor Plane, below it). On top of that a slot clip, the shape of the right shoe, hides the ball wherever it overlaps the shoe except
inside the shoe's opening, which is open at the top (the back rim stays behind the ball) and stops 0.5 px short of the opening's
drawn sides and front edge, so the shoe's dark outline (about 2 px) stays drawn around the ball as it goes in and comes out: it reads
as going into the hole, not behind the shoe (Demetre's note 1, 2026-11-04). The clip sits in the Front Plane, so it slides in and out
with the shoe.

The journey (one gravity; the strings are springs): it pops out of the shoe as soon as the yellow frame has landed, lands on the
bottom string (which gives under it), hits the frame's upright bar and comes back, and the string catches that landing (it keeps 76
percent of the speed and most of the sideways part is taken). Then it bounces lightly along the string three times (about 20, 16 and
13 px high, each keeping 90 percent), and on the next landing the string loads and flings it up over the left knob and into the
shoe's opening (Demetre's note 2, 2026-11-04: the strings may add energy, "Strands strings fling by design"). Out of sight it
settles in the shoe, waits, and pops out again. The room's own Floor Clip stays on the ball. The string gives quickly and comes back
slowly on the first landing and on the fling; the light landings only stir it (three similar quick sags in a row read as a buzz).
"""
import math

import ball_physics as bp
from common import BallArt, Cycle, add_hole, dip, emit, plane_x, prepare_ball, smooth
import geom
from sim import World

ROOM = "Strands"
FRONT_PLANE = "9:4278"
T0 = 118                                   # 1.97 s: the yellow frame it bounces on lands at 1.65 s and its squash is over at 1.97 s
IN_SHOE = (689.5, 722.0)                   # the ball's centre low in the right shoe: wholly hidden
POP = (3.2, -9.5)
E_TOP, E_BOTTOM, E_KNOB = 0.9, 0.9, 0.8
CATCH = 6                                  # frames from the opening to rest inside the shoe (out of sight)
PAUSE = 28                                 # frames in the shoe before the next pop
KR = 17.85                                 # the white knobs' radius, stroke included
SAG = 0.9                                  # the strings' first sag, local units per unit of landing speed
CATCH_AT, CATCH_KEEP, CATCH_KT = 2, 0.76, 0.4   # the bottom string's 2nd contact (after the bar) catches: 76% of the speed kept,
                                                # the sideways part cut to 40%, so the light bounces stay on the string
FLICK_AT, FLICK_T = 5, 34                  # its 5th contact flings the ball into the shoe's opening, 34 frames later
SHOE_IN = (689.5, 696.0)                   # where the fling aims: the opening, the centre at the hidden line


class StringSeg(bp.Seg):
    """A string whose n-th contact has its own bounce (e, kt): `sched` maps the contact's number to it. ball_physics reads a surface's
    e once per contact, then its kt, so counting reads of e counts contacts."""

    def __init__(self, a, b, sched, **kw):
        self.sched, self.count = sched, 0
        super().__init__(a, b, **kw)

    @property
    def e(self):
        self.count += 1
        return self.sched.get(self.count, (self._e0, None))[0]

    @e.setter
    def e(self, v):
        self._e0 = v

    @property
    def kt(self):
        k = self.sched.get(self.count, (None, None))[1]
        return self._kt0 if k is None else k

    @kt.setter
    def kt(self, v):
        self._kt0 = v
SHOE_PATHS = ("9:3465", "9:3489", "9:3503", "9:3518", "9:3642", "9:3658", "9:3677", "9:3690", "9:3705",       # the right shoe
              "9:3382", "9:3406", "9:3420", "9:3435", "9:3549", "9:3565", "9:3584", "9:3597", "9:3612")       # the left one beside it
GREEN_TOP = "9:3489"                       # the right shoe's green upper: its top edge is the opening's front edge
OPENING = (671.7, 707.4)                   # the opening's dark sides, inside their outlines, less 0.25 px
GAP = (663.0, 698.0)                       # the thin gap between the shoes (x from, and the hidden part starts at this y)
EDGE = 1.25                                # the cut sits this far above the front edge's line (0.75 stroke + 0.5 dark)


def surfaces(w, sched=None):
    rod_a, rod_b = (604 + 7.5 * 0.751, 567 - 7.5 * 0.66), (665.6 + 7.5 * 0.751, 637.1 - 7.5 * 0.66)
    out = [
        w.seg(rod_a, rod_b, name="rod", e=0.8, kt=0.95),
        w.circ((604, 567), KR, name="rod top knob", e=0.8),
        w.circ((665.6, 637.1), KR, name="rod low knob", e=0.8),
        w.seg((766, 666.2), (891.1, 666.2), name="bottom string", e=E_BOTTOM, kt=0.97),       # the strings are 15-wide strokes
        w.circ((766, 673.7), KR, name="bottom left knob", e=E_KNOB),
        w.circ((891.1, 673.7), KR, name="bottom right knob", e=E_KNOB),
        w.seg((811.4, 559.2), (891.1, 559.2), name="top string", e=E_TOP, kt=0.97),
        w.circ((811.5, 567), KR, name="top left knob", e=E_KNOB),
        w.circ((891.1, 567), KR, name="top right knob", e=E_KNOB),
        w.seg((883.6, 567), (883.6, 673.7), name="bar", e=0.8, n=(-1, 0)),
        w.seg((740, 711.8), (935, 711.8), name="floor", e=0.75),                            # (none where the shoes stand)
    ]
    for i, srf in enumerate(out):
        if srf.name == "bottom string":
            out[i] = StringSeg(srf.a, srf.b, sched or {}, name=srf.name, e=srf.e, kt=srf.kt)
    return out


def shoe_slot():
    """The hidden part of the right shoe as one polygon (room space, the planes at rest): the shoe's silhouette (all its fills and
    their 1.5 outlines), below its own top edge, except over the opening, where it starts EDGE above the green upper's top edge."""
    from PIL import Image, ImageDraw
    Z, X0, Y0, W, H = 8, 620, 686, 130, 72

    def raster(ids, stroke):
        im = Image.new("L", (W * Z, H * Z), 0)
        d = ImageDraw.Draw(im)
        for i in ids:
            pts = [((x - X0) * Z, (y - Y0) * Z) for x, y in geom.sampled(geom.BYID[i], 16)]
            d.polygon(pts, fill=255)
            if stroke:
                d.line(pts + [pts[0]], fill=255, width=int(1.5 * Z))
        return im
    S, G = raster(SHOE_PATHS, True), raster([GREEN_TOP], False)

    def col(im, x):
        px = int(round((x - X0) * Z))
        ys = [y for y in range(H * Z) if im.getpixel((px, y))]
        return (Y0 + ys[0] / Z, Y0 + (ys[-1] + 1) / Z) if ys else None
    xs = [626.0 + 0.25 * i for i in range(int((733.0 - 626.0) / 0.25) + 1)]
    top, bottom = [], []
    for x in xs:
        c = col(S, x)
        if c is None:
            continue
        y_top = c[0]
        if GAP[0] <= x < OPENING[0]:
            y_top = min(y_top, GAP[1])            # the strip of background between the two shoes: the ball inside the shoe is behind it
        if OPENING[0] <= x <= OPENING[1]:
            g = col(G, x)
            y_top = max(y_top, g[0] - EDGE)
        top.append((x, y_top))
        bottom.append((x, c[1]))
    return top + bottom[::-1]


def run_with(w, sched, frames=900):
    """The simulated journey, sampled on as many frames as the path covers (ball_physics stops covering after a long run)."""
    while True:
        try:
            return w.run(IN_SHOE, POP, surfaces(w, sched), frames=frames, max_events=22, t_max=1200)
        except ValueError as e:
            frames = int(float(str(e))) - 1


def string_hits(w, ev):
    s = w.s
    return [((e[3][0] / s, e[3][1] / s), (e[4][0] / s, e[4][1] / s)) for e in ev if e[0] == "hit" and e[2].name == "bottom string"]


def run(w):
    """The journey with the bottom string's catch and fling. Each is worked out from where and how fast the ball meets the string
    (the earlier contacts don't depend on it): the catch keeps CATCH_KEEP of the landing's speed, and the fling sends the ball on the
    parabola that reaches SHOE_IN FLICK_T frames later. Returns (events, path, the fling's speed in and out)."""
    ev, _ = run_with(w, {})
    vin = string_hits(w, ev)[CATCH_AT - 1][1]
    e_c = math.sqrt((CATCH_KEEP * math.hypot(*vin)) ** 2 - (CATCH_KT * vin[0]) ** 2) / abs(vin[1])
    sched = {CATCH_AT: (e_c, CATCH_KT)}
    ev, _ = run_with(w, sched)
    (px, py), vin = string_hits(w, ev)[FLICK_AT - 1]
    T = FLICK_T
    vx, vy = (SHOE_IN[0] - px) / T, (SHOE_IN[1] - py - 0.5 * 0.40 * T * T) / T
    sched[FLICK_AT] = (-vy / vin[1], vx / vin[0])
    ev, path = run_with(w, sched)
    return ev, path, (math.hypot(*vin), math.hypot(vx, vy))


def build(doc, scene, sheet):
    art = BallArt(scene, ROOM)
    spin = prepare_ball(doc, art)
    for oid in ("9:3291",):                   # the old journey's blue-strand bend
        doc.drop_object(f"{ROOM} Loop", oid)
    w = World(art.Rc)
    ev, path, (fling_in, fling_out) = run(w)
    s = w.s
    hits = [(e[1], e[2].name, (e[4][0] / s, e[4][1] / s), (e[5][0] / s, e[5][1] / s)) for e in ev if e[0] == "hit"]
    bottom = [i for i, h in enumerate(hits) if h[1] == "bottom string"]
    hits = hits[:bottom[FLICK_AT - 1] + 1]                          # the fling is the last contact: then it is in the shoe
    names = [h[1] for h in hits]
    assert names == ["bottom string", "bar"] + ["bottom string"] * (FLICK_AT - 1), names
    assert not [e for e in ev if e[0] == "roll" and e[1] < hits[-1][0]], "a roll on the string"
    t_fling = hits[-1][0]
    # the frame it is in the opening: the centre passes y 696 going down after the last contact
    f_in = next(f for f in range(int(hits[-1][0]) + 1, max(path) + 1) if path[f][0][1] >= 696)
    assert abs(path[f_in][0][0] - IN_SHOE[0]) < 3, path[f_in]
    # it falls on until it is low in the shoe (centre y 716: the checker's out-of-sight line, a contact point below y 731), then the
    # shoe catches it out of sight
    f_last = next(f for f in range(f_in, max(path) + 1) if path[f][0][1] >= 716)
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
        a = min(0.12, 0.016 * abs(vin[1]) + 0.01) if "string" in name else 0.04
        if a >= 0.03:
            cyc.squash(round(t), a, T=12)
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
    # each string gives under a landing: the first landing on it sags it quickly and it comes back slowly (0.7 s), so the string
    # never swings back and forth; each landing after that adds a dip less than half the one before (three similar quick sags in a
    # row read as a buzz), and the slightest are left out
    def sags(name):
        out, last = [], None
        for t, n, vin, vout in hits:
            if n != name or t == t_fling:
                continue
            d = SAG * abs(vin[1])
            if last is not None:
                d = min(d, 0.45 * last, 1.4)
            if d < 0.5:
                break
            out.append((t, d))
            last = d
        return out

    def give(u, depth, down=6, back=42):
        if u <= 0 or u >= down + back:
            return 0.0
        if u < down:
            return depth * math.sin(0.5 * math.pi * u / down) ** 2
        return depth * (1 - smooth((u - down) / back))

    def string(sg):
        return lambda g: 0.364 + sum((give(g - t, d) if i == 0 else dip(g - t, d, 12)) for i, (t, d) in enumerate(sg))
    top_sags, bottom_sags = sags("top string"), sags("bottom string")
    # the fling: the string loads under the light landing as deep as it gave under the first one, and springs back slowly, the same
    # give as the first landing's
    fling_d = SAG * abs(hits[-1][3][1])
    top_y = string(top_sags)
    bottom_y = lambda g, _b=string(bottom_sags): _b(g) + give(g - t_fling, fling_d)
    bars = [t for t, name, *_ in hits if name == "bar"]
    bar_x = lambda g: 2.515 + sum(dip(g - t, 2.5, 12) for t in bars[:1])
    px = plane_x(scene, sheet, ROOM, "Front")

    def pre(f):
        return (IN_SHOE[0] + px(f), IN_SHOE[1]), 1.0, 1.0
    pieces = [("9:3355", "y", bottom_y, None), ("9:3355", "x", lambda g: 2.515, None),
              ("9:3332", "y", top_y, None), ("9:3332", "x", lambda g: 2.515, None), ("9:3323", "x", bar_x, None)]
    emit(doc, art, spin, cyc, th, T0, pre, pieces)
    add_hole(doc, art, FRONT_PLANE, f"{ROOM} Shoe Slot", poly=shoe_slot())
    sec = lambda g: f"{(T0 + g) / 60:.2f} s"
    times = ", ".join(f"{name} {sec(t)}" for t, name, *_ in hits)
    return (f"{ROOM}: pops out of the right shoe at {sec(0)}; {times}; drops into the shoe at {sec(f_in)}; "
            f"out again {(L - f_in) / 60:.2f} s later; loop {L / 60:.2f} s; top-string sags {[round(d, 1) for _, d in top_sags]}, "
            f"bottom {[round(d, 1) for _, d in bottom_sags]}, fling {round(fling_d, 1)} at {sec(t_fling)} "
            f"(speed {fling_in:.2f} in, {fling_out:.2f} out)")
