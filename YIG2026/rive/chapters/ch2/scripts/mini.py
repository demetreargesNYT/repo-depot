"""The Mini, "the speed solve" (Demetre's brief, 2026-11-04): the cubes are the crossword grid and they come to life with the ball.

Scale (note 5, kept): each of the room's planes holds its pieces in a pivot at (747.5, 711.5), the room's middle on the floor line,
scaled 0.85; the ball is 1.7. The cubes that drop in fall 800/0.85 in their own space so on screen they drop as before; strokes are
1/0.85 thicker in their own space so the lines keep their weight. The lockup is not touched.

The mouth: the upper cube's dark top is its open mouth, and it now has a lid (a new piece, the same parallelogram as the lid box's
lid, light). The lid is hinged on the top's back edge: shut it lies over the mouth; open it stands up behind it, leaning back a
little. Its two front corners are keyed: front = back + (38.33 cos a, 44.68 cos a - 95.83 sin a) in its own space, a the opening
angle (the cube's depth seen at the room's slant, and its true height). The lid is in the Floor Plane, under the ball, so the ball
passes in front of it, and above the mouth's dark inside. The ball hides in the mouth behind the cube's front and side faces (Front
Plane), as before: the room's own drawing order is the mask. The intro is unchanged: the cubes drop in, the upper cube with its lid
shut and the ball already inside it.

The cube turns (the shared move, Chapter 1 card 5's 2D trick): each turning cube's front square gets two faces, the colour it has
and the other one (black or white), each a full-size square in a node scaled sideways and masked to the square. The face it shows
is anchored on the square's left edge, the other on its right edge, so a turn keys only scaleX: the edge they share sweeps across
at width x cos t / (cos t + sin t), t eased from 0 to 90 degrees in TURN frames, the outgoing face squeezing to its side as the
incoming one grows. A cube turns there and back (the second turn the other way), so each cube is back on its drawn colour at the
loop's seam. Their lines are 1.5 on screen and never scale (transformAffectsStroke off). They turn only while the ball is not
touching them, one at a time, in short bursts at uneven moments.

The journey (one gravity, 0.40; every flight a parabola; mini_paths.py): the lid pops open and flings the ball out three times a loop.
  1. hop: a short hop straight up and back in (while the lockup is on screen, so it stays well below it)
  2. gap: out over the gap to the left, off the left box's side and the floor beside it (3 frames apart), and straight back in
  3. rim: up and down onto the mouth's back left corner, two light bounces on it, and in
Each time it drops in out of sight, the lid snaps shut, a beat, and the lid pops open again. The loop's seam is inside the mouth with
the lid shut. The lid is the only piece that adds speed (it flings from rest); every contact keeps 80 to 100 percent.
Why only these: the upper cube is flush on the lid box, so nothing can leave or enter the lid box sideways, and with the ball's top
held at y 425 or lower, a fling has just enough energy to come back over the mouth's rim after one floor bounce. Back into the mouth
from the gap needs a turn round, and the left box's side is the only surface that gives one: its hit lands within 3 frames of the
floor bounce, which ball_speed.py reads as one contact (see the report).
"""
import math
import re

from common import CENTER_IN_SCALE, BallArt, Cycle, _set_attrs, dip, emit, plane_x, prepare_ball, smooth
from mini_paths import RC, fly, spin_rate
from rml_edit import num

ROOM = "The Mini"
T0 = 110                                   # 1.83 s: the upper cube's top (with its lid) has landed and its squash is over at 1.82 s
A = (747.5, 711.5)                         # the scale's anchor: the room's middle, on the floor line
K = 0.85
PLANES = {"Front": "9:5695", "Floor": "9:5694", "Wall": "9:5697"}
CUBES = ("9:5206", "9:5208", "9:5210", "9:5212")    # the four drop-ins (their Art offsets are -760)
BALL_SCALE = 1.7
IN_UP = (829.0, 632.0)                     # the ball's rest in the mouth: wholly behind the upper cube's front face
HIDDEN_Y = 621.0                           # a centre below this, inside the mouth, is wholly hidden (its top under the rim, y 590)
CATCH = 6                                  # frames to settle at rest in the mouth, out of sight
LAUNCH_LAG = 2                             # the ball leaves this many frames after the lid starts to pop
LEFT_BOX = "9:5276"                        # the left box's node (its own space)
LEFT_BOX_REST = (-174.91251, -26.963499)

# the three flings: launch velocity from IN_UP, (e, kt) for each contact in turn, and the contacts it must make
FLINGS = [
    ("hop", (-0.15, -9.0), [], []),
    ("gap", (-2.5, -11.5), [(0.9, 1.0), (0.9, 1.0)], ["left box side", "floor"]),
    ("rim", (-1.92, -10.02), [(0.8, 0.9), (0.85, 0.95)], ["upper cube corner", "upper cube corner"]),
]
POP_AT = [0, 92, 256]                      # cycle frames the lid pops for each fling
END_BEAT = 60                              # frames shut after the last catch before the loop starts again

# the lid (the upper cube's top's shape, in its group 9:5155): its corners shut, back right, front right, front left, back left
LID_AT = (226.3465, 23.235)
LID_SHUT = [(28.7485, -22.341), (67.0805, 22.341), (-28.7495, 22.341), (-67.0805, -22.341)]
DEPTH, HEIGHT = (38.332, 44.682), 95.829
LID_OPEN, LID_POP = 97.0, 107.0            # degrees: open (leaning back a little), and the pop's overshoot
POP_T, SETTLE_T, SNAP_T = 6, 8, 6          # frames

# the turning cubes: the front square's shape (its own position and half sizes, in its parent's space), its colour and the other
LIGHT, DARK = "FFDFDBD7", "FF1F1F1F"
SQUARES = {
    "left box": ("9:5277", (14.307, -0.249, 50.747, 50.7915), LIGHT),
    "lower cube": ("9:5246", (-100.478, 116.142, 47.9145, 47.873), LIGHT),
    "upper cube": ("9:5215", (337.08151, 93.455, 47.9145, 47.873), LIGHT),
    "lid box": ("9:5186", (939.41248, 712.203, 47.9145, 47.873), DARK),
}
TURN = 14                                  # frames: 0.23 s
TURNS = []                                 # (cube, cycle frame the turn starts): set in build() from the ball's timeline


def S(x, y):
    return (A[0] + K * (x - A[0]), A[1] + K * (y - A[1]))


def ease(u):
    u = min(1.0, max(0.0, u))
    return 4 * u ** 3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2


# ---- new art ------------------------------------------------------------------------------------------------------------------
def _pad(doc, i):
    return " " * (len(doc.lines[i]) - len(doc.lines[i].lstrip()))


def _rect_shape(doc, pad, name, pts, colour, clip_id):
    out = [f'{pad}<Shape name="{name}" id="{doc.new_id()}">', f'{pad}    <PointsPath isClosed="true" id="{doc.new_id()}">']
    out += [f'{pad}        <StraightVertex x="{num(x)}" y="{num(y)}" id="{doc.new_id()}"/>' for x, y in pts]
    out += [f"{pad}    </PointsPath>",
            f'{pad}    <Fill id="{doc.new_id()}">', f'{pad}        <SolidColor colorValue="{colour}" id="{doc.new_id()}"/>', f"{pad}    </Fill>",
            f'{pad}    <Stroke thickness="1.5" join="round" transformAffectsStroke="false" id="{doc.new_id()}">',
            f'{pad}        <SolidColor colorValue="FF1F1F1F" id="{doc.new_id()}"/>', f"{pad}    </Stroke>"]
    if clip_id:
        out.append(f'{pad}    <ClippingShape sourceId="{clip_id}" name="{name.rsplit(" Face", 1)[0]} Clip" id="{doc.new_id()}"/>')
    return out + [f"{pad}</Shape>"]


def add_faces(doc, cube, square_id, sq, colour):
    """The two faces of a cube's front square, drawn over it in its parent, and the mask (the square, 1 unit larger all round, so
    the faces' own outlines show whole). Returns (the face it shows, anchored left; the other, anchored right)."""
    cx, cy, hw, hh = sq
    x0, x1, y0, y1, W = cx - hw, cx + hw, cy - hh, cy + hh, 2 * hw
    other = DARK if colour == LIGHT else LIGHT
    i = doc.idx(square_id)
    pad = _pad(doc, i)
    clip = doc.new_id()
    shown, hidden = doc.new_id(), doc.new_id()
    name = f"{ROOM} {cube.title()}"
    lines = [f'{pad}<Node x="{num(x0)}" name="{name} Face Shown" id="{shown}">']
    lines += _rect_shape(doc, pad + "    ", f"{name} Face Shown Fill", [(0, y0), (W, y0), (W, y1), (0, y1)], colour, clip)
    lines += [f"{pad}</Node>", f'{pad}<Node x="{num(x1)}" scaleX="0" name="{name} Face Turned" id="{hidden}">']
    lines += _rect_shape(doc, pad + "    ", f"{name} Face Turned Fill", [(-W, y0), (0, y0), (0, y1), (-W, y1)], other, clip)
    lines += [f"{pad}</Node>", f'{pad}<Shape name="{name} Clip" id="{clip}">', f'{pad}    <PointsPath isClosed="true" id="{doc.new_id()}">']
    lines += [f'{pad}        <StraightVertex x="{num(x)}" y="{num(y)}" id="{doc.new_id()}"/>'
              for x, y in ((x0 - 1, y0 - 1), (x1 + 1, y0 - 1), (x1 + 1, y1 + 1), (x0 - 1, y1 + 1))]
    lines += [f"{pad}    </PointsPath>", f"{pad}</Shape>"]
    doc.lines[i:i] = lines
    return shown, hidden


def add_lid(doc):
    """The mouth's lid, shut, over the upper cube's dark top (9:5166) in its group. Returns its four corners' ids."""
    i = doc.idx("9:5166")
    pad = _pad(doc, i)
    vids = [doc.new_id() for _ in LID_SHUT]
    lines = [f'{pad}<Shape x="{num(LID_AT[0])}" y="{num(LID_AT[1])}" name="{ROOM} Lid" id="{doc.new_id()}">',
             f'{pad}    <PointsPath isClosed="true" id="{doc.new_id()}">']
    lines += [f'{pad}        <StraightVertex x="{num(x)}" y="{num(y)}" id="{v}"/>' for (x, y), v in zip(LID_SHUT, vids)]
    lines += [f"{pad}    </PointsPath>",
              f'{pad}    <Fill id="{doc.new_id()}">', f'{pad}        <SolidColor colorValue="{LIGHT}" id="{doc.new_id()}"/>', f"{pad}    </Fill>",
              f'{pad}    <Stroke thickness="1.5" cap="round" join="round" transformAffectsStroke="false" id="{doc.new_id()}">',
              f'{pad}        <SolidColor colorValue="FF1F1F1F" id="{doc.new_id()}"/>', f"{pad}    </Stroke>", f"{pad}</Shape>"]
    doc.lines[i:i] = lines
    return vids


# ---- the ball's timeline ------------------------------------------------------------------------------------------------------
def in_mouth(p, v):
    return v[1] > 0 and p[1] >= HIDDEN_Y and 790 < p[0] < 850


def journey():
    """The cycle frame by frame: {frame: (centre, mode)}, the contacts [(cycle time, name, centre, v in, v out, normal)], and per
    fling (pop frame, launch frame, the frame it is out of sight, the frame it is at rest)."""
    frames, contacts, spans = {}, [], []
    for (label, v0, rules, names), pop in zip(FLINGS, POP_AT):
        f_go = pop + LAUNCH_LAG
        path, cons = fly(IN_UP, v0, rules, in_mouth)
        got = [c[1] for c in cons]
        assert got == names, (label, got)
        assert not frames or max(frames) < f_go, label
        n = len(path) - 1                                   # the frame it is out of sight in the mouth
        for k, p in enumerate(path):
            frames[f_go + k] = (p, "air" if 0 < k < n else "hidden")
        p1 = path[-1]
        for u in range(1, CATCH + 1):
            s = smooth(u / CATCH)
            frames[f_go + n + u] = ((p1[0] + (IN_UP[0] - p1[0]) * s, p1[1] + (IN_UP[1] - p1[1]) * s), "hidden")
        contacts += [(f_go + t, name, p, vin, vout, nrm) for t, name, p, vin, vout, nrm in cons]
        spans.append((label, pop, f_go, f_go + n, f_go + n + CATCH, v0, path))
    L = spans[-1][4] + END_BEAT
    for g in range(L + 1):
        frames.setdefault(g, (IN_UP, "hidden"))
    for k in range(len(spans) - 1):
        assert spans[k][4] + 10 < spans[k + 1][1], ("a beat too short", spans[k][0])
    return frames, contacts, spans, L


def lid_angle(g, spans):
    """The lid's opening angle on cycle frame g: pops open (overshoot, settle), open while the ball is out, snaps shut once it is
    out of sight in the mouth."""
    for label, pop, f_go, f_in, f_rest, v0, path in spans:
        snap = f_in + 1
        if pop <= g < pop + POP_T:
            u = (g - pop) / POP_T
            return LID_POP * (1 - (1 - u) ** 3)
        if pop + POP_T <= g < pop + POP_T + SETTLE_T:
            return LID_POP + (LID_OPEN - LID_POP) * smooth((g - pop - POP_T) / SETTLE_T)
        if pop + POP_T + SETTLE_T <= g < snap:
            return LID_OPEN
        if snap <= g < snap + SNAP_T:
            return LID_OPEN * (1 - ((g - snap) / SNAP_T) ** 2)
    return 0.0


def lid_corner(k, a_deg):
    a = math.radians(a_deg)
    x, y = LID_SHUT[k]
    if k in (1, 2):                                          # the front corners swing about the back edge
        bx, by = LID_SHUT[0] if k == 1 else LID_SHUT[3]
        return (bx + DEPTH[0] * math.cos(a), by + DEPTH[1] * math.cos(a) - HEIGHT * math.sin(a))
    return (x, y)


def build(doc, scene, sheet):
    art = BallArt(scene, ROOM)
    n_strokes = scale_room(doc, scene)
    _set_attrs(doc, art.b01, {"scaleX": BALL_SCALE, "scaleY": BALL_SCALE})
    art.k = BALL_SCALE
    art.R, art.Rc = 17.678 * art.k, 17.2 * art.k
    assert abs(art.Rc - RC) < 1e-9
    sx, sy = -0.072021484, 0.096008301
    art.dc = (art.ox + art.k * (sx + CENTER_IN_SCALE[0]), art.oy + art.k * (sy + CENTER_IN_SCALE[1]))
    spin = prepare_ball(doc, art)
    for oid in ("9:5176", "9:5196", LEFT_BOX):               # the old loop's lid slide and box give (re-keyed below where used)
        doc.drop_object(f"{ROOM} Loop", oid)

    frames, contacts, spans, L = journey()
    cyc = Cycle(L)
    for g in range(L + 1):
        cyc.put(g, *frames[g])
    cyc.put(L, IN_UP, "hidden")
    for t, name, p, vin, vout, nrm in contacts:
        if name == "floor":
            cyc.squash(round(t), min(0.12, 0.010 * abs(vin[1]) + 0.01), T=8)

    # turn: from rest a little with the push, at each contact the turn the contact leaves it with (it grips), in the air it keeps
    # it, hidden still; the last beat takes up what is left over to a whole number of turns
    r = art.R
    at_contact = {round(t): spin_rate(vout, nrm, r) for t, name, p, vin, vout, nrm in contacts}
    launches = {f_go: 0.25 * v0[0] / r for label, pop, f_go, f_in, f_rest, v0, path in spans}
    th = [0.0]
    w = 0.0
    for g in range(L):
        if g in launches:
            w = launches[g]
        if g in at_contact:
            w = at_contact[g]
        if cyc.mode[g] == "hidden" and g not in launches:
            w = 0.0
        th.append(th[-1] + w)
    total = th[-1]
    want = round(total / (2 * math.pi)) * 2 * math.pi
    a0 = spans[-1][4] + 1
    for g in range(a0, L + 1):
        th[g] += (want - total) * smooth((g - a0) / (L - a0))

    # the cube turns: one at a time, while the ball is away from the cube, in short bursts
    global TURNS
    TURNS = [("lower cube", 58), ("lid box", 74),               # the beat after the hop (the lockup still on), the ball in the mouth
             ("upper cube", 112), ("upper cube", 134),           # the ball out over the gap: a flick there and back
             ("lower cube", 170),                                # it is on its way back up from the floor
             ("lid box", 222), ("left box", 236),                # the next beat
             ("left box", 318),                                  # it rattles on the mouth's edge
             ("lid box", 360), ("lid box", 384)]                 # the last beat: a flick there and back
    touches = {"left box": ("left box side", "left box corner"), "upper cube": ("upper cube corner",)}
    for cube, s in TURNS:
        for t, name, *_ in contacts:
            assert not (name in touches.get(cube, ()) and s - 6 <= t <= s + TURN + 16), ("a turn while the ball touches", cube, s)
        if cube == "upper cube":
            assert all(cyc.mode[g] == "air" for g in range(s - 4, s + TURN + 4)), ("the upper cube turns with the ball in it", s)
    counts = {}
    for cube, s in TURNS:
        counts[cube] = counts.get(cube, 0) + 1
    odd = [c for c, k in counts.items() if k % 2]
    assert not odd, f"a cube turns an odd number of times: {odd}"
    starts = sorted(s for _, s in TURNS)
    for a_, b_ in zip(starts, starts[1:]):
        assert b_ - a_ >= TURN, ("two turns at once", a_, b_)
    assert starts[-1] + TURN < L

    def face_scale(cube, shown):
        mine = sorted(s for c, s in TURNS if c == cube)

        def fn(g):
            on_shown = True                                   # which face is up
            for k, s in enumerate(mine):
                there = k % 2 == 0
                if g < s:
                    break
                if g < s + TURN:
                    t = math.radians(90 * ease((g - s) / TURN))
                    c, si = math.cos(t), math.sin(t)
                    out_w = c / (c + si)                      # the outgoing face's share, in from the incoming's side
                    sh = out_w if there else 1 - out_w
                    return sh if shown else 1 - sh
                on_shown = not there
            return (1.0 if on_shown else 0.0) if shown else (0.0 if on_shown else 1.0)
        return fn

    # the left box gives a little where the ball hits it: its side pushes it left, its top corner down
    side_hits = [t for t, name, *_ in contacts if name == "left box side"]
    corner_hits = [t for t, name, *_ in contacts if name == "left box corner"]
    box_x = lambda g: LEFT_BOX_REST[0] + sum(dip(g - t, -2.0, 16) for t in side_hits) + sum(dip(g - t, -0.8, 14) for t in corner_hits)
    box_y = lambda g: LEFT_BOX_REST[1] + sum(dip(g - t, 1.6, 14) for t in corner_hits)

    # new art, then its keys
    lid_ids = add_lid(doc)
    faces = {cube: add_faces(doc, cube, sid, sq, col) for cube, (sid, sq, col) in SQUARES.items()}
    pieces = [(LEFT_BOX, "x", box_x, None), (LEFT_BOX, "y", box_y, None)]
    for k in (1, 2):
        for i, prop in enumerate(("x", "y")):
            pieces.append((lid_ids[k], prop, (lambda g, k=k, i=i: lid_corner(k, lid_angle(g, spans))[i]), None))
    for cube, (shown, turned) in faces.items():
        pieces.append((shown, "scaleX", face_scale(cube, True), None))
        pieces.append((turned, "scaleX", face_scale(cube, False), None))
    px = plane_x(scene, sheet, ROOM, "Front")

    def pre(f):
        return (IN_UP[0] + px(f), IN_UP[1]), 1.0, 1.0
    with colour_keys_kept(doc, ROOM):
        emit(doc, art, spin, cyc, th, T0, pre, pieces)

    sec = lambda g: f"{(T0 + g) / 60:.2f} s"
    parts = []
    for label, pop, f_go, f_in, f_rest, v0, path in spans:
        hits = ", ".join(f"{name} {sec(t)}" for t, name, *_ in contacts if f_go <= t <= f_in)
        top = min(p[1] for p in path) - 30.8
        parts.append(f"{label}: lid pops {sec(pop)}, out {sec(f_go)}" + (f", {hits}" if hits else "") +
                     f", back in {sec(f_in)}, lid shut {sec(f_in + 1 + SNAP_T)} (ball top {top:.0f})")
    turns = ", ".join(f"{c} {sec(s)}" for c, s in sorted(TURNS, key=lambda x: x[1]))
    return (f"{ROOM}: scaled {K} about {A} ({n_strokes} strokes kept at their weight), ball {BALL_SCALE}; " + "; ".join(parts) +
            f"; turns: {turns}; loop {L / 60:.2f} s ({L} frames)")


# ---- the room's scale (note 5) ------------------------------------------------------------------------------------------------
def scale_room(doc, scene):
    """The planes' pieces into 0.85 pivots, the drop-ins' falls and the strokes compensated, the ball at 1.7."""
    root = scene.root
    byid = {e.get("id"): e for e in root.iter() if e.get("id")}
    for name, pid in PLANES.items():
        kids = [c for c in byid[pid] if c.tag in ("Node", "Shape")]
        if not kids:
            continue
        piv, _ = doc.wrap_run(kids[0].get("id"), kids[-1].get("id"), f"{ROOM} {name} Scale", *A)
        _set_attrs(doc, piv, {"scaleX": K, "scaleY": K})
    a, b = doc.anim(f"{ROOM} Intro")
    for cid in CUBES:                       # the first y key of each drop: as far above its rest on screen as before, so /K in its own space
        i = next(j for j in range(a, b) if f'objectId="{cid}"' in doc.lines[j])
        e = doc.end(i)
        j = next(j for j in range(i, e) if 'property="y"' in doc.lines[j])
        je = doc.end(j)
        ks = [m for m in range(j, je) if "<KeyFrameDouble" in doc.lines[m]]
        val = lambda m: float(re.search(r' value="([^"]+)"', doc.lines[m]).group(1)) if ' value="' in doc.lines[m] else 0.0
        v0, v1 = val(ks[0]), val(ks[-1])             # the start, and where it lands
        doc.lines[ks[0]] = re.sub(r' value="[^"]+"', f' value="{v1 + (v0 - v1) / K:.4f}"', doc.lines[ks[0]])
    strokes = [s for pid in PLANES.values() for s in byid[pid].iter("Stroke") if s.get("transformAffectsStroke") != "false"]
    sids = {s.get("id") for s in strokes}
    for s in strokes:
        _set_attrs(doc, s.get("id"), {"thickness": float(s.get("thickness", 1)) / K})
    for an in ("Intro", "Loop", "Waiting", "Built"):
        a, b = doc.anim(f"{ROOM} {an}")
        j = a
        while j < b:
            m = re.search(r'objectId="([^"]+)"', doc.lines[j])
            if m and m.group(1) in sids and "<KeyedObject" in doc.lines[j]:
                e = doc.end(j)
                for q in range(j, e):
                    v = re.search(r' value="([^"]+)"', doc.lines[q])
                    if "<KeyFrameDouble" in doc.lines[q] and v:
                        doc.lines[q] = doc.lines[q].replace(v.group(0), f' value="{float(v.group(1)) / K:.4f}"')
                j = e
            j += 1
    return len(sids)


class colour_keys_kept:
    """Workaround (the shared helpers assume every key is a number): rml_edit's rebuild_waiting crashes on the intro's colour key
    (the inner top's SolidColor, 9:5203) and common.rebuild_built drops it. While emit runs, first_values skips non-number keys; after
    it, the room's own colour KeyedObjects are put back into Waiting and Built as they were."""

    def __init__(self, doc, room):
        self.doc, self.room = doc, room

    def _colour_blocks(self, anim):
        a, b = self.doc.anim(anim)
        out, i = [], a + 1
        while i < b:
            line = self.doc.lines[i]
            if line.lstrip().startswith("<KeyedObject"):
                j = self.doc.end(i)
                block = self.doc.lines[i:j + 1]
                if any("KeyFrameColor" in l for l in block):
                    out.append(block)
                i = j + 1
            else:
                i += 1
        return out

    def __enter__(self):
        import rml_edit
        self.saved = {n: self._colour_blocks(f"{self.room} {n}") for n in ("Waiting", "Built")}
        self.orig = rml_edit.Doc.first_values

        def first_values(doc, anim_name):
            import xml.etree.ElementTree as ET
            a, b = doc.anim(anim_name)
            root = ET.fromstring("\n".join(doc.lines[a:b + 1]))
            out = []
            for ko in root.findall("KeyedObject"):
                for kp in ko.findall("KeyedProperty"):
                    keys = sorted(kp.findall("KeyFrameDouble"), key=lambda k: int(k.get("frame", 0)))
                    if keys:
                        out.append((ko.get("objectId"), kp.get("property"), float(keys[0].get("value", 0))))
            return out
        rml_edit.Doc.first_values = first_values
        return self

    def __exit__(self, *exc):
        import rml_edit
        rml_edit.Doc.first_values = self.orig
        if exc[0] is None:
            for n, blocks in self.saved.items():
                _, b = self.doc.anim(f"{self.room} {n}")
                for block in blocks:
                    self.doc.lines[b:b] = block
                    _, b = self.doc.anim(f"{self.room} {n}")
        return False
