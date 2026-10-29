# Year in Games 2026: Rive plan for the whole experience

Status (end of 2026-10-29): Files 1, 2 and 3 are in Rive; Chapter 2.5 (the `bridge` scene) is approved and pushed (revision 49171643). Step 1 of "Order of work" (the full experience in one harness page) is built and Demetre is reviewing it, together with this round's fixes; none of it is committed yet. Everything a new session needs is in "Current round" below.

## Current round (for the next session; 2026-10-29)

**Committed and pushed today:** `e1de8c8` (the integration starts files with `stateMachines`, for runtime 2.27.3; docs), `1664f79` (Chapter 2.5: the `bridge` scene, Bridge Art, the card rules; pushed to Rive as revision 49171643, tag `rive/ch2-chapter-2-5-bridge`), `3df79d8` (the new order of work; How-to mobile only).

**Built, not committed (Demetre is reviewing; commit only when he approves):**
- The full-experience page: `harness/experience.html` (`/experience`: flow, player, top game, screen size, jump to a chapter) around `harness/experience-stage.html` (`/experience-stage`), driven by the new reference integration `engineering/yig-integration.js` (three files switched on the shared empty rooms, next file loaded ahead, earlier files kept loaded and paused, Back across files, held taps, per-room community copy timing). Framing copied from engineering (`harness/yig-framing.css`, from `RiveBackground.module.scss`; desktop breakpoint 1025 px from their `desktop` mixin; tap zones are halves, theirs are 25% / 75%). This round: the runtime menu is gone (always 2.27.3), an all-seven-games player, a 375 x 812 screen, and the header and copy position from Figma (logo and progress bar, copy at 166 px in a 375 column; values in `yig-framing.css`, logo SVGs in `harness/assets/`). Browser test `harness/experience-test.mjs` (`npm run experience`, 36 checks passed before this round's header change). `harness/serve.mjs` gained the routes (`/experience`, `/experience-stage`, `/yig-integration.js`, `/yig-framing.css`, `/art/global/`, `/assets/`). It uses `art/global/` (Demetre's arrow and game icons, not in git yet: ask before adding).
- Community card copy timing: copy arrives when the room's intro settles (no lockup), per room: Wordle 3167 ms, Connections 2884, Strands 2050, Spelling Bee 2050, The Mini 2084 (Midi and Crossword 2050). In `chapters/ch2/chapter.json` (`communityCopyMs`, checked by `npm run check`), both integration files, and the text test (cases H, L, P; 165 checks passed).
- **The mouse in Chapter 1 card 1** (`chapters/ch1/scene.rml`; local only, not pushed to Rive). The mouse Demetre remembered is not the illustrator's: in their c1s1 (and c0) it is parked under their floor and never animated, and our Floor Clip hid it the same way. The running mouse is the "Mouse Scurry" of the old YIG Test file (`reference/yig-test`). It is now in card 1: the illustrator's mouse art in a pivot group `Chapter 1 Card 1 Mouse` (on the floor line, centre y 706), drawn just under the mouse hole and over the dog, clipped by `Chapter 1 Card 1 Mouse Hole Clip` (everything left of the hole's right edge, x 1089) so it disappears into the hole; the scurry's keys are copied exactly, shifted 60.8 to the right so it uses our hole, and its end hold (inside the hole) trimmed from 630 to 600 frames to fit the 10 s loop. It rests at x 548 by the plant pot. Held in the intro and Waiting pose inside the hole. `npm run check ch1` passes. Start (c0) still has the illustrator's parked, invisible mouse. Before a push: the full test suite (see the testing rule in CLAUDE.md).
- Also uncommitted: `docs/rive-plan.md` ("For the engineering guide" notes), `harness/README.md`, `package.json` (`experience` script), `tools/check_chapter.py` (communityCopyMs check), `CLAUDE.md` (testing rule).

**Open findings (reported to Demetre; no fixes yet):**
- **Ball pauses.** One shared cause, ours: the hand-off from intro to loop. In every room the ball lands 1.9 to 2.05 s into the 3.2 s intro and sits still until the loop starts at 3.2 s: 1.15 to 1.32 s (Wordle 0.98 s and Connections 1.28 s, whose loops also start their first move 0.63 s in; the stand-in balls in Chapter 1 card 1 and Chapters 3 and 4 rest 2 to 3.3 s). The waits inside the loops are the illustrator's own (two keys with the same value where the ball lands; our loops match theirs frame for frame). Ruled out: playback speeds, work areas, held keys that jump, loops set to play once, intro-to-loop transitions (immediate), the runtime (2.27.3 matches 2.45.0). Ways to fix, for Demetre to pick: delay each ball's roll-in so it lands as the intro ends; let the ball's loop start when it lands (its own layer); or add a settle in the gap.
- **Phone framing, Figma vs engineering.** The Figma mobile frame (375 x 812) shows the artboard at 100%: x 560 to 935, y 0 to 812. Engineering's CSS zooms by the window's height (scale = height / 820.8 on portrait screens), so on a 375 x 812 phone it is almost the same (scale 0.989: x 558 to 937, y 2.5 to 823), but on shorter phones it shows more width (iPhone SE 375 x 667: scale 0.81, x 517 to 978, y 2 to 823) where a width-based rule like Figma's would keep 375 wide and cut the bottom (y 0 to 667). On desktop (1440 x 900) engineering crops the top and bottom 66 units; Figma's desktop frame is the whole artboard at 100%. Framing not changed, per Demetre.
- **What falls outside the phone view** (engineering's crop, x 517 to 978 on iPhone SE and 558 to 937 on iPhone 15 Pro Max, y up to 823): the ball in Chapter 1 card 1 and Chapter 3 (stand-ins resting at x 1000 and 1030), partly in Connections and The Mini on the Pro Max; Start's armchair and plant (entirely), End's two piles of red balls, Chapter 4's side fireworks and the right of its stack, Chapter 3's side table, The Mini's front cube (below y 823), and the outer side pieces of Spelling Bee, The Crossword and Connections on the Pro Max. Everything is inside in Wordle, Strands, The Midi and Chapter 1 cards 2 to 5.

**Decisions waiting on Demetre:** tap zones as halves or engineering's 25% / 75%; the arrow art points left, so Back uses it as drawn and Next mirrors it (confirm); subscribers end Chapter 2 on one placeholder card on the empty Chapter 3 room (no Ad 3), confirm; whether `art/global/` goes into git with the page; which ball-pause fix; whether to map Figma components with Code Connect (the Figma tool asked).

**Next:** his review of the page and the mouse; then commit (and, after the full test suite, push File 1 with the mouse); then step 2 of "Order of work" (finesse), step 3 (engineering guide and React example) and step 4 (mobile How-to).


## Where things stand (for the next session)

**Committed and pushed.** Chapter 2's framework: all seven games plus the opener's intro, the empty Chapter 1 start and the empty Chapter 3 ending. Rive file 2677803, revision 49108309 "Chapter 2 framework"; GitHub `main`, tags `rive/ch2-all-seven-games`, `rive/ch2-chapter-2-framework`, `rive/ch2-handoff-4`. Since then: revision 49115884 "Engineering names" (tag `rive/ch2-engineering-names`) and handoff-5 (tag `rive/ch2-handoff-5`), which renames the state machine and view model to `Backdrop`, makes `scene` and `direction` enums and renames `community` to `lockup`. Earlier pushes: revision 49101235 "All seven games" and 49089997 "Spelling Bee". Before the framework push, `rive pull` into a scratch copy and a keyframe-by-keyframe compare against the last-pushed state confirmed no Editor edits.

| Scene | Room | Lockup | Loop vs the illustrator | Closing fix |
|---|---|---|---|---|
| 1 | Wordle | in Rive | n/a (ours) | n/a |
| 2 | Connections | in Rive | n/a (ours) | n/a |
| 3 | Strands | yes | identical on all 179 frames (needs the floor clip) | none |
| 4 | Spelling Bee | yes (pushed) | identical on frames 1 to 212; differs 213 to 239 | y last key 755 to 756 |
| 5 | The Mini | yes | differs only frames 133 to 149 | x and y return over 129 to 149 |
| 6 | The Midi | yes | differs only frames 131 to 149 | four properties return over 129 to 149 (20 frames, eased); the ball's last two keys (frames 132 and 142) are folded into the return |
| 7 | The Crossword | yes | differs only frames 160 to 179 | ball x/y and Group 2 opacity return over 158 to 179 |

**Where to look.** Harness: `cd harness && npm start`, then http://127.0.0.1:8765/ (all seven games, one placeholder card each; the Spelling Bee, Strands, Mini, Midi and Crossword icons and the copy for those games are placeholders, labelled so). Loop viewers (illustrator | ours | difference, with a scrubber): `deliver/compare/index.html`, one folder per room; `deliver/` is not in git, so rebuild with `python3 tools/compare_room.py tools/rooms/<room>.json` (about 3 minutes per room; add `--workers 8` on a fast machine). Checks: `npm run check ch2` (2,398 pass) and `python3 -m unittest discover -s tools/tests` (41 pass).

**Review round (applied, committed and pushed).** Demetre's notes: (a) The Midi's 7-frame loop return read as a jump, now 20 frames starting at frame 129, power2.inOut, for Ball_01 x/y and The Midi Ball x/y; the ball's own settle keys at frames 132 and 142 sat inside that window, so they were replaced by a hold that ends at 129 (the only illustrator keys changed) — he's keeping this as-is; (b) The Crossword's "Group 2" fade-out at the end of its loop stays; (c) the drops in The Mini, The Midi and The Crossword are staggered: The Mini Cubes 1 at 1.00 s, Cubes 3 at 1.13 s, Cubes 2 and 4 together at 1.27 s (2 and 4 are the same top piece, outline and fill); The Midi and The Crossword doors at 1.00 s and the upper or front boxes at 1.13 s. Landings and squashes unchanged; the intro is still exactly 3.2 s. Set-up for fine-tuning: `harness/review.js` (the `#mini` jump and Replay), `docs/rooms.md` (generated by `tools/rooms_sheet.py`, with a "To tune later" note on the ball feel in The Mini, The Midi and The Crossword), and the "Rooms after import" rule in `CLAUDE.md`. The loop fixes for these three rooms are also in "For the illustrator" above, for Demetre to send on.

**Chapter 2 framework (done, approved by Demetre).** Decisions: keep our Shelf opener (the illustrator's c2s1 is not used); the ending into Chapter 3 is approved; the start and the opener's intro are approved.
1. **The start.** The file loads on scene 9, the empty Chapter 1 room: cream wall F1ECC0, orange floor FF811E, floor line 712, no ball, no room art (the `Chapter 1 Colors` pose on the shared backdrop, which is also the backdrop's base colours). It is File 1's last picture, where Ad 2 plays. It is the first card (`{ game: "chapter1" }`); the first tap pans from it into the opener with the same pan as between games; Back from the opener returns to it.
2. **The opener has an intro** (`Shelf Waiting`, `Shelf Intro`; the Shelf layer is Waiting, Intro, Loop like every other room; no lockup, since it is not a game). Exactly 3.2 s: the floor (1600) and wall (1280) planes slide in 0.05 to 1.55 s; the three wall shelves drop one after another at 1.00, 1.13 and 1.27 s, squashing on landing; the toy ball on the cat tree is held on its loop pose. The opener's text waits for the intro like a game's. Details in `docs/rooms.md`.
3. **The ending** (scene 8, empty Chapter 3 backdrop, last card `{ game: "chapter3" }`): lavender E1DBF5 wall, green 05CE7C floor, floor line 712, no ball. It is File 3's first picture, where Ad 3 plays for anons.
Numbering: opener 0, games 1 to 7, chapter3 8, chapter1 9 (internal; the cards use names). Tests (`tools/tap_test.py`, `tools/back_test.py`, `harness/text-test.mjs`) cover both cards and pass; the text test's "game not built yet" cases now serve the integration file with Strands taken out of `BUILT`, since every game is built.

**Foundation (done, approved; committed, pushed to Rive as revision 49115884 "Engineering names", handoff-5 built).** Engineering's requests are in: state machine and view model `Backdrop` in every file, `scene` and `direction` as enums, `community` renamed `lockup` (meaning flipped). Chapter 2 behaves as before: `npm run check ch2` 2,398 pass (the count rose from 2,382 because of the new naming and manifest rules), 41 unit tests, the tap, back and text tests (144 checks) all pass, and the migrated file rendered pixel-identical to the old one (Wordle at 0.5 s and 2.6 s, lockup off, and a Back into Connections). New: `chapters/ch2/chapter.json` (the manifest: names, enums, rooms, who sets what), `tools/migrate_to_enums.py` (one-time, history), `tools/parked/instances-spike.mjs`. The old "YIG Test" project moved to `reference/yig-test/` with its Rive link removed. The scaffold and the importer's template-from-scratch work moves into the File 1 stage, where they can be tested on real output. The instance spike: four live copies of `chapter-2.riv` cost about 1 MB of JS heap each and no WebAssembly growth (16.6 MB, shared); a paused copy keeps its scene; a cold start at a scene shows the default colours first and crossfades to the room's over about 1.5 s, so Back across a handoff keeps the earlier file alive instead of reloading it.

**File 1 (Start + Chapter 1) is built and reviewed by Demetre (stop 2), with two changes made: card 1 got a stand-in ball, and card 5's ball jump is left as the illustrator made it.** **Pushed 2026-10-29: Rive file 2692475 "yig-ch1" (Games Year in Games project 1559255, 2026 folder), revision 49150119 "File 1 framework"; GitHub tag `rive/ch1-file-1-framework`.** `chapters/ch1`, manifest `chapter.json`: scenes `loading` (default), `start`, `ad`, `chapter-1-card-1` to `chapter-1-card-5`. The `ad` scene is the empty Chapter 1 room: the scaffold itself, which renders pixel-identical to File 2's opening picture (0 differing pixels), and Ad 1 and Ad 2 both play on it. All seven scenes share one cream/orange backdrop, so the manifest says `backdrop: fixed` (no Colors poses, no crossfade). Rooms (all imported with `tools/import_room.py` from `tools/rooms/ch1-*.json`, loops copied key for key, fixes in the table below): **Loading** is a placeholder ball hopping in place (no intro, the file opens on it); **Start** is c0 (armchair, plant, dog, outlet and a floor ball; loop 5 s, three illustrator animations merged); **card 1** is c1s1 (clock and window drop in at 1.00 s and 1.13 s; loop 10 s: dog, ping-pong pendulum, eye, and a stand-in ball that rolls in, rests at x 1000 and hops twice; the illustrator's 7 s ball story is not in, see "To tune later" in `docs/rooms-ch1.md`); **cards 2 to 5** are c1s2 to c1s5 (loop 4 s, 3 s, 3 s, 3 s; the first three have pieces that drop in at 1.00 s, 1.13 s and 1.27 s; card 4's pot rides the floor). Intros are all exactly 3.2 s in Spelling Bee's style (planes slide in 0.05 to 1.55 s, ball rolls in from the left at 1.15 s). Checks: `npm run check ch1` 1,007 pass; `back_test` 42 cases and `tap_test` 16 cases pass; `harness/file1-test.mjs` 28 checks pass in a real browser. Loops against the illustrator (`tools/compare_room.py`, frame by frame, viewers in `deliver/compare/<room>/index.html`, not in git): **Start and card 4 match on every frame**; card 3 differs only on frames 131 to 179 and card 2 only on 184 to 239 (their closing returns); card 5 differs on every frame only by the faint tracing image left out on purpose; card 1 differs only by the ball story it does not bring in (the ball leaning out of the clock, the panes flipping to tiles) and, after frame 300, the eye's return. Review page: `harness/file1.html` at `/file1` (restart `npm start` to pick it up). The tools were generalized for this: `tools/scaffold_chapter.py`, a template taken from Chapter 2 instead of a Wordle in the destination, fixed backdrops, rooms with no intro, rooms with no ball or lockup, work-area loops, merged and tiled loops, ping-pong, clipping masks.

**File 3 (Chapters 3, 4 + End) is built, approved by Demetre and pushed (2026-10-29): Rive file 2693093 "yig-ch3" (Games Year in Games project 1559255, 2026 folder), revision 49163061 "File 3 framework"; GitHub tag `rive/ch3-file-3-framework`.** `chapters/ch3`, manifest `chapter.json`: scenes `ad` (default: the empty Chapter 3 backdrop, lavender E1DBF5 wall and green 05CE7C floor, pixel-identical to File 2's `to-chapter-3` picture, 0 differing pixels; Ad 3 plays here), `chapter-3`, `chapter-4`, `end`; view model `scene`, `direction` and `topGame` (seven games, default `wordle`). The backdrop's colour poses are in the manifest (`backdrop: poses`): Chapter 3's for `ad` and `chapter-3`, one per top game for `chapter-4` (mustard FFBC45 floor; the wall is the game's), End's (DFF3F0 wall, orange FF811E floor, floor line 712); the scaffold writes them and the Backdrop layer. Rooms: **Chapter 3** is c3s1 (disco ball, picture, frames and mobile drop in at 1.00 s, 1.13 s and 1.27 s; the bird's 5 s loop; a stand-in ball in place of the 7 s journey); **Chapter 4** is the shared stack from c4s1_Wordle, with all five fireworks sets from the five artboards, each behind a gate that `topGame` switches (The Mini and The Midi show The Crossword's set and use their Chapter 2 wall colours, as placeholders), and a stand-in ball that hops up onto the yellow Spelling Bee block; **End** is c5s1 (dog, cat and bird loop, 5 s; no ball of its own). Intros are exactly 3.2 s. The top-game video is a card with no Rive copy: the stage holds Chapter 4 under it. Checks: `npm run check ch3` 462 pass; `back_test` 28 cases and `tap_test` 8 cases pass; the review page `/file3` (Top game menu) passes its browser test (23 checks). Loops against the illustrator (journey and balls taken out of both sides): End matches apart from a few anti-aliased dots; Chapter 3 differs only by the journey's opening pose (set on purpose); Chapter 4's Strands and Crossword sets match to within 6 px; Connections, Spelling Bee and Wordle differ near the end of the loop (recorded, with what is known of the cause, under "To tune later" in `docs/rooms-ch3.md`; not chased further, per Demetre). The tools gained colour poses read from a manifest (scaffold and checks), art and loops from several artboards, gates switched by an enum, stand-in balls that rest on a piece, Solo switch keys, and whole-turn rotations treated as closed.

**Chapter 2.5, the bridge card (approved by Demetre and pushed 2026-10-29: Rive file 2677803 "yig-ch2", revision 49171643 "Chapter 2.5 bridge").** The rule (`docs/experience.md`): only a player with exactly one qualifying game (10 or more completed puzzles) gets Chapter 2.5: after that game's cards, the bridge card in its own empty room, then a community card (lockup false, a normal room transition) for each other community game in the order Wordle, Connections, Spelling Bee, The Mini, Strands, leaving out the player's own; a Midi or Crossword player sees all five, and no room repeats. Two or more qualifying games: no 2.5, and the games under 10 don't appear in Chapter 2. Anons are unchanged. In File 2: the `bridge` scene, appended to the `Scene` enum (value id 1:9110, so every existing condition keeps its value), is an empty picture like `to-chapter-3`: a one-frame `Bridge Colors` pose (wall E7F1E1, floor FEA0C9, the opener's) reached from AnyState in the Backdrop layer over 1450 ms, power1.inOut, early exit. No room of its own, so the rooms' own `scene != n` exits pan the last room out. The integration's `NO_INTRO` set makes its copy arrive when the pan ends (1.65 s), even on a first visit; the card is `{ game: "bridge" }`. **Bridge Art** is a second artboard (after `Chapter 2`, since the tools read the first) holding the empty room, the floor line at 712 and Spelling Bee's ball at its room scale, with `includeInExport="false"`; `npm run check` requires that flag on any artboard after the main one. The CLI build has no tree-shaking, so `Bridge Art` is still written into the `.riv` (67 bytes when empty); `main` in `rive.yaml` keeps `Chapter 2` the one that plays. **Any engineering delivery must strip `Bridge Art` from the `.riv` they get** (Demetre, 2026-10-29): build the delivered file from a copy of `scene.rml` with that artboard removed, and check the result holds only `Chapter 2`. The harness has three example players (`?player=wordle-only`, `midi-only`, `several-games`). The new `experience.md` also notes that Chapter 1 and Chapter 3 cards can be skipped by threshold, which is HTML only and changes nothing in the Rive files.

**Handoffs are on hold** until Demetre says: no `npm run deliver`, zip or `rive/*-handoff-N` tag at the end of a stage. The next handoff includes Loading, Start and Chapter 1 together with Chapter 2. The one integration (Stage 3 onward) waits for engineering's answer on how they will drive the Rive files.

**Next:** the order of work below ("Order of work", from 2026-10-29). Still on hold until Demetre says: the next engineering handoff, which must include Loading, Start and Chapter 1 with Chapter 2, and must strip `Bridge Art` from the delivered `.riv`.

**For the engineering guide (collected as decided; Stage 3 of "Order of work" writes them up for engineering).**
- Start every file with the plural `stateMachines: "Backdrop"`; runtime 2.27.3 ignores the singular `stateMachine` and the file never moves (tested 2026-10-29). Their `RiveBackdrop.tsx` in draft PR #11222 already uses the plural.
- Set `direction` (and in File 2 `lockup`) before `scene`, on the same frame.
- **Copy timing.** A room's first visit: copy 3.2 s after the tap (its intro, with the lockup on a game's own first card). A room that comes back already built, or an empty room (the ads' rooms, `bridge`, the shared pictures): at the end of the pan, 1.65 s. Within a room: once the old copy has cleared, 0.34 s. **A community card** (Chapter 2.5 and the anon Chapter 2) has no lockup, so its copy arrives as soon as the room's intro settles, per room (2026-10-29, measured from each intro without its lockup, ball included; `communityCopyMs` in `chapters/ch2/chapter.json`, checked by `npm run check`): Wordle 3167 ms, Connections 2884, Strands 2050, Spelling Bee 2050, The Mini 2084 (The Midi and The Crossword 2050, though they have no community card today). Not one shared value: the five illustrator rooms settle within 0.04 s of each other, but in Wordle and Connections (our own intros) the ball keeps hopping into place until 3.17 s and 2.88 s. Games with a lockup keep 3.2 s.
- A Back during a pan, or a Next during a Back pan, waits for the pan to end.
- Files: switch on the shared empty pictures; keep earlier files loaded (and paused) so Back across files never reloads; load each next file ahead (`engineering/yig-integration.js` is the reference).
- Their `RiveBackdrop` sets an `intro` boolean if the view model has one, to play a scene's intro on its first visit. Our files have no such property: each room plays its intro on its first visit by itself and comes back already built.
- Their framing (`RiveBackground.module.scss`) is what our review page copies (`harness/yig-framing.css`): on phones the visible artboard is about x 517 to 978 (iPhone SE) or 558 to 937 (iPhone 15 Pro Max), and y 2 to 823, so the floor below y 823 is cut.
- The delivered `chapter-2.riv` has `Bridge Art` stripped.

**Things a new session should know without asking**
- Commit straight to `main` (repo-depot exception), adding only the files changed, never `git add -A`. Never force-push. Pushes to GitHub and to Rive happen only when Demetre asks.
- The Rive CLI is signed in as lindsey.liang on purpose.
- The illustrator's file (Rive file 2668591) is a read-only copy in `.cache/illustrator/` (git ignores it; `tools/import_room.py` pulls it again if missing). Never push to or edit it. `.cache/view/` holds throwaway copies for rendering.
- `tools/import_room.py` refuses a room that is already in the chapter. To redo one: `git checkout -- chapters/ch2/scene.rml`, then import the rooms again, in scene order, so the ids stay the same.
- Floor line 712 everywhere. Icon sizes for Strands and Spelling Bee stay as drawn until he says to match them.
- Leave the `/tmp/yig-*` scratch folders alone and do not ask about them. Skip screenshot contact sheets: he reviews in the harness and the viewers.
- To avoid permission prompts: call the Rive CLI by its full path (`/Users/demetrearges/.rive/bin/rive`, not `$R`), keep commands simple (no long chains, no `rm -rf` mixed in), and note `.claude/settings.json` at the repo-depot root holds a read-only allowlist.

## For the illustrator

A short list Demetre can send as-is. Three loops in the source file (file 2668591) don't return to their start pose, so we added a return ourselves; it would be better fixed at the source, in the original rig. Detail and exact numbers are in "Fixes to the illustrator's art" below.

1. **The Mini (c2s5):** the ball's loop ends 86 units off in x and 135 in y from where it starts.
2. **The Midi (c2s6):** the ball moves through two linked nodes, and neither returns to its start: one ends 205.5 / 22 off, the other 175.5 / 104.5 off. In the room the ball ends up 30 right of and 126 below where it started.
3. **The Crossword (c2s7):** the ball ends 141 units off in x and 54 in y; a piece ("Group 2") fades in partway through and never fades back out.
4. **Chapter 1 (c1s2, c1s3, c1s5):** c1s2's ball ends 94 / 190 units from its start after 240 frames and its `Circle_F` fades out and never back; c1s3's ball ends 2.3 units off and one vertex does not close; c1s5's ball ends 257 units off in x (it also jumps inside the loop at frames 60 and 90, so please say if that is meant). Their `Ball` animations are 300 or 180 frames long but play only a work area (240, 180, 180), which is what we copied.
5. **c1s1:** `Dog_Eye` plays once and does not return to its first shape.

## Decisions

- Both flows (subscriber/registered and anonymous) ship as the same files. Only the card list and the HTML copy differ.
- **Floor line is 712 in every file.** The illustrator's Floor groups sit at 710.5 (Chapters 1–3), 711 (Chapter 4) and 740 (End), but the drawn line is at 712 on every artboard (the group's children are offset), so nothing needs moving; the shared backdrop draws it at 712.
- **One integration file for the whole experience**, not one per Rive file (see "The integration").
- **Ads and the top-game video are cards.** When an ad or the video finishes, engineering calls `onTap()` like any other tap.
- **Rooms come in as an RML copy, not as nested components** (decided after the Spelling Bee test, see below).
- **A room's loop is the illustrator's loop, copied exactly:** the same keyframes, timing, easing, positions and pivots for every piece, ball included. Nothing is reinterpreted. The only change allowed is where a loop does not close: that property's last key is set to its first, as small a change as possible, and it is added to "Fixes to the illustrator's art". The intro is the only new motion we design.
- **The illustrator's ball rig does not come in.** No joystick, no `Ball_Move` solo, no `Ball_Squash` or `Ball_Scale` helper animations. Each room's ball is plain ball art. What the rig produced is baked into direct keys, sampled from the joystick's own keys and the rig animations (values the rig held still are set on the art; values that move get one key per frame, thinned only where a straight line is exact), so the ball moves the same. The ball's position keys, and every other piece's keys, are copied from the source untouched.
- **Fix the loops that don't close ourselves**, after a quick look at each in the Editor. Every fix is listed under "Fixes to the illustrator's art" so the illustrator can match their source.
- **Rive CLI login:** it runs as lindsey.liang on purpose. Push under it as normal.
- Art source: the illustrator's Rive file (file 2668591, Team folder). Never edit or push to it. A read-only copy is pulled into `/tmp` when needed.

## The files

| File | Scenes | Starts on | Ends on |
|---|---|---|---|
| 1 · Start + Chapter 1 | Loading, Start, Ad 1, Chapter 1 (five rooms, one per card, c1s1–c1s5), Ad 2 | Loading | empty Chapter 1 room (cream F1ECC0 wall, orange FF811E floor) |
| 2 · Chapter 2 | Opens on the empty Chapter 1 room and pans into the opener (floor changes orange to pink), then the player's games and community cards, then an empty Chapter 3 backdrop | empty Chapter 1 room | empty Chapter 3 backdrop (lavender E1DBF5 wall, green 05CE7C floor) |
| 3 · Chapters 3, 4 + End | Ad 3 (anons), Chapter 3, Chapter 4 (seven top-game versions chosen by `topGame`), the top-game video (a card), End | empty Chapter 3 backdrop | End loop on the orange floor |
| how-to-mobile.riv | one artboard, "Mobile" (mobile only; desktop uses arrow buttons in the page) | | |

- **Start** shares Chapter 1's room and moves into it in one continuous motion (c0 is c1s1 without the clock and window).
- **An ad** is one more scene: the props leave, the wall and floor stay. An ad is a card; engineering's ad finishes and they call `onTap()`.
- **Chapter 1** is five rooms that pan on the same colors, one per card.
- **The handoff rule:** every file starts and ends on an empty backdrop, and both files show the same picture at a handoff (same wall color, floor color, floor line at 712, no ball), so the file swap is invisible.
- **How-to overlay:** one file, `how-to-mobile.riv`, for mobile only (state machine and view model `Backdrop`, like every file). Engineering shows it over the stage below the mobile breakpoint; the idle timer is on their side. Desktop has no How-to file: arrow buttons at the window's left and right edges do Back and Next.

## Names and properties (engineering's requests, done in Foundation)

- Every file's state machine and view model are both named `Backdrop`. The artboard keeps a name per file (`Chapter 2`).
- `scene` and `direction` are enums. `direction`: `forward`, `back`. `scene`, Chapter 2: `intro` (the opener), `wordle`, `connections`, `strands`, `spelling-bee`, `mini`, `midi`, `daily` (The Crossword), plus two internal pictures, `from-chapter-1` (the file's default) and `to-chapter-3`. The other files' names are in each `chapters/<ch>/chapter.json`.
- `community` is now `lockup`, and the meaning flips: `lockup = true` shows a game's lockup (default true); a community card or anon slide sets it to false. The card tag in engineering's list stays `community: true`.
- Each manifest marks which properties engineering may set if they ever drive Rive directly (`scene`, `direction`, `lockup`, `topGame`) and which only our integration sets (`through`, and the internal picture scenes). The engineering README says the same.
- Conditions compare a scene by its value id, so the order of values in the enum is the value Rive stores. `tools/migrate_to_enums.py` did the Chapter 2 conversion once; it is history, like `import_room.py`.

## The integration

Engineering builds one card list for the whole experience. Each card is tagged with what it shows:

```js
{ game: "opener" } { game: "wordle" } { game: "connections", community: true }
{ ad: 1 }  { chapter1: 3 }  { topGame: "wordle" }  { video: true }  { game: "end" }
```

They call `start(cards)`, `onTap()` and `onBack()`, exactly as today. The integration works out which Rive file each card belongs to, loads the next file in the background, and swaps files on the handoff frame itself.

How it fits with the Chapter 2 handoff they already have:

- `engineering/chapter-2-integration.js` stays as it is and keeps working. The new integration (`engineering/yig-integration.js`) exports the same three calls plus the same `setScene` and `yig`, and takes over the logic in `chapter-2-integration.js` for File 2, so Chapter 2's `game` names, `community`, `BUILT` set, pan hold, intro waits and copy timing carry over unchanged.
- Cards that were `{ game: "wordle" }` today still mean the same thing. New tags are added, none renamed. A card with no file tag is treated as Chapter 2, so today's card lists keep working.
- The text CSS, `data-copy-frame` and `data-icon-game` markup stay as they are.
- Ad and video cards have no Rive copy. The integration shows nothing for them and tells engineering's code nothing except what the card is; engineering owns the ad and the video.

How a swap works:

1. While a file is on screen, the integration loads the next file into a second, hidden canvas with autoplay paused on its first picture.
2. On the tap that crosses a file boundary, it shows the second canvas and hides the first on one frame. Because both show the same picture, nothing visible changes. Then it sets the new file's `scene`, so the pan or intro starts from the shared picture.
3. Back across a boundary is the mirror: the pan back finishes inside the later file (back to the empty room), then the integration swaps to the earlier file already set to its last scene. A Back during a pan waits for the pan, as today.
4. The old canvas is cleaned up (`cleanup()`) after the swap.

What this makes harder than three separate files, honestly:

- Memory and loading: two Rive instances are alive around each handoff, and the next file has to be loaded in time. A slow connection could reach the handoff before the next file has loaded; the integration needs a rule for that (hold the tap and show the current empty room until it is ready).
- Back across a boundary needs the earlier file reloaded at its last scene, which is the one case where we load a file twice.
- One module to test instead of three small ones, with a bigger card-to-file table. It is more logic in our code and less in engineering's, which matches their priority.
- If a file fails to load, the integration has to fail in one place; with separate files each failure is local.
- None of this is a blocker. The cost is mostly the preload/swap code and its tests, written once.

## The art

The illustrator's file has 22 artboards, none exporting. Every room carries its own wall and floor shapes (removed on the way in) and the shared ball rig (not brought in). Findings on timing, measured from keyframes:

| Artboard | What it is | Wall / floor | Motion | Fits our rules? |
|---|---|---|---|---|
| NYT_YIG_c0 | Start | F1ECC0 / FF811E | Ball_Loop 1 s loop (the floor ball at x 623, scale 2.0, start = end); Loop 5 s loop (dog); Dog_Eye 5 s one-shot that closes | Loop fine. Needs a 3.2 s intro. Not simply "c1s1 without clock and window": the chair is 300 units further left than in c1s1. Leftover c1s1 animations to ignore. |
| c1s1 | Ch1 card 1 | F1ECC0 / FF811E | Ball 7 s one-shot (out of the clock, across the window, into the mouse hole; motion ends at about 5 s, no joystick rig); Loop 5 s loop (dog); Pendulum plays only a 1 s swing each way (work area 9 to 69); Dog_Eye 5 s one-shot that does not close | The dog loop and pendulum close. The ball story does not loop (framework: the ball rests; decide when tuning). Dog_Eye ends on another eye shape. Hidden full-frame still to delete (also keyed). |
| c1s2 | Ch1 card 2 | same | Ball: 300 frames with the work area 0 to 240 enabled, so it loops 4 s | No: ball ends 94 and 190 units from where it starts, and `Circle_F` fades out at frame 140 and never back. |
| c1s3 | Ch1 card 3 | same | Ball: work area 0 to 180, so it loops 3 s | Nearly: ball 2.3 units off, and one vertex (`a`, y 5.07 to 0.36) does not close; a joystick key sits past the end. |
| c1s4 | Ch1 card 4 | same | Ball: work area 0 to 180, so it loops 3 s | Yes. Hidden tracing image to delete. |
| c1s5 | Ch1 card 5 | same | Ball 3 s loop (180 frames) | x ends 257 units away, but the ball also teleports inside the loop (x 877 to 745 at frames 60 to 61, 618 to 876 at 90 to 91), so the gap may be intended; look in the Editor before fixing. Tracing image visible at 19%. |
| c2s1 | Ch2 opener (shelves, trophies, door, cat tree) | E7F1E1 / FEA0C9 | c2s1_Loop 7 s loop (closes) | Looks like a fuller version of our Shelf room. Leftover `c2-wordle 2` node. |
| c2s2 | Wordle | C3E2C0 / FEA0C9 | Ball 3 s loop | No: 35 and 58 units off. |
| c2s3 | Connections | E1DBF5 / FEA0C9 | Ball 3 s loop | Nearly: 1 unit. |
| c1s8 | Strands (misnamed; its state machine is "c2s8") | DFF3F0 / FEA0C9 | Ball 3 s loop | Yes. |
| c2s4 | Spelling Bee | FFFDEF / FEA0C9 | Ball 4 s loop | Yes (1 unit). |
| c2s5 | The Mini | 95BEFA / FEA0C9 | Ball 2.5 s loop | No: 86 and 135 units off. |
| c2s6 | The Midi | 7EAAF1 / FEA0C9 | Ball 2.5 s loop | No: 175 and 104 units off. |
| c2s7 | The Crossword | 6493E6 / FEA0C9 | Ball 3 s loop (keys radius and opacity) | Needs a look in the Editor. |
| c3s1 | Chapter 3 | E1DBF5 / 05CE7C | Loop 300 frames (the bird) set to one-shot; Ball 7 s one-shot (starts in the picture frame, ring, crib, mobile, disco ball, ends on the front floor) | Loop closes, it only needs to be set to loop. The ball journey does not loop (framework: it rests). |
| c4s1 × 5 | Chapter 4 (Strands, SpellineBee, Connections, Crossword, Wordle) | DFF3F0, FFFDEF, E1DBF5, C0D8F8, C3E2C0 / FFBC45 | Fireworks 5 s loops; Ball 7 s one-shot (hops across the stack, ends scaled 5.2x in the front right) | Same stack and same ball keys in all five. Every firework is invisible at both ends of its loop, so the wrap is clean. Only wall colour, the fireworks group and their timing differ. |
| c5s1 | End | DFF3F0 / FF811E | Loop 5 s loop (closes) | The Floor group sits at 740 but the drawn line is at 712: nothing to move. The floor is orange FF811E (confirmed; the illustrator's End.png shows yellow, so ignore it). |

None of the rooms has an intro, a pan or 3.2 s timing; we add those ourselves.

**Chapter 4 is mostly one room.** All five versions hold the same stack of every game's pieces plus the ball. Only the wall color, the fireworks group and the fireworks timing change. So `topGame` picks a wall color and a fireworks set over one shared stack. The stack is built once.

## How scenes come in

Copy each room in as RML with a small script (`tools/import_room.py`) that reads the read-only pulled copy and writes the room's art into a `<Room>` group in our file. It gives every node a fresh id, copies the SVG and image assets the room uses, and leaves out the room's wall, floor, reference images and ball rig. Then the room is plain RML like Wordle, and our checks, Waiting poses, wall lag, draw rules and Lockup Gates all work on it. Nesting scene artboards as components is not used: our parent timelines can't key inside a nested artboard, a nested artboard clips to its own frame (cutting off pieces that start outside it and the ball rolling in from beyond the left edge), and draw rules target Shapes, not nested artboards. The Editor import is kept for art that exists only as SVG (the missing lockups).

The ball in each room is rebuilt as plain ball art, the way Wordle and Connections do it, with its squash, scale and movement keyed in the room's intro and loop, using the illustrator's ball motion for timing and shape.

## What's missing

From the illustrator:
1. Chapter 4 has no Mini or Midi version. Because the stack is shared, each needs a fireworks set and a wall color (95BEFA and 7EAAF1 from Chapter 2 as a start).
2. Loading has no art.
3. The mobile How-to overlay has no art (there is no desktop How-to: desktop uses arrow buttons).
4. Lockups for Strands, Spelling Bee, The Mini, The Midi and The Crossword (all seven are done, in `art/ch2/originals/`).
5. No intros anywhere. For each new room I propose an intro in the style of Wordle and Connections (pieces arriving and settling, exactly 3.2 s) for Demetre to approve or adjust in the harness.
6. Loops that don't close (list below).

On our side:
7. Floor line to 712 everywhere.
8. Ad and Loading scenes in File 1; the Chapter 2 ending (empty Chapter 3 backdrop) and how engineering knows to swap to File 3 (the integration decides it from the card list).
9. `topGame` and the video card in File 3.
10. The tools (`check_chapter.py`, `check.py`, `deliver.py`) assume the Chapter 2 artboard and names. They need to take each file's artboard and room list.
11. Chapter 2 opener: before swapping our Shelf art for c2s1, show both side by side in the harness for Demetre to choose.

## Fixes to the illustrator's art

Each fix is made in our copy only, after a quick look in the Editor, and recorded here so the illustrator can match their source if they want.

| Artboard | Problem | Fix we made | Status |
|---|---|---|---|
| c1s2 | ball loop ends 94 / 190 units from its start; `Circle_F` fades out at frame 140 and never back; the loop is the work area (240 frames, the animation is 300) | ball x/y and `Circle_F` opacity return to their first values over frames 180 to 239 | done |
| c1s3 | ball loop 2.3 units off; one vertex does not close; a joystick key sits past the end of the work area (180 frames) | ball x/y last keys set to the first; the vertex y returns over frames 125 to 179; the joystick is sampled, so its late key still shapes the ball | done |
| c1s5 | ball loop x ends 257 units away (the ball also jumps inside the loop at frames 60 to 61 and 90 to 91, and again where the loop wraps); tracing image visible | the jump is the illustrator's design, so it is left exactly as made, with no return (Demetre, 2026-10-29): the loop does not start and end on one pose for this one property, and `chapters/ch1/chapter.json` allows it under `openLoops`; the tracing image is never imported | done, listed under "To tune later" |
| c2s2 (Wordle) | ball loop 35 / 58 units off | to do | to do |
| c2s3 (Connections) | ball loop 1 unit off | to do | to do |
| c2s5 (Mini) | ball loop 86 / 135 units off | to do | to do |
| c2s6 (Midi) | ball loop 175 / 104 units off | to do | to do |
| c2s7 (Crossword) | check ball loop | to do | to do |
| c3s1 | `Loop` (the bird) is set to one-shot, and closes (one eye-handle rotation ends a whole turn from its start, the same angle); the 7 s ball journey cannot loop | played as a 5 s loop; the journey is not brought in: a stand-in ball rests where it ends (x 1030, y 729) and hops in place; the journey's opening pose is set on the art | done, listed under "To tune later" in `docs/rooms-ch3.md` |
| c4s1 ×5 | the fireworks' pieces end their loops at a different size or point than they start, while every burst is invisible (scale 0 or opacity 0 at both ends); one Wordle pane switch (a Solo) never switches back | each piece returns to its start over the last frames of the 5 s loop, where nothing shows; the switch switches back on the last frame; the five sets come from five artboards, one gate each, chosen by `topGame` | done |
| c1s8 | misnamed (is Strands), state machine "c2s8" | renamed | to do |
| c4s1_SpellineBee | name typo | renamed | to do |
| c2s4 (Spelling Bee) | Ball_Move y: last key (frame 236) is 755, first is 756 | last key set to 756 | done in Chapter 2 |
| c1s8 (Strands) | none: the loop closes | none | done |
| c2s5 (The Mini) | Ball_Move x ends 86 units from where it starts (last key frame 91), y 135 (last key frame 129) | the ball's keys are untouched; x and y return to their first values over frames 129 to 149 (the tail that was held) | done |
| c2s6 (The Midi) | the ball moves through two nodes and neither closes: Ball_01 x/y end 205.5 / 22 from their start (last key frame 97), Ball_Move x/y 175.5 / 104.5 (frame 142). In the world the ball ends 30 right of and 126 below where it starts | all four return to their first values over frames 129 to 149 (eased); Ball_Move's last keys at frames 132 and 142 are replaced by a hold to 129 | done |
| c2s7 (The Crossword) | Ball_01 y ends 54 from its start (last key frame 158), Ball_01 x 141 (frame 129), and the Group 2 piece fades in at frame 129 and never fades out | the ball's keys and the fade-in are untouched; all three return to their first values over frames 158 to 179 (the group fades out) | done |
| c1s1, c1s4, c1s5 | reference images | never imported (the importer skips images) | done |
| c1s1 | `Dog_Eye` is a one-shot that does not close (3 vertex properties end 8.3, 3.1 and 3.1 from their start); the ball story (7 s, ends in the mouse hole) cannot loop | the eye plays at the start of the 10 s loop and returns to its first shape over frames 300 to 599; the story is not brought in: a stand-in ball (plain art, same look as the other Chapter 1 balls) rolls in during the intro, rests at x 1000 and hops in place twice in the loop (2 s and 7 s); the panes and the clock show how the story opens; Demetre will fit the story in during finesse | done, listed under "To tune later" |
| c1s1 | a clip on the clock's inactive second ball masks a shape in the mouse hole | left out (that ball never shows without the story) | done |
| c0 (Start) | the dog's loop (300 frames), the floor ball's hop (`Ball_Loop`, 60 frames) and the eye (`Dog_Eye`, a one-shot that closes) are three animations | merged into one 300 frame loop: the hop repeated 5 times, the others once; every key is the illustrator's | done |
| Loading | no art | a placeholder: a red ball hopping in place (`tools/placeholders/loading.rml`), no intro | placeholder |
| c1s8 (Strands) | a hidden bit in the left strand's group; the unused Ball_02 variant; the source's own floor stroke key | left out | done |
| c2s4 (Spelling Bee) | hidden second child in each mug group; unused Ball_02 variant; the joystick, Ball_Move solo and Ball_Squash / Ball_Scale helper animations | left out (the rig is baked) | done |
| c5s1 | Floor group at 740; the drawn line is 712; its state machine is named `c1s1` | none needed | n/a |

## Stage 1 result: Spelling Bee as an RML copy

Spelling Bee was built both ways in a scratch copy and tested against Wordle. Both built clean, played the same intro frame for frame, passed all 56 Next/Back/mid-pan tap cases with Wordle and Connections, passed the tap-out and draw-order checks, rendered identically (0 differing pixels) during pans, and played without console errors in the web runtime. Demetre picked the RML copy. The reasons:

- The rule checks (`npm run check`) read only the main artboard. In the component version the room's intro, Waiting pose and loop rules were not checked at all, so the tools would need reworking.
- The component needs a second view model, a component entry, a stateful instance bound to `scene`, and a `NestedStateMachine` child. Leaving out that last one built clean and did nothing, silently.
- Its one advantage, editing the art in its own artboard in the Editor, matters less than checked, plain RML that works with every tool we have.
- The component clips to its own 1495-wide frame. Nothing in Spelling Bee overhangs, so it did not show, but art that does would be cut.

## Importing a room

`tools/import_room.py tools/rooms/<room>.json` brings a room in; `tools/svg_to_rml.py` converts the lockup SVGs. Both have tests (`python3 -m unittest discover -s tools/tests`). The importer edits `scene.rml` by adding text only, prints every loop fix, and prints any art that overhangs the 1495-wide frame. The intro is designed in the room's config.

Spelling Bee's loop was checked against the illustrator's c2s4 on all 239 frames: frames 1 to 212 match to within 1 to 2 colour levels of anti-aliasing; frames 213 to 239 differ only by the ball sitting up to 1 px higher, which is the one closing fix. A scrubbable side-by-side is in `deliver/compare/spelling-bee/index.html` (not in git).

What still differs from c2s4, by design: our shared backdrop draws the floor line (2 px, same dark as every room) where the source has its own softer line; the source artboard has rounded corners; the source's frame 0 shown by the CLI is its authored pose, not a loop frame.

## The other four rooms

Strands, The Mini, The Midi and The Crossword were brought in together with `tools/import_room.py` (configs in `tools/rooms/`). Each loop is the illustrator's, copied key for key; the ball rig is baked. Nothing overhangs the 1495 x 1067 frame in any room, and the ball's path stays inside it. Each room is checked against the illustrator's artboard on every loop frame with `tools/compare_room.py`; the viewers are in `deliver/compare/` (not in git). Proposed intros, all exactly 3.2 s, in Spelling Bee's style (the floor pans in 0.05 to 1.55 s carrying the pieces on it, pieces that float drop in and settle with a small squash, the ball rolls in along the floor from the left and lands in the loop's first pose, the lockup plays as Wordle's does):

- **Strands:** the shoes ride the floor in; the blue strand drops at 1.00 s (lands 1.50) and the yellow strand with its base bar at 1.15 s (lands 1.65); the ball rolls in from 1.15 s and hops up onto the yellow strand's top.
- **The Mini:** the big cube rides the floor in; the cubes drop one after another: the lower left cube at 1.00 s (lands 1.50), the lower right at 1.13 s, then the two top pieces together at 1.27 s (lands 1.77); the ball rolls in along the front of the floor.
- **The Midi:** the long base rides the floor in; the doors drop at 1.00 s (lands 1.50) and the upper boxes at 1.13 s (lands 1.63); the ball rolls in and hops up to the loop's first pose.
- **The Crossword:** the base with its small cubes rides the floor in; the doors drop at 1.00 s (lands 1.50) and the front boxes at 1.13 s (lands 1.63); the ball rolls in and hops up to the loop's first pose.

The Mini, The Midi and The Crossword have loops that do not close (see the fix list). In each, every key the illustrator set is untouched and the ball (and in the Crossword, the Group 2 fade-in) returns to where it started over the last frames of the loop. The illustrator may want to look at those three.

Strands needs one more thing. In the illustrator's file the Floor is listed above the ball and above most of the pieces, so the ball sinks behind the floor and is cut off at the floor line. Our floor is the shared backdrop at the bottom, so the importer clips everything the source draws under the floor to the area above the floor line (a clip rectangle in the room, `Strands Floor Clip`). With it, Strands matches the source on every frame; without it the ball showed over the floor.

The closing rule, as built: a gap up to 2 px (0.02 for rotation, scale and opacity) is closed by setting the property's last key to its first; a wider gap keeps every key and adds a return, with all returns in a room starting on the same frame, the latest last key among them. **Refined 2026-10-29, for rooms imported from then on (File 3):** a last key that sits exactly on the wrap frame (the frame the loop jumps back to 0 from, which is never shown) no longer has its value replaced, because that flattened the whole segment leading to it (Chapter 4's Connections and Spelling Bee fireworks stopped turning over their last 50 frames). Instead the last shown frame gets a key holding the value the illustrator's keys give it, and the loop closes only in the unseen step to the wrap frame, so every shown frame is the illustrator's. This applies when the segment into the wrap key is linear or held; otherwise the old rule is used and noted. A rotation that ends a whole number of turns from its start is the same angle and counts as closed. Rooms already in (Chapter 2, File 1) were not re-imported: **File 1's card 3** was closed with the old rule (its ball's last key, on wrap frame 180, was moved 2.3 px), so its last segment differs from the illustrator's by up to 2.3 px. Demetre is leaving it as is and will handle it in the finesse round (2026-10-29).

## Lockups

All seven lockups are in `art/ch2/originals/` (`*-lockup.svg`, 175 x 128). They are plain filled paths and are converted to Rive shapes exactly, icon and word as separate nodes, placed in the same frame as Wordle's: the SVG point (87.5, 66.275) sits at the lockup's Art node, so the same frame placement means the same position in every room. Each is wired and timed like Wordle's (in from frame 115, gone at frame 192 / 3.2 s, hidden on community cards).

- The new Wordle and Connections SVGs match the lockups already in Rive: every shape's bounding box is within 0.001 units, fills are identical, and the only difference from the previously committed SVGs is rounding of 0.001. Two Connections shapes have one vertex fewer (the Editor kept a duplicated closing vertex). Nothing needs swapping.
- Consistency across the seven, in the room: icon bottoms are within 0.2 px (398.3 to 398.5), word baselines within 0.7 px (437.1 to 437.7), word centres within 0.34 px of 748. Icon sizes differ: five icons are 70.8 x 70.8, Strands is 77.1 x 80.8 and Spelling Bee 76.7 x 75.8 (their art extends upward from the same bottom line). Spelling Bee's icon centre is 0.9 px left of 748.

## Order of work

Each stage ends with `npm run check`, a screenshot, a push with `--name`, and a git commit. Stages that change what's on screen end with a list of exactly what to look at in the harness.

**Stage 0: Plan in the repo.** This file, the CLAUDE.md Status section and the login line. Commit.

**Stage 1: Spelling Bee comparison (done)** (scratch copy only, never committed, no Rive file link). Bring c2s4 into a copy of Chapter 2 as scene 4, once as a nested component and once as an RML copy with the ball rebuilt directly, and show both in the harness. It passes if it does everything Wordle does: pans in and out with the same 1280 / 1600 travel, ball keeps looping while leaving, loop starts and ends on one pose, 3.2 s intro, arrives already built on return, Back is the mirror, backdrop crossfades to FFFDEF, nothing clipped, `npm run check` passes. Stop for Demetre's pick.
- *By hand:* look at both in the harness and pick one.

**Stage 2: Finish Chapter 2 (File 2) (done).** Rooms one at a time, in this order: Spelling Bee, Strands, The Mini, The Midi, The Crossword. For each: import with `tools/import_room.py`, copy the illustrator's loop exactly, add its lockup, propose a 3.2 s intro in Spelling Bee's style, report art that overhangs the frame, run the checks, show the side-by-side with the illustrator's version and the room in the harness, and stop for review. The Chapter 2 ending and the opener swap come later. Bring in Strands, Spelling Bee, The Mini, The Midi and The Crossword with layers, intro, Waiting pose, loop fixes and lockup. Opener choice (side by side). Open on the empty Chapter 1 room and pan into the opener. Add the ending into the empty Chapter 3 backdrop. Update the README and handoff.
- *By hand:* import the five missing lockup SVGs in the Editor (I `rive pull`). Approve intro motion and the opener choice.

**Stage 3: File 1, Start + Chapter 1.** Generalize the tools. Loading, Start into Chapter 1 in one continuous motion, five rooms, Ad 1 and Ad 2 as empty-room scenes, ending on the empty Chapter 1 room.
- *By hand:* create the empty Rive file in the Team folder and send me its id. Import Loading art when it exists.

**Stage 4: File 3, Chapters 3, 4 + End.** Opens on the empty Chapter 3 backdrop (Ad 3). Chapter 3 as one room with HTML badges. Chapter 4 with `topGame`. End at 712.
- *By hand:* create the empty Rive file, send me its id. Import Mini and Midi fireworks when they arrive.

**From here (decided 2026-10-29; replaces the old Stages 5 and 6).** Stages 0 to 4 above are done. The work now goes in this order, with a review stop after each:

1. **The full experience in one harness page.** Every chapter, Loading through End, in both flows (subscriber/registered and anon), switching between the three Rive files on the empty rooms, with Back working across them. Ads and the video are placeholder cards. Framed exactly like engineering's staging page (their scale and crop of the Rive animation, from `RiveBackground.tsx` and `RiveBackground.module.scss` in `nytimes/games-phoenix`), with their values kept in one place. A screen-size switch (iPhone SE 375 x 667, iPhone 15 Pro Max 430 x 932, iPad portrait 820 x 1180, desktop 1440 x 900) and a page that also follows the real window width. Desktop arrow buttons (`art/global/ui-desktop-button.svg`, mirrored for Back), 20 px in from the window's left and right edges, centred vertically, over the animation and the copy; hidden below the mobile breakpoint, where tapping the left or right half does Back and Next. The arrows live in the harness only, never in the Rive files. `engineering/chapter-2-integration.js` grows into the reference for driving all three files.
2. **Finesse, room by room.**
3. **The engineering guide and React example.** `docs/engineering-guide.md` and a React + TypeScript example in engineering's style; the package README template in `tools/deliver.py` fixed (no internal version numbers, "completed puzzles", no git references); the delivered `.riv` has `Bridge Art` stripped.
4. **The How-to file, mobile only** (`how-to-mobile.riv`, placeholder art until Demetre's arrives; created by its first push, after he says, then moved by him into the 2026 folder).

## Verification

- Every stage: `npm run check` (verify; intros exactly 3.2 s; loops start and end on one pose; Waiting pose equals intro's first keys; everything clears the artboard).
- At each handoff: render the last frame of one file and the first frame of the next; they match exactly.
- Motion and feel are reviewed by Demetre in the harness.
