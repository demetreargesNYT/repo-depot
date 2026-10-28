# Restructure Chapter 2 for multiple games

The current "YIG Chapter 2" file (Rive file 2677803, revision 48903415 "7 State machine") handles one transition: the shelf room to the player's top game, driven by `game` and `frame`. A chapter runs through up to five games in the player's order, so this restructure lets any game follow any other. It's driven by one number, `scene`.

The motion target is `prototype/chapter-2-prototype.html`. Choose either game order and tap through four frames: opener, first game, the same game again (only the text changes), then the second game.

## What changes

1. **One value replaces two.** `scene` is now an enum (it began as a number: 0 the chapter opener, 1 Wordle, 2 Connections, 3 Strands, 4 Spelling Bee, 5 The Mini, 6 The Midi, 7 The Crossword; the names are `intro`, `wordle`, `connections`, `strands`, `spelling-bee`, `mini`, `midi`, `daily`). Keep whichever binding style the file already uses (it currently uses a view model with autoBind). Replace `game` and `frame` with a single number property, `scene`, default 0.
2. **Each room brings its own colors.** Add a `<Room> Backdrop` group as the first (bottom) child of each room group:
   - Shelf Room: wall #E7F1E1
   - Wordle Room: wall #C3E2C0
   - Connections Room: wall #E1DBF5
   Each backdrop holds:
   - a wall rectangle from (0, −200) to (1600, 712)
   - a floor rectangle from (0, 712) to (1600, 1312), fill #FEA0C9
   - a 2-unit #1F1F1F floor line along y 712 from x 0 to 1600
   - a 2-unit #1F1F1F wall corner line along x 0 from y −200 to 712
   They're plain rectangles and paths, so create them directly in RML. They're 1600 wide so neighbouring rooms meet exactly at the wall corner during the pan.

   The global Background wall color is no longer animated. Delete its keys from the intros and leave it at #E7F1E1.
3. **Each room's wall plane gets a lag wrapper.** Wrap each room's wall plane in a new group, `<Room> Wall Lag`, at x 0. The outro keys the lag wrapper, so it never fights the intro, which keys the wall plane itself. Do this for Shelf and Connections, and for Wordle too even though it's empty today, so every room has the same structure.
4. **Intros only move their own room.** Remove every Shelf key from "Wordle Intro" and "Connections Intro", along with the Background wall color key. Add a backdrop key to each intro: `<Room> Backdrop` x 0.05 1600 → 1.55 0 (power2.inOut), the same pan as the floor plane.
5. **Each room gets an outro.** The whole room leaves left with the camera, its wall plane lagging. These keys come out of the old intros:
   - "Shelf Outro", 1.6 s: Shelf Room x 0.05 0 → 1.55 −1600 (power2.inOut), and Shelf Wall Lag x 0.05 0 → 1.55 320 (power2.inOut), so the wall plane nets −1280.
   - "Wordle Outro", 1.6 s: Wordle Room x 0.05 0 → 1.55 −1600 (power2.inOut). Wordle Wall Lag holds at 0.
   - "Connections Outro", 1.6 s: Connections Room x 0.05 0 → 1.55 −1600, and Connections Wall Lag x 0.05 0 → 1.55 320 (power2.inOut).
   An outro keys only `<Room>` x and `<Room> Wall Lag` x, nothing inside the room, so the room's loop keeps playing as it leaves.
6. **Two layers per room.** Each game appears in one unbroken run of frames per chapter, so a room never comes back once it has left.
   - Layer `<Room>`:
     - Entry → Waiting (a one-frame animation that holds the design pose: everything the intro animates, at its first-key value)
     - Waiting → Intro when scene == n (no exit time, duration 0)
     - Intro → Loop at exit time 100%
     - The Shelf layer has no intro: Entry → Shelf Loop.
   - Layer `<Room> Exit`:
     - Entry → Home (a one-frame animation: `<Room>` x 0, `<Room> Wall Lag` x 0)
     - Home → Shown when scene == n
     - Shown → Outro when scene != n (no exit time, duration 0)
     - Outro → Gone at exit time 100% (Gone holds `<Room>` x −1600)
     - Shelf Exit starts in Shown, because the opener is on screen at load.
   Layers never key the same property, so they never fight. Adding a game means adding its two layers.
7. **Remove** the old transitions out of Frame 1 Loop that test `game` and `frame`.

## Checks

- With scene 0 the artboard shows only the shelf room.
- 0 → 1: Shelf leaves and Wordle arrives on the same pan. The wall corner sweeps in from the right, and the shelf ball keeps rocking as it leaves.
- 1 → 1: nothing happens, and the Wordle loop keeps running.
- 1 → 2: Wordle leaves with its ball still looping, and Connections arrives. Then test 0 → 2 → 1.
- Both intros are still exactly 3.2 s, and each loop still starts on its intro's last frame.
- Every outgoing room clears the left edge of the 1495-wide artboard by 1.55 s, and every incoming piece starts fully off stage.
- Render frames at 0.8 s and 1.6 s of each change, and compare them with the prototype at the same moments.

When it passes, push with `--name "Scene structure"`, then update `engineering/chapter-2-integration.js` to set `scene` instead of `game` and `frame`, using the binding style the file uses.
