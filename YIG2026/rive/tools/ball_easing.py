"""One time (2026-11-02, history like loading_start.py): smooth the balls of The Mini, The Midi and The Crossword (global pass 2).

    python3 tools/ball_easing.py            dry run: prints the speed per frame before and after, writes nothing
    python3 tools/ball_easing.py --write    rewrite chapters/ch2/scene.rml

What it changes, all on the ball's position keys in the Loop (how the ball enters, the pop and the roll-in, is untouched):
  * the return that closes the loop (The Mini 129 to 149, The Crossword 158 to 179) was a straight line at constant speed, so
    it started and stopped dead; it now eases in and out (power2.inOut) like The Midi's return
  * the loop's first move (The Midi, The Crossword) left the intro's pose at full speed the frame after the ball had stopped;
    it now starts from rest and reaches the old speed within 6 frames, then follows the old path exactly (baked, one key per frame)
  * The Crossword joins two moves at frame 93 with a speed step (6.4 to 4.2 units per frame); the last 12 frames before the join
    and the first 12 after it are re-baked so the speed carries across
Not changed: hidden cuts (the ball is inside a box), contacts (a bounce changes speed on purpose) and The Mini's launch from
under the floor.
"""
import math
import re
import sys
from pathlib import Path

from rml_read import Scene, chapter_dir
from rooms_sheet import Sheet, Keys

POWER2_INOUT = '<CubicEaseInterpolator x1="0.65" y1="0" x2="0.35" y2="1" id="{id}"/>'


def hermite(p0, m0, p1, m1, n, f):
    t = f / n
    return ((2 * t**3 - 3 * t**2 + 1) * p0 + (t**3 - 2 * t**2 + t) * n * m0 + (-2 * t**3 + 3 * t**2) * p1 + (t**3 - t**2) * n * m1)


class Patcher:
    def __init__(self, path):
        self.path = Path(path)
        self.text = self.path.read_text()
        self.scene = Scene(self.path)
        self.next_id = 1 + max(int(i.split(":")[1]) for i in self.scene.by_id if i.startswith("9:"))

    def new_id(self):
        self.next_id += 1
        return f"9:{self.next_id}"

    def block(self, room, obj, prop, anim="Loop"):
        """(start, end) of the KeyedProperty's text in the room's Loop (or another of its animations)."""
        a = self.text.index(f'name="{room} {anim}"')
        k = self.text.index(f'<KeyedObject objectId="{obj}"', a)
        p = self.text.index(f'<KeyedProperty property="{prop}"', k)
        e = self.text.index("</KeyedProperty>", p)
        return p, e + len("</KeyedProperty>")

    def keys_of(self, room, obj, prop):
        anim = self.scene.animations[f"{room} Loop"]
        ko = next(k for k in anim.findall("KeyedObject") if k.get("objectId") == obj)
        kp = next(p for p in ko.findall("KeyedProperty") if p.get("property") == prop)
        return Keys(self.scene, kp)

    def entries(self, p, e):
        """The block's keys as [(frame, text)]."""
        body = self.text[p:e]
        head = body[: body.index(">") + 1]
        out = []
        for m in re.finditer(r"<KeyFrameDouble [^>]*?(?:/>|>.*?</KeyFrameDouble>)", body, re.S):
            fm = re.search(r'frame="(\d+)"', m.group(0).split(">")[0])
            out.append((int(fm.group(1)) if fm else 0, m.group(0)))
        return head, out

    def write_entries(self, p, e, head, entries):
        body = head + "\n" + "\n".join("                    " + t for _, t in sorted(entries)) + "\n                </KeyedProperty>"
        self.text = self.text[:p] + body + self.text[e:]

    def ease_return(self, room, obj, frame):
        """Key `frame` of x and y: its linear move to the next key becomes power2.inOut."""
        for prop in ("x", "y"):
            p, e = self.block(room, obj, prop)
            head, ents = self.entries(p, e)
            out = []
            for f, t in ents:
                if f == frame:
                    assert 'interpolationType="linear"' in t, (room, prop, t)
                    t = t.replace('interpolationType="linear"', 'interpolationType="cubic"')
                    t = re.sub(r"\s*/>$", f'>{POWER2_INOUT.format(id=self.new_id())}</KeyFrameDouble>', t)
                out.append((f, t))
            self.write_entries(p, e, head, out)

    def rebake(self, room, obj, prop, a, b, values):
        """Replace the keys at frames a to b-1 with one linear key per frame (values: {frame: value}); key b is kept."""
        p, e = self.block(room, obj, prop)
        head, ents = self.entries(p, e)
        out = [(f, t) for f, t in ents if not (a <= f < b)]
        assert any(f == b for f, _ in out), (room, prop, b)
        for f in range(a, b):
            frame = f' frame="{f}"' if f else ""
            out.append((f, f'<KeyFrameDouble value="{round(values[f], 4):g}" interpolationType="linear"{frame} id="{self.new_id()}"/>'))
        self.write_entries(p, e, head, out)


def speeds(vals):
    fs = sorted(vals)
    return [math.dist(vals[f], vals[g]) for f, g in zip(fs, fs[1:])]


def soft_start(keys_x, keys_y, n, upto):
    """New x and y values for frames 0 to upto-1: from rest, back on the old path from frame n on."""
    out = {}
    for keys, name in ((keys_x, "x"), (keys_y, "y")):
        v = lambda f: keys.at(f)
        p0, p1, m1 = v(0), v(n), (v(n + 1) - v(n - 1)) / 2
        out[name] = {f: (hermite(p0, 0.0, p1, m1, n, f) if f < n else v(f)) for f in range(upto)}
    return out


def smooth_join(keys, joint, n):
    """Values for frames joint-n to joint+n-1 whose speed carries across the join (Hermite on each side, the join's speed the mean)."""
    v = keys.at
    m_mid = (v(joint + 1) - v(joint - 1)) / 2
    m_a, m_b = (v(joint - n) - v(joint - n - 1)), (v(joint + n + 1) - v(joint + n))
    out = {}
    for f in range(joint - n, joint):
        out[f] = hermite(v(joint - n), m_a, v(joint), m_mid, n, f - (joint - n))
    for f in range(joint, joint + n):
        out[f] = hermite(v(joint), m_mid, v(joint + n), m_b, n, f - joint)
    return out


def main(argv):
    write = "--write" in argv
    pt = Patcher(chapter_dir("ch2") / "scene.rml")
    s = pt.scene
    # the position node each Loop keys for the whole loop (The Midi's other node, The Midi Ball, only moves from frame 97)
    node = {"The Mini": "The Mini Ball", "The Midi": "Ball_01", "The Crossword": "Ball_01"}
    ids = {room: next(n.get("id") for n in Sheet(s).ball_roots(room) if n.get("name") == name) for room, name in node.items()}
    print("ball nodes:", ids)

    # returns
    pt.ease_return("The Mini", ids["The Mini"], 129)
    pt.ease_return("The Crossword", ids["The Crossword"], 158)

    # soft starts: re-read the (already patched) keys from the original file for the old path
    for room, upto in (("The Midi", 32), ("The Crossword", 34)):
        kx, ky = pt.keys_of(room, ids[room], "x"), pt.keys_of(room, ids[room], "y")
        new = soft_start(kx, ky, 6, upto)
        for prop in ("x", "y"):
            pt.rebake(room, ids[room], prop, 0, upto, new[prop])
        old = [math.dist((kx.at(f), ky.at(f)), (kx.at(f + 1), ky.at(f + 1))) for f in range(10)]
        nv = [math.dist((new["x"][f], new["y"][f]), (new["x"][f + 1], new["y"][f + 1])) for f in range(9)]
        print(f"{room} first 10 frames speed, old: {' '.join(f'{x:.1f}' for x in old)}\n{' ' * len(room)} new: {' '.join(f'{x:.1f}' for x in nv)}")

    # The Crossword's join at 93: the keys 71, 93 and 108 are curves, so the whole stretch 71 to 107 is baked, the old path
    # everywhere except within 12 frames of the join
    room = "The Crossword"
    kx, ky = pt.keys_of(room, ids[room], "x"), pt.keys_of(room, ids[room], "y")
    nx, ny = smooth_join(kx, 93, 12), smooth_join(ky, 93, 12)
    bx = {f: kx.at(f) for f in range(71, 108)}
    by = {f: ky.at(f) for f in range(71, 108)}
    bx.update(nx)
    by.update(ny)
    pt.rebake(room, ids[room], "x", 71, 108, bx)
    pt.rebake(room, ids[room], "y", 71, 108, by)
    old = [math.dist((kx.at(f), ky.at(f)), (kx.at(f + 1), ky.at(f + 1))) for f in range(86, 100)]
    nv = [math.dist((bx[f], by[f]), (bx[f + 1], by[f + 1])) for f in range(86, 100)]
    print(f"Crossword frames 86 to 99 speed, old: {' '.join(f'{x:.1f}' for x in old)}\n{' ' * 8}new: {' '.join(f'{x:.1f}' for x in nv)}")

    if write:
        pt.path.write_text(pt.text)
        print("wrote", pt.path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
