"""The Mini: the ball comes out of the upper cube (an open box: its dark top is the inside) and goes behind the box with the lid.

The cube faces are all in the Front Plane, drawn above the ball, and the dark tops in the Floor Plane below it, so a ball low in the
upper cube is hidden by its front face and a ball rising out of it shows over its dark inside; no clip is needed. The box with the lid
reaches x 987, past the safe area, so the ball never goes in it: it stops behind it, on the floor line, where its faces hide it.

The journey: as soon as the upper cube's top has landed (1.83 s) the ball peeks up out of it and drops back in (the lockup is above and
to the left, so it stays clear of it); once the lockup has gone it jumps out over the box's back-left corner, hops along the floor line,
bounces off the side of the left box (which gives a little), rolls right under the upper cube and comes to rest behind the box with the
lid. Out of sight it is put back in the upper cube, and the cycle starts again.
"""
import math

from common import INTRO, BallArt, Cycle, dip, emit, plane_x, prepare_ball

ROOM = "The Mini"
T0 = 110                                   # 1.83 s: the upper cube's top lands at 1.50 s and its squash is over at 1.82 s
IN_BOX = (843.0, 620.0)                    # the ball's centre low in the upper cube: wholly behind its front face
PEEK_VY = -7.75                            # rises 75 px: its top shows over the box, well below the lockup
JUMP_AT = 72                               # cycle frame of the jump out: it reaches the lockup's height after the lockup is gone (3.20 s)
JUMP = (-2.1, -13.5)                       # over the box's back-left corner (757, 524) with 38 px to spare (R 35.4); top at y 357
REST_X = 895.0                             # behind the box with the lid (its right edge at 930, inside the safe area)
PAUSE = 30                                 # frames back in the upper cube before the next peek
FLOOR = 711.5
LEFT_BOX_X = 637.0                         # the left box's right side


def build(doc, scene, sheet):
    art = BallArt(scene, ROOM)
    spin = prepare_ball(doc, art)
    doc.drop_object(f"{ROOM} Loop", "9:5176")          # the old loop's lid slide (the lid stays shut now)
    Rc = art.Rc
    fy = FLOOR - Rc

    # the peek: straight up and back down into the box (caught: the box's inside is soft), during the lockup and well below it
    n_peek = round(2 * -PEEK_VY / 0.40)
    cyc_frames = {}
    for f in range(n_peek + 1):
        cyc_frames[f] = ((IN_BOX[0], IN_BOX[1] + PEEK_VY * f + 0.20 * f * f), "air" if 0 < f < n_peek else "hidden")
    for f in range(n_peek + 1, JUMP_AT):
        cyc_frames[f] = (IN_BOX, "hidden")

    # the jump out and the hops (journey below: flights at 0.40, the first floor bounce keeping 74% and the rest 71%, the left box's side 70% sideways), until a
    # landing turns into a roll; from there it rolls right and friction stops it behind the box with the lid
    fr, hits, (t_r, x_r, v_r) = journey(IN_BOX, JUMP, fy, LEFT_BOX_X + Rc, e_floor=0.71, e_wall=0.70, e_first=0.74)
    t_rf = math.ceil(t_r)
    for f in range(t_rf):
        cyc_frames[JUMP_AT + f] = ((fr[f][0], fr[f][1]), "air")
    cyc_frames[JUMP_AT] = (IN_BOX, "hidden")
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
    f_in = f_rest + 1                                   # out of sight: back into the upper cube
    L = f_in + PAUSE
    cyc = Cycle(L)
    for g in range(L + 1):
        cyc.put(g, *(cyc_frames[g] if g in cyc_frames else (IN_BOX, "hidden")))
    cyc.put(L, IN_BOX, "hidden")

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
    for g in range(f_in, L + 1):
        th[g] += (want - total) * min(1.0, (g - f_in) / 20)

    # the left box gives a little where the ball hits it
    t_w = next(t for t, name, *_ in contacts if name == "left box")
    box_x = lambda g: -174.91251 + dip(g - t_w, -2.0, 16)

    px = plane_x(scene, sheet, ROOM, "Front")

    def pre(f):
        return (IN_BOX[0] + px(f), IN_BOX[1]), 1.0, 1.0
    with colour_keys_kept(doc, ROOM):
        emit(doc, art, spin, cyc, th, T0, pre, [("9:5276", "x", box_x, None)])
    sec = lambda g: f"{(T0 + g) / 60:.2f} s"
    times = ", ".join(f"{name} {sec(t)}" for t, name, *_ in contacts)
    return (f"{ROOM}: peeks out of the upper cube {sec(0)} to {sec(n_peek)}; jumps out {sec(JUMP_AT)}; {times}; rolls right and stops "
            f"behind the box with the lid {sec(f_rest)}; back in the upper cube (unseen), peeks again {PAUSE / 60:.2f} s later; loop {L / 60:.2f} s")


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
