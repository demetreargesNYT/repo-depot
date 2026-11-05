"""Connections: "purple first" (Demetre's brief, 2026-11-04).

The left stack's top slab starts the loop yellow. The ball hunts for purple on it: bounce 1 pops the slab green and it shakes sideways
(Connections' wrong-guess shake), bounce 2 pops it blue and shakes again (the ball then gathers itself a little longer), bounce 3 is a
bigger, more determined bounce: the slab turns purple and locks with a 2 px lift instead of shaking. The ball celebrates with a small
hop and a roll back of a few degrees (its dot tilts up, a glance). Then it moves on: it hops onto the wall shelf, hops down onto the
right stack, idles on its lime slab, and hops home. While it is away the left stack shuffles (its slabs slide out sideways and back in
a different order) and the top slab pops back to yellow as it settles, so the loop starts clean. The intro is unchanged except that the
top slab is yellow all through it (its setup colour). There is no hidden reset: the ball lands where it began, at rest.

The ball's node is its contact point (scaleX/scaleY on it are the squash, about the contact); its spin pivot turns it about its
centre. Every flight is a parabola at 0.40 per frame squared, on whole frames; the rolls ease in and out; the net roll distance is 0,
so the dot ends where it began.
"""
import math

from common import INTRO, bake, dip, last_values, rebuild_built, smooth

ROOM = "Connections"
BALL, SPIN = "1:559", "1:560"
SHELF, LIME, LILAC = "1:721", "1:579", "1:635"              # the wall shelf, the right stack's lime slab, the left stack's top slab
TOP_LIME, MID_BLUE, MID_BLACK = "1:664", "1:692", "1:706"   # the left stack's other moving slabs (its bottom pair stays)
TOP_STROKE, TOP_COLOUR = "1:2345", "1:648"                  # the top slab's stroke, and its fill's colour
YELLOW, GREEN, BLUE, PURPLE = "FFF9DF6D", "FFA0C35A", "FFB0C4EF", "FFBA81C5"   # Connections' own four group colours
PATH = {LILAC: "1:638", TOP_LIME: "1:667", MID_BLUE: "1:695", MID_BLACK: "1:709"}   # each slab's outline path
R = 17.68
G = 0.40
SHELF_Y = 575.0            # on the shelf board, in the pocket left of the books
STACK_Y = 678.0            # on the right stack's lime slab

SHAKE2_AT = 8                                   # bounce 2's shake starts this long after the landing (20+ frames after the last swing of the first)
SHAKE_T = 18                                    # the wrong-guess shake: 4 swings in 0.3 s, dying away to still
LIFT, LIFT_UP, LIFT_DOWN = 2.0, 6, 12           # the solved group's lock: up 2 px in 6 frames, back in 12
POP = 8                                         # the recolour pop's scale pulse (frames); the colour itself changes over 6
# the shuffle: each slab's x offset out, the frame it starts out and the frame it starts back in (relative to the shuffle's start)
SHUFFLE = [(LILAC, 56.0, 0, 50), (TOP_LIME, -60.0, 5, 56), (MID_BLUE, 28.0, 10, 38), (MID_BLACK, -48.0, 15, 44)]
SLIDE = 16


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


SHAKE_PTS = [(0, 0.0), (3, 3.0), (8, -1.6), (12, 0.8), (15, -0.25), (18, 0.0)]   # (frame, x): each swing about half the last


def shake(u):
    """The wrong-guess shake u frames after it starts: side to side, each swing about half the last, still at the end."""
    if not 0 < u < SHAKE_T:
        return 0.0
    for (u0, v0), (u1, v1) in zip(SHAKE_PTS, SHAKE_PTS[1:]):
        if u0 <= u <= u1:
            return v0 + (v1 - v0) * smooth((u - u0) / (u1 - u0))
    return 0.0


def lift(u):
    """The lock's lift (as a negative y): up LIFT in LIFT_UP frames, back to rest in LIFT_DOWN, no overshoot."""
    if not 0 < u < LIFT_UP + LIFT_DOWN:
        return 0.0
    if u <= LIFT_UP:
        return -LIFT * smooth(u / LIFT_UP)
    return -LIFT * (1 - smooth((u - LIFT_UP) / LIFT_DOWN))


def pulse(u, n=POP):
    return math.sin(math.pi * u / n) ** 2 if 0 < u < n else 0.0


def slide(u):
    """0 at the start of a slide, 1 at the end (eased both ways)."""
    return smooth(u / SLIDE)


def colour_keys(doc, anim, oid, keys):
    """Colour keys for a SolidColor: [(frame, "AARRGGBB", "hold" | "linear")]."""
    a, b = doc.anim(anim)
    pad = " " * 16
    lines = [f'            <KeyedObject objectId="{oid}" id="{doc.new_id()}">',
             f'{pad}<KeyedProperty property="colorValue" id="{doc.new_id()}">']
    for frame, value, how in keys:
        interp = ' interpolationType="linear"' if how == "linear" else ""
        lines.append(f'{pad}    <KeyFrameColor value="{value}"{interp} frame="{frame}" id="{doc.new_id()}"/>')
    lines += [f"{pad}</KeyedProperty>", "            </KeyedObject>"]
    doc.lines[b:b] = lines


def build(doc, scene, sheet):
    intro, loop = f"{ROOM} Intro", f"{ROOM} Loop"
    last = {(o, p): v for o, p, v in last_values(doc, intro)}
    start = (last[(BALL, "x")], last[(BALL, "y")])
    x0, y0 = start
    for oid in (BALL, SPIN, LILAC):                 # the old loop: the ball, its turn and the slab's old squash
        doc.drop_object(loop, oid)

    # the top slab's colour is yellow wherever the loop does not key it (the intro, Waiting, Built), and its stroke keeps its
    # weight when the slab scales
    i = doc.idx(TOP_COLOUR)
    doc.lines[i] = doc.lines[i].replace("FFD2BEFF", YELLOW)
    i = doc.idx(TOP_STROKE)
    doc.lines[i] = doc.lines[i].replace("<Stroke ", '<Stroke transformAffectsStroke="false" ', 1)

    b = Path(start)
    b.rest(8)                                       # gathers
    b.hop(start, 16)                                # bounce 1 (slab to green, shakes)
    c1 = b.f
    b.rest(4)
    b.hop(start, 18)                                # bounce 2 (slab to blue, shakes); the flight lasts as long as bounce 1's shake
    c2 = b.f
    b.rest(28)                                      # a little longer: gathering itself (it rides the slab's second shake)
    peak3 = b.hop(start, 26)                        # bounce 3: bigger, more determined (slab to purple, locks)
    c3 = b.f
    b.rest(18)                                      # the lock settles
    b.hop(start, 12)                                # the proud hop
    b.rest(6)
    glance = 4.6                                    # about 15 degrees of roll back
    b.roll(x0 - glance, 14)                         # rolls back a few degrees: the dot tilts up
    b.rest(22)
    b.roll(x0, 14)
    b.rest(4)
    f_leave = b.f
    peak1 = b.hop((734.0, SHELF_Y), 39)             # up onto the shelf, into the pocket left of the books
    f_shelf = b.f
    b.rest(10)
    peak2 = b.hop((800.0, STACK_Y), 38)             # off the shelf's front, down onto the right stack
    f_stack = b.f
    b.rest(8)
    b.roll(836.0, 28)                               # idles on the lime slab: along,
    b.rest(6)
    b.roll(800.0, 28)                               # and back
    b.rest(6)
    peak4 = b.hop(start, 47)                        # and home, landing at rest where it began
    f_home = b.f
    b.rest(20)                                      # long enough for the landing squash and the slab's dip to finish
    L = b.f
    assert abs(b.c[L][0] - x0) < 1e-9 and abs(b.c[L][1] - y0) < 1e-9

    # the shuffle starts a beat after the ball has left, and ends well before it comes back
    S = f_leave + 10
    ends = max(i0 + SLIDE for _, _, _, i0 in SHUFFLE)
    assert S + ends < f_home - 40, (S + ends, f_home)
    f_seat = S + next(i0 for pid, _, _, i0 in SHUFFLE if pid == LILAC) + SLIDE      # the top slab is back in place

    def slab_x(pid, f):                             # the left stack's slabs: the shuffle, and the top slab's shakes
        dx = 0.0
        for q, off, o0, i0 in SHUFFLE:
            if q == pid:
                dx = off * (slide(f - S - o0) - slide(f - S - i0))
        if pid == LILAC:
            dx += shake(f - (c1 + 4)) + shake(f - (c2 + SHAKE2_AT))
        return dx

    def slab_y(f):
        return lift(f - c3) + dip(f - f_home, 2.0, 20)

    # the ball rides the top slab through the second shake and the lock (it is resting on it)
    cx = list(b.c)
    for f in range(L + 1):
        if c2 + SHAKE2_AT <= f <= c2 + SHAKE2_AT + SHAKE_T and b.mode[min(f, L - 1)] == "rest":
            cx[f] = (cx[f][0] + slab_x(LILAC, f), cx[f][1])
        if c3 <= f <= c3 + LIFT_UP + LIFT_DOWN and b.mode[min(f, L - 1)] == "rest":
            cx[f] = (cx[f][0], cx[f][1] + lift(f - c3))
    b.c = cx

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

    # the pieces: the right stack and the shelf give a little where the ball lands
    doc.set_prop(intro, SHELF, "y", [(0, 0.0, "hold")])
    for oid, f, depth, T in ((SHELF, f_shelf, 1.5, 18), (LIME, f_stack, 2.5, 20)):
        rest_y = last.get((oid, "y"), 0.0)
        doc.set_prop(loop, oid, "y", bake({g: rest_y + dip(g - f, depth, T) for g in fr}, fr))
    # the top slab: lifts when it locks, dips when the ball comes home; pops at each recolour
    pops = (c1, c2, c3, f_seat)
    rest_y = last.get((LILAC, "y"), 0.0)
    doc.set_prop(loop, LILAC, "y", bake({g: rest_y + slab_y(g) for g in fr}, fr))
    sc_x = {g: 1.0 + 0.04 * sum(pulse(g - p) for p in pops) for g in fr}
    sc_y = {g: 1.0 + 0.06 * sum(pulse(g - p) for p in pops) for g in fr}
    doc.set_prop(loop, LILAC, "scaleX", bake(sc_x, fr))
    doc.set_prop(loop, LILAC, "scaleY", bake(sc_y, fr))
    # the slabs' sideways moves (the top slab's also carry its two shakes). They are keyed on each slab's outline path (fill and
    # stroke follow it), not on the slab's node: tools/check_chapter.py adds the Floor Plane's parked x (2347) to a node's keys
    # and would call a 56 px slide "beyond x 1585", although the plane is at 748 whenever the loop plays
    for pid in (LILAC, TOP_LIME, MID_BLUE, MID_BLACK):
        doc.set_prop(intro, PATH[pid], "x", [(0, 0.0, "hold")])
        doc.set_prop(loop, PATH[pid], "x", bake({g: slab_x(pid, g) for g in fr}, fr))
    # the top slab's colour: each change is a quick pop (6 frames) on the bounce's contact; yellow again as it is back in place
    colour_keys(doc, loop, TOP_COLOUR, [
        (0, YELLOW, "hold"), (c1, YELLOW, "linear"), (c1 + 6, GREEN, "hold"),
        (c2, GREEN, "linear"), (c2 + 6, BLUE, "hold"),
        (c3, BLUE, "linear"), (c3 + 6, PURPLE, "hold"),
        (f_seat, PURPLE, "linear"), (f_seat + 6, YELLOW, "hold")])
    doc.rebuild_waiting(ROOM)
    rebuild_built(doc, ROOM)
    # (after the rebuilds, which read only number keys) the intro holds the top slab yellow, so the loop may key its colour
    for anim in (intro, f"{ROOM} Waiting", f"{ROOM} Built"):
        colour_keys(doc, anim, TOP_COLOUR, [(0, YELLOW, "hold")])

    s = lambda f: f"{f / 60:.2f} s"
    tops = ", ".join(f"{p - 2 * R:.0f}" for p in (peak3, peak1, peak2, peak4))
    return (f"{ROOM}: bounces at {s(c1)}, {s(c2)}, {s(c3)} (slab green, blue, purple), proud hop and glance, leaves {s(f_leave)}, "
            f"shelf {s(f_shelf)}, right stack {s(f_stack)}, home {s(f_home)}; shuffle {s(S)} to {s(S + ends)}, top slab yellow {s(f_seat + 6)}; "
            f"loop {L / 60:.2f} s ({L} frames); ball tops at y {tops}")
