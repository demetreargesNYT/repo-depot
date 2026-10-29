# Year in Games 2026: the experience

How the whole recap flows, for both audiences, and how it maps to the Rive files. This is the product picture behind `docs/rive-plan.md`. When the two disagree, ask Demetre; don't guess.

## Basics

- **Format.** A tap-through story, like a Wrapped recap. Tap the right half of the screen for Next, the left half for Back.
- **One stage for every device.** Each Rive file uses one 1495 × 1067 artboard for desktop and mobile. Phones show the centre 375 wide. The stats, copy and icons are HTML, layered over the Rive stage.
- **Data.** While Loading shows, the site loads the player's stats from the Games API. The stats fill every variable, decide which cards the player sees and in what order, and pick card variants.
- **Two audiences.** Subscribers and registered players get a personalized experience. Anonymous players get the same structure with all-player (aggregate) stats.
- **Ads.** Ads (sponsor: T-Mobile) play between some chapters, over an empty Rive room: the props leave, and the wall and floor stay.
- **How-to overlay.** Explains tap right for Next and tap left for Back. It shows if the player is idle on Chapter 1's first card. It's two small Rive files, mobile and desktop, served by breakpoint over the stage.

## Subscriber and registered flow

| # | Part | What happens |
|---|---|---|
| 1 | Loading | Stats load from the Games API. |
| 2 | Start | "Year in Games 2026", a "Let's go" button, "Supported by T-Mobile". Same room as Chapter 1. |
| 3 | Ad 1 | Over the empty Chapter 1 room. |
| 4 | Chapter 1 | Up to five cards with personal copy: the first puzzle of the year, longest streak, total puzzles, number of games played. Some have thresholds (for example the streak card shows only above 10 days), so Chapter 1 cards can be skipped too. Five rooms on the same cream wall and orange floor. How-to overlay on card 1. |
| 5 | Ad 2 | Over the empty Chapter 1 room. |
| 6 | Chapter 2 | The longest chapter. An opener ("But that's not all"), then each game the player played, in the player's order. See "Chapter 2 rules". Pink floor; the wall color changes with each game. |
| 7 | Chapter 3 | Short: badges and launches. Slots: the Midi (and Crossplay) launch card, Wordle turned 5, Connections' 1000th puzzle, and skill badges. The player sees the cards their badges and play allow. Badges are HTML. Lavender wall, green floor. |
| 8 | Chapter 4 | The player's top game of the year: card 2 shows that game's icon and text, with that game's Rive version. Then that game's video plays (HTML). Mustard floor. |
| 9 | End | A looping Rive room, thanking the player. Orange floor. |
| 10 | Share | HTML. |

There's no ad between Chapters 2, 3 and 4 in this flow, so those handoffs between Rive files need to be invisible.

## Chapter 2 rules

- **Seven games.** Wordle, Connections, Spelling Bee, Strands, and the three crosswords: The Mini, The Midi and The Crossword (card key `"daily"`).
- **Order.** The opener comes first, then the games the player completed 10 or more puzzles in, in the player's order.
- **Chapter 2.5 (subscribers and registered).** After the player's own games, a single bridge card explains what comes next, then the community fallback cards for the games they completed fewer than 10 puzzles in. A game appears in one section only. If the player has all seven games at 10 or more, Chapter 2.5 is skipped entirely. In Rive, the bridge card is one new scene: an empty version of the Chapter 2 opener's room (wall E7F1E1, pink floor), with its copy appearing when the pan ends. It's empty for now. Demetre will arrange its pieces and a ball (made from Chapter 1 and opener elements) on a separate "Bridge Art" artboard in the Chapter 2 Rive file, which doesn't export; they're animated into the bridge card during the finesse round. The 2.5 cards are community cards (no lockup). Anons don't see the bridge card; their Chapter 2 stays as it is (no Wordle card, since Chapter 1 carries the Wordle community stats).
- **10 or more completed puzzles in 2026.** "Completed" means finished, solved or not; for Spelling Bee it means reaching the Solid rank. The game gets its ranked set of cards, as listed per game in the stats requirements doc ("Year in Games 2026: stats requirements by game"). Chapter 2 shows at least 7 cards in total.
- **Fewer than 10 completed puzzles.** The game gets its one "Community fallback card" instead, an all-player stat (for example "In Wordle, the most popular starting word was ADIEU").
- **Never played.** The game doesn't appear.
- **Skipped cards.** If the player has no stat for a card, or doesn't meet its threshold, the card is skipped. Examples: Wordle win percentage shows only above 40%; the top starting words card shows 1 to 3 words and is skipped when no word was used more than once. A stat appears only once in a player's deck.
- **Variants.** Some cards have versions picked by a threshold. Example: Wordle's hardest word of the year has three versions: played and solved it, played and missed it, didn't play it. Variants are HTML only; the Rive room doesn't change.
- **Within a game,** a tap changes only the HTML copy, and the room keeps looping.
- **Between games,** a tap plays the Rive transition to the next game's room.
- **Lockup.** A game's first card opens with that game's lockup (icon plus word) in Rive. The small HTML icon then stays for the rest of that game's cards. Community cards skip the Rive lockup, but still show the small HTML icon.
- **Connections pills.** The solving-order pills follow the player's own order from the stats.

## Anonymous flow

| # | Part | Difference from the subscriber flow |
|---|---|---|
| 1–5 | Loading, Start, Ad 1, Chapter 1, Ad 2 | Same, with all-player copy (for example "Together, you all completed X million puzzles"). |
| 6 | Chapter 2 | The opener, then one community card per game, with no lockups. Every tap moves to the next game's room. The current mock shows Connections, Spelling Bee, The Mini and Strands. |
| 7 | Ad 3 | New for anons. It plays over the empty Chapter 3 room. |
| 8 | Chapter 3 | Highlights Connections' 1000th puzzle and Wordle's 5th birthday instead of badges. |
| 9 | Chapter 4 | The top game for everyone is Wordle. The video is a special one from all the editors. |
| 10 | End | Thanks the player and invites them to register for a personalized experience next year. |

## How it maps to Rive

Both flows use the same files; only the card list and the HTML copy differ. Full detail is in `docs/rive-plan.md`.

| Rive file | Covers |
|---|---|
| File 1 | Loading, Start, Ad 1, Chapter 1, Ad 2 |
| File 2 | Chapter 2, ending on the empty Chapter 3 room |
| File 3 | Ad 3 (anons), Chapter 3, Chapter 4 with all seven top-game versions, End |
| How-to | `how-to-mobile.riv` and `how-to-desktop.riv` |

**Engineering's side.** They build one card list from the stats, tag each card with what it shows (`game: "wordle"`, `community: true`, an ad, `topGame`), call `start(cards)`, then `onTap()` and `onBack()`. Our integration handles Rive, file loading and swapping, and text timing.

## How engineering's 2026 code is built

- The page is React and TypeScript, in the Games web code (`games-phoenix`, under `src/games/year-in-games/`). The apps show the same web page inside a web view, so no native screens are needed.
- Confirmed with engineering (Oct 29): the Rive animation sits behind all the slides and stays on screen, changing rooms as the player taps, instead of one Rive file per slide.
- Engineering will write their own React code to drive the Rive files rather than use our integration file. We give them a written guide with every rule (what to set and in what order, timings, Back during a pan, switching between files) and a React reference example. Our integration file stays as a working reference.
- Their page uses an older Rive runtime (2.27.3; our files are tested on 2.45.0). Engineering is looking into upgrading.
- Because engineering builds the file switching from our guide, the move from Chapter 2 into Chapter 3 stays simple: Chapter 2 ends on the empty Chapter 3 room, then Chapter 3's room arrives. The single continuous motion is dropped.

## Not settled yet

- The bridge card's art (pieces and ball), to come on the "Bridge Art" artboard.

- Chapter 1's card copy for each flow, and how Start moves into Chapter 1.
- Chapter 3: which 2 of the 4 cards show, by badge.
- Chapter 4: card 1, and when the video takes over and gives the stage back.
- The full card list and variants for each game other than Wordle and Connections (they're in Figma).
- Art still to come: Loading, the How-to overlays, and Chapter 4 versions for The Mini and The Midi.
