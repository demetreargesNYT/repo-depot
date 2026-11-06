"""Regenerates the whole Chapter 1 Card 5 room: refuses chapters/ch1/scene.rml once it has changed since commit 2ac7464 (tools/regen_guard.py).

One time (2026-11-03, the finesse round): Chapter 1 card 5 gets Wordle Bot, the blocks at 70 percent, and the ball's climb.

    python3 chapters/ch1/ch1_card_5.py            dry run: prints the beats and clearances, writes nothing
    python3 chapters/ch1/ch1_card_5.py --write    rewrite chapters/ch1/scene.rml

Run it on the file as it was before this work (git show 2ac7464:YIG2026/rive/chapters/ch1/scene.rml): it moves and wraps pieces, so it
refuses to run twice. It reads the bot from a pull of his Rive file (2702548, read only) in .cache/scratch.nosync/ch1/wordle-bot/.

The room (round 2, Demetre's notes):
  * The blocks: the O and W blocks leave the floor plane and join their shadows in "Top Row", so the row drops as one piece with its
    shadows. The second block's letter was a B; it is the R of WORDLE now. The six blocks are scaled to 70 percent about the middle of
    their base (their lines stay 1.5) and the group is laid out with the bot and the ball's whole path inside the phone frame
    (x 560 to 935).
  * Wordle Bot, at the size of round 1 (his body 117.81 wide, as in Figma), stands on the floor behind the blocks' right end: his body
    shows above the right step, the blocks stay in front of him (every letter shows), and his tapping right shoe stands clear of the E.
    He is copied in, not nested, so his keys are on the room's own timelines (his drop, his Idle, his reaction to the ball, Back and
    startScene all work and the checks see every key). His lines are 1.5, the room's weight: his strokes were 0.954 in his own units,
    and the antennae, legs, shoes and laces, drawn as filled outlines, are redrawn as 1.5 strokes on the same centrelines.
  * The ball climbs: from its home on the floor left of the blocks it hops onto the L block, pauses (deciding), hops onto the top row
    (the L block tips a little as it pushes off) and perches there. As it lands on top the bot's screen tiles flash green twice and his
    foot tap follows like a nod. Then it rolls right and off the top row, falls behind the bot's body onto the right step and bounces,
    and while it is out of sight it is put back behind the bottom row, from where it rolls out to its home again (the loop reset is
    never seen: it happens behind the bot, and the ball comes back into view from behind the L block).
Times in the notes are Finesse-panel timecodes (from the moment the scene is set; the loop starts at 3.2 s).
"""
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

RIVE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RIVE_ROOT / "tools"))

import ch1_cards_234 as c234                                                              # noqa: E402
from ch1_cards_234 import Ball, INTRO, emit_room, round_ball, dip, phone_y, COPY_BOTTOM   # noqa: E402
from ball_motion import smooth                                                            # noqa: E402
from rml_edit import Doc, num                                                             # noqa: E402
import regen_guard                                                                        # noqa: E402
WRITTEN_AGAINST = "2ac7464"     # the file as it was before this work (see above)

SCENE = RIVE_ROOT / "chapters" / "ch1" / "scene.rml"
BOT_FILE = RIVE_ROOT / ".cache" / "scratch.nosync" / "ch1" / "wordle-bot" / "scene.rml"
ROOM = "Chapter 1 Card 5"

# ---- the blocks: scaled about the middle of their base ------------------------------------------------------------------------
S = 0.70
X0 = 618.0                                  # the L block's left face, on the artboard
PIV = (744.4, 712.0)                        # the base's middle, in the blocks' own units
CX = X0 + S * (PIV[0] - 566.75)
Wx = lambda x: CX + S * (x - PIV[0])
Wy = lambda y: PIV[1] + S * (y - PIV[1])
L_LEFT, TOP_LEFT, TOP_RIGHT, E_RIGHT = Wx(566.75), Wx(663.625), Wx(824.875), Wx(921.75)
STEP_Y, TOP_Y = Wy(608.75), Wy(506.25)      # the bottom row's top line, the top row's
ROW_Y0 = -260.0                             # the top row's drop starts here (its base, own units): above the artboard at this scale

# ---- the bot ------------------------------------------------------------------------------------------------------------------
K = 117.81 / 22.0366                        # Figma body width / the body's width inside his "Wordle Bot" node
T = 1.5 / K                                 # his stroke, in his own units, that draws 1.5 on the artboard
FEET = 33.642                               # his shoes' bottom centreline, in his own units
BOT_CX = E_RIGHT                            # his body's centre: over the blocks' right end
BOT_X = BOT_CX - K * 17.709
BOT_Y = 712.0 - K * FEET                    # feet on the floor line
BOT_Y0 = -190.0                             # where his drop starts: feet above the artboard
BOT_IN = 81                                 # intro frame his drop starts: he lands 33 frames later, at 1.9 s
BODY = (BOT_CX - K * 11.018, BOT_Y + K * 6.079, BOT_CX + K * 11.018, BOT_Y + K * 26.403, K * 4.533)   # x0, y0, x1, y1, corner radius
HEAD = (BOT_CX + K * 0.351, BOT_Y + K * 0.23)    # his dome's centre x, the antenna tips' top
IDLE_AT = (128, 250)                        # loop frames his Idle starts (it takes 120 frames); its taps fall while the ball is
                                            # out of sight (loop 188) and resting at home (loop 310), so only the perch reads as a reaction
TOE = (42, 60, 80)                          # Idle frames of the foot tap: rest, toe up (held), rest
GREEN = "FF68A963"                          # his own green tile

# ---- the ball (cycle frames; the cycle starts at intro frame T0 = 3, with the pan) ----------------------------------------------
RB = 17.1                                   # centre to the surface it rests on
R_VIS = 17.7                                # its drawn radius with the line
FLOOR_C, STEP_C, TOP_C = 712.0 - RB, STEP_Y - RB, TOP_Y - RB
HOME = 585.5
S1_X = X0 + 26.0                            # where it lands on the L block
P_X = TOP_LEFT + 26.0                       # where it perches on the top row
HIDE_X = X0 + 37.0                          # where it waits behind the bottom row, out of sight
T0 = 3
PS = 100                                    # the loop repeats from here (the ball at home); before it, the first visit's wait in the pan
T_HOP1 = 118                                # 2.02 s: the L block came in with the pan (1.55 s), the top row settled at 1.82 s
T_HOP2 = 202                                # after a pause on the L block that holds the loop's seam (cycle 188, 3.2 s)
PERCH = 50
V_ROLL, N_ACC = 1.6, 40
N_FALL = 19
E_BOUNCE = 0.78
HIDDEN = 34
N_OUT = 50
HOME_WAIT = 50                              # the loop's pause at home before the first hop
BUBBLE_BOTTOM = 502.7                       # the speech bubble's lowest edge on the phone frame, in artboard units (tail tip 20 px lower)


def parabola(p0, p1, n):
    """Points of a flight from p0 to p1 in n frames at the one gravity (0.40 per frame squared)."""
    vx = (p1[0] - p0[0]) / n
    vy = (p1[1] - p0[1] - 0.2 * n * n) / n
    return [(p0[0] + vx * t, p0[1] + vy * t + 0.2 * t * t) for t in range(n + 1)], (vx, vy + 0.4 * n)


def rect_dist(p, r):
    x0, y0, x1, y1 = r
    dx = max(x0 - p[0], 0, p[0] - x1)
    dy = max(y0 - p[1], 0, p[1] - y1)
    return math.hypot(dx, dy)


BLOCKS = [(L_LEFT, STEP_Y, E_RIGHT, 712.0), (TOP_LEFT, TOP_Y, TOP_RIGHT, STEP_Y)]


def clearance(pts):
    return min(rect_dist(p, r) for p in pts[1:-1] for r in BLOCKS)


def pick_hop(p0, p1, apex_limit=None):
    """The quickest hop that clears the blocks by 1 px or more (and keeps its top below apex_limit)."""
    for n in range(24, 60):
        pts, v = parabola(p0, p1, n)
        top = min(p[1] for p in pts) - R_VIS
        if clearance(pts) >= RB + 1.0 and (apex_limit is None or top >= apex_limit):
            return n, pts, v, top
    raise SystemExit(f"no hop clears the blocks from {p0} to {p1}")


def in_body(c):
    """Is the whole ball inside the bot's body (a rectangle with rounded corners)?"""
    x0, y0, x1, y1, r = BODY
    x0, y0, x1, y1 = x0 + R_VIS, y0 + R_VIS, x1 - R_VIS, y1 - R_VIS
    if not (x0 <= c[0] <= x1 and y0 <= c[1] <= y1):
        return False
    rr = r - R_VIS                                   # the corners: the ball's centre within the inset corner arc
    if rr <= 0:
        return True
    cx = min(max(c[0], x0 + rr), x1 - rr)
    cy = min(max(c[1], y0 + rr), y1 - rr)
    return math.hypot(c[0] - cx, c[1] - cy) <= rr + 1e-9


def ball_cycle():
    b = None
    plan = {}
    seg = []                                         # (first frame, points, mode)
    n1, hop1, v1, top1 = pick_hop((HOME, FLOOR_C), (S1_X, STEP_C))
    t_s1 = T_HOP1 + n1
    assert t_s1 < 188 < T_HOP2, "the loop's seam must fall in the pause on the L block"
    n2, hop2, v2, top2 = pick_hop((S1_X, STEP_C), (P_X, TOP_C), apex_limit=BUBBLE_BOTTOM + 15)
    t_p = T_HOP2 + n2
    t_roll = t_p + PERCH
    d = TOP_RIGHT - P_X
    n_c = math.ceil((d - 0.5 * V_ROLL * N_ACC) / V_ROLL)
    v = d / (0.5 * N_ACC + n_c)
    roll = [(P_X + (0.5 * v / N_ACC * u * u if u <= N_ACC else 0.5 * v * N_ACC + v * (u - N_ACC)), TOP_C) for u in range(N_ACC + n_c + 1)]
    t_edge = t_roll + N_ACC + n_c
    fall, v_land = parabola((TOP_RIGHT, TOP_C), (TOP_RIGHT + v * N_FALL, STEP_C), N_FALL)
    t_land = t_edge + N_FALL
    s_in = math.hypot(*v_land)
    vx_o = 0.85 * v_land[0]
    vy_o = -math.sqrt((E_BOUNCE * s_in) ** 2 - vx_o ** 2)
    n_b = round(-vy_o / 0.4)                         # to the top of the bounce, or until it would rise above his case
    while not in_body((fall[-1][0] + vx_o * n_b, STEP_C + vy_o * n_b + 0.2 * n_b * n_b)):
        n_b -= 1
    bounce = [(fall[-1][0] + vx_o * u, STEP_C + vy_o * u + 0.2 * u * u) for u in range(n_b + 1)]
    t_jump = t_land + n_b
    t_out = t_jump + 1 + HIDDEN
    t_home = t_out + N_OUT
    L = t_home + HOME_WAIT - (T_HOP1 - PS)
    b = Ball(L)
    for t in range(L + 1):
        if t <= T_HOP1:
            c, m = (HOME, FLOOR_C), "rest"
        elif t <= t_s1:
            c, m = hop1[t - T_HOP1], "air"
        elif t <= T_HOP2:
            c, m = (S1_X, STEP_C), "rest"
        elif t <= t_p:
            c, m = hop2[t - T_HOP2], "air"
        elif t <= t_roll:
            c, m = (P_X, TOP_C), "rest"
        elif t <= t_edge:
            c, m = roll[t - t_roll], "roll"
        elif t <= t_land:
            c, m = fall[t - t_edge], "air"
        elif t <= t_jump:
            c, m = bounce[t - t_land], "air"
        elif t <= t_out:
            c, m = (HIDE_X, FLOOR_C), "rest"
        elif t <= t_home:
            c, m = (HIDE_X + (HOME - HIDE_X) * smooth((t - t_out) / N_OUT), FLOOR_C), "roll"
        else:
            c, m = (HOME, FLOOR_C), "rest"
        if t < L:
            b.put(t, c, m)
        else:
            b.c[L] = c
    # the mode is the motion from a frame to the next: a hop or a roll begins on the frame before it moves
    for t in range(L):
        moves = math.dist(b.c[t + 1], b.c[t]) > 1e-9
        if b.mode[t] == "rest" and moves:
            b.mode[t] = b.mode[t + 1] if t + 1 < L else "rest"
        elif not moves:
            b.mode[t] = "rest"
    b.mode[t_jump] = "rest"                          # put back out of sight: no turn
    b.squash(t_s1, 0.06)
    b.squash(t_p, 0.06)
    plan.update(n1=n1, n2=n2, top1=top1, top2=top2, t_s1=t_s1, t_p=t_p, t_roll=t_roll, t_edge=t_edge, t_land=t_land, t_jump=t_jump,
                t_out=t_out, t_home=t_home, L=L, v_roll=v, v_land=v_land, v_out=(vx_o, vy_o), s_in=s_in, hop1=hop1, hop2=hop2,
                fall=fall, bounce=bounce)
    return b, plan


def spin(b, plan):
    """The turn on every cycle frame, and the turn the loop leaves over taken up while the ball waits out of sight."""
    theta = b.spin(r=16.9)
    L = plan["L"]
    turns = theta[L] - theta[PS]
    left = round(turns / (2 * math.pi)) * 2 * math.pi - turns
    h0, h1 = plan["t_jump"] + 1, plan["t_out"]
    for t in range(h0, L + 1):
        theta[t] += left * (smooth((t - h0) / (h1 - h0)) if t < h1 else 1.0)
    return theta, left


def loop_frame(t, L):
    return (t - (INTRO - 1 - T0)) % (L - PS)


def l_tip(t):
    """The L block tips back a little on its bottom-left corner as the ball pushes off it for the top row, and settles. Its top moves
    left (the push is to the right), so its right foot lifts about 1 px: it never dips into the floor."""
    return -(dip(t, T_HOP2, 0.012, 18) + dip(t, T_HOP2 + 18, 0.003, 12))


# ---- RML text ----------------------------------------------------------------------------------------------------------------------
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


class Bot:
    """His art from the Wordle Bot file, rebuilt for this room, and his keys."""

    def __init__(self, doc):
        self.doc = doc
        self.src = ET.parse(BOT_FILE).getroot()
        self.ids = {}                                     # his file's ids -> ours
        self.toe = []                                     # (vertex id, rest y, lifted y)

    def nid(self, old=None):
        i = self.doc.new_id()
        if old:
            self.ids[old] = i
        return i

    def stroke(self):
        s = el("Stroke", thickness=T, cap="round", join="round", id=self.nid())
        s.append(el("SolidColor", colorValue="FF000000", id=self.nid()))
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

    def shape(self, name, x, y, paths, paints):
        s = el("Shape", x=x, y=y, name=name, id=self.nid())
        for p in paths + paints:
            s.append(p)
        return s

    def antenna(self, sh, half):
        """A filled capsule becomes one round-capped 1.5 line on its centreline, reaching the old tip."""
        path = sh.find("PointsPath")
        ox, oy = float(path.get("x", 0)), float(path.get("y", 0))
        for c in list(sh):
            sh.remove(c)
        p, _ = self.path([(ox - half[0], oy - half[1]), (ox + half[0], oy + half[1])], closed=False)
        sh.append(p)
        sh.append(self.stroke())

    def foot(self, node, ox, oy, mirror, legs, lift):
        """A shoe drawn as outlines-as-fills becomes an upper (yellow) and a sole (white, as in Figma), each stroked 1.5 on the old
        outlines' centrelines, plus legs and laces as 1.5 lines. lift: whether this shoe taps (the right one)."""
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
        node.append(self.shape(f"{ROOM} Bot {side} Shoe Lines", ox, oy, lines + [lace1, lace2], [self.stroke()]))
        node.append(self.shape(f"{ROOM} Bot {side} Shoe", ox, oy, [upper], [self.fill("FFF0C105"), self.stroke()]))
        node.append(self.shape(f"{ROOM} Bot {side} Sole", ox, oy, [sole], [self.fill("FFFFFFFF"), self.stroke()]))
        if lift:
            toe = 1.022                                   # the old toe's lift at this x (1.149 on its outer edge, 0.894 inside)
            self.toe += [(uv[3], 0.717, 0.717 - toe), (uv[4], 1.551, 1.551 - toe), (sv[1], 1.551, 1.551 - toe), (sv[2], 2.863, 2.863 - toe),
                         (l1[1], 0.0, -0.51), (l2[1], -1.193, -1.193 - 0.2554)]

    def build(self):
        wb = next(e for e in self.src.iter("Node") if e.get("name") == "Wordle Bot")
        wb = ET.fromstring(ET.tostring(wb))
        for e in wb.iter():                               # every id is new; the keys follow the map
            if e.get("id"):
                e.set("id", self.nid(e.get("id")))
            if e.get("name") in ("Component", "Path", "Fill 1", "Stroke 1"):
                del e.attrib["name"]
            if e.tag == "Stroke":
                e.set("thickness", num(T))
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
        for sh in body.findall("Shape"):
            if sh.get("name") == f"{ROOM} Bot Left Antenna":
                self.antenna(sh, (-1.680, 1.540))
            elif sh.get("name") == f"{ROOM} Bot Right Antenna":
                self.antenna(sh, (-1.600, -1.739))
        rf = next(e for e in wb if e.get("name") == f"{ROOM} Bot Right Foot")
        lf = next(e for e in wb if e.get("name") == f"{ROOM} Bot Left Foot")
        self.foot(rf, 1.1181529, 4.2789497, False, [(-3.342, -4.414), (0.713, -4.414)], True)
        self.foot(lf, -0.97410905, 4.7793708, True, [(3.246, -4.653), (-0.787, -4.653)], False)
        self.node = wb
        self.tiles = [self.ids[i] for i in ("6:2698", "6:2710", "6:2722")]    # middle, right, left tiles' colours
        self.tile_rest = ["FFF0C105", "FF787C7E", "FF68A963"]
        return wb

    def anim(self, name):
        return next(a for a in self.src.iter("LinearAnimation") if a.get("name") == name)

    def keyed(self, anim, frame_shift, value_map=None):
        """[(object id, property, [key elements])] of one of his animations, on our ids, frames shifted."""
        out = []
        live = {e.get("id") for e in self.node.iter()}       # the old shoes' vertices are gone (their tap is rebuilt below)
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
                            e.set("id", self.nid())
                    keys.append(k)
                out.append((self.ids[oid], kp.get("property"), keys))
        return out

    def tap(self, at):
        """His own foot tap on the new toe vertices: rest, toe up (held), rest, at loop frames at, at + 18, at + 38."""
        return [(vid, "y", [el("KeyFrameDouble", value=y0, frame=str(at)), el("KeyFrameDouble", value=y1, frame=str(at + 18)),
                            el("KeyFrameDouble", value=y0, frame=str(at + 38))]) for vid, y0, y1 in self.toe]

    def flash(self, at):
        """The reaction: his screen tiles flash green twice (3 frames on, 9 held, 3 off, 3 on, 12 held, 3 off)."""
        out = []
        for tid, rest in zip(self.tiles, self.tile_rest):
            seq = [(0, rest), (3, GREEN), (12, GREEN), (15, rest), (18, GREEN), (30, GREEN), (33, rest)]
            out.append((tid, "colorValue", [el("KeyFrameColor", value=v, interpolationType="linear", frame=str(at + f)) for f, v in seq]))
        return out


def keyed_lines(doc, objs, pad=12):
    """KeyedObject lines for [(object id, property, [key elements])], one object per id and one list per property."""
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
    """Rewrite a one-frame pose (Waiting from the Intro's first keys, Built from its last) for every key list, whatever its kind."""
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


def r_letter(doc):
    """The B (shape 9:12184) becomes an R: its stem and bowl, left open, then a leg from the bowl's foot to the bottom right."""
    i = doc.idx("9:12185")
    doc.lines[i] = doc.lines[i].replace('isClosed="true"', 'isClosed="false"')
    for vid in ("9:12192", "9:12193", "9:12194"):
        del doc.lines[doc.idx(vid)]
    j = doc.end(doc.idx("9:12185"))
    pad = " " * (len(doc.lines[j]) - len(doc.lines[j].lstrip()))
    doc.lines[j + 1:j + 1] = [f'{pad}<PointsPath isClosed="false" id="{doc.new_id()}">',
                              f'{pad}    <StraightVertex x="-1.0885" id="{doc.new_id()}"/>',
                              f'{pad}    <StraightVertex x="9.7985001" y="33.75" id="{doc.new_id()}"/>',
                              f"{pad}</PointsPath>"]


def blocks(doc):
    """The O and W blocks (9:12290, in the floor plane) move into Top Row Art with their shadows; the row pivots on its base; the six
    blocks go in one group scaled about the middle of their base, their lines kept at 1.5."""
    i, j = doc.idx("9:12290"), doc.end(doc.idx("9:12290"))
    block = [l for l in doc.lines[i:j + 1] if "<ClippingShape" not in l]
    del doc.lines[i:j + 1]
    k = doc.end(doc.idx("9:12152"))                       # after the shadows (drawn on top of the blocks they fall on)
    ind_old = len(block[0]) - len(block[0].lstrip())
    ind_new = len(doc.lines[k]) - len(doc.lines[k].lstrip())
    doc.lines[k + 1:k + 1] = [" " * ind_new + l[ind_old:] for l in block]
    i = doc.idx("9:12180")
    doc.lines[i] = doc.lines[i].replace('y="663.75"', 'y="608.75"')
    i = doc.idx("9:12181")
    doc.lines[i] = doc.lines[i].replace('y="-663.75"', 'y="-608.75"')
    a, b = doc.anim(f"{ROOM} Intro")
    found = doc._object(a, b, "9:12180")
    for n in range(found[0], found[1] + 1):
        doc.lines[n] = doc.lines[n].replace('value="-136.25"', f'value="{num(ROW_Y0)}"').replace('value="663.75"', 'value="608.75"')
    gid, _ = doc.wrap_run("9:12180", "9:12182", f"{ROOM} Blocks", *PIV)
    i = doc.idx(gid)
    doc.lines[i] = doc.lines[i].replace(f'x="{num(PIV[0])}"', f'x="{num(CX)}" scaleX="{num(S)}" scaleY="{num(S)}"')
    a, b = doc.idx(gid), doc.end(doc.idx(gid))
    for n in range(a, b + 1):
        if "<Stroke " in doc.lines[n] and "transformAffectsStroke" not in doc.lines[n]:
            doc.lines[n] = doc.lines[n].replace("<Stroke ", '<Stroke transformAffectsStroke="false" ', 1)
    return gid


def main(argv):
    write = "--write" in argv
    doc = Doc(SCENE)
    if any(f'name="{ROOM} Bot"' in l for l in doc.lines):
        raise SystemExit(f"{ROOM} already has the bot: run this on the file as it was before (see the docstring)")
    b, p = ball_cycle()
    theta, left = spin(b, p)
    L = p["L"]
    lf = lambda t: loop_frame(t, L)
    tc = lambda t: (t + T0) / 60 if t + T0 < INTRO else 3.2 + lf(t) / 60
    t_react = p["t_p"] + 2
    k_react = lf(t_react)
    assert p["t_p"] + T0 > INTRO - 1, "the perch (and the bot's reaction) falls inside the loop"
    react = (k_react, k_react + 54)
    for s in IDLE_AT:
        assert s + 120 < L - PS and (s + 120 < react[0] or s > react[1]), (s, react)
    print(f"{ROOM}: cycle {L} frames, the loop repeats cycle {PS} to {L} ({(L - PS) / 60:.2f} s), the journey starts at intro frame {T0}")
    print(f"  blocks: scale {S}, the L block's left face at x {L_LEFT:.1f}, right end x {E_RIGHT:.1f}, top row x {TOP_LEFT:.1f} to {TOP_RIGHT:.1f}, "
          f"steps at y {STEP_Y:.1f} and {TOP_Y:.1f}")
    print(f"  bot: body x {BODY[0]:.1f} to {BODY[2]:.1f}, y {BODY[1]:.1f} to {BODY[3]:.1f}; head x {HEAD[0]:.1f}, antenna tips y {HEAD[1]:.1f}; "
          f"drop at {BOT_IN / 60:.2f} s, lands {(BOT_IN + 33) / 60:.2f} s")
    beats = [("hops onto the L block", T_HOP1), ("lands on it", p["t_s1"]), ("hops onto the top row (the L block tips)", T_HOP2),
             ("perches on top; the bot's tiles flash, then his foot tap", p["t_p"]), ("rolls right", p["t_roll"]),
             ("off the top row", p["t_edge"]), ("lands on the right step behind the bot, bounces", p["t_land"]),
             ("put back behind the bottom row (out of sight)", p["t_jump"]), ("rolls out from behind the L block", p["t_out"]),
             ("home", p["t_home"])]
    for name, t in beats:
        print(f"  cycle {t:3d}  loop frame {lf(t):3d}  timecode {tc(t):5.2f} s  {name}")
    print(f"  hops: {p['n1']} and {p['n2']} frames; their tops y {p['top1']:.1f} and {p['top2']:.1f} (the bubble's lowest edge {BUBBLE_BOTTOM}; "
          f"{phone_y(p['top2']):.0f} px on the phone frame, copy ends {COPY_BOTTOM:.0f})")
    print(f"  roll {p['v_roll']:.2f} px/frame; lands on the step at {p['s_in']:.2f}, bounces at {math.hypot(*p['v_out']):.2f} "
          f"({math.hypot(*p['v_out']) / p['s_in']:.0%}); turn taken up out of sight {left:+.2f} rad")
    shown = [t for t in range(p["t_land"], p["t_jump"] + 1) if not in_body(b.c[t])]
    print(f"  hidden behind the bot from landing to the jump: {'yes' if not shown else 'NO, frames ' + str(shown)}")
    hid = (b.c[p["t_jump"] + 1][0] - R_VIS >= L_LEFT) and (b.c[p["t_jump"] + 1][0] + R_VIS <= E_RIGHT)
    print(f"  hidden behind the bottom row while it waits: {'yes' if hid else 'NO'}")
    xs = [c[0] for c in b.c.values()]
    print(f"  the ball's whole path: x {min(xs) - R_VIS:.1f} to {max(xs) + R_VIS:.1f}; the bot to x {BODY[2] + 0.75:.1f}")
    assert not shown and hid
    if not write:
        return 0

    intro, loop = f"{ROOM} Intro", f"{ROOM} Loop"
    blocks(doc)
    r_letter(doc)
    # ---- the ball: the size of cards 2 to 4, round, a spin pivot ----
    i = doc.idx("9:12326")
    doc.lines[i] = doc.lines[i].replace('scaleY="1.7725" scaleX="1.7725" y="2"', 'scaleY="0.96" scaleX="0.96"')
    doc.drop_object(intro, "9:12326")
    doc.drop_object(loop, "9:12326")
    round_ball(doc, intro, ("9:12328", "9:12336", "9:12337", "9:12339"))
    spin_id, _ = doc.wrap_run("9:12328", "9:12334", f"{ROOM} Ball Spin", 0.0, -17.572)
    # ---- the L block's pivot: its bottom-left corner (566.75, 712), inside node "a" at (566, 505.5) ----
    l_id, _ = doc.wrap("9:12261", f"{ROOM} L Block", 566.75 - 566.0, 712.0 - 505.5)
    c234.BALL_CENTER = 16.78
    ids = dict(ball="9:12325", scale="9:12327", spin=spin_id)
    pre = lambda f: (b.c[0][0], b.c[0][1], 1.0, 1.0)
    emit_room(doc, ROOM, b, theta, T0, ids, pre, [(l_id, "rotation", l_tip, 0.0, None)], Ps=PS)
    # ---- the bot: the front plane's last child, so the blocks draw over him and he draws over the ball ----
    bot = Bot(doc)
    node = bot.build()
    i = doc.end(doc.idx("9:12734"))
    doc.lines[i:i] = ser(node, len(doc.lines[i]) - len(doc.lines[i].lstrip()) + 4)
    wb = bot.ids["6:2669"]
    drop = {("6:2669", "y"): lambda v: BOT_Y0 + (v + 105.0) * (BOT_Y - BOT_Y0) / (4.65 + 105.0)}
    i_keys = bot.keyed(bot.anim("Intro"), BOT_IN, drop)
    idle = bot.anim("Idle")
    rest_y = {("6:2669", "y"): lambda v: BOT_Y}
    l_keys = []
    for s in IDLE_AT:
        for oid, prop, keys in bot.keyed(idle, s, rest_y):
            if (oid, prop) in ((wb, "y"), (bot.ids["6:2670"], "y")) and s != IDLE_AT[0]:
                continue
            l_keys.append((oid, prop, keys))
        l_keys += bot.tap(s + TOE[0])
    l_keys += bot.flash(k_react)
    l_keys += bot.tap(k_react + 15)
    in_intro = {(o, pr) for o, pr, _ in i_keys}               # every property the loop keys is held in the intro at its rest
    for oid, prop, keys in l_keys:
        if (oid, prop) not in in_intro:
            first = min(keys, key=lambda k: int(k.get("frame", 0)))
            i_keys.append((oid, prop, [el(first.tag, **({"value": first.get("value")} if first.get("value") else {}))]))
            in_intro.add((oid, prop))
    for _, _, keys in i_keys + l_keys:
        for k in keys:
            for e in k.iter():
                if e.get("id") is None:
                    e.set("id", doc.new_id())
    add_keys(doc, intro, i_keys)
    add_keys(doc, loop, l_keys)
    pose(doc, intro, f"{ROOM} Waiting", last=False)
    pose(doc, intro, f"{ROOM} Built", last=True)
    for n, l in enumerate(doc.lines):                         # the poses' keys need ids too
        if re.match(r"^\s*<KeyFrame\w+\b(?![^>]*\bid=)", l):
            doc.lines[n] = re.sub(r"(/?>)\s*$", f' id="{doc.new_id()}"\\1', l, count=1)
    regen_guard.save(doc, WRITTEN_AGAINST, __file__)
    print("wrote", SCENE)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
