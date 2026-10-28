"""Back-and-forth tap test: real taps at exact frames, no browser.

    python3 tools/back_test.py ch2

A throwaway copy of the project gets test-only listeners: an invisible hit box per (scene, direction) that,
when pressed, writes direction and then scene, exactly as the integration file does. `rive --pointer=down` on
a box is a tap at that frame. The copy also writes each room's x out to the view model, so the run records
where every room is on every frame (`--data-dump-every=1`). Nothing in the chapter is changed.

The integration file decides when a tap reaches the file: a tap that would reverse a running pan is held until
the pan ends (1.6 s after the tap that started it), and a tap the same way, or one that keeps the room, goes at
once. Each case is a list of taps; the test applies that rule to their times, then runs the file.

Pass, for every frame of every case:
  * no snap: no room moves more than a pan's top speed between two frames;
  * nothing left on stage: from 1.6 s after the last tap that reaches the file, every room but the current one
    is off the artboard (at x -1600 or +1600) and the current one is home (x 0);
  * the rooms move as one camera: during a Back, and the Next after one, the two rooms are exactly 1600 apart;
  * draw order: each room's draw rule has one target while it is the current scene and another otherwise
    (the readout is an internal index, so the targets are compared, not named; check_chapter.py names them).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from rml_read import Scene, chapter_dir

RIVE = os.path.expanduser("~/.rive/bin/rive")
ROOMS = {0: "Shelf", 1: "Wordle", 2: "Connections"}
EMPTY = {9: "Chapter 1", 8: "Chapter 3"}       # the file's first and last scenes: the shared backdrop only, no room
NAMES = {**ROOMS, **EMPTY}
START = 9                                       # the file opens on the empty Chapter 1 room
MOVE = 1.65           # s the integration file treats a room change as running (PAN_MS)


def pan_peak():
    """The fastest a room moves in a clean pan, artboard units per frame: 1600 over 90 frames, power2.inOut."""
    def bez(u, a, b):
        return 3 * (1 - u) ** 2 * u * a + 3 * (1 - u) * u ** 2 * b + u ** 3
    xs = [(bez(i / 4000, 0.65, 0.35), bez(i / 4000, 0, 1)) for i in range(4001)]
    return max((y1 - y0) / (x1 - x0) for (x0, y0), (x1, y1) in zip(xs, xs[1:]) if x1 > x0) * 1600 / 90


TOP_SPEED = pan_peak() * 1.1     # a snap moves a room faster than any frame of a clean pan
SPOTS = [(sc, d) for sc in NAMES for d in (1, -1)]


def instrument(src):
    """Copy the project with tap boxes and room-x readouts. Returns (dir, {(scene, direction): (x, y)})."""
    dst = Path(tempfile.mkdtemp()) / "p"
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("build"))
    p = dst / "scene.rml"
    t = p.read_text()
    s = Scene(p)
    vm = s.view_model.get("id")
    prop = {e.get("name"): e.get("id") for e in s.view_model if e.tag == "ViewModelPropertyNumber"}
    top = max(int(i.split(":")[1]) for i in s.by_id if i.startswith("9:")) if any(i.startswith("9:") for i in s.by_id) else 0
    n = [top]

    def new():
        n[0] += 1
        return f"9:{n[0]}"

    boxes, listeners, where = [], [], {}
    for i, (sc, d) in enumerate(SPOTS):
        x, y = 5 + 20 * i, 1050
        where[(sc, d)] = (x + 5, y + 5)
        b = new()
        boxes.append(f'<Shape x="{x}" y="{y}" name="Test Tap {i}" id="{b}"><Rectangle width="10" height="10" originX="0" originY="0" name="R" id="{new()}"/>'
                     f'<Fill name="F" id="{new()}"><SolidColor colorValue="01000000" name="C" id="{new()}"/></Fill></Shape>')
        write = lambda pid, v: (f'<ListenerViewModelChange><BindablePropertyNumber propertyValue="{v}">'
                                f'<DataBindContext sourcePathIds="{vm}-{pid}" propertyKey="636" direction="true"/></BindablePropertyNumber></ListenerViewModelChange>')
        listeners.append(f'<StateMachineListenerSingle targetId="{b}" listenerTypeValue="down" name="Test Listener {i}" id="{new()}">'
                         + write(prop["direction"], d) + write(prop["scene"], sc) + '</StateMachineListenerSingle>')
    first = s.artboard[0]
    m = re.search(r'\n( *)<\w+ [^>]*id="%s"' % first[0].get("id"), t)    # the first child of the top group draws on top
    t = t[:m.start()] + "\n" + "\n".join(m.group(1) + b for b in boxes) + t[m.start():]
    m = re.search(r'<StateMachine [^>]*>', t)
    t = t[:m.end()] + "\n" + "\n".join(listeners) + t[m.end():]
    readouts, insts = [], []
    for r in ROOMS.values():
        pid = new()
        readouts.append(f'<ViewModelPropertyNumber name="x {r}" id="{pid}"/>')
        insts.append(f'<ViewModelInstanceNumber viewModelPropertyId="{pid}" id="{new()}"/>')
        m = re.search(r'<Node [^>]*name="%s Room" id="%s">' % (r, s.node(f"{r} Room").get("id")), t)
        t = t[:m.end()] + f'<DataBindContext sourcePathIds="{vm}-{pid}" propertyKey="13" direction="true" id="{new()}"/>' + t[m.end():]
        dr = s.node(f"{r} Room").find("DrawRules")
        pid = new()
        readouts.append(f'<ViewModelPropertyNumber name="draw {r}" id="{pid}"/>')
        insts.append(f'<ViewModelInstanceNumber viewModelPropertyId="{pid}" id="{new()}"/>')
        m = re.search(r'<DrawRules [^>]*id="%s"[^>]*>' % dr.get("id"), t)
        t = t[:m.end()] + f'<DataBindContext sourcePathIds="{vm}-{pid}" propertyKey="121" direction="true" id="{new()}"/>' + t[m.end():]
    m = re.search(r'<ViewModelPropertyNumber name="scene" id="%s"/>' % prop["scene"], t)
    t = t[:m.end()] + "".join(readouts) + t[m.end():]
    m = re.search(r'<ViewModelInstanceNumber [^>]*viewModelPropertyId="%s"[^>]*/>' % prop["scene"], t)
    t = t[:m.end()] + "".join(insts) + t[m.end():]
    p.write_text(t)
    return dst, where


def schedule(taps):
    """Apply the integration file's rule to [(seconds, scene, direction)] user taps; returns when each reaches
    the file. A room change while a pan runs waits for it if it is a Back, or if the pan is a Back; a Next during
    a Next pan goes at once. A later tap during the wait replaces the held one."""
    out, scene, pan_dir, pan_end, held = [], START, 0, -1.0, None
    events = sorted(taps)
    i = 0
    while i < len(events) or held:
        nt = events[i][0] if i < len(events) else None
        if held and (nt is None or held[0] <= nt):
            at, sc, d = held
            held = None
            out.append((at, sc, d))
            scene, pan_dir, pan_end = sc, d, at + MOVE
            continue
        t, sc, d = events[i]
        i += 1
        held = None                                      # a new tap replaces a held one
        if sc != scene and t < pan_end and (d < 0 or pan_dir < 0):
            held = (pan_end, sc, d)
            continue
        out.append((t, sc, d))
        if sc != scene:
            pan_dir, pan_end = d, t + MOVE
        scene = sc
    return out


def run_case(project, where, taps, settle=2.2):
    fired = schedule(taps)
    args, now = [], 0.0
    for t, sc, d in fired:
        if t > now:
            args.append(f"--advance={round((t - now) * 60)}")
        x, y = where[(sc, d)]
        args.append(f"--pointer=down@{x},{y}")
        now = t
    args.append(f"--advance={round(settle * 60)}")
    shutil.rmtree(project / "build", ignore_errors=True)
    r = subprocess.run([RIVE, str(project), "--data-dump-every=1", *args], capture_output=True, text=True)
    dumps = list((project / "build").glob("*.jsonl"))
    if not dumps:
        raise SystemExit("run failed:\n" + r.stdout + r.stderr)
    state, rows = {}, []
    for ln in dumps[0].read_text().splitlines():
        d = json.loads(ln)
        if "values" not in d:
            continue
        for v in d["values"]:
            state[v["path"]] = v["value"]
        rows.append((d["frame"], dict(state)))
    return fired, rows


def judge(fired, rows):
    """[(ok, text)] for one case. A room not visited yet sits at x 0 with its art held off stage by its Waiting
    pose, so it only counts as on stage once it has been the current scene."""
    out = []
    last = fired[-1][0]
    snaps, stray, apart = [], [], []
    draw_vals = {r: {True: set(), False: set()} for r in ROOMS.values()}
    visited = set()
    prev = None
    camera, last_dir = [], 1
    for at, sc, d in fired:
        if d < 0 or last_dir < 0:
            camera.append(at)
        last_dir = d
    for frame, st in rows:
        t = frame / 60
        current = int(st["scene"])
        current = ROOMS[current] if current in ROOMS else None      # None: an empty scene, nothing but the backdrop
        if current:
            visited.add(current)
        expected = [current] if current else []
        xs = {r: st.get(f"x {r}", 0) for r in ROOMS.values()}
        if prev:
            for r in xs:
                step = abs(xs[r] - prev[1][r]) / max(1, frame - prev[0])
                if step > TOP_SPEED:
                    snaps.append((round(t, 2), r, round(prev[1][r]), round(xs[r])))
        prev = (frame, xs)
        on = [r for r in visited if abs(xs[r]) < 1600 - 1e-3]
        # during a Back, and the Next that follows one, the two rooms both move by their room x and must move as
        # one camera (a Next during a Next pan staggers the rooms, as it always has)
        moving = [r for r in on if abs(xs[r]) > 1e-3]
        if len(moving) == 2 and any(a <= t <= a + MOVE for a in camera):
            a, b = (xs[r] for r in moving)
            if abs(abs(a - b) - 1600) > 1:
                apart.append((round(t, 2), {r: round(xs[r]) for r in moving}))
        if t >= last + MOVE + 0.05 and (any(abs(xs[r]) > 0.5 for r in expected) or on != expected):
            stray.append((round(t, 2), {r: round(xs[r]) for r in visited}))
        if frame > 0:                                  # frame 0 holds the authored values, before the first advance
            for r in ROOMS.values():                   # the readout is an internal index: compare, don't name
                draw_vals[r][r == current].add(st.get(f"draw {r}"))
    draw = [r for r, v in draw_vals.items() if len(v[True]) > 1 or len(v[False]) > 1 or (v[True] & v[False])]
    out.append((not snaps, f"no snap (most a room moves between frames is the pan's own speed)" + ("" if not snaps else f": {snaps[:3]}")))
    out.append((not apart, "during a Back, and the Next after one, the two rooms move together, 1600 apart" + ("" if not apart else f": {apart[:3]}")))
    out.append((not stray, f"after the last move only the current room (none, on the empty Chapter 1 and Chapter 3 scenes) is on stage, at home" + ("" if not stray else f": {stray[:2]}")))
    out.append((not draw, "each room's draw rule has one target while it is the scene and another otherwise, switching at the tap" + ("" if not draw else f": {draw}")))
    return out


def cases(first, second):
    a, b = first, second             # scene numbers, in the order the player sees the games
    T = [0.5, 1.0, 2.5]
    out = []
    # the file opens on the empty Chapter 1 room (scene 9); the first tap pans into the opener. Every case does that
    # at 0.2 s, then everything else is shifted 4 s later so the opener's pan is over.
    go = [(0.2, 0, 1)]
    sh = lambda taps: go + [(t + 4.0, sc, d) for t, sc, d in taps]
    out.append(("Next from Chapter 1 to the opener, Back to Chapter 1 0.5 s later", [(0.2, 0, 1), (0.7, 9, -1)]))
    out.append(("Next from Chapter 1 to the opener, Back to Chapter 1 2.5 s later, Next 0.5 s after that", [(0.2, 0, 1), (2.7, 9, -1), (3.2, 0, 1)]))
    out.append(("opener, Back to Chapter 1 once the intro is over", [(0.2, 0, 1), (4.0, 9, -1)]))
    for t in T:
        out.append((f"Next to {ROOMS[a]}, Back to the opener {t} s later", sh([(0.2, a, 1), (0.2 + t, 0, -1)])))
        out.append((f"Next to {ROOMS[a]}, Next to {ROOMS[b]}, Back {t} s later", sh([(0.2, a, 1), (4.0, b, 1), (4.0 + t, a, -1)])))
        out.append((f"at {ROOMS[b]}: Back to {ROOMS[a]}, Next {t} s later", sh([(0.2, a, 1), (4.0, b, 1), (8.0, a, -1), (8.0 + t, b, 1)])))
        out.append((f"at {ROOMS[b]}: Back, Back {t} s apart", sh([(0.2, a, 1), (4.0, b, 1), (8.0, a, -1), (8.0 + t, 0, -1)])))
        out.append((f"at {ROOMS[b]} (the last game): Next to Chapter 3, Back {t} s later", sh([(0.2, a, 1), (4.0, b, 1), (8.0, 8, 1), (8.0 + t, b, -1)])))
        out.append((f"at {ROOMS[b]}: Next to Chapter 3, Back, Next {t} s apart", sh([(0.2, a, 1), (4.0, b, 1), (8.0, 8, 1), (12.0, b, -1), (12.0 + t, 8, 1)])))
    out.append((f"Next to {ROOMS[a]}, Next to {ROOMS[b]} 0.5 s later, Back 0.3 s after that",
                sh([(0.2, a, 1), (0.7, b, 1), (1.0, a, -1)])))
    out.append((f"three taps during one pan: Next, Back, Next, Back", sh([(0.2, a, 1), (0.6, 0, -1), (0.9, a, 1), (1.2, 0, -1)])))
    out.append((f"Next to {ROOMS[b]}, Next to Chapter 3 0.5 s later, Back 0.3 s after that", sh([(0.2, b, 1), (0.7, 8, 1), (1.0, b, -1)])))
    return out


def main(argv):
    chapter = argv[0] if argv and not argv[0].startswith("--") else "ch2"
    project, where = instrument(chapter_dir(chapter))
    failed = 0
    try:
        for first, second in ((1, 2), (2, 1)):
            for label, taps in cases(first, second):
                fired, rows = run_case(project, where, taps)
                res = judge(fired, rows)
                bad = [t for ok, t in res if not ok]
                failed += bool(bad)
                plays = ", ".join(f"{NAMES[sc]}{'' if d > 0 else ' (back)'} at {t:.2f} s" for t, sc, d in fired)
                print(f'{"PASS" if not bad else "FAIL"}  {label}   [{plays}]')
                for t in bad:
                    print("        " + t)
    finally:
        shutil.rmtree(project.parent, ignore_errors=True)
    print(f"\n{'all cases passed' if not failed else str(failed) + ' case(s) failed'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
