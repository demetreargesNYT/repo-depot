"""The Mini, "the trick" (Demetre's brief, 2026-11-04): fast, staccato sleight of hand. The ball is a magician's ball, hiding in boxes
and bursting out of the one you didn't expect. Every cube, still or moving, is drawn by the 3D cube method (cube3d.py).

Scale (note 5, kept): each plane holds its pieces in a pivot at (747.5, 711.5), the room's middle on the floor line, scaled 0.85; the
ball is 1.7. The cubes that drop in fall 800/0.85 in their own space so on screen they drop as before. Every line is 1.5 on screen
and never scales (transformAffectsStroke off). The intro (3.2 s: the planes pan in, the tops and the right stack's front drop) is the
same as before; the new faces ride in the same nodes as the shapes they replace.

The cubes (on screen, after the 0.85 scale; the phone crop is x 560 to 935, y 0 to 812):
  Top cube (U)      front x 788.5-869.9, y 590.0-671.4; top (its opening, with a lid hinged on the back edge) y 552.0-590.0,
                    x 755.9-869.9; left side x 755.9-788.5. Fully inside the crop: the main stage.
  Right stack (R)   front x 869.9-951.3, y 671.4-752.8; top (an opening with a lid) y 633.4-671.4, x 837.3-951.3; left side
                    x 837.3-869.9. Cut by the crop on the right (x 935 to 951.3, 16 px); its opening is inside from x 837.3 to 935.
  Front cube (F)    front x 621.3-702.7, y 749.5-830.8; top (an opening with a lid) y 711.5-749.5, x 621.3-735.3; right side
                    x 702.7-735.3. Cut by the crop at the bottom (y 812 to 830.8); its opening is wholly inside.
  Left box (L)      front x 567.7-654.0, y 625.0-711.3; left side x 543.4-567.7 (cut by the crop from 543.4 to 560). It is drawn at
                    its own height, so its top is edge-on: its lid shows only when it opens; the ball leaves and enters it at x 569 to
                    629, inside the crop.
  Draw order: U's, L's and F's faces and R's front are in the Front Plane, over the ball; every lid, every dark opening, U's
  doorway and R's left side are in the Floor Plane, under it. The ball hides in a box behind its front faces. R's left side moved
  under the ball so the ball coming out of U's door (in front of R) passes over it; inside R the ball stays right of it (x 872+).

The timeline (one cycle of 771 frames, 12.85 s; times are from the scene being set, the first pass: the cycle starts at 1.83 s, once
the tops have landed, and the Loop picks it up at 3.2 s; the Finesse panel shows the same times):
  Routine 1, "nothing up my sleeve" (1.83 to 8.45 s)
    1.83   U's lid swings open (0.2 s, to 92 degrees)
    1.98   the ball rises to peek out of U (top half above the rim), glances left, right, back (12 degree turns in place)
    3.12   it ducks (down at 3.28); 3.30 U's lid snaps shut (0.12 s, one 2 degree bounce that sinks back)
    3.52   fake-out: R's lid cracks 28 degrees, holds 0.23 s, snaps shut
    3.85   fake-out: F's lid the same
    4.28   L's lid flings open and the ball bursts out of the left box (the one nobody was watching): a quick low arc (top y 530)
           over F's lid, which opens at 4.72, into F (5.22)
    5.43   it peeks straight back out of F, glances right, ducks; 6.32 F shuts (everyone has seen it go into F)
    6.33   U turns 90 degrees on its vertical axis (0.5 s, a 3 degree overshoot that settles by 7.03 s), showing its other face
    7.20   U's lid (now hinged on its right) pops; 7.27 the ball pops out of U with extra height (top y 428), arcs over F into L (8.27);
           L shuts
  Routine 2, "the door" (8.45 to 14.68 s, then routine 1 again)
    8.45   U turns back 90 degrees while F's lid cracks as a fake-out
    9.28   U's front face swings open like a door on its left hinge (to 90 degrees, 0.2 s): the ball (it went into L!) is inside;
           9.40 it shoots out of the doorway, arcs (top y 525) into R, whose lid opens at 9.72 (10.15); the door and R shut
    10.73  R's lid opens; 10.87 the ball peeks out of R, glances towards U, ducks; 11.88 R shuts
    12.13  a ripple of fake-outs, left to right: L's lid cracks, then F's (12.33), then U's (12.53)
    12.90  R's lid flings open; 12.97 the ball flies out in a high arc (top y 475) into U, whose lid opens at 13.40 (13.90); U shuts;
           a beat out of sight, and U's lid opens again: routine 1
  U's two turns (+90, then -90) put every cube back on its starting pose, so the loop closes on the drawing itself (no instant
  reset). U never turns with a lid or its door open, and no lid starts a move before its last one has settled (both asserted).

Physics: one gravity, 0.40; every flight a parabola; the lids and the door are what fling the ball (each launch is from rest inside a
box); every landing is a catch out of sight inside a box (it settles over 6 frames). The ball is hidden in a box for at most about
1.2 s, and something moves in the phone crop all that time. It keeps the spin it left with (a quarter of the roll its push would give);
the two glances are 12 degree turns in place; the last hidden rest takes up the turn left over to a whole number of turns.
Squash: none on the catches (all out of sight) and none at the peeks (an eased lift, arriving softly); a 3 percent stretch, volume
kept, on the pop out of U (the fastest move), easing back by its apex. The holds in the peeks are the held glances.
"""
import math
import re
import xml.etree.ElementTree as ET

import cube3d as c3
from cube3d import Cube, Face, LIGHT, DARK
from common import CENTER_IN_SCALE, BallArt, Cycle, _set_attrs, emit, plane_x, prepare_ball, smooth

ROOM = "The Mini"
T0 = 110                                   # 1.83 s: the tops have landed (their squash is over at 1.82 s)
A = (747.5, 711.5)                         # the scale's anchor: the room's middle, on the floor line
K = 0.85
PLANES = {"Front": "9:5695", "Floor": "9:5694"}
CUBES = ("9:5206", "9:5208", "9:5210", "9:5212")    # the four drop-ins
ART = {"c1": "9:5207", "c3": "9:5211", "c4": "9:5213"}    # their Art nodes (their space is the planes' own space)
BALL_SCALE = 1.7
G = 0.40
R_BALL = 17.678 * BALL_SCALE               # the ball's radius on the screen (30.05)
COPY_Y = 425.0                             # the ball's top and every moving piece stay at or below this
CROP = (560.0, 935.0)

# ---- the cubes, measured from the drawing (the planes' own space, before the 0.85) -----------------------------------------
U = Cube("The Mini Top Cube", (795.667, 568.582, 891.496, 664.328), (-38.332, -44.682))
R = Cube("The Mini Right Stack", (891.498, 664.330, 987.327, 760.076), (-38.332, -44.682))
F = Cube("The Mini Front Cube", (598.968, 756.178, 694.797, 851.924), (38.331, -44.682))
L = Cube("The Mini Left Box", (536.008, 609.656, 637.502, 711.239), (-28.615, 0.0))
ART_CORNERS = {                            # the drawing's own corners, for the check at PERSPECTIVE 0
    (U, "left"): [(757.338, 523.894), (795.67, 568.576), (795.67, 664.322), (757.338, 619.64)],
    (U, "top"): [(757.266, 523.894), (853.095, 523.894), (891.427, 568.576), (795.597, 568.576)],
    (R, "top"): [(853.097, 619.646), (948.926, 619.646), (987.257, 664.328), (891.428, 664.328)],
    (R, "left"): [(853.166, 619.646), (891.497, 664.328), (891.497, 760.074), (853.166, 715.392)],
    (F, "right"): [(694.798, 756.176), (733.129, 711.494), (733.129, 807.24), (694.798, 851.922)],
    (F, "top"): [(637.225, 711.494), (733.054, 711.494), (694.723, 756.176), (598.894, 756.176)],
    (L, "left"): [(507.393, 609.656), (536.008, 609.656), (536.008, 711.239), (507.393, 711.239)],
}

# each cube is one square of the puzzle: every face one solid colour, as the illustration drew it (its fills before the 3D rebuild):
# the fronts and sides light, R's front and L's side black, the tops of U and F black and R's light. Lids and the door take
# their face's colour (their insides stay light, so an open lid reads against the dark opening). U's right face, which the
# illustration never drew and the turn shows, takes the colour of the face opposite it, its left side (light).
COL = {
    (U, "front"): LIGHT, (U, "left"): LIGHT, (U, "right"): LIGHT, (U, "back"): LIGHT, (U, "lid"): DARK,
    (R, "front"): DARK, (R, "left"): LIGHT, (R, "lid"): LIGHT,
    (F, "front"): LIGHT, (F, "right"): LIGHT, (F, "lid"): DARK,
    (L, "front"): LIGHT, (L, "left"): DARK,
}

# tempo (frames)
OPEN, OPEN_N = math.radians(92), 12        # lids open to 92 degrees in 0.2 s (further, the free edge dips back and reads as a wobble)
SHUT_N, BOUNCE_UP, BOUNCE_N, BOUNCE = 7, 3, 24, math.radians(2)    # snap shut in 0.12 s, one 2 degree bounce that sinks back softly
CRACK, CRACK_N, CRACK_HOLD = math.radians(28), 7, 14      # a crack holds 0.23 s (a quicker one reads as a buzz)
DOOR = math.radians(90)
TURN_N, SETTLE_N, OVER = 30, 12, math.radians(3)
PEEK_N, PEEK_RISE, DUCK_N = 16, 39.2, 10   # the peek's lift (39.2 px in 0.27 s) and the duck: it pulls itself down, then drops at 0.40 (0.17 s)
GLANCE = math.radians(12)


def S(p):
    return (A[0] + K * (p[0] - A[0]), A[1] + K * (p[1] - A[1]))


def ease_out(u):
    u = min(1.0, max(0.0, u))
    return 1 - (1 - u) ** 3


def ease_io(u):
    u = min(1.0, max(0.0, u))
    return 4 * u ** 3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2


# ---- hinges and turns: an angle per cycle frame from a list of events -------------------------------------------------------
def angles(events, n, top=OPEN):
    """events: [(frame, kind)] with kind "open" (to `top` in OPEN_N, ease out), "shut" (to 0 in SHUT_N, ease in, then one tiny
    bounce), "crack" (to CRACK and back), or ("turn", target): a 0.5 s turn with a small overshoot that settles."""
    a = [0.0] * (n + 1)
    evs = sorted(events, key=lambda e: e[0])
    for (fa, ka), (fb, kb) in zip(evs, evs[1:]):
        assert fb - fa >= lid_ends(ka), ("a move starts before the one before it has settled", fa, ka, fb, kb)
    for k, (f0, kind) in enumerate(evs):
        f1 = evs[k + 1][0] if k + 1 < len(evs) else n + 1
        a0 = a[f0 - 1] if f0 > 0 else 0.0
        for g in range(f0, f1):
            t = g - f0
            if kind == "open":
                a[g] = a0 + (top - a0) * ease_out(t / OPEN_N)
            elif kind in ("shut", "crack"):
                if kind == "crack":
                    if t < CRACK_N:
                        a[g] = CRACK * ease_out(t / CRACK_N)
                        continue
                    if t < CRACK_N + CRACK_HOLD:
                        a[g] = CRACK
                        continue
                    t -= CRACK_N + CRACK_HOLD
                    a0 = CRACK
                if t < SHUT_N:
                    a[g] = a0 * (1 - (t / SHUT_N) ** 2)
                elif t < SHUT_N + BOUNCE_UP:
                    a[g] = BOUNCE * math.sin(0.5 * math.pi * (t - SHUT_N) / BOUNCE_UP)
                elif t < SHUT_N + BOUNCE_N:
                    a[g] = BOUNCE * (1 - smooth((t - SHUT_N - BOUNCE_UP) / (BOUNCE_N - BOUNCE_UP)))
                else:
                    a[g] = 0.0
            else:
                target = kind[1]
                over = math.copysign(OVER, target - a0)
                if t < TURN_N:
                    a[g] = a0 + (target + over - a0) * ease_io(t / TURN_N)
                elif t < TURN_N + SETTLE_N:
                    a[g] = target + over * (1 - smooth((t - TURN_N) / SETTLE_N))
                else:
                    a[g] = target
    return a


def lid_ends(kind):
    """Frames an event takes to come to rest."""
    return {"open": OPEN_N, "shut": SHUT_N + BOUNCE_N, "crack": CRACK_N + CRACK_HOLD + SHUT_N + BOUNCE_N}.get(kind, TURN_N + SETTLE_N)


# ---- the ball's timeline ----------------------------------------------------------------------------------------------------
class Path:
    def __init__(self):
        self.p, self.mode, self.w, self.glance, self.stretch = [], [], [], [], []
        self.notes = []

    @property
    def now(self):
        return len(self.p)

    def put(self, p, mode, w=0.0, gl=0.0, st=0.0):
        self.p.append(p)
        self.mode.append(mode)
        self.w.append(w)
        self.glance.append(gl)
        self.stretch.append(st)

    def rest(self, p, n, mode="hidden"):
        for _ in range(n):
            self.put(p, mode)

    def peek(self, p, glances):
        """The peek, the ball's own effort: an eased lift of PEEK_RISE in PEEK_N frames (arriving softly), the glances [(turn, frames
        to turn, frames held)], then the duck back down to p in DUCK_N frames (a small push down, then a drop at 0.40). Returns the frame it is down."""
        for t in range(1, PEEK_N + 1):
            self.put((p[0], p[1] - PEEK_RISE * smooth(t / PEEK_N)), "air")
        top = (p[0], p[1] - PEEK_RISE)
        g0 = 0.0
        for turn, n_turn, n_hold in glances:
            for t in range(1, n_turn + 1):
                self.put(top, "rest", gl=g0 + (turn - g0) * ease_io(t / n_turn))
            for _ in range(n_hold):
                self.put(top, "rest", gl=turn)
            g0 = turn
        v0 = (PEEK_RISE - 0.5 * G * DUCK_N ** 2) / DUCK_N
        for t in range(1, DUCK_N + 1):
            self.put((p[0], top[1] + v0 * t + 0.5 * G * t * t), "air" if t < DUCK_N else "hidden")
        return self.now

    def fly(self, p0, p1, catch_y, apex_y, stretch=0.0):
        """From rest at p0 (the box flings it) to p1 in another box: a parabola at 0.40 through apex_y, caught out of sight once its
        centre is at catch_y, then 6 frames settling to p1. Returns (launch frame, the frame it is out of sight, its velocity)."""
        vy = -math.sqrt(2 * G * (p0[1] - apex_y))
        T = -vy / G + math.sqrt(2 * (catch_y - apex_y) / G)
        vx = (p1[0] - p0[0]) / T
        f_go = self.now
        w = 0.25 * vx / R_BALL
        t = 0
        while True:
            t += 1
            q = (p0[0] + vx * t, p0[1] + vy * t + 0.5 * G * t * t)
            st = stretch * (smooth(t / 3) * (1 - smooth((t - 3) / 13)))
            if q[1] >= catch_y and vy + G * t > 0:
                self.put(q, "hidden")
                break
            self.put(q, "air", w=w, st=st)
        f_in = self.now - 1
        for k in range(1, 7):
            s = smooth(k / 6)
            self.put((q[0] + (p1[0] - q[0]) * s, q[1] + (p1[1] - q[1]) * s), "hidden")
        apex = min(y for _, y in self.p[f_go:f_in])
        self.notes.append((f_go, f_in, apex, (vx, vy)))
        return f_go, f_in, (vx, vy)


# ---- the art ----------------------------------------------------------------------------------------------------------------
def parse(doc):
    return ET.fromstring("\n".join(doc.lines))


def delete(doc, oid):
    i = doc.idx(oid)
    del doc.lines[i:doc.end(i) + 1]


def move_before(doc, oid, before_id):
    """Cut an element and put it just before another (same indent assumed)."""
    i = doc.idx(oid)
    block = doc.lines[i:doc.end(i) + 1]
    del doc.lines[i:doc.end(i) + 1]
    j = doc.idx(before_id)
    doc.lines[j:j] = block


def scale_room(doc):
    """The planes' pieces into 0.85 pivots, the drop-ins' falls compensated. Returns {plane: the pivot's Art node id}."""
    root = parse(doc)
    byid = {e.get("id"): e for e in root.iter() if e.get("id")}
    arts = {}
    for name, pid in PLANES.items():
        kids = [c for c in byid[pid] if c.tag in ("Node", "Shape")]
        piv, art = doc.wrap_run(kids[0].get("id"), kids[-1].get("id"), f"{ROOM} {name} Scale", *A)
        _set_attrs(doc, piv, {"scaleX": K, "scaleY": K})
        arts[name] = art
    a, b = doc.anim(f"{ROOM} Intro")
    for cid in CUBES:                       # the first y key of each drop: as far above its rest on screen as before
        i = next(j for j in range(a, b) if f'objectId="{cid}"' in doc.lines[j])
        j = next(j for j in range(i, doc.end(i)) if 'property="y"' in doc.lines[j])
        ks = [m for m in range(j, doc.end(j)) if "<KeyFrameDouble" in doc.lines[m]]
        val = lambda m: float(re.search(r' value="([^"]+)"', doc.lines[m]).group(1)) if ' value="' in doc.lines[m] else 0.0
        v0, v1 = val(ks[0]), val(ks[-1])
        doc.lines[ks[0]] = re.sub(r' value="[^"]+"', f' value="{v1 + (v0 - v1) / K:.4f}"', doc.lines[ks[0]])
    return arts


def insert_first(doc, parent_id, lines):
    i = doc.idx(parent_id)
    doc.lines[i + 1:i + 1] = lines


def insert_last(doc, parent_id, lines):
    j = doc.end(doc.idx(parent_id))
    doc.lines[j:j] = lines


def pad_in(doc, parent_id):
    l = doc.lines[doc.idx(parent_id)]
    return " " * (len(l) - len(l.lstrip()) + 4)


def check_rest_projection():
    """At PERSPECTIVE 0 every cube at rest is the drawing: the front faces exactly, the rest within the drawing's own 0.07 slack."""
    worst = 0.0
    for cube in (U, R, F, L):
        k0 = cube.cam.k
        cube.cam.k = 0.0
        x0, y0 = cube.centre[0] - cube.hx, cube.centre[1] - cube.hy
        x1, y1 = cube.centre[0] + cube.hx, cube.centre[1] + cube.hy
        for p, q in zip(cube.quad("front"), [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]):
            assert math.dist(p, q) < 1e-9, (cube.name, "front", p, q)
        for (c, face), pts in ART_CORNERS.items():
            if c is cube:
                got = cube.quad(face)
                for p in pts:
                    d = min(math.dist(p, g) for g in got)
                    worst = max(worst, d)
                    assert d < 0.1, (cube.name, face, p, d)
        cube.cam.k = k0
    return worst


# ---- the hidden check -------------------------------------------------------------------------------------------------------
def inside(pt, poly):
    s = None
    for i in range(len(poly)):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % len(poly)]
        c = (x1 - x0) * (pt[1] - y0) - (y1 - y0) * (pt[0] - x0)
        if abs(c) < 1e-9:
            continue
        if s is None:
            s = c > 0
        elif (c > 0) != s:
            return False
    return True


def disc(c, r):
    pts = [c]
    for rr in (0.35 * r, 0.7 * r, 0.98 * r):
        for k in range(28):
            a = 2 * math.pi * k / 28
            pts.append((c[0] + rr * math.cos(a), c[1] + rr * math.sin(a)))
    return pts


def doorway():
    """The inside of U seen through its open door (still: U never turns with its door open): its inner right wall and its floor,
    light, over the dark back, each cut to the doorway."""
    open_ = lambda pose: pose.get("door", 0) > 1e-6
    window = U.quad("front")
    wall = c3.clip(U.quad("right", flip=True), window)
    floor = c3.clip(U.quad("bottom", flip=True), window)
    return [c3.Fixed(U, f"{U.name} Inside Wall", wall, LIGHT, open_), c3.Fixed(U, f"{U.name} Inside Floor", floor, LIGHT, open_),
            c3.Fixed(U, f"{U.name} Doorway", window, DARK, open_)]


def build(doc, scene, sheet):
    worst = check_rest_projection()

    # ---------------------------------------------------------------- the old art out
    olds = ["9:5214", "9:5176", "9:5186", "9:5196", "9:5155"]        # the 'a' groups (U front, side, F, R side, L), R's top, front, inner top, the tops
    root = parse(doc)
    gone = {e.get("id") for o in olds for e in next(x for x in root.iter() if x.get("id") == o).iter() if e.get("id")}
    for o in olds:
        delete(doc, o)
    for an in ("Intro", "Waiting", "Built", "Loop"):
        a, b = doc.anim(f"{ROOM} {an}")
        for oid in sorted({m.group(1) for l in doc.lines[a:b] for m in [re.search(r'<KeyedObject objectId="([^"]+)"', l)] if m and m.group(1) in gone}):
            doc.drop_object(f"{ROOM} {an}", oid)
    move_before(doc, "9:5206", "9:5212")            # Cubes 1 (U's and F's tops) above Cubes 4 (R's top): U's lid sits in front of R's
    arts = scale_room(doc)

    # ---------------------------------------------------------------- the ball
    art = BallArt(scene, ROOM)
    _set_attrs(doc, art.b01, {"scaleX": BALL_SCALE, "scaleY": BALL_SCALE})
    art.k = BALL_SCALE
    art.R, art.Rc = R_BALL, 17.2 * art.k
    sx, sy = -0.072021484, 0.096008301
    art.dc = (art.ox + art.k * (sx + CENTER_IN_SCALE[0]), art.oy + art.k * (sy + CENTER_IN_SCALE[1]))
    spin = prepare_ball(doc, art)

    centre_x = lambda cube: S(cube.cam.project(cube.centre))[0]
    U_IN = (round(centre_x(U), 1), 625.0)           # wholly behind U's front and left side (top 595, under the rim at 590)
    L_IN = (round(centre_x(L), 1), 668.0)           # behind L's front (its top edge is y 625)
    F_IN = (round(centre_x(F), 1), 790.0)           # behind F's front and right side
    R_IN = (902.0, 712.0)                           # behind R's front, right of R's left side (which is under the ball)
    CATCH = {"U": 622.0, "L": 657.0, "F": 781.5, "R": 703.4}    # a centre this low is wholly out of sight

    P = Path()
    lids = {"U": [], "R": [], "F": [], "L": []}
    door, turn = [], []
    marks = {}

    def mark(k):
        marks[k] = P.now

    # routine 1
    lids["U"].append((0, "open"))
    P.rest(U_IN, 9)
    mark("peek U")
    P.peek(U_IN, [(GLANCE, 8, 10), (-GLANCE, 12, 10), (0.0, 8, 4)])
    mark("duck U")
    lids["U"].append((P.now + 1, "shut"))
    P.rest(U_IN, 14)
    lids["R"].append((P.now, "crack"))
    mark("fake R")
    P.rest(U_IN, 20)
    lids["F"].append((P.now, "crack"))
    mark("fake F")
    P.rest(U_IN, 12)
    P.rest(L_IN, 10)                                # out of sight, the ball is now in L
    lids["L"].append((P.now, "open"))
    P.rest(L_IN, 4)
    go, f_in, v = P.fly(L_IN, F_IN, CATCH["F"], 560.0)
    marks["burst L"], marks["into F"] = go, f_in
    lids["L"].append((go + 16, "shut"))
    lids["F"].append((f_in - 30, "open"))
    P.rest(F_IN, 6)
    mark("peek F")                                  # it lands in F and peeks straight out: everyone sees it is in F
    P.peek(F_IN, [(GLANCE, 8, 8), (0.0, 8, 2)])
    lids["F"].append((P.now + 1, "shut"))
    P.rest(F_IN, 2)
    turn.append((P.now, ("turn", math.pi / 2)))
    mark("turn")
    P.rest(F_IN, TURN_N + SETTLE_N)
    P.rest(U_IN, 10)                                # out of sight, back in U once it has settled
    lids["U"].append((P.now, "open"))
    P.rest(U_IN, 4)
    go, f_in, v = P.fly(U_IN, L_IN, CATCH["L"], 458.0, stretch=0.03)
    marks["pop U"], marks["into L"] = go, f_in
    lids["U"].append((go + 22, "shut"))
    lids["L"].append((f_in - 28, "open"))
    lids["L"].append((f_in + 2, "shut"))
    P.rest(L_IN, 4)
    # routine 2
    mark("turn back")
    turn.append((P.now, ("turn", 0.0)))
    lids["F"].append((P.now + 6, "crack"))
    P.rest(L_IN, TURN_N + SETTLE_N - 4)
    P.rest(U_IN, 12)                                # the door waits until the turn has settled for 0.2 s
    door.append((P.now, "open"))
    mark("door")
    P.rest(U_IN, 7, "rest")                         # the door opens: the ball shows in the doorway
    go, f_in, v = P.fly(U_IN, R_IN, CATCH["R"], 555.0)
    marks["out of the door"], marks["into R"] = go, f_in
    door.append((go + 18, "shut"))
    lids["R"].append((f_in - 26, "open"))
    lids["R"].append((f_in + 2, "shut"))
    P.rest(R_IN, 28)
    lids["R"].append((P.now, "open"))
    P.rest(R_IN, 8)
    mark("peek R")
    P.peek(R_IN, [(-GLANCE, 9, 14), (0.0, 9, 2)])
    lids["R"].append((P.now + 1, "shut"))
    P.rest(R_IN, 16)
    lids["L"].append((P.now, "crack"))                # a ripple of fake-outs, left to right: L, F, then U
    lids["F"].append((P.now + 12, "crack"))
    lids["U"].append((P.now + 24, "crack"))
    mark("ripple of fakes")
    P.rest(R_IN, 46)
    lids["R"].append((P.now, "open"))
    P.rest(R_IN, 4)
    go, f_in, v = P.fly(R_IN, U_IN, CATCH["U"], 505.0)
    marks["R to U"], marks["into U"] = go, f_in
    lids["R"].append((go + 18, "shut"))
    lids["U"].append((f_in - 30, "open"))
    lids["U"].append((f_in + 2, "shut"))
    P.rest(U_IN, 40)
    Lc = P.now                                      # frame Lc is frame 0 again
    P.put(U_IN, "hidden")

    # ---------------------------------------------------------------- the pieces' poses, frame by frame
    a_lid = {k: angles(ev, Lc) for k, ev in lids.items()}
    a_door = angles(door, Lc, top=DOOR)
    a_turn = angles(turn, Lc)
    for arr in list(a_lid.values()) + [a_door, a_turn]:
        assert abs(arr[0]) < 1e-9 and abs(arr[Lc]) < 1e-9
    poses = {
        "U": [{"turn": a_turn[g], "lid": a_lid["U"][g], "door": a_door[g]} for g in range(Lc + 1)],
        "R": [{"lid": a_lid["R"][g]} for g in range(Lc + 1)],
        "F": [{"lid": a_lid["F"][g]} for g in range(Lc + 1)],
        "L": [{"lid": a_lid["L"][g]} for g in range(Lc + 1)],
    }
    # the lids never open with the turning cube's corner over them, and U never turns with its door or lid open
    for g in range(Lc + 1):
        if abs(a_turn[g]) > 1e-6 and abs(a_turn[g] - math.pi / 2) > 1e-6:
            assert a_lid["R"][g] == 0 and a_door[g] == 0 and a_lid["U"][g] == 0, ("U turns with a lid open", g)

    # ---------------------------------------------------------------- the faces
    cub = {"U": U, "R": R, "F": F, "L": L}
    faces = {
        "front": [Face(U, "front", "door", fill=COL[(U, "front")], name=f"{U.name} Front"),
                  Face(U, "left", fill=COL[(U, "left")]), Face(U, "right", fill=COL[(U, "right")]),
                  Face(U, "back", fill=COL[(U, "back")]),
                  Face(L, "front", fill=COL[(L, "front")]), Face(L, "left", fill=COL[(L, "left")]),
                  Face(F, "front", fill=COL[(F, "front")]), Face(F, "right", fill=COL[(F, "right")])],
        "c3": [Face(R, "front", fill=COL[(R, "front")])],
        "floor": doorway(),
        "c1": [Face(U, "top", "lid", fill=COL[(U, "lid")], name=f"{U.name} Lid"), Face(U, "top", "lid", flip=True, name=f"{U.name} Lid Inside"),
               Face(U, "top", fill=DARK, name=f"{U.name} Opening"),
               Face(F, "top", "lid", fill=COL[(F, "lid")], name=f"{F.name} Lid"), Face(F, "top", "lid", flip=True, name=f"{F.name} Lid Inside"),
               Face(F, "top", fill=DARK, name=f"{F.name} Opening")],
        "c4": [Face(R, "top", "lid", fill=COL[(R, "lid")], name=f"{R.name} Lid"), Face(R, "top", "lid", flip=True, name=f"{R.name} Lid Inside"),
               Face(R, "top", fill=DARK, name=f"{R.name} Opening")],
        "floor_end": [Face(R, "left", fill=COL[(R, "left")]),
                      Face(L, "top", "lid", name=f"{L.name} Lid"), Face(L, "top", "lid", flip=True, name=f"{L.name} Lid Inside")],
    }
    key_of = {U: "U", R: "R", F: "F", L: "L"}
    rest = lambda f: poses[key_of[f.cube]][0]
    ident = lambda p: p
    where = {"front": (arts["Front"], insert_first), "c3": (ART["c3"], insert_first), "floor": (arts["Floor"], insert_first),
             "c1": (ART["c1"], insert_first), "c4": (ART["c4"], insert_first), "floor_end": (arts["Floor"], insert_last)}
    for grp in faces:                               # a face no pose ever shows is not drawn at all (U's back)
        faces[grp] = [f for f in faces[grp] if any(f.visible(poses[key_of[f.cube]][g]) for g in range(Lc + 1))]
    for grp, fs in faces.items():
        parent, put = where[grp]
        pad = pad_in(doc, parent)
        lines = []
        for f in fs:
            lines += f.lines(doc, pad, rest(f), ident)
        put(doc, parent, lines)

    # every face's tracks; only the ones that move are keyed
    pieces, vertex_ids, moving = [], [], 0
    for grp, fs in faces.items():
        for f in fs:
            ps = poses[key_of[f.cube]]
            for (oid, prop), vals in f.tracks(ps, ident).items():
                if max(vals) - min(vals) < 1e-6:
                    continue
                assert abs(vals[0] - vals[Lc]) < 1e-6, (f.name, oid, prop)
                pieces.append((oid, prop, (lambda g, a=vals: a[g]), None))
                if prop != "opacity":
                    vertex_ids.append(oid)
                    moving += 1

    # ---------------------------------------------------------------- the checks on the screen
    front_faces = [f for f in faces["front"]] + faces["c3"]
    ball_top = min(p[1] for p in P.p) - R_BALL
    assert ball_top >= COPY_Y, ("the ball crosses the copy", ball_top)
    piece_top = min(S(q)[1] for grp in faces.values() for f in grp for g in range(0, Lc + 1, 2)
                    for q in f.outline(poses[key_of[f.cube]][g]) if f.visible(poses[key_of[f.cube]][g]))
    assert piece_top >= COPY_Y, ("a piece crosses the copy", piece_top)
    seen_hidden = []
    for g in range(Lc + 1):
        if P.mode[g] != "hidden":
            assert CROP[0] <= P.p[g][0] - R_BALL and P.p[g][0] + R_BALL <= CROP[1], ("the ball leaves the phone crop", g, P.p[g])
            continue
        covers = [[S(q) for q in f.outline(poses[key_of[f.cube]][g])] for f in front_faces if f.visible(poses[key_of[f.cube]][g])]
        bad = [q for q in disc(P.p[g], R_BALL - 0.8) if not any(inside(q, c) for c in covers)]
        if bad:
            seen_hidden.append((g, len(bad)))
    assert not seen_hidden, ("the ball shows when it should be hidden", seen_hidden[:8], sorted(marks.items(), key=lambda kv: kv[1]), [P.p[g] for g, _ in seen_hidden[:3]], [a_turn[g] for g, _ in seen_hidden[:3]])
    hidden_runs, run = [], 0
    for g in list(range(Lc)) * 2:
        run = run + 1 if P.mode[g] in ("hidden",) else 0
        hidden_runs.append(run)
    longest = max(hidden_runs)

    # ---------------------------------------------------------------- the ball's keys
    cyc = Cycle(Lc)
    for g in range(Lc + 1):
        cyc.put(g, P.p[g], "air" if P.mode[g] == "air" else "hidden")
        s = P.stretch[g]
        if s:
            cyc.sy[g], cyc.sx[g] = 1 + s, 1 / (1 + s)
    th = [0.0]
    for g in range(Lc):
        th.append(th[-1] + P.w[g])
    total = th[Lc]
    want = round(total / (2 * math.pi)) * 2 * math.pi
    a0 = marks["into U"] + 8                        # the last hidden rest takes up what is left over
    for g in range(a0, Lc + 1):
        th[g] += (want - total) * smooth((g - a0) / (Lc - a0))
    th = [th[g] + P.glance[g] for g in range(Lc + 1)]
    px = plane_x(scene, sheet, ROOM, "Front")

    def pre(f):
        return (U_IN[0] + px(f), U_IN[1]), 1.0, 1.0
    emit(doc, art, spin, cyc, th, T0, pre, pieces)
    thinned = sum(c3.thin_keys(doc, f"{ROOM} {an}", vertex_ids) for an in ("Intro", "Loop"))

    sec = lambda g: f"{(T0 + g) / 60:.2f} s"
    beats = ", ".join(f"{k} {sec(v)}" for k, v in sorted(marks.items(), key=lambda kv: kv[1]))
    flights = "; ".join(f"{sec(a)}-{sec(b)} apex {apex:.0f} (top {apex - R_BALL:.0f}) v ({vv[0]:.2f}, {vv[1]:.2f})" for a, b, apex, vv in P.notes)
    moves = []
    for k, ev in list(lids.items()) + [("U door", door), ("U turn", turn)]:
        for f0, kind in ev:
            moves.append((f0, f"{k}{'' if ' ' in k else ' lid'} {kind if isinstance(kind, str) else 'turn to ' + str(round(math.degrees(kind[1])))} {sec(f0)}"))
    moves = ", ".join(m for _, m in sorted(moves))
    return (f"{ROOM}: moves: {moves}; 3D cubes (perspective {c3.PERSPECTIVE}, rest pose at 0 within {worst:.3f} of the drawing), {moving} vertex tracks keyed "
            f"({thinned} keys thinned); beats: {beats}; flights: {flights}; ball top {ball_top:.0f}, pieces top {piece_top:.0f}; "
            f"longest hidden {longest} frames ({longest / 60:.2f} s); loop {Lc / 60:.2f} s ({Lc} frames)")
