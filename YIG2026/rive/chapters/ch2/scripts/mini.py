"""The Mini, "the trick" (Demetre's brief, 2026-11-04): sleight of hand at a considered pace. The ball is a magician's ball, hiding in
boxes and bursting out of the one you didn't expect. Every cube, still or moving, is drawn by the 3D cube method (cube3d.py); every
face is one solid colour (each cube is one square of the puzzle).

Scale (note 5, kept): each plane holds its pieces in a pivot at (747.5, 711.5), the room's middle on the floor line, scaled 0.85; the
ball is 1.7. The cubes that drop in fall 800/0.85 in their own space so on screen they drop as before. Every line is 1.5 on screen
and never scales (transformAffectsStroke off). The intro (3.2 s) is unchanged.

One viewpoint (finesse note 8): all four cubes use the projection of the top cube and the right stack, depth going up and to the left
(-0.4000, -0.4663 per unit depth). The front cube F and the left box L were drawn from other viewpoints; they are redrawn by cube3d at
the same size as the others (L was a little larger). L moved down onto the floor: its front is now at y 671.4-752.8 as R's, so its base's
back edge sits on the floor line like R's (it had stood with its front's bottom on the line, which put the left-leaning side above the
floor). F moved right by 68.7 (its top now leans left, and has to clear L): front x 690.0-771.5, y 749.5-830.8 (the bottom 18 px are
below the phone crop, as before). On the screen (after the 0.85):
  U  front x 788.5-869.9, y 590.0-671.4    opening y 552.0-590.0  (inside the crop; the main stage)
  R  front x 869.9-951.3, y 671.4-752.8    opening y 633.4-671.4  (cut on the right from 935)
  F  front x 690.0-771.5, y 749.5-830.8    opening y 711.5-749.5  (cut at the bottom from 812)
  L  front x 567.7-649.2, y 671.4-752.8    opening y 633.4-671.4  (cut on the left up to 560: its side and the left 17 px of its lid)
The colours of the new faces: F's left side light like its front, L's lid light (its front is light, its side black), both openings dark.

Lids (finesse notes 6 and 7). A lid opens in 0.55 s (33 frames), eased in and out, to 92 degrees; it shuts in 0.38 s (23), eased in and
settling into the cube, and does not bounce: a bounce lifts it off the cube and shows a sliver, and a shut lid is exactly its cube's top
(the build reads the keys back and asserts every shut lid, and the shut door, within 0.05 px of the still face; it measures 0.000). The
lids that fling the ball out (and the door) open in 0.33 s (20 frames), still eased in and out, so the ball can leave on the beat. A
fake-out lifts in 0.4 s (24), holds 0.4 s (24) and closes in 0.3 s (18). Only one lid (or the door) moves at a time, at least 0.3 s
(18 frames) from one finishing to the next starting, also across the loop's seam (asserted). Each lid opens before the ball is over it
(asserted at 60 degrees or more as the ball reaches the far edge of the opening). Two fake-outs, one a routine.

The timeline (one cycle of 909 frames, 15.15 s; times are from the scene being set, the first pass: the cycle starts at 1.83 s, once the
tops have landed, and the Loop picks it up at 3.2 s; the Finesse panel shows the same times):
  Routine 1, "nothing up my sleeve"
    1.83-2.38  U's lid opens; 2.23 the ball rises to peek (top half above the rim)
    2.68-3.78  fake-out: R's lid lifts, holds and closes while the ball, out in U, glances left, then right at it, and back
    3.88       the ball ducks (down at 4.05); U's lid shuts 4.08-4.47
    4.77-5.10  L's lid pops open and, at 4.90, the ball bursts out of L, the box nobody was watching (the lid flings it); it flies over F
    5.40-5.95  F's lid opens as the ball flies; the ball is in F at 5.92 and peeks out, glances back at L (whose lid shuts 6.25-6.63)
    6.97-7.35  F's lid shuts; 7.40-8.10 U turns 90 degrees on its vertical axis (0.5 s, a 3 degree overshoot that settles): nothing in it
    8.10-8.43  U's lid (now hinged on its right) pops; 8.23 the ball pops out with extra height (top y 441) and flies over F into L
    8.73-9.28  L's lid opens as the ball flies; the ball peeks from L while U's lid shuts 9.58-9.97; L shuts 10.30-10.68
  Routine 2, "the door"
    10.47      U turns back 90 degrees (to 11.17) while the ball, in L, is out of sight
    11.17-11.50  U's front swings open like a door on its left hinge; 11.37 the ball shoots out of it (the door flings it) and arcs into R
    11.80-12.35  R's lid opens as the ball flies; the door shuts 12.65-13.03; the ball peeks from R, glancing at the door, then at
                 F's fake-out 13.33-14.43, then springs out of R at 14.43 in a high arc (top y 446) into U
    14.73-15.28  U's lid opens as the ball flies; R's lid shuts 15.58-15.97; the ball peeks from U and ducks; U's lid shuts 16.30-16.68
  U's two turns (+90, then -90) put every cube back on its starting pose, so the loop closes on the drawing itself. U never turns with
  a lid or its door open, and the door is shut before the ball goes into U (asserted).

Hidden stretches: the longest is 77 frames (1.28 s), from the ball's duck into F to its pop out of U (F's lid shuts and U turns in it); the
longest with nothing moving is 18 frames (0.3 s, the gap between two lid moves). The ball is visible, or about to be, throughout.

Physics: one gravity, 0.40; every flight a parabola of a set length (62, 62, 56 and 58 frames), every one launched from rest by a lid, the
door or the box (they fling); every landing is a catch out of sight inside a box (it settles over 6 frames). The ball keeps the spin it
left with (a quarter of the roll its push would give); the glances are 12 to 22 degree turns of its dot in place, with a faint eased roll
of about a degree in the holds; the last hidden rest takes up the turn left over to a whole number of turns.
Squash: none on the catches (out of sight) and none at the peeks (an eased lift, arriving softly); a 3 percent stretch, volume kept, on
the pop out of U (maximum 3 percent for the fastest move), easing back by its apex.

Size: lids of one colour (R's and L's) are one face drawn from both sides; U's and F's (dark above, light below) are two. A dark opening is
drawn only while its lid is off, at the still top's place (a shut lid covers it). The vertex keys are thinned to 0.3 art units (0.255 px),
the edge of every rest kept exact; the ball's spin and sideways travel (straight lines in a flight) are thinned too.
"""
import math
import os
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

# ---- the cubes (the planes' own space, before the 0.85) ---------------------------------------------------------------------
# One viewpoint for all four: the depth goes up and to the LEFT, (-38.332, -44.682) for a 95.829 cube, as the top cube's and the
# right stack's art draws it. U and R are the art's own cubes. F (the front cube) and L (the left box) were drawn from other
# viewpoints (F up and to the right, L seen straight on and a little larger), so they are redrawn here by cube3d: the same size as
# the others, F moved right so its top clears L, L moved down onto the floor (its base's back edge on the floor line, as R's).
D3 = (-38.332, -44.682)
U = Cube("The Mini Top Cube", (795.667, 568.582, 891.496, 664.328), D3)
R = Cube("The Mini Right Stack", (891.498, 664.330, 987.327, 760.076), D3)
F = Cube("The Mini Front Cube", (679.85, 756.178, 775.679, 851.924), D3)
L = Cube("The Mini Left Box", (536.008, 664.330, 631.837, 760.076), D3)
ART_CORNERS = {                            # the drawing's own corners, for the check at PERSPECTIVE 0 (the two cubes the art draws this way)
    (U, "left"): [(757.338, 523.894), (795.67, 568.576), (795.67, 664.322), (757.338, 619.64)],
    (U, "top"): [(757.266, 523.894), (853.095, 523.894), (891.427, 568.576), (795.597, 568.576)],
    (R, "top"): [(853.097, 619.646), (948.926, 619.646), (987.257, 664.328), (891.428, 664.328)],
    (R, "left"): [(853.166, 619.646), (891.497, 664.328), (891.497, 760.074), (853.166, 715.392)],
}

# each cube is one square of the puzzle: every face one solid colour, as the illustration drew it (its fills before the 3D rebuild):
# the fronts and sides light, R's front and L's side black, the tops of U and F black and R's light. Lids and the door take
# their face's colour (their insides stay light, so an open lid reads against the dark opening). U's right face, which the
# illustration never drew and the turn shows, takes the colour of the face opposite it, its left side (light).
COL = {
    (U, "front"): LIGHT, (U, "left"): LIGHT, (U, "right"): LIGHT, (U, "back"): LIGHT, (U, "lid"): DARK,
    (R, "front"): DARK, (R, "left"): LIGHT, (R, "lid"): LIGHT,
    (F, "front"): LIGHT, (F, "left"): LIGHT, (F, "lid"): DARK,
    (L, "front"): LIGHT, (L, "left"): DARK, (L, "lid"): LIGHT,
}

# tempo (frames at 60/s). A considered pace: lids open slowly and close with weight; a lid never bounces on closing (a bounce lifts
# it off the cube and shows a sliver: a shut lid lies exactly flush).
OPEN, OPEN_N = math.radians(92), 33        # lids open to 92 degrees in 0.55 s, eased in and out (past ~98 the free edge dips back and reads as a wobble)
POP_N = 20                                 # a lid or door that flings the ball out: 0.33 s, still eased in and out
SHUT_N = 23                                # shut in 0.38 s, eased in and settling into the cube
CRACK, CRACK_UP, CRACK_HOLD, CRACK_DN = math.radians(28), 24, 24, 18    # a fake-out: lift 0.4 s, hold 0.4 s, close 0.3 s
LID_GAP = 18                               # 0.3 s between one lid (or the door) finishing and the next starting
DOOR = math.radians(90)
TURN_N, SETTLE_N, OVER = 30, 12, math.radians(3)
PEEK_N, PEEK_RISE, DUCK_N = 16, 39.2, 10   # the peek's lift (39.2 px in 0.27 s) and the duck: it pulls itself down, then drops at 0.40 (0.17 s)
GL = math.radians(12)                      # a glance
DUR = {"open": OPEN_N, "pop": POP_N, "shut": SHUT_N, "crack": CRACK_UP + CRACK_HOLD + CRACK_DN}


def S(p):
    return (A[0] + K * (p[0] - A[0]), A[1] + K * (p[1] - A[1]))


def ease_io(u):
    u = min(1.0, max(0.0, u))
    return 4 * u ** 3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2


def shut_ease(u):
    """Starts gently, speeds up, slows into the closed pose."""
    u = min(1.0, max(0.0, u))
    return smooth(u ** 1.35)


# ---- hinges and turns: an angle per cycle frame from a list of events -------------------------------------------------------
def angles(events, n, top=OPEN):
    """events: [(frame, kind)] with kind "open" (to `top` in OPEN_N), "pop" (the same in POP_N), "shut" (to 0 in SHUT_N), "crack" (up
    CRACK_UP, held CRACK_HOLD, shut CRACK_DN), or ("turn", target): a 0.5 s turn with a small overshoot that settles. Every move
    ends exactly on its pose (a shut lid is exactly 0 from then on)."""
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
                a[g] = a0 + (top - a0) * ease_io(t / OPEN_N)
            elif kind == "pop":
                a[g] = a0 + (top - a0) * ease_io(t / POP_N)
            elif kind == "shut":
                a[g] = a0 * (1 - shut_ease(t / SHUT_N))
            elif kind == "crack":
                if t < CRACK_UP:
                    a[g] = CRACK * ease_io(t / CRACK_UP)
                elif t < CRACK_UP + CRACK_HOLD:
                    a[g] = CRACK
                else:
                    a[g] = CRACK * (1 - shut_ease((t - CRACK_UP - CRACK_HOLD) / CRACK_DN))
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
    return DUR.get(kind, TURN_N + SETTLE_N)


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

    def rest_until(self, p, frame, mode="hidden"):
        assert self.now <= frame, ("the ball is already past this frame", self.now, frame)
        self.rest(p, frame - self.now, mode)

    def peek(self, p, rise_at, keys, end_at, duck=True):
        """The peek, the ball's own effort: from frame rise_at an eased lift of PEEK_RISE in PEEK_N frames (arriving softly), then it
        stays up until end_at, its glance (the turn of its dot) eased between the keys [(frame, angle)]; where two keys have the same
        angle it keeps a faint eased roll of about a degree. With duck, it then pulls itself down and drops back to p in DUCK_N
        frames (hidden at the last); without, it stays up (a fling follows). Returns the frame after."""
        assert self.now == rise_at, (self.now, rise_at)

        def glance(f):
            if f <= keys[0][0]:
                return keys[0][1]
            for (f0, a0), (f1, a1) in zip(keys, keys[1:]):
                if f0 <= f <= f1:
                    u = (f - f0) / (f1 - f0)
                    return a0 + (a1 - a0) * ease_io(u) + (math.radians(1.1) * math.sin(math.pi * u) if abs(a1 - a0) < 1e-9 and a0 != 0 else 0.0)
            return keys[-1][1]
        for t in range(1, PEEK_N + 1):
            self.put((p[0], p[1] - PEEK_RISE * smooth(t / PEEK_N)), "air", gl=glance(rise_at + t - 1))
        top = (p[0], p[1] - PEEK_RISE)
        for f in range(rise_at + PEEK_N, end_at):
            self.put(top, "rest", gl=glance(f))
        if duck:
            v0 = (PEEK_RISE - 0.5 * G * DUCK_N ** 2) / DUCK_N
            for t in range(1, DUCK_N + 1):
                self.put((p[0], top[1] + v0 * t + 0.5 * G * t * t), "air" if t < DUCK_N else "hidden", gl=glance(end_at + t - 1))
        return self.now

    def fly(self, p0, p1, catch_y, T, stretch=0.0):
        """From rest at p0 (the box flings it) to p1 in another box: a parabola at 0.40 that is T frames from launch to the frame its
        centre is at catch_y (out of sight), then 6 frames settling to p1. Returns (launch frame, the frame it is out of sight, v)."""
        vy = (catch_y - p0[1]) / T - 0.5 * G * T
        assert vy < 0, ("the flight cannot rise", vy)
        vx = (p1[0] - p0[0]) / T
        f_go = self.now
        w = 0.25 * vx / R_BALL
        for t in range(1, T + 1):
            q = (p0[0] + vx * t, p0[1] + vy * t + 0.5 * G * t * t)
            st = stretch * (smooth(t / 3) * (1 - smooth((t - 3) / 13)))
            self.put(q, "air" if t < T else "hidden", w=w, st=st)
        f_in = self.now - 1
        for k in range(1, 7):
            s_ = smooth(k / 6)
            self.put((q[0] + (p1[0] - q[0]) * s_, q[1] + (p1[1] - q[1]) * s_), "hidden")
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


def lid_off(pose):
    return pose.get("lid", 0) > 1e-9


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

    cub = {"U": U, "R": R, "F": F, "L": L}
    top_y = lambda cube: S((0.0, cube.centre[1] - cube.hy))[1]            # the front face's top edge on the screen
    IN = {k: (round(S(c.cam.project(c.centre))[0], 1), round(top_y(c) + 36, 1)) for k, c in cub.items()}    # at rest in a box: wholly behind its front and side
    IN["R"] = (902.0, IN["R"][1])                                          # right of R's left side, which is under the ball
    CATCH = {k: round(top_y(c) + 32, 1) for k, c in cub.items()}          # a centre this low is wholly out of sight
    BACK_Y = {k: min(S(q)[1] for q in c.quad("top")) for k, c in cub.items()}    # the opening's far edge

    P = Path()
    lids = {"U": [], "R": [], "F": [], "L": []}
    door, turn, sched, enters = [], [], [], []
    free = [0]

    def move(name, kind, earliest):
        """A lid (or the door) move at the first frame at or after `earliest` that keeps LID_GAP from the one before. Returns (start, end)."""
        f = max(earliest, free[0])
        n = DUR[kind]
        free[0] = f + n + LID_GAP
        (door if name == "door" else lids[name]).append((f, kind))
        sched.append((f, f + n, f"{name} {kind}"))
        return f, f + n

    def fly(src, dst, T, p0=None, stretch=0.0):
        go, f_in, v = P.fly(p0 or IN[src], IN[dst], CATCH[dst], T, stretch)
        enter = next(g for g in range(go, f_in + 1) if P.p[g][1] >= BACK_Y[dst] and g > go + T // 2)
        enters.append((dst, enter))
        return go, f_in

    # ================================================================ routine 1, "nothing up my sleeve"
    u_open = move("U", "open", 0)
    rise = u_open[1] - 9                                  # the ball starts up when the lid is most of the way open
    P.rest_until(IN["U"], rise)
    r_fake = move("R", "crack", u_open[1])                # fake-out: R lifts while the ball, out in U, watches it
    P.peek(IN["U"], rise, [(rise, 0), (rise + PEEK_N + 10, -GL), (r_fake[0] + 4, -GL), (r_fake[0] + 20, GL), (r_fake[1] - 14, GL), (r_fake[1] - 4, 0)], r_fake[1])
    u_shut = move("U", "shut", P.now + 4)
    l_pop = move("L", "pop", u_shut[1])                   # the ball is in L, the box nobody was watching
    P.rest_until(IN["U"], u_shut[1] + 6)
    P.rest_until(IN["L"], l_pop[0] + 8)
    go1, in1 = fly("L", "F", 62)
    f_open = move("F", "open", l_pop[1])                  # F opens while the ball flies
    l_shut = move("L", "shut", f_open[1])
    rise = P.now
    P.peek(IN["F"], rise, [(rise, 0), (l_shut[0] + 4, -GL), (l_shut[1] - 2, -GL), (l_shut[1] + 6, 0)], l_shut[1] + 10)
    f_shut = move("F", "shut", P.now)
    turn_at = f_shut[1] + 3
    turn.append((turn_at, ("turn", math.pi / 2)))         # the top cube turns 90 degrees: nothing up my sleeve
    P.rest_until(IN["F"], turn_at + 20)
    u_pop = move("U", "pop", turn_at + TURN_N + SETTLE_N)
    P.rest_until(IN["U"], u_pop[0] + 8)
    go2, in2 = fly("U", "L", 62, stretch=0.03)            # out of the top with extra height
    l_open = move("L", "open", u_pop[1])
    u_shut2 = move("U", "shut", l_open[1])
    rise = P.now
    P.peek(IN["L"], rise, [(rise, 0), (u_shut2[0] + 4, GL), (u_shut2[1] - 2, GL), (u_shut2[1] + 6, 0)], u_shut2[1] + 10)
    l_shut2 = move("L", "shut", P.now)

    # ================================================================ routine 2, "the door"
    turn_back = l_shut2[0] + 10
    turn.append((turn_back, ("turn", 0.0)))
    d_open = move("door", "pop", turn_back + TURN_N + SETTLE_N)     # U's front swings open like a door on its left hinge
    P.rest_until(IN["L"], turn_back + 15)
    P.rest_until(IN["U"], d_open[0] + 4)
    P.rest_until(IN["U"], d_open[0] + 12, "rest")         # the ball shows in the doorway
    go3, in3 = fly("U", "R", 56)                          # out of the door, into R
    r_open = move("R", "open", d_open[1])
    P.rest(IN["R"], 8)
    d_shut = move("door", "shut", r_open[1])
    f_fake = move("F", "crack", d_shut[1])                # fake-out: F lifts while the ball watches from R
    rise = P.now
    r_peek = (IN["R"][0], IN["R"][1] - PEEK_RISE)
    P.peek(IN["R"], rise, [(rise, 0), (d_shut[0] + 8, -GL), (d_shut[1] + 6, -GL), (f_fake[0] + 6, -1.8 * GL), (f_fake[1] - 12, -1.8 * GL), (f_fake[1] - 2, 0)], f_fake[1], duck=False)
    go4, in4 = fly("R", "U", 58, p0=r_peek)               # R flings it, high, into U
    u_open2 = move("U", "open", f_fake[1])
    r_shut = move("R", "shut", u_open2[1])
    rise = P.now
    P.peek(IN["U"], rise, [(rise, 0), (r_shut[0] + 4, GL), (r_shut[1] - 2, GL), (r_shut[1] + 6, 0)], r_shut[1] + 10)
    u_shut3 = move("U", "shut", P.now)
    Lc = u_shut3[1] + LID_GAP                             # frame Lc is frame 0 again
    P.rest_until(IN["U"], Lc)
    P.put(IN["U"], "hidden")
    assert Lc + LID_GAP - 0 >= LID_GAP

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
    # one lid (or the door) moves at a time, a gap of LID_GAP between them, also across the loop's seam
    sched.sort()
    for (s0, e0, n0), (s1, e1, n1) in zip(sched, sched[1:]):
        assert s1 - e0 >= LID_GAP, ("lids too close", n0, e0, n1, s1)
    assert sched[0][0] + Lc - sched[-1][1] >= LID_GAP
    # a lid is well open before the ball is over its opening
    lid_at_enter = []
    for dst, g in enters:
        ang = math.degrees(a_lid[dst][g])
        assert ang >= 60, ("the ball arrives over a lid that is not open yet", dst, g, ang)
        lid_at_enter.append(f"{dst} {ang:.0f} deg")
    # U never turns with a lid or its door open
    for g in range(Lc + 1):
        if abs(a_turn[g]) > 1e-6 and abs(a_turn[g] - math.pi / 2) > 1e-6:
            assert a_lid["R"][g] == 0 and a_door[g] == 0 and a_lid["U"][g] == 0, ("U turns with a lid open", g)
    # the door is shut before the ball goes into U, and U's lid is open when it does
    assert all(a_door[g] == 0 for g in range(in4 - 20, Lc + 1))

    # ---------------------------------------------------------------- the faces
    faces = {
        "front": [Face(U, "front", "door", fill=COL[(U, "front")], name=f"{U.name} Front"),
                  Face(U, "left", fill=COL[(U, "left")]), Face(U, "right", fill=COL[(U, "right")]),
                  Face(U, "back", fill=COL[(U, "back")]),
                  Face(L, "front", fill=COL[(L, "front")]), Face(L, "left", fill=COL[(L, "left")]),
                  Face(F, "front", fill=COL[(F, "front")]), Face(F, "left", fill=COL[(F, "left")])],
        "c3": [Face(R, "front", fill=COL[(R, "front")])],
        "floor": doorway(),
        # a lid has two faces only where its two sides differ in colour (U's and F's are dark above, light below); R's and L's are one
        # light face, drawn from both sides. The dark opening is drawn only while its lid is off the cube, at the still top's place
        # (a shut lid covers it, so it never needs to follow the turn).
        "c1": [Face(U, "top", "lid", fill=COL[(U, "lid")], name=f"{U.name} Lid"), Face(U, "top", "lid", flip=True, name=f"{U.name} Lid Inside"),
               Face(U, "top", fill=DARK, name=f"{U.name} Opening", fixed={}, show=lid_off),
               Face(F, "top", "lid", fill=COL[(F, "lid")], name=f"{F.name} Lid"), Face(F, "top", "lid", flip=True, name=f"{F.name} Lid Inside"),
               Face(F, "top", fill=DARK, name=f"{F.name} Opening", fixed={}, show=lid_off),
               Face(L, "top", "lid", fill=COL[(L, "lid")], name=f"{L.name} Lid", two_sided=True),
               Face(L, "top", fill=DARK, name=f"{L.name} Opening", fixed={}, show=lid_off)],
        "c4": [Face(R, "top", "lid", fill=COL[(R, "lid")], name=f"{R.name} Lid", two_sided=True),
               Face(R, "top", fill=DARK, name=f"{R.name} Opening", fixed={}, show=lid_off)],
        "floor_end": [Face(R, "left", fill=COL[(R, "left")])],
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
    seen_hidden, behind = [], {}
    for g in range(Lc + 1):
        covers = [(f.cube, [S(q) for q in f.outline(poses[key_of[f.cube]][g])]) for f in front_faces if f.visible(poses[key_of[f.cube]][g])]
        if P.mode[g] != "hidden":
            assert CROP[0] <= P.p[g][0] - R_BALL and P.p[g][0] + R_BALL <= CROP[1], ("the ball leaves the phone crop", g, P.p[g])
            if P.mode[g] == "air":                      # in the air it passes only in front of, or into the top of, the boxes
                pts = disc(P.p[g], R_BALL)
                for cube, poly in covers:
                    n_in = sum(inside(q, poly) for q in pts)
                    if n_in:
                        behind.setdefault(cube.name, []).append((g, n_in))
            continue
        bad = [q for q in disc(P.p[g], R_BALL - 0.8) if not any(inside(q, c) for _, c in covers)]
        if bad:
            seen_hidden.append((g, len(bad)))
    assert not seen_hidden, ("the ball shows when it should be hidden", seen_hidden[:8], [P.p[g] for g, _ in seen_hidden[:3]], [a_turn[g] for g, _ in seen_hidden[:3]])
    moves_at = [any(abs(arr[g + 1] - arr[g]) > 1e-9 for arr in list(a_lid.values()) + [a_door, a_turn]) for g in range(Lc)]
    longest, run, still, run2 = 0, 0, 0, 0
    for g in list(range(Lc)) * 2:
        run = run + 1 if P.mode[g] == "hidden" else 0
        run2 = run2 + 1 if P.mode[g] == "hidden" and not moves_at[g] else 0
        longest, still = max(longest, run), max(still, run2)
    if os.environ.get("MINI_DEBUG"):
        for name, spans_ in behind.items():
            print("  ball in front-plane of", name, [(g, n) for g, n in spans_][:12], "...", len(spans_), "frames")

    # ---------------------------------------------------------------- the ball's keys
    cyc = Cycle(Lc)
    for g in range(Lc + 1):
        cyc.put(g, P.p[g], "air" if P.mode[g] == "air" else "hidden")
        s_ = P.stretch[g]
        if s_:
            cyc.sy[g], cyc.sx[g] = 1 + s_, 1 / (1 + s_)
    th = [0.0]
    for g in range(Lc):
        th.append(th[-1] + P.w[g])
    total = th[Lc]
    want = round(total / (2 * math.pi)) * 2 * math.pi
    a0 = u_shut3[1] + 1                              # the last hidden rest takes up what is left over
    for g in range(a0, Lc + 1):
        th[g] += (want - total) * smooth((g - a0) / (Lc - a0))
    th = [th[g] + P.glance[g] for g in range(Lc + 1)]
    px = plane_x(scene, sheet, ROOM, "Front")

    def pre(f):
        return (IN["U"][0] + px(f), IN["U"][1]), 1.0, 1.0
    emit(doc, art, spin, cyc, th, T0, pre, pieces)

    # thin the vertex keys, but keep the edge of every rest exact so a shut lid lies exactly on its cube
    phase0 = 192 - 1 - T0
    pkey = {k: [tuple(round(v, 9) for v in p.values()) for p in ps] for k, ps in poses.items()}
    edges = set()
    for k, keys_ in pkey.items():
        for g in range(Lc + 1):
            prev_same = g > 0 and keys_[g] == keys_[g - 1]
            next_same = g < Lc and keys_[g] == keys_[g + 1]
            if (next_same and not prev_same) or (prev_same and not next_same):
                edges.add(g)
    protect_loop = {(g - phase0) % Lc + j for g in edges for j in (0, Lc) if (g - phase0) % Lc + j <= Lc}
    protect_intro = {T0 + g for g in edges if T0 + g < 192}
    wl, wi = {}, {}
    for oid, prop, fn, _own in pieces:
        if prop in ("x", "y"):
            wl[(oid, prop)] = {k: fn((phase0 + k) % Lc) for k in protect_loop}
            wi[(oid, prop)] = {f: fn(f - T0) for f in protect_intro}
    c3.ensure_keys(doc, f"{ROOM} Loop", wl)
    c3.ensure_keys(doc, f"{ROOM} Intro", wi)
    ball_thinned = 0                                 # the ball's spin and sideways travel are straight lines in a flight: a key a frame is not needed
    for an in ("Intro", "Loop"):
        ball_thinned += c3.thin_keys(doc, f"{ROOM} {an}", [spin], tol=0.003, props=("rotation",))
        ball_thinned += c3.thin_keys(doc, f"{ROOM} {an}", [art.id], tol=0.1, props=("x",))
    thinned = c3.thin_keys(doc, f"{ROOM} Intro", vertex_ids, protect=protect_intro) + c3.thin_keys(doc, f"{ROOM} Loop", vertex_ids, protect=protect_loop)

    # a shut lid (and the shut door) is exactly its cube's still face: read the keys back and compare, on every frame it rests shut
    flush, flush_at = 0.0, None
    lid_faces = [f for grp in faces.values() for f in grp if getattr(f, "part", None) in ("lid", "door") and not f.flip]
    ids_ = [vid for f in lid_faces for vid in f.shapes[0][1]]
    series = [(f"{ROOM} Loop", c3.key_values(doc, f"{ROOM} Loop", ids_), lambda g: (g - phase0) % Lc, Lc),
              (f"{ROOM} Intro", c3.key_values(doc, f"{ROOM} Intro", ids_), lambda g: T0 + g, 191)]
    for f in lid_faces:
        key = key_of[f.cube]
        ps = poses[key]
        part_key = f.part
        shut = [g for g in range(1, Lc) if ps[g] == ps[g - 1] == ps[g + 1] and ps[g][part_key] == 0]
        for g in shut:
            ref = f.cube.quad(f.face, None, ps[g])
            for _, rows, frame_of, last in series:
                for fr in {frame_of(g), frame_of(g) + (Lc if frame_of(g) == (g - phase0) % Lc else 0)}:
                    if fr > last:
                        continue
                    for vid, (rx, ry) in zip(f.shapes[0][1], ref):
                        for prop, ref_v in (("x", rx), ("y", ry)):
                            r_ = rows.get((vid, prop))
                            if r_ is not None:
                                d_ = abs(c3.value_at(r_, fr) - ref_v) * K
                                if d_ > flush:
                                    flush, flush_at = d_, (f.name, g, fr, prop, c3.value_at(r_, fr), ref_v, vid)
    assert flush < 0.05, ("a shut lid is not flush with its cube", flush)
    if os.environ.get("MINI_DEBUG"):
        print("  worst flush", flush_at)

    sec = lambda g: f"{(T0 + g) / 60:.2f} s"
    moves = ", ".join(f"{n} {sec(s0)}-{sec(e0)}" for s0, e0, n in sched)
    turns = ", ".join(f"U turn to {round(math.degrees(k[1]))} {sec(f0)}" for f0, k in turn)
    flights = "; ".join(f"{sec(a)}-{sec(b)} apex {apex:.0f} (top {apex - R_BALL:.0f}) v ({vv[0]:.2f}, {vv[1]:.2f})" for a, b, apex, vv in P.notes)
    return (f"{ROOM}: moves: {moves}; {turns}; 3D cubes (perspective {c3.PERSPECTIVE}, rest pose at 0 within {worst:.3f} of the drawing), {moving} vertex tracks keyed "
            f"({thinned} keys thinned, {ball_thinned} on the ball); shut lids flush within {flush:.3f} px; lid angle as the ball arrives: {', '.join(lid_at_enter)}; "
            f"flights: {flights}; ball top {ball_top:.0f}, pieces top {piece_top:.0f}; "
            f"longest hidden {longest} frames ({longest / 60:.2f} s), longest hidden with nothing moving {still} frames; loop {Lc / 60:.2f} s ({Lc} frames)")
