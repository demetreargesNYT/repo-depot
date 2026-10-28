# Year in Games 2026 · Rive

Rive animation for NYT Games' Year in Games 2026 recap ("Well Played"). Design lead: Demetre Arges. This folder, `repo-depot/YIG2026/rive`, is the only place the Rive work happens. Engineering receives finished `.riv` files and the files in `engineering/`.

It lives inside repo-depot (moved in with its history from `~/Desktop/rive-tests/yig-rive`, now `yig-rive-archive`; don't work there). Git commands run against repo-depot, so commit and push follow repo-depot's rules, and add only files under `YIG2026/rive/`. Rive tags are `rive/ch2-…`.

## Status

Full plan and detail: `docs/rive-plan.md` (start with its "Where things stand"). In short, as of the last commit:

- **Chapter 2 file (`chapters/ch2`)** holds scene 0 the opener, 1 Wordle, 2 Connections, 3 Strands, 4 Spelling Bee, 5 The Mini, 6 The Midi, 7 The Crossword. Spelling Bee is approved and pushed to Rive (revision 49089997 "Spelling Bee", tag `rive/ch2-spelling-bee`). **Strands, The Mini, The Midi and The Crossword are in and committed ("WIP: four new rooms, before review") but NOT pushed to Rive and not on GitHub: they await Demetre's review. Do not push to Rive until he approves; never force-push.**
- **Left in Stage 2:** (1) apply Demetre's review notes on the four rooms (their intros are proposals; The Mini, The Midi and The Crossword have loops the illustrator left open, closed here with a return at the end of the loop, which he may want changed); then push (`/Users/demetrearges/.rive/bin/rive push chapters/ch2 "--name=<label>" --yes`, the flag needs `=`), tag `rive/ch2-<name>`, push main only when asked. (2) The Chapter 2 ending: after the last game the room leaves and an empty Chapter 3 backdrop (lavender E1DBF5 wall, green 05CE7C floor) pans in. Not started. (3) The opener: show the current Shelf opener and the illustrator's c2s1 side by side in the harness for his choice; do not swap until he chooses. Not started. After Stage 2: Files 1 and 3, the How-to overlays and the single integration (see the plan).
- **Where to look:** the harness (`cd harness && npm start`, http://127.0.0.1:8765/) taps through all seven games with placeholder copy and placeholder icons. The loop viewers are `deliver/compare/index.html` (generated, not in git; rebuild one with `python3 tools/compare_room.py tools/rooms/<room>.json`, about 3 minutes). Results: Strands matches the illustrator on all 179 frames; Spelling Bee, The Mini, The Midi and The Crossword differ only in their closing returns.
- **Tools:** `tools/import_room.py tools/rooms/<room>.json` (refuses a room already present: `git checkout -- chapters/ch2/scene.rml`, then import again), `tools/compare_room.py`, `tools/svg_to_rml.py`, tests with `python3 -m unittest discover -s tools/tests`, checks with `npm run check ch2`. The illustrator's file (Rive file 2668591) is a read-only copy in `.cache/illustrator/` (git ignores it; it is pulled again if missing); never push to or edit it. The floor line is 712 in every file.
- **Working agreements:** commit straight to `main` (repo-depot exception), adding only the files you changed; the Rive CLI is signed in as lindsey.liang on purpose; leave the `/tmp` scratch folders alone and do not ask about them; Demetre reviews in the harness and the viewers, so skip screenshot contact sheets; the Strands and Spelling Bee lockup icons stay as drawn until he says otherwise. To avoid confirmation prompts: call the Rive CLI by its full path (not `$R`), keep commands simple (no long chains, no `rm -rf` mixed in), and note `.claude/settings.json` at the repo-depot root holds the allowlist.

## Layout

- `chapters/chN/`: one Rive CLI project per chapter. Each is linked to its file in the Rive Team folder through its `rive.yaml`.
- `art/chN/`: import SVGs, original exports and reference PNGs.
- `docs/`: per-chapter animation specs, plus restructure notes.
- `harness/`: one example page, `index.html`, that plays a chapter's built `.riv` with the real Rive web runtime and the text CSS. It is our review page and engineering's example (`npm run deliver ch2` copies it into the handoff), so write it the way engineering will build it: example player data, `buildCards`, the copy, tap halves. No review menus.
- `engineering/`: what developers get: integration code, `yig-text-motion.css`, and a short README.
- `deliver/` (not in git): `npm run deliver ch2` writes `deliver/ch2/` (the `.riv`, integration, CSS, example page, README) and zips it to `deliver/yig-chapter-2-handoff.zip`, which is what gets sent.
- `reference/`: the earlier HTML prototypes, kept as motion references only. They aren't the source of truth.

## How engineering uses a chapter (keep it this small)

- They build the player's card list (`{ game: "wordle" }`, `{ game: "connections", community: true }`), call our `start(cards)` once, and load the chapter's `.riv` with autoplay and call our `onTap()` (Next) or `onBack()` (Back), which set **`scene`** and **`direction`** (1 Next, -1 Back): `scene` is 0 for the chapter opener, then the game the frame shows (Wordle 1, Connections 2, Strands 3, Spelling Bee 4, The Mini 5, The Midi 6, The Crossword 7). Setting the same value again does nothing.
- A game has several cards (Wordle 4, Connections 5 so far), one frame each: the opener, then each game's cards in the player's order. A tap inside a game swaps only the HTML text and the scene number stays, so Rive keeps looping. The tap after a game's last card starts the next game. The game's small icon is its own block, one per game: it pops in with the game's first card (3.2 s after the tap that starts the game) and stays while the cards change; it lifts out with the last card's text when the next game starts. Back mirrors Next: within a game it reverses the text (`yig-back`), across games the room comes back already built and its text arrives when the pan ends. They reveal the next copy with class `yig-in`, plus `yig-quick` when the scene didn't change; a same-game tap during the 3.2 s intro waits until the intro ends; the old copy is hidden at once. They write no animation timing in JavaScript and handle no Rive events.
- Engineering's priority is stats and calculations. Every extra integration step is a real cost, so solve problems inside the Rive file rather than in their code.

## Motion rules

- One Rive file per chapter, to keep file sizes down. The artboard is 1495 × 1067 and serves both desktop and mobile. The phone shows the centre 375 wide.
- The transition between rooms is Roll and pan. **Next moves the camera right; Back is its exact mirror**, moving it left:
  - The outgoing room leaves left. Its wall plane nets 1280 units of travel and its floor plane 1600.
  - The incoming room arrives on the same pan. Rooms carry art only.
- **Color changes by crossfade, never by a seam.** One shared backdrop (wall, floor, floor line) stays put under every room, with no strokes on its edges, so no hard edge ever crosses the stage. On a scene change its wall and floor colors fade to the new room's over 1.45 s, power1.inOut, starting with the tap; a tap mid-fade turns from the color on screen.
  - Everything that leaves clears the full artboard, and everything that arrives starts outside it.
- The red ball is the persistent device:
  - The outgoing room's ball is never keyed by a transition. It keeps its loop and leaves with its room.
  - The incoming ball rolls in from beyond the left edge and climbs to the room's **loop start pose**.
  - Every loop starts and ends on that pose. The ball may change scale between rooms.
- **Every intro is exactly 3.2 s**, because the text CSS waits that long. A room only plays its intro on its first visit; coming back (Back, or the Next after one) it slides in already built.
- **A move never reverses part-way.** Rive can't turn a room around mid-move without a snap (about a quarter of the move in one frame), so a Back during any pan, and a Next during a Back pan, wait in the integration file until the pan ends; only the last held tap counts. Next during a Next pan stays immediate.
- The game lockup (icon plus word) lives in Rive. It rises in after the pieces land and is gone exactly at 3.2 s. The small icon and the stats are HTML. The lockup uses the text's curves: expo.out in, power3.in out.
- **Community cards:** a player who solved fewer than 10 of a game's puzzles gets one community card for it. The boolean `community` hides only that game's Rive lockup (through its Lockup Gate); the intro, pan and backdrop are unchanged. The HTML icon still pops in with the card.
- Text motion (v3): Rise in 720 ms with a fade, 120 ms between lines; Lift out 240 ms, a short drift and dissolve, 20 ms apart, all clear within 340 ms (`--yig-clear`, which `yig-quick` waits and the integration file reads); Pop 560 ms. One mask per designed line. See `engineering/yig-text-motion.css`.
- Parked for later: Sink and stack, where the room sinks through the floor line, a color dome rises, and the pieces drop in.

## State machine pattern (per chapter)

- Two numbers, `scene` and `direction`, and a boolean, `community`. Three layers per room, plus a Lockup layer per game, so layers never key the same property:
  - `<Room>`: Waiting → Intro (scene == n) → Loop
  - `<Room> Exit`: Home → Shown (scene == n) → Outro or Back Out (scene != n, by direction) → Gone or Right → Return or Forward In (scene == n) → Shown
  - `<Room> Draw`: Below ↔ On Top on scene == n
  - `<Room> Lockup` (games): Shown ↔ Hidden on community, read only while scene == n
- A `Backdrop` layer holds the colors: from AnyState, scene == n goes to `<Room> Colors` (a one-frame pose of the backdrop's wall and floor color) with a 1450 ms power1.inOut blend and early exit on. Rive mixes the two states over the blend, which is the crossfade; no other timeline keys the backdrop.
- The moves key only `<Room>` x and `<Room> Wall Lag` x; the draw rule is keyed only by the Draw layer's two poses.
- Details are in `docs/scene-restructure.md`.

## Build rules

- A room's loop is the illustrator's, copied exactly (keys, timing, easing, positions, pivots). Bake the ball rig into direct keys; never reinterpret. Close a loop only by setting a property's last key to its first, and list the fix in `docs/rive-plan.md`. Use `tools/import_room.py` (and `tools/compare_room.py` for the frame-by-frame check against the source); the intro is the only motion designed here. The illustrator's file is kept read-only in `.cache/illustrator/` (git ignores it; the importer pulls it again if it is missing); never push to or edit it.
- The Rive CLI is the primary tool. New artwork goes in through the Rive Editor first (the CLI has no SVG import), then `rive pull`.
- Wrap anything that rotates or squashes so its group's own position sits on the pivot, with an inner "Art" group offset back.
- Keep `includeInExport` true on every artboard that ships.
- Never edit in the Editor and locally at the same time. Pull before local edits, verify and screenshot before pushing, and push with a `--name` label. Commit to git at every named push.
- When changing timing, keep each intro at 3.2 s, and keep each loop's first and last frames identical.
- After every change: run `--verify` and the automatic rule checks, as one script that takes about a second: `npm run check ch2`. It checks that Waiting poses equal their intro's first keys, every intro is exactly 3.2 s, every loop's first and last frames match (and start on the intro's last frame), and everything clears the artboard. Don't re-render, pixel-diff or time anything the change didn't touch. Full render, pixel and timing passes (`npm run tap`, `npm run back`, `npm run text`, frame-by-frame renders against `art/chN/reference-frames/` and the reference prototype) are only for a handoff to engineering, or when asked. Motion and feel are reviewed by Demetre in the harness, so when a change affects what's on screen, say exactly what to look at.
- Rive draws a group's first child on top, so children are drawn in reverse of the order they are written. Anything that must sit behind everything, such as the shared backdrop, is the last child.
- A color change is a blend between two hold poses, set by the transition's duration and ease; never author the in-between, and never give a room its own backdrop. Turn on early exit, or a tap mid-fade waits for the old fade to finish and the color jumps.
- RML omits `value="0"` on keys, so read keys with a real XML parser and treat a missing value as 0. A regular expression reads them as missing, and that once put shadows and lockups at full size in a Waiting pose.
- Each Waiting pose must equal its intro's first keys. `npm run check` tests this for every room; after editing an intro, rebuild its Waiting pose from the intro, never by hand.
- A leaving room draws below the arriving room through draw rules, not by reordering rooms: each room's Draw layer puts its rule on Top (the shared Top Marker, above every room) while it is the scene and on Bottom otherwise. A draw target has to name a Shape, not a group.
- Each lockup lives inside its own room so it leaves with the room.
- To test taps at exact moments, put test-only listeners in a throwaway copy and press them with `--pointer=down` (see `tools/back_test.py`); `--data` only sets values before the run starts. Binding a node's x out to the view model (`direction="true"`) with `--data-dump-every=1` records where it is on every frame.
