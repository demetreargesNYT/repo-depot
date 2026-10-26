# Year in Games 2026, Chapter 2: handoff for engineering

Load the chapter's file, call our Next or Back function when the player taps, and reveal the next copy. Everything else, including
all animation timing, is inside the Rive file and `yig-text-motion.css`.

## The three steps

1. **Load `chapter-2.riv`** with the Rive web runtime, autoplay on, state machine `"Chapter 2"`, and
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
| 0 | Shelf Draw |
| 1 | Wordle Draw |
| 2 | Connections Draw |
| 3 to 7 | Strands, Spelling Bee, The Mini, The Midi, The Crossword (not built yet) |

A game has several cards, one frame each. A tap inside a game keeps the same `scene` (the text changes, Rive keeps
looping); the tap after the game's last card sets the next game's `scene`. A game appears in one run of cards;
Back returns through them in reverse.

## Files

| File | What it is |
|---|---|
| `chapter-2.riv` | the Rive file (62,957 bytes): artboard `"Chapter 2"` 1495 × 1067, state machine `"Chapter 2"`, view model `"Chapter 2"` with the numbers `scene` and `direction` |
| `chapter-2-integration.js` | the integration code: load, Next and Back (`scene`, `direction`), reveal copy |
| `yig-text-motion.css` | text motion v3: Rise in 720 ms, Lift out 240 ms (clear in 340 ms), Pop 560 ms, reversed on Back; waits 3.2 s for a new game |

Built from `chapters/ch2` (source last changed in git 6914320).
