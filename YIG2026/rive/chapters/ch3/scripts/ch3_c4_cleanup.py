"""Chapter 4, new direction (Demetre, 2026-11-04): card 1 has no ball and the city comes alive; card 2 has the proud ball alone.

    python3 chapters/ch3/scripts/ch3_c4_cleanup.py --write [--scene PATH]     once, on the scene as committed in 0e325fa

Clears the way for the city and ball workers:
- deletes the crowd (Chapter 4 Crowd Ball A to D, their five Crowd animations and the "Chapter 4 Crowd" layer);
- takes the ball's journey and the F/B depth switches out of the room's Intro, Loop, Built and Waiting: the ball node and its
  inner nodes are no longer keyed there (the Ball layer will own them), and each F or B copy's opacity holds its Intro end value
  in the Loop (it only switched so the old journey could pass in front of or behind the stack);
- moves the ball to the first child of the floor plane (drawn in front of the whole city), parked below the floor, off stage.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
from rml_edit import Doc
from rml_read import Scene, chapter_dir
from rooms_sheet import Sheet

ROOM = "Chapter 4"
BALL_IDS = ("9:43975", "9:43976", "9:43978")         # the ball node, Ball_01 and the spin node (keyed by the old journey)
SWITCHED = ("Crossword_F", "Coss_F", "Coss_B", "SpB_02_F")


def main(scene):
    sc = Scene(scene)
    sh = Sheet(sc)
    ids = {e.get("id"): e for e in sc.root.iter() if e.get("id")}
    room = next(e for e in sc.root.iter("Node") if e.get("name") == f"{ROOM} Room")
    by = {}
    for e in room.iter():
        by.setdefault(e.get("name"), e)
    intro_end = {}
    ik = sh.anim_keys(sc.animations[f"{ROOM} Intro"])
    n_intro = int(sc.animations[f"{ROOM} Intro"].get("duration"))
    for name in SWITCHED:
        oid = by[name].get("id")
        intro_end[oid] = ik[oid]["opacity"].at(n_intro - 1)
    doc = Doc(scene)

    def drop_block(oid):
        i = doc.idx(oid)
        j = doc.end(i)
        del doc.lines[i:j + 1]

    # ---- the crowd
    layer = next(l for l in sc.root.iter("StateMachineLayer") if l.get("name") == f"{ROOM} Crowd")
    drop_block(layer.get("id"))
    for k in ("Away", "Wait", "Arrive", "Idle", "Leave"):
        a = next(e for e in sc.root.iter("LinearAnimation") if e.get("name") == f"{ROOM} Crowd {k}")
        drop_block(a.get("id"))
    for g in "ABCD":
        drop_block(by[f"{ROOM} Crowd Ball {g}"].get("id"))
    # ---- the old journey and its depth switches
    for an in (f"{ROOM} Intro", f"{ROOM} Loop", f"{ROOM} Built", f"{ROOM} Waiting"):
        for oid in BALL_IDS:
            doc.drop_object(an, oid)
        for oid, v in intro_end.items():
            if an == f"{ROOM} Loop":
                doc.set_prop(an, oid, "opacity", [(0, v, "hold")])
    # ---- the ball: first child of the floor plane, parked below the floor and off the left edge
    ball = by[f"{ROOM} Ball"]
    i = doc.idx(ball.get("id"))
    j = doc.end(i)
    block = doc.lines[i:j + 1]
    del doc.lines[i:j + 1]
    block[0] = re.sub(r'x="[^"]*" y="[^"]*"', 'x="-60" y="2400"', block[0], count=1)
    plane = doc.idx(next(c for c in room if c.get("name") == f"{ROOM} Floor Plane").get("id"))
    doc.lines[plane + 1:plane + 1] = block
    doc.save()
    print(f"cleaned {scene}: crowd gone, ball journey and depth switches out of the room's animations; F/B opacity holds {intro_end}")


if __name__ == "__main__":
    if "--write" not in sys.argv:
        raise SystemExit(__doc__)
    scene = Path(sys.argv[sys.argv.index("--scene") + 1]) if "--scene" in sys.argv else chapter_dir("ch3") / "scene.rml"
    main(scene)
