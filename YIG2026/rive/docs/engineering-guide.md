# Year in Games 2026: driving the Rive files from your own code

This guide has everything you need to drive our three Rive files from your React code: what to load, what to set, in what order, when each card's copy may appear, and what to do when the player taps Back in the middle of a move. It is written for the React page you are building in the Games web code (Rive runtime 2.27.3, through `@rive-app/react-canvas` 4.20.1). Everything in it was tested on that runtime.

Two other things in this package show the same rules in code:

- `react/` is a small React 18 + TypeScript example that follows this guide. Start there when you write your own.
- `reference/yig-integration.js` is the plain-JavaScript version we use to check the files. It is a working reference, not something you have to use.

`example/` is a page you can open to see the whole experience play (see the README).

## 1. The big picture

- **One stage behind every slide.** The Rive animation sits behind all the slides and stays on screen. When the player taps, the stage changes rooms (the camera pans), and the page shows the next card's copy on top. The stats, the copy and the small game icons are all HTML.
- **Three Rive files, played back to back.** The player never sees a file change, because each file starts and ends on a picture of an empty room, and the file before or after shows exactly the same picture.

  | File | `.riv` | Covers |
  |---|---|---|
  | File 1 | `start-chapter-1.riv` | Loading, Start, Ad 1, Chapter 1, Ad 2 |
  | File 2 | `chapter-2.riv` | Chapter 2 (the opener, the games, Chapter 2.5), ending on the empty Chapter 3 room |
  | File 3 | `chapters-3-4-end.riv` | Ad 3 (anonymous players), Chapter 3, Chapter 4, End |

- **One artboard per file, 1495 × 1067, the same on every device.** Phones show the centre 375 wide. Your page crops it (your own cover-style framing); we do not change the artboard for different screens. `example/yig-framing.css` has the crop we used when testing, copied from your page.
- **Every file has the same names.** The state machine is named `Backdrop` and the view model is named `Backdrop`, in all three files.
- **You set three or four view model properties, and nothing else.** There are no Rive events to listen to and no timing to write in JavaScript: the Rive side moves on its own after a property changes, and the copy timings in section 7 are fixed numbers.

## 2. Starting a file

Start each file with the **plural** option `stateMachines`. On 2.27.3 the singular `stateMachine` is ignored, and the file would not play.

```ts
const { rive, RiveComponent } = useRive({
  src: '/yig/start-chapter-1.riv',
  stateMachines: 'Backdrop', // plural
  autoplay: true,
  autoBind: true, // binds the view model instance, so rive.viewModelInstance exists once the file has loaded
})
```

After `onLoad` has fired (the `rive` object is set and `rive.viewModelInstance` is not null):

- call `rive.resizeDrawingSurfaceToCanvas()` once, and again whenever the window is resized;
- set properties with `rive.viewModelInstance.enum('scene').value = 'start'` and `rive.viewModelInstance.boolean('lockup').value = false`.

Setting a property to the value it already has does nothing. This matters: setting `scene` to the room that is already showing never restarts it.

## 3. The properties

All three files have `scene` and `direction`. File 2 also has `lockup`; File 3 also has `topGame` and `reveal`. Enum values are set by name.

| Property | Type | File | What it does |
|---|---|---|---|
| `direction` | enum: `forward`, `back` | all | `forward` for Next, `back` for Back. The camera pans right on `forward` and left on `back`; Back is the exact mirror of Next. |
| `lockup` | boolean, default `true` | File 2 | `true` shows a game's lockup (its icon and name, in Rive). `false` hides it. Community cards set it to `false`. It is read only at the moment a game's scene is entered. |
| `reveal` | boolean, default `false` | File 3 | Chapter 4 only. `false` on the first Chapter 4 card (the stack and the ball on the lighter blue wall); `true` from the top-game card on (the wall fades to the top game's colour and that game's fireworks start). Back to the first card sets it to `false` again. |
| `topGame` | enum: `wordle`, `connections`, `strands`, `spelling-bee`, `mini`, `midi`, `daily` | File 3 | The player's top game. Chooses Chapter 4's wall colour and fireworks. Default `wordle`. Set it once, as soon as File 3 has loaded, from the stats (anonymous players: always `wordle`). |
| `scene` | enum, see section 4 | all | Which room the stage shows. |

**The order to set them in: `direction`, then `lockup`, then `reveal`, then `scene`.** `scene` is the one that starts the move, and the others are read when it changes, so they must already be right. (The same applies to the second property you set on a move: set everything the card names, then `scene` last.)

Rules of thumb:

- Only set a value that the card names. A card inside the same game or room changes no Rive property at all (see section 7).
- `topGame` and `reveal` are File 3's. `lockup` is File 2's. File 1 has only `scene` and `direction`.
- Do not set a `scene` that belongs to another file. An unknown name throws.

## 4. The scenes in each file

A **room** has an intro that plays the first time the player arrives (always exactly 3.2 s), then loops until the player taps. A **picture** is an empty room: no intro, nothing in it, only the wall and floor colours; it is what a file starts and ends on, and where ads play. Every room comes back already built when the player returns to it with Back.

### File 1: `start-chapter-1.riv`

The wall is cream `#F1ECC0` and the floor orange `#FF811E` in every File 1 scene, so no colour ever changes.

| `scene` | Kind | What the stage shows |
|---|---|---|
| `loading` | picture (the file's default) | The empty room with the ball bouncing in the middle. Plays while the stats load. |
| `start` | room | The same picture; the bird drops in and lands on the ball, then the two keep playing. No pan, no colour change. |
| `ad` | picture | The empty Chapter 1 room. Ad 1 and Ad 2 play here, and File 2 opens on this same picture. |
| `chapter-1-card-1` … `chapter-1-card-5` | room | Chapter 1's five rooms, one per card. |

### File 2: `chapter-2.riv`

The wall colour changes with each game; the floor is pink.

| `scene` | Kind | What the stage shows |
|---|---|---|
| `from-chapter-1` | picture (the file's default) | The empty Chapter 1 room, the picture File 1 ends on. |
| `intro` | room | Chapter 2's opener ("But that's not all"). No lockup. |
| `wordle`, `connections`, `strands`, `spelling-bee`, `mini`, `midi`, `daily` | room (with lockup) | One game's room. `daily` is The Crossword. |
| `bridge` | picture | Chapter 2.5's bridge card: an empty version of the opener's room, with the copy arriving when the pan ends. |
| `to-chapter-3` | picture | The empty Chapter 3 room, the picture File 3 opens on. |

### File 3: `chapters-3-4-end.riv`

| `scene` | Kind | What the stage shows |
|---|---|---|
| `ad` | picture (the file's default) | The empty Chapter 3 room (lavender wall, green floor). Ad 3 plays here for anonymous players, and the badge cards use it. |
| `chapter-3` | room | Chapter 3's room. |
| `chapter-3-bird` | room | Just the ball, twice as big and in the centre, with the bird on top. |
| `chapter-4` | room | Chapter 4. `reveal` and `topGame` choose what it shows. |
| `end` | room | The End room, a looping scene thanking the player. |

## 5. Loading and Start (File 1)

1. **Load File 1 at once.** It opens on `loading`: the ball bounces in the empty room. That is the loading screen's animation; your page puts the logo lockup, the progress bar and "Supported by T-Mobile" over it. File 2 and File 3 load behind it, one after the other (section 8).
2. **Switch to Start when both are ready**: when the stats have arrived and File 1 has loaded, set `direction = forward` and then `scene = 'start'`. The ball finishes the bounce it is on (it never jumps, so this can take up to one second), then the bird drops in and lands on the ball. There is no pan and no colour change. Start is a room: its intro takes 3.2 s from the moment you set `scene`, and the Start copy ("Let's go" and the rest) arrives at 3.2 s.
3. **"Let's go" is an ordinary Next.** It sets `direction = forward` and `scene = 'ad'`. The ball and the bird pan out to the left, leaving the empty room where Ad 1 plays. The Ad 1 copy arrives when the pan ends (1.65 s). The next ball the player sees is the one coming out of the cuckoo clock in Chapter 1's first card.
4. **Back never returns to Loading.** Back on Start does nothing. Back from Ad 1 returns to Start, which comes back already built (its copy arrives when the pan ends, 1.65 s).
5. If the player taps before File 1 has loaded, hold the tap until it has.

## 6. The cards

You build one card list from the stats. Each card says which file and which scene it uses, plus the tags the copy needs (a game's icon, `community`, `topGame`, `reveal`). Many cards share a room: a game has several cards (Wordle four, Connections five, and so on), and a tap inside a game changes only the copy while the room keeps looping.

### Flow of files and the shared pictures

| End of one file | Start of the next |
|---|---|
| File 1's last picture, `ad` (Ad 2) | File 2's first picture, `from-chapter-1` |
| File 2's last picture, `to-chapter-3` | File 3's first picture, `ad` |

### Chapter 1 (File 1)

Up to five cards. Card *n* uses `chapter-1-card-n`. Some cards have thresholds and are skipped for some players; the skipped card's room is not visited. Order: `loading`, `start`, `ad` (Ad 1), the Chapter 1 cards, `ad` (Ad 2). The tutorial overlay (section 10) shows on Chapter 1's first card.

### Chapter 2 and Chapter 2.5 (File 2)

- The file's first scene is `from-chapter-1`: the card sits on the empty room (File 1's Ad 2 is the same picture). The first Next pans into `intro`.
- Then each qualifying game (10 or more completed puzzles) in the player's order, using that game's scene (`wordle`, `connections`, `strands`, `spelling-bee`, `mini`, `midi`, `daily`), with that game's cards (all in the same scene).
- **A player with exactly one qualifying game gets Chapter 2.5** after that game's cards: the `bridge` scene ("The rest of the world also came to play."), then community cards for the other community games, in the order Wordle, Connections, Spelling Bee, The Mini, Strands (leaving out the player's own game). A community card is a normal room change with `lockup = false` (no Rive lockup); the small HTML icon still pops in. A Midi or Crossword player sees all five. Players with two or more qualifying games skip Chapter 2.5.
- **Anonymous players:** the opener, then one community card per game (the mock shows Connections, Spelling Bee, The Mini and Strands), every one with `lockup = false`, then Ad 3 on the empty Chapter 3 room.
- **Subscribers and registered players have no card on the empty Chapter 3 room.** The tap on their last Chapter 2 card plays both moves by itself (section 8): the room pans out to the empty Chapter 3 room, File 3 takes over, and Chapter 3's room arrives right after, with no extra tap. Back from Chapter 3 plays them in reverse to that last Chapter 2 card.

### Chapter 3 (File 3)

Anonymous players: two cards on `chapter-3` (Connections' 1000th puzzle and Wordle's fifth birthday), after Ad 3 (`ad`, on the empty room).

Subscribers and registered players: up to four cards, in this order.

| # | Card | File 3 `scene` | Skipped when |
|---|---|---|---|
| 1 | "There's plenty more to celebrate, too." | `chapter-3` | never |
| 2 | "Crossplay, the Midi and bonus puzzles gave you new ways to play." | `chapter-3-bird` | never |
| 3 | Event badges (HTML) | `ad` | the player has no event badges |
| 4 | Achievement badges (HTML) | `ad` | the player has no achievement badges |

### Chapter 4 and End (File 3)

Three cards, all on `chapter-4`:

| # | Card | `reveal` | What the stage does |
|---|---|---|---|
| 1 | "But through it all, it's clear you play favorites." | `false` | The stack and the ball on the lighter blue wall. |
| 2 | "In 2026, your top game was…" with the game's icon and name | `true` | The wall fades (1.45 s) to the top game's colour and that game's fireworks start. |
| 3 | The game's video and the editor's name (HTML) | `true` | The stage stays as card 2 left it; your page covers it with the game's wall colour behind the video. |

Anonymous players: the top game is always Wordle (`topGame = 'wordle'`), and the video is the special one from all the editors. Then `end` (the End room), and the Share card (HTML) on the same `end` scene.

### The card list in code

A card is `{ file, scene, community?, icon?, topGame?, reveal? }`. The React example (`react/src/cards.ts`) builds the whole list for both flows from a small stats object, including every skip rule above.

## 7. When the copy may appear

The copy of a card is HTML that you show on top of the stage. It must not appear before the room has settled. These numbers are fixed; they come from the Rive files.

| Situation | Copy appears |
|---|---|
| A room's first visit with Next (it has an intro): Start, a Chapter 1 card, a game with its lockup, `intro`, `chapter-3`, `chapter-3-bird`, `chapter-4`, `end` | **3.2 s** after you set `scene` |
| A **community card** (no lockup), first visit | When the room's pieces have landed, per game: Wordle 2334 ms, Connections 2367 ms, Strands 1967 ms, Spelling Bee 2017 ms, The Mini 2084 ms, The Midi 1950 ms, The Crossword 1950 ms |
| Coming back to a room with **Back** (it slides in already built), or any picture (`ad`, `from-chapter-1`, `to-chapter-3`, `bridge`) | **1.65 s**: when the pan ends |
| Another card **inside the same room** (the next Wordle card, Chapter 4's second card) | **0.34 s**: right after the old copy has cleared (it clears in 340 ms). Nothing changes in Rive. |
| A tap inside a room whose intro is still running | When the intro ends (the 3.2 s, or the community time), not before |
| Subscriber, last Chapter 2 card → Chapter 3 (two moves) | **4.85 s**: 1.65 s for the first move, then 3.2 s for Chapter 3's intro |
| Chapter 3 → Back to that Chapter 2 card (two moves) | **3.3 s**: two pans of 1.65 s |

The old copy leaves at once on every tap (it drifts up, or down on Back, and dissolves within 340 ms).

The pan is 1.6 s long; wait 1.65 s to be safe. The first visit of a room, with its intro, is the only time 3.2 s applies: a room the player has already seen comes back built.

## 8. Moves, files and Back

### One move

For a move that stays inside a file, set `direction`, the properties the card names (`lockup`, `reveal`), then `scene`. The stage does the rest.

### A Back during a move waits

The files cannot turn a room around in the middle of a pan. So:

- a **Back during any pan**, and a **Next during a Back pan**, must wait until the pan has ended (1.65 s after it started), and only the last tap held counts;
- a **Next during a Next pan** goes ahead at once.

### Switching between the three files

Every file starts and ends on an empty picture, and the neighbouring file shows the same picture. So:

- **Load ahead.** Load File 1 at once; when it is ready, load File 2; when that is ready, File 3. Keep all three loaded for the whole visit, so Back across a file boundary never reloads. Hold a Next tap on the empty room until the next file has loaded.
- **Stack the canvases.** Each file has its own canvas, in the same place. Show one at a time. A file that is not on screen should be paused (`rive.pause()`), and played again when it is shown.
- **Next into the next file.** The next file is already sitting on the shared picture. In the same frame, show its canvas on top and set its `scene`. When the old canvas has been covered (after two animation frames), hide it and pause it.
- **Back into the earlier file.** The later file is on the shared picture. Set its `scene` to that picture (its first scene) with `direction = back` so it pans back to it, wait 1.65 s, then show the earlier file's canvas (which is still sitting on the same picture) and, if the card is not on that picture, set the earlier file's `scene` to the card's.
- **A card that is not on the empty picture when it crosses** (File 2's last game card → Chapter 3, the one real case) takes two moves: first set File 2's `scene` to `to-chapter-3` (it pans out), and after 1.65 s show File 3 and set its `scene` to the card's. If the player taps again before the second move starts, run it at once. Back is the same two moves in reverse.

## 9. Desktop and phone controls

- **Phones and tablets** (below 1025 px): tap zones. The left 25% of the screen is Back and the right 75% is Next.
- **Desktop** (1025 px and wider): no tap zones. Arrow buttons at the left and right edges of the window, 20 px in, centred vertically, do Back and Next. They are HTML. The art is in `example/assets/icons/ui-desktop-button.svg`.
- Back on the first card, Next on the last card, or a tap before everything is ready, does nothing.

## 10. The tutorial overlay (mobile only, coming later)

A small file, `how-to-mobile.riv`, will explain "tap right for Next, tap left for Back". It shows on mobile only, over the stage, if the player is idle on Chapter 1's first card. It is not in this package yet: it is built after the three files, and it comes with its own short note. Desktop has no tutorial file; the arrow buttons explain themselves.

## 11. The text CSS

`yig-text-motion.css` animates the copy with no JavaScript. Everything is at three levels, and you choose how finely to split a card's copy.

1. **A whole block.** Put the text straight into `<div class="yig-text">`. The block rises as one piece.
2. **Per element.** Put an image or icon in the block with `class="yig-pop"`. It pops in (a soft settle with a small overshoot) instead of rising.
3. **Per line.** Wrap each designed line in `<span class="yig-mask"><span class="yig-line">…</span></span>`. Each line rises in its own mask, 120 ms after the one before.

```html
<div class="yig-text">
  <img class="yig-pop" src="wordle.svg" alt="Wordle">
  <span class="yig-mask"><span class="yig-line">On average, you solved</span></span>
  <span class="yig-mask"><span class="yig-line">Wordle puzzles in</span></span>
</div>
```

Classes you add and remove:

| Class | When | What it does |
|---|---|---|
| `yig-in` | the card's copy should arrive | Waits `--yig-delay`, then rises in. Set `--yig-delay` (for example `3200ms`) on the element from the table in section 7. |
| `yig-quick` | the tap stayed inside the same room | The copy rises in right after the old copy has cleared (340 ms) instead of waiting. |
| `yig-after-icon` | a game's first card | The lines start one step after the game icon pops. |
| `yig-out` | the old copy leaves | It lifts out and dissolves (240 ms), then you hide it after `--yig-clear` (340 ms). Only do this to copy that has finished rising; copy that is still rising should simply be hidden. |
| `yig-back` | Back | The same moves, mirrored: copy comes down into place instead of up, and leaves downwards. |

The game icon is its own block, one per game, outside the cards: `<div class="yig-icon"><span class="yig-pop">…</span></div>`. It pops in with the game's first card, stays while the game's cards change, and leaves with the last card's text when the next game starts. Community cards still show it. All the timings are variables at the top of the CSS file. With reduced motion, everything becomes a 200 ms fade.

## 12. A checklist

- `stateMachines: 'Backdrop'` (plural) on every file; `autoBind: true`.
- Set `direction`, `lockup`, `reveal`, then `scene`.
- Never set the same scene value again expecting a restart: it does nothing.
- Copy at 3.2 s for a first visit; the per-game time for a community card; 1.65 s for a picture or a return; 0.34 s inside a room.
- A Back during a pan waits for it.
- Keep every file loaded; pause the one that is hidden.
- Subscribers have no card on the empty Chapter 3 room; the last Chapter 2 card's tap plays both moves.
- Anonymous players: Ad 3 on the empty Chapter 3 room, `topGame = wordle`, community cards in Chapter 2.
