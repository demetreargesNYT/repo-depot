"""Write docs/rooms.md: one plain-words section per room, read from the chapter's scene.rml.

    python3 tools/rooms_sheet.py ch2            rewrite docs/rooms.md
    python3 tools/rooms_sheet.py ch2 --check    exit 1 if docs/rooms.md is out of date

Run it after any change to a room (an intro, a ball, a loop). The numbers come from the keys, so the sheet cannot drift
from the file. Times are seconds from the start of the intro or the loop. Pieces and the ball are read from each
room's own timelines; nothing is shared between rooms except the backdrop colours and the lockup timing.
"""
import math
import sys
from pathlib import Path

from rml_read import REPO, Scene, chapter_dir

def rooms_of_manifest(scene):
    """[(scene name, room name in the file, what the sheet calls it)] in the manifest's order."""
    return [(x["name"], x["room"], x["title"]) for x in scene.manifest["scenes"] if "room" in x]


EASE_WORDS = {
    "linear": "constant speed", "hold": "stays put", "power1.out": "fast, then a soft stop", "power2.in": "starts slow, speeds up",
    "power2.out": "fast, then eases to a stop", "power2.inOut": "slow, fast, slow", "power1.inOut": "slow, fast, slow (softer)",
    "sine.inOut": "gentle slow, fast, slow", "expo.out": "very fast, then a long settle", "power3.in": "starts very slow, speeds up",
    "back.out": "overshoots a little, then settles", "cubicValue": "the illustrator's own curve", "elastic": "elastic (illustrator's)",
}
PROP_WORDS = {"scaleX": "width", "scaleY": "height", "opacity": "opacity"}


def t(frame, fps):
    return f"{frame / fps:.2f}"


def num(v, prop):
    if prop == "rotation":
        return f"{math.degrees(v):.0f}°"
    return f"{v:.2f}".rstrip("0").rstrip(".") if abs(v) < 10 else f"{v:.0f}"


def bezier_y(x1, y1, x2, y2, frac, v0=0.0, v1=1.0):
    """Value-space (cubicValue) or ease-space curve: the curve's y at time fraction frac, solved by bisection on x."""
    lo, hi = 0.0, 1.0
    for _ in range(50):
        mid = (lo + hi) / 2
        x = 3 * (1 - mid) ** 2 * mid * x1 + 3 * (1 - mid) * mid ** 2 * x2 + mid ** 3
        lo, hi = (mid, hi) if x < frac else (lo, mid)
    u = (lo + hi) / 2
    return (1 - u) ** 3 * v0 + 3 * (1 - u) ** 2 * u * y1 + 3 * (1 - u) * u ** 2 * y2 + u ** 3 * v1


class Keys:
    """One KeyedProperty: [(frame, value, how, control points)] and the value at any frame."""

    def __init__(self, scene, kp):
        self.rows = []
        for k in sorted(kp, key=lambda k: int(k.get("frame", 0))):
            how = k.get("interpolationType", "hold")
            ease = None
            if how == "cubic":
                c = k.find("CubicEaseInterpolator")
                ease = scene.eases_of(c)
                pts = tuple(float(c.get(a, d)) for a, d in (("x1", .42), ("y1", 0), ("x2", .58), ("y2", 1)))
            elif how == "cubicValue":
                c = k.find("CubicValueInterpolator")
                pts = tuple(float(c.get(a, d)) for a, d in (("x1", 0), ("y1", 0), ("x2", 1), ("y2", 0)))
            else:
                pts = None
            self.rows.append((int(k.get("frame", 0)), float(k.get("value", 0)), how, ease, pts))

    def at(self, f):
        rows = self.rows
        if f <= rows[0][0]:
            return rows[0][1]
        for (f0, v0, how, _, pts), (f1, v1, *_) in zip(rows, rows[1:]):
            if f0 <= f < f1:
                u = (f - f0) / (f1 - f0)
                if how == "hold":
                    return v0
                if how == "cubic":
                    return v0 + (v1 - v0) * bezier_y(*pts, u)
                if how == "cubicValue":
                    return bezier_y(*pts, u, v0, v1)
                return v0 + (v1 - v0) * u          # linear, and elastic approximated
        return rows[-1][1]


class Sheet:
    def __init__(self, scene):
        self.s = scene

    def anim_keys(self, anim):
        """{object id: {property: Keys}}"""
        out = {}
        for ko in anim.findall("KeyedObject"):
            for kp in ko.findall("KeyedProperty"):
                if not all(k.tag == "KeyFrameDouble" for k in kp):    # colours and draw targets are not motion
                    continue
                out.setdefault(ko.get("objectId"), {})[kp.get("property")] = Keys(self.s, kp)
        return out

    def descendants(self, node):
        return {e.get("id") for e in node.iter() if e.get("id")}

    def room_node(self, room):
        return self.s.node(f"{room} Room")

    def ball_roots(self, room):
        """The nodes whose x/y carry the ball: the chain from the ball's base shape up to the room."""
        room_node = self.room_node(room)
        base = None
        for e in room_node.iter("Shape"):
            if e.get("name") == "Ball_01_Base":
                base = e
        chain = []
        e = base
        while e is not None and e is not room_node:
            if e.tag == "Node":
                chain.append(e)
            e = self.s.parent.get(e)
        if not chain:  # Wordle, Connections, Shelf: the ball is a node called "<Room> Ball"
            chain = [n for n in room_node.iter("Node") if n.get("name") in (f"{room} Ball",)]
        return chain

    # ------------------------------------------------------------------ rows of the intro
    def segments(self, kf, prop, fps):
        out = []
        for (f0, v0, how, ease, _), (f1, v1, *_) in zip(kf.rows, kf.rows[1:]):
            if how == "hold" or (abs(v1 - v0) < 1e-6):
                continue
            name = "linear" if how == "linear" else (ease or how)
            out.append((f0, f1, v0, v1, name))
        return out

    def describe(self, label, props, fps):
        """Plain sentences for one piece: each property's moves, with squash pairs joined."""
        lines = []
        segs = {p: self.segments(k, p, fps) for p, k in props.items()}
        sx, sy = segs.pop("scaleX", []), segs.pop("scaleY", [])
        for prop, ss in segs.items():
            for f0, f1, v0, v1, ease in ss:
                if prop == "y":
                    what = f"{'rises' if v1 < v0 else 'drops'} {abs(v1 - v0):.0f} px (y {v0:.0f} → {v1:.0f})"
                elif prop == "x":
                    what = f"moves {'right' if v1 > v0 else 'left'} {abs(v1 - v0):.0f} px (x {v0:.0f} → {v1:.0f})"
                elif prop == "rotation":
                    what = f"turns {num(v0, prop)} → {num(v1, prop)}"
                else:
                    what = f"{PROP_WORDS.get(prop, prop)} {num(v0, prop)} → {num(v1, prop)}"
                lines.append(f"{what}, starts {t(f0, fps)} s, takes {(f1 - f0) / fps:.2f} s, {ease} ({EASE_WORDS.get(ease, ease)})")
        if sx or sy:
            ss = sx or sy
            squash = [s for s in ss if abs(s[3] - 1) > 0.015 and abs(s[2] - 1) < 0.0001 or abs(s[3] - 1) > 0.015]
            if squash:
                f0, f1, v0, v1, ease = squash[0]
                w = v1
                h = (sy[0][3] if sy else 1)
                settle = [s for s in ss if abs(s[3] - 1) < 0.0001]
                end = f"back to 1 by {t(settle[-1][1], fps)} s ({settle[-1][4]})" if settle else ""
                lines.append(f"squash on landing: {w:g} wide × {h:g} tall at {t(f1, fps)} s (reached over {(f1 - f0) / fps:.2f} s, {ease}); {end}")
            else:
                for f0, f1, v0, v1, ease in ss:
                    lines.append(f"scale {num(v0, 's')} → {num(v1, 's')}, starts {t(f0, fps)} s, takes {(f1 - f0) / fps:.2f} s, {ease}")
        return lines

    def intro_sections(self, room):
        s = self.s
        a = s.animations[f"{room} Intro"]
        fps = s.fps(a)
        keys = self.anim_keys(a)
        room_node = self.room_node(room)
        balls = self.ball_roots(room)
        ball_ids = set()
        for b in balls:
            ball_ids |= self.descendants(b)
        # a "ball" that is a descendant chain root has its parent chain in `balls`; include all their subtrees
        pieces, ball_rows, lockup, planes, details = [], [], [], [], []
        for oid, props in keys.items():
            label = s.label(oid)
            moving = {p: k for p, k in props.items() if len({round(r[1], 4) for r in k.rows}) > 1}
            if not moving:
                continue
            if label.startswith(f"{room} Lockup"):
                lockup.append((label, moving))
            elif "Plane" in label:
                planes.append((label, moving))
            elif oid in ball_ids:
                if s.by_id[oid].tag == "Node" and ("Ball" in label):
                    ball_rows.append((label, moving))
                else:
                    details.append((label, moving))
            else:
                pieces.append((label, moving))
        return fps, planes, pieces, ball_rows, details, lockup

    # ------------------------------------------------------------------ the loop
    def loop_info(self, room):
        s = self.s
        a = s.animations.get(f"{room} Loop")
        if a is None:
            return None
        fps, n = s.fps(a), s.duration(a)
        keys = self.anim_keys(a)
        chain = self.ball_roots(room)
        pos = []
        for f in range(n):
            x = y = 0.0
            for node in chain:
                k = keys.get(node.get("id"), {})
                x += k["x"].at(f) if "x" in k else float(node.get("x", 0))
                y += k["y"].at(f) if "y" in k else float(node.get("y", 0))
            pos.append((x, y))
        return fps, n, pos, chain, keys

    def moves(self, pos, fps):
        n = len(pos)
        speed = [math.dist(pos[i], pos[(i + 1) % n]) for i in range(n)]
        moving = [v > 0.25 for v in speed]
        runs, i = [], 0
        while i < n:
            if moving[i]:
                j = i
                while j + 1 < n and (moving[j + 1] or any(moving[j + 1:j + 5])):
                    j += 1
                runs.append((i, j + 1))
                i = j + 1
            else:
                i += 1
        out = []
        for a, b in runs:
            b = min(b, n - 1)
            if b <= a:
                continue
            x0, y0 = pos[a]
            x1, y1 = pos[min(b, n - 1)]
            top = min(p[1] for p in pos[a:b + 1])
            lift = min(y0, y1) - top
            out.append((a, b, x1 - x0, y1 - y0, lift))
        return out


def side(dx, dy):
    parts = []
    if abs(dx) >= 3:
        parts.append(f"{abs(dx):.0f} px {'right' if dx > 0 else 'left'}")
    if abs(dy) >= 3:
        parts.append(f"{abs(dy):.0f} px {'down' if dy > 0 else 'up'}")
    return " and ".join(parts) or "ends where it began"


def render(chapter):
    scene = Scene(chapter_dir(chapter) / "scene.rml")
    sh = Sheet(scene)
    out = [header(chapter, scene)]
    for n, room, title in rooms_of_manifest(scene):
        out.append(f"\n## {title} · scene `{n}`\n")
        li = sh.loop_info(room)
        if li:
            fps, frames, pos, chain, lkeys = li
            out.append(f"**Loop:** {frames / fps:.2f} s ({frames} frames at {fps}/s), repeats. First and last frames are the same pose.\n")
        if f"{room} Intro" in scene.animations:
            fps, planes, pieces, ball_rows, details, lockup = sh.intro_sections(room)
            total = scene.duration(scene.animations[f"{room} Intro"]) / fps
            out.append(f"### Intro · exactly {total:.1f} s\n")
            for label, props in planes:
                for line in sh.describe(label, props, fps):
                    out.append(f"- **Floor and front slide in** ({label}): {line}")
            for label, props in sorted(pieces, key=lambda p: min(r[0] for k in p[1].values() for r in k.rows)):
                for line in sh.describe(label, props, fps):
                    out.append(f"- **{label}**: {line}")
            if lockup:
                lines = []
                for label, props in lockup:
                    if label.endswith("Lockup"):
                        k = props.get("opacity")
                        if k:
                            lines.append(f"fades in {t(k.rows[0][0], fps)}–{t(k.rows[1][0], fps)} s, held, fades out ending {t(k.rows[-1][0], fps)} s")
                out.append(f"- **Lockup** (icon and word): {'; '.join(lines)}; hidden when lockup is false (community cards and anon slides)")
            out.append("\n### Ball · intro\n")
            if ball_rows:
                for label, props in ball_rows:
                    for line in sh.describe(label, props, fps):
                        out.append(f"- **{label}**: {line}")
            if details:
                times = [r[0] for _, p in details for k in p.values() for r in k.rows]
                out.append(f"- Highlight and shape ease into the landing pose, {t(min(times), fps)} s to {t(max(times), fps)} s.")
        else:
            out.append("No intro of its own (the file opens on this room, already built).\n")
        if li:
            out.append("\n### Ball · loop\n")
            moves = sh.moves(pos, fps)
            if not moves:
                out.append("- The ball stays put.")
            for i, (a, b, dx, dy, lift) in enumerate(moves, 1):
                hop = f", rising {lift:.0f} px above its start/finish height" if lift > 15 else ""
                out.append(f"- **Move {i}**: {t(a, fps)} s to {t(b, fps)} s ({(b - a) / fps:.2f} s): {side(dx, dy)}{hop}")
            if moves:
                still = [(moves[k][1], moves[k + 1][0]) for k in range(len(moves) - 1) if moves[k + 1][0] - moves[k][1] > 3]
                if still:
                    out.append("- Waits: " + ", ".join(f"{t(a, fps)}–{t(b, fps)} s" for a, b in still))
    return "\n".join(out) + "\n"


TUNE_LATER = """## To tune later

**The ball in The Mini, The Midi and The Crossword does not look quite right, and its easing does not feel like the illustrator's original, even though `tools/compare_room.py` says the loops match.** Known, not fixed. Look into it when the finesse work starts. Best guesses at the cause, most likely first:

1. **The baked rig.** The illustrator's ball is driven by a joystick, a `Ball_Move` solo and the `Ball_Squash` / `Ball_Scale` helper animations. We sampled that rig into direct keys, one per frame where a value moves, thinned where a straight line was "exact" (tolerance 1e-4). Squash and stretch then play as straight lines between whole frames, where the rig mixed several animations with their own easing and could change between frames. Timing that lives between frames, and the overlap of two eases, are flattened.
2. **Squash, stretch and pivots.** The squash is drawn into the ball's shape keys (vertex x/y, in and out handles) and the highlight. Baking turned a rig that scaled around its own origin into keys on the shape. If a pivot, handle rotation or the Solo's active child is read slightly differently, the ball changes shape the wrong way around the floor line even when each frame is close.
3. **Two position nodes.** The Midi (and the other two) place the ball with `Ball_Move` plus a `Ball_01` offset, each with its own curves (some `cubicValue`). We copy both untouched, but our sheet and the Rive runtime may read `cubicValue` or `elastic` keys differently from the Editor's preview, and any ease the Editor shows is the sum of the two.
4. **What the frame comparison cannot see.** It compares whole frames at whole-frame times, ignores differences of 12 colour levels or less, the 30 px border and the floor-line rows (709 to 715), which is exactly where the ball lands and squashes. It also never compares speed (the frame before and after), the hand-off from the intro into the loop, or the loop wrapping from its last frame to its first. A ball that is in the right place on every frame can still move with the wrong easing.
5. **The returns we added.** Where the source loop does not close we added a return at the end (the Midi return is now 20 frames, eased). The ball's easing into and out of that return is ours, not the illustrator's.
6. **Intro hand-off.** Our intro lands the ball on the loop's first pose with our own roll and hop; the source has no intro, so its first loop frames are never seen the way ours are.

Ways to look: play the source's ball and ours at the same size, slowed, and plot ball position and scale per frame for both; compare crops of the ball only, with the floor-line rows included; check the rig's helper animations for keys on half frames; try the room with the ball left un-thinned.

"""

HEADER = """
Generated from `chapters/{chapter}/scene.rml` by `python3 tools/rooms_sheet.py {chapter}`. Do not edit by hand: change the room, then run the
script (it also runs `--check` in `npm run check`). Use it to ask for changes in these terms, for example
"The Mini: Move 2 of the ball 0.1 s slower" or "The Midi Boxes 2 drops 0.05 s later".

Times are seconds from the start of the intro (it is exactly 3.2 s) or of the loop. Every room is self-contained: its intro,
ball and loop are keyed only on its own pieces, so a change in one room never reaches another.

**Easing, in words:** `power2.in` starts slow and speeds up (a drop); `power2.out` is fast, then eases to a stop;
`power2.inOut` and `sine.inOut` are slow, fast, slow; `back.out` overshoots a little then settles (the squash recovery);
`expo.out` is very fast then a long settle (the lockup); `linear` is constant speed.

**Ball moves in the loop** are found from where the ball actually is on each frame (its position nodes added together), so
"Move 2" is the second time the ball travels. "Rising N px" means a hop. Squash and stretch inside a loop are drawn into the
illustrator's shape keys and are not listed here.
"""


def header(chapter, scene):
    """The sheet's top: the ch2 tuning note only for a chapter whose manifest asks for it."""
    note = TUNE_LATER if scene.manifest.get("tuneLaterNote") else ""
    if scene.manifest.get("tuneLater"):
        note = "## To tune later\n\n" + "\n\n".join(f"- {x}" for x in scene.manifest["tuneLater"]) + "\n\n"
    return "# Rooms, in plain words\n\n" + note + HEADER.format(chapter=chapter)


def sheet_path(chapter):
    return REPO / chapter_manifest_path(chapter)


def chapter_manifest_path(chapter):
    return Scene(chapter_dir(chapter) / "scene.rml").manifest.get("roomsSheet", f"docs/rooms-{chapter}.md")


def main(argv):
    if not argv:
        raise SystemExit(__doc__)
    text = render(argv[0])
    target = sheet_path(argv[0])
    if "--check" in argv:
        if not target.exists() or target.read_text() != text:
            print(f"{target.relative_to(REPO)} is out of date: run python3 tools/rooms_sheet.py", argv[0])
            return 1
        print(f"{target.relative_to(REPO)} is up to date")
        return 0
    target.write_text(text)
    print(f"wrote {target.relative_to(REPO)} ({len(text.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
