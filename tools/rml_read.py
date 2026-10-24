"""Read a chapter's scene.rml with a real XML parser.

RML omits any attribute that equals its default, so a key with value 0 has no
value attribute at all. Everything here treats a missing value as 0; never read
keys with a regular expression.
"""
import math
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# the cubic beziers the spec names, keyed by their four control numbers
EASES = {
    (0.65, 0, 0.35, 1): "power2.inOut", (0.32, 0, 0.67, 0): "power2.in", (0.33, 1, 0.68, 1): "power2.out",
    (0.5, 1, 0.89, 1): "power1.out", (0.45, 0, 0.55, 1): "power1.inOut", (0.37, 0, 0.63, 1): "sine.inOut",
    (0.16, 1, 0.3, 1): "expo.out", (0.5, 0, 0.75, 0): "power3.in", (0.34, 1.56, 0.64, 1): "back.out",
}


def chapter_dir(name):
    if Path(name).is_dir():          # a path works too, which is how the tests point it at a broken copy
        return Path(name)
    d = REPO / "chapters" / name
    if not (d / "scene.rml").exists():
        raise SystemExit(f"no chapter {name!r}: expected {d / 'scene.rml'}")
    return d


class Scene:
    def __init__(self, path):
        self.path = Path(path)
        self.root = ET.parse(self.path).getroot()
        self.artboard = self.root.find("Artboard")
        self.by_id = {e.get("id"): e for e in self.root.iter() if e.get("id")}
        self.names = {i: e.get("name") for i, e in self.by_id.items() if e.get("name")}
        self.parent = {c: p for p in self.root.iter() for c in p}
        self.animations = {a.get("name"): a for a in self.artboard.iter("LinearAnimation")}
        self.view_model = self.root.find("ViewModel")

    def node(self, name):
        hits = [e for e in self.artboard.iter("Node") if e.get("name") == name]
        if len(hits) != 1:
            raise KeyError(f"{name!r}: {len(hits)} matches")
        return hits[0]

    def label(self, oid):
        if oid in self.names:
            return self.names[oid]
        e = self.by_id.get(oid)
        if e is not None and e.tag == "SolidColor":
            shape = self.parent[self.parent[e]]
            return f'{shape.get("name") or "?"} colour'
        return oid

    def fps(self, anim):
        return int(anim.get("fps", 60))

    def duration(self, anim):
        return int(anim.get("duration", 60))

    def keys(self, anim):
        """{(object name, property): [(frame, value)]} with value a float, or a hex string for colours."""
        out = {}
        for ko in anim.findall("KeyedObject"):
            for kp in ko.findall("KeyedProperty"):
                ks = []
                for k in sorted(kp, key=lambda k: int(k.get("frame", 0))):
                    v = k.get("value", "0")
                    # colours are hex strings and draw-target keys are object ids; only doubles are numbers
                    ks.append((int(k.get("frame", 0)), float(v) if k.tag == "KeyFrameDouble" else v))
                out[(self.label(ko.get("objectId")), kp.get("property"))] = ks
        return out

    def eases(self, anim):
        """{(object name, property): [ease leaving each key]}; the ease on key i shapes the segment i -> i+1."""
        out = {}
        for ko in anim.findall("KeyedObject"):
            for kp in ko.findall("KeyedProperty"):
                es = []
                for k in sorted(kp, key=lambda k: int(k.get("frame", 0))):
                    it = k.get("interpolationType", "hold")
                    if it in ("hold", "linear"):
                        es.append(it)
                        continue
                    c = k.find("CubicEaseInterpolator")
                    key = tuple(round(float(c.get(a, d)), 2) for a, d in (("x1", .42), ("y1", 0), ("x2", .58), ("y2", 1)))
                    es.append(EASES.get(key, f"cubic{key}"))
                out[(self.label(ko.get("objectId")), kp.get("property"))] = es
        return out

    def scene_numbers(self):
        """{state machine layer name: scene value its Intro/Home->Shown transition waits for}, read from the conditions."""
        out = {}
        props = {p.get("id"): p.get("name") for p in self.view_model if p.tag.startswith("ViewModelProperty")}
        for layer in self.artboard.find("StateMachine").findall("StateMachineLayer"):
            for tr in layer.iter("StateTransition"):
                for c in tr.findall("TransitionViewModelCondition"):
                    ctx = c.find(".//DataBindContext").get("sourcePathIds").split("-")[-1]
                    if c.get("opValue", "equal") == "equal" and props.get(ctx) == "scene":
                        out[layer.get("name")] = int(float(c.find("TransitionValueNumberComparator").get("value", "0")))
        return out


def degrees(rad):
    return math.degrees(rad)
