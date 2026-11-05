"""Wordle: the four shadows are cast by the blocks above them as those blocks settle, instead of scaling up from nothing after
(Demetre's pinned note, 2026-11-04 10:58).

Each shadow is a right triangle whose node sits on its corner, on the edge of the block it falls on:
* Shadow E (on E1's top right) and Shadow B (on B's top left) are cast by Pair WR, the top-left pair, onto the top edge it lands on;
* Shadow K (on K's top left) is cast by Pair OM's M onto K's top edge;
* Shadow R (up R's right side) is cast by Pair OM's O, beside it.
The caster drops, lands still tilted 14 degrees, and tips flat (power2.in). The shadow sweeps along its edge in step with that last tip
(so it closes in as the gap under the block closes), and its depth off the edge follows just behind, easing out 6 frames after the
caster is flat; while the caster squashes on landing the shadow deepens with it a little and settles back as it does. The final
shape is the drawn one (scale 1 on both axes).
"""
import re

from common import INTRO, bake

ROOM = "Wordle"
WR, OM = "1:918", "1:883"
# shadow node: (caster, the property that runs along its edge, the one that goes off the edge)
SHADOWS = {"1:972": (WR, "scaleX", "scaleY"), "1:849": (WR, "scaleX", "scaleY"),
           "1:1056": (OM, "scaleX", "scaleY"), "1:935": (OM, "scaleY", "scaleX")}
BALL = "1:1073"
TOP_RAISE = 4.0             # px the ball rides higher on the top row of blocks
TOP_Y = {"604.10999": "600.10999", "592.10999": "588.10999", "578.10999": "574.10999"}
DEPTH_LAG = 6               # the depth finishes this many frames after the caster is flat
SQUASH_GAIN = 1.5           # how much the shadow deepens per unit of the caster's squash


def ease_out(t):
    t = min(1.0, max(0.0, t))
    return 1 - (1 - t) ** 2


def build(doc, scene, sheet):
    keys = sheet.anim_keys(scene.animations[f"{ROOM} Intro"])
    intro = f"{ROOM} Intro"
    notes = []
    for sid, (caster, along_p, depth_p) in SHADOWS.items():
        c = keys[caster]
        land = int(c["y"].rows[-1][0])                       # the drop ends: the block is down, still tilted
        flat = int(c["rotation"].rows[-1][0])                # it has tipped flat
        r0 = c["rotation"].at(land)
        along = {f: (0.0 if f < land else min(1.0, (r0 - c["rotation"].at(f)) / r0)) for f in range(INTRO)}
        depth = {}
        for f in range(INTRO):
            d = ease_out((f - land) / (flat + DEPTH_LAG - land))
            depth[f] = d * (1 + SQUASH_GAIN * (1 - c["scaleY"].at(f)))
        doc.set_prop(intro, sid, along_p, bake(along, range(INTRO)))
        doc.set_prop(intro, sid, depth_p, bake(depth, range(INTRO)))
        notes.append(f"{sid} from {land / 60:.2f} s, along its edge by {flat / 60:.2f} s, full depth {(flat + DEPTH_LAG) / 60:.2f} s")
    # Demetre's pinned note, 2026-11-04 23:15: the ball sat too low on the top row of blocks. Its contact line there (604.11) is raised
    # by TOP_RAISE; the hops that leave the top row keep their rise above it, the ones that land on it keep their apex.
    n_up = 0
    for anim in (f"{ROOM} Intro", f"{ROOM} Loop"):
        a, b = doc.anim(anim)
        i, j = doc._object(a, b, BALL)
        pat = re.compile(r'^\s*<KeyedProperty\b[^>]*\bproperty="y"')
        k = next(k for k in range(i + 1, j) if pat.match(doc.lines[k]))
        for m in range(k, doc.end(k) + 1):
            for old, new in TOP_Y.items():
                if f'value="{old}"' in doc.lines[m]:
                    doc.lines[m] = doc.lines[m].replace(f'value="{old}"', f'value="{new}"')
                    n_up += 1
    notes.append(f"ball on the top row raised {TOP_RAISE} px (contact 604.11 to {604.10999 - TOP_RAISE:.2f}; {n_up} keys)")
    doc.rebuild_waiting(ROOM)
    from common import rebuild_built
    rebuild_built(doc, ROOM)
    return f"{ROOM}: shadows cast by the settling blocks: " + "; ".join(notes)
