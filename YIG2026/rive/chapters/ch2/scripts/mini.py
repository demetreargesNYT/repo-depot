"""The Mini (Demetre's note 5, 2026-11-04): every piece 15% smaller, and a longer loop that plays hide and seek with two boxes.

Scale: each of the room's planes holds its pieces in a pivot at (747.5, 711.5), the room's middle on the floor line, scaled 0.85, so
everything still stands on the floor line; the ball is 1.7 (was 2). The cubes that drop in fall 800/0.85 in their own space, so on
screen they still drop 800 from above the artboard on the same timing and land where they now stand; their strokes are 1/0.85 thicker
in their own space, so the lines keep the weight they have in every other room. The lockup is not touched.

Hiding: the cube faces are in the Front Plane, drawn above the ball, and the boxes' dark insides in the Floor Plane, below it. So a
ball low in a box is hidden by the box's front, and a ball rising out of it shows over its dark inside; the room's own drawing order is
the mask, cut exactly to each box (no clip shape is needed, so nothing can cut the ball anywhere else).

The journey (times on a first visit, from the scene being set):
  1.83 s  as soon as the upper cube's dark top has landed, the ball peeks up out of the upper cube (an open box) and drops back in;
          the lockup is above it, so it stays well below it
  3.03 s  once the lockup has gone it jumps out over the box's back-left corner, hops along the floor line, bounces off the side of the
          left box (which gives a little), hops and rolls right under the upper cube and stops behind the box with the lid
  then    out of sight it drops into that box; the lid slides open, the ball pops straight up out of it and falls back in (caught: a
          box's inside is soft), and the lid slides shut
  then    out of sight it goes back to the upper cube, and after a pause peeks again
The upper cube sits flush on the lid box's front-left, so a ball leaving the lid box can't go left over it (its edge would be 4 px
from the cube's side until it had risen past the cube's top): it goes straight up and down.
"""
import math
import re

from common import CENTER_IN_SCALE, BallArt, Cycle, _set_attrs, dip, emit, plane_x, prepare_ball

ROOM = "The Mini"
T0 = 110                                   # 1.83 s: the upper cube's top lands at 1.50 s and its squash is over at 1.82 s
A = (747.5, 711.5)                         # the scale's anchor: the room's middle, on the floor line
K = 0.85
PLANES = {"Front": "9:5695", "Floor": "9:5694", "Wall": "9:5697"}
CUBES = ("9:5206", "9:5208", "9:5210", "9:5212")    # the four drop-ins (their Art offsets are -760)
BALL_SCALE = 1.7
IN_UP = (829.0, 632.0)                     # low in the upper cube (front 788.5 to 870, 590 to 671): wholly behind its front face
IN_LID = (904.0, 712.0)                    # low in the box with the lid (front 870 to 951, 671 to 753); right edge 934, in the safe area
PEEK_VY = -7.75                            # the peek rises 75 px (its top at y 527)
JUMP_AT = 72                               # the jump out: it reaches the lockup's height at 3.32 s, after the lockup has gone (3.20 s)
JUMP = (-2.1, -11.9)                       # over the upper cube's back-left corner (755.6, 552.1) with 32 px to spare (R 30.05); top at y 425
REST_X = 895.0                             # behind the box with the lid, on the floor line
LID_OPEN = 20                              # frames for the lid to slide open (as the old loop did), and 18 to slide shut
POP_VY = -11.0                             # the pop out of the lid box rises 151 px (its top at y 531)
PAUSE = 40                                 # frames back in the upper cube before the next peek
LID_REST, LID_OUT = (920.177, 641.987), (958.5, 686.5)   # the lid's own position shut and slid open (its space; as the old loop had)
FLOOR = 711.5
LEFT_BOX_X = 637.0                         # the left box's right side (its own space)


def S(x, y):
    return (A[0] + K * (x - A[0]), A[1] + K * (y - A[1]))


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


def build(doc, scene, sheet):
    art = BallArt(scene, ROOM)
    n_strokes = scale_room(doc, scene)
    _set_attrs(doc, art.b01, {"scaleX": BALL_SCALE, "scaleY": BALL_SCALE})
    art.k = BALL_SCALE
    art.R, art.Rc = 17.678 * art.k, 17.2 * art.k
    sx, sy = -0.072021484, 0.096008301
    art.dc = (art.ox + art.k * (sx + CENTER_IN_SCALE[0]), art.oy + art.k * (sy + CENTER_IN_SCALE[1]))
    spin = prepare_ball(doc, art)
    Rc = art.Rc
    fy = FLOOR - Rc
    cyc_frames = {}

    # 1. the peek out of the upper cube, and the wait before the jump
    n_peek = round(2 * -PEEK_VY / 0.40)
    for f in range(n_peek + 1):
        cyc_frames[f] = ((IN_UP[0], IN_UP[1] + PEEK_VY * f + 0.20 * f * f), "air" if 0 < f < n_peek else "hidden")
    for f in range(n_peek + 1, JUMP_AT):
        cyc_frames[f] = (IN_UP, "hidden")

    # 2. the jump out, the hops and the left box (journey below), then a roll right that friction stops behind the box with the lid
    wall_x = S(LEFT_BOX_X, 0)[0] + Rc
    fr, hits, (t_r, x_r, v_r) = journey(IN_UP, JUMP, fy, wall_x, e_floor=0.71, e_wall=0.70, e_first=0.74)
    t_rf = math.ceil(t_r)
    for f in range(t_rf):
        cyc_frames[JUMP_AT + f] = ((fr[f][0], fr[f][1]), "air")
    cyc_frames[JUMP_AT] = (IN_UP, "hidden")
    x0 = x_r + v_r * (t_rf - t_r)
    a = v_r * v_r / (2 * (REST_X - x0))
    t_stop = v_r / a
    f = JUMP_AT + t_rf
    u = 0
    while u < t_stop:
        cyc_frames[f] = ((x0 + v_r * u - 0.5 * a * u * u, fy), "roll")
        f += 1
        u += 1
    f_rest = f
    cyc_frames[f_rest] = ((REST_X, fy), "rest")

    # 3. out of sight into the box with the lid; the lid slides open, the ball pops up and falls back in, the lid slides shut
    f_lid = f_rest + 6
    f_pop = f_lid + 16
    n_pop = round(2 * -POP_VY / 0.40)
    for g in range(f_rest + 1, f_pop):
        cyc_frames[g] = (IN_LID, "hidden")
    for u in range(n_pop + 1):
        cyc_frames[f_pop + u] = ((IN_LID[0], IN_LID[1] + POP_VY * u + 0.20 * u * u), "air" if 0 < u < n_pop else "hidden")
    f_shut = f_pop + n_pop + 4
    f_shut_end = f_shut + 18
    for g in range(f_pop + n_pop + 1, f_shut_end + 1):
        cyc_frames[g] = (IN_LID, "hidden")

    # 4. out of sight back to the upper cube, and the pause before the next peek
    L = f_shut_end + 1 + PAUSE
    cyc = Cycle(L)
    for g in range(L + 1):
        cyc.put(g, *(cyc_frames[g] if g in cyc_frames else (IN_UP, "hidden")))
    cyc.put(L, IN_UP, "hidden")

    contacts = [(JUMP_AT + t, name, None, vout, vin) for t, name, vin, vout in hits]
    for t, name, p, vout, vin in contacts:
        n = abs(vin[0]) if name == "left box" else abs(vin[1])
        cyc.squash(round(t), min(0.14, 0.012 * n + 0.01), T=12)

    # turn: rolling with the distance, in the air the turn it had when it last touched (grip), from rest a little from the push
    r = art.R
    contact_w = {round(t): vout[0] / r for t, name, p, vout, vin in contacts}
    th = [0.0]
    w_now = 0.0
    for g in range(L):
        m = cyc.mode[g]
        dx = cyc.c[g + 1][0] - cyc.c[g][0]
        if g in contact_w:
            w_now = contact_w[g]
        if m == "roll":
            w_now = dx / r
        elif m == "air":
            if cyc.mode.get(g - 1) == "hidden":
                w_now = 0.25 * dx / r
        else:
            w_now = 0.0
        th.append(th[-1] + w_now)
    total = th[-1]
    want = round(total / (2 * math.pi)) * 2 * math.pi
    for g in range(f_rest + 1, L + 1):
        th[g] += (want - total) * min(1.0, (g - f_rest - 1) / 20)

    # pieces: the left box gives a little where the ball hits it; the lid slides open and shut around the pop
    t_w = next(t for t, name, *_ in contacts if name == "left box")
    box_x = lambda g: -174.91251 + dip(g - t_w, -2.0, 16)

    def lid(g, i):
        if f_lid <= g < f_lid + LID_OPEN:
            s = smooth((g - f_lid) / LID_OPEN)
        elif f_lid + LID_OPEN <= g < f_shut:
            s = 1.0
        elif f_shut <= g < f_shut_end:
            s = 1 - smooth((g - f_shut) / 18)
        else:
            s = 0.0
        return LID_REST[i] + (LID_OUT[i] - LID_REST[i]) * s
    px = plane_x(scene, sheet, ROOM, "Front")

    def pre(f):
        return (IN_UP[0] + px(f), IN_UP[1]), 1.0, 1.0
    pieces = [("9:5276", "x", box_x, None), ("9:5176", "x", lambda g: lid(g, 0), None), ("9:5176", "y", lambda g: lid(g, 1), None)]
    with colour_keys_kept(doc, ROOM):
        emit(doc, art, spin, cyc, th, T0, pre, pieces)
    sec = lambda g: f"{(T0 + g) / 60:.2f} s"
    times = ", ".join(f"{name} {sec(t)}" for t, name, *_ in contacts)
    return (f"{ROOM}: scaled {K} about {A} ({n_strokes} strokes kept at their weight), ball {BALL_SCALE}; peeks out of the upper cube "
            f"{sec(0)} to {sec(n_peek)}; jumps out {sec(JUMP_AT)}; {times}; rolls right and stops behind the lid box {sec(f_rest)}; lid "
            f"opens {sec(f_lid)}, pops out {sec(f_pop)}, back in {sec(f_pop + n_pop)}, lid shut {sec(f_shut_end)}; peeks again "
            f"{(L - f_shut_end) / 60:.2f} s after; loop {L / 60:.2f} s")


def smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


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
        orig = self.orig

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


# ---- the journey after the jump, by hand -------------------------------------------------------------------------------------
# The Mini's journey after the jump, by hand: parabola flights at 0.40, floor bounces, the left box's side as a vertical wall.
# A floor landing becomes a roll once the ball would keep at least half of its speed sideways (lands and rolls).

G_ = 0.40                                   # the project's one gravity, per frame squared


def segdist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy)))
    return math.dist(p, (a[0] + t * dx, a[1] + t * dy))


def journey(p0, v0, fy, wall_x, e_floor=0.72, e_wall=0.8, kt=0.97, sub=16, e_first=None):
    """Frames from the jump: [(x, y, mode)] until the landing that turns into a roll; contacts [(t, name, vin, vout)]; the roll's start
    (t, x, vx)."""
    x, y = p0
    vx, vy = v0
    dt = 1.0 / sub
    t = 0.0
    out = [(x, y, "air")]
    contacts = []
    nxt = 1
    while t < 600:
        x += vx * dt
        vy += G_ * dt
        y += vy * dt - 0.5 * G_ * dt * dt
        t += dt
        if vx < 0 and x <= wall_x:
            x = wall_x + (wall_x - x)
            vin = (vx, vy)
            vx = -e_wall * vx
            vy = kt * vy
            contacts.append((t, "left box", vin, (vx, vy)))
        if vy > 0 and y >= fy:
            y = fy - (y - fy)
            vin = (vx, vy)
            if abs(vx) >= 0.5 * math.hypot(vx, vy) * 1.0 and abs(vy) < 4.0:
                contacts.append((t, "floor (rolls)", vin, (kt * vx, 0.0)))
                return out, contacts, (t, x, kt * vx)
            e = e_first if (e_first and not any(c[1] == "floor" for c in contacts)) else e_floor
            vx, vy = kt * vx, -e * vy
            contacts.append((t, "floor", vin, (vx, vy)))
        if t >= nxt - 1e-9:
            out.append((x, y, "air"))
            nxt += 1
    raise RuntimeError("never settled")
