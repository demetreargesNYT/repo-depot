"""A small physics for the ball's journeys (finesse round 5): one gravity, flights as parabolas, bounces that keep most of their speed,
rolls that speed up downhill. Times are in frames and may be fractional; positions are sampled on whole frames afterwards.

The rules are the ones in CLAUDE.md ("The ball's physics"): G below is the project's one gravity; a contact changes direction and keeps
70 to 90 percent of the speed; only a surface turns the ball round; slopes add G times the sine of the slope.
"""
import math

G = 0.40            # artboard units per frame squared
RB = 17.1           # distance from the ball's centre to what it rests on


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def mul(a, k):
    return (a[0] * k, a[1] * k)


def norm(a):
    return math.hypot(a[0], a[1])


def unit(a):
    n = norm(a)
    return (a[0] / n, a[1] / n)


class Seg:
    """A straight surface from a to b. n is the unit normal on the ball's side (default: the one pointing up)."""

    def __init__(self, a, b, name="", e=0.8, kt=0.95, n=None):
        self.a, self.b, self.name, self.e, self.kt = a, b, name, e, kt
        self.len = norm(sub(b, a))
        self.d = unit(sub(b, a))
        self.n = n if n is not None else ((self.d[1], -self.d[0]) if -self.d[0] < 0 else (-self.d[1], self.d[0]))
        if n is None and self.n[1] > 0:
            self.n = (-self.n[0], -self.n[1])

    def touches(self, p, v, rad=RB):
        sd = dot(sub(p, self.a), self.n)
        s = dot(sub(p, self.a), self.d)
        return 0.0 <= s <= self.len and -rad * 0.4 <= sd <= rad and dot(v, self.n) < 0

    def normal_at(self, p):
        return self.n

    def centre_at(self, s, rad=RB):
        return (self.a[0] + s * self.d[0] + rad * self.n[0], self.a[1] + s * self.d[1] + rad * self.n[1])

    def param_of(self, p):
        return dot(sub(p, self.a), self.d)


class Circ:
    """A round bump (a white joint or knob)."""

    def __init__(self, c, r, name="", e=0.75, kt=0.95):
        self.c, self.r, self.name, self.e, self.kt = c, r, name, e, kt

    def touches(self, p, v, rad=RB):
        return norm(sub(p, self.c)) <= self.r + rad and dot(v, sub(p, self.c)) < 0

    def normal_at(self, p):
        return unit(sub(p, self.c))


def reflect(v, n, e, kt):
    vn = dot(v, n)
    vt = sub(v, mul(n, vn))
    return add(mul(vt, kt), mul(n, -e * vn))


def flight(p0, v0, t0):
    """pos(t), vel(t) of a parabola from p0 with velocity v0 at time t0."""
    pos = lambda t: (p0[0] + v0[0] * (t - t0), p0[1] + v0[1] * (t - t0) + 0.5 * G * (t - t0) ** 2)
    vel = lambda t: (v0[0], v0[1] + G * (t - t0))
    return pos, vel


def find_hit(p0, v0, t0, surfaces, t_max=400.0, rad=RB, dt=1.0 / 16, ignore=None, ignore_for=1.5):
    """First time the flight touches one of the surfaces: (t, surface, position, velocity), or None."""
    pos, vel = flight(p0, v0, t0)
    t = t0
    while t < t_max:
        t += dt
        for s in surfaces:
            if s is ignore and t - t0 < ignore_for:
                continue
            if s.touches(pos(t), vel(t), rad):
                lo, hi = t - dt, t
                for _ in range(8):
                    mid = (lo + hi) / 2
                    if s.touches(pos(mid), vel(mid), rad):
                        hi = mid
                    else:
                        lo = mid
                return hi, s, pos(hi), vel(hi)
    return None


class Roll:
    """Rolling along a Seg: s(t) = s0 + v0 t + a t^2 / 2 with a = G times the downhill part of the direction (plus friction)."""

    def __init__(self, seg, s0, v0, t0, friction=0.0):
        self.seg, self.s0, self.v0, self.t0, self.mu = seg, s0, v0, t0, friction
        self.a = G * seg.d[1]
        self.t_stop = None
        if friction:
            # friction opposes the motion until it stops (only used on level ground)
            self.t_stop = t0 + abs(v0) / friction if abs(self.a) < 1e-9 else None

    def s(self, t):
        tau = t - self.t0
        if self.t_stop is not None:
            tau = min(tau, self.t_stop - self.t0)
            a = -math.copysign(self.mu, self.v0)
            return self.s0 + self.v0 * tau + 0.5 * a * tau * tau
        return self.s0 + self.v0 * tau + 0.5 * self.a * tau * tau

    def v(self, t):
        tau = t - self.t0
        if self.t_stop is not None:
            if t >= self.t_stop:
                return 0.0
            return self.v0 - math.copysign(self.mu, self.v0) * tau
        return self.v0 + self.a * tau

    def pos(self, t):
        return self.seg.centre_at(self.s(t))

    def vel(self, t):
        return mul(self.seg.d, self.v(t))

    def until(self, t_max, circles=(), dt=1.0 / 16):
        """Roll until the ball leaves an end of the segment (kind "end"), touches one of the circles (kind "circle", with the circle),
        or stops (kind "stop"). Returns (t, kind, extra)."""
        t = self.t0
        while t < t_max:
            t += dt
            s = self.s(t)
            if self.t_stop is not None and t >= self.t_stop:
                return self.t_stop, "stop", None
            if s <= 0 or s >= self.seg.len:
                return t, "end", None
            p, v = self.pos(t), self.vel(t)
            for c in circles:
                if c.touches(p, v):
                    return t, "circle", c
        return t_max, "time", None


def sample(pieces, t):
    """Position at time t from a list of (t0, t1, pos_fn); the last piece that has started wins."""
    best = None
    for t0, t1, fn in pieces:
        if t0 - 1e-9 <= t <= t1 + 1e-9:
            best = fn
    if best is None:
        raise ValueError(f"no piece covers t={t}")
    return best(t)


def simulate(p, v, t, surfaces, stop_at=None, max_events=14, roll_below=1.6, t_max=400.0, no_roll_circles=()):
    """Follow the ball from p (centre) with velocity v at time t until it has made max_events contacts, `stop_at(p, t)` is true, or it
    leaves (no hit). Returns a list of events: ("hit", t, surface, p, v_in, v_out), ("roll", t0, t1, seg, s0, s1, v0, v1, kind, extra)
    and ("leave", t, p, v). A contact whose normal speed afterwards is below roll_below on a Seg turns into a roll along it; a roll ends
    at the segment's end (the ball leaves tangentially), or on a bump (a Circ), which reflects it like any other contact."""
    events = []
    ignore = None
    for _ in range(max_events):
        h = find_hit(p, v, t, surfaces, t_max, ignore=ignore)
        if h is None:
            events.append(("leave", t, p, v))
            return events
        th, s, ph, vin = h
        vout = reflect(vin, s.normal_at(ph), s.e, s.kt)
        events.append(("hit", th, s, ph, vin, vout))
        ignore = s
        if isinstance(s, Seg) and dot(vout, s.n) < roll_below:
            s0 = s.param_of(ph)
            v0 = dot(vout, s.d)
            r = Roll(s, s0, v0, th)
            circles = [c for c in surfaces if isinstance(c, Circ) and c not in no_roll_circles]
            t1, kind, extra = r.until(t_max, circles)
            events.append(("roll", th, t1, s, s0, r.s(t1), v0, r.v(t1), kind, extra))
            if kind == "end":
                p, v, t = r.pos(t1), r.vel(t1), t1
                ignore = s
            elif kind == "circle":
                pc, vc, tc = r.pos(t1), r.vel(t1), t1
                vo = reflect(vc, extra.normal_at(pc), extra.e, extra.kt)
                events.append(("hit", tc, extra, pc, vc, vo))
                p, v, t = pc, vo, tc
                ignore = s
            else:
                return events
        else:
            p, v, t = ph, vout, th
        if stop_at and stop_at(p, t):
            return events
    return events


def build_path(events, p0, v0, t0):
    """The motion the events describe, as pieces [(ta, tb, fn, mode)]: flights ("air") between contacts and rolls ("roll"). The last
    piece is the flight that carries on from the final state (to be cut by the caller)."""
    pieces = []
    t, p, v = t0, p0, v0
    for e in events:
        if e[0] == "hit":
            th, ph, vout = e[1], e[3], e[5]
            if th > t + 1e-9:
                pieces.append((t, th, flight(p, v, t)[0], "air"))
            t, p, v = th, ph, vout
        elif e[0] == "roll":
            _, th, t1, seg, s0, s1, rv0, rv1, kind, extra = e
            r = Roll(seg, s0, rv0, th)
            pieces.append((th, t1, r.pos, "roll"))
            t, p, v = t1, r.pos(t1), r.vel(t1)
        elif e[0] == "leave":
            t, p, v = e[1], e[2], e[3]
    pieces.append((t, t + 400.0, flight(p, v, t)[0], "air"))
    return pieces


def piece_at(pieces, t):
    """(position, mode) at time t; at a boundary the later piece wins."""
    best = None
    for ta, tb, fn, mode in pieces:
        if ta - 1e-9 <= t <= tb + 1e-9:
            best = (fn(t), mode)
    if best is None:
        raise ValueError(t)
    return best
