# Rooms, in plain words

## To tune later

- **Card 1 (c1s1): the illustrator's 7 s ball story is not in.** In their file the ball comes out of the cuckoo clock, bounces across the window (the panes flip to Wordle tiles as it passes), drops to the floor, squashes the chair cushion and runs into the mouse hole. It plays once and does not loop. Our card 1 has a stand-in ball instead: it rolls in during the intro, rests on the floor at x 1000 (between the dog and the mouse hole) and hops in place twice in the 10 s loop (at 2 s and 7 s). The panes and the clock show how the story opens. To fit the story in during finesse: the source animation is `Ball` in NYT_YIG_c1s1 (420 frames, 57 objects), and the importer config is `tools/rooms/ch1-card-1.json` (`start_pose_from` sets the opening pose).

- **Card 1: the dog's eye.** `Dog_Eye` plays once in the source and ends on a different shape. In the loop it plays at the start of the 10 s and returns to its first shape over frames 300 to 599 (a slow drift). Worth looking at.

- **Card 5 (c1s5): the ball's 257-unit jump is the illustrator's.** The ball jumps between the two tile tops inside the loop (x 877 to 745 at frames 60 to 61, and 617 to 875 at frames 90 to 91) and again where the loop wraps (875 to 618). We left it exactly as made, with no return. The loop therefore does not start and end on one pose for this one property; `chapters/ch1/chapter.json` lists it under `openLoops` so the check allows it.


Generated from `chapters/ch1/scene.rml` by `python3 tools/rooms_sheet.py ch1`. Do not edit by hand: change the room, then run the
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


## Loading (placeholder) · scene `loading`

**Loop:** 1.00 s (60 frames at 60/s), repeats. First and last frames are the same pose.

No intro of its own (the file opens on this room, already built).


### Ball · loop

- **Move 1**: 0.00 s to 0.27 s (0.27 s): 72 px up
- **Move 2**: 0.33 s to 0.60 s (0.27 s): 72 px down
- Waits: 0.27–0.33 s

## Start (c0) · scene `start`

**Loop:** 5.00 s (300 frames at 60/s), repeats. First and last frames are the same pose.

### Intro · exactly 3.2 s

- **Floor and front slide in** (Start Floor Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)

### Ball · intro

- **Start Ball**: moves right 703 px (x -80 → 623), starts 1.15 s, takes 0.75 s, power1.out (fast, then a soft stop)
- **Start Ball**: rises 44 px (y 756 → 712), starts 1.90 s, takes 0.15 s, power2.out (fast, then eases to a stop)
- Highlight and shape ease into the landing pose, 1.15 s to 2.05 s.

### Ball · loop

- **Move 1**: 0.02 s to 0.42 s (0.40 s): 39 px up
- **Move 2**: 0.60 s to 1.42 s (0.82 s): ends where it began
- **Move 3**: 1.60 s to 2.42 s (0.82 s): ends where it began
- **Move 4**: 2.60 s to 3.42 s (0.82 s): ends where it began
- **Move 5**: 3.60 s to 4.42 s (0.82 s): ends where it began
- **Move 6**: 4.60 s to 4.98 s (0.38 s): 39 px down
- Waits: 0.42–0.60 s, 1.42–1.60 s, 2.42–2.60 s, 3.42–3.60 s, 4.42–4.60 s

## Chapter 1, card 1 (c1s1) · scene `chapter-1-card-1`

**Loop:** 10.00 s (600 frames at 60/s), repeats. First and last frames are the same pose.

### Intro · exactly 3.2 s

- **Floor and front slide in** (Chapter 1 Card 1 Floor Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)
- **Floor and front slide in** (Chapter 1 Card 1 Front Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)
- **Chapter 1 Card 1 Clock**: drops 800 px (y -281 → 519), starts 1.00 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **Chapter 1 Card 1 Clock**: squash on landing: 1.03 wide × 0.93 tall at 1.57 s (reached over 0.07 s, power2.out); back to 1 by 1.82 s (back.out)
- **Chapter 1 Card 1 Window**: drops 800 px (y -169 → 631), starts 1.13 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **Chapter 1 Card 1 Window**: squash on landing: 1.03 wide × 0.93 tall at 1.70 s (reached over 0.07 s, power2.out); back to 1 by 1.95 s (back.out)

### Ball · intro

- **Chapter 1 Card 1 Ball**: moves right 1080 px (x -80 → 1000), starts 1.15 s, takes 0.75 s, power1.out (fast, then a soft stop)

### Ball · loop

- **Move 1**: 2.00 s to 2.20 s (0.20 s): 40 px up
- **Move 2**: 2.27 s to 2.47 s (0.20 s): 40 px down
- **Move 3**: 7.00 s to 7.20 s (0.20 s): 40 px up
- **Move 4**: 7.27 s to 7.47 s (0.20 s): 40 px down
- Waits: 2.20–2.27 s, 2.47–7.00 s, 7.20–7.27 s

## Chapter 1, card 2 (c1s2) · scene `chapter-1-card-2`

**Loop:** 4.00 s (240 frames at 60/s), repeats. First and last frames are the same pose.

### Intro · exactly 3.2 s

- **Floor and front slide in** (Chapter 1 Card 2 Floor Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)
- **Floor and front slide in** (Chapter 1 Card 2 Front Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)
- **Chapter 1 Card 2 Stack**: drops 800 px (y -180 → 620), starts 1.00 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **Chapter 1 Card 2 Stack**: squash on landing: 1.03 wide × 0.93 tall at 1.57 s (reached over 0.07 s, power2.out); back to 1 by 1.82 s (back.out)
- **Chapter 1 Card 2 Top Piece**: drops 800 px (y -336 → 464), starts 1.13 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **Chapter 1 Card 2 Top Piece**: squash on landing: 1.03 wide × 0.93 tall at 1.70 s (reached over 0.07 s, power2.out); back to 1 by 1.95 s (back.out)

### Ball · intro

- **Chapter 1 Card 2 Ball**: moves right 762 px (x -80 → 682), starts 1.15 s, takes 0.75 s, power1.out (fast, then a soft stop)
- **Chapter 1 Card 2 Ball**: rises 258 px (y 756 → 498), starts 1.90 s, takes 0.15 s, power2.out (fast, then eases to a stop)

### Ball · loop

- **Move 1**: 0.03 s to 3.98 s (3.95 s): ends where it began

## Chapter 1, card 3 (c1s3) · scene `chapter-1-card-3`

**Loop:** 3.00 s (180 frames at 60/s), repeats. First and last frames are the same pose.

### Intro · exactly 3.2 s

- **Floor and front slide in** (Chapter 1 Card 3 Floor Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)
- **Chapter 1 Card 3 Stick**: drops 800 px (y -124 → 676), starts 1.00 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **Chapter 1 Card 3 Stick**: squash on landing: 1.03 wide × 0.93 tall at 1.57 s (reached over 0.07 s, power2.out); back to 1 by 1.82 s (back.out)
- **Chapter 1 Card 3 First Card**: drops 800 px (y -145 → 655), starts 1.13 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **Chapter 1 Card 3 First Card**: squash on landing: 1.03 wide × 0.93 tall at 1.70 s (reached over 0.07 s, power2.out); back to 1 by 1.95 s (back.out)
- **Chapter 1 Card 3 Shelf**: drops 800 px (y -261 → 539), starts 1.27 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **Chapter 1 Card 3 Shelf**: squash on landing: 1.03 wide × 0.93 tall at 1.83 s (reached over 0.07 s, power2.out); back to 1 by 2.08 s (back.out)

### Ball · intro

- **Chapter 1 Card 3 Ball**: moves right 908 px (x -80 → 828), starts 1.15 s, takes 0.75 s, power1.out (fast, then a soft stop)
- **Chapter 1 Card 3 Ball**: rises 272 px (y 756 → 484), starts 1.90 s, takes 0.15 s, power2.out (fast, then eases to a stop)
- Highlight and shape ease into the landing pose, 1.15 s to 2.05 s.

### Ball · loop

- **Move 1**: 0.00 s to 0.23 s (0.23 s): 34 px up
- **Move 2**: 0.30 s to 2.98 s (2.68 s): 5 px left and 21 px down, rising 37 px above its start/finish height
- Waits: 0.23–0.30 s

## Chapter 1, card 4 (c1s4) · scene `chapter-1-card-4`

**Loop:** 3.00 s (180 frames at 60/s), repeats. First and last frames are the same pose.

### Intro · exactly 3.2 s

- **Floor and front slide in** (Chapter 1 Card 4 Floor Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)
- **Floor and front slide in** (Chapter 1 Card 4 Front Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)

### Ball · intro

- **Chapter 1 Card 4 Ball**: moves right 801 px (x -80 → 721), starts 1.15 s, takes 0.75 s, power1.out (fast, then a soft stop)
- **Chapter 1 Card 4 Ball**: rises 245 px (y 756 → 511), starts 1.90 s, takes 0.15 s, power2.out (fast, then eases to a stop)
- Highlight and shape ease into the landing pose, 1.15 s to 2.05 s.

### Ball · loop

- **Move 1**: 0.03 s to 0.37 s (0.33 s): 24 px up
- **Move 2**: 0.57 s to 1.45 s (0.88 s): 32 px up
- **Move 3**: 1.55 s to 2.37 s (0.82 s): 32 px down
- **Move 4**: 2.62 s to 2.98 s (0.37 s): 24 px down
- Waits: 0.37–0.57 s, 1.45–1.55 s, 2.37–2.62 s

## Chapter 1, card 5 (c1s5) · scene `chapter-1-card-5`

**Loop:** 3.00 s (180 frames at 60/s), repeats. First and last frames are the same pose.

### Intro · exactly 3.2 s

- **Floor and front slide in** (Chapter 1 Card 5 Floor Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)
- **Floor and front slide in** (Chapter 1 Card 5 Front Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)
- **Chapter 1 Card 5 Top Row**: drops 800 px (y -136 → 664), starts 1.00 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **Chapter 1 Card 5 Top Row**: squash on landing: 1.03 wide × 0.93 tall at 1.57 s (reached over 0.07 s, power2.out); back to 1 by 1.82 s (back.out)

### Ball · intro

- **Chapter 1 Card 5 Ball**: moves right 698 px (x -80 → 618), starts 1.15 s, takes 0.75 s, power1.out (fast, then a soft stop)
- **Chapter 1 Card 5 Ball**: rises 80 px (y 754 → 674), starts 1.90 s, takes 0.15 s, power2.out (fast, then eases to a stop)

### Ball · loop

- **Move 1**: 0.00 s to 2.98 s (2.98 s): 257 px right, rising 133 px above its start/finish height
