"""Bring one of the illustrator's rooms into a chapter, copying their loop exactly.

    python3 tools/import_room.py tools/rooms/spelling-bee.json                     into chapters/ch2
    python3 tools/import_room.py tools/rooms/spelling-bee.json --out /tmp/try      into a copy of the chapter instead
    python3 tools/import_room.py tools/rooms/spelling-bee.json --illustrator FILE  another pull of the art source

The art source is read, never written. A config in tools/rooms/ names the room. The importer:

  * copies the room's art: every top-level group of the artboard except the source's own wall, floor, joystick and
    ball, with hidden nodes left out and fresh ids. Pieces above the ball in the source stay above it;
  * rebuilds the ball as plain art: the Solo becomes a Node and the joystick is dropped. What the rig produced is
    written down directly: values it held still are set on the art, values that move are keyed, one key per frame,
    sampled from the joystick's own keys and the rig animations, then thinned where a straight line is exact;
  * copies the illustrator's loop key for key (frames, values, easing, elastic and value-eased keys included). The
    only change is where a property's last key differs from its first: that key is set to the first, and the change
    is printed so it goes on the fix list;
  * adds the room the way Wordle is built: wrappers for pieces that drop in, the intro and its Waiting pose, the
    moves, the colour pose, the draw rule, the state machine layers, and the lockup from the config's SVG.

The intro is the one motion designed here, from the config. Everything else is the source's.
The chapter is edited by splicing new text in, so the git diff holds only what was added.
"""
import argparse
import copy
import json
import math
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import svg_to_rml
from rml_read import REPO, chapter_dir

ILLUSTRATOR = Path("/tmp/yig-illus-2668591/scene.rml")
TOL = 1e-4

EASE = {  # the spec's named curves: (x1, y1, x2, y2)
    "power2.in": (0.32, 0, 0.67, 0), "power2.out": (0.33, 1, 0.68, 1), "power2.inOut": (0.65, 0, 0.35, 1),
    "power1.out": (0.5, 1, 0.89, 1), "power1.inOut": (0.45, 0, 0.55, 1), "sine.inOut": (0.37, 0, 0.63, 1),
    "back.out": (0.34, 1.56, 0.64, 1), "expo.out": (0.16, 1, 0.3, 1), "power3.in": (0.5, 0, 0.75, 0),
}
# The lockup is Wordle's, to the frame: in from frame 115, gone at frame 192 (3.2 s).
LOCKUP_AT = (748.0, 363.0)              # the Lockup node
LOCKUP_ART = (0.0, 19.475349)           # the Art node, relative to it
SVG_ART_ORIGIN = (87.5, 66.275)         # where the Art node sits in the lockup SVGs' 175 x 128 frame
WORD_DRIFT = 10.0
LOCKUP_FRAMES = {"in": 115, "settle": 149, "show": 128, "hold": 176, "out": 192, "word_in": 119, "word_settle": 153}

VERTEX = ("StraightVertex", "CubicDetachedVertex", "CubicMirroredVertex", "CubicAsymmetricVertex")
SKIP_TOP = ("Floor", "Wall")            # the source's own backdrop; the chapter has one shared backdrop
SKIP_ATTRS = ("name", "id", "folderId")
UNSUPPORTED = {"Image", "ImageAsset", "ClippingShape", "Text", "NestedArtboard"}


class Ids:
    """Fresh ids in the 9: namespace, continuing after any already in the file's text."""

    def __init__(self, text):
        self.n = max((int(m) for m in re.findall(r'id="9:(\d+)"', text)), default=0)

    def __call__(self):
        self.n += 1
        return f"9:{self.n}"


def fresh(elem, ids, idmap):
    """Deep copy with new ids; every attribute that held an old id now holds the new one."""
    c = copy.deepcopy(elem)
    for e in c.iter():
        if e.get("id"):
            idmap[e.get("id")] = ids()
    for e in c.iter():
        for k, v in list(e.attrib.items()):
            if v in idmap:
                e.set(k, idmap[v])
    return c


def fnum(v):
    s = f"{v:.7f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


# ---------------------------------------------------------------------------------------------------- easing
def bezier_ease(x1, y1, x2, y2, t):
    """The eased fraction for time fraction t on a cubic-bezier easing curve."""
    if t <= 0:
        return 0.0
    if t >= 1:
        return 1.0

    def b(u, a, c):
        return 3 * (1 - u) ** 2 * u * a + 3 * (1 - u) * u ** 2 * c + u ** 3

    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if b(mid, x1, x2) < t else (lo, mid)
    return b((lo + hi) / 2, y1, y2)


def read_keys(kp):
    """[(frame, value, interpolation, (x1, y1, x2, y2) or None)] for a KeyedProperty, in frame order."""
    out = []
    for k in kp:
        c = k.find("CubicEaseInterpolator")
        ctrl = tuple(float(c.get(a, d)) for a, d in (("x1", .42), ("y1", 0), ("x2", .58), ("y2", 1))) if c is not None else None
        out.append((int(k.get("frame", 0)), float(k.get("value", 0)), k.get("interpolationType", "hold"), ctrl))
    return sorted(out, key=lambda t: t[0])


def value_at(keys, f):
    """A property's value at frame f from its keys. Hold, linear and cubic-ease keys: all a joystick or rig needs."""
    if f <= keys[0][0]:
        return keys[0][1]
    for (f0, v0, how, ctrl), (f1, v1, _, _) in zip(keys, keys[1:]):
        if f0 <= f < f1:
            t = (f - f0) / (f1 - f0)
            if how == "hold":
                return v0
            if how == "linear":
                return v0 + (v1 - v0) * t
            if how == "cubic" and ctrl:
                return v0 + (v1 - v0) * bezier_ease(*ctrl, t)
            raise ValueError(f"cannot sample a {how!r} key")
    return keys[-1][1]


# ------------------------------------------------------------------------------------------------- geometry
def affine(node):
    """The node's own transform (a, b, c, d, tx, ty): translate, rotate, then scale, as Rive composes them."""
    r = float(node.get("rotation", 0))
    sx, sy = float(node.get("scaleX", 1)), float(node.get("scaleY", 1))
    cs, sn = math.cos(r), math.sin(r)
    return (cs * sx, sn * sx, -sn * sy, cs * sy, float(node.get("x", 0)), float(node.get("y", 0)))


def compose(m, n):
    a, b, c, d, e, f = m
    p, q, r, s, t, u = n
    return (a * p + c * q, b * p + d * q, a * r + c * s, b * r + d * s, a * t + c * u + e, b * t + d * u + f)


def extent(elem, m=(1, 0, 0, 1, 0, 0), out=None):
    """[x0, y0, x1, y1] of every vertex and handle under elem, in elem's parent space transformed by m."""
    out = out if out is not None else [1e9, 1e9, -1e9, -1e9]
    for c in elem:
        if c.tag in ("Node", "Shape", "Solo", "Ellipse"):
            extent(c, compose(m, affine(c)), out)
        elif c.tag == "PointsPath":
            extent(c, m, out)
        elif c.tag in VERTEX:
            px, py = float(c.get("x", 0)), float(c.get("y", 0))
            pts = [(px, py)]
            for key in ("in", "out"):
                d = float(c.get(f"{key}Distance", 0))
                if d:
                    r = float(c.get(f"{key}Rotation", 0))
                    pts.append((px + d * math.cos(r), py + d * math.sin(r)))
            for qx, qy in pts:
                x, y = m[0] * qx + m[2] * qy + m[4], m[1] * qx + m[3] * qy + m[5]
                out[:] = [min(out[0], x), min(out[1], y), max(out[2], x), max(out[3], y)]
    return out


# --------------------------------------------------------------------------------------------- the ball rig
class Rig:
    """What the illustrator's joystick rig makes a ball do, read from their file and sampled, not reinterpreted."""

    def __init__(self, joystick, anims_by_id):
        self.joystick = joystick
        self.invert = {"x": joystick.get("invertX") == "true", "y": joystick.get("invertY") == "true"}
        self.axes = {"x": anims_by_id.get(joystick.get("xId")), "y": anims_by_id.get(joystick.get("yId"))}
        self.targets = {}      # (source object id, property) -> (axis, keys)
        for axis, anim in self.axes.items():
            for ko in (anim.findall("KeyedObject") if anim is not None else []):
                for kp in ko.findall("KeyedProperty"):
                    self.targets[(ko.get("objectId"), kp.get("property"))] = (axis, read_keys(kp))

    def frame(self, axis, j):
        """The frame the joystick holds an axis animation at, for joystick value j in [-1, 1]."""
        j = max(-1.0, min(1.0, -j if self.invert[axis] else j))
        return (j + 1) / 2 * int(self.axes[axis].get("duration", 60))

    def sample(self, jx, jy):
        """{(object id, property): value} with the joystick at (jx, jy)."""
        return {key: value_at(keys, self.frame(axis, jx if axis == "x" else jy)) for key, (axis, keys) in self.targets.items()}


def thin(samples, eps=1e-4):
    """Drop interior samples that a straight line between their neighbours reproduces to within eps. [(frame, value)]."""
    keep, stack = {0, len(samples) - 1}, [(0, len(samples) - 1)]
    while stack:
        a, b = stack.pop()
        (fa, va), (fb, vb) = samples[a], samples[b]
        worst, at = 0.0, None
        for i in range(a + 1, b):
            f, v = samples[i]
            err = abs(v - (va + (vb - va) * (f - fa) / (fb - fa)))
            if err > worst:
                worst, at = err, i
        if at is not None and worst > eps:
            keep.add(at)
            stack += [(a, at), (at, b)]
    return [samples[i] for i in sorted(keep)]


# ----------------------------------------------------------------------------------------------- writing keys
def key_xml(frame, value, ease, ids, color=False):
    tag = "KeyFrameColor" if color else "KeyFrameDouble"
    v = "" if (not color and abs(value) < 1e-12) else f' value="{value if color else fnum(value)}"'
    if ease is None:
        return f'<{tag}{v} frame="{frame}" id="{ids()}"/>'
    if ease == "linear":
        return f'<{tag}{v} interpolationType="linear" frame="{frame}" id="{ids()}"/>'
    x1, y1, x2, y2 = EASE[ease]
    return (f'<{tag}{v} interpolationType="cubic" frame="{frame}" id="{ids()}">'
            f'<CubicEaseInterpolator x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" id="{ids()}"/></{tag}>')


def animation(name, duration, spec, ids, loop=False, one_frame=False):
    """spec: {object id: {property: [(time, value, ease)]}}; an int time is a frame, a float is seconds."""
    parts = []
    for oid, props in spec.items():
        kps = [f'<KeyedProperty property="{p}" id="{ids()}">'
               + "".join(key_xml(t if isinstance(t, int) else round(t * 60), v, e, ids) for t, v, e in ks) + "</KeyedProperty>"
               for p, ks in props.items()]
        parts.append(f'<KeyedObject objectId="{oid}" id="{ids()}">' + "".join(kps) + "</KeyedObject>")
    attrs = (' loopValue="loop"' if loop else "") + (' fps="60"' if one_frame else "")
    return ET.fromstring(f'<LinearAnimation{attrs} duration="{duration}" name="{name}" id="{ids()}">' + "".join(parts) + "</LinearAnimation>")


def to_text(elem, level):
    """An element as text, indented to sit at `level` (four spaces each) in the chapter's file."""
    elem = copy.deepcopy(elem)
    ET.indent(elem, space="    ", level=level)
    return "    " * level + ET.tostring(elem, encoding="unicode").replace(" />", "/>")


# ----------------------------------------------------------------------------------------------- the build
class Build:
    def __init__(self, cfg, text, illustrator_root):
        self.cfg, self.text = cfg, text
        self.name = cfg["room"]
        self.root = ET.fromstring(text)
        self.ab = self.root.find("Artboard")
        self.sm = self.ab.find("StateMachine")
        self.ids = Ids(text)
        self.anims = {a.get("name"): a for a in self.ab.iter("LinearAnimation")}
        self.layers = {l.get("name"): l for l in self.sm.findall("StateMachineLayer")}
        self.named = {n.get("name"): n for n in self.ab.iter() if n.get("name")}
        self.src = next(a for a in illustrator_root.findall("Artboard") if a.get("name") == cfg["artboard"])
        self.src_by_id = {e.get("id"): e for e in self.src.iter() if e.get("id")}
        self.idmap = {}        # source id -> id in this file
        self.mine = {}         # id in this file -> element, for the art brought in
        self.fixes = []        # (what, was, now) where a loop did not close
        self.notes = []
        if f"{self.name} Room" in self.named:
            raise SystemExit(f"{self.name} Room is already in this chapter; restore scene.rml (git checkout) to import it again")

    def register(self, tree):
        for e in tree.iter():
            if e.get("id"):
                self.mine[e.get("id")] = e

    def rename(self, tree):
        for e in tree.iter():
            if e.get("name") and "Wordle" in e.get("name"):
                e.set("name", e.get("name").replace("Wordle", self.name))

    # -- art
    def take(self, src_id):
        e = fresh(self.src_by_id[src_id], self.ids, self.idmap)
        for parent in list(e.iter()):
            for c in list(parent):
                if c.get("hidden") == "true":
                    parent.remove(c)
        bad = {x.tag for x in e.iter()} & UNSUPPORTED
        if bad:
            raise SystemExit(f"{self.name}: {sorted(bad)} in {self.src_by_id[src_id].get('name')!r} are not handled by this importer yet")
        self.register(e)
        return e

    def wrappers(self, name, src_ids):
        """For a piece that drops in: each group gets a wrapper positioned on the pieces' shared base centre, art offset back."""
        arts = [self.take(i) for i in src_ids]
        box = [1e9, 1e9, -1e9, -1e9]
        for a in arts:
            holder = ET.Element("Node")
            holder.append(a)
            b = extent(holder)
            box = [min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3])]
        px, py = round((box[0] + box[2]) / 2, 3), round(box[3], 3)
        out = []
        for i, art in enumerate(arts):
            label = name if len(arts) == 1 else f"{name} {i + 1}"
            w = ET.fromstring(f'<Node x="{px}" y="{py}" name="{self.name} {label}" id="{self.ids()}"/>')
            inner = ET.fromstring(f'<Node x="{-px}" y="{-py}" name="{self.name} {label} Art" id="{self.ids()}"/>')
            inner.append(art)
            w.append(inner)
            self.register(w)
            out.append(w)
        return out, py

    # -- the ball
    def make_ball(self, solo):
        """The Solo's active child under a plain Node that takes the Solo's place."""
        child = next(c for c in solo if c.get("id") == solo.get("activeComponentId"))
        ball = ET.fromstring(f'<Node name="{self.name} Ball" id="{self.ids()}"/>')
        self.idmap[solo.get("id")] = ball.get("id")       # the loop's keys on Ball_Move now key this node
        ball.append(self.take(child.get("id")))
        self.register(ball)
        return ball

    def joystick_series(self, joystick, loop):
        """The joystick's (x, y) on every frame of the loop: its keyed values, else its authored value."""
        keys = {}
        for ko in loop.findall("KeyedObject"):
            if ko.get("objectId") == joystick.get("id"):
                for kp in ko.findall("KeyedProperty"):
                    keys[kp.get("property")] = read_keys(kp)
        authored = {"x": float(joystick.get("x", 0)), "y": float(joystick.get("y", 0))}
        n = int(loop.get("duration", 60))
        return [tuple(value_at(keys[a], f) if a in keys else authored[a] for a in "xy") for f in range(n)]

    def bake(self, rig, series):
        """(static, moving, series). static {source id: {prop: value}} is set on the art; moving {source id: {prop:
        [(frame, value)]}} is keyed. Both are what the rig produced on each frame of the loop."""
        per_frame = [rig.sample(jx, jy) for jx, jy in series]
        static, moving = {}, {}
        for key in per_frame[0]:
            if key[0] not in self.idmap:
                continue
            s = [(f, pf[key]) for f, pf in enumerate(per_frame)]
            if all(abs(v - s[0][1]) < 1e-9 for _, v in s):
                static.setdefault(key[0], {})[key[1]] = s[0][1]
            else:
                last = max(f for f, v in s if abs(v - s[-1][1]) > 1e-9) + 1
                moving.setdefault(key[0], {})[key[1]] = thin(s[:last + 1])
        return static, moving

    # -- the loop
    def copy_loop(self, loop, moving, joystick_id):
        """The illustrator's loop with the joystick replaced by the baked keys."""
        ids = self.ids
        anim = ET.Element("LinearAnimation", {k: v for k, v in loop.attrib.items() if k not in SKIP_ATTRS})
        anim.set("name", f"{self.name} Loop")
        anim.set("id", ids())
        left_out = []
        for ko in loop.findall("KeyedObject"):
            old = ko.get("objectId")
            if old == joystick_id:
                continue
            if old not in self.idmap:
                left_out.append(old)
                continue
            new = copy.deepcopy(ko)
            for e in new.iter():
                if e.get("id"):
                    e.set("id", ids())
            new.set("objectId", self.idmap[old])
            self.close(new, old)
            anim.append(new)
        for oid, props in moving.items():
            ko = ET.SubElement(anim, "KeyedObject", {"objectId": self.idmap[oid], "id": ids()})
            for prop, series in props.items():
                kp = ET.SubElement(ko, "KeyedProperty", {"property": prop, "id": ids()})
                for i, (f, v) in enumerate(series):
                    attrs = {"frame": str(f), "id": ids()}
                    if abs(v) > 1e-12:
                        attrs["value"] = fnum(v)
                    if i < len(series) - 1:
                        attrs["interpolationType"] = "linear"
                    ET.SubElement(kp, "KeyFrameDouble", attrs)
        if left_out:
            self.notes.append(f"the loop keys objects that were not brought in, left out: {left_out}")
        return anim

    def close(self, ko, old_id):
        """Where a property's last key is not its first, set the last to the first: the smallest change that closes it."""
        label = self.src_by_id[old_id].get("name") or self.src_by_id[old_id].tag
        for kp in ko.findall("KeyedProperty"):
            keys = sorted(kp, key=lambda k: int(k.get("frame", 0)))
            if len(keys) < 2 or keys[0].tag != "KeyFrameDouble":
                continue
            first, last = float(keys[0].get("value", 0)), float(keys[-1].get("value", 0))
            if abs(first - last) > TOL:
                self.fixes.append((f"{label} {kp.get('property')}, last key at frame {keys[-1].get('frame')}", last, first))
                if abs(first) < 1e-12:
                    keys[-1].attrib.pop("value", None)
                else:
                    keys[-1].set("value", fnum(first))

    def start_pose(self, loop):
        """Every property the loop keys starts at its first key: the art is authored in that pose. Returns {(id, prop): v}."""
        pose = {}
        for ko in loop.findall("KeyedObject"):
            node = self.mine.get(ko.get("objectId"))
            for kp in ko.findall("KeyedProperty"):
                keys = sorted(kp, key=lambda k: int(k.get("frame", 0)))
                if keys[0].tag != "KeyFrameDouble":
                    continue
                v, prop = float(keys[0].get("value", 0)), kp.get("property")
                pose[(ko.get("objectId"), prop)] = v
                if node is not None and prop in ("x", "y", "rotation", "scaleX", "scaleY", "opacity"):
                    if abs(v - (1.0 if prop in ("scaleX", "scaleY", "opacity") else 0.0)) > 1e-12:
                        node.set(prop, fnum(v))
                    else:
                        node.attrib.pop(prop, None)
        return pose

    # -- the lockup
    def lockup(self):
        """The gate, the lockup and its icon and word, converted from the config's SVG. Returns (gate, ids dict, word rest y)."""
        ids = self.ids
        svg = svg_to_rml.svg_paths((REPO / self.cfg["lockup"]).read_text())
        parts = {"Word": [], "Icon": []}
        for colour, subs in svg:
            b = svg_to_rml.bounds(svg_to_rml.points(subs))
            parts["Word" if (b[1] + b[3]) / 2 > 92 else "Icon"].append((colour, subs))
        gate = ET.fromstring(f'<Node name="{self.name} Lockup Gate" id="{ids()}"/>')
        lock = ET.SubElement(gate, "Node", {"x": fnum(LOCKUP_AT[0]), "y": fnum(LOCKUP_AT[1]), "opacity": "0", "name": f"{self.name} Lockup", "id": ids()})
        art = ET.SubElement(lock, "Node", {"y": fnum(LOCKUP_ART[1]), "name": f"{self.name} Lockup Art", "id": ids()})
        made = {"gate": gate.get("id"), "lockup": lock.get("id")}
        for part in ("Word", "Icon"):
            pts = [p for _, subs in parts[part] for p in svg_to_rml.points(subs)]
            x0, y0, x1, y1 = svg_to_rml.bounds(pts)
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            node = ET.SubElement(art, "Node", {"name": f"{self.name} Lockup {part}", "id": ids()})
            rx, ry = cx - SVG_ART_ORIGIN[0], cy - SVG_ART_ORIGIN[1]
            if abs(rx) > 1e-9:
                node.set("x", fnum(rx))
            if abs(ry) > 1e-9:
                node.set("y", fnum(ry))
            for colour, subs in reversed(parts[part]):           # the SVG paints first path at the back; RML draws first child on top
                node.append(ET.fromstring(svg_to_rml.shape_xml(colour, subs, ids, offset=(cx, cy))))
            made[part.lower()] = node.get("id")
            made[part.lower() + "_y"] = ry
        return gate, made

    def lockup_animations(self, made):
        out = {}
        for m in ("Shown", "Hidden"):
            c = fresh(self.anims[f"Wordle Lockup {m}"], self.ids, {self.named["Wordle Lockup Gate"].get("id"): made["gate"]})
            c.set("name", f"{self.name} Lockup {m}")
            out[c.get("name")] = c
        return out

    def lockup_keys(self, made):
        F = LOCKUP_FRAMES
        return {
            made["lockup"]: {
                "opacity": [(F["in"], 0, "linear"), (F["show"], 1, None), (F["hold"], 1, "power2.in"), (F["out"], 0, None)],
                "scaleX": [(F["in"], 0.96, "expo.out"), (F["settle"], 1, None), (F["hold"], 1, "power3.in"), (F["out"], 0.97, None)],
                "scaleY": [(F["in"], 0.96, "expo.out"), (F["settle"], 1, None), (F["hold"], 1, "power3.in"), (F["out"], 0.97, None)],
                "y": [(F["in"], LOCKUP_AT[1] + 18, "expo.out"), (F["settle"], LOCKUP_AT[1], None), (F["hold"], LOCKUP_AT[1], "power3.in"), (F["out"], LOCKUP_AT[1] - 30, None)],
            },
            made["word"]: {
                "opacity": [(F["word_in"], 0, "expo.out"), (F["word_settle"], 1, None)],
                "y": [(F["word_in"], made["word_y"] + WORD_DRIFT, "expo.out"), (F["word_settle"], made["word_y"], None)],
            },
        }

    # -- the intro
    def intro(self, cfg, loop, pose, rig, series, moving, ball, planes, drops, made):
        """The designed motion: the floor pans in with the pieces on it, pieces drop and settle, the ball rolls in and
        lands in the loop's first pose, the lockup plays as Wordle's does. Every property the loop keys is held at its
        first value, so the loop starts on the intro's last frame."""
        c = cfg["intro"]
        spec = {}
        pan0, pan1 = c["plane"]
        for plane in planes:
            spec[plane.get("id")] = {"x": [(pan0, 1600, "power2.inOut"), (pan1, 0, None)]}
        for d in c["drops"]:
            wrappers, base_y = drops[d["name"]]
            t0, t1 = d["from"], d["to"]
            for w in wrappers:
                spec[w.get("id")] = {
                    "y": [(t0, base_y - 800, "power2.in"), (t1, base_y, None)],
                    "scaleX": [(t1, 1, "power2.out"), (t1 + 0.07, 1.03, "back.out"), (t1 + 0.32, 1, None)],
                    "scaleY": [(t1, 1, "power2.out"), (t1 + 0.07, 0.93, "back.out"), (t1 + 0.32, 1, None)],
                }
        bid = ball.get("id")
        roll0, roll1 = c["ball"]["roll"]
        land0, land1 = c["ball"]["land"]
        spec[bid] = {"x": [(roll0, c["ball"].get("from_x", -80), "power1.out"), (roll1, pose[(bid, "x")], None)],
                     "y": [(roll0, pose[(bid, "y")], None)]}
        round_pose = rig.sample(-1.0, series[0][1])            # the joystick at its round end, the pose the ball rolls in with
        for oid, props in moving.items():
            nid = self.idmap[oid]
            spec[nid] = {}
            for prop, s in props.items():
                v0, v1 = round_pose[(oid, prop)], s[0][1]
                spec[nid][prop] = [(roll0, v0, None), (land0, v0, "power2.out"), (land1, v1, None)]
        for (nid, prop), v in pose.items():                    # anything else the loop keys is held at its first value
            if prop in spec.get(nid, {}):
                continue
            spec.setdefault(nid, {})[prop] = [(0.0, v, None)]
        for nid, props in self.lockup_keys(made).items():
            spec.setdefault(nid, {}).update(props)
        waiting = {o: {p: [(0, ks[0][1], None)] for p, ks in props.items()} for o, props in spec.items()}
        return spec, waiting

    def check_intro(self, spec, pose):
        """The intro must end where the loop begins."""
        for (nid, prop), v in pose.items():
            last = spec[nid][prop][-1][1]
            if abs(last - v) > TOL:
                raise SystemExit(f"{self.name}: the intro ends {prop} at {last} but the loop starts it at {v}")

    # -- everything
    def build(self):
        cfg, name, ids = self.cfg, self.name, self.ids
        loop_src = next(a for a in self.src.findall("LinearAnimation") if a.get("name") == cfg["loop"])
        solo = next(e for e in self.src.iter("Solo") if e.get("name") == cfg.get("ball", "Ball_Move"))
        joystick = next(e for e in self.src.iter("Joystick"))
        rig = Rig(joystick, {a.get("id"): a for a in self.src.findall("LinearAnimation")})

        order = [c for c in self.src if c.tag in ("Node", "Shape", "Solo") and not (c.get("name") or "").startswith(SKIP_TOP)]
        ball_at = next(i for i, c in enumerate(order) if c is solo)
        dropped = {i: d for d in cfg["intro"]["drops"] for i in d["ids"]}
        drops = {d["name"]: self.wrappers(d["name"], d["ids"]) for d in cfg["intro"]["drops"]}
        front, back = ET.Element("Front"), ET.Element("Back")
        for pos, c in enumerate(order):
            if c is solo:
                continue
            bucket = front if pos < ball_at else back
            d = dropped.get(c.get("id"))
            bucket.append(drops[d["name"]][0][d["ids"].index(c.get("id"))] if d else self.take(c.get("id")))
        ball = self.make_ball(solo)

        series = self.joystick_series(joystick, loop_src)
        static, moving = self.bake(rig, series)
        for oid, props in static.items():                      # what the rig held still: set on the art
            node = self.mine[self.idmap[oid]]
            for prop, v in props.items():
                if abs(v - (1.0 if prop in ("scaleX", "scaleY") else 0.0)) > 1e-12:
                    node.set(prop, fnum(v))
                else:
                    node.attrib.pop(prop, None)
        loop = self.copy_loop(loop_src, moving, joystick.get("id"))
        pose = self.start_pose(loop)

        back_plane = ET.fromstring(f'<Node name="{name} Floor Plane" id="{ids()}"/>')
        back_plane.extend(list(back))
        planes = [back_plane]
        front_plane = None
        if len(front):
            front_plane = ET.fromstring(f'<Node name="{name} Front Plane" id="{ids()}"/>')
            front_plane.extend(list(front))
            planes.append(front_plane)
        wall_lag = ET.fromstring(f'<Node name="{name} Wall Lag" id="{ids()}"><Node name="{name} Wall Plane" id="{ids()}"/></Node>')
        room = ET.fromstring(f'<Node name="{name} Room" id="{ids()}"/>')
        drmap = {}
        draw_rules = fresh(self.named["Wordle Draw Rules"], self.ids, drmap)
        self.rename(draw_rules)
        gate, made = self.lockup()
        for part in (draw_rules, gate, front_plane, ball, back_plane, wall_lag):
            if part is not None:
                room.append(part)

        spec, waiting_spec = self.intro(cfg, loop_src, pose, rig, series, moving, ball, planes, drops, made)
        self.check_intro(spec, pose)
        new = {f"{name} Intro": animation(f"{name} Intro", 192, spec, ids),
               f"{name} Waiting": animation(f"{name} Waiting", 1, waiting_spec, ids, one_frame=True), f"{name} Loop": loop}
        move_map = {self.named["Wordle Room"].get("id"): room.get("id"), self.named["Wordle Wall Lag"].get("id"): wall_lag.get("id")}
        for m in ("Outro", "Home", "Gone", "Back Out", "Right", "Return", "Forward In"):
            c = fresh(self.anims[f"Wordle {m}"], self.ids, dict(move_map))
            c.set("name", f"{name} {m}")
            new[c.get("name")] = c
        for m in ("On Top", "Below"):
            c = fresh(self.anims[f"Wordle {m}"], self.ids, dict(drmap))
            c.set("name", f"{name} {m}")
            new[c.get("name")] = c
        new[f"{name} Colors"] = ET.fromstring(
            f'<LinearAnimation fps="60" duration="1" name="{name} Colors" id="{ids()}">'
            f'<KeyedObject objectId="1:2304" id="{ids()}"><KeyedProperty property="colorValue" id="{ids()}">{key_xml(0, cfg["wall"], None, ids, True)}</KeyedProperty></KeyedObject>'
            f'<KeyedObject objectId="1:2297" id="{ids()}"><KeyedProperty property="colorValue" id="{ids()}">{key_xml(0, cfg["floor"], None, ids, True)}</KeyedProperty></KeyedObject>'
            f'</LinearAnimation>')
        new.update(self.lockup_animations(made))

        amap = {self.anims[f"Wordle {m}"].get("id"): new[f"{name} {m}"].get("id")
                for m in ("Waiting", "Intro", "Loop", "Outro", "Home", "Gone", "Back Out", "Right", "Return", "Forward In", "On Top", "Below")}
        amap.update({self.anims[f"Wordle Lockup {m}"].get("id"): new[f"{name} Lockup {m}"].get("id") for m in ("Shown", "Hidden")})
        scene_prop = next(p.get("id") for p in self.root.find("ViewModel") if p.get("name") == "scene")
        layers = []
        for ln in ("Wordle", "Wordle Exit", "Wordle Draw", "Wordle Lockup"):
            lay = fresh(self.layers[ln], self.ids, dict(amap))
            self.rename(lay)
            for cond in lay.iter("TransitionViewModelCondition"):
                dbc, cmp_ = cond.find(".//DataBindContext"), cond.find("TransitionValueNumberComparator")
                if dbc is not None and dbc.get("sourcePathIds", "").endswith("-" + scene_prop) and cmp_ is not None:
                    cmp_.set("value", str(cfg["scene"]))
            layers.append(lay)

        bd = self.layers["Backdrop"]
        state_id = ids()
        tr = fresh(bd.find("AnyState").findall("StateTransition")[1], self.ids, {})
        tr.set("stateToId", state_id)
        tr.find(".//TransitionValueNumberComparator").set("value", str(cfg["scene"]))
        state = ET.fromstring(f'<AnimationState animationId="{new[f"{name} Colors"].get("id")}" x="{160 + 240 * len(bd.findall("AnimationState"))}" y="0" id="{state_id}"/>')

        self.report_overhang(planes, ball, loop_src)
        return {"room": room, "animations": list(new.values()), "layers": layers, "backdrop_transition": tr, "backdrop_state": state}

    def report_overhang(self, planes, ball, loop_src):
        W, H = float(self.ab.get("width")), float(self.ab.get("height"))
        for plane in planes:
            for piece in plane:
                x0, y0, x1, y1 = extent(_hold(piece))
                if x0 < 0 or y0 < 0 or x1 > W or y1 > H:
                    self.notes.append(f"OVERHANG: {piece.get('name') or piece.tag} spans x {x0:.0f}..{x1:.0f}, y {y0:.0f}..{y1:.0f} against 0..{W:.0f} x 0..{H:.0f}")
        # the ball's path in the loop, with its radius
        xs, ys = [], []
        for ko in loop_src.findall("KeyedObject"):
            if self.idmap.get(ko.get("objectId")) == ball.get("id"):
                for kp in ko.findall("KeyedProperty"):
                    vals = [float(k.get("value", 0)) for k in kp]
                    (xs if kp.get("property") == "x" else ys if kp.get("property") == "y" else []).extend(vals)
        if xs and ys:
            box = extent(_hold(ball.find("Node")))
            r = max(abs(box[2] - box[0]), abs(box[3] - box[1])) / 2
            if min(xs) - r < 0 or max(xs) + r > W or min(ys) - 2 * r < 0 or max(ys) + r > H:
                self.notes.append(f"OVERHANG: the ball's loop path reaches x {min(xs) - r:.0f}..{max(xs) + r:.0f}, y {min(ys) - 2 * r:.0f}..{max(ys) + r:.0f}")


def _hold(elem):
    holder = ET.Element("Node")
    holder.append(elem)
    return holder


def splice(text, pieces):
    """Insert the new elements into the chapter's text. Nothing already there is rewritten except the Backdrop layer's
    two additions."""
    def before(marker, add, level):
        nonlocal text
        i = text.index(marker)
        i = text.rfind("\n", 0, i) + 1
        text = text[:i] + add + "\n" + text[i:]

    room_text = to_text(pieces["room"], 3)
    before('<Node name="Connections Room"', room_text, 3)
    before('<StateMachine name="Chapter 2"', "\n".join(to_text(a, 2) for a in pieces["animations"]), 2)
    # Backdrop: one more AnyState transition and one more state
    start = text.index('<StateMachineLayer name="Backdrop"')
    end = text.index("</StateMachineLayer>", start)
    layer = text[start:end]
    layer = layer.replace("</AnyState>", to_text(pieces["backdrop_transition"], 5).lstrip() + "\n                </AnyState>", 1) if "</AnyState>" in layer else layer
    layer = layer.rstrip() + "\n" + to_text(pieces["backdrop_state"], 4) + "\n            "
    text = text[:start] + layer + text[end:]
    before("</StateMachine>", "\n".join(to_text(l, 3) for l in pieces["layers"]), 3)
    return text


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config")
    ap.add_argument("--chapter", default="ch2")
    ap.add_argument("--out", help="write into a copy of the chapter here instead of editing it")
    ap.add_argument("--illustrator", default=str(ILLUSTRATOR))
    args = ap.parse_args(argv)
    cfg = json.loads(Path(args.config).read_text())
    src_dir = chapter_dir(args.chapter)
    if args.out:
        out = Path(args.out)
        if out.exists():
            shutil.rmtree(out)
        shutil.copytree(src_dir, out, ignore=shutil.ignore_patterns("build"))
        src_dir = out
    scene = src_dir / "scene.rml"
    text = scene.read_text()
    build = Build(cfg, text, ET.parse(args.illustrator).getroot())
    pieces = build.build()
    scene.write_text(splice(text, pieces))
    print(f"{cfg['room']} added to {scene}")
    if build.fixes:
        print("\nLoop fixes (the loop did not close; its last key now equals its first):")
        for what, was, now in build.fixes:
            print(f"  {what}: {was:g} -> {now:g}")
    else:
        print("\nLoop fixes: none, the illustrator's loop closes.")
    for n in build.notes:
        print(n)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
