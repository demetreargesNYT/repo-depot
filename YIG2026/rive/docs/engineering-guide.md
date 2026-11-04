# Year in Games 2026: driving the Rive files

This guide covers what your code needs to drive our three Rive files: what to load, what to set and in what order, when each card's copy appears, and how to handle Back. It was tested on Rive runtime 2.27.3, through `@rive-app/react-canvas` 4.20.1.

**What you need** is in `core/`: the three `.riv` files, this guide, `yig-text-motion.css` and the desktop arrow art (`ui-desktop-button.svg`). The `reference/` folder has optional working examples (section 9).

## What's new in this delivery

- **`startScene`**, a new property in all three files, lets a file open directly on any of its scenes, already built and looping. Use it if you mount one file at a time (section 8).
- **Copy arrives sooner on a first visit:** 2.0 s after you set the scene. A Chapter 2 game's first card with its lockup keeps 3.2 s (section 6).
- **Desktop Loading and Start:** keep their HTML above artboard y 525 (section 4).
- Chapter 1 animation polish. No code change.
- No property or scene name changed, so your current code keeps working.

## The rules

**The stage**

1. One Rive stage sits behind every card, from Loading to End. Rive changes the room underneath; your code changes the HTML on top.
2. Rive draws only the rooms (pans, balls, props, colour changes) and Chapter 2's game lockups. Everything else is HTML: the header, copy, icons, buttons, badges, ads, the video and Share.
3. Every file is one 1495 × 1067 artboard on every device. Your page sets the crop and scale. Keep at least x 560–935 and y 0–812 visible (the phone frame in the design); pieces beyond it may be cropped on narrow screens.

**Moves**

4. Each move, set `direction`, then `lockup` (File 2) or `reveal` (File 3) if the card names one, then `scene`. Rive plays the pan, the intro, the loop and the colour change on its own. There are no Rive events to listen for.
5. A room's intro plays only on its first visit with Next and lasts 3.2 s. On any later visit the room slides in already built.
6. A card in the same room as the one before changes only the HTML. Set nothing in Rive, except Chapter 4's `reveal`.
7. Setting a property to the value it already has does nothing. Setting the same `scene` never restarts a room.
8. Next pans right and Back pans left. A pan takes 1.6 s; treat it as 1.65 s.
9. A pan can't reverse part-way. Hold a Back during any pan, and a Next during a Back pan, until the pan ends; only the last held tap counts. A Next during a Next pan goes ahead at once.
10. Back on Start does nothing, Back never returns to Loading, and Next on the last card does nothing.

**When copy appears** (section 6)

11. There are four waits, timed from when you set the scene:
    - **A new room:** 2.0 s. A Chapter 2 game's first card with its lockup: 3.2 s, so the copy never overlaps the lockup.
    - **A room already built:** 1.65 s. Back, a room seen before, an empty room, or an ad.
    - **The same room:** 0.34 s.
    - **Chapter 4's reveal:** 1.45 s, forward and back.
12. Crossing two files in one tap adds two waits together: 1.65 + 2.0 = 3.65 s forward, 1.65 + 1.65 = 3.3 s back.
13. The old copy leaves at once on every tap.

**Files and ads** (section 7)

14. Three files play back to back. Each ends on an empty room, and the next opens on the same picture, so the switch is invisible.
15. Load File 1 at once and the others one after another behind it. Keep all three loaded; pause the hidden one.
16. Ad 1, Ad 2 and the anonymous Ad 3 show only the first time the player reaches them with Next. After that, Back and Next skip them.

## 1. Starting a file

Start each file with the **plural** option `stateMachines`. On 2.27.3 the singular `stateMachine` is ignored and the file won't play.

```ts
const { rive, RiveComponent } = useRive({
  src: '/yig/start-chapter-1.riv',
  stateMachines: 'Backdrop', // plural
  autoplay: true,
  autoBind: true, // so rive.viewModelInstance exists once the file has loaded
})
```

In `onLoad`, call `rive.resizeDrawingSurfaceToCanvas()`, and call it again on every window resize. Set properties by name: `rive.viewModelInstance.enum('scene').value = 'start'`, `rive.viewModelInstance.boolean('lockup').value = false`.

In every file, the state machine and the view model are both named `Backdrop`.

## 2. The properties

| Property | Type | File | What it does |
|---|---|---|---|
| `direction` | enum: `forward`, `back` | all | `forward` for Next, `back` for Back. |
| `lockup` | boolean, default `true` | 2 | `true` shows a game's lockup. Community cards set `false`. |
| `reveal` | boolean, default `false` | 3 | Chapter 4: `false` on the first card (lighter wall), `true` on the next two (the wall fades to the top game's colour and its fireworks start). |
| `topGame` | enum: `wordle`, `connections`, `strands`, `spelling-bee`, `mini`, `midi`, `daily` | 3 | The player's top game, for Chapter 4. Set once when File 3 loads. Anonymous: `wordle`. |
| `scene` | enum (section 3) | all | The room to show. Set it last; it starts the move. |
| `startScene` | enum, same values as `scene` | all | Set only in `onLoad`, to open on a scene (section 8). |

Set them in this order: `direction`, `lockup`, `reveal`, `scene`. Only set what the card names. A `scene` from another file throws.

## 3. The scenes

A **room** has an intro on its first visit, then loops. An **empty room** has only a wall and floor; ads and the file switches use them.

| File | `scene` | Kind |
|---|---|---|
| 1 `start-chapter-1.riv` | `loading` | the opening scene: the ball bouncing while stats load |
| | `start` | room (the bird lands on the ball; no pan) |
| | `ad` | empty room: Ad 1 and Ad 2 |
| | `chapter-1-card-1` … `chapter-1-card-5` | rooms |
| 2 `chapter-2.riv` | `from-chapter-1` | empty room: the file opens here |
| | `intro` | room: Chapter 2's opener (no lockup) |
| | `wordle`, `connections`, `spelling-bee`, `mini`, `midi`, `daily`, `strands` | rooms, with lockup. `daily` is The Crossword. |
| | `bridge` | empty room: Chapter 2.5's bridge card |
| | `to-chapter-3` | empty room: Ad 3 for anonymous players |
| 3 `chapters-3-4-end.riv` | `ad` | empty room: the file opens here; Chapter 3's badge cards |
| | `chapter-3`, `chapter-3-bird` | rooms |
| | `chapter-4` | room: `reveal` and `topGame` choose what it shows |
| | `end` | room |

## 4. Loading and Start

1. Load File 1 at once. It opens on `loading`. What your page shows over Loading is up to you.
2. When the stats have arrived and File 1 has loaded, set `direction = forward`, then `scene = 'start'`. Start's HTML arrives 2.0 s later.
3. "Let's go" is an ordinary Next to `ad` (Ad 1). Show the ad when the pan ends (1.65 s).
4. **Desktop (1025 px and wider):** keep the Loading and Start HTML above artboard y 525, clear of the ball and the bird. Artboard y sits at `artboardTop + y / 1067 * artboardHeight` on screen. At 1440 × 900 that's 442 px from the top of the window; at 1280 × 720, 353 px. The bird drops in past the block once, quickly; that's expected. `layoutSplash()` in `reference/example/` is a working version. Below 1025 px, keep the layout as designed.
5. **Chapter 1 card 5's speech bubble** points its tail at Wordle Bot's head. In artboard units, the head is at x 755.7, y 376.5 (the dome's centre x, and the top of the antenna tips). Place it the same way as item 4: x sits at `artboardLeft + x / 1495 * artboardWidth` on screen, y as above. *Card 5 is still being finessed; this may move.*

## 5. Building the card list

- **One set of files serves every player.** The flow only changes which cards are in the list and what the HTML says.
- **Build the list once, chapter by chapter.** A card that doesn't qualify is never added, so nothing is skipped at runtime. The cards within a game follow "Year in Games 2026: stats requirements by game".
- **A qualifying game** has 10 or more completed puzzles in 2026. A subscriber or registered player with none gets the anonymous flow.
- **The game order is one constant**, our default: Wordle, Connections, Spelling Bee, The Mini, The Midi, The Crossword, Strands. Change it in one place (`GAME_ORDER` in `reference/react/src/cards.ts`); Rive plays any order. Community cards exist for Wordle, Connections, Spelling Bee, The Mini and Strands.

Each card carries `file`, `scene`, any Rive values it names (`lockup`, `reveal`, `topGame`), and the tags its HTML needs: `ad` on Ad 1, Ad 2 and Ad 3; `community` on community cards; `icon` for the game icon its copy shows with.

### Subscribers and registered players

| Part | Cards | Scenes |
|---|---|---|
| Loading, Start, Ad 1 | always | `loading`, `start`, `ad` (File 1) |
| Chapter 1 | five, never skipped | `chapter-1-card-1` … `-5` |
| Ad 2 | always | `ad` |
| Chapter 2 | the opener, then each qualifying game's cards, in the game order | `intro`, then each game's scene (File 2) |
| Chapter 2.5 | only with **exactly one** qualifying game | `bridge`, then a community card for each other community game (`lockup = false`), leaving out the player's own |
| Chapter 3 | cards 1 and 2; card 3 with event badges; card 4 with achievement badges | `chapter-3`, `chapter-3-bird`, `ad`, `ad` (File 3) |
| Chapter 4 | three | `chapter-4` ×3: `reveal` false (with `topGame`), true, true |
| End | End, Share | `end` ×2 |

There's no card on the empty Chapter 3 room: the tap on the last Chapter 2 card plays both moves (section 7).

**Example: several games.** Wordle (4 cards), Spelling Bee (2) and Strands (1) qualify; 14 achievement badges, no event badges; top game Wordle.

| # | Card | File · scene |
|---|---|---|
| 0–2 | Loading, Start, Ad 1 | 1 · `loading`, `start`, `ad` |
| 3–7 | Chapter 1 ×5 | 1 · `chapter-1-card-1` … `-5` |
| 8 | Ad 2 | 1 · `ad` |
| 9 | Chapter 2 opener | 2 · `intro` |
| 10–16 | Wordle ×4, Spelling Bee ×2, Strands | 2 · `wordle`, `spelling-bee`, `strands` |
| 17–18 | Chapter 3 ×2 | 3 · `chapter-3`, `chapter-3-bird` |
| 19 | Achievement badges | 3 · `ad` |
| 20–22 | Chapter 4 ×3 | 3 · `chapter-4` |
| 23–24 | End, Share | 3 · `end` |

**Example: one game (Chapter 2.5).** Only Connections (5 cards) qualifies: cards 10–14 are Connections, 15 is `bridge`, and 16–19 are community cards for Wordle, Spelling Bee, The Mini and Strands. The rest follows the table above.

### Anonymous players

| # | Card | File · scene |
|---|---|---|
| 0–8 | Loading through Ad 2, as above | 1 |
| 9 | Chapter 2 opener | 2 · `intro` |
| 10–13 | Community cards: Connections, Spelling Bee, The Mini, Strands (no Wordle; Chapter 1 covers it) | 2 · each game's scene, `lockup = false` |
| 14 | Ad 3 | 2 · `to-chapter-3` |
| 15–18 | Chapter 3 ×4, never skipped | 3 · `chapter-3`, `chapter-3-bird`, `ad`, `ad` |
| 19–21 | Chapter 4 ×3, `topGame = 'wordle'` | 3 · `chapter-4` |
| 22 | End (no Share) | 3 · `end` |

## 6. When the copy appears

Each card's copy arrives a fixed time after you set `scene`.

| Wait | When |
|---|---|
| **2.0 s** | A new room: the first visit with Next (Start, Chapter 1, the opener, community cards, Chapter 3, Chapter 4's first card, End). The intro is still finishing; that's intended. |
| **3.2 s** | A Chapter 2 game's first card with its lockup (`lockup` true), first visit. |
| **1.65 s** | A room already built: Back, a room seen before, an empty room, an ad. Show an ad when the pan ends. |
| **0.34 s** | Another card in the same room. Nothing changes in Rive. |
| **1.45 s** | Chapter 4's reveal: `reveal` changes, forward or back. Chapter 4's third card uses 0.34 s. |

- **Crossing two files** in one tap adds two waits: 3.65 s forward (1.65 + 2.0), 3.3 s back (1.65 + 1.65). Skipping a seen ad across files is the same: 3.3 s.
- **A tap before the copy has arrived** doesn't restart the wait. The copy still arrives at its original time.
- **Keep 2.0 s and 3.2 s as one named constant each.** In our files they're `--yig-first-visit` and `--yig-lockup` in `core/yig-text-motion.css`, and `FIRST_VISIT_COPY_MS` and `LOCKUP_COPY_MS` in `reference/react/src/timing.ts`.

`reference/timing-demo.html` plays every case with stand-in rooms and opens with a double-click.

## 7. Files, ads and Back

**Ads are shown once.** Keep a set of the ads reached. When a tap would land on a seen ad, step over it, and work out the move from the card you land on. Whether Back works while an ad is on screen is your choice.

**Switching files.** Each file ends on the empty room the next one opens on:

| End of one file | Start of the next |
|---|---|
| File 1 `ad` | File 2 `from-chapter-1` |
| File 2 `to-chapter-3` | File 3 `ad` |

- **Stack the canvases** in the same place and show one at a time. Pause the hidden one; play it again when it's shown.
- **Hold a Next** on the empty room until the next file has loaded.
- **Next into the next file:** in the same frame, show its canvas and set its `scene`. After two animation frames, hide and pause the old one.
- **Back into the earlier file:** set the later file's `scene` to its first picture with `direction = back`. After 1.65 s, show the earlier file, and set its `scene` to the card's if the card isn't on that picture.
- **Two moves:** a crossing from a card that isn't on the empty room takes two pans. First pan out to the empty room, then after 1.65 s the other file takes over and pans in. If the player taps again before the second move starts, run it at once. This covers the subscriber's last Chapter 2 card to Chapter 3, and any seen ad skipped across files.

## 8. Opening a file on any scene (`startScene`)

For mounting one file at a time instead of keeping all three loaded. The file opens on the scene already built and looping, as if the player had come back to it: no intro, pan, colour fade or lockup.

In `onLoad`, before anything else:

1. File 3 only: set `topGame`, and on `chapter-4` set `reveal` to the card's value.
2. Set `startScene` to the scene.
3. Set `scene` to the same scene.

```ts
onLoad: () => {
  rive.resizeDrawingSurfaceToCanvas()
  const vm = rive.viewModelInstance
  vm.enum('startScene').value = 'wordle'
  vm.enum('scene').value = 'wordle'
}
```

Don't change `startScene` afterwards. The copy can show as soon as the canvas is on screen.

**Swapping files.** Mount the neighbour on the empty room the two files share (the table in section 7), with `startScene` and `scene` set to it. Mount it early, so it has loaded by the time the pan ends. Once it has drawn (two animation frames), swap the canvases and play the move.

**Timing after a mount.** A freshly mounted file has seen none of its rooms. Back into it brings rooms in built (1.65 s). Next into it plays the intro, so treat it as a first visit (2.0 s, or 3.2 s with a lockup).

## 9. Controls, text CSS and the reference folder

### Controls

- **Below 1025 px:** tap zones. The left 25% is Back and the right 75% is Next.
- **1025 px and wider:** arrow buttons at the left and right edges, 20 px in and centred vertically (`core/ui-desktop-button.svg`).

### The text CSS

`yig-text-motion.css` animates the copy with no JavaScript. Put `yig-in` on a `yig-text` block, and set `--yig-delay` on it from section 6. Every card uses per-line motion, with each designed line as its own piece. Block and per element are fallbacks if a card can't be split yet:

1. **Block:** the whole block rises as one piece.
2. **Per element:** wrap each piece in `<span class="yig-mask"><span class="yig-line">…</span></span>`; they rise 120 ms apart. An icon uses `yig-pop`.
3. **Per line:** the same markup, one piece per designed line, plus the classes below.

| Class | When | What it does |
|---|---|---|
| `yig-quick` | the tap stayed in the same room | Rises right after the old copy clears (0.34 s). |
| `yig-after-icon` | the game icon arrives with this card | Lines start one step after the icon pops. |
| `yig-out` | the old copy leaves | Lifts out; hide it after 340 ms. Copy still rising should just be hidden. |
| `yig-back` | Back | Mirrors the motion: copy comes down into place. |

The stagger covers the first 8 pieces of a block; no card should need more.

The game icon is its own block, one per game: `<div class="yig-icon"><span class="yig-pop">…</span></div>`. It pops in with the game's first card and stays while that game's cards change. With reduced motion, every move becomes a 200 ms fade; the timings don't change.

### The reference folder (optional)

| Path | What it is |
|---|---|
| `reference/timing-demo.html` | The copy timing and the Rive calls, with stand-in rooms. Opens with a double-click. |
| `reference/text-motion.html` | How the copy moves on each card, per line. Opens with a double-click. |
| `reference/example/` | The whole experience with the real files. |
| `reference/react/` | React 18 + TypeScript example. `src/useYigStage.ts` has every rule in one hook; `src/cards.ts` builds the card list. |
| `reference/yig-integration.js` | The same rules in plain JavaScript. |

To run the example, start any static server from the package folder (`python3 -m http.server 8000`) and open `http://localhost:8000/reference/example/`. It loads the Rive runtime from a CDN. Useful options: `?flow=anon`, `?player=connections-only` (or `several-games`, `midi-only`, `all-seven`, `none`), `?goto=3:chapter-4`, `?jump=12`, `?rive-only` (or the H key) hides all the HTML.

## Checklist

- `stateMachines: 'Backdrop'` (plural) and `autoBind: true` on every file.
- Build the card list once; never add a card that doesn't qualify.
- Each move: `direction`, `lockup`, `reveal`, then `scene`.
- Copy waits: 2.0 s for a new room (3.2 s with a lockup), 1.65 s for a room already built, 0.34 s for the same room, 1.45 s for the reveal. Crossing two files adds two waits.
- Hold a Back during a pan.
- Keep all three files loaded; pause the hidden one.
- Ads show once; Back and Next skip them after that.
- Opening on a scene: in `onLoad`, set `startScene`, then `scene` (File 3: `topGame` and `reveal` first).
