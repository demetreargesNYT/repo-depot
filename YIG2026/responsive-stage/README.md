# Responsive stage prototype: Subscriber / Registered flow

Shows how one Rive artboard, authored at desktop size, can serve desktop and mobile while the header and text stay in the same spot relative to the animation. Built as a **data-driven click-through** of the Subscriber/Registered frames in the "YIG - Prototype" Figma file.

## Status

| | |
|---|---|
| **Implemented from real Figma-matched copy** | 5 Chapter 1 screens (already in this folder before the data-driven refactor) |
| **Blocked (no invented copy)** | 40 remaining frames in the 45-frame link order |
| **Shared Rive** | Same `assets/2026_yig-test_no-template.riv` on every screen (per-screen `.riv` files later) |

Figma file: [YIG - Prototype](https://www.figma.com/design/SPgdDz5gM1VQIg2Z6gLqZf/YIG---Prototype) (`SPgdDz5gM1VQIg2Z6gLqZf`). Node ids for the full flow are listed in `screens.js` as `FLOW_NODE_IDS`; pending ones as `PENDING_FIGMA_NODES`.

### Figma access blocker

This environment has **no usable Figma credential**:

- No `FIGMA_TOKEN` / `FIGMA_ACCESS_TOKEN` (or similar) in process env or injected Cloud Agent secrets
- No Figma MCP server in the available tool namespaces
- `GET https://api.figma.com/v1/...` returns **401/403 Invalid token** without a token
- Figma oEmbed / public file endpoints return **404/403**
- Chrome profile has **no Figma cookies**

Until a Figma personal access token (or MCP) is available, do **not** invent the other 40 screens' copy. Add a `FIGMA_TOKEN` secret, re-run node fetches against `FLOW_NODE_IDS`, and append entries to `SCREENS` in `screens.js`.

Chapter 2 was called out as an exception to be explained later; nothing here blocks on that once those frames can be read.

## Open it

The page loads the `.riv` file, and browsers block that over `file://`, so serve the folder over HTTP. From this folder:

```
python3 -m http.server 8000
```

then open http://localhost:8000/index.html. (The GitHub Pages URL works as is.)

- Click the stage, press `→` / `←`, or use the arrows at the bottom to move between screens.
- The Min scale slider (or `?min=65`) sets how far the stage may shrink on a short window. All controls are in the panel at the top right (at the bottom on phone-width windows).
- `O` (or the Overlay button) shows or hides a device frame; the dropdown below it picks which of 13 devices (see Device overlay).
- `?step=3&overlay=1&device=ipad-pro-1024&template=1&min=65` in the URL sets all three, for repeatable screenshots.

Live URL pattern: `https://demetreargesnyt.github.io/repo-depot/YIG2026/responsive-stage/index.html`

## How screens are defined

- `screens.js` — `SCREENS` (implemented steps), `PROTOTYPE_PAYLOAD` (hardcoded Figma-matched stats for those steps), `FLOW_NODE_IDS` / `PENDING_FIGMA_NODES` (full Subscriber/Registered order).
- `stage-render.js` — mounts one screen into `#screen-root` using renderer-style `{ style: value }` lines and `{placeholder}` fill from the payload. Supports `headline`, `display`, `label`, `quote`, `game-icon`, `game-icon-stack`, and other text styles reserved for later frames.
- `controls.js` — navigation (`?step=`, click, arrows), shared Rive canvas, device overlay, template guides, min-scale / fit-to-window.
- One stage, shared Rive canvas, header (progress, wordmark, menu/close placeholders), HTML text in the centered 375px column.

A later real Games API payload can replace `PROTOTYPE_PAYLOAD` without changing the line templates. Do **not** treat `../sample-data.js` as the source of truth over Figma.

## How the stage works

Everything (art, header, text) is absolutely positioned inside one `.stage`, in Figma coordinates. The 375px phone frame from the mobile designs sits at `--column-x`, exactly centered. The stage is centered horizontally and pinned to the top of the window, so the header, text and art never move relative to each other. Under 600px wide the stage shifts up 56px (the Figma mobile frame's fake iOS status bar is dropped, because a real device draws its own).

## The artboard

The Rive file is **1495×1067**. It is shown as a rounded card (30px corners) on one constant outside color (`--outside`), currently dark grey (#4a4a4a) so the artboard edge is easy to see and black device frames stay visible where they extend past it; the final outside color is still to be decided. Nothing is drawn outside the artboard: art that runs off the frame (the river, the tube) simply ends at the card edge, so animators never need to draw filler.

## Fit to window

The whole stage (text, nav and art together, so alignment stays exact) scales to the browser window:

- **Bigger than the artboard:** it grows to fit, capped at 1.5×, then the outside color shows around the card.
- **Shorter than the artboard:** it shrinks so the artboard is visible down to y 812 (the bottom of the Figma phone frame), but never below the **Min scale** floor (default 90%, so the 26px headline stays about 23px). Below `812 × floor` px of window height (731px at 90%) the bottom of the artboard crops instead.
- **Phone-width windows** (under 600px) are never scaled.

Raising the floor keeps text larger but crops sooner; lowering it keeps more of the animation visible but makes the small text (the 12px label is 11px at 90%, 9px at 75%) harder to read. Current default: 90%. `MAX_SCALE` and `FIT_HEIGHT` are at the top of `controls.js`.

## Device overlay

The Overlay button (or `O`) shows a black rounded frame at a device's real size, centered on the artboard and aligned to its top, with a label such as "iPhone 14 – 375px · 375×812". The dropdown picks the device; choosing one while the overlay is off just selects it. The devices come from the Figma overlay sheets (plus iPhone SE, added by hand) and are listed in `DEVICES` in `controls.js`; `?device=<id>` selects one in the URL. `?overlay=1` alone shows the default, iPhone 14 – 375px.

| Group | Devices (width × height) |
|---|---|
| Desktop | MacBook Air 1280 × 832, MacBook Pro 14" 1512 × 982, MacBook Pro 16" 1728 × 1117 |
| Tablet | iPad Mini 744 × 1133, iPad Pro 834 × 1194, iPad Pro 1024 × 1366 |
| Mobile | iPhone SE 375 × 667 (added by hand, not in the Figma sheets), iPhone 14 375 × 812, iPhone 13 & 14 390 × 844, iPhone 17 402 × 874, iPhone 16 Plus 430 × 932, iPhone 16 & 17 Pro Max 440 × 956, iPhone Duo Closed 466 × 678, iPhone Duo Open 890 × 626 |

Frames are drawn at their real size in artboard pixels and are not clipped by the card: a device wider or taller than 1495 × 1067 extends past the card edge, with a thin white outer line so it stays visible on the dark outside color. They scale with the stage.

## Notes for the Rive hand-off

- Keep the important content inside the center 375px column; everything outside it is only seen on wider windows.
- All graphics and animation come from one Rive file, `assets/2026_yig-test_no-template.riv` (artboard `YIG Test`, state machine `Scene Loop`), drawn on one `<canvas>` by the Rive runtime (`assets/vendor/rive.js`, `@rive-app/canvas-single` 2.45.0, MIT). The text and stats in the HTML are the dynamic part.
- The same animation plays behind every step for now. Per-step control (state machine inputs or data binding) is not wired up yet. Per-screen `.riv` files will replace this later; do not invent new `.riv` files in this prototype.
- The `.riv` is the no-template version: no guide shapes are drawn in it. The **Rive template** button (or `T`, or `?template=1`) overlays the guides from `assets/yig-rive-template-guides.svg` exactly over the artboard.
- `prefers-reduced-motion` turns all animation off.

## Known gaps

- The Figma copy reads "You first puzzle of the year was"; probably meant to be "Your". Matched to Figma as is.
- The left icon and close buttons are empty placeholders, as in Figma.
- The desktop frames in Figma are FPO; where they differ from the mobile frames, the mobile frames were used.
- Progress segments still use the Chapter 1 Figma widths (26 ticks). When the full flow is authored from Figma, regenerate the bar to match that chrome.
- 40 Subscriber/Registered frames after Chapter 1 are not implemented (Figma access blocked).
