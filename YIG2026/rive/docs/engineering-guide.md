# Year in Games 2026: building with the Rive files

Everything you need to drive the three Rive files behind the Year in Games cards. Tested on Rive runtime 2.27.3, through `@rive-app/react-canvas` 4.20.1.

## What's new since Nov 3

### Renamed

| Setting | File | Old | New |
|---|---|---|---|
| `scene` | 1 | `chapter-1-card-1` | `chapter-1` |
| `scene` | 1 | `chapter-1-card-2` … `chapter-1-card-5` | `chapter-1-2` … `chapter-1-5` |
| `scene` | 2 | `intro` | `chapter-2` |
| `scene` | 2 | `daily` | `crossword` |
| `scene` | 2 | `bridge` | `chapter-2-community-intro` |
| `scene` | 3 | `chapter-3-bird` | `chapter-3-2` |
| `topGame` | 3 | `daily` | `crossword` |

`startScene` uses the same values as `scene`, so it has the same renames. Nothing else was renamed, and nothing was removed.

### New scenes

All five are in File 3. Each one replaces a scene that several cards used to share.

| Scene | Card | It replaces |
|---|---|---|
| `chapter-3-personal-badges` | Personal badges | `ad` |
| `chapter-3-event-badges` | Event badges, and both Anon badge cards | `ad` |
| `chapter-4-top-game` | Chapter 4's top-game card | `chapter-4` |
| `chapter-4-editor-video` | Chapter 4's video card | `chapter-4` |
| `share` | Share | `end` |

### Rules that changed

- Some scenes share a room. A move between them has no pan, and the copy waits 0.34 s. `chapter-3` to `chapter-3-2` is now one of these moves.
- Set `topGame` when File 3 loads, before `chapter-4-top-game`. Leave it unchanged through `chapter-4-editor-video`.
- The badge cards swapped places. Personal badges come first, then event badges.

This is the final engineering update. From here on, I'll only send updated Rive files, with no code changes needed.

## The files

| File | What it covers | Opens on |
|---|---|---|
| `start-chapter-1.riv` (File 1) | Loading, Start, Ad 1, Chapter 1, Ad 2 | `loading` |
| `chapter-2.riv` (File 2) | Chapter 2, Chapter 2.5, Ad 3 | `from-chapter-1` |
| `chapters-3-4-end.riv` (File 3) | Chapter 3, Chapter 4, End, Share | `ad` |

Each file is one 1495 × 1067 artboard. In every file, the state machine is `Backdrop` and the view model is `Backdrop`.

Load each file like this. Use the plural `stateMachines`: version 2.27.3 ignores the singular.

```ts
const { rive, RiveComponent } = useRive({
  src: '/yig/start-chapter-1.riv',
  stateMachines: 'Backdrop',
  autoplay: true,
  autoBind: true,
})
```

In `onLoad`, and on every window resize, call `rive.resizeDrawingSurfaceToCanvas()`. Then set a scene and a setting like this:

```ts
const vm = rive.viewModelInstance
vm.enum('direction').value = 'forward'
vm.boolean('lockup').value = false
vm.enum('scene').value = 'connections'
```

## Settings

All settings are on the `Backdrop` view model. Set them in this order: `direction`, `lockup`, `reveal`, `scene`. Set only the ones the card has.

| Setting | File | Values | What it does |
|---|---|---|---|
| `direction` | all | `forward`, `back` | `forward` on Next, `back` on Back. |
| `lockup` | 2 | `true` (default), `false` | `false` hides the game's name and icon in Rive, for community cards. |
| `reveal` | 3 | `false` (default), `true` | `true` turns Chapter 4's wall the top game's colour. |
| `topGame` | 3 | `wordle`, `connections`, `strands`, `spelling-bee`, `mini`, `midi`, `crossword` | The player's top game. Anon is always `wordle`. |
| `scene` | all | the scenes below | The scene to show. Setting it starts the move. |
| `startScene` | all | the same values as `scene` | Opens the file directly on a scene. Set it only in `onLoad`. |

## Scenes

In flow order. Regi/Sub means a registered player or a subscriber. Anon means an anonymous player. A game qualifies with 10 or more completed puzzles in 2026. A Regi/Sub player with no qualifying game gets the Anon cards.

| Scene | File | Regi/Sub cards | Anon cards | Skip when |
|---|---|---|---|---|
| `loading` | 1 | Loading | Loading | Never. |
| `start` | 1 | Start | Start | Never. |
| `ad` | 1 | Ad 1, Ad 2 | Ad 1, Ad 2 | The player has already seen that ad. |
| `chapter-1`, `chapter-1-2` … `chapter-1-5` | 1 | The five Chapter 1 cards, one scene each | Same | Never. |
| `from-chapter-1` | 2 | No card | No card | Always. File 2 opens here. |
| `chapter-2` | 2 | Chapter 2 opener | Chapter 2 opener | Never. |
| `wordle`, `connections`, `spelling-bee`, `mini`, `midi`, `crossword`, `strands` | 2 | Each qualifying game's cards, `lockup` true. In Chapter 2.5, one community card for each other community game, `lockup` false. | One community card each for Connections, Spelling Bee, The Mini and Strands, `lockup` false | The game doesn't qualify. The Midi and The Crossword have no community cards. |
| `chapter-2-community-intro` | 2 | Chapter 2.5's first card | No card | The player doesn't have exactly one qualifying game. |
| `to-chapter-3` | 2 | No card | Ad 3 | Regi/Sub: always. Anon: the player has already seen Ad 3. |
| `ad` | 3 | No card | No card | Always. File 3 opens here. It is not Ad 3. |
| `chapter-3` | 3 | First Chapter 3 card | Same | Never. |
| `chapter-3-2` | 3 | Second Chapter 3 card | Same | Never. |
| `chapter-3-personal-badges` | 3 | Personal badges | No card | The player has no personal badges. |
| `chapter-3-event-badges` | 3 | Event badges | Both badge cards | Regi/Sub: the player has no event badges. Anon: never. |
| `chapter-4` | 3 | First Chapter 4 card, `reveal` false | Same | Never. |
| `chapter-4-top-game` | 3 | Top-game card, `reveal` true | Same | Never. |
| `chapter-4-editor-video` | 3 | Video card, `reveal` true | Same | Never. |
| `end` | 3 | End | End | Never. |
| `share` | 3 | Share | No card | Anon: always. |

## Rules

1. Build the card list once, from the stats, and leave out every card the Scenes table says to skip.
2. The number of cards for each game follows "Year in Games 2026: stats requirements by game".
3. Chapter 2's games go in this order: Wordle, Connections, Spelling Bee, The Mini, The Midi, The Crossword, Strands. You can change it; the files play any order.
4. Each card has its file, its scene, and any setting it needs (`lockup`, `reveal`, `topGame`).
5. On every Next or Back, set `direction`, then `lockup` or `reveal` if the card has one, then `scene`.
6. When the next card has the same scene, set nothing in Rive and change only the HTML.
7. Setting a value that is already set does nothing. Setting a scene from another file throws an error.
8. A room plays its intro only the first time the player reaches it with Next.
9. A move to another room pans right on Next and left on Back, and takes 1.65 s.
10. A Back during any pan, or a Next during a Back pan, waits until the pan ends, and only the last waiting tap counts.
11. A Next during a Next pan runs at once.
12. Back on Start does nothing, Back never goes to Loading, and Next on the last card does nothing.
13. Show each ad only the first time the player reaches it with Next; after that, Back and Next step over it.
14. When the stats and File 1 are ready, go from `loading` to `start` as a normal Next.
15. "Let's go" on Start is a normal Next to Ad 1.
16. Load File 1 first, then File 2, then File 3, and keep all three loaded.
17. Stack the three canvases in the same place, show one at a time, and pause the hidden ones.
18. Files hand over on matching scenes: File 1's `ad` matches File 2's `from-chapter-1`, and File 2's `to-chapter-3` matches File 3's `ad`.
19. Hold a Next on a file's last scene until the next file has loaded.
20. On Next into the next file, show its canvas and set its `scene` in the same frame, then hide and pause the old canvas two animation frames later.
21. On Back into the earlier file, set the later file's `scene` to its first scene with `direction` set to `back`, then after 1.65 s show the earlier file and set the card's scene.
22. Crossing files from a card that isn't on a matching scene takes two moves: pan to the matching scene, then after 1.65 s the other file pans in.
23. If the player taps again before that second move starts, start it at once.
24. To open one file on any scene, set these in `onLoad`: `topGame` and `reveal` (File 3 only), then `startScene`, then `scene` to the same value.
25. A file opened with `startScene` shows the scene already built, with no intro, and `startScene` must not change after that.
26. If you mount one file at a time, open the next file with `startScene` on the matching scene, and swap the canvases two animation frames after it has drawn.
27. Keep at least artboard x 560 to 935 and y 0 to 812 on screen.
28. On screens 1025 px wide and wider, keep the Loading and Start HTML above artboard y 525.
29. Point the tail of the `chapter-1-5` speech bubble at Wordle Bot's head, at artboard x 755.7, y 376.5.
30. To place HTML on the artboard, use screen x = artboard left + x ÷ 1495 × artboard width, and screen y = artboard top + y ÷ 1067 × artboard height.
31. Below 1025 px, the left 25% of the screen is Back and the right 75% is Next.
32. From 1025 px, use the arrow buttons in `core/ui-desktop-button.svg`, 20 px in from each side and centred top to bottom.

## Copy timing

Each card's copy appears a set time after you set `scene`. The old copy leaves at once.

| Change | Wait |
|---|---|
| A room's first visit with Next | 2.0 s |
| A Chapter 2 game's first card, first visit, with `lockup` true | 3.2 s |
| `chapter-4` to `chapter-4-top-game`, and back | 1.45 s |
| The same scene again, or a scene that shares the room: `chapter-3` and `chapter-3-2`; `ad` and the two badge scenes; `chapter-4-top-game` and `chapter-4-editor-video`; `end` and `share` | 0.34 s |
| Anything else: a room seen before, a Back to another room, an ad, `chapter-2-community-intro`, or a badge scene | 1.65 s |
| Two moves across files | 3.65 s on Next to a new room, 3.3 s otherwise |

- A tap before the copy appears doesn't restart the wait.
- Show an ad when its pan ends.
- A file opened with `startScene` has seen none of its rooms. Next into one of them is a first visit.

**Using the CSS** (`core/yig-text-motion.css`):

- Put each card's copy in a `yig-text` block.
- Wrap each designed line as `<span class="yig-mask"><span class="yig-line">…</span></span>`.
- Set `--yig-delay` on the block to the wait, then add `yig-in`.
- Put the game icon in its own block: `<div class="yig-icon"><span class="yig-pop">…</span></div>`. It pops in with the game's first card and stays for that game's cards.
- The CSS holds the waits as `--yig-first-visit` (2.0 s), `--yig-lockup` (3.2 s) and `--yig-clear` (0.34 s).
- The first 8 lines of a block rise one after another.
- With reduced motion, every move is a 200 ms fade, and the waits stay the same.

| Class | When to add it | What it does |
|---|---|---|
| `yig-quick` | The scene stays in the same room | The copy rises as soon as the old copy clears. No delay needed. |
| `yig-after-icon` | The game icon arrives with this card | The lines start one step after the icon. |
| `yig-out` | The old copy leaves | The copy lifts out. Hide it after 340 ms. Hide copy that is still rising right away. |
| `yig-back` | On Back | The copy comes down into place instead of up. |

## What stays fixed

Scene names, settings, their values, the waits and the positions in this guide won't change. New `.riv` files keep the same names. Swap in the new files; your code doesn't change.
