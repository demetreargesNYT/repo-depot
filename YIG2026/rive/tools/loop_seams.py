"""One time (2026-11-02, history like ball_easing.py): close two Chapter 1 loops (global pass 3).

    python3 tools/loop_seams.py            dry run
    python3 tools/loop_seams.py --write    rewrite chapters/ch1/scene.rml

  * Chapter 1 card 2: the return that closes the loop (frames 180 to 239) was a straight line at constant speed, so it
    started and stopped dead; it now eases in and out (power2.inOut)
  * Chapter 1 card 5: the ball jumped 257 units at the wrap. It now slides from the right tile top back to the first one over
    frames 177 to 179, hidden behind the letter tiles, so the loop closes on one pose (openLoops is empty)
"""
import sys

from ball_easing import Patcher
from rml_read import chapter_dir
from rooms_sheet import Sheet


def add_key(pt, room, obj, prop, frame, value):
    p, e = pt.block(room, obj, prop)
    head, ents = pt.entries(p, e)
    ents.append((frame, f'<KeyFrameDouble value="{value!r}" interpolationType="linear" frame="{frame}" id="{pt.new_id()}"/>'))
    pt.write_entries(p, e, head, ents)


def main(argv):
    pt = Patcher(chapter_dir("ch1") / "scene.rml")
    sheet = Sheet(pt.scene)
    ball = lambda room: next(n.get("id") for n in sheet.ball_roots(room) if n.get("name") == f"{room} Ball")
    pt.ease_return("Chapter 1 Card 2", ball("Chapter 1 Card 2"), 180)
    room, obj = "Chapter 1 Card 5", ball("Chapter 1 Card 5")
    add_key(pt, room, obj, "x", 177, 875.5)       # the ball waits hidden at the right tile top until here
    add_key(pt, room, obj, "x", 179, 618.30444)       # and is back at the first one when the loop wraps
    if "--write" in argv:
        pt.path.write_text(pt.text)
        print("wrote", pt.path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
