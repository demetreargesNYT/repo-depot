"""Chapter 3's 10.6 s loop: the tracks (Demetre, 2026-11-05, second round). Pure computation, writes nothing.

    from ch3_loop_tracks import build
    t = build(scene_path)       # {"loop": {(object id, property): (kind, keys, holds)}, "meta": {...}}

kind is "linear" (one key per frame, baked), "hold" (steps), "eased" ([(frame, value, how)]) or "color".

The source is the 416 frame journey in "Chapter 3 Loop" as the scene has it before ch3_loop_pauses.py runs. The ball's y is where its
BOTTOM is (the Ball node sits at the foot of the ball), so a ball at rest on the floor line has y 712 and one on the calendar's edge 571.
Every rest in the new stretches is on a drawn surface (the floor line, the calendar); the dot stays up (the ball's rotation is a constant,
tilting a little only inside the pause-rolls).

The new loop, in order:
  0 to 62          as it was: out of the picture, down onto the ring box lid
  62 to ~107       a small push off the lid, down to the floor line between the bird cage and the blocks
  to ~195          the landing bounces in (each rebound keeps about 75 percent) and settles into a roll, then a pause-roll on the floor (0.8 s)
  to ~249          the jump to the calendar
  to ~335          lands on the calendar, one hop, a pause-roll on its edge (0.63 s), then the old jump off it
  to ~455          as it was: the mobile, the disco ball, the clock, the box (the fall into the box now ends behind its front)
  then             out of sight for a while (the bird bounces), back into the picture; 636 frames in all
"""
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
from rml_edit import bake  # noqa: E402

G = 0.4
B = 0.9182
R = 17.678 * B
LOOP = 636
BEAT = 34

BALL, BALL_S, BALL_SPIN = "9:41640", "9:41641", "9:41643"
BIRD, BIRD_LEG2 = "9:1321", "9:1302"
FACE, DIGITS_A = "9:1072", "9:1073"
CELL_ROWS = [["9:914", "9:904", "9:894"], ["9:945", "9:935", "9:925"], ["9:976", "9:966", "9:956"], ["9:1007", "9:997", "9:987"]]   # bottom row first
ROW_COLORS = ["FFBBAAF0", "FFA592E6", "FFCFC2F6", "FF9684DD"]      # the lavender family, one per row
CELL_BASE = ["FFDFDBD7", "FFDFDBD7", "FFDFDBD7", "FF05CE7C"]
KEEP = ["9:691", "9:741", "9:1386", "9:1422", "9:1144", "9:1145", "9:1171", "9:1197", "9:1321", "9:1328", BALL, BALL_S, BALL_SPIN]
BOX_FIX = [(265, 690.0), (266, 706.0), (267, 722.0), (268, 729.0)]    # old frame, y: the ball keeps falling behind the box front

FLOOR_Y, FLOOR_X = 712.0, 748.0         # the floor line, and the gap between the bird cage and the blocks
CAL_Y, CAL_X = 571.0, 687.0             # the calendar's top edge (the old journey's contact)


def cid(shape_id):                      # a cell's SolidColor id is its shape's id + 7
    p, n = shape_id.split(":")
    return f"{p}:{int(n) + 7}"


def read_old(scene):
    root = ET.parse(scene).getroot()
    loop = next(a for a in root.iter("LinearAnimation") if a.get("name") == "Chapter 3 Loop")
    out = {}
    for ko in loop.findall("KeyedObject"):
        if ko.get("objectId") not in KEEP:
            continue
        for kp in ko.findall("KeyedProperty"):
            ks = [(int(k.get("frame", 0)), float(k.get("value", 0)), k.get("interpolationType")) for k in kp]
            kind = "hold" if kp.get("property") == "opacity" else "linear"
            out[(ko.get("objectId"), kp.get("property"))] = (kind, [(f, v) for f, v, _ in ks])
    return out


def sample(keys, t, kind):
    if t <= keys[0][0]:
        return keys[0][1]
    if t >= keys[-1][0]:
        return keys[-1][1]
    lo, hi = 0, len(keys) - 1
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


class Warp:
    """Piecewise map new frame -> old frame: segs [(new_start, new_end, old_start, old_end)], contiguous in new time."""

    def __init__(self, segs):
        self.segs = segs
        self.total = segs[-1][1]

    def old(self, n):
        for ns, ne, os_, oe in self.segs:
            if ns <= n <= ne:
                return os_ if (ne == ns or os_ == oe) else os_ + (oe - os_) * (n - ns) / (ne - ns)
        raise ValueError(n)

    def new_of_key(self, f):
        for ns, ne, os_, oe in self.segs:
            if os_ <= f < oe:
                return int(round(ns + (ne - ns) * (f - os_) / (oe - os_)))
        return self.total if f >= self.segs[-1][3] else None


def resample(track, warp):
    kind, keys = track
    if kind == "hold":
        out = []
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
        return ("hold", out, set())
    vals = {n: sample(keys, warp.old(n), "linear") for n in range(warp.total + 1)}
    return ("linear", [(f, v) for f, v, _ in bake(vals, range(warp.total + 1))], set())


# the ball --------------------------------------------------------------------------------------------------------------------------
LAND_SQ = [0.06, 0.052, 0.04, 0.026, 0.013, 0.004, -0.004, -0.003, -0.001]      # 6 percent, back within 0.15 s, one tiny overshoot


class Ball:
    """Frame by frame: rows (x, y, rot, kx, ky); y is the ball's bottom, so a squash keeps it on its surface; volume constant."""

    def __init__(self, row):
        self.rows = [row]

    @property
    def last(self):
        return self.rows[-1]

    def add(self, x, y, rot, ky):
        self.rows.append((x, y, rot, 1 / ky, ky))

    def air(self, T, dx=0.0):
        """A hop from the surface back to the surface: T frames at gravity G, so it rises G*T*T/8."""
        x0, y0, r0, _, _ = self.last
        h = G * T * T / 8
        for k in range(1, T + 1):
            u = k / T
            self.add(x0 + dx * u, y0 - 4 * h * u * (1 - u), r0, 1 + 0.02 * math.sin(math.pi * u) if h > 30 else 1.0)

    def arc_to(self, T, x1, y1):
        """A parabola to (x1, y1) in T frames; the squash it leaves with eases out over 4 frames."""
        x0, y0, r0, _, ky0 = self.last
        vy = (y1 - y0) / T - 0.5 * G * T
        for k in range(1, T + 1):
            u = min(1.0, k / 4)
            self.add(x0 + (x1 - x0) * k / T, y0 + vy * k + 0.5 * G * k * k, r0, ky0 + (1.0 - ky0) * u)

    def ground(self, n, roll=0.0, land=LAND_SQ, scale=1.0, gather=0, tilt=0.5):
        """n frames on the surface the ball is on: the landing squash, an eased roll of `roll` units (the dot only tilts), a gather at the end."""
        x0, y0, r0, _, _ = self.last
        for k in range(1, n + 1):
            s = (land[k - 1] if k - 1 < len(land) else 0.0) * scale * (0.5 if k == 1 else 1.0)       # the impact takes two frames to bite
            if gather and k > n - gather:
                s = max(s, 0.05 * (k - (n - gather)) / gather)
            e = min(1.0, max(0.0, (k - 1) / max(1, n - 2)))
            e = e * e * (3 - 2 * e)
            self.add(x0 + roll * e, y0, r0 + tilt * roll * e / R, 1 - s)


def thin_hits(hits, gap=34):
    out = []
    for h in sorted(hits):
        if not out or h - out[-1] >= gap:
            out.append(h)
    return out


def env(t, pts):
    if t <= pts[0][0]:
        return pts[0][1]
    for (a, va), (b, vb) in zip(pts, pts[1:]):
        if t <= b:
            return va + (vb - va) * (t - a) / (b - a)
    return pts[-1][1]


def beat_bounce(total, start, stop, ramp_in=40, ramp_out=60, amp=6.0, hop=18):
    """The bird's bounce after the ball has gone: one 6 unit bob per beat, with an envelope in and out; baked per frame."""
    vals = {}
    for f in range(total + 1):
        inside = start < f < stop
        a = env(f, [(start, 0), (start + ramp_in, 1), (stop - ramp_out, 1), (stop, 0)]) if inside else 0.0
        u = (f - start) % BEAT
        vals[f] = -amp * a * math.sin(math.pi * u / hop) if (inside and u < hop) else 0.0
    return [(f, v) for f, v, _ in bake(vals, range(total + 1))]


def wobble(total, hit):
    sc = [(0, 1.0, "hold"), (hit - 1, 1.0, "power2.out"), (hit + 3, 1.18, "power2.out"), (hit + 16, 1.0, "hold"), (total, 1.0, "hold")]
    rt = [(0, 0.0, "hold"), (hit - 1, 0.0, "sine.inOut"), (hit + 4, 0.14, "sine.inOut"), (hit + 10, -0.09, "sine.inOut"), (hit + 16, 0.04, "sine.inOut"),
          (hit + 24, 0.0, "hold"), (total, 0.0, "hold")]
    return sc, rt


def cell_tracks(total, hits):
    """The calendar's colour wave at each landing: row by row (bottom up), each cell fades to its row colour, holds, fades back."""
    out = {}
    hits = thin_hits(hits)
    for r, row in enumerate(CELL_ROWS):
        for sid in row:
            ks = [(0, CELL_BASE[r])]
            for h in hits:
                d = h + 3 * r
                ks += [(d, CELL_BASE[r]), (d + 3, ROW_COLORS[r]), (d + 11, ROW_COLORS[r]), (d + 23, CELL_BASE[r])]
            ks.append((total, CELL_BASE[r]))
            clean = []
            for f, c in ks:
                if clean and f <= clean[-1][0]:
                    f = clean[-1][0] + 1
                clean.append((f, c))
            out[(cid(sid), "colorValue")] = ("color", clean, set())
    return out, hits


def clock_hit_frame(tracks):
    """The old frame where the ball is closest to the clock (its left edge, x 845, y 477..513 for the ball's centre, which is 17 above y)."""
    best = (1e9, None)
    for t in range(170, 215):
        x = sample(tracks[(BALL, "x")][1], t, "linear")
        y = sample(tracks[(BALL, "y")][1], t, "linear") - 17.0
        d = math.hypot(max(845 - x, 0, x - 893), max(477 - y, 0, y - 513))
        if d < best[0]:
            best = (d, t)
    return best[1]


def build(scene):
    raw = read_old(scene)
    ox, oy = raw[(BALL, "x")][1], raw[(BALL, "y")][1]
    osx, osy = raw[(BALL_S, "scaleX")][1], raw[(BALL_S, "scaleY")][1]
    rot0 = sample(raw[(BALL_SPIN, "rotation")][1], 0, "linear")      # the dot's pose at rest: up
    old_row = lambda t: (sample(ox, t, "linear"), sample(oy, t, "linear"), rot0, sample(osx, t, "linear") / B, sample(osy, t, "linear") / B)
    chit = clock_hit_frame(raw)

    rows = [old_row(t) for t in range(0, 63)]                    # as it was, down onto the ring box lid
    b = Ball(rows[-1])
    b.arc_to(44, FLOOR_X, FLOOR_Y)                               # a small push off the lid, down to the floor line
    b.ground(4, scale=1.2)                                       # the landing
    b.air(40)                                                    # bounces in: each rebound keeps about 75 percent of the speed
    b.ground(3)
    b.air(30)
    b.ground(16, 9.0, scale=0.8)                                 # the last landing rolls on into the pause-roll on the floor: right, left, right (0.8 s)
    b.ground(16, -18.0, scale=0.0)
    b.ground(16, 9.0, scale=0.0, gather=5)
    floor_end = len(b.rows) - 1 + 62                              # absolute frames (the ball's own rows start at frame 62)
    b.arc_to(54, CAL_X, CAL_Y)                                   # the jump to the calendar
    arrive = len(b.rows) - 1 + 62
    b.ground(4)                                                  # lands on its edge
    b.air(31)                                                    # one hop (75 percent of the speed it landed with)
    hop_land = len(b.rows) - 1 + 62
    b.ground(4)
    b.ground(12, 3.0, scale=0.0)                                 # the pause-roll on the calendar's edge
    b.ground(14, -6.0, scale=0.0)
    b.ground(12, 3.0, scale=0.0)
    rows += b.rows[1:]
    launch = len(rows) - 1                                       # the ball is at rest on the calendar (old frame 151)
    tgt = old_row(151)
    for i in range(3):                                           # the old launch's squash comes in over three frames
        x, y, r, kx, ky = rows[-1 - i]
        u = (3 - i) / 4
        rows[-1 - i] = (x, y, r, kx + (tgt[3] - kx) * u, ky + (tgt[4] - ky) * u)
    rows[-1] = (CAL_X, CAL_Y, rot0, tgt[3], tgt[4])
    rows += [old_row(t) for t in range(152, 265)]
    x, y, r, kx, ky = rows[-1]
    for _, yy in BOX_FIX:
        rows.append((x, yy, r, kx, ky))
    hidden_from = len(rows)                                      # old frame 268's place: out of sight
    reentry = [old_row(t) for t in range(342, 417)]
    hid = LOOP + 1 - hidden_from - len(reentry)
    assert hid > 40, hid
    hold_row = rows[-1]
    rows += [hold_row] * hid
    rows += reentry
    assert len(rows) == LOOP + 1, (len(rows), LOOP + 1)
    reentry_first = hidden_from + hid

    # the ball's tracks
    vals = {"x": {i: r[0] for i, r in enumerate(rows)}, "y": {i: r[1] for i, r in enumerate(rows)}, "rot": {i: r[2] for i, r in enumerate(rows)},
            "sx": {i: r[3] * B for i, r in enumerate(rows)}, "sy": {i: r[4] * B for i, r in enumerate(rows)}}
    target = {"x": (BALL, "x"), "y": (BALL, "y"), "rot": (BALL_SPIN, "rotation"), "sx": (BALL_S, "scaleX"), "sy": (BALL_S, "scaleY")}
    loop = {}
    for name, v in vals.items():
        loop[target[name]] = ("linear", [(f, val) for f, val, _ in bake(v, range(LOOP + 1))], {reentry_first - 1})

    # everything the ball touches, from the old keys, warped: [0,62] as it was, [62,151] over the new stretch, [151,268] shifted, hidden, back
    segs = [(0, 62, 0, 62), (62, launch, 62, 151), (launch, launch + 117, 151, 268), (launch + 117, launch + 117 + hid, 268, 341), (launch + 117 + hid, LOOP, 341, 416)]
    assert segs[-1][1] - segs[-1][0] == 75 and launch + 117 == hidden_from - 1, (segs, hidden_from)
    w = Warp(segs)
    for key, tr in raw.items():
        if key[0] in (BALL, BALL_S, BALL_SPIN):
            continue
        loop[key] = resample(tr, w)

    # the clock: the old digits go, 12:00 flickers on the pink panel (never a hole), the old digits come back; the face wobbles
    hit = launch + (chit - 151)
    loop[(DIGITS_A, "opacity")] = ("hold", [(0, 1.0), (hit, 0.0), (hit + 34, 1.0), (LOOP, 1.0)], set())
    loop[("DIGITS_B", "opacity")] = ("hold", [(0, 0.0), (hit, 1.0), (hit + 5, 0.0), (hit + 9, 1.0), (hit + 14, 0.0), (hit + 18, 1.0), (hit + 23, 0.0), (hit + 27, 1.0), (hit + 31, 0.0), (LOOP, 0.0)], set())
    sc, rt = wobble(LOOP, hit)
    loop[(FACE, "scaleX")] = ("eased", sc, set())
    loop[(FACE, "scaleY")] = ("eased", sc, set())
    loop[(FACE, "rotation")] = ("eased", rt, set())
    # the calendar's wave at each landing on it
    cells, wave_hits = cell_tracks(LOOP, [arrive, hop_land])
    loop.update(cells)
    # the bird bounces on the beat for a few seconds after the ball has gone into the box
    bounce = beat_bounce(LOOP, hidden_from - 2, LOOP - 4)
    loop[(BIRD, "y")] = ("linear", [(f, 541.5 + v) for f, v in bounce], set())
    loop[(BIRD_LEG2, "y")] = ("linear", [(f, 541.5 + v) for f, v in bounce], set())

    meta = {"loop_frames": LOOP, "floor_landing": 62 + 44, "floor_pause": (floor_end - 53, floor_end), "calendar_arrive": arrive, "calendar_hop_land": hop_land,
            "calendar_pause": (launch - 38, launch), "launch": launch, "clock_hit": hit, "wave_hits": wave_hits, "ball_hidden": hidden_from, "reentry": reentry_first,
            "bird_bounce": (hidden_from - 2, LOOP - 4), "old_clock_hit": chit}
    return {"loop": loop, "meta": meta, "rows": rows}
