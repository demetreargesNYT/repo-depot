"""Regenerates the whole Chapter 2 file: with --real it refuses chapters/ch2/scene.rml once it has changed since commit ed0e522 or since its own last build (tools/regen_guard.py).

Rebuild Chapter 2's scene.rml: the 2026-11-03 delivery's scene (common.BASE_REV), then the step 1 spin fix, then the rooms given,
in order. Run from anywhere:

    python3 chapters/ch2/scripts/build.py --real bee mini strands daily midi     writes chapters/ch2/scene.rml
    python3 chapters/ch2/scripts/build.py --out <folder> strands                 writes <folder>/scene.rml (a copy of chapters/ch2 made
                                                                                 on first use), to work on one room without the real file
                                                                                 (CH2_OUT=<folder> still works, but chats use --out)

A rebuild replaces the whole file, so it would undo any edit made in the Rive Editor (or by hand) since: pull those in and fold them
into the room scripts first.
"""
import importlib
import os
import shutil
import sys
from pathlib import Path

from common import RIVE_DIR, Doc, Scene, Sheet, base_text
import regen_guard
import wordle_connections_spin

# The file the room scripts were last folded against: the real file may be rebuilt when it is this commit's, or this script's own last
# build. After an Editor pull or a hand edit, fold the change into the room's script, commit, and move this to that commit.
WRITTEN_AGAINST = "ed0e522"

out = os.environ.get("CH2_OUT")
if "--out" in sys.argv:                 # the flag, in place of the CH2_OUT environment variable
    i = sys.argv.index("--out")
    if i + 1 >= len(sys.argv):
        sys.exit("--out needs a folder")
    out = sys.argv[i + 1]
    del sys.argv[i:i + 2]
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
regen_guard.check(SCENE, WRITTEN_AGAINST, __file__)        # only the real file is checked; a copy (--out) is always rebuilt
SCENE.write_text(base_text())
wordle_connections_spin.apply(SCENE)
scene = Scene(SCENE)
sheet = Sheet(scene)
doc = Doc(SCENE)
for name in sys.argv[1:]:
    print(importlib.import_module(name).build(doc, scene, sheet))
doc.save()
regen_guard.stamp(SCENE, __file__)
print("wrote", SCENE)
