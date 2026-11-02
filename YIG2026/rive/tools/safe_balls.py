"""One time (2026-11-02, history like ball_easing.py): bring the balls inside the safe area (x 560 to 935, y 0 to 812; global pass 4).

    python3 tools/safe_balls.py            dry run: prints the new extents, writes nothing
    python3 tools/safe_balls.py --write    rewrite chapters/ch2/scene.rml and chapters/ch3/scene.rml

A ball's whole body counts: its centre stays at least one radius inside (35.4 for the balls with a Ball_01_Scale chain, 17.7 for
Connections and the Chapter 3 and 4 stand-ins). Only the ball moves; no other piece does, and how the ball enters (the roll-in
from beyond the left edge, the pop) is untouched except that its last stop is the new resting place.
  * The Mini: the ball's x path (580 to 921) is squeezed to 596 to 899 (an even 0.888 scale about the left end), so it still
    comes out of the left box, lands on the same block and drops into the right cube
  * Connections: the roll to the left (616 to 550) is shortened to 616 to 578.5, the spin with it (the ball still rolls without slipping)
  * Chapter 3: the stand-in rests at x 748 on the front floor between the cage and the blocks, not at x 1030 right of the safe area
  * Chapter 4: the stand-in rests at x 600 on the yellow block, not x 577 (its left edge reached x 559)
"""
import re
import sys

from ball_easing import Patcher
from rml_read import chapter_dir

NUM = r"-?\d+(?:\.\d+)?(?:e-?\d+)?"


def fmt(v):
    return repr(round(v, 5))


def remap(pt, room, obj, prop, anim, fn):
    """Apply fn to every key value and every cubicValue control value of one property."""
    p, e = pt.block(room, obj, prop, anim)
    body = pt.text[p:e]
    body = re.sub(rf'(<KeyFrameDouble\b[^>]*?\bvalue=")({NUM})(")', lambda m: m.group(1) + fmt(fn(float(m.group(2)))) + m.group(3), body)
    body = re.sub(rf'(<CubicValueInterpolator\b[^>]*?\by1=")({NUM})(")', lambda m: m.group(1) + fmt(fn(float(m.group(2)))) + m.group(3), body)
    body = re.sub(rf'(<CubicValueInterpolator\b[^>]*?\by2=")({NUM})(")', lambda m: m.group(1) + fmt(fn(float(m.group(2)))) + m.group(3), body)
    pt.text = pt.text[:p] + body + pt.text[e:]


def set_key(pt, room, obj, prop, anim, frame, value):
    p, e = pt.block(room, obj, prop, anim)
    body = pt.text[p:e]
    for m in re.finditer(r"<KeyFrameDouble\b[^>]*>", body):
        tag = m.group(0)
        if re.search(rf'\bframe="{frame}"', tag) and re.search(r'\bvalue="', tag):
            body = body[:m.start()] + re.sub(rf'(\bvalue=")({NUM})(")', lambda v: v.group(1) + fmt(value) + v.group(3), tag, count=1) + body[m.end():]
            pt.text = pt.text[:p] + body + pt.text[e:]
            return
    raise AssertionError((room, prop, anim, frame))


def set_node_x(pt, name, old, new):
    """The node's own x, which the Waiting pose and the keys override but a reader of the file sees."""
    m = re.search(rf'<Node [^>]*?\bx="{re.escape(old)}"[^>]*?name="{re.escape(name)}"|<Node [^>]*?name="{re.escape(name)}"[^>]*?\bx="{re.escape(old)}"', pt.text)
    assert m, (name, old)
    seg = m.group(0)
    pt.text = pt.text[:m.start()] + seg.replace(f'x="{old}"', f'x="{new}"', 1) + pt.text[m.end():]


def node_id(pt, name):
    return next(n.get("id") for n in pt.scene.artboard.iter("Node") if n.get("name") == name)


def main(argv):
    write = "--write" in argv
    # ---- chapter 2
    pt = Patcher(chapter_dir("ch2") / "scene.rml")
    # The Mini
    mini = node_id(pt, "The Mini Ball")
    lo, hi, new_lo, new_hi = 579.5, 920.82, 596.0, 899.0
    a = (new_hi - new_lo) / (hi - lo)
    f = lambda x: new_lo + (x - lo) * a
    remap(pt, "The Mini", mini, "x", "Loop", f)
    set_key(pt, "The Mini", mini, "x", "Intro", 183, f(665.5))
    set_node_x(pt, "The Mini Ball", "665.5", fmt(f(665.5)))
    print(f"The Mini: x {lo:g}..{hi:g} -> {new_lo:g}..{new_hi:g} (scale {a:.4f}); rest 665.5 -> {f(665.5):.1f}")
    # Connections
    con = node_id(pt, "Connections Ball")
    k = (616.07001 - 578.5) / (616.07001 - 550.0)
    g = lambda x: 616.07001 + (x - 616.07001) * k
    remap(pt, "Connections", con, "x", "Loop", g)
    spin = next(n.get("id") for n in pt.scene.artboard.iter("Node") if n.get("name") == "Connections Ball Spin")
    remap(pt, "Connections", spin, "rotation", "Loop", lambda r: r * k)
    print(f"Connections: roll 616.07..550 -> 616.07..578.5 (scale {k:.4f}), spin scaled the same")
    if write:
        pt.path.write_text(pt.text)
    # ---- chapter 3
    p3 = Patcher(chapter_dir("ch3") / "scene.rml")
    c3, c4 = node_id(p3, "Chapter 3 Ball"), node_id(p3, "Chapter 4 Ball")
    set_key(p3, "Chapter 3", c3, "x", "Intro", 192, 748.0)
    set_node_x(p3, "Chapter 3 Ball", "1030.5", "748")
    set_key(p3, "Chapter 4", c4, "x", "Intro", 177, 600.0)
    set_node_x(p3, "Chapter 4 Ball", "577", "600")
    print("Chapter 3: rest x 1030.5 -> 748; Chapter 4: rest x 577 -> 600")
    if write:
        p3.path.write_text(p3.text)
        print("wrote ch2 and ch3 scene.rml")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
