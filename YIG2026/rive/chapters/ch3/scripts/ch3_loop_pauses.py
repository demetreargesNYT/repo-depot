"""Regenerates the whole Chapter 3 loop: refuses chapters/ch3/scene.rml once it has changed since commit c72d210 (tools/regen_guard.py).

Chapter 3's 10.6 s loop (Demetre, 2026-11-05, second round: the dance, the dim and the light spots are gone). Writes it into the scene.

    python3 chapters/ch3/scripts/ch3_loop_pauses.py --scene PATH            # a dry run: PATH is rewritten only with --write
    python3 chapters/ch3/scripts/ch3_loop_pauses.py --scene PATH --write

Run it on the scene as it was after the pin 1 and pin 2 fixes (commit before the first dance). It:
- adds a second set of clock digits, 12:00, in the drawn digits' line weight (the old "201" stays, so the first 3.2 s are unchanged);
- moves the mirror ball's keys, byte for byte, from "Chapter 3 Loop" into "Chapter 3 Disco Loop" (416 frames, loop) on a new layer "Chapter 3 Disco"
  that starts when the Loop used to (ch3_disco.py reads the new name as the old one);
- makes "Chapter 3 Loop" the ball's 636 frame loop (ch3_loop_tracks.py): the old journey with a pause-roll on the floor and one on the calendar,
  the clock's 12:00 flicker and wobble on touch, the calendar's colour wave on each landing, the bird bouncing after the ball is in the box;
- holds every new property at its rest value in the Intro, Waiting and Built poses (the room's checks want that; it changes no pixel);
- lengthens "Chapter 3 Small Loop" to 636 so the two stay in step.
There is no separate first-visit timeline: the main layer is Intro -> Loop as before. Run once; it asserts on a second run.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rml_edit import Doc  # noqa: E402
import regen_guard  # noqa: E402
WRITTEN_AGAINST = "c72d210"     # the scene after the pin 1 and pin 2 fixes, before the first dance (see above)
from rml_read import chapter_dir  # noqa: E402
import ch3_loop_tracks as T  # noqa: E402

VM = "1:14"
SCENE_P, DIR_P, START_P = "1:2713", "1:2855", "1:3400"
CH3, CH3_2, BACK = "1:9101", "1:9104", "1:9201"
FLOOR_CLIP = "9:3108"
INK = "FF1F1F1F"


def scene_path(argv):
    return Path(argv[argv.index("--scene") + 1]) if "--scene" in argv else chapter_dir("ch3") / "scene.rml"


# ---- art -----------------------------------------------------------------------------------------------------------------------
def shape_xml(n, sid, name, x, y, prim, fill, stroke=INK, clip=FLOOR_CLIP, opacity=None, thickness="1.5"):
    op = f' opacity="{opacity}"' if opacity is not None else ""
    xs = f' x="{x}"' if x else ""
    ys = f' y="{y}"' if y else ""
    nm = f' name="{name}"' if name else ""
    out = [f'<Shape{xs}{ys}{nm}{op} id="{sid}">', f"    {prim.replace('ID', n())}"]
    if fill:
        out += [f'    <Fill id="{n()}">', f'        <SolidColor colorValue="{fill}" id="{n()}"/>', "    </Fill>"]
    out += [f'    <Stroke thickness="{thickness}" cap="round" join="round" id="{n()}">', f'        <SolidColor colorValue="{stroke}" id="{n()}"/>', "    </Stroke>"]
    if clip:
        out.append(f'    <ClippingShape sourceId="{clip}" name="Floor Clip" id="{n()}"/>')
    out.append("</Shape>")
    return out


def digits_b(n):
    """12:00 in the clock's own digits: the old drawn 1 and 2 and 0, a second 0, and a colon of two dots. Stroke 1.5, round."""
    one = '<PointsPath id="ID"><StraightVertex x="-1.25" y="-5" id="ID"/><StraightVertex x="1.25" y="-5" id="ID"/><StraightVertex x="1.25" y="5" id="ID"/></PointsPath>'
    two = ('<PointsPath id="ID"><CubicDetachedVertex outRotation="-1.5707964" outDistance="1.381" x="-2.5" y="-2.5" id="ID"/>'
           '<CubicDetachedVertex inRotation="3.1415927" inDistance="1.381" outDistance="1.381" y="-5" id="ID"/>'
           '<CubicDetachedVertex inRotation="-1.5707964" inDistance="1.381" outRotation="1.5707964" outDistance="1.601" x="2.5" y="-2.5" id="ID"/>'
           '<CubicDetachedVertex inRotation="-0.78539819" inDistance="1.6008898" x="0.73199999" y="1.768" id="ID"/>'
           '<StraightVertex x="-2.5" y="5" id="ID"/><StraightVertex x="2.5" y="5" id="ID"/></PointsPath>')
    zero = '<Rectangle cornerRadiusTL="2.5" width="5" height="10" id="ID"/>'
    dot = '<Ellipse width="0.8" height="0.8" id="ID"/>'
    # a PointsPath written on one line has several ids: every ID is replaced in turn
    def prim(p):
        return re.sub(r"ID", lambda m: n(), p)
    gid = n()
    out = [f'<Node x="-0.30199999" y="-0.30199999" name="Clock Digits 12:00" opacity="0" id="{gid}">']
    for name, x, y, p, fill in (("1", -12, 0, one, None), ("2", -5.5, 0, two, None), ("0", 6, 0, zero, None), ("0", 13, 0, zero, None),
                                ("colon top", 0.5, -2.5, dot, INK), ("colon bottom", 0.5, 2.5, dot, INK)):
        ytxt = f' y="{y}"' if y else ""
        sx = [f'<Shape x="{x}"{ytxt} name="Digit {name}" id="{n()}">', f"    {prim(p)}"]
        if fill:
            sx += [f'    <Fill id="{n()}">', f'        <SolidColor colorValue="{fill}" id="{n()}"/>', "    </Fill>"]
        sx += [f'    <Stroke thickness="1.5" cap="round" join="round" id="{n()}">', f'        <SolidColor colorValue="{INK}" id="{n()}"/>', "    </Stroke>",
               f'    <ClippingShape sourceId="{FLOOR_CLIP}" name="Floor Clip" id="{n()}"/>', "</Shape>"]
        out += ["    " + l for l in sx]
    out.append("</Node>")
    return gid, out


# ---- tracks -------------------------------------------------------------------------------------------------------------------
def color_lines(doc, keys):
    out = []
    for f, c in keys:
        fr = f' frame="{f}"' if f else ""
        out.append(f'                    <KeyFrameColor value="{c}" interpolationType="linear"{fr} id="{doc.new_id()}"/>')
    return out


def put(doc, anim, oid, prop, kind, keys, holds):
    if kind == "color":
        a, b = doc.anim(anim)
        found = doc._object(a, b, oid)
        if found is None:
            doc.lines[b:b] = [f'            <KeyedObject objectId="{oid}" id="{doc.new_id()}">', "            </KeyedObject>"]
            found = (b, b + 1)
        i, j = found
        block = [f'                <KeyedProperty property="{prop}" id="{doc.new_id()}">'] + color_lines(doc, keys) + ["                </KeyedProperty>"]
        doc.lines[j:j] = block
        return
    if kind == "linear":
        ks = [(f, v, "hold" if f in holds else "linear") for f, v in keys]
    elif kind == "hold":
        ks = [(f, v, "hold") for f, v in keys]
    else:
        ks = list(keys)
    doc.set_prop(anim, oid, prop, ks)


# ---- state machine --------------------------------------------------------------------------------------------------------------
def cond(n, prop, value, op="equal"):
    return [f'<TransitionViewModelCondition opValue="{op}" id="{n()}">', f'    <TransitionPropertyViewModelComparator id="{n()}">',
            f'        <BindablePropertyEnum id="{n()}">', f'            <DataBindContext sourcePathIds="{VM}-{prop}" propertyKey="637" id="{n()}"/>',
            '        </BindablePropertyEnum>', '    </TransitionPropertyViewModelComparator>', f'    <TransitionValueEnumComparator value="{value}" id="{n()}"/>',
            '</TransitionViewModelCondition>']


def layer_xml(doc, name, states, plan):
    """states: ordered [(key, animation id)]; plan: {key: [transition lines builder]} given the state ids."""
    n = doc.new_id
    sid = {k: n() for k, _ in states}
    pad = " " * 16

    def tr(to, conds=(), exit_time=False, ms=0):
        attrs = f' stateToId="{sid[to]}" duration="{ms}"'
        if exit_time:
            attrs += ' enableExitTime="true" exitTimeIsPercetange="true" exitTime="100"'
        if not conds:
            return [f'<StateTransition{attrs} id="{n()}"/>']
        body = [l for c in conds for l in c]
        return [f'<StateTransition{attrs} id="{n()}">'] + ["    " + l for l in body] + ["</StateTransition>"]

    c = lambda prop, val, op="equal": cond(n, prop, val, op)
    out = [f'            <StateMachineLayer name="{name}" id="{n()}">', f'{pad}<AnyState x="160" y="200" id="{n()}"/>', f'{pad}<ExitState x="720" y="200" id="{n()}"/>',
           f'{pad}<EntryState x="0" y="0" id="{n()}">', f'{pad}    <StateTransition stateToId="{sid[states[0][0]]}" id="{n()}"/>', f'{pad}</EntryState>']
    for i, (k, aid) in enumerate(states):
        out.append(f'{pad}<AnimationState animationId="{aid}" x="{160 + 200 * i}" y="0" id="{sid[k]}">')
        out += [pad + "    " + l for l in plan(k, tr, c)]
        out.append(f"{pad}</AnimationState>")
    out.append("            </StateMachineLayer>")
    return out


def idle_out(tr, c, built_to, first_to):
    """The same arrival rules as the room's own Waiting state: a startScene or a Back arrives already built; otherwise it is a first visit."""
    t = []
    for sc in (CH3, CH3_2):
        t += tr(built_to, (c(SCENE_P, sc), c(START_P, sc)))
    for sc in (CH3, CH3_2):
        t += tr(built_to, (c(SCENE_P, sc), c(DIR_P, BACK)))
    for sc in (CH3, CH3_2):
        t += tr(first_to, (c(SCENE_P, sc),))
    return t


def main():
    argv = sys.argv
    path = scene_path(argv)
    doc = Doc(path)
    assert not any('name="Chapter 3 Disco Loop"' in l for l in doc.lines), "already applied"
    tracks = T.build(path)
    meta = tracks["meta"]
    n = doc.new_id
    # the 12:00 digits go in front of the old digits inside the clock's face
    a_i = doc.idx(T.DIGITS_A)
    gid, lines = digits_b(n)
    doc.lines[a_i:a_i] = ["                        " + l for l in lines]
    ids = {"DIGITS_B": gid}
    # note 2: one of the disco ball's sparkles (a copy of "Chapter 3 Sparkle 3", same star, same outline) on the ring, first child so it draws on top
    si_ = doc.idx("9:33769")
    spark = doc.lines[si_:doc.end(si_) + 1]
    remap = {}
    def new_id(m):
        remap.setdefault(m.group(1), n())
        return f'id="{remap[m.group(1)]}"'
    spark = [re.sub(r'\bid="([^"]+)"', new_id, l) for l in spark]
    spark = [re.sub(r'sourceId="[^"]+"', f'sourceId="{FLOOR_CLIP}"', l) for l in spark]
    spark[0] = '<Shape x="27" y="14" rotation="0.7" name="Ring Sparkle" opacity="0" ' + 'id="' + remap["9:33769"] + '">'
    spark[1] = spark[1].replace('<PointsPath isClosed="true"', '<PointsPath name="Ring Sparkle Star" isClosed="true"')
    ids["RING_SPARKLE"] = remap["9:33769"]
    ids["RING_STAR"] = remap["9:33770"]
    ring_i = doc.idx("9:1385")
    doc.lines[ring_i + 1:ring_i + 1] = ["                        " + l.strip() if k in (0, len(spark) - 1) else "                            " + l.strip() for k, l in enumerate(spark)]
    # name the calendar cells' colours so each reads as its own property in the checks
    cells = {}
    for r, row in enumerate(T.CELL_ROWS):
        for c_, sid in enumerate(row):
            col = T.cid(sid)
            i = doc.idx(col)
            doc.lines[i] = doc.lines[i].replace(f' id="{col}"', f' name="Calendar cell {r + 1}.{c_ + 1} colour" id="{col}"', 1)
            cells[col] = T.CELL_BASE[r]

    # 1. the mirror ball's keys move, untouched, out of "Chapter 3 Loop" into "Chapter 3 Disco Loop"; "Chapter 3 Loop" becomes the ball's loop
    for oid in T.KEEP:
        doc.drop_object("Chapter 3 Loop", oid)
    a, b = doc.anim("Chapter 3 Loop")
    disco_body = doc.lines[a + 1:b]
    del doc.lines[a + 1:b]
    doc.set_duration("Chapter 3 Loop", meta["loop_frames"])
    out_i = doc.anim("Chapter 3 Outro")[0]
    shells = [("DiscoIdle", "Chapter 3 Disco Idle", 1, "oneShot"), ("DiscoWait", "Chapter 3 Disco Wait", 192, "oneShot"), ("Disco", "Chapter 3 Disco Loop", 416, "loop")]
    aid, lines = {}, []
    for key, name, dur, lv in shells:
        aid[key] = n()
        lines += [f'        <LinearAnimation fps="60" duration="{dur}" loopValue="{lv}" name="{name}" id="{aid[key]}">'] + (disco_body if key == "Disco" else []) + ["        </LinearAnimation>"]
    doc.lines[out_i:out_i] = lines
    for (o, prop), (kind, keys, holds) in tracks["loop"].items():
        put(doc, "Chapter 3 Loop", ids.get(o, o), prop, kind, keys, holds)

    # 2. every property the Loop keys is also held at rest in the Intro, Waiting and Built (checks want it; no pixel changes)
    rest = [(T.FACE, "scaleX", 1.0), (T.FACE, "scaleY", 1.0), (T.FACE, "rotation", 0.0), (T.DIGITS_A, "opacity", 1.0), (ids["DIGITS_B"], "opacity", 0.0),
            (T.BIRD, "y", 541.5), (T.BIRD_LEG2, "y", 541.5),
            (ids["RING_SPARKLE"], "opacity", 0.0), (ids["RING_STAR"], "scaleX", 0.0), (ids["RING_STAR"], "scaleY", 0.0)]
    for anim, ks in (("Chapter 3 Intro", lambda v: [(0, v, "hold"), (191, v, "hold")]), ("Chapter 3 Waiting", lambda v: [(0, v, "hold")]), ("Chapter 3 Built", lambda v: [(0, v, "hold")])):
        for o, prop, v in rest:
            doc.set_prop(anim, o, prop, ks(v))
        for col, base in cells.items():
            put(doc, anim, col, "colorValue", "color", [(0, base)] if anim != "Chapter 3 Intro" else [(0, base), (191, base)], set())
    doc.set_duration("Chapter 3 Small Loop", meta["loop_frames"])       # the bird's eye cycle keeps its length and rests on its first pose until the Loop ends

    # 3. the mirror ball's layer: starts when the Loop used to
    def disco_plan(k, tr, c):
        if k == "DiscoIdle":
            return idle_out(tr, c, "Disco", "DiscoWait")
        if k == "DiscoWait":
            return tr("Disco", exit_time=True)
        return []

    lay = layer_xml(doc, "Chapter 3 Disco", [("DiscoIdle", aid["DiscoIdle"]), ("DiscoWait", aid["DiscoWait"]), ("Disco", aid["Disco"])], disco_plan)
    si = max(i for i, l in enumerate(doc.lines) if l.strip() == "</StateMachine>")
    doc.lines[si:si] = lay
    print(meta)
    if "--write" in argv:
        regen_guard.save(doc, WRITTEN_AGAINST, __file__)
        print("written", path)


if __name__ == "__main__":
    main()
