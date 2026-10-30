"""One time (2026-10-30, history): Start's Loop bird choreography, second version (Demetre's review of Part 1).

    python3 tools/loading_start_bird.py --write

The bird's motion must read as caused by the ball. Version 1 had the bird hop on its own after the ball landed. Now it is
carried up with the ball, keeps rising a little as the ball comes down (launched), then falls back on its own, slower and
softer than the ball, and lands on the settled ball with a small squash. LOOP and BLINK in loading_start.py hold the keys;
this rewrites Start Loop and retimes the blinks (30, and 190 for the double) in the built file. Also thins the ball's
outline: the ball art is drawn at scale 2, so its 1.5 px stroke is 0.75 here, which draws 1.5 px, like the bird's.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import loading_start as L  # noqa: E402
from import_room import Ids  # noqa: E402
from rml_read import chapter_dir  # noqa: E402
from xml_fragments import parse, ser  # noqa: E402

RETIME = {60: 30, 64: 34, 68: 38, 160: 190, 164: 194, 168: 198, 172: 202, 176: 206}


def main(argv):
    path = chapter_dir("ch1") / "scene.rml"
    text = path.read_text()
    root = parse(text)
    ids = Ids(text)
    ab = root.find("Artboard")
    named = {e.get("name"): e.get("id") for e in ab.iter("Node")}
    nodes = {"ball": named["Start Ball"], "squash": named["Start Ball Squash"], "ride": named["Start Bird Carrier"], "bird": named["Start Bird"]}
    anims = {a.get("name"): a for a in ab.findall("LinearAnimation")}
    L.make_animation_content(anims["Start Loop"], L.LOOP, nodes, ids)
    for ko in anims["Start Small Loop"].findall("KeyedObject"):
        for kp in ko.findall("KeyedProperty"):
            for k in kp:
                f = int(k.get("frame", 0))
                if f in RETIME:
                    k.set("frame", str(RETIME[f]))
    for st in named_strokes(ab):
        st.set("thickness", "0.75")
    if "--write" in argv:
        path.write_text(ser(root))
        print("wrote", path)


def named_strokes(ab):
    art = next(e for e in ab.iter("Node") if e.get("name") == "Start Ball Art")
    return list(art.iter("Stroke"))


if __name__ == "__main__":
    main(sys.argv[1:])
