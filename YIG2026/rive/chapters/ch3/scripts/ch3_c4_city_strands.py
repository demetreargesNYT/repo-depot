"""Chapter 4 card 1, the living city: Strands, the lattice of grey spheres on blue and yellow sticks (Demetre, 2026-11-04).

    python3 chapters/ch3/scripts/ch3_c4_city_strands.py [--scene PATH] --write      once; without --write it only measures

The art (children of the "Strands" node, id 9:3993): five 40 unit grey spheres, three of them with a white highlight (the small
white ellipse on the upper left of the sphere), and seven sticks (a Node holding a coloured stroke and its dark outline stroke)
that join the sphere centres as a lattice: top sphere A to the two middle spheres B and C, B and C each to both bottom spheres D
and E (a cross), and D to E along the floor. Every stick ends on a sphere centre.

The motion: a hanging mobile. The top sphere A is the hook and stays put. B, C, then D, E swing about A on a 200 frame (3.333 s)
pendulum, three cycles to the 600 frame loop, each a few frames behind the one above it (lag 4, 5 then 7, 9 frames) and by a
slightly different amount (1.5 to 2.1 degrees; with the lag's offset the largest angle is 2.7). Every stick is recomputed from
the two sphere centres it joins (its middle, its angle), so a sphere's centre always stays on its stick's end; the stick lengths
change by under a pixel or two, which the spheres (drawn over the sticks, radius 20) hide. Once, at 8.6 to 9.4 s (frames 516 to
564), the sphere C rolls 22 degrees clockwise on its stick and back, its highlight travelling round with one small overshoot each
way (the highlight sits in its own pivot at the sphere's centre). Wake: from frame 136, one pull back and a release that ends on
the rest pose moving at the loop's first speed, so the sway carries on from it. Calm: the same sway at 1.2 degrees at most, no roll.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ch3_c4_city import LOOP, WAKE, WAKE_AT, add_building, scene_path, ROOM
from rml_edit import Doc
from rml_read import Scene

NAME = "Strands"
PERIOD = 200
W = 2 * math.pi / PERIOD
LAG_AMP = {1: [(4, 1.5), (5, 1.6)], 2: [(7, 2.0), (9, 2.1)]}      # by depth from the hook, left to right: (lag frames, degrees)
GAIN = 0.82                                                       # keeps every stick's own tilt under 3 degrees
CALM_MAX = 1.2                                                    # degrees, the largest angle in Calm
ROLL_DEG, ROLL_AT = 22.0, (516, 534, 540, 562)                    # the roll: start, turned, start back, back (frames)
WAKE_T = (WAKE_AT[NAME], 164, WAKE)                               # the wake: start, the pull back's end, end
WAKE_D = WAKE - WAKE_T[1]


def ellipse_size(shape):
    e = shape.find("Ellipse")
    return None if e is None else float(e.get("width"))


def read_art(scene):
    sc = Scene(scene)
    room = next(e for e in sc.root.iter("Node") if e.get("name") == f"{ROOM} Room")
    node = next(e for e in room.iter("Node") if e.get("name") == NAME)
    assert node.get("id") == "9:3993", node.get("id")
    spheres, lights, sticks = [], [], []
    for ch in node:
        f = lambda k: float(ch.get(k, 0))
        if ch.tag == "Shape" and ellipse_size(ch) == 40:
            spheres.append((ch.get("id"), f("x"), f("y")))
        elif ch.tag == "Shape" and ellipse_size(ch) is not None:
            lights.append((ch.get("id"), f("x"), f("y")))
        elif ch.tag == "Node":
            v = [(float(a.get("x", 0)), float(a.get("y", 0))) for a in ch.find("Shape").find("PointsPath")]
            sticks.append((ch.get("id"), f("x"), f("y"), v))
    assert (len(spheres), len(lights), len(sticks)) == (5, 3, 7) and len(list(node)) == 15
    return node, spheres, lights, sticks


def build(scene):
    node, spheres, lights, sticks = read_art(scene)
    spheres.sort(key=lambda s: s[2])
    hook = spheres[0]
    S = {s[0]: (s[1], s[2]) for s in spheres}
    near = lambda p: next(k for k, q in S.items() if math.dist(p, q) < 1)
    edges = []
    for oid, x, y, v in sticks:
        a, b = near((x + v[0][0], y + v[0][1])), near((x + v[1][0], y + v[1][1]))
        edges.append((oid, a, b, (x, y), math.atan2(v[1][1] - v[0][1], v[1][0] - v[0][0])))
    # depth from the hook along the sticks
    depth, todo = {hook[0]: 0}, [hook[0]]
    while todo:
        cur = todo.pop(0)
        for _, a, b, _, _ in edges:
            for p, q in ((a, b), (b, a)):
                if p == cur and q not in depth:
                    depth[q] = depth[cur] + 1
                    todo.append(q)
    swing = {}
    for d, spec in LAG_AMP.items():
        ids = sorted((k for k in S if depth[k] == d), key=lambda k: S[k][0])
        assert len(ids) == len(spec), (d, ids)
        swing.update(dict(zip(ids, spec)))
    # the highlight belongs to the sphere it sits on (within 20 units)
    light_of = {}
    for lid, lx, ly in lights:
        k = near_sphere = next(k for k, q in S.items() if math.dist((lx, ly), q) < 20)
        light_of[k] = (lid, lx, ly)
    rollers = sorted((k for k in light_of if k in swing), key=lambda k: -S[k][0])
    roller = rollers[0]                                           # the right hand middle sphere (C)
    return dict(spheres=S, hook=hook, edges=edges, swing=swing, light_of=light_of, roller=roller, lights=lights)


def angles_at(a, t, k=1.0):
    """{sphere id: angle in radians} of every swinging sphere at frame t (k scales the sway)."""
    return {s: GAIN * k * math.radians(amp) * (math.sin(W * (t - lag)) + math.sin(W * lag)) for s, (lag, amp) in a["swing"].items()}


def pose(a, th):
    """{(object id, property): value} for the spheres' angles `th` ({sphere id: radians}; the hook 0)."""
    hx, hy = a["spheres"][a["hook"][0]]
    P = {}
    for s, (x, y) in a["spheres"].items():
        c, sn = math.cos(th.get(s, 0)), math.sin(th.get(s, 0))
        P[s] = (hx + (x - hx) * c - (y - hy) * sn, hy + (x - hx) * sn + (y - hy) * c)
    out = {}
    for s, (x, y) in P.items():
        if s != a["hook"][0]:
            out[(s, "x")], out[(s, "y")] = x, y
    for s, (lid, lx, ly) in a["light_of"].items():
        if s in a["swing"]:
            ox, oy = x0, y0 = a["spheres"][s]
            if s == a["roller"]:
                out[(lid + "#pivot", "x")], out[(lid + "#pivot", "y")] = P[s]
            else:
                out[(lid, "x")], out[(lid, "y")] = lx + P[s][0] - ox, ly + P[s][1] - oy
    for oid, u, v, mid, ang in a["edges"]:
        (ux, uy), (vx, vy) = P[u], P[v]
        out[(oid, "x")], out[(oid, "y")] = (ux + vx) / 2, (uy + vy) / 2
        d = math.atan2(vy - uy, vx - ux) - ang
        out[(oid, "rotation")] = (d + math.pi) % (2 * math.pi) - math.pi
    return out


def extremes(fn, n=LOOP):
    """Frames (rounded) and values of every extreme of fn over 0..n, plus the first and last frames."""
    step = 0.05
    xs = [i * step for i in range(int(n / step) + 1)]
    ys = [fn(x) for x in xs]
    found = []
    for i in range(1, len(xs) - 1):
        if (ys[i] - ys[i - 1]) * (ys[i + 1] - ys[i]) < 0 or (ys[i] != ys[i - 1] and ys[i + 1] == ys[i] and False):
            found.append((round(xs[i]), ys[i]))
    return found


def sway_keys(fn, tol):
    """Keys for a sinusoid-like loop signal: a key at each extreme, sine.inOut between them, sine.out into the first and sine.in out of the last."""
    ex = extremes(fn)
    lo, hi = min(fn(i * 0.5) for i in range(2 * LOOP + 1)), max(fn(i * 0.5) for i in range(2 * LOOP + 1))
    if hi - lo < tol:
        return None
    keys = [(0, fn(0), "sine.out")]
    for f, v in ex:
        keys.append((f, v, "sine.inOut"))
    keys[-1] = (keys[-1][0], keys[-1][1], "sine.in")
    keys.append((LOOP, fn(LOOP), "hold"))
    return keys


def tracks(a, k):
    keys = {}
    sig = {}
    for key in pose(a, angles_at(a, 0, k)):
        sig[key] = (lambda key: lambda t: pose(a, angles_at(a, t, k))[key])(key)
    for key, fn in sig.items():
        tol = 0.0003 if key[1] == "rotation" else 0.02
        ks = sway_keys(fn, tol)
        if ks:
            keys[key] = ks
    return keys


def wake_tracks(a, loop_keys):
    th = {s: -0.56 * math.cos(W * lag) * GAIN * math.radians(amp) for s, (lag, amp) in a["swing"].items()}
    trough = pose(a, th)
    rest = pose(a, {})
    out = {}
    for key in loop_keys:
        if key in trough and abs(trough[key] - rest[key]) > (0.0003 if key[1] == "rotation" else 0.02) * 0.2:
            out[key] = [(0, rest[key], "hold"), (WAKE_T[0], rest[key], "sine.inOut"), (WAKE_T[1], trough[key], "sine.in"), (WAKE, rest[key], "hold")]
    return out


def roll_tracks(a):
    r = math.radians(ROLL_DEG)
    s0, s1, s2, s3 = ROLL_AT
    return [(0, 0.0, "hold"), (s0, 0.0, "back.out.small"), (s1, r, "hold"), (s2, r, "back.out.small"), (s3, 0.0, "hold"), (LOOP, 0.0, "hold")]


def measure(a, trk):
    rest = pose(a, {})
    worst = {"sphere travel": 0.0, "stick travel": 0.0, "stick tilt deg": 0.0, "sphere angle deg": 0.0}
    for t in range(LOOP + 1):
        th = angles_at(a, t)
        worst["sphere angle deg"] = max(worst["sphere angle deg"], max(abs(math.degrees(v)) for v in th.values()))
        p = pose(a, th)
        for (oid, prop), v in p.items():
            if prop == "rotation":
                worst["stick tilt deg"] = max(worst["stick tilt deg"], abs(math.degrees(v)))
        for s in a["swing"]:
            worst["sphere travel"] = max(worst["sphere travel"], math.hypot(p[(s, "x")] - rest[(s, "x")], p[(s, "y")] - rest[(s, "y")]))
        for oid, *_ in a["edges"]:
            worst["stick travel"] = max(worst["stick travel"], math.hypot(p[(oid, "x")] - rest[(oid, "x")], p[(oid, "y")] - rest[(oid, "y")]))
    # stick length change (the spheres hide it)
    S = a["spheres"]
    dl = 0.0
    for t in range(LOOP + 1):
        th = angles_at(a, t)
        hx, hy = S[a["hook"][0]]
        P = {s: (hx + (x - hx) * math.cos(th.get(s, 0)) - (y - hy) * math.sin(th.get(s, 0)),
                 hy + (x - hx) * math.sin(th.get(s, 0)) + (y - hy) * math.cos(th.get(s, 0))) for s, (x, y) in S.items()}
        for _, u, v, _, _ in a["edges"]:
            dl = max(dl, abs(math.dist(P[u], P[v]) - math.dist(S[u], S[v])))
    worst["stick length change"] = dl
    return worst


def main(path, write):
    doc = Doc(path)
    assert f"{ROOM} City {NAME}" not in "\n".join(doc.lines), "Strands' layer already exists"
    a = build(path)
    full = tracks(a, 1.0)
    peak = max(abs(v) for v in angles_at(a, 0).values())
    kmax = max(max(abs(angles_at(a, t / 2)[s]) for s in a["swing"]) for t in range(2 * LOOP + 1))
    calm_k = math.radians(CALM_MAX) / kmax
    calm = tracks(a, calm_k)
    wake = wake_tracks(a, full)
    # the roll on the right middle sphere's highlight, which gets its own pivot at the sphere's centre
    lid, lx, ly = a["light_of"][a["roller"]]
    cx, cy = a["spheres"][a["roller"]]
    pivot_key = lid + "#pivot"
    if write:
        pid, _ = doc.wrap(lid, "Strands Highlight Roll", cx, cy)
    else:
        pid = "PIVOT"
    remap = lambda trk: {((pid if k[0] == pivot_key else k[0]), k[1]): v for k, v in trk.items()}
    full, calm, wake = remap(full), remap(calm), remap(wake)
    full[(pid, "rotation")] = roll_tracks(a)
    if write:
        add_building(doc, NAME, {"loop": full, "calm": calm, "wake": wake})
        doc.save()
    w = measure(a, full)
    print({k: round(v, 3) for k, v in w.items()}, "calm scale", round(calm_k, 3), "keyed loop tracks", len(full), "calm", len(calm), "wake", len(wake))


if __name__ == "__main__":
    main(scene_path(), "--write" in sys.argv)
