# Year in Games 2026: card flow

Every card in order, for both flows. Scenes, settings and waits are the ones in `engineering-guide.md` (its Settings, Scenes and Copy timing sections); this page lists them card by card. `direction` is set on every move, so it isn't listed. The first column is the frame's name in the design files.

## Rules

- A game qualifies with 10 or more completed puzzles, and Chapter 2 shows each qualifying game's cards in the order Wordle, Connections, Spelling Bee, The Mini, The Midi, The Crossword, Strands.
- A Regi/Sub player with no qualifying game gets the Anonymous cards.
- Chapter 2.5 shows only when the player has exactly one qualifying game: `chapter-2-community-intro`, then one community card for each community game except the one they qualified in.
- The community games are Wordle, Connections, Spelling Bee, The Mini and Strands.
- The Mini's community card stands in for all three crosswords (The Mini, The Midi and The Crossword), so it is dropped only when the one qualifying game is The Mini, and a player whose one game is The Midi or The Crossword sees all five.
- Anonymous Chapter 2 is fixed: the opener, then the community cards for Connections, Spelling Bee, The Mini and Strands (Wordle's is covered in Chapter 1), then Ad 3.
- Chapter 1 is five fixed cards, never skipped, with different copy for Anonymous.
- Anonymous shows `chapter-3-event-badges` twice in a row; Regi/Sub shows `chapter-3-personal-badges` only when earned, then `chapter-3-event-badges` only when earned.
- `topGame` is set once, when File 3 loads (the example reads it from the `chapter-4` card), and it is always `wordle` for Anonymous.
- The front end chooses the `chapter-4-editor-video` frame to match `topGame`; it is the same scene for every game.
- Cards with variants in the design files (`wordle--03a/b/c`, `spelling-bee--02a/b` and `--04a/b`, `strands--03a/b`) are one card slot, and which variant shows is a stats rule, not an animation rule; only one variant shows per player.
- The number of cards per game comes from the stats. A game's later cards drop when the player lacks the stat or misses its threshold (the stats requirements doc defines both).
- The three ads show once; after that Back and Next step over them (guide rule 14).
- A copy wait is counted from setting `scene`, for a Next that reaches the card for the first time; Back and revisits use the guide's Copy timing table.
- Which stat each card shows, and its threshold, is defined in "Year in Games 2026: stats requirements by game" (Games team), not here.

## Registered and subscribers

| Frame | File | Scene | Settings | Copy wait | Skip when |
|---|---|---|---|---|---|
| `loading` | 1 | `loading` | — | — | Never. |
| `start` | 1 | `start` | — | 2.0 s | Never. |
| `ad--1` | 1 | `ad` | — | 1.65 s | Ad: after the first time it is shown. |
| `chapter-1--intro` | 1 | `chapter-1` | — | 2.0 s | Never. |
| `chapter-1-2--total-solves` | 1 | `chapter-1-2` | — | 2.0 s | Never. |
| `chapter-1-3--first-puzzle` | 1 | `chapter-1-3` | — | 2.0 s | Never. |
| `chapter-1-4--longest-streak` | 1 | `chapter-1-4` | — | 2.0 s | Never. |
| `chapter-1-5--bot` | 1 | `chapter-1-5` | — | 2.0 s | Never. |
| `ad--2` | 1 | `ad` | — | 1.65 s | Ad: after the first time it is shown. |
| `chapter-2--intro` | 2 | `chapter-2` | — | 2.0 s | Never. |
| `wordle--01` | 2 | `wordle` | `lockup=true` | 3.2 s | Fewer than 10 completed puzzles in Wordle. |
| `wordle--02` | 2 | `wordle` | `lockup=true` | 0.34 s | Fewer than 10 completed puzzles in Wordle, or the stats requirements leave this card out. |
| `wordle--03a/b/c` | 2 | `wordle` | `lockup=true` | 0.34 s | Fewer than 10 completed puzzles in Wordle, or the stats requirements leave this card out. |
| `wordle--04` | 2 | `wordle` | `lockup=true` | 0.34 s | Fewer than 10 completed puzzles in Wordle, or the stats requirements leave this card out. |
| `connections--01` | 2 | `connections` | `lockup=true` | 3.2 s | Fewer than 10 completed puzzles in Connections. |
| `connections--02` | 2 | `connections` | `lockup=true` | 0.34 s | Fewer than 10 completed puzzles in Connections, or the stats requirements leave this card out. |
| `connections--03` | 2 | `connections` | `lockup=true` | 0.34 s | Fewer than 10 completed puzzles in Connections, or the stats requirements leave this card out. |
| `connections--04` | 2 | `connections` | `lockup=true` | 0.34 s | Fewer than 10 completed puzzles in Connections, or the stats requirements leave this card out. |
| `connections--05` | 2 | `connections` | `lockup=true` | 0.34 s | Fewer than 10 completed puzzles in Connections, or the stats requirements leave this card out. |
| `spelling-bee--01` | 2 | `spelling-bee` | `lockup=true` | 3.2 s | Fewer than 10 completed puzzles in Spelling Bee. |
| `spelling-bee--02a/b` | 2 | `spelling-bee` | `lockup=true` | 0.34 s | Fewer than 10 completed puzzles in Spelling Bee, or the stats requirements leave this card out. |
| `spelling-bee--03` | 2 | `spelling-bee` | `lockup=true` | 0.34 s | Fewer than 10 completed puzzles in Spelling Bee, or the stats requirements leave this card out. |
| `spelling-bee--04a/b` | 2 | `spelling-bee` | `lockup=true` | 0.34 s | Fewer than 10 completed puzzles in Spelling Bee, or the stats requirements leave this card out. |
| `mini--01` | 2 | `mini` | `lockup=true` | 3.2 s | Fewer than 10 completed puzzles in The Mini. |
| `mini--02` | 2 | `mini` | `lockup=true` | 0.34 s | Fewer than 10 completed puzzles in The Mini, or the stats requirements leave this card out. |
| `mini--03` | 2 | `mini` | `lockup=true` | 0.34 s | Fewer than 10 completed puzzles in The Mini, or the stats requirements leave this card out. |
| `mini--04` | 2 | `mini` | `lockup=true` | 0.34 s | Fewer than 10 completed puzzles in The Mini, or the stats requirements leave this card out. |
| `midi--01` | 2 | `midi` | `lockup=true` | 3.2 s | Fewer than 10 completed puzzles in The Midi. |
| `midi--02` | 2 | `midi` | `lockup=true` | 0.34 s | Fewer than 10 completed puzzles in The Midi, or the stats requirements leave this card out. |
| `midi--03` | 2 | `midi` | `lockup=true` | 0.34 s | Fewer than 10 completed puzzles in The Midi, or the stats requirements leave this card out. |
| `crossword--01` | 2 | `crossword` | `lockup=true` | 3.2 s | Fewer than 10 completed puzzles in The Crossword. |
| `crossword--02` | 2 | `crossword` | `lockup=true` | 0.34 s | Fewer than 10 completed puzzles in The Crossword, or the stats requirements leave this card out. |
| `crossword--03` | 2 | `crossword` | `lockup=true` | 0.34 s | Fewer than 10 completed puzzles in The Crossword, or the stats requirements leave this card out. |
| `crossword--04` | 2 | `crossword` | `lockup=true` | 0.34 s | Fewer than 10 completed puzzles in The Crossword, or the stats requirements leave this card out. |
| `strands--01` | 2 | `strands` | `lockup=true` | 3.2 s | Fewer than 10 completed puzzles in Strands. |
| `strands--02` | 2 | `strands` | `lockup=true` | 0.34 s | Fewer than 10 completed puzzles in Strands, or the stats requirements leave this card out. |
| `strands--03a/b` | 2 | `strands` | `lockup=true` | 0.34 s | Fewer than 10 completed puzzles in Strands, or the stats requirements leave this card out. |
| `strands--04` | 2 | `strands` | `lockup=true` | 0.34 s | Fewer than 10 completed puzzles in Strands, or the stats requirements leave this card out. |
| `chapter-2-community-intro` | 2 | `chapter-2-community-intro` | — | 2.0 s | The player doesn't have exactly one qualifying game. |
| `wordle--community` | 2 | `wordle` | `lockup=false` | 2.0 s | The player doesn't have exactly one qualifying game, or that game is Wordle. |
| `connections--community` | 2 | `connections` | `lockup=false` | 2.0 s | The player doesn't have exactly one qualifying game, or that game is Connections. |
| `spelling-bee--community` | 2 | `spelling-bee` | `lockup=false` | 2.0 s | The player doesn't have exactly one qualifying game, or that game is Spelling Bee. |
| `mini--community` | 2 | `mini` | `lockup=false` | 2.0 s | The player doesn't have exactly one qualifying game, or that game is The Mini. |
| `strands--community` | 2 | `strands` | `lockup=false` | 2.0 s | The player doesn't have exactly one qualifying game, or that game is Strands. |
| `chapter-3--intro` | 3 | `chapter-3` | — | 3.65 s | Never. |
| `chapter-3-2--new-ways-to-play` | 3 | `chapter-3-2` | — | 0.34 s | Never. |
| `chapter-3-personal-badges` | 3 | `chapter-3-personal-badges` | — | 1.65 s | The player has no personal badges. |
| `chapter-3-event-badges` | 3 | `chapter-3-event-badges` | — | 1.65 s, or 0.34 s straight after `chapter-3-personal-badges` | The player has no event badges. |
| `chapter-4--intro` | 3 | `chapter-4` | `reveal=false`, `topGame=<top game>` | 2.0 s | Never. |
| `chapter-4-top-game` | 3 | `chapter-4-top-game` | `reveal=true` | 1.45 s | Never. |
| `chapter-4-editor-video--<game>` | 3 | `chapter-4-editor-video` | `reveal=true` | 0.34 s | Never. |
| `end` | 3 | `end` | — | 2.0 s | Never. |
| `share` | 3 | `share` | — | 0.34 s | Never. |

## Anonymous

| Frame | File | Scene | Settings | Copy wait | Skip when |
|---|---|---|---|---|---|
| `loading--anon` | 1 | `loading` | — | — | Never. |
| `start--anon` | 1 | `start` | — | 2.0 s | Never. |
| `ad--1` | 1 | `ad` | — | 1.65 s | Ad: after the first time it is shown. |
| `chapter-1--intro--anon` | 1 | `chapter-1` | — | 2.0 s | Never. |
| `chapter-1-2--anon` | 1 | `chapter-1-2` | — | 2.0 s | Never. |
| `chapter-1-3--anon` | 1 | `chapter-1-3` | — | 2.0 s | Never. |
| `chapter-1-4--anon` | 1 | `chapter-1-4` | — | 2.0 s | Never. |
| `chapter-1-5--bot--anon` | 1 | `chapter-1-5` | — | 2.0 s | Never. |
| `ad--2` | 1 | `ad` | — | 1.65 s | Ad: after the first time it is shown. |
| `chapter-2--intro--anon` | 2 | `chapter-2` | — | 2.0 s | Never. |
| `connections--community` | 2 | `connections` | `lockup=false` | 2.0 s | Never. |
| `spelling-bee--community` | 2 | `spelling-bee` | `lockup=false` | 2.0 s | Never. |
| `mini--community` | 2 | `mini` | `lockup=false` | 2.0 s | Never. |
| `strands--community` | 2 | `strands` | `lockup=false` | 2.0 s | Never. |
| `ad--3` | 2 | `to-chapter-3` | — | 1.65 s | Ad: after the first time it is shown. |
| `chapter-3--intro` | 3 | `chapter-3` | — | 2.0 s | Never. |
| `chapter-3-2--new-ways-to-play` | 3 | `chapter-3-2` | — | 0.34 s | Never. |
| `chapter-3-event-badges--connections-1000` | 3 | `chapter-3-event-badges` | — | 1.65 s | Never. |
| `chapter-3-event-badges--wordle-5` | 3 | `chapter-3-event-badges` | — | 0.34 s | Never. |
| `chapter-4--intro` | 3 | `chapter-4` | `reveal=false`, `topGame=wordle` | 2.0 s | Never. |
| `chapter-4-top-game--anon` | 3 | `chapter-4-top-game` | `reveal=true` | 1.45 s | Never. |
| `chapter-4-editor-video--wordle` | 3 | `chapter-4-editor-video` | `reveal=true` | 0.34 s | Never. |
| `end--anon` | 3 | `end` | — | 2.0 s | Never. |
