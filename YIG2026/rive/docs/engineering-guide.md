# Year in Games 2026: driving the Rive files from your own code

This guide has everything you need to drive our three Rive files from your React code: what to load, how to build the card list, what to set and in what order, when each card's copy may appear, and what to do when the player taps Back in the middle of a move. It is written for the page you are building in the Games web code (Rive runtime 2.27.3, through `@rive-app/react-canvas` 4.20.1). Everything in it was tested on that runtime.

You need the four things in this folder (`core/`): the three `.riv` files, this guide, `yig-text-motion.css` and the desktop arrow art (`ui-desktop-button.svg`). The `reference/` folder next to it has a working example of the guide (section 13). It is optional.

## How the animation works, in plain English

These are the rules the animation follows, written so each one can become code and a test. Each group says what Rive does by itself and what your code must do. The later sections have the details; the number in brackets is the section.

**The stage**

1. One Rive animation sits behind every card, from Loading to End. Your code changes the HTML on top; Rive changes the room underneath. [2]
2. The animation is one 1495 × 1067 artboard on every device. Your page decides the crop and the scale. [2]
3. Show at least x 560 to 935 and y 0 to 812 of the artboard (the phone frame in the design). Every ball rests and moves inside it, except when it rolls in from beyond the left edge and when the ball in Chapter 1's first room rolls off the right edge, both on purpose. Some other pieces reach beyond it, so expect them to be cropped on narrow screens. [2]
4. Rive draws the rooms and, in Chapter 2, the game lockups. Everything else is HTML: the header, copy, icons, buttons, ads, the video and Share. [1]

**Rooms and scenes**

5. Your code tells Rive one thing per move: which scene to show. Rive plays the pan, the room's intro, its loop and the colour change on its own. [3, 4]
6. A room's intro plays only the first time the player reaches it with Next, and it lasts exactly 3.2 s. On any later visit the room slides in already built, with no intro. [5, 8]
7. After its intro a room loops until the next tap. A loop never freezes while the room leaves, and a room that comes back is already moving. [5]
8. A picture is an empty room with only a wall and a floor: no intro, no props. Ads, the switches between files and the bridge use pictures. [5]
9. When the scene changes to a room with different wall and floor colours, the colours crossfade over 1.45 s, starting at the tap. Your code does nothing for this. [4]
10. Setting the scene to the one already showing does nothing. Never rely on it to restart a room. [3]
11. Set the properties in this order: `direction`, `lockup`, `reveal`, then `scene`. [4]
12. A card inside the same room as the one before it changes only the HTML. Rive keeps looping and your code sets nothing, except Chapter 4's `reveal`. [4, 8]

**Moving between cards**

13. Next pans the camera right and Back pans it left, the exact mirror. A pan takes 1.6 s; treat it as 1.65 s. [9]
14. A pan cannot reverse part-way. Your code holds a Back during any pan, and a Next during a Back pan, until the pan ends; only the last tap held counts. A Next during a Next pan goes ahead at once. [9]
15. Back on Start does nothing, Back never returns to Loading, and Next on the last card does nothing. [6, 10]

**When copy appears** [8 has every timing]

16. Never show a card's copy before its room has settled.
17. First visit to a room with an intro: 3.2 s after you set the scene. A community card has no lockup, so it uses a per-game time instead (about 2 s).
18. A room that comes back, or any picture: 1.65 s, when the pan ends.
19. Another card in the same room: 0.34 s, right after the old copy has cleared.
20. Chapter 4's reveal card: 1.45 s, after the wall's fade, forward and back.
21. A move that takes two pans, such as Chapter 2's last card to Chapter 3: 3.3 s back, 4.85 s forward the first time.
22. The old copy leaves at once on every tap. [12]
23. With reduced motion on, the text CSS turns every move into a 200 ms fade. The timings do not change. [12]

**The three files** [9]

24. Three files play back to back: File 1 (Loading, Start, ads, Chapter 1), File 2 (Chapter 2) and File 3 (Chapters 3 and 4, End).
25. Each file ends on an empty room and the next file opens on the same picture, so the switch is invisible.
26. Load File 1 at once and the others one after another behind it. Keep all three loaded and pause the one that is hidden. Hold a Next on the empty room until the next file has loaded.
27. Next into the next file: show its canvas and set its scene in the same frame. Back into the earlier file: pan the later file back to the shared picture, wait 1.65 s, then show the earlier file.
28. A move across files from a card that is not on the empty room takes two pans of 1.65 s each: the room pans out to the empty room, the other file takes over, and the new room pans in.

**Ads**

29. Ad 1, Ad 2 and the anonymous Ad 3 carry `ad: true`. Each one shows only the first time the player reaches it with Next.
30. After that, Back and Next skip it and land on the card on its other side. Work out the move from the card you land on: one move inside a file, or two across files.
31. Whether Back works while an ad is on screen is your choice.

**Chapter by chapter**

32. Start: set the scene when the stats have arrived and File 1 has loaded. The Loading bounce blends into the intro over 0.25 s, so the intro starts on your tap and Start's HTML arrives 3.2 s after it. "Let's go" is a normal Next. [6]
33. Chapter 2: a game's first card shows its lockup, drawn by Rive and gone by 3.2 s. A community card sets `lockup` to `false`. The small game icon is HTML and stays while the game's cards change. [4, 7, 12]
34. Chapter 2 to 3: subscribers have no card on the empty Chapter 3 room, so the tap on their last Chapter 2 card plays both moves. Anonymous players have Ad 3 there. [9]
35. Chapter 4: set `topGame` once File 3 has loaded. `reveal` is `false` on the first card (lighter wall, no fireworks) and `true` on the next two (the wall fades to the game's colour and its fireworks start). [4, 8]
36. End: a looping room. The Share card for subscribers is another card on the same room, in HTML. [7]

## What's new in this delivery

- **Ads show once.** Back and Next skip an ad the player has already seen, so ad cards need the `ad` tag (sections 6 to 9). This creates new moves: Chapter 1's first card back to Start (one move, copy at 1.65 s), Chapter 1's last card to the Chapter 2 opener and back (two moves, 3.3 s), and, for anonymous players, the first Chapter 3 card to the last Chapter 2 community card and back (two moves, 3.3 s).
- **Start's intro begins on the tap.** The Loading bounce blends into it over 0.25 s instead of finishing its bounce first, so Start's copy always arrives 3.2 s after you set the scene (section 6).
- **The Mini and The Midi in Chapter 4 are final.** They use The Crossword's fireworks on their own wall colours.
- **The Crossword's Chapter 4 wall now matches its Chapter 2 room** (6493E6). Every game's Chapter 4 wall now equals its Chapter 2 wall.
- **Animation polish in the Rive files.** The bird on Start lands with the ball, the balls in The Mini, The Midi and The Crossword move more smoothly, loops close cleanly, balls stay inside the phone frame, and Chapter 1's first ball comes out of the clock door. No property name or scene name changed, so none of this needs a code change.

## 1. What is Rive and what is HTML

**Rive contains only:**

- the rooms and scenes and their animations (the camera pans, the balls, the props);
- the Chapter 2 lockups (a game's icon plus its name) on the first card of each game, for subscribers and registered players.

**Everything on top is HTML:**

- the header (the NYT logo, "Year in Games" and the progress bar);
- the desktop arrows and the tap zones;
- Start's title, the "Let's go" button and the sponsor line;
- all card copy, stats and variants;
- every other game icon (the small icon that stays while a game's cards change, and the icons on Chapter 3's cards);
- Chapter 3's badges and the Crossplay button;
- Chapter 4's top-game icon and text;
- the ads, the video and Share.

The How-to overlay (mobile only) will be a separate small Rive file, coming later (section 11).

## 2. The big picture

- **One stage behind every slide.** The Rive animation sits behind all the slides and stays on screen. When the player taps, the stage changes rooms (the camera pans), and the page shows the next card's copy on top.
- **Three Rive files, played back to back.** The player never sees a file change, because each file ends on a picture of an empty room and the next file starts on exactly the same picture.

  | File | `.riv` | Covers |
  |---|---|---|
  | File 1 | `start-chapter-1.riv` | Loading, Start, Ad 1, Chapter 1, Ad 2 |
  | File 2 | `chapter-2.riv` | Chapter 2 (the opener, the games, Chapter 2.5), ending on the empty Chapter 3 room |
  | File 3 | `chapters-3-4-end.riv` | Chapter 3, Chapter 4, End |

- **One artboard per file, 1495 × 1067, the same on every device.** Your page decides the crop and scaling. Keep x 560 to 935 and y 0 to 812 visible: the balls stay inside that area, and other pieces may reach beyond it.
- **Every file has the same names.** The state machine is named `Backdrop` and the view model is named `Backdrop`, in all three files.
- **You set a few view model properties, and nothing else.** There are no Rive events to listen to. Every timing is a fixed number, listed in section 8, that your code uses; the Rive side moves on its own after a property changes.

## 3. Starting a file

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

## 4. The properties

All three files have `scene` and `direction`. File 2 also has `lockup`; File 3 also has `topGame` and `reveal`. Enum values are set by name.

| Property | Type | File | What it does |
|---|---|---|---|
| `direction` | enum: `forward`, `back` | all | `forward` for Next, `back` for Back. The camera pans right on `forward` and left on `back`; Back is the exact mirror of Next. |
| `lockup` | boolean, default `true` | File 2 | `true` shows a game's lockup (its icon and name, in Rive). `false` hides it. Community cards set it to `false`. It is read only at the moment a game's scene is entered. |
| `reveal` | boolean, default `false` | File 3 | Chapter 4 only. `false` on the first Chapter 4 card (the stack and the ball on the lighter blue wall); `true` from the top-game card on (the wall fades to the top game's colour and that game's fireworks start). Back to the first card sets it to `false` again. |
| `topGame` | enum: `wordle`, `connections`, `strands`, `spelling-bee`, `mini`, `midi`, `daily` | File 3 | The player's top game. Chooses Chapter 4's wall colour and fireworks. Default `wordle`. Set it once, as soon as File 3 has loaded, from the stats (anonymous players: always `wordle`). |
| `scene` | enum, see section 5 | all | Which room the stage shows. |

**The order to set them in: `direction`, then `lockup`, then `reveal`, then `scene`.** `scene` is the one that starts the move, and the others are read when it changes, so they must already be right.

Rules of thumb:

- Only set a value that the card names. A card inside the same room changes no Rive property at all, except Chapter 4's `reveal` (section 8).
- `topGame` and `reveal` are File 3's. `lockup` is File 2's. File 1 has only `scene` and `direction`.
- Do not set a `scene` that belongs to another file. An unknown name throws.

## 5. The scenes in each file

A **room** has an intro that plays the first time the player arrives (always exactly 3.2 s), then loops until the player taps. A **picture** is an empty room: no intro, nothing in it, only the wall and floor colours; it is where ads play. Files 2 and 3 start on a picture, and every file ends on one. Every room comes back already built when the player returns to it with Back.

### File 1: `start-chapter-1.riv`

The wall is cream `#F1ECC0` and the floor orange `#FF811E` in every File 1 scene, so no colour ever changes.

| `scene` | Kind | What the stage shows |
|---|---|---|
| `loading` | its own scene (the file's default) | The ball bouncing on the floor in the middle of the room. Plays while the stats load. |
| `start` | room | The same room as `loading`; the bird drops in and lands on the ball, then the two keep playing. No pan, no colour change. |
| `ad` | picture | The empty Chapter 1 room. Ad 1 and Ad 2 play here, and File 2 opens on this same picture. |
| `chapter-1-card-1` … `chapter-1-card-5` | room | Chapter 1's five rooms, one per card. |

### File 2: `chapter-2.riv`

The wall colour changes with each game; the floor is pink.

| `scene` | Kind | What the stage shows |
|---|---|---|
| `from-chapter-1` | picture (the file's default) | The empty Chapter 1 room, the picture File 1 ends on. |
| `intro` | room | Chapter 2's opener ("But that's not all"). No lockup. |
| `wordle`, `connections`, `spelling-bee`, `mini`, `midi`, `daily`, `strands` | room (with lockup) | One game's room. `daily` is The Crossword. |
| `bridge` | picture | Chapter 2.5's bridge card: an empty version of the opener's room. |
| `to-chapter-3` | picture | The empty Chapter 3 room, the picture File 3 opens on. Ad 3 plays here for anonymous players. |

### File 3: `chapters-3-4-end.riv`

| `scene` | Kind | What the stage shows |
|---|---|---|
| `ad` | picture (the file's default) | The empty Chapter 3 room (lavender wall, green floor). Chapter 3's badge cards use it. |
| `chapter-3` | room | Chapter 3's room. |
| `chapter-3-bird` | room | Just the ball, twice as big and in the centre, with the bird on top. |
| `chapter-4` | room | Chapter 4. `reveal` and `topGame` choose what it shows. |
| `end` | room | The End room, a looping scene thanking the player. |

## 6. Loading and Start (File 1)

1. **Load File 1 at once.** It opens on `loading`: the ball bounces in the middle of the room. The Rive side is only that bouncing ball; what your page shows over Loading is up to you, and it isn't designed yet. File 2 and File 3 load behind it, one after the other (section 9).
2. **Switch to Start when both are ready**: when the stats have arrived and File 1 has loaded, set `direction = forward` and then `scene = 'start'`. The Loading bounce blends into Start's intro over 0.25 s, so the intro starts on your tap, wherever the ball is in its bounce. The bird drops in and lands on the ball. There is no pan and no colour change. Start is a room: its intro takes 3.2 s from the moment you set `scene`, and Start's HTML ("Let's go" and the rest) arrives at 3.2 s.
3. **"Let's go" is an ordinary Next.** It sets `direction = forward` and `scene = 'ad'`. The ball and the bird pan out to the left, leaving the empty room. Show Ad 1 when the pan ends (1.65 s). The next ball the player sees is the one coming out of the cuckoo clock in Chapter 1's first card.
4. **Back never returns to Loading.** Back on Start does nothing. Ad 1 shows only the first time the player reaches it (section 9); after that, Back from Chapter 1's first card lands on Start, which comes back already built (its HTML arrives when the pan ends, 1.65 s).
5. If the player taps before File 1 has loaded, hold the tap until it has.
6. **On desktop (1025 px and wider), keep the Loading and Start HTML in the top part of the screen, clear of the ball and the bird.** The block is the lockup (The New York Times, Year in Games, the 2026 tiles), the progress bar or the "Let's go" button, and "Supported by T-Mobile". On phone and tablet (below 1025 px) it stays exactly as the design frames show it (the lockup at 197 px from the top of the 375 x 812 frame); the middle of a desktop window is where the ball and the bird are, so there the block has to move up. What the animation uses, in artboard units (the artboard is 1495 x 1067; a point at artboard y sits at `artboardTop + y / 1067 * artboardHeight` on screen, where the artboard fills the window and is centred on it, as in your `RiveBackground`):
   - **Highest point of anything: y 525** (the bird's hop on Start; measured 529, 4 units of margin). The Loading bounce tops out at y 568. The ball and the bird at rest on Start top out at y 600.
   - **The floor line is y 712**, with the ball and bird standing on it. Everything from y 525 down to the bottom of the artboard belongs to the animation; keep the HTML above y 525 (we leave about 28 px of gap above the hop).
   - **The bird's drop** starts above the top of the artboard and falls to its perch in about half a second (it crosses the top part of the screen, where the block sits, in the first 0.4 s of the drop). That one fast pass behind or in front of the block is expected.
   - Where this puts the block: at 1440 x 900 the artboard's y 525 is at 442 px from the top of the window; at 1280 x 720 it is at 353 px. The demo page in the package (`reference/example/`) puts the block 16 px from the top and, if the window is so short that it would not clear the hop, shrinks the whole block uniformly (its spacing is unchanged, the progress bar and the button stay in the same place within it). A working version is `layoutSplash()` in that demo page.

## 7. Building the card list

### The idea

- **One set of Rive files serves both flows.** Rive doesn't know who the player is. The flow only changes which cards are in the list and what the HTML says.
- **Build the card list once from the payload, chapter by chapter.** Each card names the file and scene it shows, plus the tags its HTML needs. Many cards share a room: a game has several cards, and a tap inside a game changes only the HTML while the room keeps looping.
- **One skip rule: a card that doesn't qualify is never added to the list, so nothing is skipped at runtime.** A game that doesn't qualify brings no cards, so its room is never visited. The cards inside a game follow the ranked list and thresholds in "Year in Games 2026: stats requirements by game"; that document decides them, so they are not repeated here.
- **A subscriber or registered player with no qualifying game gets the anonymous flow.** A qualifying game has 10 or more completed puzzles in 2026.
- **The order of the games is one constant.** Our default, in Chapter 2 and in Chapter 2.5's community cards, is:

  Wordle, Connections, Spelling Bee, The Mini, The Midi, The Crossword (card key `daily`), Strands.

  It is a default: you can override it by changing one constant (`GAME_ORDER` in `reference/react/src/cards.ts`). Rive plays any order, because each move just sets the next scene (we checked every move between neighbouring rooms in this order, forward and back, including Chapter 2.5 and the anonymous list). The games that have community cards are Wordle, Connections, Spelling Bee, The Mini and Strands (`COMMUNITY_GAMES`); The Midi and The Crossword have none.

### Each card in the list

A card carries what the Rive side needs and what the HTML side needs.

| For | Field | Meaning |
|---|---|---|
| Rive | `file` and `scene` | Which file and which scene the card shows (section 5). |
| Navigation | `ad` | `true` on Ad 1, Ad 2 and the anonymous Ad 3. An ad shows the first time the player reaches it with Next; after that Back and Next skip it (section 9). Not on the badge cards in Chapter 3, which are ordinary cards. |
| Rive | `direction` | Not stored on the card: it is `forward` on Next and `back` on Back, set on every move. |
| Rive | `lockup` | File 2 only. `true` unless the card is a community card (a community card sets it to `false`). |
| Rive | `topGame` | File 3 only, on the first Chapter 4 card: the player's top game (anonymous: `wordle`). Set once when File 3 loads. |
| Rive | `reveal` | File 3 only, on Chapter 4's cards: `false` on the first, `true` on the next two. |
| HTML | which copy | The card's index is the key to its copy block, and `icon` names the game icon block it shows with (the icon stays while a game's cards change). |
| HTML | first visit or not | Worked out from the list: the first time the player reaches a room with Next it is a first visit (the copy waits for the intro); coming back with Back it is not (section 8). |

### Subscribers and registered players

| Part | Always there | Only when | Order |
|---|---|---|---|
| Loading, Start, Ad 1 | all three | | `loading`, `start`, `ad` (File 1) |
| Chapter 1 | five cards | | `chapter-1-card-1` … `chapter-1-card-5` (File 1). Chapter 1 never skips a card. |
| Ad 2 | the ad | | `ad` (File 1) |
| Chapter 2 | the opener (`intro`) | each game the player qualifies in brings its cards | the opener, then the qualifying games in the game order (File 2, each game's scene, `lockup = true`) |
| Chapter 2.5 | | the player has **exactly one** qualifying game | after that game's cards: `bridge`, then a community card (`lockup = false`) for each other community game, in the game order, leaving out the player's own game |
| Chapter 3 | card 1 (`chapter-3`), card 2 (`chapter-3-bird`) | card 3 only if the player has event badges; card 4 only if the player has achievement badges | File 3: `chapter-3`, `chapter-3-bird`, then `ad` (event badges), `ad` (achievement badges). There is no card on the empty Chapter 3 room before them: the tap on the last Chapter 2 card plays both moves (section 9). |
| Chapter 4 | three cards | | `chapter-4` ×3: `reveal` false (with `topGame`), true, true |
| End | End card, Share card | | `end` ×2 |

### Anonymous players

| Part | Always there | Order |
|---|---|---|
| Loading, Start, Ad 1 | all three | `loading`, `start`, `ad` |
| Chapter 1 | five cards (never skipped) | `chapter-1-card-1` … `chapter-1-card-5` |
| Ad 2 | the ad | `ad` |
| Chapter 2 | the opener, then community cards (`lockup = false`) for **Connections, Spelling Bee, The Mini, Strands**. There is no Wordle card, because the anonymous Chapter 1 copy already covers Wordle. | `intro`, `connections`, `spelling-bee`, `mini`, `strands` (File 2) |
| Ad 3 | the ad, on the empty Chapter 3 room | `to-chapter-3` (File 2) |
| Chapter 3 | four cards, never skipped, in the same rooms as the subscribers' | `chapter-3`, `chapter-3-bird`, `ad`, `ad` (File 3). The third and fourth cards share the empty room (the fourth is the next card in that room). |
| Chapter 4 | three cards; the top game is always Wordle (`topGame = 'wordle'`); the video is the special one from all the editors | `chapter-4` ×3 |
| End | the End card (no Share card) | `end` |

Anonymous Chapter 3's cards, in order: (1) "There's plenty more to celebrate, too." in `chapter-3`; (2) "Crossplay, the Midi and bonus puzzles introduced new ways to play." with a "Download Crossplay app" button and the Connections, Crossword and Midi icons, in `chapter-3-bird`; (3) "Connections hit 1000 puzzles." with the 1000th badge, on the empty room; (4) "And Wordle turned 5 and fabulous." with the Wordle 5 icon, on the same empty room.

### Worked example 1: several games

A subscriber qualifies in Wordle (212 completed puzzles), Spelling Bee (64) and Strands (30), and has played a little Connections (7, which does not qualify). They have no event badges and 14 achievement badges, and their top game is Wordle. Say, for this example, that Wordle has 4 cards, Spelling Bee 2 and Strands 1; the real cards come from the stats requirements.

| # | Card | File | Scene | Tags |
|---|---|---|---|---|
| 0 | Loading | 1 | `loading` | |
| 1 | Start | 1 | `start` | |
| 2 | Ad 1 | 1 | `ad` | `ad` |
| 3–7 | Chapter 1, cards 1–5 | 1 | `chapter-1-card-1` … `-5` | |
| 8 | Ad 2 | 1 | `ad` | `ad` |
| 9 | Chapter 2 opener | 2 | `intro` | |
| 10–13 | Wordle, 4 cards | 2 | `wordle` | icon `wordle` |
| 14–15 | Spelling Bee, 2 cards | 2 | `spelling-bee` | icon `spelling-bee` |
| 16 | Strands | 2 | `strands` | icon `strands` |
| 17 | Chapter 3, card 1 | 3 | `chapter-3` | |
| 18 | Chapter 3, card 2 | 3 | `chapter-3-bird` | |
| 19 | Achievement badges | 3 | `ad` | (no event badges, so no card) |
| 20 | Chapter 4, card 1 | 3 | `chapter-4` | `topGame` wordle, `reveal` false |
| 21 | Chapter 4, top game | 3 | `chapter-4` | icon `wordle`, `reveal` true |
| 22 | Chapter 4, video | 3 | `chapter-4` | `reveal` true |
| 23 | End | 3 | `end` | |
| 24 | Share | 3 | `end` | |

There is no Chapter 2.5 (three qualifying games), and no card on the empty Chapter 3 room: the tap on card 16 plays both moves. Once Ad 1 and Ad 2 have been seen, Back from card 3 lands on card 1, Next from card 1 lands on card 3, Back from card 9 lands on card 7 (two moves) and Next from card 7 lands on card 9 (two moves).

### Worked example 2: one game (Chapter 2.5)

A subscriber qualifies only in Connections (120 completed puzzles; the rest under 10). They have no event badges and 3 achievement badges, and their top game is Connections. Say, for this example, that Connections has 5 cards; the real count comes from the stats requirements.

| # | Card | File | Scene | Tags |
|---|---|---|---|---|
| 0–8 | Loading, Start, Ad 1, Chapter 1 ×5, Ad 2 | 1 | as above | `ad` on Ad 1 and Ad 2 |
| 9 | Chapter 2 opener | 2 | `intro` | |
| 10–14 | Connections, 5 cards | 2 | `connections` | icon `connections` |
| 15 | Bridge | 2 | `bridge` | Chapter 2.5 |
| 16 | Community card: Wordle | 2 | `wordle` | `community`, icon `wordle` |
| 17 | Community card: Spelling Bee | 2 | `spelling-bee` | `community`, icon `spelling-bee` |
| 18 | Community card: The Mini | 2 | `mini` | `community`, icon `mini` |
| 19 | Community card: Strands | 2 | `strands` | `community`, icon `strands` |
| 20–21 | Chapter 3, cards 1–2 | 3 | `chapter-3`, `chapter-3-bird` | |
| 22 | Achievement badges | 3 | `ad` | |
| 23–25 | Chapter 4 ×3 | 3 | `chapter-4` | `topGame` connections; `reveal` false, true, true |
| 26–27 | End, Share | 3 | `end` | |

The player's own game (Connections) is left out of the community cards, and no room is visited twice.

### The anonymous list

| # | Card | File | Scene | Tags |
|---|---|---|---|---|
| 0–8 | Loading, Start, Ad 1, Chapter 1 ×5, Ad 2 | 1 | as above | `ad` on Ad 1 and Ad 2 |
| 9 | Chapter 2 opener | 2 | `intro` | |
| 10 | Community card: Connections | 2 | `connections` | `community`, icon `connections` |
| 11 | Community card: Spelling Bee | 2 | `spelling-bee` | `community`, icon `spelling-bee` |
| 12 | Community card: The Mini | 2 | `mini` | `community`, icon `mini` |
| 13 | Community card: Strands | 2 | `strands` | `community`, icon `strands` |
| 14 | Ad 3 | 2 | `to-chapter-3` | `ad`; the empty Chapter 3 room |
| 15 | Chapter 3, card 1 | 3 | `chapter-3` | |
| 16 | Chapter 3, card 2 | 3 | `chapter-3-bird` | |
| 17 | Chapter 3, card 3 | 3 | `ad` | the empty room |
| 18 | Chapter 3, card 4 | 3 | `ad` | the same empty room |
| 19–21 | Chapter 4 ×3 | 3 | `chapter-4` | `topGame` wordle; `reveal` false, true, true |
| 22 | End | 3 | `end` | |

Once Ad 3 has been seen, Back from card 15 lands on card 13 (two moves) and Next from card 13 lands on card 15 (two moves).

## 8. When the copy may appear

The HTML of a card must not appear before its room has settled. These numbers are fixed; they come from the Rive files.

| Situation | HTML appears |
|---|---|
| A room's first visit with Next (it has an intro): Start, a Chapter 1 card, a game with its lockup, `intro`, `chapter-3`, `chapter-3-bird`, `chapter-4`, `end` | **3.2 s** after you set `scene` (Start too: its intro begins on your tap) |
| A **community card** (no lockup), first visit | When the room's pieces have landed, per game: Wordle 2334 ms, Connections 2367 ms, Strands 1967 ms, Spelling Bee 2017 ms, The Mini 2084 ms. (The Midi and The Crossword have no community cards.) |
| Coming back to a room with **Back** (it slides in already built), or any picture (`ad`, `from-chapter-1`, `to-chapter-3`, `bridge`). Show an ad when the pan ends. | **1.65 s**: when the pan ends |
| Another card **inside the same room** (the next Wordle card) | **0.34 s**: right after the old copy has cleared (it clears in 340 ms). Nothing changes in Rive. |
| Chapter 4's **reveal card** (the second card, `reveal` becomes `true`) | **1.45 s**: the copy waits until the wall has finished fading to the game's colour. Back to the first card replays the fade (`reveal` becomes `false`), so the same 1.45 s applies; the third card (the video, `reveal` stays `true`) uses the normal 0.34 s. |
| A tap inside a room whose intro is still running | When the intro ends (the 3.2 s, or the community time), not before |
| Subscriber, last Chapter 2 card → Chapter 3 (two moves) | **4.85 s**: 1.65 s for the first move, then 3.2 s for Chapter 3's intro |
| Chapter 3 → Back to that Chapter 2 card (two moves) | **3.3 s**: two pans of 1.65 s |
| A move that skips a seen ad, inside one file (Chapter 1 card 1 ⇄ Start) | **1.65 s**: both rooms are already built |
| A move that skips a seen ad across files, in either direction (Chapter 1 card 5 ⇄ the opener; anonymous Chapter 3 card 1 ⇄ the last Chapter 2 community card) | **3.3 s**: two pans of 1.65 s |

The old copy leaves at once on every tap (it drifts up, or down on Back, and dissolves within 340 ms).

The pan is 1.6 s long; wait 1.65 s to be safe. 3.2 s applies only to the first visit of a room: a room the player has already seen comes back built.

## 9. Moves, files and Back

### One move

For a move that stays inside a file, set `direction`, the properties the card names (`lockup`, `reveal`), then `scene`. The stage does the rest.

### Ads are shown once

An ad (a card tagged `ad`: Ad 1, Ad 2 and the anonymous Ad 3) shows the first time the player reaches it with Next. After that, Back and Next both skip it and land on the card on its other side. Keep a set of the ads reached; when a tap would land on a seen ad, step over it. Work out the move from the card the tap lands on: one move inside a file, or the two-move crossing below. Whether Back is allowed while an ad is on screen is your choice.

### A Back during a move waits

The files cannot turn a room around in the middle of a pan. So:

- a **Back during any pan**, and a **Next during a Back pan**, must wait until the pan has ended (1.65 s after it started), and only the last tap held counts;
- a **Next during a Next pan** goes ahead at once.

### Switching between the three files

Files 2 and 3 start on an empty picture, and every file ends on one. The neighbouring file shows the same picture:

| End of one file | Start of the next |
|---|---|
| File 1's last picture, `ad` (Ad 2) | File 2's first picture, `from-chapter-1` |
| File 2's last picture, `to-chapter-3` | File 3's first picture, `ad` |

- **Load ahead.** Load File 1 at once; when it is ready, load File 2; when that is ready, File 3. Keep all three loaded for the whole visit, so Back across a file boundary never reloads. Hold a Next tap on the empty room until the next file has loaded.
- **Stack the canvases.** Each file has its own canvas, in the same place. Show one at a time. A file that is not on screen should be paused (`rive.pause()`), and played again when it is shown.
- **Next into the next file.** The next file is already sitting on the shared picture. In the same frame, show its canvas on top and set its `scene`. When the old canvas has been covered (after two animation frames), hide it and pause it.
- **Back into the earlier file.** The later file is on the shared picture. Set its `scene` to that picture (its first scene) with `direction = back` so it pans back to it, wait 1.65 s, then show the earlier file's canvas (which is still sitting on the same picture) and, if the card is not on that picture, set the earlier file's `scene` to the card's.
- **A card that is not on the empty picture takes two moves to cross.** Skipping a seen ad creates more of these: Back from the Chapter 2 opener to Chapter 1 card 5 (Ad 2 skipped), Next from card 5 to the opener, and, for anonymous players, Chapter 3 card 1 to the last Chapter 2 community card and back (Ad 3 skipped). They are the same two moves as the crossing below.
- **The subscriber crossing from Chapter 2 into Chapter 3, with no extra tap.** Subscribers and registered players have no card on the empty Chapter 3 room. The tap on their last Chapter 2 card takes two moves: first set File 2's `scene` to `to-chapter-3` (the room pans out), and after 1.65 s show File 3 and set its `scene` to the card's (`chapter-3`). If the player taps again before the second move starts, run it at once. Back is the same two moves in reverse. Anonymous players have Ad 3 as a card on that empty room instead, so their crossing is a single move.

## 10. Controls

- **Phones and tablets** (below 1025 px): tap zones. The left 25% of the screen is Back and the right 75% is Next.
- **Desktop** (1025 px and wider): no tap zones. Arrow buttons at the left and right edges of the window, 20 px in, centred vertically, do Back and Next. The art is `core/ui-desktop-button.svg`.
- Back on the first card, Next on the last card, or a tap before everything is ready, does nothing.

## 11. The How-to overlay (mobile only, coming later)

A small file, `how-to-mobile.riv`, will explain "tap right for Next, tap left for Back". It shows on mobile only, over the stage, if the player is idle on Chapter 1's first card. It is not in this package yet: it comes later, with its own short note. Desktop has no How-to file; the arrow buttons explain themselves.

## 12. The text CSS

`yig-text-motion.css` animates the copy with no JavaScript. You choose how finely to split each card's copy; there are three levels.

**Level 1, Block.** Put `yig-in` on the whole block (the `yig-text` element). The block rises in as one piece. Use it when you have no time to split the copy.

```html
<div class="yig-text yig-in">Your stat in one block of text.</div>
```

**Level 2, Per element.** Wrap each copy piece (the headline, the stat, the body) in `yig-mask` + `yig-line`, so each rises in turn, 120 ms after the one before. An icon in the block uses `yig-pop`; it takes its place in the same order and pops in instead of rising.

```html
<div class="yig-text yig-in">
  <img class="yig-pop" src="wordle.svg" alt="Wordle">
  <span class="yig-mask"><span class="yig-line">You solved 212 puzzles</span></span>
  <span class="yig-mask"><span class="yig-line">and won most in three guesses.</span></span>
</div>
```

**Level 3, Per line.** The designed line breaks: each line of the design is its own `yig-mask` + `yig-line`, so every line rises on its own beat. The markup is the same as level 2, with one piece per designed line. This level also uses the classes below.

| Class | When | What it does |
|---|---|---|
| `yig-in` | the card's copy should arrive | Waits `--yig-delay`, then rises in. Set `--yig-delay` (for example `3200ms`) on the element from the table in section 8. |
| `yig-quick` | the tap stayed inside the same room | The copy rises in right after the old copy has cleared (340 ms) instead of waiting. |
| `yig-after-icon` | a game's first card | The lines start one step after the game icon pops. |
| `yig-out` | the old copy leaves | It lifts out and dissolves (240 ms); hide it after `--yig-clear` (340 ms). Only do this to copy that has finished rising; copy that is still rising should simply be hidden. |
| `yig-back` | Back | The same moves, mirrored: copy comes down into place instead of up, and leaves downwards. |

The stagger comes from the position of each piece among the direct children of the block, so you add no index attributes. The game icon is its own block, one per game, outside the cards: `<div class="yig-icon"><span class="yig-pop">…</span></div>`. It pops in with the game's first card, stays while the game's cards change, and leaves with the last card's text when the next game starts. Community cards still show it. All the timings are variables at the top of the CSS file. With reduced motion, everything becomes a 200 ms fade.

## 13. The reference folder

`reference/` is optional: a working example of this guide, not something to copy.

| Path | What it is |
|---|---|
| `reference/react/` | A small React 18 + TypeScript example (`@rive-app/react-canvas` 4.20.1, CSS Modules) that does what the guide says. `src/useYigStage.ts` is the whole rule set in one hook, `src/cards.ts` builds the card list for a player (and holds `GAME_ORDER`), and `src/YigStage.tsx` draws the stage, the copy and the controls. |
| `reference/yig-integration.js` | The same rules as plain JavaScript. |
| `reference/example/` | A page that plays the whole experience, so you can see what the files do. |

**Run the example page.** Any static server will do; opening the page straight from disk will not load the `.riv` files. From the package folder (the one with `core/` and `reference/` in it):

```
python3 -m http.server 8000
```

Then open <http://localhost:8000/reference/example/>. It needs an internet connection, because the page loads the Rive runtime (2.27.3) from a CDN. Tap or click the right side to go forward and the left side to go back; at a desktop width use the arrow buttons, or the arrow keys. All copy on the page is placeholder.

Things to try (add them to the address):

- `?flow=anon` plays the anonymous flow.
- `?player=midi-only`, `connections-only` (Chapter 2.5), `several-games`, `all-seven` or `none` (no qualifying game, so the anonymous flow) changes the subscriber's games; the default is `wordle-only`.
- `?goto=3:chapter-4` jumps to the first card on a scene (`file:scene`), and `?jump=12` jumps to a card by number.

**Read or check the React example.** The Rive files are expected at `/yig/<file>.riv` (change `src/files.ts`), and `yig-text-motion.css` is imported once in `src/main.tsx`. To check it compiles on its own:

```
cd reference/react
npm install
npx tsc --noEmit
```

**Coming later.** These pieces are stand-ins or not built yet, and arrive as updated `.riv` files; the property names and your code do not change.

- The bridge room art (Chapter 2.5's `bridge` scene is an empty room for now).
- The room animation for Chapter 3's first card (it isn't showing yet; a stand-in ball hops there for now).
- The stand-in balls in Chapter 4.
- The bird-on-ball stand-in in `chapter-3-bird`.
- The How-to overlay (`how-to-mobile.riv`, mobile only; section 11).

## 14. A checklist

- `stateMachines: 'Backdrop'` (plural) on every file; `autoBind: true`.
- Build the card list once, chapter by chapter; a card that doesn't qualify is never added.
- Set `direction`, `lockup`, `reveal`, then `scene`.
- Never set the same scene value again expecting a restart: it does nothing.
- HTML at 3.2 s for a first visit; the per-game time for a community card; 1.65 s for a picture or a return; 0.34 s inside a room; 1.45 s for Chapter 4's reveal card.
- A Back during a pan waits for it.
- Keep every file loaded; pause the one that is hidden.
- Tag Ad 1, Ad 2 and the anonymous Ad 3 with `ad`: shown the first time only, skipped by Back and Next after that; work out the move (one move, or two across files) from the card landed on.
- Subscribers have no card on the empty Chapter 3 room; the last Chapter 2 card's tap plays both moves.
- Anonymous players: community cards in Chapter 2 (no Wordle), Ad 3 on the empty Chapter 3 room, four Chapter 3 cards, `topGame = 'wordle'`.
