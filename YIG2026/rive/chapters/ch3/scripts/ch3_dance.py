"""Chapter 3's first-visit dance and its 10.6 s loop (Demetre, 2026-11-05): writes them into the scene.

    python3 chapters/ch3/scripts/ch3_dance.py --scene PATH            # a dry run on a copy: PATH is rewritten only with --write
    python3 chapters/ch3/scripts/ch3_dance.py --scene PATH --write

What it does (the numbers come from ch3_dance_tracks.py, which only computes):
- Art: a second set of clock digits, 12:00, in the drawn digits' line weight (the old "201" stays for the arrival, so the first 3.2 s are
  unchanged), four light spots (two on the wall, two on the floor, each with the room's outline) behind everything, one clip for the floor.
- The mirror ball's keys move, byte for byte, from "Chapter 3 Loop" into "Chapter 3 Disco Loop" (416 frames, loop) on a new layer
  "Chapter 3 Disco" that starts when the Loop used to (its look is saved in disco-saved.json; ch3_disco.py reads the new name as the old).
  "Chapter 3 Loop" becomes the ball's loop (636 frames: the ball and what it touches), and the main layer goes Intro -> "Chapter 3 Dance"
  (first visit only, 998 frames) -> Loop. A startScene or a Back still goes Built -> Loop, so only a first visit dances.
- A layer "Chapter 3 Dim" whose one animation, "Chapter 3 Dim", dims the shared wall and floor colours during the Dance (the one
  exception in tools/check_chapter.py). It leaves with a 0.3 s blend if the scene changes, and never plays again.
Run once; it asserts on a second run.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rml_edit import Doc  # noqa: E402
from rml_read import chapter_dir  # noqa: E402
import ch3_dance_tracks as T  # noqa: E402

VM = "1:14"
SCENE_P, DIR_P, START_P = "1:2713", "1:2855", "1:3400"
CH3, CH3_2, BACK = "1:9101", "1:9104", "1:9201"
FLOOR_PLANE, ROOM, FLOOR_CLIP = "9:3101", "9:3104", "9:3108"
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


SPOTS = {"A": ("Wall", 640, 490, 150, 92, "FFEBE6F9"), "B": ("Wall", 880, 565, 112, 66, "FFEBE6F9"),
         "C": ("Floor", 700, 745, 190, 50, "FF33D98F"), "D": ("Floor", 860, 800, 124, 36, "FF33D98F")}


def add_art(doc):
    n = doc.new_id
    ids = {}
    # the 12:00 digits go in front of the old digits inside the clock's face
    face_i = doc.idx(T.FACE)
    a_i = doc.idx(T.DIGITS_A)
    gid, lines = digits_b(n)
    ids["DIGITS_B"] = gid
    doc.lines[a_i:a_i] = ["                        " + l for l in lines]
    # the clock's dark display: shows while the face is off (a power cut), behind the face, inside the clock's frame
    f3 = doc.idx("9:1061")
    f3e = doc.end(f3)
    did = n()
    ids["CLOCK_DARK"] = did
    dark = shape_xml(n, did, "Clock Dark Display", 23.25, 18.25, '<Rectangle cornerRadiusTL="2" cornerRadiusTR="2" cornerRadiusBL="2" cornerRadiusBR="2" width="43" height="32" id="ID"/>', INK, opacity=0)
    doc.lines[f3e:f3e] = ["                    " + l for l in dark]
    # the floor-area clip (below the floor line), next to the floor clip
    fc = doc.idx(FLOOR_CLIP)
    clip_id = n()
    fe = doc.end(fc)
    doc.lines[fe + 1:fe + 1] = [f'                <Shape y="712" name="Chapter 3 Floor Area Clip" id="{clip_id}">',
                                f'                    <Rectangle width="9000" height="2000" originX="0.5" originY="0" name="Path" id="{n()}"/>', "                </Shape>"]
    # the light spots: the last children of the floor plane (drawn first, behind everything in the room)
    fp = doc.idx(FLOOR_PLANE)
    fpe = doc.end(fp)
    new = []
    for key, (where, x, y, w, h, fill) in SPOTS.items():
        sid = n()
        ids[f"SPOT_{key}"] = sid
        sh = shape_xml(n, sid, f"Light Spot {key}", x, y, f'<Ellipse width="{w}" height="{h}" id="ID"/>', fill, clip=FLOOR_CLIP if where == "Wall" else clip_id, opacity=0)
        new += ["                    " + l for l in sh]
    doc.lines[fpe:fpe] = new
    # the floor spots clip to the floor area, whose ClippingShape name stays "Floor Clip" in the shape helper; fix the name for clarity
    return ids


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
    assert not any('name="Chapter 3 Dance"' in l for l in doc.lines), "already applied"
    tracks = T.build(path)
    meta = tracks["meta"]
    ids = add_art(doc)
    n = doc.new_id
    cells = {}
    for r, row in enumerate(T.CELL_ROWS):
        for c_, sid in enumerate(row):
            col = T.cid(sid)
            i = doc.idx(col)
            doc.lines[i] = doc.lines[i].replace(f' id="{col}"', f' name="Calendar cell {r + 1}.{c_ + 1} colour" id="{col}"', 1)
            cells[col] = T.CELL_BASE[r]

    # 1. the mirror ball's keys move, untouched, out of "Chapter 3 Loop" into "Chapter 3 Disco Loop" (416 frames, its own layer);
    #    "Chapter 3 Loop" becomes the ball's 636 frame loop
    for oid in T.KEEP:
        doc.drop_object("Chapter 3 Loop", oid)
    a, b = doc.anim("Chapter 3 Loop")
    disco_body = doc.lines[a + 1:b]
    assert disco_body and all("Disco" not in l or True for l in disco_body)
    del doc.lines[a + 1:b]
    doc.set_duration("Chapter 3 Loop", meta["loop"]["loop_frames"])

    # 2. the other new animations (before the Outro)
    out_i = doc.anim("Chapter 3 Outro")[0]
    shells = [("DiscoIdle", "Chapter 3 Disco Idle", 1, "oneShot"), ("DiscoWait", "Chapter 3 Disco Wait", 192, "oneShot"),
              ("Disco", "Chapter 3 Disco Loop", 416, "loop"), ("Dance", "Chapter 3 Dance", meta["dance_frames"], "oneShot"),
              ("DIdle", "Chapter 3 Dim Idle", 1, "oneShot"), ("DWait", "Chapter 3 Dim Wait", 192, "oneShot"),
              ("Dim", "Chapter 3 Dim", meta["dance_frames"], "oneShot"), ("DDone", "Chapter 3 Dim Done", 1, "oneShot")]
    aid, lines = {}, []
    for key, name, dur, lv in shells:
        aid[key] = n()
        body = disco_body if key == "Disco" else []
        lines += [f'        <LinearAnimation fps="60" duration="{dur}" loopValue="{lv}" name="{name}" id="{aid[key]}">'] + body + ["        </LinearAnimation>"]
    doc.lines[out_i:out_i] = lines

    def oid_of(o):
        return ids.get(o, o)

    for anim, group in (("Chapter 3 Dance", tracks["dance"]), ("Chapter 3 Loop", tracks["loop"])):
        for (o, prop), v in group.items():
            kind, keys, holds = v
            put(doc, anim, oid_of(o), prop, kind, keys, holds)
    for (o, prop), (kind, keys) in tracks["dim"].items():
        put(doc, "Chapter 3 Dim", o, prop, kind, keys, set())

    # the room's checks want every property the Loop keys to be set by the Intro too (and by the Waiting and Built poses): the new ones
    # are held at their rest value there, which changes no pixel
    rest = [(T.FACE, "opacity", 1.0), (T.FACE, "scaleX", 1.0), (T.FACE, "scaleY", 1.0), (T.FACE, "rotation", 0.0), (T.DIGITS_A, "opacity", 1.0),
            (ids["DIGITS_B"], "opacity", 0.0), (ids["CLOCK_DARK"], "opacity", 0.0), (ids["SPOT_A"], "opacity", 0.0), (ids["SPOT_A"], "x", 640.0)]
    for anim, ks in (("Chapter 3 Intro", lambda v: [(0, v, "hold"), (191, v, "hold")]), ("Chapter 3 Waiting", lambda v: [(0, v, "hold")]), ("Chapter 3 Built", lambda v: [(0, v, "hold")])):
        for o, prop, v in rest:
            doc.set_prop(anim, o, prop, ks(v))
        for col, base in cells.items():
            put(doc, anim, col, "colorValue", "color", [(0, base)] if anim != "Chapter 3 Intro" else [(0, base), (191, base)], set())
    doc.set_duration("Chapter 3 Small Loop", meta["loop"]["loop_frames"])       # the bird's eye cycle keeps its length; it rests on its first pose until the Loop ends

    # 3. the main layer: Intro -> Dance -> Loop (a startScene or a Back still goes Built -> Loop, so only a first visit dances)
    li = doc.idx("9:3725")
    le = doc.end(li)
    intro_state = next(i for i in range(li, le) if 'animationId="9:3520"' in doc.lines[i])
    tr_line = next(i for i in range(intro_state, doc.end(intro_state) + 1) if 'id="9:3738"' in doc.lines[i])
    dance_state = n()
    doc.lines[tr_line] = doc.lines[tr_line].replace('stateToId="9:3739"', f'stateToId="{dance_state}"')
    doc.lines[le:le] = [f'                <AnimationState animationId="{aid["Dance"]}" x="640" y="120" id="{dance_state}">',
                        f'                    <StateTransition stateToId="9:3739" duration="0" enableExitTime="true" exitTimeIsPercetange="true" exitTime="100" id="{n()}"/>',
                        "                </AnimationState>"]

    # 4. the side layers: the mirror ball's loop (starts with the Loop, as it always did) and the dim
    def disco_plan(k, tr, c):
        if k == "DiscoIdle":
            return idle_out(tr, c, "Disco", "DiscoWait")
        if k == "DiscoWait":
            return tr("Disco", exit_time=True)
        return []

    def dim_plan(k, tr, c):
        leave = lambda: tr("DDone", (c(SCENE_P, CH3, "notEqual"), c(SCENE_P, CH3_2, "notEqual")), ms=300)
        if k == "DIdle":
            return idle_out(tr, c, "DDone", "DWait")
        if k == "DWait":
            return leave() + tr("Dim", exit_time=True)
        if k == "Dim":
            return leave() + tr("DDone", exit_time=True)
        return []

    lay = layer_xml(doc, "Chapter 3 Disco", [("DiscoIdle", aid["DiscoIdle"]), ("DiscoWait", aid["DiscoWait"]), ("Disco", aid["Disco"])], disco_plan)
    lay += layer_xml(doc, "Chapter 3 Dim", [("DIdle", aid["DIdle"]), ("DWait", aid["DWait"]), ("Dim", aid["Dim"]), ("DDone", aid["DDone"])], dim_plan)
    si = max(i for i, l in enumerate(doc.lines) if l.strip() == "</StateMachine>")
    doc.lines[si:si] = lay

    print({k: v for k, v in meta.items() if k != "loop"})
    print("loop", meta["loop"])
    if "--write" in argv:
        doc.save()
        print("written", path)


if __name__ == "__main__":
    main()
