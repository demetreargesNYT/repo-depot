"""The opener (Shelf, scene intro): the illustrator's c2s1 animation as the room's loop, as they made it (their file 2668591, artboard
NYT_YIG_c2s1, state machine c2s1: layer Ball plays C2s1_Ball, 420 frames; layer Loop plays c2s1_Loop, 420 frames, looping).

Our Shelf room is the same drawing, rebuilt with clean names and laid out 14 px to the left (every piece measures -13.5 to -15 in x and
-0.4 to +3.2 in y against theirs), so their moves come in with one shift, (-14, 0), on every key frame and interpolation they wrote.
What had to be fitted, and nothing else:

* The ball: their Ball_Move (a Solo whose active child is Ball_01; Ball_02 never shows) moves our Shelf Ball, which moves to the top of
  the floor plane so it can travel the room. Its art is a copy of their Ball_01 (our old ball was a different drawing, radius 29.7).
  Their joystick (x picks a frame of Ball_Squash, y a frame of Ball_Scale) is baked into direct keys that give the same values on every
  frame. Their doorway mask (Door Way_Mask) comes in as a clip on the ball.
* Draw order: they draw the crown shelf, the open door panel and, from frame 247, the trophy's front (Trophy_F, which takes over from
  Trophy_B) above the ball. Here those pieces sit below it, so each gets a slot: a clip on the ball cut to that piece's own outline,
  placed where the piece is (it travels with it, wall lag included); the trophy's slot is on from frame 247.
* Their reflection sweeps across the plate (our blue yarn ball), clipped by the plate; ours was drawn flat at its rest pose, so it is
  replaced by theirs, clipped by our plate. Their pupils are clipped by their eyes; ours get the same clips.
* The cat tree's two moving parts turn about their own pivots, so ours are wrapped in pivots at those points.
* The loop joins the intro by holding, through the intro, every value the loop starts on.
"""
import math
import xml.etree.ElementTree as ET

from common import G, INTRO, RIVE_DIR, num, rebuild_built

SRC = RIVE_DIR / ".cache/scratch.nosync/ch2/illustrator-pull/scene.rml"     # a read-only pull of their file
ROOM = "Shelf"
DX, DY = -14.0, 0.0
L = 420
T0 = 115                                 # their frame 0 on this intro frame: the door starts to open on their frame 10 = intro frame 125
                                         # (2.08 s), when the crown shelf, the last piece the journey needs, has landed and settled;
                                         # 22 frames later than their own start, so the door and the roll-out have time (their frame 60
                                         # is where the ball comes to rest on the floor, then c2s1 carries on as drawn)
DOOR_OPEN = (10, 34)                     # the door swings open to its drawn pose (power2.out)
DOOR_CLOSE = (194, 218)                  # and swings shut again (the same swing, reversed) when the ball bounces on the cat shelf above it
ROLL = (20, 60)                          # the ball rolls from inside the doorway (hidden) to their rest spot, slowing evenly to a stop
WAIT_X = 540.0                           # where it waits, inside the doorway behind the closed door (room x; hidden by the doorway mask)
BACK = 300                               # out of sight in the trophy: the ball steps back to its start (behind the doorway) after this
TROPHY_ON, TROPHY_OFF = 247, 310         # their Trophy_F shows from 247; the slot goes off once the ball is behind the doorway
TROPHY_SLOT_DY = 4.5                     # the trophy front slot, moved down so only a stroke's width of black shows under the ball
SIZE_FULL_AT = 73                        # their frame where the ball reaches its floor size
SHRINK = (232, 252)                      # the ball scales down to fit the trophy's mouth (cycle frames), in the air above it
SHRINK_TO = 1.2                          # 42 px across, inside the rim's 46
PUPILS_BACK = 384                        # the quiet end: the pupils ease back to where the cycle starts, 384 to 420
FLOOR = "1:1093"
PLANE = (756.71997, 650.09998)           # the Shelf Floor Plane where the intro leaves it


# ---- reading their file ----------------------------------------------------------------------------------------------------------------
def source():
    r = ET.parse(SRC).getroot()
    a = [x for x in r.iter("Artboard") if x.get("name") == "NYT_YIG_c2s1"][0]
    anims = {x.get("name"): x for x in a.iter("LinearAnimation")}
    return a, {e.get("id"): e for e in a.iter() if e.get("id")}, anims


def props_of(anim, oid):
    ko = next((k for k in anim.findall("KeyedObject") if k.get("objectId") == oid), None)
    return {kp.get("property"): kp for kp in ko.findall("KeyedProperty")} if ko is not None else {}


def bez(x1, y1, x2, y2, u, v0=0.0, v1=1.0):
    lo, hi = 0.0, 1.0
    for _ in range(50):
        m = (lo + hi) / 2
        xm = 3 * (1 - m) ** 2 * m * x1 + 3 * (1 - m) * m * m * x2 + m ** 3
        lo, hi = (m, hi) if xm < u else (lo, m)
    t = (lo + hi) / 2
    return (1 - t) ** 3 * v0 + 3 * (1 - t) ** 2 * t * y1 + 3 * (1 - t) * t * t * y2 + t ** 3 * v1


def value_at(kp, f):
    """A numeric key list's value at frame f (hold, linear, cubic ease, cubic value; elastic only between its keys is approximated
    as linear, which is never asked for here: only frame 0 and the joystick's linear keys are evaluated)."""
    ks = sorted(kp, key=lambda k: float(k.get("frame", 0)))
    val = lambda k: float(k.get("value", 0))
    if f <= float(ks[0].get("frame", 0)):
        return val(ks[0])
    for k0, k1 in zip(ks, ks[1:]):
        f0, f1 = float(k0.get("frame", 0)), float(k1.get("frame", 0))
        if f0 <= f < f1:
            u = (f - f0) / (f1 - f0)
            it = k0.get("interpolationType", "hold")
            if it == "hold":
                return val(k0)
            c = k0.find("CubicEaseInterpolator")
            if it == "cubic" and c is not None:
                p = [float(c.get(q, d)) for q, d in (("x1", .42), ("y1", 0), ("x2", .58), ("y2", 1))]
                return val(k0) + (val(k1) - val(k0)) * bez(*p, u)
            c = k0.find("CubicValueInterpolator")
            if it == "cubicValue" and c is not None:
                p = [float(c.get(q, d)) for q, d in (("x1", 0), ("y1", 0), ("x2", 1), ("y2", 0))]
                return bez(p[0], p[1], p[2], p[3], u, val(k0), val(k1))
            return val(k0) + (val(k1) - val(k0)) * u
    return val(ks[-1])


# ---- writing ours ----------------------------------------------------------------------------------------------------------------------
def key_lines(doc, kp, f=lambda v: v, pad=" " * 20):
    """Their keys, one for one: frame, interpolation and interpolator kept (fresh ids), values (and a value curve's control values)
    passed through f."""
    out = []
    for k in sorted(kp, key=lambda k: float(k.get("frame", 0))):
        v = f(float(k.get("value", 0)))
        attrs = f' value="{num(v)}"' if num(v) != "0" else ""
        it = k.get("interpolationType")
        if it:
            attrs += f' interpolationType="{it}"'
        if k.get("frame"):
            attrs += f' frame="{k.get("frame")}"'
        kid = list(k)
        if not kid:
            out.append(f'{pad}<KeyFrameDouble{attrs} id="{doc.new_id()}"/>')
            continue
        out.append(f'{pad}<KeyFrameDouble{attrs} id="{doc.new_id()}">')
        for c in kid:
            a = dict(c.attrib)
            a.pop("id", None)
            if c.tag == "CubicValueInterpolator":
                a["y1"] = num(f(float(a.get("y1", 0))))
                a["y2"] = num(f(float(a.get("y2", 0))))
            s = " ".join(f'{q}="{w}"' for q, w in a.items())
            out.append(f'{pad}    <{c.tag} {s} id="{doc.new_id()}"/>'.replace("  id=", " id="))
        out.append(f"{pad}</KeyFrameDouble>")
    return out


def put(doc, anim_name, oid, prop, lines):
    """set_prop with key lines already written."""
    a, b = doc.anim(anim_name)
    found = doc._object(a, b, oid)
    if found is None:
        doc.lines[b:b] = [f'            <KeyedObject objectId="{oid}" id="{doc.new_id()}">', "            </KeyedObject>"]
        found = (b, b + 1)
    i, j = found
    import re
    pat = re.compile(r'^\s*<KeyedProperty\b[^>]*\bproperty="%s"' % re.escape(prop))
    at = next((k for k in range(i + 1, j) if pat.match(doc.lines[k])), None)
    block = [f'                <KeyedProperty property="{prop}" id="{doc.new_id()}">'] + lines + ["                </KeyedProperty>"]
    if at is None:
        doc.lines[j:j] = block
    else:
        doc.lines[at:doc.end(at) + 1] = block


# ---- tracks: every loop property in cycle time, then written to the intro and the loop with the cycle's phase ---------------------
def de_casteljau(p0, p1, p2, p3, t):
    lerp = lambda a, b: (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    a, b, c = lerp(p0, p1), lerp(p1, p2), lerp(p2, p3)
    d, e = lerp(a, b), lerp(b, c)
    m = lerp(d, e)
    return (p0, a, d, m), (m, e, c, p3)


def param_for_x(p1x, p2x, u):
    lo, hi = 0.0, 1.0
    for _ in range(60):
        m = (lo + hi) / 2
        xm = 3 * (1 - m) ** 2 * m * p1x + 3 * (1 - m) * m * m * p2x + m ** 3
        lo, hi = (m, hi) if xm < u else (lo, m)
    return (lo + hi) / 2


def elastic_out(u, amplitude=1.0, period=1.0):
    """Rive's elastic ease (out, its default)."""
    if u <= 0 or u >= 1:
        return u
    s = period / 4 if amplitude < 1 else period / (2 * math.pi) * math.asin(1 / amplitude)
    return amplitude * 2 ** (-10 * u) * math.sin((u - s) * 2 * math.pi / period) + 1


def spec_value(ks, t):
    if t <= ks[0]["fr"]:
        return ks[0]["v"]
    for k0, k1 in zip(ks, ks[1:]):
        if k0["fr"] <= t < k1["fr"]:
            u = (t - k0["fr"]) / (k1["fr"] - k0["fr"])
            it, c = k0["it"], k0["c"]
            if it == "hold":
                return k0["v"]
            if it == "cubic":
                return k0["v"] + (k1["v"] - k0["v"]) * bez(*c, u)
            if it == "cubicValue":
                return bez(c[0], c[1], c[2], c[3], u, k0["v"], k1["v"])
            if it == "elastic":
                return k0["v"] + (k1["v"] - k0["v"]) * elastic_out(u, float(c.get("amplitude", 1)), float(c.get("period", 1)))
            return k0["v"] + (k1["v"] - k0["v"]) * u
    return ks[-1]["v"]


def specs_of(kp, f=lambda v: v):
    out = []
    for k in sorted(kp, key=lambda k: float(k.get("frame", 0))):
        it = k.get("interpolationType", "hold")
        c = None
        ce, cv, el = k.find("CubicEaseInterpolator"), k.find("CubicValueInterpolator"), k.find("ElasticInterpolator")
        if it == "cubic" and ce is not None:
            c = tuple(float(ce.get(q, d)) for q, d in (("x1", .42), ("y1", 0), ("x2", .58), ("y2", 1)))
        elif it == "cubicValue" and cv is not None:
            x1, y1, x2, y2 = (float(cv.get(q, d)) for q, d in (("x1", 0), ("y1", 0), ("x2", 1), ("y2", 0)))
            c = (x1, f(y1), x2, f(y2))
        elif it == "elastic" and el is not None:
            c = {q: w for q, w in el.attrib.items() if q != "id"}
        elif it == "cubic":
            c = (.42, 0, .58, 1)
        out.append({"fr": int(float(k.get("frame", 0))), "v": f(float(k.get("value", 0))), "it": it, "c": c})
    return out


def split(ks, t):
    """The same curve with a key at frame t (cubic ease and value curves split exactly; an elastic segment is written frame by frame)."""
    if any(k["fr"] == t for k in ks):
        return ks
    if t < ks[0]["fr"]:
        return [{"fr": t, "v": ks[0]["v"], "it": "hold", "c": None}] + ks
    if t > ks[-1]["fr"]:
        return ks + [{"fr": t, "v": ks[-1]["v"], "it": "hold", "c": None}]
    i = next(i for i in range(len(ks) - 1) if ks[i]["fr"] < t < ks[i + 1]["fr"])
    k0, k1 = ks[i], ks[i + 1]
    u = (t - k0["fr"]) / (k1["fr"] - k0["fr"])
    it, c = k0["it"], k0["c"]
    if it in ("hold", "linear"):
        mid = {"fr": t, "v": spec_value(ks, t), "it": it, "c": None}
        return ks[:i + 1] + [mid] + ks[i + 1:]
    if it in ("cubic", "cubicValue"):
        v0, v1 = (0.0, 1.0) if it == "cubic" else (k0["v"], k1["v"])
        P = ((0.0, v0), (c[0], c[1]), (c[2], c[3]), (1.0, v1))
        s = param_for_x(c[0], c[2], u)
        (a0, a1, a2, m), (_, b1, b2, b3) = de_casteljau(*P, s)
        mx = m[0]
        if it == "cubic":
            if abs(m[1]) < 1e-9 or abs(1 - m[1]) < 1e-9:
                return bake_segment(ks, i, t)
            left = (a1[0] / mx, a1[1] / m[1], a2[0] / mx, a2[1] / m[1])
            right = ((b1[0] - mx) / (1 - mx), (b1[1] - m[1]) / (1 - m[1]), (b2[0] - mx) / (1 - mx), (b2[1] - m[1]) / (1 - m[1]))
            vm = k0["v"] + (k1["v"] - k0["v"]) * m[1]
        else:
            left = (a1[0] / mx, a1[1], a2[0] / mx, a2[1])
            right = ((b1[0] - mx) / (1 - mx), b1[1], (b2[0] - mx) / (1 - mx), b2[1])
            vm = m[1]
        return ks[:i] + [dict(k0, c=left), {"fr": t, "v": vm, "it": it, "c": right}] + ks[i + 1:]
    return bake_segment(ks, i, t)


def bake_segment(ks, i, t):
    k0, k1 = ks[i], ks[i + 1]
    seg = [{"fr": f, "v": spec_value(ks, f), "it": "linear", "c": None} for f in range(k0["fr"], k1["fr"])]
    return ks[:i] + seg + ks[i + 1:]


def window(ks, a, b, shift):
    ks = split(split(ks, a), b)
    return [dict(k, fr=k["fr"] + shift) for k in ks if a <= k["fr"] <= b]


class Tracks:
    def __init__(self):
        self.items = []          # [oid, prop, "keys" or "frames", data]

    def keys(self, oid, prop, kp, f=lambda v: v):
        self.items.append([oid, prop, "keys", specs_of(kp, f)])

    def frames(self, oid, prop, vals):
        self.items.append([oid, prop, "frames", dict(vals)])

    def find(self, oid, prop):
        return next(t for t in self.items if t[0] == oid and t[1] == prop)

    def hidden_return(self, oid, prop, at):
        """Back to the cycle's first value at frame `at` + 1, while the ball is out of sight (a step, no in-between)."""
        t = self.find(oid, prop)
        if t[2] == "frames":
            v0 = t[3][0]
            for f in range(at + 1, L + 1):
                t[3][f] = v0
            return
        ks = split(t[3], 0)
        v0, va = spec_value(ks, 0), spec_value(ks, at)
        ks = [k for k in ks if k["fr"] < at] + [{"fr": at, "v": va, "it": "hold", "c": None},
                                                {"fr": at + 1, "v": v0, "it": "hold", "c": None},
                                                {"fr": L, "v": v0, "it": "hold", "c": None}]
        t[3] = ks

    def ease_back(self, oid, prop, start):
        """Back to the cycle's first value over the quiet end, start to L, sine-like (power1.inOut)."""
        t = self.find(oid, prop)
        ks = split(split(t[3], 0), start)
        v0 = spec_value(ks, 0)
        ks = [k for k in ks if k["fr"] < start] + [{"fr": start, "v": spec_value(ks, start), "it": "cubic", "c": (0.45, 0, 0.55, 1)},
                                                   {"fr": L, "v": v0, "it": "hold", "c": None}]
        t[3] = ks

    def write(self, doc, intro, loop, T0):
        C = INTRO - 1 - T0                       # the cycle frame on the intro's last frame, where the loop picks up
        from common import bake
        for oid, prop, kind, data in self.items:
            if kind == "frames":
                iv = {f: data[0] if f < T0 else data[f - T0] for f in range(INTRO)}
                lv = {k: data[(C + k) % L] for k in range(L + 1)}
                doc.set_prop(intro, oid, prop, bake(iv, range(INTRO)))
                doc.set_prop(loop, oid, prop, bake(lv, range(L + 1)))
                continue
            ks = split(split(data, 0), L)
            ks = [k for k in ks if 0 <= k["fr"] <= L]
            assert abs(spec_value(ks, 0) - spec_value(ks, L)) < 1e-3, (oid, prop, spec_value(ks, 0), spec_value(ks, L))
            ik = window(ks, 0, C, T0)
            if T0 > 0:
                ik = [{"fr": 0, "v": ik[0]["v"], "it": "hold", "c": None}] + ik
            lk = window(ks, C, L, -C)[:-1] + window(ks, 0, C, L - C)
            put(doc, intro, oid, prop, spec_lines(doc, ik))
            put(doc, loop, oid, prop, spec_lines(doc, lk))


def spec_lines(doc, ks, pad=" " * 20):
    out = []
    for k in ks:
        attrs = f' value="{num(k["v"])}"' if num(k["v"]) != "0" else ""
        if k["it"] != "hold":
            attrs += f' interpolationType="{k["it"]}"'
        if k["fr"]:
            attrs += f' frame="{k["fr"]}"'
        c = k["c"]
        if k["it"] == "cubic":
            inner = f'<CubicEaseInterpolator x1="{num(c[0])}" y1="{num(c[1])}" x2="{num(c[2])}" y2="{num(c[3])}" id="{doc.new_id()}"/>'
        elif k["it"] == "cubicValue":
            inner = f'<CubicValueInterpolator x1="{num(c[0])}" y1="{num(c[1])}" x2="{num(c[2])}" y2="{num(c[3])}" id="{doc.new_id()}"/>'
        elif k["it"] == "elastic":
            inner = "<ElasticInterpolator " + " ".join(f'{q}="{w}"' for q, w in c.items()) + f' id="{doc.new_id()}"/>'
        else:
            out.append(f'{pad}<KeyFrameDouble{attrs} id="{doc.new_id()}"/>')
            continue
        out += [f'{pad}<KeyFrameDouble{attrs} id="{doc.new_id()}">', f"{pad}    {inner}", f"{pad}</KeyFrameDouble>"]
    return out


def xml_lines(doc, e, depth, idmap, skip=lambda e: False):
    """Their element as our lines, every id fresh (recorded in idmap)."""
    pad = " " * (4 * depth)
    nid = doc.new_id()
    idmap[e.get("id")] = nid
    a = " ".join(f'{q}="{w}"' for q, w in e.attrib.items() if q not in ("id", "locked"))
    head = f"{pad}<{e.tag}{' ' + a if a else ''} id=\"{nid}\""
    kids = [c for c in e if not skip(c)]
    if not kids:
        return [head + "/>"]
    out = [head + ">"]
    for c in kids:
        out += xml_lines(doc, c, depth + 1, idmap, skip)
    return out + [f"{pad}</{e.tag}>"]


def indent_of(doc, i):
    return (len(doc.lines[i]) - len(doc.lines[i].lstrip())) // 4


def insert_child(doc, parent_id, lines_fn, first=True):
    """Insert an element as the parent's first child (drawn on top) or last."""
    i = doc.idx(parent_id)
    d = indent_of(doc, i) + 1
    lines = lines_fn(d)
    at = i + 1 if first else doc.end(i)
    doc.lines[at:at] = lines


def hole_shape(doc, d, name, path_lines, x=0.0, y=0.0, rotation=None, sx=None, sy=None):
    """A clip source: a huge rectangle with one outline cut out of it (evenOdd: the ball is hidden only inside the outline)."""
    pad = " " * (4 * d)
    hid = doc.new_id()
    extra = (f' rotation="{num(rotation)}"' if rotation else "") + (f' scaleX="{num(sx)}"' if sx and sx != 1 else "") + (f' scaleY="{num(sy)}"' if sy and sy != 1 else "")
    out = [f'{pad}<Shape x="{num(x)}" y="{num(y)}"{extra} name="{name}" id="{hid}">',
           f'{pad}    <Rectangle width="30000" height="30000" originX="0.5" originY="0.5" name="Path" id="{doc.new_id()}"/>']
    out += path_lines
    return hid, out + [f"{pad}</Shape>"]


def copy_paths(doc, scene_byid, shape_id, d, idmap=None):
    """Our shape's own path elements (PointsPath with vertices, Ellipse, Rectangle), fresh ids, at depth d."""
    out = []
    for c in scene_byid[shape_id]:
        if c.tag in ("PointsPath", "Ellipse", "Rectangle"):
            out += xml_lines(doc, c, d, idmap if idmap is not None else {})
    return out


def world(scene, oid):
    par = scene.parent
    e = scene.by_id[oid] if hasattr(scene, "by_id") else next(n for n in scene.root.iter() if n.get("id") == oid)
    chain = []
    while e is not None and e.get("name") != "Shelf Room":
        if e.tag in ("Node", "Shape"):
            chain.append(e)
        e = par.get(e)
    m = (1, 0, 0, 1, 0, 0)
    for n in reversed(chain):
        x, y = float(n.get("x", 0)), float(n.get("y", 0))
        r = float(n.get("rotation", 0))
        sx, sy = float(n.get("scaleX", 1)), float(n.get("scaleY", 1))
        c, s = math.cos(r), math.sin(r)
        a, b, cc, dd, tx, ty = m
        n2 = (c * sx, s * sx, -s * sy, c * sy, x, y)
        a2, b2, c2, d2, tx2, ty2 = n2
        m = (a * a2 + cc * b2, b * a2 + dd * b2, a * c2 + cc * d2, b * c2 + dd * d2, a * tx2 + cc * ty2 + tx, b * tx2 + dd * ty2 + ty)
    return m


def build(doc, scene, sheet):
    A, S, anims = source()
    ball_anim, loop_anim = anims["C2s1_Ball"], anims["c2s1_Loop"]
    squash_anim, scale_anim = anims["Ball_Squash"], anims["Ball_Scale"]
    byid = {e.get("id"): e for e in scene.root.iter() if e.get("id")}
    if not hasattr(scene, "parent"):
        scene.parent = {c: p for p in scene.root.iter() for c in p}
    intro, loop = f"{ROOM} Intro", f"{ROOM} Loop"
    keyed = []
    T = Tracks()
    notes = []

    # ---- the old ball loop goes (the c2s1 ball replaces it) -------------------------------------------------------------------------
    for a in (intro, loop):
        doc.drop_object(a, "1:1245")
    doc.drop_object(loop, "1:1246")

    # ---- the ball: our Shelf Ball moves to the top of the floor plane, with a copy of their Ball_01 as its art -------------------------
    i = doc.idx("1:1245")
    j = doc.end(i)
    block = doc.lines[i:j + 1]
    del doc.lines[i:j + 1]
    d_old = indent_of_line(block[0])
    fi = doc.idx(FLOOR)
    d_new = indent_of(doc, fi) + 1
    block = [" " * (4 * (d_new - d_old)) + l if d_new >= d_old else l[4 * (d_old - d_new):] for l in block]
    doc.lines[fi + 1:fi + 1] = block
    # the doorway mask (their Door Way_Mask: x 588.25 to 1229.2, y 220.3 to 712.0 on their artboard), in the floor plane
    x0, x1, y0, y1 = 588.25 + DX, 1229.2 + DX, 220.3 + DY, 712.0 + DY
    mask = doc.new_id()
    cx, cy = (x0 + x1) / 2 - PLANE[0], (y0 + y1) / 2 - PLANE[1]
    fi = doc.idx(FLOOR)
    d = indent_of(doc, fi) + 1
    doc.lines[fi + 1:fi + 1] = [f'{" " * 4 * d}<Shape x="{num(cx)}" y="{num(cy)}" name="Shelf Doorway Mask" id="{mask}">',
                                f'{" " * 4 * (d + 1)}<Rectangle width="{num(x1 - x0)}" height="{num(y1 - y0)}" originX="0.5" originY="0.5" name="Path" id="{doc.new_id()}"/>',
                                f'{" " * 4 * d}</Shape>']
    # the art: our standard ball (Wordle's: a body of radius 17.68 and the white dot at (6.37, -6.26) from the centre), not theirs; the
    # spin pivot sits at the centre, 17.68 above the Shelf Ball node, which is the contact point and carries the size and the squash
    ai = doc.idx("1:1247")
    aj = doc.end(ai)
    da = indent_of(doc, ai) + 1
    lines = []
    for c in byid["1:1075"]:
        cl = xml_lines(doc, c, da, {})
        if c.get("id") == "1:1084":                               # the body: named as in the other rooms, so the ball check follows it
            cl[0] = cl[0].replace("<Shape ", '<Shape name="Ball_01_Base" ', 1)
        cl = [l.replace("<Stroke ", '<Stroke transformAffectsStroke="false" ', 1) if "<Stroke " in l and "transformAffectsStroke" not in l else l for l in cl]
        lines += cl
    lines.append(f'{" " * 4 * da}<ClippingShape sourceId="{mask}" name="Doorway Mask" id="{doc.new_id()}"/>')
    doc.lines[ai + 1:aj] = lines
    si = doc.idx("1:1246")
    import re
    doc.lines[si] = re.sub(r' y="[^"]*"', ' y="-17.68"', re.sub(r' x="[^"]*"', "", doc.lines[si]))
    clip_at = lambda: doc.end(doc.idx("1:1247"))                  # where the ball's clips go (inside its art)

    # ---- the ball's position: their Ball_Move keys, shifted into our floor plane ----------------------------------------------------
    bm = props_of(ball_anim, "1:13638")
    fx = lambda v: v + DX - PLANE[0]
    fy = lambda v: v + DY - PLANE[1]
    roll = (1 / 3, 2 / 3, 2 / 3, 1)                              # x steady in time, the position easing out: an even slow-down to a stop
    xs = [{"fr": 0, "v": WAIT_X - PLANE[0], "it": "hold", "c": None}, {"fr": ROLL[0], "v": WAIT_X - PLANE[0], "it": "cubic", "c": roll}]
    xs += [k for k in specs_of(bm["x"], fx) if k["fr"] >= ROLL[1]]
    ys = [{"fr": 0, "v": fy(712.0), "it": "hold", "c": None}] + [k for k in specs_of(bm["y"], fy) if k["fr"] >= ROLL[1]]
    T.items += [["1:1245", "x", "keys", xs], ["1:1245", "y", "keys", ys]]
    keyed += [("1:1245", "x", fx(value_at(bm["x"], 0))), ("1:1245", "y", fy(value_at(bm["y"], 0)))]

    # ---- size and squash: their joystick, baked. y picks a frame of Ball_Scale (Ball_01's scale, 0.7 to 2), x a frame of Ball_Squash
    # (the outline flattens to 0.854 of its height and widens to 1.131, its bottom fixed). Here both are a scale of the Shelf Ball node
    # about the contact point: size times squash, every frame. Their highlight's keys don't come over (our dot is the highlight).
    from common import bake
    js = props_of(ball_anim, "1:15194")
    jx0 = lambda f: value_at(js["x"], f) if "x" in js else -1.0
    jx = lambda f: -1.0 if f <= ROLL[1] else (-1.0 + 2.0 * (f - ROLL[1]) / 3 if f < 63 else jx0(f))
    jy = lambda f: value_at(js["y"], f) if "y" in js else 0.0
    sc_kp = props_of(scale_anim, "1:13658")["scaleX"]
    sq = {k: props_of(squash_anim, k) for k in ("1:13668", "1:13669", "1:13671")}
    size = {f: value_at(sc_kp, (jy(f) + 1) / 2 * 60) for f in range(L + 1)}
    # Demetre's note, 2026-11-04 23:15: the ball keeps one size for the whole scene, the size it has once it is fully out on the floor
    # (their 1.805, reached on frame 73), from the first frame: rolling out of the door, on every hop, on every shelf. Only at the end,
    # as it goes into the trophy, does it scale down (slightly) to fit the cup's mouth, SHRINK_TO by SHRINK[1]; the squash pulses stay.
    # (Their joystick's size changes, 1.435 on the roll-out, 1.805 to 0.886 over the hops, are not kept.)
    full = size[SIZE_FULL_AT]
    for f in range(L + 1):
        if f <= SHRINK[0]:
            size[f] = full
        elif f < SHRINK[1]:
            u = (f - SHRINK[0]) / (SHRINK[1] - SHRINK[0])
            size[f] = full + (SHRINK_TO - full) * (u * u * (3 - 2 * u))
        else:
            size[f] = SHRINK_TO
    notes.append(f"ball size {full:.3f} for the whole scene, scaling to {SHRINK_TO} into the trophy over {SHRINK[0]}-{SHRINK[1]} (was 1.435 on the roll-out, 1.805 to 0.886 on the hops)")
    def squash(f):
        t = (jx(f) + 1) / 2 * 60
        top = value_at(sq["1:13668"]["y"], t)
        w = value_at(sq["1:13669"]["x"], t) - value_at(sq["1:13671"]["x"], t)
        return w / (2 * 17.677999), (17.677999 - top) / (2 * 17.677999)
    sxs = {f: size[f] * squash(f)[0] for f in range(L + 1)}
    sys_ = {f: size[f] * squash(f)[1] for f in range(L + 1)}
    for prop, vals in (("scaleX", sxs), ("scaleY", sys_)):
        T.frames("1:1245", prop, vals)
        keyed.append(("1:1245", prop, vals[0]))

    # ---- the turn: one turn per circumference at the size it has on each frame ----------------------------------------------------
    # Their ball is in the air nearly all the time (hops between the floor, the cat tree, the shelves): at each contact it grips (the
    # turn rate becomes its sideways speed over its radius), in the air it keeps that rate, at rest and while hidden it does not turn.
    # Contacts are their Ball_Move key frames. Hidden: before it shows over the door (frame 38) and once it is in the trophy (247).
    cxs = {f: spec_value(xs, f) for f in range(L + 1)}
    contacts = sorted({int(float(k.get("frame", 0))) for k in bm["x"]} | {int(float(k.get("frame", 0))) for k in bm["y"]})
    contacts = [c for c in contacts if c >= 63]
    th = [0.0]
    w = 0.0
    for f in range(L):
        r = 17.678 * size[f]
        dx = cxs[f + 1] - cxs[f]
        if ROLL[0] <= f < ROLL[1]:
            w = dx / r                                            # rolling out of the doorway: the turn is the travel over the radius
        elif f < 63 or f >= 247 or (abs(dx) < 1e-9 and f >= contacts[-1]):
            w = 0.0                                               # waiting, at rest on the floor, or in the trophy
        elif f in contacts:
            w = dx / r                                            # grips at each contact, then keeps that rate in the air
        th.append(th[-1] + w)
    total = th[-1]
    want = round(total / (2 * math.pi)) * 2 * math.pi
    h0, h1 = 262, L                                               # in the trophy, out of sight: take up the rest to a whole number of turns
    for f in range(h0, L + 1):
        th[f] += (want - total) * (0.5 - 0.5 * math.cos(math.pi * (f - h0) / (h1 - h0)))
    T.frames("1:1246", "rotation", {f: th[f] for f in range(L + 1)})
    keyed.append(("1:1246", "rotation", 0.0))
    notes.append(f"spin {total / (2 * math.pi):.2f} turns in sight, closed to {round(total / (2 * math.pi))} in the trophy")

    # ---- draw order: slots for what they draw above the ball -----------------------------------------------------------------------
    slot_clips = []
    slot_vmap = {}
    # the open door panel (their Door_open) and the crown shelf (their Shelf_Bottom): always above the ball
    for name, shapes in (("Door Panel", ["1:1228"]),
                         ("Crown Shelf", [s.get("id") for s in byid["9:10706"].iter("Shape") if s.get("name") != "crown-sparkle"])):
        for sid in shapes:
            e = byid[sid]
            par = scene.parent[e]
            pi = doc.idx(par.get("id"))
            d = indent_of(doc, pi) + 1
            hid, lines = hole_shape(doc, d, f"Shelf {name} Slot", copy_paths(doc, byid, sid, d + 1, slot_vmap), float(e.get("x", 0)), float(e.get("y", 0)),
                                    float(e.get("rotation", 0)), float(e.get("scaleX", 1)), float(e.get("scaleY", 1)))
            doc.lines[pi + 1:pi + 1] = lines
            slot_clips.append(hid)
    # the sparkles (their Burst_01, Burst_02) are drawn above the ball too: their slot's outline scales with them (only the outline:
    # scaling the slot's rectangle to 0 would hide the whole ball)
    sparkle_slots = []
    for sid, burst, name in (("1:1779", "1:14501", "Crown Sparkle"), ("1:1895", "1:15491", "Trophy Sparkle")):
        e = byid[sid]
        par = scene.parent[e]
        pi = doc.idx(par.get("id"))
        d = indent_of(doc, pi) + 1
        pmap = {}
        paths = []
        for c in byid[sid]:
            if c.tag in ("PointsPath", "Ellipse", "Rectangle"):
                pl = xml_lines(doc, c, d + 1, pmap)
                pl[0] = pl[0].replace(f' id="{pmap[c.get("id")]}"', f' scaleX="0" scaleY="0" id="{pmap[c.get("id")]}"')
                paths += pl
        hid, lines = hole_shape(doc, d, f"Shelf {name} Slot", paths, float(e.get("x", 0)), float(e.get("y", 0)), float(e.get("rotation", 0)))
        doc.lines[pi + 1:pi + 1] = lines
        slot_clips.append(hid)
        sparkle_slots.extend((pmap[c.get("id")], burst) for c in byid[sid] if c.get("id") in pmap)

    # the trophy's front (their Trophy_F, shown from frame 247): the cup, handles and base, not the rim (the ball shows over the hole)
    tnode = doc.new_id()
    ti = doc.idx("1:1914")
    d = indent_of(doc, ti) + 1
    tl = [f'{" " * 4 * d}<Node y="-3000" name="Shelf Trophy Front Slot" id="{tnode}">']
    for sid in ("1:1944", "1:1960", "1:1970", "1:1980"):
        e = byid[sid]
        hid, lines = hole_shape(doc, d + 1, "Shelf Trophy Front Slot", copy_paths(doc, byid, sid, d + 2), float(e.get("x", 0)), float(e.get("y", 0)))
        tl += lines
        slot_clips.append(hid)
    doc.lines[ti + 1:ti + 1] = tl + [f'{" " * 4 * d}</Node>']
    ci = clip_at()
    dc = indent_of(doc, doc.idx("1:1247")) + 1
    doc.lines[ci:ci] = [f'{" " * 4 * dc}<ClippingShape sourceId="{h}" fillRule="evenOdd" name="Draw Order Slot" id="{doc.new_id()}"/>' for h in slot_clips]
    # Trophy_F's opacity (0 to 1 between frames 246 and 247) as the trophy slot's switch; Trophy_B's fade is not needed, ours stays under
    T.frames(tnode, "y", {f: (TROPHY_SLOT_DY if TROPHY_ON <= f < TROPHY_OFF else -3000.0) for f in range(L + 1)})   # off: 3000 px up

    # ---- the bursts: their scale keys on our sparkles, and on the sparkles' slots -------------------------------------------------
    for sid, burst in (("1:1779", "1:14501"), ("1:1895", "1:15491")):
        bp_ = props_of(ball_anim, burst)
        for prop in ("scaleX", "scaleY"):
            T.keys(sid, prop, bp_[prop])
            keyed.append((sid, prop, value_at(bp_[prop], 0)))
    for pid, burst in sparkle_slots:
        bp_ = props_of(ball_anim, burst)
        for prop in ("scaleX", "scaleY"):
            T.keys(pid, prop, bp_[prop])
            keyed.append((pid, prop, value_at(bp_[prop], 0)))

    pieces_react(doc, scene, byid, T, slot_vmap, bm, size, notes)

    # ---- the cat tree: their two moving shapes turn about their own pivots ------------------------------------------------------
    ts = world(scene, "1:1244")              # Toy Stand
    def stand_local(p):
        a, b, c, dd, tx, ty = ts
        det = a * dd - b * c
        x, y = p[0] - tx, p[1] - ty
        return ((dd * x - c * y) / det, (-b * x + a * y) / det)
    for src, ours, piv in (("1:13454", ("1:1305", "1:1355"), (826.8, 606.9)), ("1:13508", ("1:1345",), (822.8, 661.9))):
        rot = props_of(ball_anim, src)["rotation"]
        lp = stand_local((piv[0] + DX, piv[1] + DY))
        for oid in ours:
            pid, _ = doc.wrap(oid, f"Shelf {byid[oid].get('name')} Pivot", *lp)
            T.keys(pid, "rotation", rot)
            keyed.append((pid, "rotation", value_at(rot, 0)))

    # ---- the reflection on the plate: theirs, clipped by our plate --------------------------------------------------------------
    cs = world(scene, "1:1502")              # our Cat Shelf group (their Shelf_Mid sits at 569.5, 463.5)
    ox, oy = 569.5 + DX - cs[4], 463.5 + DY - cs[5]
    refl = S["1:20599"]
    ri = doc.idx("1:1532")
    d = indent_of(doc, ri)
    rmap = {}
    lines = xml_lines(doc, refl, d, rmap, skip=lambda c: c.tag == "ClippingShape")
    import re
    lines[0] = re.sub(r' x="[^"]*"', f' x="{num(float(refl.get("x")) + ox)}"', lines[0])
    lines[0] = re.sub(r' y="[^"]*"', f' y="{num(float(refl.get("y")) + oy)}"', lines[0])
    lines.insert(-1, f'{" " * 4 * (d + 1)}<ClippingShape sourceId="1:1571" name="Plate Clip" id="{doc.new_id()}"/>')
    doc.lines[ri:ri] = lines
    k = doc.idx("1:1556")
    doc.lines[k] = doc.lines[k].replace(' id="1:1556"', ' opacity="0" id="1:1556"') if "opacity=" not in doc.lines[k] else doc.lines[k]
    rf = props_of(ball_anim, "1:20599")
    T.keys(rmap["1:20599"], "x", rf["x"], lambda v: v + ox)
    T.keys(rmap["1:20599"], "y", rf["y"], lambda v: v + oy)
    keyed += [(rmap["1:20599"], "x", value_at(rf["x"], 0) + ox), (rmap["1:20599"], "y", value_at(rf["y"], 0) + oy)]

    # ---- the cat: pupils (C2s1_Ball), blinks and the tail (c2s1_Loop) ------------------------------------------------------------
    # their Eye_L is our right eye, their Eye_L 2 our left; their eye paths have a fifth vertex repeating the first, so their first
    # vertex's in-handle is a dead one (always 0): ours stays as drawn. C2s1_Ball's own eye keys (frames 0 to 16) never show in their
    # file (the Loop layer keys the same vertices after it), so only c2s1_Loop's are used.
    def offs(src_e, our_e, prop):
        return float(our_e.get(prop, 0)) - float(src_e.get(prop, 0))
    for src, ours, eye_white in (("1:14384", "1:1710", "1:1718"), ("1:97372", "1:1693", "1:1701")):
        pp = props_of(ball_anim, src)
        for prop in ("x", "y"):
            o = offs(S[src], byid[ours], prop)
            T.keys(ours, prop, pp[prop], lambda v, o=o: v + o)
            keyed.append((ours, prop, value_at(pp[prop], 0) + o))
        j = doc.end(doc.idx(ours))
        dd = indent_of(doc, doc.idx(ours)) + 1
        doc.lines[j:j] = [f'{" " * 4 * dd}<ClippingShape sourceId="{eye_white}" name="Eye Clip" id="{doc.new_id()}"/>']
    vmap = {"1:14390": "1:1720", "1:14391": "1:1721", "1:14392": "1:1722", "1:97381": "1:1703", "1:97382": "1:1704", "1:97383": "1:1705"}
    first = {"1:14390", "1:97381"}
    for ko in loop_anim.findall("KeyedObject"):
        sid = ko.get("objectId")
        if sid in vmap:
            for kp in ko.findall("KeyedProperty"):
                prop = kp.get("property")
                if sid in first and prop in ("inRotation", "inDistance"):
                    continue
                o = offs(S[sid], byid[vmap[sid]], prop)
                T.keys(vmap[sid], prop, kp, lambda v, o=o: v + o)
                keyed.append((vmap[sid], prop, value_at(kp, 0) + o))
    e2 = props_of(loop_anim, "1:97371")["x"]
    o = offs(S["1:97371"], byid["1:1692"], "x")
    T.keys("1:1692", "x", e2, lambda v: v + o)
    keyed.append(("1:1692", "x", value_at(e2, 0) + o))
    # the tail: our tail is two shapes (fill and outline), each with an extra end point at the tip, which follows the tip
    tmap = {"1:14436": ("1:1765", "1:1774"), "1:14437": ("1:1766", "1:1775")}
    for sid, ours in tmap.items():
        for kp in props_of(loop_anim, sid).values():
            prop = kp.get("property")
            for oid in ours:
                o = offs(S[sid], byid[oid], prop)
                T.keys(oid, prop, kp, lambda v, o=o: v + o)
                keyed.append((oid, prop, value_at(kp, 0) + o))
    tip = props_of(loop_anim, "1:14437")
    for end_v, tip_v in (("1:1767", "1:1766"), ("1:1776", "1:1775")):
        for prop in ("x", "y"):
            o = float(byid[end_v].get(prop, 0)) - float(S["1:14437"].get(prop, 0))
            T.keys(end_v, prop, tip[prop], lambda v, o=o: v + o)
            keyed.append((end_v, prop, value_at(tip[prop], 0) + o))
    th = props_of(loop_anim, "1:97841")["thickness"]
    T.keys("1:2544", "thickness", th)
    keyed.append(("1:2544", "thickness", value_at(th, 0)))
    notes.append("tail stroke colour key (one key, FF1F1F1F, equal to the art) left out: it changes nothing")

    # ---- the loop and the join: the loop is their 420 frames; the intro holds what the loop starts on --------------------------------
    # ---- the seam (their frame 420 back to 0): out of sight, the ball, its size and squash go back to where the cycle starts (the
    # step happens in the trophy, the trophy's slot switches off once the ball is behind the doorway); in sight, the pupils ease back
    # the position steps (hold keys) on BACK + 1, while the trophy slot still hides the ball; the size steps a frame later, once the
    # ball is behind the doorway mask, because a size baked frame by frame eases over the frame in between, and that in-between must
    # never be seen in the trophy (a display faster than 60 fps samples it)
    for oid, prop in (("1:1245", "x"), ("1:1245", "y"), (rmap["1:20599"], "x"), (rmap["1:20599"], "y")):
        T.hidden_return(oid, prop, BACK)
    for prop in ("scaleX", "scaleY"):
        T.hidden_return("1:1245", prop, BACK + 1)
    for oid in ("1:1710", "1:1693"):
        for prop in ("x", "y"):
            T.ease_back(oid, prop, PUPILS_BACK)
    doc.set_duration(loop, L)
    T.write(doc, intro, loop, T0)
    doc.rebuild_waiting(ROOM)
    rebuild_built(doc, ROOM)
    return (f"{ROOM}: c2s1 in as the loop ({L} frames); {len(keyed)} properties keyed; " + "; ".join(notes))


def indent_of_line(l):
    return (len(l) - len(l.lstrip())) // 4


# ---- Demetre's notes on the opener (2026-11-04) ------------------------------------------------------------------------------------
THETA0 = math.acos(70.0 / 92.5)          # the drawn door is open by this much: its free edge at 70 of the doorway's 92.5 px
SHEAR0 = 24.95 / 92.5                    # and its free edge has dropped 24.95 px (the near side of an open door)


def door_theta(f):
    a, b = DOOR_OPEN
    c, d = DOOR_CLOSE
    if f < a or f >= d:
        return 0.0
    if f < b:
        u = (f - a) / (b - a)
        return THETA0 * (1 - (1 - u) ** 2)
    if f < c:
        return THETA0
    u = (f - c) / (d - c)
    return THETA0 * (1 - u * u)                                   # the opening swing played backwards


def door_map(X, Y, th):
    """A point of the drawn (open) panel, in Door Panel space, on the panel swung to th: the hinge (x -35) stays; the free edge comes in
    by cos and drops by sin, which at 0 is the closed door filling the doorway and at THETA0 is the drawing itself."""
    dxc = (X + 35.0) / math.cos(THETA0)
    yc = Y - SHEAR0 / math.sin(THETA0) * math.sin(THETA0) * dxc
    return (-35.0 + math.cos(th) * dxc, yc + SHEAR0 / math.sin(THETA0) * math.sin(th) * dxc)


def unwrap(a, near):
    while a - near > math.pi:
        a -= 2 * math.pi
    while near - a > math.pi:
        a += 2 * math.pi
    return a


def to_local(m, p):
    a, b, c, d, tx, ty = m
    det = a * d - b * c
    x, y = p[0] - tx, p[1] - ty
    return ((d * x - c * y) / det, (-b * x + a * y) / det)


def pts_world(scene, byid, shape_id):
    m = world(scene, shape_id)
    out = []
    for c in byid[shape_id]:
        if c.tag == "PointsPath":
            for v in c:
                if "Vertex" in v.tag:
                    x, y = float(v.get("x", 0)), float(v.get("y", 0))
                    out.append((m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5]))
    return out


def pieces_react(doc, scene, byid, T, slot_vmap, bm, size, notes):
    # ---- note 1: the door is shut until the room has settled, then swings open to its drawing; every part of the panel (fill, slits,
    # knob, and the slot that hides the ball behind it) moves as one, vertex by vertex, handles included
    shapes = [c for c in byid["1:1191"] if c.tag == "Shape" and c.get("name") not in ("Shelf Door Panel Slot", "door-knob")]
    # the knob is drawn round on the open door; it rides with the panel (its centre follows the swing) and stays round
    knob = byid["1:1220"]
    kx0, ky0 = float(knob.get("x", 0)), float(knob.get("y", 0))
    kpos = {f: door_map(kx0, ky0, door_theta(f)) for f in range(L + 1)}
    T.frames("1:1220", "x", {f: kpos[f][0] for f in kpos})
    T.frames("1:1220", "y", {f: kpos[f][1] for f in kpos})
    verts = []
    for sh in shapes:
        sx, sy = float(sh.get("x", 0)), float(sh.get("y", 0))
        for pth in sh:
            if pth.tag == "PointsPath":
                for v in pth:
                    if "Vertex" in v.tag:
                        verts.append((v, sx, sy, [v.get("id")] + ([slot_vmap[v.get("id")]] if v.get("id") in slot_vmap else [])))
    for v, sx, sy, ids in verts:
        X, Y = sx + float(v.get("x", 0)), sy + float(v.get("y", 0))
        cubic = v.tag == "CubicDetachedVertex"
        vals = {q: {} for q in ("x", "y", "inRotation", "inDistance", "outRotation", "outDistance")}
        for f in range(L + 1):
            th = door_theta(f)
            px, py = door_map(X, Y, th)
            vals["x"][f], vals["y"][f] = px - sx, py - sy
            if cubic:
                for side in ("in", "out"):
                    r0, d0 = float(v.get(side + "Rotation", 0)), float(v.get(side + "Distance", 0))
                    hx, hy = door_map(X + d0 * math.cos(r0), Y + d0 * math.sin(r0), th)
                    vals[side + "Rotation"][f] = unwrap(math.atan2(hy - py, hx - px), r0)
                    vals[side + "Distance"][f] = math.hypot(hx - px, hy - py)
        for q, d in vals.items():
            if d:
                for oid in ids:
                    T.frames(oid, q, d)
    notes.append(f"door shut until {DOOR_OPEN[0]}, open {DOOR_OPEN[0]}-{DOOR_OPEN[1]}, shuts {DOOR_CLOSE[0]}-{DOOR_CLOSE[1]} (cycle frames)")

    # the slam: the umbrella in the bin next to the door jumps a little as the door shuts (4 px at the ball's gravity, then one small
    # rebound of 1 px), with a slight tilt, back at rest a quarter second later
    slam = DOOR_CLOSE[1]
    um = byid["1:1151"]
    uy0, ur0 = float(um.get("y", 0)), float(um.get("rotation", 0))
    def hop(u):
        out = 0.0
        t = u
        for h in (4.0, 1.0):
            v0 = math.sqrt(2 * G * h)
            dur = 2 * v0 / G
            if 0 <= t < dur:
                return -(v0 * t - 0.5 * G * t * t)
            t -= dur
        return out
    T.frames("1:1151", "y", {f: uy0 + hop(f - slam) for f in range(L + 1)})
    T.frames("1:1151", "rotation", {f: ur0 + (0.02 * math.sin(math.pi * (f - slam) / 9) ** 2 if 0 <= f - slam < 9 else 0.0) for f in range(L + 1)})
    notes.append(f"umbrella hop from cycle {slam}")

    # ---- note 3: the trophy shakes a little as the ball drops in, about its base, dying away fast (each swing 0.55 of the one before)
    base = pts_world(scene, byid, "1:1980")
    bx = sum(p[0] for p in base) / len(base)
    by = max(p[1] for p in base)
    tpx, tpy = to_local(world(scene, "1:1894"), (bx, by))
    tpiv, _ = doc.wrap("1:1914", "Shelf Trophy Shake", tpx, tpy)
    rim = pts_world(scene, byid, "1:1915") or [(0, 420)]
    rim_y = sum(p[1] for p in rim) / len(rim)
    ent = next(f for f in range(TROPHY_ON - 20, 300) if value_at(bm["y"], f) + DY > rim_y + 2 and value_at(bm["y"], f + 1) >= value_at(bm["y"], f))
    P, r_ = 10.0, 0.55
    tau = (P / 2) / math.log(1 / r_)
    shake = {f: (-0.03 * math.exp(-(f - ent) / tau) * math.sin(2 * math.pi * (f - ent) / P) if 0 <= f - ent < 40 else 0.0) for f in range(L + 1)}
    T.frames(tpiv, "rotation", shake)
    notes.append(f"trophy shake from cycle {ent}")

    # ---- note 4: the crown dips and tilts a little where the ball bounces off it, quick down, slow back, no overshoot
    cb = pts_world(scene, byid, "1:1842")
    cx_ = sum(p[0] for p in cb) / len(cb)
    cy_ = max(p[1] for p in cb)
    cpx, cpy = to_local(world(scene, "1:1778"), (cx_, cy_))
    cpiv, _ = doc.wrap("1:1805", "Shelf Crown Bump", cpx, cpy)
    hit = 225
    vy = abs(value_at(bm["y"], hit) - value_at(bm["y"], hit - 1))
    vx = value_at(bm["x"], hit) - value_at(bm["x"], hit - 1)
    depth = max(1.0, min(2.0, 0.25 * vy))
    tilt = math.copysign(0.03, vx if vx else 1.0)
    def g(u):
        if u < 0 or u >= 35:
            return 0.0
        return math.sin(0.5 * math.pi * u / 5) if u <= 5 else 0.5 + 0.5 * math.cos(math.pi * (u - 5) / 30)
    T.frames(cpiv, "y", {f: cpy + depth * g(f - hit) for f in range(L + 1)})
    T.frames(cpiv, "rotation", {f: tilt * g(f - hit) for f in range(L + 1)})
    notes.append(f"crown dips {depth:.1f} px and tilts {math.degrees(tilt):.1f} deg at cycle {hit}")
