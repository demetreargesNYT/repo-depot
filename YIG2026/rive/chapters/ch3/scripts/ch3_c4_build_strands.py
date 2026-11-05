"""Chapter 4 city, Strands: the build (spheres pop in, then the sticks draw between them) and the slight sway (Demetre, 2026-11-04).

    python3 chapters/ch3/scripts/ch3_c4_build_strands.py [--scene PATH] --write      without --write it only measures

Art (children of the "Strands" node 9:3993): five 40 unit grey spheres, three white highlights, seven sticks (a Node holding a coloured
stroke and its dark outline stroke, each ending on two sphere centres).
BUILD (front layer, frames 130 to 190): spheres pop in bottom to top, 5 frames apart, each scaling and fading in from its own centre
with one small overshoot (highlights ride with their sphere: scaled about the sphere's centre). Then each stick grows from the centre of
the sphere that came in first to the other, once both spheres are in (uniform scale plus x, y keyed together so the end stays put).
LOOP: the reference sway (3 cycles of 200 frames, spheres lag, sticks recomputed from their two spheres), no roll, no wake. Calm: 1.2 degrees.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ch3_c4_city import LOOP, BUILD, add_building, scene_path, ROOM
from rml_edit import Doc
from rml_read import Scene

NAME = "Strands"
PERIOD = 200
W = 2 * math.pi / PERIOD
LAG_AMP = {1: [(4, 1.5), (5, 1.6)], 2: [(7, 2.0), (9, 2.1)]}
GAIN = 0.81
CALM_MAX = 1.2
POP_START, POP_GAP, POP_LEN, FADE = 130, 5, 14, 5     # sphere i pops at POP_START + i * POP_GAP (bottom to top)
STICK_LEN, STICK_FADE = 20, 3


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


def build_art(scene):
    node, spheres, lights, sticks = read_art(scene)
    spheres.sort(key=lambda s: s[2])
    hook = spheres[0]
    S = {s[0]: (s[1], s[2]) for s in spheres}
    near = lambda p: next(k for k, q in S.items() if math.dist(p, q) < 1)
    edges = []
    for oid, x, y, v in sticks:
        a, b = near((x + v[0][0], y + v[0][1])), near((x + v[1][0], y + v[1][1]))
        edges.append((oid, a, b, (x, y), math.atan2(v[1][1] - v[0][1], v[1][0] - v[0][0])))
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
    light_of = {}
    for lid, lx, ly in lights:
        k = next(k for k, q in S.items() if math.dist((lx, ly), q) < 20)
        light_of[k] = (lid, lx, ly)
    return dict(spheres=S, hook=hook, edges=edges, swing=swing, light_of=light_of, lights=lights)


def angles_at(a, t, k=1.0):
    return {s: GAIN * k * math.radians(amp) * (math.sin(W * (t - lag)) + math.sin(W * lag)) for s, (lag, amp) in a["swing"].items()}


def pose(a, th):
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
            ox, oy = a["spheres"][s]
            out[(lid, "x")], out[(lid, "y")] = lx + P[s][0] - ox, ly + P[s][1] - oy
    for oid, u, v, mid, ang in a["edges"]:
        (ux, uy), (vx, vy) = P[u], P[v]
        out[(oid, "x")], out[(oid, "y")] = (ux + vx) / 2, (uy + vy) / 2
        d = math.atan2(vy - uy, vx - ux) - ang
        out[(oid, "rotation")] = (d + math.pi) % (2 * math.pi) - math.pi
    return out


def extremes(fn, n=LOOP):
    step = 0.05
    xs = [i * step for i in range(int(n / step) + 1)]
    ys = [fn(x) for x in xs]
    return [(round(xs[i]), ys[i]) for i in range(1, len(xs) - 1) if (ys[i] - ys[i - 1]) * (ys[i + 1] - ys[i]) < 0]


def sway_keys(fn, tol):
    ex = extremes(fn)
    vals = [fn(i * 0.5) for i in range(2 * LOOP + 1)]
    if max(vals) - min(vals) < tol:
        return None
    keys = [(0, fn(0), "sine.out")] + [(f, v, "sine.inOut") for f, v in ex]
    keys[-1] = (keys[-1][0], keys[-1][1], "sine.in")
    keys.append((LOOP, fn(LOOP), "hold"))
    return keys


def sway_tracks(a, k):
    keys = {}
    for key in pose(a, angles_at(a, 0, k)):
        fn = (lambda key: lambda t: pose(a, angles_at(a, t, k))[key])(key)
        ks = sway_keys(fn, 0.0003 if key[1] == "rotation" else 0.02)
        if ks:
            keys[key] = ks
    return keys


def build_tracks(a):
    """The build: {(id, prop): keys} and per-piece first-visible frames."""
    S, rest = a["spheres"], pose(a, {})
    order = sorted(S, key=lambda s: (-S[s][1], S[s][0]))          # bottom to top, left to right
    start = {s: POP_START + POP_GAP * i for i, s in enumerate(order)}
    tr, seen = {}, {}

    def pop(oid, f0, scale_keys=True):
        tr[(oid, "opacity")] = [(0, 0, "hold"), (f0, 0, "power1.out"), (f0 + FADE, 1, "hold"), (BUILD, 1, "hold")]
        if scale_keys:
            for p in ("scaleX", "scaleY"):
                tr[(oid, p)] = [(0, 0, "hold"), (f0, 0, "back.out.small"), (f0 + POP_LEN, 1, "hold"), (BUILD, 1, "hold")]
        seen[oid] = f0
    for s in order:
        pop(s, start[s])
    for s, (lid, lx, ly) in a["light_of"].items():
        f0, (sx, sy) = start[s], S[s]
        pop(lid, f0)
        # the highlight rides with its sphere's pop: it sits at the sphere's centre and moves out to its place in step with the scale
        for p, c, v in (("x", sx, lx), ("y", sy, ly)):
            tr[(lid, p)] = [(0, c, "hold"), (f0, c, "back.out.small"), (f0 + POP_LEN, v, "hold"), (BUILD, v, "hold")]
    for oid, u, v, _, _ in a["edges"]:
        first, second = (u, v) if start[u] <= start[v] else (v, u)
        f0 = max(start[u], start[v]) + POP_LEN
        f1 = min(f0 + STICK_LEN, BUILD - 2)
        f0 = f1 - STICK_LEN
        (ax, ay), (bx, by) = S[first], S[second]
        tr[(oid, "opacity")] = [(0, 0, "hold"), (f0, 0, "power1.out"), (f0 + STICK_FADE, 1, "hold"), (BUILD, 1, "hold")]
        for p in ("scaleX", "scaleY"):
            tr[(oid, p)] = [(0, 0, "hold"), (f0, 0, "back.out.small"), (f1, 1, "hold"), (BUILD, 1, "hold")]
        for p, c, e in (("x", ax, (ax + bx) / 2), ("y", ay, (ay + by) / 2)):
            tr[(oid, p)] = [(0, c, "hold"), (f0, c, "back.out.small"), (f1, e, "hold"), (BUILD, e, "hold")]
        seen[oid] = f0
    # the build's x, y end on the sway's first value (the rest pose): the sticks' midpoints, the lights' places
    for key, keys in tr.items():
        if key in rest:
            assert abs(keys[-1][1] - rest[key]) < 1e-6, (key, keys[-1][1], rest[key])
    return tr, seen


def measure(a):
    rest = pose(a, {})
    worst = {"sphere travel": 0.0, "stick tilt deg": 0.0}
    for t in range(LOOP + 1):
        p = pose(a, angles_at(a, t))
        for (oid, prop), v in p.items():
            if prop == "rotation":
                worst["stick tilt deg"] = max(worst["stick tilt deg"], abs(math.degrees(v)))
        for s in a["swing"]:
            worst["sphere travel"] = max(worst["sphere travel"], math.hypot(p[(s, "x")] - rest[(s, "x")], p[(s, "y")] - rest[(s, "y")]))
    worst["max sphere angle deg"] = max(math.degrees(abs(v)) for t in range(LOOP + 1) for v in angles_at(a, t).values())
    return worst


def fix_strokes(doc):
    """Every stroke inside Strands keeps 1.5 / its weight when scaled."""
    i = doc.idx("9:3993")
    j = doc.end(i)
    n = 0
    for k in range(i, j + 1):
        l = doc.lines[k]
        if l.lstrip().startswith("<Stroke ") and "transformAffectsStroke" not in l:
            doc.lines[k] = l.replace(' id="', ' transformAffectsStroke="false" id="', 1)
            n += 1
    return n


def main(path, write):
    doc = Doc(path)
    assert f"{ROOM} City {NAME}" not in "\n".join(doc.lines), "Strands' layer already exists"
    a = build_art(path)
    full = sway_tracks(a, 1.0)
    kmax = max(max(abs(angles_at(a, t / 2)[s]) for s in a["swing"]) for t in range(2 * LOOP + 1))
    calm_k = math.radians(CALM_MAX) / kmax
    calm = sway_tracks(a, calm_k)
    for key, keys in full.items():           # a property the loop sways stays keyed in Calm too
        calm.setdefault(key, [(0, keys[0][1], "hold"), (LOOP, keys[0][1], "hold")])
    bt, seen = build_tracks(a)
    if write:
        print("strokes fixed:", fix_strokes(doc))
        add_building(doc, NAME, {"build": bt, "loop": full, "calm": calm})
        doc.save()
    print({k: round(v, 3) for k, v in measure(a).items()}, "calm scale", round(calm_k, 3), "build tracks", len(bt), "loop", len(full), "calm", len(calm))
    print("first visible frames:", {k: v for k, v in sorted(seen.items(), key=lambda kv: kv[1])})
    print("complete at frame", max(f for v in seen.values() for f in [v]) + STICK_LEN)


if __name__ == "__main__":
    main(scene_path(), "--write" in sys.argv)
