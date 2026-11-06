"""Regenerates the whole Chapter 3 loop (rejected version): refuses chapters/ch3/scene.rml once it has changed since commit 340b2c7 (tools/regen_guard.py).

REJECTED (Demetre, 2026-11-03: bring in c3s1 itself instead; see ch3_c3s1_import.py). Kept because it built the disco ball's
facet spin and sparkles (facet_keys, SPARKS, spark), which stay in the room; the saved copy is chapters/ch3/disco-saved.json.

Chapter 3 card 1 (scene chapter-3): the illustrator's ball journey (their file 2668591, artboard NYT_YIG_c3s1, animation "Ball"),
brought into the room under the ball rules, with the disco ball's spin and sparkle (Demetre, 2026-11-03).

    python3 chapters/ch3/scripts/ch3_chapter3_loop.py            dry run: prints each beat, the contacts and the clearances, writes nothing
    python3 chapters/ch3/scripts/ch3_chapter3_loop.py --write    rewrites chapters/ch3/scene.rml (run it once, on the file as it was at
                                                  rive/ch3-chapter-1-polish-startscene plus the disco ball's earlier drop:
                                                  it wraps nodes in pivots, so it is not safe to run twice)

The journey keeps the illustrator's beats where the room's geometry allows them. The ball is the sun in the picture: it rests on
the hill, hops out of the picture onto the ring box (the lid pops open and the ring peeks out), is tossed onto the little calendar
frame, settles, springs up onto the disco ball's shoulder (the ball sparkles and swings a little) and glances off back into the
picture, where it sets behind the hill, out of sight. It rises again from behind the hill and settles on its crest. Their joystick
rig, their scale changes (0.7 to 1.92 times) and their beats that the room has no space for are not brought in: the mobile hangs 17
units above the crib and the calendar 17 above the cage, less than the ball's size, so the ball cannot pass there.

Depth: inside the picture the ball is the distant sun (0.7 times its size), drawn behind the picture's front frame and hill and
clipped to the picture's window; in the room it is full size and in front of the frame. The switch between the two is made while the
ball is wholly inside the window and clear of the hill, so it cannot be seen (the picture's front frame and hill have back copies,
Pictures 3 and 4, that stay put).

Physics (CLAUDE.md): one gravity, 0.40 a frame squared, on the ball's node (its contact point); the toss off the ring box is the
lid's spring and returns less than it received; the hop out of the picture and the jump off the calendar are the ball's own effort,
each after a pause; the glance off the disco ball keeps about 85 percent of its speed. Times printed are Finesse-panel timecodes.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
import math
import sys

from ball_motion import pulse, smooth, spring
from rml_edit import Doc, bake, num
import regen_guard
WRITTEN_AGAINST = "340b2c7"     # rive/ch3-chapter-1-polish-startscene (see above)
from rml_read import Scene, chapter_dir

SCENE = chapter_dir("ch3") / "scene.rml"
ROOM = "Chapter 3"
INTRO = 192
G = 0.40
R = 17.68                       # the ball's radius at full size (its node is the contact point, the centre is R above it)
SUN = 0.7                       # its size inside the picture
L = 416                         # the cycle, frames: 16 steps of the disco ball's spin (26 frames each)
SPIN_STEP = 26
T0 = 120                        # intro frame of the hop out of the picture (2.0 s): the picture has landed and settled

# ---- the room (world coordinates once the room has arrived; read off the art and a render) ----------------------------------------
WINDOW = (574.25, 515.75, 643.75, 571.25)        # the picture's window (inside the frame)
HILL = [(574.0, 558.5), (596.0, 554.0), (604.0, 551.0), (608.0, 549.0), (612.0, 548.0), (624.0, 548.0), (628.0, 549.0), (643.75, 555.5)]
CREST = (618.0, 548.0)                           # where the sun sits
RING_TOP = 639.0                                 # the ring box's flat top, x 622 to 639
RING_HINGE = (617.0, 651.5)                      # Ring_lid's own origin
CAL = (667.8, 571.0, 704.0, 611.2)               # the little calendar frame (Fame_02)
DISCO_PIVOT = (748.75, 412.5)                    # the hanging group's own origin (the top of the line)
DISCO_C = (748.75, 497.2)                        # the disco ball's centre at rest
DISCO_R = 45.05
OBSTACLES = {                                    # boxes (x0, y0, x1, y1) and circles ((x, y), r) the ball must not touch in flight
    "calendar": ("box", CAL), "clock": ("box", (844.3, 476.7, 893.3, 512.3)), "ring box": ("box", (616.0, 639.0, 644.5, 659.0)),
    "FIRST": ("box", (526.0, 619.0, 610.0, 659.0)), "cage": ("box", (653.0, 629.0, 714.0, 712.0)), "line": ("box", (748.0, 397.0, 749.5, 452.2)),
    "disco ball": ("circ", (DISCO_C, DISCO_R)), "mount": ("box", (736.0, 397.0, 762.0, 412.5)),
}

# ---- ids in chapters/ch3/scene.rml --------------------------------------------------------------------------------------------------
BALL, BALL_ART, HIGHLIGHT, BODY = "9:2100", "9:2101", "9:2102", "9:2108"
FLOOR_PLANE, PICTURE_2, DISCO_WRAP = "9:3101", "9:871", "9:689"
FRAME_F, LAND_F = "9:691", "9:741"               # Picture 1 and 2's art: the front frame and the front hill
PICTURE_6, SKY = "9:879", "9:859"                # Picture 6 (the sky) and its wrapper, which drops and squashes with the picture
PIC_PIVOT = (606.25, 581.25)
RING_LID, JEM = "9:1386", "9:1422"
FAME_02 = "9:881"
DISCO_SWING, DISCO_BALL, BURST, BURST_PATH = "9:2", "9:33", "9:3", "9:4"
LIGHT, DARK = "FFDFDBD7", "FF1F1F1F"


# ================================================================================================= the journey
def parabola(p0, p1, n):
    """The node's flight from p0 to p1 in n frames under G: positions at frames 0..n, and the velocities leaving and arriving."""
    vx = (p1[0] - p0[0]) / n
    vy = (p1[1] - p0[1]) / n - 0.5 * G * n
    pts = [(p0[0] + vx * t, p0[1] + vy * t + 0.5 * G * t * t) for t in range(n + 1)]
    return pts, (vx, vy), (vx, vy + G * n)


def flight_from(p0, v0, n):
    return [(p0[0] + v0[0] * t, p0[1] + v0[1] * t + 0.5 * G * t * t) for t in range(n + 1)]


def reflect(v, nrm, e, kt=0.95):
    vn = v[0] * nrm[0] + v[1] * nrm[1]
    vt = (v[0] - vn * nrm[0], v[1] - vn * nrm[1])
    return (kt * vt[0] - e * vn * nrm[0], kt * vt[1] - e * vn * nrm[1])


def hill_y(x):
    for (x0, y0), (x1, y1) in zip(HILL, HILL[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return HILL[0][1] if x < HILL[0][0] else HILL[-1][1]


def inside_window(c, r, pad=0.8):
    return WINDOW[0] + r + pad <= c[0] <= WINDOW[2] - r - pad and WINDOW[1] + r + pad <= c[1]


def above_hill(c, r, pad=1.5):
    return all(c[1] + math.sqrt(max(r * r - (x - c[0]) ** 2, 0.0)) + pad <= hill_y(x) for x in [c[0] + r * k / 8 for k in range(-8, 9)])


def behind_hill(c, r):
    """Hidden: every point of the ball is below the hill line (behind the front hill) or below the window (clipped)."""
    top = c[1] - r
    return all(c[1] - math.sqrt(max(r * r - (x - c[0]) ** 2, 0.0)) - 1.0 >= hill_y(x) or c[1] - math.sqrt(max(r * r - (x - c[0]) ** 2, 0.0)) >= WINDOW[3]
               for x in [c[0] + r * k / 8 for k in range(-8, 9)]) and top > 0


def gap(c, r, ob):
    kind, g = ob
    if kind == "box":
        x0, y0, x1, y1 = g
        dx = max(x0 - c[0], 0.0, c[0] - x1)
        dy = max(y0 - c[1], 0.0, c[1] - y1)
        return math.hypot(dx, dy) - r
    (cx, cy), rr = g
    return math.hypot(c[0] - cx, c[1] - cy) - r - rr


class Journey:
    """The ball over one cycle: node position, size, whether it is inside the picture, and the moments things happen."""

    def __init__(self):
        self.node, self.size, self.inside, self.mode = {}, {}, {}, {}
        self.sx = {f: 1.0 for f in range(L + 1)}
        self.sy = {f: 1.0 for f in range(L + 1)}
        self.at = {}
        self.notes = []
        self.kick = {}

    def put(self, f, p, s, inside, mode):
        self.node[f], self.size[f], self.inside[f], self.mode[f] = p, s, inside, mode

    def centre(self, f):
        (x, y), s = self.node[f], self.size[f]
        return (x, y - R * s)

    def squash(self, f, a):
        for k in range(30):
            if f + k <= L:
                p = pulse(k)
                self.sy[f + k] *= 1 - a * p
                self.sx[f + k] *= 1 + 0.7 * a * p


def build():
    j = Journey()
    f = 0
    # 1. the hop out of the picture, from the crest onto the ring box (own effort, after the rest that ends the cycle)
    n1 = 34
    land1 = (631.0, RING_TOP)
    pts, v_out1, v_in1 = parabola(CREST, land1, n1)
    for t, p in enumerate(pts):
        u = smooth(min(t / (n1 * 0.8), 1.0))
        j.put(f + t, p, SUN + (1 - SUN) * u, t < 2, "air")
    j.at["hop"] = f
    j.at["out of the picture"] = f + 2
    f += n1
    j.at["ring box"] = f
    # 2. the lid's spring tosses it onto the calendar (it returns less than it received)
    n2 = 27
    land2 = (669.5, CAL[1])
    pts, v_out2, v_in2 = parabola(land1, land2, n2)
    for t, p in enumerate(pts):
        j.put(f + t, p, 1.0, False, "air")
    j.notes.append(("ring box", v_in1, v_out2, (0.0, -1.0)))
    f += n2
    j.at["calendar"] = f
    # 3. a small bounce on the calendar, then it settles
    n3 = 12
    land3 = (674.0, CAL[1])
    pts, v_out3, v_in3 = parabola(land2, land3, n3)
    for t, p in enumerate(pts):
        j.put(f + t, p, 1.0, False, "air")
    j.notes.append(("calendar", v_in2, v_out3, (0.0, -1.0)))
    f += n3
    j.at["settles on the calendar"] = f
    rest = 19
    for t in range(rest):
        j.put(f + t, land3, 1.0, False, "rest")
    f += rest
    # 4. the jump onto the disco ball's shoulder (own effort): up, then down onto its upper left
    j.at["jumps"] = f
    phi = math.radians(38.0)                           # the contact's direction from the disco ball's centre, above the left
    dd = DISCO_R + R
    hit_c = (DISCO_C[0] - dd * math.cos(phi), DISCO_C[1] - dd * math.sin(phi))
    hit = (hit_c[0], hit_c[1] + R)
    n4 = 36
    pts, v_out4, v_in4 = parabola(land3, hit, n4)
    for t, p in enumerate(pts):
        j.put(f + t, p, 1.0, False, "air")
    f += n4
    j.at["disco ball"] = f
    nrm = (-math.cos(phi), -math.sin(phi))
    v5 = reflect(v_in4, nrm, 0.86)
    j.notes.append(("disco ball", v_in4, v5, nrm))
    # 5. it glances off, back into the picture, shrinking to the sun's size; the switch to "inside" when it is wholly in the window
    #    and clear of the hill; it sets behind the hill until it is out of sight
    n5 = 70
    pts = flight_from(hit, v5, n5)
    switched = hidden = None
    for t, p in enumerate(pts):
        u = smooth(min(t / 22.0, 1.0))
        s = 1.0 - (1 - SUN) * u
        c = (p[0], p[1] - R * s)
        if switched is None and inside_window(c, R * s) and above_hill(c, R * s):
            switched = t
        if switched is not None and hidden is None and behind_hill(c, R * s):
            hidden = t
        j.put(f + t, p, s, switched is not None, "air")
        if hidden is not None:
            break
    if switched is None or hidden is None:
        raise SystemExit(f"the glance does not set behind the hill (switched {switched}, hidden {hidden}); last centre {c}")
    j.at["into the picture"] = f + switched
    j.at["out of sight"] = f + hidden
    f += hidden
    # 6. out of sight behind the hill (the spin's leftover turn goes here), then the sunrise and the rest on the crest
    low = (CREST[0], 640.0)                     # below the window: clipped (the jump there is out of sight)
    night = 30
    for t in range(1, night + 1):
        j.put(f + t, low, SUN, True, "hidden")
    f += night + 1
    j.at["sunrise"] = f
    n6 = 54
    for t in range(n6 + 1):
        u = 0.5 - 0.5 * math.cos(math.pi * t / n6)
        j.put(f + t, (CREST[0], low[1] + (CREST[1] - low[1]) * u), SUN, True, "rise")
    f += n6
    j.at["on the crest"] = f
    while f < L:
        f += 1
        j.put(f, CREST, SUN, True, "rest")
    assert f == L, f
    j.put(L, CREST, SUN, True, "rest")
    j.node[0] = CREST
    j.mode[0] = "rest"
    for name, a in (("ring box", 0.10), ("calendar", 0.07), ("settles on the calendar", 0.04), ("disco ball", 0.05)):
        j.squash(j.at[name], a)
    j.v = dict(hop=v_out1, toss=v_out2, jump=v_out4, glance=v5)
    return j


def spin_of(j):
    """The ball's turn on every cycle frame (radians, clockwise positive): no rolling in this journey, so it is the air spin it leaves
    a surface with (a little from each push), changed a little by the glance; at rest it stops; the leftover to whole turns is
    taken out while it is out of sight behind the hill."""
    th = [0.0]
    w = 0.0
    for f in range(L):
        m, m_next = j.mode[f], j.mode.get(f + 1)
        if f in (j.at["hop"], j.at["ring box"], j.at["calendar"], j.at["jumps"], j.at["disco ball"]):
            v = j.v["hop"] if f == j.at["hop"] else None
            nxt = j.node[f + 1]
            vx = nxt[0] - j.node[f][0]
            w = 0.5 * vx / (R * j.size[f])
            if f == j.at["disco ball"]:
                w = -0.05          # the glance off the upper left sends it turning the other way, a little
        if m in ("rest", "hidden", "rise") or (m_next in ("rest",) and m != "air"):
            w = 0.0
        th.append(th[-1] + (w if m == "air" else 0.0))
    resid = th[L] - 2 * math.pi * round(th[L] / (2 * math.pi))
    a, z = j.at["out of sight"] + 2, j.at["sunrise"] - 2
    return [t - resid * (smooth((f - a) / (z - a)) if f <= z else 1.0) for f, t in enumerate(th)], resid


# ================================================================================================= reactions
def lid(k):
    """The ring box's lid (radians, its own rotation): pops open as the ball lands, then falls shut."""
    if k <= 0:
        return 0.0
    if k <= 9:
        return -0.42 * math.sin(0.5 * math.pi * k / 9)
    u = k - 9
    if u <= 22:                                     # falls shut, speeding up like a lid dropping
        return -0.42 * (1 - (u / 22) ** 2)
    return 0.0


def jem(k):
    """The ring peeks up while the lid is open (Jem y, from -3)."""
    if k <= 0 or k >= 22:
        return -3.0
    return -3.0 - 3.25 * math.sin(math.pi * k / 22) ** 1.5


def disco_swing(k):
    """A small damped swing (radians) after the ball pushes the disco ball's shoulder down and to the right: about the top of the
    line, a pendulum of 85 units (period about 90 frames), gone after 4 swings."""
    if k <= 0:
        return 0.0
    T, tau = 90.0, 55.0
    w = 2 * math.pi / T
    v = -0.035 * math.exp(-k / tau) * math.sin(w * k)
    return v * (1 - smooth((k - 220) / 40.0))


# ================================================================================================= the spin and the sparkle
def tiles():
    """The disco ball's facets by row: [(row y, [tile ids left to right], [their colours])]."""
    sc = Scene(SCENE)
    db = next(e for e in sc.root.iter() if e.get("id") == DISCO_BALL)
    rows = {}
    for sh in db:
        if sh.tag != "Shape":
            continue
        col = sh.find("Fill/SolidColor")
        rows.setdefault(float(sh.get("y", 0)), []).append((float(sh.get("x", 0)), col.get("id"), col.get("colorValue")))
    out = []
    for y in sorted(rows):
        r = sorted(rows[y])
        out.append((y, [c for _, c, _ in r], [v for _, _, v in r]))
    return out


# the sparkles: spots on the ball (relative to its centre) and when each flashes (cycle frames); never more than two at once
SPARKS = [
    ("Sparkle 1", (40.9, -18.75), [38, 251]),          # Burst_01 itself, on the rim at the upper right
    ("Sparkle 2", (-20.0, -24.0), [118, 330]),
    ("Sparkle 3", (14.0, 14.0), [196, 392]),
    ("Sparkle 4", (-30.0, 20.0), [76, 286]),
    ("Sparkle 5", (-35.5, -27.7), [129]),              # where the ball glances off
]
SPARK_PEAK = 0.62
SPARK_FRAMES = 18


def spark(k):
    """One flash: up fast, a short hold, down slower (scale of the star)."""
    if k < 0 or k > SPARK_FRAMES:
        return 0.0
    if k <= 5:
        return SPARK_PEAK * math.sin(0.5 * math.pi * k / 5)
    return SPARK_PEAK * (1 - smooth((k - 5) / (SPARK_FRAMES - 5)))


# ================================================================================================= report
def report(j, theta, resid):
    tc = lambda f: (f + T0) / 60.0
    print(f"{ROOM}: cycle {L} frames ({L / 60:.2f} s); the hop out of the picture at intro frame {T0} ({T0 / 60:.2f} s); the loop starts at cycle frame {INTRO - 1 - T0}")
    for name in ("hop", "out of the picture", "ring box", "calendar", "settles on the calendar", "jumps", "disco ball", "into the picture", "out of sight", "sunrise", "on the crest"):
        print(f"  cycle {j.at[name]:3d}  timecode {tc(j.at[name]):5.2f} s  {name}")
    sp = lambda v: math.hypot(*v)
    print(f"  launches: hop {sp(j.v['hop']):.2f}, jump {sp(j.v['jump']):.2f} (own effort, after a pause)")
    for name, vin, vout, nrm in j.notes:
        dv = (vout[0] - vin[0], vout[1] - vin[1])
        ang = math.degrees(math.atan2(dv[0] * nrm[1] - dv[1] * nrm[0], dv[0] * nrm[0] + dv[1] * nrm[1]))
        print(f"  {name}: in {sp(vin):.2f} ({vin[0]:+.2f}, {vin[1]:+.2f}), out {sp(vout):.2f} ({vout[0]:+.2f}, {vout[1]:+.2f}), kept {100 * sp(vout) / sp(vin):.0f}%, push {ang:+.0f} deg from the surface normal")
    # clearances in flight, outside the picture
    worst = {}
    for f in range(L + 1):
        if j.mode[f] != "air" or j.inside[f]:
            continue
        c, r = j.centre(f), R * j.size[f]
        for name, ob in OBSTACLES.items():
            g = gap(c, r, ob)
            near = {"ring box": "ring box", "calendar": "calendar", "disco ball": "disco ball"}.get(name)
            if near and min(abs(f - j.at[k]) for k in j.at if k.startswith(near)) <= 2:
                continue
            if g < worst.get(name, (1e9,))[0]:
                worst[name] = (g, f)
    for name, (g, f) in sorted(worst.items(), key=lambda x: x[1][0]):
        print(f"  closest to the {name}: {g:5.1f} at cycle {f} {'(TOUCHES)' if g < 0.5 else ''}")
    top = min(j.centre(f)[1] - R * j.size[f] for f in range(L + 1))
    xs = [j.centre(f)[0] for f in range(L + 1) if j.mode[f] != "hidden"]
    print(f"  highest point y {top:.1f} (the phone copy ends near y 256); x {min(xs) - R:.0f} to {max(xs) + R:.0f} (safe area 560 to 935)")
    print(f"  spin: {theta[L] / (2 * math.pi):.2f} turns (leftover {resid:+.2f} rad taken out out of sight)")


# ================================================================================================= writing
PHASE0 = INTRO - 1 - T0                 # the loop's first frame is this cycle frame (the intro's last)
SPIN_SHIFT = 18                         # the spin's phase: puts the intro's first frame and the loop's seam inside a hold
FADE = (13, 23)                         # each spin step holds, then crossfades over these frames of its 26


def cyc_intro(f):
    return f - T0                       # negative before the hop (only the periodic things use those)


def cyc_loop(k):
    return (PHASE0 + k) % L


def picture_pose(sheet, sc, f):
    """The picture's drop and squash on intro frame f (Picture 6's wrapper; all six move together)."""
    k = sheet.anim_keys(sc.animations[f"{ROOM} Intro"])[PICTURE_6]
    return k["y"].at(f) - PIC_PIVOT[1], k["scaleX"].at(f), k["scaleY"].at(f)


def series(j, theta, sheet, sc):
    """{(object id, property): (intro values by frame, loop values by frame)} for every per-frame property."""
    def ball_at(c):
        x, y = j.node[c]
        return x, y, j.size[c] * j.sx[c], j.size[c] * j.sy[c], theta[c]
    out = {}
    names = ("x", "y", "sx", "sy", "th")
    intro = {n: {} for n in names}
    for f in range(INTRO):
        c = cyc_intro(f)
        if c < 0:
            dy, sx, sy = picture_pose(sheet, sc, f)
            vals = (PIC_PIVOT[0] + (CREST[0] - PIC_PIVOT[0]) * sx, PIC_PIVOT[1] + (CREST[1] - PIC_PIVOT[1]) * sy + dy, SUN * sx, SUN * sy, 0.0)
        else:
            vals = ball_at(c)
        for n, v in zip(names, vals):
            intro[n][f] = v
    loop = {n: {} for n in names}
    turns = theta[L] - theta[0]
    for k in range(L + 1):
        c = cyc_loop(k)
        vals = list(ball_at(c))
        vals[4] += turns * ((PHASE0 + k) // L)
        for n, v in zip(names, vals):
            loop[n][k] = v
    ids = j.ids
    for n, (oid, prop) in zip(names, ((BALL, "x"), (BALL, "y"), (ids["scale"], "scaleX"), (ids["scale"], "scaleY"), (ids["spin"], "rotation"))):
        out[(oid, prop)] = (intro[n], loop[n])
    # the pieces' reactions, functions of the cycle frame
    react = [((RING_LID, "rotation"), lambda c: lid(c - j.at["ring box"]), 0.0),
             ((JEM, "y"), lambda c: jem(c - j.at["ring box"] - 2), -3.0),
             ((FAME_02, "y"), lambda c: 570.5 + spring(c - j.at["calendar"], 1.4, down=3, tau=7.0, period=16.0), 570.5),
             ((DISCO_SWING, "rotation"), lambda c: disco_swing(c - j.at["disco ball"]), 0.0)]
    for key, fn, rest in react:
        iv = {f: (fn(cyc_intro(f)) if cyc_intro(f) >= 0 else rest) for f in range(INTRO)}
        lv = {k: fn(cyc_loop(k)) for k in range(L + 1)}
        assert abs(lv[0] - lv[L]) < 1e-6 and abs(fn(0) - rest) < 1e-6 and abs(fn(L - 1) - rest) < 1e-4, (key, fn(0), fn(L - 1))
        out[key] = (iv, lv)
    for name, _, times in SPARKS:
        fn = lambda c, times=times: max(spark(c - t) for t in times)
        iv = {f: (fn(cyc_intro(f) % L) if f >= 140 else 0.0) for f in range(INTRO)}
        lv = {k: fn(cyc_loop(k)) for k in range(L + 1)}
        for prop in ("scaleX", "scaleY"):
            out[(j.ids["sparks"][name], prop)] = (iv, lv)
        # off between flashes: a star scaled to 0 still draws its outline as a dot
        out[(j.ids["spark_shapes"][name], "opacity")] = ({f: 1.0 if v > 0.04 * SPARK_PEAK else 0.0 for f, v in iv.items()},
                                                         {k: 1.0 if v > 0.04 * SPARK_PEAK else 0.0 for k, v in lv.items()})
    return out


def steps(j):
    """Hold keys for what switches with the ball inside or outside the picture: [(object id, property, kind, intro keys, loop keys)]."""
    def keys(vals, frames):
        ks, prev = [], None
        for f in frames:
            if vals[f] != prev:
                ks.append((f, vals[f]))
                prev = vals[f]
        if ks[-1][0] != frames[-1]:
            ks.append((frames[-1], vals[frames[-1]]))
        return ks
    inside_i = {f: (j.inside[cyc_intro(f)] if cyc_intro(f) >= 0 else True) for f in range(INTRO)}
    inside_l = {k: j.inside[cyc_loop(k)] for k in range(L + 1)}
    out = []
    for oid in (FRAME_F, LAND_F):
        out.append((oid, "opacity", "double", keys({f: 1.0 if v else 0.0 for f, v in inside_i.items()}, list(range(INTRO))),
                    keys({k: 1.0 if v else 0.0 for k, v in inside_l.items()}, list(range(L + 1)))))
    for oid in j.ids["clips"]:
        out.append((oid, "isVisible", "bool", keys(inside_i, list(range(INTRO))), keys(inside_l, list(range(L + 1)))))
    return out


def facet_keys(colours, col, frames, cyc):
    """Colour keys for one facet: the pattern moves one column right each SPIN_STEP frames, holding, then crossfading over FADE
    (the first and last frames of both animations fall inside a hold)."""
    n = len(colours)

    def step(c):
        k, u = divmod(c + SPIN_SHIFT, SPIN_STEP)
        return colours[(col - k) % n], colours[(col - k - 1) % n], u

    def colour(c):
        a, b, u = step(c)
        assert not FADE[0] < u < FADE[1], (c, u)
        return b if u >= FADE[1] else a
    ks = [(frames[0], colour(cyc(frames[0])), "hold")]
    for f in frames[1:-1]:
        a, b, u = step(cyc(f))
        if a != b and u == FADE[0]:
            ks.append((f, a, "sine.inOut"))
        elif a != b and u == FADE[1]:
            ks.append((f, b, "hold"))
    ks.append((frames[-1], colour(cyc(frames[-1])), "hold"))
    return ks


class Writer(Doc):
    def key_xml(self, kind, frame, value, how, pad):
        fr = f' frame="{frame}"' if frame else ""
        if kind == "bool":
            v = ' value="true"' if value else ""
            return [f'{pad}<KeyFrameBool{v}{fr} id="{self.new_id()}"/>']
        if kind == "color":
            if how == "hold":
                return [f'{pad}<KeyFrameColor value="{value}"{fr} id="{self.new_id()}"/>']
            x1, y1, x2, y2 = (0.37, 0, 0.63, 1)
            return [f'{pad}<KeyFrameColor value="{value}" interpolationType="cubic"{fr} id="{self.new_id()}">',
                    f'{pad}    <CubicEaseInterpolator x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" id="{self.new_id()}"/>', f"{pad}</KeyFrameColor>"]
        return self.key_lines([(frame, value, how)], pad)

    def set_any(self, anim_name, oid, prop, kind, keys):
        """set_prop for number, colour and bool keys: keys [(frame, value, how)]."""
        if kind == "double":
            return self.set_prop(anim_name, oid, prop, keys)
        a, b = self.anim(anim_name)
        found = self._object(a, b, oid)
        if found is None:
            self.lines[b:b] = [f'            <KeyedObject objectId="{oid}" id="{self.new_id()}">', "            </KeyedObject>"]
            found = (b, b + 1)
        i, j = found
        block = [f'                <KeyedProperty property="{prop}" id="{self.new_id()}">']
        for fr, v, how in keys:
            block += self.key_xml(kind, fr, v, how, " " * 20)
        block.append("                </KeyedProperty>")
        self.lines[j:j] = block

    def pose_from(self, src, dst, last):
        """Rebuild the one-frame pose `dst` from every key list of `src`: its first keys (Waiting) or its last (Built)."""
        import xml.etree.ElementTree as ET
        a, b = self.anim(src)
        root = ET.fromstring("\n".join(self.lines[a:b + 1]))
        self.clear(dst)
        a2, b2 = self.anim(dst)
        new = []
        for ko in root.findall("KeyedObject"):
            new.append(f'            <KeyedObject objectId="{ko.get("objectId")}" id="{self.new_id()}">')
            for kp in ko.findall("KeyedProperty"):
                ks = sorted(list(kp), key=lambda k: int(k.get("frame", 0)))
                k = ks[-1] if last else ks[0]
                kind = {"KeyFrameDouble": "double", "KeyFrameColor": "color", "KeyFrameBool": "bool"}[k.tag]
                v = k.get("value", {"double": "0", "color": "FF000000", "bool": "false"}[kind])
                v = float(v) if kind == "double" else (v == "true" if kind == "bool" else v)
                new.append(f'                <KeyedProperty property="{kp.get("property")}" id="{self.new_id()}">')
                new += self.key_xml(kind, 0, v, "hold", " " * 20)
                new.append("                </KeyedProperty>")
            new.append("            </KeyedObject>")
        self.lines[b2:b2] = new

    def move_before(self, oid, before_oid):
        """Move an element (and its children) to just before another, re-indented to its level."""
        i = self.idx(oid)
        j = self.end(i)
        block = self.lines[i:j + 1]
        del self.lines[i:j + 1]
        t = self.idx(before_oid)
        d = (len(self.lines[t]) - len(self.lines[t].lstrip())) - (len(block[0]) - len(block[0].lstrip()))
        block = [(" " * d + l) if d >= 0 else l[-d:] for l in block]
        self.lines[t:t] = block

    def copy_shape(self, oid, name, x, y, rotation):
        """A copy of a shape with fresh ids, placed just after it; returns (shape id, its path id)."""
        i = self.idx(oid)
        j = self.end(i)
        import re
        block = list(self.lines[i:j + 1])
        path_id = None
        for n, l in enumerate(block):
            new = self.new_id()
            if "<PointsPath" in l and path_id is None:
                path_id = new
            block[n] = re.sub(r'\bid="[^"]+"', f'id="{new}"', l, count=1) if ' id="' in l else l
        block[0] = re.sub(r'x="[^"]*" y="[^"]*" name="[^"]*"', f'x="{num(x)}" y="{num(y)}" rotation="{num(rotation)}" name="{name}"', block[0])
        shape_id = re.search(r'\bid="([^"]+)"', block[0]).group(1)
        self.lines[j + 1:j + 1] = block
        return shape_id, path_id


def write(j, theta):
    from rooms_sheet import Sheet
    sc = Scene(SCENE)
    sheet = Sheet(sc)
    doc = Writer(SCENE)
    intro, loop, waiting, built = (f"{ROOM} {n}" for n in ("Intro", "Loop", "Waiting", "Built"))
    # the ball moves into the floor plane, between the picture's front hill (above it) and the disco ball (below it)
    doc.move_before(BALL, DISCO_WRAP)
    for an in (intro, loop, waiting, built):
        doc.drop_object(an, BALL)
    scale, _ = doc.wrap(BALL_ART, f"{ROOM} Ball Scale", 0.0, 0.0)
    spin, _ = doc.wrap_run(HIGHLIGHT, BODY, f"{ROOM} Ball Spin", 0.0, 0.0)
    # the picture's window, which clips the ball while it is inside the picture; it rides the picture's drop
    clip = doc.new_id()
    art6 = doc.idx(next(e.get("id") for e in sc.root.iter() if e.get("name") == "Chapter 3 Picture 6 Art"))
    pad = " " * (len(doc.lines[art6]) - len(doc.lines[art6].lstrip()) + 4)
    wx, wy = (WINDOW[0] + WINDOW[2]) / 2, (WINDOW[1] + WINDOW[3]) / 2
    doc.lines[art6 + 1:art6 + 1] = [f'{pad}<Shape x="{num(wx)}" y="{num(wy)}" name="{ROOM} Window Clip" id="{clip}">',
                                    f'{pad}    <Rectangle width="{num(WINDOW[2] - WINDOW[0])}" height="{num(WINDOW[3] - WINDOW[1])}" name="Path" id="{doc.new_id()}"/>',
                                    f"{pad}</Shape>"]
    clips = []
    for shape in (HIGHLIGHT, BODY):
        i = doc.idx(shape)
        e = doc.end(i)
        cid = doc.new_id()
        ind = " " * (len(doc.lines[i]) - len(doc.lines[i].lstrip()) + 4)
        doc.lines[e:e] = [f'{ind}<ClippingShape sourceId="{clip}" name="Window Clip" id="{cid}"/>']
        clips.append(cid)
    # the sparkles: Burst_01 and copies of it at other spots on the ball (relative to the hanging group: the ball's centre is 84.75 down)
    sparks, spark_shapes = {SPARKS[0][0]: BURST_PATH}, {SPARKS[0][0]: BURST}
    for n, (name, (dx, dy), _) in enumerate(SPARKS[1:]):
        shape, path = doc.copy_shape(BURST, f"{ROOM} {name}", dx, 84.75 + dy, 0.35 * (n + 1))
        sparks[name], spark_shapes[name] = path, shape
    j.ids = dict(scale=scale, spin=spin, clips=clips, sparks=sparks, spark_shapes=spark_shapes)
    # keys
    doc.clear(loop)
    doc.set_duration(loop, L)
    doc.set_duration(f"{ROOM} Small Loop", L)       # the bird's blink: the same keys, held open longer, in step with the Loop
    fr_i, fr_l = range(INTRO), range(L + 1)
    for (oid, prop), (iv, lv) in series(j, theta, sheet, sc).items():
        doc.set_prop(intro, oid, prop, bake(iv, fr_i))
        doc.set_prop(loop, oid, prop, bake(lv, fr_l))
    for oid, prop, kind, ik, lk in steps(j):
        doc.set_any(intro, oid, prop, kind, [(f, v, "hold") for f, v in ik])
        doc.set_any(loop, oid, prop, kind, [(f, v, "hold") for f, v in lk])
    for y, cols, colours in tiles():
        for col, cid in enumerate(cols):
            doc.set_any(intro, cid, "colorValue", "color", facet_keys(colours, col, list(fr_i), cyc_intro))
            doc.set_any(loop, cid, "colorValue", "color", facet_keys(colours, col, list(fr_l), lambda k: PHASE0 + k))
    doc.pose_from(intro, waiting, last=False)
    doc.pose_from(intro, built, last=True)
    regen_guard.save(doc, WRITTEN_AGAINST, __file__)
    print(f"wrote {SCENE}")


if __name__ == "__main__":
    jj = build()
    th, rs = spin_of(jj)
    report(jj, th, rs)
    if "--write" in sys.argv:
        write(jj, th)
