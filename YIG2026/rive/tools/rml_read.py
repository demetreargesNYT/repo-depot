"""Read a chapter's scene.rml with a real XML parser.

RML omits any attribute that equals its default, so a key with value 0 has no
value attribute at all. Everything here treats a missing value as 0; never read
keys with a regular expression.
"""
import json
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


def chapter_dir_for_new(name):
    """chapters/<name>, which must already hold a chapter.json (a new file starts from its manifest)."""
    d = REPO / "chapters" / name
    if not (d / "chapter.json").exists():
        raise SystemExit(f"no {d / 'chapter.json'}: write the manifest first")
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
        manifest = self.path.parent / "chapter.json"
        self.manifest = json.loads(manifest.read_text()) if manifest.exists() else None

    # enums: a comparator or a default points at a DataEnumValue by id; its place in the enum is the value Rive stores
    def enum_index(self, value_id):
        e = self.by_id[value_id]
        return [v.get("id") for v in self.parent[e] if v.tag == "DataEnumValue"].index(value_id)

    def enum_name(self, value_id):
        return self.by_id[value_id].get("key")

    def enum_names(self, enum_name):
        enum = next(e for e in self.root.findall("DataEnumCustom") if e.get("name") == enum_name)
        return [v.get("key") for v in enum if v.tag == "DataEnumValue"]

    def cond_value(self, cond):
        """What a TransitionViewModelCondition compares against: an enum value's index, "true"/"false", or a number."""
        e = cond.find("TransitionValueEnumComparator")
        if e is not None:
            return self.enum_index(e.get("value"))
        b = cond.find("TransitionValueBooleanComparator")
        if b is not None:
            return b.get("value", "false")
        return int(float(cond.find("TransitionValueNumberComparator").get("value", "0")))

    def property_default(self, prop_id):
        """A view model property's default: the enum value's name, "true"/"false", or the number as written."""
        for v in self.view_model.iter("ViewModelInstanceEnum"):
            if v.get("viewModelPropertyId") == prop_id:
                return self.enum_name(v.get("propertyValue"))
        for v in self.view_model.iter():
            if v.tag.startswith("ViewModelInstance") and v.get("viewModelPropertyId") == prop_id:
                return v.get("propertyValue", "0" if v.tag.endswith("Number") else "false")
        return None

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
                    if k.tag == "KeyFrameId":
                        v = self.names.get(v, v)            # draw targets read as their names, not ids
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
                    if it in ("hold", "linear", "cubicValue", "elastic"):    # the illustrator's own curves have no named ease
                        es.append(it)
                        continue
                    es.append(self.eases_of(k.find("CubicEaseInterpolator")))
                out[(self.label(ko.get("objectId")), kp.get("property"))] = es
        return out

    def eases_of(self, c):
        """The spec's name for a CubicEaseInterpolator (on a key or a state transition)."""
        key = tuple(round(float(c.get(a, d)), 2) for a, d in (("x1", .42), ("y1", 0), ("x2", .58), ("y2", 1)))
        return EASES.get(key, f"cubic{key}")

    def scene_numbers(self):
        """{state machine layer name: the scene's place in the Scene enum its Intro/Home->Shown transition waits for}."""
        out = {}
        props = {p.get("id"): p.get("name") for p in self.view_model if p.tag.startswith("ViewModelProperty")}
        for layer in self.artboard.find("StateMachine").findall("StateMachineLayer"):
            if layer.get("name") == "Backdrop":       # waits for every room's value, not one; it has no room of its own
                continue
            for tr in layer.iter("StateTransition"):
                for c in tr.findall("TransitionViewModelCondition"):
                    ctx = c.find(".//DataBindContext").get("sourcePathIds").split("-")[-1]
                    if c.get("opValue", "equal") == "equal" and props.get(ctx) == "scene":
                        out[layer.get("name")] = self.cond_value(c)
        return out

    def scene_names(self):
        """The Scene enum's names in order; scene_numbers() values index into this."""
        return self.enum_names("Scene")


def degrees(rad):
    return math.degrees(rad)
