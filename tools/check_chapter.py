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

    for room in rooms:
        # draw order: the first child draws on top, so a backdrop that must sit behind everything is last
        room_node = s.node(f"{room} Room")
        kids = [c.get("name") for c in room_node if c.tag == "Node"]
        check(kids and kids[-1] == f"{room} Backdrop", f"{room} Backdrop is the last child of {room} Room (children: {kids})")
        backdrop = s.node(f"{room} Backdrop")
        corner = [sh for sh in backdrop if sh.tag == "Shape" and sh.get("name") == "Wall Corner"]
        xs = [float(v.get("x", 0)) for sh in corner for v in sh.iter("StraightVertex")]
        check(corner and all(x == -1 for x in xs), f"{room} Wall Corner sits at x -1 so its line stays off the artboard edge at rest (x: {xs})")
        check(f"{room} Wall Lag" in kids, f"{room} Room holds a {room} Wall Lag wrapper")

        # outro keys only the room and its wall lag
        outro = A[f"{room} Outro"]
        touched = {k for k in s.keys(outro)}
        check(touched == {(f"{room} Room", "x"), (f"{room} Wall Lag", "x")}, f"{room} Outro keys only {room} Room x and {room} Wall Lag x")
        check(s.duration(outro) == OUTRO_FRAMES, f"{room} Outro is {OUTRO_FRAMES} frames (1.6 s)")
        for pose in ("Home", "Gone"):
            check(s.duration(A[f"{room} {pose}"]) == 1, f"{room} {pose} is a one-frame pose")

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
