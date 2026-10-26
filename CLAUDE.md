# Year in Games 2026 · Rive

Rive animation for NYT Games' Year in Games 2026 recap ("Well Played"). Design lead: Demetre Arges. This repo is the only place the Rive work happens. Engineering receives finished `.riv` files and the files in `engineering/`.

## Layout

- `chapters/chN/`: one Rive CLI project per chapter. Each is linked to its file in the Rive Team folder through its `rive.yaml`.
- `art/chN/`: import SVGs, original exports and reference PNGs.
- `docs/`: per-chapter animation specs, plus restructure notes.
- `harness/`: a local page that plays a chapter's built `.riv` with the real Rive web runtime and the text CSS, for review.
- `engineering/`: what developers get: integration code, `yig-text-motion.css`, and a short README.
- `reference/`: the earlier HTML prototypes, kept as motion references only. They aren't the source of truth.

## How engineering uses a chapter (keep it this small)

- They load the chapter's `.riv` with autoplay and set **one number, `scene`**, on every tap: 0 for the chapter opener, then the game the frame shows (Wordle 1, Connections 2, Strands 3, Spelling Bee 4, The Mini 5, The Midi 6, The Crossword 7). Setting the same value again does nothing.
- A game has several cards (Wordle 4, Connections 5 so far), one frame each: the opener, then each game's cards in the player's order. A tap inside a game swaps only the HTML text and the scene number stays, so Rive keeps looping. The tap after a game's last card starts the next game. The game's small icon is its own block, one per game: it pops in with the game's first card (3.2 s after the tap that starts the game) and stays while the cards change; it lifts out with the last card's text when the next game starts. They reveal the next copy with class `yig-in`, plus `yig-quick` when the scene didn't change; a same-game tap during the 3.2 s intro waits until the intro ends; the old copy is hidden at once. They write no animation timing in JavaScript and handle no Rive events.
- Engineering's priority is stats and calculations. Every extra integration step is a real cost, so solve problems inside the Rive file rather than in their code.

## Motion rules

- One Rive file per chapter, to keep file sizes down. The artboard is 1495 × 1067 and serves both desktop and mobile. The phone shows the centre 375 wide.
- The transition between rooms is Roll and pan, and **the camera always moves right**:
  - The outgoing room leaves left. Its wall plane nets 1280 units of travel and its floor plane 1600.
  - The incoming room arrives on the same pan. Rooms carry art only.
- **Color changes by crossfade, never by a seam.** One shared backdrop (wall, floor, floor line) stays put under every room, with no strokes on its edges, so no hard edge ever crosses the stage. On a scene change its wall and floor colors fade to the new room's over 1.45 s, power1.inOut, starting with the tap; a tap mid-fade turns from the color on screen.
  - Everything that leaves clears the full artboard, and everything that arrives starts outside it.
- The red ball is the persistent device:
  - The outgoing room's ball is never keyed by a transition. It keeps its loop and leaves with its room.
  - The incoming ball rolls in from beyond the left edge and climbs to the room's **loop start pose**.
  - Every loop starts and ends on that pose. The ball may change scale between rooms.
- **Every intro is exactly 3.2 s**, because the text CSS waits that long.
- The game lockup (icon plus word) lives in Rive. It rises in after the pieces land and is gone exactly at 3.2 s. The small icon and the stats are HTML. The lockup uses the text's curves: expo.out in, power3.in out.
- Text motion: Rise in 560 ms, Lift out 260 ms, Pop 440 ms, one mask per designed line. See `engineering/yig-text-motion.css`.
- Parked for later: Sink and stack, where the room sinks through the floor line, a color dome rises, and the pieces drop in.

## State machine pattern (per chapter)

- One number, `scene`. Two layers per room, so layers never key the same property:
  - `<Room>`: Waiting → Intro (scene == n) → Loop
  - `<Room> Exit`: Home → Shown (scene == n) → Outro (scene != n) → Gone
- A `Backdrop` layer holds the colors: from AnyState, scene == n goes to `<Room> Colors` (a one-frame pose of the backdrop's wall and floor color) with a 1450 ms power1.inOut blend and early exit on. Rive mixes the two states over the blend, which is the crossfade; no other timeline keys the backdrop.
- The outro keys only `<Room>` x and `<Room> Wall Lag` x. A game appears in one unbroken run of frames, so rooms never come back.
- Details are in `docs/scene-restructure.md`.

## Build rules

- The Rive CLI is the primary tool. New artwork goes in through the Rive Editor first (the CLI has no SVG import), then `rive pull`.
- Wrap anything that rotates or squashes so its group's own position sits on the pivot, with an inner "Art" group offset back.
- Keep `includeInExport` true on every artboard that ships.
- Never edit in the Editor and locally at the same time. Pull before local edits, verify and screenshot before pushing, and push with a `--name` label. Commit to git at every named push.
- When changing timing, keep each intro at 3.2 s, and keep each loop's first and last frames identical.
- After every change: run `--verify` and the automatic rule checks, as one script that takes about a second: `npm run check ch2`. It checks that Waiting poses equal their intro's first keys, every intro is exactly 3.2 s, every loop's first and last frames match (and start on the intro's last frame), and everything clears the artboard. Don't re-render, pixel-diff or time anything the change didn't touch. Full render, pixel and timing passes (`npm run tap`, `npm run text`, frame-by-frame renders against `art/chN/reference-frames/` and the reference prototype) are only for a handoff to engineering, or when asked. Motion and feel are reviewed by Demetre in the harness, so when a change affects what's on screen, say exactly what to look at.
- Rive draws a group's first child on top, so children are drawn in reverse of the order they are written. Anything that must sit behind everything, such as the shared backdrop, is the last child.
- A color change is a blend between two hold poses, set by the transition's duration and ease; never author the in-between, and never give a room its own backdrop. Turn on early exit, or a tap mid-fade waits for the old fade to finish and the color jumps.
- RML omits `value="0"` on keys, so read keys with a real XML parser and treat a missing value as 0. A regular expression reads them as missing, and that once put shadows and lockups at full size in a Waiting pose.
- Each Waiting pose must equal its intro's first keys. `npm run check` tests this for every room; after editing an intro, rebuild its Waiting pose from the intro, never by hand.
- A leaving room draws below the arriving room through draw rules, not by reordering rooms: each room's Outro and Gone key its rule to Bottom and its Home keys it back to Normal. A draw target has to name a Shape, not a group.
- Each lockup lives inside its own room so it leaves with the room.
