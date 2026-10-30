"""One time (2026-10-30, history like card1_story.py): Demetre's review of card 1's story, applied to the built card.

    python3 tools/card1_refine.py /tmp/yig-test-2666044/scene.rml          dry run
    python3 tools/card1_refine.py /tmp/yig-test-2666044/scene.rml --write

Runs on card 1 as card1_story.py left it. From the old YIG Test file (Rive file 2666044, read only):

  1. the blue perch under the cuckoo clock's door (the old "Perch", the illustrator's clock Tongue shape); the ball
     rolls out along it;
  2. every place the ball touches something sits on its surface: the old file's contacts are matched to the
     illustrator's art one at a time (perch, shelf, chair, window, dog bed, floor), where the first build used one
     shift for the whole clock-to-shelf stretch and left the ball floating 2 px above the shelf;
  3. the slow white clouds in the nine panes (the old file's Cloud Big and Cloud Small, each pane's own positions and
     start phase), fitted to the 762-frame loop: same speed, passing once per loop, waiting out of sight on the side;
     they hide with the sky when a pane flips to its tile and come back with it;
  4. the plant's sway and drift (old Plant Sway 317 frames, Plant Drift 223), 2 and 3 cycles per loop;
  5. the dog's eye: asleep while the mouse is in front of it (it closes as the mouse approaches, stays closed the whole
     time the mouse is out and passing, and opens once the mouse is past, the old file's 109 to 443);
  6. the dog's tail: 3 wags per loop (the illustrator's first wag, at the illustrator's speed, three times).
"""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from card1_story import (BALL, BALL_ART, EYE, MOUSE, OLD_HOLD, OLD_ROOM_X, OLD_ROOM_Y, PENDULUM, ROOM, EXIT_X, key,  # noqa: E402
                         kobj, lerp_at, old_keys, old_pane_keys, prop, fmt)
from rml_read import chapter_dir  # noqa: E402
from xml_fragments import block_range, parse, ser  # noqa: E402

# the old art against the illustrator's, contact by contact: (old frame, dx, dy). The perch and shelf stretches differ
# by 2 px in height (the clock sits 2 px higher in the illustrator's, the window shelf level with it)
OFFSETS = [(0, 7, -2), (83, 7, -2), (106, 7, 0), (186, 7, 0), (233, 8, 1), (344, 8, 1), (389, 7, 0), (410, 7, 0), (432, 8, 1),
           (461, 8, 1), (506, 8, 0), (642, 8, 0)]
EYE_CLOSE, EYE_OPEN, EYE_MOVE = 90, 435, 30             # asleep as the mouse nears; awake once it is past (old file: 109 and 443)
EYE_BLINKS = [43, 83, 503, 573, 593, 683]
BLINK = 10
WAG_AT = (0, 254, 508)                                  # 3 wags in the 762-frame loop
WAG_END = 114                                           # the illustrator's first wag is done by original frame 114
CLOUD_EDGE = 28                                         # a cloud is out of sight past this, either side of its pane's centre
SWAYS = (381, 2)                                        # plant sway: frames per cycle, cycles; old cycle 317
DRIFTS = (254, 3)                                       # plant drift; old cycle 223
PERCH_AT = (55.85, 70.75)                               # beside the door, as in the old file (12.68 right, 17.5 below the door)


def offset(frame):
    for (f0, x0, y0), (f1, x1, y1) in zip(OFFSETS, OFFSETS[1:]):
        if f0 <= frame <= f1:
            t = (frame - f0) / (f1 - f0)
            return x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
    return OFFSETS[-1][1:]


class Ids:
    def __init__(self, text):
        import re
        self.n = max(int(m) for m in re.findall(r'id="15:(\d+)"', text))

    def __call__(self):
        self.n += 1
        return f"15:{self.n}"


def renumbered(elem, ids):
    for e in elem.iter():
        if e.get("id"):
            e.set("id", ids())
    return elem


def main():
    import xml.etree.ElementTree as ET
    old = ET.parse(sys.argv[1]).getroot()
    write = "--write" in sys.argv
    path = chapter_dir("ch1") / "scene.rml"
    text = path.read_text()
    ids = Ids(text)
    lines = text.split("\n")

    a, b = block_range(lines, rf'<LinearAnimation .*name="{ROOM} Loop"')
    loop = parse("\n".join(lines[a:b + 1]))
    loop_len = int(loop.get("duration"))
    by_obj = {ko.get("objectId"): ko for ko in loop if ko.tag == "KeyedObject"}

    # head's loop: the illustrator's dog, in its own frames
    import subprocess
    head = subprocess.run(["git", "show", "HEAD:YIG2026/rive/chapters/ch1/scene.rml"], capture_output=True, text=True, cwd=chapter_dir("ch1")).stdout.split("\n")
    ha, hb = block_range(head, rf'<LinearAnimation .*name="{ROOM} Loop"')
    head_loop = parse("\n".join(head[ha:hb + 1]))

    # ---- 2. the ball, contact by contact --------------------------------------------------------------------------------
    def shifted(prop_name, anim_node="Clock Ball"):
        out = []
        for f, v, interp, cubic in [k[:4] for k in old_keys(old, "Ball", anim_node, prop_name)]:
            if f < OLD_HOLD:
                continue
            dx, dy = offset(f)
            if prop_name == "x":
                v = (-128.33 if f == OLD_HOLD else v) + OLD_ROOM_X + dx
            elif prop_name == "y":
                v = v + OLD_ROOM_Y + dy
            out.append([f - OLD_HOLD, v, interp, cubic])
        return out

    keys = {"x": shifted("x"), "y": shifted("y"), "scaleX": shifted("scaleX"), "scaleY": shifted("scaleY"), "rotation": shifted("rotation", "Clock Ball Roll")}
    exit_frame = min(f for f in range(300, keys["x"][-1][0] + 1) if lerp_at(keys["x"], f) >= EXIT_X)
    removed = exit_frame + 1
    assert removed + 180 + (-(removed + 180)) % 6 == loop_len, "the loop length must not change"
    start = {p: keys[p][0][1] for p in keys}
    for p, ks in keys.items():
        v = lerp_at(ks, exit_frame)
        keys[p] = [k for k in ks if k[0] < exit_frame] + [[exit_frame, v, None, None], [removed, start[p], None, None], [loop_len, start[p], None, None]]
    to_keys = lambda ks: [key(ids, f, v, i, c) for f, v, i, c in ks]    # noqa: E731
    ball_obj = kobj(ids, BALL, [prop(ids, p, to_keys(keys[p])) for p in ("x", "y", "scaleX", "scaleY")])
    roll_obj = kobj(ids, BALL_ART, [prop(ids, "rotation", to_keys(keys["rotation"]))])

    # ---- 5. the eye ----------------------------------------------------------------------------------------------------
    eye_objs = []
    for oid in EYE:
        o = kobj(ids, oid, [])
        for kp in by_obj[oid].findall("KeyedProperty"):
            ks = {int(k.get("frame", 0)): k for k in head_loop.find(f'KeyedObject[@objectId="{oid}"]').find(f'KeyedProperty[@property="{kp.get("property")}"]')}
            val = lambda f, d: float(ks[f].get("value", 0)) if f in ks else d    # noqa: E731
            opened, blink, closed = val(0, 0.0), val(10, val(0, 0.0)), val(300, val(278, val(0, 0.0)))

            def ease(*frames):
                for f in frames:
                    if f in ks and ks[f].find("CubicEaseInterpolator") is not None:
                        return {a: b for a, b in ks[f].find("CubicEaseInterpolator").attrib.items() if a != "id"}
                return {}
            to_blink, from_blink, to_closed, to_open = ease(0), ease(10, 0), ease(278, 0), ease(300, 0)
            events = [(0, opened, to_blink)]
            if blink != opened or closed != opened:
                for t_ in EYE_BLINKS:
                    events += [(t_ - BLINK, opened, to_blink), (t_, blink, from_blink), (t_ + BLINK, opened, to_blink)]
                events += [(EYE_CLOSE, opened, to_closed), (EYE_CLOSE + EYE_MOVE, closed, to_open), (EYE_OPEN, closed, to_open), (EYE_OPEN + EYE_MOVE, opened, to_blink)]
            seen, uniq = set(), []
            for f, v, e in sorted(events, key=lambda e: e[0]):
                if f not in seen:
                    seen.add(f)
                    uniq.append((f, v, e))
            o.append(prop(ids, kp.get("property"), [key(ids, f, v, "cubic", e) for f, v, e in uniq]))
        eye_objs.append(o)

    # ---- 6. the tail: the illustrator's first wag, three times -----------------------------------------------------------
    dog_objs = []
    for ko in head_loop:
        oid = ko.get("objectId") if ko.tag == "KeyedObject" else None
        if oid is None or oid in (BALL, MOUSE, PENDULUM) or oid in EYE:
            continue
        new = kobj(ids, oid, [])
        for kp in ko.findall("KeyedProperty"):
            first = [k for k in kp if int(k.get("frame", 0)) <= WAG_END]
            assert first, (oid, kp.get("property"))
            np_ = parse("<KeyedProperty/>")
            np_.set("property", kp.get("property"))
            np_.set("id", ids())
            for at in WAG_AT:
                for k in first:
                    n = copy.deepcopy(k)
                    attrs = dict(n.attrib)
                    n.attrib.clear()
                    for name in ("value", "interpolationType"):
                        if name in attrs:
                            n.set(name, attrs[name])
                    f = int(k.get("frame", 0)) + at
                    if f:
                        n.set("frame", str(f))
                    n.set("id", ids())
                    for c in n:
                        c.set("id", ids())
                    np_.append(n)
            new.append(np_)
        dog_objs.append(new)

    # ---- 1/3/4. new pieces in the scene tree ---------------------------------------------------------------------------
    old_ab = old.find("Artboard")
    perch = renumbered(copy.deepcopy(next(e for e in old_ab.iter("Shape") if e.get("name") == "Perch")), ids)
    perch.attrib.clear()
    perch.set("x", fmt(PERCH_AT[0]))
    perch.set("y", fmt(PERCH_AT[1]))
    perch.set("name", f"{ROOM} Perch")
    perch.set("id", ids())
    door_line = next(i for i, l in enumerate(lines) if '<Shape x="43.1675" y="53.25" id="9:3447">' in l)

    wa0, wb0 = block_range(lines, rf'name="{ROOM} Window" id=', 20)
    window = parse("\n".join(lines[wa0:wb0 + 1]))
    parent_of = {c: p for p in window.iter() for c in p}
    solos = {s.get("name"): s for s in window.iter("Solo")}
    cloud_objs, cloud_hold, pane_cloud = [], [], {}
    P = loop_len
    v = 0.088
    span = 2 * CLOUD_EDGE
    total = v * P                                       # how far a cloud travels in one loop
    assert total > span
    old_panes = {e.get("name"): e for e in old_ab.iter("Node") if (e.get("name") or "").startswith("Pane R")}

    def cloud_keys(s0):
        """x keys of one cloud over one loop: it travels at the old speed through -edge..edge, waits out of sight, repeats.
        s0 is its place on the track (0..total) at frame 0; the track is the window's span, then the wait."""
        pts, t, s = [], 0.0, s0
        x = lambda s_: -CLOUD_EDGE + min(s_, span)       # noqa: E731
        pts.append((0, x(s)))
        while t < P:
            to_wrap = (total - s) / v
            if s < span and t + (span - s) / v < P:       # still crossing: reaches the right edge, then waits there
                pts.append((round(t + (span - s) / v), CLOUD_EDGE))
            if t + to_wrap >= P:
                break
            t += to_wrap
            pts.append((round(t), CLOUD_EDGE))
            pts.append((round(t) + 1, -CLOUD_EDGE))
            s = 0.0
            t += 1
        pts.append((P, x((s0 + v * P) % total)))
        out, seen = [], set()
        for f, val in pts:
            if f in seen:
                out.append((f, val))
                continue
            seen.add(f)
            out.append((f, val))
        return out

    for row in range(3):
        for col in range(3):
            solo = solos[f"Pane_{row + 1}{'abc'[col]}"]
            oldpane = old_panes[f"Pane R{row}C{col}"]
            clouds_src = next(n for n in oldpane.iter("Node") if n.get("name") == "Clouds")
            big = next(n for n in clouds_src if n.get("name") == "Cloud Big")
            small = next(n for n in clouds_src if n.get("name") == "Cloud Small")
            rect = next(n for n in oldpane.iter("Shape") if n.get("name") == "Cloud Window")
            cont = parse(f'<Node x="{solo.get("x")}" y="{solo.get("y")}" name="{ROOM} Clouds R{row}C{col}" id="{ids()}"/>')
            wrap = parse(f'<Node name="Clouds" id="{ids()}"/>')
            clip_id = ids()
            cont.append(parse(f'<Shape name="Cloud Window" id="{clip_id}"/>'))
            cont[0].append(parse(f'<Rectangle width="35.169998" height="35.169998" id="{ids()}"/>'))
            wrap.append(parse(f'<ClippingShape sourceId="{clip_id}" name="Glass Clip" id="{ids()}"/>'))
            made = {}
            for nm, src in (("Cloud Big", big), ("Cloud Small", small)):
                c = renumbered(copy.deepcopy(src), ids)
                made[nm] = c
                wrap.append(c)
            cont.append(wrap)
            # the old clouds' start phase on the track, kept: where the cloud is in the old cycle sets where it is in ours
            for nm, c in made.items():
                x0 = float(c.get("x", 0))
                old_lo, old_hi = -29.33, 102.67
                # in the window's own range the phase is the place; out beyond the right edge it waits on the right
                s0 = (x0 + CLOUD_EDGE) if abs(x0) <= CLOUD_EDGE else (x0 - old_lo) / (old_hi - old_lo) * (total - span) + span if x0 > CLOUD_EDGE else 0.0
                s0 = min(max(s0, 0.0), total - 0.01)
                c.set("x", fmt(-CLOUD_EDGE + min(s0, span)))
                cloud_objs.append(kobj(ids, c.get("id"), [prop(ids, "x", [key(ids, f, val, "linear" if i < len(cloud_keys(s0)) - 1 else None) for i, (f, val) in enumerate(cloud_keys(s0))])]))
            # the container flips and hides with its pane
            pk = old_pane_keys(old, row, col)
            sy = [(max(f - OLD_HOLD, 0) if f else 0, vv, i, c) for f, vv, i, c in pk[("Pane R%dC%d" % (row, col), "scaleY")] if f < 779]
            op = pk[("Face A", "opacity")]
            tile_at = next(f for f, vv, *_ in op if f and vv == 0.0) - OLD_HOLD
            sky_at = next(f for f, vv, *_ in op if f and vv == 1.0 and f < 779) - OLD_HOLD
            cloud_hold.append(kobj(ids, cont.get("id"), [prop(ids, "scaleY", [key(ids, f, vv, i, c) for f, vv, i, c in sy]),
                                                         prop(ids, "opacity", [key(ids, 0, 1.0), key(ids, tile_at, 0.0), key(ids, sky_at, 1.0)])]))
            pane_cloud[cont.get("id")] = cont
            at = list(parent_of[solo]).index(solo)
            parent_of[solo].insert(at, cont)

    # the plant: foliage and drift pivot at the pot's rim
    pa, pb = block_range(lines, r'<Node x="30.75" y="95.75" name="Plant" id="9:4352">', 24)
    plant = parse("\n".join(lines[pa:pb + 1]))
    pivot = (-7.5, 30.6)
    foliage_ids = ("9:4353", "9:4392", "9:4398")
    shapes = [c for c in plant if c.get("id") in foliage_ids]
    foliage = parse(f'<Node x="{pivot[0]}" y="{pivot[1]}" name="{ROOM} Plant Foliage" id="{ids()}"/>')
    drift = parse(f'<Node name="{ROOM} Plant Drift" id="{ids()}"/>')
    for sh in shapes:
        sh.set("x", fmt(float(sh.get("x", 0)) - pivot[0]))
        sh.set("y", fmt(float(sh.get("y", 0)) - pivot[1]))
        drift.append(sh)
    foliage.append(drift)
    at = min(list(plant).index(sh) for sh in shapes) if False else 0
    kids = list(plant)
    first = next(i for i, c in enumerate(kids) if c.get("id") in foliage_ids)
    for sh in shapes:
        plant.remove(sh)
    plant.insert(first, foliage)

    def sway(name, cycle_old, cycle_new, copies):
        ks = old_keys(old, name, "Plant Foliage" if name == "Plant Sway" else "Plant Foliage Drift", "rotation")
        out = []
        for t in range(copies):
            for f, vv, interp, cubic, *_ in ks:
                if f == cycle_old and t < copies - 1:
                    continue
                out.append(key(ids, round(f * cycle_new / cycle_old) + cycle_new * t, vv, "cubic", {}))
        return prop(ids, "rotation", out)
    sway_obj = kobj(ids, foliage.get("id"), [sway("Plant Sway", 317, SWAYS[0], SWAYS[1])])
    drift_obj = kobj(ids, drift.get("id"), [sway("Plant Drift", 223, DRIFTS[0], DRIFTS[1])])

    # ---- the animations: swap the regenerated objects in -----------------------------------------------------------
    replaced = {BALL, BALL_ART, *EYE} | {c.get("objectId") for c in dog_objs}
    kept = [c for c in loop if not (c.tag == "KeyedObject" and c.get("objectId") in replaced)]
    for c in list(loop):
        loop.remove(c)
    for c in kept + dog_objs + eye_objs + [ball_obj, roll_obj] + cloud_objs + cloud_hold + [sway_obj, drift_obj]:
        loop.append(c)

    def hold(anim_name, with_drop):
        i0, i1 = block_range(lines, rf'<LinearAnimation .*name="{ROOM} {anim_name}"')
        anim = parse("\n".join(lines[i0:i1 + 1]))
        for c in anim:
            if c.tag == "KeyedObject" and c.get("objectId") == BALL:
                for kp in c.findall("KeyedProperty"):
                    if kp.get("property") == "y" and not with_drop:
                        pass
        for cont in pane_cloud.values():
            anim.append(kobj(ids, cont.get("id"), [prop(ids, "scaleY", [key(ids, 0, 1.0)]), prop(ids, "opacity", [key(ids, 0, 1.0)])]))
        return (i0, i1, anim)
    intro_edit, wait_edit = hold("Intro", True), hold("Waiting", False)

    print(f"loop {loop_len} frames; ball out of sight {exit_frame}, removed {removed}; eye closes {EYE_CLOSE}-{EYE_CLOSE + EYE_MOVE}, "
          f"opens {EYE_OPEN}-{EYE_OPEN + EYE_MOVE}; 3 wags; {len(cloud_objs)} clouds; plant sway x{SWAYS[1]}, drift x{DRIFTS[1]}")
    print("start pose", {p: round(start[p], 2) for p in ("x", "y")})
    if not write:
        return
    edits = [(a, b, ser(loop, 2)), (intro_edit[0], intro_edit[1], ser(intro_edit[2], 2)), (wait_edit[0], wait_edit[1], ser(wait_edit[2], 2)),
             (wa0, wb0, ser(window, 5)), (pa, pb, ser(plant, 6)), (door_line, door_line - 1, ser(perch, 9))]
    for s, e, new in sorted(edits, key=lambda t: -t[0]):
        lines[s:e + 1] = new.rstrip("\n").split("\n")
    path.write_text("\n".join(lines))
    print("wrote", path)


if __name__ == "__main__":
    main()
