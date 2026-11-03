"""Rebuild Chapter 2's scene.rml: the 2026-11-03 delivery's scene (common.BASE_REV), then the step 1 spin fix, then the rooms given,
in order. Run from anywhere:

    python3 chapters/ch2/scripts/build.py --real bee mini strands daily midi     writes chapters/ch2/scene.rml
    CH2_OUT=<folder> python3 chapters/ch2/scripts/build.py strands               writes <folder>/scene.rml (a copy of chapters/ch2 made
                                                                                 on first use), to work on one room without the real file

A rebuild replaces the whole file, so it would undo any edit made in the Rive Editor (or by hand) since: pull those in and fold them
into the room scripts first.
"""
import importlib
import os
import shutil
import sys
from pathlib import Path

from common import RIVE_DIR, Doc, Scene, Sheet, base_text
import wordle_connections_spin

out = os.environ.get("CH2_OUT")
if out:
    out = Path(out)
    if not out.exists():
        shutil.copytree(RIVE_DIR / "chapters/ch2", out, ignore=shutil.ignore_patterns("build", "scripts"))
    SCENE = out / "scene.rml"
elif "--real" in sys.argv:
    SCENE = RIVE_DIR / "chapters/ch2/scene.rml"
    sys.argv.remove("--real")
else:
    sys.exit("set CH2_OUT=<a copy folder>, or pass --real to write chapters/ch2/scene.rml")
SCENE.write_text(base_text())
wordle_connections_spin.apply(SCENE)
scene = Scene(SCENE)
sheet = Sheet(scene)
doc = Doc(SCENE)
for name in sys.argv[1:]:
    print(importlib.import_module(name).build(doc, scene, sheet))
doc.save()
print("wrote", SCENE)
