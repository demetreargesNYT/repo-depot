# Year in Games 2026: the experience

How the whole recap flows, for both audiences, and how it maps to the Rive files. This is the product picture behind `docs/rive-plan.md`. When the two disagree, ask Demetre; don't guess.

## Basics

- **What is Rive and what is HTML (decided 2026-10-31).** Rive contains only the rooms and scenes, their animations, and the Chapter 2 lockups (a game's icon plus its name) on the first card of each game for subscribers and registered players. Everything on top is HTML: the header (NYT logo, "Year in Games", progress bar), the desktop arrows and tap zones, Start's title, button and sponsor line, all card copy, stats and variants, every other game icon, the Chapter 3 badges and the Crossplay button, Chapter 4's top-game icon and text, the ads, the video and Share. The How-to overlay (mobile only) will be a separate small Rive file, coming later.
- **One fixed game order for the whole experience (decided 2026-10-31):** Wordle, Connections, Spelling Bee, The Mini, The Midi, The Crossword (card key `daily`), Strands. It is our default and one constant in engineering's code (`GAME_ORDER`); Rive plays any order because each move just sets the next scene.
- **One skip rule.** A card that doesn't qualify is never added to the card list, so nothing is skipped at runtime; a game that doesn't qualify brings no cards, so its room is never visited. Subscribers and registered players with no qualifying game get the anonymous flow.
- **Format.** A tap-through story, like a Wrapped recap. On mobile, tap the right 75% of the screen for Next and the left 25% for Back (engineering's tap zones). On desktop, arrow buttons at the left and right edges of the window do Back and Next (HTML, not part of the Rive files).
- **One stage for every device.** Each Rive file uses one 1495 × 1067 artboard for desktop and mobile. Phones show the centre 375 wide. The stats, copy and icons are HTML, layered over the Rive stage.
- **Data.** While Loading shows, the site loads the player's stats from the Games API. The stats fill every variable, decide which cards the player sees and in what order, and pick card variants.
- **Two audiences.** Subscribers and registered players get a personalized experience. Anonymous players get the same structure with all-player (aggregate) stats.
- **Ads.** Ads (sponsor: T-Mobile) play between some chapters, over an empty Rive room: the props leave, and the wall and floor stay.
- **How-to overlay (mobile only).** Explains tap right for Next and tap left for Back. It shows if the player is idle on Chapter 1's first card. It's one small Rive file, `how-to-mobile.riv`, shown over the stage below the mobile breakpoint. Desktop has no How-to file: the arrow buttons explain themselves.

## Subscriber and registered flow

| # | Part | What happens |
|---|---|---|
| 1 | Loading | Stats load from the Games API. In Rive: the empty cream-and-orange room with the ball bouncing. What the page shows over it is up to engineering and isn't designed yet. |
| 2 | Start | "Year in Games 2026", a "Let's go" button, "Supported by T-Mobile" (HTML). In Rive: the same room as Loading, and the bird drops onto the ball. Same colours as Chapter 1. |
| 3 | Ad 1 | Over the empty Chapter 1 room. |
| 4 | Chapter 1 | Five cards, never skipped, in both flows. Subscriber and registered copy: "This year, you turned downtime into playtime." / "You played a total of X puzzles. Cheers, super solver." / "Your first puzzle was [game icon + name], [date, time]." / "And your longest streak was in [game] at X days. Keep the wins coming." / the "Did you know" robot card. Five rooms on the same cream wall and orange floor. How-to overlay on card 1. |
| 5 | Ad 2 | Over the empty Chapter 1 room. |
| 6 | Chapter 2 | The longest chapter. An opener ("But that's not all"), then each qualifying game in the fixed game order, then Chapter 2.5 for players with only one qualifying game. See "Chapter 2 rules". Pink floor; the wall color changes with each game. |
| 7 | Chapter 3 | Short. Subscribers and registered players see up to four cards ("Chapter 3 and Chapter 4 cards" below): the intro (the Chapter 3 room), the ball with the bird on top, event badges and achievement badges (HTML on the empty Chapter 3 room), the last two added only when the player has some. Lavender wall, green floor. |
| 8 | Chapter 4 | The player's top game of the year, in three cards: the stack and the ball on a lighter blue wall; the wall tints to the top game's colour and that game's fireworks start; that game's video (HTML) on that game's colour. Mustard floor. |
| 9 | End | A looping Rive room, thanking the player. Orange floor. |
| 10 | Share | HTML. |

There's no ad between Chapters 2, 3 and 4 in this flow, so those handoffs between Rive files need to be invisible.

## Chapter 2 rules

- **Seven games.** Wordle, Connections, Spelling Bee, Strands, and the three crosswords: The Mini, The Midi and The Crossword (card key `"daily"`).
- **Qualifying game:** 10 or more completed puzzles in 2026. "Completed" means finished, solved or not; for Spelling Bee it means reaching the Solid rank. Which cards a player gets is engineering's logic, built from the stats payload.
- **Order.** The opener comes first, then each qualifying game in the fixed game order (Wordle, Connections, Spelling Bee, The Mini, The Midi, The Crossword, Strands), with that game's ranked cards (listed per game in "Year in Games 2026: stats requirements by game"). Games that don't qualify don't appear in Chapter 2.
- **Chapter 2.5 (community fallback), only for players with exactly one qualifying game.** Players with two or more qualifying games don't get it. For a one-game player, after that game's own cards:
  1. The bridge card ("The rest of the world also came to play.") in its own empty room.
  2. Community cards for the other community games, in the same game order (Wordle, Connections, Spelling Bee, The Mini, Strands; only the games that have community cards), leaving out the player's own game. Each is a normal room transition with no lockup.
  A Midi or Crossword player sees all five community cards. No room is ever visited twice.
- **No qualifying game** (0 games, or every game under the threshold): the player gets the anon flow, with a few elements removed from the cards. Nothing changes in Rive.
- **In Rive, Chapter 2.5 adds one scene:** the bridge room, an empty version of the opener's room (wall E7F1E1, pink floor, floor line at 712), with the bridge copy appearing when the pan ends. A separate "Bridge Art" artboard (never exported) holds the empty room and a red ball for scale; Demetre arranges its pieces and ball there later, and they're animated in during the finesse round. 2.5 cards are community cards: no lockup.
- **Cards that don't qualify.** If the player has no stat for a card, or doesn't meet its threshold, the card is never added to the list. Examples: Wordle win percentage shows only above 40%; the top starting words card shows 1 to 3 words and isn't added when no word was used more than once. A stat appears only once in a player's deck.
- **Variants.** Some cards have versions picked by a threshold. Example: Wordle's hardest word of the year has three versions: played and solved it, played and missed it, didn't play it. Variants are HTML only; the Rive room doesn't change.
- **Within a game,** a tap changes only the HTML copy, and the room keeps looping.
- **Between games,** a tap plays the Rive transition to the next game's room.
- **Lockup.** A game's first card opens with that game's lockup (icon plus word) in Rive. The small HTML icon then stays for the rest of that game's cards. Community cards skip the Rive lockup, but still show the small HTML icon.
- **Connections pills.** The solving-order pills follow the player's own order from the stats.

## Anonymous flow

| # | Part | Difference from the subscriber flow |
|---|---|---|
| 1–5 | Loading, Start, Ad 1, Chapter 1, Ad 2 | Same, with all-player copy. Chapter 1 is five cards, never skipped: "In 2026, you brought your best game." / "Together, you all completed X million puzzles. That's some serious puzzle power." / "The most popular Wordle starting word was ADIEU. Oh là là!" / "And the word that stumped the most players was PSHAW. (n) An expression of disapproval or disbelief." / the "Did you know" robot card. |
| 6 | Chapter 2 | The opener, then community cards for Connections, Spelling Bee, The Mini and Strands (in the game order), with no lockups. No Wordle card, because anonymous Chapter 1 already covers Wordle (ADIEU and PSHAW). Every tap moves to the next game's room. |
| 7 | Ad 3 | New for anons. It plays over the empty Chapter 3 room. |
| 8 | Chapter 3 | Four cards, never skipped, in the same rooms as the subscribers': the room, the ball with the bird (with a "Download Crossplay app" button and the Connections, Crossword and Midi icons), "Connections hit 1000 puzzles." with the 1000th badge, and "And Wordle turned 5 and fabulous." with the Wordle 5 icon, the last two on the empty Chapter 3 room. See "Chapter 3 and Chapter 4 cards". |
| 9 | Chapter 4 | The top game for everyone is Wordle. The video is a special one from all the editors. |
| 10 | End | Thanks the player and invites them to register for a personalized experience next year. There is no Share card in this flow. |

## How it maps to Rive

Both flows use the same files; only the card list and the HTML copy differ. Full detail is in `docs/rive-plan.md`.

| Rive file | Covers |
|---|---|
| File 1 | Loading, Start, Ad 1, Chapter 1, Ad 2 |
| File 2 | Chapter 2, ending on the empty Chapter 3 room |
| File 3 | Ad 3 (anons), Chapter 3, Chapter 4 with all seven top-game versions, End |
| How-to | `how-to-mobile.riv` (mobile only; desktop uses the arrow buttons) |

**Engineering's side.** They build one card list from the stats, each card naming the file and scene it shows plus the tags its HTML needs, and drive the three files from `docs/engineering-guide.md` (what to set and in what order, the copy timings, Back during a pan, switching files). `engineering/yig-integration.js` and the React example are working references.

## How engineering's 2026 code is built

- The page is React and TypeScript, in the Games web code (`games-phoenix`, under `src/games/year-in-games/`). The apps show the same web page inside a web view, so no native screens are needed.
- Confirmed with engineering (Oct 29): the Rive animation sits behind all the slides and stays on screen, changing rooms as the player taps, instead of one Rive file per slide.
- Engineering will write their own React code to drive the Rive files rather than use our integration file. We give them a written guide with every rule (what to set and in what order, timings, Back during a pan, switching between files) and a React reference example. Our integration file stays as a working reference.
- Their page uses Rive runtime 2.27.3 (via @rive-app/react-canvas 4.20.1). All three of our files were tested on it and work: no upgrade needed. The file must be started with the plural option `stateMachines: "Backdrop"`; the singular is ignored on 2.27.3.
- Because engineering builds the file switching from our guide, the move from Chapter 2 into Chapter 3 stays simple: Chapter 2 ends on the empty Chapter 3 room, then Chapter 3's room arrives. The single continuous motion is dropped. **Subscribers have no card on the empty Chapter 3 room** (Demetre, 2026-10-29): the tap on their last Chapter 2 card plays both moves itself (the room pans out to the empty Chapter 3 room, File 3 takes over, and Chapter 3's room arrives right after, with no extra tap), and Back from Chapter 3 returns to that last Chapter 2 card. Anons keep Ad 3 as a card on the empty room.

## Not settled yet

- The bridge room's art (pieces and ball), to come on the "Bridge Art" artboard.
- Chapter 3: the badge art (the badges are HTML), and the second card's ball with the bird (a stand-in for now).
- Chapter 4: the video, and how the page takes over from the stage behind it.
- The full card list and variants for each game other than Wordle and Connections (they're in Figma).
- What the page shows over Loading (not designed yet).
- Art still to come: the mobile How-to overlay, and Chapter 4 versions for The Mini and The Midi.

## Chapter 3 and Chapter 4 cards (Figma frames, 2026-10-30)

Subscribers and registered players (frames: 10406:87455, 10500:106385, 10406:87479, 10406:87502 for Chapter 3; 10522:108393, 11729:47076, 10406:84746 for Chapter 4).

**Chapter 3** (File 3; the tap on their last Chapter 2 card plays the pan out to the empty Chapter 3 room and Chapter 3's room arrives):

| # | Card | Rive scene | Notes |
|---|---|---|---|
| 1 | Intro: "There's plenty more to celebrate, too." | `chapter-3` | The Chapter 3 room (disco ball, picture, frames, mobile with the bird, crib, gifts). |
| 2 | "Crossplay, the Midi and bonus puzzles gave you new ways to play." | `chapter-3-bird` | The room gives way to just the ball (twice the size, centred) with the bird sitting on top; the bird's own loop keeps running. A stand-in idea for now. |
| 3 | Event badges: "You also earned new badges" | `ad` (the empty room on the Chapter 3 colours) | The badges are HTML. Added only if the player has event badges. |
| 4 | Achievement badges: "...and bragging rights." | `ad` | The badges are HTML. Added only if the player has achievement badges. |

The example players in the review page cover every case: Wordle only has both badge cards, Midi only has event badges only, Connections only and Several games have achievement badges only, All seven games has neither, and No qualifying game gets the anonymous flow. Anons get four cards, never skipped, in the same rooms: card 1 `chapter-3` ("There's plenty more to celebrate, too."); card 2 `chapter-3-bird` ("Crossplay, the Midi and bonus puzzles introduced new ways to play." with a "Download Crossplay app" button and the Connections, Crossword and Midi icons); card 3 on the empty room ("Connections hit 1000 puzzles." with the 1000th badge); card 4 on the same empty room ("And Wordle turned 5 and fabulous." with the Wordle 5 icon). Anons still get Ad 3 on the empty Chapter 3 room before card 1.

**Chapter 4** (File 3, scene `chapter-4`; the property `reveal` says which card):

| # | Card | `reveal` | What the stage does |
|---|---|---|---|
| 1 | "But through it all, it's clear you play favorites." | false | The stack and the ball on the lighter blue wall (DFF3F0), mustard floor, no fireworks. |
| 2 | "In 2026, your top game was..." with the game's icon and name | true | The wall fades (1.45 s) to the top game's colour and that game's fireworks start looping from their opening. The card's copy waits for the fade to finish (1.45 s after the tap, instead of the usual 0.34 s). |
| 3 | The game's video and the editor's name | true | The stage stays on card 2's picture; the page covers it with the game's wall colour, flat, behind the video (the Figma frame has no stack or floor there). |

Going back to card 1 sets `reveal` back to false: the wall fades back to the lighter blue (the same 1.45 s wait for the copy applies) and the fireworks stop. Anons: the top game is always Wordle, so after the first card it shifts to Wordle's colour (C3E2C0) and Wordle's fireworks; their video is the special one from all the editors. Wall colours: Wordle C3E2C0, Connections E1DBF5, Strands DFF3F0, Spelling Bee FFFDEF, The Mini 95BEFA and The Midi 7EAAF1 (placeholders until their art arrives), The Crossword C0D8F8.
