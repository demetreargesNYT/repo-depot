# Chapter 2 animation spec

The single source of truth for the Chapter 2 Rive file. The prompts in PROMPTS.md point Claude Code at one section at a time.

## Conventions

- **Artboard:** "Chapter 2", 1495 × 1067, clipping on. Coordinates are artboard units, origin top left, y down.
- **Time** is written in seconds. RML keys by frame at the animation's fps, so at 60 fps multiply by 60 (3.2 s = frame 192).
- **Rotation** is written in degrees, positive clockwise. RML stores rotation in radians, so multiply by π/180.
- **Colors** are written as #RRGGBB. RML colors are ARGB hex without the #, so #C3E2C0 becomes FFC3E2C0.
- **Eases** are written as GSAP names. Use the cubic bezier from the table at the end, and look up how RML expresses cubic interpolation with `rive docs --search interpolation` and `rive schema --search cubic`. Each ease applies to the segment that ends at that key.
- **Hold** means the value doesn't change between the two keys.
- **Balls** are three nested groups: `Ball` (positioned at the base of the ball; squash and stretch are scale keys here, so the ball stays on its surface), `Ball Spin` (rotation around the ball's centre) and `Ball Art`. In this spec, "Ball x / y" always means the base of the ball.
- **Pivots:** every group that rotates or squashes was exported with its own position on the pivot point and an inner "Art" group offset back, so the artwork stays put. Keep that structure.
- **Never key the Shelf Ball or Shelf Ball Spin in an intro.** The toy ball has to hold whatever pose it had when the player tapped, and leave with its room.

## Section 1 · Organize the import and set the design pose

The imported SVG holds the whole chapter. Organize it and set the design pose. No animations yet.

1. Artboard
   - Rename the artboard to "Chapter 2" and make sure it is 1495 × 1067 with clipping on.

2. Rename every imported group from hyphenated to Title Case with spaces, keeping the hierarchy:
   "Shelf-Wall-Plane" becomes "Shelf Wall Plane", "Pair-WR" becomes "Pair WR", "Wordle-Ball-Spin"
   becomes "Wordle Ball Spin", and so on. Groups ending in "-Art" become "... Art".
   Inner pieces like "cat-tail" become "Cat Tail".

3. Check the pivots. Each group below was imported with its position on a pivot point, and its
   "Art" child offset back so the artwork stays in place. Check each one with rive inspect and confirm its x and y
   match this list. If the import flattened a group so its origin isn't on the point, wrap its
   artwork in a new group placed at that point so the artwork doesn't move on screen. Report every
   group you had to fix.
   - Pair LE 712.14, 711.6 · Pair BD 792.43, 711.6 · Pair KE 862.68, 711.6
   - Pair WR 668.36, 654.85 · Pair OM 829.98, 654.85
   - Shadow E 712.14, 654.85 · Shadow B 712.14, 654.85 · Shadow K 792.43, 655.33 · Shadow R 740.69, 654.85
   - Left Bottom Black 562, 712.5 · Left Bottom Green 610, 712.5 · Left Middle Black 582, 693.5
   - Left Middle Blue 628.75, 693.5 · Left Top Lime 597, 675 · Left Slab Lilac 592.25, 656
   - Right Bottom Black 933, 712.5 · Right Bottom Lilac 900.5, 712.5 · Right Middle Blue 917, 693.5
   - Right Slab Lime 794.75, 712.5
   - Shelf Ball 778.88, 656.72 · Wordle Ball 707.11, 604.11 · Connections Ball 616.07, 624.36
     (these sit at the base of each ball; each "Ball Spin" child sits at the ball's center, 29.68 above
     for the Shelf Ball and 17.68 above for the other two)
   - Wordle Lockup 748, 363 · Connections Lockup 748, 363

4. Design pose. This is what frame 1 looks like, and what every intro animates away from. Set these
   values directly on the objects, not as keys:
   - Wall fill #E7F1E1. Floor fill #FEA0C9.
   - Wordle Floor Plane x +1600 from where it is now.
   - Pair LE, Pair BD, Pair KE rotation 90.
   - Pair WR y −800 and rotation −62. Pair OM y −800 and rotation 62.
   - Shadow E, Shadow B, Shadow K, Shadow R scale 0.
   - Wordle Ball x −80 and y 712 (just off the left edge, resting on the floor). Wordle Ball Spin rotation −1080.
   - Connections Wall Plane x +1280. Connections Floor Plane x +1600.
   - Every Connections tile y −800, with rotation:
     Left Bottom Black 9, Left Bottom Green −7, Right Bottom Black 11, Right Bottom Lilac −9,
     Left Middle Black 6, Left Middle Blue −10, Right Middle Blue 8, Left Top Lime −6,
     Left Slab Lilac 12, Right Slab Lime −8.
   - Connections Ball x −80 and y 712. Connections Ball Spin rotation −1080.
   - The two incoming balls are siblings of their room's floor plane, not children, so the pan
     doesn't carry them. Wordle Ball sits behind the Wordle Floor Plane (it rests behind the
     blocks' top edge) and Connections Ball sits in front of the Connections Floor Plane.
   - Wordle Lockup and Connections Lockup opacity 0.

5. Report what you changed. Confirm that with this pose the artboard shows only the shelf room on
   #E7F1E1, and that nothing from the Wordle or Connections rooms is inside the 1495 × 1067 bounds.

## Section 2 · Frame 1 Loop

Create a looping linear animation on the "Chapter 2" artboard named "Frame 1 Loop", 1.8 seconds,
loop on. It keys only the shelf room's toy ball, which rocks in place in the toy stand.

Keys, ease sine.inOut on every key (bezier 0.37, 0, 0.63, 1):
- Shelf Ball x: 0.00 rest · 0.45 rest +5 · 1.35 rest −5 · 1.80 rest
- Shelf Ball Spin rotation: 0.00 0 · 0.45 16 · 1.35 −16 · 1.80 0

Nothing else is keyed, so the rest of the room stays exactly in the design pose.

## Section 3 · Wordle Intro

Create a one-shot linear animation named "Wordle Intro", 3.2 seconds, loop off, on the "Chapter 2"
artboard. Key exactly what's listed and nothing else. In particular, never key the Shelf Ball or
Shelf Ball Spin, so the toy ball holds whatever pose it had when the player tapped and rides out
with its room. The first key on each property is its design pose value.

Ease beziers: power2.inOut 0.65,0,0.35,1 · power2.in 0.32,0,0.67,0 · power2.out 0.33,1,0.68,1 ·
power1.out 0.5,1,0.89,1 · power1.inOut 0.45,0,0.55,1 · expo.out 0.16,1,0.3,1 · power3.in 0.5,0,0.75,0 ·
back.out 0.34,1.56,0.64,1. Each ease applies to the segment ending at that key.

Camera pan (the camera moves right, so everything moves left)
- Shelf Wall Plane x: 0.05 0 · 1.55 −1280 (power2.inOut)
- Shelf Floor Plane x: 0.05 0 · 1.55 −1600 (power2.inOut)
- Wordle Floor Plane x: 0.05 design (+1600) · 1.55 0 (power2.inOut)
- Wall fill: 0.10 #E7F1E1 · 1.45 #C3E2C0 (power1.inOut)

Bottom row tips over, left to right. Rotation 90 → 0 with power2.in, then a squash:
scaleY 1 → 0.93 over 0.06s (power2.out) and back to 1 over 0.26s (back.out), with scaleX
1 → 1.028 → 1 on the same keys.
- Pair LE: rotation 1.15 90 · 1.45 0 · squash 1.45–1.77
- Pair BD: rotation 1.27 90 · 1.57 0 · squash 1.57–1.89
- Pair KE: rotation 1.39 90 · 1.69 0 · squash 1.69–2.01

Top pairs tumble in from above, land on a corner, and rock flat
- Pair WR: y 1.33 −800 · 1.75 0 (power2.in); rotation 1.33 −62 · 1.75 −14 (power2.in) · 1.89 0 (power2.in);
  squash scaleY 1.89 1 · 1.95 0.94 · 2.21 1 and scaleX 1 · 1.024 · 1
- Pair OM: y 1.45 −800 · 1.87 0 (power2.in); rotation 1.45 62 · 1.87 14 · 2.01 0 (power2.in); squash 2.01–2.33 as above

Shadows grow from each contact as the pair above settles (scale 0 → 1, power2.out)
- Shadow E and Shadow B: 1.89 0 · 2.09 1
- Shadow K and Shadow R: 2.01 0 · 2.21 1

New ball rolls in behind the camera and climbs. Wordle Ball sits at the base of the ball:
y 712 = on the floor, 654.85 = on the L block, 604.11 = resting on W.
- Wordle Ball x: 1.15 −80 · 1.75 556 (power1.out) · 2.11 651 (linear) · 2.17 651 (hold) · 2.53 707.11 (linear)
- Wordle Ball y: 1.15 712 · 1.75 712 (hold) · 1.912 609.85 (power2.out) · 2.11 654.85 (power2.in)
  · 2.17 654.85 (hold) · 2.332 559.11 (power2.out) · 2.53 604.11 (power2.in)
  · 2.61 604.11 (hold) · 2.73 592.11 (power2.out) · 2.85 604.11 (power2.in)
- Wordle Ball Spin rotation: 1.15 −1080 · 2.53 0 (power1.out)
- Wordle Ball squash, keys on scaleX / scaleY:
  2.11 1/1 · 2.19 1.16/0.84 (power2.out) · 2.43 1/1 (back.out)
  2.53 1/1 · 2.61 1.22/0.78 (power2.out) · 2.85 1/1 (back.out)
  2.85 1/1 · 2.93 1.08/0.92 (power2.out) · 3.17 1/1 (back.out)
- From 2.97 the ball is exactly on its loop start pose: x 707.11, y 604.11, rotation 0, scale 1.

Wordle lockup: rises in after the blocks land, gone exactly at 3.2 when the page text arrives
- Wordle Lockup y: 1.92 381 · 2.48 363 (expo.out) · 2.94 363 (hold) · 3.20 333 (power3.in)
- Wordle Lockup scale: 1.92 0.96 · 2.48 1 (expo.out) · 2.94 1 · 3.20 0.97 (power3.in)
- Wordle Lockup opacity: 1.92 0 · 2.14 1 (linear) · 2.94 1 · 3.20 0 (power2.in)
- Wordle Lockup Word: opacity 1.99 0 · 2.55 1 (expo.out); y 1.99 +10 · 2.55 0 (expo.out)

## Section 4 · Wordle Loop

Create a looping linear animation named "Wordle Loop", 7.2 seconds, loop on. Its first and last
frames must equal the end of "Wordle Intro": Wordle Ball x 707.11, y 604.11, Wordle Ball Spin 0,
ball scale 1. Only the Wordle Ball, Pair KE and Pair OM are keyed.
Y values are the base of the ball: 604.11 = on the top row, 654.85 = on the E block.
Eases as in Prompt 3, plus sine.inOut 0.37,0,0.63,1.

- 0.00–0.60 rest
- Roll right to the edge of M: x 0.60 707.11 · 1.70 812 (sine.inOut); Spin 0 → 340 (sine.inOut)
- Teeter at the edge: x 1.90 814 · 2.20 811 · 2.40 812; Spin 1.90 350 · 2.20 332 · 2.40 340 (sine.inOut)
- Hop down onto E: x 2.40 812 · 2.82 841 (linear); y 2.40 604.11 · 2.589 578.11 (power2.out) · 2.82 654.85 (power2.in)
- Bounce: y 2.88 654.85 (hold) · 3.06 630.85 (power2.out) · 3.24 654.85 (power2.in)
  · 3.29 654.85 (hold) · 3.42 642.85 (power2.out) · 3.55 654.85 (power2.in)
- Hop back up onto M: x 3.67 841 · 4.17 790 (linear); y 3.67 654.85 · 3.895 552.11 (power2.out) · 4.17 604.11 (power2.in);
  Spin 3.67 340 · 4.17 269 (power1.inOut)
- Roll home: x 4.27 790 · 5.17 707.11 (sine.inOut); Spin 4.27 269 · 5.17 0 (sine.inOut)
- 5.17–7.20 rest
- Ball squash (scaleX / scaleY, power2.out down over 0.08s, back.out up over 0.24s):
  1.20/0.80 at 2.82 · 1.14/0.86 at 3.24 · 1.08/0.92 at 3.55 · 1.22/0.78 at 4.17 · 1.06/0.94 at 5.17
- Pair KE thumps when the ball lands on E: scaleY 0.94 and scaleX 1.024 over 0.06s at 2.82,
  back over 0.26s (back.out); a softer 0.96 / 1.016 at 3.24
- Pair OM thumps at 4.17: scaleY 0.94, scaleX 1.024, same timing

Check that the loop point is seamless.

## Section 5 · Connections Intro

Create a one-shot linear animation named "Connections Intro", 3.2 seconds, loop off. Same rules as
"Wordle Intro": key only what's listed, and never key the Shelf Ball or Shelf Ball Spin.
Eases as in Prompt 3.

Camera pan
- Shelf Wall Plane x: 0.05 0 · 1.55 −1280 (power2.inOut)
- Shelf Floor Plane x: 0.05 0 · 1.55 −1600 (power2.inOut)
- Connections Wall Plane x: 0.05 design (+1280) · 1.55 0 (power2.inOut)
- Connections Floor Plane x: 0.05 design (+1600) · 1.55 0 (power2.inOut)
- Wall fill: 0.10 #E7F1E1 · 1.45 #E1DBF5 (power1.inOut)

Tiles drop in from above, bottom row first, 0.07s apart. Each one keys y −800 → 0 and rotation
from its design tilt → 0 over 0.42s with power2.in. On landing it squashes: scaleY 0.92 and scaleX
1.032 over 0.06s (power2.out), back to 1 over 0.26s (back.out).
Start times: Left Bottom Black 1.00 · Left Bottom Green 1.07 · Right Bottom Black 1.14 ·
Right Bottom Lilac 1.21 · Left Middle Black 1.28 · Left Middle Blue 1.35 · Right Middle Blue 1.42 ·
Left Top Lime 1.49 · Left Slab Lilac 1.56 · Right Slab Lime 1.63

New ball rolls in and takes one big hop onto the lilac slab.
Connections Ball y is the base of the ball: 712 = floor, 624.36 = resting on the slab.
- Connections Ball x: 1.15 −80 · 1.75 470 (power1.out) · 2.25 616.07 (linear)
- Connections Ball y: 1.15 712 · 1.75 712 (hold) · 1.975 564.36 (power2.out) · 2.25 624.36 (power2.in)
  · 2.33 624.36 (hold) · 2.45 612.36 (power2.out) · 2.57 624.36 (power2.in)
- Connections Ball Spin rotation: 1.15 −1080 · 2.25 0 (power1.out)
- Squash: 1.22/0.78 at 2.25 · 1.08/0.92 at 2.57 (power2.out down over 0.08s, back.out up over 0.24s)
- From 2.69 the ball is on its loop start pose: x 616.07, y 624.36, rotation 0, scale 1.

Connections lockup, same curves as Wordle's, later because the tiles finish later
- Connections Lockup y: 2.10 381 · 2.66 363 (expo.out) · 2.94 363 · 3.20 333 (power3.in)
- Connections Lockup scale: 2.10 0.96 · 2.66 1 · 2.94 1 · 3.20 0.97
- Connections Lockup opacity: 2.10 0 · 2.32 1 (linear) · 2.94 1 · 3.20 0 (power2.in)
- Connections Lockup Word: opacity 2.17 0 · 2.73 1; y 2.17 +10 · 2.73 0 (expo.out)

## Section 6 · Connections Loop

Create a looping linear animation named "Connections Loop", 6.2 seconds, loop on. First and last
frames equal the end of "Connections Intro": Connections Ball x 616.07, y 624.36, Spin 0, scale 1.
Only the Connections Ball and Left Slab Lilac are keyed.

- 0.00–0.60 rest
- Roll left to the slab's edge: x 0.60 616.07 · 1.60 552 (sine.inOut); Spin 0 → −207 (sine.inOut)
- Teeter: x 1.80 550 · 2.10 553 · 2.30 552; Spin 1.80 −217 · 2.10 −199 · 2.30 −207 (sine.inOut)
- Roll back: x 2.30 552 · 3.30 616.07; Spin −207 → 0 (sine.inOut)
- Two hops in place: y 3.30 624.36 · 3.38 624.36 (hold) · 3.58 598.36 (power2.out) · 3.78 624.36 (power2.in)
  · 3.86 624.36 (hold) · 4.06 610.36 (power2.out) · 4.26 624.36 (power2.in)
- Ball squash: 1.12/0.88 at 3.30 and 3.78 · 1.06/0.94 at 4.26
- Left Slab Lilac thumps as the ball lands: scaleY 0.95, scaleX 1.02 over 0.06s at 3.78 and at 4.26,
  back over 0.26s (back.out)
- 4.26–6.20 rest

Check that the loop point is seamless.

## Section 7 · State machine

Create a state machine named "Chapter 2" on the "Chapter 2" artboard, one layer.

Inputs: two Number inputs, "Game" and "Frame", both default 0.
(If this version of Rive wants data binding rather than state machine inputs, create a view model
named "Chapter 2" with two number properties, "game" and "frame", use them in the conditions below
instead, and tell me so I can update the engineering code.)

States and transitions:
- Entry → "Frame 1 Loop" (plays Frame 1 Loop)
- "Frame 1 Loop" → "Wordle Intro" when Frame == 2 AND Game == 1. Exit time off, duration 0.
- "Frame 1 Loop" → "Connections Intro" when Frame == 2 AND Game == 2. Exit time off, duration 0.
- "Wordle Intro" → "Wordle Loop" at exit time 100%, no conditions, duration 0.
- "Connections Intro" → "Connections Loop" at exit time 100%, no conditions, duration 0.

Leave room to add Strands (3), Spelling Bee (4), The Mini (5), The Midi (6) and The Crossword (7) later
the same way. Frames 3 to 5 need no states: the game loop keeps running while only the page text changes.

Then test it: set Game to 1, then Frame to 1, then 2 (for example with the preview's --data flag or the state machine test tools in rive docs). Confirm the Wordle Intro plays
and hands off to the Wordle Loop with no jump. Do the same with Game 2. Also tap through while the
shelf ball is mid-rock and confirm it holds its pose and leaves with the room.

## Section 8 · Final check

Do a final pass on the "Chapter 2" artboard and report back as a checklist:
- Every object that leaves the stage clears all four edges of the 1495 × 1067 artboard by its
  last key, and everything that enters starts fully outside it. List any that don't.
- Both intros are exactly 3.2s. The page text is timed to that.
- Each loop's first and last frame match its intro's last frame.
- No intro keys the Shelf Ball or Shelf Ball Spin.
- Names of the state machine and its inputs, exactly as engineering will type them.
- Exported .riv file size.

## Ease reference

| GSAP name | Rive cubic bezier | Used for |
|---|---|---|
| power2.inOut | 0.65, 0, 0.35, 1 | camera pan |
| power2.in | 0.32, 0, 0.67, 0 | falls, tips, hop descents |
| power2.out | 0.33, 1, 0.68, 1 | hop ascents, squash down, shadows |
| power1.out | 0.5, 1, 0.89, 1 | ball rolling in |
| power1.inOut | 0.45, 0, 0.55, 1 | wall color, ball spin on hops |
| sine.inOut | 0.37, 0, 0.63, 1 | loops: rocking, rolling, teetering |
| expo.out | 0.16, 1, 0.3, 1 | lockup rising in (matches the text's Rise in) |
| power3.in | 0.5, 0, 0.75, 0 | lockup lifting out (close to the text's Lift out) |
| back.out | 0.34, 1.56, 0.64, 1 | squash recovering, with a small overshoot |

