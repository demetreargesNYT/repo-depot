"""Check a chapter's scene.rml against the structure the spec describes.

    python3 tools/check_chapter.py ch2

Exits 1 if anything fails. `npm run deliver` runs this first.
"""
import sys
from rml_read import Scene, chapter_dir

INTRO_FRAMES = 192    # 3.2 s at 60 fps; the text CSS waits exactly this long
OUTRO_FRAMES = 96     # 1.6 s
ARTBOARD = (1495, 1067)
START_SCENE = 9                  # the empty Chapter 1 room File 2 opens on: colours only, no room
START_COLORS = "Chapter 1 Colors"
TOL = 1e-4

results = []


def check(ok, text):
    results.append((ok, text))


def same(a, b):
    if isinstance(a, str) or isinstance(b, str):
        return a == b
    return abs(a - b) <= TOL


def rooms_of(s):
    """Rooms are the animations named '<Room> Intro' (the opener has none, so Shelf is found by its Outro)."""
    return sorted({n.rsplit(" ", 1)[0] for n in s.animations if n.endswith((" Intro", " Outro"))})


def first_values(s, anim):
    return {k: ks[0][1] for k, ks in s.keys(anim).items()}


def last_values(s, anim):
    return {k: ks[-1][1] for k, ks in s.keys(anim).items()}


def state_names(s, layer):
    """{state id: name}, numbering a timeline's second state the way the key dump does ("Home (2)")."""
    names, seen = {}, {}
    for st in layer.findall("AnimationState"):
        n = s.names[st.get("animationId")]
        seen[n] = seen.get(n, 0) + 1
        names[st.get("id")] = n if seen[n] == 1 else f"{n} ({seen[n]})"
    return names


def start_of(s, layer):
    return state_names(s, layer).get(layer.find("EntryState/StateTransition").get("stateToId"))


def layer_moves(s, layer):
    """[(from, to, conditions or "end", duration ms, power2.inOut blend with early-exit-free cubic)]"""
    props = {p.get("id"): p.get("name") for p in s.view_model if p.tag.startswith("ViewModelProperty")}
    names = state_names(s, layer)
    out = []
    for st in layer.findall("AnimationState"):
        for tr in st.findall("StateTransition"):
            conds = []
            for c in tr.findall("TransitionViewModelCondition"):
                prop = props[c.find(".//DataBindContext").get("sourcePathIds").split("-")[-1]]
                op = "==" if c.get("opValue", "equal") == "equal" else "!="
                conds.append((prop, op, int(float(c.find("TransitionValueNumberComparator").get("value", "0")))))
            gate = "end" if tr.get("enableExitTime") == "true" and not conds else tuple(sorted(conds))
            c = tr.find("CubicEaseInterpolator")
            blend = tr.get("interpolationType") == "cubic" and c is not None and s.eases_of(c) == "power2.inOut"
            out.append((names[st.get("id")], names[tr.get("stateToId")], gate, tr.get("duration", "0"), blend))
    return out


def run(chapter):
    results.clear()          # run() may be called more than once in a process
    s = Scene(chapter_dir(chapter) / "scene.rml")
    ab, A = s.artboard, s.animations
    rooms = rooms_of(s)

    # artboard
    check((int(ab.get("width")), int(ab.get("height"))) == ARTBOARD, f'artboard is {ab.get("width")} x {ab.get("height")} (want {ARTBOARD[0]} x {ARTBOARD[1]})')
    check(ab.get("clip") == "true", "artboard clips its content")
    check(ab.get("includeInExport", "true") != "false", "artboard is included in the export (includeInExport is not false)")

    # state machine and view model
    sm = ab.find("StateMachine")
    check(sm is not None and s.names.get(ab.get("defaultStateMachineId")) == sm.get("name"), "the state machine is the artboard's default, so it plays on load")
    props = {p.get("name"): p for p in s.view_model if p.tag == "ViewModelPropertyNumber"}
    check("scene" in props, 'the view model has a number property named "scene"')
    check("direction" in props, 'the view model has a number property named "direction" (1 Next, -1 Back)')
    dflt = next((v.get("propertyValue", "0") for v in s.view_model.iter("ViewModelInstanceNumber") if "direction" in props and v.get("viewModelPropertyId") == props["direction"].get("id")), None)
    check(dflt == "1", f"direction defaults to 1 (Next), so a file loaded without our integration code behaves as before (it is {dflt})")
    numbers = s.scene_numbers()
    layers = {l.get("name") for l in sm.findall("StateMachineLayer")}
    for room in rooms:
        check(room in layers and f"{room} Exit" in layers, f'layers "{room}" and "{room} Exit" exist' if room != "Shelf" else 'layers "Shelf" and "Shelf Exit" exist')
    vals = [v for k, v in numbers.items() if not k.endswith("Exit") or True]
    per_room = {r: numbers.get(r, numbers.get(f"{r} Exit")) for r in rooms}
    check(len(set(per_room.values())) == len(per_room), f"each room waits for its own scene value: {per_room}")

    # backdrop: one shared Background (wall, floor, floor line) under every room; its colours change by crossfade
    bg = s.node("Background")
    container = s.parent[bg]
    siblings = [c.get("name") for c in container if c.tag == "Node"]
    # draw order: the first child draws on top, so the Background must be the last child to sit under every room
    check(siblings[-1] == "Background", f"Background is the last child of {container.get('name')}, so it draws under every room (children: {siblings})")
    shapes = {sh.get("name"): sh for sh in bg if sh.tag == "Shape"}
    check(set(shapes) == {"Wall", "Floor", "Floor-Line"}, f"Background holds the Wall, Floor and Floor-Line shapes (has {sorted(shapes)})")
    for name in ("Wall", "Floor"):
        sh = shapes.get(name)
        check(sh is not None and sh.find("Stroke") is None and sh.find("Fill") is not None, f"Background {name} is a fill with no stroke on its edges")
    edged = sorted(n.get("name") for n in ab.iter("Node") if (n.get("name") or "").endswith(" Backdrop"))
    check(not edged, "no room has a backdrop of its own (rooms carry art only; a room backdrop slides a hard edge across the stage)" + ("" if not edged else f": {edged}"))
    colour_ids = {name: shapes[name].find("Fill").find("SolidColor").get("id") for name in ("Wall", "Floor") if name in shapes}
    base_wall = shapes["Wall"].find("Fill").find("SolidColor").get("colorValue") if "Wall" in shapes else None
    layer = next((l for l in sm.findall("StateMachineLayer") if l.get("name") == "Backdrop"), None)
    check(layer is not None, 'the state machine has a "Backdrop" layer')
    if layer is not None:
        anys = layer.findall("AnyState")
        trs = anys[0].findall("StateTransition") if len(anys) == 1 else []
        state_anim = {st.get("id"): s.names.get(st.get("animationId")) for st in layer.findall("AnimationState")}
        targets = {}
        for tr in trs:
            cond = tr.find("TransitionViewModelCondition")
            n = int(float(cond.find("TransitionValueNumberComparator").get("value", "0"))) if cond is not None and cond.get("opValue", "equal") == "equal" else None
            targets[n] = state_anim.get(tr.get("stateToId"))
            c = tr.find("CubicEaseInterpolator")
            ease = s.eases_of(c) if c is not None else None
            check(tr.get("duration") == "1450" and tr.get("interpolationType") == "cubic" and ease == "power1.inOut",
                  f"Backdrop fade to {targets[n]} blends over 1450 ms, power1.inOut (duration {tr.get('duration')}, ease {ease})")
            # without early exit a tap during a fade waits for that fade to finish, so the wall reaches the old
            # room's colour first and the new room arrives on it; with it the fade turns from the colour on screen
            check(tr.get("enableEarlyExit") == "true", f"Backdrop fade to {targets[n]} can be interrupted (enableEarlyExit), so a tap mid-fade turns from the colour on screen")
        want_rooms = {per_room[r]: f"{r} Colors" for r in rooms}
        check(all(targets.get(n) == name for n, name in want_rooms.items()),
              f"Backdrop's AnyState sends each room's scene value to its own Colors (want {want_rooms}, has {targets})")
        # a scene with no animated room (an ad, a chapter handoff) may still have a Colors pose of its own: the
        # shared backdrop crossfades to it like any room's, but there is no "<label> Room" node to go with it
        extra = {n: name for n, name in targets.items() if n not in want_rooms}
        for n, name in extra.items():
            label = name.rsplit(" Colors", 1)[0]
            check(n not in per_room.values() and not any(e.get("name") == f"{label} Room" for e in ab.iter("Node")),
                  f"scene {n}'s {name} is a shared-backdrop-only scene (no {label} Room of its own)")
        entry = layer.find("EntryState/StateTransition")
        check(entry is not None and state_anim.get(entry.get("stateToId")) == START_COLORS, f"Backdrop starts on {START_COLORS}")
    colors_names = sorted(set(targets.values())) if layer is not None else [f"{room} Colors" for room in rooms]
    for name in colors_names:
        a = A.get(name)
        check(a is not None, f'"{name}" timeline exists')
        if a is None:
            continue
        ks = s.keys(a)
        check(s.duration(a) == 1 and set(ks) == {("Wall colour", "colorValue"), ("Floor colour", "colorValue")} and all(len(v) == 1 for v in ks.values()),
              f"{name} is one frame holding only the Background's wall and floor colours")
    # the base colour on load is the start scene's (the empty Chapter 1 room), so nothing flashes before the Backdrop layer's first frame
    start = A.get(START_COLORS)
    if start is not None and base_wall:
        held = s.keys(start)[("Wall colour", "colorValue")][0][1]
        check(held.upper() == base_wall.upper(), f"the Background's own wall colour ({base_wall}) is {START_COLORS}'s ({held})")
        want_start = {"Wall colour": "FFF1ECC0", "Floor colour": "FFFF811E"}
        got_start = {o: ks[0][1].upper() for (o, _p), ks in s.keys(start).items()}
        check(got_start == want_start, f"{START_COLORS} is the cream wall F1ECC0 and orange floor FF811E File 1 ends on ({got_start})")
        dflt_scene = next((v.get("propertyValue", "0") for v in s.view_model.iter("ViewModelInstanceNumber") if v.get("viewModelPropertyId") == props["scene"].get("id")), None)
        check(dflt_scene == str(START_SCENE), f"the file starts on scene {START_SCENE}, the empty Chapter 1 room, with no room of its own (scene defaults to {dflt_scene})")
    # only the Colors timelines may key the Background, or two layers would fight over its colours
    for name, a in A.items():
        if not name.endswith(" Colors"):
            bad = sorted({o for (o, _p) in s.keys(a) if o in ("Wall colour", "Floor colour", "Background", "Wall", "Floor", "Floor-Line")})
            check(not bad, f"{name} does not key the Background" + ("" if not bad else f": {bad}"))

    for room in rooms:
        kids = [c.get("name") for c in s.node(f"{room} Room") if c.tag == "Node"]
        check(f"{room} Wall Lag" in kids, f"{room} Room holds a {room} Wall Lag wrapper")

        # the moves key only the room and its wall lag; the draw rule is the Draw layer's alone
        outro = A[f"{room} Outro"]
        rules = f"{room} Draw Rules"
        moves = ("Outro", "Home", "Gone", "Back Out", "Right", "Return", "Forward In")
        for pose in moves:
            a = A.get(f"{room} {pose}")
            check(a is not None and set(s.keys(a)) == {(f"{room} Room", "x"), (f"{room} Wall Lag", "x")},
                  f"{room} {pose} keys only {room} Room x and {room} Wall Lag x")
        for name, a in A.items():
            if name not in (f"{room} On Top", f"{room} Below"):
                check((rules, "drawTargetId") not in s.keys(a), f"{name} does not key {rules}")

        # the leaving room draws below the arriving room, in either direction: the "<Room> Draw" layer holds the
        # rule on Top while scene == n and on Bottom otherwise, and Top sits above every room
        for pose, target in (("On Top", f"{room} Top"), ("Below", f"{room} Bottom")):
            ks = s.keys(A[f"{room} {pose}"]).get((rules, "drawTargetId"), []) if f"{room} {pose}" in A else []
            check(len(ks) == 1 and ks[0][1] == target and s.duration(A[f"{room} {pose}"]) == 1,
                  f"{room} {pose} is a one-frame pose putting the room's draw rule on {target.split()[-1]}")
        tops = {t.get("name"): s.names.get(t.get("drawableId")) for t in s.node(f"{room} Room").find("DrawRules")}
        check(tops.get(f"{room} Top") == "Top Marker", f"{room} Top is placed at the Top Marker, above every room (it is at {tops.get(f'{room} Top')})")
        n = per_room[room]
        dl = next((l for l in sm.findall("StateMachineLayer") if l.get("name") == f"{room} Draw"), None)
        got = sorted(layer_moves(s, dl)) if dl is not None else []
        want = sorted([(f"{room} Below", f"{room} On Top", ((("scene", "==", n),)), "0", False),
                       (f"{room} On Top", f"{room} Below", ((("scene", "!=", n),)), "0", False)])
        check(got == want and start_of(s, dl) == f"{room} Below", f'layer "{room} Draw" starts Below and goes On Top exactly while scene == {n}, at once')

        check(s.duration(outro) == OUTRO_FRAMES, f"{room} Outro is {OUTRO_FRAMES} frames (1.6 s)")
        for pose in ("Home", "Gone", "Right"):
            check(s.duration(A[f"{room} {pose}"]) == 1, f"{room} {pose} is a one-frame pose")

        # Back mirrors Next: every move is the Outro's pan (0.05 -> 1.55 s, power2.inOut), and the right-hand side
        # mirrors the left (room x +1600 for -1600, the lag negated)
        def track(pose, obj):
            return s.keys(A[f"{room} {pose}"])[(f"{room} {obj}", "x")]
        o_keys = {obj: track("Outro", obj) for obj in ("Room", "Wall Lag")}
        L = o_keys["Wall Lag"][-1][1]
        mirror = {"Back Out": {"Room": (0, 1600), "Wall Lag": (0, -L)}, "Return": {"Room": (-1600, 0), "Wall Lag": (L, 0)},
                  "Forward In": {"Room": (1600, 0), "Wall Lag": (-L, 0)}}
        for pose, objs in mirror.items():
            a = A[f"{room} {pose}"]
            for obj, (v0, v1) in objs.items():
                ks = track(pose, obj)
                frames_ok = [f for f, _ in ks] == [f for f, _ in o_keys[obj]]
                eases_ok = s.eases(a)[(f"{room} {obj}", "x")][:1] == (["hold"] if v0 == v1 else ["power2.inOut"])
                check(s.duration(a) == OUTRO_FRAMES and frames_ok and eases_ok and same(ks[0][1], v0) and same(ks[-1][1], v1),
                      f"{room} {pose} moves {room} {obj} x {v0:g} -> {v1:g} on the Outro's pan ({[(f, v) for f, v in ks]})")
        check(same(track("Right", "Room")[0][1], 1600) and same(track("Right", "Wall Lag")[0][1], -L),
              f"{room} Right holds the room at x 1600, the lag at {-L:g}, where Back Out ends")

        # the exit layer: every move starts from a held pose, except a Next during a Forward In, which blends on
        # from the plain timeline (continuous); a Back during any pan, or a Next during a Back pan, waits in the
        # integration file
        el = next(l for l in sm.findall("StateMachineLayer") if l.get("name") == f"{room} Exit")
        S, N, B = ("scene", "==", n), ("scene", "!=", n), ("direction", "==", -1)
        F = ("direction", "!=", -1)
        R = lambda p: f"{room} {p}"
        want = sorted([
            (R("Home"), R("Home (2)"), (S,), "0", False),
            (R("Home (2)"), R("Outro"), (N, F), "0", False),
            (R("Home (2)"), R("Back Out"), (N, B), "0", False),
            (R("Outro"), R("Gone"), "end", "0", False),
            (R("Gone"), R("Return"), (S,), "0", False),
            (R("Back Out"), R("Right"), "end", "0", False),
            (R("Right"), R("Forward In"), (S,), "0", False),
            (R("Return"), R("Home (2)"), "end", "0", False),
            (R("Forward In"), R("Outro"), (N, F), "1550", True),
            (R("Forward In"), R("Home (2)"), "end", "0", False),
        ])
        want = sorted((a, b, g if g == "end" else tuple(sorted(g)), d, bl) for a, b, g, d, bl in want)
        got = sorted(layer_moves(s, el))
        check(got == want, f'layer "{room} Exit" has exactly the Next and Back moves' + ("" if got == want else f"; extra {sorted(set(got) - set(want))}, missing {sorted(set(want) - set(got))}"))
        start = start_of(s, el)
        check(start == R("Home"), f'layer "{room} Exit" starts in {start}')
        # the outro must end exactly where the Gone pose holds the room, and that must be off the artboard (the
        # room's art reaches at most 1600 right of its origin), or the hand-over from Outro to Gone would jump
        o_end = s.keys(outro)[(f"{room} Room", "x")][-1][1]
        g_end = s.keys(A[f"{room} Gone"])[(f"{room} Room", "x")][0][1]
        check(same(o_end, g_end) and g_end <= -1600, f"{room} Outro ends at {room} Room x {o_end:g}, where {room} Gone holds it ({g_end:g}); that clears the artboard")
        o_lag = s.keys(outro)[(f"{room} Wall Lag", "x")][-1][1]
        g_lag = s.keys(A[f"{room} Gone"])[(f"{room} Wall Lag", "x")][0][1]
        check(same(o_lag, g_lag), f"{room} Outro ends at {room} Wall Lag x {o_lag:g}, where {room} Gone holds it ({g_lag:g})")

    # rooms with an intro
    for room in [r for r in rooms if f"{r} Intro" in A]:
        intro, wait, loop = A[f"{room} Intro"], A[f"{room} Waiting"], A[f"{room} Loop"]
        check(s.duration(intro) == INTRO_FRAMES and s.fps(intro) == 60, f"{room} Intro is exactly {INTRO_FRAMES} frames at 60 fps (3.2 s)")
        check(intro.get("loopValue", "oneShot") == "oneShot", f"{room} Intro plays once")
        check(loop.get("loopValue") == "loop", f"{room} Loop loops")

        # each Waiting pose equals the intro's first keys
        i_first, w_first = first_values(s, intro), first_values(s, wait)
        missing = sorted(set(i_first) - set(w_first))
        extra = sorted(set(w_first) - set(i_first))
        wrong = sorted(k for k in i_first if k in w_first and not same(i_first[k], w_first[k]))
        check(s.duration(wait) == 1, f"{room} Waiting is a one-frame pose")
        check(not (missing or extra or wrong),
              f"{room} Waiting equals {room} Intro's first keys ({len(i_first)} properties)"
              + ("" if not (missing or extra or wrong) else f"; missing {missing}, extra {extra}, wrong {[(k, i_first[k], w_first[k]) for k in wrong]}"))

        # loops start and end on the intro's last frame
        l_keys = s.keys(loop)
        seam = sorted(k for k, ks in l_keys.items() if not same(ks[0][1], ks[-1][1]))
        check(not seam, f"{room} Loop's first and last keys match on every property" + ("" if not seam else f": {seam}"))
        i_last = last_values(s, intro)
        off = sorted((k, l_keys[k][0][1], i_last[k]) for k in l_keys if k in i_last and not same(l_keys[k][0][1], i_last[k]))
        check(not off, f"{room} Loop starts on {room} Intro's last frame" + ("" if not off else f": {off}"))
        unknown = sorted(k for k in l_keys if k not in i_last)
        check(not unknown, f"every property {room} Loop keys is also set by {room} Intro" + ("" if not unknown else f": {unknown}"))

    # community cards: a boolean hides each game's lockup through a gate, and nothing else changes
    flag = next((p for p in s.view_model if p.tag == "ViewModelPropertyBoolean" and p.get("name") == "community"), None)
    check(flag is not None, 'the view model has a boolean named "community"')
    if flag is not None:
        dflt = next((v.get("propertyValue", "false") for v in s.view_model.iter("ViewModelInstanceBoolean") if v.get("viewModelPropertyId") == flag.get("id")), None)
        check(dflt == "false", f"community defaults to false, so a game shows its lockup unless told otherwise (it is {dflt})")
    for room in [r for r in rooms if f"{r} Intro" in A and any(e.get("name") == f"{r} Lockup Gate" for e in ab.iter("Node"))]:   # the opener is not a game: no lockup
        gate = s.node(f"{room} Lockup Gate") if any(e.get("name") == f"{room} Lockup Gate" for e in ab.iter("Node")) else None
        kids = [c.get("name") for c in gate if c.tag == "Node"] if gate is not None else []
        check(gate is not None and kids == [f"{room} Lockup"] and s.parent[gate].get("name") == f"{room} Room"
              and float(gate.get("x", 0)) == 0 and float(gate.get("y", 0)) == 0,
              f"{room} Lockup sits alone in a {room} Lockup Gate at 0, 0 inside {room} Room")
        for pose, v in (("Shown", 1.0), ("Hidden", 0.0)):
            a = A.get(f"{room} Lockup {pose}")
            ks = s.keys(a) if a is not None else {}
            check(a is not None and s.duration(a) == 1 and list(ks) == [(f"{room} Lockup Gate", "opacity")] and ks[(f"{room} Lockup Gate", "opacity")][0][1] == v,
                  f"{room} Lockup {pose} is a one-frame pose holding the gate's opacity at {v:g}")
        for name, an in A.items():
            if not name.startswith(f"{room} Lockup "):
                check((f"{room} Lockup Gate", "opacity") not in s.keys(an), f"{name} does not key {room} Lockup Gate")
        gl = next((l for l in sm.findall("StateMachineLayer") if l.get("name") == f"{room} Lockup"), None)
        got = []
        if gl is not None:
            names = state_names(s, gl)
            for st in gl.findall("AnimationState"):
                for tr in st.findall("StateTransition"):
                    conds = []
                    for c in tr.findall("TransitionViewModelCondition"):
                        pid = c.find(".//DataBindContext").get("sourcePathIds").split("-")[-1]
                        b, v = c.find("TransitionValueBooleanComparator"), c.find("TransitionValueNumberComparator")
                        val = b.get("value", "false") if b is not None else int(float(v.get("value", "0")))
                        conds.append((pid, c.get("opValue", "equal"), val))
                    got.append((names[st.get("id")], names[tr.get("stateToId")], tuple(sorted(conds, key=str)), tr.get("duration", "0")))
        fid = flag.get("id") if flag is not None else None
        sid = props["scene"].get("id")
        n = per_room[room]
        want = [(f"{room} Lockup Shown", f"{room} Lockup Hidden", tuple(sorted([(fid, "equal", "true"), (sid, "equal", n)], key=str)), "0"),
                (f"{room} Lockup Hidden", f"{room} Lockup Shown", tuple(sorted([(fid, "equal", "false"), (sid, "equal", n)], key=str)), "0")]
        check(gl is not None and sorted(got) == sorted(want) and start_of(s, gl) == f"{room} Lockup Shown",
              f'layer "{room} Lockup" starts Shown, and reads community only while scene == {n}: hides when it is true, shows when it is false, at once')

    # the opener's toy ball is keyed only by its own loop, and held on the loop's first pose by its Intro and Waiting
    for name, a in A.items():
        if name not in ("Shelf Loop", "Shelf Intro", "Shelf Waiting"):
            bad = [o for (o, _p) in s.keys(a) if o in ("Shelf Ball", "Shelf Ball Spin")]
            check(not bad, f"{name} does not key the Shelf Ball or its Spin")
    return results


if __name__ == "__main__":
    chapter = sys.argv[1] if len(sys.argv) > 1 else "ch2"
    out = run(chapter)
    failed = [t for ok, t in out if not ok]
    for ok, t in out:
        print(("PASS  " if ok else "FAIL  ") + t)
    print(f"\n{len(out) - len(failed)} of {len(out)} checks passed")
    sys.exit(1 if failed else 0)
