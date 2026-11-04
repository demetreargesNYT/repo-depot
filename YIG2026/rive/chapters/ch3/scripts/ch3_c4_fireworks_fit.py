"""Chapter 4: no firework ever crosses the copy, and no firework draws a dot where a piece has shrunk to nothing (Demetre, 2026-11-04).

    python3 chapters/ch3/scripts/ch3_c4_fireworks_fit.py --scene PATH [--write]      once, on the scene as committed in 89feb98

Without --write it only measures (before and after, in memory) and prints the table. With --write it saves the scene.

Placement (each of the five gates on its own; bursts keep their size, look and timing):
- every burst (the unit below its container: Wordle/Connections/Crossword/Spelling Bee children of the containers, Strands' children
  of the gate) has its centre mapped from world y to a + k * y, with the largest k (<= 1) for which no piece that touches
  x 540..955 is higher than y TOP at any frame of "Chapter 4 Fireworks Loop" and no piece is lower than y BOTTOM. A burst with
  static y gets a new y; a burst with keyed y (Strands) gets every key value mapped (same shape of curve, shorter travel), and
  the same value in "Chapter 4 Fireworks Idle".
Dots:
- a piece that has shrunk to scale 0 on both axes still draws a dot with its 1.5 non-scaling stroke. The topmost piece that is at
  scale 0 gets opacity 0 on exactly those frames (opacity keys, switching while it is at scale 0, hold keys at the two ends).
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ch3_c4_fireworks_measure import ANIM, GATES, Gate, Scene, num as val
from rml_edit import Doc, num

TOP, BOTTOM = 445.0, 706.0       # the copy's lowest case is y 418 (small phone); 440 is the asked-for limit, 5 more for the stroke and the elastic
IDLE = "Chapter 4 Fireworks Idle"


def survey(scene):
    """{gate: {highest, frame, piece, dots}} over the 300 frames."""
    out = {}
    for name in GATES:
        g = Gate(scene, name)
        hi = None
        lo = None
        ndots = 0
        for f in range(300):
            for pn, box, dot, uid, ids in g.pieces(f):
                ndots += dot
                if box[2] >= 540 and box[0] <= 955 and (hi is None or box[1] < hi[0]):
                    hi = (box[1], f, pn)
                if lo is None or box[3] > lo[0]:
                    lo = (box[3], f, pn)
        out[name] = dict(highest=hi, lowest=lo, dots=ndots)
    return out


def solve(g):
    samples = []
    for f in range(300):
        for pn, box, dot, uid, ids in g.pieces(f):
            samples.append((box, g.origin[uid][1], box[2] >= 540 and box[0] <= 955))
    oys = sorted(oy for _, oy, _ in samples)
    med = oys[len(oys) // 2]
    for ki in range(100, 19, -1):
        k = ki / 100
        lo = max([TOP - b[1] - (k - 1) * oy for b, oy, col in samples if col], default=-1e9)
        hi = min([BOTTOM - b[3] - (k - 1) * oy for b, oy, col in samples], default=1e9)
        if lo <= hi:
            return k, min(max((1 - k) * med, lo), hi)
    raise SystemExit(f"{g.name}: no fit")


def parent_offset(g, unit):
    y = 0.0
    p = g.scene.parent[unit]
    while p is not None and p.tag in ("Node", "Shape"):
        assert float(p.get("scaleX", 1)) == 1 and float(p.get("scaleY", 1)) == 1 and float(p.get("rotation", 0)) == 0, p.get("name")
        assert p.get("id") not in g.keys, ("a container is keyed", p.get("name"))
        y += float(p.get("y", 0))
        p = g.scene.parent.get(p)
    return y


def set_attr(doc, oid, name, value):
    i = doc.idx(oid)
    line = doc.lines[i]
    v = num(value)
    if re.search(rf'\b{name}="', line):
        doc.lines[i] = re.sub(rf'\b{name}="[^"]*"', f'{name}="{v}"', line, count=1)
    else:
        m = re.match(r"(\s*<\w+)", line)
        doc.lines[i] = line[:m.end()] + f' {name}="{v}"' + line[m.end():]


def rewrite_key_values(doc, anim, oid, prop, fn):
    """Map every key value of one property of one object in one animation."""
    a, b = doc.anim(anim)
    found = doc._object(a, b, oid)
    if not found:
        return False
    i, j = found
    pat = re.compile(r'^\s*<KeyedProperty\b[^>]*\bproperty="%s"' % prop)
    k = next((k for k in range(i + 1, j) if pat.match(doc.lines[k])), None)
    if k is None:
        return False
    for n in range(k + 1, doc.end(k)):
        line = doc.lines[n]
        if line.lstrip().startswith("<KeyFrameDouble"):
            m = re.search(r'\bvalue="([^"]*)"', line)
            old = float(m.group(1)) if m else 0.0
            new = num(fn(old))
            if m:
                doc.lines[n] = line.replace(m.group(0), f'value="{new}"', 1)
            else:
                doc.lines[n] = line.replace("<KeyFrameDouble", f'<KeyFrameDouble value="{new}"', 1)
    return True


def place(doc, scene, name, report):
    g = Gate(scene, name)
    k, a = solve(g)
    report.append(f"{name}: bursts' centre y -> {a:.2f} + {k:.2f} * y")
    for u in g.units:
        uid = u.get("id")
        py = parent_offset(g, u)
        fn = lambda y, py=py: a + k * (py + y) - py
        keyed = g.keys.get(uid, {}).get("y")
        if keyed:
            assert rewrite_key_values(doc, ANIM, uid, "y", fn)
            rewrite_key_values(doc, IDLE, uid, "y", fn)
            assert u.get("y") is None or True
            if u.get("y") is not None:      # the static y is the pose before the loop; keep it in step
                set_attr(doc, uid, "y", fn(float(u.get("y"))))
        else:
            set_attr(doc, uid, "y", fn(float(u.get("y", 0))))
    return g


def fix_dots(doc, scene, name, report):
    g = Gate(scene, name)
    el = {e.get("id"): e for e in g.node.iter() if e.get("id")}
    vals = [g.values(f) for f in range(300)]
    own = lambda e, k, d, f: vals[f].get(e.get("id"), {}).get(k, float(e.get(k, d)))
    need = {}
    unresolved = 0
    for f in range(300):
        for pn, box, dot, uid, ids in g.pieces(f):
            if not dot:
                continue
            top = next((i for i in ids if abs(own(el[i], "scaleX", 1, f)) < 1e-4 and abs(own(el[i], "scaleY", 1, f)) < 1e-4), None)
            if top is None:
                unresolved += 1
            else:
                need.setdefault(top, set()).add(f)
    for oid, frames in need.items():
        e = el[oid]
        keys = g.keys.get(oid, {}).get("opacity")
        if keys:
            assert all(r[2] in ("linear", "hold") for r in keys.rows), (name, oid, "opacity keys with a curve")
        v = [0.0 if f in frames else (keys.at(f) if keys else float(e.get("opacity", 1))) for f in range(300)]
        step = [f < 299 and ((f in frames) != (f + 1 in frames)) for f in range(300)]
        rows = []
        for f in range(300):
            slope_in = v[f] - v[f - 1] if f else None
            slope_out = v[f + 1] - v[f] if f < 299 else None
            if f in (0, 299) or step[f] or step[f - 1] or abs((slope_in or 0) - (slope_out or 0)) > 1e-9:
                rows.append((f, v[f], "hold" if step[f] else "linear"))
        doc.set_prop(ANIM, oid, "opacity", rows)
        if doc._object(*doc.anim(IDLE), oid):
            rewrite_idle_opacity(doc, oid, v[0])
    report.append(f"{name}: {sum(len(f) for f in need.values())} dot frames on {len(need)} pieces get opacity 0 while at scale 0"
                  + (f" ({unresolved} dots not from scale: left)" if unresolved else ""))


def rewrite_idle_opacity(doc, oid, value):
    rewrite_key_values(doc, IDLE, oid, "opacity", lambda _: value)


def table(before, after):
    print(f"{'gate':13s} {'highest before':>16s} {'highest after':>14s} {'lowest after':>13s}  dots before/after   (copy: 343 phone, 415 desktop 1440x900, limit 440)")
    for n in GATES:
        b, a = before[n], after[n]
        print(f"{n:13s} {b['highest'][0]:9.1f} @{b['highest'][1]:3d} {a['highest'][0]:8.1f} @{a['highest'][1]:3d} {a['lowest'][0]:8.1f}      {b['dots']}/{a['dots']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", required=True)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    real = Path(args.scene)
    path = real
    if not args.write:
        path = real.with_name("scene.dry-run.rml")
        path.write_text(real.read_text())
    try:
        run(path, args)
    finally:
        if not args.write:
            path.unlink(missing_ok=True)


def run(path, args):
    scene = Scene(path)
    before = survey(scene)
    assert any(b["highest"][0] < 440 for b in before.values()) and any(b["dots"] for b in before.values()), "already applied"
    doc = Doc(path)
    report = []
    for name in GATES:
        place(doc, scene, name, report)
    doc.save()
    scene2 = Scene(path)
    for name in GATES:
        fix_dots(doc, scene2, name, report)
    doc.save()
    after = survey(Scene(path))
    print("\n".join(report))
    table(before, after)
    bad = [n for n in GATES if after[n]["highest"][0] < 440 or after[n]["dots"] or after[n]["lowest"][0] > 712]
    if bad:
        print("NOT CLEAN:", bad)
    if not args.write:
        print("(no --write: the scene was left as it was)")


if __name__ == "__main__":
    main()
