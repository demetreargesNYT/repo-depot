# Harness

One page, `index.html`, that is both our review harness and the example engineering receives. It plays the chapter's real built `.riv` with the Rive web runtime (2.45.0, pinned, from jsDelivr), driven by `engineering/chapter-2-integration.js` and `engineering/yig-text-motion.css` exactly as engineering will use them. `npm run deliver ch2` copies this page into the handoff unchanged.

```bash
cd harness
npm start          # http://127.0.0.1:8765/
CHAPTER=ch1 PORT=9000 npm start   # another chapter or port
```

- The server rebuilds the `.riv` with `rive --once` whenever `scene.rml` is newer than the build, so reload the page after an edit. It also adds the NYT fonts from `fonts/`, which the handoff leaves out (engineering's site has them).
- Tap the right 75% of the stage (or →) for Next, which runs `onTap()`; the left 25% (or ←) for Back, `onBack()`. **Restart** reloads. **Desktop / Phone** switches between the full artboard and the phone crop.
- There are no menus. Three example players are in the page's script, picked by `?player=` in the address: `wordle-only` (the default; one qualifying game, so Chapter 2.5 follows), `midi-only` (Chapter 2.5 with all five community cards) and `several-games` (no Chapter 2.5). To try another case, edit `EXAMPLE_PLAYERS` (the comment above it lists the usual ones) and reload. `buildCards(player)` turns a player into the card list. Our `#game` jump works with them too: `/?player=midi-only#bridge`.
- Cards name their game (`{ game: "wordle" }`) and go to the integration once, as `const cards = buildCards(EXAMPLE_PLAYER); start(cards);`. The integration turns each name into a value of the Rive `scene` enum (and sets `direction` and `lockup`).
- `npm run text` (from the repo root, with this server running) times the text against Rive and tests the cases by swapping in other players.

## Per-file review pages (retired)

`/file1` and `/file3` (one file each, `file-review.html`) were retired on 2026-10-30. `/experience` below is the only review page.

## The full experience

`http://127.0.0.1:8765/experience` plays the whole experience, Loading through End, across all three Rive files, in both
flows. It is driven by `engineering/yig-integration.js` (the reference for driving every file: switching files on the
empty rooms they share, loading the next file ahead, keeping earlier ones loaded so Back works across them). The page
frames the Rive stage exactly like engineering's staging page: their values are copied into `yig-framing.css`, the one
place to update them. The bar picks the flow, the subscriber's example player and top game, the screen (Window, which
follows the browser's size, or iPhone SE, iPhone 15 Pro Max, iPad portrait, desktop 1440 x 900), the Rive runtime
(engineering's 2.27.3, always) and **Jump to**, a dropdown of every scene in every file grouped by chapter (a scene the current flow or player doesn't have switches them to ones that do). The page asks the server which build of each file is current before it loads, and reloads the stage on the card it was on whenever a file is rebuilt, so it always shows the current build. At engineering's desktop breakpoint (1025 px wide and up)
the arrow buttons from `art/global/ui-desktop-button.svg` do Back and Next; below it, tap the left 25% (Back) or the right 75% (Next). The
stage alone is `/experience-stage` (same query: `flow`, `player`, `top`, `jump` (a card number), `goto` (`file:scene`, for example `1:chapter-1-card-3`)). A subscriber's tap on the last Chapter 2 card plays two moves by itself (out to the empty Chapter 3 room, then Chapter 3's room); anons stop on Ad 3 in between. Chapter 3 shows four cards to subscribers (the room, the ball with the bird, then the event and achievement badge cards, each skipped when the player has none); Chapter 4 shows three (the first on the lighter wall, the top game with its colour and fireworks, the video on the game's colour). Ads, the video and the
share card are placeholder cards, and all copy is placeholder. `npm run experience` tests it in a real browser.
