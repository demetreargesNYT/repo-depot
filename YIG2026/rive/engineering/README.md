# Year in Games 2026, Chapter 2: handoff for engineering

This folder is a working example of Chapter 2. Run it, tap through it, then build the real thing the same way.

## Run it locally

```bash
cd chapter-2
python3 -m http.server 8000      # or any static server; opening index.html from disk won't load the .riv
```

Open http://localhost:8000/. Tap the right half of the stage (or →) for Next, the left half (or ←) for Back.
**Restart** reloads; **Desktop / Phone** switches between the full 1495 × 1067 artboard and the
centre 375-wide phone crop. The page loads the Rive runtime from jsDelivr, so it needs the network.

The NYT fonts aren't included, so the example copy shows in a fallback font. On your site, its fonts (NYT Franklin
and NYT Karnak) apply as normal.

## Files

| File | What it is |
|---|---|
| `chapter-2.riv` | the Rive file (63,523 bytes): artboard `"Chapter 2"`, state machine `"Chapter 2"`, view model `"Chapter 2"` (numbers `scene`, `direction`; boolean `community`) |
| `chapter-2-integration.js` | our integration code. Use it as written: it loads the file, handles Next and Back, and reveals the copy |
| `yig-text-motion.css` | the text motion; all text timing lives here |
| `index.html` | the example page: example player data, `buildCards`, the copy, `start(cards)` and the tap wiring |

## Cards and game names

The chapter is an ordered list of cards, one per tap. Build it from the player's stats and pass it to the
integration's `start(cards)` once, before any tap:

```js
import { start, onTap, onBack } from "./chapter-2-integration.js";

const cards = buildCards(EXAMPLE_PLAYER); start(cards);
```

Each card names its game:

```js
[{ game: "opener" }, { game: "wordle" }, { game: "wordle" }, { game: "connections", community: true }]
```

- `game` is one of `"opener"`, `"wordle"`, `"connections"`, `"strands"`, `"spelling-bee"`, `"mini"`, `"midi"`, `"daily"`.
  The integration turns the name into the Rive file's `scene` number; you never set Rive values yourself.
- `community: true` marks a game's community card (the player solved fewer than 10 of its puzzles). Rive then
  leaves out that game's lockup; everything else plays the same.
- Any other fields (the example uses `card` and `variant`) are yours, for choosing the copy.
- The opener comes first, then each game's cards together, in the player's order.
- An unknown name throws. A game that isn't built in the `.riv` yet keeps the current room on screen, still changes
  the copy, and logs a console warning, so you can wire up later games before their art ships.

## buildCards: an example of your logic

In `index.html`, `EXAMPLE_PLAYER` stands in for the Games API (it's made-up data), and `buildCards(player)` turns
it into the card list. It's an example of the logic you'll write against the real stats, not code to ship:

- the opener first, then each game in the player's order;
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

## start, onTap and onBack

Call `start(cards)` once with the card list, then `onTap()` on Next and `onBack()` on Back. That's the whole
integration:

- They move to the next or previous card, and set Rive's `scene`, `direction` and `community` for it. A card in the
  same game changes only the copy; Rive keeps looping.
- They reveal the card's copy and the game's icon, timed to Rive (3.2 s after the tap for a game's first visit, when
  the pan ends for a game you come back to, about 0.34 s for a card in the same game).
- Back on the opener, Next on the last card, or a tap before `start`, does nothing. A tap that would reverse a pan waits for it to end.
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

`@rive-app/canvas` **2.45.0**. Pin that version. In your app, `npm install @rive-app/canvas@2.45.0` and the
integration's `import { Rive } from "@rive-app/canvas"` resolves as usual. The example page maps that import to the
same version on a CDN only so it runs without a build step.

## Built and coming

| Game | Name | Rive `scene` | Status |
|---|---|---|---|
| Opener | `"opener"` | 0 | built |
| Wordle | `"wordle"` | 1 | built |
| Connections | `"connections"` | 2 | built |
| Strands | `"strands"` | 3 | coming |
| Spelling Bee | `"spelling-bee"` | 4 | coming |
| The Mini | `"mini"` | 5 | coming |
| The Midi | `"midi"` | 6 | coming |
| The Crossword | `"daily"` | 7 | coming |

New games arrive as an updated `chapter-2.riv`; the card format and your calls don't change. Copy text is placeholder.

Built from `chapters/ch2` (source last changed in git 8edc3df). Rooms in this file: scene 0, 1, 2.
