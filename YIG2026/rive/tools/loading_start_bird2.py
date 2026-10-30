"""One time (2026-10-30, history): Start's Loop bird choreography, third version (Demetre: one motion caused by the ball).

    python3 tools/loading_start_bird2.py --write

Version 2 had the bird kick up 14 frames after the ball's top (sine out starts at full speed: a second push). Now the bird
separates near the top with an ease that starts at zero relative speed, drifts up 15 px, and comes back on a soft curve
that overshoots a hair and settles, landing 10 frames after the ball has settled, with a small squash. The pause between
bounces is longer (the loop is 4.5 s, 270 frames); the blinks are in the still part (frames 30 and 215).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import loading_start as L  # noqa: E402
from import_room import Ids  # noqa: E402
from rml_read import chapter_dir  # noqa: E402
from xml_fragments import parse, ser  # noqa: E402

RETIME = {190: 215, 194: 219, 198: 223, 202: 227, 206: 231, 240: 270}


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
    anims["Start Loop"].set("duration", str(L.LOOP_FRAMES))
    anims["Start Small Loop"].set("duration", str(L.LOOP_FRAMES))
    for ko in anims["Start Small Loop"].findall("KeyedObject"):
        for kp in ko.findall("KeyedProperty"):
            for k in kp:
                f = int(k.get("frame", 0))
                if f in RETIME:
                    k.set("frame", str(RETIME[f]))
    if "--write" in argv:
        path.write_text(ser(root))
        print("wrote", path)


if __name__ == "__main__":
    main(sys.argv[1:])
