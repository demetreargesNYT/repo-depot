"""Chapter 4, the city builds itself (Demetre, 2026-11-04): the room's own animations stop placing the city.

    python3 chapters/ch3/scripts/ch3_c4_cleanup2.py --write [--scene PATH]      once, after ch3_c4_cleanup.py

The room's Intro, Waiting, Built and Loop held every stack piece at its final place with constant keys (an import leftover: the
stack arrived with the pan). The new build moves the pieces itself, one layer per building, so those keys go: each keyed
property's final value (the Intro's last frame) is written onto the node as its plain value, and the keys are dropped. Only the
Floor Plane's slide-in (x, 1600 to 0 in the Intro) stays in the room's animations. Crossword_F, the hidden copy that used to show
until frame 142, is plain opacity 0 (the build keeps the pair in step, so it is never needed on top of the Coss pieces).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
from rml_edit import Doc, num
from rml_read import Scene, chapter_dir
from rooms_sheet import Sheet

ROOM = "Chapter 4"
ANIMS = ("Intro", "Waiting", "Built", "Loop")
DEFAULT = {"x": 0.0, "y": 0.0, "opacity": 1.0}


def set_attr(doc, oid, prop, value):
    i = doc.idx(oid)
    line = doc.lines[i]
    tag_end = line.index(">") if ">" in line else len(line)
    head, tail = line[:tag_end], line[tag_end:]
    head = re.sub(r'\s%s="[^"]*"' % prop, "", head, count=1)
    if abs(value - DEFAULT[prop]) > 1e-9:
        at = head.index(" name=") if " name=" in head else head.index(" id=")
        head = head[:at] + f' {prop}="{num(value)}"' + head[at:]
    doc.lines[i] = head + tail


def main(scene):
    sc = Scene(scene)
    sh = Sheet(sc)
    floor = next(e for e in sc.root.iter("Node") if e.get("name") == f"{ROOM} Floor Plane").get("id")
    n_intro = int(sc.animations[f"{ROOM} Intro"].get("duration"))
    ik = sh.anim_keys(sc.animations[f"{ROOM} Intro"])
    doc = Doc(scene)
    moved = []
    for oid, props in ik.items():
        if oid == floor:
            continue
        for prop, keys in props.items():
            assert prop in DEFAULT, (oid, prop)
            set_attr(doc, oid, prop, keys.at(n_intro - 1))
            moved.append((oid, prop, round(keys.at(n_intro - 1), 3)))
        for an in ANIMS:
            doc.drop_object(f"{ROOM} {an}", oid)
    for an in ANIMS:                                         # the Loop must keep one key: a loop with none is not a loop
        pass
    doc.save()
    print(f"cleaned {scene}: {len(moved)} properties now plain values: {moved}")


if __name__ == "__main__":
    if "--write" not in sys.argv:
        raise SystemExit(__doc__)
    main(Path(sys.argv[sys.argv.index("--scene") + 1]) if "--scene" in sys.argv else chapter_dir("ch3") / "scene.rml")
