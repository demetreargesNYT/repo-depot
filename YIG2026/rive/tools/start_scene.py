"""Add `startScene` (open a file directly on any of its scenes) and "Back into a room that was never shown" to a chapter.

    python3 tools/start_scene.py ch2

Written once per chapter (2026-11-03); it refuses to run on a file that already has startScene. The rules it builds:

* `startScene` is a second enum property on the Backdrop view model that shares the `Scene` enum, so its values are the scene
  values, in the same order. Its default is the file's default scene.
* A room that is still in Waiting when scene == startScene == the room goes straight to its Loop through "<Room> Built", a
  one-frame pose made from the last keys of its Intro (the room as it stands when its intro has finished). Its small loops
  go straight to their Loop. No intro, no pan, no lockup.
* The Backdrop layer opens in the start room's colours with no fade. Rive looks at AnyState rules before a state's own, so
  Entry leads to a Boot state that cuts to the start room's colours; the AnyState fade rules skip the start room
  (startScene != scene), and every colour state carries the fade to the start room's colours instead.
* A room still in Waiting (or Home, on its Exit layer) that is asked for with direction == back arrives built, from the left,
  exactly like a visited room coming back. This is what lets a file be mounted on the empty room it shares with its neighbour and
  then go Back into the last room of the file before it.
* File 3: Chapter 4's fireworks sets are chosen only while scene is chapter-4 (as in normal playback, where reveal turns true
  only there), so a file opened on another scene with reveal already true shows no fireworks.

* The Backdrop's Boot state keeps no cut for the file's default scene (boot_waits: the web runtime runs the machine once
  before onLoad, with the defaults; Boot waits on the default colours instead).

    python3 tools/start_scene.py ch3 --fireworks    only that step (added after the first run)
    python3 tools/start_scene.py ch2 --boot-waits   only that step (added after the first run)
"""
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from rml_read import chapter_dir

SCENE_PROP, DIRECTION_PROP, START_PROP = "1:2713", "1:2855", "1:3400"
START_INSTANCE = "1:3401"
BACK_VALUE = "1:9201"


class Edit:
    def __init__(self, path, again=False):
        self.path = Path(path)
        self.text = self.path.read_text()
        self.lines = self.text.split("\n")
        if again:       # a later step: new ids carry on after the ones the first run wrote
            self.n = max(int(i) for i in re.findall(r'id="20:(\d+)"', self.text))
            return
        assert "startScene" not in self.text, "startScene is already in this file"
        assert not re.search(r'id="20:', self.text) and START_PROP not in self.text
        self.n = 0

    def nid(self):
        self.n += 1
        return f"20:{self.n}"

    def save(self):
        self.path.write_text("\n".join(self.lines))

    def find(self, pattern, start=0):
        rx = re.compile(pattern)
        for i in range(start, len(self.lines)):
            if rx.search(self.lines[i]):
                return i
        raise KeyError(pattern)

    def close(self, i):
        line = self.lines[i]
        if line.rstrip().endswith("/>"):
            return i
        indent = len(line) - len(line.lstrip())
        tag = re.match(r"\s*<(\w+)", line).group(1)
        if tag == "StateTransition":        # never nested, and a few in the file are indented unevenly
            return next(j for j in range(i + 1, len(self.lines)) if self.lines[j].strip() == "</StateTransition>")
        for j in range(i + 1, len(self.lines)):
            if len(self.lines[j]) - len(self.lines[j].lstrip()) == indent and self.lines[j].lstrip().startswith(f"</{tag}>"):
                return j
        raise KeyError(line)

    def layer(self, name):
        i = self.find(r'<StateMachineLayer name="%s"' % re.escape(name))
        return i, self.close(i)

    def state_line(self, layer_range, sid):
        a, b = layer_range
        return self.find(r'<(AnimationState|EntryState)\b[^>]*\bid="%s"' % re.escape(sid), a)

    def anim(self, name):
        i = self.find(r'<LinearAnimation\b[^>]*\bname="%s"' % re.escape(name))
        return i, self.close(i)


def cond(e, prop, op, value, kind="enum", indent=24):
    p = " " * indent
    key, bind, cmp_ = (("637", "BindablePropertyEnum", "TransitionValueEnumComparator") if kind == "enum"
                       else ("634", "BindablePropertyBoolean", "TransitionValueBooleanComparator"))
    return [f'{p}<TransitionViewModelCondition opValue="{op}" id="{e.nid()}">',
            f'{p}    <TransitionPropertyViewModelComparator id="{e.nid()}">',
            f'{p}        <{bind} id="{e.nid()}">',
            f'{p}            <DataBindContext sourcePathIds="1:14-{prop}" propertyKey="{key}" id="{e.nid()}"/>',
            f'{p}        </{bind}>',
            f'{p}    </TransitionPropertyViewModelComparator>',
            f'{p}    <{cmp_} value="{value}" id="{e.nid()}"/>',
            f'{p}</TransitionViewModelCondition>']


def transition(e, to, conds, exit_time=False, indent=20):
    p = " " * indent
    if exit_time:
        return [f'{p}<StateTransition stateToId="{to}" duration="0" enableExitTime="true" exitTimeIsPercetange="true" exitTime="100" id="{e.nid()}"/>']
    out = [f'{p}<StateTransition stateToId="{to}" duration="0" id="{e.nid()}">']
    for c in conds:
        out += cond(e, *c, indent=indent + 4)
    return out + [f'{p}</StateTransition>']


def built_animation(e, room):
    """`<Room> Built`: one frame holding every key list of the Intro at its last key."""
    a, b = e.anim(f"{room} Intro")
    root = ET.fromstring("\n".join(e.lines[a:b + 1]))
    out = [f'        <LinearAnimation fps="60" duration="1" name="{room} Built" id="{e.nid()}">']
    for ko in root.findall("KeyedObject"):
        out.append(f'            <KeyedObject objectId="{ko.get("objectId")}" id="{e.nid()}">')
        for kp in ko.findall("KeyedProperty"):
            keys = [k for k in kp if k.tag.startswith("KeyFrame")]
            last = max(keys, key=lambda k: int(k.get("frame", 0)))
            value = f' value="{last.get("value")}"' if last.get("value") not in (None, "0") else ""
            out += [f'                <KeyedProperty property="{kp.get("property")}" id="{e.nid()}">',
                    f'                    <{last.tag}{value} frame="0" id="{e.nid()}"/>',
                    '                </KeyedProperty>']
        out.append("            </KeyedObject>")
    out.append("        </LinearAnimation>")
    return out


def first_scene_value(layer_el):
    """The scene value the layer's first "scene ==" condition waits for (Start's first rule is a "scene !=" one)."""
    for t in layer_el.iter("StateTransition"):
        for c in t.findall("TransitionViewModelCondition"):
            if c.find(".//DataBindContext").get("sourcePathIds") == f"1:14-{SCENE_PROP}" and c.get("opValue", "equal") == "equal":
                return c.find("TransitionValueEnumComparator").get("value")
    raise KeyError(layer_el.get("name"))


def main(ch):
    path = chapter_dir(ch) / "scene.rml"
    e = Edit(path)
    root = ET.parse(path).getroot()
    anims = {a.get("name"): a for a in root.iter("LinearAnimation")}
    layers = {l.get("name"): l for l in root.iter("StateMachineLayer")}
    names_by_id = {a.get("id"): a.get("name") for a in anims.values()}
    default_scene = next(v for v in root.iter("ViewModelInstanceEnum") if v.get("viewModelPropertyId") == SCENE_PROP).get("propertyValue")

    # work from the bottom of the file up so the line numbers found from the parsed copy stay true: gather the plan first
    plan = []       # (kind, layer name, ...)
    rooms = [n for n in layers if f"{n} Intro" in anims and f"{n} Waiting" in anims and f"{n} Exit" in layers]
    smalls = [n for n in layers if n.endswith(" Small") and f"{n} Waiting" in anims and f"{n} Loop" in anims]
    # File 1's Start has no Waiting state: it sits in the Loading bounce until its scene arrives
    special_start = "Start" in layers and not any(s.get("animationId") == (anims.get("Start Waiting").get("id") if "Start Waiting" in anims else None)
                                                  for s in layers["Start"])
    if special_start:
        rooms = [r for r in rooms if r != "Start"]

    def states(layer):
        return {s.get("id"): s for s in layer if s.tag in ("AnimationState", "EntryState")}

    def state_named(layer, anim_name):
        return [s.get("id") for s in layer if s.tag == "AnimationState" and names_by_id.get(s.get("animationId")) == anim_name]

    # the new animations first (placed after each room's Waiting), then the layers
    for room in rooms:
        a, b = e.anim(f"{room} Waiting")
        e.lines[b + 1:b + 1] = built_animation(e, room)
    if special_start:
        a, b = e.anim("Start Hidden")
        e.lines[b + 1:b + 1] = built_animation(e, "Start")

    def add_state_and_edit(room):
        layer = layers[room]
        n = first_scene_value(layer)
        waiting = state_named(layer, f"{room} Waiting")[0]
        intro_t = [t for t in layer.iter("StateTransition") if t.get("stateToId") in state_named(layer, f"{room} Intro")][0]
        loop = state_named(layer, f"{room} Loop")[0]
        built = e.nid()
        a, b = e.layer(room)
        # new state + its way on to the Loop, at the end of the layer
        e.lines[b:b] = [f'                <AnimationState animationId="{e.lines[e.anim(room + " Built")[0]].split(chr(34))[-2]}" x="160" y="240" id="{built}">'] \
            + transition(e, loop, [], exit_time=True) + ['                </AnimationState>']
        w = e.state_line((a, b), waiting)
        e.lines[w + 1:w + 1] = (transition(e, built, [(SCENE_PROP, "equal", n), (START_PROP, "equal", n)])
                                + transition(e, built, [(SCENE_PROP, "equal", n), (DIRECTION_PROP, "equal", BACK_VALUE)]))

    def edit_exit(room):
        layer = layers[f"{room} Exit"]
        n = first_scene_value(layers[room])
        entry = next(s for s in layer if s.tag == "EntryState")
        home = entry.find("StateTransition").get("stateToId")
        ret = state_named(layer, f"{room} Return")[0]
        shown = [t for t in layer.find(f"AnimationState[@id='{home}']").findall("StateTransition")][0].get("stateToId")
        a, b = e.layer(f"{room} Exit")
        h = e.state_line((a, b), home)
        e.lines[h + 1:h + 1] = (transition(e, shown, [(SCENE_PROP, "equal", n), (START_PROP, "equal", n)])
                                + transition(e, ret, [(SCENE_PROP, "equal", n), (DIRECTION_PROP, "equal", BACK_VALUE)]))

    def edit_small(small):
        layer = layers[small]
        room = small[:-len(" Small")]
        n = first_scene_value(layer)
        waiting = state_named(layer, f"{small} Waiting")[0]
        loop = state_named(layer, f"{small} Loop")[0]
        a, b = e.layer(small)
        w = e.state_line((a, b), waiting)
        back = [(SCENE_PROP, "equal", n), (DIRECTION_PROP, "equal", BACK_VALUE)]
        e.lines[w + 1:w + 1] = transition(e, loop, [(SCENE_PROP, "equal", n), (START_PROP, "equal", n)]) + transition(e, loop, back)

    for room in rooms:
        add_state_and_edit(room)
        edit_exit(room)
    for small in smalls:
        edit_small(small)

    if special_start:
        layer = layers["Start"]
        n = first_scene_value(layer)
        loading = state_named(layer, "Start Loading Loop")
        loop = state_named(layer, "Start Loop")[0]
        built = e.nid()
        a, b = e.layer("Start")
        anim_id = e.lines[e.anim("Start Built")[0]].split('"')[-2]
        e.lines[b:b] = [f'                <AnimationState animationId="{anim_id}" x="160" y="360" id="{built}">'] \
            + transition(e, loop, [], exit_time=True) + ['                </AnimationState>']
        for sid in loading:
            s = e.state_line((a, b), sid)
            e.lines[s + 1:s + 1] = (transition(e, built, [(SCENE_PROP, "equal", n), (START_PROP, "equal", n)])
                                    + transition(e, built, [(SCENE_PROP, "equal", n), (DIRECTION_PROP, "equal", BACK_VALUE)]))
        edit_exit("Start")

    # the Backdrop layer. Rive looks at AnyState rules before a state's own, so a cut to the start room's colours cannot sit
    # beside the AnyState fade to it. The fade rule skips the start room (startScene != scene); a Boot state, which Entry now
    # leads to, cuts to the start room's colours; every other colour state carries the fade for the start room.
    if "Backdrop" in layers:
        layer = layers["Backdrop"]
        anystate = layer.find("AnyState")
        entry = layer.find("EntryState")
        default_state = entry.find("StateTransition").get("stateToId")
        colour_states = [s for s in layer if s.tag == "AnimationState"]
        rules = []
        for t in anystate.findall("StateTransition"):
            conds, scene_val = [], None
            for c in t.findall("TransitionViewModelCondition"):
                path = c.find(".//DataBindContext").get("sourcePathIds").split("-")[1]
                if c.find("TransitionValueEnumComparator") is not None:
                    v, kind = c.find("TransitionValueEnumComparator").get("value"), "enum"
                else:
                    v, kind = c.find("TransitionValueBooleanComparator").get("value"), "bool"
                conds.append((path, c.get("opValue"), v, kind))
                if path == SCENE_PROP:
                    scene_val = v
            rules.append((t.get("id"), t.get("stateToId"), conds, scene_val))

        def fade(to, conds):
            out = [f'                    <StateTransition stateToId="{to}" duration="1450" interpolationType="cubic" enableEarlyExit="true" id="{e.nid()}">',
                   f'                        <CubicEaseInterpolator x1="0.45" y1="0" x2="0.55" y2="1" id="{e.nid()}"/>']
            for c in conds:
                out += cond(e, *c, indent=24)
            return out + ['                    </StateTransition>']

        # the fade rules built first (state-by-state), while the line numbers of the states are still those of the parsed copy
        a, b = e.layer("Backdrop")
        boot = e.nid()
        boot_anim = next(s.get("animationId") for s in colour_states if s.get("id") == default_state)
        for st in colour_states:
            h = e.state_line((a, b), st.get("id"))
            if e.lines[h].rstrip().endswith("/>"):
                e.lines[h:h + 1] = [e.lines[h].rstrip()[:-2].rstrip() + ">", " " * 16 + "</AnimationState>"]
            add = []
            for tid, target, conds, scene_val in rules:
                if target != st.get("id"):
                    add += fade(target, conds + [(START_PROP, "equal", scene_val, "enum")])
            e.lines[h + 1:h + 1] = add
            b += len(add) + (1 if not e.lines[h].rstrip().endswith("/>") and "</AnimationState>" in e.lines[h + 1 + len(add)] and False else 0)
            a, b = e.layer("Backdrop")
        # the existing fade rules skip the start room
        for tid, target, conds, scene_val in rules:
            t = e.find(r'<StateTransition\b[^>]*\bid="%s"' % re.escape(tid))
            close = e.close(t)
            e.lines[close:close] = cond(e, START_PROP, "notEqual", scene_val, indent=24)
        # Boot: a state like the default colours that cuts to the start room's colours
        a, b = e.layer("Backdrop")
        cut = []
        for tid, target, conds, scene_val in rules:
            if scene_val != default_scene:      # see boot_waits
                cut += transition(e, target, conds + [(START_PROP, "equal", scene_val, "enum")], indent=20)
        e.lines[b:b] = [f'                <AnimationState animationId="{boot_anim}" x="400" y="-200" id="{boot}">'] + cut + ["                </AnimationState>"]
        ent = e.state_line((a, b + len(cut) + 2), entry.get("id"))
        j = e.close(ent)
        assert 'stateToId="%s"' % default_state in "\n".join(e.lines[ent:j + 1])
        for k in range(ent, j + 1):
            e.lines[k] = e.lines[k].replace('stateToId="%s"' % default_state, 'stateToId="%s"' % boot)

    # the view model
    i = e.find(r'<ViewModelPropertyEnumCustom enumId="[^"]*" name="direction"')
    scene_prop = e.lines[e.find(r'<ViewModelPropertyEnumCustom enumId="[^"]*" name="scene"')]
    enum_id = re.search(r'enumId="([^"]*)"', scene_prop).group(1)
    props_end = e.find(r'<ViewModelInstance exports="true"')
    e.lines[props_end:props_end] = [f'        <ViewModelPropertyEnumCustom enumId="{enum_id}" name="startScene" id="{START_PROP}"/>']
    inst_end = e.find(r'</ViewModelInstance>', props_end)
    e.lines[inst_end:inst_end] = [f'            <ViewModelInstanceEnum propertyValue="{default_scene}" viewModelPropertyId="{START_PROP}" id="{START_INSTANCE}"/>']
    e.save()
    print(ch, "rooms:", len(rooms), "small:", len(smalls), "start:", special_start, "new ids:", e.n)
    fireworks(ch)


def boot_waits(ch):
    """Boot keeps no cut for the file's default scene. The web runtime (2.27.3) runs the state machine once before onLoad,
    while startScene and scene still hold their defaults: a cut for the default fired then, Boot was left, and the values
    onLoad sets arrived as an ordinary fade. Boot already shows the default scene's colours, so it simply waits for them."""
    path = chapter_dir(ch) / "scene.rml"
    root = ET.parse(path).getroot()
    layer = next((l for l in root.iter("StateMachineLayer") if l.get("name") == "Backdrop"), None)
    if layer is None:
        return
    default_scene = next(v for v in root.iter("ViewModelInstanceEnum") if v.get("viewModelPropertyId") == SCENE_PROP).get("propertyValue")
    boot = next(st for st in layer.findall("AnimationState") if st.get("id") == layer.find("EntryState/StateTransition").get("stateToId"))
    e = Edit(path, again=True)
    dropped = 0
    for tr in boot.findall("StateTransition"):
        vals = {(c.find(".//DataBindContext").get("sourcePathIds"), c.find("TransitionValueEnumComparator").get("value"))
                for c in tr.findall("TransitionViewModelCondition") if c.find("TransitionValueEnumComparator") is not None}
        if (f"1:14-{START_PROP}", default_scene) in vals:
            i = e.find(r'<StateTransition\b[^>]*\bid="%s"' % re.escape(tr.get("id")))
            del e.lines[i:e.close(i) + 1]
            dropped += 1
    e.save()
    print(ch, "Boot cuts dropped for the default scene:", dropped)


def fireworks(ch):
    """Chapter 4's fireworks sets: each AnyState rule that picks a set (topGame and reveal) also needs scene == chapter-4."""
    path = chapter_dir(ch) / "scene.rml"
    root = ET.parse(path).getroot()
    layer = next((l for l in root.iter("StateMachineLayer") if l.get("name") == "Chapter 4 Fireworks"), None)
    if layer is None:
        return
    names = [v.get("key") for v in next(e for e in root.iter("DataEnumCustom") if e.get("name") == "Scene") if v.tag == "DataEnumValue"]
    ids = [v.get("id") for v in next(e for e in root.iter("DataEnumCustom") if e.get("name") == "Scene") if v.tag == "DataEnumValue"]
    chapter_4 = ids[names.index("chapter-4")]
    e = Edit(path, again=True)
    done = 0
    for t in layer.find("AnyState").findall("StateTransition"):
        paths = [c.find(".//DataBindContext").get("sourcePathIds") for c in t.findall("TransitionViewModelCondition")]
        if f"1:14-{SCENE_PROP}" in paths or not any(p.endswith("1:3300") for p in paths):
            continue        # already has it, or the rule that hides every set (reveal false)
        i = e.find(r'<StateTransition\b[^>]*\bid="%s"' % re.escape(t.get("id")))
        close = e.close(i)
        e.lines[close:close] = cond(e, SCENE_PROP, "equal", chapter_4, indent=24)
        done += 1
    e.save()
    print(ch, "fireworks rules that now need scene == chapter-4:", done)


if __name__ == "__main__":
    if "--boot-waits" in sys.argv:
        boot_waits(sys.argv[1])
    elif "--fireworks" in sys.argv:
        fireworks(sys.argv[1])
    else:
        main(sys.argv[1])
