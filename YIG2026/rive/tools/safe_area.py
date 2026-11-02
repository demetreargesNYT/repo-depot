"""Which pieces of each room fall outside the safe area (x 560 to 935, y 0 to 812, the Figma phone frame)?

    python3 tools/safe_area.py ch2 [--rooms "Wordle,Connections"] [--out FILE]

For every piece of a room (a child of its Front, Floor and Wall planes, or a loose child of the room) the piece is hidden in a
throwaway copy of the project, the room's settled picture (3.4 s in) is rendered, and the pixels that change are the piece's
true extent, strokes included. Balls and lockups are left out (balls are checked against their own keys; lockups are HTML-sized
Rive text). Prints a markdown list: the piece, its extent, and which sides cross the safe area. Nothing in the chapter changes.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageChops

from rml_read import Scene, chapter_dir

RIVE = os.path.expanduser("~/.rive/bin/rive")
SAFE = (560, 935, 0, 812)          # x0, x1, y0, y1
SETTLED = 205                      # frames after the scene is set: the intro (192) is over and the loop is on its first pose
THRESHOLD = 24                     # per-channel colour difference that counts as the piece
MIN_PIXELS = 20


def pieces(s, room):
    """[(node element, label)] for a room: the children of its planes and any other loose child."""
    rn = s.node(f"{room} Room")
    out = []
    skip = ("Ball", "Lockup", "Clip", "Wall Lag")
    for top in rn:
        if top.tag not in ("Node", "Shape"):
            continue
        name = top.get("name") or ""
        if name.endswith("Plane"):
            for c in top:
                if c.tag in ("Node", "Shape"):
                    out.append((c, f'{c.get("name") or "?"} ({name.replace(room + " ", "")})'))
        elif name.endswith("Wall Lag"):
            for plane in top:
                if plane.tag in ("Node", "Shape"):
                    for c in plane:
                        if c.tag in ("Node", "Shape"):
                            out.append((c, f'{c.get("name") or "?"} (Wall Plane)'))
        elif not any(k in name for k in skip):
            out.append((top, name))
    return [(e, l) for e, l in out if "Ball" not in (e.get("name") or "") and "Lockup" not in (e.get("name") or "")]


def render(project, scene, out):
    r = subprocess.run([RIVE, str(project), f"--data=scene={scene}", f"--advance={SETTLED}", f"--screenshot={out}"], capture_output=True, text=True)
    if not Path(out).exists():
        raise SystemExit("render failed:\n" + r.stdout + r.stderr)
    return Image.open(out).convert("RGB")


def survey(chapter, only=None, log=print):
    src = chapter_dir(chapter)
    s = Scene(src / "scene.rml")
    work = Path(tempfile.mkdtemp()) / "p"
    shutil.copytree(src, work, ignore=shutil.ignore_patterns("build"))
    rows = []
    try:
        for x in s.manifest["scenes"]:
            room = x.get("room")
            if not room or (only and room not in only):
                continue
            base = render(work, x["name"], work.parent / "base.png")
            for el, label in pieces(s, room):
                tree = ET.parse(work / "scene.rml")
                node = next(e for e in tree.getroot().iter() if e.get("id") == el.get("id"))
                node.set("hidden", "true")
                tree.write(work / "scene.rml", encoding="utf-8")
                img = render(work, x["name"], work.parent / "p.png")
                mask = ImageChops.difference(base, img).convert("L").point(lambda v: 255 if v > THRESHOLD else 0)
                if mask.histogram()[255] >= MIN_PIXELS:
                    x0, y0, x1, y1 = mask.getbbox()
                    sides = [n for n, bad in (("left", x0 < SAFE[0]), ("right", x1 > SAFE[1]), ("below", y1 > SAFE[3])) if bad]
                    rows.append((room, label, (x0, y0, x1, y1), sides))
                    log(f"{room} | {label} | x {x0}-{x1}, y {y0}-{y1} | {', '.join(sides) or 'inside'}")
                shutil.copyfile(src / "scene.rml", work / "scene.rml")
    finally:
        shutil.rmtree(work.parent, ignore_errors=True)
    return rows


def main(argv):
    chapter = argv[0]
    only = argv[argv.index("--rooms") + 1].split(",") if "--rooms" in argv else None
    out = open(argv[argv.index("--out") + 1], "w") if "--out" in argv else None

    def log(line):
        print(line, flush=True)
        if out:
            out.write(line + "\n")
            out.flush()
    survey(chapter, only, log)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
