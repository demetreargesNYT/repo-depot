"""Community (scene chapter-2-community-intro, Chapter 2.5's card "The rest of the world also came to play."): the cat, the ball with
the bird on top, and the dog on its cushion, all on the floor line. At rest the ball sits in front of the mouse hole and hides it. Every
few seconds the ball hops (a light, playful hop: gather, launch, hang, land), the mouse slides out of the hole to the left, has a quick
look and darts back in, and the bird, which rode up with the ball, floats a touch longer and comes down after it.

Built from existing art, copied in as new elements (nothing in File 1 or File 3 is touched):
* the cat and the dog (File 3's End room, `chapters/ch3/scene.rml`) with their idles exactly as drawn (End Small Loop's keys);
* the bird and its blink (File 1's Start room), the hole, the mouse and the hole's mask (File 1's Chapter 1 card 1);
* the ball is Chapter 2's standard ball art (the Bridge Art artboard's ball, as common.prepare_ball takes it), 67.4 across;
* the room's moves, layers and draw rule are copied from Wordle's, with new ids; the backdrop pose is the old `Bridge Colors`, renamed
  `Community Colors` because the checks look for "<Room> Colors".

Layout (artboard units, the group centred on the phone crop's centre, 747.5, so there is room on both sides): ball centre x 719.7,
hole under it, the cat 590 to 643 and the dog 782 to 903.

The loop (481 frames, 8.0 s; frame 0 is the intro's last frame): the ball rests; at LAUNCH - 9 it gathers (4.5 percent), at LAUNCH it
leaves (3 percent stretch), flies a clean parabola at the project gravity (rise 56, air time 33.5 frames), lands (6 percent, once) and
settles. The bird rides the ball's top, separates while the ball is still rising, goes on a little, hangs, and comes down on its own
ease to touch the ball 9.5 frames after the ball landed (its feet show only while it is off the ball), with a 3.5 percent dip. The
mouse slides out (6 frames, ease out), looks (a tiny nose-up tilt), turns and darts back in nose first, tail last (6 frames, ease in).

Small Loop (the cat's, the dog's and the bird's blink): copied key for key from the End and Start rooms; the loop is 481 frames, so each
holds its own last pose (which is its first) after its drawn cycle. The cat's drawn cycle is 384 frames; File 3 cut it at 300 and the
cat jumped at the seam; here it plays out whole.
"""
import math
import re

from common import RIVE_DIR, BallArt, Doc, INTRO, bake, emit, prepare_ball, rebuild_built, smooth
from rml_edit import num

ROOM = "Community"
SCENE_VALUE = "1:9110"                      # chapter-2-community-intro in the Scene enum
OLD_COLORS = "Bridge Colors"

# ---- layout ---------------------------------------------------------------------------------------------------------------------
SHIFT = -28.0                               # the reference group (x 621 to 930, centre 775.5) moved to the crop's centre (747.5)
FLOOR = 712.0
D = 67.4                                    # the ball's diameter
R = D / 2
K = R / 17.678                              # Ball_01's scale
RC = 17.2 * K                               # centre to the floor line at rest (the stroke sits a little into the surface)
BALL_X = 747.7 + SHIFT
REST_Y = FLOOR - RC                         # the ball's centre at rest
HOLE_X = 747.25 + SHIFT                     # the hole's node (its arch is 18.75 wide, centred 0.125 to the right of it)
CAT_X, CAT_Y = 618.65, 680.5                # File 3's Cat 2 node, moved so the cat's box centres on 616.8
DOG_X, DOG_Y = 842.0, 686.0                 # File 3's Dog node, moved so the dog's box centres on 842
BIRD_DX = 6.0                               # the bird's origin right of the ball's centre (File 1's Start)
BIRD_OVER = 4.96                            # and above the ball's top (feet 1.6 px into the ball's outline)
BIRD_FEET = 5.0                             # the foot ticks sit 5 below the bird's origin; the squash pivots there
BIRD_Y0 = REST_Y - R - BIRD_OVER            # the bird's origin at rest

MOUSE_Y = 706.0
MOUSE_HIDE = 34.0                           # mouse node x minus hole x, behind the mask (File 1's rest is 28.56; facing right its tail points
                                            # left, so it has to go 5 further to be wholly behind the mask)
MOUSE_OUT = -4.0                            # and at the look: the head half out of the hole's left edge
MOUSE_PIVOT = -5.3                          # the head's centre in the mouse node's space: the turn pivots there
MASK_DX = 9.5                               # the mask's edge: right of the hole node

# ---- the intro (192 frames) -----------------------------------------------------------------------------------------------------
ROLL = (30, 128)                            # the ball rolls in from off the left edge, easing to a stop
START_X = -80.0
PAN = (3, 93)                               # the plane (cat, dog, hole) slides in on the pan, like every room's
PLANE_WAIT = 1600.0

# ---- the loop (481 frames) ------------------------------------------------------------------------------------------------------
G = 0.40                                    # the project gravity, units per frame squared
RISE = 56.0                                 # how high the ball's bottom goes: clears the hole's top (19.5) by 36
V0 = math.sqrt(2 * G * RISE)
T = 2 * V0 / G                              # air time in frames (33.5)
L = 480
LAUNCH = 80
GATHER, GATHER_A = 9, 0.045                 # frames and amount of the squash before the launch
STRETCH_A = 0.03                            # the stretch as it leaves the floor, back to round by 12 frames
LAND_A, LAND_OVER = 0.06, 0.012             # the landing squash, and the one tiny overshoot on the way back
TS = 8                                      # the bird lets go this many frames after the launch (the ball is still rising)
BIRD_TA, BIRD_GAP_TOP = 17.5, 8.0           # its own top (frames after the launch) and how far above the ball it is when the ball tops out
BIRD_DELAY = 9.5                            # touch-down this many frames after the ball lands (0.16 s)
BIRD_DIP = 0.035                            # the bird's dip on landing
FEET_MIN_GAP = 1.2                          # the feet show while the bird is at least this far off the ball's top
MOUSE_T = dict(out=(4.0, 10.0), tilt=(10.0, 14.5), turn=(14.5, 17.5), dart=(17.5, 23.5))
TILT = 0.17                                 # radians, nose up


def ease_out(u):
    u = min(1.0, max(0.0, u))
    return 1 - (1 - u) ** 2


def ease_in(u):
    u = min(1.0, max(0.0, u))
    return u * u


def seg(t, a, b, v0, v1):
    """v0 -> v1 over t in [a, b] on a smooth step."""
    return v0 + (v1 - v0) * smooth((t - a) / (b - a))


# ---- the plan: every series, pure arithmetic --------------------------------------------------------------------------------------
def ball_h(t):
    """The ball's rise (its bottom's height above rest) t frames after the launch."""
    return V0 * t - 0.5 * G * t * t if 0 < t < T else 0.0


def ball_sy(t):
    """The ball's height scale: gather, stretch, landing squash. Volume is constant (scaleX = 1 / scaleY)."""
    if -GATHER <= t < 0:
        return 1 - GATHER_A * smooth((t + GATHER) / GATHER)
    if 0 <= t < 3:
        return seg(t, 0, 3, 1 - GATHER_A, 1 + STRETCH_A)
    if 3 <= t < 12:
        return seg(t, 3, 12, 1 + STRETCH_A, 1.0)
    u = t - T
    if 0 <= u < 3:
        return seg(u, 0, 3, 1.0, 1 - LAND_A)
    if 3 <= u < 10:
        return seg(u, 3, 10, 1 - LAND_A, 1 + LAND_OVER)
    if 10 <= u < 16:
        return seg(u, 10, 16, 1 + LAND_OVER, 1.0)
    return 1.0


def top_h(t):
    """The ball's top, as a height above its rest top."""
    return ball_h(t) + 2 * R * (ball_sy(t) - 1)


def _hermite(p0, m0, p1, m1, a, b, t):
    s = (t - a) / (b - a)
    h = b - a
    return (p0 * (2 * s ** 3 - 3 * s ** 2 + 1) + m0 * h * (s ** 3 - 2 * s ** 2 + s) + p1 * (-2 * s ** 3 + 3 * s ** 2) + m1 * h * (s ** 3 - s ** 2))


def _slope(f, t, e=0.05):
    return (f(t + e) - f(t - e)) / (2 * e)


TE = T + BIRD_DELAY


def _bird_top_height():
    """The bird's own top, found so that it is BIRD_GAP_TOP above the ball's top at the moment the ball tops out."""
    lo, hi = 50.0, 90.0
    for _ in range(60):
        mid = (lo + hi) / 2
        v = _hermite(top_h(TS), _slope(top_h, TS), mid, 0.0, TS, BIRD_TA, T / 2)
        if v - top_h(T / 2) < BIRD_GAP_TOP:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


BIRD_TOP = _bird_top_height()


def bird_h(t):
    """The bird's origin height above rest: on the ball's top until it lets go, up a little more, a hang, then its own soft descent to
    the ball (zero speed relative to where the ball's top is moving at touch-down), then on the ball again."""
    if t < TS:
        return top_h(t)
    if t < BIRD_TA:
        return _hermite(top_h(TS), _slope(top_h, TS), BIRD_TOP, 0.0, TS, BIRD_TA, t)
    if t < TE:
        return _hermite(BIRD_TOP, 0.0, top_h(TE), _slope(top_h, TE), BIRD_TA, TE, t)
    return top_h(t)


def bird_sy(t):
    u = t - TE
    if 0 <= u < 4:
        return seg(u, 0, 4, 1.0, 1 - BIRD_DIP)
    if 4 <= u < 12:
        return seg(u, 4, 12, 1 - BIRD_DIP, 1.0)
    return 1.0


def feet_visible(t):
    """0 to 1: the foot ticks show while the bird is off the ball, fading over 2 frames at each end."""
    gap = bird_h(t) - top_h(t)
    if t < TS or t > TE:
        return 0.0
    # on the way up the gap grows from zero; on the way down it closes to zero at TE
    return 1.0 if gap >= FEET_MIN_GAP else 0.0


def mouse_state(t):
    """(x offset from the hole node, rotation, scaleX) of the mouse t frames after the launch."""
    o0, o1 = MOUSE_T["out"]
    t0, t1 = MOUSE_T["tilt"]
    u0, u1 = MOUSE_T["turn"]
    d0, d1 = MOUSE_T["dart"]
    if t <= o0:
        return MOUSE_HIDE, 0.0, 1.0
    if t < o1:
        return MOUSE_HIDE + (MOUSE_OUT - MOUSE_HIDE) * ease_out((t - o0) / (o1 - o0)), 0.0, 1.0
    rot = 0.0
    if t0 <= t < t1:
        mid = (t0 + t1) / 2
        rot = TILT * (smooth((t - t0) / (mid - t0)) if t < mid else 1 - smooth((t - mid) / (t1 - mid)))
    x = MOUSE_OUT
    sx = 1.0
    if u0 <= t < u1:
        sx = 1 - 2 * smooth((t - u0) / (u1 - u0))
    elif t >= u1:
        sx = -1.0
    if d0 <= t < d1:
        x = MOUSE_OUT + (MOUSE_HIDE - MOUSE_OUT) * ease_in((t - d0) / (d1 - d0))
    elif t >= d1:
        x = MOUSE_HIDE
    return x, rot, sx if t < d1 else -1.0


def mouse_loop_end_sx():
    """After the dart the mouse is hidden and faces right; it turns back to face left while hidden, before the loop ends."""
    return 1.0


def mouse_full(t):
    x, rot, sx = mouse_state(t)
    if t >= 28.0:                                   # hidden behind the mask: turn back round (the flip cannot be seen)
        sx = 1.0
    return x, rot, sx


def plan():
    """Every series the room needs, keyed by loop frame or intro frame."""
    out = {"intro": {}, "loop": {}}
    # ---- the intro: the ball rolls in with the bird on its top
    f0, f1 = ROLL
    dist = BALL_X - START_X
    intro = {k: {} for k in ("bx", "bth", "byo", "bird_x", "bird_y", "plane", "mouse")}
    for f in range(INTRO):
        u = min(1.0, max(0.0, (f - f0) / (f1 - f0)))
        x = START_X + dist * ease_out(u)
        intro["bx"][f] = x
        intro["bth"][f] = (x - BALL_X) / R
        intro["bird_x"][f] = x + BIRD_DX
        intro["bird_y"][f] = BIRD_Y0
    out["intro"] = intro
    loop = {k: {} for k in ("cy", "sx", "sy", "bird_y", "bird_sy", "feet", "mouse_x", "mouse_rot", "mouse_sx")}
    for f in range(L + 1):
        t = f - LAUNCH
        sy = ball_sy(t)
        loop["cy"][f] = REST_Y - ball_h(t)
        loop["sy"][f] = sy
        loop["sx"][f] = 1.0 / sy
        loop["bird_y"][f] = BIRD_Y0 - bird_h(t)
        bsy = bird_sy(t)
        loop["bird_sy"][f] = bsy
        loop["feet"][f] = feet_visible(t)
        x, rot, sx = mouse_full(t)
        loop["mouse_x"][f] = HOLE_X + x
        loop["mouse_rot"][f] = rot
        loop["mouse_sx"][f] = sx
    out["loop"] = loop
    return out


# ---- copying art -------------------------------------------------------------------------------------------------------------------
ID_ATTR = re.compile(r'(?<![A-Za-z])id="([^"]*)"')
REF_ATTRS = ("sourceId", "objectId", "animationId", "stateToId", "drawTargetId", "drawableId")


def element(doc, oid):
    i = doc.idx(oid)
    return doc.lines[i:doc.end(i) + 1]


def reindent(lines, indent):
    lines = [l for l in lines if l.strip() and not l.strip().startswith("<!--")]
    base = len(lines[0]) - len(lines[0].lstrip())
    return [" " * indent + l[base:] for l in lines]


def clone(doc, lines, extra=None):
    """A copy of the lines with a new id for every element defined in them; references to those (and to the ids in `extra`, an old to
    new map) follow. Returns (lines, old to new map)."""
    mp = {}
    for l in lines:
        for m in ID_ATTR.findall(l):
            mp.setdefault(m, doc.new_id())
    mp.update(extra or {})
    out = []
    for l in lines:
        l = ID_ATTR.sub(lambda m: f'id="{mp[m.group(1)]}"', l)
        for a in REF_ATTRS:
            l = re.sub(rf'\b{a}="([^"]*)"', lambda m, a=a: f'{a}="{mp.get(m.group(1), m.group(1))}"', l)
        if "<KeyFrameId" in l:
            l = re.sub(r'value="([^"]*)"', lambda m: f'value="{mp.get(m.group(1), m.group(1))}"', l)
        out.append(l)
    return out, mp


def set_attrs(line, **kv):
    for k, v in kv.items():
        val = v if isinstance(v, str) else num(v)
        if re.search(rf' {k}="[^"]*"', line):
            line = re.sub(rf' {k}="[^"]*"', f' {k}="{val}"', line, count=1)
        else:
            line = re.sub(r"^(\s*<\w+)", rf'\1 {k}="{val}"', line, count=1)
    return line


def unset_attrs(line, *keys):
    for k in keys:
        line = re.sub(rf' {k}="[^"]*"', "", line, count=1)
    return line


def keyed_objects(src, anim_name, ids):
    """The KeyedObject blocks of a source animation for the given object ids (lines)."""
    a, b = src.anim(anim_name)
    out = []
    i = a + 1
    while i < b:
        l = src.lines[i]
        m = re.match(r'\s*<KeyedObject\b[^>]*\bobjectId="([^"]*)"', l)
        if m:
            j = src.end(i)
            if m.group(1) in ids:
                out += src.lines[i:j + 1]
            i = j + 1
        else:
            i += 1
    return out


def ids_in(lines):
    return {m for l in lines for m in ID_ATTR.findall(l)}


def anim_shell(name, aid, duration, loop=False, one_shot=False):
    attrs = ""
    if duration != 192 or not (loop or one_shot):
        pass
    if one_shot:
        attrs = ' loopValue="oneShot"'
    elif loop:
        attrs = ' loopValue="loop"'
    fps = "" if duration == 192 or loop else ' fps="60"'
    return [f'        <LinearAnimation{attrs}{fps} duration="{duration}" name="{name}" id="{aid}">', "        </LinearAnimation>"]


def insert_block(doc, anchor_re, lines, before=True):
    i = next(k for k, l in enumerate(doc.lines) if re.search(anchor_re, l))
    doc.lines[i:i] = lines


def build(doc, scene, sheet):
    ch3 = Doc(RIVE_DIR / "chapters/ch3/scene.rml")
    ch1 = Doc(RIVE_DIR / "chapters/ch1/scene.rml")
    notes = []
    # ---------------------------------------------------------------- ids of the room's own nodes and the animations
    room_id, plane_id, lag_id, lag_plane_id = (doc.new_id() for _ in range(4))
    bird_id, bird_sq, bird_art = doc.new_id(), doc.new_id(), doc.new_id()
    rules_id, top_id, bottom_id, floor_clip = (doc.new_id() for _ in range(4))
    mouse_id, mouse_turn, mouse_art_wrap, hole_clip = (doc.new_id() for _ in range(4))
    anims = {n: doc.new_id() for n in ("Intro", "Waiting", "Built", "Loop", "Small Loop", "Small Waiting", "Small Hold")}

    # ---------------------------------------------------------------- the art
    cat_l, cat_map = clone(doc, reindent(element(ch3, "9:27980"), 20), {"9:31256": floor_clip})
    cat_l[0] = set_attrs(cat_l[0], x=CAT_X, y=CAT_Y, name="Community Cat")
    dog_l, dog_map = clone(doc, reindent(element(ch3, "9:27380"), 20), {"9:31256": floor_clip})
    dog_l[0] = set_attrs(dog_l[0], x=DOG_X, y=DOG_Y, name="Community Dog")
    hole_l, hole_map = clone(doc, reindent(element(ch1, "9:4782"), 20), {"9:6714": floor_clip})
    hole_l[0] = set_attrs(hole_l[0], x=HOLE_X, y=FLOOR, name="Community Mouse Hole")
    mouse_l, mouse_map = clone(doc, reindent(element(ch1, "9:4059"), 20), {"12:2": hole_clip, "9:6714": floor_clip})
    mouse_l[0] = set_attrs(mouse_l[0], name="Community Mouse Art")
    # the bird: File 1's figure, origin at its own (0, 0)
    bird_l, bird_map = clone(doc, reindent(element(ch1, "9:13163"), 20))
    bird_l[0] = set_attrs(unset_attrs(bird_l[0], "x", "y"), name="Community Bird Figure")
    feet = [bird_map["9:13088"], bird_map["9:13145"]]            # the two foot ticks (Shape 6 of each leg)
    # the ball: the Bridge Art artboard's ball in Chapter 2's standard art
    ball_l, ball_map = clone(doc, reindent(element(doc, "12:40"), 16))
    ball_l = [l.replace('name="Bridge Ball"', f'name="{ROOM} Ball"') for l in ball_l]
    ball_l[0] = set_attrs(ball_l[0], x=START_X, y=REST_Y)
    k_line = next(i for i, l in enumerate(ball_l) if 'name="Ball_01"' in l)
    ball_l[k_line] = set_attrs(ball_l[k_line], scaleX=K, scaleY=K)

    I = lambda n: " " * n
    # its setup x stays 0 (the Waiting pose puts it at PLANE_WAIT): the loop-range check adds up the parents' setup x
    plane = [f'{I(16)}<Node name="{ROOM} Floor Plane" id="{plane_id}">']
    # the mouse sits in front of the hole; the mask is a plane sibling, the mouse inside two pivots: the turn about the head, the move
    plane += [f'{I(20)}<Node x="{num(HOLE_X + MOUSE_HIDE)}" y="{num(MOUSE_Y)}" name="{ROOM} Mouse" id="{mouse_id}">',
              f'{I(24)}<Node x="{num(MOUSE_PIVOT)}" name="{ROOM} Mouse Turn" id="{mouse_turn}">',
              f'{I(28)}<Node x="{num(-MOUSE_PIVOT)}" name="{ROOM} Mouse Turn Art" id="{mouse_art_wrap}">']
    plane += reindent(mouse_l, 32)
    plane += [f"{I(28)}</Node>", f"{I(24)}</Node>", f"{I(20)}</Node>"]
    plane += [f'{I(20)}<Shape x="{num(HOLE_X + MASK_DX)}" y="{num(FLOOR)}" name="{ROOM} Mouse Hole Clip" id="{hole_clip}">',
              f'{I(24)}<Rectangle width="9000" height="2000" originX="1" originY="1" name="Path" id="{doc.new_id()}"/>', f"{I(20)}</Shape>"]
    plane += reindent(hole_l, 20) + reindent(cat_l, 20) + reindent(dog_l, 20) + [f"{I(16)}</Node>"]

    bird = [f'{I(16)}<Node x="{num(START_X + BIRD_DX)}" y="{num(BIRD_Y0)}" name="{ROOM} Bird" id="{bird_id}">',
            f'{I(20)}<Node y="{num(BIRD_FEET)}" name="{ROOM} Bird Squash" id="{bird_sq}">',
            f'{I(24)}<Node y="{num(-BIRD_FEET)}" name="{ROOM} Bird Art" id="{bird_art}">'] + reindent(bird_l, 28) + \
           [f"{I(24)}</Node>", f"{I(20)}</Node>", f"{I(16)}</Node>"]

    room = [f'{I(12)}<Node name="{ROOM} Room" id="{room_id}">',
            f'{I(16)}<DrawRules drawTargetId="{top_id}" name="{ROOM} Draw Rules" id="{rules_id}">',
            f'{I(20)}<DrawTarget drawableId="1:2857" placementValue="before" name="{ROOM} Top" id="{top_id}"/>',
            f'{I(20)}<DrawTarget drawableId="1:2286" placementValue="before" name="{ROOM} Bottom" id="{bottom_id}"/>',
            f"{I(16)}</DrawRules>"] + bird + reindent(ball_l, 16) + plane + \
           [f'{I(16)}<Node name="{ROOM} Wall Lag" id="{lag_id}">', f'{I(20)}<Node name="{ROOM} Wall Plane" id="{lag_plane_id}"/>', f"{I(16)}</Node>",
            f'{I(16)}<Shape y="{num(FLOOR)}" name="{ROOM} Floor Clip" id="{floor_clip}">',
            f'{I(20)}<Rectangle width="9000" height="2000" originX="0.5" originY="1" name="Path" id="{doc.new_id()}"/>', f"{I(16)}</Shape>",
            f"{I(12)}</Node>"]
    insert_block(doc, r'<Node x="747.5" y="533.5" name="Background"', room)

    # ---------------------------------------------------------------- the animations
    wordle = {"Home": "1:2708", "Gone": "1:2709", "Outro": "1:2707", "Back Out": "1:2942", "Right": "1:2943", "Return": "1:2944",
              "Forward In": "1:2945", "On Top": "1:2946", "Below": "1:2950"}
    ext = {"1:831": room_id, "1:2657": lag_id, "1:2820": rules_id, "1:2821": top_id, "1:2822": bottom_id}
    pose_ids = {}
    blocks = []
    for n in ("Intro", "Waiting", "Built"):
        blocks += anim_shell(f"{ROOM} {n}", anims[n], 192 if n == "Intro" else 1, one_shot=False)
    blocks += anim_shell(f"{ROOM} Loop", anims["Loop"], L + 1, loop=True)
    blocks += anim_shell(f"{ROOM} Small Loop", anims["Small Loop"], L + 1, loop=True)
    blocks += anim_shell(f"{ROOM} Small Waiting", anims["Small Waiting"], 1)
    blocks += anim_shell(f"{ROOM} Small Hold", anims["Small Hold"], 99)
    for n, wid in wordle.items():
        src = element(doc, wid)
        lines, mp = clone(doc, reindent(src, 8), ext)
        lines[0] = lines[0].replace('name="Wordle ', f'name="{ROOM} ')
        pose_ids[wid] = mp[wid]
        blocks += lines
    first_artboard_end = next(i for i, l in enumerate(doc.lines) if l == "    </Artboard>")
    doc.lines[first_artboard_end:first_artboard_end] = blocks

    # Bridge Colors becomes Community Colors (the checks look for "<Room> Colors")
    i = next(k for k, l in enumerate(doc.lines) if f'name="{OLD_COLORS}"' in l)
    doc.lines[i] = doc.lines[i].replace(f'name="{OLD_COLORS}"', f'name="{ROOM} Colors"')

    # ---------------------------------------------------------------- the state machine layers
    anim_map = {"1:2702": anims["Waiting"], "1:2621": anims["Intro"], "1:2622": anims["Loop"], "20:35": anims["Built"]}
    anim_map.update({wid: pose_ids[wid] for wid in wordle.values()})
    layer_lines = []
    for lid, nm in (("1:2756", ""), ("1:2778", " Exit"), ("1:3157", " Draw")):
        lines, _ = clone(doc, reindent(element(doc, lid), 12), anim_map)
        lines = [l.replace(f'name="Wordle{nm}"', f'name="{ROOM}{nm}"') for l in lines]
        lines = [l.replace('value="1:9101"', f'value="{SCENE_VALUE}"') for l in lines]
        assert not any("1:9101" in l for l in lines)
        layer_lines += lines
    layer_lines += small_layer(doc, anims)
    sm_end = next(i for i, l in enumerate(doc.lines) if l == "        </StateMachine>")
    doc.lines[sm_end:sm_end] = layer_lines

    # ---------------------------------------------------------------- the ball: standard art and a spin pivot
    doc.save()
    from rml_read import Scene
    from rooms_sheet import Sheet
    scene2 = Scene(doc.path)
    art = BallArt(scene2, ROOM)
    spin = prepare_ball(doc, art)
    start = art.node_of((START_X, REST_Y))
    j = doc.idx(art.id)
    doc.lines[j] = set_attrs(doc.lines[j], x=start[0], y=start[1])

    # ---------------------------------------------------------------- the intro and the loop
    p = plan()
    intro, loop = p["intro"], p["loop"]
    in_, lo_ = f"{ROOM} Intro", f"{ROOM} Loop"
    fi, fl = range(INTRO), range(L + 1)
    node = art.node_of((BALL_X, REST_Y))
    # intro
    doc.set_prop(in_, plane_id, "x", [(PAN[0], PLANE_WAIT, "power2.inOut"), (PAN[1], 0.0, "hold")])
    doc.set_prop(in_, art.id, "x", bake({f: art.node_of((intro["bx"][f], REST_Y))[0] for f in fi}, fi))
    doc.set_prop(in_, art.id, "y", [(0, art.node_of((BALL_X, REST_Y))[1], "hold")])
    doc.set_prop(in_, art.scale, "scaleX", [(0, 1.0, "hold")])
    doc.set_prop(in_, art.scale, "scaleY", [(0, 1.0, "hold")])
    doc.set_prop(in_, spin, "rotation", bake(intro["bth"], fi))
    doc.set_prop(in_, bird_id, "x", bake(intro["bird_x"], fi))
    doc.set_prop(in_, bird_id, "y", [(0, BIRD_Y0, "hold")])
    doc.set_prop(in_, bird_sq, "scaleX", [(0, 1.0, "hold")])
    doc.set_prop(in_, bird_sq, "scaleY", [(0, 1.0, "hold")])
    for fid in feet:
        doc.set_prop(in_, fid, "opacity", [(0, 0.0, "hold")])
    doc.set_prop(in_, mouse_id, "x", [(0, HOLE_X + MOUSE_HIDE, "hold")])
    doc.set_prop(in_, mouse_id, "rotation", [(0, 0.0, "hold")])
    doc.set_prop(in_, mouse_turn, "scaleX", [(0, 1.0, "hold")])
    # loop (the rest frames are flat runs: bake keeps only their two ends)
    doc.set_prop(lo_, art.id, "x", [(0, node[0], "hold")])
    doc.set_prop(lo_, art.id, "y", bake({f: art.node_of((BALL_X, loop["cy"][f]))[1] for f in fl}, fl))
    doc.set_prop(lo_, art.scale, "scaleX", bake(loop["sx"], fl))
    doc.set_prop(lo_, art.scale, "scaleY", bake(loop["sy"], fl))
    doc.set_prop(lo_, spin, "rotation", [(0, 0.0, "hold")])
    doc.set_prop(lo_, bird_id, "x", [(0, BALL_X + BIRD_DX, "hold")])
    doc.set_prop(lo_, bird_id, "y", bake(loop["bird_y"], fl))
    doc.set_prop(lo_, bird_sq, "scaleX", bake({f: 1.0 / loop["bird_sy"][f] for f in fl}, fl))
    doc.set_prop(lo_, bird_sq, "scaleY", bake(loop["bird_sy"], fl))
    for fid in feet:
        doc.set_prop(lo_, fid, "opacity", bake(loop["feet"], fl))
    doc.set_prop(lo_, mouse_id, "x", bake(loop["mouse_x"], fl))
    doc.set_prop(lo_, mouse_id, "rotation", bake(loop["mouse_rot"], fl))
    doc.set_prop(lo_, mouse_turn, "scaleX", bake(loop["mouse_sx"], fl))
    # the intro's last frame must equal the loop's first on every property: the ball's spin ends at 0 (the highlight where it is drawn)
    doc.rebuild_waiting(ROOM)
    rebuild_built(doc, ROOM)

    # ---------------------------------------------------------------- small loops: the cat's, the dog's and the bird's blink
    cat_ids = {o for o in cat_map if o in ids_in(element(ch3, "9:27980"))}
    dog_ids = {o for o in dog_map if o in ids_in(element(ch3, "9:27380"))}
    bird_src = ids_in(element(ch1, "9:13163"))
    for nm, src, ids, mp in (("Small Loop", ("End Small Loop", ch3), cat_ids | dog_ids, {**cat_map, **dog_map}),
                              ("Small Waiting", ("End Small Waiting", ch3), cat_ids | dog_ids, {**cat_map, **dog_map}),
                              ("Small Hold", ("End Small Hold", ch3), cat_ids | dog_ids, {**cat_map, **dog_map}),
                              ("Small Loop", ("Start Small Loop", ch1), bird_src, bird_map),
                              ("Small Waiting", ("Start Small Waiting", ch1), bird_src, bird_map),
                              ("Small Hold", ("Start Small Hold", ch1), bird_src, bird_map)):
        kos = keyed_objects(src[1], src[0], ids)
        lines, _ = clone(doc, reindent(kos, 12), mp)
        a, b = doc.anim(f"{ROOM} {nm}")
        doc.lines[b:b] = lines
    cat_n = len(cat_ids)
    notes.append(f"cat {cat_n} and dog {len(dog_ids)} pieces, bird {len(bird_src)}")
    return (f"{ROOM}: ball rolls in {ROLL[0] / 60:.2f} s to {ROLL[1] / 60:.2f} s; hop at {LAUNCH / 60:.2f} s of the loop, rise {RISE:.0f}, "
            f"air {T:.1f} frames ({T / 60:.2f} s), bird top {BIRD_TOP:.1f}, touches {BIRD_DELAY:.1f} frames after the ball; loop {L + 1} frames")


def small_layer(doc, anims):
    """The small loops' layer (File 3's End Small, for this room's scene): Small Waiting, then Small Loop at once when the file opens on
    the room or asks for it with Back before it was shown, else Small Hold (99 frames, the pan) and then Small Loop."""
    wait, hold, loop = doc.new_id(), doc.new_id(), doc.new_id()
    lay = doc.new_id()

    def cond(prop, value):
        return [f'                        <TransitionViewModelCondition opValue="equal" id="{doc.new_id()}">',
                f'                            <TransitionPropertyViewModelComparator id="{doc.new_id()}">',
                f'                                <BindablePropertyEnum id="{doc.new_id()}">',
                f'                                    <DataBindContext sourcePathIds="1:14-{prop}" propertyKey="637" id="{doc.new_id()}"/>',
                "                                </BindablePropertyEnum>", "                            </TransitionPropertyViewModelComparator>",
                f'                            <TransitionValueEnumComparator value="{value}" id="{doc.new_id()}"/>',
                "                        </TransitionViewModelCondition>"]

    def tr(to, conds):
        return [f'                    <StateTransition stateToId="{to}" duration="0" id="{doc.new_id()}">'] + conds + ["                    </StateTransition>"]
    SCENE, START, DIRECTION = "1:2713", "1:3400", "1:2855"
    out = [f'            <StateMachineLayer name="{ROOM} Small" id="{lay}">',
           f'                <AnyState x="160" y="200" id="{doc.new_id()}"/>', f'                <ExitState x="720" y="200" id="{doc.new_id()}"/>']
    entry = doc.new_id()
    out += [f'                <EntryState x="0" y="0" id="{entry}">', f'                    <StateTransition stateToId="{wait}" id="{doc.new_id()}"/>',
            "                </EntryState>"]
    out += [f'                <AnimationState animationId="{anims["Small Waiting"]}" x="160" y="0" id="{wait}">']
    out += tr(loop, cond(SCENE, SCENE_VALUE) + cond(START, SCENE_VALUE))
    out += tr(loop, cond(SCENE, SCENE_VALUE) + cond(DIRECTION, "1:9201"))
    out += tr(hold, cond(SCENE, SCENE_VALUE))
    out += ["                </AnimationState>",
            f'                <AnimationState animationId="{anims["Small Hold"]}" x="400" y="0" id="{hold}">',
            f'                    <StateTransition stateToId="{loop}" duration="0" enableExitTime="true" exitTimeIsPercetange="true" exitTime="100" id="{doc.new_id()}"/>',
            "                </AnimationState>",
            f'                <AnimationState animationId="{anims["Small Loop"]}" x="640" y="0" id="{loop}"/>',
            "            </StateMachineLayer>"]
    return out
