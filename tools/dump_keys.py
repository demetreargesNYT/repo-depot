"""Print a chapter's timelines and state machine in spec notation.

    python3 tools/dump_keys.py ch2

Times are seconds, rotation degrees, colours #RRGGBB. In "a (ease) b", the ease
shapes the segment that ends at b; "hold" means the value does not change.
"""
import sys
from rml_read import Scene, chapter_dir, degrees

ORDER = ["Shelf Loop", "Shelf Outro", "Shelf Home", "Shelf Gone",
         "Wordle Waiting", "Wordle Intro", "Wordle Loop", "Wordle Outro", "Wordle Home", "Wordle Gone",
         "Connections Waiting", "Connections Intro", "Connections Loop", "Connections Outro", "Connections Home", "Connections Gone"]


def fmt_t(frame, fps):
    return (f"{frame / fps:.3f}".rstrip("0").rstrip(".")) or "0"


def fmt_v(prop, v):
    if isinstance(v, str):
        return "#" + ("%08X" % int(v, 16))[2:]
    if prop == "rotation":
        d = degrees(v)
        return f"{d:.0f}°" if abs(d - round(d)) < 0.05 else f"{d:.1f}°"
    return (f"{v:.3f}".rstrip("0").rstrip(".")) or "0"


def timeline(s, a):
    fps, dur = s.fps(a), s.duration(a)
    span = f"{dur} frame" + ("" if dur == 1 else f"s, {fmt_t(dur, fps)} s")
    print(f'\n## {a.get("name")}  ({span}, {a.get("loopValue", "oneShot")})')
    eases = s.eases(a)
    for (obj, prop), ks in s.keys(a).items():
        parts = []
        for i, (f, v) in enumerate(ks):
            txt = f"{fmt_t(f, fps)} {fmt_v(prop, v)}"
            if i:
                e = eases[(obj, prop)][i - 1]
                txt += " (hold)" if ks[i - 1][1] == v else f" ({e})"
            parts.append(txt)
        print(f"- {obj} {prop}: " + " · ".join(parts))


def state_machine(s):
    ab, sm = s.artboard, s.artboard.find("StateMachine")
    anim = {a.get("id"): a.get("name") for a in ab.iter("LinearAnimation")}
    props = {p.get("id"): p.get("name") for p in s.view_model if p.tag.startswith("ViewModelProperty")}
    print(f'\n## State machine "{sm.get("name")}"  (view model "{s.view_model.get("name")}": {", ".join(props.values())})')
    print("default state machine:", s.names.get(ab.get("defaultStateMachineId")))
    for layer in sm.findall("StateMachineLayer"):
        names = {st.get("id"): anim[st.get("animationId")] for st in layer.findall("AnimationState")}
        entry = layer.find("EntryState").find("StateTransition").get("stateToId")
        print(f'- layer "{layer.get("name")}": starts in {names[entry]}')
        for st in layer.findall("AnimationState"):
            for tr in st.findall("StateTransition"):
                conds = []
                for c in tr.findall("TransitionViewModelCondition"):
                    ctx = c.find(".//DataBindContext").get("sourcePathIds").split("-")[-1]
                    op = "==" if c.get("opValue", "equal") == "equal" else "!="
                    conds.append(f'{props[ctx]} {op} {c.find("TransitionValueNumberComparator").get("value", "0")}')
                gate = "at the end (exit time 100%)" if tr.get("enableExitTime") == "true" else "when " + " and ".join(conds)
                print(f'    {names[st.get("id")]} -> {names[tr.get("stateToId")]} {gate}, duration {tr.get("duration", "0")} ms')


def main(chapter):
    s = Scene(chapter_dir(chapter) / "scene.rml")
    ab = s.artboard
    print(f'Artboard "{ab.get("name")}" {ab.get("width")} x {ab.get("height")}, clip {ab.get("clip")}, '
          f'includeInExport {ab.get("includeInExport", "true")}')
    extra = set(s.animations) - set(ORDER)
    for n in ORDER + sorted(extra):
        if n in s.animations:
            timeline(s, s.animations[n])
    state_machine(s)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "ch2")
