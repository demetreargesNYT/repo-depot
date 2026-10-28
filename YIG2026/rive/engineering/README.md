# Year in Games 2026, Chapter 2: handoff for engineering

This folder is a working example of Chapter 2. Run it, tap through it, then build the real thing the same way.

## What changed since handoff-4

- **One state machine name and one view model name, in every file: `"Backdrop"` for both.** Your side is the same as before:
  `start(cards)`, `onTap()` and `onBack()`.
- **`scene` and `direction` are enums (named values), not numbers.**
  - `direction`: `forward`, `back`.
  - `scene`: `intro`, `wordle`, `connections`, `strands`, `spelling-bee`, `mini`, `midi`, `daily`, `to-chapter-3`, `from-chapter-1`. The last two, `to-chapter-3` and `from-chapter-1`, are the empty pictures
    this file ends and starts on; they are internal to our integration, so your card list never names them as scenes.
- **`community` is now `lockup`, and true means the lockup is shown** (it defaults to true; a community card sets it to false).
  The `community: true` tag on a card in your list is unchanged: the integration turns it into `lockup = false`.
- **The handoff-4 integration will not work with this `.riv`**, because it set the old numbers and the old `"Chapter 2"` state
  machine name. Use the `chapter-2-integration.js` in this folder instead. The card list, the markup, the CSS and the three
  calls are unchanged.

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
| `chapter-2.riv` | the Rive file (188,503 bytes): artboard `"Chapter 2"`, state machine `"Backdrop"`, view model `"Backdrop"` (enums `scene`, `direction`; boolean `lockup`) |
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
[{ game: "chapter1" }, { game: "opener" }, { game: "wordle" }, { game: "wordle" }, { game: "connections", community: true }, { game: "chapter3" }]
```

- `game` is one of `"chapter1"`, `"opener"`, `"wordle"`, `"connections"`, `"strands"`, `"spelling-bee"`, `"mini"`, `"midi"`, `"daily"`, `"chapter3"`.
  The integration turns the name into the Rive file's `scene` value; you never set Rive values yourself.
- `community: true` marks a game's community card (the player solved fewer than 10 of its puzzles). The integration
  then sets Rive's `lockup` to false, which leaves out that game's lockup; everything else plays the same.
- Any other fields (the example uses `card` and `variant`) are yours, for choosing the copy.
- **The list always starts with `{ game: "chapter1" }` and ends with `{ game: "chapter3" }`** (see "The first and last cards" below).
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

- **First card, `{ game: "chapter1" }`**: the file loads on the empty Chapter 1 room (cream `#F1ECC0` wall, orange
  `#FF811E` floor, floor line at 712, no ball, no copy). It is the picture File 1 ends on, where Ad 2 plays. The first
  tap pans from it into the opener (the same pan as between games, 1.6 s), and the opener plays its own 3.2 s intro
  (no lockup: it isn't a game). Back from the opener returns to it; Back on this card does nothing.
- **Last card, `{ game: "chapter3" }`**: after the player's last game, a tap makes that room leave and an empty
  Chapter 3 backdrop (lavender `#E1DBF5` wall, green `#05CE7C` floor, floor line at 712, no ball) pan in. It is the
  picture File 3 opens on, and where Ad 3 plays for anonymous players. Back from it returns to the last game.

File 1 and File 3 aren't built yet. When they are, one integration will swap files on these exact pictures, so keep
these two cards in the list now and your calls (`start(cards)`, `onTap()`, `onBack()`) won't change. Neither card
has Rive copy: the example page shows placeholder text on the last card only so you can see it arrive.

## start, onTap and onBack

Call `start(cards)` once with the card list, then `onTap()` on Next and `onBack()` on Back. That's the whole
integration:

- They move to the next or previous card, and set Rive's `scene`, `direction` and `lockup` for it. A card in the
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

## The Rive file's properties

Every Rive file has a state machine named `"Backdrop"` and a view model named `"Backdrop"`, the same in all of our files. The
integration sets these for you. If you ever drive Rive directly instead, these are the properties, and who sets them:

| Property | Type | Who sets it | What it does |
|---|---|---|---|
| `scene` | enum: intro, wordle, connections, strands, spelling-bee, mini, midi, daily, to-chapter-3, from-chapter-1 | you may | Which room the stage shows. Setting the same value again does nothing. |
| `direction` | enum: forward, back | you may | forward for Next, back for Back. Set before scene. |
| `lockup` | boolean | you may | true shows the game lockup, false hides it (anon slides and community cards). Read only while a game's scene is entered. |

Set `direction` and `lockup` before `scene`; setting the same `scene` again does nothing. `scene` also has two internal
values, `from-chapter-1` and `to-chapter-3`: the empty pictures this file starts and ends on. Only our integration
uses them, so a card list never names them as scenes.

## Rive runtime

`@rive-app/canvas` **2.45.0**. Pin that version. In your app, `npm install @rive-app/canvas@2.45.0` and the
integration's `import { Rive } from "@rive-app/canvas"` resolves as usual. The example page maps that import to the
same version on a CDN only so it runs without a build step.

## Built and coming

| Card | Name | Rive `scene` (enum value) | Status |
|---|---|---|---|
| Empty Chapter 1 room (first card) | `"chapter1"` | `from-chapter-1` | built |
| Opener | `"opener"` | `intro` | built |
| Wordle | `"wordle"` | `wordle` | built |
| Connections | `"connections"` | `connections` | built |
| Strands | `"strands"` | `strands` | built |
| Spelling Bee | `"spelling-bee"` | `spelling-bee` | built |
| The Mini | `"mini"` | `mini` | built |
| The Midi | `"midi"` | `midi` | built |
| The Crossword | `"daily"` | `daily` | built |
| Empty Chapter 3 backdrop (last card) | `"chapter3"` | `to-chapter-3` | built |

The icons for Strands, Spelling Bee, The Mini, The Midi and The Crossword on the example page are placeholders cut from their lockups, until final icons are supplied. Their card copy is placeholder too.

New games arrive as an updated `chapter-2.riv`; the card format and your calls don't change. Copy text is placeholder.

Built from `chapters/ch2` (source last changed in git 51a9281). Rooms in this file: connections, daily, intro, midi, mini, spelling-bee, strands, wordle.
