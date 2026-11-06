"""Chapter 4 finesse note 1 of the 2026-11-06 12:06 send: the clouds come in one by one as the city reaches the sky, each with its own small
animation, and go out the same way when reveal turns true (the next card).

    python3 chapters/ch3/scripts/ch3_c4_clouds_in_out.py --scene PATH [--write]       once; it asserts on a second run

Replaces the "Chapter 4 Clouds Fade" layer of ch3_c4_city_lives.py (a plain 0.5 s fade of the whole group) with one layer, "Chapter 4 Clouds":
    Rest (hidden) -> In (192 frames, the room's Intro: each cloud pops in at its own frame, 112 to 186) -> Shown
    Shown -> Out (38 frames, every cloud its own way out, 2 frames apart) on reveal true -> Hidden -> Return (60 frames) on Back to card 1
    a startScene or a Back arrival goes straight to Shown (reveal false) or Hidden (reveal true), already built.
Each cloud is keyed on scaleX, scaleY, rotation and opacity only (the drift layer keeps x and y). No new setting.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rml_edit import Doc  # noqa: E402
from rml_read import Scene, chapter_dir  # noqa: E402
import ch3_c4_city as city  # noqa: E402
from ch3_c4_city_lives import key_lines, ROOM  # noqa: E402

# cloud number (the shape is "Chapter 4 Cloud N") -> (entrance style, exit style, frame it comes in at during the Intro)
PIECES = {
    "9": ("puff", "puff", 112), "1": ("inflate", "deflate", 124), "6": ("dot", "dot", 132), "7": ("pill", "pill", 138),
    "2": ("tilt", "tilt", 142), "8": ("pill", "pill", 150), "10": ("spin", "spin", 150), "5": ("dot", "dot", 160),
    "3": ("pop", "pop", 160), "4": ("dot", "dot", 168),
}
EXIT_ORDER = ["1", "3", "4", "2", "8", "7", "9", "6", "10", "5"]
IN_LEN, OUT_LEN, RETURN_LEN = 192, 38, 60
PROPS = ("scaleX", "scaleY", "rotation", "opacity")

# per style: prop -> [(frames after the start, value, ease leaving that key)]; props not listed stay at the shown value
ENTER = {
    "pop": {"s": [(0, 0, "power2.out"), (12, 1.15, "power2.inOut"), (22, 1, "hold")]},
    "inflate": {"scaleX": [(0, 0, "power2.out"), (10, 1.2, "power2.inOut"), (20, 1, "hold")],
                "scaleY": [(0, 0, "power2.out"), (13, 1.3, "power2.inOut"), (24, 1, "hold")]},
    "tilt": {"s": [(0, 0, "power2.out"), (14, 1.1, "power2.inOut"), (24, 1, "hold")], "rotation": [(0, -0.55, "power2.out"), (24, 0, "hold")]},
    "puff": {"scaleX": [(0, 0, "power2.out"), (16, 1, "hold")], "scaleY": [(0, 0, "power2.out"), (12, 1.25, "power2.inOut"), (24, 1, "hold")]},
    "spin": {"s": [(0, 0, "power2.out"), (18, 1, "hold")], "rotation": [(0, 0.9, "power2.out"), (26, 0, "hold")]},
    "dot": {"s": [(0, 0, "power2.out"), (9, 1.5, "power2.inOut"), (18, 1, "hold")]},
    "pill": {"scaleX": [(0, 0, "power2.out"), (12, 1.2, "power2.inOut"), (20, 1, "hold")], "scaleY": [(0, 0, "power2.out"), (6, 1, "hold")]},
}
LEAVE = {
    "pop": {"s": [(0, 1, "power2.out"), (5, 1.1, "power2.in"), (18, 0, "hold")]},
    "deflate": {"scaleX": [(0, 1, "power2.out"), (5, 1.15, "power2.in"), (18, 0, "hold")], "scaleY": [(0, 1, "power2.in"), (16, 0, "hold")]},
    "tilt": {"s": [(0, 1, "power2.in"), (16, 0, "hold")], "rotation": [(0, 0, "power2.in"), (16, 0.5, "hold")]},
    "puff": {"scaleY": [(0, 1, "power2.out"), (5, 1.2, "power2.in"), (18, 0, "hold")], "scaleX": [(0, 1, "power2.in"), (18, 0, "hold")]},
    "spin": {"s": [(0, 1, "power2.in"), (18, 0, "hold")], "rotation": [(0, 0, "power2.in"), (18, -0.9, "hold")]},
    "dot": {"s": [(0, 1, "power2.out"), (4, 1.3, "power2.in"), (12, 0, "hold")]},
    "pill": {"scaleX": [(0, 1, "power2.in"), (12, 0, "hold")], "scaleY": [(0, 1, "hold"), (8, 1, "power2.in"), (14, 0, "hold")]},
}


def piece_tracks(style_spec, t0, entering, length):
    """{prop: keys} for one cloud in an animation of `length` frames: waiting (hidden, or shown), its own move from t0, then settled."""
    before, after = (0, 1) if entering else (1, 0)
    out = {}
    for prop in PROPS[:3]:
        spec = style_spec.get(prop) or (style_spec.get("s") if prop in ("scaleX", "scaleY") else None)
        rest = before if prop != "rotation" else 0
        end = after if prop != "rotation" else (0 if entering else None)
        if spec is None:
            v = after if prop != "rotation" else 0
            out[prop] = [(0, rest, "hold"), (length, v, "hold")] if rest != v else [(0, v, "hold"), (length, v, "hold")]
            continue
        keys = [(0, rest, "hold")] if t0 > 0 else []
        for dt, v, how in spec:
            keys.append((t0 + dt, v, how))
        last = keys[-1]
        if last[0] < length:
            keys.append((length, last[1], "hold"))
        else:
            keys[-1] = (last[0], last[1], "hold")
        out[prop] = keys
    span = max(dt for spec in style_spec.values() for dt, _, _ in spec)
    if entering:
        out["opacity"] = [(0, 0.0, "hold"), (t0, 1.0, "hold"), (length, 1.0, "hold")] if t0 > 0 else [(0, 1.0, "hold"), (length, 1.0, "hold")]
    else:
        out["opacity"] = [(0, 1.0, "hold"), (t0 + span, 0.0, "hold"), (length, 0.0, "hold")]
    return out


def dedupe(keys):
    out = []
    for f, v, h in keys:
        if out and out[-1][0] == f:
            out.pop()
        out.append((f, v, h))
    return out


def animation(doc, name, length, loop_value, tracks):
    """tracks: {shape id: {prop: keys}}"""
    aid = doc.new_id()
    lines = [f'        <LinearAnimation fps="60" duration="{length}"{" loopValue=" + chr(34) + loop_value + chr(34) if loop_value else ""} name="{name}" id="{aid}">']
    for sid, props in tracks.items():
        lines.append(f'            <KeyedObject objectId="{sid}" id="{doc.new_id()}">')
        for prop in PROPS:
            lines.append(f'                <KeyedProperty property="{prop}" id="{doc.new_id()}">')
            lines += key_lines(doc, dedupe(props[prop]), " " * 20)
            lines.append("                </KeyedProperty>")
        lines.append("            </KeyedObject>")
    lines.append("        </LinearAnimation>")
    return aid, lines


def pose(value, rot=0.0):
    return {"scaleX": [(0, value, "hold")], "scaleY": [(0, value, "hold")], "rotation": [(0, rot, "hold")], "opacity": [(0, value, "hold")]}


def main():
    argv = sys.argv
    path = Path(argv[argv.index("--scene") + 1]) if "--scene" in argv else chapter_dir("ch3") / "scene.rml"
    doc = Doc(path)
    assert any(f'name="{ROOM} Clouds Fade"' in l for l in doc.lines), "already applied (or the cloud pass is missing)"
    sc = Scene(path)
    ids = {n: e.get("id") for e in sc.root.iter("Shape") for n in [(e.get("name") or "").replace(f"{ROOM} Cloud ", "")] if (e.get("name") or "").startswith(f"{ROOM} Cloud ")}
    assert set(ids) == set(PIECES), ids

    # remove the old fade layer and its two poses
    for nm in (f"{ROOM} Clouds Shown", f"{ROOM} Clouds Hidden"):
        a, b = doc.anim(nm)
        del doc.lines[a:b + 1]
    li = next(i for i, l in enumerate(doc.lines) if f'<StateMachineLayer name="{ROOM} Clouds Fade"' in l)
    del doc.lines[li:doc.end(li) + 1]

    tracks = {}
    tracks["hidden"] = {ids[k]: pose(0.0) for k in ids}
    tracks["shown"] = {ids[k]: pose(1.0) for k in ids}
    tracks["in"] = {ids[k]: piece_tracks(ENTER[PIECES[k][0]], PIECES[k][2], True, IN_LEN) for k in ids}
    tracks["out"] = {ids[k]: piece_tracks(LEAVE[PIECES[k][1]], 2 * EXIT_ORDER.index(k), False, OUT_LEN) for k in ids}
    tracks["return"] = {ids[k]: piece_tracks(ENTER[PIECES[k][0]], 3 * EXIT_ORDER.index(k), True, RETURN_LEN) for k in ids}
    specs = [("hidden", f"{ROOM} Clouds Hidden", 1, None), ("shown", f"{ROOM} Clouds Shown", 1, None), ("in", f"{ROOM} Clouds In", IN_LEN, "oneShot"),
             ("out", f"{ROOM} Clouds Out", OUT_LEN, "oneShot"), ("return", f"{ROOM} Clouds Return", RETURN_LEN, "oneShot")]
    aids, blocks = {}, []
    for key, nm, length, lv in specs:
        aids[key], lines = animation(doc, nm, length, lv, tracks[key])
        blocks += lines
    loop_anim = next(e for e in sc.root.iter("LinearAnimation") if e.get("name") == f"{ROOM} Loop")
    li = doc.idx(loop_anim.get("id"))
    doc.lines[li:li] = blocks

    n = doc.new_id
    pad = " " * 16
    sid = {k: n() for k in ("rest", "in", "shown", "out", "hidden", "return")}
    on4 = lambda: city._cond_enum(n, city.SCENE_P, city.CH4)
    rev = lambda v: city._cond_bool(n, city.REVEAL_P, v)

    def tr(to, conds=(), exit_time=False):
        attrs = f' stateToId="{sid[to]}" duration="0"'
        if exit_time:
            attrs += ' enableExitTime="true" exitTimeIsPercetange="true" exitTime="100"'
        if not conds:
            return [f'<StateTransition{attrs} id="{n()}"/>']
        return [f'<StateTransition{attrs} id="{n()}">'] + ["    " + l for c in conds for l in c] + ["</StateTransition>"]
    outs = {
        "rest": (tr("hidden", (on4(), rev("true"), city._cond_enum(n, city.START_P, city.CH4))) + tr("hidden", (on4(), rev("true"), city._cond_enum(n, city.DIR_P, city.BACK)))
                 + tr("shown", (on4(), rev("false"), city._cond_enum(n, city.START_P, city.CH4))) + tr("shown", (on4(), rev("false"), city._cond_enum(n, city.DIR_P, city.BACK)))
                 + tr("in", (on4(),))),
        "in": tr("shown", (rev("false"),), True) + tr("hidden", (rev("true"),), True),
        "shown": tr("out", (rev("true"),)),
        "out": tr("hidden", (), True),
        "hidden": tr("return", (on4(), rev("false"))),
        "return": tr("shown", (), True),
    }
    anim_of = {"rest": "hidden", "in": "in", "shown": "shown", "out": "out", "hidden": "hidden", "return": "return"}
    layer = [f'            <StateMachineLayer name="{ROOM} Clouds" id="{n()}">', f'{pad}<AnyState x="160" y="200" id="{n()}"/>', f'{pad}<ExitState x="720" y="200" id="{n()}"/>',
             f'{pad}<EntryState x="0" y="0" id="{n()}">', f'{pad}    <StateTransition stateToId="{sid["rest"]}" id="{n()}"/>', f'{pad}</EntryState>']
    for i, k in enumerate(("rest", "in", "shown", "out", "hidden", "return")):
        layer.append(f'{pad}<AnimationState animationId="{aids[anim_of[k]]}" x="{160 + 200 * i}" y="0" id="{sid[k]}">')
        layer += [pad + "    " + l for l in outs[k]]
        layer.append(f"{pad}</AnimationState>")
    layer.append("            </StateMachineLayer>")
    si = max(i for i, l in enumerate(doc.lines) if l.strip() == "</StateMachine>")
    doc.lines[si:si] = layer
    if "--write" in argv:
        doc.save()
        print("written", path)
    else:
        print("dry run")


if __name__ == "__main__":
    main()
