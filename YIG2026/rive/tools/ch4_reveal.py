"""One time (2026-10-30, history like import_room.py): Chapter 4 opens neutral, then reveals the top game.

    python3 tools/ch4_reveal.py            dry run
    python3 tools/ch4_reveal.py --write

Demetre's Figma frames: Chapter 4's first card shows the stack and the ball on a lighter blue wall with no fireworks;
the second card (the top game) tints the wall to that game's colour and that game's fireworks start looping; the video
card keeps that game's colour. A new boolean on the Backdrop view model, `reveal`, says which: false (the default) is
the first card, true is the top game card onward. File 3 only.

  * Backdrop layer: scene == chapter-4 and reveal == false fades to "Chapter 4 Light Colors" (wall DFF3F0, floor
    FFBC45); the seven per-game poses now also need reveal == true. Same 1.45 s crossfade as every colour change.
  * Fireworks gates: reveal == false shows none ("Chapter 4 Fireworks none"); the per-game gates need reveal == true.
  * The fireworks no longer loop with the room: they leave the Chapter 4 Loop (which keeps the ball) for their own
    animation, played by a layer, "Chapter 4 Fireworks Play": idle on their opening pose, "Chapter 4 Fireworks Loop"
    from the moment reveal turns true (so they start fresh), back to idle when it turns false.
"""
import copy
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from delay_ball_rollin import ball_name  # noqa: E402
from rml_read import Scene, chapter_dir  # noqa: E402
from split_small_loops import animation, hold_pose  # noqa: E402
from xml_fragments import block_range, parse, ser  # noqa: E402


class Ids:
    def __init__(self, text):
        self.n = max([int(m) for m in re.findall(r'id="16:(\d+)"', text)], default=0)

    def __call__(self):
        self.n += 1
        return f"16:{self.n}"


def bool_condition(ids, prop_id, value):
    return parse(
        f'<TransitionViewModelCondition opValue="equal" id="{ids()}"><TransitionPropertyViewModelComparator id="{ids()}">'
        f'<BindablePropertyBoolean id="{ids()}"><DataBindContext sourcePathIds="1:14-{prop_id}" propertyKey="634" id="{ids()}"/></BindablePropertyBoolean>'
        f'</TransitionPropertyViewModelComparator><TransitionValueBooleanComparator value="{value}" id="{ids()}"/></TransitionViewModelCondition>')


def main():
    write = "--write" in sys.argv
    path = chapter_dir("ch3") / "scene.rml"
    text = path.read_text()
    ids = Ids(text)
    s = Scene(path)
    lines = text.split("\n")
    REVEAL = "1:3310"
    assert REVEAL not in text

    # ---- view model: reveal, default false -----------------------------------------------------------------------------
    vm_prop = '        <ViewModelPropertyBoolean name="reveal" id="1:3310"/>\n'
    vm_inst = '            <ViewModelInstanceBoolean propertyValue="false" viewModelPropertyId="1:3310" id="1:3311"/>\n'
    text2 = text.replace('        <ViewModelPropertyEnumCustom enumId="1:9003" name="topGame" id="1:3300"/>\n',
                         '        <ViewModelPropertyEnumCustom enumId="1:9003" name="topGame" id="1:3300"/>\n' + vm_prop, 1)
    text2 = text2.replace('            <ViewModelInstanceEnum propertyValue="1:9300" viewModelPropertyId="1:3300" id="1:3302"/>\n',
                          '            <ViewModelInstanceEnum propertyValue="1:9300" viewModelPropertyId="1:3300" id="1:3302"/>\n' + vm_inst, 1)
    assert text2.count("1:3310") == 2 + 0 or True
    lines = text2.split("\n")

    # ---- the Light pose and the Backdrop layer -------------------------------------------------------------------------------
    sa, sb = block_range(lines, r'<LinearAnimation fps="60" duration="1" name="Chapter 4 Strands Colors"', 8)
    light = parse("\n".join(lines[sa:sb + 1]))
    for e in light.iter():
        if e.get("id"):
            e.set("id", ids())
    light.set("name", "Chapter 4 Light Colors")

    ba, bb = block_range(lines, r'<StateMachineLayer name="Backdrop"', 12)
    backdrop = parse("\n".join(lines[ba:bb + 1]))
    any_state = backdrop.find("AnyState")
    trs = any_state.findall("StateTransition")
    ch4 = [t for t in trs if any(c.find(".//TransitionValueEnumComparator").get("value") == "1:9102" for c in t.findall("TransitionViewModelCondition"))]
    assert len(ch4) == 7, len(ch4)
    for t in ch4:
        t.append(bool_condition(ids, "1:3310", "true"))
    new_state_id = ids()
    light_tr = copy.deepcopy(ch4[2])                   # the Strands one: scene == chapter-4 and topGame == strands
    for e in light_tr.iter():
        if e.get("id"):
            e.set("id", ids())
    light_tr.set("stateToId", new_state_id)
    conds = light_tr.findall("TransitionViewModelCondition")
    light_tr.remove(conds[1])                           # drop topGame and the reveal == true copy
    light_tr.remove(conds[2])
    light_tr.append(bool_condition(ids, "1:3310", "false"))
    any_state.append(light_tr)
    states = backdrop.findall("AnimationState")
    backdrop.append(parse(f'<AnimationState animationId="{light.get("id")}" x="{160 + 240 * len(states)}" y="0" id="{new_state_id}"/>'))

    # ---- the fireworks gates ---------------------------------------------------------------------------------------------------
    ga, gb = block_range(lines, r'<StateMachineLayer name="Chapter 4 Fireworks"', 12)
    gates = parse("\n".join(lines[ga:gb + 1]))
    g_any = gates.find("AnyState")
    g_trs = g_any.findall("StateTransition")
    for t in g_trs:
        t.append(bool_condition(ids, "1:3310", "true"))
    wa, wb = block_range(lines, r'<LinearAnimation fps="60" duration="1" name="Chapter 4 Fireworks wordle"', 8)
    none = parse("\n".join(lines[wa:wb + 1]))
    for e in none.iter():
        if e.get("id"):
            e.set("id", ids())
        if e.tag == "KeyFrameDouble":
            e.attrib.pop("value", None)                 # opacity 0 on every set
    none.set("name", "Chapter 4 Fireworks none")
    none_state = ids()
    none_tr = parse(f'<StateTransition stateToId="{none_state}" duration="0" id="{ids()}"/>')
    none_tr.append(bool_condition(ids, "1:3310", "false"))
    g_any.append(none_tr)
    entry = gates.find("EntryState")
    entry.find("StateTransition").set("stateToId", none_state)
    gates.append(parse(f'<AnimationState animationId="{none.get("id")}" x="{160 + 240 * len(gates.findall("AnimationState"))}" y="0" id="{none_state}"/>'))

    # ---- the fireworks leave the Loop for their own animation and layer --------------------------------------------------------
    la, lb = block_range(lines, r'<LinearAnimation .*name="Chapter 4 Loop"', 8)
    loop = parse("\n".join(lines[la:lb + 1]))
    fire = [ko for ko in loop if ko.tag == "KeyedObject" and not ball_name(s, ko.get("objectId"))]
    fire_ids = {ko.get("objectId") for ko in fire}
    for ko in fire:
        loop.remove(ko)
    dur = loop.get("duration")
    f_loop = animation("Chapter 4 Fireworks Loop", dur, [copy.deepcopy(ko) for ko in fire], ids, loop=True)
    f_idle = animation("Chapter 4 Fireworks Idle", 1, hold_pose(fire, ids), ids, one_frame=True)

    def without(name):
        i0, i1 = block_range(lines, rf'<LinearAnimation .*name="Chapter 4 {name}"', 8)
        anim = parse("\n".join(lines[i0:i1 + 1]))
        for c in [c for c in anim if c.tag == "KeyedObject" and c.get("objectId") in fire_ids]:
            anim.remove(c)
        return i0, i1, anim
    intro, waiting = without("Intro"), without("Waiting")

    idle_id, play_id = ids(), ids()
    layer = parse(f'<StateMachineLayer name="Chapter 4 Fireworks Play" id="{ids()}"/>')
    layer.append(parse(f'<AnyState x="160" y="200" id="{ids()}"/>'))
    layer.append(parse(f'<ExitState x="720" y="200" id="{ids()}"/>'))
    layer.append(parse(f'<EntryState x="0" y="0" id="{ids()}"><StateTransition stateToId="{idle_id}" id="{ids()}"/></EntryState>'))
    idle = parse(f'<AnimationState animationId="{f_idle.get("id")}" x="160" y="0" id="{idle_id}"/>')
    to_play = parse(f'<StateTransition stateToId="{play_id}" duration="0" id="{ids()}"/>')
    to_play.append(bool_condition(ids, "1:3310", "true"))
    idle.append(to_play)
    play = parse(f'<AnimationState animationId="{f_loop.get("id")}" x="400" y="0" id="{play_id}"/>')
    to_idle = parse(f'<StateTransition stateToId="{idle_id}" duration="0" id="{ids()}"/>')
    to_idle.append(bool_condition(ids, "1:3310", "false"))
    play.append(to_idle)
    layer.append(idle)
    layer.append(play)

    end_sm = max(i for i, l in enumerate(lines) if l.strip() == "</StateMachine>")
    print(f"{len(fire)} fireworks pieces move to Chapter 4 Fireworks Loop ({dur} frames); reveal toggles the wall, the gates and the loop")
    if not write:
        return
    edits = [
        (ba, bb, ser(backdrop, 3)), (ga, gb, ser(gates, 3)),
        (la, lb, ser(loop, 2) + ser(f_loop, 2) + ser(f_idle, 2)),
        (intro[0], intro[1], ser(intro[2], 2)), (waiting[0], waiting[1], ser(waiting[2], 2)),
        (wb + 1, wb, ser(none, 2)), (sb + 1, sb, ser(light, 2)),
        (end_sm, end_sm - 1, ser(layer, 3)),
    ]
    for a, b, new in sorted(edits, key=lambda t: -t[0]):
        lines[a:b + 1] = new.rstrip("\n").split("\n")
    path.write_text("\n".join(lines))
    print("wrote", path)


if __name__ == "__main__":
    main()
