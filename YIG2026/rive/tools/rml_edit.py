"""Edit a chapter's scene.rml as text: wrap a node in a pivot, and write keys into a room's animations.

The scene file is indented one level per element and every element's tags sit on their own lines, so an element is found by the
line that opens it (its id) and ends on the closing line at the same indent. Reading is still done with a real XML parser
(rml_read.Scene); this module only writes. Used by the one-time room scripts (ch1_cards_234.py).

Key lists are [(frame, value, how)] where how is "hold" (the default, steps to the next key), "linear", or an ease name from EASES
(a cubic ease leaving that key). A value of exactly 0 is written without a value attribute, as the Rive CLI does.
"""
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path

EASES = {
    "power2.inOut": (0.65, 0, 0.35, 1), "power2.in": (0.32, 0, 0.67, 0), "power2.out": (0.33, 1, 0.68, 1),
    "power1.out": (0.5, 1, 0.89, 1), "power1.inOut": (0.45, 0, 0.55, 1), "sine.inOut": (0.37, 0, 0.63, 1),
    "back.out": (0.34, 1.56, 0.64, 1),
}


def num(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


class Doc:
    def __init__(self, path):
        self.path = Path(path)
        self.lines = self.path.read_text().split("\n")
        ids = [int(m.group(1)) for m in re.finditer(r'\bid="9:(\d+)"', "\n".join(self.lines))]
        self.next_id = max(ids)

    def new_id(self):
        self.next_id += 1
        return f"9:{self.next_id}"

    def save(self):
        self.path.write_text("\n".join(self.lines))

    # ---- elements ------------------------------------------------------------------------------------------------------
    def idx(self, oid):
        pat = re.compile(r'^\s*<(\w+)\b[^>]*\bid="%s"' % re.escape(oid))
        hits = [i for i, l in enumerate(self.lines) if pat.match(l)]
        assert len(hits) == 1, (oid, hits)
        return hits[0]

    def end(self, i):
        line = self.lines[i]
        if line.rstrip().endswith("/>"):
            return i
        indent = len(line) - len(line.lstrip())
        tag = re.match(r"\s*<(\w+)", line).group(1)
        for j in range(i + 1, len(self.lines)):
            l = self.lines[j]
            if len(l) - len(l.lstrip()) == indent and l.lstrip().startswith(f"</{tag}>"):
                return j
        raise KeyError(line)

    def wrap(self, oid, name, px, py):
        """Put the element in a pivot: a node at (px, py) holding an "Art" node at (-px, -py), the pattern the stacks use.
        Returns (pivot id, art id). The pivot's own rotation and scale then turn the piece about (px, py)."""
        i = self.idx(oid)
        j = self.end(i)
        ind = len(self.lines[i]) - len(self.lines[i].lstrip())
        pad = " " * ind
        pid, aid = self.new_id(), self.new_id()
        body = [" " * 8 + l for l in self.lines[i:j + 1]]
        new = ([f'{pad}<Node x="{num(px)}" y="{num(py)}" name="{name}" id="{pid}">',
                f'{pad}    <Node x="{num(-px)}" y="{num(-py)}" name="{name} Art" id="{aid}">']
               + body + [f"{pad}    </Node>", f"{pad}</Node>"])
        self.lines[i:j + 1] = new
        return pid, aid

    def wrap_run(self, first_oid, last_oid, name, px, py):
        """The same, around a run of sibling elements from first to last."""
        i, j = self.idx(first_oid), self.end(self.idx(last_oid))
        ind = len(self.lines[i]) - len(self.lines[i].lstrip())
        pad = " " * ind
        pid, aid = self.new_id(), self.new_id()
        body = [" " * 8 + l for l in self.lines[i:j + 1]]
        new = ([f'{pad}<Node x="{num(px)}" y="{num(py)}" name="{name}" id="{pid}">',
                f'{pad}    <Node x="{num(-px)}" y="{num(-py)}" name="{name} Art" id="{aid}">']
               + body + [f"{pad}    </Node>", f"{pad}</Node>"])
        self.lines[i:j + 1] = new
        return pid, aid

    # ---- animations ----------------------------------------------------------------------------------------------------
    def anim(self, name):
        pat = re.compile(r'^\s*<LinearAnimation\b[^>]*\bname="%s"' % re.escape(name))
        hits = [i for i, l in enumerate(self.lines) if pat.match(l)]
        assert len(hits) == 1, (name, hits)
        return hits[0], self.end(hits[0])

    def set_duration(self, name, frames):
        i, _ = self.anim(name)
        self.lines[i] = re.sub(r'duration="\d+"', f'duration="{frames}"', self.lines[i])

    def key_lines(self, keys, pad):
        out = []
        for frame, value, how in keys:
            v = f' value="{num(value)}"' if num(value) != "0" else ""
            fr = f' frame="{frame}"' if frame else ""
            if how == "hold":
                out.append(f'{pad}<KeyFrameDouble{v}{fr} id="{self.new_id()}"/>')
            elif how == "linear":
                out.append(f'{pad}<KeyFrameDouble{v} interpolationType="linear"{fr} id="{self.new_id()}"/>')
            else:
                x1, y1, x2, y2 = EASES[how]
                out.append(f'{pad}<KeyFrameDouble{v} interpolationType="cubic"{fr} id="{self.new_id()}">')
                out.append(f'{pad}    <CubicEaseInterpolator x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" id="{self.new_id()}"/>')
                out.append(f"{pad}</KeyFrameDouble>")
        return out

    def _object(self, a, b, oid):
        """(first, last) line of the KeyedObject for oid inside animation lines a..b, or None."""
        pat = re.compile(r'^\s*<KeyedObject\b[^>]*\bobjectId="%s"' % re.escape(oid))
        for i in range(a, b):
            if pat.match(self.lines[i]):
                return i, self.end(i)
        return None

    def set_prop(self, anim_name, oid, prop, keys):
        """Replace (or create) the keys of one property of one object in one animation."""
        a, b = self.anim(anim_name)
        found = self._object(a, b, oid)
        if found is None:
            new = [f'            <KeyedObject objectId="{oid}" id="{self.new_id()}">', "            </KeyedObject>"]
            self.lines[b:b] = new
            found = (b, b + 1)
        i, j = found
        pat = re.compile(r'^\s*<KeyedProperty\b[^>]*\bproperty="%s"' % re.escape(prop))
        prop_at = next((k for k in range(i + 1, j) if pat.match(self.lines[k])), None)
        block = [f'                <KeyedProperty property="{prop}" id="{self.new_id()}">'] + self.key_lines(keys, " " * 20) + ["                </KeyedProperty>"]
        if prop_at is None:
            self.lines[j:j] = block
        else:
            self.lines[prop_at:self.end(prop_at) + 1] = block

    def drop_object(self, anim_name, oid):
        a, b = self.anim(anim_name)
        found = self._object(a, b, oid)
        if found:
            del self.lines[found[0]:found[1] + 1]

    def clear(self, anim_name):
        a, b = self.anim(anim_name)
        del self.lines[a + 1:b]

    def first_values(self, anim_name):
        """[(object id, property, value)] of each key list's first key (frame 0), read with an XML parser."""
        a, b = self.anim(anim_name)
        root = ET.fromstring("\n".join(self.lines[a:b + 1]))
        out = []
        for ko in root.findall("KeyedObject"):
            for kp in ko.findall("KeyedProperty"):
                keys = sorted(kp.findall("KeyFrameDouble"), key=lambda k: int(k.get("frame", 0)))
                out.append((ko.get("objectId"), kp.get("property"), float(keys[0].get("value", 0))))
        return out

    def rebuild_waiting(self, room):
        """The room's Waiting pose from its Intro's first keys, in the Intro's own order."""
        firsts = self.first_values(f"{room} Intro")
        self.clear(f"{room} Waiting")
        a, b = self.anim(f"{room} Waiting")
        by_obj = {}
        for oid, prop, v in firsts:
            by_obj.setdefault(oid, []).append((prop, v))
        new = []
        for oid, props in by_obj.items():
            new.append(f'            <KeyedObject objectId="{oid}" id="{self.new_id()}">')
            for prop, v in props:
                new.append(f'                <KeyedProperty property="{prop}" id="{self.new_id()}">')
                new += self.key_lines([(0, v, "hold")], " " * 20)
                new.append("                </KeyedProperty>")
            new.append("            </KeyedObject>")
        self.lines[b:b] = new


def bake(values, frames, tol=1e-3):
    """Keys for a per-frame curve: one linear key per frame, except inside a run of equal values only its two ends are kept.

    values: {frame: value} for every frame in `frames` (a range). Returns [(frame, value, "linear")]; a flat run ends on a hold."""
    fs = list(frames)
    keys = []
    for k, f in enumerate(fs):
        v = values[f]
        prev = values[fs[k - 1]] if k else None
        nxt = values[fs[k + 1]] if k + 1 < len(fs) else None
        if prev is not None and nxt is not None and abs(v - prev) < tol and abs(v - nxt) < tol:
            continue
        keys.append((f, v, "linear"))
    return keys
