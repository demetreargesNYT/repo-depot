"""Loop continuity test: does a room keep moving while it pans out on Next and when it pans back in on Back?

    python3 tools/loop_motion.py ch1
    python3 tools/loop_motion.py ch3 --rooms "Chapter 4"

For each room the file plays it, taps Next to another scene mid-loop, then taps Back to the room, in a throwaway copy of
the project (tap boxes as in back_test.py). Every piece the room's loops move (x, y, rotation, scale, opacity) is written
out to the view model on every frame. A control run that never leaves the room gives what each piece should read; a loop
that keeps playing matches it on every frame, through the pan out, the time away and the pan back in. A piece that
stops, jumps or restarts differs from the control, and the test names it and the first frame where it does.

Nothing in the chapter is changed.
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from rml_read import Scene, chapter_dir
import scratch  # scratch output goes in .cache/scratch/, never /tmp

RIVE = os.path.expanduser("~/.rive/bin/rive")
PROPS = {"x": 13, "y": 14, "rotation": 15, "scaleX": 16, "scaleY": 17, "opacity": 18}   # Rive's property keys for a node or shape
ENTER, OUT, BACK, END = 0.2, 7.0, 11.0, 14.0     # s: into the room, Next out (its loop is running), Back in, end of the run
TOL = 1e-3


def loop_pieces(s, room):
    """[(object id, property)] that the room's Loop, Small Loop and any other loop named for it key on a node or shape."""
    out = []
    for name, anim in s.animations.items():
        if not name.startswith(room + " ") or not name.endswith("Loop") or name == f"{room} Loop" and False:
            continue
        for ko in anim.findall("KeyedObject"):
            e = s.by_id.get(ko.get("objectId"))
            if e is None or e.tag not in ("Node", "Shape"):
                continue
            for kp in ko.findall("KeyedProperty"):
                if kp.get("property") in PROPS and (ko.get("objectId"), kp.get("property")) not in out:
                    out.append((ko.get("objectId"), kp.get("property")))
    return out


def instrument(src, pieces, taps):
    """Copy the project with one tap box per (scene, direction) in taps and a view model readout per piece.
    Returns (dir, {(scene, direction): (x, y)}, {readout name: (object id, property)})."""
    dst = scratch.mkdtemp("loop-motion-") / "p"
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("build"))
    p = dst / "scene.rml"
    t = p.read_text()
    s = Scene(p)
    vm = s.view_model.get("id")
    prop = {e.get("name"): e.get("id") for e in s.view_model if e.tag.startswith("ViewModelProperty")}
    enum_ids = {e.get("name"): [v.get("id") for v in e if v.tag == "DataEnumValue"] for e in s.root.findall("DataEnumCustom")}
    n = [0]

    def new():
        n[0] += 1
        return f"99:{n[0]}"

    boxes, listeners, where = [], [], {}
    for i, (sc, d) in enumerate(taps):
        x, y = 5 + 20 * i, 1050
        where[(sc, d)] = (x + 5, y + 5)
        b = new()
        boxes.append(f'<Shape x="{x}" y="{y}" name="Test Tap {i}" id="{b}"><Rectangle width="10" height="10" originX="0" originY="0" name="R" id="{new()}"/>'
                     f'<Fill name="F" id="{new()}"><SolidColor colorValue="01000000" name="C" id="{new()}"/></Fill></Shape>')
        write = lambda pid, v: (f'<ListenerViewModelChange><BindablePropertyEnum propertyValue="{v}">'
                                f'<DataBindContext sourcePathIds="{vm}-{pid}" propertyKey="637" direction="true"/></BindablePropertyEnum></ListenerViewModelChange>')
        listeners.append(f'<StateMachineListenerSingle targetId="{b}" listenerTypeValue="down" name="Test Listener {i}" id="{new()}">'
                         + write(prop["direction"], enum_ids["Direction"][0 if d > 0 else 1]) + write(prop["scene"], enum_ids["Scene"][sc]) + '</StateMachineListenerSingle>')
    first = s.artboard[0]
    m = re.search(r'\n( *)<\w+ [^>]*id="%s"' % first[0].get("id"), t)    # the first child of the top group draws on top
    t = t[:m.start()] + "\n" + "\n".join(m.group(1) + b for b in boxes) + t[m.start():]
    m = re.search(r'<StateMachine [^>]*>', t)
    t = t[:m.end()] + "\n" + "\n".join(listeners) + t[m.end():]

    readouts, insts, names = [], [], {}
    for i, (oid, pname) in enumerate(pieces):
        pid = new()
        name = f"r{i}"
        names[name] = (oid, pname)
        readouts.append(f'<ViewModelPropertyNumber name="{name}" id="{pid}"/>')
        insts.append(f'<ViewModelInstanceNumber viewModelPropertyId="{pid}" id="{new()}"/>')
        bind = f'<DataBindContext sourcePathIds="{vm}-{pid}" propertyKey="{PROPS[pname]}" direction="true" id="{new()}"/>'
        m = re.search(r'<(\w+) [^>]*\bid="%s"[^>]*?(/?)>' % re.escape(oid), t)
        if m.group(2):       # self-closing: open it so the binding can be its child
            tag = m.group(1)
            t = t[:m.end() - 2] + ">" + bind + f"</{tag}>" + t[m.end():]
        else:
            t = t[:m.end()] + bind + t[m.end():]
    m = re.search(r'<ViewModelPropertyEnumCustom [^>]*name="scene" id="%s"/>' % prop["scene"], t)
    t = t[:m.end()] + "".join(readouts) + t[m.end():]
    m = re.search(r'<ViewModelInstanceEnum [^>]*viewModelPropertyId="%s"[^>]*/>' % prop["scene"], t)
    t = t[:m.end()] + "".join(insts) + t[m.end():]
    p.write_text(t)
    return dst, where, names


def play(project, where, fired):
    """Run the taps [(seconds, scene, direction)] to END; returns {frame: {readout: value}} with every frame filled in."""
    args, now = [], 0.0
    for at, sc, d in fired:
        if at > now:
            args.append(f"--advance={round((at - now) * 60)}")
        args.append("--pointer=down@%d,%d" % where[(sc, d)])
        now = at
    args.append(f"--advance={round((END - now) * 60)}")
    shutil.rmtree(project / "build", ignore_errors=True)
    r = subprocess.run([RIVE, str(project), "--data-dump-every=1", *args], capture_output=True, text=True)
    dumps = list((project / "build").glob("*.jsonl"))
    if not dumps:
        raise SystemExit("run failed:\n" + r.stdout + r.stderr)
    state, frames = {}, {}
    for ln in dumps[0].read_text().splitlines():
        d = json.loads(ln)
        if "values" not in d:
            continue
        for v in d["values"]:
            state[v["path"]] = v["value"]
        frames[d["frame"]] = dict(state)
    # a frame is only dumped when something changed, so carry the last state forward to give every frame a row
    dense, last = {}, {}
    for f in range(max(frames) + 1):
        last = frames.get(f, last)
        dense[f] = last
    return dense


def judge(frames, control, names, s):
    """Pieces that differ from the control run, as [(label, property, first frame, control value, value)]."""
    bad = {}
    for frame in sorted(frames):
        if frame < round(OUT * 60) or frame not in control:
            continue
        for name, v in frames[frame].items():
            if name in names and name not in bad and abs(v - control[frame].get(name, v)) > TOL:
                bad[name] = (frame, control[frame].get(name), v)
    return [(s.label(names[nm][0]), names[nm][1], f, c, v) for nm, (f, c, v) in bad.items()]


def other_scene(chapter_names, flow, scene):
    """A scene to leave for: the next one in the file's flow, else the next in the enum."""
    order = flow or chapter_names
    return order[(order.index(scene) + 1) % len(order)] if scene in order else chapter_names[(chapter_names.index(scene) + 1) % len(chapter_names)]


def survey(chapter, only=None):
    """[(room, scene name, pieces checked, [differences])]; run from a script or from the command line."""
    src = chapter_dir(chapter)
    s = Scene(src / "scene.rml")
    names = s.scene_names()
    flow = (s.manifest.get("tests") or {}).get("flow")
    rows = []
    for x in s.manifest["scenes"]:
        room = x.get("room")
        if not room or (only and room not in only):
            continue
        pieces = loop_pieces(s, room)
        if not pieces:
            rows.append((room, x["name"], 0, []))
            continue
        away = other_scene(names, flow, x["name"])
        sc, sa = names.index(x["name"]), names.index(away)
        taps = [(sc, 1), (sa, 1), (sc, -1)]
        project, where, readouts = instrument(src, pieces, taps)
        try:
            control = play(project, where, [(ENTER, sc, 1)])
            frames = play(project, where, [(ENTER, sc, 1), (OUT, sa, 1), (BACK, sc, -1)])
        finally:
            shutil.rmtree(project.parent, ignore_errors=True)
        rows.append((room, x["name"], len(pieces), judge(frames, control, readouts, s)))
    return rows


def main(argv):
    """Each room is tapped out twice: 0.25 s into its visit (its intro and the opening hold are running) and once its loop
    is running. --out S taps out at S seconds instead."""
    global OUT, BACK
    chapter = argv[0] if argv and not argv[0].startswith("--") else "ch2"
    only = argv[argv.index("--rooms") + 1].split(",") if "--rooms" in argv else None
    times = [float(argv[argv.index("--out") + 1])] if "--out" in argv else [0.45, 7.0]
    failed = 0
    for out in times:
        OUT, BACK = out, out + 4.0
        print(f"-- tap out at {out} s after the room starts, Back 4 s later")
        for room, scene, count, diffs in survey(chapter, only):
            failed += bool(diffs)
            print(f'{"PASS" if not diffs else "FAIL"}  {room} ({scene}): {count} moving properties'
                  + ("" if not diffs else f", {len(diffs)} differ from the control run"))
            for label, pname, frame, c, v in diffs[:6]:
                print(f"        {label} {pname}: from frame {frame} ({frame / 60:.2f} s) reads {v:.3f}, the control {c:.3f}")
    print(f"\n{'all rooms keep moving' if not failed else str(failed) + ' room(s) stop or jump'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
