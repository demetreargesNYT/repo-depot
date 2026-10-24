# Chapter 2 animation spec

This documents the Chapter 2 Rive file as it is now. **The file is the source of truth; this spec describes it.**
It matches the file's revision named in `chapters/ch2` (see the git tag `ch2-scene-structure` and later commits).
The key listings below are generated from `chapters/ch2/scene.rml`, so they cannot drift:

```bash
npm run keys ch2                                   # print every timeline and the state machine
python3 tools/dump_keys.py ch2 --write docs/animation-spec-ch2.md   # refresh the listings in this file
python3 tools/dump_keys.py ch2 --check docs/animation-spec-ch2.md   # fail if any listing differs from the file
npm run check ch2                                  # the fast check: build, rules, structure
```

## Conventions

- **Artboard** "Chapter 2": 1495 × 1067, clipping on, `includeInExport` true. Coordinates are artboard units, origin top left, y down. The phone shows the centre 375 wide.
- **Time** is seconds in this spec; the file keys frames at 60 fps (3.2 s = frame 192). Transition durations in the state machine are milliseconds.
- **Rotation** is degrees here, positive clockwise; the file stores radians.
- **Colours** are #RRGGBB here; the file stores ARGB hex.
- **Eases** are GSAP names. In a listing, `a (ease) b` means the ease shapes the segment that ends at `b`; `hold` means the value does not change. The beziers are in the table at the end.
- **Balls** are three nested groups: `Ball` (positioned at the base of the ball, so squash and stretch keep it on its surface), `Ball Spin` (rotates about the ball's centre) and `Ball Art`. "Ball x / y" means the base of the ball.
- **Pivots:** a group that rotates or squashes has its own position on the pivot, with an inner `… Art` group offset back so the artwork stays put.
- **Draw order:** Rive draws a group's first child on top, so children draw in reverse of the order written.
- **Names** are Title Case with spaces ("Pair WR", "Wordle Ball Spin"), and are what the timelines and the checker use.

## Scene values

One number drives the whole file. Engineering sets it; nothing else is exposed.

| `scene` | Shows | Rooms it brings in |
|---|---|---|
| 0 | the chapter opener | Shelf Room (on stage at load) |
| 1 | Wordle | Wordle Room |
| 2 | Connections | Connections Room |
| 3–7 | Strands, Spelling Bee, The Mini, The Midi, The Crossword | not built yet; see "Adding a game" |

- The view model is named "Chapter 2" with one number property, `scene`, default 0. The state machine is "Chapter 2", the artboard's default, so it plays on load.
- Setting the same value again does nothing, so it is always safe to set.
- A game appears in one unbroken run of cards in a chapter, so a room never comes back once it has left. Going back to a scene that already left is not supported.
- Setting a value no room waits for (3 to 7 today) makes the current room leave and nothing arrive: the Background shows, empty, in the opener's colours (checked at scene 3 and 7, 3.5 s in).

## Structure

`Chapter 2 Rive Import` holds the rooms, in draw order from top to bottom:

```text
Lockups               an empty group left from the import; nothing is in it any more
Connections Room      (scene 2)
Wordle Room           (scene 1)
Shelf Room            (scene 0, the opener)
Background            the global wall #E7F1E1, floor and floor line; never animated. Every room's backdrop covers it, so it only shows when no room is on stage
```

Every room has the same structure, and every room sits at x 0:

```text
<Room>                                  the whole room; Outro moves it left
  <Room> Draw Rules                     two targets: <Room> Normal, <Room> Bottom
  <Room> Lockup                         (Wordle and Connections) icon + word, drawn on top of the room's art
  <Room> Ball                           (Wordle and Connections) the incoming ball, a sibling of the floor plane
  <Room> Floor Plane                    the room's pieces; the pan moves it 1600
  <Room> Wall Lag                       a wrapper, always at x 0, so the outro can lag the wall plane
    <Room> Wall Plane                   the room's wall art; the pan moves it 1280
  <Room> Backdrop                       the room's wall, floor, floor line and wall corner; the LAST child, so it is at the bottom
```

(Wordle and Connections have the ball and floor plane in a different order, and Shelf has no lockup or ball. `npm run check` verifies the rules that matter: the backdrop is the last child, the lockup is inside its room, a Wall Lag wrapper exists.)

### Backdrops

Each room brings its own colours, so the colour change arrives as the next room's wall corner during the pan.

| Room | Wall |
|---|---|
| Shelf | #E7F1E1 |
| Wordle | #C3E2C0 |
| Connections | #E1DBF5 |

Every backdrop is the same shape: a wall rectangle from (0, −200), 1600 × 912; a floor rectangle from (0, 712), 1600 × 600, #FEA0C9; a 2-unit #1F1F1F floor line along y 712 from x 0 to 1600; and a 2-unit #1F1F1F wall corner line **at x −1** from y −200 to 712. The corner sits at −1, not 0, so its stroke stays off the artboard edge at rest. Backdrops are 1600 wide so neighbouring rooms meet exactly at the wall corner during the pan. Wordle and Connections backdrops wait at x 1600; Shelf's is at 0.

### Wall Lag wrappers

Each room's wall plane sits inside a `<Room> Wall Lag` group at x 0. The intro moves the wall plane itself (pulling it in 1280); the outro moves the Wall Lag (pushing it +320), so the wall plane nets −1280 when the room leaves. Because the two never key the same object they never fight. Wordle has no wall art, so its Wall Plane is empty and its lag holds at 0; it exists so every room has the same structure.

### Draw rules

A leaving room must draw below the arriving room, whichever game order is played, without reordering rooms. Each room has a `DrawRules` named "<Room> Draw Rules" with two targets:

- **<Room> Normal**: just above the top-most shape of the room under it in the tree (Shelf, the lowest room, uses the Background's floor line). The rule starts here.
- **<Room> Bottom**: just above the Background's floor line, under every other room.

`<Room> Outro` and `<Room> Gone` key the rule to Bottom; `<Room> Home` keys it back to Normal. A draw target has to name a Shape, not a group, so each target is the top-most shape of its room.

## Poses

Each room's timelines are listed under its own heading below. These one-frame timelines set a pose; the state machine plays them in the layer states.

- **Waiting** (Wordle, Connections): the room's design pose, everything its intro animates away from, off stage to the right. **A Waiting pose is, by rule, its intro's first keys**, one for one; `npm run check` verifies it for every room. If an intro changes, rebuild its Waiting pose from the intro, never by hand. Because it has no listing of its own, the intro's first key of each property is the Waiting value: backdrop x 1600, floor plane x +1600, pairs and tiles tilted and raised, shadows at scale 0, the incoming ball at x −80, y 712 spun −1080°, the lockup at opacity 0, y 381, scale 0.96.
- **Home**: `<Room> x 0`, `<Room> Wall Lag x 0`, and the draw rule on Normal.
- **Gone**: `<Room> x −1600`, `<Room> Wall Lag x` at its outro end value (320, or 0 for Wordle), and the draw rule on Bottom. Nothing of the room is on the artboard.

## Timelines

All timelines are on the "Chapter 2" artboard. Every intro is **exactly 3.2 s**, because the page text is timed to that. The first key on an intro property is its design-pose value.

### Shelf (the opener)

The opener has no intro. Its toy ball rocks in place; **no other timeline ever keys the Shelf Ball or Shelf Ball Spin**, so the toy ball holds whatever pose it had when the player tapped and leaves with its room.

<!-- keys: Shelf Loop -->
```text
Shelf Loop · 108 frames · 1.8 s · loops
Shelf Ball x: 0 -29.39 · 0.45 -24.39 (sine.inOut) · 1.35 -34.39 (sine.inOut) · 1.8 -29.39 (sine.inOut)
Shelf Ball Spin rotation: 0 0° · 0.45 16° (sine.inOut) · 1.35 -16° (sine.inOut) · 1.8 0° (sine.inOut)
```
<!-- /keys -->

The outro moves the whole room left with the camera, its wall plane lagging, and keys only the room, its Wall Lag and its draw rule, so the room's loop keeps playing as it leaves.

<!-- keys: Shelf Outro -->
```text
Shelf Outro · 96 frames · 1.6 s · plays once
Shelf Room x: 0.05 0 · 1.55 -1600 (power2.inOut)
Shelf Wall Lag x: 0.05 0 · 1.55 320 (power2.inOut)
Shelf Draw Rules drawTargetId: 0 Shelf Bottom
```
<!-- /keys -->

<!-- keys: Shelf Home -->
```text
Shelf Home · 1 frame · plays once
Shelf Room x: 0 0
Shelf Wall Lag x: 0 0
Shelf Draw Rules drawTargetId: 0 Shelf Normal
```
<!-- /keys -->

<!-- keys: Shelf Gone -->
```text
Shelf Gone · 1 frame · plays once
Shelf Room x: 0 -1600
Shelf Wall Lag x: 0 320
Shelf Draw Rules drawTargetId: 0 Shelf Bottom
```
<!-- /keys -->

### Wordle

The intro pans the camera right (everything moves left), tips the bottom row over, tumbles the top pairs in, grows the shadows, rolls the new ball in and up onto the blocks, and runs the lockup.

<!-- keys: Wordle Intro -->
```text
Wordle Intro · 192 frames · 3.2 s · plays once
Pair BD rotation: 1.267 90° · 1.567 0° (power2.in)
Pair BD scaleX: 1.567 1 · 1.633 1.028 (power2.out) · 1.883 1 (back.out)
Pair BD scaleY: 1.567 1 · 1.633 0.93 (power2.out) · 1.883 1 (back.out)
Pair KE rotation: 1.383 90° · 1.683 0° (power2.in)
Pair KE scaleX: 1.683 1 · 1.75 1.028 (power2.out) · 2.017 1 (back.out)
Pair KE scaleY: 1.683 1 · 1.75 0.93 (power2.out) · 2.017 1 (back.out)
Pair LE rotation: 1.15 90° · 1.45 0° (power2.in)
Pair LE scaleX: 1.45 1 · 1.517 1.028 (power2.out) · 1.767 1 (back.out)
Pair LE scaleY: 1.45 1 · 1.517 0.93 (power2.out) · 1.767 1 (back.out)
Pair OM rotation: 1.45 62° · 1.867 14° (power2.in) · 2.017 0° (power2.in)
Pair OM scaleX: 2.017 1 · 2.067 1.024 (power2.out) · 2.333 1 (back.out)
Pair OM scaleY: 2.017 1 · 2.067 0.94 (power2.out) · 2.333 1 (back.out)
Pair OM y: 1.45 -800 · 1.867 0 (power2.in)
Pair WR rotation: 1.333 -62° · 1.75 -14° (power2.in) · 1.883 0° (power2.in)
Pair WR scaleX: 1.883 1 · 1.95 1.024 (power2.out) · 2.217 1 (back.out)
Pair WR scaleY: 1.883 1 · 1.95 0.94 (power2.out) · 2.217 1 (back.out)
Pair WR y: 1.333 -800 · 1.75 0 (power2.in)
Shadow B scaleX: 1.883 0 · 2.083 1 (power2.out)
Shadow B scaleY: 1.883 0 · 2.083 1 (power2.out)
Shadow E scaleX: 1.883 0 · 2.083 1 (power2.out)
Shadow E scaleY: 1.883 0 · 2.083 1 (power2.out)
Shadow K scaleX: 2.017 0 · 2.217 1 (power2.out)
Shadow K scaleY: 2.017 0 · 2.217 1 (power2.out)
Shadow R scaleX: 2.017 0 · 2.217 1 (power2.out)
Shadow R scaleY: 2.017 0 · 2.217 1 (power2.out)
Wordle Ball scaleX: 2.117 1 · 2.183 1.16 (power2.out) · 2.433 1 (back.out) · 2.533 1 (hold) · 2.617 1.22 (power2.out) · 2.85 1 (back.out) · 2.933 1.08 (power2.out) · 3.167 1 (back.out)
Wordle Ball scaleY: 2.117 1 · 2.183 0.84 (power2.out) · 2.433 1 (back.out) · 2.533 1 (hold) · 2.617 0.78 (power2.out) · 2.85 1 (back.out) · 2.933 0.92 (power2.out) · 3.167 1 (back.out)
Wordle Ball x: 1.15 -80 · 1.75 556 (power1.out) · 2.117 651 (linear) · 2.167 651 (hold) · 2.533 707.11 (linear)
Wordle Ball y: 1.15 712 · 1.75 712 (hold) · 1.917 609.85 (power2.out) · 2.117 654.85 (power2.in) · 2.167 654.85 (hold) · 2.333 559.11 (power2.out) · 2.533 604.11 (power2.in) · 2.617 604.11 (hold) · 2.733 592.11 (power2.out) · 2.85 604.11 (power2.in)
Wordle Ball Spin rotation: 1.15 -1080° · 2.533 0° (power1.out)
Wordle Floor Plane x: 0.05 2348.215 · 1.55 748.215 (power2.inOut)
Wordle Lockup opacity: 1.917 0 · 2.133 1 (linear) · 2.933 1 (hold) · 3.2 0 (power2.in)
Wordle Lockup scaleX: 1.917 0.96 · 2.483 1 (expo.out) · 2.933 1 (hold) · 3.2 0.97 (power3.in)
Wordle Lockup scaleY: 1.917 0.96 · 2.483 1 (expo.out) · 2.933 1 (hold) · 3.2 0.97 (power3.in)
Wordle Lockup y: 1.917 381 · 2.483 363 (expo.out) · 2.933 363 (hold) · 3.2 333 (power3.in)
Wordle Lockup Word opacity: 1.983 0 · 2.55 1 (expo.out)
Wordle Lockup Word y: 1.983 54.353 · 2.55 44.353 (expo.out)
Wordle Backdrop x: 0.05 1600 · 1.55 0 (power2.inOut)
```
<!-- /keys -->

The loop starts and ends on the intro's last frame (ball x 707.11, y 604.11, spin 0, scale 1) and only keys the ball, Pair KE and Pair OM: the ball rolls to the edge of M, teeters, hops down onto E with two bounces, hops back up and rolls home.

<!-- keys: Wordle Loop -->
```text
Wordle Loop · 432 frames · 7.2 s · loops
Pair KE scaleX: 2.817 1 · 2.883 1.024 (power2.out) · 3.133 1 (back.out) · 3.233 1 (hold) · 3.3 1.016 (power2.out) · 3.567 1 (back.out)
Pair KE scaleY: 2.817 1 · 2.883 0.94 (power2.out) · 3.133 1 (back.out) · 3.233 1 (hold) · 3.3 0.96 (power2.out) · 3.567 1 (back.out)
Pair OM scaleX: 4.167 1 · 4.233 1.024 (power2.out) · 4.483 1 (back.out)
Pair OM scaleY: 4.167 1 · 4.233 0.94 (power2.out) · 4.483 1 (back.out)
Wordle Ball scaleX: 2.817 1 · 2.9 1.2 (power2.out) · 3.133 1 (back.out) · 3.233 1 (hold) · 3.317 1.14 (power2.out) · 3.55 1 (back.out) · 3.633 1.08 (power2.out) · 3.867 1 (back.out) · 4.167 1 (hold) · 4.25 1.22 (power2.out) · 4.483 1 (back.out) · 5.167 1 (hold) · 5.25 1.06 (power2.out) · 5.483 1 (back.out)
Wordle Ball scaleY: 2.817 1 · 2.9 0.8 (power2.out) · 3.133 1 (back.out) · 3.233 1 (hold) · 3.317 0.86 (power2.out) · 3.55 1 (back.out) · 3.633 0.92 (power2.out) · 3.867 1 (back.out) · 4.167 1 (hold) · 4.25 0.78 (power2.out) · 4.483 1 (back.out) · 5.167 1 (hold) · 5.25 0.94 (power2.out) · 5.483 1 (back.out)
Wordle Ball x: 0 707.11 · 0.6 707.11 (hold) · 1.7 812 (sine.inOut) · 1.9 814 (sine.inOut) · 2.2 811 (sine.inOut) · 2.4 812 (sine.inOut) · 2.817 841 (linear) · 3.667 841 (hold) · 4.167 790 (linear) · 4.267 790 (hold) · 5.167 707.11 (sine.inOut) · 7.2 707.11 (hold)
Wordle Ball y: 0 604.11 · 2.4 604.11 (hold) · 2.583 578.11 (power2.out) · 2.817 654.85 (power2.in) · 2.883 654.85 (hold) · 3.067 630.85 (power2.out) · 3.233 654.85 (power2.in) · 3.283 654.85 (hold) · 3.417 642.85 (power2.out) · 3.55 654.85 (power2.in) · 3.667 654.85 (hold) · 3.9 552.11 (power2.out) · 4.167 604.11 (power2.in) · 7.2 604.11 (hold)
Wordle Ball Spin rotation: 0 0° · 0.6 0° (hold) · 1.7 340° (sine.inOut) · 1.9 350° (sine.inOut) · 2.2 332° (sine.inOut) · 2.4 340° (sine.inOut) · 3.667 340° (hold) · 4.167 269° (power1.inOut) · 4.267 269° (hold) · 5.167 0° (sine.inOut) · 7.2 0° (hold)
```
<!-- /keys -->

<!-- keys: Wordle Outro -->
```text
Wordle Outro · 96 frames · 1.6 s · plays once
Wordle Room x: 0.05 0 · 1.55 -1600 (power2.inOut)
Wordle Wall Lag x: 0.05 0 · 1.55 0 (hold)
Wordle Draw Rules drawTargetId: 0 Wordle Bottom
```
<!-- /keys -->

<!-- keys: Wordle Home -->
```text
Wordle Home · 1 frame · plays once
Wordle Room x: 0 0
Wordle Wall Lag x: 0 0
Wordle Draw Rules drawTargetId: 0 Wordle Normal
```
<!-- /keys -->

<!-- keys: Wordle Gone -->
```text
Wordle Gone · 1 frame · plays once
Wordle Room x: 0 -1600
Wordle Wall Lag x: 0 0
Wordle Draw Rules drawTargetId: 0 Wordle Bottom
```
<!-- /keys -->

### Connections

The intro pans, drops the ten tiles in from above (bottom row first, 0.07 s apart, each squashing on landing), rolls the new ball in and onto the lilac slab in one big hop, and runs the lockup.

<!-- keys: Connections Intro -->
```text
Connections Intro · 192 frames · 3.2 s · plays once
Connections Ball scaleX: 2.25 1 · 2.333 1.22 (power2.out) · 2.567 1 (back.out) · 2.65 1.08 (power2.out) · 2.883 1 (back.out)
Connections Ball scaleY: 2.25 1 · 2.333 0.78 (power2.out) · 2.567 1 (back.out) · 2.65 0.92 (power2.out) · 2.883 1 (back.out)
Connections Ball x: 1.15 -80 · 1.75 470 (power1.out) · 2.25 616.07 (linear)
Connections Ball y: 1.15 712 · 1.75 712 (hold) · 1.983 564.36 (power2.out) · 2.25 624.36 (power2.in) · 2.333 624.36 (hold) · 2.45 612.36 (power2.out) · 2.567 624.36 (power2.in)
Connections Ball Spin rotation: 1.15 -1080° · 2.25 0° (power1.out)
Connections Floor Plane x: 0.05 2347.5 · 1.55 747.5 (power2.inOut)
Connections Lockup opacity: 2.1 0 · 2.317 1 (linear) · 2.933 1 (hold) · 3.2 0 (power2.in)
Connections Lockup scaleX: 2.1 0.96 · 2.667 1 (expo.out) · 2.933 1 (hold) · 3.2 0.97 (power3.in)
Connections Lockup scaleY: 2.1 0.96 · 2.667 1 (expo.out) · 2.933 1 (hold) · 3.2 0.97 (power3.in)
Connections Lockup y: 2.1 381 · 2.667 363 (expo.out) · 2.933 363 (hold) · 3.2 333 (power3.in)
Connections Lockup Word opacity: 2.167 0 · 2.733 1 (expo.out)
Connections Lockup Word y: 2.167 54.188 · 2.733 44.188 (expo.out)
Connections Wall Plane x: 0.05 2068.745 · 1.55 788.745 (power2.inOut)
Left Bottom Black rotation: 1 9° · 1.417 0° (power2.in)
Left Bottom Black scaleX: 1.417 1 · 1.483 1.032 (power2.out) · 1.733 1 (back.out)
Left Bottom Black scaleY: 1.417 1 · 1.483 0.92 (power2.out) · 1.733 1 (back.out)
Left Bottom Black y: 1 -748.25 · 1.417 51.75 (power2.in)
Left Bottom Green rotation: 1.067 -7° · 1.483 0° (power2.in)
Left Bottom Green scaleX: 1.483 1 · 1.55 1.032 (power2.out) · 1.817 1 (back.out)
Left Bottom Green scaleY: 1.483 1 · 1.55 0.92 (power2.out) · 1.817 1 (back.out)
Left Bottom Green y: 1.067 -748.25 · 1.483 51.75 (power2.in)
Left Middle Black rotation: 1.283 6° · 1.7 0° (power2.in)
Left Middle Black scaleX: 1.7 1 · 1.767 1.032 (power2.out) · 2.017 1 (back.out)
Left Middle Black scaleY: 1.7 1 · 1.767 0.92 (power2.out) · 2.017 1 (back.out)
Left Middle Black y: 1.283 -767.25 · 1.7 32.75 (power2.in)
Left Middle Blue rotation: 1.35 -10° · 1.767 0° (power2.in)
Left Middle Blue scaleX: 1.767 1 · 1.833 1.032 (power2.out) · 2.083 1 (back.out)
Left Middle Blue scaleY: 1.767 1 · 1.833 0.92 (power2.out) · 2.083 1 (back.out)
Left Middle Blue y: 1.35 -767.25 · 1.767 32.75 (power2.in)
Left Slab Lilac rotation: 1.567 12° · 1.983 0° (power2.in)
Left Slab Lilac scaleX: 1.983 1 · 2.033 1.032 (power2.out) · 2.3 1 (back.out)
Left Slab Lilac scaleY: 1.983 1 · 2.033 0.92 (power2.out) · 2.3 1 (back.out)
Left Slab Lilac y: 1.567 -804.75 · 1.983 -4.75 (power2.in)
Left Top Lime rotation: 1.483 -6° · 1.917 0° (power2.in)
Left Top Lime scaleX: 1.917 1 · 1.967 1.032 (power2.out) · 2.233 1 (back.out)
Left Top Lime scaleY: 1.917 1 · 1.967 0.92 (power2.out) · 2.233 1 (back.out)
Left Top Lime y: 1.483 -785.75 · 1.917 14.25 (power2.in)
Right Bottom Black rotation: 1.133 11° · 1.567 0° (power2.in)
Right Bottom Black scaleX: 1.567 1 · 1.617 1.032 (power2.out) · 1.883 1 (back.out)
Right Bottom Black scaleY: 1.567 1 · 1.617 0.92 (power2.out) · 1.883 1 (back.out)
Right Bottom Black y: 1.133 -748.25 · 1.567 51.75 (power2.in)
Right Bottom Lilac rotation: 1.217 -9° · 1.633 0° (power2.in)
Right Bottom Lilac scaleX: 1.633 1 · 1.683 1.032 (power2.out) · 1.95 1 (back.out)
Right Bottom Lilac scaleY: 1.633 1 · 1.683 0.92 (power2.out) · 1.95 1 (back.out)
Right Bottom Lilac y: 1.217 -748.25 · 1.633 51.75 (power2.in)
Right Middle Blue rotation: 1.417 8° · 1.833 0° (power2.in)
Right Middle Blue scaleX: 1.833 1 · 1.9 1.032 (power2.out) · 2.167 1 (back.out)
Right Middle Blue scaleY: 1.833 1 · 1.9 0.92 (power2.out) · 2.167 1 (back.out)
Right Middle Blue y: 1.417 -767.25 · 1.833 32.75 (power2.in)
Right Slab Lime rotation: 1.633 -8° · 2.05 0° (power2.in)
Right Slab Lime scaleX: 2.05 1 · 2.117 1.032 (power2.out) · 2.367 1 (back.out)
Right Slab Lime scaleY: 2.05 1 · 2.117 0.92 (power2.out) · 2.367 1 (back.out)
Right Slab Lime y: 1.633 -748.25 · 2.05 51.75 (power2.in)
Connections Backdrop x: 0.05 1600 · 1.55 0 (power2.inOut)
```
<!-- /keys -->

The loop starts and ends on the intro's last frame (ball x 616.07, y 624.36, spin 0, scale 1) and only keys the ball and the Left Slab Lilac: the ball rolls left to the slab's edge, teeters, rolls back and does two hops in place, the slab thumping as it lands.

<!-- keys: Connections Loop -->
```text
Connections Loop · 372 frames · 6.2 s · loops
Connections Ball scaleX: 3.3 1 · 3.383 1.12 (power2.out) · 3.617 1 (back.out) · 3.783 1 (hold) · 3.867 1.12 (power2.out) · 4.1 1 (back.out) · 4.267 1 (hold) · 4.333 1.06 (power2.out) · 4.583 1 (back.out)
Connections Ball scaleY: 3.3 1 · 3.383 0.88 (power2.out) · 3.617 1 (back.out) · 3.783 1 (hold) · 3.867 0.88 (power2.out) · 4.1 1 (back.out) · 4.267 1 (hold) · 4.333 0.94 (power2.out) · 4.583 1 (back.out)
Connections Ball x: 0 616.07 · 0.6 616.07 (hold) · 1.6 552 (sine.inOut) · 1.8 550 (sine.inOut) · 2.1 553 (sine.inOut) · 2.3 552 (sine.inOut) · 3.3 616.07 (sine.inOut) · 6.2 616.07 (hold)
Connections Ball y: 0 624.36 · 3.383 624.36 (hold) · 3.583 598.36 (power2.out) · 3.783 624.36 (power2.in) · 3.867 624.36 (hold) · 4.067 610.36 (power2.out) · 4.267 624.36 (power2.in) · 6.2 624.36 (hold)
Connections Ball Spin rotation: 0 0° · 0.6 0° (hold) · 1.6 -207° (sine.inOut) · 1.8 -217° (sine.inOut) · 2.1 -199° (sine.inOut) · 2.3 -207° (sine.inOut) · 3.3 0° (sine.inOut) · 6.2 0° (hold)
Left Slab Lilac scaleX: 3.783 1 · 3.833 1.02 (power2.out) · 4.1 1 (back.out) · 4.267 1 (hold) · 4.317 1.02 (power2.out) · 4.583 1 (back.out)
Left Slab Lilac scaleY: 3.783 1 · 3.833 0.95 (power2.out) · 4.1 1 (back.out) · 4.267 1 (hold) · 4.317 0.95 (power2.out) · 4.583 1 (back.out)
```
<!-- /keys -->

<!-- keys: Connections Outro -->
```text
Connections Outro · 96 frames · 1.6 s · plays once
Connections Room x: 0.05 0 · 1.55 -1600 (power2.inOut)
Connections Wall Lag x: 0.05 0 · 1.55 320 (power2.inOut)
Connections Draw Rules drawTargetId: 0 Connections Bottom
```
<!-- /keys -->

<!-- keys: Connections Home -->
```text
Connections Home · 1 frame · plays once
Connections Room x: 0 0
Connections Wall Lag x: 0 0
Connections Draw Rules drawTargetId: 0 Connections Normal
```
<!-- /keys -->

<!-- keys: Connections Gone -->
```text
Connections Gone · 1 frame · plays once
Connections Room x: 0 -1600
Connections Wall Lag x: 0 320
Connections Draw Rules drawTargetId: 0 Connections Bottom
```
<!-- /keys -->

## State machine

Two layers per room, so layers never key the same property. A game appears in one unbroken run of cards, so a room never comes back once it has left.

- **`<Room>`**: Waiting → Intro when `scene` == n (no exit time, duration 0) → Loop at exit time 100% (duration 0). The Shelf layer has no intro: it starts in Shelf Loop.
- **`<Room> Exit`**: Home → Shown when `scene` == n → Outro when `scene` != n (no exit time, duration 0) → Gone at exit time 100%. "Shown" plays the Home pose again, so the room holds at x 0 while it is the current scene. Shelf Exit starts in Shown, because the opener is on screen at load.

<!-- keys: State machine -->
```text
State machine "Chapter 2" · view model "Chapter 2": scene · default state machine: Chapter 2
layer "Shelf": starts in Shelf Loop
layer "Shelf Exit": starts in Shelf Home (2)
  Shelf Home -> Shelf Home (2) when scene == 0, 0 ms
  Shelf Home (2) -> Shelf Outro when scene != 0, 0 ms
  Shelf Outro -> Shelf Gone at the end (exit time 100%), 0 ms
layer "Wordle": starts in Wordle Waiting
  Wordle Waiting -> Wordle Intro when scene == 1, 0 ms
  Wordle Intro -> Wordle Loop at the end (exit time 100%), 0 ms
layer "Wordle Exit": starts in Wordle Home
  Wordle Home -> Wordle Home (2) when scene == 1, 0 ms
  Wordle Home (2) -> Wordle Outro when scene != 1, 0 ms
  Wordle Outro -> Wordle Gone at the end (exit time 100%), 0 ms
layer "Connections": starts in Connections Waiting
  Connections Waiting -> Connections Intro when scene == 2, 0 ms
  Connections Intro -> Connections Loop at the end (exit time 100%), 0 ms
layer "Connections Exit": starts in Connections Home
  Connections Home -> Connections Home (2) when scene == 2, 0 ms
  Connections Home (2) -> Connections Outro when scene != 2, 0 ms
  Connections Outro -> Connections Gone at the end (exit time 100%), 0 ms
```
<!-- /keys -->

What engineering relies on: the artboard "Chapter 2", the state machine "Chapter 2", the view model "Chapter 2" with the number `scene`, and the file loaded with autoplay and the view model bound (`autoBind`). Nothing else is needed. Each intro takes exactly 3.2 s from the moment `scene` changes, and its loop starts on the same frame.

## HTML text and icon (not in the Rive file; for reference)

The page's text motion is `engineering/yig-text-motion.css`, timed to the 3.2 s intro. A game has several cards, one frame each; a tap inside a game swaps only the text, and the tap after the game's last card starts the next game. The game's small icon is its own block, one per game: it pops in with the first card (3.2 s after the tap that starts the game), stays while later cards change, and lifts out with the last card's text. The Rive lockup (icon plus word) plays during the intro and is gone at 3.2 s. A same-game tap during the intro waits until the intro ends.

## Adding a game

Built from adding Wordle and Connections. A new game, say Strands (scene 3), is a new room plus two layers. In stages, running `npm run check ch2` after each one:

1. **Import the art** into the Rive Editor first (the CLI has no SVG import), then `rive pull chapters/ch2`. Name groups in Title Case with spaces. Give every group that rotates or squashes its pivot, with an inner "Art" group offset back (wrap it if the import flattened it).
2. **Make the room.** A `Strands Room` at x 0, in the tree above the room below it: Floor Plane (pieces), Wall Lag wrapping a Wall Plane (even if empty), the incoming Ball (Ball > Ball Spin > Ball Art), the Lockup as the room's first child, and the Backdrop as the **last** child (wall colour, floor, 2-unit floor line, 2-unit wall corner at x −1, all 1600 wide). Add `Strands Draw Rules` with two targets (see Draw rules).
3. **Waiting, then Intro.** Build the Intro (3.2 s exactly): the backdrop 1600 → 0, the floor plane (and wall plane) pan with `power2.inOut` 0.05 → 1.55, the pieces' entrance, the ball rolling in to the room's loop start pose, and the lockup (rise in after the pieces land, gone exactly at 3.2 s). **Never key anything outside the room.** Then build `Strands Waiting` from the Intro's first keys.
4. **Loop.** It starts and ends on the Intro's last frame, so the seam is invisible.
5. **Outro, Home, Gone.** Outro keys only the room's x, its Wall Lag x and its draw rule (Bottom): `0.05 0 → 1.55 −1600`, lag `0 → 320`. Home keys x 0, lag 0 and the draw rule Normal. Gone holds x −1600, the lag at its end value and the draw rule Bottom.
6. **The two layers.** `Strands`: Waiting → Intro (`scene` == 3) → Loop. `Strands Exit`: Home → Shown (`scene` == 3) → Outro (`scene` != 3) → Gone.
7. **Draw order.** Add the new room's Normal target for the room above it, and re-point the room above's Normal target at the new room's top shape.
8. **Check.** `npm run check ch2`; then the slower passes before handoff: `npm run tap` (interrupted taps, both orders, now with the new pair), `npm run text`, and look at it in the harness.
9. **Add its cards** to `harness/copy.html`, and its scene number to the integration file's table.

## Ease reference

| GSAP name | Rive cubic bezier | Used for |
|---|---|---|
| power2.inOut | 0.65, 0, 0.35, 1 | camera pan, outro, backdrop |
| power2.in | 0.32, 0, 0.67, 0 | falls, tips, hop descents |
| power2.out | 0.33, 1, 0.68, 1 | hop ascents, squash down, shadows |
| power1.out | 0.5, 1, 0.89, 1 | ball rolling in |
| power1.inOut | 0.45, 0, 0.55, 1 | ball spin on hops |
| sine.inOut | 0.37, 0, 0.63, 1 | loops: rocking, rolling, teetering |
| expo.out | 0.16, 1, 0.3, 1 | lockup rising in (matches the text's Rise in) |
| power3.in | 0.5, 0, 0.75, 0 | lockup lifting out (close to the text's Lift out) |
| back.out | 0.34, 1.56, 0.64, 1 | squash recovering, with a small overshoot |
