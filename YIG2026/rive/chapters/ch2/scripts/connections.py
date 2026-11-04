"""Connections: a longer loop that plays at once (Demetre's pins, 2026-11-04 10:40, notes 2 and 3).

The intro is unchanged (the roll-in, the hop onto the left stack, the lockup). The loop starts on the intro's last pose and moves at
once: the ball idles on the left stack's lilac slab (rolls left, then right), hops up onto the wall shelf (the free spot left of the
books), drops off its front onto the right stack, idles there (rolls right, then back), and hops back to where it began. It lands
there at rest and the loop ends exactly as it started (same place, at rest), so the reset can't be seen.

The ball's node is its contact point (scaleX/scaleY on it are the squash, about the contact); its spin pivot turns it about its
centre. Every flight is a parabola at 0.40 per frame squared, on whole frames; the rolls ease in and out; the net roll distance is 0,
so the dot ends where it began. The shelf and the two slabs dip a little when the ball lands on them.
"""
import math

from common import INTRO, bake, dip, last_values, rebuild_built

ROOM = "Connections"
BALL, SPIN = "1:559", "1:560"
SHELF, LIME, LILAC = "1:721", "1:579", "1:635"         # the wall shelf, the right stack's lime slab, the left stack's lilac slab
R = 17.68
G = 0.40
SLAB_Y = 624.36            # contact y on the lilac slab's face (where the intro leaves the ball)
SHELF_Y = 575.0            # on the shelf board, in the pocket left of the books
STACK_Y = 678.0            # on the right stack (the lime slab's face and the blue bar)


class Path:
    """The ball's contact point frame by frame, with what it is doing from each frame to the next."""

    def __init__(self, p):
        self.c = [p]
        self.mode = []
        self.landings = []                  # (frame, impact speed)

    @property
    def f(self):
        return len(self.c) - 1

    def rest(self, n):
        for _ in range(n):
            self.mode.append("rest")
            self.c.append(self.c[-1])

    def roll(self, x1, n):
        x0, y = self.c[-1]
        for i in range(1, n + 1):
            u = 0.5 - 0.5 * math.cos(math.pi * i / n)
            self.mode.append("roll")
            self.c.append((x0 + (x1 - x0) * u, y))

    def hop(self, p1, n):
        """A parabola at G from the current point to p1 in exactly n frames (from rest: the ball's own push)."""
        (x0, y0), (x1, y1) = self.c[-1], p1
        vx = (x1 - x0) / n
        vy0 = (y1 - y0 - 0.5 * G * n * n) / n
        for i in range(1, n + 1):
            self.mode.append("air")
            self.c.append((x0 + vx * i, y0 + vy0 * i + 0.5 * G * i * i))
        self.c[-1] = p1
        self.landings.append((self.f, math.hypot(vx, vy0 + G * n)))
        return min(y0 + vy0 * t + 0.5 * G * t * t for t in range(n + 1))


def build(doc, scene, sheet):
    intro, loop = f"{ROOM} Intro", f"{ROOM} Loop"
    last = {(o, p): v for o, p, v in last_values(doc, intro)}
    start = (last[(BALL, "x")], last[(BALL, "y")])
    for oid in (BALL, SPIN, LILAC):                 # the old loop: the ball, its turn and the slab's old squash
        doc.drop_object(loop, oid)

    b = Path(start)
    b.roll(588.0, 42)                               # idle on the lilac slab: a little roll left,
    b.rest(6)
    b.roll(638.0, 54)                               # then right, to the slab's right side
    b.rest(6)
    peak1 = b.hop((734.0, SHELF_Y), 39)             # up onto the shelf, into the pocket left of the books
    f_shelf = b.f
    b.rest(14)
    peak2 = b.hop((800.0, STACK_Y), 38)             # off the shelf's front, down onto the right stack
    f_stack = b.f
    b.rest(10)
    b.roll(880.0, 62)                               # idle on the right stack: along onto the blue bar,
    b.rest(10)
    # ...and back, to where the rolls add up to nothing, so the dot comes round to where it began
    net = (588.0 - start[0]) + (638.0 - 588.0) + (880.0 - 800.0)
    b.roll(880.0 - net, 60)
    b.rest(6)
    peak3 = b.hop(start, 47)                        # and back to where it started, landing at rest
    f_home = b.f
    b.rest(20)                                      # long enough for the landing squash and the slab's dip to finish
    L = b.f
    assert abs(b.c[L][0] - start[0]) < 1e-9 and abs(b.c[L][1] - start[1]) < 1e-9

    # squash on each landing, in proportion to the impact (a smooth pulse, 14 frames, no overshoot)
    sx = [1.0] * (L + 1)
    sy = [1.0] * (L + 1)
    for f, v in b.landings:
        a = min(0.16, 0.014 * v + 0.02)
        for u in range(15):
            g = f + u
            if g > L:
                break
            p = math.sin(math.pi * u / 14) ** 2
            sy[g] = min(sy[g], 1 - a * p)
            sx[g] = max(sx[g], 1 + 0.7 * a * p)
    # the turn: rolling turns with the distance; the hops leave from rest, so they carry no turn; at rest it is still
    th = [0.0]
    for f in range(L):
        dx = b.c[f + 1][0] - b.c[f][0]
        th.append(th[-1] + (dx / R if b.mode[f] == "roll" else 0.0))
    assert abs(th[-1]) < 1e-6, th[-1]

    fr = range(L + 1)
    doc.set_duration(loop, L + 1)
    for oid, prop, vals in ((BALL, "x", [c[0] for c in b.c]), (BALL, "y", [c[1] for c in b.c]),
                            (BALL, "scaleX", sx), (BALL, "scaleY", sy), (SPIN, "rotation", th)):
        doc.set_prop(loop, oid, prop, bake({f: vals[f] for f in fr}, fr))
    # the pieces give a little where the ball lands (each about its own node; a single smooth dip, no overshoot)
    doc.set_prop(intro, SHELF, "y", [(0, 0.0, "hold")])
    for oid, f, depth, T in ((SHELF, f_shelf, 1.5, 18), (LIME, f_stack, 2.5, 20), (LILAC, f_home, 2.0, 20)):
        rest_y = last.get((oid, "y"), 0.0)
        doc.set_prop(loop, oid, "y", bake({g: rest_y + dip(g - f, depth, T) for g in fr}, fr))
    doc.rebuild_waiting(ROOM)
    rebuild_built(doc, ROOM)

    s = lambda f: f"{(INTRO + f) / 60:.2f} s"
    tops = ", ".join(f"{p - 2 * R:.0f}" for p in (peak1, peak2, peak3))
    return (f"{ROOM}: idles on the left stack from {s(0)}, hops onto the shelf {s(f_shelf)}, drops onto the right stack {s(f_stack)}, "
            f"idles, hops home {s(f_home)}; loop {L / 60:.2f} s; ball tops at y {tops}")
