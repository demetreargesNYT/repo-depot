"""Regenerates the whole Chapter 4 ball (its animations and its layer): refuses chapters/ch3/scene.rml once it has changed since commit 35883e9 (tools/regen_guard.py).

Chapter 4: the ball arrives on card 1 to see the city, stays for good, and celebrates on card 2 (Demetre, 2026-11-04).

    python3 chapters/ch3/scripts/ch3_c4_ball_stay.py [--scene PATH]            prints the plan and the measured numbers, writes nothing
    python3 chapters/ch3/scripts/ch3_c4_ball_stay.py [--scene PATH] --write    adds the ball's animations and its one layer

Replaces ch3_c4_ball_idle.py (no exit layer, no Exit Turn wrapper, no roll-out, no puff). The ball is "Chapter 4 Ball" (parked at x -60,
y 2400 in the Floor Plane, drawn in front of the city). Nothing else in the scene changes.

Layer "Chapter 4 Ball Motion" (reads scene, reveal, direction, startScene, topGame):
  Boot -> Away (parked) ; Away -> Wait (192 frames, hidden: the city's build) -> Arrive -> Idle 1 (reveal false) | Celebrate (reveal true).
  Away/Boot -> Idle 1 / Idle <set> directly for startScene and for Back (the ball is already in place).
  Idle 1 <-> Idle <set> on reveal (250 ms in, 600 ms out); Celebrate -> Idle <set>. Nothing ever leaves: no roll-out.
Arrive (card 1, once): bounces in from off the left edge (squash and stretch kept subtle), rolls, slows and stops in its tracks at the
  foot of the city (a little past its place), pauses, rolls back so the dot tilts up, and holds still for a moment of wonder.
Idle 1: a faint eased roll, +-3 px, the dot turning with it. 600 frames, first and last frame equal.
Idle <set>: 600 frames (two fireworks loops), frame 0 = the fireworks' frame 0. A small excited hop (with a gather) whose apex is on the
  gate's first big burst, small hops on the bigger bursts, each landing settling with a roll on and a tiny rock back, and once in the
  second half a bigger, showing-off hop (leans back in the air, 8 percent landing squash, no puff).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
from ball_motion import smooth
from rml_edit import Doc, bake
import regen_guard
WRITTEN_AGAINST = "35883e9"     # the file before this script's commit (0178eec)
from rml_read import Scene, chapter_dir

args = sys.argv[1:]
SCENE = Path(args[args.index("--scene") + 1]) if "--scene" in args else chapter_dir("ch3") / "scene.rml"
ROOM = "Chapter 4"
G, R, S = 0.40, 17.678, 1.2                    # gravity, the ball's radius at scale 1, its size
RS = R * S
FLOOR, DROP, BOT = 711.3, 14.5, 0.202          # the ball's lowest point; Ball_01 sits DROP below its node; its bottom is BOT*scale below Ball_01
REST_X = 747.0
TILT = -0.26                                   # the dot at rest: straight up (its highlight sits 15 degrees right of vertical), looking at the city
OVER = 0.40 * RS                               # it stops this far past its place, then rolls back
AWAY_X, AWAY_NODE_Y = -60.0, 2400.0
WAIT, IDLE = 192, 600
VM = "1:14"
SCENE_P, DIR_P, TOP_P, REVEAL_P, START_P = "1:2713", "1:2855", "1:3300", "1:3310", "1:3400"
CH4, BACK, FWD = "1:9102", "1:9201", "1:9200"
TOP_VALUES = {"wordle": "1:9300", "connections": "1:9301", "strands": "1:9302", "spelling-bee": "1:9303",
              "mini": "1:9304", "midi": "1:9305", "crossword": "1:9306"}   # "crossword" was "daily" until ch3_topgame_crossword.py
SET_OF = {"wordle": "Wordle", "connections": "Connections", "strands": "Strands", "spelling-bee": "Spelling Bee",
          "mini": "Crossword", "midi": "Crossword", "crossword": "Crossword"}
SETS = ["Wordle", "Connections", "Strands", "Spelling Bee", "Crossword"]
# The burst frames (apex of the hop = the frame the burst's large pieces reach their full size in "Chapter 4 Fireworks Loop") and
# the hop's flight in frames (12 -> 7.2 units, 14 -> 9.8, 16 -> 12.8; a hop of T frames rises 0.4 * T * T / 8). Read from the keys:
#   Wordle       Firework_Lg x1.94 peaks 64, x2.07 at 156, x2.01 at 274 (the x1.5 ones at 73, 113, 223 are smaller)
#   Connections  the seven big ring groups (Firewor_Lg_01) reach full size at 35, 66, 101, 131, 155, 186, 243; three spread across the loop
#   Strands      the three big strand bursts: 1.0 times at 94, 1.41 at 138, 1.63 at 229 (36, 80, 105 ... are flashes of small pieces)
#   Spelling Bee the big groups (Firwork_Big 3 and 4, x4.21) peak at 125, 159, 217, 270
#   Crossword    the seven big ring groups reach full size at 26, 46, 83, 97, 134, 183, 240; three spread across the loop
BURSTS = {"Wordle": [(64, 12), (156, 16), (274, 16)],
          "Connections": [(35, 12), (131, 14), (243, 14)],
          "Strands": [(94, 12), (138, 14), (229, 16)],
          "Spelling Bee": [(125, 12), (217, 14), (270, 16)],
          "Crossword": [(26, 12), (134, 16), (240, 16)]}
SHOW_T = 20                                    # the showing-off hop: 20 units
GATHER = 9                                     # frames of gather before a take-off (0.15 s)
SQUASH_LIMIT = 0.08


def node_y(contact, sy):
    """The ball node's y when the ball's lowest point is at `contact` and Ball_01's vertical scale is sy."""
    return contact - DROP - BOT * sy


def ease(t):
    t = min(1.0, max(0.0, t))
    return 0.5 - 0.5 * math.cos(math.pi * t)


def land_spring(k, A, tau=3.5, period=18.0):
    """Squash after a landing k frames after the contact: A at the contact, back within 0.2 s, one tiny overshoot."""
    if k < 0:
        return 0.0
    if k >= 16:
        return 0.0
    w = 2 * math.pi / period
    fade = 1 - smooth((k - 10) / 6)                       # the last bit of the tail is faded so it is exactly 0 when the spring ends
    return fade * A * math.exp(-k / tau) * (math.cos(w * k) + math.sin(w * k) / (w * tau))


def squash_to_scales(a):
    """a > 0: shorter and wider by the same amount (volume stays constant); a < 0: taller and thinner."""
    return S * (1 + a), S * (1 - a)


def waypoints(points, t):
    """Cosine-eased value at t through [(frame, value)] (zero speed at each waypoint)."""
    if t <= points[0][0]:
        return points[0][1]
    for (t0, v0), (t1, v1) in zip(points, points[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * ease((t - t0) / (t1 - t0))
    return points[-1][1]


# ---- Arrive ---------------------------------------------------------------------------------------------------------------------
FLIGHTS = [36, 25, 18, 12, 9]                  # the bounces, in frames: 64, 31, 16, 7 and 4 units; the vertical speed keeps 70 percent; the first one is long so two landings fall inside the phone crop (x 560 to 935)
KX = 0.85                                      # and 85 percent of the horizontal speed (the whole speed keeps 78 to 88 percent)
ROLL_T = 40                                    # frames it rolls on, slowing evenly to a stop
PAUSE, BACKT, HOLD = 6, 28, 54                 # it stops, pauses, rolls back, holds still (0.9 s)


def arrive():
    """Per frame 0..ARRIVE: x, lift, rotation, squash a, plus the schedule and measurements."""
    stop_x = REST_X + OVER
    reach = sum(T * KX ** k for k, T in enumerate(FLIGHTS)) + KX ** len(FLIGHTS) * ROLL_T / 2
    vx0 = (stop_x - AWAY_X) / reach
    starts, f = [], 0
    for T in FLIGHTS:
        starts.append(f)
        f += T
    roll_start = f
    f_stop = roll_start + ROLL_T
    arrive_len = f_stop + PAUSE + BACKT + HOLD
    x, lift, a = {}, {}, {}
    xi = AWAY_X
    vx = vx0
    info = []
    for k, T in enumerate(FLIGHTS):
        v = G * T / 2
        speed_in = math.hypot(vx, v)
        for j in range(T):
            x[starts[k] + j] = xi + vx * j
            lift[starts[k] + j] = max(0.0, v * j - 0.5 * G * j * j)
        xi += vx * T
        vx_next = vx * KX
        v_next = G * FLIGHTS[k + 1] / 2 if k + 1 < len(FLIGHTS) else 0.0
        info.append((k, T, 0.5 * G * (T / 2) ** 2, vx, v, speed_in, math.hypot(vx_next, v_next)))
        vx = vx_next
    vr = vx
    for j in range(ROLL_T + 1):
        x[roll_start + j] = xi + vr * (j - j * j / (2 * ROLL_T))
        lift[roll_start + j] = 0.0
    assert abs(x[f_stop] - stop_x) < 1e-6, (x[f_stop], stop_x)
    for j in range(1, PAUSE + BACKT + HOLD + 1):
        t = f_stop + j
        x[t] = stop_x - OVER * ease((j - PAUSE) / BACKT)
        lift[t] = 0.0
    for t in range(arrive_len + 1):
        a[t] = 0.0
    # squash: a landing after every bounce (from the vertical speed in), a little stretch in the fastest flights
    for k in range(1, len(FLIGHTS) + 1):
        tl = starts[k] if k < len(FLIGHTS) else roll_start
        v_in = G * FLIGHTS[k - 1] / 2
        A = min(0.06, 0.0125 * v_in)
        for t in range(tl - 1, tl + 16):
            a[t] = a.get(t, 0.0) + (0.3 * A if t == tl - 1 else land_spring(t - tl, A))
    for k, T in enumerate(FLIGHTS):
        sp = info[k][5]
        stretch = min(0.03, max(0.0, 0.004 * (sp - 6.0)))
        for j in range(T):
            a[starts[k] + j] += -stretch * math.sin(math.pi * (j + 0.5) / T) ** 2 if sp > 7.0 else 0.0
    rot = {t: (x[t] - REST_X) / RS + TILT for t in x}
    return dict(x=x, lift=lift, rot=rot, a=a, len=arrive_len, starts=starts, roll_start=roll_start, f_stop=f_stop, vx0=vx0, info=info,
                stop_x=stop_x)


# ---- hops and idles -----------------------------------------------------------------------------------------------------------
def add_hop(lift, a, t0, T, gather_amp, land_amp, label, plan):
    """A parabola of T integer frames from t0, a gather before it and a squash after the landing."""
    n = len(lift) - 1
    v = G * T / 2
    for k in range(T + 1):
        lift[t0 + k] = max(0.0, v * k - 0.5 * G * k * k)
    lift[t0 + T] = 0.0
    for i in range(GATHER + 1):
        if t0 - GATHER + i >= 0:
            a[t0 - GATHER + i] += gather_amp * smooth(i / GATHER)
    for k in range(1, 4):
        a[t0 + k] += gather_amp * (1 - smooth(k / 3))
    tl = t0 + T
    a[tl - 1] += 0.3 * land_amp
    for k in range(0, 16):
        if tl + k <= n:
            a[tl + k] += land_spring(k, land_amp)
    plan.append((t0 + T // 2, f"{label}: {0.4 * T * T / 8:.1f} units, take-off {t0}, apex {t0 + T // 2}, lands {tl}, gather {gather_amp * 100:.0f} percent, "
                              f"landing squash {land_amp * 100:.1f} percent"))


def settle(xo, tl, length, amp, sign):
    """After a landing: it rolls on a touch (eased), comes back through its place a hair (a tiny rock back) and rests."""
    pts = [(tl, 0.0), (tl + 0.30 * length, sign * amp), (tl + 0.74 * length, -sign * 0.32 * amp), (tl + length, 0.0)]
    for t in range(tl, min(len(xo) - 1, tl + length) + 1):
        xo[t] += waypoints(pts, t)


def celebration(bursts):
    """Per frame 0..IDLE: x, contact y, rotation, scale x, scale y, and the schedule. Frame 0 = the fireworks' frame 0."""
    n = IDLE
    lift = [0.0] * (n + 1)
    a = [0.0] * (n + 1)
    xo = [0.0] * (n + 1)
    lean = [0.0] * (n + 1)
    plan = []
    hops = []
    for h in (0, 300):
        for i, (p, T) in enumerate(bursts):
            hops.append((p + h - T // 2, T, i, p + h))
    hops.sort()
    # the showing-off hop: the roomiest gap in the second half, centred
    busy = [(t0 - GATHER - 1, t0 + T + 14) for t0, T, _, _ in hops]
    gaps, prev = [], 4
    for s, e in busy:
        gaps.append((prev, s))
        prev = e
    gaps.append((prev, n - 4))
    frag = []
    for s, e in gaps:
        if s < 300 < e:
            frag += [(s, 300), (300, e)]
        else:
            frag.append((s, e))
    AFTER = 28
    need = GATHER + SHOW_T + AFTER
    second = [(e - s, s, e) for s, e in frag if s >= 300 and e - s >= need + 4]
    L, s, e = max(second)
    show_t0 = s + (L - need) // 2 + GATHER
    events = [(t0, T, 'hop', i, p) for t0, T, i, p in hops] + [(show_t0, SHOW_T, 'show', 0, show_t0 + SHOW_T // 2)]
    events.sort()
    for idx, (t0, T, kind, i, p) in enumerate(events):
        nxt = events[idx + 1][0] - GATHER - 3 if idx + 1 < len(events) else n
        avail = max(8, nxt - (t0 + T))
        length = min(46 if kind == 'hop' else 44, avail)
        if kind == 'show':
            add_hop(lift, a, t0, T, 0.05, SQUASH_LIMIT, "SHOWING OFF hop", plan)
            for k in range(T + 1):
                lean[t0 + k] = -0.5 * math.sin(math.pi * k / T) ** 2
            settle(xo, t0 + T, length, 5.0, 1)
        else:
            first = (i == 0 and p < 300) or (i == 0 and p >= 300)
            g_amp = 0.05 if i == 0 else 0.04
            l_amp = min(0.06, 0.017 * G * T / 2)                 # 4.1, 4.8 and 5.4 percent for 12, 14 and 16 frame hops
            add_hop(lift, a, t0, T, g_amp, l_amp, f"hop {'(first) ' if i == 0 else ''}on the burst at {p}", plan)
            settle(xo, t0 + T, length, 2.6 if length >= 30 else 1.6, 1 if (i % 2 == 0) else -1)
    x = [REST_X + xo[f] for f in range(n + 1)]
    y = [FLOOR - lift[f] for f in range(n + 1)]
    rot = [TILT + xo[f] / RS + lean[f] for f in range(n + 1)]
    sx, sy = zip(*[squash_to_scales(a[f]) for f in range(n + 1)])
    return x, y, rot, list(sx), list(sy), a, sorted(plan)


def idle_one():
    """A faint, eased roll: +-3 px, two slow swings; the dot turns with it. First and last frame equal."""
    n = IDLE
    xo = [2.2 * math.sin(2 * math.pi * f / n) + 0.9 * math.sin(4 * math.pi * f / n) for f in range(n + 1)]
    x = [REST_X + v for v in xo]
    y = [FLOOR] * (n + 1)
    rot = [TILT + v / RS for v in xo]
    return x, y, rot, [S] * (n + 1), [S] * (n + 1)


def celebrate_hop():
    """The short celebration hop after an arrival that was still going when the player tapped: one small excited hop."""
    n = 64
    lift = [0.0] * (n + 1)
    a = [0.0] * (n + 1)
    xo = [0.0] * (n + 1)
    plan = []
    t0, T = GATHER + 1, 12
    add_hop(lift, a, t0, T, 0.05, 0.041, "celebration hop", plan)
    settle(xo, t0 + T, n - (t0 + T) - 1, 2.0, 1)
    x = [REST_X + xo[f] for f in range(n + 1)]
    y = [FLOOR - lift[f] for f in range(n + 1)]
    rot = [TILT + xo[f] / RS for f in range(n + 1)]
    sx, sy = zip(*[squash_to_scales(a[f]) for f in range(n + 1)])
    return x, y, rot, list(sx), list(sy), a


# ---- the scene ----------------------------------------------------------------------------------------------------------------
def cond_enum(n, prop, value, op="equal"):
    return [f'<TransitionViewModelCondition opValue="{op}" id="{n()}">', f'    <TransitionPropertyViewModelComparator id="{n()}">',
            f'        <BindablePropertyEnum id="{n()}">', f'            <DataBindContext sourcePathIds="{VM}-{prop}" propertyKey="637" id="{n()}"/>',
            f'        </BindablePropertyEnum>', f'    </TransitionPropertyViewModelComparator>', f'    <TransitionValueEnumComparator value="{value}" id="{n()}"/>',
            '</TransitionViewModelCondition>']


def cond_bool(n, prop, value):
    return [f'<TransitionViewModelCondition opValue="equal" id="{n()}">', f'    <TransitionPropertyViewModelComparator id="{n()}">',
            f'        <BindablePropertyBoolean id="{n()}">', f'            <DataBindContext sourcePathIds="{VM}-{prop}" propertyKey="634" id="{n()}"/>',
            f'        </BindablePropertyBoolean>', f'    </TransitionPropertyViewModelComparator>', f'    <TransitionValueBooleanComparator value="{value}" id="{n()}"/>',
            '</TransitionViewModelCondition>']


def report(arr, idles, cel):
    print(f"Arrive: {arr['len']} frames; bounces {FLIGHTS} frames; horizontal speed in {arr['vx0']:.2f}/frame, stops at x {arr['stop_x']:.1f} "
          f"(frame {arr['f_stop']}), rolls back to {REST_X}, holds {HOLD} frames")
    for k, T, h, vx, v, sp_in, sp_out in arr["info"]:
        print(f"   flight {k}: {T} frames, {h:.1f} units high, speed {sp_in:.2f} -> {sp_out:.2f} after (keeps {sp_out / sp_in * 100:.0f} percent)")
    for s in SETS:
        x, y, rot, sx, sy, a, plan = idles[s]
        print(f"Idle {s}: top of the ball y {min(y[f] - 2 * R * sy[f] for f in range(IDLE + 1)):.1f}; first/last equal "
              f"{all(abs(v[0] - v[-1]) < 1e-9 for v in (x, y, rot, sx, sy))}; max squash {max(a) * 100:.1f}%, max stretch {-min(a) * 100:.1f}%")
        for _, text in plan:
            print("   ", text)


def main():
    write = "--write" in args
    sc = Scene(SCENE)
    byid = sc.by_id
    ball, b01, spin = "9:43975", "9:43976", "9:43978"
    assert byid[ball].get("name") == f"{ROOM} Ball" and byid[b01].get("name") == "Ball_01" and byid[spin].get("name") == f"{ROOM} Ball Spin", "ball ids changed"
    assert not any(l.get("name") == f"{ROOM} Ball Motion" for l in sc.root.iter("StateMachineLayer")), "already applied"
    assert f"{ROOM} Ball Arrive" not in sc.animations and f"{ROOM} Ball Idle 1" not in sc.animations, "already applied"

    arr = arrive()
    idles = {s: celebration(BURSTS[s]) for s in SETS}
    report(arr, idles, None)
    if not write:
        return
    doc = Doc(SCENE)
    n = doc.new_id

    A = lambda k: f"{ROOM} Ball {k}"
    cx, cy, crot, csx, csy, _ = celebrate_hop()
    anims = [("Away", 1, False), ("Wait", WAIT, False), ("Arrive", arr["len"], False), ("Celebrate", len(cx) - 1, False),
             ("Idle 1", IDLE, True)] + [(f"Idle {s}", IDLE, True) for s in SETS]
    aids, new = {}, []
    for k, length, loop in anims:
        aids[k] = n()
        new += [f'        <LinearAnimation fps="60" duration="{length}"{" loopValue=" + chr(34) + "loop" + chr(34) if loop else ""} name="{A(k)}" id="{aids[k]}">',
                "        </LinearAnimation>"]
    li = doc.idx(next(e.get("id") for e in sc.root.iter("LinearAnimation") if e.get("name") == f"{ROOM} Loop"))
    doc.lines[li:li] = new

    # ---- Away and Wait: parked far below the stage, at the x where Arrive starts
    rot0 = arr["rot"][0]
    for nm, length in (("Away", 1), ("Wait", WAIT)):
        keys = lambda v: [(0, v, "hold")] + ([(length - 1, v, "hold")] if length > 1 else [])
        doc.set_prop(A(nm), ball, "x", keys(AWAY_X))
        doc.set_prop(A(nm), ball, "y", keys(AWAY_NODE_Y))
        doc.set_prop(A(nm), spin, "rotation", keys(rot0))
        doc.set_prop(A(nm), b01, "scaleX", keys(S))
        doc.set_prop(A(nm), b01, "scaleY", keys(S))
    # ---- Arrive
    L = arr["len"]
    fr = range(L + 1)
    sxs, sys_ = zip(*[squash_to_scales(arr["a"][f]) for f in fr])
    ys = {f: node_y(FLOOR - arr["lift"][f], sys_[f]) for f in fr}
    doc.set_prop(A("Arrive"), ball, "x", bake(arr["x"], fr))
    doc.set_prop(A("Arrive"), ball, "y", bake(ys, fr))
    doc.set_prop(A("Arrive"), spin, "rotation", bake(arr["rot"], fr))
    doc.set_prop(A("Arrive"), b01, "scaleX", bake(dict(enumerate(sxs)), fr))
    doc.set_prop(A("Arrive"), b01, "scaleY", bake(dict(enumerate(sys_)), fr))

    def put(nm, x, y, rot, sx, sy):
        fi = range(len(x))
        doc.set_prop(nm, ball, "x", bake(dict(enumerate(x)), fi))
        doc.set_prop(nm, ball, "y", bake({f: node_y(y[f], sy[f]) for f in fi}, fi))
        doc.set_prop(nm, spin, "rotation", bake(dict(enumerate(rot)), fi))
        doc.set_prop(nm, b01, "scaleX", bake(dict(enumerate(sx)), fi))
        doc.set_prop(nm, b01, "scaleY", bake(dict(enumerate(sy)), fi))

    put(A("Celebrate"), cx, cy, crot, csx, csy)
    put(A("Idle 1"), *idle_one())
    for s in SETS:
        x, y, rot, sx, sy, _, _ = idles[s]
        put(A(f"Idle {s}"), x, y, rot, sx, sy)

    # ---- the layer
    sid = {k: n() for k in ["Boot", "Away", "Wait", "Arrive", "Celebrate", "Idle 1"] + [f"Idle {s}" for s in SETS]}
    anim_of = {"Boot": "Away"}

    def tr(to, conds=(), exit_time=False, ms=0):
        attrs = f' stateToId="{sid[to]}" duration="{ms}"'
        if exit_time:
            attrs += ' enableExitTime="true" exitTimeIsPercetange="true" exitTime="100"'
        if not conds:
            return [f'<StateTransition{attrs} id="{n()}"/>']
        body = [l for c in conds for l in c]
        return [f'<StateTransition{attrs} id="{n()}">'] + ["    " + l for l in body] + ["</StateTransition>"]

    on4 = lambda: cond_enum(n, SCENE_P, CH4)
    rev = lambda v: lambda: cond_bool(n, REVEAL_P, v)
    is_back = lambda: cond_enum(n, DIR_P, BACK)
    is_fwd = lambda: cond_enum(n, DIR_P, FWD)
    started = lambda: cond_enum(n, START_P, CH4)

    def by_game(conds, exit_time=False, ms=0):
        out = []
        for tv, val in TOP_VALUES.items():
            out += tr(f"Idle {SET_OF[tv]}", [c() for c in conds] + [cond_enum(n, TOP_P, val)], exit_time=exit_time, ms=ms)
        return out

    def only(conds, to, exit_time=False, ms=0):
        return tr(to, [c() for c in conds], exit_time=exit_time, ms=ms)

    outs = {
        "Boot": by_game([on4, rev("true"), started]) + only([on4, rev("false"), started], "Idle 1")
                + by_game([on4, rev("true"), is_back]) + only([on4, rev("false"), is_back], "Idle 1")
                + only([on4, is_fwd], "Wait") + tr("Away"),
        "Away": by_game([on4, rev("true"), is_back]) + only([on4, rev("false"), is_back], "Idle 1") + only([on4, is_fwd], "Wait"),
        "Wait": tr("Arrive", exit_time=True),
        "Arrive": only([rev("true")], "Celebrate", exit_time=True) + only([rev("false")], "Idle 1", exit_time=True),
        "Celebrate": by_game([rev("true")], exit_time=True) + only([rev("false")], "Idle 1", exit_time=True),
        "Idle 1": by_game([on4, rev("true")], ms=250),
    }
    for s in SETS:
        outs[f"Idle {s}"] = only([on4, rev("false")], "Idle 1", ms=600)
    pad = " " * 16
    order = ["Boot", "Away", "Wait", "Arrive", "Celebrate", "Idle 1"] + [f"Idle {s}" for s in SETS]
    out = [f'            <StateMachineLayer name="{ROOM} Ball Motion" id="{n()}">', f'{pad}<AnyState x="160" y="200" id="{n()}"/>',
           f'{pad}<ExitState x="720" y="200" id="{n()}"/>', f'{pad}<EntryState x="0" y="0" id="{n()}">',
           f'{pad}    <StateTransition stateToId="{sid["Boot"]}" id="{n()}"/>', f'{pad}</EntryState>']
    for i, k in enumerate(order):
        out.append(f'{pad}<AnimationState animationId="{aids[anim_of.get(k, k)]}" x="{160 + 200 * i}" y="0" id="{sid[k]}">')
        out += [pad + "    " + l for l in outs[k]]
        out.append(f"{pad}</AnimationState>")
    out.append("            </StateMachineLayer>")
    si = max(i for i, l in enumerate(doc.lines) if l.strip() == "</StateMachine>")
    doc.lines[si:si] = out
    regen_guard.save(doc, WRITTEN_AGAINST, __file__)
    print(f"wrote {SCENE}")


if __name__ == "__main__":
    main()
