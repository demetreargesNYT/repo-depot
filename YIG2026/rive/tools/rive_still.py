"""Render stills of a built room, to look at before reporting. Pushes nothing and writes nothing outside the scratch folder.

    python3 tools/rive_still.py <ch> <scene> <seconds> [<seconds> ...]
    python3 tools/rive_still.py ch2 mini 1.9 5.5 12
    python3 tools/rive_still.py .cache/scratch.nosync/ch2/mini-work mini 6

<ch> is 1, 2, 3 or ch1, ch2, ch3 (the chapter as it is in chapters/<ch>), or the path of a scratch copy of a chapter (a helper's
build folder: --out of tools like chapters/ch2/scripts/build.py). <scene> is a scene name from that file's scene enum (chapter.json
lists them). Each <seconds> is a time after the scene is set, the same clock as the Finesse panel's timecode (a room's intro plays
first, so the loop starts at 3.2 s).

The stills go to .cache/scratch.nosync/<ch1|ch2|ch3|shared>/stills/<scene>-<seconds>s.png, each run replacing the same names (the
folder is that of the chapter you name, or YIG_SESSION if it is set; a path with no chapter in it goes to shared). The project is
copied first, so a render never touches chapters/<ch>/build, and parallel renders do not share a build folder. Open the PNGs with the
Read tool. Prints the path of every still. Exit code 0 when all rendered, 1 when one did not.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rml_read import REPO, Scene, chapter_dir  # noqa: E402
import scratch  # noqa: E402

RIVE = os.path.expanduser("~/.rive/bin/rive")
TRIES = 4               # a render can fail when the machine is busy: try again
LIMIT = 180             # seconds per render attempt


def session_for(arg):
    """The scratch subfolder: YIG_SESSION, else the chapter named (ch1, ch2, ch3 or a path with one in it), else shared."""
    if os.environ.get("YIG_SESSION") in scratch.SESSIONS:
        return os.environ["YIG_SESSION"]
    m = re.search(r"(?:^|/)(ch[123])(?:/|$)", arg) or re.fullmatch(r"([123])", arg)
    if m:
        return m.group(1) if m.group(1).startswith("ch") else f"ch{m.group(1)}"
    return "shared"


def scene_names(scene_rml):
    """The scene enum's values in a scene.rml."""
    root = ET.parse(scene_rml).getroot()
    for e in root.iter("DataEnumCustom"):
        if e.get("name") == "Scene":
            return [v.get("value") for v in e.iter("DataEnumValue")]
    return []


def copy_project(source, dest):
    """A copy of the chapter project to render from, without its build folder, scripts or references; the room a file opens on
    (Loading) starts looping at once, so it is hidden: the still is of one room."""
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(source, dest, ignore=shutil.ignore_patterns("build", "scripts", "refs", "__pycache__"))
    manifest = Scene(dest / "scene.rml").manifest
    opening = {x["room"] + " Room" for x in manifest["scenes"] if x.get("kind") == "loading" and "room" in x}
    if any(x.get("kind") == "loading" and "room" not in x for x in manifest["scenes"]):
        opening.add("Start Room")
    if opening:
        tree = ET.parse(dest / "scene.rml")
        for n in tree.getroot().iter("Node"):
            if n.get("name") in opening:
                n.set("hidden", "true")
        tree.write(dest / "scene.rml", encoding="utf-8")


def render(project, scene, seconds, out):
    args = [RIVE, str(project), f"--data=scene={scene}", f"--screenshot={out}", f"--advance={seconds}s"]
    for _ in range(TRIES):
        out.unlink(missing_ok=True)
        try:
            subprocess.run(args, capture_output=True, timeout=LIMIT)
        except subprocess.TimeoutExpired:
            continue
        if out.exists():
            return True
    return False


def main(argv):
    ap = argparse.ArgumentParser(description="Render stills of a built room at the given times.")
    ap.add_argument("chapter", help="1, 2, 3, ch1, ch2, ch3, or the path of a scratch copy of a chapter")
    ap.add_argument("scene", help="a scene name from the file's scene enum")
    ap.add_argument("seconds", nargs="+", type=float, help="times after the scene is set (the Finesse panel's clock)")
    args = ap.parse_args(argv)
    ch = args.chapter
    source = chapter_dir(f"ch{ch}" if re.fullmatch(r"[123]", ch) else ch)
    names = scene_names(source / "scene.rml")
    if args.scene not in names:
        sys.exit(f"no scene {args.scene!r} in {source / 'scene.rml'}: the scene enum has {', '.join(names)}")
    sess = session_for(args.chapter)
    folder = scratch.ROOT / sess / "stills"
    folder.mkdir(parents=True, exist_ok=True)
    work = scratch.ROOT / sess / f"still-work-{args.scene}"
    copy_project(source, work)
    failed = 0
    try:
        for s in args.seconds:
            out = folder / f"{args.scene}-{s:g}s.png"
            if render(work, args.scene, f"{s:g}", out):
                print(out)
            else:
                print(f"could not render {args.scene} at {s:g} s", file=sys.stderr)
                failed += 1
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
