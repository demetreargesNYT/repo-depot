"""One time (2026-10-30, history like import_room.py): start a room's small loops as soon as its transition ends.

    python3 tools/split_small_loops.py ch1 "Chapter 1 Card 1"          dry run
    python3 tools/split_small_loops.py ch1 "Chapter 1 Card 1" --write

Demetre's review: there was too long a pause between a room finishing its arrival and its small loops (eyes, swaying,
ticking, clouds, tails) starting, because they lived in the room's Loop, which starts after the 3.2 s intro. The
ball's journey stays in the Loop (its timing and the copy's are untouched); the small loops move to a second layer,
"<Room> Small": Small Waiting (their opening pose) while the room waits, then Small Hold (the same pose, 99 frames, to
the end of the pan, 1.65 s) from the moment the room's scene is set, then Small Loop, which repeats for good. They are
the same keys, so a loop that already fitted the Loop's length still does, and the two loops stay in step.

What counts as small is decided per room (SMALL below): the pieces that react to the ball (a mug that squashes when it
lands) stay with it; decor that runs on its own (a tail, a clock hand, a bird, an eye) moves. The Intro and Waiting
timelines no longer hold the small pieces; Small Waiting does.
"""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from delay_ball_rollin import ball_name  # noqa: E402
from rml_read import Scene, chapter_dir  # noqa: E402
from xml_fragments import block_range, parse, ser  # noqa: E402

HOLD_FRAMES = 99          # 1.65 s: the pan ends (its 1.6 s plus a few frames)


def inside(s, oid, ancestor_ids):
    e = s.by_id.get(oid)
    while e is not None:
        if e.get("id") in ancestor_ids:
            return True
        e = s.parent.get(e)
    return False


def card1_story(s, oid):
    """Card 1: the ball, its roll, the panes with their clouds' flips are the story; the rest is decor."""
    e = s.by_id.get(oid)
    name = (e.get("name") or "") if e is not None else ""
    if name in ("Cloud Big", "Cloud Small"):
        return False                      # the drifting clouds are decor, though they sit in the panes
    return inside(s, oid, {"9:3531"}) or name.startswith("Chapter 1 Card 1 Clouds R") or oid in ("9:4805", "9:4806")


# (chapter, room): which keyed objects stay with the ball (and the story). Everything else in the Loop is small.
SMALL = {
    ("ch1", "Start"): lambda s, oid: False,
    ("ch1", "Chapter 1 Card 1"): card1_story,
    ("ch3", "Chapter 3"): lambda s, oid: False,
    ("ch3", "End"): lambda s, oid: False,
    ("ch3", "Bird on Ball"): lambda s, oid: False,
}


# pieces that are small though they sit in the ball's group (the bird that rides on the ball in Chapter 3 card 2)
SMALL_ANYWAY = {("ch3", "Bird on Ball"): lambda s, oid: any((e.get("name") or "") in ("Bird", "Bird_Leg_2") for e in _chain(s, oid))}


def _chain(s, oid):
    e = s.by_id.get(oid)
    while e is not None:
        yield e
        e = s.parent.get(e)


class Ids:
    def __init__(self, text):
        import re
        found = [int(m) for m in re.findall(r'id="16:(\d+)"', text)]
        self.n = max(found, default=0)

    def __call__(self):
        self.n += 1
        return f"16:{self.n}"


def hold_pose(loop_kos, ids):
    """KeyedObjects holding each property at its first key's value, on frame 0 (a one-key pose)."""
    out = []
    for ko in loop_kos:
        new = parse("<KeyedObject/>")
        new.set("objectId", ko.get("objectId"))
        new.set("id", ids())
        for kp in ko.findall("KeyedProperty"):
            first = min(kp, key=lambda k: int(k.get("frame", 0)))
            p = parse("<KeyedProperty/>")
            p.set("property", kp.get("property"))
            p.set("id", ids())
            k = parse(f"<{first.tag}/>")
            for a in ("value",):
                if first.get(a) is not None:
                    k.set(a, first.get(a))
            k.set("id", ids())
            p.append(k)
            new.append(p)
        out.append(new)
    return out


def animation(name, duration, kos, ids, loop=False, one_frame=False):
    a = parse("<LinearAnimation/>")
    if one_frame:
        a.set("fps", "60")
    a.set("duration", str(duration))
    if loop:
        a.set("loopValue", "loop")
    a.set("name", name)
    a.set("id", ids())
    for ko in kos:
        a.append(ko)
    return a


def small_layer(room_layer, mapping, ids, name):
    """The room's own layer, copied: Waiting -> (scene == n) -> a hold -> the loop. mapping: old animation id -> new."""
    layer = copy.deepcopy(room_layer)
    layer.set("name", name)
    idmap = {}
    for e in layer.iter():
        if e.get("id"):
            idmap[e.get("id")] = ids()
            e.set("id", idmap[e.get("id")])
    for e in layer.iter():
        for attr in ("stateToId", "animationId"):
            if e.get(attr):
                e.set(attr, mapping.get(e.get(attr), idmap.get(e.get(attr), e.get(attr))))
    return layer


def main():
    chapter, room = sys.argv[1], sys.argv[2]
    write = "--write" in sys.argv
    path = chapter_dir(chapter) / "scene.rml"
    s = Scene(path)
    text = path.read_text()
    lines = text.split("\n")
    ids = Ids(text)
    story = SMALL[(chapter, room)]

    la, lb = block_range(lines, rf'<LinearAnimation .*name="{room} Loop"')
    loop = parse("\n".join(lines[la:lb + 1]))
    force = SMALL_ANYWAY.get((chapter, room), lambda s, oid: False)
    small = [ko for ko in loop if ko.tag == "KeyedObject" and (force(s, ko.get("objectId")) or
                                                              (not ball_name(s, ko.get("objectId")) and not story(s, ko.get("objectId"))))]
    small_ids = {ko.get("objectId") for ko in small}
    if not small:
        print(room, "has no small loops")
        return
    kept = [c for c in loop if c.tag != "KeyedObject" or c.get("objectId") not in small_ids]
    for c in list(loop):
        loop.remove(c)
    for c in kept:
        loop.append(c)

    dur = loop.get("duration")
    s_loop = animation(f"{room} Small Loop", dur, [copy.deepcopy(ko) for ko in small], ids, loop=True)
    s_wait = animation(f"{room} Small Waiting", 1, hold_pose(small, ids), ids, one_frame=True)
    s_hold = animation(f"{room} Small Hold", HOLD_FRAMES, hold_pose(small, ids), ids)

    def without(name):
        i0, i1 = block_range(lines, rf'<LinearAnimation .*name="{room} {name}"')
        anim = parse("\n".join(lines[i0:i1 + 1]))
        for c in [c for c in anim if c.tag == "KeyedObject" and c.get("objectId") in small_ids]:
            anim.remove(c)
        return i0, i1, anim
    intro, waiting = without("Intro"), without("Waiting")

    # the layer: a copy of the room's own, pointing at the new animations
    ra, rb = block_range(lines, rf'<StateMachineLayer name="{room}" id=', 12)
    room_layer = parse("\n".join(lines[ra:rb + 1]))
    anim_ids = {a.get("name"): a.get("id") for a in s.animations.values()}
    mapping = {anim_ids[f"{room} Waiting"]: s_wait.get("id"), anim_ids[f"{room} Intro"]: s_hold.get("id"), anim_ids[f"{room} Loop"]: s_loop.get("id")}
    layer = small_layer(room_layer, mapping, ids, f"{room} Small")
    end_sm = max(i for i, l in enumerate(lines) if l.strip() == "</StateMachine>")

    print(f"{room}: {len(small)} small pieces leave the Loop ({dur} frames); Small Hold {HOLD_FRAMES} frames, then Small Loop")
    if not write:
        return
    edits = [(la, lb, ser(loop, 2) + ser(s_loop, 2) + ser(s_wait, 2) + ser(s_hold, 2)),
             (intro[0], intro[1], ser(intro[2], 2)), (waiting[0], waiting[1], ser(waiting[2], 2)),
             (end_sm, end_sm - 1, ser(layer, 3))]
    for a, b, new in sorted(edits, key=lambda t: -t[0]):
        lines[a:b + 1] = new.rstrip("\n").split("\n")
    path.write_text("\n".join(lines))
    print("wrote", path)


if __name__ == "__main__":
    main()
