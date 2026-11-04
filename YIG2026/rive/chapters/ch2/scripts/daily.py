"""The Crossword, "the rooftop run" (2026-11-04): the ball runs up the skyline from the hollow bar and dives back into it, and the
skyline has its own life.

The pieces. The hollow bar is the floating three-square bar above the crate: its dark back (Floor Plane) is below the ball and its
white front (Front Boxes 1: 9:8461 and the right-hand panel 9:8471/9:8472, held shut at x 6.92) is above it, so a ball low in the bar
is hidden, and a ball rising out of its top (or dropping in) shows above the bar's top edge (y 598.1) only. The stacks, left to
right: the tall stack outside the frame (9:8612), the crate (9:8780 and its flap 9:8451), the biggest stack, five squares (9:8539,
9:8560, 9:8717), the right stack, four squares (9:8738, 9:8759 and its door 9:8441), the far cube outside the frame (9:8581). The
floating pair are two cubes whose faces are split over both planes (the lower cube: 9:8431, 9:8483, 9:8503, 9:8697; the upper cube:
9:8676, 9:8686, 9:8707, 9:8493), keyed face by face so each cube can move on its own.

The run (one gravity, 0.40 a frame squared; every move from rest is the ball's own push, as in the other game rooms' climbs): once the
bar has landed and settled (1.83 s) the ball springs up out of the bar's top and lands on the biggest stack's roof, and a small wave
ripples out along the row of stacks (the biggest stack dips, then the crate and the right stack, then the two outer stacks). A beat,
and it hops up onto the lower floating cube (which gives under it), then up onto the upper one (which gives too), the top of the
skyline; a small hop in place there, then it dives up and left and drops into the hollow bar through its open top, behind its front.
Out of sight it waits in the bar while the skyline carries on, and springs out again.

The skyline's own moves, at uneven moments, one at a time, never while the ball is on the piece: two squares turn a quarter on their
vertical axis (white to black, and later back), the 2D trick of Chapter 1 card 5's cube: two faces share one sweeping edge, their
widths in the proportion cos t : sin t, masked to the square, every line 1.5 at any width (transformAffectsStroke off); the crate is
pressed like a key (sinks 5 px, holds, comes back); and the floating pair bobs (rises 3 px and settles).

The old journey's keys are dropped: Ball_01's moves, the floating cube's old door (9:8434, 9:8435), the copy of the middle cube used to
cover the old return (Group 2's opacity) and the bar panel's slide (it stays shut: the ball goes in and out through the top).
"""
import math
import re

from common import INTRO, BallArt, Cycle, dip, emit, intro_series, plane_x, prepare_ball, smooth, num

ROOM = "The Crossword"
T0 = 110                                   # 1.83 s: the bar (Front Boxes 1) lands at 1.50 s and its squash is over at 1.82 s
G = 0.40
PANEL, PANEL_SHUT = "9:8472", 6.92
WHITE, BLACK, INK = "FFDFDBD7", "FF1F1F1F", "FF1F1F1F"

# contact lines (the line the ball's bottom sits on) and where it sits on each
BAR_FLOOR = 627.8                          # the bar's inside floor; a ball resting there is wholly behind the front (608.2 to 667.5)
BAR_X = 641.0
BAR_TOP, FRONT_L, FRONT_R = 598.1, 608.2, 667.5
MID_TOP, MID_X = 652.7, 758.0              # the biggest stack's roof (737.8 to 790.2)
LOW_TOP, LOW_X = 610.9, 836.0              # the lower floating cube's top, at its back edge (its top face is drawn over the ball, so it
                                           # sits on the back edge, 832.8 to 862.4, not into the face)
UP_TOP, UP_X = 587.15, 866.0               # the upper floating cube's top, half way back (its top face is under the ball)

# the beats: (vy at the push, frames of rest after landing)
POP_VY, MID_REST = -6.6, 14
LOW_VY, LOW_REST = -7.2, 16
UP_VY, UP_REST = -6.8, 16
TAP_VY, TAP_REST = -3.4, 12                # the small hop in place on the top of the skyline
BACK1_VY, BACK1_REST = -5.0, 14            # the way back: down to the lower floating cube
BACK2_VY, BACK2_REST = -5.0, 12            # and down to the biggest stack's roof
TAP2_VY, TAP2_REST = -3.4, 12              # a small hop in place on the roof
DIVE_VY = -8.4                             # then the dive up and left into the hollow bar
L_TOTAL = 420                              # the loop: 7.0 s, of which the ball is out of sight in the bar for about 1.5 s
WAVE2 = 0.6                                # the way back lands on the biggest stack again: a lighter wave

# the wave on the biggest stack's landing: (nodes, depth, delay frames)
MID = ("9:8539", "9:8560", "9:8717")
CRATE = ("9:8780", "9:8451")
RIGHT = ("9:8738", "9:8759", "9:8441")
OUTER = ("9:8612", "9:8581")
LOWER = ("9:8431", "9:8483", "9:8503", "9:8697")
UPPER = ("9:8676", "9:8686", "9:8707", "9:8493")
WAVE = ((MID, 2.6, 0), (CRATE, 1.8, 5), (RIGHT, 1.8, 5), (OUTER, 1.2, 10))
WAVE_T = 14
# the turning squares: (name, parent node, square shape, turns [(cycle frame, frames)]); white to black, then back
TURN_T = 22
TURNS = (("Biggest Stack Square", "9:8560", "9:8561"), ("Right Stack Square", "9:8738", "9:8739"))
BOB_T, BOB_H = 48, 3.0
PRESS_D = 5.0


class Track:
    """The ball's centre and mode on whole frames, segment by segment."""

    def __init__(self, start):
        self.pts, self.modes = [start], []
        self.pushes, self.lands, self.notes = {}, [], []

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

    def hop(self, p1, vy0, label, squash):
        """An own-effort hop from rest at the current centre that rises with vy0 and comes down onto p1 (its x and centre height)."""
        (x0, y0), (x1, y1) = self.p, p1
        T = (-vy0 + math.sqrt(vy0 * vy0 + 2 * G * (y1 - y0))) / G
        vx = (x1 - x0) / T
        self.pushes[self.f] = vx
        n = math.ceil(T - 1e-9)
        for k in range(1, n + 1):
            u = min(k, T)
            self.pts.append((x0 + vx * u, y0 + vy0 * u + 0.5 * G * u * u))
            self.modes.append("air")
        self.pts[-1] = p1
        self.lands.append((self.f, label, squash, (vx, vy0 + G * T)))
        self.notes.append((label, self.f))
        return T, (vx, vy0), (vx, vy0 + G * T)


def ease3(u):
    u = min(1.0, max(0.0, u))
    return 4 * u ** 3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2


def press(u):
    """A key press, u frames in: down in 6 frames, held 16, back up in 12."""
    if u <= 0 or u >= 34:
        return 0.0
    if u < 6:
        return PRESS_D * smooth(u / 6)
    if u < 22:
        return PRESS_D
    return PRESS_D * (1 - smooth((u - 22) / 12))


def turn_amount(k, turns):
    """0 (white) to 1 (black) and back: the turn's angle as a share of the quarter turn, eased in and out."""
    a, b = turns
    if k < a:
        return 0.0
    if k < a + TURN_T:
        return ease3((k - a) / TURN_T)
    if k < b:
        return 1.0
    if k < b + TURN_T:
        return 1 - ease3((k - b) / TURN_T)
    return 0.0


def edge(share, W):
    """The shared edge's distance from the square's left side: W cos t / (cos t + sin t), t the turn (0 to 90 degrees)."""
    t = share * math.pi / 2
    c, s = math.cos(t), math.sin(t)
    return W * c / (c + s)


def add_turn(doc, parent_id, x0, y0, W, H, name):
    """A turning square inside the stack's node (first child, so it draws over the square it stands for): the white face and the black
    face, each drawn at the square's full width and scaled sideways from its left edge, both clipped to the square. Returns the two face
    nodes' ids (white, black)."""
    i = doc.idx(parent_id)
    pad = " " * (len(doc.lines[i]) - len(doc.lines[i].lstrip()) + 4)
    clip, node = doc.new_id(), doc.new_id()
    body = [f'{pad}<Node name="{ROOM} {name}" id="{node}">']
    ids = []
    for label, colour, x, sx in (("White", WHITE, x0, 1.0), ("Black", BLACK, x0 + W, 0.0)):
        fid = doc.new_id()
        ids.append(fid)
        p = pad + "    "
        body += [f'{p}<Node x="{num(x)}" y="{num(y0)}"{"" if sx == 1 else f" scaleX={chr(34)}{num(sx)}{chr(34)}"} name="{ROOM} {name} {label}" id="{fid}">',
                 f'{p}    <Shape name="{ROOM} {name} {label} Face" id="{doc.new_id()}">',
                 f'{p}        <PointsPath isClosed="true" id="{doc.new_id()}">']
        body += [f'{p}            <StraightVertex x="{num(vx)}" y="{num(vy)}" id="{doc.new_id()}"/>' for vx, vy in ((0, 0), (W, 0), (W, H), (0, H))]
        body += [f'{p}        </PointsPath>',
                 f'{p}        <Fill id="{doc.new_id()}">',
                 f'{p}            <SolidColor colorValue="{colour}" id="{doc.new_id()}"/>',
                 f'{p}        </Fill>',
                 f'{p}        <Stroke thickness="1.5" cap="round" join="round" transformAffectsStroke="false" id="{doc.new_id()}">',
                 f'{p}            <SolidColor colorValue="{INK}" id="{doc.new_id()}"/>',
                 f'{p}        </Stroke>',
                 f'{p}        <ClippingShape sourceId="{clip}" name="{ROOM} {name} Clip" id="{doc.new_id()}"/>',
                 f'{p}    </Shape>',
                 f'{p}</Node>']
    m = 0.75                                                 # half the line: the clip keeps the faces' lines on the square's own
    body += [f'{pad}    <Shape name="{ROOM} {name} Clip" id="{clip}">',
             f'{pad}        <PointsPath isClosed="true" id="{doc.new_id()}">']
    body += [f'{pad}            <StraightVertex x="{num(vx)}" y="{num(vy)}" id="{doc.new_id()}"/>'
             for vx, vy in ((x0 - m, y0 - m), (x0 + W + m, y0 - m), (x0 + W + m, y0 + H + m), (x0 - m, y0 + H + m))]
    body += [f'{pad}        </PointsPath>', f'{pad}    </Shape>', f'{pad}</Node>']
    doc.lines[i + 1:i + 1] = body
    return ids


def square_in_parent(byid, shape_id):
    """The square's left, top, width, height in its parent node's space (the shapes are squares, some turned half a turn)."""
    sh = byid[shape_id]
    path = sh.find("PointsPath")
    vs = [(float(v.get("x", 0)), float(v.get("y", 0))) for v in path.findall("StraightVertex")]
    r = float(sh.get("rotation", 0))
    c, s = math.cos(r), math.sin(r)
    sx, sy = float(sh.get("x", 0)), float(sh.get("y", 0))
    pts = [(sx + c * x - s * y, sy + s * x + c * y) for x, y in vs]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)


# ---- clearances: the pieces as outlines on the artboard (at rest), for the flights ---------------------------------------------------
SOLIDS = {
    "the bar": [(594.3, 598.1), (667.5, 598.1), (667.5, 627.8), (594.3, 627.8)],
    "the biggest stack": [(737.8, 652.7), (790.2, 652.7), (790.2, 682.3), (804.5, 682.3), (804.5, 712.0), (722.5, 712.0), (722.5, 682.3), (737.8, 682.3)],
    "the right stack": [(882.4, 652.7), (934.7, 652.7), (934.7, 712.0), (882.4, 712.0)],
    "the lower cube": [(818.9, 622.8), (832.8, 610.9), (862.4, 610.9), (862.4, 640.5), (848.5, 652.4), (818.9, 652.4)],
    "the upper cube": [(848.5, 593.1), (862.4, 581.2), (892.0, 581.2), (892.0, 610.9), (878.2, 622.8), (848.5, 622.8)],
    "the crate": [(570.2, 681.8), (659.2, 681.8), (675.0, 702.6), (675.0, 732.2), (586.0, 732.2), (570.2, 711.5)],
}


def seg_dist(p, a, b):
    ax, ay = b[0] - a[0], b[1] - a[1]
    t = max(0.0, min(1.0, ((p[0] - a[0]) * ax + (p[1] - a[1]) * ay) / (ax * ax + ay * ay)))
    return math.hypot(p[0] - a[0] - t * ax, p[1] - a[1] - t * ay)


def inside(p, poly):
    n, c = len(poly), False
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > p[1]) != (y2 > p[1]) and p[0] < x1 + (p[1] - y1) * (x2 - x1) / (y2 - y1):
            c = not c
    return c


def clearance(p, poly):
    d = min(seg_dist(p, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))
    return -d if inside(p, poly) else d


def build(doc, scene, sheet):
    art = BallArt(scene, ROOM)
    spin = prepare_ball(doc, art)
    for a in ("Intro", "Loop", "Waiting", "Built"):
        doc.drop_object(f"{ROOM} {a}", art.b01)
    for oid in ("9:8513", "9:8434", "9:8435"):
        doc.drop_object(f"{ROOM} Loop", oid)
    doc.drop_object(f"{ROOM} Loop", PANEL)
    Rc, R = art.Rc, art.R
    byid = {e.get("id"): e for e in scene.root.iter() if e.get("id")}
    rest_y = lambda oid: float(byid[oid].get("y", 0))

    # ---- the ball's run -------------------------------------------------------------------------------------------------------
    in_bar = (BAR_X, BAR_FLOOR - Rc)
    mid, low, up = (MID_X, MID_TOP - Rc), (LOW_X, LOW_TOP - Rc), (UP_X, UP_TOP - Rc)
    tr = Track(in_bar)
    _, v_pop, _ = tr.hop(mid, POP_VY, "lands on the biggest stack's roof", 0.12)
    f_mid = tr.f
    tr.rest(MID_REST)
    tr.hop(low, LOW_VY, "lands on the lower floating cube", 0.07)
    f_low = tr.f
    tr.rest(LOW_REST)
    tr.hop(up, UP_VY, "lands on the upper floating cube, the top of the skyline", 0.09)
    f_up = tr.f
    tr.rest(UP_REST)
    tr.hop(up, TAP_VY, "a small hop in place there", 0.05)
    f_tap = tr.f
    tr.rest(TAP_REST)
    tr.hop(low, BACK1_VY, "back down onto the lower floating cube", 0.06)
    f_low2 = tr.f
    tr.rest(BACK1_REST)
    tr.hop(mid, BACK2_VY, "back onto the biggest stack's roof", 0.08)
    f_mid2 = tr.f
    tr.rest(BACK2_REST)
    tr.hop(mid, TAP2_VY, "a small hop in place on the roof", 0.05)
    f_tap2 = tr.f
    tr.rest(TAP2_REST)
    f_dive = tr.f
    tr.hop(in_bar, DIVE_VY, "drops into the hollow bar", 0.0)
    f_in = tr.f
    L = L_TOTAL
    assert L > f_in + 60, (L, f_in)
    tr.rest(L - f_in, "hidden")
    # out of sight from the frame its top is below the bar's top edge
    for g in range(f_dive + 1, f_in + 1):
        if tr.pts[g][1] - R >= BAR_TOP and FRONT_L <= tr.pts[g][0] - R and tr.pts[g][0] + R <= FRONT_R:
            tr.modes[g - 1] = "hidden"
    # the ball rides the pieces it rests on: the biggest stack's wave dip, the floating cubes' gives
    LOW_GIVE, UP_GIVE, TAP_GIVE = 2.0, 2.2, 1.0
    mid_dip = lambda k: dip(k - f_mid, WAVE[0][1], WAVE_T) + WAVE2 * dip(k - f_mid2, WAVE[0][1], WAVE_T) + dip(k - f_tap2, TAP_GIVE, 12)
    low_dip = lambda k: dip(k - f_low, LOW_GIVE, 16) + dip(k - f_low2, LOW_GIVE, 16)
    up_dip = lambda k: dip(k - f_up, UP_GIVE, 16) + dip(k - f_tap, TAP_GIVE, 12)
    pts = list(tr.pts)
    for f0, n in ((f_mid, MID_REST), (f_mid2, BACK2_REST), (f_tap2, TAP2_REST)):
        for g in range(f0, f0 + n + 1):
            pts[g] = (pts[g][0], pts[g][1] + mid_dip(g))
    for f0, n in ((f_low, LOW_REST), (f_low2, BACK1_REST)):
        for g in range(f0, f0 + n + 1):
            pts[g] = (pts[g][0], pts[g][1] + low_dip(g))
    for g in list(range(f_up, f_up + UP_REST + 1)) + list(range(f_tap, f_tap + TAP_REST + 1)):
        pts[g] = (pts[g][0], pts[g][1] + up_dip(g))
    cyc = Cycle(L)
    for g in range(L + 1):
        cyc.put(g, pts[g], tr.modes[g] if g < L else "hidden")
    for f, label, sq, vin in tr.lands:
        if sq:
            cyc.squash(f, sq, T=12)

    # ---- checks: the flights clear every piece, the ball stays under the copy line, and it goes in and out of the bar's top only ---
    worst = {}
    for g in range(1, f_in + 1):
        if tr.modes[g - 1] != "air":
            continue
        c = tr.pts[g]
        assert c[1] - R >= 425.0, ("above the copy line", g, c)
        for name, poly in SOLIDS.items():
            if name == "the bar":
                continue
            d = clearance(c, poly)
            # the ball sits on the piece it has just left or is landing on (the stroke a little into it), and passes in front of the
            # upper cube's front face on the hop up (that face is under the ball and further back)
            near_end = any(abs(g - f) <= 2 for f in (0, f_mid, f_low, f_up, f_tap, f_low2, f_mid2, f_tap2, f_dive, f_in))
            # and while it is on the floating pair (up, the hop in place, and back down) it is over the upper cube's top or beside its
            # left face, where it sits half way back
            if near_end or (name == "the upper cube" and f_low < g <= f_low2 + BACK1_REST + 4):
                continue
            worst[name] = min(worst.get(name, 1e9), d - R)
        # below the bar's top edge the ball must be wholly within the front's span (no part of it poking out of the bar's ends)
        cx, cy = c
        if cy + R > BAR_TOP and FRONT_L - R < cx < FRONT_R + R and (g < 14 or g > f_dive):
            hw = R if cy >= BAR_TOP else math.sqrt(max(0.0, R * R - (BAR_TOP - cy) ** 2))
            assert FRONT_L <= cx - hw and cx + hw <= FRONT_R, ("pokes out of the bar's end", g, c)
    for name, d in worst.items():
        assert d >= 1.0, ("too close to", name, d)

    # ---- the turn: grips at a landing (stops), from rest a little from the push, keeps its turn in the air, still at rest ---------
    r = art.R
    th = [0.0]
    w = 0.0
    for g in range(L):
        m = cyc.mode[g]
        if g in tr.pushes:
            w = 0.25 * tr.pushes[g] / r
        if m not in ("air",):
            w = 0.0
        th.append(th[-1] + w)
    total = th[-1]
    want = round(total / (2 * math.pi)) * 2 * math.pi
    for g in range(f_in + 1, L + 1):
        th[g] += (want - total) * smooth((g - f_in - 1) / 30)

    # ---- when the skyline moves on its own: uneven moments, one at a time, never on a piece the ball is on or about to land on --------
    TURN_AT = {"Right Stack Square": (f_low + 22, f_in + 8),          # black while the ball is on the floating pair; white again once it is in the bar
               "Biggest Stack Square": (f_tap - 6, f_dive + 14)}     # black while it taps on the top; white once it has dived away from the stack
    PRESS_AT = f_low2 - 6                                             # the crate is pressed (far left) while the ball comes back down the pair
    BOB_AT = f_in + 37                                                # the floating pair bobs while the ball is out of sight in the bar
    pieces = [(PANEL, "x", (lambda k: PANEL_SHUT), None)]

    def wave_of(depth, delay):
        return lambda k: dip(k - f_mid - delay, depth, WAVE_T) + WAVE2 * dip(k - f_mid2 - delay, depth, WAVE_T)

    for nodes, depth, delay in WAVE:
        wv = wave_of(depth, delay)
        for oid in nodes:
            y0 = rest_y(oid)
            extra = (lambda k: press(k - PRESS_AT)) if nodes is CRATE else (lambda k: 0.0)
            tapd = (lambda k: dip(k - f_tap2, TAP_GIVE, 12)) if nodes is MID else (lambda k: 0.0)
            pieces.append((oid, "y", (lambda k, y0=y0, wv=wv, extra=extra, tapd=tapd: y0 + wv(k) + extra(k) + tapd(k)), None))
    bob = lambda k: -dip(k - BOB_AT, BOB_H, BOB_T)
    for nodes, give in ((LOWER, low_dip), (UPPER, up_dip)):
        for oid in nodes:
            y0 = rest_y(oid)
            pieces.append((oid, "y", (lambda k, y0=y0, give=give: y0 + bob(k) + give(k)), None))
    for name, parent, shape in TURNS:
        x0, y0, W, H = square_in_parent(byid, shape)
        white, black = add_turn(doc, parent, x0, y0, W, H, name)
        turns = TURN_AT[name]
        e = lambda k, turns=turns, W=W: edge(turn_amount(k, turns), W)
        pieces += [(white, "scaleX", (lambda k, e=e, W=W: e(k) / W), None),
                   (black, "x", (lambda k, e=e, x0=x0: x0 + e(k)), None),
                   (black, "scaleX", (lambda k, e=e, W=W: (W - e(k)) / W), None)]

    # ---- the ambient moves never overlap each other, and never touch a piece while the ball is on it or landing on it ------------
    spans = [("wave", f_mid, f_mid + WAVE_T + 10), ("lighter wave", f_mid2, f_mid2 + WAVE_T + 10),
             ("bob", BOB_AT, BOB_AT + BOB_T), ("press", PRESS_AT, PRESS_AT + 34)]
    spans += [(f"{n} turn", a, a + TURN_T) for n, ts in TURN_AT.items() for a in ts]
    spans.sort(key=lambda s: s[1])
    for (n1, a1, b1), (n2, a2, b2) in zip(spans, spans[1:]):
        assert b1 <= a2, ("overlap", n1, n2)
    assert spans[-1][2] < L, spans[-1]
    assert BOB_AT > f_dive + 20, "the bob while the ball is on the floating pair"
    assert TURN_AT["Right Stack Square"][0] > f_low + 16 and TURN_AT["Biggest Stack Square"][0] > f_mid + MID_REST + 20
    assert TURN_AT["Biggest Stack Square"][1] > f_dive + 10 and TURN_AT["Biggest Stack Square"][1] + TURN_T < f_mid2 + 400

    # before T0 the ball sits in the bar and rides in with the bar's front (the pan, the drop and the landing squash)
    px = plane_x(scene, sheet, ROOM, "Front")
    by = intro_series(scene, sheet, ROOM, "9:8534", "y")
    bsx = intro_series(scene, sheet, ROOM, "9:8534", "scaleX")
    bsy = intro_series(scene, sheet, ROOM, "9:8534", "scaleY")
    piv = (760.094, 747.921)

    def pre(f):
        cx = piv[0] + bsx(f) * (in_bar[0] - piv[0]) + px(f)
        cy = by(f) + bsy(f) * (in_bar[1] - piv[1])
        return (cx, cy), 1.0, 1.0
    emit(doc, art, spin, cyc, th, T0, pre, pieces)
    S = lambda k: f"{(T0 + k) / 60:.2f} s"
    seam = INTRO - 1 - T0
    beats = "; ".join(f"{label} {S(f)}" for label, f in tr.notes)
    amb = ", ".join(f"{n} {S(a)}" for n, a, b in spans)
    hid = next(g for g in range(f_dive, L) if tr.modes[g] == "hidden")
    return (f"{ROOM}: hidden {(L - hid) / 60:.2f} s ({L - hid} frames, from {S(hid)}); springs out of the bar {S(0)} (up {-v_pop[1]:.1f}, across {v_pop[0]:.2f}); {beats} (dives from {S(f_dive)}), out of "
            f"sight; next run {(L - f_in) / 60:.2f} s later; skyline: {amb}; loop {L / 60:.2f} s ({L} frames); "
            f"intro-to-loop seam at cycle frame {seam} ({tr.modes[seam] if seam < len(tr.modes) else '?'}); closest pass "
            + ", ".join(f"{n} {d:.1f}" for n, d in sorted(worst.items())))
