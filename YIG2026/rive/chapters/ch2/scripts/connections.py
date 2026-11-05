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
SHELF_COLOUR, LIME_COLOUR, BAR_COLOUR = "1:829", "1:591", "1:605"   # the shelf board's, the lime slab's and the far right blue bar's fills
DRAWN_LIME, DRAWN_BLUE = "FFE6FFAA", "FF82D1FF"             # their drawn colours
BAR = "1:593"                                               # the far right stack's blue bar (Right Middle Blue)
# the items on the shelf, nearest the ball's landing first: (shapes that move together, tilt in degrees, lift in px, delay in frames).
# The ball lands left of the books; each book answers the shelf's dip with its own small tilt (leaning away) and lift, a short chain
BOOKS = [(("1:767",), 2.0, 2.0, 0), (("1:759",), 1.6, 1.6, 2), (("1:783",), 1.2, 1.2, 4),
         (("1:735", "1:743", "1:751"), 0.8, 0.8, 6), (("1:727", "1:722"), 0.6, 0.6, 8)]
BOOK_T = 18                                                 # one book's reaction: 0.3 s, a single bump, no wobble
YELLOW, GREEN, BLUE, PURPLE = "FFF9DF6D", "FFA0C35A", "FFB0C4EF", "FFBA81C5"   # Connections' own four group colours
PATH = {LILAC: "1:638", TOP_LIME: "1:667", MID_BLUE: "1:695", MID_BLACK: "1:709"}   # each slab's outline path
R = 17.68
G = 0.40
SHELF_Y = 575.0            # on the shelf board, in the pocket left of the books
STACK_Y = 678.0            # on the lime slab
BAR_Y = 676.0              # on the far right stack's blue bar (its top edge is at 674)

SHAKE2_AT = 8                                   # bounce 2's shake starts this long after the landing (20+ frames after the last swing of the first)
SHAKE_T = 18                                    # the wrong-guess shake: 4 swings in 0.3 s, dying away to still
LIFT, LIFT_UP, LIFT_DOWN = 2.0, 6, 12           # the solved group's lock: up 2 px in 6 frames, back in 12
POP = 8                                         # the recolour pop's scale pulse (frames); the colour itself changes over 6
# the shuffle: each slab's x offset out, the frame it starts out and the frame it starts back in (relative to the shuffle's start)
SHUFFLE = [(LILAC, 56.0, 0, 50), (TOP_LIME, -60.0, 5, 56), (MID_BLUE, 28.0, 10, 38), (MID_BLACK, -48.0, 15, 44)]
SLIDE = 16
RIDE_X = 2 / 7                                  # a rolling ball's centre follows 2/7 of a board moved under it
LAND_MAX, BIG, GATHER = 0.06, 0.08, 0.05        # squash maximums (CLAUDE.md): a landing 6%, the big earned landing 8%, a gather 5%


class Path:
    """The ball's contact point frame by frame, with what it is doing from each frame to the next."""

    def __init__(self, p):
        self.c = [p]
        self.mode = []
        self.landings = []                  # (frame, impact speed)
        self.flights = []                   # (takeoff frame, landing frame)
        self.vx = 0.0                       # the last hop's sideways speed

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

    def settle(self, v0, n):
        """Settles into rest: rolls on at v0 a frame (signed) and eases to a stop in n frames (a steady slowing, 0 at the end)."""
        x0, y = self.c[-1]
        for i in range(1, n + 1):
            self.mode.append("roll")
            self.c.append((x0 + v0 * i - v0 * i * i / (2 * n), y))

    def hop(self, p1, n):
        """A parabola at G from the current point to p1 in exactly n frames (from rest: the ball's own push)."""
        (x0, y0), (x1, y1) = self.c[-1], p1
        vx = (x1 - x0) / n
        vy0 = (y1 - y0 - 0.5 * G * n * n) / n
        for i in range(1, n + 1):
            self.mode.append("air")
            self.c.append((x0 + vx * i, y0 + vy0 * i + 0.5 * G * i * i))
        self.c[-1] = p1
        self.flights.append((self.f - n, self.f))
        self.vx = vx
        self.landings.append((self.f, math.hypot(vx, vy0 + G * n)))
        return min(y0 + vy0 * t + 0.5 * G * t * t for t in range(n + 1))


SHAKE_PTS = [(0, 0.0), (3, 3.0), (8, -1.6), (12, 0.8), (15, -0.25), (18, 0.0)]   # (frame, x): each swing about half the last


def small_hop_landing(xa, target, nh, ns):
    """Where a small hop from xa (nh frames) must land so that its settle roll (ns frames, starting at the hop's sideways speed)
    ends exactly on target."""
    k = ns / (2 * nh)
    return (target + xa * k) / (1 + k)


def small_hop(b, target, nh, ns):
    """A smaller bounce on the same piece, by the ball's own effort, that lands and settles exactly onto target. Returns its landing
    frame (its contact pops the piece's colour)."""
    xa, y = b.c[-1]
    b.hop((small_hop_landing(xa, target, nh, ns), y), nh)
    f = b.f
    b.settle(b.vx, ns)
    b.c[-1] = (target, y)
    return f


def shake(u):
    """The wrong-guess shake u frames after it starts: side to side, each swing about half the last, still at the end."""
    if not 0 < u < SHAKE_T:
        return 0.0
    for (u0, v0), (u1, v1) in zip(SHAKE_PTS, SHAKE_PTS[1:]):
        if u0 <= u <= u1:
            return v0 + (v1 - v0) * smooth((u - u0) / (u1 - u0))
    return 0.0


def book_bump(u, T=BOOK_T):
    """One book's answer u frames after the shelf's hit: up to 1 and back to 0 in T frames, a single smooth bump."""
    return math.sin(math.pi * u / T) ** 2 if 0 < u < T else 0.0


def doc_attr(doc, oid, name):
    import re
    m = re.search(rf' {name}="([^"]*)"', doc.lines[doc.idx(oid)])
    return m.group(1) if m else "0"


def lift(u):
    """The lock's lift (as a negative y): up LIFT in LIFT_UP frames, back to rest in LIFT_DOWN, no overshoot."""
    if not 0 < u < LIFT_UP + LIFT_DOWN:
        return 0.0
    if u <= LIFT_UP:
        return -LIFT * smooth(u / LIFT_UP)
    return -LIFT * (1 - smooth((u - LIFT_UP) / LIFT_DOWN))


def pulse(u, n=POP):
    return math.sin(math.pi * u / n) ** 2 if 0 < u < n else 0.0


def land_squash(u, a):
    """A landing squash u frames after the contact (as a change of scaleY): down to a in 3 frames, springing back past rest by a fifth
    of it at 8 frames (the one tiny overshoot), and at rest by 12 (0.2 s)."""
    if not 0 < u < 12:
        return 0.0
    if u <= 3:
        return -a * smooth(u / 3)
    if u <= 8:
        return -a + 1.2 * a * smooth((u - 3) / 5)
    return 0.2 * a * (1 - smooth((u - 8) / 4))


def gather_squash(u, a=GATHER):
    """The gather before a big hop, u frames from the takeoff: down to a over 9 frames (0.15 s), released in the hop's first 4."""
    if -9 < u <= 0:
        return -a * smooth((u + 9) / 9)
    if 0 < u < 4:
        return -a * (1 - smooth(u / 4))
    return 0.0


def landing_amount(v):
    """The landing squash for an impact of v a frame: up to 6%."""
    return min(LAND_MAX, 0.006 * v + 0.01)


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


def settle_intro(doc, intro):
    """The intro's landing (2.57 s) no longer stops dead: it lands 10 px short of where the ball used to land and rolls on, easing,
    through its small hop and second landing (2.88 s), to rest on the same spot as before (x 616.07) by frame 188. The roll-in
    before the landing keeps its keys but ends 10 px earlier (a touch slower), and the turn follows the ball: it is (x - 616.07) / R
    all the way, in flight as well, so it comes round to 0 at rest. The intro's y keys and its length are untouched."""
    end, D = 616.07001, 10.0
    v0, f_a, f_b, f_c = 1.2, 159, 173, 188
    v1 = (D - 2.5 * v0) / (2.5 + 14 + 7.5)
    d = {}
    for f in range(154, f_c):
        if f < f_a:
            d[f] = v0 + (v1 - v0) * (f - 154 + 0.5) / (f_a - 154)
        elif f < f_b:
            d[f] = v1
        else:
            d[f] = v1 * (1 - (f - f_b + 0.5) / (f_c - f_b))
    assert abs(sum(d.values()) - D) < 1e-9
    x = {154: end - D}
    for f in range(154, f_c):
        x[f + 1] = x[f] + d[f]
    fr = range(154, f_c + 1)
    xk = bake(x, fr)
    rot = {f: (x[f] - end) / R for f in fr}
    head_x = [(88, -80.0, "power1.out"), (124, 470.0, "linear")]
    head_r = [(88, (-80.0 - end) / R, "power1.out"), (124, (470.0 - end) / R, "linear")]
    doc.set_prop(intro, BALL, "x", head_x + xk)
    doc.set_prop(intro, SPIN, "rotation", head_r + bake(rot, fr))


def build(doc, scene, sheet):
    intro, loop = f"{ROOM} Intro", f"{ROOM} Loop"
    settle_intro(doc, intro)
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

    # The ball never stops dead on a landing: it rolls on a touch with the sideways speed it landed with and eases to a stop, now and
    # then with a tiny rock back (1.2 px, under the ball check's 1.5 px swing). Full stillness only for the gathers and the held glance.
    # The top slab's flat face runs from about x 536 to 621, the lime slab's from 738 to 824, the shelf's pocket from 730 to 736.
    b = Path(start)
    b.rest(4)                                       # gathers
    b.hop((606.0, y0), 16)                          # bounce 1 (slab to green, shakes), drifting left
    c1 = b.f
    b.settle(b.vx, 10)
    b.rest(2)
    b.hop((594.0, y0), 18)                          # bounce 2 (slab to blue, shakes)
    c2 = b.f
    b.settle(b.vx, 10)
    b.roll(b.c[-1][0] + 1.2, 10)                    # a tiny rock back
    f_gather3 = b.f
    b.rest(9)                                       # a little longer: gathering itself (it rides the slab's second shake)
    t3 = b.f
    peak3 = b.hop((604.0, y0), 26)                  # bounce 3: bigger, more determined, back to the right (slab to purple, locks)
    c3 = b.f
    b.settle(b.vx, 12)                              # rides the lock's lift as it settles
    b.rest(2)
    glance = 4.6                                    # about 15 degrees of roll back
    xg = b.c[-1][0]
    b.roll(xg - glance, 12)                         # rolls back a few degrees: the dot tilts up
    b.rest(12)                                      # the held glance
    b.roll(xg, 12)
    b.rest(9)                                       # the gather before the big hop
    f_leave = b.f
    # The journey: left stack -> the shelf -> the lime slab under it -> the far right stack (the bar) -> back to the lime slab (the
    # centre stack) -> home. Every hop between pieces is a flight (never a roll across a change of depth or of piece).
    peak1 = b.hop((731.0, SHELF_Y), 36)             # up onto the shelf, into the pocket left of the books
    f_shelf = b.f
    b.settle(0.8, 10)                               # the board takes most of the fall: a short roll, 4 px, short of the books
    b.rest(2)
    f_shelf2 = small_hop(b, 731.5, 14, 8)           # a smaller bounce back across the pocket: the shelf pops back to its lime
    b.rest(2)
    peak2 = b.hop((800.0, STACK_Y), 34)             # off the shelf's front, down onto the lime slab below it
    f_stack = b.f
    b.settle(b.vx, 12)                              # rolls on along the lime slab,
    b.roll(b.c[-1][0] - 1.2, 10)                    # a tiny rock back
    b.rest(3)
    peak5 = b.hop((896.0, BAR_Y), 30)               # over to the far right stack: onto its blue bar (it pops yellow)
    f_bar = b.f
    b.settle(b.vx, 12)
    b.roll(b.c[-1][0] - 1.2, 10)                    # a tiny rock back
    b.rest(3)
    f_bar2 = small_hop(b, b.c[-1][0], 14, 10)       # a smaller bounce on the bar: it pops back to its blue
    b.rest(3)
    peak6 = b.hop((800.0, STACK_Y), 32)             # and back to the centre (the lime slab): this landing restores its lime
    f_lime2 = b.f
    b.settle(b.vx, 12)
    # the home landing settles 7 px left and its small bounce settles onto the start; the last roll along the lime slab takes
    # what makes all the rolls add up to nothing, so the dot comes round to where it began
    home_land, home_mid = x0 + 4.0, x0 - 3.0
    x_h2 = small_hop_landing(home_mid, x0, 14, 12)
    after = (home_mid - home_land) + (x0 - x_h2)
    net = sum(b.c[f + 1][0] - b.c[f][0] for f in range(b.f) if b.mode[f] == "roll") + after
    b.rest(2)
    b.roll(b.c[-1][0] - net, 20)                    # idles along the lime slab (to where the rolls add up to nothing)
    b.rest(3)
    peak4 = b.hop((home_land, y0), 42)              # and home, landing just right of where it began (top slab to blue),
    f_home = b.f
    b.settle(2 * (home_mid - home_land) / 14, 14)   # settling left (the slab's face ends at 621: most of the fall is taken)
    b.rest(3)
    f_home2 = small_hop(b, x0, 14, 12)              # and a smaller bounce onto the start: the slab pops back to yellow
    b.rest(4)
    L = b.f
    assert abs(b.c[L][0] - x0) < 1e-9 and abs(b.c[L][1] - y0) < 1e-9, b.c[L]
    lime_xs = [x for x, _ in b.c[f_stack:f_bar - 30]] + [x for x, _ in b.c[f_lime2:f_home - 42]]
    assert 738 <= min(lime_xs) and max(lime_xs) <= 824, (min(lime_xs), max(lime_xs))
    bar_xs = [x for x, _ in b.c[f_bar:f_lime2 - 32]]
    assert 880 <= min(bar_xs) and max(bar_xs) <= 950, (min(bar_xs), max(bar_xs))
    assert 730 <= min(x for x, _ in b.c[f_shelf:f_stack - 34]) and max(x for x, _ in b.c[f_shelf:f_stack - 34]) <= 736

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
        return lift(f - c3) + dip(f - f_home, 2.0, 20) + dip(f - f_home2, 1.0, 16)

    # the turn: rolling turns with the distance (relative to the slab); the hops leave from rest, so they carry no turn
    th = [0.0]
    for f in range(L):
        dx = b.c[f + 1][0] - b.c[f][0]
        th.append(th[-1] + (dx / R if b.mode[f] == "roll" else 0.0))
    assert abs(th[-1]) < 1e-6, th[-1]

    # the ball rides the top slab while it is on it: the lock's lift and the home dip in full; the shakes as a ball on a moving
    # board does, rolling: its centre follows 2/7 of the slab's sideways move and it turns by the rest (so a shake never buzzes it).
    # A flight from the slab to the slab carries the difference as a steady drift (and spin), so it stays a parabola at 0.40
    on = set(range(0, f_leave + 1)) | set(range(f_home, L + 1))
    ride = {f: (RIDE_X * slab_x(LILAC, f), slab_y(f), (RIDE_X - 1) * slab_x(LILAC, f) / R) for f in on}
    for f0, f1 in b.flights:
        if f0 in on and f1 in on:
            for f in range(f0 + 1, f1):
                u = (f - f0) / (f1 - f0)
                ride[f] = tuple(p + (q - p) * u for p, q in zip(ride[f0], ride[f1]))
    zero = (0.0, 0.0, 0.0)
    b.c = [(c[0] + ride.get(f, zero)[0], c[1] + ride.get(f, zero)[1]) for f, c in enumerate(b.c)]
    th = [t + ride.get(f, zero)[2] for f, t in enumerate(th)]
    assert abs(th[L] - th[0]) < 1e-9

    # squash (CLAUDE.md maximums): a landing up to 6% (bounce 3, the big earned one, 8%), springing back within 0.2 s with one tiny
    # overshoot; a 5% gather before bounce 3 and before the hop to the shelf; volume constant (scaleX = 1 / scaleY)
    d = [0.0] * (L + 1)
    for f, v in b.landings:
        a = BIG if f == c3 else landing_amount(v)
        for g in range(f, min(L, f + 12) + 1):
            d[g] += land_squash(g - f, a)
    for t in (t3, f_leave):
        for g in range(t - 9, t + 4):
            d[g] += gather_squash(g - t)
    sy = [1 + x for x in d]
    sx = [1 / y for y in sy]
    squash_report = {"landings": [(round(f / 60, 2), round(BIG if f == c3 else landing_amount(v), 3)) for f, v in b.landings],
                     "gather": GATHER, "max scaleY dev": round(max(abs(x) for x in d), 3)}

    fr = range(L + 1)
    doc.set_duration(loop, L + 1)
    for oid, prop, vals in ((BALL, "x", [c[0] for c in b.c]), (BALL, "y", [c[1] for c in b.c]),
                            (BALL, "scaleX", sx), (BALL, "scaleY", sy), (SPIN, "rotation", th)):
        doc.set_prop(loop, oid, prop, bake({f: vals[f] for f in fr}, fr))

    # the intro's two landings on the top slab (2.57 s and 2.88 s) squashed 22% and 8%; brought to the maximums: 6%, and 3.9% for
    # the small one, each springing back with one tiny overshoot (the intro's motion itself is unchanged)
    fi = range(154, INTRO)
    di = {g: land_squash(g - 154, LAND_MAX) + land_squash(g - 173, landing_amount(4.8)) for g in fi}
    doc.set_prop(intro, BALL, "scaleY", [(0, 1.0, "hold")] + bake({g: 1 + di[g] for g in fi}, fi))
    doc.set_prop(intro, BALL, "scaleX", [(0, 1.0, "hold")] + bake({g: 1 / (1 + di[g]) for g in fi}, fi))

    # the pieces: the right stack and the shelf give a little where the ball lands
    doc.set_prop(intro, SHELF, "y", [(0, 0.0, "hold")])
    for oid, hits in ((SHELF, [(f_shelf, 1.5, 18), (f_shelf2, 0.8, 14)]), (LIME, [(f_stack, 2.5, 20), (f_lime2, 2.0, 18)]),
                      (BAR, [(f_bar, 2.0, 18), (f_bar2, 0.8, 14)])):
        rest_y = last.get((oid, "y"), 0.0)
        doc.set_prop(loop, oid, "y", bake({g: rest_y + sum(dip(g - f, depth, T) for f, depth, T in hits) for g in fr}, fr))
    # the books answer the shelf's dip, each in its own time and size (the shelf's group carries them; these are on top of it)
    for shapes, tilt, rise, delay in BOOKS:
        for oid in shapes:
            base_y = float(doc_attr(doc, oid, "y"))
            doc.set_prop(intro, oid, "y", [(0, base_y, "hold")])
            doc.set_prop(intro, oid, "rotation", [(0, 0.0, "hold")])
            hit = lambda g, amp: sum(amp * k * book_bump(g - f - delay) for f, k in ((f_shelf, 1.0), (f_shelf2, 0.5)))
            doc.set_prop(loop, oid, "y", bake({g: base_y - hit(g, rise) for g in fr}, fr))
            doc.set_prop(loop, oid, "rotation", bake({g: math.radians(hit(g, tilt)) for g in fr}, fr))
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
        (f_seat, PURPLE, "linear"), (f_seat + 6, YELLOW, "hold"),
        (f_home, YELLOW, "linear"), (f_home + 6, BLUE, "hold"), (f_home2, BLUE, "linear"), (f_home2 + 6, YELLOW, "hold")])
    # every other landing on a shelf or a bar pops it to a Connections colour, and its smaller bounce pops it back to its drawn lime
    # (the shelf goes blue: purple is on the top slab then; the lime slab goes green: the top slab is yellow by then)
    # the shelf goes blue and back at its smaller bounce; the lime slab goes green on its first landing and back on its second (the
    # return from the bar); the far right bar goes yellow and back to its blue at its smaller bounce
    pops2 = ((SHELF_COLOUR, f_shelf, f_shelf2, BLUE, DRAWN_LIME), (LIME_COLOUR, f_stack, f_lime2, GREEN, DRAWN_LIME),
             (BAR_COLOUR, f_bar, f_bar2, YELLOW, DRAWN_BLUE))
    for oid, f1, f2, c, drawn in pops2:
        colour_keys(doc, loop, oid, [(0, drawn, "hold"), (f1, drawn, "linear"), (f1 + 6, c, "hold"),
                                     (f2, c, "linear"), (f2 + 6, drawn, "hold")])
    doc.rebuild_waiting(ROOM)
    rebuild_built(doc, ROOM)
    # (after the rebuilds, which read only number keys) the colours in the intro: the top slab pops blue on the ball's first landing
    # (2.57 s) and back to yellow on its small hop (2.88 s); the shelf and the lime slab hold their lime. Waiting and Built hold the
    # intro's first and last colours, yellow and lime
    colour_keys(doc, intro, TOP_COLOUR, [(0, YELLOW, "hold"), (154, YELLOW, "linear"), (160, BLUE, "hold"),
                                         (173, BLUE, "linear"), (179, YELLOW, "hold")])
    for anim in (f"{ROOM} Waiting", f"{ROOM} Built"):
        colour_keys(doc, anim, TOP_COLOUR, [(0, YELLOW, "hold")])
    for anim in (intro, f"{ROOM} Waiting", f"{ROOM} Built"):
        for oid, _f1, _f2, _c, drawn in pops2:
            colour_keys(doc, anim, oid, [(0, drawn, "hold")])

    s = lambda f: f"{(INTRO + f) / 60:.2f} s"
    tops = ", ".join(f"{p - 2 * R:.0f}" for p in (peak3, peak1, peak2, peak5, peak6, peak4))
    return (f"{ROOM}: bounces at {s(c1)}, {s(c2)}, {s(c3)} (slab green, blue, purple), glance, leaves {s(f_leave)}, "
            f"shelf {s(f_shelf)} (blue) and {s(f_shelf2)} (lime), lime slab {s(f_stack)} (green), far right bar {s(f_bar)} (yellow) and {s(f_bar2)} (blue), lime slab again {s(f_lime2)} (lime), home {s(f_home)} (blue) and {s(f_home2)} (yellow); shuffle {s(S)} to {s(S + ends)}, top slab yellow {s(f_seat + 6)}; "
            f"loop {L / 60:.2f} s ({L} frames); ball tops at y {tops}; squash {squash_report}")
