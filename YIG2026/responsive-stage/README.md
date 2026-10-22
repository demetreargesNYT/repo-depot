# Responsive stage prototype: Subscriber / Registered flow

Shows how one Rive artboard, authored at desktop size, can serve desktop and mobile while the header and text stay in the same spot relative to the animation. Built as a **data-driven click-through of 55 Subscriber/Registered frames**.

## Status

| | |
|---|---|
| **Screens** | 55 (`SCREENS` in `screens.js`; `FLOW_NODE_IDS` is derived from it) |
| **Shared Rive** | Same `assets/2026_yig-test_no-template.riv` on every screen (artboard `YIG Test`, state machine `Scene Loop`). The revised frames reference per-frame Rive instances (`c1-s1` to `c1-s5`, `c2-wordle`, `c2-connections`, `c2-spelling-bee`, `c2-mini`, `c2-midi`, `c2-daily`, `c2-strands`) that are not in the repo yet. Do not invent new `.riv` files. |
| **Stats / copy** | Exact Figma placeholders (`X guesses`, `X times`, `X%`, `X:XX`, `XXX players`, `TKTKTKTKTK`, `[Rank]`, `Month XX`, chart sample values). Not from `sample-data.js`. |
| **Fonts** | Bundled only: `YIG2026/fonts/woff2` Karnak 500/600/700 + Franklin 300/500/600/700. No SF Pro / Inter / downloaded faces. |

Figma files:

- Steps 1–5, 7–25, 30–47 (revised Chapter 1, Chapter 2 game cards, and the five community fallbacks): `9kgGqMlvJXa4jUolapkp89`.
- Step 6, steps 26–29, and steps 48–55 (older frames): [YIG - Prototype](https://www.figma.com/design/SPgdDz5gM1VQIg2Z6gLqZf/YIG---Prototype) (`SPgdDz5gM1VQIg2Z6gLqZf`).

Each screen can set `figmaFileKey`; `figmaUrl(screen)` falls back to `SPgdDz5gM1VQIg2Z6gLqZf` when it is not set.

## Screen order

| Steps | Screens |
|---|---|
| 1–5 | Chapter 1: intro, total puzzles, first puzzle (Strands), longest streak (Connections), bot fact |
| 6 | Chapter 2 intro (“Let’s take a closer look at your puzzle powers.”) |
| 7–13 | Wordle: average guesses, best solves, hardest word (03a missed, 03b solved, 03c not played), top starting words, community fallback |
| 14–19 | Connections: solving order, purple first, solve rate, average mistakes, mistake-free solves, community fallback |
| 20–25 | Spelling Bee: total words, longest word, pangrams, Genius and Queen Bee (04a), top rank (04b), community fallback |
| 26–28 | Two ads and the repeat ad |
| 29 | Start |
| 30–33 | Mini: total solves, fastest time, average time, longest streak |
| 34–36 | Midi: total solves, longest streak, fastest and average times |
| 37–40 | Daily Crossword: most-played weekday, average time, fastest time, longest streak |
| 41 | Crosswords community fallback (shared by Mini, Midi, and Daily) |
| 42–47 | Strands: total solves, spangram first, no-hint solves, hints used, non-theme words, community fallback |
| 48–55 | Badges, Chapter 3, remaining chapters, editor video, end card |

Ads and Start sit after Spelling Bee for now; their real placement waits for the full flow.

## Card rules

The review click-through shows **every** card and variant. The rules for when a card is skipped, or which variant fills a slot, live in [`card-rules.csv`](card-rules.csv) (columns `screen, audience, game, rule, alternate, skip`) and as a short `rule` note on each screen in `screens.js`. They are recorded, not applied.

- Chapter 2 personalized cards for a game appear only at 10 or more solves of that game. Below that, the review still shows the personalized cards, and the recorded alternate is that game’s community fallback: `ch2-wordle-fallback`, `ch2-connections-fallback`, `ch2-spelling-bee-fallback`, `ch2-strands-fallback`, or the shared `ch2-crosswords-fallback` (one card for Mini, Midi, and the Daily Crossword).
- Wordle 01: show the community-average lines only when the player’s average is lower than the community’s.
- Wordle 03a, 03b, 03c are one slot: played PSHAW and missed, played and solved, or did not play.
- Connections 02 is skipped when the player never got purple first; Connections 05 is skipped with no mistake-free solves. Neither has an alternate.
- Spelling Bee 03 is skipped with no pangrams.
- Spelling Bee 04a and 04b are one slot: 04a when Genius or Queen Bee was reached at least once, 04b when the top rank is Solid or higher without Genius or Queen Bee. Both are skipped below Solid.
- Mini 04, Midi 02, and Daily Crossword 04 are skipped when the player’s longest streak is below that game’s configured threshold. The threshold values are still TBD and are not invented in the prototype.
- Strands 02 is skipped when the player never found the spangram first; 03 with no hint-free solves; 04 when no hints were used; and 05 when no non-theme words were found.

### Placeholders and the future API

API details are not available yet. Screen definitions stay data-driven (`SCREENS` + `{ style: value }` lines), with placeholder text authored as Figma wrote it.

When an API exists it will provide **raw play data**. A **front-end stats calculation layer** will turn that into the strings and chart rows shown on screen. Do **not** assume the API returns precomputed fields like “X guesses” or “solve rate,” and do not implement those calculations until the schema is known. `PROTOTYPE_PAYLOAD` today only holds Figma-authored chart/end-card samples for the click-through — it is not a stand-in API contract.

### Special screens

| Kind | Steps (1-based) | Notes |
|---|---|---|
| **Bot** | 5 | Speech bubble + bot illustration (`assets/bot-illustration.png` until `c1-s5` exists as a `.riv`). |
| **Ads** | 26, 27, 28 | Full-screen ad creative + “Continue in 5” skip control. Stage click and the skip control advance. No live countdown timer — the “5” is static Figma art. No global nav. |
| **Start** | 29 | Games logo, “Year in Games 2026”, **Let’s go** primary button, Supported by T-Mobile. No global nav. Button advances. |
| **Badges** | 48, 51 | Badge images + **Share** primary button (advances). Hidden “SHARE FROM HERE” layers ignored. |
| **Editor video** | 54 | Poster frame + “Tracy Bennett / Editor of Wordle”. No playable video URL. |
| **End card** | 55 | Four Wordle tiles (`2026`) + closing headline. Next disabled. |

Global nav (“The New York Times” over the Year in Games wordmark, 26 progress segments, empty menu/close; 134px of chrome including the 56px status bar) is hidden on Start and ad screens. Progress fills the existing 26 Figma segment widths in proportion to step / 55.

Per-screen chapter background colors (Chapter 1 `#f1ecc0`, Wordle `#c3e2c0`, Connections `#e1dbf5`, Spelling Bee `#fffdef`, Mini `#c0d8f8`, Midi `#9ebff5`, Daily `#84a9eb`, Strands `#dff3f0`, badges `#f3eec2`) are set on `--chapter-bg` when the step changes. The Rive canvas still covers the artboard; the chapter color is the fallback behind/around it.

## Open it

The page loads the `.riv` file, and browsers block that over `file://`, so serve the folder over HTTP. From this folder:

```
python3 -m http.server 8000
```

then open http://localhost:8000/index.html.

- Click the stage (not a primary/skip button), press `→` / `←`, or use the arrows in the controls panel.
- Primary buttons (**Let’s go**, **Share**) and the ad skip control advance and are keyboard-focusable; stage click does not steal those clicks.
- `?step=1` … `?step=55` deep-links a screen. Step label reads `n / 55`.
- Min scale, Overlay (`O`), Rive template (`T`), and device frames work as before.

Live URL pattern: `https://demetreargesnyt.github.io/repo-depot/YIG2026/responsive-stage/index.html`

## How screens are defined

- `screens.js` — `SCREENS` (55 steps), `PROTOTYPE_PAYLOAD` (Figma chart/end-card samples only), `FLOW_NODE_IDS`, `figmaUrl()`.
- `stage-render.js` — mounts one screen into `#screen-root` with `{ style: value }` lines plus special kinds (`ad`, `start`, `bot`, badges, video, end card).
  - Text styles from bundled woff2: `headline` (Karnak 500 / 26), `headline-strong` (Karnak 600 / 26), `body` (Franklin 500 / 20), `label` (Franklin 600), `label-bold` (Franklin 700). `**text**` inside a line renders an inline emphasis run (Karnak 600 in headlines).
  - Other lines: `game-icon` (`size: 75` for the large icon), `connections-color` (one color or an array of colors), `wordle-row` (one word or an array, `state: "correct"` green or `"empty"` white), `image` (`width`, `height`, `alt`), `honeycomb` (Spelling Bee longest word), `weekday-chart`.
  - Any line can add `marginTop` (px, on top of the 16px lockup gap) and `nowrap`.
- `card-rules.csv` — skip and variant rules for the revised cards (recorded, not applied).
- `controls.js` — navigation, shared Rive, progress proportion, chapter bg, device overlay, template guides, min-scale.

## How the stage works

Everything (art, header, text) is absolutely positioned inside one `.stage`, in Figma coordinates. The 375px phone frame sits at `--column-x`. Under 600px wide the stage shifts up 56px (fake iOS status bar dropped).

## Fit to window / device overlay / Rive

Unchanged from the prior stage architecture: fit-to-window scaling, Min scale slider, device overlay frames, one shared Rive canvas, Rive template guides overlay. See prior notes in git history for the full device table and scale math.
