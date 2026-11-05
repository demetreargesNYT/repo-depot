"""Chapter 3's first-visit dance and its longer loop: the tracks (Demetre, 2026-11-05). Pure computation, writes nothing.

    from ch3_dance_tracks import build
    t = build(scene_path)       # {"dance": {...}, "loop": {...}, "dim": {...}, "meta": {...}}

Each animation is a dict {(object id, property): (kind, [(frame, value), ...])} with kind "linear" (one key per frame, baked),
"hold" (steps, used for opacity) or "color" (linear colour keys, values 'AARRGGBB').

The old 416 frame journey ("Chapter 3 Loop", as it stands in the scene) is the source. Everything the ball touches is moved out of it
into two new animations on a new layer, by a time warp: the stretches where the ball dances are new, the rest of the old keys are
copied (shifted, or stretched where the ball is somewhere new) so every reaction keeps its place against the ball.

  Dance  (first visit only, after the 3.2 s Intro): the ball leaves the picture as it always did, lands on the floor under the disco ball,
         dances 12 beats at 34 frames (105.9 bpm), jumps to the calendar and leaves the room as today (calendar, disco side, clock, box),
         the bird keeps bouncing while the ball is out of sight, the room comes back up and the ball returns to the picture.
  Loop   (every visit, 636 frames = 10.6 s): the old journey with two pauses (the ball rocks in the picture; dances on the calendar)
         and a longer wait before it returns; the clock and the calendar answer each touch.
"""
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
from rml_edit import bake  # noqa: E402

G = 0.4                                  # artboard units per frame squared (CLAUDE.md: one gravity)
B = 0.9182                               # the ball's one size (pin 1)
R = 17.678 * B                           # its radius
FLOOR_C = 712 - R                        # ball centre resting on the floor line
BEAT = 34                                # frames: 105.9 bpm
OLD = 416

# ids ------------------------------------------------------------------------------------------------------------------------------
BALL, BALL_S, BALL_SPIN = "9:41640", "9:41641", "9:41643"
PICS = ["9:869", "9:871", "9:873", "9:875", "9:877", "9:879"]
BIRD, BIRD_LEG2 = "9:1321", "9:1302"
FACE = "9:1072"                          # the clock's face (pink panel, corner ticks, digits): blinks and wobbles as one
DIGITS_A = "9:1073"                      # the drawn "201"
CELL_ROWS = [["9:914", "9:904", "9:894"], ["9:945", "9:935", "9:925"], ["9:976", "9:966", "9:956"], ["9:1007", "9:997", "9:987"]]  # bottom row first
WALL_C, FLOOR_C_ID = "1:2304", "1:2297"                 # the Background's wall and floor colours
WALL_BASE, FLOOR_BASE = "FFE1DBF5", "FF05CE7C"
WALL_DIM, FLOOR_DIM = "FFCFC9E1", "FF05B970"             # one shade darker: x0.92 and x0.90
ROW_COLORS = ["FFBBAAF0", "FFA592E6", "FFCFC2F6", "FF9684DD"]    # the lavender family, one per row
CELL_BASE = ["FFDFDBD7", "FFDFDBD7", "FFDFDBD7", "FF05CE7C"]


def cid(shape_id):                       # a cell's SolidColor id is its shape's id + 7
    p, n = shape_id.split(":")
    return f"{p}:{int(n) + 7}"


# reading the old loop ------------------------------------------------------------------------------------------------------------
KEEP = ["9:691", "9:741", "9:1386", "9:1422", "9:1144", "9:1145", "9:1171", "9:1197", "9:1321", "9:1328", BALL, BALL_S, BALL_SPIN]


def read_old(scene):
    root = ET.parse(scene).getroot()
    loop = next(a for a in root.iter("LinearAnimation") if a.get("name") == "Chapter 3 Loop")
    out = {}
    for ko in loop.findall("KeyedObject"):
        if ko.get("objectId") not in KEEP:
            continue
        for kp in ko.findall("KeyedProperty"):
            ks = [(int(k.get("frame", 0)), float(k.get("value", 0)), k.get("interpolationType")) for k in kp]
            kind = "linear" if all(k[2] == "linear" for k in ks[:-1] if True) or ks[0][2] == "linear" else "hold"
            if kp.get("property") == "opacity":
                kind = "hold"
            out[(ko.get("objectId"), kp.get("property"))] = (kind, [(f, v) for f, v, _ in ks], ks)
    return out


def sample(keys, t, kind):
    """Value of a key list at (fractional) old frame t."""
    if t <= keys[0][0]:
        return keys[0][1]
    if t >= keys[-1][0]:
        return keys[-1][1]
    lo = 0
    hi = len(keys) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if keys[mid][0] <= t:
            lo = mid
        else:
            hi = mid
    (f0, v0), (f1, v1) = keys[lo], keys[hi]
    if kind == "hold":
        return v0 if t < f1 else v1
    return v0 + (v1 - v0) * (t - f0) / (f1 - f0)


# the warp ---------------------------------------------------------------------------------------------------------------------------
class Warp:
    """Piecewise map new frame -> old frame. segs: [(new_start, new_end, old_start, old_end)] covering 0..total, contiguous in new time;
    old_start == old_end holds one old frame."""

    def __init__(self, segs):
        self.segs = segs
        self.total = segs[-1][1]

    def old(self, n):
        for ns, ne, os_, oe in self.segs:
            if ns <= n <= ne:
                if ne == ns or os_ == oe:
                    return os_
                return os_ + (oe - os_) * (n - ns) / (ne - ns)
        raise ValueError(n)

    def new_of_key(self, f):
        """New frame for an old key at frame f (a hold key keeps its place against the ball)."""
        best = None
        for ns, ne, os_, oe in self.segs:
            if os_ <= f <= oe and os_ != oe:
                v = ns + (ne - ns) * (f - os_) / (oe - os_)
                if f == oe:
                    best = v if best is None else best
                    continue
                return int(round(v))
            if os_ == oe == f and best is None:
                best = ne
        return int(round(best)) if best is not None else None


def resample(old_track, warp):
    kind, keys, _ = old_track
    if kind == "hold":
        out, last = [], None
        for f, v in keys:
            n = warp.new_of_key(f)
            if n is None:
                continue
            if out and out[-1][0] == n:
                out[-1] = (n, v)
            else:
                out.append((n, v))
        if out[0][0] != 0:
            out.insert(0, (0, keys[0][1]))
        out = [k for i, k in enumerate(out) if i == 0 or k[1] != out[i - 1][1]]
        out.append((warp.total, out[-1][1]))
        return ("hold", out)
    vals = {n: sample(keys, warp.old(n), "linear") for n in range(warp.total + 1)}
    return ("linear", [(f, v) for f, v, _ in bake(vals, range(warp.total + 1))])


# ball motion ------------------------------------------------------------------------------------------------------------------------
LAND_SQ = [0.06, 0.052, 0.04, 0.026, 0.013, 0.004, -0.004, -0.003, -0.001]      # 6 percent, springs back in 0.15 s, one tiny overshoot


class Ball:
    """Frame by frame ball state. Rows are (x, y, rot, kx, ky): kx, ky multiply the ball's one size; volume constant (kx = 1/ky)."""

    def __init__(self, x, y, rot, ky=1.0):
        self.rows = [(x, y, rot, 1 / ky, ky)]

    @property
    def x(self): return self.rows[-1][0]
    @property
    def y(self): return self.rows[-1][1]
    @property
    def rot(self): return self.rows[-1][2]

    def add(self, x, y, rot, ky):
        self.rows.append((x, y, rot, 1 / ky, ky))

    def air(self, T, h, dx=0.0, spin=0.0, y_rest=None):
        """A parabola (gravity G) from the resting height back to it: T frames, apex h above, travels dx. h = G*T^2/8."""
        assert abs(h - G * T * T / 8) < 0.6, (T, h, G * T * T / 8)
        x0, y0, r0 = self.x, y_rest, self.rot
        for k in range(1, T + 1):
            u = k / T
            stretch = 1 + 0.02 * math.sin(math.pi * u) if h > 30 else 1.0
            ky = stretch
            self.add(x0 + dx * u, y0 - 4 * h * u * (1 - u) - (R * (ky - 1) if k < T else 0), r0 + spin * u + (dx / R) * u * 0.5, ky)

    def arc_to(self, T, x1, y1, apex_rise_override=None, spin=None):
        """A parabola from here to (x1, y1) in T frames at gravity G (the rise follows from the endpoints)."""
        x0, y0, r0 = self.x, self.y, self.rot
        vy = (y1 - y0) / T - 0.5 * G * T
        for k in range(1, T + 1):
            self.add(x0 + (x1 - x0) * k / T, y0 + vy * k + 0.5 * G * k * k, r0 + (x1 - x0) / R * k / T if spin is None else r0 + spin * k / T, 1.0)

    def ground(self, n, surface, roll=0.0, land=LAND_SQ, gather_from=None, scale_land=1.0):
        """n frames on a surface (its y): the landing squash, an eased roll of `roll` units, a gather at the end if gather_from is set."""
        floor_c = surface
        x0, r0 = self.x, self.rot
        for k in range(1, n + 1):
            s = (land[k - 1] if k - 1 < len(land) else 0.0) * scale_land
            if gather_from is not None and k > n - gather_from:
                j = k - (n - gather_from)
                s = max(s, 0.05 * j / gather_from)
            e = 0.0 if n < 4 else min(1.0, max(0.0, (k - 1) / (n - 2)))
            e = e * e * (3 - 2 * e)
            ky = 1 - s
            self.add(x0 + roll * e, floor_c - R * ky if floor_c is not None else self.y, r0 + roll * e / R, ky)


def floor_ball(x):
    return Ball(x, FLOOR_C, 0.0)


def choreography(b):
    """The 12 beats on the floor. Returns the beat frames (where each hop lands) for the room's beat keys. b is on the floor, ky 1."""
    hops = []
    def hop(T=22, dx=0.0, spin=0.0, h=None):
        h = G * T * T / 8 if h is None else h
        b.air(T, h, dx, spin, FLOOR_C)
        hops.append(len(b.rows) - 1)
        b.ground(BEAT - T, 712, 0.0, gather_from=4)
    def hop_big():
        b.air(30, G * 900 / 8, 0, 0, FLOOR_C)
        hops.append(len(b.rows) - 1)
        b.ground(BEAT - 30, 712, 0.0, scale_land=1.33, gather_from=3)
    def rock(d):
        b.ground(BEAT, 712, d, scale_land=0.35)
    def shimmy(a, c, d):
        b.ground(12, 712, a, scale_land=0.3)
        b.ground(12, 712, c, scale_land=0.0)
        b.ground(BEAT - 24, 712, d, scale_land=0.0)
    hop(); hop()                              # 1 2   two hops in place
    rock(12); rock(-12)                       # 3 4   rock right, rock left
    shimmy(8, -16, 8); shimmy(-8, 16, -8)     # 5 6   two quick rolls each way
    hop_big()                                 # 7     the big beat
    hop(spin=1.4)                             # 8     a spin hop
    rock(12); rock(-12)                       # 9 10  settle
    return hops


# ---------------------------------------------------------------------------------------------------------------------------------
CAL_SURF = 584.6                         # the calendar's contact line, as the old journey uses it (the ball sinks behind the frame's edge)
CAL_X = 687.0
DANCE_ARC = (66, 748.0)                  # the old keys are kept to frame 66, then the ball flies to the floor at x 748
EXIT_T = 56                              # frames: floor to calendar
BOX_FIX = [(265, 690.0), (266, 706.0), (267, 722.0), (268, 729.0)]    # old frame, y: the ball keeps falling behind the box front


class Old:
    """The old journey as functions of the old frame."""

    def __init__(self, tracks):
        g = lambda oid, p: (tracks[(oid, p)][0], tracks[(oid, p)][1])
        self.t = {k: g(*k) for k in tracks if k[0] in (BALL, BALL_S, BALL_SPIN)}
        self.raw = tracks

    def v(self, oid, prop, t):
        kind, keys = self.t[(oid, prop)]
        return sample(keys, t, kind)

    def row(self, t, rot_off=0.0):
        return (self.v(BALL, "x", t), self.v(BALL, "y", t), self.v(BALL_SPIN, "rotation", t) + rot_off,
                self.v(BALL_S, "scaleX", t) / B, self.v(BALL_S, "scaleY", t) / B)


def smooth_join(rows, i0, i1, a, b):
    """Blend the scale of rows i0..i1 from row a's kx,ky to row b's (so a squash never pops at a join)."""
    for i in range(i0, i1 + 1):
        u = (i - i0) / max(1, i1 - i0)
        x, y, r, kx, ky = rows[i]
        rows[i] = (x, y, r, a[3] + (b[3] - a[3]) * u if u < 1 else b[3], a[4] + (b[4] - a[4]) * u if u < 1 else b[4])


def ball_tracks(rows, holds=()):
    out = {}
    for name, idx, scale in (("x", 0, 1), ("y", 1, 1), ("rotation", 2, 1)):
        out[name] = [(i, r[idx]) for i, r in enumerate(rows)]
    out["scaleX"] = [(i, r[3] * B) for i, r in enumerate(rows)]
    out["scaleY"] = [(i, r[4] * B) for i, r in enumerate(rows)]
    res = {}
    n = len(rows) - 1
    for name, pts in out.items():
        vals = {f: v for f, v in pts}
        keys = bake(vals, range(n + 1))
        oid, prop = {"x": (BALL, "x"), "y": (BALL, "y"), "rotation": (BALL_SPIN, "rotation"), "scaleX": (BALL_S, "scaleX"), "scaleY": (BALL_S, "scaleY")}[name]
        res[(oid, prop)] = ("linear", [(f, v) for f, v, _ in keys], set(holds))
    return res


def tail_rows(old, first_old, rot_off, shift_ok=True):
    """Old rows first_old..264 shifted, the box fix, and the rest of the fall behind the box front (the pin-2 and pin-1 fixes)."""
    rows = [old.row(t, rot_off) for t in range(first_old, 265)]
    x, y, r, kx, ky = rows[-1]
    for _, yy in BOX_FIX:
        rows.append((x, yy, r + 0.0, kx, ky))
    return rows


def reentry_rows(old, rot_off_from, hid_frames, last_rows):
    """The ball hidden at the box for hid_frames (rotation ramps to the old value at frame 341), then the old re-entry 342..416."""
    x, y, r, kx, ky = last_rows[-1]
    r_end = old.v(BALL_SPIN, "rotation", 341)
    rows = []
    for k in range(1, hid_frames + 1):
        rows.append((x, y, r + (r_end - r) * k / hid_frames, kx, ky))
    hold_at = len(rows) - 1
    for t in range(342, 417):
        rows.append(old.row(t, 0.0))
    return rows, hold_at


def clock_hit_frame(old):
    """The old frame where the ball is closest to the clock (its left edge, x 845, y 477..513) before it leaves."""
    best = (1e9, None)
    for t in range(170, 215):
        x, y = old.v(BALL, "x", t), old.v(BALL, "y", t)
        d = math.hypot(max(845 - x, 0, x - 893), max(477 - y, 0, y - 513))
        if d < best[0]:
            best = (d, t)
    return best[1]


def thin_hits(hits, gap=34):
    out = []
    for h in sorted(hits):
        if not out or h - out[-1] >= gap:
            out.append(h)
    return out


# the room's pieces -----------------------------------------------------------------------------------------------------------------
def env(t, pts):
    """Linear envelope through (frame, value) points."""
    if t <= pts[0][0]:
        return pts[0][1]
    for (a, va), (b, vb) in zip(pts, pts[1:]):
        if t <= b:
            return va + (vb - va) * (t - a) / (b - a)
    return pts[-1][1]


def beat_bounce(total, start, stop, ramp_in=68, ramp_out=100, amp=6.0, hop=18):
    """The bird's bounce: one 6 unit bob per beat from `start`, with an envelope that ramps in and out; baked per frame."""
    vals = {}
    for f in range(total + 1):
        a = env(f, [(start, 0), (start + ramp_in, 1), (stop - ramp_out, 1), (stop, 0)]) if start < f < stop else 0.0
        u = (f - start) % BEAT
        vals[f] = -amp * a * math.sin(math.pi * u / hop) if (start < f < stop and u < hop) else 0.0
    return [(f, v) for f, v, _ in bake(vals, range(total + 1))]


def sway(total, start, stop, amp=0.022):
    """Wall pictures sway a degree or two: alternate sides each beat, eased, with an envelope; sparse eased keys."""
    keys = [(0, 0.0, "hold")]
    k = 0
    f = start
    while f < stop:
        a = env(f, [(start, 0), (start + 2 * BEAT, 1), (stop - 2 * BEAT, 1), (stop, 0)])
        keys.append((f, amp * a * (1 if k % 2 == 0 else -1), "sine.inOut"))
        k += 1
        f += BEAT
    keys.append((stop, 0.0, "sine.inOut"))
    keys.append((total, 0.0, "hold"))
    return keys


def face_tracks(total, blink_from, blink_to, hits, hit_hold=44):
    """The clock: from blink_from the face blinks (off and on every beat, with the digits swapped to 12:00 while it is dark), until blink_to,
    when it goes dark once more, the old digits come back and it lights. Around every hit it stays lit and wobbles. hold keys."""
    on = [(0, 1.0)]
    A = [(0, 1.0)]
    Bd = [(0, 0.0)]
    forced = [(h - 4, h + hit_hold) for h in hits]
    t = blink_from
    lit = False
    if blink_from is not None:
        on.append((blink_from, 0.0)); A.append((blink_from, 0.0)); Bd.append((blink_from, 1.0))
        t = blink_from + BEAT
        lit = True
        while t < blink_to - BEAT:
            on.append((t, 1.0 if lit else 0.0))
            lit = not lit
            t += BEAT
        on.append((blink_to - 6, 0.0)); A.append((blink_to - 6, 1.0)); Bd.append((blink_to - 6, 0.0))
        on.append((blink_to, 1.0))
    # hits keep the face lit
    ev = sorted(on)
    return on, A, Bd, forced


def wobble(total, hits):
    sc = [(0, 1.0, "hold")]
    rt = [(0, 0.0, "hold")]
    for h in hits:
        sc += [(h - 1, 1.0, "power2.out"), (h + 3, 1.18, "power2.out"), (h + 16, 1.0, "hold")]
        rt += [(h - 1, 0.0, "sine.inOut"), (h + 4, 0.14, "sine.inOut"), (h + 10, -0.09, "sine.inOut"), (h + 16, 0.04, "sine.inOut"), (h + 24, 0.0, "hold")]
    sc.append((total, 1.0, "hold")); rt.append((total, 0.0, "hold"))
    return sc, rt


def cell_tracks(total, hits):
    """The calendar's colour wave at every hit: row by row (bottom up), each cell fades to its row colour, holds, fades back."""
    out = {}
    hits = thin_hits(hits)
    for r, row in enumerate(CELL_ROWS):
        for sid in row:
            ks = [(0, CELL_BASE[r])]
            for h in hits:
                d = h + 3 * r
                ks += [(d, CELL_BASE[r]), (d + 3, ROW_COLORS[r]), (d + 11, ROW_COLORS[r]), (d + 23, CELL_BASE[r])]
            ks.append((total, CELL_BASE[r]))
            # strictly increasing frames
            clean = []
            for f, c in ks:
                if clean and f <= clean[-1][0]:
                    f = clean[-1][0] + 1
                clean.append((f, c))
            out[(cid(sid), "colorValue")] = ("color", clean)
    return out, hits


def build(scene):
    old = Old(read_old(scene))
    raw = old.raw
    chit = clock_hit_frame(old)

    # ===== Dance =================================================================================================================
    rows = [old.row(t) for t in range(0, DANCE_ARC[0] + 1)]
    x0, y0 = rows[-1][0], rows[-1][1]
    vy0 = rows[-1][1] - rows[-2][1]
    # arc to the floor: .5 G T^2 + vy0 T - (FLOOR_C - y0) = 0
    Tn = (-vy0 + math.sqrt(vy0 * vy0 + 2 * G * (FLOOR_C - y0))) / G
    Tn = int(round(Tn))
    b = Ball(*rows[-1][:3], ky=rows[-1][4])
    b.rows = [rows[-1]]
    b.arc_to(Tn, DANCE_ARC[1], FLOOR_C)
    rows += b.rows[1:]
    smooth_join(rows, DANCE_ARC[0], DANCE_ARC[0] + 8, rows[DANCE_ARC[0]], (0, 0, 0, 1.0, 1.0))
    L = len(rows) - 1                       # the landing frame
    b.rows = [rows[-1]]
    b.ground(4, 712, 0.0, scale_land=1.3)                    # the landing, then it bounces in: each rebound keeps about 75 percent of the speed
    for T_, g_ in ((44, 3), (33, 3), (25, 3)):
        b.air(T_, G * T_ * T_ / 8, 0, 0, FLOOR_C)
        b.ground(g_, 712, 0.0)
    L2 = L + len(b.rows) - 1                # the beat grid starts here
    hops = choreography(b)
    nb = len(b.rows) - 1
    rows += b.rows[1:]
    DANCE_END = len(rows) - 1               # last floor frame (the gather)
    hop_frames = [L + h for h in hops]

    # exit: floor to the calendar contact (the old frame 148)
    tgt = old.row(148)
    b.rows = [rows[-1]]
    b.arc_to(EXIT_T, tgt[0], tgt[1])
    rows += b.rows[1:]
    smooth_join(rows, len(rows) - 4, len(rows) - 1, rows[-4], tgt)
    rows[-1] = tgt[:2] + (rows[-1][2],) + tgt[3:]
    TC = len(rows) - 1                      # the calendar contact (= old 148)
    rot_off = rows[-1][2] - old.row(148)[2]
    tail = tail_rows(old, 149, rot_off)
    rows += tail
    HIDD = 190
    hid_rows, hid_hold = reentry_rows(old, rot_off, HIDD, rows)
    first_hidden = len(rows)
    rows += hid_rows
    reentry_first = first_hidden + HIDD
    DT = len(rows) - 1
    dance_holds = [reentry_first - 1]
    dance = ball_tracks(rows, dance_holds)
    # the old shared keys, warped: [0,66] as they were; [66,148] stretched over the dance; [148,268] shifted; [268,341] over the hiding; [341,416] shifted
    segs = [(0, 66, 0, 66), (66, TC, 66, 148), (TC, TC + 120, 148, 268), (TC + 120, TC + 120 + HIDD, 268, 341), (TC + 120 + HIDD, DT, 341, 416)]
    assert segs[-1][1] - segs[-1][0] == 75 and segs[-1][1] == DT, (segs, DT)
    w = Warp(segs)
    for key in raw:
        if key[0] in (BALL, BALL_S, BALL_SPIN):
            continue
        k = resample(raw[key], w)
        dance[key] = k + (set(),)
    dance_hit = TC + (chit - 148)
    bird_end = reentry_first - 20
    bounce = beat_bounce(DT, L2, bird_end)
    dance[(BIRD, "y")] = ("linear", [(f, 541.5 + v) for f, v in bounce], set())
    dance[(BIRD_LEG2, "y")] = ("linear", [(f, 541.5 + v) for f, v in bounce], set())
    sw = sway(DT, L2, DANCE_END + 40)
    for p in PICS:
        dance[(p, "rotation")] = ("eased", sw, set())
    on, A, Bd, forced = face_tracks(DT, L2 + BEAT, bird_end, [dance_hit])
    face_keys = merge_forced(on, forced)
    dance[(FACE, "opacity")] = ("hold", face_keys, set())
    dance[("CLOCK_DARK", "opacity")] = ("hold", [(f, 1.0 - v) for f, v in face_keys], set())     # the dark display shows while the face is off
    dance[(DIGITS_A, "opacity")] = ("hold", dedupe(A), set())
    dance[("DIGITS_B", "opacity")] = ("hold", dedupe(Bd), set())
    sc, rt = wobble(DT, [dance_hit])
    dance[(FACE, "scaleX")] = ("eased", sc, set()); dance[(FACE, "scaleY")] = ("eased", sc, set()); dance[(FACE, "rotation")] = ("eased", rt, set())
    cells, hits_used = cell_tracks(DT, [TC])
    dance.update({k: v + (set(),) for k, v in cells.items()})
    # light spots (wall: A, B; floor: C, D)
    SP = {"A": (640, 860, 490), "B": (880, 660, 565), "C": (700, 840, 745), "D": (860, 700, 800)}
    fade_in, fade_out = L - 12, bird_end - 40
    for name, (xa, xb, _y) in SP.items():
        dance[(f"SPOT_{name}", "x")] = ("eased", [(0, xa, "sine.inOut"), (fade_in, xa, "sine.inOut"), (fade_out + 40, xb, "sine.inOut"), (DT, xb, "hold")], set())
        dance[(f"SPOT_{name}", "opacity")] = ("eased", [(0, 0.0, "hold"), (fade_in, 0.0, "linear"), (fade_in + 30, 1.0, "hold"), (fade_out, 1.0, "linear"), (fade_out + 40, 0.0, "hold"), (DT, 0.0, "hold")], set())
    # the dim: down as the dance starts, back up as the bird winds down
    dim_down, dim_up = L - 20, bird_end - 60
    dim = {(WALL_C, "colorValue"): ("color", [(0, WALL_BASE), (dim_down, WALL_BASE), (dim_down + 30, WALL_DIM), (dim_up, WALL_DIM), (dim_up + 30, WALL_BASE), (DT, WALL_BASE)]),
           (FLOOR_C_ID, "colorValue"): ("color", [(0, FLOOR_BASE), (dim_down, FLOOR_BASE), (dim_down + 30, FLOOR_DIM), (dim_up, FLOOR_DIM), (dim_up + 30, FLOOR_BASE), (DT, FLOOR_BASE)])}
    meta = {"dance_frames": DT, "landing": L, "beats_from": L2, "dance_end": DANCE_END, "exit_contact": TC, "ball_hidden": first_hidden, "reentry": reentry_first,
            "clock_hit": dance_hit, "grid_hits": hits_used, "bird_end": bird_end, "dim": (dim_down, dim_up), "hops": hop_frames, "old_clock_hit": chit}

    # ===== Loop ==================================================================================================================
    dA, HID = 56, 122
    rows = [old.row(0)]
    x, y, r, kx, ky = rows[0]
    bb = Ball(x, y, r, ky=1.0)
    bb.rows = [rows[0]]
    # the pause in the picture: two small bobs with a sway, back to the start pose
    for k in range(1, dA + 1):
        u = k / dA
        bob = math.sin(2 * math.pi * 2 * u) ** 2 * 3.0 * math.sin(math.pi * u)
        sway_x = 5 * math.sin(2 * math.pi * u) * math.sin(math.pi * u) ** 0.5
        bb.add(x + sway_x, y - bob, r + sway_x / R, 1.0)
    bb.rows[-1] = rows[0]
    rows = bb.rows[:]
    rows += [old.row(t) for t in range(1, 89)]
    arr = rows[-1]
    cal = Ball(arr[0], arr[1], arr[2], ky=arr[4])
    cal.rows = [arr]
    s0 = 1 - arr[4]
    cal.ground(7, CAL_SURF, 0.0, land=[s0 * (1 - k / 7) for k in range(1, 8)])
    rest_c = CAL_SURF - R
    def chop(T, dx=0.0):
        cal.air(T, G * T * T / 8, dx, 0.0, rest_c)
        hit_rows.append(len(cal.rows) - 1)
    hit_rows = []
    for T, dx, gl in ((30, 0, 5), (26, 0, 5), (26, 8, 5), (26, -8, 5)):
        chop(T, dx)
        cal.ground(gl, CAL_SURF, 0.0, land=[0.06 * (1 - k / 5) for k in range(5)] if gl else [])
    chop(34, 0)
    # the last landing is the old press (frame 148)
    tgt = old.row(148)
    cal.ground(6, CAL_SURF, 0.0)
    first_cal = len(rows) - 1
    cal_rows = cal.rows[1:]
    block_len = 60 + 115
    # trim or pad the block to its length, ending on the old 148 state
    if len(cal_rows) > block_len:
        cal_rows = cal_rows[:block_len]
    while len(cal_rows) < block_len:
        cal_rows.append(cal_rows[-1])
    rows += cal_rows
    smooth_join(rows, len(rows) - 4, len(rows) - 1, rows[-4], tgt)
    rows[-1] = tgt[:2] + (rows[-1][2],) + tgt[3:]
    TC2 = len(rows) - 1
    rot_off2 = rows[-1][2] - old.row(148)[2]
    rows += tail_rows(old, 149, rot_off2)
    hid_rows, _ = reentry_rows(old, rot_off2, HID, rows)
    first_hidden2 = len(rows)
    rows += hid_rows
    reentry2 = first_hidden2 + HID
    LT = len(rows) - 1
    loop = ball_tracks(rows, [reentry2 - 1])
    segs = [(0, dA, 0, 0), (dA, dA + 88, 0, 88), (dA + 88, TC2, 88, 148), (TC2, TC2 + 120, 148, 268), (TC2 + 120, TC2 + 120 + HID, 268, 341), (TC2 + 120 + HID, LT, 341, 416)]
    assert segs[-1][1] - segs[-1][0] == 75, segs
    w2 = Warp(segs)
    for key in raw:
        if key[0] in (BALL, BALL_S, BALL_SPIN):
            continue
        loop[key] = resample(raw[key], w2) + (set(),)
    loop_hit = TC2 + (chit - 148)
    cal_hits = [dA + 88 + h for h in hit_rows]       # the hops' landings, in new frames
    cells2, hits_used2 = cell_tracks(LT, [dA + 88] + cal_hits + [TC2])
    loop.update({k: v + (set(),) for k, v in cells2.items()})
    on, A, Bd, forced = face_tracks(LT, None, None, [loop_hit])
    # the clock answers the touch: dark, 12:00 flickers on, then the old digits come back
    h = loop_hit
    face = [(0, 1.0), (h - 1, 1.0), (h, 0.0), (h + 3, 1.0), (h + 9, 0.0), (h + 12, 1.0), (h + 19, 0.0), (h + 22, 1.0), (h + 40, 0.0), (h + 42, 1.0), (LT, 1.0)]
    loop[(FACE, "opacity")] = ("hold", face, set())
    loop[("CLOCK_DARK", "opacity")] = ("hold", [(f, 1.0 - v) for f, v in face], set())
    loop[(DIGITS_A, "opacity")] = ("hold", [(0, 1.0), (h, 0.0), (h + 40, 1.0)] + [(LT, 1.0)], set())
    loop[("DIGITS_B", "opacity")] = ("hold", [(0, 0.0), (h, 1.0), (h + 40, 0.0)] + [(LT, 0.0)], set())
    sc, rt = wobble(LT, [loop_hit])
    loop[(FACE, "scaleX")] = ("eased", sc, set()); loop[(FACE, "scaleY")] = ("eased", sc, set()); loop[(FACE, "rotation")] = ("eased", rt, set())
    # the echo: one faint light spot drifts across the wall
    loop[("SPOT_A", "x")] = ("eased", [(0, 640, "sine.inOut"), (LT // 2, 860, "sine.inOut"), (LT, 640, "hold")], set())
    loop[("SPOT_A", "opacity")] = ("eased", [(0, 0.0, "linear"), (90, 0.55, "hold"), (LT - 150, 0.55, "linear"), (LT - 60, 0.0, "hold"), (LT, 0.0, "hold")], set())
    meta2 = {"loop_frames": LT, "pause_picture": (0, dA), "pause_calendar": (dA + 88, TC2), "calendar_contact_launch": TC2, "ball_hidden": first_hidden2, "reentry": reentry2,
             "clock_hit": loop_hit, "grid_hits": hits_used2}
    meta["loop"] = meta2
    return {"dance": dance, "loop": loop, "dim": dim, "meta": meta}


def dedupe(keys):
    out = []
    for f, v in sorted(keys):
        if out and out[-1][0] == f:
            out[-1] = (f, v)
        elif not out or out[-1][1] != v:
            out.append((f, v))
    return out


def merge_forced(on, forced):
    """The face's hold keys with the forced-lit windows (a hit) laid over them."""
    pts = sorted(on)
    def val(f):
        v = pts[0][1]
        for ff, vv in pts:
            if ff <= f:
                v = vv
        return v
    frames = sorted({f for f, _ in pts} | {x for a, b in forced for x in (a, b)})
    out = []
    for f in frames:
        v = 1.0 if any(a <= f < b for a, b in forced) else val(f)
        if not out or out[-1][1] != v:
            out.append((f, v))
    return out
