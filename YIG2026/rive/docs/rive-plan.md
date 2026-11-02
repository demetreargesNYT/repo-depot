# Year in Games 2026: Rive plan for the whole experience

## Start here

**What this is.** The Rive animation behind NYT Games' Year in Games 2026 recap ("Well Played"): three Rive files (`chapters/ch1`, `ch2`, `ch3`) that play back to back behind HTML slides, for subscribers and anonymous players alike. Design lead: Demetre Arges. Engineering drives the files from their own React code, using `docs/engineering-guide.md`.

**Read, in this order:** `CLAUDE.md` (the rules and how we work), this file, `docs/experience.md` (the product picture: both flows, the card rules), `docs/rooms.md` (Chapter 2), `docs/rooms-ch1.md`, `docs/rooms-ch3.md` (plain-words sheets of every room, each with its "To tune later" items), and `docs/engineering-guide.md` (what engineering gets; final, don't edit it without being asked).

**Test tiers** (the same as `CLAUDE.md`; every one stops at the first failure and names the piece, the reason and its log in `test-logs/`):

| Tier | Command | Covers | Takes |
|---|---|---|---|
| While iterating | `npm run check <ch>` | The rule checks for one file: Waiting poses equal their intro's first keys, every intro is exactly 3.2 s, every loop starts and ends on one pose, nothing is left on the stage, no piece strays beyond the room's bounds. | 1 to 5 seconds |
| After a meaningful change | `npm run smoke` | The rule checks for all three files, the unit tests, the Chapter 2 page's text timing in its short form, and the experience harness for one subscriber player and the anonymous flow on phone. | about 10 minutes (9 min 52 s measured) |
| Before a Rive push or an engineering handoff | `npm run suite` | Everything, in short pieces one at a time: rule checks, unit tests, tap and back for each file, the full text test, the experience harness (subscriber and anon, phone and desktop), the Finesse panel, and the package demo for every example player. | about 1 hour (58 min measured before the Finesse piece was added) |

**Standing rules.**

- No Rive push, no engineering handoff and no `git push` without Demetre's approval. Never force-push. Commit straight to `main` (repo-depot exception), adding only the files you changed.
- Never edit or push to the illustrator's file (Rive file 2668591; a read-only copy in `.cache/illustrator/`) or to the YIG Test copy (Rive file 2666044; `.cache/yig-test/`). Both are only art and history now.
- **What is in Rive now is the current version of every room.** There is no "illustrator's version" to match: any change you make becomes the newest version. Room-by-room calls (how the ball enters, whether it squashes, a full journey or a hop, where a loop starts) are made during finesse and need not be the same on every card.
- **Animations keep running while a room pans out on Next and pans in on Back.** Nothing freezes mid-motion. Any exception is a one-off, listed with its room (none yet).
- The scene loop guideline in `CLAUDE.md` stays as the intent; the Rive CLI is signed in as lindsey.liang on purpose.

**Next:** the global pass (below), then the rooms in the Finesse order.

## Status (2026-11-02)

- **The engineering package is final** (commit `158faed`, `deliver/yig-engineering-package.zip`, built with `python3 tools/package_engineering.py`) and goes to engineering from Demetre. Nothing is sent without him.
- **Done:** the engineering guide and React example; the test cleanup (the three tiers, one entry point `window.__yigTest` for the Chapter 2 page's text test); the Finesse panel on `/experience`. Nothing from the package rework onward has been pushed to GitHub (local commits on `main`).
- **Latest Rive revisions** (all pushed 2026-10-30 as "Framework for engineering", tags `rive/ch1-framework-for-engineering`, `rive/ch2-framework-for-engineering`, `rive/ch3-framework-for-engineering`; no Rive file has changed since):

| File | Rive file | Revision |
|---|---|---|
| File 1 · `chapters/ch1` · "yig-ch1" | 2692475 | 49235075 |
| File 2 · `chapters/ch2` · "yig-ch2" | 2677803 | 49235086 |
| File 3 · `chapters/ch3` · "yig-ch3" | 2693093 | 49235090 |

- **Next:** the global pass, then rooms in the Finesse order. Then the mobile How-to file (`how-to-mobile.riv`, placeholder art until Demetre's arrives).

## Global pass (decided 2026-11-02)

Four things that repeat across rooms. Everything else that repeats (the 0.15 s pop at 3.05 s, the shared roll-in, the landing squash, the Wordle and Connections stillness at the loop start, journey versus hop) is a room-by-room call, listed under the rooms in the Finesse order.

1. **No room freezes mid-motion.** Two cases only. (a) When a room pans out on Next, its loop and its small loops keep playing as it leaves. (b) A room that is already built pans back in already moving on Back. Survey both by stepping through every room's pan out and Back pan in with the Finesse panel, list anything that stops, and fix it room by room; list any one-off exception with its room. **Not part of this, and intended (Demetre, 2026-10-30):** on a room's first visit the room pans in and plays its intro, and its small loops (the "<Room> Small" layers) hold their opening pose until the pan ends (1.65 s, 99 frames), then start.
2. **The ball's easing in The Mini, The Midi and The Crossword.** The balls do not feel right yet. Likely causes, in `docs/rooms.md` ("To tune later"): how the keys were baked (one key per frame, thinned), squash and pivots, two position nodes, the returns that close each loop, the intro hand-off. First step: compare speed per frame, not just position, and re-bake or hand-ease.
3. **The loop seams.** Use the panel's seam flash on every loop. Known: The Mini, The Midi and The Crossword close their loops with a return (The Midi's is 20 frames, eased); Strands' second move ends 0.02 s before the loop restarts; Chapter 1 card 5's ball jumps 257 units and the loop does not close on that property (`openLoops`); three Chapter 4 fireworks sets (Connections, Spelling Bee, Wordle) look different near the end of their 5 s loop.
4. **The safe area** (x 560 to 935, y 0 to 812, the Figma phone frame): balls and key pieces stay inside. Known outside: the stand-in balls in Chapter 3 (rests at x 1030) and Chapter 4 (x 577, reaching past the left edge); the ball in Chapter 1 card 1 when it rolls off the right edge; parts of Connections and The Mini, the outer side pieces of Spelling Bee, The Crossword and Connections on the largest phone, Start's armchair and plant, End's two piles, Chapter 4's side fireworks, The Mini's front cube (below y 823).

## Finesse order

Each room starts with its current "To tune later" items (`docs/rooms*.md` have the full text). **Room-by-room calls for every room with a ball, decided as we go:** how the ball enters (it won't be the same on every card, and sometimes it is just part of the loop); whether it squashes; a full journey or a hop; where the loop starts. Reference facts for those calls: the roll-in runs 2.30 to 3.05 s in Chapter 1 cards 2 to 5, Strands, Spelling Bee, The Mini, The Midi and The Crossword (from x -80, 0.75 s, `power1.out`, a soft stop) and the ball is absent for about 0.65 s after the pan ends; a 0.15 s `power2.out` "pop" at 3.05 s lifts the ball 76 to 272 px onto the loop's first pose in seven rooms (Chapter 1 cards 2 to 5, Strands, The Midi, The Crossword); only Wordle and Connections have a landing squash and a spin.

1. **Loading / Start (File 1).** The bird's bounce (third version): check it in the panel. The stage crop puts the floor line at about 702, not the mock's 712, so the ball sits a little high against the HTML. Call: how the ball and bird enter.
2. **Chapter 1 rooms 1 to 5 (File 1).**
   - Card 1: the shift per contact, the 3 s pause (3.03 s), the eye's timing and a bigger "asleep" cue (head dips, a small z), the dog's tail speed, the clouds' speed; the ball leaves off the right edge (safe area). Already follows the loop guideline.
   - Cards 2 to 4: the pop (258, 272, 245 px) and the shared roll-in; squash. Card 5: the 257-unit jump and the open loop (global 3); the pop (80 px).
3. **Chapter 2 opener (Shelf, File 2).** None recorded; the ball's loop is three small moves (0.15 s, 0.30 s, 0.15 s). Calls: entry, squash.
4. **Chapter 3 and the bird room (File 3).** Chapter 3: a stand-in ball instead of a full journey (call: journey or hop; safe area, global 4). Bird on Ball (`chapter-3-bird`): the bird on the ball is a stand-in.
5. **Chapter 4 with the reveal (File 3).** The stand-in ball (journey saved until card 1 and the video hand-off are decided; safe area); three fireworks sets' loop ends (global 3); The Mini and The Midi are placeholders (walls and The Crossword's fireworks); the stack rides in with the floor (a drop needs both halves timed together); the video background is page HTML. The reveal: the wall fades over 1.45 s and the copy waits for it.
6. **End (File 3).** No ball of its own (two piles and the big one under the bird); the pieces ride in with the floor.
7. **Game rooms, in this order.**
   1. **Wordle:** about 0.6 s of stillness at the start of its loop (first move at 0.63 s; call: where the loop starts); squash and spin that most rooms lack.
   2. **Connections:** the same stillness (0.65 s); partly outside the largest phone's view.
   3. **Spelling Bee:** one 3.93 s hop; the outer side pieces fall outside the largest phone's view; the lockup icon stays as drawn until you say.
   4. **The Mini:** the ball's easing (global 2); it reaches its place at 3.05 s; the front cube sits below y 823.
   5. **Strands:** the 76 px pop; the second move ends 0.02 s before the loop restarts (global 3); the lockup icon stays as drawn until you say.
   6. **The Midi:** the ball's easing and the 20-frame return (globals 2 and 3); the 139 px pop.
   7. **The Crossword:** the ball's easing (global 2); the 128 px pop in 0.15 s; its loop is 2.5 s inside a 3 s animation.
8. **The bridge room, last, once Demetre's art is in.** An empty version of the opener's room for now (also on the guide's Coming later list).

## The Finesse panel (on `/experience`)

Off by default. The **Finesse** button, or the **F** key, docks a panel at the right and reloads the stage on the same card with a clock the panel controls (`harness/finesse-clock.js`, added to the stage page only when the address has `?finesse=1`; with the panel off the stage page is unchanged). The existing **Screen** menu picks the phone crop.

- **Replay room:** reloads on the room's first card (the way Jump to does), so its intro plays as on a first visit, then its loop.
- **Timecode:** seconds to one decimal, 0 at the moment the scene is set, plus the 60 fps frame number. A strip shows the intro, an orange mark where each loop restarts, a blue mark where each small loop restarts, and the playhead (times from `tools/room_timing.py`, served as `/room-timing`).
- **Pause / play, step:** `◀|` and `|▶` (or `,` and `.`) step one frame; Space pauses and plays. Stepping forward runs exactly 1/60 s. The Rive runtime cannot run backwards, so every frame drawn is also copied (reduced in size) into a buffer of the last 2 s, and stepping back walks through those copies over the live canvas.
- **Speed:** 1× or 0.5×. The copy's CSS animations follow; the integration's timers (copy delays, held taps) keep real time, so tap on the stage only when a pan has ended at 0.5× or while paused.
- **Loop seam:** each time a loop restarts, a bar at the top of the stage flashes orange (blue for a small loop) and the panel counts seams passed. Seams are tracked on a first visit only; a room that comes back already built keeps its first-visit phase, so use Replay room for a clean run.
- Tested by `harness/finesse-test.mjs` (20 checks; in `npm run suite`).
- **Before and after:** `python3 tools/compare_room.py <ch> <scene> [--rev <commit>] [--frames A-B]` renders a room now and at an earlier commit (HEAD by default) side by side with a scrubber and the differing pixels in red (`deliver/compare/`, not in git).

## Decisions that still hold

One line each, newest last within a theme; git keeps the full history.

**Design and structure**

- Both flows (subscriber/registered and anonymous) ship as the same three files; only the card list and the HTML copy differ.
- The floor line is 712 in every file. The artboard is 1495 × 1067 for desktop and mobile. Balls and key pieces stay inside the safe area, x 560 to 935 and y 0 to 812 (the Figma phone frame); engineering's framing decides the actual crop.
- Rooms are plain RML in the file, not nested components (2026-10, Stage 1: the rule checks only read the main artboard, and a component clips to its own frame). Each room's ball is plain ball art; the rig it came from was baked into direct keys.
- Ads and the top-game video are cards with no Rive copy; the HTML owns them.
- Every intro is exactly 3.2 s; a room plays its intro on its first visit only. Small loops (decor that runs on its own) live in a "<Room> Small" layer that holds its opening pose until the first-visit pan ends (1.65 s), then starts; that hold is intended (2026-10-30).
- Today's default in most rooms (2026-10-29): the ball's roll-in lands as the intro ends. It is not a rule: how the ball enters is a room-by-room call that finesse may change. Community-card copy arrives when the room's pieces have landed, measured without the ball: Wordle 2334 ms, Connections 2367, Strands 1967, Spelling Bee 2017, The Mini 2084 (`communityCopyMs` in `chapters/ch2/chapter.json`; The Midi and The Crossword have no community cards).
- Colour changes by crossfade over 1.45 s from one shared backdrop; Chapter 4's `reveal` fades the wall the same way and the copy waits for it (2026-10-31).
- Loading and Start are one room: the empty cream-and-orange room with the ball bouncing, then the bird drops onto it (2026-10-30). What the page shows over Loading is up to engineering and isn't designed yet.
- Chapter 2.5 (a player with exactly one qualifying game): the `bridge` scene (an empty version of the opener's room), then a community card for each other community game in the game order, leaving out the player's own. The Bridge Art artboard (`includeInExport` false) is where Demetre arranges the bridge's pieces; it is stripped from the delivered `.riv` (2026-10-29).
- Subscribers have no card on the empty Chapter 3 room: the tap on their last Chapter 2 card plays both moves (4.85 s to Chapter 3's copy; Back 3.3 s). Anons keep Ad 3 there and have four Chapter 3 cards in the subscribers' rooms (2026-10-29, 2026-10-31).
- One fixed game order (Wordle, Connections, Spelling Bee, The Mini, The Midi, The Crossword, Strands), one constant; Rive plays any order. Chapter 1 never skips a card; one skip rule: a card that doesn't qualify is never added (2026-10-31).
- Rive holds the rooms, scenes, animations and the Chapter 2 lockups; everything else is HTML (2026-10-31). The mobile How-to overlay will be a separate small Rive file (`how-to-mobile.riv`); desktop uses arrow buttons.
- Framing: engineering's (`harness/yig-framing.css`) is kept; tap zones are 25% Back and 75% Next; the safe area for balls and key pieces is x 560 to 935, y 0 to 812 (2026-10-29).
- The Strands and Spelling Bee lockup icons stay as drawn until Demetre says otherwise. Figma Code Connect: no.

**Engineering and tooling**

- Engineering uses runtime 2.27.3 (via `@rive-app/react-canvas` 4.20.1) and writes its own React code from the guide; files start with the plural `stateMachines: "Backdrop"`. The package is `core/` (three `.riv` files, the guide, the text CSS, the desktop arrow art) plus `reference/` (React example, `yig-integration.js`, a demo page); built by `python3 tools/package_engineering.py`.
- Testing is three tiers (above). The Chapter 2 page and its text test meet at one entry point, `window.__yigTest`; no other demo-page hook may be read by a test.
- `tools/import_room.py` (and the configs in `tools/rooms/`) brought rooms in once and are history: never re-run them on a room that is already in.- Standing rule from 2026-11-02: what's in Rive is the current version; tools compare against the last commit (`tools/compare_room.py`), not a source.

## Reference

### The files

| File | Scenes | Starts on | Ends on |
|---|---|---|---|
| 1 · `start-chapter-1.riv` | `loading`, `start`, `ad` (Ads 1 and 2), `chapter-1-card-1` to `-5` | Loading | the empty Chapter 1 room (cream F1ECC0 wall, orange FF811E floor) |
| 2 · `chapter-2.riv` | `from-chapter-1`, `intro` (the opener), the seven games (`daily` is The Crossword), `bridge`, `to-chapter-3` | the empty Chapter 1 room | the empty Chapter 3 room (lavender E1DBF5 wall, green 05CE7C floor) |
| 3 · `chapters-3-4-end.riv` | `ad`, `chapter-3`, `chapter-3-bird`, `chapter-4` (seven top-game versions chosen by `topGame`, `reveal`), `end` | the empty Chapter 3 room | End on the orange floor |
| `how-to-mobile.riv` | one artboard, "Mobile" (not built yet) | | |

Every file starts and ends on an empty picture where it meets its neighbour (same wall colour, floor colour, floor line 712, no ball), so the file swap is invisible. Chapter 4 is mostly one room: the same stack of every game's pieces plus the ball, with `topGame` picking a wall colour and a fireworks set.

### Names and properties

- Every file's state machine and view model are both named `Backdrop`. `scene` and `direction` (`forward`, `back`) are enums; `lockup` (File 2; true shows a game's lockup, a community card sets it false), `topGame` and `reveal` (File 3) are the other settable properties. Set `direction`, `lockup`, `reveal`, then `scene`. Each manifest (`chapters/<ch>/chapter.json`) lists every property and enum value, which ones engineering may set, the rooms, the colour poses and each file's "To tune later" notes.
- Conditions compare a scene by its value id, so the order of values in the enum is the value Rive stores: append new values, never reorder.

### The integration

`engineering/yig-integration.js` is the reference for driving all three files from one card list: each card is `{ file, scene, community?, icon?, topGame?, reveal? }`; it loads the next file ahead, keeps earlier files loaded and paused, switches files on the shared empty pictures, holds a Back during a pan, and times the copy (`docs/engineering-guide.md`, section 8). A swap: the next file is already sitting on the shared picture; on the tap that crosses, show its canvas and set its `scene` on the same frame; Back mirrors it (pan back inside the later file, then hand the stage back). `engineering/chapter-2-integration.js` serves only the Chapter 2 test page (`harness/index.html`).

### Review pages and servers

Start the server yourself (`cd harness && npm start`) and open the page: `http://127.0.0.1:8765/experience` is the review page (the whole experience across the three files, a Jump to menu, the flow, the example player, the top game, the screen size, the Finesse panel; it reloads itself on a newer build). `http://127.0.0.1:8765/` is the Chapter 2 test page. Restart the server after changing `harness/serve.mjs`.

### How scenes come in and the tools

`tools/import_room.py` copied the illustrator's rooms into `scene.rml` once each (history; its configs are in `tools/rooms/`). New art that exists only as SVG goes in through the Rive Editor first (the CLI has no SVG import), then `rive pull`. `tools/svg_to_rml.py` converts the lockup SVGs. `tools/scaffold_chapter.py` writes a new file from its manifest. `tools/rooms_sheet.py <ch>` writes `docs/rooms*.md` from the scene file and the manifest (`npm run check` fails when a sheet is out of date). `tools/check_chapter.py` holds the rule checks; `tools/tap_test.py` and `tools/back_test.py` play taps at exact moments in the Rive runtime.

### Lockups

All seven lockups are in `art/ch2/originals/` (`*-lockup.svg`, 175 × 128), converted to Rive shapes with icon and word as separate nodes, placed in the same frame as Wordle's, and wired and timed like Wordle's (in from frame 115, gone at frame 192 / 3.2 s, hidden on community cards). Icon sizes differ (five are 70.8 × 70.8, Strands 77.1 × 80.8, Spelling Bee 76.7 × 75.8) and stay as drawn.

### What's still to come

The mobile How-to overlay; the bridge room's art; Chapter 4 versions (fireworks and walls) for The Mini and The Midi; the real ball journeys in Chapters 3 and 4; the bird-on-ball art in `chapter-3-bird`; what the page shows over Loading.

### Order of work

Done: Chapter 2 (all seven games, the opener, Chapter 2.5), File 1, File 3, the whole experience in one harness page, the engineering guide and React example, the package. **Now:** finesse, room by room (global pass first). **Then:** the mobile How-to file (`how-to-mobile.riv`, created by its first push after Demetre says, then moved by him into the 2026 folder). Every step ends with `npm run check`, and with a list of exactly what to look at in `/experience` when it changes what's on screen.
