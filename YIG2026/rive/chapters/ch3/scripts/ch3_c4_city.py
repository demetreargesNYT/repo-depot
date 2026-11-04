"""Shared writer for Chapter 4's living city (Demetre, 2026-11-04): one state machine layer and four animations per building.

A building script computes keys and hands them to add_building(); this module writes the animations and the layer. Used as:

    from ch3_c4_city import LOOP, WAKE, WAKE_AT, SEAM_OK, add_building, reserved, scene_path
    tracks = {"wake": {(oid, "rotation"): [(frame, value, how), ...]}, "loop": {...}, "calm": {...}}
    add_building(doc, "Tower", tracks)

For a building called NAME ("Tower"), add_building writes into the scene (all fps 60):
- "Chapter 4 City NAME Rest"  1 frame, oneShot: every tracked property at its resting value (the layer's start state)
- "Chapter 4 City NAME Wake"  WAKE frames, oneShot: the building's first move as the room settles (plays with the room's Intro)
- "Chapter 4 City NAME"        LOOP frames, loop: card 1 (reveal false), the whole motion
- "Chapter 4 City NAME Calm"   LOOP frames, loop: card 2 (reveal true), the same city more gently behind the ball
and the layer "Chapter 4 City NAME":
    Rest -> Wake (the room's first visit, with its Intro) | Loop or Calm directly (startScene, or arriving with Back; by reveal)
    Wake -> Loop (reveal false) | Calm (reveal true), on exit time
    Loop <-> Calm on reveal, a 1.45 s blend (the wall's fade), so the city never jumps when the card changes.

Keys are (frame, value, how); how is "hold", "linear" or one of rml_edit.EASES plus the ones this module adds: power1.out, power1.inOut, power2.in, power2.out, power2.inOut, power3.in, power3.out, power3.inOut, sine.in, sine.out, sine.inOut, expo.out, back.out, back.out.small (use eases, never linear, for anything that moves).
Rules it enforces (it stops with an assertion, writing nothing, when one fails):
- every tracked (object, property) is keyed by nothing else in the file (layers never key the same property);
- Rest values equal the first key of Loop and Calm; Loop and Calm end (frame LOOP) on the value they start on (frame 0);
- Wake starts at the rest value and ends (frame WAKE) on it.
Frame numbers: a track needs a key at frame 0 and at the last frame (WAKE or LOOP) to be a full track; a property that no beat moves
in a given animation may be left out of it (it then rests at its base value).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
from rml_edit import Doc, EASES
from rml_read import Scene, chapter_dir

FPS = 60
LOOP = 600            # frames: the city's loop, 10 s, the same as two of the fireworks' 300 frame loops
WAKE = 192            # frames: the Wake, as long as the room's Intro (3.2 s); a building's first move sits inside it
WAKE_AT = {           # when each building's first move begins inside the Wake, frame: left to right, 9 frames (0.15 s) apart,
    "Coss": 100,      # from 1.67 s, when the room has finished its pan; the last move is over by the end of the Wake
    "Dome": 109,
    "Tower": 118,
    "Connections": 127,
    "Strands": 136,
    "Hex": 145,
    "Cross": 154,
}
SEAM_OK = 1e-6
# more eases for the building scripts (rml_edit's own list is shared and stays as it is): importing this module adds them.
EASES.update({"power3.out": (0.215, 0.61, 0.355, 1), "power3.in": (0.55, 0.055, 0.675, 0.19), "power3.inOut": (0.645, 0.045, 0.355, 1),
              "expo.out": (0.16, 1, 0.3, 1), "sine.out": (0.61, 1, 0.88, 1), "sine.in": (0.12, 0, 0.39, 0),
              "back.out.small": (0.34, 1.25, 0.64, 1)})     # back.out.small: one small overshoot, then still
ROOM = "Chapter 4"
VM = "1:14"
SCENE_P, DIR_P, REVEAL_P, START_P = "1:2713", "1:2855", "1:3310", "1:3400"
CH4, BACK = "1:9102", "1:9201"


def scene_path(argv=None):
    """The scene to work on: --scene PATH, else the chapter's own."""
    argv = sys.argv if argv is None else argv
    return Path(argv[argv.index("--scene") + 1]) if "--scene" in argv else chapter_dir("ch3") / "scene.rml"


def reserved(scene):
    """{(object id, property key)}: everything any animation outside the city keys (the city must stay off these)."""
    import xml.etree.ElementTree as ET
    root = ET.parse(scene).getroot()
    out = set()
    for a in root.iter("LinearAnimation"):
        if a.get("name", "").startswith(f"{ROOM} City "):
            continue
        for ko in a.findall("KeyedObject"):
            for kp in ko.findall("KeyedProperty"):
                out.add((ko.get("objectId"), kp.get("property")))
    return out


def _cond_enum(n, prop, value):
    return [f'<TransitionViewModelCondition opValue="equal" id="{n()}">', f'    <TransitionPropertyViewModelComparator id="{n()}">',
            f'        <BindablePropertyEnum id="{n()}">', f'            <DataBindContext sourcePathIds="{VM}-{prop}" propertyKey="637" id="{n()}"/>',
            '        </BindablePropertyEnum>', '    </TransitionPropertyViewModelComparator>', f'    <TransitionValueEnumComparator value="{value}" id="{n()}"/>',
            '</TransitionViewModelCondition>']


def _cond_bool(n, prop, value):
    return [f'<TransitionViewModelCondition opValue="equal" id="{n()}">', f'    <TransitionPropertyViewModelComparator id="{n()}">',
            f'        <BindablePropertyBoolean id="{n()}">', f'            <DataBindContext sourcePathIds="{VM}-{prop}" propertyKey="634" id="{n()}"/>',
            '        </BindablePropertyBoolean>', '    </TransitionPropertyViewModelComparator>', f'    <TransitionValueBooleanComparator value="{value}" id="{n()}"/>',
            '</TransitionViewModelCondition>']


def check_tracks(name, tracks, taken):
    loop, calm, wake = tracks["loop"], tracks.get("calm", tracks["loop"]), tracks.get("wake", {})
    for label, group, end in (("loop", loop, LOOP), ("calm", calm, LOOP), ("wake", wake, WAKE)):
        for key, keys in group.items():
            assert key not in taken, f"{name}: {key} is keyed by something else already"
            frames = [k[0] for k in keys]
            assert frames == sorted(frames) and frames[0] == 0 and frames[-1] == end, f"{name} {label} {key}: keys must run from 0 to {end}"
            assert abs(keys[0][1] - keys[-1][1]) < SEAM_OK, f"{name} {label} {key}: first {keys[0][1]} and last {keys[-1][1]} differ"
    rest = {}
    for key, keys in loop.items():
        rest[key] = keys[0][1]
    for label, group in (("calm", calm), ("wake", wake)):
        for key, keys in group.items():
            if key in rest:
                assert abs(keys[0][1] - rest[key]) < SEAM_OK, f"{name} {label} {key}: starts on {keys[0][1]}, rest is {rest[key]}"
            else:
                rest[key] = keys[0][1]
    return rest


def add_building(doc, name, tracks):
    """Write the building's four animations and its layer into `doc` (not saved; the caller saves)."""
    scene = Scene(doc.path)
    taken = reserved(doc.path)
    rest = check_tracks(name, tracks, taken)
    n = doc.new_id
    loop_anim = next(e for e in scene.root.iter("LinearAnimation") if e.get("name") == f"{ROOM} Loop")
    li = doc.idx(loop_anim.get("id"))
    base = f"{ROOM} City {name}"
    spec = [("Rest", base + " Rest", 1, "oneShot", {k: [(0, v, "hold")] for k, v in rest.items()}),
            ("Wake", base + " Wake", WAKE, "oneShot", tracks.get("wake", {})),
            ("Loop", base, LOOP, "loop", tracks["loop"]),
            ("Calm", base + " Calm", LOOP, "loop", tracks.get("calm", tracks["loop"]))]
    aids, new = {}, []
    for key, nm, dur, lv, _ in spec:
        aids[key] = n()
        new += [f'        <LinearAnimation fps="60" duration="{dur}" loopValue="{lv}" name="{nm}" id="{aids[key]}">', "        </LinearAnimation>"]
    doc.lines[li:li] = new
    for key, nm, dur, lv, group in spec:
        for (oid, prop), keys in group.items():
            doc.set_prop(nm, oid, prop, keys)
    sid = {k: n() for k in ("Rest", "Wake", "Loop", "Calm")}

    def tr(to, conds=(), exit_time=False, ms=0):
        attrs = f' stateToId="{sid[to]}" duration="{ms}"'
        if exit_time:
            attrs += ' enableExitTime="true" exitTimeIsPercetange="true" exitTime="100"'
        if not conds:
            return [f'<StateTransition{attrs} id="{n()}"/>']
        body = [l for c in conds for l in c]
        return [f'<StateTransition{attrs} id="{n()}">'] + ["    " + l for l in body] + ["</StateTransition>"]
    on4 = lambda: _cond_enum(n, SCENE_P, CH4)
    rev = lambda v: _cond_bool(n, REVEAL_P, v)
    outs = {
        "Rest": tr("Calm", (on4(), rev("true"), _cond_enum(n, START_P, CH4))) + tr("Calm", (on4(), rev("true"), _cond_enum(n, DIR_P, BACK)))
                + tr("Loop", (on4(), rev("false"), _cond_enum(n, START_P, CH4))) + tr("Loop", (on4(), rev("false"), _cond_enum(n, DIR_P, BACK)))
                + tr("Wake", (on4(),)),
        "Wake": tr("Calm", (rev("true"),), exit_time=True) + tr("Loop", (rev("false"),), exit_time=True),
        "Loop": tr("Calm", (rev("true"),), ms=1450),
        "Calm": tr("Loop", (rev("false"),), ms=1450),
    }
    pad = " " * 16
    layer = [f'            <StateMachineLayer name="{base}" id="{n()}">', f'{pad}<AnyState x="160" y="200" id="{n()}"/>',
             f'{pad}<ExitState x="720" y="200" id="{n()}"/>', f'{pad}<EntryState x="0" y="0" id="{n()}">',
             f'{pad}    <StateTransition stateToId="{sid["Rest"]}" id="{n()}"/>', f'{pad}</EntryState>']
    for i, k in enumerate(("Rest", "Wake", "Loop", "Calm")):
        layer.append(f'{pad}<AnimationState animationId="{aids[k]}" x="{160 + 200 * i}" y="0" id="{sid[k]}">')
        layer += [pad + "    " + l for l in outs[k]]
        layer.append(f"{pad}</AnimationState>")
    layer.append("            </StateMachineLayer>")
    si = max(i for i, l in enumerate(doc.lines) if l.strip() == "</StateMachine>")
    doc.lines[si:si] = layer
    return rest
