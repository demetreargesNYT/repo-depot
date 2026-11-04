"""One time (2026-11-04, round 3): Chapter 1 card 5 restaged from Figma: one cube that turns in, Wordle Bot on top, the ball's three tries.

    python3 chapters/ch1/ch1_card_5_r3.py            dry run: the beats, the contacts and the clearances
    python3 chapters/ch1/ch1_card_5_r3.py --write    rewrite chapters/ch1/scene.rml

It runs on the file as round 2 left it (commit 3596ae7: the six blocks, the bot on the floor): it removes round 2's blocks and bot, and
writes the room's Intro and Loop fresh. It refuses to run twice. The bot is read from a pull of his Rive file (2702548, read only) in
.cache/scratch.nosync/ch1/wordle-bot/.

References: Figma "Ch1 05 - Bot" (10702:73032, the layout) and "Block-Twist" (12865:62317, the cube turn).
  * The cube: one block, 200.58 x 127.5 at x 647 (Figma x 87 in the phone frame, +560), its base on the floor line; its lines 1.866
    (Figma's). It is a cube seen from an angle: its side face (O, green) is 73.08 wide and its front face (W, grey; Figma draws the same
    zigzag upside down, as an M) 127.5. No shadows. The turn is a 2D trick inside the fixed outline: four faces (D, R, O, W), each drawn
    at the block's full width and scaled sideways, masked to the block. Two faces share one vertical edge; the left face squeezes toward
    the left as it turns away and the next grows in from the right, the two always the block's width together. The edge sits at
    width x cos t / (cos t + sin t): the faces' widths in the proportion a turning cube shows them (cos t and sin t), held to the fixed
    outline. At rest t = 60.2 degrees (73.08 : 127.5). The cube comes in with the pan showing D and R, and from 0.8 s turns two quarter
    turns (through R and O) to rest on O and W at 1.35 s. Every line keeps its weight while the faces scale (transformAffectsStroke off).
  * Wordle Bot, at Figma's size (body 137 wide, scale 6.2169; his feet on the cube's top, centred on it as in Figma), drops from 1.35 s
    with his Drop In - Foot Tap and lands at 1.9 s. His lines are 2.326, Figma's at his Figma size, and stay that weight through his
    squash and the tile flips. His antennas are behind his dome, so the dome covers their base. His screen tiles are Figma's: green
    #77A76A, yellow #E9C342, grey #787C7E (his Idle's slow colour crossfades, which made them look muddy, are gone).
  * The ball (radius 17, as in cards 2 to 4), "three tries": it waits on the floor left of the cube until he has landed. Try 1: a hop that
    hits the cube's face and drops back (the cube gives a little; his first tile flips to grey). Try 2: a bigger hop that clips the cube's
    top corner and falls back (his second tile flips to yellow). Try 3: it lands on top beside his left shoe; his three tiles flip to green
    one after another and his foot tap follows. A beat, then it rolls off the back of the cube and drops out of sight behind it; hidden, it
    is put back behind the cube's base, his tiles flip back to their resting colours, and it rolls out from behind the cube's left side to
    its spot. Every flight is a parabola at 0.40; contacts keep 70 to 90 percent of their speed.
Times in the notes are Finesse-panel timecodes (from the moment the scene is set; the loop starts at 3.2 s).
"""
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

RIVE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RIVE_ROOT / "tools"))

import ch1_cards_234 as c234                                                    # noqa: E402
from ch1_cards_234 import Ball, INTRO, emit_room, round_ball, dip, phone_y, COPY_BOTTOM   # noqa: E402
from ball_motion import smooth                                                  # noqa: E402
from rml_edit import Doc, num                                                   # noqa: E402

SCENE = RIVE_ROOT / "chapters" / "ch1" / "scene.rml"
BOT_FILE = RIVE_ROOT / ".cache" / "scratch.nosync" / "ch1" / "wordle-bot" / "scene.rml"
ROOM = "Chapter 1 Card 5"
INK = "FF1F1F1F"

# ---- the cube (artboard units; Figma phone frame x + 560) ---------------------------------------------------------------------
X0, Y0, W, H = 647.0, 584.18, 200.58, 127.5
CUBE_LINE = 1.8659
SIDE = 73.08
T_REST = math.degrees(math.atan2(W - SIDE, SIDE))          # 60.2: the rest pose's turn
TURN = (48, 81)                                            # intro frames of the two quarter turns (0.8 to 1.35 s)
# the faces in the order the turn shows them: (name, fill, letter shape id, letter's share of the face's width, letter height)
FACES = [("D", "FFE4E93B", "9:12197", 0.598, 83.0), ("R", "FFDFDBD7", "9:12184", 0.50, 84.0),
         ("O", "FF05CE7C", "9:12300", 0.535, 90.31), ("W", "FFDFDBD7", "9:12291", 0.625, 86.63)]
FIRST = -2                                                 # the index of the first face (D); O is 0

# ---- the bot ----------------------------------------------------------------------------------------------------------------
K = 137.0 / 22.0366                                        # Figma body width / his body's width in his own units
LINE = 2.3258                                              # Figma's line at his Figma size (he is that size here)
FEET = 33.642
BOT_CX = 119.0 + 68.5 + 560.0                              # Figma body centre x
BOT_X = BOT_CX - K * 17.709
BOT_Y = Y0 - K * FEET                                      # feet on the cube's top line
BOT_Y0 = -230.0
BOT_IN = TURN[1]                                           # his drop starts as the turn settles; lands 33 frames later (1.9 s)
BODY = (BOT_CX - K * 11.018, BOT_Y + K * 6.079, BOT_CX + K * 11.018, BOT_Y + K * 26.403)
HEAD = (BOT_CX + K * 0.351, BOT_Y + K * 0.23)              # dome centre x, antenna tips' top
SHOE_LEFT = BOT_CX + K * (13.53 - 17.709) - K * 3.70 - 0.75 * 0   # his left shoe's left edge (centreline)
TILES = {"left": "FF77A76A", "middle": "FFE9C342", "right": "FF787C7E"}
GREY, YELLOW, GREEN = "FF787C7E", "FFE9C342", "FF77A76A"

# ---- the ball -------------------------------------------------------------------------------------------------------------
RB = 17.1
R_VIS = 17.7
G = 0.40
FLOOR_C = 712.0 - RB
HOME = 605.0
HIDE_X = X0 + 23.0                                         # where it waits out of sight, behind the cube's base
T0, PS = 3, 100
T1 = 132                                                   # try 1 starts (2.25 s): he landed at 1.9 s and settled at 2.15 s
PAUSE = 40                                                 # gathering itself between tries
BEAT = 72                                                  # on top, while his tiles go green and he cheers
HIDDEN, N_OUT, HOME_WAIT = 54, 46, 46
E_N, E_T = 0.80, 0.95                                      # restitution along the contact normal, and along the surface
BUBBLE_BOTTOM = 365.0                                      # the speech bubble's lowest edge (Figma 367, in artboard units on the phone)

BLOCK = (X0, Y0, X0 + W, Y0 + H)


def rect_dist(p, r):
    dx = max(r[0] - p[0], 0.0, p[0] - r[2])
    dy = max(r[1] - p[1], 0.0, p[1] - r[3])
    return math.hypot(dx, dy)


def closest(p, r):
    return (min(max(p[0], r[0]), r[2]), min(max(p[1], r[1]), r[3]))


def flight(p0, v0, t):
    return (p0[0] + v0[0] * t, p0[1] + v0[1] * t + 0.5 * G * t * t)


def fly(p0, v0, t_max=200.0):
    """The first contact of a flight from p0 with v0: with the cube (RB from its lines) or the floor. (t, point, kind, normal)."""
    t = 0.0
    step = 0.02
    while t < t_max:
        t += step
        p = flight(p0, v0, t)
        if p[1] >= FLOOR_C:
            lo, hi = t - step, t                          # refine
            for _ in range(30):
                mid = (lo + hi) / 2
                (lo, hi) = (lo, mid) if flight(p0, v0, mid)[1] >= FLOOR_C else (mid, hi)
            p = flight(p0, v0, hi)
            return hi, (p[0], FLOOR_C), "floor", (0.0, -1.0)
        if rect_dist(p, BLOCK) <= RB:
            lo, hi = t - step, t
            for _ in range(30):
                mid = (lo + hi) / 2
                (lo, hi) = (lo, mid) if rect_dist(flight(p0, v0, mid), BLOCK) <= RB else (mid, hi)
            p = flight(p0, v0, hi)
            q = closest(p, BLOCK)
            d = math.dist(p, q)
            n = ((p[0] - q[0]) / d, (p[1] - q[1]) / d)
            kind = "top" if abs(n[1] + 1) < 1e-3 else "face" if abs(n[0] + 1) < 1e-3 else "corner"
            return hi, p, kind, n
    raise SystemExit(f"no contact from {p0} {v0}")


def bounce(v, n):
    vn = v[0] * n[0] + v[1] * n[1]
    vt = (v[0] - vn * n[0], v[1] - vn * n[1])
    return (vt[0] * E_T - E_N * vn * n[0], vt[1] * E_T - E_N * vn * n[1])


def vel(v0, t):
    return (v0[0], v0[1] + G * t)


class Track:
    """The ball's centre in continuous time (frames), built segment by segment, sampled on whole frames afterwards."""

    def __init__(self):
        self.segs = []                                   # (t0, t1, fn(t) -> (x, y), mode)
        self.t = 0.0
        self.events = {}

    def add(self, dur, fn, mode):
        self.segs.append((self.t, self.t + dur, fn, mode))
        self.t += dur

    def rest(self, p, dur):
        self.add(dur, lambda t, p=p: p, "rest")

    def at(self, t):
        for t0, t1, fn, mode in self.segs:
            if t0 <= t <= t1:
                return fn(t - t0), mode
        return self.segs[-1][2](self.segs[-1][1] - self.segs[-1][0]), "rest"


def floor_roll(tr, x0, v0, n):
    """After a landing: rolls on the floor at v0, slowing evenly to rest in n frames. Returns where it stops."""
    a = v0 / n
    tr.add(n, lambda t: (x0 + v0 * t - 0.5 * a * t * t, FLOOR_C), "roll")
    return x0 + 0.5 * v0 * n


def hop(tr, p0, v0, want, name, notes):
    """A flight from p0 at v0 to its first contact; checks it is the contact wanted. Returns (t, point, normal, velocity in)."""
    t, p, kind, n = fly(p0, v0)
    assert kind == want, (name, kind, p)
    tr.add(t, lambda u, p0=p0, v0=v0: flight(p0, v0, u), "air")
    pts = [flight(p0, v0, u) for u in [i * 0.25 for i in range(int(t * 4) + 1)]]
    top = min(q[1] for q in pts) - R_VIS
    clear_bot = min(rect_dist(q, BODY) for q in pts) - R_VIS
    notes.append((name, tr.t, kind, p, top, clear_bot))
    return t, p, n, vel(v0, t)


def ball_track():
    tr = Track()
    notes = []
    tr.rest((HOME, FLOOR_C), T1)
    # ---- try 1: hits the face, drops back ----
    _, p, n, v = hop(tr, (HOME, FLOOR_C), (1.6, -7.2), "face", "try 1", notes)
    tr.events["hit1"] = tr.t
    vo = bounce(v, n)
    k1 = math.hypot(*vo) / math.hypot(*v)
    _, p2, _, v2 = hop(tr, p, vo, "floor", "try 1 back", notes)
    tr.events["land1"] = tr.t
    s2 = floor_roll(tr, p2[0], v2[0] * 0.8, 16)
    tr.rest((s2, FLOOR_C), PAUSE)
    # ---- try 2: clips the top corner, falls back ----
    best, score = None, None
    for i in range(0, 600):                               # the corner hit that throws it back near its spot (x 605)
        vx = 0.6 + i * 0.0025
        t, q, kind, nn = fly((s2, FLOOR_C), (vx, -10.4))
        if kind != "corner":
            continue
        vi = vel((vx, -10.4), t)
        vo = bounce(vi, nn)
        keep = math.hypot(*vo) / math.hypot(*vi)
        t2, q2, k2, _ = fly(q, vo)
        if k2 == "floor" and 0.72 <= keep <= 0.9 and vo[0] < 0 and (score is None or abs(q2[0] - HOME) < score):
            best, score = vx, abs(q2[0] - HOME)
    assert best, "no corner hit for try 2"
    tr.events["try2"] = tr.t
    _, p, n, v = hop(tr, (s2, FLOOR_C), (best, -10.4), "corner", "try 2", notes)
    tr.events["hit2"] = tr.t
    vo = bounce(v, n)
    k2 = math.hypot(*vo) / math.hypot(*v)
    _, p3, _, v3 = hop(tr, p, vo, "floor", "try 2 back", notes)
    tr.events["land2"] = tr.t
    s3 = floor_roll(tr, p3[0], v3[0] * 0.8, 16)
    tr.rest((s3, FLOOR_C), PAUSE // 2)
    run = 585.0                                           # it backs up for a run-up: gathering itself for the last try
    tr.add(28, lambda u, s3=s3: (s3 + (run - s3) * smooth(u / 28), FLOOR_C), "roll")
    s3 = run
    tr.rest((s3, FLOOR_C), PAUSE // 2)
    # ---- try 3: lands on top beside his left shoe ----
    target = X0 + 26.0
    sol = None
    for i in range(0, 300):
        vy = -11.0 - i * 0.01
        lo, hi = 0.5, 4.0
        for _ in range(40):                               # the vx that lands it at the target
            mid = (lo + hi) / 2
            t, q, kind, nn = fly((s3, FLOOR_C), (mid, vy))
            if kind != "top" or q[0] < target:
                lo = mid
            else:
                hi = mid
        t, q, kind, nn = fly((s3, FLOOR_C), (hi, vy))
        pts = [flight((s3, FLOOR_C), (hi, vy), u * 0.25) for u in range(int(t * 4) + 1)]
        if kind == "top" and abs(q[0] - target) < 1.0 and min(rect_dist(z, BLOCK) for z in pts[:-8]) >= RB + 2.0 \
                and min(rect_dist(z, BODY) for z in pts) >= R_VIS + 2.0:
            sol = (hi, vy)
            break
    assert sol, "no landing on top for try 3"
    tr.events["try3"] = tr.t
    _, p, n, v = hop(tr, (s3, FLOOR_C), sol, "top", "try 3", notes)
    tr.events["land3"] = tr.t
    top_c = (p[0], Y0 - RB)
    tr.rest(top_c, BEAT)
    # ---- off the back: it drops behind the cube's top edge ----
    tr.events["off"] = tr.t
    u_hid = math.sqrt(2 * (Y0 + CUBE_LINE / 2 + R_VIS - top_c[1]) / G)     # its top below the cube's top line
    n_drop = math.ceil(u_hid) + 2                         # two frames more, so the whole frame it is put back on is out of sight
    tr.add(n_drop, lambda u: (top_c[0], top_c[1] + 0.5 * G * u * u), "air")
    tr.events["hidden"] = tr.t
    tr.rest((HIDE_X, FLOOR_C), HIDDEN)
    tr.events["out"] = tr.t
    tr.add(N_OUT, lambda u: (HIDE_X + (HOME - HIDE_X) * smooth(u / N_OUT), FLOOR_C), "roll")
    tr.events["home"] = tr.t
    L = math.ceil(tr.t) + HOME_WAIT - (T1 - PS)
    tr.rest((HOME, FLOOR_C), L - tr.t + 1)
    return tr, L, notes, (k1, k2)


def to_ball(tr, L):
    b = Ball(L)
    for f in range(L + 1):
        c, m = tr.at(float(f))
        if f < L:
            b.put(f, c, m)
        else:
            b.c[L] = b.c[PS]
    for f in range(L):
        moves = math.dist(b.c[f + 1], b.c[f]) > 1e-9
        if not moves:
            b.mode[f] = "rest"
        elif b.mode[f] == "rest":
            b.mode[f] = tr.at(f + 0.5)[1]
    jump = math.floor(tr.events["hidden"])               # the drop's last whole frame, already out of sight
    b.mode[jump] = "rest"                                 # put back out of sight: no turn
    for key in ("land1", "land2", "land3"):
        b.squash(math.ceil(tr.events[key]), 0.05)
    return b, jump


def spin(b, tr, L, jump):
    theta = b.spin(r=16.9)
    turns = theta[L] - theta[PS]
    left = round(turns / (2 * math.pi)) * 2 * math.pi - turns
    h0, h1 = jump + 2, math.floor(tr.events["out"])
    for t in range(h0, L + 1):
        theta[t] += left * (smooth((t - h0) / (h1 - h0)) if t < h1 else 1.0)
    return theta, left


def loop_frame(t, L):
    return (t - (INTRO - 1 - T0)) % (L - PS)


# ---- the cube's faces ------------------------------------------------------------------------------------------------------------
def ease(u):
    u = min(1.0, max(0.0, u))
    return 4 * u ** 3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2


def phi_at(f):
    return T_REST - 180.0 + 180.0 * ease((f - TURN[0]) / (TURN[1] - TURN[0]))


def faces_at(phi):
    """{face index: (x, scaleX)} for a turn of phi degrees (O at index 0)."""
    i = math.floor(phi / 90.0 + 1e-9)
    th = math.radians(phi - 90.0 * i)
    c, s = math.cos(th), math.sin(th)
    e = W * c / (c + s)
    out = {}
    for k in range(FIRST, FIRST + len(FACES)):
        if k < i:
            out[k] = (X0, 0.0)
        elif k == i:
            out[k] = (X0, e / W)
        elif k == i + 1:
            out[k] = (X0 + e, (W - e) / W)
        else:
            out[k] = (X0 + W, 0.0)
    return out


# ---- RML text -----------------------------------------------------------------------------------------------------------------
def ser(e, ind):
    pad = " " * ind
    attrs = "".join(f' {k}="{v}"' for k, v in e.attrib.items())
    kids = list(e)
    if not kids:
        return [f"{pad}<{e.tag}{attrs}/>"]
    out = [f"{pad}<{e.tag}{attrs}>"]
    for c in kids:
        out += ser(c, ind + 4)
    return out + [f"{pad}</{e.tag}>"]


def el(tag, **a):
    e = ET.Element(tag)
    for k, v in a.items():
        e.set(k, v if isinstance(v, str) else num(v))
    return e


class Build:
    def __init__(self, doc):
        self.doc = doc

    def nid(self):
        return self.doc.new_id()

    def stroke(self, w, cap="round"):
        s = el("Stroke", transformAffectsStroke="false", thickness=w, cap=cap, join="round", id=self.nid())
        s.append(el("SolidColor", colorValue=INK if w == CUBE_LINE else "FF000000", id=self.nid()))
        return s

    def fill(self, colour):
        f = el("Fill", id=self.nid())
        f.append(el("SolidColor", colorValue=colour, id=self.nid()))
        return f

    def path(self, pts, closed=True, radius=None):
        p = el("PointsPath", isClosed="true" if closed else "false", id=self.nid())
        vids = []
        for i, (x, y) in enumerate(pts):
            v = el("StraightVertex", x=x, y=y, id=self.nid())
            if radius and radius.get(i):
                v.set("radius", num(radius[i]))
            p.append(v)
            vids.append(v.get("id"))
        return p, vids

    def copy(self, e):
        c = ET.fromstring(ET.tostring(e))
        for x in c.iter():
            if x.get("id"):
                x.set("id", self.nid())
        return c


def letter_bounds(shape):
    xs, ys = [], []
    for p in shape:
        if p.tag == "Ellipse":
            w, h = float(p.get("width")), float(p.get("height"))
            xs += [-w / 2, w / 2]
            ys += [-h / 2, h / 2]
        elif p.tag == "PointsPath":
            for v in p:
                xs.append(float(v.get("x", 0)))
                ys.append(float(v.get("y", 0)))
    return min(xs), max(xs), min(ys), max(ys)


def cube(bd, scene_root):
    """The cube's node: a pivot on its right foot (for the give), its Art, the outline on top, the four faces, the mask last."""
    by_id = {e.get("id"): e for e in scene_root.iter() if e.get("id")}
    piv = el("Node", x=X0 + W, y=Y0 + H, name=f"{ROOM} Cube", id=bd.nid())
    art = el("Node", x=-(X0 + W), y=-(Y0 + H), name=f"{ROOM} Cube Art", id=bd.nid())
    piv.append(art)
    clip_id = bd.nid()
    outline = el("Shape", name=f"{ROOM} Cube Outline", id=bd.nid())
    outline.append(bd.path([(X0, Y0), (X0 + W, Y0), (X0 + W, Y0 + H), (X0, Y0 + H)])[0])
    outline.append(bd.stroke(CUBE_LINE, cap="butt"))
    art.append(outline)
    face_ids = {}
    for k, (name, colour, sid, share, lh) in enumerate(FACES):
        idx = FIRST + k
        fx, fsx = faces_at(phi_at(0))[idx]
        node = el("Node", x=fx, y=Y0, scaleX=max(fsx, 0.0), name=f"{ROOM} Face {name}", id=bd.nid())
        src = by_id[sid]
        x0, x1, y0, y1 = letter_bounds(src)
        lw, lh0 = x1 - x0, y1 - y0
        wrap = el("Node", x=W / 2, y=H / 2 + 1.6, scaleX=share * W / lw, scaleY=lh / lh0, name=f"{ROOM} Face {name} Letter", id=bd.nid())
        sh = el("Shape", x=-(x0 + x1) / 2, y=-(y0 + y1) / 2, id=bd.nid())
        for p in src:
            if p.tag in ("PointsPath", "Ellipse"):
                sh.append(bd.copy(p))
        sh.append(bd.stroke(CUBE_LINE))
        sh.append(el("ClippingShape", sourceId=clip_id, name="Cube Clip", id=bd.nid()))
        wrap.append(sh)
        node.append(wrap)
        face = el("Shape", name=f"{ROOM} Face {name} Fill", id=bd.nid())
        face.append(bd.path([(0, 0), (W, 0), (W, H), (0, H)])[0])
        face.append(bd.fill(colour))
        face.append(bd.stroke(CUBE_LINE, cap="butt"))
        face.append(el("ClippingShape", sourceId=clip_id, name="Cube Clip", id=bd.nid()))
        node.append(face)
        art.append(node)
        face_ids[idx] = node.get("id")
    clip = el("Shape", name=f"{ROOM} Cube Clip", id=clip_id)
    clip.append(bd.path([(X0 - 1.2, Y0 - 1.2), (X0 + W + 1.2, Y0 - 1.2), (X0 + W + 1.2, Y0 + H + 1.2), (X0 - 1.2, Y0 + H + 1.2)])[0])
    art.append(clip)
    return piv, face_ids


class Bot(Build):
    """His art from the Wordle Bot file, rebuilt at Figma's size and line weight."""

    def __init__(self, doc):
        super().__init__(doc)
        self.src = ET.parse(BOT_FILE).getroot()
        self.ids = {}
        self.toe = []

    def nid(self, old=None):
        i = self.doc.new_id()
        if old:
            self.ids[old] = i
        return i

    def stroke(self, w=LINE, cap="round"):
        s = el("Stroke", transformAffectsStroke="false", thickness=w, cap=cap, join="round", id=self.nid())
        s.append(el("SolidColor", colorValue="FF000000", id=self.nid()))
        return s

    def antenna(self, sh, half):
        path = sh.find("PointsPath")
        ox, oy = float(path.get("x", 0)), float(path.get("y", 0))
        for c in list(sh):
            sh.remove(c)
        sh.append(self.path([(ox - half[0], oy - half[1]), (ox + half[0], oy + half[1])], closed=False)[0])
        sh.append(self.stroke())

    def foot(self, node, ox, oy, mirror, legs, lift):
        m = -1.0 if mirror else 1.0
        for c in list(node):
            node.remove(c)
        X = lambda x: m * x
        upper, uv = self.path([(X(-3.699), -2.863), (X(1.550), -2.863), (X(1.550), -1.558), (X(3.699), 0.717), (X(3.699), 1.551),
                               (X(-3.699), 1.551)])
        sole, sv = self.path([(X(-3.699), 1.551), (X(3.699), 1.551), (X(3.699), 2.863), (X(-3.699), 2.863)], radius={2: 0.24})
        lines = [self.path([(lx, y0), (lx, -2.863)], closed=False)[0] for lx, y0 in legs]
        lace1, l1 = self.path([(X(-1.790), 0.0), (X(1.072), 0.0)], closed=False)
        lace2, l2 = self.path([(X(-1.791), -1.193), (X(0.117), -1.193)], closed=False)
        side = node.get("name").split()[-2]
        for nm, paths, paints in ((f"{ROOM} Bot {side} Shoe Lines", lines + [lace1, lace2], [self.stroke()]),
                                  (f"{ROOM} Bot {side} Shoe", [upper], [self.fill("FFE9C342"), self.stroke()]),
                                  (f"{ROOM} Bot {side} Sole", [sole], [self.fill("FFFFFFFF"), self.stroke()])):
            s = el("Shape", x=ox, y=oy, name=nm, id=self.nid())
            for p in paths + paints:
                s.append(p)
            node.append(s)
        if lift:
            toe = 1.022
            self.toe += [(uv[3], 0.717, 0.717 - toe), (uv[4], 1.551, 1.551 - toe), (sv[1], 1.551, 1.551 - toe), (sv[2], 2.863, 2.863 - toe),
                         (l1[1], 0.0, -0.51), (l2[1], -1.193, -1.193 - 0.2554)]

    def build(self):
        wb = next(e for e in self.src.iter("Node") if e.get("name") == "Wordle Bot")
        wb = ET.fromstring(ET.tostring(wb))
        for e in wb.iter():
            if e.get("id"):
                e.set("id", self.nid(e.get("id")))
            if e.get("name") in ("Component", "Path", "Fill 1", "Stroke 1"):
                del e.attrib["name"]
            if e.tag == "Stroke":                         # every line at Figma's weight, whatever the scale or squash
                e.set("thickness", num(LINE))
                e.set("transformAffectsStroke", "false")
        wb.set("name", f"{ROOM} Bot")
        wb.set("x", num(BOT_X))
        wb.set("y", num(BOT_Y))
        wb.set("scaleX", num(K))
        wb.set("scaleY", num(K))
        names = {"Body": "Body", "Right Foot": "Right Foot", "Left Foot": "Left Foot", "left antennae": "Left Antenna",
                 "right antennae": "Right Antenna", "middle": "Tile Middle", "right": "Tile Right", "left": "Tile Left", "Rectangle": "Case"}
        for e in wb.iter():
            if e.tag in ("Node", "Shape") and e.get("name") in names:
                e.set("name", f"{ROOM} Bot {names[e.get('name')]}")
        body = next(e for e in wb if e.get("name") == f"{ROOM} Bot Body")
        ants = []
        for sh in list(body.findall("Shape")):
            if sh.get("name") == f"{ROOM} Bot Left Antenna":
                self.antenna(sh, (-1.680, 1.540))
                ants.append(sh)
            elif sh.get("name") == f"{ROOM} Bot Right Antenna":
                self.antenna(sh, (-1.600, -1.739))
                ants.append(sh)
        for sh in ants:                                   # behind the dome (the body's last child is drawn at the back)
            body.remove(sh)
            body.append(sh)
        for side, colour in TILES.items():                # Figma's tile colours
            tile = next(e for e in body if e.get("name") == f"{ROOM} Bot Tile {side.title()}")
            tile.find("Fill").find("SolidColor").set("colorValue", colour)
        rf = next(e for e in wb if e.get("name") == f"{ROOM} Bot Right Foot")
        lf = next(e for e in wb if e.get("name") == f"{ROOM} Bot Left Foot")
        self.foot(rf, 1.1181529, 4.2789497, False, [(-3.342, -4.414), (0.713, -4.414)], True)
        self.foot(lf, -0.97410905, 4.7793708, True, [(3.246, -4.653), (-0.787, -4.653)], False)
        self.node = wb
        self.tile_shape = {s: self.ids[i] for s, i in (("left", "6:2713"), ("middle", "6:2691"), ("right", "6:2701"))}
        self.tile_colour = {s: self.ids[i] for s, i in (("left", "6:2722"), ("middle", "6:2698"), ("right", "6:2710"))}
        return wb

    def anim(self, name):
        return next(a for a in self.src.iter("LinearAnimation") if a.get("name") == name)

    def keyed(self, anim, frame_shift, value_map=None):
        out = []
        live = {e.get("id") for e in self.node.iter()}
        for ko in anim.findall("KeyedObject"):
            oid = ko.get("objectId")
            if self.ids.get(oid) not in live:
                continue
            for kp in ko.findall("KeyedProperty"):
                keys = []
                for k in kp:
                    k = ET.fromstring(ET.tostring(k))
                    k.set("frame", str(int(k.get("frame", 0)) + frame_shift))
                    if value_map and (oid, kp.get("property")) in value_map:
                        k.set("value", num(value_map[(oid, kp.get("property"))](float(k.get("value", 0)))))
                    for e in k.iter():
                        if e.get("id"):
                            e.set("id", self.doc.new_id())
                    keys.append(k)
                out.append((self.ids[oid], kp.get("property"), keys))
        return out


def keyed_lines(doc, objs, pad=12):
    by = {}
    for oid, prop, keys in objs:
        by.setdefault(oid, {}).setdefault(prop, []).extend(keys)
    out = []
    for oid, props in by.items():
        out.append(f'{" " * pad}<KeyedObject objectId="{oid}" id="{doc.new_id()}">')
        for prop, keys in props.items():
            out.append(f'{" " * (pad + 4)}<KeyedProperty property="{prop}" id="{doc.new_id()}">')
            seen = set()
            for k in sorted(keys, key=lambda k: int(k.get("frame", 0))):
                f = int(k.get("frame", 0))
                assert f not in seen, (oid, prop, f)
                seen.add(f)
                if not k.get("id"):
                    k.set("id", doc.new_id())
                if f == 0:
                    k.attrib.pop("frame", None)
                if k.get("value") == "0":
                    del k.attrib["value"]
                out += ser(k, pad + 8)
            out.append(f'{" " * (pad + 4)}</KeyedProperty>')
        out.append(f'{" " * pad}</KeyedObject>')
    return out


def add_keys(doc, anim_name, objs):
    _, b = doc.anim(anim_name)
    doc.lines[b:b] = keyed_lines(doc, objs)


def pose(doc, src_name, dst_name, last):
    a, b = doc.anim(src_name)
    root = ET.fromstring("\n".join(doc.lines[a:b + 1]))
    objs = []
    for ko in root.findall("KeyedObject"):
        for kp in ko.findall("KeyedProperty"):
            keys = sorted([k for k in kp if k.tag.startswith("KeyFrame")], key=lambda k: int(k.get("frame", 0)))
            k = keys[-1] if last else keys[0]
            objs.append((ko.get("objectId"), kp.get("property"), [el(k.tag, **({"value": k.get("value")} if k.get("value") else {}))]))
    doc.clear(dst_name)
    add_keys(doc, dst_name, objs)


def doubles(values, frames):
    """Keys for a per-frame curve, one linear key per frame, a flat run kept only at its ends."""
    fs = list(frames)
    keys = []
    for i, f in enumerate(fs):
        v = values[f]
        prev = values[fs[i - 1]] if i else None
        nxt = values[fs[i + 1]] if i + 1 < len(fs) else None
        if prev is not None and nxt is not None and abs(v - prev) < 1e-4 and abs(v - nxt) < 1e-4:
            continue
        keys.append(el("KeyFrameDouble", value=v, interpolationType="linear", frame=str(f)))
    return keys


def colour_keys(fn, L):
    """Hold keys for a colour that steps in cycle time: (intro keys, loop keys)."""
    ik = [el("KeyFrameColor", value=fn(0), frame="0")]
    prev = fn(0)
    for f in range(T0, INTRO):
        c = fn(f - T0)
        if c != prev:
            ik.append(el("KeyFrameColor", value=c, frame=str(f)))
            prev = c
    lp = L - PS
    lk = [el("KeyFrameColor", value=fn(INTRO - 1 - T0), frame="0")]
    prev = fn(INTRO - 1 - T0)
    for k in range(1, lp + 1):
        t = PS + ((INTRO - 1 - T0 - PS + k) % lp)
        c = fn(t)
        if c != prev:
            lk.append(el("KeyFrameColor", value=c, frame=str(k)))
            prev = c
    if lk[-1].get("frame") != str(lp):
        lk.append(el("KeyFrameColor", value=prev, frame=str(lp)))
    assert lk[0].get("value") == lk[-1].get("value")
    return ik, lk


def main(argv):
    write = "--write" in argv
    doc = Doc(SCENE)
    if any(f'name="{ROOM} Cube"' in l for l in doc.lines):
        raise SystemExit(f"{ROOM} already has the cube: run this on the file as round 2 left it (see the docstring)")
    tr, L, notes, (k1, k2) = ball_track()
    b, jump = to_ball(tr, L)
    theta, left = spin(b, tr, L, jump)
    lf = lambda t: loop_frame(t, L)
    tc = lambda t: (t + T0) / 60 if t + T0 < INTRO else 3.2 + lf(round(t)) / 60
    ev = {k: v for k, v in tr.events.items()}
    seam = INTRO - 1 - T0
    assert ev["land1"] + 16 < seam < ev["try2"], ("the loop's seam must fall in the pause after try 1", ev["land1"], ev["try2"])
    # the bot's tiles and his cheer, in cycle frames
    flips = []                                        # (tile, start, colour after)
    hit1, hit2, land3, hid = round(ev["hit1"]), round(ev["hit2"]), round(ev["land3"]), round(ev["hidden"])
    flips += [("left", hit1 + 4, GREY), ("middle", hit2 + 4, YELLOW)]
    flips += [("left", land3 + 3, GREEN), ("middle", land3 + 11, GREEN), ("right", land3 + 19, GREEN)]
    flips += [("left", hid + 6, TILES["left"]), ("middle", hid + 14, TILES["middle"]), ("right", hid + 22, TILES["right"])]
    FLIP = 10
    cheer = (land3 + 34, land3 + 52)
    print(f"{ROOM}: cycle {L} frames, the loop repeats cycle {PS} to {L} ({(L - PS) / 60:.2f} s), the journey starts at intro frame {T0}")
    print(f"  cube: x {X0} to {X0 + W:.2f}, y {Y0} to {Y0 + H:.2f}, rest turn {T_REST:.1f} degrees, turns at {TURN[0] / 60:.2f} to {TURN[1] / 60:.2f} s")
    print(f"  bot: scale {K:.4f}, body x {BODY[0]:.1f} to {BODY[2]:.1f}, y {BODY[1]:.1f} to {BODY[3]:.1f}; head x {HEAD[0]:.1f}, antenna tips y "
          f"{HEAD[1]:.1f}; drop {BOT_IN / 60:.2f} s, lands {(BOT_IN + 33) / 60:.2f} s; line {LINE}")
    for name, t, kind, p, top, cb in notes:
        print(f"  {name:11s} contact ({kind}) at cycle {t:6.1f}, timecode {tc(t):5.2f} s, centre ({p[0]:.1f}, {p[1]:.1f}); "
              f"its top y {top:.1f}; clear of the bot by {cb:.1f}")
    print(f"  contacts keep: try 1 {k1:.0%}, try 2 {k2:.0%}")
    for k in ("try2", "try3", "off", "hidden", "out", "home"):
        print(f"  {k:7s} cycle {ev[k]:6.1f}  timecode {tc(ev[k]):5.2f} s")
    print(f"  flips: " + ", ".join(f"{s} {tc(t0):.2f} s" for s, t0, _ in flips) + f"; cheer {tc(cheer[0]):.2f} s")
    xs = [c[0] for c in b.c.values()]
    print(f"  ball x {min(xs) - R_VIS:.1f} to {max(xs) + R_VIS:.1f}; its highest point y {min(c[1] for c in b.c.values()) - R_VIS:.1f} "
          f"(the bubble's lowest edge {BUBBLE_BOTTOM}); turn taken up out of sight {left:+.2f} rad")
    hidden_ok = all(rect_dist(b.c[f], BLOCK) == 0 and b.c[f][1] - R_VIS >= Y0 for f in range(jump, math.floor(ev["out"]) + 1)) \
        or all((X0 + R_VIS <= b.c[f][0] <= X0 + W - R_VIS and b.c[f][1] - R_VIS >= Y0 + CUBE_LINE / 2) for f in range(jump, math.floor(ev["out"]) + 1))
    print(f"  hidden behind the cube from the drop to rolling out: {'yes' if hidden_ok else 'NO'}")
    assert hidden_ok
    if not write:
        return 0

    root = ET.fromstring("\n".join(doc.lines))
    intro, loop = f"{ROOM} Intro", f"{ROOM} Loop"
    # ---- out with round 2: its blocks, its bot, its keys (the planes' pan is kept) ----
    a, z = doc.anim(intro)
    plane_lines = []
    for oid in ("9:12733", "9:12734"):
        o = doc._object(a, z, oid)
        plane_lines += doc.lines[o[0]:o[1] + 1]
    for name in ("Blocks", "Bot"):
        i = next(n for n, l in enumerate(doc.lines) if f'name="{ROOM} {name}"' in l and "<Node" in l)
        del doc.lines[i:doc.end(i) + 1]
    doc.clear(intro)
    doc.clear(loop)
    _, z = doc.anim(intro)
    doc.lines[z:z] = plane_lines
    # ---- the cube and the bot in the front plane: the bot first (over the cube), the cube behind him ----
    bd = Build(doc)
    cube_node, face_ids = cube(bd, root)
    bot = Bot(doc)
    bot_node = bot.build()
    i = doc.idx("9:12734")
    ind = len(doc.lines[i]) - len(doc.lines[i].lstrip()) + 4
    doc.lines[i + 1:i + 1] = ser(bot_node, ind) + ser(cube_node, ind)
    # ---- the ball (the size of cards 2 to 4 already), its pieces: tiles' flips, his cheer, the cube's give ----
    round_ball(doc, intro, ("9:12328", "9:12336", "9:12337", "9:12339"))
    spin_id = next(e.get("id") for e in root.iter("Node") if e.get("name") == f"{ROOM} Ball Spin")

    def tile_scale(side):
        mine = [t0 for s, t0, _ in flips if s == side]
        return lambda t: next((abs(math.cos(math.pi * (t - t0) / FLIP)) for t0 in mine if t0 <= t <= t0 + FLIP), 1.0)

    def tile_colour(side):
        mine = sorted((t0, c) for s, t0, c in flips if s == side)
        rest = TILES[side]
        return lambda t: next((c for t0, c in reversed(mine) if t >= t0 + FLIP / 2), rest) if t < hid + 40 else rest

    def toe(vid, y0, y1):
        return lambda t: y1 if cheer[0] <= t < cheer[1] else y0

    give = lambda t: 1.0 - dip(t, hit1, 0.008, 12)
    pieces = [(bot.tile_shape[s], "scaleY", tile_scale(s), 1.0, None) for s in TILES]
    pieces += [(vid, "y", toe(vid, y0, y1), y0, None) for vid, y0, y1 in bot.toe]
    pieces += [(cube_node.get("id"), "scaleX", give, 1.0, None)]
    c234.BALL_CENTER = 16.78
    ids = dict(ball="9:12325", scale="9:12327", spin=spin_id)
    pre = lambda f: (b.c[0][0], b.c[0][1], 1.0, 1.0)
    emit_room(doc, ROOM, b, theta, T0, ids, pre, pieces, Ps=PS)
    # ---- the intro-only keys: the cube's turn and his drop; the tiles' colours (intro and loop) ----
    i_keys, l_keys = [], []
    for idx, fid in face_ids.items():
        xs = {f: faces_at(phi_at(f))[idx][0] for f in range(INTRO)}
        ss = {f: faces_at(phi_at(f))[idx][1] for f in range(INTRO)}
        i_keys += [(fid, "x", doubles(xs, range(INTRO))), (fid, "scaleX", doubles(ss, range(INTRO)))]
    drop = {("6:2669", "y"): lambda v: BOT_Y0 + (v + 105.0) * (BOT_Y - BOT_Y0) / (4.65 + 105.0)}
    i_keys += bot.keyed(bot.anim("Intro"), BOT_IN, drop)
    for side in TILES:
        ik, lk = colour_keys(tile_colour(side), L)
        i_keys.append((bot.tile_colour[side], "colorValue", ik))
        l_keys.append((bot.tile_colour[side], "colorValue", lk))
    add_keys(doc, intro, i_keys)
    add_keys(doc, loop, l_keys)
    pose(doc, intro, f"{ROOM} Waiting", last=False)
    pose(doc, intro, f"{ROOM} Built", last=True)
    for n, l in enumerate(doc.lines):
        if re.match(r"^\s*<KeyFrame\w+\b(?![^>]*\bid=)", l):
            doc.lines[n] = re.sub(r"(/?>)\s*$", f' id="{doc.new_id()}"\\1', l, count=1)
    doc.save()
    print("wrote", SCENE)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
