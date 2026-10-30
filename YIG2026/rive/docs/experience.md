# Year in Games 2026: the experience

How the whole recap flows, for both audiences, and how it maps to the Rive files. This is the product picture behind `docs/rive-plan.md`. When the two disagree, ask Demetre; don't guess.

## Basics

- **Format.** A tap-through story, like a Wrapped recap. On mobile, tap the right 75% of the screen for Next and the left 25% for Back (engineering's tap zones). On desktop, arrow buttons at the left and right edges of the window do Back and Next (HTML, not part of the Rive files).
- **One stage for every device.** Each Rive file uses one 1495 × 1067 artboard for desktop and mobile. Phones show the centre 375 wide. The stats, copy and icons are HTML, layered over the Rive stage.
- **Data.** While Loading shows, the site loads the player's stats from the Games API. The stats fill every variable, decide which cards the player sees and in what order, and pick card variants.
- **Two audiences.** Subscribers and registered players get a personalized experience. Anonymous players get the same structure with all-player (aggregate) stats.
- **Ads.** Ads (sponsor: T-Mobile) play between some chapters, over an empty Rive room: the props leave, and the wall and floor stay.
- **How-to overlay (mobile only).** Explains tap right for Next and tap left for Back. It shows if the player is idle on Chapter 1's first card. It's one small Rive file, `how-to-mobile.riv`, shown over the stage below the mobile breakpoint. Desktop has no How-to file: the arrow buttons explain themselves.

## Subscriber and registered flow

| # | Part | What happens |
|---|---|---|
| 1 | Loading | Stats load from the Games API. |
| 2 | Start | "Year in Games 2026", a "Let's go" button, "Supported by T-Mobile". Same room as Chapter 1. |
| 3 | Ad 1 | Over the empty Chapter 1 room. |
| 4 | Chapter 1 | Up to five cards with personal copy: the first puzzle of the year, longest streak, total puzzles, number of games played. Some have thresholds (for example the streak card shows only above 10 days), so Chapter 1 cards can be skipped too. Five rooms on the same cream wall and orange floor. How-to overlay on card 1. |
| 5 | Ad 2 | Over the empty Chapter 1 room. |
| 6 | Chapter 2 | The longest chapter. An opener ("But that's not all"), then each qualifying game in the player's order, then Chapter 2.5 for players with only one qualifying game. See "Chapter 2 rules". Pink floor; the wall color changes with each game. |
| 7 | Chapter 3 | Short. Subscribers and registered players see up to four cards ("Chapter 3 and Chapter 4 cards" below): the intro (the Chapter 3 room), the ball with the bird on top, event badges and achievement badges (HTML on the empty Chapter 3 room), the last two skipped when the player has none. Lavender wall, green floor. |
| 8 | Chapter 4 | The player's top game of the year, in three cards: the stack and the ball on a lighter blue wall; the wall tints to the top game's colour and that game's fireworks start; that game's video (HTML) on that game's colour. Mustard floor. |
| 9 | End | A looping Rive room, thanking the player. Orange floor. |
| 10 | Share | HTML. |

There's no ad between Chapters 2, 3 and 4 in this flow, so those handoffs between Rive files need to be invisible.

## Chapter 2 rules

- **Seven games.** Wordle, Connections, Spelling Bee, Strands, and the three crosswords: The Mini, The Midi and The Crossword (card key `"daily"`).
- **Qualifying game:** 10 or more completed puzzles in 2026. "Completed" means finished, solved or not; for Spelling Bee it means reaching the Solid rank. Which cards a player gets is engineering's logic, built from the stats payload.
- **Order.** The opener comes first, then each qualifying game in the player's order, with that game's ranked cards (listed per game in "Year in Games 2026: stats requirements by game"). Games that don't qualify don't appear in Chapter 2.
- **Chapter 2.5 (community fallback), only for players with exactly one qualifying game.** Players with two or more qualifying games skip it entirely. For a one-game player, after that game's own cards:
  1. The bridge card ("The rest of the world also came to play.") in its own empty room.
  2. Community cards for the other community games, in the order Wordle, Connections, Spelling Bee, The Mini, Strands, leaving out the player's own game. Each is a normal room transition with no lockup.
  A Midi or Crossword player sees all five community cards. No room is ever visited twice.
- **No qualifying game** (0 games, or every game under the threshold): the player gets the anon flow, with a few elements removed from the cards. Nothing changes in Rive.
- **In Rive, Chapter 2.5 adds one scene:** the bridge room, an empty version of the opener's room (wall E7F1E1, pink floor, floor line at 712), with the bridge copy appearing when the pan ends. A separate "Bridge Art" artboard (never exported) holds the empty room and a red ball for scale; Demetre arranges its pieces and ball there later, and they're animated in during the finesse round. 2.5 cards are community cards: no lockup.
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
| How-to | `how-to-mobile.riv` (mobile only; desktop uses the arrow buttons) |

**Engineering's side.** They build one card list from the stats, tag each card with what it shows (`game: "wordle"`, `community: true`, an ad, `topGame`), call `start(cards)`, then `onTap()` and `onBack()`. Our integration handles Rive, file loading and swapping, and text timing.

## How engineering's 2026 code is built

- The page is React and TypeScript, in the Games web code (`games-phoenix`, under `src/games/year-in-games/`). The apps show the same web page inside a web view, so no native screens are needed.
- Confirmed with engineering (Oct 29): the Rive animation sits behind all the slides and stays on screen, changing rooms as the player taps, instead of one Rive file per slide.
- Engineering will write their own React code to drive the Rive files rather than use our integration file. We give them a written guide with every rule (what to set and in what order, timings, Back during a pan, switching between files) and a React reference example. Our integration file stays as a working reference.
- Their page uses Rive runtime 2.27.3 (via @rive-app/react-canvas 4.20.1). All three of our files were tested on it and work: no upgrade needed. The file must be started with the plural option `stateMachines: "Backdrop"`; the singular is ignored on 2.27.3.
- Because engineering builds the file switching from our guide, the move from Chapter 2 into Chapter 3 stays simple: Chapter 2 ends on the empty Chapter 3 room, then Chapter 3's room arrives. The single continuous motion is dropped. **Subscribers have no card on the empty Chapter 3 room** (Demetre, 2026-10-29): the tap on their last Chapter 2 card plays both moves itself (the room pans out to the empty Chapter 3 room, File 3 takes over, and Chapter 3's room arrives right after, with no extra tap), and Back from Chapter 3 returns to that last Chapter 2 card. Anons keep Ad 3 as a card on the empty room.

## Not settled yet

- The bridge room's art (pieces and ball), to come on the "Bridge Art" artboard.


- Chapter 1's card copy for each flow, and how Start moves into Chapter 1.
- Chapter 3: the real copy and the badge art (the badges are HTML), and the second card's ball with the bird (a stand-in idea for now).
- Chapter 4: the video, and how the page takes over from the stage behind it.
- The full card list and variants for each game other than Wordle and Connections (they're in Figma).
- Art still to come: Loading, the mobile How-to overlay, and Chapter 4 versions for The Mini and The Midi.

## Chapter 3 and Chapter 4 cards (Figma frames, 2026-10-30)

Subscribers and registered players (frames: 10406:87455, 10500:106385, 10406:87479, 10406:87502 for Chapter 3; 10522:108393, 11729:47076, 10406:84746 for Chapter 4).

**Chapter 3** (File 3; the tap on their last Chapter 2 card plays the pan out to the empty Chapter 3 room and Chapter 3's room arrives):

| # | Card | Rive scene | Notes |
|---|---|---|---|
| 1 | Intro: "There's plenty more to celebrate, too." | `chapter-3` | The Chapter 3 room (disco ball, picture, frames, mobile with the bird, crib, gifts). |
| 2 | "Crossplay, the Midi and bonus puzzles gave you new ways to play." | `chapter-3-bird` | The room gives way to just the ball (twice the size, centred) with the bird sitting on top; the bird's own loop keeps running. A stand-in idea for now. |
| 3 | Event badges: "You also earned new badges" | `ad` (the empty room on the Chapter 3 colours) | The badges are HTML. Skipped if the player has no event badges. |
| 4 | Achievement badges: "...and bragging rights." | `ad` | The badges are HTML. Skipped if the player has no achievement badges. |

The example players in the review page cover every case: Wordle only has both badge cards, Midi only has event badges only, Several games has achievement badges only, All seven games has neither. Anons keep two cards in the Chapter 3 room.

**Chapter 4** (File 3, scene `chapter-4`; the property `reveal` says which card):

| # | Card | `reveal` | What the stage does |
|---|---|---|---|
| 1 | "But through it all, it's clear you play favorites." | false | The stack and the ball on the lighter blue wall (DFF3F0), mustard floor, no fireworks. |
| 2 | "In 2026, your top game was..." with the game's icon and name | true | The wall fades (1.45 s) to the top game's colour and that game's fireworks start looping from their opening. |
| 3 | The game's video and the editor's name | true | The stage stays on card 2's picture; the page covers it with the game's wall colour, flat, behind the video (the Figma frame has no stack or floor there). |

Going back to card 1 sets `reveal` back to false: the wall returns to the lighter blue and the fireworks stop. Anons: the top game is always Wordle, so after the first card it shifts to Wordle's colour (C3E2C0) and Wordle's fireworks; their video is the special one from all the editors. Wall colours: Wordle C3E2C0, Connections E1DBF5, Strands DFF3F0, Spelling Bee FFFDEF, The Mini 95BEFA and The Midi 7EAAF1 (placeholders until their art arrives), The Crossword C0D8F8.
