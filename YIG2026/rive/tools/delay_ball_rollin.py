"""One time (2026-10-29, history like import_room.py): delay every ball's roll-in so it lands as its intro ends.

    python3 tools/delay_ball_rollin.py ch2            show what would move
    python3 tools/delay_ball_rollin.py ch2 --write    move it

In every room the ball used to land 1.9 to 2.05 s into the 3.2 s intro and sit still until the loop began. Each
room's ball keys (the ball and everything inside it) now move later by one amount, the one that puts its last
key on the intro's last frame. Only the frame numbers change: values, easing and the gaps between keys are
untouched, and a property whose only key is on frame 0 (a pose the ball holds) stays where it is. A room's
Waiting pose equals its intro's first keys, and those keep their values, so nothing else needs rebuilding.
"""
import re
import sys
from pathlib import Path
from rml_read import Scene, chapter_dir


def ball_name(scene, oid):
    """The name of the ball node that holds this object, or None. The wall plane and the masks are not balls."""
    e = scene.by_id.get(oid)
    while e is not None:
        n = e.get("name") or ""
        if e.tag in ("Node", "Shape") and "Ball" in n and "Wall" not in n and "Mask" not in n:
            return n
        e = scene.parent.get(e)
    return None


def plan(scene):
    """{intro name: (shift in frames, [key ids to move])}."""
    out = {}
    for name, anim in scene.animations.items():
        if not name.endswith(" Intro"):
            continue
        moving, last = [], 0
        for ko in anim.findall("KeyedObject"):
            if not ball_name(scene, ko.get("objectId")):
                continue
            for kp in ko.findall("KeyedProperty"):
                keys = sorted(kp, key=lambda k: int(k.get("frame", 0)))
                if len(keys) == 1 and int(keys[0].get("frame", 0)) == 0:
                    continue                       # a held pose, not part of the roll-in
                if int(keys[0].get("frame", 0)) == 0:
                    raise SystemExit(f"{name}: {scene.label(ko.get('objectId'))} {kp.get('property')} starts on frame 0 and has more keys; decide by hand")
                moving += [k.get("id") for k in keys]
                last = max(last, int(keys[-1].get("frame", 0)))
        if moving:
            out[name] = (int(anim.get("duration")) - last, moving)
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    d = chapter_dir(args[0])
    scene = Scene(d / "scene.rml")
    moves = plan(scene)
    shift_by_key = {k: shift for shift, ids in moves.values() for k in ids}
    for name, (shift, ids) in moves.items():
        print(f"{name}: later by {shift} frames ({shift / 60:.3f} s), {len(ids)} keys")
    if "--write" not in sys.argv:
        return
    path = Path(d / "scene.rml")
    out, done = [], 0
    for line in path.read_text().split("\n"):
        m = re.match(r'(\s*<KeyFrame\w+ .*?)\bid="([^"]+)"', line)
        if m and m.group(2) in shift_by_key:
            line, n = re.subn(r'frame="(\d+)"', lambda f: f'frame="{int(f.group(1)) + shift_by_key[m.group(2)]}"', line, count=1)
            done += n
        out.append(line)
    path.write_text("\n".join(out))
    print(f"moved {done} keys")


if __name__ == "__main__":
    main()
