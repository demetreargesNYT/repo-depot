"""Chapter 4 finesse note 2, piece 1 (Demetre, 2026-11-06): the ball leaves during the editor video, once, and comes back on Back.

    python3 chapters/ch3/scripts/ch3_c4_ball_exit.py --scene PATH [--write]       once; it asserts on a second run

Built as the room's own reaction to its own scene, like the fireworks (no transition keys the outgoing ball), in the "Chapter 4 Ball Motion"
layer:
- Idle <game> -> Exit (200 ms blend) when scene turns chapter-4-editor-video. Exit (90 frames, one shot): the dot glances right (10 frames),
  a 10 percent gather (14 to 24), a launch at frame 26 with a 3 percent stretch, one bounce at x 1212 with a 12 percent landing squash
  (frame 57, keeping 85 percent of the speed), and out of the right edge in the second flight. Gravity 0.40 on both flights. Then -> Away
  (the ball waits off stage, as it does before a visit) for the whole card.
- Away no longer starts any ball on chapter-4-editor-video (a startScene, a Back from End or a jump shows no ball).
- Back to chapter-4-top-game (reveal true): Away -> Return (100 frames, one shot): it rolls in from the right edge decelerating (at most 23 a
  frame), stops 5.5 units past its spot, rolls back and settles on x 747; then -> the game's idle, as Celebrate does.
The ball is not keyed by any transition; no scene, setting or enum changes.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rml_edit import Doc  # noqa: E402
from rml_read import Scene, chapter_dir  # noqa: E402
import ch3_c4_city as city  # noqa: E402
from ch3_c4_city_lives import key_lines  # noqa: E402

BALL, SPIN, ART = "9:43975", "9:43978", "9:43976"        # the ball node, its spin node and Ball_01 (the scale)
EDITOR, TOPGAME, BACK_DIR = "1:9108", "1:9107", "1:9201"
Y0, X_HOME, ROT_HOME, SCALE = 696.5576, 747.0, -0.26, 1.2
R = 17.678 * SCALE                                          # the ball's radius at this size
G = 0.40
EXIT_LEN, RETURN_LEN = 90, 100


def hermite_points(points):
    """Keys through [(frame, value, slope)] as cubic Hermite segments (a cubic ease whose handles carry the slopes)."""
    keys = []
    for i, (f, v, m) in enumerate(points):
        if i == len(points) - 1:
            keys.append((f, v, "hold"))
            break
        f2, v2, m2 = points[i + 1]
        dt, dv = f2 - f, v2 - v
        if abs(dv) < 1e-9:
            keys.append((f, v, "hold"))
        else:
            keys.append((f, v, (1 / 3, m * dt / 3 / dv, 2 / 3, 1 - m2 * dt / 3 / dv)))
    return keys


def exit_tracks():
    v1, vx1 = 6.2, 15.0                       # launch: up speed and sideways speed (units a frame)
    land = 26 + int(2 * v1 / G)               # 57
    v2, vx2 = 5.2, vx1 * 0.85                 # the bounce keeps 85 percent of the speed
    t2 = land + 2
    end = t2 + int(2 * v2 / G)                # 85
    assert land == 57 and end == 85
    xs = [(0, X_HOME, "hold"), (26, X_HOME, "linear"), (land, X_HOME + vx1 * (land - 26), "linear"), (end, X_HOME + vx1 * (land - 26) + vx2 * (end - land), "hold"),
          (EXIT_LEN, X_HOME + vx1 * (land - 26) + vx2 * (end - land), "hold")]
    ys = [(0, Y0, "hold")]
    ys += hermite_points([(26, Y0, -v1), (26 + 15, Y0 - (v1 * 15 - 0.2 * 225), -v1 + 0.4 * 15), (land, Y0, v1)])[:-1]
    ys += [(land, Y0, "hold")]
    ys += hermite_points([(t2, Y0, -v2), (t2 + 13, Y0 - (v2 * 13 - 0.2 * 169), 0.0), (end, Y0, v2)])[:-1]
    ys += [(end, Y0, "hold"), (EXIT_LEN, Y0, "hold")]
    rot = [(0, ROT_HOME, "power2.inOut"), (10, 0.24, "hold"), (26, 0.24, "linear"), (land, 0.50, "linear"), (end, 0.80, "hold"), (EXIT_LEN, 0.80, "hold")]
    sx = [(0, SCALE, "hold"), (14, SCALE, "power2.inOut"), (24, SCALE * 1.10, "hold"), (26, SCALE * 1.10, "power2.out"), (30, SCALE / 1.03, "linear"),
          (54, SCALE / 1.03, "power2.inOut"), (land, SCALE * 1.12, "power2.out"), (land + 4, SCALE / 1.03, "hold"), (EXIT_LEN, SCALE / 1.03, "hold")]
    sy = [(0, SCALE, "hold"), (14, SCALE, "power2.inOut"), (24, SCALE * 0.90, "hold"), (26, SCALE * 0.90, "power2.out"), (30, SCALE * 1.03, "linear"),
          (54, SCALE * 1.03, "power2.inOut"), (land, SCALE * 0.88, "power2.out"), (land + 4, SCALE * 1.03, "hold"), (EXIT_LEN, SCALE * 1.03, "hold")]
    return {(BALL, "x"): xs, (BALL, "y"): ys, (SPIN, "rotation"): rot, (ART, "scaleX"): sx, (ART, "scaleY"): sy}


def return_tracks():
    x_start, x_over, T = 1560.0, X_HOME - 5.5, 72
    v0 = 2 * (x_start - x_over) / T                          # decelerating evenly to rest at x_over
    rot_at = lambda x: ROT_HOME + (x - X_HOME) / R           # rolling left turns it anticlockwise
    xs = hermite_points([(0, x_start, -v0), (T, x_over, 0.0)])[:-1] + [(T, x_over, "sine.inOut"), (RETURN_LEN, X_HOME, "hold")]
    rot = hermite_points([(0, rot_at(x_start), -v0 / R), (T, rot_at(x_over), 0.0)])[:-1] + [(T, rot_at(x_over), "sine.inOut"), (RETURN_LEN, ROT_HOME, "hold")]
    ys = [(0, Y0, "hold"), (RETURN_LEN, Y0, "hold")]
    s = [(0, SCALE, "hold"), (RETURN_LEN, SCALE, "hold")]
    return {(BALL, "x"): xs, (BALL, "y"): ys, (SPIN, "rotation"): rot, (ART, "scaleX"): s, (ART, "scaleY"): s}


def animation(doc, name, length, tracks):
    aid = doc.new_id()
    lines = [f'        <LinearAnimation fps="60" duration="{length}" loopValue="oneShot" name="{name}" id="{aid}">']
    by_obj = {}
    for (oid, prop), keys in tracks.items():
        by_obj.setdefault(oid, []).append((prop, keys))
    for oid, props in by_obj.items():
        lines.append(f'            <KeyedObject objectId="{oid}" id="{doc.new_id()}">')
        for prop, keys in props:
            lines.append(f'                <KeyedProperty property="{prop}" id="{doc.new_id()}">')
            lines += key_lines(doc, keys, " " * 20)
            lines.append("                </KeyedProperty>")
        lines.append("            </KeyedObject>")
    lines.append("        </LinearAnimation>")
    return aid, lines


def states_of(doc, a, b):
    """[(first line, last line, animation id, state id)] of the AnimationStates of the layer on lines a..b."""
    out = []
    i = a + 1
    while i < b:
        m = re.match(r'^ {16}<AnimationState animationId="([^"]+)"[^>]*\bid="([^"]+)"', doc.lines[i])
        if m:
            out.append((i, doc.end(i), m.group(1), m.group(2)))
            i = doc.end(i)
        i += 1
    return out


def transitions_of(doc, i, j):
    """[(first, last)] of the StateTransitions inside the state on lines i..j (indent 20)."""
    out = []
    k = i + 1
    while k < j:
        if re.match(r"^ {20}<StateTransition\b", doc.lines[k]):
            e = doc.end(k)
            out.append((k, e))
            k = e
        k += 1
    return out


def main():
    argv = sys.argv
    path = Path(argv[argv.index("--scene") + 1]) if "--scene" in argv else chapter_dir("ch3") / "scene.rml"
    doc = Doc(path)
    assert not any('name="Chapter 4 Ball Exit"' in l for l in doc.lines), "already applied"
    sc = Scene(path)
    anim_id = {n: a.get("id") for n, a in sc.animations.items()}
    n = doc.new_id

    exit_id, exit_lines = animation(doc, "Chapter 4 Ball Exit", EXIT_LEN, exit_tracks())
    ret_id, ret_lines = animation(doc, "Chapter 4 Ball Return", RETURN_LEN, return_tracks())
    li = doc.idx(anim_id["Chapter 4 Loop"])
    doc.lines[li:li] = exit_lines + ret_lines

    # 1. Away (the layer has two Away states): nothing starts a ball on the editor video; Back onto the top-game card plays Return
    la = next(i for i, l in enumerate(doc.lines) if '<StateMachineLayer name="Chapter 4 Ball Motion"' in l)
    lb = doc.end(la)
    sts = {aid: (i, j, sid) for i, j, aid, sid in states_of(doc, la, lb)}
    exit_sid, ret_sid = n(), n()
    removed = redirected = 0
    aways = sorted([x for x in states_of(doc, la, lb) if x[2] == anim_id["Chapter 4 Ball Away"]], key=lambda x: -x[0])      # bottom up
    assert len(aways) == 2, aways
    for away_i, away_j, _, _ in aways:
        for first, last in reversed(transitions_of(doc, away_i, away_j)):
            block = "\n".join(doc.lines[first:last + 1])
            if f'value="{EDITOR}"' in block:
                del doc.lines[first:last + 1]
                removed += 1
            elif f'value="{TOPGAME}"' in block and f'value="{BACK_DIR}"' in block and 'TransitionValueBooleanComparator value="true"' in block:
                doc.lines[first] = re.sub(r'stateToId="[^"]+"', f'stateToId="{ret_sid}"', doc.lines[first])
                redirected += 1
    assert removed and redirected, (removed, redirected)

    # 2. every game idle leaves through Exit when the scene turns to the editor video (first, so it wins)
    la = next(i for i, l in enumerate(doc.lines) if '<StateMachineLayer name="Chapter 4 Ball Motion"' in l)
    lb = doc.end(la)
    sts = {aid: (i, j, sid) for i, j, aid, sid in states_of(doc, la, lb)}
    idles = [nm for nm in anim_id if nm.startswith("Chapter 4 Ball Idle ") and nm != "Chapter 4 Ball Idle 1"]
    assert len(idles) == 5, idles
    for nm in sorted(idles, key=lambda nm: -sts[anim_id[nm]][0]):                   # bottom up, so the line numbers stay right
        i, j, sid = sts[anim_id[nm]]
        blk = [f'                    <StateTransition stateToId="{exit_sid}" duration="200" id="{n()}">']
        blk += ["                        " + l for l in city._cond_enum(n, city.SCENE_P, EDITOR)]
        blk += ["                    </StateTransition>"]
        doc.lines[i + 1:i + 1] = blk

    # 3. the two new states, at the end of the layer
    la = next(i for i, l in enumerate(doc.lines) if '<StateMachineLayer name="Chapter 4 Ball Motion"' in l)
    lb = doc.end(la)
    sts = {aid: (i, j, sid) for i, j, aid, sid in states_of(doc, la, lb)}
    away_sid = sts[anim_id["Chapter 4 Ball Away"]][2]      # either Away state will do for the way back
    ci, cj, _ = sts[anim_id["Chapter 4 Ball Celebrate"]]
    celeb_trs = [re.sub(r'\bid="[^"]+"', lambda m: f'id="{n()}"', l) for l in doc.lines[ci + 1:cj]]
    pad = " " * 16
    new = [f'{pad}<AnimationState animationId="{exit_id}" x="1000" y="400" id="{exit_sid}">',
           f'{pad}    <StateTransition stateToId="{away_sid}" duration="0" enableExitTime="true" exitTimeIsPercetange="true" exitTime="100" id="{n()}"/>',
           f"{pad}</AnimationState>",
           f'{pad}<AnimationState animationId="{ret_id}" x="1000" y="600" id="{ret_sid}">'] + celeb_trs + [f"{pad}</AnimationState>"]
    doc.lines[lb:lb] = new
    print(f"Away: {removed} editor-video starts removed, {redirected} top-game Back starts now play Return; Exit from 5 idles")
    if "--write" in argv:
        doc.save()
        print("written", path)
    else:
        print("dry run")


if __name__ == "__main__":
    main()
