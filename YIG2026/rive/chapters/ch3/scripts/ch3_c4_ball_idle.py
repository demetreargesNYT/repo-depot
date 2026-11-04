"""Chapter 4 card 2: the proud ball (Demetre, 2026-11-04).

    python3 chapters/ch3/scripts/ch3_c4_ball_idle.py [--scene PATH]            prints the plan and the measured numbers, writes nothing
    python3 chapters/ch3/scripts/ch3_c4_ball_idle.py [--scene PATH] --write    adds the ball's animations and its two layers

The ball is "Chapter 4 Ball" (parked at x -60, y 2400 in the Floor Plane, drawn in front of the city). Nothing else in the scene is
changed except one wrapper node around Ball_01 ("Chapter 4 Ball Exit Turn", a pivot at the ball's centre), which the exit uses.

Layer "Chapter 4 Ball Motion" (reads scene, reveal, direction, startScene, topGame):
  Away (parked) -> Wait (87 frames, hidden, the wall's fade) -> Arrive (213 frames) -> Idle (600 frames, loops, one per fireworks set).
  Wait + Arrive are exactly the fireworks' 300 frame loop, so the Idle starts as the fireworks start again, and an Idle entered
  directly (startScene, or Back from the video / End) is in the same phase.
  Arrive: rolls in from off the left edge (six turns of the dot), slowing to a stop 5.5 units past its place, settles, looks up at the
  fireworks (rolls back, the dot tilts up) and comes to rest at x 747 on the floor line, size 1.2.
  Idle: hops (7 to 13 units) with the apex on that set's biggest bursts, looks up and gentle rocks in the gaps, and once, in the second
  half only, a showing-off hop (22 units, leaning back in the air) after which the ball puffs up and looks up. The first and last frame
  are the same pose.
  mini, midi and daily use the Crossword set's idle, like the fireworks.
  Leaving: reveal turns false. The ball's own pose is held (only its height and squash blend to the floor) and the exit layer carries it
  away, so a Back at any moment, even mid-roll, never snaps.

Layer "Chapter 4 Ball Exit": a wrapper node around Ball_01 (x and rotation only) rolls the ball out to the left, accelerating over 60 frames,
turning one dot-turn per circumference; it parks there until reveal is true again, then returns to 0 while the ball is hidden.

One gravity, 0.40 per frame squared: every hop is a parabola of integer frames.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
from ball_motion import pulse, release, smooth
from rml_edit import Doc, bake
from rml_read import Scene, chapter_dir

args = sys.argv[1:]
SCENE = Path(args[args.index("--scene") + 1]) if "--scene" in args else chapter_dir("ch3") / "scene.rml"
ROOM = "Chapter 4"
G, R, S = 0.40, 17.678, 1.2                    # gravity, the ball's radius at scale 1, its size
RS = R * S
FLOOR, DROP, BOT = 711.3, 14.5, 0.202          # the ball's lowest point; Ball_01 sits DROP below its node; its bottom is BOT*scale below Ball_01
REST_X = 747.0
X_START = REST_X - 12 * math.pi * RS           # six dot turns before its place: the dot is where it started when the ball stops
AWAY_Y, AWAY_X = 2400.0, X_START
WAIT, ARRIVE, IDLE, LEAVING = 87, 213, 600, 62
ROLL_T, OVER = 150, 5.5                        # roll-in frames and how far past its place it stops
EXIT_T, EXIT_D, EXIT_LEN, EXIT_REST = 60, 1000.0, 68, 1
VM = "1:14"
SCENE_P, DIR_P, TOP_P, REVEAL_P, START_P = "1:2713", "1:2855", "1:3300", "1:3310", "1:3400"
CH4, BACK = "1:9102", "1:9201"
TOP_VALUES = {"wordle": "1:9300", "connections": "1:9301", "strands": "1:9302", "spelling-bee": "1:9303",
              "mini": "1:9304", "midi": "1:9305", "daily": "1:9306"}
SET_OF = {"wordle": "Wordle", "connections": "Connections", "strands": "Strands", "spelling-bee": "Spelling Bee",
          "mini": "Crossword", "midi": "Crossword", "daily": "Crossword"}
SETS = ["Wordle", "Connections", "Strands", "Spelling Bee", "Crossword"]
# the burst peaks used per set (frame of the loop where the biggest bursts reach full size) and the hop's flight in frames
# (12 -> 7.2 units, 14 -> 9.8, 16 -> 12.8; a hop of T frames rises 0.4 * T * T / 8)
BURSTS = {"Wordle": [(64, 14), (156, 16), (274, 16)],            # large pieces at 1.94, 2.07 and 2.01 times
          "Connections": [(46, 14), (142, 16), (254, 14)],       # seven equal bursts; three spread across the loop
          "Strands": [(94, 12), (138, 14), (229, 16)],           # the 1.0, 1.41 and 1.63 times bursts
          "Spelling Bee": [(125, 14), (217, 14), (270, 16)],     # the big groups peaking at 125, 217 and 270
          "Crossword": [(46, 14), (134, 16), (240, 16)]}
SHOW_T = 21                                                      # the showing-off hop: 22 units
SQUAT, AFTER = 8, 30                                             # frames of squat before a take-off; the showing-off hop's aftermath
LOOK_AMP, ROCK_AMP = 0.40, 0.12                                  # radians the dot tilts for a look up; for a rock
SHOW_LEAN, PUFF = 0.55, 1.10


def node_y(contact, sy):
    """The ball node's y when the ball's lowest point is at `contact` and Ball_01's vertical scale is sy."""
    return contact - DROP - BOT * sy


# ---- Arrive -------------------------------------------------------------------------------------------------------------------
def arrive():
    """Per frame 0..ARRIVE: (x of the contact, rotation, scale)."""
    ease = lambda t: 0.5 - 0.5 * math.cos(math.pi * min(max(t, 0.0), 1.0))
    xs = {}
    D1 = REST_X + OVER - X_START
    look = -LOOK_AMP * RS
    for f in range(ARRIVE + 1):
        if f <= ROLL_T:
            u = f / ROLL_T
            xs[f] = X_START + D1 * (1 - (1 - u) ** 2.2)
        elif f <= 156:
            xs[f] = REST_X + OVER
        elif f <= 182:                                           # rolls back: looks up
            xs[f] = REST_X + OVER + (look - OVER) * ease((f - 156) / 26)
        elif f <= 192:
            xs[f] = REST_X + look
        else:                                                    # and settles into its place
            xs[f] = REST_X + look * (1 - ease((f - 192) / 21))
    xs[ARRIVE] = REST_X
    rot = {f: (xs[f] - REST_X) / RS for f in xs}
    return xs, rot


# ---- Idle ---------------------------------------------------------------------------------------------------------------------
def idle(bursts):
    """Per frame 0..IDLE: x, y of the contact, rotation, scale x, scale y; and the schedule as text."""
    a = [0.0] * (IDLE + 1)         # rolling tilt: the ball rolls this many radians (x follows, rotation follows)
    air = [0.0] * (IDLE + 1)       # extra turn in the air (x stays)
    lift = [0.0] * (IDLE + 1)
    d = [0.0] * (IDLE + 1)         # squash (+ stretch) in sy, sx moves the other way
    puff = [1.0] * (IDLE + 1)
    plan, busy = [], []

    def add_hop(t0, T, label):
        v = G * T / 2
        for k in range(T + 1):
            lift[t0 + k] = max(0.0, v * k - 0.5 * G * k * k)
        lift[t0 + T] = 0.0
        for k in range(SQUAT + 1):                               # squat before the take-off
            if t0 - SQUAT + k < t0:
                d[t0 - SQUAT + k] += -0.07 * smooth(k / SQUAT)
        for t in range(t0, min(IDLE, t0 + 40) + 1):              # then it lets go: a stretch that settles
            d[t] += release(t - t0, -0.07, tau=6.0, period=14.0) if t > t0 else -0.07
        amt = 0.05 + 0.002 * T
        for k in range(36):                                      # and squashes on landing
            if t0 + T + k <= IDLE:
                d[t0 + T + k] += -amt * pulse(k)
        plan.append((t0 + T // 2, f"hop {label} {0.4 * T * T / 8:.1f} units, apex {t0 + T // 2}"))

    for h in (0, 300):
        for p, T in bursts:
            t0 = p + h - T // 2
            add_hop(t0, T, f"on the burst at {p + h}")
            busy.append((t0 - SQUAT - 1, t0 + T + 14))
    busy.sort()
    gaps, prev = [], 4
    for s, e in busy:
        gaps.append((prev, s))
        prev = e
    gaps.append((prev, IDLE - 4))
    frag = []
    for s, e in gaps:                                            # cut the gaps at the half
        if s < 300 < e:
            frag += [(s, 300), (300, e)]
        else:
            frag.append((s, e))
    # the showing-off hop: the roomiest gap in the second half, centred
    need = SQUAT + SHOW_T + AFTER
    second = [(e - s, s, e) for s, e in frag if s >= 300 and e - s >= need + 6]
    L, s, e = max(second)
    t0 = s + (L - need) // 2 + SQUAT
    show = (t0 - SQUAT, t0 + SHOW_T + AFTER)
    v = G * SHOW_T / 2
    for k in range(SHOW_T + 1):
        lift[t0 + k] = max(0.0, v * k - 0.5 * G * k * k)
        air[t0 + k] = -SHOW_LEAN * math.sin(math.pi * k / SHOW_T) ** 2     # leans back in the air, upright again on landing
    lift[t0 + SHOW_T] = 0.0
    for k in range(SQUAT + 1):
        if t0 - SQUAT + k < t0:
            d[t0 - SQUAT + k] += -0.09 * smooth(k / SQUAT)
    for t in range(t0, t0 + 40):
        d[t] += release(t - t0, -0.09, tau=6.0, period=14.0) if t > t0 else -0.09
    for k in range(36):
        d[t0 + SHOW_T + k] += -0.10 * pulse(k)
    for k in range(AFTER + 1):                                   # puffs up and tilts the dot up, then settles
        u = k / AFTER
        puff[t0 + SHOW_T + k] = 1 + (PUFF - 1) * smooth(min(u / 0.35, 1)) * (1 - smooth(max((u - 0.55) / 0.45, 0)))
        a[t0 + SHOW_T + k] = -0.30 * smooth(min(u / 0.35, 1)) * (1 - smooth(max((u - 0.55) / 0.45, 0)))
    plan.append((t0 + SHOW_T // 2, f"SHOWING OFF: hop {0.4 * SHOW_T * SHOW_T / 8:.1f} units, apex {t0 + SHOW_T // 2}, leans back {SHOW_LEAN} rad, puffs to {PUFF}"))
    frag = [(fs, fe) for fs, fe in frag if fe <= show[0] or fs >= show[1]] + [(fs, show[0]) for fs, fe in frag if fs < show[0] < fe] \
        + [(show[1], fe) for fs, fe in frag if fs < show[1] < fe]
    for fs, fe in sorted(set(frag)):
        L = fe - fs
        if L >= 75:                                              # a look up at the fireworks, ending as the next hop begins
            D = 70
            e2 = fe - 4
            s2 = e2 - D
            for t in range(s2, e2 + 1):
                k = t - s2
                a[t] += -LOOK_AMP * smooth(min(k / 22, 1)) * (1 - smooth(max((k - 46) / 24, 0)))
            plan.append((s2, f"look up {s2}..{e2}, dot tilts {LOOK_AMP} rad"))
        elif L >= 48:                                            # a gentle rock, just after the landing
            P, n = 28, 1.5
            s2 = fs + 4
            for k in range(int(P * n) + 1):
                a[s2 + k] += ROCK_AMP * math.sin(2 * math.pi * k / P) * math.sin(math.pi * k / (P * n))
            plan.append((s2, f"rock {s2}..{s2 + int(P * n)}, +-{ROCK_AMP} rad"))
    for t in range(IDLE - 14, IDLE + 1):                         # a landing near the seam settles before the loop ends
        d[t] *= 1 - smooth((t - (IDLE - 14)) / 12)
    x = [REST_X + RS * a[f] for f in range(IDLE + 1)]
    y = [FLOOR - lift[f] for f in range(IDLE + 1)]
    rot = [a[f] + air[f] for f in range(IDLE + 1)]
    sy = [S * puff[f] * (1 + d[f]) for f in range(IDLE + 1)]
    sx = [S * puff[f] * (1 - 0.7 * d[f]) for f in range(IDLE + 1)]
    return x, y, rot, sx, sy, sorted(plan)


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


def main():
    write = "--write" in args
    sc = Scene(SCENE)
    room = next(e for e in sc.root.iter("Node") if e.get("name") == f"{ROOM} Room")
    by_name = {}
    for e in room.iter():
        by_name.setdefault(e.get("name"), e)
    ball, b01, spin = (by_name[k].get("id") for k in (f"{ROOM} Ball", "Ball_01", f"{ROOM} Ball Spin"))
    assert f"{ROOM} Ball Motion Arrive" not in [a for a in sc.animations] and "Chapter 4 Ball Exit Turn" not in by_name, "already applied"
    assert not any(l.get("name") == f"{ROOM} Ball Motion" for l in sc.root.iter("StateMachineLayer")), "already applied"

    ax, arot = arrive()
    idles = {s: idle(BURSTS[s]) for s in SETS}
    print(f"Arrive: x {X_START:.1f} -> {REST_X + OVER} in {ROLL_T} frames (start speed {2.2 * (REST_X + OVER - X_START) / ROLL_T:.1f}/frame), "
          f"rests {REST_X}, size {S}, rotation at rest {arot[ARRIVE]:.4f}")
    for s in SETS:
        x, y, rot, sx, sy, plan = idles[s]
        print(f"Idle {s}: top of the ball y {min(y[f] - 2 * R * sy[f] for f in range(IDLE + 1)):.1f}; first/last equal "
              f"{all(abs(v[0] - v[-1]) < 1e-9 for v in (x, y, rot, sx, sy))}")
        for _, text in plan:
            print("   ", text)
    if not write:
        return
    doc = Doc(SCENE)
    n = doc.new_id

    # ---- the exit wrapper around Ball_01: a pivot at the ball's centre
    px, py = -0.072 * S, DROP - 17.476 * S
    pid, aid = doc.wrap(b01, f"{ROOM} Ball Exit Turn", px, py)

    # ---- animations
    A = lambda k: f"{ROOM} Ball {k}"
    anims = [("Away", 1, False), ("Wait", WAIT, False), ("Arrive", ARRIVE, False)] + [(f"Idle {s}", IDLE, True) for s in SETS] + [("Leaving", LEAVING, False),
             ("Exit Rest", EXIT_REST, False), ("Exit Out", EXIT_LEN, False), ("Exit Parked", 1, False)]
    aids, new = {}, []
    for k, length, loop in anims:
        aids[k] = n()
        new += [f'        <LinearAnimation fps="60" duration="{length}"{" loopValue=" + chr(34) + "loop" + chr(34) if loop else ""} name="{A(k)}" id="{aids[k]}">',
                "        </LinearAnimation>"]
    li = doc.idx(next(e.get("id") for e in sc.root.iter("LinearAnimation") if e.get("name") == f"{ROOM} Loop"))
    doc.lines[li:li] = new

    def pose(anim, x, y, rot, sx, sy, length):
        last = length - 1
        for obj, prop, v in ((ball, "x", x), (ball, "y", node_y(y, sy)), (spin, "rotation", rot), (b01, "scaleX", sx), (b01, "scaleY", sy)):
            doc.set_prop(anim, obj, prop, [(0, v, "hold")] + ([(last, v, "hold")] if last else []))

    pose(A("Away"), AWAY_X, AWAY_Y, 0.0, S, S, 1)
    # Wait: parked far below the stage, where Arrive starts from (x), pose of the hidden ball
    for obj, prop, v in ((ball, "x", AWAY_X), (ball, "y", node_y(AWAY_Y, S)), (spin, "rotation", arot[0]), (b01, "scaleX", S), (b01, "scaleY", S)):
        doc.set_prop(A("Wait"), obj, prop, [(0, v, "hold"), (WAIT - 1, v, "hold")])
    fr = range(ARRIVE + 1)
    doc.set_prop(A("Arrive"), ball, "x", bake(ax, fr))
    doc.set_prop(A("Arrive"), ball, "y", [(0, node_y(FLOOR, S), "hold"), (ARRIVE, node_y(FLOOR, S), "hold")])
    doc.set_prop(A("Arrive"), spin, "rotation", bake(arot, fr))
    for prop in ("scaleX", "scaleY"):
        doc.set_prop(A("Arrive"), b01, prop, [(0, S, "hold"), (ARRIVE, S, "hold")])
    # Away's rotation is Arrive's first, so the pose does not turn when it starts
    doc.set_prop(A("Away"), spin, "rotation", [(0, arot[0], "hold")])
    fi = range(IDLE + 1)
    for s in SETS:
        x, y, rot, sx, sy, _ = idles[s]
        nm = A(f"Idle {s}")
        doc.set_prop(nm, ball, "x", bake(dict(enumerate(x)), fi))
        doc.set_prop(nm, ball, "y", bake({f: node_y(y[f], sy[f]) for f in fi}, fi))
        doc.set_prop(nm, spin, "rotation", bake(dict(enumerate(rot)), fi))
        doc.set_prop(nm, b01, "scaleX", bake(dict(enumerate(sx)), fi))
        doc.set_prop(nm, b01, "scaleY", bake(dict(enumerate(sy)), fi))
    # Leaving keys only the height and the squash: they blend to the floor, while x and the turn keep their last values
    doc.set_prop(A("Leaving"), ball, "y", [(0, node_y(FLOOR, S), "hold")])
    doc.set_prop(A("Leaving"), b01, "scaleX", [(0, S, "hold")])
    doc.set_prop(A("Leaving"), b01, "scaleY", [(0, S, "hold")])
    # the exit wrapper
    doc.set_prop(A("Exit Rest"), pid, "x", [(0, px, "hold")])
    doc.set_prop(A("Exit Rest"), pid, "rotation", [(0, 0.0, "hold")])
    fo = range(EXIT_LEN + 1)
    ex = {f: -EXIT_D * (min(f, EXIT_T) / EXIT_T) ** 2 for f in fo}
    doc.set_prop(A("Exit Out"), pid, "x", bake({f: px + ex[f] for f in fo}, fo))
    doc.set_prop(A("Exit Out"), pid, "rotation", bake({f: ex[f] / RS for f in fo}, fo))
    doc.set_prop(A("Exit Parked"), pid, "x", [(0, px - EXIT_D, "hold")])
    doc.set_prop(A("Exit Parked"), pid, "rotation", [(0, -EXIT_D / RS, "hold")])

    # ---- the layers
    sid = {k: n() for k in ["Boot", "Away", "Wait", "Arrive"] + [f"Idle {s}" for s in SETS] + ["Leaving", "Rest", "Out", "Parked"]}
    anim_of = {"Boot": "Away", "Rest": "Exit Rest", "Out": "Exit Out", "Parked": "Exit Parked"}

    def tr(to, conds=(), exit_time=False, ms=0):
        attrs = f' stateToId="{sid[to]}" duration="{ms}"'
        if exit_time:
            attrs += ' enableExitTime="true" exitTimeIsPercetange="true" exitTime="100"'
        if not conds:
            return [f'<StateTransition{attrs} id="{n()}"/>']
        body = [l for c in conds for l in c]
        return [f'<StateTransition{attrs} id="{n()}">'] + ["    " + l for l in body] + ["</StateTransition>"]

    on4 = lambda: cond_enum(n, SCENE_P, CH4)
    rev = lambda v: cond_bool(n, REVEAL_P, v)

    def by_game(conds, exit_time=False):
        out = []
        for tv, val in TOP_VALUES.items():
            out += tr(f"Idle {SET_OF[tv]}", [c() for c in conds] + [cond_enum(n, TOP_P, val)], exit_time=exit_time)
        return out

    outs = {
        "Boot": by_game([on4, lambda: rev("true"), lambda: cond_enum(n, START_P, CH4)]) + by_game([on4, lambda: rev("true"), lambda: cond_enum(n, DIR_P, BACK)])
                + tr("Wait", (on4(), rev("true"))) + tr("Away", (on4(), rev("false"))),
        "Away": by_game([on4, lambda: rev("true"), lambda: cond_enum(n, DIR_P, BACK)]) + tr("Wait", (on4(), rev("true"))),
        "Wait": tr("Away", (rev("false"),)) + tr("Arrive", exit_time=True),
        "Arrive": tr("Leaving", (on4(), rev("false")), ms=100) + by_game([], exit_time=True),
        "Leaving": tr("Away", exit_time=True),
        "Rest": tr("Out", (on4(), rev("false"))),
        "Out": tr("Parked", exit_time=True),
        "Parked": tr("Rest", (rev("true"),)),
    }
    for s in SETS:
        outs[f"Idle {s}"] = tr("Leaving", (on4(), rev("false")), ms=100)
    pad = " " * 16

    def layer(name, states):
        out = [f'            <StateMachineLayer name="{name}" id="{n()}">', f'{pad}<AnyState x="160" y="200" id="{n()}"/>',
               f'{pad}<ExitState x="720" y="200" id="{n()}"/>', f'{pad}<EntryState x="0" y="0" id="{n()}">',
               f'{pad}    <StateTransition stateToId="{sid[states[0]]}" id="{n()}"/>', f'{pad}</EntryState>']
        for i, k in enumerate(states):
            out.append(f'{pad}<AnimationState animationId="{aids[anim_of.get(k, k)]}" x="{160 + 200 * i}" y="0" id="{sid[k]}">')
            out += [pad + "    " + l for l in outs[k]]
            out.append(f"{pad}</AnimationState>")
        out.append("            </StateMachineLayer>")
        return out

    # Boot's animation is Away; the states that play an animation named like themselves use it
    anim_of.update({"Boot": "Away"})
    for k in ("Away", "Wait", "Arrive", "Leaving"):
        anim_of[k] = k
    for s in SETS:
        anim_of[f"Idle {s}"] = f"Idle {s}"
    aids = {**aids}
    motion = layer(f"{ROOM} Ball Motion", ["Boot", "Away", "Wait", "Arrive"] + [f"Idle {s}" for s in SETS] + ["Leaving"])
    exitl = layer(f"{ROOM} Ball Exit", ["Rest", "Out", "Parked"])
    si = max(i for i, l in enumerate(doc.lines) if l.strip() == "</StateMachine>")
    doc.lines[si:si] = motion + exitl
    doc.save()
    print(f"wrote {SCENE}")


if __name__ == "__main__":
    main()
