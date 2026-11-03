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
"""
import math
import sys

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
    if abs(a[0]) < 0.03 and a[1] > 0.05 and len(vs) >= 5:
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
            if abs(g - G_STD) > 0.04:
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
        if abs(vin[0]) > 1.5 and abs(vout[0]) > 1.5 and vin[0] * vout[0] < 0:
            tilt = abs(math.degrees(math.atan2(dv[0], -dv[1]))) if math.hypot(*dv) > 0.5 else 0
            if tilt < 30 or tilt > 150:
                notes.append("FLAG turns round off a near-flat surface")
                flags.append((t, f"turn-round at {t:.2f} s (x {pts[i][0]:.0f}) off a surface tilted only {tilt:.0f} deg"))
            else:
                notes.append("turns round (surface tilted %d deg)" % round(tilt))
        row = f"{t:6.2f} ({pts[i][0]:5.0f},{pts[i][1]:4.0f})  {si:5.1f} @{ang(vin):5.0f}  {so:5.1f} @{ang(vout):5.0f}  {kept * 100:4.0f}%  {nrm:>7}  " + "; ".join(notes)
        print(row)
    kinds = {}
    for a0, a1, vs, a, kind in segs:
        kinds[kind] = kinds.get(kind, 0) + 1
    print(f"\n{len([c for c in contacts if t_of(c[0]) <= tmax_report])} contacts; segments: " + ", ".join(f"{n} {k}" for k, n in kinds.items()))
    flags = sorted({(round(t, 3), m_) for t, m_ in flags if t <= tmax_report})
    if flags:
        print(f"{len(flags)} FLAGS:")
        for t, msg in flags:
            print("  -", msg)
    else:
        print("no flags")
    return flags


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
        contacts_report(seq, t_of, (192 + n + 40) / 60.0)
        return 0
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
