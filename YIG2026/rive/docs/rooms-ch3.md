# Rooms, in plain words

## To tune later

- **Chapter 3 (c3s1): the illustrator's 7 s ball journey is not in.** In their file the ball starts inside the picture frame, hops out onto the ring box (the lid opens), bounces in the crib, swings past the mobile and the disco ball (it bursts), and lands on the front floor at x 1030, y 729. It plays once and does not loop. Our Chapter 3 has a stand-in ball instead: it rolls in during the intro and rests where the journey ends (x 1030, y 729, in front of the gift box), hopping in place at 1 s and 3.5 s of the 5 s loop. The opening pose of the journey (the picture frame, the ring box) is set on the art. Source: `Ball` in NYT_YIG_c3s1; config `tools/rooms/ch3-chapter-3.json`.

- **Chapter 3: the loop is the bird's.** The source's `Loop` (300 frames) keys only the bird and is set to play once; we play it as a loop (it closes; one eye-handle rotation ends a whole turn from its start, which is the same angle).

- **Chapters 3 and 4: the stand-in ball sits outside the phone's view.** The phone shows the centre 375 of the artboard (x 560 to 935). Chapter 3's ball rests at x 1030 (where the illustrator's journey ends), right of it; Chapter 4's rests at x 577 on the yellow Spelling Bee block, so with its 17.7 px radius it reaches past the left edge. Noted by Demetre on 2026-10-29; to fix during finesse, not now.

- **Chapter 4: the ball's journey is saved for when card 1 and the video hand-off are decided.** The illustrator's ball hops up the stack (Spelling Bee, Connections, the crosswords) and ends leaping toward the viewer at 5.2 times its size. Our stand-in ball rolls in, hops up onto the yellow Spelling Bee block (x 577, y 630, where the illustrator's ball first rests) and hops in place there at 1 s and 3.5 s of the 5 s loop.

- **Chapter 4: The Mini and The Midi are placeholders.** Their walls are 95BEFA and 7EAAF1 (their Chapter 2 colours) and they show The Crossword's fireworks until their own art arrives.

- **Chapter 4: the fireworks are the illustrator's, all five sets, behind one gate each (`topGame` picks the set), but three sets do not yet match the source at the end of the 5 s loop.** Compared frame by frame with the illustrator's ball journey and our stand-in ball taken out of both sides (`python3 tools/compare_room.py tools/rooms/ch3-chapter-4.json --chapter ch3 --compare <set>`, viewers in `deliver/compare/chapter-4-<set>/`): **Connections** differs on frames 258 to 299 (up to about 3,300 px; the rounded-rectangle burst at the lower left of the stack: its rings are spaced and turned slightly differently); **Spelling Bee** on frames 273 to 299 (up to about 2,700 px; the hexagon burst above the stack); **Wordle** on single frames 31, 93, 118 and 133 (a tile pane flips one frame late) and on 295 to 299. Strands and The Crossword match to within a few pixels. What is known about the cause: every key before frame 293 is the illustrator's, unchanged. The differences come from how the importer closes loops whose pieces do not end where they start. Many firework pieces have their last key exactly on frame 300, the wrap frame that is never shown; the old closing rule replaced that key's value, which reshaped the whole segment leading into it, so motion changed from that segment's start (frames 245 to 273). A fix keeps the last shown frame (299) exactly as the illustrator's keys give it and closes the loop only in the unseen step to 300; it handles linear, held and eased segments (an eased segment is split exactly at frame 299). It is in this build, but the comparison was not rerun after the eased-segment part, so how much of the Connections and Spelling Bee difference remains is not known. Segments with the illustrator's elastic curves (most of Wordle's set) still use the old rule, which is the likely cause of Wordle's 295 to 299. The one-frame-late pane flips are Solo switch keys: they jump instead of blending, so a sub-frame offset where the loop starts shows as one frame. Next step when tuning: rerun the three comparisons above; if a difference remains, compare the room's keys with the source including the wrap-frame keys.

- **Chapter 4: the stack rides in with the floor; nothing drops.** Every piece of the stack has a front and a back half drawn at different depths, so a drop would need the two halves timed together. Worth designing during finesse.

- **End (c5s1) has no ball of its own.** The room is full of red balls (the two piles and the big one the bird stands on), so there is no single ball to roll in. The pieces ride in with the floor.


Generated from `chapters/ch3/scene.rml` by `python3 tools/rooms_sheet.py ch3`. Do not edit by hand: change the room, then run the
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


## Chapter 3 (c3s1) · scene `chapter-3`

**Loop:** 5.00 s (300 frames at 60/s), repeats. First and last frames are the same pose.

### Intro · exactly 3.2 s

- **Floor and front slide in** (Chapter 3 Floor Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)
- **Chapter 3 Disco Ball**: drops 800 px (y -258 → 542), starts 1.00 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **Chapter 3 Disco Ball**: squash on landing: 1.03 wide × 0.93 tall at 1.57 s (reached over 0.07 s, power2.out); back to 1 by 1.82 s (back.out)
- **Chapter 3 Picture 1**: drops 800 px (y -219 → 581), starts 1.13 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **Chapter 3 Picture 1**: squash on landing: 1.03 wide × 0.93 tall at 1.70 s (reached over 0.07 s, power2.out); back to 1 by 1.95 s (back.out)
- **Chapter 3 Picture 2**: drops 800 px (y -219 → 581), starts 1.13 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **Chapter 3 Picture 2**: squash on landing: 1.03 wide × 0.93 tall at 1.70 s (reached over 0.07 s, power2.out); back to 1 by 1.95 s (back.out)
- **Chapter 3 Picture 3**: drops 800 px (y -219 → 581), starts 1.13 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **Chapter 3 Picture 3**: squash on landing: 1.03 wide × 0.93 tall at 1.70 s (reached over 0.07 s, power2.out); back to 1 by 1.95 s (back.out)
- **Chapter 3 Picture 4**: drops 800 px (y -219 → 581), starts 1.13 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **Chapter 3 Picture 4**: squash on landing: 1.03 wide × 0.93 tall at 1.70 s (reached over 0.07 s, power2.out); back to 1 by 1.95 s (back.out)
- **Chapter 3 Picture 5**: drops 800 px (y -219 → 581), starts 1.13 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **Chapter 3 Picture 5**: squash on landing: 1.03 wide × 0.93 tall at 1.70 s (reached over 0.07 s, power2.out); back to 1 by 1.95 s (back.out)
- **Chapter 3 Picture 6**: drops 800 px (y -219 → 581), starts 1.13 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **Chapter 3 Picture 6**: squash on landing: 1.03 wide × 0.93 tall at 1.70 s (reached over 0.07 s, power2.out); back to 1 by 1.95 s (back.out)
- **Chapter 3 Frames 1**: drops 800 px (y -189 → 611), starts 1.27 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **Chapter 3 Frames 1**: squash on landing: 1.03 wide × 0.93 tall at 1.83 s (reached over 0.07 s, power2.out); back to 1 by 2.08 s (back.out)
- **Chapter 3 Frames 2**: drops 800 px (y -189 → 611), starts 1.27 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **Chapter 3 Frames 2**: squash on landing: 1.03 wide × 0.93 tall at 1.83 s (reached over 0.07 s, power2.out); back to 1 by 2.08 s (back.out)
- **Chapter 3 Mobile**: drops 800 px (y -188 → 612), starts 1.27 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **Chapter 3 Mobile**: squash on landing: 1.03 wide × 0.93 tall at 1.83 s (reached over 0.07 s, power2.out); back to 1 by 2.08 s (back.out)

### Ball · intro

- **Chapter 3 Ball**: moves right 1110 px (x -80 → 1030), starts 1.15 s, takes 0.75 s, power1.out (fast, then a soft stop)

### Ball · loop

- **Move 1**: 1.00 s to 1.20 s (0.20 s): 40 px up
- **Move 2**: 1.27 s to 1.47 s (0.20 s): 40 px down
- **Move 3**: 3.50 s to 3.70 s (0.20 s): 40 px up
- **Move 4**: 3.77 s to 3.97 s (0.20 s): 40 px down
- Waits: 1.20–1.27 s, 1.47–3.50 s, 3.70–3.77 s

## Chapter 4 (c4s1, the shared stack) · scene `chapter-4`

**Loop:** 5.00 s (300 frames at 60/s), repeats. First and last frames are the same pose.

### Intro · exactly 3.2 s

- **Floor and front slide in** (Chapter 4 Floor Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)

### Ball · intro

- **Chapter 4 Ball**: moves right 657 px (x -80 → 577), starts 1.15 s, takes 0.75 s, power1.out (fast, then a soft stop)
- **Chapter 4 Ball**: rises 82 px (y 712 → 630), starts 1.90 s, takes 0.25 s, power2.out (fast, then eases to a stop)

### Ball · loop

- **Move 1**: 1.00 s to 1.20 s (0.20 s): 36 px up
- **Move 2**: 1.27 s to 1.47 s (0.20 s): 36 px down
- **Move 3**: 3.50 s to 3.70 s (0.20 s): 36 px up
- **Move 4**: 3.77 s to 3.97 s (0.20 s): 36 px down
- Waits: 1.20–1.27 s, 1.47–3.50 s, 3.70–3.77 s

## End (c5s1) · scene `end`

**Loop:** 5.00 s (300 frames at 60/s), repeats. First and last frames are the same pose.

### Intro · exactly 3.2 s

- **Floor and front slide in** (End Floor Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)
- **Floor and front slide in** (End Front Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)

### Ball · intro


### Ball · loop

- The ball stays put.
