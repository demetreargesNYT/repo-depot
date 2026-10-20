# Responsive stage prototype: Subscriber / Registered flow

Shows how one Rive artboard, authored at desktop size, can serve desktop and mobile while the header and text stay in the same spot relative to the animation. Built as a **data-driven click-through of all 45 Subscriber/Registered frames** in the "YIG - Prototype" Figma file.

## Status

| | |
|---|---|
| **Screens** | 45 (full Subscriber/Registered order in `FLOW_NODE_IDS` / `SCREENS`) |
| **Shared Rive** | Same `assets/2026_yig-test_no-template.riv` on every screen (artboard `YIG Test`, state machine `Scene Loop`). Do not invent new `.riv` files. |
| **Stats / copy** | Exact Figma placeholders (`X guesses`, `X times`, `X%`, `X:XX`, `XXX players`, `TKTKTKTKTK`, `Month XX`, starting-word lines, chart sample values). Not from `sample-data.js`. |
| **Fonts** | Bundled only: `YIG2026/fonts/woff2` Karnak 500/600/700 + Franklin 300/500/600/700. No SF Pro / Inter / downloaded faces. |

Figma file: [YIG - Prototype](https://www.figma.com/design/SPgdDz5gM1VQIg2Z6gLqZf/YIG---Prototype) (`SPgdDz5gM1VQIg2Z6gLqZf`).

### Placeholders and the future API

API details are not available yet. Screen definitions stay data-driven (`SCREENS` + `{ style: value }` lines), with placeholder text authored as Figma wrote it.

When an API exists it will provide **raw play data**. A **front-end stats calculation layer** will turn that into the strings and chart rows shown on screen. Do **not** assume the API returns precomputed fields like “X guesses” or “solve rate,” and do not implement those calculations until the schema is known. `PROTOTYPE_PAYLOAD` today only holds Figma-authored chart/end-card samples for the click-through — it is not a stand-in API contract.

### Special screens

| Kind | Steps (1-based) | Notes |
|---|---|---|
| **Ads** | 3, 4, 14 | Full-screen ad creative + “Continue in 5” skip control. Stage click and the skip control advance. No live countdown timer — the “5” is static Figma art. No global nav. |
| **Start** | 15 | Games logo, “Year in Games 2026”, **Let’s go** primary button, Supported by T-Mobile. No global nav. Button advances. |
| **Bot** | 16 | Speech bubble + bot illustration assets. |
| **Badges** | 38, 41 | Badge images + **Share** primary button (advances). Hidden “SHARE FROM HERE” layers ignored. |
| **Editor video** | 44 | Poster frame + “Tracy Bennett / Editor of Wordle”. No playable video URL. |
| **End card** | 45 | Four Wordle tiles (`2026`) + closing headline. Next disabled. |

Global nav (wordmark, 26 progress segments, empty menu/close) is hidden on Start and ad screens. Progress fills the existing 26 Figma segment widths in proportion to step / 45 (not 45 segments).

Per-screen chapter background colors (e.g. Wordle `#c3e2c0`, Crossword `#c0d8f8`, badges `#f3eec2`) are set on `--chapter-bg` when the step changes. The Rive canvas still covers the artboard; the chapter color is the fallback behind/around it.

## Open it

The page loads the `.riv` file, and browsers block that over `file://`, so serve the folder over HTTP. From this folder:

```
python3 -m http.server 8000
```

then open http://localhost:8000/index.html.

- Click the stage (not a primary/skip button), press `→` / `←`, or use the arrows in the controls panel.
- Primary buttons (**Let’s go**, **Share**) and the ad skip control advance and are keyboard-focusable; stage click does not steal those clicks.
- `?step=1` … `?step=45` deep-links a screen. Step label reads `n / 45`.
- Min scale, Overlay (`O`), Rive template (`T`), and device frames work as before.

Live URL pattern: `https://demetreargesnyt.github.io/repo-depot/YIG2026/responsive-stage/index.html`

## How screens are defined

- `screens.js` — `SCREENS` (45 steps), `PROTOTYPE_PAYLOAD` (Figma chart/end-card samples only), `FLOW_NODE_IDS`.
- `stage-render.js` — mounts one screen into `#screen-root` with `{ style: value }` lines plus special kinds (`ad`, `start`, `bot`, badges, video, end card). Text styles from bundled woff2: `headline` (Karnak 500 / 26), `headline-strong` (Karnak 600 / 26), `body` (Franklin 500 / 20), `label` (Franklin 600), `label-bold` (Franklin 700), plus `connections-color`, `weekday-chart`, game icons from `YIG2026/icons/` / stage assets.
- `controls.js` — navigation, shared Rive, progress proportion, chapter bg, device overlay, template guides, min-scale.

## How the stage works

Everything (art, header, text) is absolutely positioned inside one `.stage`, in Figma coordinates. The 375px phone frame sits at `--column-x`. Under 600px wide the stage shifts up 56px (fake iOS status bar dropped).

## Fit to window / device overlay / Rive

Unchanged from the prior stage architecture: fit-to-window scaling, Min scale slider, device overlay frames, one shared Rive canvas, Rive template guides overlay. See prior notes in git history for the full device table and scale math.
