# Rooms, in plain words

## To tune later

**The ball in The Mini, The Midi and The Crossword does not look quite right, and its easing does not feel like the illustrator's original, even though `tools/compare_room.py` says the loops match.** Known, not fixed. Look into it when the finesse work starts. Best guesses at the cause, most likely first:

1. **The baked rig.** The illustrator's ball is driven by a joystick, a `Ball_Move` solo and the `Ball_Squash` / `Ball_Scale` helper animations. We sampled that rig into direct keys, one per frame where a value moves, thinned where a straight line was "exact" (tolerance 1e-4). Squash and stretch then play as straight lines between whole frames, where the rig mixed several animations with their own easing and could change between frames. Timing that lives between frames, and the overlap of two eases, are flattened.
2. **Squash, stretch and pivots.** The squash is drawn into the ball's shape keys (vertex x/y, in and out handles) and the highlight. Baking turned a rig that scaled around its own origin into keys on the shape. If a pivot, handle rotation or the Solo's active child is read slightly differently, the ball changes shape the wrong way around the floor line even when each frame is close.
3. **Two position nodes.** The Midi (and the other two) place the ball with `Ball_Move` plus a `Ball_01` offset, each with its own curves (some `cubicValue`). We copy both untouched, but our sheet and the Rive runtime may read `cubicValue` or `elastic` keys differently from the Editor's preview, and any ease the Editor shows is the sum of the two.
4. **What the frame comparison cannot see.** It compares whole frames at whole-frame times, ignores differences of 12 colour levels or less, the 30 px border and the floor-line rows (709 to 715), which is exactly where the ball lands and squashes. It also never compares speed (the frame before and after), the hand-off from the intro into the loop, or the loop wrapping from its last frame to its first. A ball that is in the right place on every frame can still move with the wrong easing.
5. **The returns we added.** Where the source loop does not close we added a return at the end (the Midi return is now 20 frames, eased). The ball's easing into and out of that return is ours, not the illustrator's.
6. **Intro hand-off.** Our intro lands the ball on the loop's first pose with our own roll and hop; the source has no intro, so its first loop frames are never seen the way ours are.

Ways to look: play the source's ball and ours at the same size, slowed, and plot ball position and scale per frame for both; compare crops of the ball only, with the floor-line rows included; check the rig's helper animations for keys on half frames; try the room with the ball left un-thinned.


Generated from `chapters/ch2/scene.rml` by `python3 tools/rooms_sheet.py ch2`. Do not edit by hand: change the room, then run the
script (it also runs `--check` in `npm run check`). Use it to ask for changes in these terms, for example
"The Mini: Move 2 of the ball 0.1 s slower" or "The Midi Boxes 2 drops 0.05 s later".

Times are seconds from the start of the intro (it is exactly 3.2 s) or of the loop. Every room is self-contained: its intro,
ball and loop are keyed only on its own pieces, so a change in one room never reaches another.

**Easing, in words:** `power2.in` starts slow and speeds up (a drop); `power2.out` is fast, then eases to a stop;
`power2.inOut` and `sine.inOut` are slow, fast, slow; `back.out` overshoots a little then settles (the squash recovery);
`expo.out` is very fast then a long settle (the lockup); `linear` is constant speed.

**Ball moves in the loop** are found from where the ball actually is on each frame (its position nodes added together), so
"Move 2" is the second time the ball travels. "Rising N px" means a hop. Squash and stretch inside a loop are drawn into the
illustrator's shape keys and are not listed here.


## The opener (Shelf) · scene 0

**Loop:** 1.80 s (108 frames at 60/s), repeats. First and last frames are the same pose.

No intro of its own (the opener is the first frame).


### Ball · loop

- **Move 1**: 0.15 s to 0.30 s (0.15 s): ends where it began
- **Move 2**: 0.75 s to 1.05 s (0.30 s): 5 px left
- **Move 3**: 1.50 s to 1.65 s (0.15 s): ends where it began
- Waits: 0.30–0.75 s, 1.05–1.50 s

## Wordle · scene 1

**Loop:** 7.20 s (432 frames at 60/s), repeats. First and last frames are the same pose.

### Intro · exactly 3.2 s

- **Floor and front slide in** (Wordle Floor Plane): moves left 1600 px (x 2348 → 748), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)
- **Pair LE**: turns 90° → 0°, starts 1.15 s, takes 0.30 s, power2.in (starts slow, speeds up)
- **Pair LE**: squash on landing: 1.028 wide × 0.93 tall at 1.52 s (reached over 0.07 s, power2.out); back to 1 by 1.77 s (back.out)
- **Pair BD**: turns 90° → 0°, starts 1.27 s, takes 0.30 s, power2.in (starts slow, speeds up)
- **Pair BD**: squash on landing: 1.028 wide × 0.93 tall at 1.63 s (reached over 0.07 s, power2.out); back to 1 by 1.88 s (back.out)
- **Pair WR**: turns -62° → -14°, starts 1.33 s, takes 0.42 s, power2.in (starts slow, speeds up)
- **Pair WR**: turns -14° → 0°, starts 1.75 s, takes 0.13 s, power2.in (starts slow, speeds up)
- **Pair WR**: drops 800 px (y -800 → 0), starts 1.33 s, takes 0.42 s, power2.in (starts slow, speeds up)
- **Pair WR**: squash on landing: 1.024 wide × 0.94 tall at 1.95 s (reached over 0.07 s, power2.out); back to 1 by 2.22 s (back.out)
- **Pair KE**: turns 90° → 0°, starts 1.38 s, takes 0.30 s, power2.in (starts slow, speeds up)
- **Pair KE**: squash on landing: 1.028 wide × 0.93 tall at 1.75 s (reached over 0.07 s, power2.out); back to 1 by 2.02 s (back.out)
- **Pair OM**: turns 62° → 14°, starts 1.45 s, takes 0.42 s, power2.in (starts slow, speeds up)
- **Pair OM**: turns 14° → 0°, starts 1.87 s, takes 0.15 s, power2.in (starts slow, speeds up)
- **Pair OM**: drops 800 px (y -800 → 0), starts 1.45 s, takes 0.42 s, power2.in (starts slow, speeds up)
- **Pair OM**: squash on landing: 1.024 wide × 0.94 tall at 2.07 s (reached over 0.05 s, power2.out); back to 1 by 2.33 s (back.out)
- **Shadow B**: scale 0 → 1, starts 1.88 s, takes 0.20 s, power2.out
- **Shadow E**: scale 0 → 1, starts 1.88 s, takes 0.20 s, power2.out
- **Shadow K**: scale 0 → 1, starts 2.02 s, takes 0.20 s, power2.out
- **Shadow R**: scale 0 → 1, starts 2.02 s, takes 0.20 s, power2.out
- **Lockup** (icon and word): fades in 1.92–2.13 s, held, fades out ending 3.20 s; hidden on community cards

### Ball · intro

- **Wordle Ball**: moves right 636 px (x -80 → 556), starts 1.15 s, takes 0.60 s, power1.out (fast, then a soft stop)
- **Wordle Ball**: moves right 95 px (x 556 → 651), starts 1.75 s, takes 0.37 s, linear (constant speed)
- **Wordle Ball**: moves right 56 px (x 651 → 707), starts 2.17 s, takes 0.37 s, linear (constant speed)
- **Wordle Ball**: rises 102 px (y 712 → 610), starts 1.75 s, takes 0.17 s, power2.out (fast, then eases to a stop)
- **Wordle Ball**: drops 45 px (y 610 → 655), starts 1.92 s, takes 0.20 s, power2.in (starts slow, speeds up)
- **Wordle Ball**: rises 96 px (y 655 → 559), starts 2.17 s, takes 0.17 s, power2.out (fast, then eases to a stop)
- **Wordle Ball**: drops 45 px (y 559 → 604), starts 2.33 s, takes 0.20 s, power2.in (starts slow, speeds up)
- **Wordle Ball**: rises 12 px (y 604 → 592), starts 2.62 s, takes 0.12 s, power2.out (fast, then eases to a stop)
- **Wordle Ball**: drops 12 px (y 592 → 604), starts 2.73 s, takes 0.12 s, power2.in (starts slow, speeds up)
- **Wordle Ball**: squash on landing: 1.16 wide × 0.84 tall at 2.18 s (reached over 0.07 s, power2.out); back to 1 by 3.17 s (back.out)
- **Wordle Ball Spin**: turns -1080° → 0°, starts 1.15 s, takes 1.38 s, power1.out (fast, then a soft stop)

### Ball · loop

- **Move 1**: 0.63 s to 1.67 s (1.03 s): 104 px right
- **Move 2**: 1.78 s to 1.82 s (0.03 s): ends where it began
- **Move 3**: 2.02 s to 2.08 s (0.07 s): ends where it began
- **Move 4**: 2.40 s to 2.82 s (0.42 s): 29 px right and 51 px down, rising 26 px above its start/finish height
- **Move 5**: 2.88 s to 3.03 s (0.15 s): 24 px up
- **Move 6**: 3.10 s to 3.38 s (0.28 s): 12 px down
- **Move 7**: 3.45 s to 3.55 s (0.10 s): 12 px down
- **Move 8**: 3.67 s to 4.17 s (0.50 s): 51 px left and 51 px up, rising 52 px above its start/finish height
- **Move 9**: 4.30 s to 5.13 s (0.83 s): 82 px left
- Waits: 1.67–1.78 s, 1.82–2.02 s, 2.08–2.40 s, 2.82–2.88 s, 3.03–3.10 s, 3.38–3.45 s, 3.55–3.67 s, 4.17–4.30 s

## Connections · scene 2

**Loop:** 6.20 s (372 frames at 60/s), repeats. First and last frames are the same pose.

### Intro · exactly 3.2 s

- **Floor and front slide in** (Connections Floor Plane): moves left 1600 px (x 2348 → 748), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)
- **Floor and front slide in** (Connections Wall Plane): moves left 1280 px (x 2069 → 789), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)
- **Left Bottom Black**: turns 9° → 0°, starts 1.00 s, takes 0.42 s, power2.in (starts slow, speeds up)
- **Left Bottom Black**: drops 800 px (y -748 → 52), starts 1.00 s, takes 0.42 s, power2.in (starts slow, speeds up)
- **Left Bottom Black**: squash on landing: 1.032 wide × 0.92 tall at 1.48 s (reached over 0.07 s, power2.out); back to 1 by 1.73 s (back.out)
- **Left Bottom Green**: turns -7° → 0°, starts 1.07 s, takes 0.42 s, power2.in (starts slow, speeds up)
- **Left Bottom Green**: drops 800 px (y -748 → 52), starts 1.07 s, takes 0.42 s, power2.in (starts slow, speeds up)
- **Left Bottom Green**: squash on landing: 1.032 wide × 0.92 tall at 1.55 s (reached over 0.07 s, power2.out); back to 1 by 1.82 s (back.out)
- **Right Bottom Black**: turns 11° → 0°, starts 1.13 s, takes 0.43 s, power2.in (starts slow, speeds up)
- **Right Bottom Black**: drops 800 px (y -748 → 52), starts 1.13 s, takes 0.43 s, power2.in (starts slow, speeds up)
- **Right Bottom Black**: squash on landing: 1.032 wide × 0.92 tall at 1.62 s (reached over 0.05 s, power2.out); back to 1 by 1.88 s (back.out)
- **Right Bottom Lilac**: turns -9° → 0°, starts 1.22 s, takes 0.42 s, power2.in (starts slow, speeds up)
- **Right Bottom Lilac**: drops 800 px (y -748 → 52), starts 1.22 s, takes 0.42 s, power2.in (starts slow, speeds up)
- **Right Bottom Lilac**: squash on landing: 1.032 wide × 0.92 tall at 1.68 s (reached over 0.05 s, power2.out); back to 1 by 1.95 s (back.out)
- **Left Middle Black**: turns 6° → 0°, starts 1.28 s, takes 0.42 s, power2.in (starts slow, speeds up)
- **Left Middle Black**: drops 800 px (y -767 → 33), starts 1.28 s, takes 0.42 s, power2.in (starts slow, speeds up)
- **Left Middle Black**: squash on landing: 1.032 wide × 0.92 tall at 1.77 s (reached over 0.07 s, power2.out); back to 1 by 2.02 s (back.out)
- **Left Middle Blue**: turns -10° → 0°, starts 1.35 s, takes 0.42 s, power2.in (starts slow, speeds up)
- **Left Middle Blue**: drops 800 px (y -767 → 33), starts 1.35 s, takes 0.42 s, power2.in (starts slow, speeds up)
- **Left Middle Blue**: squash on landing: 1.032 wide × 0.92 tall at 1.83 s (reached over 0.07 s, power2.out); back to 1 by 2.08 s (back.out)
- **Right Middle Blue**: turns 8° → 0°, starts 1.42 s, takes 0.42 s, power2.in (starts slow, speeds up)
- **Right Middle Blue**: drops 800 px (y -767 → 33), starts 1.42 s, takes 0.42 s, power2.in (starts slow, speeds up)
- **Right Middle Blue**: squash on landing: 1.032 wide × 0.92 tall at 1.90 s (reached over 0.07 s, power2.out); back to 1 by 2.17 s (back.out)
- **Left Top Lime**: turns -6° → 0°, starts 1.48 s, takes 0.43 s, power2.in (starts slow, speeds up)
- **Left Top Lime**: drops 800 px (y -786 → 14), starts 1.48 s, takes 0.43 s, power2.in (starts slow, speeds up)
- **Left Top Lime**: squash on landing: 1.032 wide × 0.92 tall at 1.97 s (reached over 0.05 s, power2.out); back to 1 by 2.23 s (back.out)
- **Left Slab Lilac**: turns 12° → 0°, starts 1.57 s, takes 0.42 s, power2.in (starts slow, speeds up)
- **Left Slab Lilac**: drops 800 px (y -805 → -5), starts 1.57 s, takes 0.42 s, power2.in (starts slow, speeds up)
- **Left Slab Lilac**: squash on landing: 1.032 wide × 0.92 tall at 2.03 s (reached over 0.05 s, power2.out); back to 1 by 2.30 s (back.out)
- **Right Slab Lime**: turns -8° → 0°, starts 1.63 s, takes 0.42 s, power2.in (starts slow, speeds up)
- **Right Slab Lime**: drops 800 px (y -748 → 52), starts 1.63 s, takes 0.42 s, power2.in (starts slow, speeds up)
- **Right Slab Lime**: squash on landing: 1.032 wide × 0.92 tall at 2.12 s (reached over 0.07 s, power2.out); back to 1 by 2.37 s (back.out)
- **Lockup** (icon and word): fades in 2.10–2.32 s, held, fades out ending 3.20 s; hidden on community cards

### Ball · intro

- **Connections Ball**: moves right 550 px (x -80 → 470), starts 1.15 s, takes 0.60 s, power1.out (fast, then a soft stop)
- **Connections Ball**: moves right 146 px (x 470 → 616), starts 1.75 s, takes 0.50 s, linear (constant speed)
- **Connections Ball**: rises 148 px (y 712 → 564), starts 1.75 s, takes 0.23 s, power2.out (fast, then eases to a stop)
- **Connections Ball**: drops 60 px (y 564 → 624), starts 1.98 s, takes 0.27 s, power2.in (starts slow, speeds up)
- **Connections Ball**: rises 12 px (y 624 → 612), starts 2.33 s, takes 0.12 s, power2.out (fast, then eases to a stop)
- **Connections Ball**: drops 12 px (y 612 → 624), starts 2.45 s, takes 0.12 s, power2.in (starts slow, speeds up)
- **Connections Ball**: squash on landing: 1.22 wide × 0.78 tall at 2.33 s (reached over 0.08 s, power2.out); back to 1 by 2.88 s (back.out)
- **Connections Ball Spin**: turns -1080° → 0°, starts 1.15 s, takes 1.10 s, power1.out (fast, then a soft stop)

### Ball · loop

- **Move 1**: 0.65 s to 1.55 s (0.90 s): 63 px left
- **Move 2**: 1.68 s to 1.72 s (0.03 s): ends where it began
- **Move 3**: 1.92 s to 1.98 s (0.07 s): ends where it began
- **Move 4**: 2.35 s to 3.25 s (0.90 s): 63 px right
- **Move 5**: 3.38 s to 3.55 s (0.17 s): 26 px up
- **Move 6**: 3.62 s to 3.78 s (0.17 s): 26 px down
- **Move 7**: 3.87 s to 4.02 s (0.15 s): 14 px up
- **Move 8**: 4.12 s to 4.27 s (0.15 s): 14 px down
- Waits: 1.55–1.68 s, 1.72–1.92 s, 1.98–2.35 s, 3.25–3.38 s, 3.55–3.62 s, 3.78–3.87 s, 4.02–4.12 s

## Strands · scene 3

**Loop:** 3.00 s (180 frames at 60/s), repeats. First and last frames are the same pose.

### Intro · exactly 3.2 s

- **Floor and front slide in** (Strands Floor Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)
- **Floor and front slide in** (Strands Front Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)
- **Strands Left Strand**: drops 800 px (y -163 → 637), starts 1.00 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **Strands Left Strand**: squash on landing: 1.03 wide × 0.93 tall at 1.57 s (reached over 0.07 s, power2.out); back to 1 by 1.82 s (back.out)
- **Strands Yellow Strand 1**: drops 800 px (y -118 → 682), starts 1.15 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **Strands Yellow Strand 1**: squash on landing: 1.03 wide × 0.93 tall at 1.72 s (reached over 0.07 s, power2.out); back to 1 by 1.97 s (back.out)
- **Strands Yellow Strand 2**: drops 800 px (y -118 → 682), starts 1.15 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **Strands Yellow Strand 2**: squash on landing: 1.03 wide × 0.93 tall at 1.72 s (reached over 0.07 s, power2.out); back to 1 by 1.97 s (back.out)
- **Lockup** (icon and word): fades in 1.92–2.13 s, held, fades out ending 3.20 s; hidden on community cards

### Ball · intro

- **Strands Ball**: moves right 909 px (x -80 → 829), starts 1.15 s, takes 0.75 s, power1.out (fast, then a soft stop)
- **Strands Ball**: rises 76 px (y 756 → 680), starts 1.90 s, takes 0.15 s, power2.out (fast, then eases to a stop)
- Highlight and shape ease into the landing pose, 1.15 s to 2.05 s.

### Ball · loop

- **Move 1**: 0.00 s to 1.25 s (1.25 s): 182 px left and 58 px down, rising 156 px above its start/finish height
- **Move 2**: 1.50 s to 2.98 s (1.48 s): 177 px right and 72 px up, rising 137 px above its start/finish height
- Waits: 1.25–1.50 s

## Spelling Bee · scene 4

**Loop:** 4.00 s (240 frames at 60/s), repeats. First and last frames are the same pose.

### Intro · exactly 3.2 s

- **Floor and front slide in** (Spelling Bee Floor Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)
- **Floor and front slide in** (Spelling Bee Front Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)
- **Spelling Bee Mug 1**: drops 800 px (y -225 → 575), starts 1.00 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **Spelling Bee Mug 1**: squash on landing: 1.03 wide × 0.93 tall at 1.57 s (reached over 0.07 s, power2.out); back to 1 by 1.82 s (back.out)
- **Spelling Bee Mug 2**: drops 800 px (y -225 → 575), starts 1.00 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **Spelling Bee Mug 2**: squash on landing: 1.03 wide × 0.93 tall at 1.57 s (reached over 0.07 s, power2.out); back to 1 by 1.82 s (back.out)
- **Spelling Bee Left Hex**: drops 800 px (y -141 → 659), starts 1.10 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **Spelling Bee Left Hex**: squash on landing: 1.03 wide × 0.93 tall at 1.67 s (reached over 0.07 s, power2.out); back to 1 by 1.92 s (back.out)
- **Spelling Bee Right Hex**: drops 800 px (y -181 → 619), starts 1.20 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **Spelling Bee Right Hex**: squash on landing: 1.03 wide × 0.93 tall at 1.77 s (reached over 0.07 s, power2.out); back to 1 by 2.02 s (back.out)
- **Lockup** (icon and word): fades in 1.92–2.13 s, held, fades out ending 3.20 s; hidden on community cards

### Ball · intro

- **Spelling Bee Ball**: moves right 785 px (x -80 → 705), starts 1.15 s, takes 0.75 s, power1.out (fast, then a soft stop)
- Highlight and shape ease into the landing pose, 1.15 s to 2.05 s.

### Ball · loop

- **Move 1**: 0.00 s to 3.93 s (3.93 s): ends where it began, rising 203 px above its start/finish height

## The Mini · scene 5

**Loop:** 2.50 s (150 frames at 60/s), repeats. First and last frames are the same pose.

### Intro · exactly 3.2 s

- **Floor and front slide in** (The Mini Floor Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)
- **Floor and front slide in** (The Mini Front Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)
- **The Mini Cubes 1**: drops 800 px (y -40 → 760), starts 1.00 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **The Mini Cubes 1**: squash on landing: 1.03 wide × 0.93 tall at 1.57 s (reached over 0.07 s, power2.out); back to 1 by 1.82 s (back.out)
- **The Mini Cubes 3**: drops 800 px (y -40 → 760), starts 1.13 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **The Mini Cubes 3**: squash on landing: 1.03 wide × 0.93 tall at 1.70 s (reached over 0.07 s, power2.out); back to 1 by 1.95 s (back.out)
- **The Mini Cubes 2**: drops 800 px (y -40 → 760), starts 1.27 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **The Mini Cubes 2**: squash on landing: 1.03 wide × 0.93 tall at 1.83 s (reached over 0.07 s, power2.out); back to 1 by 2.08 s (back.out)
- **The Mini Cubes 4**: drops 800 px (y -40 → 760), starts 1.27 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **The Mini Cubes 4**: squash on landing: 1.03 wide × 0.93 tall at 1.83 s (reached over 0.07 s, power2.out); back to 1 by 2.08 s (back.out)
- **Lockup** (icon and word): fades in 1.92–2.13 s, held, fades out ending 3.20 s; hidden on community cards

### Ball · intro

- **The Mini Ball**: moves right 746 px (x -80 → 666), starts 1.15 s, takes 0.75 s, power1.out (fast, then a soft stop)

### Ball · loop

- **Move 1**: 0.00 s to 1.23 s (1.23 s): 86 px left and 135 px up, rising 268 px above its start/finish height
- **Move 2**: 1.52 s to 2.48 s (0.97 s): 86 px right and 135 px down, rising 150 px above its start/finish height
- Waits: 1.23–1.52 s

## The Midi · scene 6

**Loop:** 2.50 s (150 frames at 60/s), repeats. First and last frames are the same pose.

### Intro · exactly 3.2 s

- **Floor and front slide in** (The Midi Floor Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)
- **Floor and front slide in** (The Midi Front Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)
- **The Midi Boxes 1**: drops 800 px (y -24 → 776), starts 1.00 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **The Midi Boxes 1**: squash on landing: 1.03 wide × 0.93 tall at 1.57 s (reached over 0.07 s, power2.out); back to 1 by 1.82 s (back.out)
- **The Midi Boxes 2**: drops 800 px (y -24 → 776), starts 1.13 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **The Midi Boxes 2**: squash on landing: 1.03 wide × 0.93 tall at 1.70 s (reached over 0.07 s, power2.out); back to 1 by 1.95 s (back.out)
- **Lockup** (icon and word): fades in 1.92–2.13 s, held, fades out ending 3.20 s; hidden on community cards

### Ball · intro

- **The Midi Ball**: moves right 939 px (x -259 → 680), starts 1.15 s, takes 0.75 s, power1.out (fast, then a soft stop)
- **The Midi Ball**: rises 139 px (y 792 → 652), starts 1.90 s, takes 0.15 s, power2.out (fast, then eases to a stop)

### Ball · loop

- **Move 1**: 0.00 s to 0.98 s (0.98 s): 125 px left and 68 px down
- **Move 2**: 1.35 s to 1.88 s (0.53 s): 66 px right and 80 px down, rising 46 px above its start/finish height
- **Move 3**: 2.15 s to 2.48 s (0.33 s): 59 px right and 148 px up
- Waits: 0.98–1.35 s, 1.88–2.15 s

## The Crossword · scene 7

**Loop:** 3.00 s (180 frames at 60/s), repeats. First and last frames are the same pose.

### Intro · exactly 3.2 s

- **Floor and front slide in** (The Crossword Floor Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)
- **Floor and front slide in** (The Crossword Front Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)
- **The Crossword Front Boxes 1**: drops 800 px (y -52 → 748), starts 1.00 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **The Crossword Front Boxes 1**: squash on landing: 1.03 wide × 0.93 tall at 1.57 s (reached over 0.07 s, power2.out); back to 1 by 1.82 s (back.out)
- **The Crossword Front Boxes 2**: drops 800 px (y -52 → 748), starts 1.13 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **The Crossword Front Boxes 2**: squash on landing: 1.03 wide × 0.93 tall at 1.70 s (reached over 0.07 s, power2.out); back to 1 by 1.95 s (back.out)
- **Lockup** (icon and word): fades in 1.92–2.13 s, held, fades out ending 3.20 s; hidden on community cards

### Ball · intro

- **The Crossword Ball**: moves right 704 px (x -40 → 664), starts 1.15 s, takes 0.75 s, power1.out (fast, then a soft stop)
- **The Crossword Ball**: rises 128 px (y 821 → 692), starts 1.90 s, takes 0.15 s, power2.out (fast, then eases to a stop)

### Ball · loop

- **Move 1**: 0.00 s to 0.87 s (0.87 s): 92 px right and 67 px down
- **Move 2**: 0.93 s to 1.80 s (0.87 s): 128 px right and 54 px up
- **Move 3**: 2.13 s to 2.98 s (0.85 s): 221 px left and 14 px up
- Waits: 0.87–0.93 s, 1.80–2.13 s
