"""Step 1 of the Chapter 2 pass (2026-11-03), applied to the base before the rooms: Wordle's roll-in carries its speed into the first
hop (a constant deceleration from 31 to 4.3 px a frame instead of power1.out's soft stop, which nearly stopped the ball at 1.75 s),
and the intro spin of Wordle and Connections turns one full turn per circumference of the ball's travel (it was 3 turns for about 790
and 700 px). The spin is keyed on the same frames and eases as the ball's x (spin = x / R, so the curve is identical).

It replays the edits in the order they were first made (a per-frame bake, then the keys that replaced it), so the ids it hands out,
and so the whole file, come out the same as the first time."""
import re

import rml_edit
from common import Doc, Scene, Sheet, bake, num

R = 17.68
ROOMS = [("Wordle", "1:1073", "1:1074", 71, 154), ("Connections", "1:559", "1:560", 88, 154)]
XKEYS = {"Wordle": [(71, -80, "wordle.rollin"), (107, 556, "linear"), (129, 651, "linear"), (132, 651, "linear"), (154, 707.10999, "hold")],
         "Connections": [(88, -80, "power1.out"), (124, 470, "linear"), (154, 616.07001, "hold")]}


def apply(path):
    doc = Doc(path)
    i = doc.idx("0:2826")
    doc.lines[i] = re.sub(r"<CubicEaseInterpolator [^/]*", '<CubicEaseInterpolator x1="0.3333" y1="0.5853" x2="0.6667" y2="0.9187" id="0:2826" ',
                          doc.lines[i]).replace('" />', '"/>').replace('  "/>', '"/>')
    doc.save()
    scene = Scene(path)
    sheet = Sheet(scene)
    anim = {a.get("name"): a for a in scene.root.iter("LinearAnimation")}
    doc = Doc(path)
    for room, ball, spin, f0, f1 in ROOMS:
        kx = sheet.anim_keys(anim[f"{room} Intro"])[ball]["x"]
        end = kx.at(f1)
        rot = {f: (kx.at(f) - end) / R for f in range(f0, f1 + 1)}
        keys = bake(rot, range(f0, f1 + 1))
        keys[-1] = (keys[-1][0], 0.0, "hold")
        doc.set_prop(f"{room} Intro", spin, "rotation", keys)
        doc.set_prop(f"{room} Waiting", spin, "rotation", [(0, rot[f0], "hold")])
        j = doc.idx(spin)
        doc.lines[j] = re.sub(r'rotation="[^"]*"', f'rotation="{num(rot[f0])}"', doc.lines[j])
    doc.save()
    rml_edit.EASES["wordle.rollin"] = (0.3333, 0.5853, 0.6667, 0.9187)
    doc = Doc(path)
    for room, ball, spin, f0, f1 in ROOMS:
        xs = XKEYS[room]
        end = xs[-1][1]
        doc.set_prop(f"{room} Intro", spin, "rotation", [(f, (x - end) / R, how) for f, x, how in xs])
    doc.save()
