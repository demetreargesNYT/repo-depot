"""File 3's scenes get neutral names (Demetre, 2026-11-05): names describe position or data, never the illustrations.

    python3 chapters/ch3/scripts/ch3_scene_names.py --write [--scene PATH]      once

Old name         -> new name                      value id
  ad               ad-3                             1:9100   (File 3's empty Chapter 3 backdrop: Ad 3 plays here)
  chapter-3        chapter-3                        1:9101
  chapter-3-bird   chapter-3-2                      1:9104   (shares chapter-3's room, since ch3_bird_shared_room.py)
  (new)            chapter-3-personal-badges        1:9105   (shares ad-3's plain wall-and-floor picture)
  (new)            chapter-3-event-badges           1:9106   (same; the same scene again is a no-op, so anon's two in a row are seamless)
  chapter-4        chapter-4                        1:9102
  (new)            chapter-4-top-game               1:9107   (shares chapter-4's room)
  (new)            chapter-4-editor-video           1:9108   (shares chapter-4's room; the fireworks are off for the whole card)
  end              end                              1:9103
  (new)            share                            1:9109   (shares end's room, identical for now)

The enum values keep their ids, so every condition follows a rename by itself. For each room (or picture) that new scenes share,
every transition that waits for scene == <base> (and startScene == <base>) gets a twin per new scene, and every transition that leaves
on scene != <base> also requires scene != each new scene, in every state machine layer (the Backdrop's colour poses, the room's
layers, the city layers, the ball). A change between scenes of one group is a same-room change: nothing resets, nothing pans.
The scene enum is stored in flow order.

chapter-4-editor-video: the fireworks layer goes to its all-gates-off pose on this scene over 0.4 s (a burst in progress fades), and
the pose-to-game transitions for it are gone, so no new bursts show; the fireworks' loop keeps running underneath (the ball's hops stay
in step), and chapter-4-top-game fades the set back in over 0.25 s. The wall colour, the ball and the city carry straight through.
The manifest (chapter.json) is updated by the same script.
"""
import copy
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
from rml_edit import Doc
from rml_read import chapter_dir

SCENE_P, START_P = "1:2713", "1:3400"
NAMES = {"1:9100": "ad-3", "1:9101": "chapter-3", "1:9102": "chapter-4", "1:9103": "end", "1:9104": "chapter-3-2",
         "1:9105": "chapter-3-personal-badges", "1:9106": "chapter-3-event-badges", "1:9107": "chapter-4-top-game",
         "1:9108": "chapter-4-editor-video", "1:9109": "share"}
ORDER = ["1:9100", "1:9101", "1:9104", "1:9105", "1:9106", "1:9102", "1:9107", "1:9108", "1:9103", "1:9109"]
GROUPS = [("1:9100", ["1:9105", "1:9106"]), ("1:9102", ["1:9107", "1:9108"]), ("1:9103", ["1:9109"])]
TOP, VIDEO = "1:9107", "1:9108"
FADE_OUT_MS, FADE_IN_MS = 400, 250


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


def transition_blocks(doc, layer_id):
    start = doc.idx(layer_id)
    stop = doc.end(start)
    blocks, i = [], start
    while i <= stop:
        if doc.lines[i].lstrip().startswith("<StateTransition"):
            j = doc.end(i)
            blocks.append((i, j))
            i = j
        i += 1
    return blocks


def twin_layer(doc, layer_id, base, news):
    made = changed = 0
    for i, j in reversed(transition_blocks(doc, layer_id)):
        tr = ET.fromstring("\n".join(doc.lines[i:j + 1]))
        indent = len(doc.lines[i]) - len(doc.lines[i].lstrip())
        conds = [(c,) + cond_info(c) for c in tr.findall("TransitionViewModelCondition")]
        reads_scene = any(p == SCENE_P for _, p, op, comp in conds)
        boot_cut = (not reads_scene) and any(p == START_P and op == "equal" and comp.get("value") == base for _, p, op, comp in conds)
        if boot_cut or any(p == SCENE_P and op == "equal" and comp.get("value") == base for _, p, op, comp in conds):   # boot_cut: the Backdrop's Boot cuts on startScene alone
            out = []
            for new in news:
                twin = copy.deepcopy(tr)
                for c in twin.findall("TransitionViewModelCondition"):
                    p, op, comp = cond_info(c)
                    if p in (SCENE_P, START_P) and comp.get("value") == base:
                        comp.set("value", new)
                fresh_ids(twin, doc)
                out += serial(twin, indent)
            doc.lines[j + 1:j + 1] = out
            made += len(news)
        ne = next((c for c, p, op, comp in conds if p == SCENE_P and op == "notEqual" and comp.get("value") == base), None)
        if ne is not None:
            for new in news:
                extra = copy.deepcopy(ne)
                cond_info(extra)[2].set("value", new)
                fresh_ids(extra, doc)
                tr.append(extra)
            doc.lines[i:j + 1] = serial(tr, indent)
            changed += 1
    return made, changed


def rename_enum(doc):
    first = next(i for i, l in enumerate(doc.lines) if '<DataEnumCustom name="Scene"' in l)
    last = doc.end(first)
    pad = " " * 8
    doc.lines[first + 1:last] = [f'{pad}<DataEnumValue key="{NAMES[i]}" value="{NAMES[i]}" id="{i}"/>' for i in ORDER]


def fireworks_off_for_video(doc):
    root = ET.fromstring("\n".join(doc.lines))
    layer = next(l for l in root.iter("StateMachineLayer") if l.get("name") == "Chapter 4 Fireworks")
    layer_id = layer.get("id")
    removed = faded = 0
    none_block = None
    for i, j in reversed(transition_blocks(doc, layer_id)):
        tr = ET.fromstring("\n".join(doc.lines[i:j + 1]))
        conds = [cond_info(c) for c in tr.findall("TransitionViewModelCondition")]
        scenes = {comp.get("value") for p, op, comp in conds if p == SCENE_P and op == "equal"}
        if VIDEO in scenes:
            del doc.lines[i:j + 1]
            removed += 1
        elif TOP in scenes:
            tr.set("duration", str(FADE_IN_MS))
            doc.lines[i:j + 1] = serial(tr, len(doc.lines[i]) - len(doc.lines[i].lstrip()))
            faded += 1
    # a copy of the "everything off" move (reveal false) for scene == chapter-4-editor-video, with a 0.4 s blend
    root = ET.fromstring("\n".join(doc.lines))
    layer = next(l for l in root.iter("StateMachineLayer") if l.get("name") == "Chapter 4 Fireworks")
    anim = {a.get("id"): a.get("name") for a in root.iter("LinearAnimation")}
    states = {s.get("id"): anim.get(s.get("animationId")) for s in layer}
    for i, j in transition_blocks(doc, layer_id):
        tr = ET.fromstring("\n".join(doc.lines[i:j + 1]))
        if states.get(tr.get("stateToId")) == "Chapter 4 Fireworks none" and any(cond_info(c)[0] == "1:3310" for c in tr.findall("TransitionViewModelCondition")):
            none_block = (i, j, tr)
            break
    assert none_block, "the Fireworks none move is missing"
    i, j, tr = none_block
    off = copy.deepcopy(tr)
    off.set("duration", str(FADE_OUT_MS))
    scene_cond = None
    for k, c in enumerate(off.findall("TransitionViewModelCondition")):
        off.remove(c)
        scene_cond = c
    cond_template = next(c for tr2 in ET.fromstring("\n".join(doc.lines)).iter("StateTransition")
                         for c in tr2.findall("TransitionViewModelCondition") if cond_info(c)[0] == SCENE_P and cond_info(c)[1] == "equal")
    new_cond = copy.deepcopy(cond_template)
    cond_info(new_cond)[2].set("value", VIDEO)
    off.append(new_cond)
    fresh_ids(off, doc)
    doc.lines[j + 1:j + 1] = serial(off, len(doc.lines[i]) - len(doc.lines[i].lstrip()))
    return removed, faded


def badge_boot_cuts(doc):
    """The Backdrop's Boot state shows ad-3's colours already, so it had no cut for ad-3 itself; the badge scenes share those colours
    and get the same self-cut chapter-3 has (a copy of it), which the structure checks expect for every scene but the default."""
    root = ET.fromstring("\n".join(doc.lines))
    layer = next(l for l in root.iter("StateMachineLayer") if l.get("name") == "Backdrop")
    boot = layer.find("EntryState/StateTransition").get("stateToId")
    start = doc.idx(boot)
    stop = doc.end(start)
    for i, j in reversed(transition_blocks(doc, layer.get("id"))):
        if not (start < i < stop):
            continue
        tr = ET.fromstring("\n".join(doc.lines[i:j + 1]))
        vals = {(cond_info(c)[0], cond_info(c)[1], cond_info(c)[2].get("value")) for c in tr.findall("TransitionViewModelCondition")}
        if vals == {(SCENE_P, "equal", "1:9101"), (START_P, "equal", "1:9101")}:
            out = []
            for new in ("1:9105", "1:9106"):
                twin = copy.deepcopy(tr)
                for c in twin.findall("TransitionViewModelCondition"):
                    cond_info(c)[2].set("value", new)
                fresh_ids(twin, doc)
                out += serial(twin, len(doc.lines[i]) - len(doc.lines[i].lstrip()))
            doc.lines[j + 1:j + 1] = out
            return 2
    raise AssertionError("chapter-3's self-cut in the Backdrop's Boot state was not found")


def update_manifest(path):
    m = json.loads(path.read_text())
    m["properties"]["scene"]["default"] = "ad-3"
    m["properties"]["startScene"]["default"] = "ad-3"
    old = {"ad": "ad-3", "chapter-3-bird": "chapter-3-2"}
    base = {"chapter-3-personal-badges": "ad-3", "chapter-3-event-badges": "ad-3", "chapter-4-top-game": "chapter-4",
            "chapter-4-editor-video": "chapter-4", "share": "end"}
    by_name = {}
    for s in m["scenes"]:
        s["name"] = old.get(s["name"], s["name"])
        by_name[s["name"]] = s
    by_name["chapter-3-2"]["title"] = "Chapter 3, card 2 (the same room as chapter-3: the copy changes, the room keeps looping)"
    new = {
        "chapter-3-personal-badges": {"kind": "shared-picture", "sameRoomAs": "ad-3",
                                      "title": "Chapter 3, the personal badges (ad-3's plain wall and floor; no room of its own)"},
        "chapter-3-event-badges": {"kind": "shared-picture", "sameRoomAs": "ad-3",
                                   "title": "Chapter 3, the event badges (ad-3's plain wall and floor; anon shows it twice in a row, which is seamless because the same scene again does nothing)"},
        "chapter-4-top-game": {"kind": "shared-room", "sameRoomAs": "chapter-4", "title": "Chapter 4, the top game (chapter-4's room; reveal true: the game's wall, fireworks and the celebrating ball)"},
        "chapter-4-editor-video": {"kind": "shared-room", "sameRoomAs": "chapter-4", "fireworks": "off",
                                   "title": "Chapter 4, the editor's video (chapter-4's room, nothing resets; the fireworks fade out and stay off, and fade back in on chapter-4-top-game)"},
        "share": {"kind": "shared-room", "sameRoomAs": "end", "title": "Share (end's room, identical for now)"},
    }
    for name, entry in new.items():
        by_name[name] = {"name": name, **entry}
    order = [NAMES[i] for i in ORDER]
    m["scenes"] = [by_name[n] for n in order]
    for pose in m["poses"]:
        scenes = [old.get(n, n) for n in pose["scenes"]]
        for name, b in base.items():
            if b in scenes and name not in scenes:
                scenes.append(name)
        pose["scenes"] = sorted(scenes, key=order.index)
    t = m["tests"]
    t["flow"] = [old.get(n, n) for n in t["flow"]]
    path.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n")


def main(path):
    doc = Doc(path)
    assert not any('key="share"' in l for l in doc.lines), "already applied"
    rename_enum(doc)
    for base, news in GROUPS:
        root = ET.fromstring("\n".join(doc.lines))
        layers = [l.get("id") for l in root.iter("StateMachineLayer")]
        made = changed = 0
        for lid in layers:
            a, b = twin_layer(doc, lid, base, news)
            made, changed = made + a, changed + b
        print(f"  {NAMES[base]}: {made} twins for {[NAMES[n] for n in news]}, {changed} leaving transitions also require scene != each")
    print(f"  Backdrop Boot: {badge_boot_cuts(doc)} self-cuts for the badge scenes")
    removed, faded = fireworks_off_for_video(doc)
    print(f"  fireworks: {removed} video moves removed, {faded} top-game moves now blend {FADE_IN_MS} ms, video goes to the all-off pose over {FADE_OUT_MS} ms")
    doc.save()
    update_manifest(Path(path).parent / "chapter.json")
    print(f"wrote {path} and the manifest")


if __name__ == "__main__":
    if "--write" not in sys.argv:
        raise SystemExit(__doc__)
    main(Path(sys.argv[sys.argv.index("--scene") + 1]) if "--scene" in sys.argv else chapter_dir("ch3") / "scene.rml")
