"""Chapter 4: when reveal turns true, a few more balls join the player's, building towards End's pile (Demetre, 2026-11-03).

    python3 chapters/ch3/scripts/ch3_c4_crowd.py --write      once, on the scene as committed in 9871650

Four standard balls (Chapter 1 card 3's art and dot) in End's red, 0.7 to 1.1 times, drawn in front of the stack in its floor plane.
A layer of their own, "Chapter 4 Crowd", reads reveal (engineering changes nothing):
- reveal turns true on chapter-4: they wait for the wall's fade (1.45 s), then come in one at a time: one rolls in from the left, one
  from the right, one drops from above just outside the phone frame (so it never crosses the copy) and bounces down, keeping 70
  percent of its speed each time, then rolls into place; the last, the smallest, rolls in from the left and taps the first, which
  gives a little and settles. They settle at the base of the stack at the frame's sides (card 3's video covers the centre).
- settled, they idle: small hops at different times, never together; the 6 s loop ends on its first pose.
- reveal turns false on chapter-4 (Back to card 1): they roll quickly back out the way they came.
- opened on chapter-4 with reveal true (startScene), or arriving there with Back, they are already settled.
Out of play they wait far below the stage, so the room's pans never carry them across it. One gravity (0.40) for every flight; the
dots turn one turn per circumference as they roll.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
from ball_motion import pulse, smooth
from rml_edit import Doc, bake, num
from rml_read import Scene, chapter_dir

SCENE = chapter_dir("ch3") / "scene.rml"
ROOM = "Chapter 4"
G, R, FLOOR = 0.40, 17.678, 712.0
WAIT, IDLE, LEAVE = 87, 360, 36
AWAY_Y = 2400.0
VM = "1:14"
SCENE_P, DIR_P, REVEAL_P, START_P = "1:2713", "1:2855", "1:3310", "1:3400"
CH4, BACK = "1:9102", "1:9201"
# name, size, rest x, how it comes in, when it starts (frames after the wait), which way it leaves
BALLS = [("A", 0.7, None, "left", 75, "left"), ("B", 1.0, 614.0, "left", 0, "left"),
         ("C", 1.1, 878.0, "right", 25, "right"), ("D", 0.8, 914.0, "drop", 45, "right")]
HOPS = {"A": [(35, 5.0)], "B": [(170, 7.0)], "C": [(95, 8.0), (290, 6.0)], "D": [(230, 5.0)]}


def roll_in(x0, x1, start, T, v_end=0.0):
    """Positions from x0 (at frame start) to x1 (at start + T), slowing evenly to v_end."""
    D = x1 - x0
    v0 = 2 * D / T - v_end
    a = (v_end - v0) / T
    return lambda f: x0 if f <= start else (x1 if f >= start + T else x0 + v0 * (f - start) + 0.5 * a * (f - start) ** 2)


def build():
    """Per ball: (x, y of the contact point, squash, spin) on every frame of Arrive; its rest pose; its Away pose."""
    out = {}
    rB, rA = R * 1.0, R * 0.7
    tapB = 0
    # B and C roll in; A rolls in last and taps B
    for name, size, rest, how, start, _ in BALLS:
        r = R * size
        xs, ys, sqs = {}, {}, {}
        if how in ("left", "right"):
            if name == "A":
                contact_x = 614.0 - rB - rA
                T = 110
                fn = roll_in(-30.0, contact_x, start, T, v_end=1.2)
                meet = start + T
                for f in range(0, meet + 60):
                    if f <= meet:
                        xs[f] = fn(f)
                    else:
                        t = min(f - meet, 4)
                        xs[f] = contact_x + 1.2 * (t - t * t / 8)
                tapB = meet
            else:
                x0 = -30.0 if how == "left" else 1525.0
                fn = roll_in(x0, rest, start, 110)
                for f in range(0, start + 170):
                    xs[f] = fn(f)
            for f in xs:
                ys[f] = FLOOR
        else:                                                   # drops from above, outside the phone frame, and bounces down
            x, y, vx, vy = 1028.0, -2.0, -0.32, 0.0
            f = start
            xs[f], ys[f] = x, y
            for f0 in range(start):
                xs[f0], ys[f0] = x, y
            bounces = 0
            while True:
                f += 1
                vy += G
                x += vx
                y += vy
                if y >= FLOOR:
                    y = FLOOR
                    vy = -0.7 * vy
                    vx *= 0.95
                    bounces += 1
                    sqs[f] = min(0.10, 0.006 * abs(vy / 0.7))
                    if abs(vy) < 2.0:
                        break
                xs[f], ys[f] = x, y
            xs[f], ys[f] = x, FLOOR
            land = f
            fn = roll_in(x, rest, land, 40)
            for g in range(land, land + 60):
                xs[g], ys[g] = fn(g), FLOOR
        out[name] = dict(size=size, r=r, xs=xs, ys=ys, sqs=sqs)
    # B gives a little when A taps it, and settles
    b = out["B"]
    for f in range(tapB, tapB + 30):
        b["xs"][f] = 614.0 + 3.0 * smooth(min((f - tapB) / 8, 1)) - 0.6 * smooth(min(max((f - tapB - 8) / 10, 0), 1))
    end = max(max(v["xs"]) for v in out.values()) + 1
    for v in out.values():                                    # between moves a ball stays where it was
        for f in range(end + 1):
            if f not in v["xs"]:
                v["xs"][f] = v["xs"][f - 1]
            if f not in v["ys"]:
                v["ys"][f] = v["ys"][f - 1]
        v["rest"] = (v["xs"][end], FLOOR)
    return out, end


def squash_series(sqs, n):
    """Landing squash pulses (scale y down, x up) from {frame: amount}."""
    sy = {f: 1.0 for f in range(n + 1)}
    sx = {f: 1.0 for f in range(n + 1)}
    for f0, a in sqs.items():
        for k in range(30):
            if f0 + k <= n:
                p = pulse(k)
                sy[f0 + k] *= 1 - a * p
                sx[f0 + k] *= 1 + 0.7 * a * p
    return sx, sy


def ball_lines(p, ids, size, x, y):
    ball, b01, b01s, spin, spinart, hl, base, n = ids
    return [f'{p}<Node x="{num(x)}" y="{num(y)}" name="{ball[1]}" id="{ball[0]}">',
            f'{p}    <Node scaleX="{size}" scaleY="{size}" name="Ball_01" id="{b01}">',
            f'{p}        <Node x="-0.072021484" y="0.096008301" name="Ball_01_Scale" id="{b01s}">',
            f'{p}            <Node y="-17.572" name="{ball[1]} Spin" id="{spin}">',
            f'{p}                <Node y="17.572" name="{ball[1]} Spin Art" id="{spinart}">',
            f'{p}                    <Shape x="6.3640137" y="-23.834076" rotation="-0.77726489" name="Ball_01_Highlight" id="{hl}">',
            f'{p}                        <Ellipse width="7.5" height="9.6440001" x="-1.0000001" scaleY="1.174" scaleX="1.174" id="{n()}"/>',
            f'{p}                        <Fill id="{n()}">', f'{p}                            <SolidColor colorValue="FFFFFFFF" id="{n()}"/>', f'{p}                        </Fill>',
            f'{p}                        <Stroke thickness="1.5" cap="round" join="round" transformAffectsStroke="false" id="{n()}">',
            f'{p}                            <SolidColor colorValue="FF1F1F1F" id="{n()}"/>', f'{p}                        </Stroke>',
            f'{p}                    </Shape>',
            f'{p}                    <Shape y="-17.571991" name="Crowd_Base" id="{base}">',
            f'{p}                        <PointsPath isClosed="true" name="Path" id="{n()}">',
            f'{p}                            <CubicDetachedVertex inRotation="3.1415927" inDistance="9.7632895" outDistance="9.7632895" y="-17.677999" id="{n()}"/>',
            f'{p}                            <CubicDetachedVertex inRotation="-1.5707964" inDistance="9.7632895" outRotation="1.5707964" outDistance="9.7632895" x="17.677999" id="{n()}"/>',
            f'{p}                            <CubicDetachedVertex inDistance="9.7632895" outRotation="3.1415927" outDistance="9.7632895" y="17.677999" id="{n()}"/>',
            f'{p}                            <CubicDetachedVertex inRotation="1.5707964" inDistance="9.7632895" outRotation="-1.5707964" outDistance="9.7632895" x="-17.677999" id="{n()}"/>',
            f'{p}                        </PointsPath>',
            f'{p}                        <Fill id="{n()}">', f'{p}                            <SolidColor colorValue="FFFF5959" id="{n()}"/>', f'{p}                        </Fill>',
            f'{p}                        <Stroke thickness="1.5" cap="round" join="round" transformAffectsStroke="false" id="{n()}">',
            f'{p}                            <SolidColor colorValue="FF1F1F1F" id="{n()}"/>', f'{p}                        </Stroke>',
            f'{p}                    </Shape>',
            f'{p}                </Node>', f'{p}            </Node>', f'{p}        </Node>', f'{p}    </Node>', f'{p}</Node>']


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
    arrive, A_len = build()
    doc = Doc(SCENE)
    n = doc.new_id
    sc = Scene(SCENE)
    room = next(e for e in sc.root.iter("Node") if e.get("name") == f"{ROOM} Room")
    plane = next(c for c in room if c.get("name") == f"{ROOM} Floor Plane").get("id")
    pi = doc.idx(plane)
    p = " " * (len(doc.lines[pi]) - len(doc.lines[pi].lstrip()) + 4)
    ids, lines = {}, []
    for name, size, *_ in BALLS:
        i = ((n(), f"{ROOM} Crowd Ball {name}"), n(), n(), n(), n(), n(), n(), n)
        ids[name] = i
        lines += ball_lines(p, i, size, arrive[name]["xs"][0], AWAY_Y)
    doc.lines[pi + 1:pi + 1] = lines                           # first in the floor plane: drawn in front of the stack
    # ---- the animations
    names = {k: f"{ROOM} Crowd {k}" for k in ("Away", "Wait", "Arrive", "Idle", "Leave")}
    lengths = {"Away": 1, "Wait": WAIT, "Arrive": A_len, "Idle": IDLE, "Leave": LEAVE}
    loops = {"Idle": "loop"}
    aids = {}
    li = doc.idx(next(e.get("id") for e in sc.root.iter("LinearAnimation") if e.get("name") == f"{ROOM} Loop"))
    new = []
    for k, nm in names.items():
        aids[k] = n()
        lv = f' loopValue="{loops.get(k, "oneShot")}"'
        new += [f'        <LinearAnimation fps="60" duration="{lengths[k]}"{lv} name="{nm}" id="{aids[k]}">', "        </LinearAnimation>"]
    doc.lines[li:li] = new
    for name, size, rest, how, start, leave in BALLS:
        ball, b01, b01s, spin, *_ = ids[name]
        a = arrive[name]
        r = a["r"]
        xs, ys = a["xs"], a["ys"]
        th = [0.0]
        for f in range(1, A_len + 1):
            th.append(th[-1] + (xs[f] - xs[f - 1]) / r)
        sx, sy = squash_series(a["sqs"], A_len)
        rest_x = xs[A_len]
        th_rest = th[A_len]
        # Away and Wait: far below the stage, where Arrive starts from (x), turned as at the end of Leave
        for k in ("Away", "Wait"):
            L = lengths[k]
            doc.set_prop(names[k], ball[0], "x", [(0, xs[0], "hold")] + ([(L - 1, xs[0], "hold")] if L > 1 else []))
            doc.set_prop(names[k], ball[0], "y", [(0, AWAY_Y, "hold")] + ([(L - 1, AWAY_Y, "hold")] if L > 1 else []))
            doc.set_prop(names[k], spin, "rotation", [(0, 0.0, "hold")])
            for prop in ("scaleX", "scaleY"):
                doc.set_prop(names[k], b01, prop, [(0, size, "hold")])
        fr = range(A_len + 1)
        yv = {f: (AWAY_Y if f < start else ys[f]) for f in fr}       # out of play until its start; there x is off the stage
        doc.set_prop(names["Arrive"], ball[0], "x", bake(xs, fr))
        doc.set_prop(names["Arrive"], ball[0], "y", [(0, AWAY_Y, "hold")] + [k for k in bake(yv, fr) if k[0] >= start - 1])
        doc.set_prop(names["Arrive"], spin, "rotation", bake({f: th[f] for f in fr}, fr))
        doc.set_prop(names["Arrive"], b01, "scaleX", bake({f: size * sx[f] for f in fr}, fr))
        doc.set_prop(names["Arrive"], b01, "scaleY", bake({f: size * sy[f] for f in fr}, fr))
        # Idle: small hops at their own times; the loop ends on its first pose
        fi = range(IDLE + 1)
        iy = {f: FLOOR for f in fi}
        hsq = {}
        for t0, h in HOPS[name]:
            v = math.sqrt(2 * G * h)
            T = int(round(2 * v / G))
            for t in range(T + 1):
                iy[t0 + t] = FLOOR - (v * t - 0.5 * G * t * t)
            iy[t0 + T] = FLOOR
            hsq[t0 + T] = 0.05
        isx, isy = squash_series(hsq, IDLE)
        doc.set_prop(names["Idle"], ball[0], "x", [(0, rest_x, "hold"), (IDLE, rest_x, "hold")])
        doc.set_prop(names["Idle"], ball[0], "y", bake(iy, fi))
        doc.set_prop(names["Idle"], spin, "rotation", [(0, th_rest, "hold"), (IDLE, th_rest, "hold")])
        doc.set_prop(names["Idle"], b01, "scaleX", bake({f: size * isx[f] for f in fi}, fi))
        doc.set_prop(names["Idle"], b01, "scaleY", bake({f: size * isy[f] for f in fi}, fi))
        # Leave: rolls out quickly the way it came, speeding up evenly
        target = -40.0 if leave == "left" else 1535.0
        acc = 2 * (target - rest_x) / LEAVE ** 2
        fl = range(LEAVE + 1)
        lx = {f: rest_x + 0.5 * acc * f * f for f in fl}
        doc.set_prop(names["Leave"], ball[0], "x", bake(lx, fl))
        doc.set_prop(names["Leave"], ball[0], "y", [(0, FLOOR, "hold"), (LEAVE, FLOOR, "hold")])
        doc.set_prop(names["Leave"], spin, "rotation", bake({f: th_rest + (lx[f] - rest_x) / r for f in fl}, fl))
        for prop in ("scaleX", "scaleY"):
            doc.set_prop(names["Leave"], b01, prop, [(0, size, "hold")])
    # ---- the layer
    sid = {k: n() for k in ("Boot", "Away", "Wait", "Arrive", "Idle", "Leave")}
    anim_of = {"Boot": "Away", "Away": "Away", "Wait": "Wait", "Arrive": "Arrive", "Idle": "Idle", "Leave": "Leave"}

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
    outs = {
        "Boot": tr("Idle", (on4(), rev("true"), cond_enum(n, START_P, CH4))) + tr("Idle", (on4(), rev("true"), cond_enum(n, DIR_P, BACK)))
                + tr("Wait", (on4(), rev("true"))) + tr("Away", (on4(), rev("false"))),
        "Away": tr("Idle", (on4(), rev("true"), cond_enum(n, DIR_P, BACK))) + tr("Wait", (on4(), rev("true"))),
        "Wait": tr("Away", (rev("false"),)) + tr("Arrive", exit_time=True),
        "Arrive": tr("Leave", (on4(), rev("false")), ms=150) + tr("Idle", exit_time=True),
        "Idle": tr("Leave", (on4(), rev("false")), ms=150),
        "Leave": tr("Away", exit_time=True),
    }
    pad = " " * 16
    layer = [f'            <StateMachineLayer name="{ROOM} Crowd" id="{n()}">', f'{pad}<AnyState x="160" y="200" id="{n()}"/>',
             f'{pad}<ExitState x="720" y="200" id="{n()}"/>', f'{pad}<EntryState x="0" y="0" id="{n()}">',
             f'{pad}    <StateTransition stateToId="{sid["Boot"]}" id="{n()}"/>', f'{pad}</EntryState>']
    for i, k in enumerate(("Boot", "Away", "Wait", "Arrive", "Idle", "Leave")):
        body = outs[k]
        layer.append(f'{pad}<AnimationState animationId="{aids[anim_of[k]]}" x="{160 + 200 * i}" y="0" id="{sid[k]}">')
        layer += [pad + "    " + l for l in body]
        layer.append(f"{pad}</AnimationState>")
    layer.append("            </StateMachineLayer>")
    si = max(i for i, l in enumerate(doc.lines) if l.strip() == "</StateMachine>")
    doc.lines[si:si] = layer
    doc.save()
    print(f"wrote {SCENE}: {ROOM} Crowd: Arrive {A_len} frames ({A_len / 60:.2f} s after the {WAIT / 60:.2f} s wait); rests "
          + ", ".join(f"{k} x {arrive[k]['xs'][A_len]:.1f} ({arrive[k]['size']}x)" for k in arrive))


if __name__ == "__main__":
    if "--write" not in sys.argv:
        raise SystemExit(__doc__)
    main()
