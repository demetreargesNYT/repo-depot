"""One time (2026-10-30, history like import_room.py): put the old YIG Test file's story into Chapter 1 card 1.

    python3 tools/card1_story.py /tmp/yig-test-2666044/scene.rml          dry run (nothing is written)
    python3 tools/card1_story.py /tmp/yig-test-2666044/scene.rml --write

Run it on card 1 as it was after the roll-ins were delayed (the stand-in ball still in). The old file (Rive file
2666044, read only: pull it into a scratch folder, never push to it) has the ball coming out of the cuckoo clock,
bouncing on the chair and onto the window, the minute hand ticking, and the panes flipping. Its keys are copied
onto the matching pieces of the illustrator's card 1, replacing the stand-in ball. The loop is the ball's journey
(Demetre's scene-loop guideline, docs/rive-plan.md):

  * it starts the moment the intro ends: the ball waits behind the clock door and slides out at frame 0 (the old
    file's frame 41; the 41 frames it held hidden before that are left out), then bounces on the chair and onto the
    window, knocks the panes over, and rolls off the right edge;
  * the ball is removed only once it is out of sight (centre past the artboard edge by its radius) and put back
    behind the clock door, also out of sight; 3 s later (about: the loop is a multiple of 6 frames) it slides out
    of the door again, and the loop repeats;
  * the ball never parks beyond x 1560, so when its room leaves (the front plane travels 1600 left) it is off the
    stage and never shows up in another room (the first build parked it at x 1685 and it floated in card 3);
  * its positions are shifted 7 to 8 px right onto the illustrator's art (the shift eases between the clock, the
    chair, the window and the floor, which sit 0 to 3 px differently in the two files);
  * the nine panes flip as in the old file (scaleY keys), with the face switched on the illustrator's Solo at the
    middle of each flip (the old file crossfades two faces by opacity there); they flip back after the ball has gone;
  * the small loops keep running and are fitted to the full loop (no jump at the loop point): the minute hand turns
    twice (24 ticks, a touch slower than the old file's 30-frame ticks), the pendulum swings 12 times, the dog's
    tail wags 3 times (a cycle 15% shorter than the illustrator's 300 frames), the mouse runs once and waits in its
    hole (the old file's keys, copied), and the dog's eye follows the mouse: it closes as the mouse passes to its
    left, opens again once the mouse has passed back to its right and heads for the hole, and blinks while open
    (the illustrator's blink and closing shapes, the old file's blink times).

The ball no longer rolls in during the intro: it rides in hidden behind the clock door, with the clock's drop.
"""
import copy
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rml_read import chapter_dir  # noqa: E402
from xml_fragments import block_range, parse, ser  # noqa: E402

ROOM = "Chapter 1 Card 1"
BALL, BALL_ART = "9:4805", "9:4806"
MOUSE, PENDULUM, EYE = "12:1", "9:3491", ("9:4188", "9:4191", "9:4189")
CLOCK_HAND_SHAPE = "9:3409"
OLD_ROOM_X, OLD_ROOM_Y = 757.26001, 558.949997   # the old file's Room node, with its Scene node (460) added in y
OLD_HOLD = 41                                      # the old story holds the ball hidden for 41 frames; ours starts there
PAUSE = 180                                        # 3 s between the ball's removal and its next appearance
EXIT_X = 1514                                      # the ball is out of sight past the artboard's right edge (1495 + radius)

# the old art sits 7 to 8 px left of the illustrator's: (old frame, dx, dy) from comparing the two files' clock,
# chair, window and floor; the shift eases between the places the ball touches them
OFFSETS = [(0, 7, -2), (200, 7, -2), (232, 8, 1), (366, 8, 1), (396, 7, 0), (432, 7, 0), (460, 8, 0), (642, 8, 0)]
DOORWAY_LEFT = 647.86 + 7                         # the old Doorway Clip's left edge, in the illustrator's art

# the dog's eye follows the mouse (the mouse's x is the old scurry's, 60.8 right): the dog's head is at about x 830
EYE_CLOSE_AT, EYE_OPEN_AT, EYE_MOVE = 181, 425, 22     # frames: the mouse passes left of the head; passes back right of it
EYE_BLINKS = [43, 83, 503, 573, 593, 683]              # centres of the blinks (the old file's 43, 83, 503, 573, 593)
BLINK = 10                                             # frames each way


def offset(frame):
    for (f0, x0, y0), (f1, x1, y1) in zip(OFFSETS, OFFSETS[1:]):
        if f0 <= frame <= f1:
            t = (frame - f0) / (f1 - f0)
            return x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
    return OFFSETS[-1][1:]


class Ids:
    def __init__(self, text):
        assert 'id="15:' not in text, "ids 15:* are taken"
        self.n = 0

    def __call__(self):
        self.n += 1
        return f"15:{self.n}"


def fmt(v):
    return format(v, ".8g")


def key(ids, frame, value=None, interp=None, cubic=None, tag="KeyFrameDouble"):
    k = parse(f"<{tag}/>")
    if value is not None and not (tag == "KeyFrameDouble" and float(value) == 0):
        k.set("value", fmt(value) if tag == "KeyFrameDouble" else value)
    if interp:
        k.set("interpolationType", interp)
    if frame:
        k.set("frame", str(frame))
    k.set("id", ids())
    if cubic is not None:
        c = parse("<CubicEaseInterpolator/>")
        for a, v in cubic.items():
            c.set(a, v)
        c.set("id", ids())
        k.append(c)
    return k


def prop(ids, name, keys):
    p = parse("<KeyedProperty/>")
    p.set("property", name)
    p.set("id", ids())
    for k in keys:
        p.append(k)
    return p


def kobj(ids, oid, props):
    o = parse("<KeyedObject/>")
    o.set("objectId", oid)
    o.set("id", ids())
    for p in props:
        o.append(p)
    return o


def read_keys(kp):
    """[(frame, value, interpolationType, cubic attribs or None)] of a KeyedProperty."""
    out = []
    for k in kp:
        c = k.find("CubicEaseInterpolator")
        out.append((int(k.get("frame", 0)), float(k.get("value", 0)), k.get("interpolationType"), dict(c.attrib) if c is not None else None))
    return out


def old_keys(root, anim, object_name, prop_name):
    ab = root.find("Artboard")
    byid = {e.get("id"): e for e in ab.iter() if e.get("id")}
    an = next(a for a in ab.findall("LinearAnimation") if a.get("name") == anim)
    for ko in an.findall("KeyedObject"):
        if byid[ko.get("objectId")].get("name") == object_name:
            for kp in ko.findall("KeyedProperty"):
                if kp.get("property") == prop_name:
                    return read_keys(kp)
    raise KeyError((anim, object_name, prop_name))


def old_pane_keys(root, row, col):
    ab = root.find("Artboard")
    byid = {e.get("id"): e for e in ab.iter() if e.get("id")}
    an = next(a for a in ab.findall("LinearAnimation") if a.get("name") == "Ball")
    pane = next(e for e in ab.iter("Node") if e.get("name") == f"Pane R{row}C{col}")
    out = {}
    for ko in an.findall("KeyedObject"):
        e = byid[ko.get("objectId")]
        if e is pane or (e.get("name") == "Face A" and any(e is c for c in pane)):
            for kp in ko.findall("KeyedProperty"):
                out[(e.get("name"), kp.get("property"))] = read_keys(kp)
    return out


def lerp_at(keys, frame):
    """The value of a run of linear keys at a frame (the old ball's keys past the window are all linear)."""
    for (f0, v0, i0, _c0), (f1, v1, _i1, _c1) in zip(keys, keys[1:]):
        if f0 <= frame <= f1:
            assert i0 == "linear", (f0, i0)
            return v0 + (v1 - v0) * (frame - f0) / (f1 - f0)
    raise ValueError(frame)


def main():
    import xml.etree.ElementTree as ET
    old = ET.parse(sys.argv[1]).getroot()
    write = "--write" in sys.argv
    path = chapter_dir("ch1") / "scene.rml"
    text = path.read_text()
    ids = Ids(text)
    lines = text.split("\n")
    a, b = block_range(lines, rf'<LinearAnimation .*name="{ROOM} Loop"')
    orig = parse("\n".join(lines[a:b + 1]))
    assert orig.get("duration") == "600"
    by_obj = {ko.get("objectId"): ko for ko in orig if ko.tag == "KeyedObject"}

    # ---- the ball: the old keys from frame 41, shifted onto the illustrator's art, cut where the ball is out of sight --------
    def shifted(prop_name, anim_node="Clock Ball"):
        out = []
        for f, v, interp, cubic in old_keys(old, "Ball", anim_node, prop_name):
            if f < OLD_HOLD:
                continue
            dx, dy = offset(f)
            if prop_name == "x":
                v = (-128.33 if f == OLD_HOLD else v) + OLD_ROOM_X + dx
            elif prop_name == "y":
                v = v + OLD_ROOM_Y + dy
            out.append([f - OLD_HOLD, v, interp, cubic])
        return out

    keys = {"x": shifted("x"), "y": shifted("y"), "scaleX": shifted("scaleX"), "scaleY": shifted("scaleY"),
            "rotation": shifted("rotation", "Clock Ball Roll")}
    # the frame the ball is out of sight: the first whole frame past EXIT_X, found on the x keys (all linear there)
    exit_frame = min(f for f in range(300, keys["x"][-1][0] + 1) if lerp_at(keys["x"], f) >= EXIT_X)
    removed = exit_frame + 1
    loop_len = removed + PAUSE
    loop_len += (-loop_len) % 6                       # the small loops divide it: 6 pendulum cycles, 24 hand ticks, 3 tail wags
    start = {p: keys[p][0][1] for p in keys}          # the opening pose: hidden behind the door
    for p, ks in keys.items():
        v = lerp_at(ks, exit_frame)
        keys[p] = [k for k in ks if k[0] < exit_frame] + [[exit_frame, v, None, None]]
        keys[p].append([removed, start[p], None, None])
        keys[p].append([loop_len, start[p], None, None])
    # keys that are cut short must not interpolate into the cut: the last original key before it is linear, fine

    def to_keys(ks):
        return [key(ids, f, v, i, c) for f, v, i, c in ks]

    ball_obj = kobj(ids, BALL, [prop(ids, p, to_keys(keys[p])) for p in ("x", "y", "scaleX", "scaleY")])
    roll_obj = kobj(ids, BALL_ART, [prop(ids, "rotation", to_keys(keys["rotation"]))])

    # ---- the panes ------------------------------------------------------------------------------------------------
    wa0, wb0 = block_range(lines, rf'name="{ROOM} Window" id=', 20)
    window = parse("\n".join(lines[wa0:wb0 + 1]))
    solos = {s.get("name"): s for s in window.iter("Solo")}
    pane_objs, pane_start = [], {}
    last_flip = 0
    for row in range(3):
        for col in range(3):
            solo = solos[f"Pane_{row + 1}{'abc'[col]}"]
            tile, sky = [c.get("id") for c in solo if c.tag == "Shape"]
            pk = old_pane_keys(old, row, col)
            sy = [(max(f - OLD_HOLD, 0) if f else 0, v, i, c) for f, v, i, c in pk[("Pane R%dC%d" % (row, col), "scaleY")] if f < 779]
            op = pk[("Face A", "opacity")]
            tile_at = next(f for f, v, *_ in op if f and v == 0.0) - OLD_HOLD
            sky_at = next(f for f, v, *_ in op if f and v == 1.0 and f < 779) - OLD_HOLD
            last_flip = max(last_flip, sy[-1][0])
            for shape in (tile, sky):
                pane_objs.append(kobj(ids, shape, [prop(ids, "scaleY", [key(ids, f, v, i, c) for f, v, i, c in sy])]))
            pane_objs.append(kobj(ids, solo.get("id"), [prop(ids, "activeComponentId", [
                key(ids, 0, sky, tag="KeyFrameId"), key(ids, tile_at, tile, tag="KeyFrameId"), key(ids, sky_at, sky, tag="KeyFrameId")])]))
            pane_start[solo.get("id")] = (tile, sky)
    assert last_flip < exit_frame + PAUSE, "the panes flip back before the ball is next out"

    # ---- the minute hand: two turns of 12 ticks, the old tick shape stretched to fit; never winds back ----------------------
    turns = 2
    g = loop_len / turns / 360
    tick = old_keys(old, "Clock Tick", "Clock Hand B", "rotation")
    hand_keys = []
    for k in range(turns):
        for f, v, i, c in tick:
            if f == 360 and k < turns - 1:
                continue
            hand_keys.append([round((f + 360 * k) * g), v + 2 * math.pi * k, i, c])
    hand_id = ids()
    hand_obj = kobj(ids, hand_id, [prop(ids, "rotation", [key(ids, f, v, i, c) for f, v, i, c in hand_keys])])

    # ---- the small loops, fitted to the loop ---------------------------------------------------------------------------
    def retimed(ko, cycle, copies, mapping):
        """A KeyedObject whose keys are one cycle (frames < cycle) repeated `copies` times, frames mapped by mapping(f, t)."""
        new = copy.deepcopy(ko)
        new.set("id", ids())
        for kp in new.findall("KeyedProperty"):
            kp.set("id", ids())
            ks = list(kp)
            first = [k for k in ks if int(k.get("frame", 0)) < cycle]
            second = [k for k in ks if int(k.get("frame", 0)) >= cycle]
            if second:                                    # the file carries two cycles of the dog's wag; they must match
                assert len(first) == len(second) and all(
                    int(s.get("frame")) - cycle == int(f.get("frame", 0)) and s.get("value") == f.get("value") for f, s in zip(first, second)), \
                    (ko.get("objectId"), kp.get("property"))
            for k in ks:
                kp.remove(k)
            for t in range(copies):
                for k in first:
                    n = copy.deepcopy(k)
                    f = mapping(int(k.get("frame", 0)), t)
                    attrs = dict(n.attrib)
                    n.attrib.clear()
                    for name in ("value", "interpolationType"):
                        if name in attrs:
                            n.set(name, attrs[name])
                    if f:
                        n.set("frame", str(f))
                    n.set("id", ids())
                    for c in n:
                        c.set("id", ids())
                    kp.append(n)
        return new

    wag = loop_len // 3
    dog, pendulum_obj, mouse_obj = [], None, None
    for oid, ko in by_obj.items():
        if oid in (BALL, MOUSE, PENDULUM) or oid in EYE:
            continue
        dog.append(retimed(ko, 300, 3, lambda f, t: round(f * wag / 300) + wag * t))
    swing = loop_len / 12                                  # a pendulum cycle is 120 frames of two 60-frame swings
    pk = by_obj[PENDULUM].find("KeyedProperty")
    pend_keys = [k for k in pk if int(k.get("frame", 0)) < 120]
    pend = copy.deepcopy(by_obj[PENDULUM])
    pend.set("id", ids())
    pp = pend.find("KeyedProperty")
    pp.set("id", ids())
    for k in list(pp):
        pp.remove(k)
    for n_ in range(13):
        src = copy.deepcopy(pend_keys[n_ % 2])
        attrs = dict(src.attrib)
        src.attrib.clear()
        for name in ("value", "interpolationType"):
            if name in attrs:
                src.set(name, attrs[name])
        f = round(n_ * swing)
        if f:
            src.set("frame", str(f))
        src.set("id", ids())
        for c in src:
            c.set("id", ids())
        pp.append(src)
    pendulum_obj = pend

    mouse_obj = copy.deepcopy(by_obj[MOUSE])               # one run, then it waits in its hole until the loop repeats
    mouse_obj.set("id", ids())
    for kp in mouse_obj.findall("KeyedProperty"):
        kp.set("id", ids())
        for k in list(kp):
            k.set("id", ids())
            for c in k:
                c.set("id", ids())
        last = copy.deepcopy(list(kp)[-1])
        assert last.get("frame") == "600"
        last.set("frame", str(loop_len))
        last.set("id", ids())
        for c in last:
            c.set("id", ids())
        kp.append(last)

    # the eye: the illustrator's open, blink and closed shapes and their easing, timed by the mouse
    eye_objs = []
    for oid in EYE:
        ko = by_obj[oid]
        o = kobj(ids, oid, [])
        for kp in ko.findall("KeyedProperty"):
            ks = {int(k.get("frame", 0)): k for k in kp}
            val = lambda f, default: float(ks[f].get("value", 0)) if f in ks else default       # noqa: E731
            opened = val(0, 0.0)
            blink, closed = val(10, opened), val(300, val(278, opened))

            def ease(*frames):
                for f in frames:
                    if f in ks and ks[f].find("CubicEaseInterpolator") is not None:
                        return dict(ks[f].find("CubicEaseInterpolator").attrib) | {"id": None}
                return {}
            to_blink, from_blink, to_closed, to_open = ease(0), ease(10, 0), ease(278, 0), ease(300, 0)
            events = [(0, opened, to_blink)]
            if blink != opened or closed != opened:
                for t_ in EYE_BLINKS:
                    events += [(t_ - BLINK, opened, to_blink), (t_, blink, from_blink), (t_ + BLINK, opened, to_blink)]
                events += [(EYE_CLOSE_AT, opened, to_closed), (EYE_CLOSE_AT + EYE_MOVE, closed, to_open),
                           (EYE_OPEN_AT, closed, to_open), (EYE_OPEN_AT + EYE_MOVE, opened, to_blink)]
            seen, uniq = set(), []
            for f, v, e in sorted(events, key=lambda e: e[0]):
                if f not in seen:
                    seen.add(f)
                    uniq.append((f, v, e))
            o.append(prop(ids, kp.get("property"), [key(ids, f, v, "cubic", {a: b for a, b in e.items() if a != "id"}) for f, v, e in uniq]))
        eye_objs.append(o)

    loop = copy.deepcopy(orig)
    for c in list(loop):
        loop.remove(c)
    for c in dog + [pendulum_obj, mouse_obj] + eye_objs + [ball_obj, roll_obj, hand_obj] + pane_objs:
        loop.append(c)
    loop.set("duration", str(loop_len))

    # ---- the intro and the Waiting pose: the ball rides in hidden with the clock, everything else is held at the loop's start ---
    ia, ib = block_range(lines, rf'<LinearAnimation .*name="{ROOM} Intro"')
    intro = parse("\n".join(lines[ia:ib + 1]))
    clock_drop = None
    for ko in intro:
        if ko.tag == "KeyedObject" and ko.get("objectId") == "9:3528":
            clock_drop = [(int(k.get("frame", 0)), float(k.get("value")), k.find("CubicEaseInterpolator")) for k in ko.find("KeyedProperty")]
    assert clock_drop and clock_drop[0][0] == 60 and clock_drop[1][0] == 90, clock_drop
    lift = clock_drop[0][1] - clock_drop[1][1]

    def hold_objects(with_drop):
        ball_props = [prop(ids, "x", [key(ids, 0, start["x"])])]
        if with_drop:
            ball_props.append(prop(ids, "y", [key(ids, 60, start["y"] + lift, "cubic", dict(clock_drop[0][2].attrib)), key(ids, 90, start["y"])]))
        else:
            ball_props.append(prop(ids, "y", [key(ids, 0, start["y"] + lift)]))
        ball_props += [prop(ids, "scaleX", [key(ids, 0, 1.0)]), prop(ids, "scaleY", [key(ids, 0, 1.0)])]
        objs = [kobj(ids, BALL, ball_props), kobj(ids, BALL_ART, [prop(ids, "rotation", [key(ids, 0, start["rotation"])])]),
                kobj(ids, hand_id, [prop(ids, "rotation", [key(ids, 0, 0.0)])])]
        for solo_id, (tile, sky) in pane_start.items():
            for shape in (tile, sky):
                objs.append(kobj(ids, shape, [prop(ids, "scaleY", [key(ids, 0, 1.0)])]))
            objs.append(kobj(ids, solo_id, [prop(ids, "activeComponentId", [key(ids, 0, sky, tag="KeyFrameId")])]))
        return objs

    def swap_ball(anim, with_drop):
        kept = [c for c in anim if not (c.tag == "KeyedObject" and c.get("objectId") == BALL)]
        for c in list(anim):
            anim.remove(c)
        for c in kept + hold_objects(with_drop):
            anim.append(c)

    swap_ball(intro, True)
    wa, wb = block_range(lines, rf'<LinearAnimation .*name="{ROOM} Waiting"')
    waiting = parse("\n".join(lines[wa:wb + 1]))
    swap_ball(waiting, False)

    # ---- the scene tree: the ball moves to the front of the room's pieces (still inside the room, so it leaves with it),
    # with its doorway clip; the minute hand gets a pivot on the clock face ------------------------------------------------
    ba, bb = block_range(lines, rf'<Node x="1000" y="712" name="{ROOM} Ball"', 16)
    ball_node = parse("\n".join(lines[ba:bb + 1]))
    ball_node.set("x", fmt(start["x"]))
    ball_node.set("y", fmt(start["y"]))
    del ball_node.find("Node").attrib["y"]
    clip_id = ids()
    ball_node.append(parse(f'<ClippingShape sourceId="{clip_id}" name="Ball Doorway Clip" id="{ids()}"/>'))
    clip = parse(f'<Shape x="{fmt(DOORWAY_LEFT)}" y="600" name="{ROOM} Ball Doorway Clip" id="{clip_id}">'
                 f'<Rectangle width="3000" height="2000" originX="0" originY="0.5" name="Path" id="{ids()}"/></Shape>')
    fa = next(i for i, l in enumerate(lines) if rf'name="{ROOM} Front Plane"' in l)
    ha, hb = block_range(lines, rf'<Shape x="43.25" y="18.893499" id="{CLOCK_HAND_SHAPE}"', 36)
    hand = parse("\n".join(lines[ha:hb + 1]))
    del hand.attrib["x"]
    hand.set("y", "-1.8565")
    wrapper = parse(f'<Node x="43.25" y="20.75" name="{ROOM} Clock Hand" id="{hand_id}"/>')
    wrapper.append(hand)

    print(f"loop {loop_len} frames ({loop_len / 60:.2f} s): the ball is out of sight at {exit_frame}, removed at {removed}, "
          f"out again at {loop_len} ({(loop_len - removed) / 60:.2f} s later); dog wag {wag} frames; pendulum half-cycle {swing:.1f}; hand tick {loop_len / 24:.2f}")
    print(f"ball opening pose x {start['x']:.2f} y {start['y']:.2f}; max x {max(k[1] for k in keys['x']):.1f}; intro lift {lift}; last pane flip ends {last_flip}")
    if not write:
        return
    edits = [
        (ia, ib, ser(intro, 2)), (wa, wb, ser(waiting, 2)), (a, b, ser(loop, 2)),
        (ba, bb, None),
        (fa + 1, fa, ser(ball_node, 5) + "                    <!-- where the ball comes out of the cuckoo clock: everything right of the door's left edge -->\n" + ser(clip, 5)),
        (ha, hb, ser(wrapper, 9)),
    ]
    for s, e, new in sorted(edits, key=lambda t: -t[0]):
        lines[s:e + 1] = [] if new is None else new.rstrip("\n").split("\n")
    path.write_text("\n".join(lines))
    print("wrote", path)


if __name__ == "__main__":
    main()
