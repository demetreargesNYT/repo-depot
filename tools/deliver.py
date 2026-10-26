"""Build a chapter and put what engineering needs in deliver/<chapter>/.

    npm run deliver ch2

  1. runs the fast check (build, rule checks); stops if anything fails
  2. builds the chapter with `rive --once`
  3. checks the artboard is included in the export: includeInExport is not false in scene.rml, and the built
     .riv contains the artboard, state machine and view model by name
  4. copies the build as chapter-2.riv together with engineering/chapter-2-integration.js and
     engineering/yig-text-motion.css into deliver/<chapter>/
  5. writes deliver/<chapter>/README.md (a short note for engineering), and refreshes engineering/README.md

Nothing is copied to repo-depot; copy the deliver/<chapter>/ folder there yourself when you are ready.
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import check
import check_chapter
from rml_read import Scene, REPO, chapter_dir

RIVE = os.path.expanduser("~/.rive/bin/rive")
# the file name engineering's integration code loads from; one name per chapter
DELIVERED_NAME = {"ch2": "chapter-2.riv"}
FILES = ["chapter-2-integration.js", "yig-text-motion.css"]


def fail(msg):
    print("STOPPED  " + msg)
    sys.exit(1)


def readme(scene, riv_name, riv_bytes, chapter, revision):
    ab = scene.artboard
    numbers = scene.scene_numbers()
    # Shelf is the opener; every other layer name is the game it shows
    # (the Shelf layer has no intro, so its scene value is only in the conditions of "Shelf Exit")
    labels = {n: ("the chapter opener" if name.removesuffix(" Exit") == "Shelf" else name.removesuffix(" Exit")) for name, n in numbers.items()}
    table = "\n".join(f"| {n} | {labels[n]} |" for n in sorted(labels))
    table += "\n| 3 to 7 | Strands, Spelling Bee, The Mini, The Midi, The Crossword (not built yet) |"
    return f"""# Year in Games 2026, Chapter 2: handoff for engineering

Load the chapter's file, call our Next or Back function when the player taps, and reveal the next copy. Everything else, including
all animation timing, is inside the Rive file and `yig-text-motion.css`.

## The three steps

1. **Load `{riv_name}`** with the Rive web runtime, autoplay on, state machine `"{scene.artboard.find('StateMachine').get('name')}"`, and
   `autoBind: true` so the file's view model is bound (see `chapter-2-integration.js`; pin the runtime version you ship).
2. **On Next, call `onTap()`; on Back, call `onBack()`.** They set the view model numbers `direction` (1 or −1)
   and `scene` (the scene the new frame shows). Setting the value `scene` already has does nothing, so it is
   always safe. Back on the opener does nothing. A Back that lands while the rooms are panning waits for the
   pan to end (at most 1.65 s), then plays; the integration file handles it, nothing for you to time.
3. **Reveal the next copy** with class `yig-in`, plus `yig-quick` when the scene didn't change, and `yig-back` on
   Back. The CSS does all the timing: copy for a new game rises 3.2 s after the tap, matching the Rive intro; copy
   for a game you come back to arrives when the pan ends. Hide the old copy at once. A tap that only moves to the
   game's next card, while that game's intro is still running, waits until the intro ends (the integration file
   sets that delay).

`chapter-2-integration.js` does all three; use it as written. Its exports are `onTap`, `onBack`, `setScene` and `yig`.

## Scene values

| `scene` | Shows |
|---|---|
{table}

A game has several cards, one frame each. A tap inside a game keeps the same `scene` (the text changes, Rive keeps
looping); the tap after the game's last card sets the next game's `scene`. A game appears in one run of cards;
Back returns through them in reverse.

## Files

| File | What it is |
|---|---|
| `{riv_name}` | the Rive file ({riv_bytes:,} bytes): artboard `"{ab.get('name')}"` {ab.get('width')} × {ab.get('height')}, state machine `"{scene.artboard.find('StateMachine').get('name')}"`, view model `"{scene.view_model.get('name')}"` with the numbers `scene` and `direction` |
| `chapter-2-integration.js` | the integration code: load, Next and Back (`scene`, `direction`), reveal copy |
| `yig-text-motion.css` | text motion v3: Rise in 720 ms, Lift out 240 ms (clear in 340 ms), Pop 560 ms, reversed on Back; waits 3.2 s for a new game |

Built from `chapters/{chapter}` {revision}.
"""


def main(argv):
    chapter = argv[0] if argv else "ch2"
    if chapter not in DELIVERED_NAME:
        fail(f"no delivery name for {chapter!r}; add it to DELIVERED_NAME in tools/deliver.py")
    project = chapter_dir(chapter)

    print("1. fast check")
    results = check.build_checks(project) + check_chapter.run(chapter) + [check.opener_clears(project)]
    bad = [t for ok, t in results if not ok]
    if bad:
        for t in bad:
            print("   FAIL  " + t)
        fail(f"{len(bad)} check(s) failed; nothing was built or copied")
    print(f"   {len(results)} checks passed")

    print("2. build")
    r = subprocess.run([RIVE, str(project), "--once", "--format=json"], capture_output=True, text=True)
    try:
        info = json.loads(r.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        fail("the build produced no readable result:\n" + r.stdout + r.stderr)
    if not info.get("success") or info["data"].get("problems"):
        fail("the build reported problems: " + json.dumps(info["data"].get("problems") or info.get("errors")))
    built = (project / info["data"]["riv"]).resolve()
    print(f"   {built.relative_to(REPO)}  ({built.stat().st_size:,} bytes)")

    print("3. the artboard is included in the export")
    scene = Scene(project / "scene.rml")
    ab = scene.artboard
    flag = ab.get("includeInExport", "true")
    if flag == "false":
        fail('the artboard has includeInExport="false", so the export would leave it out')
    blob = built.read_bytes()
    missing = [n for n in (ab.get("name"), ab.find("StateMachine").get("name"), scene.view_model.get("name"), "scene", "direction") if n.encode() not in blob]
    if missing:
        fail(f"the built file does not contain {missing}")
    print(f'   includeInExport {flag}; the built file holds artboard "{ab.get("name")}", state machine '
          f'"{ab.find("StateMachine").get("name")}", view model "{scene.view_model.get("name")}" and the number "scene"')

    print("4. copy")
    out = REPO / "deliver" / chapter
    out.mkdir(parents=True, exist_ok=True)
    shutil.copy2(built, out / DELIVERED_NAME[chapter])
    for f in FILES:
        shutil.copy2(REPO / "engineering" / f, out / f)
    # the commit the chapter's source was last changed in (not "dirty": the README itself is written into the repo)
    sha = subprocess.run(["git", "-C", str(REPO), "log", "-1", "--format=%h", "--", f"chapters/{chapter}"], capture_output=True, text=True).stdout.strip()
    text = readme(scene, DELIVERED_NAME[chapter], built.stat().st_size, chapter, f"(source last changed in git {sha})" if sha else "")
    (out / "README.md").write_text(text)
    (REPO / "engineering" / "README.md").write_text(text)
    for p in sorted(out.iterdir()):
        print(f"   {p.relative_to(REPO)}  ({p.stat().st_size:,} bytes)")
    print("\ndone. Nothing was copied to repo-depot.")


if __name__ == "__main__":
    main(sys.argv[1:])
