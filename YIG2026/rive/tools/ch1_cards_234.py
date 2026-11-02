"""One time (2026-11-02, history like loading_start.py): new ball loops for Chapter 1 cards 2, 3 and 4 (finesse round).

    python3 tools/ch1_cards_234.py --cards 2            dry run: prints each beat and the clearances, writes nothing
    python3 tools/ch1_cards_234.py --cards 2 --write    rewrite chapters/ch1/scene.rml

Shared by the three rooms: the ball arrives with its room, already at its home spot (no roll-in, no pop), the loop starts the moment
the intro ends, the ball has weight (steady gravity in every flight, a squash on every landing), and the pieces it touches react a
little and settle (a dip with a spring back, a rock, a wobble), each one turning about its own pivot. A reaction starts on the frame
of the contact and the ball rides the piece while it moves. The ball's position is written one key per frame, like the other
rooms' baked arcs. The old roll-in (x -80 at 2.30 to 3.05 s, then the 0.15 s pop) is gone from the intros.

Times in the notes are Finesse-panel timecodes: the loop's time plus 3.2 s (the intro).
"""
import math
import sys

from ball_motion import G, arc, fall_height, gravity, pulse, rot, roll_distance, smooth, ease_in, spring
from rml_edit import Doc, bake
from rml_read import Scene, chapter_dir

SCENE = chapter_dir("ch1") / "scene.rml"
INTRO = 192
BALL_CENTER = 16.66          # the ball's centre is this far above its node (the contact point) at full size
R = 17.0                     # centre to the edge of what it rests on
COPY_BOTTOM = 251.0          # lowest line of the card's copy on the 375 x 812 phone frame (measured in the harness, worst card)


def phone_y(y):
    """Artboard y on the phone frame: scale 0.9893 (artboard 1479 px wide for 1495 units), top at -2.45."""
    return 0.9893 * y - 2.45


def plane_x(room):
    """The room's Floor Plane x on every Intro frame (1600 sliding to 0): the ball is not inside the planes, so it rides this."""
    from rooms_sheet import Sheet
    sc = Scene(SCENE)
    sh = Sheet(sc)
    oid = next(e.get("id") for e in sc.root.iter("Node") if e.get("name") == f"{room} Floor Plane")
    k = sh.anim_keys(sc.animations[f"{room} Intro"])[oid]["x"]
    return lambda f: k.at(f)


def series(f0, f1, fn):
    return {f: fn(f) for f in range(f0, f1)}


class Ball:
    """The ball's centre, size and the frame each beat happens, built up from one segment after another."""

    def __init__(self, n):
        self.n = n
        self.c = {}
        self.sx = {f: 1.0 for f in range(n)}
        self.sy = {f: 1.0 for f in range(n)}
        self.notes = []

    def put(self, f, c):
        self.c[f] = c

    def seg(self, f0, f1, pts):
        for i, p in enumerate(pts):
            self.c[f0 + i] = p
        assert len(pts) == f1 - f0 + 1, (f0, f1, len(pts))

    def squash(self, f, a):
        for k in range(0, 30):
            if f + k < self.n:
                p = pulse(k)
                self.sy[f + k] = 1 - a * p
                self.sx[f + k] = 1 + 0.7 * a * p

    def node(self):
        """x and y of the ball node (the contact point) on every frame."""
        xs = {f: self.c[f][0] for f in self.c}
        ys = {f: self.c[f][1] + BALL_CENTER for f in self.c}
        return xs, ys


def card2(doc, write):
    room = "Chapter 1 Card 2"
    N = 450
    # ---- the art (measured from the file, see the notes in the module header) -----------------------------------------
    T = (856.1, 711.4)                              # the pencil's tip, on the floor: it turns about this
    E = (821.5, 475.7)                              # the top of the pencil's eraser
    UPRIGHT = math.atan2(T[0] - E[0], T[1] - E[1])  # how far it leans: standing up is this much clockwise
    bar_c, bar_d = (728.27, 517.52), (math.cos(0.22066198), math.sin(0.22066198))
    bar_n = (bar_d[1], -bar_d[0])
    BAR_UP = 7.59 + 16.855 + 0.0                    # half the bar plus the ball's radius
    bar_pivot = (781.5, 538.0)                      # the bar rests on the middle white joint
    j_mid, j_low = (782.02, 555.32), (667.10, 620.37)
    st_a, st_b = (781.7, 555.3), (666.8, 620.4)
    st_len = math.dist(st_a, st_b)
    st_d = ((st_b[0] - st_a[0]) / st_len, (st_b[1] - st_a[1]) / st_len)
    st_n = (st_d[1], -st_d[0])                      # pointing up
    ST_UP = 7.25 + 16.855
    total_pivot = (681.0, 711.8)
    dom_pivot = (697.0, 572.5)

    def bar_pt(p, th):
        c = (bar_c[0] + p * bar_d[0] + BAR_UP * bar_n[0], bar_c[1] + p * bar_d[1] + BAR_UP * bar_n[1])
        return rot(c, bar_pivot, th)

    def stick_pt(q, th):
        c = (st_a[0] + q * st_d[0] + ST_UP * st_n[0], st_a[1] + q * st_d[1] + ST_UP * st_n[1])
        return rot(c, j_mid, th)

    # ---- when things happen (loop frames, 60 per second; the Finesse timecode is the frame / 60 + 3.2 s) -----------------
    SWAY_END, LEAN_END, FLICK_END = 72, 84, 90
    F_BAR, F_ROLL_END = 114, 168
    F_JOINT, F_LEAVE_JOINT, F_STICK = 178, 180, 206
    F_STICK_END, F_TOTAL, F_SPRING, F_HOME = 254, 276, 286, 354
    P_BAR0, P_BAR1 = 0.4, 40.0
    Q0, Q1 = 45.0, 94.0
    joint_shoulder = (j_mid[0] + 34.2 * math.cos(math.radians(-115)), j_mid[1] + 34.2 * math.sin(math.radians(-115)))
    total_land = (654.4, 661.2)

    # ---- the pieces' reactions --------------------------------------------------------------------------------------------
    A_SWAY, A_LEAN = 0.014, 0.05

    def pencil(f):
        if f < SWAY_END:
            return A_SWAY * (1 - math.cos(2 * math.pi * f / 36)) / 2
        if f < LEAN_END:
            return A_LEAN * smooth((f - SWAY_END) / (LEAN_END - SWAY_END))
        if f < FLICK_END:
            return A_LEAN * (1 - ease_in((f - LEAN_END) / (FLICK_END - LEAN_END)))     # snaps forward onto the bar
        if f < F_HOME:
            u = f - FLICK_END
            return 0.009 * math.sin(math.pi * u / 8) if u < 8 else 0.0                   # a small rebound off the bar
        return spring(f - F_HOME, 0.035, down=5, tau=10.0, period=24.0)

    bar = lambda f: spring(f - F_BAR, -0.03, down=4, tau=10.0, period=22.0)
    stick = lambda f: spring(f - F_STICK, -0.035, down=4, tau=9.0, period=20.0)
    joint_p = lambda f: pulse(f - F_JOINT, down=3, tau=7.0, period=16.0)
    total_dip = lambda f: spring(f - F_TOTAL, 0.07, down=5, tau=12.0, period=24.0)       # how much the card is pressed
    domino = lambda f: 0.05 * math.exp(-(f - F_BAR) / 14.0) * math.sin(2 * math.pi * (f - F_BAR) / 22.0) if f > F_BAR else 0.0

    def pencil_center(f_theta):
        th = f_theta
        Er = rot(E, T, th)
        nx, ny = math.sin(th), -math.cos(th)
        u = 60.0 * th                                  # the ball rolls a touch downhill to stay balanced
        return (Er[0] + nx * R + math.cos(th) * u, Er[1] + ny * R + math.sin(th) * u)

    # ---- the ball, loop ---------------------------------------------------------------------------------------------------
    b = Ball(N)
    for f in range(0, FLICK_END + 1):
        b.put(f, pencil_center(pencil(f)))
    n1 = F_BAR - FLICK_END
    b.seg(FLICK_END, F_BAR, arc(b.c[FLICK_END], bar_pt(P_BAR0, 0.0), n1, 14))
    s_roll, a_roll = roll_distance(F_ROLL_END - F_BAR, 0.0, P_BAR1 - P_BAR0)
    for i, s in enumerate(s_roll):
        f = F_BAR + i
        b.put(f, bar_pt(P_BAR0 + s, bar(f)))
    b.seg(F_ROLL_END, F_JOINT, arc(b.c[F_ROLL_END], joint_shoulder, F_JOINT - F_ROLL_END, fall_height(F_JOINT - F_ROLL_END) + 1))
    for f in range(F_JOINT, F_LEAVE_JOINT):
        b.put(f, joint_shoulder)
    b.seg(F_LEAVE_JOINT, F_STICK, arc(joint_shoulder, stick_pt(Q0, 0.0), F_STICK - F_LEAVE_JOINT, 16))
    s_roll2, a_roll2 = roll_distance(F_STICK_END - F_STICK, 0.3, Q1 - Q0)
    for i, s in enumerate(s_roll2):
        f = F_STICK + i
        b.put(f, stick_pt(Q0 + s, stick(f)))
    b.seg(F_STICK_END, F_TOTAL, arc(b.c[F_STICK_END], total_land, F_TOTAL - F_STICK_END, fall_height(F_TOTAL - F_STICK_END)))

    def on_total(f):
        k = 1 - total_dip(f)
        return (total_land[0], total_pivot[1] + (total_land[1] - total_pivot[1]) * k)
    for f in range(F_TOTAL, F_SPRING + 1):
        b.put(f, on_total(f))
    home = pencil_center(pencil(F_HOME))
    b.seg(F_SPRING, F_HOME, arc(b.c[F_SPRING], home, F_HOME - F_SPRING, 140))
    for f in range(F_HOME, N):
        b.put(f, pencil_center(pencil(f)))
    for f, a in ((F_BAR, 0.10), (F_JOINT, 0.12), (F_STICK, 0.10), (F_TOTAL, 0.16), (F_HOME, 0.16)):
        b.squash(f, a)
    xs, ys = b.node()

    # ---- numbers to check ----------------------------------------------------------------------------------------------------
    top = min(c[1] for c in b.c.values()) - 17.6
    print(f"{room}: loop {N} frames ({N / 60:.2f} s)")
    for name, f in (("leans back", SWAY_END), ("flicks, ball leaves the eraser", FLICK_END), ("lands on the purple bar", F_BAR),
                    ("steps off the bar onto the middle white joint", F_JOINT), ("lands on the yellow stick", F_STICK),
                    ("leaves the stick's low end", F_STICK_END), ("lands on TOTAL's left edge", F_TOTAL),
                    ("TOTAL springs it away", F_SPRING), ("lands back on the eraser", F_HOME)):
        print(f"  frame {f:3d}  loop {f / 60:5.2f} s  timecode {f / 60 + 3.2:5.2f} s  {name}")
    print(f"  highest point of the ball: y {top:.1f} ({phone_y(top):.0f} px on the phone frame); copy ends at {COPY_BOTTOM:.0f}: clearance {phone_y(top) - COPY_BOTTOM:.0f} px")
    print(f"  gravity per flight (px/frame^2, plain fall {G}): eraser to bar {gravity(F_BAR - FLICK_END, 14):.2f}, bounce {gravity(F_STICK - F_LEAVE_JOINT, 16):.2f}, spring {gravity(F_HOME - F_SPRING, 140):.2f}")
    print(f"  x range {min(c[0] for c in b.c.values()) - 17.6:.0f} to {max(c[0] for c in b.c.values()) + 17.6:.0f}")
    if not write:
        return

    # ---- write -----------------------------------------------------------------------------------------------------------------
    ids = dict(ball="9:8040", scale="9:8042", pencil="9:7760", bar="9:7865", domino="9:7872", total="9:7959", stick="9:7655", joint="9:7643",
               frontcircle="9:7748")
    old = ["9:7659", "9:7748", "9:8049", "9:8043", "9:8054", "9:8052", "9:8051"]       # the ball's vertex/highlight keys and the front circle
    loop, intro = f"{room} Loop", f"{room} Intro"
    piv = {}
    piv["pencil"], _ = doc.wrap(ids["pencil"], f"{room} Pencil", *T)
    piv["bar"], _ = doc.wrap(ids["bar"], f"{room} Bar", *bar_pivot)
    piv["domino"], _ = doc.wrap(ids["domino"], f"{room} Domino", *dom_pivot)
    piv["total"], _ = doc.wrap(ids["total"], f"{room} Total", *total_pivot)
    piv["stick"], _ = doc.wrap(ids["stick"], f"{room} Yellow Stick", j_mid[0] - 649.0, j_mid[1] - 463.5)      # inside a node at (649, 463.5)
    for oid in old:
        doc.drop_object(loop, oid)
        doc.drop_object(intro, oid)
    doc.set_duration(loop, N)

    # intro: the pencil stands up, the ball on its eraser, and tips over onto the bar at 2.5 to 2.9 s
    TIP0, HIT = 148, 168

    def p_intro(f):
        if f < TIP0:
            return UPRIGHT
        if f < HIT:
            return UPRIGHT * (1 - ease_in((f - TIP0) / (HIT - TIP0)) ** 1)
        u = f - HIT
        if u < 10:
            return 0.02 * math.sin(math.pi * u / 10)
        if u < 18:
            return 0.005 * math.sin(math.pi * (u - 10) / 8)
        return 0.0
    ib = Ball(INTRO)
    for f in range(INTRO):
        ib.put(f, pencil_center(p_intro(f)))
    ib.squash(HIT, 0.08)
    ixs, iys = ib.node()
    px = plane_x(room)
    ixs = {f: x + px(f) for f, x in ixs.items()}                 # carried in by the pan
    fr_i, fr_l = range(INTRO), range(N)
    doc.set_prop(intro, ids["ball"], "x", bake(ixs, fr_i))
    doc.set_prop(intro, ids["ball"], "y", bake(iys, fr_i))
    doc.set_prop(loop, ids["ball"], "x", bake(xs, fr_l))
    doc.set_prop(loop, ids["ball"], "y", bake(ys, fr_l))
    for prop, ser_i, ser_l in (("scaleX", ib.sx, b.sx), ("scaleY", ib.sy, b.sy)):
        doc.set_prop(intro, ids["scale"], prop, bake(ser_i, fr_i))
        doc.set_prop(loop, ids["scale"], prop, bake(ser_l, fr_l))
    doc.set_prop(intro, ids["frontcircle"], "opacity", [(0, 0.0, "hold")])

    def both(oid, prop, fn, rest, intro_fn=None):
        doc.set_prop(loop, oid, prop, bake(series(0, N, fn), fr_l))
        if intro_fn is None:
            doc.set_prop(intro, oid, prop, [(0, rest, "hold"), (INTRO - 1, rest, "hold")])
        else:
            doc.set_prop(intro, oid, prop, bake(series(0, INTRO, intro_fn), fr_i))
    both(piv["pencil"], "rotation", pencil, 0.0, p_intro)
    both(piv["bar"], "rotation", bar, 0.0)
    both(piv["domino"], "rotation", domino, 0.0)
    both(piv["stick"], "rotation", stick, 0.0)
    both(ids["joint"], "scaleY", lambda f: 1 - 0.14 * joint_p(f), 1.0)
    both(ids["joint"], "scaleX", lambda f: 1 + 0.10 * joint_p(f), 1.0)
    both(piv["total"], "scaleY", lambda f: 1 - total_dip(f), 1.0)
    both(piv["total"], "scaleX", lambda f: 1 + 0.5 * total_dip(f), 1.0)
    doc.rebuild_waiting(room)


def segdist(p, a, b):
    """Distance from point p to the segment a-b."""
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy)))
    return math.dist(p, (ax + t * dx, ay + t * dy))


def round_ball(doc, intro, ids):
    """Hold the ball's shape round for the whole room (the old rooms drew it squashed at rest): key the Intro, drop it from the Loop."""
    loop = intro.replace("Intro", "Loop")
    hold = lambda oid, prop, v: doc.set_prop(intro, oid, prop, [(0, v, "hold"), (INTRO - 1, v, "hold")])
    hl, top, right, left = ids
    hold(hl, "x", 6.364); hold(hl, "y", -23.834); hold(hl, "scaleX", 1.0); hold(hl, "scaleY", 1.0)
    hold(top, "y", -17.678); hold(top, "inDistance", 9.7633); hold(top, "outDistance", 9.7633)
    hold(right, "x", 17.678); hold(right, "y", 0.0)
    hold(left, "x", -17.678); hold(left, "y", 0.0)
    for oid in ids:
        doc.drop_object(loop, oid)


def card3(doc, write):
    global BALL_CENTER
    room = "Chapter 1 Card 3"
    N = 432
    BALL_CENTER = 16.78
    Rb = 17.1
    mug_in = (722.0, 722.0)                 # hidden inside the mug (its front rim is at y 698)
    mug_hide = (737.0, 724.0)
    band_x = 827.0                          # between the two posts (they are at x 792 and 862, radius 14.9)
    band_top = 490.0 - 6.4 + 0.4            # the band's low point is y 490.0 and it is 12.75 thick
    book_land = (645.0, 473.9 - Rb)         # the leaning books' top edge
    shelf_land = (585.0, 509.6 - Rb)        # the left end of the shelf plank
    tip = (594.5, 591.0)
    shoulder = (tip[0] - 32.4 * math.sin(math.radians(22)), tip[1] - 32.4 * math.cos(math.radians(22)))
    low_joint = (671.0, 676.0)
    st_len = math.dist(tip, low_joint)
    st_d = ((low_joint[0] - tip[0]) / st_len, (low_joint[1] - tip[1]) / st_len)
    st_n = (st_d[1], -st_d[0])
    ST_UP = 22.6
    card_tap = (858.0, 538.6 - Rb)
    card_edge = [(830.2, 538.6), (820.1, 544.4), (761.6, 644.0), (767.9, 654.9)]
    books_pivot, stick_pivot, card_pivot, mug_pivot = (650.0, 508.0), low_joint, (795.0, 654.9), (737.0, 745.0)

    def stick_pt(q, th):
        c = (tip[0] + q * st_d[0] + ST_UP * st_n[0], tip[1] + q * st_d[1] + ST_UP * st_n[1])
        return rot(c, stick_pivot, th)

    F_POP, F_BAND, F_UP, F_BOOK, F_BOOK_UP = 34, 104, 114, 164, 172
    F_SHELF, F_EDGE, F_TIP, F_TIP_UP, F_STK, F_STK_END = 206, 214, 240, 246, 262, 306
    F_CARD, F_CARD_UP, F_IN = 354, 356, 406
    Q0, Q1 = 32.0, 104.0

    band = lambda f: spring(f - F_BAND, 9.0, down=5, tau=11.0, period=24.0)          # px the band's middle sags
    books = lambda f: spring(f - F_BOOK, 0.07, down=3, tau=9.0, period=20.0)
    stick = lambda f: spring(f - F_TIP, -0.045, down=4, tau=9.0, period=20.0)
    card = lambda f: spring(f - F_CARD, 0.035, down=3, tau=9.0, period=20.0)
    mug = lambda f: spring(f - F_POP, 0.05, down=3, tau=10.0, period=20.0) + spring(f - F_IN, -0.07, down=3, tau=5.0, period=13.0)

    b = Ball(N)
    for f in range(0, F_POP + 1):
        b.put(f, mug_hide)
    c_band = (band_x, band_top - Rb)
    b.seg(F_POP, F_BAND, arc(mug_hide, c_band, F_BAND - F_POP, 165, 1.8))
    for f in range(F_BAND, F_UP + 1):
        b.put(f, (c_band[0], c_band[1] + 0.85 * band(f)))
    b.seg(F_UP, F_BOOK, arc(b.c[F_UP], book_land, F_BOOK - F_UP, 48))
    for f in range(F_BOOK, F_BOOK_UP + 1):
        b.put(f, rot(book_land, books_pivot, books(f)))
    b.seg(F_BOOK_UP, F_SHELF, arc(b.c[F_BOOK_UP], shelf_land, F_SHELF - F_BOOK_UP, 40))
    for f in range(F_SHELF, F_EDGE + 1):
        t = (f - F_SHELF) / (F_EDGE - F_SHELF)
        b.put(f, (shelf_land[0] - 6.0 * t, shelf_land[1] + 2.0 * t * t))
    b.seg(F_EDGE, F_TIP, arc(b.c[F_EDGE], shoulder, F_TIP - F_EDGE, fall_height(F_TIP - F_EDGE)))
    for f in range(F_TIP, F_TIP_UP + 1):
        b.put(f, rot(shoulder, stick_pivot, stick(f)))
    b.seg(F_TIP_UP, F_STK, arc(b.c[F_TIP_UP], stick_pt(Q0, 0.0), F_STK - F_TIP_UP, 12))
    s_roll, _ = roll_distance(F_STK_END - F_STK, 0.5, Q1 - Q0)
    for i, s in enumerate(s_roll):
        b.put(F_STK + i, stick_pt(Q0 + s, 0.0))
    b.seg(F_STK_END, F_CARD, arc(b.c[F_STK_END], card_tap, F_CARD - F_STK_END, 70))
    for f in range(F_CARD, F_CARD_UP + 1):
        b.put(f, card_tap)
    b.seg(F_CARD_UP, F_IN, arc(card_tap, mug_in, F_IN - F_CARD_UP, 69, 0.55))
    for f in range(F_IN, N):
        b.put(f, mug_in)
    b.seg(N - 1, N - 1, [mug_hide]) if False else None
    # the last frames settle to the hidden spot the loop starts on
    for f in range(F_IN + 6, N):
        t = smooth((f - (F_IN + 6)) / (N - 1 - (F_IN + 6)))
        b.put(f, (mug_in[0] + (mug_hide[0] - mug_in[0]) * t, mug_in[1] + (mug_hide[1] - mug_in[1]) * t))
    for f, a in ((F_BAND, 0.10), (F_BOOK, 0.10), (F_SHELF, 0.10), (F_TIP, 0.10), (F_STK, 0.10), (F_CARD, 0.06)):
        b.squash(f, a)
    xs, ys = b.node()

    top = min(c[1] for c in b.c.values()) - 17.6
    flight1 = [b.c[f] for f in range(F_POP, F_BAND + 1)]
    flight6 = [b.c[f] for f in range(F_CARD_UP, F_IN + 1)]
    flight5 = [b.c[f] for f in range(F_STK_END, F_CARD + 1)]
    edge_d = lambda pts: min(min(segdist(p, card_edge[i], card_edge[i + 1]) for i in range(3)) for p in pts)
    print(f"{room}: loop {N} frames ({N / 60:.2f} s)")
    for name, f in (("ball hops out of the mug", F_POP), ("lands on the yellow band", F_BAND), ("springs off the band", F_UP),
                    ("lands on the leaning books", F_BOOK), ("leaves the books", F_BOOK_UP), ("lands on the shelf's left end", F_SHELF),
                    ("rolls off the shelf's left end", F_EDGE), ("lands on the blue stick's white tip", F_TIP), ("leaves the tip", F_TIP_UP),
                    ("lands on the blue stick", F_STK), ("leaves the stick's low end", F_STK_END), ("taps the FIRST card", F_CARD),
                    ("drops into the mug", F_IN)):
        print(f"  frame {f:3d}  loop {f / 60:5.2f} s  timecode {f / 60 + 3.2:5.2f} s  {name}")
    print(f"  highest point of the ball: y {top:.1f} ({phone_y(top):.0f} px on the phone frame); copy ends at {COPY_BOTTOM:.0f}: clearance {phone_y(top) - COPY_BOTTOM:.0f} px")
    print(f"  closest the ball's centre gets to the FIRST card's left edge: mug to band {edge_d(flight1):.1f}, stick to card {edge_d(flight5):.1f}, card to mug {edge_d(flight6):.1f} (ball radius 17)")
    posts = [(792.0, 486.0), (862.1, 486.0)]
    pd = lambda pts: min(math.dist(p, q) for p in pts for q in posts)
    print(f"  closest to a white post's centre (post radius 14.9 + ball 17 = 32): mug to band {pd(flight1):.1f}; band to books {pd([b.c[f] for f in range(F_UP, F_BOOK + 1)]):.1f}")
    print(f"  gravity: mug to band {gravity(F_BAND - F_POP, 165):.2f}, band to books {gravity(F_BOOK - F_UP, 48):.2f}, books to shelf {gravity(F_SHELF - F_BOOK_UP, 40):.2f}, stick to card {gravity(F_CARD - F_STK_END, 70):.2f}, card to mug {gravity(F_IN - F_CARD_UP, 69):.2f}")
    print(f"  x range {min(c[0] for c in b.c.values()) - 17.6:.0f} to {max(c[0] for c in b.c.values()) + 17.6:.0f}")
    if not write:
        return

    ids = dict(ball="9:9619", scale="9:9621", total_hl="9:9622")
    loop, intro = f"{room} Loop", f"{room} Intro"
    piv = {}
    piv["mug"], _ = doc.wrap_run("9:9482", "9:9522", f"{room} Mug", (mug_pivot[0] - 679.0) / 0.85, (mug_pivot[1] - 676.0) / 0.85)      # inside a node at (679, 676) scaled 0.85
    piv["books"], _ = doc.wrap("9:9432", f"{room} Leaning Books", (books_pivot[0] - 581.0) / 0.85, (books_pivot[1] - 460.0) / 0.85)      # inside a node at (581, 460) scaled 0.85
    piv["stick"], _ = doc.wrap("9:9239", f"{room} Blue Stick", *stick_pivot)
    piv["card"], _ = doc.wrap("9:9272", f"{room} First Card Wobble", *card_pivot)
    # the ball hides in the mug behind a clip: everything above the mug's front rim
    clip_id = doc.new_id()
    floor_clip = doc.idx("9:10551")
    doc.lines[floor_clip:floor_clip] = [f'                <Shape y="697" name="{room} Mug Clip" id="{clip_id}">',
                                        f'                    <Rectangle width="9000" height="2000" originX="0.5" originY="1" name="Path" id="{doc.new_id()}"/>',
                                        "                </Shape>"]
    for shape in ("9:9622", "9:9628"):
        i = doc.idx(shape)
        j = doc.end(i)
        doc.lines[j:j] = [f'                                <ClippingShape sourceId="{clip_id}" name="Mug Clip" id="{doc.new_id()}"/>']
    round_ball(doc, intro, ("9:9622", "9:9630", "9:9631", "9:9633"))
    for oid in ("9:9628", "9:9257", "9:9272", "9:9481"):
        doc.drop_object(loop, oid)
    doc.drop_object(intro, "9:9628")
    doc.set_duration(loop, N)
    fr_i, fr_l = range(INTRO), range(N)
    hide_x, hide_y = mug_hide[0], mug_hide[1] + BALL_CENTER
    px = plane_x(room)
    doc.set_prop(intro, ids["ball"], "x", bake({f: hide_x + px(f) for f in fr_i}, fr_i))
    doc.set_prop(intro, ids["ball"], "y", [(0, hide_y, "hold")])
    doc.set_prop(loop, ids["ball"], "x", bake(xs, fr_l))
    doc.set_prop(loop, ids["ball"], "y", bake(ys, fr_l))
    for prop, ser in (("scaleX", b.sx), ("scaleY", b.sy)):
        doc.set_prop(intro, ids["scale"], prop, [(0, 1.0, "hold"), (INTRO - 1, 1.0, "hold")])
        doc.set_prop(loop, ids["scale"], prop, bake(ser, fr_l))

    def both(oid, prop, fn, rest):
        doc.set_prop(loop, oid, prop, bake(series(0, N, fn), fr_l))
        doc.set_prop(intro, oid, prop, [(0, rest, "hold"), (INTRO - 1, rest, "hold")])
    both(piv["mug"], "rotation", mug, 0.0)
    both(piv["books"], "rotation", books, 0.0)
    both(piv["stick"], "rotation", stick, 0.0)
    both(piv["card"], "rotation", card, 0.0)
    # the band's middle vertex sags under the ball (it was already keyed this way by the old loop)
    band_vertex = "9:9613"
    doc.set_prop(loop, band_vertex, "y", bake(series(0, N, lambda f: 5.0702 + band(f) / 0.85), fr_l))
    doc.set_prop(loop, band_vertex, "x", bake(series(0, N, lambda f: 2.5149 - 0.07 * band(f)), fr_l))
    doc.rebuild_waiting(room)



def card4(doc, write):
    global BALL_CENTER
    room = "Chapter 1 Card 4"
    N = 400
    BALL_CENTER = 16.78
    Rb = 17.1
    A = (721.0, 511.2 - Rb)           # the crossword flower's checker head
    B = (786.0, 532.2 - Rb)           # the yellow S hexagon's flat top
    C = (680.0, 548.2 - Rb)           # the purple leaf's top edge
    base_y = 634.2                    # where the stems meet the pot's rim
    pivots = dict(cross=(720.9, base_y), hexa=(765.5, base_y), leaf=(714.5, 633.0))
    HOP, STAY = 40, 4                 # frames in the air, frames on the flower before the next hop: a steady beat of 44
    F_GO = 72
    legs = [("cross", A, "hexa", B, 38), ("hexa", B, "leaf", C, 68), ("leaf", C, "cross", A, 26)]
    sched = []                       # (frame landed, flower)
    f = F_GO
    takeoffs = []
    for rnd in range(2):
        for src, ps, dst, pd_, h in legs:
            takeoffs.append((f, f + HOP, src, pd_, h, dst))
            sched.append((f + HOP, dst))
            f += HOP + STAY
    F_END = takeoffs[-1][1]

    dip = {"cross": 0.04, "hexa": 0.04, "leaf": 0.04}
    land = {}
    for fl, who in sched:
        land.setdefault(who, []).append(fl)
    def react(who, fr):
        return sum(spring(fr - fl, 1.0, down=3, tau=8.0, period=16.0) for fl in land.get(who, []))
    sway = lambda fr: 0.014 * (1 - math.cos(2 * math.pi * fr / 48)) / 2 if fr < F_GO - 24 else (
        0.014 * (1 - math.cos(2 * math.pi * (F_GO - 24) / 48)) / 2 * (1 - smooth((fr - (F_GO - 24)) / 24)) if fr < F_GO else 0.0)
    scale_y = {w: (lambda fr, w=w: 1 - dip[w] * react(w, fr)) for w in dip}
    rotation = {"cross": lambda fr: sway(fr) + 0.02 * react("cross", fr), "hexa": lambda fr: 0.025 * react("hexa", fr), "leaf": lambda fr: -0.025 * react("leaf", fr)}

    b = Ball(N)
    pos = {"cross": A, "hexa": B, "leaf": C}
    contact_y = {"cross": 511.2, "hexa": 532.2, "leaf": 548.2}
    def ride(who, fr):
        p = pos[who]
        sy = scale_y[who](fr)
        return (p[0], p[1] + (1 - sy) * (base_y - contact_y[who]))
    cur = "cross"
    fr = 0
    for (fl, fland, ps, pd_, h, dst) in takeoffs:
        for g in range(fr, fl + 1):
            b.put(g, ride(cur, g))
        pts = arc(b.c[fl], ride(dst, fland), fland - fl, h)
        b.seg(fl, fland, pts)
        cur = dst
        fr = fland
    for g in range(fr, N):
        b.put(g, ride(cur, g))
    for fl, who in sched:
        b.squash(fl, 0.10)
    xs, ys = b.node()

    top = min(c[1] for c in b.c.values()) - 17.6
    print(f"{room}: loop {N} frames ({N / 60:.2f} s)")
    names = {"cross": "crossword flower", "hexa": "yellow S hexagon", "leaf": "purple leaf"}
    print(f"  rest on the crossword flower until frame {F_GO}")
    for fl, fland, ps, pd_, h, dst in takeoffs:
        print(f"  frame {fl:3d} hop off the {names[ps]}; frame {fland:3d} lands on the {names[dst]}  (loop {fland / 60:5.2f} s, timecode {fland / 60 + 3.2:5.2f} s; arc {h} high, gravity {gravity(HOP, h):.2f})")
    print(f"  highest point of the ball: y {top:.1f} ({phone_y(top):.0f} px on the phone frame); copy ends at {COPY_BOTTOM:.0f}: clearance {phone_y(top) - COPY_BOTTOM:.0f} px")
    head_top = 511.2
    cl = min(c[1] for f_, c in b.c.items() if 701.8 - 17 < c[0] < 740 + 17)
    over = [(f_, c) for f_, c in b.c.items() if 701.8 - 14 < c[0] < 740 + 14 and c[1] + 17 > head_top + 0.5 and not (abs(c[0] - A[0]) < 1 and abs(c[1] - A[1]) < 6)]
    print(f"  frames where the ball is in the checker head (should be none): {[f_ for f_, _ in over][:5]}")
    print(f"  x range {min(c[0] for c in b.c.values()) - 17.6:.0f} to {max(c[0] for c in b.c.values()) + 17.6:.0f}")
    if not write:
        return

    loop, intro = f"{room} Loop", f"{room} Intro"
    ball_id, scale_id = "9:11187", "9:11189"
    piv = {}
    piv["cross"], _ = doc.wrap("9:11138", f"{room} Crossword Flower", pivots["cross"][0] - 669.0, pivots["cross"][1] - 489.0)
    piv["hexa"], _ = doc.wrap("9:10996", f"{room} S Flower", pivots["hexa"][0] - 669.0, pivots["hexa"][1] - 489.0)
    piv["leaf"], _ = doc.wrap("9:11075", f"{room} Purple Leaf", pivots["leaf"][0] - 669.0, pivots["leaf"][1] - 489.0)
    round_ball(doc, intro, ("9:11190", "9:11198", "9:11199", "9:11201"))
    doc.drop_object(loop, "9:11138")
    doc.set_duration(loop, N)
    fr_i, fr_l = range(INTRO), range(N)
    px = plane_x(room)
    hx, hy = A[0], A[1] + BALL_CENTER
    doc.set_prop(intro, ball_id, "x", bake({f_: hx + px(f_) for f_ in fr_i}, fr_i))
    doc.set_prop(intro, ball_id, "y", [(0, hy, "hold")])
    doc.set_prop(loop, ball_id, "x", bake(xs, fr_l))
    doc.set_prop(loop, ball_id, "y", bake(ys, fr_l))
    for prop, ser in (("scaleX", b.sx), ("scaleY", b.sy)):
        doc.set_prop(intro, scale_id, prop, [(0, 1.0, "hold"), (INTRO - 1, 1.0, "hold")])
        doc.set_prop(loop, scale_id, prop, bake(ser, fr_l))

    def both(oid, prop, fn, rest):
        doc.set_prop(loop, oid, prop, bake(series(0, N, fn), fr_l))
        doc.set_prop(intro, oid, prop, [(0, rest, "hold"), (INTRO - 1, rest, "hold")])
    for w in ("cross", "hexa", "leaf"):
        both(piv[w], "scaleY", scale_y[w], 1.0)
        both(piv[w], "rotation", rotation[w], 0.0)
    doc.rebuild_waiting(room)


def main(argv):
    cards = [int(c) for c in argv[argv.index("--cards") + 1].split(",")] if "--cards" in argv else [2, 3, 4]
    doc = Doc(SCENE)
    for c in cards:
        {2: card2, 3: card3, 4: card4}[c](doc, "--write" in argv)
    if "--write" in argv:
        doc.save()
        print("wrote", SCENE)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
