"""One time (2026-10-30, history like import_room.py): File 1's Loading and Start become one room, the Start room.

    python3 tools/loading_start.py            dry run (checks, writes nothing)
    python3 tools/loading_start.py --write    rewrite chapters/ch1/scene.rml

Demetre: drop the illustrator's old Start room art completely. Loading is the empty cream-and-orange room with just the
standard ball bouncing in the centre. Start is the same picture (no pan, no floor or colour change): the bird drops in and
lands on top of the ball; the loop is the ball bouncing about every 4 s, the bird hopping up and landing back on top, and
the bird blinking now and then. "Let's go" is the room's ordinary exit (a pan to the left, leaving the empty room).

So there is one room, "Start", and the scene `loading` has no room of its own (like `ad`):
  - the Start layer opens on a ball-bouncing timeline (Start Loading A/B, the same one-second timeline twice, so each pass
    ends at the end of a bounce); when scene becomes start it waits for the pass to end, so the ball is at rest, and plays
    the Intro (the bird drops in). The Intro's first frame is the Loading loop's last, so nothing jumps
  - a scene that is neither loading nor start sends the layer to Start Hidden (the ball off the stage), for a review jump
    straight from Loading to a later scene; the real flow always goes through Start
  - the ball is the Bird on Ball room's art (File 3), the bird is that room's bird with its blink, copied here with new ids
The Loading room, its layers and its timelines are gone. Start Floor Clip, the floor plane's art and the old ball rig too.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from import_room import Ids, fresh, fnum, bezier_ease  # noqa: E402
from rml_read import chapter_dir  # noqa: E402
from xml_fragments import parse, ser  # noqa: E402

EASE = {
    "power2.out": (0.33, 1, 0.68, 1), "power2.in": (0.32, 0, 0.67, 0), "power2.inOut": (0.65, 0, 0.35, 1),
    "back.out": (0.34, 1.56, 0.64, 1), "sine.inOut": (0.37, 0, 0.63, 1),
    "sine.out": (0.61, 1, 0.88, 1), "power1.in": (0.11, 0, 0.5, 0),
    "soft.land": (0.4, 0, 0.6, 1.35),            # soft in, lands with a small overshoot and settles back
}
SCENE_PATH, SCENE_START, SCENE_LOADING = "1:14-1:2713", "1:9101", "1:9100"
BALL_X, FLOOR = 748.0, 712.0
BALL_R2 = 70.72                       # the ball's diameter (the Bird on Ball ball: 35.36 at scale 2)
RIDE_REST = -17.68                    # the bird's carrier sits this far above the ball's floor contact (as in Bird on Ball)
BIRD_REST, BIRD_HIDDEN = -58.0, -778.0  # the bird's feet node in the carrier: on the ball, and above the stage
BIRD_X = 6.0
LOOP_FRAMES, INTRO_FRAMES, HOLD_FRAMES = 270, 192, 99
HIDDEN_X = -300.0


def carrier(sy):
    """The bird's carrier follows the ball's top while the ball squashes or stretches about its floor contact."""
    return RIDE_REST + BALL_R2 * (1 - sy)


# ---- timelines: {(node, property): [(frame, value, the ease that leaves this key or None)]}
def squash(keys):
    sx = [(f, x, e) for f, x, y, e in keys]
    sy = [(f, y, e) for f, x, y, e in keys]
    ride = [(f, carrier(y), e) for f, x, y, e in keys]
    return sx, sy, ride


LOADING_LOOP = {
    "frames": 60,
    "ball_y": [(0, 712, "power2.out"), (18, 640, "power2.in"), (36, 712, None), (60, 712, None)],
    "squash": [(0, 1, 1, None), (36, 1, 1, "power2.out"), (40, 1.18, 0.82, "back.out"), (52, 1, 1, None), (60, 1, 1, None)],
}
INTRO = {
    "frames": INTRO_FRAMES,
    "ball_y": [(0, FLOOR, None), (INTRO_FRAMES, FLOOR, None)],
    # the bird lands at frame 84 and the ball squashes under it
    "squash": [(0, 1, 1, None), (84, 1, 1, "power2.out"), (88, 1.12, 0.86, "back.out"), (108, 1, 1, None), (INTRO_FRAMES, 1, 1, None)],
    "bird_y": [(0, BIRD_HIDDEN, None), (30, BIRD_HIDDEN, "power2.in"), (84, BIRD_REST, None), (INTRO_FRAMES, BIRD_REST, None)],
    "bird_sx": [(0, 1, None), (84, 1, "power2.out"), (88, 1.15, "back.out"), (106, 1, None), (INTRO_FRAMES, 1, None)],
    "bird_sy": [(0, 1, None), (84, 1, "power2.out"), (88, 0.8, "back.out"), (106, 1, None), (INTRO_FRAMES, 1, None)],
}
LOOP = {
    "frames": LOOP_FRAMES,
    # the ball hops every 4.5 s: crouch, stretch, up, down, squash. The bird is carried up with it (no push of its own); near
    # the top it separates smoothly (eased in, so there is no kick) and drifts up a little, then comes back down on a soft
    # curve that overshoots a hair and settles, landing at frame 134, ten frames after the ball has settled (124), with a small squash
    "ball_y": [(0, FLOOR, None), (60, FLOOR, "power2.out"), (84, FLOOR - 58, "power2.in"), (108, FLOOR, None), (LOOP_FRAMES, FLOOR, None)],
    "squash": [(0, 1, 1, None), (48, 1, 1, "sine.inOut"), (58, 1.1, 0.88, "power2.out"), (66, 0.95, 1.08, "sine.inOut"), (84, 1, 1, None),
               (108, 1, 1, "power2.out"), (112, 1.14, 0.84, "back.out"), (124, 1, 1, None), (LOOP_FRAMES, 1, 1, None)],
    "bird_y": [(0, BIRD_REST, None), (76, BIRD_REST, "sine.inOut"), (100, BIRD_REST - 15, "soft.land"), (134, BIRD_REST, None), (LOOP_FRAMES, BIRD_REST, None)],
    "bird_sx": [(0, 1, None), (76, 1, "sine.inOut"), (88, 0.97, "sine.inOut"), (100, 1, None), (134, 1, "power2.out"), (138, 1.12, "back.out"), (154, 1, None), (LOOP_FRAMES, 1, None)],
    "bird_sy": [(0, 1, None), (76, 1, "sine.inOut"), (88, 1.06, "sine.inOut"), (100, 1, None), (134, 1, "power2.out"), (138, 0.84, "back.out"), (154, 1, None), (LOOP_FRAMES, 1, None)],
}
def _value(keys, f):
    """A keyed series evaluated at frame f (each key's ease shapes the segment that leaves it)."""
    for (f0, v0, e), (f1, v1, _) in zip(keys, keys[1:]):
        if f0 <= f <= f1:
            if v0 == v1:
                return v0
            if e is None:                  # no ease: linear, as Rive plays it
                return v0 + (v1 - v0) * (f - f0) / (f1 - f0)
            x1, y1, x2, y2 = EASE[e]
            return v0 + (v1 - v0) * bezier_ease(x1, y1, x2, y2, (f - f0) / (f1 - f0))
    return keys[-1][1]


def bird_keys():
    """The bird's own y (in its carrier), baked per frame while it is airborne. The carrier follows the ball's top (squash and
    all) while the bird sits on it, and is held still from frame 78 to the end of the loop, so the ball's squash as it lands
    cannot reach the bird in the air (that was a second jump). The ball's hop still carries the bird (it is the ball's child),
    so the bird's y cancels it. The bird's path in the air is one smooth curve: it leaves the ball's rise near the top with
    the ball's own speed, drifts up to its peak at frame 92, then falls on a soft quadratic and lands at 134."""
    f0, f_peak, f_land = 78, 92, 134
    def ball_top(f):
        return _value(LOOP["ball_y"], f) + RIDE_REST + BIRD_REST
    p0, v0 = ball_top(f0), ball_top(f0 + 1) - ball_top(f0)
    peak, land = ball_top(f_peak) - 9.0, ball_top(f_land)
    out = [(0, BIRD_REST, None)]
    for f in range(f0, f_land + 1):
        if f <= f_peak:                    # Hermite from (p0, v0) to (peak, 0)
            u, n = (f - f0) / (f_peak - f0), f_peak - f0
            h00, h10, h01 = 2*u**3 - 3*u**2 + 1, u**3 - 2*u**2 + u, -2*u**3 + 3*u**2
            a = h00 * p0 + h10 * n * v0 + h01 * peak
        else:
            u = (f - f_peak) / (f_land - f_peak)
            a = peak + (land - peak) * u * u
        out.append((f, round(a - _value(LOOP["ball_y"], f) - RIDE_REST, 3), None))
    out += [(140, BIRD_REST - 2.5, "power2.out"), (151, BIRD_REST, None), (LOOP_FRAMES, BIRD_REST, None)]
    return out


# The ball's hop is keyed frame by frame (linear keys on the eased curve), not as two eased segments: the bird rides the ball
# (it is the ball's child) and its own keys cancel the ball's hop, which only stays exact if the ball plays exactly the numbers
# the bird was computed from. With eased segments Rive's curve differed from the model by up to 5 px near the landing, and the
# bird popped up when the ball stopped (a second jump).
_hop = LOOP["ball_y"]
LOOP["ball_y"] = [(0, FLOOR, None)] + [(f, round(_value(_hop, f), 3), None) for f in range(60, 109)] + [(LOOP_FRAMES, FLOOR, None)]

# the carrier follows the squash through the stretch (to frame 66), eases to rest by 78 and stays there
_sq = [(f, carrier(y), e) for f, x, y, e in LOOP["squash"] if f <= 66]
LOOP["ride"] = _sq[:-1] + [(_sq[-1][0], _sq[-1][1], "sine.inOut"), (78, RIDE_REST, None), (LOOP_FRAMES, RIDE_REST, None)]


LOOP["bird_y"] = bird_keys()

# the bird blinks twice per loop: once, then twice (the Bird on Ball blink, frames 30-38 and 61-77 there)
BLINK = {30: 70, 34: 74, 38: 78, 61: 120, 65: 124, 69: 128, 73: 132, 77: 136}   # small-loop frames; see the note in docs/rive-plan.md


def double_key(frame, value, ease, ids):
    k = {"interpolationType": "cubic"} if ease else {}
    e = parse(f'<KeyFrameDouble id="{ids()}"/>')
    if value:
        e.set("value", fnum(value))
    if frame:
        e.set("frame", str(frame))
    if ease:
        e.set("interpolationType", "cubic")
        c = parse(f'<CubicEaseInterpolator x1="{EASE[ease][0]}" y1="{EASE[ease][1]}" x2="{EASE[ease][2]}" y2="{EASE[ease][3]}" id="{ids()}"/>')
        e.append(c)
    return e


def keyed(obj_id, props, ids):
    ko = parse(f'<KeyedObject objectId="{obj_id}" id="{ids()}"/>')
    for prop, keys in props.items():
        kp = parse(f'<KeyedProperty property="{prop}" id="{ids()}"/>')
        for f, v, e in keys:
            kp.append(double_key(f, v, e, ids))
        ko.append(kp)
    return ko


def make_animation_content(anim, spec, nodes, ids, with_x=False, with_bird=True, with_ball=True):
    for ko in list(anim.findall("KeyedObject")):
        anim.remove(ko)
    ball, sq, ride, bird = nodes["ball"], nodes["squash"], nodes["ride"], nodes["bird"]
    props = {"y": spec["ball_y"]}
    if with_x:
        props["x"] = [(0, BALL_X, None), (spec["frames"], BALL_X, None)]
    anim.append(keyed(ball, props, ids))
    sx, sy, rd = squash(spec["squash"])
    rd = spec.get("ride", rd)
    anim.append(keyed(sq, {"scaleX": sx, "scaleY": sy}, ids))
    if with_bird:
        anim.append(keyed(ride, {"y": rd}, ids))
        anim.append(keyed(bird, {"y": spec["bird_y"], "scaleX": spec["bird_sx"], "scaleY": spec["bird_sy"]}, ids))


def one_frame(anim, values, ids):
    for ko in list(anim.findall("KeyedObject")):
        anim.remove(ko)
    for obj, props in values:
        anim.append(keyed(obj, {p: [(0, v, None)] for p, v in props.items()}, ids))


def transition(to, ids, conds=(), exit_time=False):
    """conds: [(property path, 'equal' | 'notEqual', enum value id)] all of which must hold (and the exit time, if asked)."""
    t = parse(f'<StateTransition stateToId="{to}" duration="0" id="{ids()}"/>')
    if exit_time:
        t.set("enableExitTime", "true")
        t.set("exitTimeIsPercetange", "true")
        t.set("exitTime", "100")
    for op, value in conds:
        t.append(parse(
            f'<TransitionViewModelCondition opValue="{op}" id="{ids()}"><TransitionPropertyViewModelComparator id="{ids()}">'
            f'<BindablePropertyEnum id="{ids()}"><DataBindContext sourcePathIds="{SCENE_PATH}" propertyKey="637" id="{ids()}"/></BindablePropertyEnum>'
            f'</TransitionPropertyViewModelComparator><TransitionValueEnumComparator value="{value}" id="{ids()}"/></TransitionViewModelCondition>'))
    return t


def build(text, bird_src_text):
    root = parse(text)
    ab = root.find("Artboard")
    ids = Ids(text)
    by_id = {e.get("id"): e for e in root.iter() if e.get("id")}
    parent = {c: p for p in root.iter() for c in p}
    anims = {a.get("name"): a for a in ab.findall("LinearAnimation")}
    src = parse(bird_src_text)
    src_by_id = {e.get("id"): e for e in src.iter() if e.get("id")}
    room = by_id["9:2441"]
    assert room.get("name") == "Start Room"

    # ---- the ball (art from Bird on Ball) and the bird, copied with new ids
    idmap = {}
    ball_art = fresh(src_by_id["9:32449"], ids, idmap)
    bird = fresh(src_by_id["9:32384"], ids, idmap)
    leg2 = fresh(src_by_id["9:32365"], ids, idmap)
    ball_art.set("name", "Start Ball Art")
    ball_art.set("y", fnum(-35.36))                 # centre of the ball: its radius above the floor contact
    for n in (bird, leg2):
        n.attrib.pop("x", None)
        n.attrib.pop("y", None)                     # they sit on the feet node below
    feet = parse(f'<Node x="{fnum(BIRD_X)}" y="{fnum(BIRD_HIDDEN)}" name="Start Bird" id="{ids()}"/>')
    feet.extend([bird, leg2])                       # Bird draws above its second leg, as in Bird on Ball
    ride = parse(f'<Node y="{fnum(RIDE_REST)}" name="Start Bird Carrier" id="{ids()}"/>')
    ride.append(feet)
    sq = parse(f'<Node name="Start Ball Squash" id="{ids()}"/>')
    sq.append(ball_art)
    ball = parse(f'<Node x="{fnum(BALL_X)}" y="{fnum(FLOOR)}" name="Start Ball" id="{ids()}"/>')
    ball.extend([ride, sq])                         # the bird draws above the ball
    nodes = {"ball": ball.get("id"), "squash": sq.get("id"), "ride": ride.get("id"), "bird": feet.get("id")}

    # ---- the room: the old ball and the floor plane's art and clip go; the new ball takes the old ball's place in the draw order
    old_ball = next(c for c in room if c.get("name") == "Start Ball")
    room.insert(list(room).index(old_ball), ball)
    room.remove(old_ball)
    for c in list(room):
        if c.get("name") == "Start Floor Clip":
            room.remove(c)
    plane = next(c for c in room if c.get("name") == "Start Floor Plane")
    for c in list(plane):
        plane.remove(c)

    # ---- the Loading room goes
    loading_room = by_id["9:44"]
    assert loading_room.get("name") == "Loading Room"
    parent[loading_room].remove(loading_room)
    for name in [n for n in anims if n.startswith("Loading ")]:
        ab.remove(anims.pop(name))
    sm = ab.find("StateMachine")
    for layer in list(sm.findall("StateMachineLayer")):
        if layer.get("name") in ("Loading", "Loading Exit", "Loading Draw"):
            sm.remove(layer)

    # ---- timelines
    make_animation_content(anims["Start Intro"], INTRO, nodes, ids, with_x=True)
    anims["Start Intro"].set("duration", str(INTRO_FRAMES))
    first = {
        nodes["ball"]: {"x": BALL_X, "y": FLOOR},
        nodes["squash"]: {"scaleX": 1, "scaleY": 1},
        nodes["ride"]: {"y": carrier(1)},
        nodes["bird"]: {"y": BIRD_HIDDEN, "scaleX": 1, "scaleY": 1},
    }
    for ko in list(anims["Start Waiting"].findall("KeyedObject")):
        anims["Start Waiting"].remove(ko)
    one_frame(anims["Start Waiting"], list(first.items()), ids)
    make_animation_content(anims["Start Loop"], LOOP, nodes, ids)
    anims["Start Loop"].set("duration", str(LOOP_FRAMES))

    def new_anim(name, after, **attrs):
        a = parse(f'<LinearAnimation name="{name}" id="{ids()}"/>')
        for k, v in attrs.items():
            a.set(k, str(v))
        ab.insert(list(ab).index(after) + 1, a)
        anims[name] = a
        return a

    loading = new_anim("Start Loading Loop", anims["Start Waiting"], duration=LOADING_LOOP["frames"])
    make_animation_content(loading, LOADING_LOOP, nodes, ids, with_bird=False)
    hidden = new_anim("Start Hidden", loading, fps=60, duration=1)
    one_frame(hidden, [(nodes["ball"], {"x": HIDDEN_X})], ids)

    # ---- the bird's blink: the Eye's four vertices, from Bird on Ball, on the new bird
    src_anim = next(a for a in src.iter("LinearAnimation") if a.get("name") == "Bird on Ball Small Loop")
    eye_objs = [ko for ko in src_anim.findall("KeyedObject")]
    small, small_wait, small_hold = anims["Start Small Loop"], anims["Start Small Waiting"], anims["Start Small Hold"]
    for a in (small, small_wait, small_hold):
        for ko in list(a.findall("KeyedObject")):
            a.remove(ko)
    for ko in eye_objs:
        new_id = idmap[ko.get("objectId")]
        loop_ko = parse(f'<KeyedObject objectId="{new_id}" id="{ids()}"/>')
        wait_ko = parse(f'<KeyedObject objectId="{new_id}" id="{ids()}"/>')
        hold_ko = parse(f'<KeyedObject objectId="{new_id}" id="{ids()}"/>')
        for kp in ko.findall("KeyedProperty"):
            by_frame = {int(k.get("frame", 0)): k for k in kp}
            lp = parse(f'<KeyedProperty property="{kp.get("property")}" id="{ids()}"/>')
            plan = [(0, 0)] + sorted((new, old) for old, new in BLINK.items()) + [(LOOP_FRAMES, 38)]
            for new, old in plan:
                if old not in by_frame:      # a property that stays put through the blink has no key there
                    continue
                k = fresh(by_frame[old], ids, {})
                if new:
                    k.set("frame", str(new))
                else:
                    k.attrib.pop("frame", None)
                lp.append(k)
            loop_ko.append(lp)
            for target in (wait_ko, hold_ko):
                wp = parse(f'<KeyedProperty property="{kp.get("property")}" id="{ids()}"/>')
                k = fresh(by_frame[0], ids, {})
                for child in list(k):
                    k.remove(child)
                k.attrib.pop("interpolationType", None)
                k.attrib.pop("frame", None)
                wp.append(k)
                target.append(wp)
        small.append(loop_ko)
        small_wait.append(wait_ko)
        small_hold.append(hold_ko)
    small.set("duration", str(LOOP_FRAMES))

    # ---- the Start layer: ball bouncing (twice, so a pass ends at the end of a bounce) -> Intro -> Loop
    layer = next(l for l in sm.findall("StateMachineLayer") if l.get("name") == "Start")
    for c in list(layer):
        layer.remove(c)
    a, b, hid, intro, loop = (ids() for _ in range(5))
    layer.append(parse(f'<AnyState x="160" y="200" id="{ids()}"/>'))
    layer.append(parse(f'<ExitState x="720" y="200" id="{ids()}"/>'))
    entry = parse(f'<EntryState x="0" y="0" id="{ids()}"/>')
    entry.append(parse(f'<StateTransition stateToId="{a}" id="{ids()}"/>'))
    layer.append(entry)
    for sid, other, x in ((a, b, 160), (b, a, 160)):
        st = parse(f'<AnimationState animationId="{loading.get("id")}" x="{x}" y="{0 if sid == a else 120}" id="{sid}"/>')
        st.append(transition(hid, ids, [("notEqual", SCENE_LOADING), ("notEqual", SCENE_START)]))     # at once: nothing of Loading shows in another scene
        st.append(transition(intro, ids, [("equal", SCENE_START)], exit_time=True))
        st.append(transition(other, ids, exit_time=True))
        layer.append(st)
    st = parse(f'<AnimationState animationId="{hidden.get("id")}" x="160" y="240" id="{hid}"/>')
    st.append(transition(intro, ids, [("equal", SCENE_START)]))
    layer.append(st)
    st = parse(f'<AnimationState animationId="{anims["Start Intro"].get("id")}" x="400" y="0" id="{intro}"/>')
    st.append(transition(loop, ids, exit_time=True))
    layer.append(st)
    layer.append(parse(f'<AnimationState animationId="{anims["Start Loop"].get("id")}" x="640" y="0" id="{loop}"/>'))
    return root


def dangling(root):
    ids = {e.get("id") for e in root.iter() if e.get("id")}
    bad = []
    for e in root.iter():
        for k, v in e.attrib.items():
            if k not in ("id", "name") and re.fullmatch(r"\d+:\d+", v or "") and v not in ids and k not in ("value", "enumId"):
                bad.append((e.tag, e.get("name") or e.get("id"), k, v))
    return bad


def main(argv):
    write = "--write" in argv
    path = chapter_dir("ch1") / "scene.rml"
    text = path.read_text()
    if "Start Loading Loop" in text:
        raise SystemExit("already done")
    bird_text = (chapter_dir("ch3") / "scene.rml").read_text()
    root = build(text, bird_text)
    bad = dangling(root)
    print("dangling references:", bad[:20] if bad else "none")
    if write and not bad:
        path.write_text(ser(root))
        print("wrote", path)


if __name__ == "__main__":
    main(sys.argv[1:])
