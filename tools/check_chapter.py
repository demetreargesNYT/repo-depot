"""Check a chapter's scene.rml against the structure the spec describes.

    python3 tools/check_chapter.py ch2

Exits 1 if anything fails. `npm run deliver` runs this first.
"""
import sys
from rml_read import Scene, chapter_dir

INTRO_FRAMES = 192    # 3.2 s at 60 fps; the text CSS waits exactly this long
OUTRO_FRAMES = 96     # 1.6 s
ARTBOARD = (1495, 1067)
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
        want = {per_room[r]: f"{r} Colors" for r in rooms}
        check(targets == want, f"Backdrop's AnyState sends each scene value to its room's Colors (want {want}, has {targets})")
        entry = layer.find("EntryState/StateTransition")
        check(entry is not None and state_anim.get(entry.get("stateToId")) == "Shelf Colors", "Backdrop starts on Shelf Colors")
    for room in rooms:
        a = A.get(f"{room} Colors")
        check(a is not None, f'"{room} Colors" timeline exists')
        if a is None:
            continue
        ks = s.keys(a)
        check(s.duration(a) == 1 and set(ks) == {("Wall colour", "colorValue"), ("Floor colour", "colorValue")} and all(len(v) == 1 for v in ks.values()),
              f"{room} Colors is one frame holding only the Background's wall and floor colours")
    # the base colour on load is the opener's, so nothing flashes before the Backdrop layer's first frame
    shelf = A.get("Shelf Colors")
    if shelf is not None and base_wall:
        held = s.keys(shelf)[("Wall colour", "colorValue")][0][1]
        check(held.upper() == base_wall.upper(), f"the Background's own wall colour ({base_wall}) is the opener's ({held})")
    # only the Colors timelines may key the Background, or two layers would fight over its colours
    for name, a in A.items():
        if not name.endswith(" Colors"):
            bad = sorted({o for (o, _p) in s.keys(a) if o in ("Wall colour", "Floor colour", "Background", "Wall", "Floor", "Floor-Line")})
            check(not bad, f"{name} does not key the Background" + ("" if not bad else f": {bad}"))

    for room in rooms:
        kids = [c.get("name") for c in s.node(f"{room} Room") if c.tag == "Node"]
        check(f"{room} Wall Lag" in kids, f"{room} Room holds a {room} Wall Lag wrapper")

        # outro keys only the room and its wall lag
        outro = A[f"{room} Outro"]
        touched = {k for k in s.keys(outro)}
        rules = f"{room} Draw Rules"
        check(touched == {(f"{room} Room", "x"), (f"{room} Wall Lag", "x"), (rules, "drawTargetId")},
              f"{room} Outro keys only {room} Room x, {room} Wall Lag x and its draw rule")

        # the leaving room draws below the arriving room: Outro and Gone key the Bottom target, Home keys Normal
        want = {"Outro": f"{room} Bottom", "Gone": f"{room} Bottom", "Home": f"{room} Normal"}
        for pose, target in want.items():
            ks = s.keys(A[f"{room} {pose}"]).get((rules, "drawTargetId"), [])      # keys read as target names
            check(len(ks) == 1 and ks[0][1] == target, f"{room} {pose} puts the room's draw rule on {target.split()[-1]}")
        check(s.duration(outro) == OUTRO_FRAMES, f"{room} Outro is {OUTRO_FRAMES} frames (1.6 s)")
        for pose in ("Home", "Gone"):
            check(s.duration(A[f"{room} {pose}"]) == 1, f"{room} {pose} is a one-frame pose")
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

    # the opener's toy ball is keyed only by its own loop
    for name, a in A.items():
        if name != "Shelf Loop":
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
