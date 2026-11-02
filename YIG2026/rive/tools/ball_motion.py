"""Motion pieces for the ball loops that are written frame by frame (ch1_cards_234.py): flights, rolls, springs.

Everything returns plain numbers per frame (60 per second). Positions are in artboard units, y grows downward.
"""
import math

G = 0.2                       # px per frame squared: the fall every flight is checked against (a 30-frame fall drops 90 px)


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
