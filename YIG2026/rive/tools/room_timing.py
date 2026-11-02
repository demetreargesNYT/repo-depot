"""Write each scene's intro and loop lengths, read from the three scene.rml files, as JSON (for the review page's Finesse panel).

    python3 tools/room_timing.py

Keys are "<file>:<scene>" (file 1, 2 or 3). Times are seconds at 60 fps. A scene's `loop` is its room loop (its work area when it
has one), `small` is the room's Small loop (the layer that starts when the pan ends), `smallStart` is when that layer starts.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rml_read import Scene, chapter_dir  # noqa: E402

FPS = 60
INTRO_FRAMES = 192
PAN_FRAMES = 99     # "<Room> Small Hold": the small loops wait out the pan, then start


def length(anim):
    start, end = anim.get("workStart"), anim.get("workEnd")
    if end is not None:
        return (int(end) - int(start or 0)) / FPS
    return int(anim.get("duration")) / FPS


def main():
    out = {}
    for file_no, ch in enumerate(("ch1", "ch2", "ch3"), 1):
        scene = Scene(chapter_dir(ch) / "scene.rml")
        for s in scene.manifest["scenes"]:
            room = s.get("room")
            entry = {"room": room, "kind": s["kind"]}
            if s["name"] == "loading":
                entry["loop"] = length(scene.animations["Start Loading Loop"])
            elif room:
                entry["intro"] = INTRO_FRAMES / FPS
                if f"{room} Loop" in scene.animations:
                    entry["loop"] = length(scene.animations[f"{room} Loop"])
                if f"{room} Small Loop" in scene.animations:
                    entry["small"] = length(scene.animations[f"{room} Small Loop"])
                    entry["smallStart"] = PAN_FRAMES / FPS
            out[f"{file_no}:{s['name']}"] = entry
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
