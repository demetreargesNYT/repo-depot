"""Print a chapter's timelines and state machine in spec notation, or keep a spec's listings in step with the file.

    python3 tools/dump_keys.py ch2                      print everything
    python3 tools/dump_keys.py ch2 --write SPEC.md      rewrite the listings in SPEC.md
    python3 tools/dump_keys.py ch2 --check SPEC.md      exit 1 if any listing in SPEC.md differs from the file

Times are seconds, rotation degrees, colours #RRGGBB. In "a (ease) b", the ease
shapes the segment that ends at b; "hold" means the value does not change.

A listing sits in the spec between markers, and is replaced as a whole:

    <!-- keys: Wordle Intro -->
    ```text
    ...
    ```
    <!-- /keys -->

The Waiting timelines have no listing: each one is, by rule, its intro's first
keys, and check_chapter.py verifies that.
"""
import re
import sys
from pathlib import Path
from rml_read import Scene, chapter_dir, degrees

MOVES = ['Outro', 'Home', 'Gone', 'Back Out', 'Right', 'Return', 'Forward In', 'On Top', 'Below']
ORDER = (["Shelf Loop"] + [f"Shelf {m}" for m in MOVES]
         + ["Wordle Waiting", "Wordle Intro", "Wordle Loop"] + [f"Wordle {m}" for m in MOVES]
         + ["Connections Waiting", "Connections Intro", "Connections Loop"] + [f"Connections {m}" for m in MOVES])
ORDER += [f"{g} Lockup {p}" for g in ("Wordle", "Connections") for p in ("Shown", "Hidden")]
STATE_MACHINE = "State machine"
MARKER = re.compile(r"(<!-- keys: (?P<name>.+?) -->\n```text\n)(?P<body>.*?)(\n```\n<!-- /keys -->)", re.S)


def fmt_t(frame, fps):
    return (f"{frame / fps:.3f}".rstrip("0").rstrip(".")) or "0"


def fmt_v(prop, v):
    if isinstance(v, str) and prop == "drawTargetId":
        return v
    if isinstance(v, str):
        return "#" + ("%08X" % int(v, 16))[2:]
    if prop == "rotation":
        d = degrees(v)
        return f"{d:.0f}°" if abs(d - round(d)) < 0.05 else f"{d:.1f}°"
    return (f"{v:.3f}".rstrip("0").rstrip(".")) or "0"


def timeline_lines(s, a):
    fps, dur = s.fps(a), s.duration(a)
    span = f"{dur} frame" + ("" if dur == 1 else f"s · {fmt_t(dur, fps)} s")
    head = f'{a.get("name")} · {span} · ' + ("loops" if a.get("loopValue", "oneShot") == "loop" else "plays once")
    out = [head]
    eases = s.eases(a)
    for (obj, prop), ks in s.keys(a).items():
        parts = []
        for i, (f, v) in enumerate(ks):
            txt = f"{fmt_t(f, fps)} {fmt_v(prop, v)}"
            if i:
                txt += " (hold)" if ks[i - 1][1] == v else f" ({eases[(obj, prop)][i - 1]})"
            parts.append(txt)
        out.append(f"{obj} {prop}: " + " · ".join(parts))
    return out


def state_machine_lines(s):
    ab, sm = s.artboard, s.artboard.find("StateMachine")
    anim = {a.get("id"): a.get("name") for a in ab.iter("LinearAnimation")}
    props = {p.get("id"): p.get("name") for p in s.view_model if p.tag.startswith("ViewModelProperty")}
    out = [f'State machine "{sm.get("name")}" · view model "{s.view_model.get("name")}": {", ".join(props.values())} · '
           f'default state machine: {s.names.get(ab.get("defaultStateMachineId"))}']
    for layer in sm.findall("StateMachineLayer"):
        # two states can play the same timeline (Home and Shown both play the Home pose); the second is numbered
        names, seen = {}, {}
        for st in layer.findall("AnimationState"):
            n = anim[st.get("animationId")]
            seen[n] = seen.get(n, 0) + 1
            names[st.get("id")] = n if seen[n] == 1 else f"{n} ({seen[n]})"
        entry = layer.find("EntryState").find("StateTransition").get("stateToId")
        out.append(f'layer "{layer.get("name")}": starts in {names[entry]}')
        sources = [(st, names[st.get("id")]) for st in layer.findall("AnimationState")] + [(a, "any state") for a in layer.findall("AnyState")]
        for st, src in sources:
            for tr in st.findall("StateTransition"):
                conds = []
                for c in tr.findall("TransitionViewModelCondition"):
                    ctx = c.find(".//DataBindContext").get("sourcePathIds").split("-")[-1]
                    op = "==" if c.get("opValue", "equal") == "equal" else "!="
                    num, flag = c.find("TransitionValueNumberComparator"), c.find("TransitionValueBooleanComparator")
                    value = num.get("value", "0") if num is not None else flag.get("value", "false")
                    conds.append(f'{props[ctx]} {op} {value}')
                gate = "at the end (exit time 100%)" if tr.get("enableExitTime") == "true" else "when " + " and ".join(conds)
                blend = f'{tr.get("duration", "0")} ms'
                c = tr.find("CubicEaseInterpolator")
                if c is not None:
                    blend += f" {s.eases_of(c)} blend"
                if tr.get("enableEarlyExit") == "true":
                    blend += ", early exit"
                out.append(f'  {src} -> {names[tr.get("stateToId")]} {gate}, {blend}')
    return out


def listings(s):
    """{listing name: text} for everything a spec embeds."""
    out = {n: "\n".join(timeline_lines(s, s.animations[n])) for n in ORDER if n in s.animations and not n.endswith("Waiting")}
    for n in sorted(set(s.animations) - set(ORDER)):
        out[n] = "\n".join(timeline_lines(s, s.animations[n]))
    out[STATE_MACHINE] = "\n".join(state_machine_lines(s))
    return out


def print_all(s):
    ab = s.artboard
    print(f'Artboard "{ab.get("name")}" {ab.get("width")} x {ab.get("height")}, clip {ab.get("clip")}, '
          f'includeInExport {ab.get("includeInExport", "true")}\n')
    for n in ORDER + sorted(set(s.animations) - set(ORDER)):
        if n in s.animations:
            print("\n".join(timeline_lines(s, s.animations[n])) + "\n")
    print("\n".join(state_machine_lines(s)))


def write_spec(s, spec, check):
    want, text = listings(s), spec.read_text()
    problems, found = [], set()

    def swap(m):
        name = m.group("name")
        found.add(name)
        if name not in want:
            problems.append(f"the spec has a listing for {name!r}, which is not in the file")
            return m.group(0)
        if m.group("body") != want[name]:
            problems.append(f"listing {name!r} no longer matches the file")
        return m.group(1) + want[name] + m.group(4)

    new = MARKER.sub(swap, text)
    missing = [f"the spec has no listing for {n!r}" for n in want if n not in found]
    if check:
        for p in problems + missing:
            print("FAIL  " + p)
        bad = problems + missing
        print(f"{len(found)} listings checked, {len(bad)} problem(s)" if bad else f"all {len(found)} listings match the file")
        return 1 if bad else 0
    spec.write_text(new)
    for p in missing:
        print("note: " + p)
    print(f"rewrote {len(found)} listings in {spec}")
    return 0


def main(argv):
    chapter = argv[0] if argv and not argv[0].startswith("--") else "ch2"
    s = Scene(chapter_dir(chapter) / "scene.rml")
    for mode in ("--write", "--check"):
        if mode in argv:
            return write_spec(s, Path(argv[argv.index(mode) + 1]), check=(mode == "--check"))
    print_all(s)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
