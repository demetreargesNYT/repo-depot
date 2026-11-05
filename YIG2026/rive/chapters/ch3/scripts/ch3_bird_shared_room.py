"""Chapter 3: the scene "chapter-3-bird" shows chapter-3's own room (Demetre, 2026-11-05); the Bird on Ball room is removed.

    python3 chapters/ch3/scripts/ch3_bird_shared_room.py --write [--scene PATH]      once

(The scene was renamed chapter-3-2 by ch3_scene_names.py the same day; this script's names are the ones it ran with.)
Chapter 1 copied the bird's loop into the Start card (commit 125b175), so nothing else needs the bird room. The scene name and the Scene
enum stay (engineering's scene list does not change); only what the file does with the value changes:
- the layers of Chapter 3's room (Chapter 3, Exit, Draw, Small) answer "chapter-3-bird" exactly as they answer "chapter-3": every
  transition that waits for scene == chapter-3 (and startScene == chapter-3) gets a twin for chapter-3-bird, and every transition that
  leaves the room on scene != chapter-3 also requires scene != chapter-3-bird. So chapter-3 to chapter-3-bird (and back) is a same-room
  change: the room keeps looping from wherever it is, no reset, no rebuild, no pan; arriving at chapter-3-bird directly builds the room as
  chapter-3 would, and startScene shows it built. (The Backdrop already mapped chapter-3-bird to Chapter 3's colours.)
- the Bird on Ball room is deleted: its Room node (art, draw rules, ball, bird), its four layers and its sixteen animations.
"""
import copy
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
from rml_edit import Doc
from rml_read import chapter_dir

SCENE_P, START_P = "1:2713", "1:3400"
CH3, BIRD = "1:9101", "1:9104"
LAYERS = ("Chapter 3", "Chapter 3 Exit", "Chapter 3 Draw", "Chapter 3 Small")
ROOM = "Bird on Ball"


def cond_info(c):
    path = next(d.get("sourcePathIds") for d in c.iter("DataBindContext")).split("-")[-1]
    comp = next(e for e in c.iter() if e.tag.startswith("TransitionValue"))
    return path, c.get("opValue"), comp


def fresh_ids(elem, doc):
    for e in elem.iter():
        if e.get("id"):
            e.set("id", doc.new_id())


def serial(elem, indent):
    ET.indent(elem, space="    ")
    return [" " * indent + line for line in ET.tostring(elem, encoding="unicode").split("\n")]


def twin_layer(doc, layer_name):
    root = ET.fromstring("\n".join(doc.lines))
    layer = next(l for l in root.iter("StateMachineLayer") if l.get("name") == layer_name)
    start = doc.idx(layer.get("id"))
    stop = doc.end(start)
    blocks = []
    i = start
    while i <= stop:
        if doc.lines[i].lstrip().startswith("<StateTransition"):
            j = doc.end(i)
            blocks.append((i, j))
            i = j
        i += 1
    made = changed = 0
    for i, j in reversed(blocks):
        tr = ET.fromstring("\n".join(doc.lines[i:j + 1]))
        indent = len(doc.lines[i]) - len(doc.lines[i].lstrip())
        conds = [(c,) + cond_info(c) for c in tr.findall("TransitionViewModelCondition")]
        if any(p == SCENE_P and op == "equal" and comp.get("value") == CH3 for _, p, op, comp in conds):
            twin = copy.deepcopy(tr)
            for c in twin.findall("TransitionViewModelCondition"):
                p, op, comp = cond_info(c)
                if p in (SCENE_P, START_P) and comp.get("value") == CH3:
                    comp.set("value", BIRD)
            fresh_ids(twin, doc)
            doc.lines[j + 1:j + 1] = serial(twin, indent)
            made += 1
        ne = next((c for c, p, op, comp in conds if p == SCENE_P and op == "notEqual" and comp.get("value") == CH3), None)
        if ne is not None:
            extra = copy.deepcopy(ne)
            cond_info(extra)[2].set("value", BIRD)
            fresh_ids(extra, doc)
            tr.append(extra)
            doc.lines[i:j + 1] = serial(tr, indent)
            changed += 1
    return made, changed


def remove_room(doc):
    root = ET.fromstring("\n".join(doc.lines))
    room = next(e for e in root.iter("Node") if e.get("name") == f"{ROOM} Room")
    targets = [room] + [l for l in root.iter("StateMachineLayer") if (l.get("name") or "").startswith(ROOM)] \
        + [a for a in root.iter("LinearAnimation") if (a.get("name") or "").startswith(ROOM)]
    ids = {e.get("id") for t in targets for e in t.iter() if e.get("id")}
    for t in targets:
        i = doc.idx(t.get("id"))
        del doc.lines[i:doc.end(i) + 1]
    text = "\n".join(doc.lines)
    left = sorted(x for x in ids if f'"{x}"' in text)
    assert not left, f"still referenced after removing the bird room: {left}"
    return len(targets), len(ids)


def main(path):
    doc = Doc(path)
    assert any(f'name="{ROOM} Room"' in l for l in doc.lines), "the Bird on Ball room is already gone"
    for name in LAYERS:
        made, changed = twin_layer(doc, name)
        print(f"  {name}: {made} twins for chapter-3-bird, {changed} leaving transitions also require scene != chapter-3-bird")
    n, ids = remove_room(doc)
    doc.save()
    print(f"wrote {path}: removed the {ROOM} room ({n} elements: room, layers, animations; {ids} ids)")


if __name__ == "__main__":
    if "--write" not in sys.argv:
        raise SystemExit(__doc__)
    main(Path(sys.argv[sys.argv.index("--scene") + 1]) if "--scene" in sys.argv else chapter_dir("ch3") / "scene.rml")
