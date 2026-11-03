"""The Midi: the ball lives in the lower stair cube (the cube with the door) and climbs the stairs.

The cube's door (Boxes 1) and its sides (Boxes 2) are in the Front Plane, drawn above the ball, and its dark inside is in the Floor
Plane, below it: a ball inside the cube is hidden by the cube's own art, and shows in the doorway when the door is open. So no clip is
needed. The journey: once the boxes have landed (1.95 s) the door swings open and the ball hops out onto the base bar and rolls to a stop, hops up the
stairs (the lower cube's top, then the upper cube's top, the last step up, with the clear squash), comes back down them, hops back in
through the doorway and the door shuts. Each hop starts from rest by the ball's own effort, as in the other game rooms' climbs.
"""
import math
import xml.etree.ElementTree as ET

from common import INTRO, BallArt, Cycle, emit, intro_series, plane_x, prepare_ball, smooth

ROOM = "The Midi"
T0 = 117                                    # 1.95 s: Boxes 2 (the stair) lands at 1.63 s, its squash is over at 1.95 s
G = 0.40
HOME = (662.5, 638.0)                       # the ball's centre resting inside the lower cube, wholly behind its door
BASE_Y, LOW_Y, UP_Y = 684.0, 596.0, 544.0   # contact lines on the base bar's top, the lower cube's top, the upper cube's top
EDGE_X = 689.0                              # the doorway's right edge (the box floor ends there)
WALL_X = 645.0                              # inside the box, where it comes to rest: covered by the side face and the shut door
DOOR = ("9:6489", "9:6490")                 # the door's two moving corners (its hinge is the left edge)


class Track:
    """The ball's centre, mode and squash, appended segment by segment on whole frames."""

    def __init__(self, start):
        self.pts = [start]
        self.modes = []
        self.contacts = []                  # (frame, kind, v_out) for spin grip and notes
        self.squashes = []

    @property
    def f(self):
        return len(self.pts) - 1

    @property
    def p(self):
        return self.pts[-1]

    def rest(self, n, mode="rest"):
        for _ in range(n):
            self.pts.append(self.p)
            self.modes.append(mode)

    def roll(self, y, v0, x_stop=None, x_end=None, a=0.0):
        """Roll along a level line at centre height y from the current x at speed v0 (signed): to x_end at constant speed, or easing
        to a stop at x_stop (constant deceleration). Returns the speed at the end."""
        x0 = self.p[0]
        if x_stop is not None:
            d = x_stop - x0
            a = v0 * v0 / (2 * abs(d))
            t_stop = abs(v0) / a
            sgn = math.copysign(1, v0)
            n = math.ceil(t_stop)
            for k in range(1, n + 1):
                u = min(k, t_stop)
                self.pts.append((x0 + v0 * u - sgn * 0.5 * a * u * u, y))
                self.modes.append("roll")
            self.pts[-1] = (x_stop, y)
            return 0.0
        n = math.ceil(abs(x_end - x0) / abs(v0))
        for k in range(1, n + 1):
            self.pts.append((x0 + v0 * k, y))
            self.modes.append("roll")
        return v0

    def fly(self, v, y_land, kind):
        """A flight from the current centre with velocity v, until it comes down to centre height y_land (descending). The landing
        frame is the first whole frame at or past it; the position there is put on the line. Returns (frame, v_in)."""
        x0, y0 = self.p
        vx, vy = v
        disc = vy * vy + 2 * G * (y_land - y0)
        T = (-vy + math.sqrt(disc)) / G
        n = math.ceil(T - 1e-9)
        for k in range(1, n + 1):
            u = min(k, T)
            self.pts.append((x0 + vx * u, y0 + vy * u + 0.5 * G * u * u))
            self.modes.append("air")
        self.pts[-1] = (x0 + vx * T, y_land)
        v_in = (vx, vy + G * T)
        return self.f, v_in


def hop_to(p0, p1, vy0):
    """Velocity of an own-effort hop from p0 that rises with vy0 (negative = up) and comes down onto p1's height at p1's x."""
    dy = p1[1] - p0[1]
    T = (-vy0 + math.sqrt(vy0 * vy0 + 2 * G * dy)) / G
    return ((p1[0] - p0[0]) / T, vy0), T


def build(doc, scene, sheet):
    art = BallArt(scene, ROOM)
    spin = prepare_ball(doc, art)
    for oid in ("9:6786", "9:6518", "9:6499", "9:6500"):      # old journey: Ball_01's offset moves, the right cube's push, the base door
        doc.drop_object(f"{ROOM} Loop", oid)
    Rc = art.Rc
    base_c, low_c, up_c = BASE_Y - Rc, LOW_Y - Rc, UP_Y - Rc
    tr = Track(HOME)
    notes = []
    tr.rest(14, "hidden")                                    # the door opens (frames 0 to 12)
    # out through the doorway: rolls right along the box floor, off its edge, down onto the base bar, and rolls to a stop
    # (a low hop: it rises 5 px, so its top stays under the cube's front corner at y 607 until it is clear of the cube)
    v, T = hop_to(tr.p, (718.0, base_c), -2.0)
    tr.contacts.append((tr.f, "hop", v))
    f, vin = tr.fly(v, base_c, "base")
    tr.squashes.append((f, 0.04))
    tr.contacts.append((f, "base", (vin[0], 0.0)))
    notes.append(("lands on the base bar", f))
    tr.roll(base_c, vin[0] * 0.95, x_stop=745.0)
    tr.rest(INTRO - 1 - T0 - tr.f + 12)                      # still on the bar when the intro hands over to the loop (cycle frame 74),
    assert tr.f > INTRO - 1 - T0                              # so the loop's repeated seam frame falls on a rest, not mid-hop
    # up the stairs: onto the lower cube's top, then the upper cube's top (the last step up)
    for (x1, yc, vy0, sq, pause, label) in ((670.0, low_c, -8.86, 0.05, 12, "the lower step"),
                                            (600.0, up_c, -9.0, 0.14, 24, "the top step")):
        v, T = hop_to(tr.p, (x1, yc), vy0)
        tr.contacts.append((tr.f, "hop", v))
        f, vin = tr.fly(v, yc, label)
        tr.squashes.append((f, sq))
        tr.contacts.append((f, "land", (0.0, 0.0)))
        notes.append((f"lands on {label}", f))
        tr.rest(pause)
    # back down: to the lower cube's top, then the base bar
    for (x1, yc, vy0, sq, pause, label) in ((667.0, low_c, -6.0, 0.07, 10, "the lower step"),
                                            (739.0, base_c, -3.0, 0.07, 12, "the base bar")):
        v, T = hop_to(tr.p, (x1, yc), vy0)
        tr.contacts.append((tr.f, "hop", v))
        f, vin = tr.fly(v, yc, label)
        tr.squashes.append((f, sq))
        tr.contacts.append((f, "land", (0.0, 0.0)))
        notes.append((f"lands on {label} (down)", f))
        tr.rest(pause)
    f_open2 = tr.f - 12
    # back in through the doorway: a low hop that passes under the cube's front corner, then it rolls to the far wall, out of sight
    v, T = hop_to(tr.p, (HOME[0], HOME[1]), -5.15)
    tr.contacts.append((tr.f, "hop", v))
    f_in, vin = tr.fly(v, HOME[1], "box")
    tr.squashes.append((f_in, 0.03))
    tr.contacts.append((f_in, "box", (vin[0], 0.0)))
    notes.append(("hops back into the box", f_in))
    tr.roll(HOME[1], vin[0], x_stop=WALL_X)
    f_hidden = tr.f
    f_close2 = f_hidden + 2
    L = f_close2 + 14 + 10
    while tr.f < L:
        tr.pts.append(HOME)
        tr.modes.append("hidden")
    cyc = Cycle(L)
    for g in range(L + 1):
        cyc.put(g, tr.pts[g], tr.modes[g] if g < L else "hidden")
    for g in range(f_hidden + 1, L + 1):
        cyc.mode[g] = "hidden"
    for f, a in tr.squashes:
        cyc.squash(f, a, T=12)
    # turn: rolling turns with the distance; a hop from rest gets a little from the push and keeps it in the air; at rest still
    r = art.R
    hops = {f: v for f, kind, v in tr.contacts if kind in ("hop",)}
    th = [0.0]
    w = 0.0
    for g in range(L):
        m = cyc.mode[g]
        dx = cyc.c[g + 1][0] - cyc.c[g][0]
        if m == "roll":
            w = dx / r
        elif m == "air":
            if g in hops:
                w = 0.25 * hops[g][0] / r
            elif g > 0 and cyc.mode[g - 1] == "roll":
                pass                                          # leaves the box floor still turning
        else:
            w = 0.0
        th.append(th[-1] + w)
    total = th[-1]
    want = round(total / (2 * math.pi)) * 2 * math.pi
    for g in range(f_hidden + 1, L + 1):
        th[g] += (want - total) * smooth((g - f_hidden - 1) / max(1, L - f_hidden - 1))
    # the door: opens for the ball to come out, shuts after it has left; opens again as it comes back, shuts once it is inside
    base = ET.parse(str(scene.path)).getroot()
    byid = {e.get("id"): e for e in base.iter() if e.get("id")}
    closed = {oid: (float(byid[oid].get("x", 0)), float(byid[oid].get("y", 0))) for oid in DOOR}
    opened = {"9:6489": (19.25, 41.609501), "9:6490": (19.25, -10.890499)}
    f_shut1 = notes[0][1] + 8

    def door_amount(g):
        if g <= 12:
            return smooth(g / 12)
        if g < f_shut1:
            return 1.0
        if g < f_shut1 + 14:
            return 1 - smooth((g - f_shut1) / 14)
        if g < f_open2:
            return 0.0
        if g < f_open2 + 12:
            return smooth((g - f_open2) / 12)
        if g < f_close2:
            return 1.0
        if g < f_close2 + 14:
            return 1 - smooth((g - f_close2) / 14)
        return 0.0

    pieces = []
    for oid in DOOR:
        for k, prop in enumerate(("x", "y")):
            c0, c1 = closed[oid][k], opened[oid][k]
            pieces.append((oid, prop, (lambda g, c0=c0, c1=c1: c0 + (c1 - c0) * door_amount(g)), None))
    # before T0 the ball sits in the cube and rides in with the door (the pan, the drop and the landing squash)
    px = plane_x(scene, sheet, ROOM, "Front")
    by = intro_series(scene, sheet, ROOM, "9:6592", "y")
    bsx = intro_series(scene, sheet, ROOM, "9:6592", "scaleX")
    bsy = intro_series(scene, sheet, ROOM, "9:6592", "scaleY")
    piv = (723.008, 775.94)

    def pre(f):
        cx = piv[0] + bsx(f) * (HOME[0] - piv[0]) + px(f)
        cy = by(f) + bsy(f) * (HOME[1] - piv[1])
        return (cx, cy), 1.0, 1.0
    emit(doc, art, spin, cyc, th, T0, pre, pieces)
    s = lambda g: f"{(T0 + g) / 60:.2f} s"
    beats = "; ".join(f"{label} {s(f)}" for label, f in notes)
    return (f"{ROOM}: the door opens at {s(0)}, the ball hops out at {s(14)}; {beats}; out of sight {s(f_hidden)}; "
            f"loop {L / 60:.2f} s")
