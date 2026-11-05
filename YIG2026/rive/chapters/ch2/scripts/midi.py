"""The Midi, "building the grid" (2026-11-04): the cubes come to life with the ball.

The pieces (room space, the planes at rest): the two floating pairs are the left pair (9:6731, a black and a white square, in the Floor
Plane, below the ball) and the right pair (two white squares, 9:6507, in the Front Plane, above the ball, with their black backs 9:6763
and 9:6775 in the Floor Plane). The four-cell floor bar is Base_Back's 9:6597: four tops (9:6608, 9:6618, 9:6628, 9:6638) over its
row of fronts. The stairs (the two cubes on the left, Boxes 2's 9:6528, with the door cube's door in Boxes 1) are steps only now.

The ball lives in the right pair: its white fronts are drawn above the ball, so a ball behind them is hidden (it pops out of the pair's
top edge and comes back in through its bottom edge, and only the part past that edge shows). It rides in hidden with the pair's drop.

The loop, from the moment the pieces have landed (1.95 s):
  * the two pairs slide towards each other, above the stairs (left pair up and left, right pair up and left; they meet at y 476) and
    click together into one four-cell bar, with a 1.2 px recoil that settles;
  * the ball pops up out of the bar's top and lands on it; the bar carries it right 122 px (the ball held, not turning) to its dock at
    x 711 to 933.5; the ball rolls left along the docked bar and hops off its left end onto the upper stair cube, then down the stairs;
  * it hops onto the floor bar's first cell and rolls right across it (the surface takes the fall), slowing to a stop on the last cell;
    each cell's top turns from black to white as the ball rolls onto it, the turn's edge following the ball;
  * it hops up into the docked bar's right pair from below and is out of sight; the pairs separate back to where they started, the four
    tops turn back to black one after another, and the ball pops out again.
Ambient: the right pair's right square turns black and back, and the floor bar's second front turns white and back, at their own times.

The cube turn is Chapter 1 card 5's 2D trick: each turning square is two faces that share one edge; the edge sits at the faces' widths
in the proportion sin t : cos t as t turns a quarter (eased in and out), and ends exactly on the drawn pose. Here the faces are plain
fills, so instead of scaling each face the shared edge's two vertices are keyed: the faces stay inside the square (no mask needed) and
every line keeps its 1.5 weight.
"""
import math
import xml.etree.ElementTree as ET

from common import INTRO, BallArt, Cycle, _set_attrs, dip, emit, intro_series, plane_x, prepare_ball, smooth
import geom

ROOM = "The Midi"
T0 = 117                                    # 1.95 s: Boxes 2 (the right pair's fronts and the stairs) lands at 1.63 s, its squash is over at 1.95 s
G = 0.40
INK, PAPER = "FF1F1F1F", "FFDFDBD7"

# ---- the pieces ---------------------------------------------------------------------------------------------------------------
LEFT_PAIR = ("9:6731",)                     # the black and white squares, x 672.4 to 765.1, y 487.3 to 539.8
RIGHT_PAIR = ("9:6507", "9:6763", "9:6775") # the white fronts (x 781.5 to 886.8, y 565 to 617.5) and their black backs
L_HOME = (672.4, 487.3)                     # the left pair's left edge and top
R_HOME = (781.5, 565.0)                     # the right pair's white fronts' left edge and top
L_WIDTH = 92.7                              # the left pair's width (its black square shows 40.2, its white 52.5)
R_WHITES = 105.3                            # the right pair's two white fronts (its black back shows 24.5 more on the right)
YP = 476.0                                  # the joined bar's top: its bottom (528.5) clears the upper cube's top (533.5), so it can pass above it
LP_J = 589.0                                # the joined bar's left edge where the pairs click: above the stairs
LP_DOCK = 711.0                             # where the ride docks it: its right end (933.5) stops 1.5 px inside the phone frame (935)
DL = (LP_J - L_HOME[0], YP - L_HOME[1])     # the left pair's slide (left and a little up)
DR = (LP_J + L_WIDTH - R_HOME[0], YP - R_HOME[1])   # the right pair's slide (left and up)
RIDE = LP_DOCK - LP_J                       # 122: the ride, rightwards

# ---- the ball's surfaces (contact lines) -------------------------------------------------------------------------------------
BASE_Y = 670.0                              # on the floor bar's tops, a third of the way back
LOW_Y, UP_Y = 596.0, 544.0                  # the stairs' lower and upper cube tops (as before)
UP_X, LOW_X = 585.0, 656.0                  # where it lands on each step
XS = 884.0                                  # where it comes to rest on the floor bar's last cell
IN_REL = (48.0, 26.25)                      # the ball's centre hidden in the right pair, from its fronts' top-left corner
TOP_LIMIT = 425.0                           # the ball's top never higher (copy clearance)

# ---- timing (cycle frames from T0) ---------------------------------------------------------------------------------------------
C_CLICK = 42                                # the pairs meet
RECOIL, RECOIL_T = 1.2, 10
C_POP = 44                                  # the ball pops out (lands on the bar before the intro hands over to the loop, cycle frame 74)
C_RIDE0, RIDE_T = 80, 52
TURN_T = 16                                 # a cube turn
SEP_T = 36


def hop_to(p0, p1, vy0):
    """Velocity of an own-effort hop from p0 that rises with vy0 (negative = up) and comes down onto p1's height at p1's x."""
    dy = p1[1] - p0[1]
    T = (-vy0 + math.sqrt(vy0 * vy0 + 2 * G * dy)) / G
    return ((p1[0] - p0[0]) / T, vy0), T


class Path:
    """The ball's centre and mode on every cycle frame, appended segment by segment."""

    def __init__(self, start, mode):
        self.pts, self.modes = [start], [mode]

    @property
    def f(self):
        return len(self.pts) - 1

    @property
    def p(self):
        return self.pts[-1]

    def add(self, p, mode):
        self.pts.append(p)
        self.modes.append(mode)

    def fly(self, v, y_land):
        """A flight with velocity v from the current centre down onto centre height y_land; the landing frame is the first whole
        frame at or past it, put on the line. Returns (frame, v_in)."""
        x0, y0 = self.p
        vx, vy = v
        T = (-vy + math.sqrt(vy * vy + 2 * G * (y_land - y0))) / G
        n = math.ceil(T - 1e-9)
        for k in range(1, n + 1):
            u = min(k, T)
            self.add((x0 + vx * u, y0 + vy * u + 0.5 * G * u * u), "air")
        self.pts[-1] = (x0 + vx * T, y_land)
        return self.f, (vx, vy + G * T)

    def roll_to_stop(self, y, v0, x_stop):
        x0 = self.p[0]
        a = v0 * v0 / (2 * abs(x_stop - x0))
        t_stop = abs(v0) / a
        sgn = math.copysign(1, v0)
        for k in range(1, math.ceil(t_stop) + 1):
            u = min(k, t_stop)
            self.add((x0 + v0 * u - sgn * 0.5 * a * u * u, y), "roll")
        self.pts[-1] = (x_stop, y)

    def rest(self, n, mode="rest"):
        for _ in range(n):
            self.add(self.p, mode)


# ---- the cube turn -----------------------------------------------------------------------------------------------------------
def turn_curve(u):
    """The shared edge's place across the square (0 to 1) as the cube turns a quarter: t eased in and out, the faces at sin t : cos t."""
    t = 0.5 * math.pi * smooth(u)
    return math.sin(t) / (math.sin(t) + math.cos(t))


def schedule(s0, moves):
    """s(g): the edge's place, from s0, with moves [(start frame, s_to)], each TURN_T long."""
    def s(g):
        v = s0
        for start, to in moves:
            if g <= start:
                break
            u = min(1.0, (g - start) / TURN_T)
            v = v + (to - v) * turn_curve(u)
        return v
    return s


def inv(m):
    a, b, c, d, tx, ty = m
    det = a * d - b * c
    ia, ib, ic, id_ = d / det, -b / det, -c / det, a / det
    return (ia, ib, ic, id_, -(ia * tx + ic * ty), -(ib * tx + id_ * ty))


class Square:
    """One turning square: the drawn face (an existing path) and a new face of the other colour beside it in the same parent. The two
    share the edge at s across the square (0 = the left edge, 1 = the right): the left face is from the left edge to it, the right face
    from it to the right edge. Only the edge's two vertices move, along the square's top and bottom edges."""

    def __init__(self, doc, path_id, drawn_side, new_fill, name):
        e = geom.BYID[path_id]
        shape = geom.PARENT[e]
        self.m_old = geom.world(e)
        world = geom.outline(e)
        ids = [v.get("id") for v in e if v.tag.endswith("Vertex")]
        ys = sorted({round(p[1], 1) for p in world})
        top, bottom = ys[0], ys[-1]
        corner = {}
        for vid, p in zip(ids, world):
            row = "T" if abs(p[1] - top) < 0.5 else "B"
            others = [q for q in world if abs(q[1] - p[1]) < 0.5]
            col = "L" if p[0] <= min(q[0] for q in others) + 1e-6 else "R"
            corner[row + col] = (vid, p)
        assert set(corner) == {"TL", "TR", "BL", "BR"}, (path_id, corner)
        self.c = {k: v[1] for k, v in corner.items()}
        self.drawn_side = drawn_side
        # the new face, placed in the drawn face's parent with no transform of its own
        parent = geom.PARENT[shape]
        self.m_new = geom.world(parent)
        sid, pid = doc.new_id(), doc.new_id()
        vids = {k: doc.new_id() for k in ("TL", "TR", "BR", "BL")}
        i = doc.idx(shape.get("id"))
        j = doc.end(i)
        pad = " " * (len(doc.lines[i]) - len(doc.lines[i].lstrip()))
        loc = {k: geom.apply(inv(self.m_new), self.c[k]) for k in vids}
        body = [f'{pad}<Shape name="{name}" id="{sid}">', f'{pad}    <PointsPath isClosed="true" id="{pid}">']
        body += [f'{pad}        <StraightVertex x="{loc[k][0]:.4f}" y="{loc[k][1]:.4f}" id="{vids[k]}"/>' for k in ("TL", "TR", "BR", "BL")]
        body += [f"{pad}    </PointsPath>", f'{pad}    <Fill id="{doc.new_id()}">', f'{pad}        <SolidColor colorValue="{new_fill}" id="{doc.new_id()}"/>',
                 f"{pad}    </Fill>", f'{pad}    <Stroke thickness="1.5" cap="round" join="round" id="{doc.new_id()}">',
                 f'{pad}        <SolidColor colorValue="{INK}" id="{doc.new_id()}"/>', f"{pad}    </Stroke>", f"{pad}</Shape>"]
        doc.lines[j + 1:j + 1] = body
        # the moving vertices: the drawn face's edge on the shared side, and the new face's
        old_edge = ("TR", "BR") if drawn_side == "L" else ("TL", "BL")
        new_edge = ("TL", "BL") if drawn_side == "L" else ("TR", "BR")
        self.moving = [(corner[k][0], k[0], self.m_old) for k in old_edge] + [(vids[k], k[0], self.m_new) for k in new_edge]

    def edge(self, s, row):
        a, b = (self.c["TL"], self.c["TR"]) if row == "T" else (self.c["BL"], self.c["BR"])
        return (a[0] + s * (b[0] - a[0]), a[1] + s * (b[1] - a[1]))

    def pieces(self, s_fn):
        out = []
        for vid, row, m in self.moving:
            mi = inv(m)
            out.append((vid, "x", (lambda g, row=row, mi=mi: geom.apply(mi, self.edge(s_fn(g), row))[0]), None))
        return out

    def set_rest(self, doc, s_rest):
        for vid, row, m in self.moving:
            _set_attrs(doc, vid, {"x": geom.apply(inv(m), self.edge(s_rest, row))[0]})


# ---- the pairs -------------------------------------------------------------------------------------------------------------------
def pair_offsets(f_sep):
    """(dL(g), dR(g), ride(g)): the pairs' displacement from where they are drawn. They slide to the click, the joined bar rides right
    to its dock and stays there, then both pairs go home (the separation, from f_sep). ride(g) is the bar's ride in px, for the ball."""
    def join(g):
        return 0.0 if g <= 0 else min(1.0, g / C_CLICK) ** 0.85      # a quick start that eases off into the click

    def recoil(g):                                         # the click: they spring 1.2 px apart and settle, once
        return dip(g - C_CLICK, RECOIL, RECOIL_T)

    def ride(g):
        if g < C_RIDE0:
            return 0.0
        return RIDE * smooth((g - C_RIDE0) / RIDE_T)

    def home(g):                                           # 0 at the dock, 1 when the pairs are back
        return smooth((g - f_sep) / SEP_T) if g > f_sep else 0.0

    nl, nr = math.hypot(*DL), math.hypot(*DR)

    def dl(g):
        j, r, x, h = join(g), recoil(g), ride(g), home(g)
        return ((DL[0] * j + x) * (1 - h) - DL[0] / nl * r, (DL[1] * j) * (1 - h) - DL[1] / nl * r)

    def dr(g):
        j, r, x, h = join(g), recoil(g), ride(g), home(g)
        return ((DR[0] * j + x) * (1 - h) - DR[0] / nr * r, (DR[1] * j) * (1 - h) - DR[1] / nr * r)
    return dl, dr, ride


def build(doc, scene, sheet):
    art = BallArt(scene, ROOM)
    spin = prepare_ball(doc, art)
    for oid in ("9:6786", "9:6518", "9:6499", "9:6500", "9:6489", "9:6490"):   # the old journey: Ball_01's offsets, the right pair's
        doc.drop_object(f"{ROOM} Loop", oid)                                    # push, the base door and the stair door
    Rc, R = art.Rc, art.R
    yb = lambda contact: contact - Rc

    # ---- the ball's journey -------------------------------------------------------------------------------------------------
    r_home_in = (R_HOME[0] + IN_REL[0], R_HOME[1] + IN_REL[1])
    # a provisional pair motion, to place the ball while it is hidden; the catch and the separation are worked out below
    beats = {}
    pa = Path(r_home_in, "hidden")
    dl0, dr0, ride = pair_offsets(10 ** 6)
    for g in range(1, C_POP + 1):
        d = dr0(g)
        pa.add((r_home_in[0] + d[0], r_home_in[1] + d[1]), "hidden")
    # out of the bar's top: a pop up and a little left, onto the left pair's white
    f, vin = pa.fly((-2.5, -6.5), yb(YP))
    beats["lands on the bar"] = f
    land_bar = pa.p
    sq = [(f, 0.05)]
    assert f + 3 < INTRO - 1 - T0, (f, "the ball must be resting when the intro hands over to the loop")
    f_bar = f
    while pa.f < C_RIDE0 + RIDE_T + 6:                     # the bar carries it, the ball held (no turn)
        g = pa.f + 1
        pa.add((land_bar[0] + ride(g), land_bar[1] + dip(g - f_bar, 1.5, 16)), "ride")
    beats["bar docks"] = C_RIDE0 + RIDE_T
    # then it rolls left along the docked bar, to near its left end (from rest: the speed builds and eases off), and hops off
    x0, y0 = pa.p
    x_end, N_ROLL = LP_DOCK + 31.0, 20
    for k in range(1, N_ROLL + 1):
        pa.add((x0 + (x_end - x0) * smooth(k / N_ROLL), y0), "roll")
    pa.rest(6)
    beats["hops off the bar"] = pa.f
    f_hop = pa.f
    v, _ = hop_to(pa.p, (UP_X, yb(UP_Y)), -2.4)
    hop_v = {pa.f: v}
    f, vin = pa.fly(v, yb(UP_Y))
    beats["lands on the upper cube"] = f
    sq.append((f, 0.10))
    pa.rest(12)
    v, _ = hop_to(pa.p, (LOW_X, yb(LOW_Y)), -4.6)
    hop_v[pa.f] = v
    f, vin = pa.fly(v, yb(LOW_Y))
    beats["lands on the lower cube"] = f
    sq.append((f, 0.07))
    pa.rest(8)
    v = (4.3, -0.5)
    hop_v[pa.f] = v
    f, vin = pa.fly(v, yb(BASE_Y))
    beats["lands on the floor bar"] = f
    sq.append((f, 0.06))
    f_floor = f
    pa.roll_to_stop(yb(BASE_Y), vin[0], XS)
    beats["stops on the last cell"] = pa.f
    pa.rest(6)
    # up into the right pair (joined, at its dock): apex inside its fronts, N_UP frames later
    N_UP = 27
    wl_j = LP_DOCK + L_WIDTH
    apex = (wl_j + 52.0, yb(BASE_Y) - 0.5 * G * N_UP * N_UP)
    vx = (apex[0] - pa.p[0]) / N_UP
    hop_v[pa.f] = (vx, -G * N_UP)
    x0, y0 = pa.p
    for k in range(1, N_UP + 1):
        pa.add((x0 + vx * k, y0 - G * N_UP * k + 0.5 * G * k * k), "air")
    f_catch = pa.f
    beats["out of sight in the right pair"] = f_catch
    f_sep = f_catch + 8
    resets = [f_catch + d for d in (8, 17, 28, 36)]        # the tops turn back, one after another, at uneven gaps
    L = max(f_sep + SEP_T, resets[-1] + TURN_T) + 8
    dl, dr, ride = pair_offsets(f_sep)
    assert all(abs(dr(g)[k] - dr0(g)[k]) < 1e-9 for g in range(f_catch) for k in (0, 1))
    # hidden: rides with the right pair, and moves within it (out of sight) from where it was caught to where it pops from
    rel_catch = (apex[0] - (R_HOME[0] + dr(f_catch)[0]), apex[1] - (R_HOME[1] + dr(f_catch)[1]))
    h0, h1 = f_sep + SEP_T, L - 6
    for g in range(f_catch + 1, L + 1):
        k = smooth((g - h0) / (h1 - h0))
        rel = (rel_catch[0] + (IN_REL[0] - rel_catch[0]) * k, rel_catch[1] + (IN_REL[1] - rel_catch[1]) * k)
        d = dr(g)
        pa.add((R_HOME[0] + d[0] + rel[0], R_HOME[1] + d[1] + rel[1]), "hidden")
    assert pa.f == L and math.dist(pa.pts[L], pa.pts[0]) < 1e-6

    # ---- checks: out of sight while hidden, clear of the copy, inside the phone frame ------------------------------------------
    for g in range(L + 1):
        x, y = pa.pts[g]
        d = dr(g)
        wl, wt = R_HOME[0] + d[0], R_HOME[1] + d[1]
        inside = wl + R - 0.01 <= x <= wl + R_WHITES - R + 0.01 and wt + R - 0.01 <= y <= wt + 52.5 - R + 0.01
        if pa.modes[g] == "hidden":
            assert inside, (g, x, y, "hidden but not covered by the right pair")
        if pa.modes[g] == "air" and y + R > wt + 1.5 and (g <= C_POP + 12 or g >= f_catch - 12):
            # in or out of the pair: any part still below its top edge (or past its bottom edge) must be behind its fronts
            if y - R < wt + 52.5:
                assert wl - 0.01 <= x - R and x + R <= wl + R_WHITES + 0.01, (g, x, y, "the ball shows beside the pair as it passes")
        assert y - R >= TOP_LIMIT, (g, y - R)
        if pa.modes[g] != "hidden":
            assert 560 <= x - R and x + R <= 935, (g, x)
    # the docked bar clears the ball as it hops off and goes down the stairs
    assert LP_DOCK - (UP_X + R) > 100
    for g in range(f_hop + 1, beats["lands on the floor bar"]):
        x, y = pa.pts[g]
        lp, top = L_HOME[0] + dl(g)[0], L_HOME[1] + dl(g)[1]      # (the left pair's corner: the bar's)
        qx, qy = min(max(x, lp), lp + L_WIDTH + R_WHITES + 24.5), min(max(y, top), top + 52.5)
        assert math.hypot(x - qx, y - qy) > R + 1, (g, x, y, lp, "the bar is in the ball's way")

    cyc = Cycle(L)
    for g in range(L + 1):
        cyc.put(g, pa.pts[g], pa.modes[g])
    for fr, a in sq:
        cyc.squash(fr, a, T=12)

    # ---- the turn: rolling turns with the distance; a hop from rest takes a little from the push and keeps it; held or still: none
    hop_v[C_POP] = (-2.5, -6.5)
    th = [0.0]
    w = 0.0
    for g in range(L):
        nxt = pa.modes[g + 1]
        if g in hop_v:
            w = 0.25 * hop_v[g][0] / R
        if nxt == "roll":
            w = (pa.pts[g + 1][0] - pa.pts[g][0]) / R
        elif nxt != "air":
            w = 0.0
        th.append(th[-1] + w)
    total = th[-1]
    want = round(total / (2 * math.pi)) * 2 * math.pi
    for g in range(f_catch + 1, L + 1):
        th[g] += (want - total) * smooth((g - f_catch - 1) / max(1, h1 - f_catch - 1))

    # ---- the squares ------------------------------------------------------------------------------------------------------------
    pieces = []
    # the pairs' slide, click, ride and separation
    base = ET.parse(str(scene.path)).getroot()
    byid = {e.get("id"): e for e in base.iter() if e.get("id")}
    for ids, fn in ((LEFT_PAIR, dl), (RIGHT_PAIR, dr)):
        for oid in ids:
            x0, y0 = float(byid[oid].get("x", 0)), float(byid[oid].get("y", 0))
            pieces.append((oid, "x", (lambda g, x0=x0, fn=fn: x0 + fn(g)[0]), None))
            pieces.append((oid, "y", (lambda g, y0=y0, fn=fn: y0 + fn(g)[1]), None))
    # the floor bar's tops: black at rest; each turns white as the ball rolls onto it (the edge going its way), and back while it is
    # out of sight. s is the white's share, from the left.
    tops = [("9:6609", "L", INK), ("9:6619", "L", INK), ("9:6629", "L", INK), ("9:6639", "R", PAPER)]
    cell_left = [725.8 - 28.0 * (BASE_Y - 658.9) / 36.8 + 52.5 * i for i in range(4)]   # the cells' left edges on the contact line
    fills = []
    for i, (pid, side, fill) in enumerate(tops):
        sqr = Square(doc, pid, side, fill, f"{ROOM} Top {i + 1} {'Black' if fill == INK else 'White'}")
        on = next(g for g in range(f_floor, L) if pa.pts[g][0] >= cell_left[i] + (0 if i == 0 else 6))
        fills.append(on)
        s = schedule(0.0, [(on, 1.0), (resets[i], 0.0)])
        sqr.set_rest(doc, 0.0)
        pieces += sqr.pieces(s)
    # ambient: the right pair's right square turns black and back; the floor bar's second front turns white and back. The right
    # square: s is the white's share from the left (it squeezes left, the black grows in from the right). The front: the black's share.
    amb = {"right square": (C_RIDE0 + 18, beats["lands on the lower cube"] + 4), "second front": (beats["lands on the upper cube"] - 6, fills[3] + 24)}
    sqr = Square(doc, "9:6509", "L", INK, f"{ROOM} Pair Square Black")
    s = schedule(1.0, [(amb["right square"][0], 0.0), (amb["right square"][1], 1.0)])
    sqr.set_rest(doc, 1.0)
    pieces += sqr.pieces(s)
    sqr = Square(doc, "9:6681", "L", PAPER, f"{ROOM} Front 2 White")
    s = schedule(1.0, [(amb["second front"][0], 0.0), (amb["second front"][1], 1.0)])
    sqr.set_rest(doc, 1.0)
    pieces += sqr.pieces(s)
    turns = sorted([(g, "fill") for g in fills] + [(g, "reset") for g in resets] + [(g, k) for k, v in amb.items() for g in v])
    for (a, ka), (b, kb) in zip(turns, turns[1:]):
        assert b - a >= 6, (a, ka, b, kb, "two turns start together")
    assert turns[-1][0] + TURN_T <= L

    # before T0 the ball sits in the right pair and rides in with its drop (the pan, Boxes 2's fall and its landing squash)
    px = plane_x(scene, sheet, ROOM, "Front")
    by = intro_series(scene, sheet, ROOM, "9:6594", "y")
    bsx = intro_series(scene, sheet, ROOM, "9:6594", "scaleX")
    bsy = intro_series(scene, sheet, ROOM, "9:6594", "scaleY")
    piv = (723.008, 775.94)

    def pre(f):
        cx = piv[0] + bsx(f) * (r_home_in[0] - piv[0]) + px(f)
        cy = by(f) + bsy(f) * (r_home_in[1] - piv[1])
        return (cx, cy), 1.0, 1.0
    emit(doc, art, spin, cyc, th, T0, pre, pieces)
    sec = lambda g: f"{(T0 + g) / 60:.2f} s"
    told = "; ".join(f"{k} {sec(v)}" for k, v in beats.items())
    return (f"{ROOM}: the pairs slide together from {sec(0)} and click at {sec(C_CLICK)}; the ball pops out at {sec(C_POP)}; {told}; "
            f"the bar rides {sec(C_RIDE0)} to {sec(C_RIDE0 + RIDE_T)} and hops off at {sec(f_hop)}; tops turn white at "
            f"{', '.join(sec(g) for g in fills)}, back at {', '.join(sec(g) for g in resets)}; the pairs part at {sec(f_sep)}; "
            f"ambient turns: " + "; ".join(f"{k} {sec(a)} and {sec(b)}" for k, (a, b) in amb.items()) +
            f"; loop {L / 60:.2f} s ({L} frames)")
