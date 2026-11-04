"""Spelling Bee: the ball shoots out of the #1 mug, plays on the floating yellow hexes and drops back into the mug.

The mug is drawn in two halves around the ball (Mug 1, its front wall, above; Mug 2, its inside and back, below), so a ball sitting
low in it is hidden by the front wall and a ball rising out of it shows over the dark inside. The floating hexes sit further back:
the ball passes in front of their faces, lands on the right hex's top and bounces off the left hex's lower right face.

The journey (Demetre's note, 2026-11-04): it shoots up out of the mug (1.83 s, once the mug has landed and settled), lands on top of
the right hex and hops there, rolls slowly along its top (the idle), runs down its left slant onto the floor line, bounces up into the
left hex's lower right face, which knocks it back to the right, and drops into the mug off the far side of the rim. Low in the mug,
out of sight, it waits and shoots out again. Every flight falls at 0.40; every contact keeps 72 to 85 percent of its speed.
"""
import math

from common import BallArt, Cycle, dip, emit, intro_series, plane_x, prepare_ball
from sim import World

ROOM = "Spelling Bee"
T0 = 110                                   # 1.83 s: the mug landed at 1.50 s and its squash is over at 1.82 s
IN_MUG = (807.0, 710.0)                    # the ball's centre low in the mug: wholly behind its front wall
POP = (-0.2, -12.8)                        # its top stays under y 482, clear of the lockup (gone at 3.20 s anyway)
PAUSE = 40                                 # frames low in the mug before the next shot


def surfaces(w):
    S = dict(
        R_top=w.seg((774, 553.8), (846.4, 553.8), name="the right hex's top", e=0.8),
        R_sL=w.seg((774, 553.8), (755.2, 586.2), name="the right hex's left slant", e=0.8),
        R_sR=w.seg((846.4, 553.8), (865.3, 586.2), name="the right hex's right slant", e=0.8),
        L_top=w.seg((590.5, 595.2), (641.8, 595.2), name="the left hex's top", e=0.8),
        L_sR=w.seg((641.8, 595.2), (674.5, 627.1), name="the left hex's right slant", e=0.8),
        L_lowR=w.seg((674.5, 627.1), (664.7, 658.9), name="the left hex's lower right face", e=0.9, kt=0.97, n=(0.955, 0.294)),
        L_bot=w.seg((664.7, 658.9), (613.4, 658.9), name="the left hex's bottom", e=0.8, n=(0.0, 1.0)),
        floor=w.seg((623.1, 711.8), (935, 711.8), name="the floor", e=0.88),
        corner=w.circ((623.1, 694.2), 0.5, name="the brick step", e=0.85, kt=0.97),
        step=w.seg((593.1, 694.2), (623.1, 694.2), name="the brick step's top"),
        rimL=w.circ((768.5, 663.0), 2.0, name="the mug's near rim", e=0.75),
        rimR=w.circ((846.0, 663.0), 2.0, name="the mug's far rim", e=0.75),
    )
    return list(S.values())


def caught_at(path):
    for f in range(41, len(path)):
        (x, y), _ = path[f]
        if 796 <= x <= 818 and y >= 668 and y > path[f - 1][0][1]:
            return f
    raise SystemExit("Spelling Bee: the journey never drops back into the mug")


def build(doc, scene, sheet):
    art = BallArt(scene, ROOM)
    spin = prepare_ball(doc, art)
    for oid in ("9:506", "9:467"):        # the old loop's hex drifts (reactions to the old journey)
        doc.drop_object(f"{ROOM} Loop", oid)
    w = World(art.Rc)
    s = w.s
    ev, path = w.run(IN_MUG, POP, surfaces(w), frames=600, max_events=30, t_max=620)
    f_c = caught_at(path)
    hits = [(e[1], e[2].name, (e[4][0] / s, e[4][1] / s), (e[5][0] / s, e[5][1] / s)) for e in ev if e[0] == "hit" and e[1] < f_c]
    # the catch: from where it drops into the mug it keeps falling (0.40) to the bottom, out of sight, and stops there (the mug catches
    # it); while it rests, out of sight, it moves to its starting place for the next shot
    (cx, cy), (px_, py_) = path[f_c][0], path[f_c - 1][0]
    vx, vy = cx - px_, cy - py_
    fall = []
    while cy < IN_MUG[1]:
        vy += 0.40
        cx, cy = min(819.0, max(795.0, cx + vx)), min(IN_MUG[1], cy + vy)
        fall.append((cx, cy))
    L = f_c + len(fall) + PAUSE
    cyc = Cycle(L)
    cyc.put(0, IN_MUG, "hidden")
    for f in range(1, f_c + 1):
        p, mode = path[f]
        cyc.put(f, p, "roll" if mode == "roll" else "air")
    for u, q in enumerate(fall, 1):
        cyc.put(f_c + u, q, "hidden")
    f_bottom = f_c + len(fall)
    for f in range(f_bottom + 1, L + 1):
        cyc.put(f, fall[-1] if f < f_bottom + PAUSE // 2 else IN_MUG, "hidden")
    SINK_ = len(fall)
    # a squash on every landing, in proportion to the speed into the surface (single pulses, 12 frames)
    for t, name, vin, vout in hits:
        hit = math.hypot(*vin) if "rim" in name or "face" in name else abs(vin[1])
        cyc.squash(round(t), min(0.13, 0.011 * hit + 0.005), T=12)
    # the turn: rolling turns with the distance, in the air it keeps the turn it had when it left a surface (it grips at each contact)
    r = art.R
    grip = {round(t): vout[0] / r for t, name, vin, vout in hits}
    th = [0.0]
    w_now = 0.0
    for g in range(L):
        m = cyc.mode[g]
        dx = cyc.c[g + 1][0] - cyc.c[g][0]
        if g in grip:
            w_now = grip[g]
        if m == "roll":
            w_now = dx / r
        elif m == "air":
            if g == 1:
                w_now = 0.25 * dx / r
        else:
            w_now = 0.0
        th.append(th[-1] + w_now)
    total = th[-1]
    want = round(total / (2 * math.pi)) * 2 * math.pi
    for g in range(f_bottom, L + 1):
        th[g] += (want - total) * min(1.0, (g - f_bottom) / 20)
    # the hexes react: the right hex dips under the first two landings on its top, the left hex tips back from the knock
    tops = [t for t, name, *_ in hits if name == "the right hex's top"]
    knock = next(t for t, name, *_ in hits if name == "the left hex's lower right face")
    r_y = lambda g: 618.633 + dip(g - tops[0], 2.4, 22) + dip(g - tops[1], 1.2, 18)
    l_rot = lambda g: dip(g - knock, -0.035, 28)
    r_own = intro_series(scene, sheet, ROOM, "9:553", "y")
    # before T0 the ball sits low in the mug and rides it in (the pan, the drop and the landing squash)
    px = plane_x(scene, sheet, ROOM, "Front")
    my = intro_series(scene, sheet, ROOM, "9:463", "y")
    msx = intro_series(scene, sheet, ROOM, "9:463", "scaleX")
    msy = intro_series(scene, sheet, ROOM, "9:463", "scaleY")
    piv = (747.501, 575.111)

    def pre(f):
        dy = my(f) - piv[1]
        cx = piv[0] + msx(f) * (IN_MUG[0] - piv[0]) + px(f)
        cy = piv[1] + dy + msy(f) * (IN_MUG[1] - piv[1])
        return (cx, cy), 1.0, 1.0
    pieces = [("9:553", "y", r_y, r_own), ("9:504", "rotation", l_rot, None)]
    emit(doc, art, spin, cyc, th, T0, pre, pieces)
    seen, beats = set(), []
    for t, name, *_ in hits:
        if name not in seen or name == "the floor":
            beats.append(f"{name} {sec(t)}")
            seen.add(name)
    return (f"{ROOM}: shoots out of the mug at {sec(1)}; " + ", ".join(beats) + f"; drops into the mug at {sec(f_c)}; "
            f"out again {(SINK_ + PAUSE) / 60:.2f} s later; loop {L / 60:.2f} s")


def sec(g):
    return f"{(T0 + g) / 60:.2f} s"
