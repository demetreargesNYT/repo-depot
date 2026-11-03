# Year in Games 2026: Rive plan for the whole experience

## Start here

**What this is.** The Rive animation behind NYT Games' Year in Games 2026 recap ("Well Played"): three Rive files (`chapters/ch1`, `ch2`, `ch3`) that play back to back behind HTML slides, for subscribers and anonymous players alike. Design lead: Demetre Arges. Engineering drives the files from their own React code, using `docs/engineering-guide.md`.

**Read, in this order:** `CLAUDE.md` (the rules and how we work), this file, `docs/experience.md` (the product picture: both flows, the card rules), `docs/rooms.md` (Chapter 2), `docs/rooms-ch1.md`, `docs/rooms-ch3.md` (plain-words sheets of every room, each with its "To tune later" items), and `docs/engineering-guide.md` (what engineering gets; final, don't edit it without being asked).

**Test tiers** (the same as `CLAUDE.md`; every one stops at the first failure and names the piece, the reason and its log in `test-logs/`):

| Tier | Command | Covers | Takes |
|---|---|---|---|
| After a finesse change | `npm run finesse <ch> "<room>"` | The rule checks for that chapter, the room's ball physics and jitter check (`tools/ball_speed.py --contacts`, with the flags accepted on purpose in `tools/ball_speed_accepted.json`), and the `/experience` address that opens on the room with the Finesse panel on. No renders, no smoke. | about 2.5 s (2.5 s measured for Chapter 1 card 4) |
| Before a delivery | `npm run smoke` | The rule checks for all three files, the unit tests, the Chapter 2 page's text timing in its short form, and the experience harness for one subscriber player and the anonymous flow on phone. It runs only when the reference code, the harness, the guide or the runner changed since its last pass, says why it ran or skipped, and skips a chapter's own pieces when that chapter is unchanged (`-- --all` forces everything). | about 12 minutes (11 min 35 s measured with the chapter pieces skipped; about 2 minutes more when they run) |
| When Demetre asks, or a delivery changes Rive files | `npm run suite` | Everything, in short pieces one at a time: rule checks, unit tests, tap and back for each file, the full text test, the experience harness (subscriber and anon, phone and desktop), the Finesse panel, and the package demo for every example player. A chapter's pieces are skipped while it is unchanged since they last passed (`-- --all` forces everything). | about 1 hour (58 min measured before the Finesse piece was added) |

**Standing rules.**

- No Rive push, no engineering handoff and no `git push` without Demetre's approval. Never force-push. Commit straight to `main` (repo-depot exception), adding only the files you changed.
- Never edit or push to the illustrator's file (Rive file 2668591; a read-only copy in `.cache/illustrator/`) or to the YIG Test copy (Rive file 2666044; `.cache/yig-test/`). Both are only art and history now.
- **What is in Rive now is the current version of every room.** There is no "illustrator's version" to match: any change you make becomes the newest version. Room-by-room calls (how the ball enters, whether it squashes, a full journey or a hop, where a loop starts) are made during finesse and need not be the same on every card.
- **Animations keep running while a room pans out on Next and pans in on Back.** Nothing freezes mid-motion. Any exception is a one-off, listed with its room (none yet).
- The scene loop guideline in `CLAUDE.md` stays as the intent; the Rive CLI is signed in as lindsey.liang on purpose.

**Next:** the finesse round goes on in the Finesse order. Start and Chapter 1 cards 1 to 4 have been through it; **card 5 (with Wordle Bot) is next, then Chapter 2 onward.**

## Status (2026-11-03)

- **The latest engineering package is the 2026-11-03 delivery, "Chapter 1 polish, startScene"** (`deliver/yig-engineering-package.zip`, built with `python3 tools/package_engineering.py`; the first package was commit `158faed`). It goes to engineering from Demetre. Nothing is sent without him.
- **Done:** the engineering guide and React example; the test cleanup (the three tiers, one entry point `window.__yigTest` for the Chapter 2 page's text test); the Finesse panel on `/experience`; the global pass; the finesse round for Start and Chapter 1 cards 1 to 4; `startScene` in all three files.
- **Latest Rive revisions** (all pushed 2026-11-03 as "Chapter 1 polish, startScene", tags `rive/ch1-chapter-1-polish-startscene`, `rive/ch2-chapter-1-polish-startscene`, `rive/ch3-chapter-1-polish-startscene`; the push before it, 2026-11-02, is tagged `rive/chN-ads-once-polish`). Before the push all three were pulled into a scratch copy and compared with their last push: no Editor edits.

| File | Rive file | Revision |
|---|---|---|
| File 1 · `chapters/ch1` · "yig-ch1" | 2692475 | 49418454 |
| File 2 · `chapters/ch2` · "yig-ch2" | 2677803 | 49418480 |
| File 3 · `chapters/ch3` · "yig-ch3" | 2693093 | 49418501 |

- **Next:** Chapter 1 card 5 (with Wordle Bot), then Chapter 2 onward, in the Finesse order. Then the mobile How-to file (`how-to-mobile.riv`, placeholder art until Demetre's arrives).

## Changes since the last delivery

The last delivery went out on 2026-11-03 (below). Keep this list current; the next note to engineering is made from it. Add a line whenever something changes that engineering would notice, in the code (the card list, the guide) or in the Rive files.

- **The engineering guide was slimmed and renumbered** (2026-11-03; `docs/engineering-guide.md`, the text Demetre reviewed; no rule, timing, property or Rive file changed). Its structure: What's new, The rules (16 numbered rules), then sections 1 Starting a file, 2 Properties, 3 Scenes, 4 Loading and Start, 5 Card list, 6 When the copy appears, 7 Files, ads and Back, 8 startScene, 9 Controls, text CSS and the reference folder, and the Checklist. Section numbers quoted in the notes below are the new ones. The package README points to "The rules" first, then "What's new in this delivery".
- **A visual timing demo, `reference/timing-demo.html`** (2026-11-03; source `engineering/timing-demo.html`, copied into the package by `tools/package_engineering.py`; no Rive change, nothing in `core/` or the guide changed). It opens with a double-click, links the real `core/yig-text-motion.css` and plays the card strip for the subscriber (several games or one game) and anonymous flows with stand-in rooms. Each tap or jump shows the Rive properties set in order, the one timing rule that applied, the wait and a live timer, and highlights its row in an "All the waits" table built from the same constants; the tap code shown at the bottom is the code that runs. It is a visual companion to the guide's section 8 (the package README points to it).

### Delivered 2026-11-03 ("Chapter 1 polish, startScene")

Rive revisions: File 1 (2692475) 49418454, File 2 (2677803) 49418480, File 3 (2693093) 49418501, all named "Chapter 1 polish, startScene"; git tags `rive/ch1-chapter-1-polish-startscene`, `rive/ch2-chapter-1-polish-startscene`, `rive/ch3-chapter-1-polish-startscene`. The package is `deliver/yig-engineering-package.zip` (308,817 bytes, rebuilt after the copy timing change; sent by Demetre). The full suite was skipped for this delivery only (Demetre's call, 2026-11-03); what ran instead: `npm run check` for all three files, the unit tests, startScene spot checks in the CLI and in runtime 2.27.3, the text test in its short form (after the copy timing change), the experience harness (subscriber and anon, phone) and the unzipped package's demo (subscriber and anon, phone). With the copy at 2.0 s, Chapter 3's disco ball visibly drops through the copy area on its first visit (2.6 to 2.8 s); no other room moves there after 2.0 s. Left as it is for now (no Rive change in this delivery). The guide's section 4 now says Start's intro starts when you set the scene (it said "on your tap"); the guide gained section 8, "Opening a file on any scene".

- **A new copy timing** (Demetre, 2026-11-03, added before the zip was sent; no Rive change and no Rive push; guide rules 11 to 13, sections 4, 6, 7 and 9, the checklist). On a room's first visit the copy arrives at one constant, 2.0 s after the scene is set, everywhere: Start, Chapter 1, the Chapter 2 opener, community cards (their per-room times and `communityCopyMs` are gone), Chapter 3, Chapter 4's first card and End. The one exception: a Chapter 2 game's first card with its lockup keeps 3.2 s, so the copy never overlaps the lockup. Unchanged: 1.65 s for a room that comes back or any picture, 0.34 s within a room, 1.45 s for Chapter 4's reveal card; a two-move crossing is 1.65 s plus the landing room's time (subscriber Chapter 2 → 3 is now 3.65 s on a first visit, was 4.85 s). The intros stay exactly 3.2 s. The two constants: `--yig-first-visit` and `--yig-lockup` in `yig-text-motion.css` (the default `--yig-delay` is now `--yig-first-visit`; `yig-integration.js` and the Chapter 2 test page read both from the CSS), and `FIRST_VISIT_COPY_MS` and `LOCKUP_COPY_MS` in the React example's `timing.ts`. The text test and the experience test check the new times.
- **Loading and Start on desktop (HTML layout, no Rive change; guide section 4, item 4).** On desktop (1025 px and wider) the Loading and Start HTML (the lockup, the 2026 tiles, the progress bar or "Let's go", "Supported by T-Mobile") goes in the top part of the window, clear of the ball, the bird and the floor line. The animation uses artboard y 525 (the bird's hop on Start) down to the bottom; the Loading bounce tops out at 568, the resting bird and ball at 600, the floor line is 712. The review page (`layoutSplash()` in `harness/experience-stage.html`, and so the package's demo page) puts the block 16 px from the top and shrinks it uniformly on short windows to keep 28 px above the hop. Below 1025 px nothing changes. The bird's drop still passes through the top of the window once, for about 0.4 s.
- **Chapter 1 cards 2, 3 and 4 have new ball loops** (finesse round, Rive file change in File 1, no property or code change). Each starts moving as soon as its room arrives: card 2 slides down the stack and climbs back up; card 3 runs mug → band → books → FIRST → stick → mug; card 4 balances, hops a streak and rolls around the pot. Full detail in `docs/rooms-ch1.md`.
- **The ball now turns as it rolls** (cards 1 to 4; File 1): one full turn per circumference, in the direction of travel, keeping its spin in the air and stopping at rest.
- **Smoother motion** under the new physics rule (one gravity, contacts that keep most of their speed) and the jitter checks (no hitch, lurch, stall or buzz) in cards 1 to 4.
- **No property or scene name changed**, so none of the above needs a code change.
- **`startScene`, a new property in all three files** (2026-11-03; appended to the `Backdrop` view model, nothing existing renamed or reordered; guide sections 1, 2 and 8, and the checklist). An enum with exactly the file's `scene` values, in the same order; its default is the file's usual opening scene (File 1 `loading`, File 2 `from-chapter-1`, File 3 `ad`), so code that never sets it behaves exactly as before (every file renders pixel-identical to its last push without it). Set it and `scene` to the same value in `onLoad` (File 3: `topGame` and `reveal` first) and the file opens directly on that scene, already built and looping, as the room looks when it comes back with Back: no intro, pan, colour fade or lockup, the backdrop already in its colours, every other room off stage; after that, scene changes play the normal moves. Engineering may need it to mount one file at a time in app webviews: mount the next file with `startScene` set to the empty room the two files share, swap on that picture, then play the move. Built by `tools/start_scene.py` (each room gets a one-frame "<Room> Built" pose, its Intro's last keys; the Backdrop layer gets a Boot state). Two rules came with it: a room asked for with Back before it was ever shown in that file arrives built from the left, like a room coming back (this is what makes Back into a freshly mounted earlier file work); and Chapter 4's fireworks show only while `scene` is `chapter-4` (in normal playback `reveal` only turns true there, so nothing changes; it keeps a File 3 opened on another scene with `reveal` true free of stray fireworks). Tested in runtime 2.27.3: it runs the state machine once before `onLoad`, with the defaults, so the Backdrop's Boot state keeps no cut for the default scene and waits on its colours instead. One thing the guide spells out: a freshly mounted file has seen none of its rooms, so a Next into one plays its intro (copy at 3.2 s) even if the player saw it before the file was last mounted; Back into one always brings it in built.

### Delivered 2026-11-02 ("Ads once, polish")

Rive revisions: File 1 (2692475) 49362750, File 2 (2677803) 49362756, File 3 (2693093) 49362763, all named "Ads once, polish"; git tags `rive/ch1-ads-once-polish`, `rive/ch2-ads-once-polish`, `rive/ch3-ads-once-polish`. The package is `deliver/yig-engineering-package.zip` (sent by Demetre). The guide gained the opening sections "How the animation works, in plain English" and "What's new in this delivery".

- **Ads are skipped once seen** (2026-11-02; engineering's rule, card navigation only, no Rive change). Ad 1, Ad 2 and the anonymous Ad 3 show the first time the player reaches them with Next; after that Back and Next skip them, so the cards need an `ad: true` tag. New moves this creates: Chapter 1 card 1 ⇄ Start (one move); Chapter 1 card 5 ⇄ the Chapter 2 opener (two moves across files); anonymous Chapter 3 card 1 ⇄ the last Chapter 2 community card (two moves across files). The guide (rule 16, sections 5, 6, 7 and the checklist), the reference code (`yig-integration.js`, the React example) and the example page are updated.
- **The Mini and The Midi in Chapter 4 use The Crossword's fireworks on their own wall colours, final** (no longer placeholders). Their walls, 95BEFA and 7EAAF1, are exactly their Chapter 2 walls. The guide's "Coming later" list no longer has them.
- **The Crossword's Chapter 4 wall is now 6493E6** (was C0D8F8), its Chapter 2 colour, so every game's Chapter 4 wall matches its Chapter 2 room (2026-11-02; a Rive file change in File 3, no property or code change). The example page's video background uses it too.
- **Rive files changed in the global pass** (new `.riv` files, no property or code change): Start no longer stops when tapped in its first second (its intro now starts on the tap, blending from the Loading bounce over 0.25 s); the returns that close the loops in The Mini and The Crossword ease; The Midi's and The Crossword's first move starts from rest; Chapter 1 card 5's loop closes behind the tiles; the Chapter 3 and Chapter 4 stand-in balls, Connections' ball and The Mini's ball path moved inside the safe area. Pushed to Rive with this delivery.

## Global pass (decided and done 2026-11-02, for Demetre's review)

Four things that repeat across rooms. Everything else that repeats (the 0.15 s pop at 3.05 s, the shared roll-in, the landing squash, the Wordle and Connections stillness at the loop start, journey versus hop) is a room-by-room call, listed under the rooms in the Finesse order.

1. **No room freezes mid-motion.** Surveyed in the Rive runtime for every room in all three files (`python3 tools/loop_motion.py <ch>`, in `npm run suite`): each room is tapped out mid-loop and early in its visit, then tapped back in, and every piece its loops move is compared on every frame with a run that never leaves. Only **Start** stopped: a tap in the first second of its visit (while the Loading bounce was finishing) sent it to the Hidden pose, so the bird stayed above the stage and the intro never played. Fixed: the Loading bounce now blends into the Intro over 0.25 s from the tap instead of waiting up to a second for the bounce to end (so the Intro also starts on the tap, in step with the 3.2 s copy). `npm run check` now fails when any room's Intro, Hold or Loop state can be left on a scene change. No exceptions. The first-visit hold of the small loops (1.65 s) is intended and unchanged.
2. **The ball's easing in The Mini, The Midi and The Crossword.** Compared speed per frame (`python3 tools/ball_speed.py ch2 "<room>"`; the model matches the runtime to 0.06 units). Done: the returns that close the loops in The Mini and The Crossword ease in and out (they were constant-speed straight lines that started and stopped dead); The Midi's and The Crossword's first move starts from rest over 6 frames; The Crossword's speed step at frame 93 is smoothed. Left as drawn: the cuts hidden inside boxes, the contacts, The Mini's launch from under the floor, the roll-in and the pop, and the squash (drawn into the shape keys).
3. **The loop seams.** Chapter 1 card 5's loop is closed (the ball slides back behind the letter tiles over frames 177 to 179 instead of jumping 257 units at the wrap; `openLoops` is empty now); card 2's return eases. Strands' second move does not end early: the loop wraps on the string's contact and the ball arrives at 15.5 and leaves at 13.1 units per frame, a bounce (the sheet showed 2.98 s because it stopped counting at the last rendered frame; it now shows 3.00 s). Chapter 4's fireworks: at the wrap every set changes by under 100 pixels (against 1,500 to 2,900 mid-loop), so no set pops; each goes quiet for 0.1 to 0.3 s around the restart (Wordle 5 frames, Connections 11, Strands 7, Spelling Bee 17, The Mini, The Midi and The Crossword sets 19), left as drawn.
4. **The safe area** (x 560 to 935, y 0 to 812): every ball is inside it now except Chapter 1 card 1's, which rolls off the right edge between 7.2 s and 9.7 s on purpose. Moved: the Chapter 3 stand-in (x 1030 to 748), the Chapter 4 stand-in (x 577 to 600), Connections (rolls 616 to 578.5, not to 550) and The Mini (path squeezed from 580..921 to 596..899). Non-ball pieces outside it are not moved: each room's "To tune later" lists them (`python3 tools/safe_area.py <ch>` finds them).

## Finesse order

Each room starts with its current "To tune later" items (`docs/rooms*.md` have the full text). **Room-by-room calls for every room with a ball, decided as we go:** how the ball enters (it won't be the same on every card, and sometimes it is just part of the loop); whether it squashes; a full journey or a hop; where the loop starts. Reference facts for those calls: the roll-in runs 2.30 to 3.05 s in Chapter 1 cards 2 to 5, Strands, Spelling Bee, The Mini, The Midi and The Crossword (from x -80, 0.75 s, `power1.out`, a soft stop) and the ball is absent for about 0.65 s after the pan ends; a 0.15 s `power2.out` "pop" at 3.05 s lifts the ball 76 to 272 px onto the loop's first pose in seven rooms (Chapter 1 cards 2 to 5, Strands, The Midi, The Crossword); only Wordle and Connections have a landing squash and a spin.

**Global rule added 2026-11-02: the ball rotates** (full text in CLAUDE.md next to the ball's role): it turns one full turn per circumference rolled, clockwise rolling right and anticlockwise rolling left, keeps its spin in the air, and stops at rest. It is a rotation of the white dot and body about the ball's own centre (a "Ball Spin" pivot inside the squash node, so the squash stays relative to the floor contact). Done so far: Chapter 1 cards 1 to 4. **Every other room gets it during its own finesse round** (the Chapter 2 rooms and their Chapter 4 twins, the Chapter 3 stand-ins and Chapter 1 card 5 are still without it; Start's ball only bounces in place, so it has nothing to turn with).

1. **Loading / Start (File 1). Through the finesse round.** The bird's bounce is its fourth version (2026-11-02): it rides the ball up, tops out at 1.55 s into the loop, falls for 0.35 s and lands at 1.9 s, 0.1 s after the ball touches down at 1.8 s. On desktop the Loading and Start HTML sits at the top of the window, clear of the ball and the bird (2026-11-03, HTML only; guide section 4, item 4). The ball bounces in place, so it has no roll to turn with. Still open: the stage crop puts the floor line at about 702, not the mock's 712, so the ball sits a little high against the HTML.
2. **Chapter 1 rooms 1 to 5 (File 1).** Cards 1 to 4 are through the finesse round; each starts its ball moving as soon as its room arrives, the ball turns as it rolls, and each passes the physics and jitter checks (`tools/ball_speed.py ch1 "<room>" --contacts`). Their full current state, with every time, is in `docs/rooms-ch1.md` ("To tune later").
   - Card 1: the ball's story is the loop (out of the cuckoo clock's door, chair, window, off the right edge, 3.03 s pause); it rolls off the right edge on purpose (safe area). Left to tune: the shift per contact, the pause, the eye's timing and a bigger "asleep" cue, the dog's tail speed, the clouds' speed.
   - Card 2: the pencil knocks the stack, the ball teeters off the block, slides down the stack to the floor, runs back behind TOTAL and climbs back up (loop 8.3 s).
   - Card 3: the #1 mug circuit: out of the mug, band, books, FIRST, the knob and the blue stick, whose spring-back lifts it back into the mug (loop 3.65 s).
   - Card 4: balances on the crossword head as the room pans in, hops a streak across the flowers, rolls down to the pot's rim and climbs back (loop 10.2 s). Its softer gravity and two faster-out contacts are kept on purpose (Demetre, 2026-11-03).
   - **Card 5 (with Wordle Bot) is next:** the pop (80 px); its ball moves between the tile tops while hidden (loop closed in the global pass); it does not turn yet.
3. **Chapter 2 opener (Shelf, File 2).** None recorded; the ball's loop is three small moves (0.15 s, 0.30 s, 0.15 s). Calls: entry, squash.
4. **Chapter 3 and the bird room (File 3).** Chapter 3: a stand-in ball instead of a full journey (call: journey or hop; it rests inside the safe area at x 748 now). Bird on Ball (`chapter-3-bird`): the bird on the ball is a stand-in.
5. **Chapter 4 with the reveal (File 3).** The stand-in ball (journey saved until card 1 and the video hand-off are decided; it rests inside the safe area at x 600 now); the fireworks sets go quiet for 0.1 to 0.3 s around the loop restart (no pop; a call); The Mini and The Midi use The Crossword's fireworks on their own walls (final); the stack rides in with the floor (a drop needs both halves timed together); the video background is page HTML. The reveal: the wall fades over 1.45 s and the copy waits for it.
6. **End (File 3).** No ball of its own (two piles and the big one under the bird); the pieces ride in with the floor.
7. **Game rooms, in this order.**
   1. **Wordle:** about 0.6 s of stillness at the start of its loop (first move at 0.63 s; call: where the loop starts); squash and spin that most rooms lack.
   2. **Connections:** the same stillness (0.65 s); partly outside the largest phone's view.
   3. **Spelling Bee:** one 3.93 s hop; the outer side pieces fall outside the largest phone's view; the lockup icon stays as drawn until you say.
   4. **The Mini:** the ball's path is inside the safe area now; it reaches its place at 3.05 s; the front cube sits below y 823.
   5. **Strands:** the 76 px pop; the loop wraps on the string's contact (a bounce, checked: nothing to fix); the lockup icon stays as drawn until you say.
   6. **The Midi:** the 139 px pop (easing and the return done in the global pass).
   7. **The Crossword:** the 128 px pop in 0.15 s; its loop is 2.5 s inside a 3 s animation.
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
- **Ads show once** (engineering, 2026-11-02): Ad 1, Ad 2 and the anonymous Ad 3 appear the first time the player reaches them with Next, then Back and Next skip them. Card navigation only; the Rive files do not change.
- The floor line is 712 in every file. The artboard is 1495 × 1067 for desktop and mobile. Balls and key pieces stay inside the safe area, x 560 to 935 and y 0 to 812 (the Figma phone frame); engineering's framing decides the actual crop.
- Rooms are plain RML in the file, not nested components (2026-10, Stage 1: the rule checks only read the main artboard, and a component clips to its own frame). Each room's ball is plain ball art; the rig it came from was baked into direct keys.
- Ads and the top-game video are cards with no Rive copy; the HTML owns them.
- Every intro is exactly 3.2 s; a room plays its intro on its first visit only. The copy doesn't wait for all of it (2026-11-03): on a first visit it arrives at the first-visit constant, 2.0 s after the scene is set, everywhere; only a Chapter 2 game's first card with its lockup waits 3.2 s. Small loops (decor that runs on its own) live in a "<Room> Small" layer that holds its opening pose until the first-visit pan ends (1.65 s), then starts; that hold is intended (2026-10-30).
- Today's default in most rooms (2026-10-29): the ball's roll-in lands as the intro ends. It is not a rule: how the ball enters is a room-by-room call that finesse may change. Community-card copy arrives at the first-visit constant, 2.0 s, like every room without a lockup (2026-11-03; the per-room times, measured from when each room's pieces landed, are gone, and so is `communityCopyMs` in `chapters/ch2/chapter.json`).
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
- `tools/import_room.py` (and the configs in `tools/rooms/`) brought rooms in once and are history: never re-run them on a room that is already in.
- Standing rule from 2026-11-02: what's in Rive is the current version; tools compare against the last commit (`tools/compare_room.py`), not a source.

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

`engineering/yig-integration.js` is the reference for driving all three files from one card list: each card is `{ file, scene, community?, icon?, topGame?, reveal? }`; it loads the next file ahead, keeps earlier files loaded and paused, switches files on the shared empty pictures, holds a Back during a pan, and times the copy (`docs/engineering-guide.md`, sections 6 and 7). A swap: the next file is already sitting on the shared picture; on the tap that crosses, show its canvas and set its `scene` on the same frame; Back mirrors it (pan back inside the later file, then hand the stage back). `engineering/chapter-2-integration.js` serves only the Chapter 2 test page (`harness/index.html`).

### Review pages and servers

Start the server yourself (`cd harness && npm start`) and open the page: `http://127.0.0.1:8765/experience` is the review page (the whole experience across the three files, a Jump to menu, the flow, the example player, the top game, the screen size, the Finesse panel; it reloads itself on a newer build). `http://127.0.0.1:8765/` is the Chapter 2 test page. Restart the server after changing `harness/serve.mjs`.

### How scenes come in and the tools

`tools/import_room.py` copied the illustrator's rooms into `scene.rml` once each (history; its configs are in `tools/rooms/`). New art that exists only as SVG goes in through the Rive Editor first (the CLI has no SVG import), then `rive pull`. `tools/svg_to_rml.py` converts the lockup SVGs. `tools/scaffold_chapter.py` writes a new file from its manifest. `tools/rooms_sheet.py <ch>` writes `docs/rooms*.md` from the scene file and the manifest (`npm run check` fails when a sheet is out of date). `tools/check_chapter.py` holds the rule checks; `tools/tap_test.py` and `tools/back_test.py` play taps at exact moments in the Rive runtime.

### Lockups

All seven lockups are in `art/ch2/originals/` (`*-lockup.svg`, 175 × 128), converted to Rive shapes with icon and word as separate nodes, placed in the same frame as Wordle's, and wired and timed like Wordle's (in from frame 115, gone at frame 192 / 3.2 s, hidden on community cards). Icon sizes differ (five are 70.8 × 70.8, Strands 77.1 × 80.8, Spelling Bee 76.7 × 75.8) and stay as drawn.

### What's still to come

The mobile How-to overlay; the bridge room's art; the real ball journeys in Chapters 3 and 4; the bird-on-ball art in `chapter-3-bird`; what the page shows over Loading.

**startScene for a new room (before the bridge art comes in).** `tools/start_scene.py` adds the startScene rules to a whole file and refuses to run twice. `tools/import_room.py` copies an existing room's layers as a template, so since 2026-11-03 it drops the template's startScene rules from the copy (they name the template's scene and its Built pose). A newly imported room therefore comes in without them, and `npm run check` fails on it until they are added: its Built pose, its Waiting and Home transitions, its small loops, and its colour pose's place in the Backdrop's Boot state and start-room fades. Teach `start_scene.py` to add them to one room before importing the bridge room.

### Order of work

Done: Chapter 2 (all seven games, the opener, Chapter 2.5), File 1, File 3, the whole experience in one harness page, the engineering guide and React example, the package. **Now:** finesse, room by room (global pass first). **Then:** the mobile How-to file (`how-to-mobile.riv`, created by its first push after Demetre says, then moved by him into the 2026 folder). Every step ends with `npm run check`, and with a list of exactly what to look at in `/experience` when it changes what's on screen.
