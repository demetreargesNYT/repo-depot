# Responsive stage prototype: Chapter 1

Shows how one Rive artboard, authored at desktop size, can serve desktop and mobile while the header and text stay in the same spot relative to the animation. Built from the Chapter 1 mobile frames in the "YIG - Prototype" Figma file (5 regular screens). The 3 tunnel interstitials are not built yet.

## Open it

Double-click `index.html`. No install, no server.

- Click the stage, press `→` / `←`, or use the arrows at the bottom to move between the 5 screens.
- `S` (or the Fit button) cycles the short-window behavior: All, Art only, Off (see below).
- `M` (or the Layout button) switches between the two artboard options below.
- `O` (or the Mobile overlay button) draws the 375×812 phone outline.
- `?layout=large&step=3&overlay=1&fit=art` in the URL sets all three, for repeatable screenshots.

## How it works

Everything (art, header, text) is absolutely positioned inside one `.stage`, in Figma coordinates. The 375px phone frame from the mobile designs sits at `--column-x`, exactly centered. The stage is centered horizontally and pinned to the top of the window, so the header, text and art never move relative to each other. Under 600px wide the stage shifts up 56px (the Figma mobile frame's fake iOS status bar is dropped, because a real device draws its own).

## The two options being compared

| | Card | Large |
|---|---|---|
| Artboard | 1495×1067 | 2555×1440 |
| Outside the artboard | one constant color, `--outside` (#ebebeb) | nothing; the chapter color fills the window |
| Edge | 30px rounded corners | hard edge, only visible beyond 2555×1440 |
| Extra art needed | none | extend art that runs off the frame (river, tube) |

Any artboard has a maximum size. Large only postpones the edge; Card makes it a designed feature.

## Recommended: Card, with fit-to-window

Card is the default. Big windows scale the whole stage up to fit (capped at 1.5×, then the outside color shows around the card). Phones (under 600px wide) are never scaled. For windows that are **shorter** than the artboard, three modes are compared with the Fit button / `S` / `?fit=`:

| Mode | What scales | On a short window |
|---|---|---|
| **All** (default) | the whole stage | Text, nav and art shrink together so the artboard is visible down to y 812 (the Figma phone frame's bottom). Never below 75%, so the headline stays about 19px. Alignment stays exact. |
| **Art only** | the art layer only | Header and text stay full size; the art shrinks to fit (down to 40%) with its y 812 line at the window bottom. Relative positions of text and art change: on a short window the ball can overlap the label, and the speech bubble covers the robot. |
| **Off** | nothing | 1:1 as designed; the bottom of the artboard is cropped. |

Constants (`MAX_SCALE`, `FIT_HEIGHT`, `MIN_SCALE_ALL`, `MIN_SCALE_ART`) are at the top of `controls.js`. `?scale=0` is the old name for `?fit=off`.

## Notes for the Rive hand-off

- Keep the important content inside the center 375px column; everything outside it is only seen on wider windows.
- Motion is CSS copied from Figma's motion export (`screens.css`) as a stand-in. Replace a screen's art with one `<canvas>` for the `.riv` and keep the `.phone` box.
- `prefers-reduced-motion` turns all animation off.

## Known gaps

- The Figma copy reads "You first puzzle of the year was"; probably meant to be "Your". Matched to Figma as is.
- The left icon and close buttons are empty placeholders, as in Figma.
- The desktop frames in Figma are FPO; where they differ from the mobile frames, the mobile frames were used.
