"""The ball's speed on every frame, for finding jerks: python3 tools/ball_speed.py ch2 "The Mini" [--from F --to F] [--keys]

Prints the end of the intro, then the loop twice over (so the wrap shows), as position, speed in units per frame and the
change in speed from the frame before. A jerk is a frame where the speed changes much more than its neighbours', which is
what a thinned or half-frame key looks like. `--keys` lists the position nodes' keys with their ease.
"""
import math
import sys

from rml_read import Scene, chapter_dir
from rooms_sheet import Sheet


def positions(sheet, anim, chain, frames, n):
    keys = sheet.anim_keys(anim)
    out = []
    for f in frames:
        x = y = 0.0
        for node in chain:
            k = keys.get(node.get("id"), {})
            x += k["x"].at(f) if "x" in k else float(node.get("x", 0))
            y += k["y"].at(f) if "y" in k else float(node.get("y", 0))
        out.append((x, y))
    return out


def main(argv):
    chapter, room = argv[0], argv[1]
    s = Scene(chapter_dir(chapter) / "scene.rml")
    sheet = Sheet(s)
    chain = sheet.ball_roots(room)
    intro, loop = s.animations[f"{room} Intro"], s.animations[f"{room} Loop"]
    n = s.duration(loop)
    if "--keys" in argv:
        for name, an in (("Intro", intro), ("Loop", loop)):
            keys = sheet.anim_keys(an)
            for node in chain:
                for prop, k in keys.get(node.get("id"), {}).items():
                    if prop in ("x", "y"):
                        print(f'{name} {node.get("name")} {prop}: ' + " · ".join(f"{f} {v:.2f} ({e or h})" for f, v, h, e, _ in k.rows))
        return 0
    lo = int(argv[argv.index("--from") + 1]) if "--from" in argv else 120
    hi = int(argv[argv.index("--to") + 1]) if "--to" in argv else None
    seq = [("intro", f, p) for f, p in zip(range(lo, 192), positions(sheet, intro, chain, range(lo, 192), 192))]
    seq += [("loop", f, p) for f, p in zip(range(n), positions(sheet, loop, chain, range(n), n))]
    seq += [("loop", f, p) for f, p in zip(range(n), positions(sheet, loop, chain, range(n), n))][:30]
    last_v = None
    prev = None
    for i, (where, f, p) in enumerate(seq):
        if hi is not None and where == "loop" and f > hi and i < len(seq) - 30:
            continue
        if prev is None:
            print(f"{where} {f:3d}  x {p[0]:8.2f} y {p[1]:8.2f}")
        else:
            vx, vy = p[0] - prev[0], p[1] - prev[1]
            v = math.hypot(vx, vy)
            dv = "" if last_v is None else f"{v - last_v:+7.2f}"
            print(f"{where} {f:3d}  x {p[0]:8.2f} y {p[1]:8.2f}  v {v:6.2f}  dv {dv}")
            last_v = v
        prev = p
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
