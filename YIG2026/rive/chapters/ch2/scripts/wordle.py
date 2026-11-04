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
from common import INTRO, bake

ROOM = "Wordle"
WR, OM = "1:918", "1:883"
# shadow node: (caster, the property that runs along its edge, the one that goes off the edge)
SHADOWS = {"1:972": (WR, "scaleX", "scaleY"), "1:849": (WR, "scaleX", "scaleY"),
           "1:1056": (OM, "scaleX", "scaleY"), "1:935": (OM, "scaleY", "scaleX")}
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
    doc.rebuild_waiting(ROOM)
    from common import rebuild_built
    rebuild_built(doc, ROOM)
    return f"{ROOM}: shadows cast by the settling blocks: " + "; ".join(notes)
