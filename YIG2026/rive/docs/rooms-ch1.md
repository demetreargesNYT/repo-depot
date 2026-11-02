# Rooms, in plain words

## To tune later

- **Card 1: the ball's story is this scene's loop** (762 frames, 12.7 s), and the only scene that follows the scene loop guideline so far. It starts the moment the intro ends: the ball slides out of the cuckoo clock's door along the blue perch, bounces on the chair and onto the window, the nine panes flip to tiles and back (the ball is knocked off), and it rolls off the right edge. Once it is out of sight it is removed (put back behind the clock door, also out of sight); 3 s later it slides out again, and the loop repeats. The ball never goes beyond x 1519, so it always leaves with its room. The small loops (their own "Chapter 1 Card 1 Small" layer, which starts when the pan ends) fit the loop with no jump: the minute hand turns twice (24 ticks), the pendulum swings 12 times, the dog's tail wags 3 times, the mouse runs once and waits in its hole, one set of clouds drifts across the whole window (hidden while the panes are tiles), the plant sways and drifts, and the dog's eye follows the mouse (it closes as the mouse approaches, stays closed while the mouse passes, opens once the mouse is past on its way home, and blinks while open). To tune: the shift per contact (the clock, shelf, chair, window, dog bed and floor each have their own), the pause (3.03 s), the eye's timing against the mouse, the dog's tail speed and the clouds' speed.

- **Card 1: the dog's eye.** It is asleep while the mouse is in front of it. If it still doesn't read as asleep, the next step is a bigger cue (the head dipping, or a small z).

- **Card 5: the ball moves between the tile tops while hidden.** Inside the loop the ball goes from one tile top to the next in a single frame (x 877 to 745 at frames 60 to 61, and 617 to 875 at frames 90 to 91) and the wrap now closes: the ball slides from x 875 back to 618 over frames 177 to 179, behind the letter tiles (global pass 3, 2026-11-02; it was a 257-unit jump at the wrap before). All three moves happen with the ball out of sight behind the tiles, so none shows. If the ball should visibly travel between the tops, that is a finesse call.

- **Card 1: pieces outside the safe area** (x 560 to 935, y 0 to 812; found in the global pass, nothing moved, a room-by-room call): the Mouse and its Mouse Hole Clip (x 958 to 984, y 697 to 711), the Mouse Hole (x 1069 to 1090, y 692 to 712) and the Outlet (x 930 to 944, y 681 to 703), all past the right line. They are the pieces the ball passes as it rolls off the right edge, which is part of its story.


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
the ball's shape keys and are not listed here.


## Start and Loading · scene `start`

**Loop:** 4.50 s (270 frames at 60/s), repeats. First and last frames are the same pose.

### Intro · exactly 3.2 s


### Ball · intro

- **Start Ball Squash**: squash on landing: 1.12 wide × 0.86 tall at 1.47 s (reached over 0.07 s, power2.out); back to 1 by 1.80 s (back.out)
- Highlight and shape ease into the landing pose, 0.00 s to 3.20 s.

### Ball · loop

- **Move 1**: 1.00 s to 1.33 s (0.33 s): 58 px up
- **Move 2**: 1.47 s to 1.80 s (0.33 s): 58 px down
- Waits: 1.33–1.47 s

## Chapter 1, card 1 · scene `chapter-1-card-1`

**Loop:** 12.70 s (762 frames at 60/s), repeats. First and last frames are the same pose.

### Intro · exactly 3.2 s

- **Floor and front slide in** (Chapter 1 Card 1 Floor Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)
- **Floor and front slide in** (Chapter 1 Card 1 Front Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)
- **Chapter 1 Card 1 Clock**: drops 800 px (y -281 → 519), starts 1.00 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **Chapter 1 Card 1 Clock**: squash on landing: 1.03 wide × 0.93 tall at 1.57 s (reached over 0.07 s, power2.out); back to 1 by 1.82 s (back.out)
- **Chapter 1 Card 1 Window**: drops 800 px (y -169 → 631), starts 1.13 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **Chapter 1 Card 1 Window**: squash on landing: 1.03 wide × 0.93 tall at 1.70 s (reached over 0.07 s, power2.out); back to 1 by 1.95 s (back.out)

### Ball · intro

- **Chapter 1 Card 1 Ball**: drops 800 px (y -357 → 443), starts 1.00 s, takes 0.50 s, power2.in (starts slow, speeds up)

### Ball · loop

- **Move 1**: 0.07 s to 1.87 s (1.80 s): 149 px right and 19 px down, rising 16 px above its start/finish height
- **Move 2**: 2.32 s to 4.50 s (2.18 s): 103 px left and 191 px down, rising 25 px above its start/finish height
- **Move 3**: 4.95 s to 9.67 s (4.72 s): 46 px left and 210 px up
- Waits: 1.87–2.32 s, 4.50–4.95 s

## Chapter 1, card 2 · scene `chapter-1-card-2`

**Loop:** 4.00 s (240 frames at 60/s), repeats. First and last frames are the same pose.

### Intro · exactly 3.2 s

- **Floor and front slide in** (Chapter 1 Card 2 Floor Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)
- **Floor and front slide in** (Chapter 1 Card 2 Front Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)
- **Chapter 1 Card 2 Stack**: drops 800 px (y -180 → 620), starts 1.00 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **Chapter 1 Card 2 Stack**: squash on landing: 1.03 wide × 0.93 tall at 1.57 s (reached over 0.07 s, power2.out); back to 1 by 1.82 s (back.out)
- **Chapter 1 Card 2 Top Piece**: drops 800 px (y -336 → 464), starts 1.13 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **Chapter 1 Card 2 Top Piece**: squash on landing: 1.03 wide × 0.93 tall at 1.70 s (reached over 0.07 s, power2.out); back to 1 by 1.95 s (back.out)

### Ball · intro

- **Chapter 1 Card 2 Ball**: moves right 762 px (x -80 → 682), starts 2.30 s, takes 0.75 s, power1.out (fast, then a soft stop)
- **Chapter 1 Card 2 Ball**: rises 258 px (y 756 → 498), starts 3.05 s, takes 0.15 s, power2.out (fast, then eases to a stop)

### Ball · loop

- **Move 1**: 0.03 s to 3.95 s (3.92 s): ends where it began

## Chapter 1, card 3 · scene `chapter-1-card-3`

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

- **Chapter 1 Card 3 Ball**: moves right 908 px (x -80 → 828), starts 2.30 s, takes 0.75 s, power1.out (fast, then a soft stop)
- **Chapter 1 Card 3 Ball**: rises 272 px (y 756 → 484), starts 3.05 s, takes 0.15 s, power2.out (fast, then eases to a stop)
- Highlight and shape ease into the landing pose, 2.30 s to 3.20 s.

### Ball · loop

- **Move 1**: 0.00 s to 0.23 s (0.23 s): 34 px up
- **Move 2**: 0.30 s to 3.00 s (2.70 s): 34 px down, rising 37 px above its start/finish height
- Waits: 0.23–0.30 s

## Chapter 1, card 4 · scene `chapter-1-card-4`

**Loop:** 3.00 s (180 frames at 60/s), repeats. First and last frames are the same pose.

### Intro · exactly 3.2 s

- **Floor and front slide in** (Chapter 1 Card 4 Floor Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)
- **Floor and front slide in** (Chapter 1 Card 4 Front Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)

### Ball · intro

- **Chapter 1 Card 4 Ball**: moves right 801 px (x -80 → 721), starts 2.30 s, takes 0.75 s, power1.out (fast, then a soft stop)
- **Chapter 1 Card 4 Ball**: rises 245 px (y 756 → 511), starts 3.05 s, takes 0.15 s, power2.out (fast, then eases to a stop)
- Highlight and shape ease into the landing pose, 2.30 s to 3.20 s.

### Ball · loop

- **Move 1**: 0.03 s to 0.37 s (0.33 s): 24 px up
- **Move 2**: 0.57 s to 1.45 s (0.88 s): 32 px up
- **Move 3**: 1.55 s to 2.37 s (0.82 s): 32 px down
- **Move 4**: 2.62 s to 2.98 s (0.37 s): 24 px down
- Waits: 0.37–0.57 s, 1.45–1.55 s, 2.37–2.62 s

## Chapter 1, card 5 · scene `chapter-1-card-5`

**Loop:** 3.00 s (180 frames at 60/s), repeats. First and last frames are the same pose.

### Intro · exactly 3.2 s

- **Floor and front slide in** (Chapter 1 Card 5 Floor Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)
- **Floor and front slide in** (Chapter 1 Card 5 Front Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)
- **Chapter 1 Card 5 Top Row**: drops 800 px (y -136 → 664), starts 1.00 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **Chapter 1 Card 5 Top Row**: squash on landing: 1.03 wide × 0.93 tall at 1.57 s (reached over 0.07 s, power2.out); back to 1 by 1.82 s (back.out)

### Ball · intro

- **Chapter 1 Card 5 Ball**: moves right 698 px (x -80 → 618), starts 2.30 s, takes 0.75 s, power1.out (fast, then a soft stop)
- **Chapter 1 Card 5 Ball**: rises 80 px (y 754 → 674), starts 3.05 s, takes 0.15 s, power2.out (fast, then eases to a stop)

### Ball · loop

- **Move 1**: 0.00 s to 2.98 s (2.98 s): ends where it began, rising 133 px above its start/finish height
