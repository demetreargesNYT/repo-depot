"""Build a chapter and put what engineering needs in deliver/<chapter>/.

    npm run deliver ch2

  1. runs the fast check (build, rule checks); stops if anything fails
  2. builds the chapter with `rive --once`
  3. checks the artboard is included in the export: includeInExport is not false in scene.rml, and the built
     .riv contains the artboard, state machine and view model by name
  4. checks the example page (harness/index.html) pins a Rive runtime and loads only files that are delivered
  5. copies the build as chapter-2.riv, engineering/chapter-2-integration.js, engineering/yig-text-motion.css and the
     example page as index.html into deliver/<chapter>/, removing anything else there, and writes README.md
     (one page for engineering, also copied to engineering/README.md)
  6. zips deliver/<chapter>/ to deliver/yig-chapter-2-handoff.zip

deliver/ is ignored by git; send the zip.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import check
import check_chapter
from rml_read import Scene, REPO, chapter_dir

RIVE = os.path.expanduser("~/.rive/bin/rive")
# the file name engineering's integration code loads from; one name per chapter
DELIVERED_NAME = {"ch2": "chapter-2.riv"}
FILES = ["chapter-2-integration.js", "yig-text-motion.css"]   # from engineering/
PAGE = REPO / "harness" / "index.html"                          # the example page, copied as index.html
ZIP_NAME = {"ch2": "yig-chapter-2-handoff.zip"}
ZIP_ROOT = {"ch2": "chapter-2"}                                 # the folder name inside the zip
# everything deliver/<chapter>/ may hold; anything else left from an older delivery is removed
ALLOWED = {"chapter-2.riv", "chapter-2-integration.js", "yig-text-motion.css", "index.html", "README.md"}


def fail(msg):
    print("STOPPED  " + msg)
    sys.exit(1)


def readme(scene, riv_name, riv_bytes, chapter, revision, runtime):
    ab = scene.artboard
    sm = ab.find("StateMachine").get("name")
    vm = scene.view_model.get("name")
    built = sorted(set(scene.scene_numbers().values()))
    games = [("Empty Chapter 1 room (first card)", "chapter1", 9), ("Opener", "opener", 0), ("Wordle", "wordle", 1), ("Connections", "connections", 2),
             ("Strands", "strands", 3), ("Spelling Bee", "spelling-bee", 4), ("The Mini", "mini", 5), ("The Midi", "midi", 6),
             ("The Crossword", "daily", 7), ("Empty Chapter 3 backdrop (last card)", "chapter3", 8)]
    backdrops = {"chapter1", "chapter3"}      # colours only: no room, no lockup, no ball
    games_table = "\n".join(f'| {label} | `"{name}"` | {n} | {"built" if name in backdrops or n in built else "coming"} |' for label, name, n in games)
    return f"""# Year in Games 2026, Chapter 2: handoff for engineering

This folder is a working example of Chapter 2. Run it, tap through it, then build the real thing the same way.

## Run it locally

```bash
cd chapter-2
python3 -m http.server 8000      # or any static server; opening index.html from disk won't load the .riv
```

Open http://localhost:8000/. Tap the right half of the stage (or →) for Next, the left half (or ←) for Back.
**Restart** reloads; **Desktop / Phone** switches between the full {ab.get('width')} × {ab.get('height')} artboard and the
centre 375-wide phone crop. The page loads the Rive runtime from jsDelivr, so it needs the network.

The NYT fonts aren't included, so the example copy shows in a fallback font. On your site, its fonts (NYT Franklin
and NYT Karnak) apply as normal.

## Files

| File | What it is |
|---|---|
| `{riv_name}` | the Rive file ({riv_bytes:,} bytes): artboard `"{ab.get('name')}"`, state machine `"{sm}"`, view model `"{vm}"` (numbers `scene`, `direction`; boolean `community`) |
| `chapter-2-integration.js` | our integration code. Use it as written: it loads the file, handles Next and Back, and reveals the copy |
| `yig-text-motion.css` | the text motion; all text timing lives here |
| `index.html` | the example page: example player data, `buildCards`, the copy, `start(cards)` and the tap wiring |

## Cards and game names

The chapter is an ordered list of cards, one per tap. Build it from the player's stats and pass it to the
integration's `start(cards)` once, before any tap:

```js
import {{ start, onTap, onBack }} from "./chapter-2-integration.js";

const cards = buildCards(EXAMPLE_PLAYER); start(cards);
```

Each card names its game:

```js
[{{ game: "chapter1" }}, {{ game: "opener" }}, {{ game: "wordle" }}, {{ game: "wordle" }}, {{ game: "connections", community: true }}, {{ game: "chapter3" }}]
```

- `game` is one of `"chapter1"`, `"opener"`, `"wordle"`, `"connections"`, `"strands"`, `"spelling-bee"`, `"mini"`, `"midi"`, `"daily"`, `"chapter3"`.
  The integration turns the name into the Rive file's `scene` number; you never set Rive values yourself.
- `community: true` marks a game's community card (the player solved fewer than 10 of its puzzles). Rive then
  leaves out that game's lockup; everything else plays the same.
- Any other fields (the example uses `card` and `variant`) are yours, for choosing the copy.
- **The list always starts with `{{ game: "chapter1" }}` and ends with `{{ game: "chapter3" }}`** (see "The first and last cards" below).
  Between them: the opener, then each game's cards together, in the player's order.
- An unknown name throws. A game that isn't built in the `.riv` yet keeps the current room on screen, still changes
  the copy, and logs a console warning, so you can wire up later games before their art ships.

## buildCards: an example of your logic

In `index.html`, `EXAMPLE_PLAYER` stands in for the Games API (it's made-up data), and `buildCards(player)` turns
it into the card list. It's an example of the logic you'll write against the real stats, not code to ship:

- `chapter1` first, then the opener, then each game in the player's order, then `chapter3` last;
- 10 or more solves: the game's own cards, skipping a card that has no stat (for example the top starting words
  card when no word repeated), and picking the hardest-word card's variant from the result (solved, missed,
  not played);
- fewer than 10 solves: the game's one community card;
- games not built yet are left out for now.

The Connections solving-order pills follow the order in the player's stats (`solvingOrder` in the example), not a
fixed order.

The example player is a mixed case: Wordle with its own cards and two starting words, then Connections as a
community card. The comment above `EXAMPLE_PLAYER` shows how to try other cases.

Each card's copy is a block of HTML, rendered up front and hidden, marked `data-copy-frame="<card index>"`; each game's
icon is a block marked `data-icon-game="<game name>"`. The integration shows and hides them.

## The first and last cards

Chapter 2 is one of several Rive files that play back to back. The player never sees a file swap, because each file
starts and ends on a picture of an empty room, and the file before or after shows exactly the same picture:

- **First card, `{{ game: "chapter1" }}`**: the file loads on the empty Chapter 1 room (cream `#F1ECC0` wall, orange
  `#FF811E` floor, floor line at 712, no ball, no copy). It is the picture File 1 ends on, where Ad 2 plays. The first
  tap pans from it into the opener (the same pan as between games, 1.6 s), and the opener plays its own 3.2 s intro
  (no lockup: it isn't a game). Back from the opener returns to it; Back on this card does nothing.
- **Last card, `{{ game: "chapter3" }}`**: after the player's last game, a tap makes that room leave and an empty
  Chapter 3 backdrop (lavender `#E1DBF5` wall, green `#05CE7C` floor, floor line at 712, no ball) pan in. It is the
  picture File 3 opens on, and where Ad 3 plays for anonymous players. Back from it returns to the last game.

File 1 and File 3 aren't built yet. When they are, one integration will swap files on these exact pictures, so keep
these two cards in the list now and your calls (`start(cards)`, `onTap()`, `onBack()`) won't change. Neither card
has Rive copy: the example page shows placeholder text on the last card only so you can see it arrive.

## start, onTap and onBack

Call `start(cards)` once with the card list, then `onTap()` on Next and `onBack()` on Back. That's the whole
integration:

- They move to the next or previous card, and set Rive's `scene`, `direction` and `community` for it. A card in the
  same game changes only the copy; Rive keeps looping.
- They reveal the card's copy and the game's icon, timed to Rive (3.2 s after the tap for a game's first visit, when
  the pan ends for a game you come back to, about 0.34 s for a card in the same game).
- Back on the first card (`chapter1`), Next on the last card (`chapter3`), or a tap before `start`, does nothing. A tap that would reverse a pan waits for it to end.
  You don't time anything in JavaScript and you don't handle Rive events.

The module also exports `setScene` and `yig` (the Rive instance, for cleanup: `yig.cleanup()`).

## CSS classes

All set by the integration; you only write the markup.

| Class | Meaning |
|---|---|
| `yig-text` | a card's copy block |
| `yig-icon` | a game's icon block, with the icon inside `yig-pop` |
| `yig-mask` > `yig-line` | one designed line; each line rises in its own mask. `yig-pop` on an image pops instead |
| `yig-in` | reveal: waits `--yig-delay` (3.2 s by default), then rises in |
| `yig-quick` | same game: rises right after the old copy clears (`--yig-clear`, 340 ms) |
| `yig-after-icon` | a game's first card: its lines start one step after the icon |
| `yig-out` | leave: lifts out and dissolves |
| `yig-back` | Back: the same moves, reversed (down instead of up) |

## Rive runtime

`@rive-app/canvas` **{runtime}**. Pin that version. In your app, `npm install @rive-app/canvas@{runtime}` and the
integration's `import {{ Rive }} from "@rive-app/canvas"` resolves as usual. The example page maps that import to the
same version on a CDN only so it runs without a build step.

## Built and coming

| Card | Name | Rive `scene` | Status |
|---|---|---|---|
{games_table}

The icons for Strands, Spelling Bee, The Mini, The Midi and The Crossword on the example page are placeholders cut from their lockups, until final icons are supplied. Their card copy is placeholder too.

New games arrive as an updated `{riv_name}`; the card format and your calls don't change. Copy text is placeholder.

Built from `chapters/{chapter}` {revision}. Rooms in this file: scene {", ".join(map(str, built))}.
"""


def main(argv):
    chapter = argv[0] if argv else "ch2"
    if chapter not in DELIVERED_NAME:
        fail(f"no delivery name for {chapter!r}; add it to DELIVERED_NAME in tools/deliver.py")
    project = chapter_dir(chapter)

    print("1. fast check")
    results = (check.build_checks(project) + check_chapter.run(chapter)
               + [check.opener_clears(project), check.community_hides_lockup(project),
                  check.rooms_are_separate(chapter), check.rooms_sheet_current(chapter)])
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
    missing = [n for n in (ab.get("name"), ab.find("StateMachine").get("name"), scene.view_model.get("name"), "scene", "direction", "community") if n.encode() not in blob]
    if missing:
        fail(f"the built file does not contain {missing}")
    print(f'   includeInExport {flag}; the built file holds artboard "{ab.get("name")}", state machine '
          f'"{ab.find("StateMachine").get("name")}", view model "{scene.view_model.get("name")}" and the number "scene"')

    print("4. the example page works from the delivery folder on its own")
    page = PAGE.read_text()
    runtime = re.search(r"@rive-app/canvas@(\d+\.\d+\.\d+)/", page)
    if not runtime:
        fail("harness/index.html does not load a pinned @rive-app/canvas version")
    runtime = runtime.group(1)
    integration = (REPO / "engineering" / "chapter-2-integration.js").read_text()
    # every local file the page and the integration load must be one of the delivered files, by a relative path
    local = re.findall(r'(?:href|src)="(?!https?:|data:|#)([^"]+)"', page) + re.findall(r'(?:import\(\s*|from\s+)"(\./[^"]+)"', page)
    local += re.findall(r'src:\s*"([^"]+)"', integration)
    extra = sorted({u for u in local if u.lstrip("./") not in ALLOWED})
    if extra:
        fail(f"the example page or integration loads files that aren't delivered: {extra}")
    # the card format engineering sees: { game: ... } passed to start(cards); the old field and global must be gone
    old = [w for w in ("chapterFrames", "scene: \"", "data-copy-scene", "data-icon-scene") if w in page + integration]
    if old or "const cards = buildCards(EXAMPLE_PLAYER); start(cards);" not in page:
        fail(f"the example page or integration still uses the old card format {old or ''} or doesn't call start(cards)")
    print(f"   runtime @rive-app/canvas {runtime}; local files loaded: {', '.join(sorted({u.lstrip('./') for u in local}))}")

    print("5. copy")
    out = REPO / "deliver" / chapter
    out.mkdir(parents=True, exist_ok=True)
    for p in out.iterdir():
        if p.name not in ALLOWED:
            shutil.rmtree(p) if p.is_dir() else p.unlink()
    shutil.copy2(built, out / DELIVERED_NAME[chapter])
    for f in FILES:
        shutil.copy2(REPO / "engineering" / f, out / f)
    shutil.copy2(PAGE, out / "index.html")
    # the commit the chapter's source was last changed in (not "dirty": the README itself is written into the repo)
    sha = subprocess.run(["git", "-C", str(REPO), "log", "-1", "--format=%h", "--", f"chapters/{chapter}"], capture_output=True, text=True).stdout.strip()
    text = readme(scene, DELIVERED_NAME[chapter], built.stat().st_size, chapter, f"(source last changed in git {sha})" if sha else "", runtime)
    (out / "README.md").write_text(text)
    (REPO / "engineering" / "README.md").write_text(text)
    for p in sorted(out.iterdir()):
        print(f"   {p.relative_to(REPO)}  ({p.stat().st_size:,} bytes)")

    print("6. zip")
    zpath = REPO / "deliver" / ZIP_NAME[chapter]
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(out.iterdir()):
            z.write(p, f"{ZIP_ROOT[chapter]}/{p.name}")
    print(f"   {zpath.relative_to(REPO)}  ({zpath.stat().st_size:,} bytes), unzips to {ZIP_ROOT[chapter]}/")
    print("\ndone.")


if __name__ == "__main__":
    main(sys.argv[1:])
