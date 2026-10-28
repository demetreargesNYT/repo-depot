"""The fast check, run after every change:  npm run check ch2

  1. rive --verify and rive inspect: the file builds and reports no problems
  2. the rule checks in check_chapter.py: Waiting poses equal their intro's first keys, every intro is exactly
     3.2 s, every loop's first and last frames match (and start on the intro's last frame), the shared
     backdrop and its colour crossfade, the Next and Back moves and the draw layers are as the spec says,
     no intro keys the shelf ball
  3. the opener clears the artboard: with the first game started, the shelf room draws nothing from 1.7 s on
     (two renders; the other rooms are covered by tap_test.py, which needs a pair of games)
  4. lockup off hides the lockup: the first game with lockup false equals the same game with its lockup removed (three renders)

It does not re-render, pixel-diff or time anything else. Full passes (tap_test.py, back_test.py, harness/text-test.mjs,
frame-by-frame renders) are for a handoff to engineering, or when asked.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageChops
import check_chapter
from rml_read import Scene, chapter_dir

RIVE = os.path.expanduser("~/.rive/bin/rive")


def rive_json(args):
    r = subprocess.run([RIVE, *args, "--format=json"], capture_output=True, text=True)
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return {"success": False, "errors": [r.stdout + r.stderr], "data": {"problems": []}}


def build_checks(project):
    out = []
    v = rive_json([str(project), "--verify"])
    out.append((v.get("success", False) and not v.get("errors"), f"rive --verify: {len(v.get('errors', []))} error(s), {len(v.get('warnings', []))} warning(s)"))
    ins = subprocess.run([RIVE, "inspect", str(project), "--summary"], capture_output=True, text=True)
    try:
        problems = json.loads(ins.stdout)["problems"]
    except (json.JSONDecodeError, KeyError):
        problems = ["inspect output could not be read"]
    out.append((not problems, f"rive inspect: {len(problems)} problem(s)" + ("" if not problems else f" {problems[:2]}")))
    return out


def first_game(project):
    """(scene name, room) of the manifest's first game: the room the lockup and opener checks look at."""
    m = Scene(Path(project) / "scene.rml").manifest
    x = next(x for x in m["scenes"] if x.get("kind") == "game")
    return x["name"], x["room"]


def lockup_off_hides_lockup(project):
    """The first game with lockup off, at 2.6 s (its lockup is fully shown then): it must look exactly like that game
    with its lockup removed, and differ from the game with lockup on, so the flag hides the lockup and nothing else."""
    scene_name, room = first_game(project)
    tmp = Path(tempfile.mkdtemp())
    try:
        shots = {}
        for name, data, hide in (("off", ["--data=lockup=false"], False), ("on", [], False), ("bare", [], True)):
            dst = tmp / name
            shutil.copytree(project, dst, ignore=shutil.ignore_patterns("build"))
            if hide:
                tree = ET.parse(dst / "scene.rml")
                for n in tree.getroot().iter("Node"):
                    if n.get("name") == f"{room} Lockup":
                        n.set("hidden", "true")
                tree.write(dst / "scene.rml", encoding="utf-8")
            out = tmp / f"{name}.png"
            subprocess.run([RIVE, str(dst), f"--data=scene={scene_name}", *data, f"--screenshot={out}", "--advance=2.6s"], capture_output=True)
            if not out.exists():
                return False, "the lockup check could not render the scene (the build failed)"
            shots[name] = Image.open(out).convert("RGB")
        lit = lambda a, b: ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v > 12 else 0).histogram()[255]
        left, lockup = lit(shots["off"], shots["bare"]), lit(shots["on"], shots["bare"])
        return left == 0 and lockup > 0, f"lockup false hides the {room} lockup and nothing else at 2.6 s: {left} px differ from the scene without its lockup (want 0); the lockup itself is {lockup} px"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def opener_clears(project):
    """The first game from the start: the opener leaves. At 1.58 s, the outro's last frame (the Gone pose takes over at
    1.6 s and would hide a broken outro), it must draw nothing."""
    m = Scene(Path(project) / "scene.rml").manifest
    opener = next((x for x in m["scenes"] if x.get("kind") == "opener"), None)
    if opener is None:
        return True, "no opener in this file, so there is no opener to clear"
    game = first_game(project)[0]
    tmp = Path(tempfile.mkdtemp())
    try:
        dst = tmp / "p"
        shutil.copytree(project, dst, ignore=shutil.ignore_patterns("build"))
        full_t = tmp / "full.png"
        subprocess.run([RIVE, str(dst), f"--data=scene={game}", f"--screenshot={full_t}", "--advance=1.58s"], capture_output=True)
        if not full_t.exists():
            return False, "the opener check could not render the scene (the build failed)"
        tree = ET.parse(dst / "scene.rml")
        for n in tree.getroot().iter("Node"):
            if n.get("name") == f'{opener["room"]} Room':
                n.set("hidden", "true")
        tree.write(dst / "scene.rml", encoding="utf-8")
        bare_t = tmp / "bare.png"
        subprocess.run([RIVE, str(dst), f"--data=scene={game}", f"--screenshot={bare_t}", "--advance=1.58s"], capture_output=True)
        if not bare_t.exists():
            return False, "the opener check could not render the scene (the build failed)"
        diff = ImageChops.difference(Image.open(full_t).convert("RGB"), Image.open(bare_t).convert("RGB")).convert("L").point(lambda v: 255 if v > 12 else 0)
        px = diff.histogram()[255]
        return px == 0, f"the opener clears the artboard by the outro's last frame (1.58 s): {px} px of the shelf room still drawn"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def rooms_are_separate(chapter):
    """Every timeline named for a room keys only pieces inside that room (its colours pose keys the shared backdrop),
    so a change to one room's intro, ball or loop cannot reach another room."""
    from rml_read import Scene
    import rooms_sheet
    scene = Scene(chapter_dir(chapter) / "scene.rml")
    rooms = [r[1] for r in rooms_sheet.rooms_of_manifest(scene)]
    room_of = {}
    for room in rooms:
        for e in scene.node(f"{room} Room").iter():
            if e.get("id"):
                room_of[e.get("id")] = room
    background = {e.get("id") for e in scene.node("Background").iter() if e.get("id")}
    leaks = []
    for name, anim in scene.animations.items():
        owner = next((r for r in rooms if name.startswith(r + " ")), None)
        if owner is None:
            continue
        for ko in anim.findall("KeyedObject"):
            oid = ko.get("objectId")
            if name.endswith(" Colors"):
                ok = oid in background
            else:
                ok = room_of.get(oid) == owner
            if not ok:
                leaks.append(f"{name} keys {scene.label(oid)}")
    return not leaks, f"each room's timelines key only its own pieces: {len(leaks)} leak(s)" + ("" if not leaks else f" {leaks[:3]}")


def rooms_sheet_current(chapter):
    import rooms_sheet
    return rooms_sheet.main([chapter, "--check"]) == 0, "docs/rooms.md matches the rooms (python3 tools/rooms_sheet.py ch2 rewrites it)"


def main(argv):
    chapter = argv[0] if argv else "ch2"
    t0 = time.time()
    project = chapter_dir(chapter)
    results = build_checks(project) + check_chapter.run(chapter) + [opener_clears(project), lockup_off_hides_lockup(project),
                                                                    rooms_are_separate(chapter), rooms_sheet_current(chapter)]
    failed = [t for ok, t in results if not ok]
    for ok, t in results:
        if not ok:
            print("FAIL  " + t)
    print(f"{len(results) - len(failed)} of {len(results)} checks passed in {time.time() - t0:.1f} s" + ("" if not failed else f"; {len(failed)} FAILED"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
