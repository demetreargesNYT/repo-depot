# Year in Games 2026, Chapter 2: handoff for engineering

Load the chapter's file, set one number when the player taps, and reveal the next copy. Everything else, including
all animation timing, is inside the Rive file and `yig-text-motion.css`.

## The three steps

1. **Load `chapter-2.riv`** with the Rive web runtime, autoplay on, state machine `"Chapter 2"`, and
   `autoBind: true` so the file's view model is bound (see `chapter-2-integration.js`; pin the runtime version you ship).
2. **On every tap, set the view model number `scene`** to the scene the new frame shows:
   `yig.viewModelInstance.number("scene").value = n`. Setting the value it already has does nothing, so it is always safe.
3. **Reveal the next copy** with class `yig-in`, plus `yig-quick` when the scene didn't change. The CSS does all the
   timing: copy for a new game rises 3.2 s after the tap, matching the Rive intro. Hide the old copy at once. A tap
   that only moves to the game's next card, while that game's intro is still running, waits until the intro ends
   (the integration file sets that delay).

`chapter-2-integration.js` does all three; use it as written.

## Scene values

| `scene` | Shows |
|---|---|
| 0 | the chapter opener |
| 1 | Wordle |
| 2 | Connections |
| 3 to 7 | Strands, Spelling Bee, The Mini, The Midi, The Crossword (not built yet) |

A game has several cards, one frame each. A tap inside a game keeps the same `scene` (the text changes, Rive keeps
looping); the tap after the game's last card sets the next game's `scene`. A game appears in one run of cards.

## Files

| File | What it is |
|---|---|
| `chapter-2.riv` | the Rive file (61,088 bytes): artboard `"Chapter 2"` 1495 × 1067, state machine `"Chapter 2"`, view model `"Chapter 2"` with the number `scene` |
| `chapter-2-integration.js` | the integration code: load, set `scene`, reveal copy |
| `yig-text-motion.css` | text motion: Rise in 560 ms, Lift out 260 ms, Pop 440 ms; waits 3.2 s for a new game |

Built from `chapters/ch2` (source last changed in git b36bfa0).
