# Harness

One page, `index.html`, that is both our review harness and the example engineering receives. It plays the chapter's real built `.riv` with the Rive web runtime (2.45.0, pinned, from jsDelivr), driven by `engineering/chapter-2-integration.js` and `engineering/yig-text-motion.css` exactly as engineering will use them. `npm run deliver ch2` copies this page into the handoff unchanged.

```bash
cd harness
npm start          # http://127.0.0.1:8765/
CHAPTER=ch1 PORT=9000 npm start   # another chapter or port
```

- The server rebuilds the `.riv` with `rive --once` whenever `scene.rml` is newer than the build, so reload the page after an edit. It also adds the NYT fonts from `fonts/`, which the handoff leaves out (engineering's site has them).
- Tap the right half of the stage (or →) for Next, which runs `onTap()`; the left half (or ←) for Back, `onBack()`. **Restart** reloads. **Desktop / Phone** switches between the full artboard and the phone crop.
- There are no menus. Three example players are in the page's script, picked by `?player=` in the address: `wordle-only` (the default; one qualifying game, so Chapter 2.5 follows), `midi-only` (Chapter 2.5 with all five community cards) and `several-games` (no Chapter 2.5). To try another case, edit `EXAMPLE_PLAYERS` (the comment above it lists the usual ones) and reload. `buildCards(player)` turns a player into the card list. Our `#game` jump works with them too: `/?player=midi-only#bridge`.
- Cards name their game (`{ game: "wordle" }`) and go to the integration once, as `const cards = buildCards(EXAMPLE_PLAYER); start(cards);`. The integration turns each name into a value of the Rive `scene` enum (and sets `direction` and `lockup`).
- `npm run text` (from the repo root, with this server running) times the text against Rive and tests the cases by swapping in other players.

## Per-file review pages

`http://127.0.0.1:8765/file1` and `http://127.0.0.1:8765/file3` (restart `npm start` first so the server knows them) play one file on its own, from `harness/file-review.html`. File 1 is `chapters/ch1`, the Start + Chapter 1 file:
Loading, Start, the empty room that Ads 1 and 2 play over, and Chapter 1's five rooms. File 3 is `chapters/ch3`: the empty Chapter 3 backdrop (Ad 3), Chapter 3's two cards, Chapter 4's cards and the top-game video card, then End; its **Top game** menu picks Chapter 4's wall colour and fireworks (`?top=connections`). It is our review page, not the engineering
example (the one integration across all files comes later), so it drives the file directly with the same rules the integration will
have. Tap the right half or press → for Next, the left half or ← for Back. **Jump to** buttons start on any scene (the rooms before it
are tapped through behind a curtain), **Replay** plays the current room's intro again, **Restart** reloads. All copy is placeholder.
`npm run review -- --url http://127.0.0.1:8765/file3` runs a browser smoke test of a page (`harness/file-review-test.mjs`).
