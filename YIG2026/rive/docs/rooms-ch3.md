# Rooms, in plain words

## To tune later

- **Chapter 3: the ball is a stand-in, not a full journey.** It rolls in during the intro and rests at x 748, y 729 (on the front floor between the cage and the blocks; it was x 1030, in front of the gift box, until the safe-area pass of 2026-11-02), hopping in place at 1 s and 3.5 s of the 5 s loop. A fuller journey is an option for finesse: the ball starting inside the picture frame, hopping out onto the ring box (the lid opens), bouncing in the crib, swinging past the mobile and the disco ball (it bursts) and landing on the front floor. The opening pose of that journey (the picture frame, the ring box) is already set on the art. Whether the room gets a journey or keeps a hop is a room-by-room call.

- **Chapter 3: the loop is the bird's.** The 5 s loop keys the bird (it closes; one eye-handle rotation ends a whole turn from its start, which is the same angle).

- **Chapters 3 and 4: the stand-in balls are inside the safe area now** (global pass 4, 2026-11-02; the safe area is x 560 to 935 and y 0 to 812). Chapter 3's ball rests at x 748 (it was x 1030); Chapter 4's at x 600 on the yellow Spelling Bee block (it was x 577, whose left edge reached x 559). Only the ball moved. If either room gets a journey, the path has to stay inside the same lines.

- **Chapter 4: the ball is a stand-in until its journey is decided** with card 1 and the video hand-off. A fuller journey would hop up the stack (Spelling Bee, Connections, the crosswords) and end leaping toward the viewer at 5.2 times its size. The stand-in rolls in, hops up onto the yellow Spelling Bee block (x 600, y 630) and hops in place there at 1 s and 3.5 s of the 5 s loop.

- **Chapter 4: The Mini and The Midi use The Crossword's fireworks on their own walls, and that is final** (2026-11-02). Their walls are 95BEFA and 7EAAF1, exactly their Chapter 2 colours.

- **Chapter 4: the fireworks seams are fine** (global pass 3, reviewed by Demetre in the Finesse panel, 2026-11-02: they look good). All five sets are in, behind one gate each (`topGame` picks the set). Measured at the loop restart, nothing pops: every set changes by under 100 pixels from the last frame to the first, against 1,500 to 2,900 mid-loop. Each set goes quiet for 0.1 to 0.3 s around the restart (Wordle 5 frames, Connections 11, Strands 7, Spelling Bee 17, and The Mini, The Midi and The Crossword, which share The Crossword's set, 19). Nothing to do.

- **Chapter 4: the stack rides in with the floor; nothing drops.** Every piece of the stack has a front and a back half drawn at different depths, so a drop would need the two halves timed together. Worth designing during finesse.

- **End has no ball of its own.** The room is full of red balls (the two piles and the big one the bird stands on), so there is no single ball to roll in. The pieces ride in with the floor.

- **Bird on Ball (`chapter-3-bird`): the bird on the ball is a stand-in.** The ball is twice its size and centred, rolls in to land as the intro ends, and the bird from the Chapter 3 room rides on top with its own loop running.

- **Chapter 3 card 1 (`chapter-3`): use the illustrator's animation for this room.** It isn't showing yet (Demetre, 2026-11-02). See also the journey-or-hop note above.

- **Chapter 3 card 2 (`chapter-3-bird`, bird on ball): the ball's stroke is too thick.** It should match the bird's stroke.

- **Chapter 3: pieces outside the safe area** (x 560 to 935, y 0 to 812; found in the global pass, nothing moved, a room-by-room call): Box (Floor Plane) (x 995-1075, y 683-711, right); Bird (Floor Plane) (x 900-945, y 505-547, right); Chapter 3 Picture 1 (Floor Plane) (x 558-655, y 505-582, left); Crib (Floor Plane) (x 780-982, y 546-712, right); Chapter 3 Picture 4 (Floor Plane) (x 558-655, y 505-582, left); Gifts (Floor Plane) (x 492-715, y 606-711, left). Pieces named `a` are unnamed groups.

- **Chapter 4: pieces outside the safe area** (x 560 to 935, y 0 to 812; found in the global pass, nothing moved, a room-by-room call): Cross_02 (Floor Plane) (x 912-989, y 661-712, right); SpB_01 (Floor Plane) (x 514-639, y 639-712, left); Crossword_F (Floor Plane) (x 551-653, y 435-647, left); Coss_F (Floor Plane) (x 427-1054, y 491-711, left, right); SpB_02_F (Floor Plane) (x 775-966, y 465-697, right); Crossword_B (Floor Plane) (x 551-653, y 435-647, left); Coss_B (Floor Plane) (x 427-1054, y 491-711, left, right); SpB_02_B (Floor Plane) (x 775-966, y 465-697, right). Pieces named `a` are unnamed groups.

- **End: pieces outside the safe area** (x 560 to 935, y 0 to 812; found in the global pass, nothing moved, a room-by-room call): a (Front Plane) (x 223-1275, y 451-712, left, right). Pieces named `a` are unnamed groups.


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
the ball's shape keys and are not listed here.


## Chapter 3, card 1 (the room) · scene `chapter-3`

**Loop:** 5.00 s (300 frames at 60/s), repeats. First and last frames are the same pose.

### Intro · exactly 3.2 s

- **Floor and front slide in** (Chapter 3 Floor Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)
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
- **Chapter 3 Disco Ball**: drops 800 px (y -258 → 542), starts 2.30 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **Chapter 3 Disco Ball**: squash on landing: 1.03 wide × 0.93 tall at 2.87 s (reached over 0.07 s, power2.out); back to 1 by 3.12 s (back.out)

### Ball · intro

- **Chapter 3 Ball**: moves right 828 px (x -80 → 748), starts 2.45 s, takes 0.75 s, power1.out (fast, then a soft stop)

### Ball · loop

- **Move 1**: 1.00 s to 1.20 s (0.20 s): 40 px up
- **Move 2**: 1.27 s to 1.47 s (0.20 s): 40 px down
- **Move 3**: 3.50 s to 3.70 s (0.20 s): 40 px up
- **Move 4**: 3.77 s to 3.97 s (0.20 s): 40 px down
- Waits: 1.20–1.27 s, 1.47–3.50 s, 3.70–3.77 s

## Chapter 4 (the shared stack) · scene `chapter-4`

**Loop:** 5.00 s (300 frames at 60/s), repeats. First and last frames are the same pose.

### Intro · exactly 3.2 s

- **Floor and front slide in** (Chapter 4 Floor Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)

### Ball · intro

- **Chapter 4 Ball**: moves right 680 px (x -80 → 600), starts 2.20 s, takes 0.75 s, power1.out (fast, then a soft stop)
- **Chapter 4 Ball**: rises 82 px (y 712 → 630), starts 2.95 s, takes 0.25 s, power2.out (fast, then eases to a stop)

### Ball · loop

- **Move 1**: 1.00 s to 1.20 s (0.20 s): 36 px up
- **Move 2**: 1.27 s to 1.47 s (0.20 s): 36 px down
- **Move 3**: 3.50 s to 3.70 s (0.20 s): 36 px up
- **Move 4**: 3.77 s to 3.97 s (0.20 s): 36 px down
- Waits: 1.20–1.27 s, 1.47–3.50 s, 3.70–3.77 s

## End · scene `end`

**Loop:** 5.00 s (300 frames at 60/s), repeats. First and last frames are the same pose.

### Intro · exactly 3.2 s

- **Floor and front slide in** (End Floor Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)
- **Floor and front slide in** (End Front Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)

### Ball · intro


### Ball · loop

- The ball stays put.

## Chapter 3, card 2 (the ball with the bird on top) · scene `chapter-3-bird`

**Loop:** 5.00 s (300 frames at 60/s), repeats. First and last frames are the same pose.

### Intro · exactly 3.2 s

- **Floor and front slide in** (Bird on Ball Floor Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)

### Ball · intro

- **Bird on Ball Ball**: moves right 828 px (x -80 → 748), starts 2.30 s, takes 0.90 s, power1.out (fast, then a soft stop)

### Ball · loop

- The ball stays put.
