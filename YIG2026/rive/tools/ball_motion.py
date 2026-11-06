"""Motion pieces for the ball loops that are written frame by frame (ch1_cards_234.py): flights, rolls, springs.

Everything returns plain numbers per frame (60 per second). Positions are in artboard units, y grows downward.
"""
import math

# Artboard units per frame squared: the project's one gravity (CLAUDE.md, "The ball's physics"; ball_physics.G and ball_speed's check).
# It was 0.2 until 2026-11-06; Chapter 1 cards 2 to 4 (tools/ch1_cards_234.py, now history) were built with that, and card 4's softer
# hops are accepted as they are (tools/ball_speed_accepted.json).
G = 0.40                      # a 30-frame fall drops 180


def arc(p0, p1, n, h, xe=1.0):
    """n + 1 points from p0 to p1: y is the chord plus a parabola h high (so one steady gravity, 8 h / n^2); x moves steadily, or
    with t ** xe when the ball should go up first and across later (xe above 1)."""
    out = []
    for i in range(n + 1):
        t = i / n
        out.append((p0[0] + (p1[0] - p0[0]) * t ** xe, p0[1] + (p1[1] - p0[1]) * t - 4 * h * t * (1 - t)))
    return out


def gravity(n, h):
    return 8 * h / (n * n)


def fall_height(n):
    """The arc height for a plain fall of n frames at G."""
    return G * n * n / 8


def roll_distance(n, v0, D):
    """Constant acceleration that covers D in n frames starting at v0: returns s(i) for i = 0..n."""
    a = 2 * (D - v0 * n) / (n * n)
    return [v0 * i + 0.5 * a * i * i for i in range(n + 1)], a


def spring(k, depth, down=4, tau=9.0, period=18.0, cut=0.03):
    """A dip and its spring back: k frames after the contact the value goes to `depth` in `down` frames (ease-out), then returns
    with an overshoot that dies away (a released spring, so no kink where the two meet). 0 before the contact and after it dies."""
    if k <= 0:
        return 0.0
    if k <= down:
        return depth * math.sin(0.5 * math.pi * k / down)
    u = k - down
    w = 2 * math.pi / period
    v = depth * math.exp(-u / tau) * (math.cos(w * u) + math.sin(w * u) / (w * tau))
    return 0.0 if abs(v) < abs(depth) * cut and u > period else v


def pulse(k, down=2, tau=5.0, period=14.0):
    """0 to 1 quickly then back with a small overshoot: the shape of a squash on a landing."""
    return spring(k, 1.0, down, tau, period)


def smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def ease_in(t):
    t = min(1.0, max(0.0, t))
    return t * t


def ease_out(t):
    t = min(1.0, max(0.0, t))
    return 1 - (1 - t) ** 2


def rot(p, pivot, th):
    """p turned clockwise on screen by th (radians) about pivot."""
    c, s = math.cos(th), math.sin(th)
    x, y = p[0] - pivot[0], p[1] - pivot[1]
    return (pivot[0] + x * c - y * s, pivot[1] + x * s + y * c)


def release(u, depth, tau=8.0, period=18.0):
    """A spring let go from `depth` at rest, u frames ago: `depth` before the release, then it swings back past 0 and settles."""
    if u <= 0:
        return depth
    w = 2 * math.pi / period
    v = depth * math.exp(-u / tau) * (math.cos(w * u) + math.sin(w * u) / (w * tau))
    return 0.0 if abs(v) < abs(depth) * 0.03 and u > period else v


def bezier(p0, p1, p2, p3, n=60):
    """n + 1 points along a cubic Bezier."""
    out = []
    for i in range(n + 1):
        u = i / n
        a, b, c, d = (1 - u) ** 3, 3 * u * (1 - u) ** 2, 3 * u * u * (1 - u), u ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


class Path:
    """A polyline with its length, so a ball can be put at a distance along it."""

    def __init__(self, pts):
        self.pts = pts
        self.cum = [0.0]
        for a, b in zip(pts, pts[1:]):
            self.cum.append(self.cum[-1] + math.dist(a, b))
        self.length = self.cum[-1]

    def at(self, s):
        s = max(0.0, min(self.length, s))
        lo, hi = 0, len(self.pts) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if self.cum[mid] <= s:
                lo = mid
            else:
                hi = mid
        seg = self.cum[hi] - self.cum[lo]
        u = (s - self.cum[lo]) / seg if seg else 0.0
        a, b = self.pts[lo], self.pts[hi]
        return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)


def speed_profile(n, v0, v1, stop):
    """Distances covered on each of n frames: speed goes steadily from v0 to v1, and in the last `stop` frames eases to a halt.
    Returns the cumulative distance at frames 0 to n, scaled so it ends at 1.0."""
    sp = []
    for i in range(n):
        v = v0 + (v1 - v0) * i / max(n - 1, 1)
        if i >= n - stop:
            v *= 1 - smooth((i - (n - stop)) / stop) * 0.97
        sp.append(v)
    tot = sum(sp)
    cum, out = 0.0, [0.0]
    for v in sp:
        cum += v / tot
        out.append(cum)
    return out
