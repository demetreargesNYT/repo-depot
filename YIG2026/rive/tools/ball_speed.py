"""The ball's speed on every frame, for finding jerks: python3 tools/ball_speed.py ch2 "The Mini" [--from F --to F] [--keys]

Prints the end of the intro, then the loop twice over (so the wrap shows), as position, speed in units per frame and the
change in speed from the frame before. A jerk is a frame where the speed changes much more than its neighbours', which is
what a thinned or half-frame key looks like. `--keys` lists the position nodes' keys with their ease.

`--contacts` is the physics check (CLAUDE.md, "The ball's physics"): it finds every contact in the room's first pass and the wrap
from the ball's positions alone, and for each lists the Finesse-panel timecode, the speed and direction going in and coming out, and
flags what breaks the rules: a bounce that drops below 70 percent of its speed, a dead stop, a launch faster than the ball arrived, a
turn-round that no flat surface explains, a roll downhill that slows (or uphill that speeds up), and a flight whose gravity is not
the project's 0.40. A landing that turns into a roll keeps the sideways part of the speed and is flagged only below 45 percent. A landing that pauses a few frames and pushes off again (the climb's steps) and a catch out of sight below the
mug's rim are listed but not flagged. `--lo F` sets the first intro frame read (default 100).

It also looks for jitter, on the ball and on every piece the room moves (rotation, x, y): a HITCH (a piece or the ball stops for one
or two frames in the middle of a movement and then carries on the same way), a LURCH (the speed jumps from one frame to the next with
no turn to explain it, or the ball's contact has no surface: speed changes more than 25 percent while the direction stays within 20
degrees), and a BUZZ (swings back and forth shorter than 20 frames, i.e. faster than about 3 a second, two in a row (three turning points) without dying
away: the second between 0.6 and 1.5 times the first). A swing is one way, from one end to the other. Stillness at a contact, at the end
of a swing and at a real rest is fine. The repeated frame where the intro hands over to the loop and where the loop wraps (every room has them) is not read as a hitch.

Flags Demetre accepted on purpose are listed in tools/ball_speed_accepted.json: they are still reported, marked ACCEPTED, and
only the other flags make `--contacts` exit with 1. Adding to that list needs his approval.
"""
import json
import math
import re
import sys
from pathlib import Path

from rml_read import Scene, chapter_dir
from rooms_sheet import Sheet


def positions(sheet, anim, chain, frames, n):
    keys = sheet.anim_keys(anim)
    out = []
    for f in frames:
        x = y = 0.0
        for node in chain:
            k = keys.get(node.get("id"), {})
            x += k["x"].at(f) if "x" in k else float(node.get("x", 0))
            y += k["y"].at(f) if "y" in k else float(node.get("y", 0))
        out.append((x, y))
    return out


G_STD = 0.40

# "The jump" (docs/ball-character.md): the approved character arc, measured from Wordle's jump (loop frames 221 to 250, y 654.85 to 552.11
# and back to 600.11): one fast launch step of 20.6 units that eases out (cubic: each step about 0.85 of the one before) over 15 frames to a
# floaty peak (under 2 units a frame for 11 frames), then a fall that accelerates (cubic ease-in) over 15 frames to 8.5 a frame at contact.
# It is not a 0.40 parabola, so a flight that follows it is accepted as well as a strict parabola; the parabola stays the rule for every
# other flight (a long free fall: its speed grows by a steady 0.40 a frame, so its last step is only twice its mean, not three times).
# The rise or the fall may stand alone (a hop onto a higher surface ends in the float, a drop starts in it), and any hold at the peak
# (the ball hidden in a box) is part of the float. Shape, not a fit: the numbers below are the tolerances.
JUMP_FAST = 2.2          # the launch step (rise) or the contact step (fall) is at least this many times the mean step; a parabola is 2.0
JUMP_MIN_STEP = 4.0      # ... and at least this many units: not a creep
JUMP_FRAMES = (6, 26)    # the rise, and the fall, each last this many frames (holds at the peak not counted)
JUMP_FLOAT = 4           # frames under 2 units a frame (holds included), at least
JUMP_MONO = 0.35         # units a frame: how much a step may go the wrong way (a rise slowing down must not speed up again)
HOLD = 0.05              # a step under this is a hold


def _eased(steps, rising):
    """The steps (positive magnitudes, in time order) of one side of a jump. A rise starts fast and slows; a fall starts slow and speeds up."""
    if not JUMP_FRAMES[0] <= len(steps) <= JUMP_FRAMES[1]:
        return False
    fast = steps[0] if rising else steps[-1]
    if fast < JUMP_MIN_STEP or fast < JUMP_FAST * (sum(steps) / len(steps)):
        return False
    pairs = zip(steps, steps[1:])
    return all((b <= a + JUMP_MONO) if rising else (b >= a - JUMP_MONO) for a, b in pairs)


def follows_jump(dy):
    """True when the vertical steps dy (units a frame, down positive), from the launch frame to the last frame before contact, follow
    the jump: a fast eased-out rise and/or an eased-in fall with a float between (see above). Horizontal travel is ignored."""
    d = list(dy)
    while d and abs(d[0]) < HOLD:
        d.pop(0)
    while d and abs(d[-1]) < HOLD:
        d.pop()
    if len(d) < 8 or sum(1 for x in dy if abs(x) < 2.0) < JUMP_FLOAT:
        return False
    p = next((i for i, x in enumerate(d) if x >= HOLD), len(d))        # the first frame that falls: the rise is before it
    rise = [-x for x in d[:p] if x < 0]
    fall = [x for x in d[p:] if x > 0]
    if len(rise) and max(rise) < 2.5:                                  # a slow drift up before a drop is part of the float
        rise = []
    if len(fall) and max(fall) < 2.0:                                  # a slow settle after a hop onto a higher surface is too
        fall = []
    if not rise and not fall:
        return False
    return (not rise or _eased(rise, True)) and (not fall or _eased(fall, False))




def fit_segment(vs):
    """Mean acceleration over a run of velocities."""
    if len(vs) < 2:
        return (0.0, 0.0)
    n = len(vs) - 1
    return ((vs[-1][0] - vs[0][0]) / n, (vs[-1][1] - vs[0][1]) / n)


def classify(vs, a):
    sp = sum(math.hypot(*v) for v in vs) / len(vs)
    if sp < 0.2:
        return "rest"
    if abs(a[0]) < 0.03 and a[1] > 0.12 and len(vs) >= 5:
        return "flight"
    return "roll"


def contacts_report(pts, t_of, tmax_report):
    """pts: positions on consecutive frames; t_of(i): Finesse timecode in seconds of frame i. Prints the table and returns the flags."""
    m = len(pts)
    v = [(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(m - 1)]
    jump = [math.hypot(*x) > 30 for x in v]          # the ball hidden and put somewhere else: not a motion
    acc = [None] + [(v[i][0] - v[i - 1][0], v[i][1] - v[i - 1][1]) for i in range(1, len(v))]
    breaks = []
    for i in range(2, len(v)):
        if jump[i] or jump[i - 1] or jump[i - 2]:
            continue
        d = math.hypot(acc[i][0] - acc[i - 1][0], acc[i][1] - acc[i - 1][1])
        if d > 0.35:
            breaks.append((i, d))
    # one contact per cluster of breaks (the biggest one); a contact that falls between two frames shows as two breaks in a row, and the
    # speeds going in and out are read just outside the cluster
    contacts = []
    for i, d in breaks:
        if contacts and i - contacts[-1][3] <= 2:
            main, dm, first, last = contacts[-1]
            contacts[-1] = ((i, d, first, i) if d > dm else (main, dm, first, i))
        else:
            contacts.append((i, d, i, i))
    contacts = [(c[0], c[1], c[2], c[3]) for c in contacts]
    cidx = [c[0] for c in contacts]
    # segments between contacts: intervals of v between one cluster and the next
    segs = []
    starts = [0] + [c[3] + 1 for c in contacts]
    ends = [c[2] - 1 for c in contacts] + [len(v) - 1]
    for k in range(len(starts)):
        a0, a1 = starts[k], ends[k]
        run = [x for x in range(a0, a1 + 1) if 0 <= x < len(v) and not jump[x]]
        vs = [v[x] for x in run]
        a = fit_segment(vs)
        if len(vs) < 5:
            a = (0.0, G_STD)                      # too short to fit: assume it is falling
        segs.append((a0, a1, vs, a, classify(vs, a) if vs else "rest"))
    flags, rows = [], []
    for k, seg in enumerate(segs):
        a0, a1, vs, a, kind = seg
        if kind == "flight" and len(vs) >= 6:
            g = a[1]
            w0 = contacts[k - 1][2] if k > 0 else a0                       # from the launch frame, which the contact before holds
            w1 = contacts[k][2] - 1 if k < len(contacts) else a1           # to the frame before the landing
            window = [v[x][1] for x in range(w0, w1 + 1)]
            if abs(g - G_STD) > 0.04 and not follows_jump(window):
                msg = f"flight at {t_of(a0):.2f} to {t_of(a1 + 1):.2f} s falls at {g:.2f} per frame squared, not {G_STD:.2f}"
                flags.append((t_of(a0), msg))
        if kind == "roll" and len(vs) >= 6:
            sp = [math.hypot(*x) for x in vs]
            dy = sum(x[1] for x in vs)
            if dy > 12 and sp[-1] < sp[0] * 0.9 and sp[0] > 1.0:
                flags.append((t_of(a0), f"roll downhill at {t_of(a0):.2f} s slows from {sp[0]:.1f} to {sp[-1]:.1f}"))
            if dy < -12 and sp[-1] > sp[0] * 1.1 and sp[0] > 0.5:
                flags.append((t_of(a0), f"roll uphill at {t_of(a0):.2f} s speeds up from {sp[0]:.1f} to {sp[-1]:.1f}"))
    print(f"{'time':>6} {'at (x, y)':>13}  {'in':>14}  {'out':>14}  {'kept':>5}  {'normal':>7}  note")
    # a spring or a ride (a short stay on something that gives, between two contacts) counts as one contact: in at the first, out at the last
    groups, k = [], 0
    while k < len(contacts):
        i, d, c_first, c_last = contacts[k]
        j = k
        while j + 1 < len(contacts) and segs[j + 1][4] == "roll" and len(segs[j + 1][2]) <= 8:
            j += 1
        groups.append((i, d, c_first, contacts[j][3], segs[k], segs[j + 1]))
        k = j + 1
    for i, d, c_first, c_last, A, B in groups:
        if t_of(i) > tmax_report:
            break
        n_in = n_out = 0.5                  # the velocities are read on the frames just outside the contact
        vin = (v[c_first - 1][0] + n_in * A[3][0], v[c_first - 1][1] + n_in * A[3][1]) if A[4] != "rest" else (0.0, 0.0)
        vout = (v[c_last][0] - n_out * B[3][0], v[c_last][1] - n_out * B[3][1]) if B[4] != "rest" else (0.0, 0.0)
        si, so = math.hypot(*vin), math.hypot(*vout)
        ang = lambda x: math.degrees(math.atan2(-x[1], x[0])) if math.hypot(*x) > 0.05 else float("nan")
        kept = so / si if si > 0.3 else float("nan")
        dv = (vout[0] - vin[0], vout[1] - vin[1])
        nrm = ""
        notes = []
        if math.hypot(*dv) > 0.5:
            nrm = f"{math.degrees(math.atan2(-dv[1], dv[0])):.0f} deg"
        t = t_of(i)
        hidden = pts[i][1] > 731          # the ball's centre is below the mug's front rim (card 3): caught out of sight
        # a landing, a pause (speed under 1.8 for 2 frames or more), then it goes on: the ball's own step (the climb), not a bounce
        pause = 0
        for x in range(c_last, min(c_last + 20, len(v))):
            if math.hypot(*v[x]) < 1.8:
                pause += 1
            elif pause:
                break
        step = pause >= 2 and t_of(i) < tmax_report - 0.2
        if si > 2.5 and so < 0.7 * si and (hidden or step):
            notes.append("caught out of sight (not flagged)" if hidden else "step: lands, pauses %d frames, goes on (its own effort; not flagged)" % pause)
        elif si > 2.5 and B[4] == "roll" and so >= 0.45 * si:
            notes.append("lands and rolls (the surface takes the fall; %d%% kept)" % round(100 * kept))
        elif si > 2.5 and so < 0.7 * si:
            notes.append("FLAG slows to %d%%" % round(100 * kept) + (" (dead stop)" if so < 0.5 else ""))
            flags.append((t, f"contact at {t:.2f} s keeps only {round(100 * kept)}% of its speed ({si:.1f} to {so:.1f})"))
        if si > 1.0 and so > 1.05 * si and A[4] == "flight" and not step:
            notes.append("FLAG leaves faster than it came")
            flags.append((t, f"contact at {t:.2f} s leaves faster than it arrived ({si:.1f} to {so:.1f})"))
        if A[4] not in ("rest", "flight") and B[4] not in ("rest", "flight") and si > 0.8 and so > 0.3 and abs(so - si) > max(0.6, 0.25 * si) and not hidden:
            cosang = (vin[0] * vout[0] + vin[1] * vout[1]) / (si * so)
            if cosang > math.cos(math.radians(20)):
                notes.append("FLAG lurch: speed jumps %.1f to %.1f with no turn" % (si, so))
                flags.append((t, f"LURCH: the ball's speed jumps from {si:.1f} to {so:.1f} at {t:.2f} s with no turn to explain it"))
        if abs(vin[0]) > 1.5 and abs(vout[0]) > 1.5 and vin[0] * vout[0] < 0:
            tilt = abs(math.degrees(math.atan2(dv[0], -dv[1]))) if math.hypot(*dv) > 0.5 else 0
            if tilt < 30 or tilt > 150:
                notes.append("FLAG turns round off a near-flat surface")
                flags.append((t, f"turn-round at {t:.2f} s (x {pts[i][0]:.0f}) off a surface tilted only {tilt:.0f} deg"))
            else:
                notes.append("turns round (surface tilted %d deg)" % round(tilt))
        row = f"{t:6.2f} ({pts[i][0]:5.0f},{pts[i][1]:4.0f})  {si:5.1f} @{ang(vin):5.0f}  {so:5.1f} @{ang(vout):5.0f}  {kept * 100:4.0f}%  {nrm:>7}  " + "; ".join(notes)
        print(row)
    # a hitch on the ball: its speed drops to nearly nothing for one or two frames in the middle of a movement and then goes on the same way
    near_contact = set()
    for i_, d_, c0_, c1_ in contacts:
        near_contact.update(range(c0_ - 2, c1_ + 3))
    i = 1
    while i < len(v) - 3:
        sp0 = math.hypot(*v[i - 1])
        if sp0 > 1.2 and math.hypot(*v[i]) < 0.2 * sp0 and not jump[i]:
            k = 1
            while i + k < len(v) - 1 and math.hypot(*v[i + k]) < 0.2 * sp0 and k < 3:
                k += 1
            sp1 = math.hypot(*v[i + k])
            same = v[i - 1][0] * v[i + k][0] + v[i - 1][1] * v[i + k][1] > 0
            if k <= 2 and sp1 >= 0.6 * sp0 and same and not any(j in near_contact for j in range(i - 1, i + k + 1)) and t_of(i) <= tmax_report:
                flags.append((t_of(i), f"HITCH: the ball stops for {k} frame{'s' if k > 1 else ''} at {t_of(i):.2f} s in the middle of a movement"))
            i += k
        i += 1
    # a lurch or a stall on the ball: its speed jumps or collapses from one frame to the next with no turn, not after a flight (a landing
    # is a contact) and not a push-off into a flight
    in_contact = set()                       # frames of a contact that a flight comes into or goes out of (a landing, a spring, a push-off)
    for g_i, g_d, g_first, g_last, g_A, g_B in groups:
        if g_A[4] == "flight" or g_B[4] == "flight":
            in_contact.update(range(g_first - 1, g_last + 3))
    is_flight = lambda i: 0 <= i < len(acc) and acc[i] is not None and abs(acc[i][0]) < 0.12 and 0.25 < acc[i][1] < 0.55
    for i in range(2, len(v) - 2):
        if jump[i] or jump[i - 1] or t_of(i) > tmax_report or pts[i][1] > 731:
            continue
        s0, s1 = math.hypot(*v[i - 1]), math.hypot(*v[i])
        if min(s0, s1) < 0.3 or abs(s1 - s0) <= max(1.0, 0.4 * max(s0, s1)):
            continue
        if is_flight(i - 1) or i in in_contact or (i - 1) in in_contact:
            continue
        if is_flight(i + 1) and any(math.hypot(*v[j]) < 0.8 for j in range(max(0, i - 3), i)):      # a push-off from a pause
            continue
        if (v[i - 1][0] * v[i][0] + v[i - 1][1] * v[i][1]) / (s0 * s1) < math.cos(math.radians(25)):
            continue
        what = "LURCH" if s1 > s0 else "STALL"
        flags.append((t_of(i), f"{what}: the ball's speed goes from {s0:.1f} to {s1:.1f} in one frame at {t_of(i):.2f} s with no turn to explain it"))
    jitter_track("the ball", [p[0] for p in pts], "x", t_of, flags, hitch=False)
    kinds = {}
    for a0, a1, vs, a, kind in segs:
        kinds[kind] = kinds.get(kind, 0) + 1
    print(f"\n{len([c for c in contacts if t_of(c[0]) <= tmax_report])} contacts; segments: " + ", ".join(f"{n} {k}" for k, n in kinds.items()))
    return sorted({(round(t, 3), m_) for t, m_ in flags if t <= tmax_report})


SWING = 20          # a swing (one way) shorter than this many frames, repeated without dying away, is a buzz
AMP_MIN = {"rotation": 0.015, "x": 1.5, "y": 1.5}      # swings smaller than this are noise
HITCH_MIN = {"rotation": 0.004, "x": 0.5, "y": 0.5}   # a movement of at least this much a frame on both sides of a stop


def swings(vals, amp_min):
    """[(frame, value)] of the turning points, ignoring wiggles smaller than amp_min."""
    pts = []
    direction = 0
    ext = (0, vals[0])
    for i, v in enumerate(vals):
        if direction == 0:
            if abs(v - ext[1]) >= amp_min:
                pts.append(ext)
                direction = 1 if v > ext[1] else -1
                ext = (i, v)
        elif direction == 1:
            if v >= ext[1]:
                ext = (i, v)
            elif v <= ext[1] - amp_min:
                pts.append(ext)
                direction, ext = -1, (i, v)
        else:
            if v <= ext[1]:
                ext = (i, v)
            elif v >= ext[1] + amp_min:
                pts.append(ext)
                direction, ext = 1, (i, v)
    pts.append(ext)
    return pts


def jitter_track(label, vals, kind, t_of, flags, skip=(), hitch=True):
    """Hitches and buzz on one value-per-frame track (a piece's rotation, x or y)."""
    amp, thr = AMP_MIN[kind], HITCH_MIN[kind]
    n = len(vals)
    d = [vals[i + 1] - vals[i] for i in range(n - 1)]
    i = 1
    while hitch and i < len(d) - 2:
        if abs(d[i - 1]) >= thr and abs(d[i]) < 0.12 * abs(d[i - 1]) and i not in skip and i + 1 not in skip:
            k = 1
            while i + k < len(d) and abs(d[i + k]) < 0.12 * abs(d[i - 1]) and k < 3:
                k += 1
            if k <= 2 and i + k < len(d) and abs(d[i + k]) >= thr and d[i + k] * d[i - 1] > 0 and not any(j in skip for j in range(i, i + k + 1)):
                flags.append((t_of(i), f"HITCH: {label} stops for {k} frame{'s' if k > 1 else ''} at {t_of(i):.2f} s in the middle of a movement"))
            i += k
        i += 1
    pts = swings(vals, amp)[1:-1]            # the turning points only (not where it starts from rest or ends)
    for a, b, c in zip(pts, pts[1:], pts[2:]):
        s1, s2 = abs(b[1] - a[1]), abs(c[1] - b[1])
        if b[0] - a[0] < SWING and c[0] - b[0] < SWING and 0.6 * s1 <= s2 <= 1.5 * s1:
            flags.append((t_of(a[0]), f"BUZZ: {label} swings back and forth every {b[0] - a[0]} to {c[0] - b[0]} frames from {t_of(a[0]):.2f} s"))
            break


def piece_jitter(sheet, scene, intro, loop, n, lo, t_of, flags, skip_nodes, repeat=True):
    elems = {e.get("id"): e for e in scene.root.iter() if e.get("id")}
    names = {k: e.get("name") or e.tag for k, e in elems.items()}
    ik, lk = sheet.anim_keys(intro), sheet.anim_keys(loop)
    for oid in sorted(set(ik) | set(lk)):
        name = names.get(oid, oid)
        if oid in skip_nodes or "Ball" in name:
            continue
        for prop in ("rotation", "x", "y"):
            if prop not in ik.get(oid, {}) and prop not in lk.get(oid, {}):
                continue
            def val(anim_keys, fr, node=oid, p=prop):
                k = anim_keys.get(node, {}).get(p)
                if k is not None:
                    return k.at(fr)
                return float(elems[node].get(p, 0))
            vals = [val(ik, fr) for fr in range(lo, 192)] + [val(lk, fr) for fr in range(n)] * 2
            wrap = {192 - lo - 1, 192 - lo + n - 1, 192 - lo + n, 192 - lo + 2 * n - 1}     # the repeated frame where the intro hands over to the loop, and where the loop wraps
            jitter_track(f"{name} {prop}", vals, prop, t_of, flags, skip=wrap)


PARKED = 36                 # frames (0.6 s): the longest the ball may be motionless outside a declared rest (docs/ball-character.md)
# PARKED fails only for a room changed after 2026-11-06 (Demetre, 2026-11-06): a room whose own pieces and timelines differ from the
# chapter's last commit of that day. The rooms as they stood then keep reporting their stillness without failing, until he rules on
# each the next time it is touched (docs/ball-character.md lists them).
PARKED_FAILS = "after 2026-11-06"
PARKED_CUTOFF = "2026-11-07 00:00"


def chapter_name(arg, room):
    """ch1, ch2 or ch3 for a chapter name, or for a copy of one (a scratch folder): the chapter whose file has this room."""
    if arg in ("ch1", "ch2", "ch3"):
        return arg
    for ch in ("ch1", "ch2", "ch3"):
        p = Path(__file__).resolve().parent.parent / "chapters" / ch / "scene.rml"
        if f'name="{room} Room"' in p.read_text():
            return ch
    return arg


def room_print(root, room):
    """The room's own content: its Room node's whole subtree and every timeline named after it, as text. Ids and the references to
    them are blanked (Chapter 2's build renumbers every id on each rebuild, which changes no room), and so is the layout whitespace."""
    import xml.etree.ElementTree as ET
    parts = []
    for e in root.iter():
        if (e.tag == "Node" and e.get("name") == f"{room} Room") or (e.tag == "LinearAnimation" and (e.get("name") or "").startswith(f"{room} ")):
            text = ET.tostring(e, encoding="unicode")
            text = re.sub(r'"\d+:\d+"', '"#"', text)
            parts.append(re.sub(r">\s+<", "><", text))
    return "\n".join(sorted(parts))


def parked_fails_for(ch, room, scene):
    """True when PARKED should fail for this room: it differs from (or didn't exist in) the chapter's last commit before the cutoff.
    Before the cutoff (on 2026-11-06 itself) nothing fails."""
    import datetime
    import subprocess
    import xml.etree.ElementTree as ET
    if not PARKED_FAILS:
        return False
    cutoff = datetime.datetime.strptime(PARKED_CUTOFF, "%Y-%m-%d %H:%M")
    if datetime.datetime.now() < cutoff:
        return False
    repo = Path(__file__).resolve().parent.parent
    rel = f"chapters/{ch}/scene.rml"
    sha = subprocess.run(["git", "log", "-1", f"--before={PARKED_CUTOFF}", "--format=%H", "--", rel], cwd=repo,
                         capture_output=True, text=True).stdout.strip()
    if not sha:
        return True
    old = subprocess.run(["git", "show", f"{sha}:./{rel}"], cwd=repo, capture_output=True, text=True)
    if old.returncode:
        return True
    return room_print(ET.fromstring(old.stdout), room) != room_print(scene.root, room)
# "Motionless" is a range over the whole stretch, not a distance from its first frame: the ball moves no more than STILL_POS units in x
# or in y, its dot turns no more than STILL_TURN degrees and its squash changes no more than STILL_SCALE of its size. A dot swaying a degree and a
# squash of a percent or two is still a parked ball (the Mini's top cube, 6.70 to 7.68 s, was missed with 0.3 units, 0.5 degrees and
# 0.005 measured from the first frame); an idle roll of a few units, a glance or a hop is not.
STILL_POS, STILL_TURN, STILL_SCALE = 2.0, 3.0, 0.03     # units, degrees, fraction of the ball's size
RESTS = Path(__file__).resolve().parent / "ball_rests.json"


def ball_tracks(sheet, anim, chain, frames):
    """[(x, y, turn in degrees, scaleX, scaleY, seen)] of the ball on each frame: the chain's position, the turn and scale of every node
    under the ball's top node (its spin pivot, its squash), and whether it can be seen (not faded out, not shrunk away, on the
    artboard; a ball hidden by a clip inside an object can't be told apart from a visible one: declare that as a rest)."""
    keys = sheet.anim_keys(anim)
    nodes = list(chain[-1].iter("Node"))
    # what decides whether the ball shows: its body (Ball_01_Base) and every node from it up to the ball's top node (not the other
    # shapes under the ball, such as a clip's hidden source or a spare copy, which may be at opacity 0 all along)
    body = next((e for e in chain[-1].iter("Shape") if e.get("name") == "Ball_01_Base"), None)
    shapes = ([body] if body is not None else []) + [e for e in chain[-1].iter("Node") if body is not None and body in e.iter()]

    def val(node, prop, f, default):
        k = keys.get(node.get("id"), {}).get(prop)
        return k.at(f) if k is not None else float(node.get(prop, default))
    out = []
    for f in frames:
        x = sum(val(n, "x", f, 0) for n in chain)
        y = sum(val(n, "y", f, 0) for n in chain)
        turn = math.degrees(sum(val(n, "rotation", f, 0) for n in nodes))
        sx = sy = 1.0
        for n in nodes:
            sx *= val(n, "scaleX", f, 1)
            sy *= val(n, "scaleY", f, 1)
        op = 1.0
        for n in shapes:
            op *= val(n, "opacity", f, 1)
        seen = op > 0.05 and abs(sx * sy) > 0.01 and -60 < x < 1555 and -60 < y < 1127
        out.append((x, y, turn, sx, sy, seen))
    return out


def rests_for(chapter, room):
    """The rests declared for this room in tools/ball_rests.json: [(from, to, why)] in Finesse-panel seconds."""
    try:
        entries = json.loads(RESTS.read_text())["rests"]
    except (OSError, ValueError, KeyError):
        return []
    return [(float(e["from"]), float(e["to"]), e.get("why", "")) for e in entries if e.get("chapter") == chapter and e.get("room") == room]


def parked_report(tracks, t_of, loop_s, tmax, rests):
    """Stretches of more than PARKED frames where the ball neither moves, turns nor squashes (within STILL_POS, STILL_TURN and STILL_SCALE), outside a declared rest. tracks: one
    entry per frame of the sequence (intro tail, then the loop twice); t_of(i): its Finesse time. A rest covers a frame when the
    frame's time, or that time one loop earlier (the rest runs across the seam), falls inside it. Frames where the ball can't be seen
    don't count. The sequence starts at Finesse 1.67 s, when the room's pan (1.65 s) is over, so the ball's wait for its room to arrive
    isn't read; stillness after that is (the Mini's ball sat in its box from 2.1 to 3.5 s and an earlier version of this check skipped it)."""
    def resting(i):
        t = t_of(i)
        return not tracks[i][5] or any(a <= tt <= b for a, b, _ in rests for tt in (t, t - loop_s, t + loop_s))
    flags, i, n = [], 0, len(tracks)
    while i < n:
        x, y, r, sx, sy, _ = tracks[i]
        lo_ = [x, y, r, sx, sy]
        hi_ = list(lo_)
        j = i
        while j + 1 < n:
            nxt = tracks[j + 1][:5]
            l2, h2 = [min(a, b) for a, b in zip(lo_, nxt)], [max(a, b) for a, b in zip(hi_, nxt)]
            if h2[0] - l2[0] > STILL_POS or h2[1] - l2[1] > STILL_POS or h2[2] - l2[2] > STILL_TURN or (h2[3] - l2[3]) > STILL_SCALE * h2[3] or (h2[4] - l2[4]) > STILL_SCALE * h2[4]:
                break
            lo_, hi_ = l2, h2
            j += 1
        length = sum(1 for k in range(i, j + 1) if not resting(k))
        if length > PARKED and t_of(i) <= tmax:
            flags.append((t_of(i), f"PARKED: the ball is motionless for {(j - i + 1) / 60:.2f} s from {t_of(i):.2f} s ({length} frames outside a declared rest; "
                                   f"the most is {PARKED}, or declare the rest in tools/ball_rests.json)"))
        i = j + 1
    return flags


ACCEPTED = Path(__file__).resolve().parent / "ball_speed_accepted.json"


def accepted_for(chapter, room):
    try:
        entries = json.loads(ACCEPTED.read_text())["accepted"]
    except (OSError, ValueError, KeyError):
        return []
    return [e for e in entries if e.get("chapter") == chapter and e.get("room") == room]


def acceptance(msg, entries):
    """The entry that accepts this flag, or None."""
    for e in entries:
        m = re.search(e["pattern"], msg)
        if not m:
            continue
        if m.groups() and ("min" in e or "max" in e):
            v = float(m.group(1))
            if v < e.get("min", float("-inf")) or v > e.get("max", float("inf")):
                continue
        return e
    return None


def print_flags(title, flags, entries):
    """Prints the flags, the accepted ones marked; returns how many are not accepted."""
    if not flags:
        print(f"{title}: no flags")
        return 0
    marked = [(msg, acceptance(msg, entries)) for _, msg in flags]
    open_ = sum(1 for _, e in marked if e is None)
    print(f"{title}: {len(flags)} flag{'s' if len(flags) != 1 else ''}, {len(flags) - open_} accepted, {open_} open")
    for msg, e in marked:
        print(f"  - {msg}" + (f"   ACCEPTED ({e['why']}; {e['approved']})" if e else ""))
    return open_


def main(argv):
    chapter, room = argv[0], argv[1]
    s = Scene(chapter_dir(chapter) / "scene.rml")
    sheet = Sheet(s)
    chain = sheet.ball_roots(room)
    intro, loop = s.animations[f"{room} Intro"], s.animations[f"{room} Loop"]
    n = s.duration(loop)
    if "--keys" in argv:
        for name, an in (("Intro", intro), ("Loop", loop)):
            keys = sheet.anim_keys(an)
            for node in chain:
                for prop, k in keys.get(node.get("id"), {}).items():
                    if prop in ("x", "y"):
                        print(f'{name} {node.get("name")} {prop}: ' + " · ".join(f"{f} {v:.2f} ({e or h})" for f, v, h, e, _ in k.rows))
        return 0
    if "--contacts" in argv:
        lo = int(argv[argv.index("--lo") + 1]) if "--lo" in argv else 100
        seq = positions(sheet, intro, chain, range(lo, 192), 192) + positions(sheet, loop, chain, range(n), n) * 2
        # Finesse timecode of sequence index i: intro frame lo + i, or 192 + loop frame (first pass); the second pass repeats the loop
        t_of = lambda i: (lo + i) / 60.0
        flags = contacts_report(seq, t_of, (192 + n + 40) / 60.0)
        tracks = ball_tracks(sheet, intro, chain, range(lo, 192)) + ball_tracks(sheet, loop, chain, range(n)) * 2
        ch = chapter_name(chapter, room)                      # a copy (a scratch folder) reads its chapter's rests and accepted flags
        rests = rests_for(ch, room)
        parked = parked_report(tracks, t_of, n / 60.0, (192 + n) / 60.0, rests)
        parked = sorted({(round(t, 3), m_) for t, m_ in parked})
        if parked and parked_fails_for(ch, room, s):
            flags, parked = sorted(set(flags) | set(parked)), []
        for a, b, why in rests:
            print(f"declared rest {a:.2f} to {b:.2f} s: {why}")
        entries = accepted_for(ch, room)
        print()
        open_ = print_flags("the ball", flags, entries)
        jit = []
        piece_jitter(sheet, s, intro, loop, n, lo, t_of, jit, {x.get("id") for x in chain})
        tmax = (192 + n + 40) / 60.0
        jit = sorted({(round(t, 3), m_) for t, m_ in jit if t <= tmax})
        open_ += print_flags("jitter on the pieces", jit, entries)
        if parked:
            print(f"parked, reported only (this room is unchanged since 2026-11-06; it fails once the room changes): {len(parked)}")
            for _, m_ in parked:
                print(f"  - {m_}")
        print(f"\n{'PASS' if not open_ else 'FAIL'}  {room}: {open_} open flag{'s' if open_ != 1 else ''}" + ("" if not open_ else " (fix them, or ask Demetre to accept them in tools/ball_speed_accepted.json)"))
        return 1 if open_ else 0
    lo = int(argv[argv.index("--from") + 1]) if "--from" in argv else 120
    hi = int(argv[argv.index("--to") + 1]) if "--to" in argv else None
    seq = [("intro", f, p) for f, p in zip(range(lo, 192), positions(sheet, intro, chain, range(lo, 192), 192))]
    seq += [("loop", f, p) for f, p in zip(range(n), positions(sheet, loop, chain, range(n), n))]
    seq += [("loop", f, p) for f, p in zip(range(n), positions(sheet, loop, chain, range(n), n))][:30]
    last_v = None
    prev = None
    for i, (where, f, p) in enumerate(seq):
        if hi is not None and where == "loop" and f > hi and i < len(seq) - 30:
            continue
        if prev is None:
            print(f"{where} {f:3d}  x {p[0]:8.2f} y {p[1]:8.2f}")
        else:
            vx, vy = p[0] - prev[0], p[1] - prev[1]
            v = math.hypot(vx, vy)
            dv = "" if last_v is None else f"{v - last_v:+7.2f}"
            print(f"{where} {f:3d}  x {p[0]:8.2f} y {p[1]:8.2f}  v {v:6.2f}  dv {dv}")
            last_v = v
        prev = p
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
