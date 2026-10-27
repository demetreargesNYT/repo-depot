# Harness

One page, `index.html`, that is both our review harness and the example engineering receives. It plays the chapter's real built `.riv` with the Rive web runtime (2.45.0, pinned, from jsDelivr), driven by `engineering/chapter-2-integration.js` and `engineering/yig-text-motion.css` exactly as engineering will use them. `npm run deliver ch2` copies this page into the handoff unchanged.

```bash
cd harness
npm start          # http://127.0.0.1:8765/
CHAPTER=ch1 PORT=9000 npm start   # another chapter or port
```

- The server rebuilds the `.riv` with `rive --once` whenever `scene.rml` is newer than the build, so reload the page after an edit. It also adds the NYT fonts from `fonts/`, which the handoff leaves out (engineering's site has them).
- Tap the right half of the stage (or →) for Next, which runs `onTap()`; the left half (or ←) for Back, `onBack()`. **Restart** reloads. **Desktop / Phone** switches between the full artboard and the phone crop.
- There are no menus. To try another case, edit `EXAMPLE_PLAYER` at the top of the page's script (the comment above it lists the usual ones) and reload. `buildCards(player)` turns it into the card list.
- Cards name their game (`{ game: "wordle" }`) and go to the integration once, as `const cards = buildCards(EXAMPLE_PLAYER); start(cards);`. The integration turns each name into the Rive `scene` number.
- `npm run text` (from the repo root, with this server running) times the text against Rive and tests the cases by swapping in other players.
