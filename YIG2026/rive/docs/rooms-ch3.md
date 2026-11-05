# Rooms, in plain words

## To tune later

- **Chapter 3: the illustrator's c3s1 animation is in, as drawn** (2026-11-03; `chapters/ch3/scripts/ch3_c3s1_import.py`, then Demetre's decisions, `ch3_c3s1_decisions.py`). It starts at 1.95 s behind the hill: the sun rises and sinks in the picture, leaps out onto the ring box (the lid opens, the ring rises), hops on the calendar, flies at 1.92 times its size to the mobile (it and the bird react), hits the disco ball (6.62 s), lands on the clock and drops into the cardboard box, where it rests hidden; the lid shuts and the ring lowers meanwhile. The standard ball with c3s1's motion, sizes and squash; the dot turns with the travel. Accepted as drawn: the box landing outside the phone frame and below the floor line (hidden in the box), and six physics flags (`tools/ball_speed_accepted.json`).

- **Chapter 3: the disco ball spins and sparkles** (2026-11-03): its facets slide a column every 0.43 s (a full turn about every 7 s), five small stars flash one or two at a time; its small swing and the contact sparkle answer the ball's hit at 6.62 s (both were made for a hit on its upper left: the swing starts to the right and the sparkle sits upper left; the hit is on its upper right). The Loop and the bird's blink loop are 416 frames.

- **Chapter 4: the city builds itself, the ball arrives to see it, card 2 celebrates** (2026-11-04, replaces the first living-city round; rebuild order: `ch3_c4_cleanup.py`, `ch3_c4_fireworks_fit.py`, `ch3_c4_cleanup2.py`, `ch3_c4_build_tower/hex/connections/dome/strands/cross.py` on the shared writer `ch3_c4_city.py`, then `ch3_c4_ball_stay.py`, all on the scene as committed in 0e325fa). Card 1 BUILD (the 192 frame Intro, one layer per building, "Chapter 4 City <Name>": Rest = nothing on the ground, Build, Loop, Calm): back to front, the tower stacks row by row from frame 69 (157 squares per copy), the hex column drops in bottom-up from frame 72 with each inner hex doing the coin spin as it lands (96, 126, 156), Connections slides its four colour groups in from alternating sides (96 to 180), the Coss towers assemble tile by tile like a sliding puzzle (cross tower 100 to 175; the far left column and the right L tower, outside the phone crop, from 40 and 50), the dome pops in cell by cell from the middle out (130 to 180), Strands pops its spheres then draws its sticks (130 to 184), Cross_02 steps up block by block (120 to 188). Back and startScene show the city built. Card 1 LOOP (600 frames, 10 s): two hero moments, never together: the hex column's cascade of inner hex coin spins (frames 150, 168, 186, 36 frames each, width |cos| to 0.07) and one Connections slide-and-lock (372 to 462, 12 px); Strands sways slightly all loop (3 cycles, at most 2.9 degrees); everything else is still. Calm (card 2): the spins narrow to 0.5, the slide is 6 px, the sway 1.2 degrees. The BALL (layer "Chapter 4 Ball Motion") is on card 1 now and never leaves: after the build (3.2 s) it bounces in from the left (flights 36, 25, 18, 12, 9 frames, 82 to 84 percent of the speed kept), rolls to a stop at x 755, rolls back to x 747 with its dot up and holds still 0.9 s, then idles on a faint eased roll (+-2.7 px, 600 frames). reveal true blends it into the top game's celebration idle (600 frames, phase aligned with the fireworks): a small excited hop on that gate's first big burst (Wordle 64, Connections 35, Strands 94, Spelling Bee 125, Crossword 26), small hops on the bigger bursts, rocks between, one showing-off hop of 20 units (8 percent landing squash, no puff). reveal false blends back to the card 1 idle (no roll-out); a reveal during the arrival lets it finish, hop once, and enter the celebration idle out of phase. Fireworks: moved down and together (k 0.58 to 0.78) so no piece rises above y 445 inside x 540 to 955, and scale-0 pieces got opacity keys (they drew dots). To tune: the tower has no loop motion yet (its 3D cube turns wait for Demetre's approval of the cube method being tested in Chapter 2's The Mini); most of the first two bounces land left of the phone crop; the Connections tile flip and its square-corner fix were dropped from the loop this round (commit 4a6adf4 has them); the Chapter 4 ball check (tools/ball_speed.py) reads only the Intro and Loop, so it does not see the ball layer.

- **Chapter 4: The Mini and The Midi use The Crossword's fireworks on their own walls, and that is final** (2026-11-02). Their walls are 95BEFA and 7EAAF1, exactly their Chapter 2 colours.

- **Chapter 4: the fireworks seams are fine** (global pass 3, reviewed by Demetre in the Finesse panel, 2026-11-02: they look good). All five sets are in, behind one gate each (`topGame` picks the set). Measured at the loop restart, nothing pops: every set changes by under 100 pixels from the last frame to the first, against 1,500 to 2,900 mid-loop. Each set goes quiet for 0.1 to 0.3 s around the restart (Wordle 5 frames, Connections 11, Strands 7, Spelling Bee 17, and The Mini, The Midi and The Crossword, which share The Crossword's set, 19). Nothing to do.

- **Chapter 4: the stack rides in with the floor; nothing drops.** Every piece of the stack has a front and a back half drawn at different depths, so a drop would need the two halves timed together. Worth designing during finesse.

- **End: one more ball joins the pile in the intro** (2026-11-03, `chapters/ch3/scripts/ch3_end_ball.py`). The standard ball at 0.9 times, End's red, rolls in from the room's left as the pan starts, its dot turning, meets the loose ball at the left pile's edge at 1.60 s and rests in front of the pile's edge at 1.67 s; the loose ball gives 4 and settles back 1, the edge ball gives a little, all still by 1.93 s. The loop leaves it in the pile.

- **Scene names are neutral, and four scenes share rooms** (2026-11-05, `chapters/ch3/scripts/ch3_scene_names.py`; a scene name describes position or data, never the illustration). ad stays ad (it was ad-3 for a few hours on 2026-11-05; `ch3_scene_ad.py` renamed it back, since every file's ad scene is just ad), chapter-3-bird is chapter-3-2; new: chapter-3-personal-badges and chapter-3-event-badges (they share ad's plain wall-and-floor picture; the same scene set again does nothing, so anon's two event-badge cards in a row are seamless), chapter-4-top-game and chapter-4-editor-video (they share chapter-4's room: the wall colour, the city and the ball carry straight through; chapter-4-editor-video fades the fireworks out over 0.4 s and keeps them off, chapter-4-top-game fades them back in over 0.25 s; the fireworks loop runs on underneath, so the ball's hops stay in step) and share (shares end's room, identical for now). `reveal` still drives the wall colour, the fireworks and the ball's celebration, as before. The enum keeps its value ids and is stored in flow order. Harness and docs still use the old names until the shared-files session updates them.

- **`chapter-3-bird` (now chapter-3-2) shows chapter-3's own room** (2026-11-05, `chapters/ch3/scripts/ch3_bird_shared_room.py`; the Bird on Ball room, its art, four layers and sixteen animations are gone, 27.5 KB smaller; Chapter 1 had already copied its loop into the Start card, commit 125b175). Chapter 3's four layers (Chapter 3, Exit, Draw, Small) answer chapter-3-bird as they answer chapter-3 (each transition that waits for scene == chapter-3 has a twin for the bird, each one that leaves on scene != chapter-3 also requires scene != chapter-3-bird), so chapter-3 to chapter-3-bird and back is a same-room change: the room keeps looping from where it is, no reset, no pan; arriving at the bird directly builds the room as chapter-3 would, and startScene shows it built. The Backdrop already used Chapter 3's colours for both. The manifest entry has kind shared-room and sameRoomAs chapter-3 and no room, which `tools/check_chapter.py` does not know yet (its Chapter 3 checks fail until the shared-files session teaches it).

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

`chapter-3-2` shares Chapter 3's room.

**Loop:** 6.93 s (416 frames at 60/s), repeats. First and last frames are the same pose.

### Intro · exactly 3.2 s

- **Floor and front slide in** (Chapter 3 Floor Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)

### Ball · intro

- **Chapter 3 Disco Ball**: drops 800 px (y -258 → 542), starts 1.40 s, takes 0.50 s, power2.in (starts slow, speeds up)
- **Chapter 3 Disco Ball**: squash on landing: 1.03 wide × 0.93 tall at 1.97 s (reached over 0.07 s, power2.out); back to 1 by 2.22 s (back.out)
- **Chapter 3 Ball**: moves left 0 px (x 596 → 596), starts 1.63 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: moves left 0 px (x 596 → 596), starts 1.65 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: moves left 0 px (x 596 → 596), starts 1.67 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: moves left 0 px (x 596 → 596), starts 1.68 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: moves right 0 px (x 596 → 596), starts 1.70 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: moves right 0 px (x 596 → 596), starts 1.72 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: moves right 0 px (x 596 → 596), starts 1.73 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: moves right 0 px (x 596 → 596), starts 1.75 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: moves right 0 px (x 596 → 596), starts 1.77 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: moves right 0 px (x 596 → 596), starts 1.78 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: moves right 0 px (x 596 → 596), starts 1.80 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: moves right 0 px (x 596 → 596), starts 1.82 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: moves right 0 px (x 596 → 596), starts 1.83 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: moves left 0 px (x 596 → 596), starts 1.85 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: moves left 0 px (x 596 → 596), starts 1.87 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: moves left 0 px (x 596 → 596), starts 1.88 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: moves left 0 px (x 596 → 596), starts 1.90 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: moves left 0 px (x 596 → 596), starts 1.92 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: moves left 0 px (x 596 → 596), starts 1.93 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: moves left 0 px (x 596 → 596), starts 1.95 s, takes 1.02 s, linear (constant speed)
- **Chapter 3 Ball**: moves left 0 px (x 596 → 596), starts 2.97 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: moves left 0 px (x 596 → 596), starts 2.98 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: moves left 0 px (x 596 → 596), starts 3.00 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: moves left 0 px (x 596 → 596), starts 3.02 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: moves left 0 px (x 596 → 596), starts 3.03 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: moves left 0 px (x 596 → 596), starts 3.05 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: moves left 0 px (x 596 → 596), starts 3.07 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: moves left 0 px (x 596 → 596), starts 3.08 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: moves left 0 px (x 596 → 596), starts 3.10 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: moves left 0 px (x 596 → 596), starts 3.12 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: moves left 0 px (x 596 → 596), starts 3.13 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: moves left 0 px (x 596 → 596), starts 3.15 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: moves left 0 px (x 596 → 596), starts 3.17 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 0 px (y -219 → -219), starts 1.13 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 0 px (y -219 → -219), starts 1.15 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 1 px (y -219 → -218), starts 1.17 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 1 px (y -218 → -217), starts 1.18 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 2 px (y -217 → -215), starts 1.20 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 3 px (y -215 → -212), starts 1.22 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 4 px (y -212 → -208), starts 1.23 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 5 px (y -208 → -203), starts 1.25 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 7 px (y -203 → -196), starts 1.27 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 8 px (y -196 → -188), starts 1.28 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 10 px (y -188 → -178), starts 1.30 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 12 px (y -178 → -166), starts 1.32 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 14 px (y -166 → -152), starts 1.33 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 16 px (y -152 → -136), starts 1.35 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 19 px (y -136 → -117), starts 1.37 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 21 px (y -117 → -95), starts 1.38 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 24 px (y -95 → -71), starts 1.40 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 27 px (y -71 → -44), starts 1.42 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 30 px (y -44 → -14), starts 1.43 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 34 px (y -14 → 20), starts 1.45 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 37 px (y 20 → 57), starts 1.47 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 41 px (y 57 → 97), starts 1.48 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 45 px (y 97 → 142), starts 1.50 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 49 px (y 142 → 191), starts 1.52 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 53 px (y 191 → 244), starts 1.53 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 57 px (y 244 → 301), starts 1.55 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 62 px (y 301 → 363), starts 1.57 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 67 px (y 363 → 431), starts 1.58 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 72 px (y 431 → 503), starts 1.60 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 78 px (y 503 → 581), starts 1.62 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 0 px (y 581 → 581), starts 1.63 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 0 px (y 581 → 581), starts 1.65 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 0 px (y 581 → 581), starts 1.67 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 0 px (y 581 → 581), starts 1.68 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 581 → 581), starts 1.70 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 581 → 581), starts 1.72 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 581 → 581), starts 1.73 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 581 → 581), starts 1.75 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 581 → 581), starts 1.77 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 581 → 581), starts 1.78 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 0 px (y 581 → 581), starts 1.80 s, takes 0.15 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 581 → 581), starts 1.95 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 581 → 581), starts 1.97 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 581 → 581), starts 1.98 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 581 → 581), starts 2.00 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 581 → 580), starts 2.02 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 580 → 580), starts 2.03 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 580 → 580), starts 2.05 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 1 px (y 580 → 579), starts 2.07 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 1 px (y 579 → 578), starts 2.08 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 1 px (y 578 → 577), starts 2.10 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 1 px (y 577 → 576), starts 2.12 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 2 px (y 576 → 575), starts 2.13 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 2 px (y 575 → 573), starts 2.15 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 2 px (y 573 → 570), starts 2.17 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 3 px (y 570 → 568), starts 2.18 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 2 px (y 568 → 565), starts 2.20 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 2 px (y 565 → 563), starts 2.22 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 2 px (y 563 → 561), starts 2.23 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 2 px (y 561 → 560), starts 2.25 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 1 px (y 560 → 558), starts 2.27 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 1 px (y 558 → 557), starts 2.28 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 1 px (y 557 → 556), starts 2.30 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 1 px (y 556 → 555), starts 2.32 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 1 px (y 555 → 554), starts 2.33 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 1 px (y 554 → 553), starts 2.35 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 1 px (y 553 → 553), starts 2.37 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 1 px (y 553 → 552), starts 2.38 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 1 px (y 552 → 552), starts 2.40 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 1 px (y 552 → 551), starts 2.42 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 551 → 550), starts 2.43 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 550 → 550), starts 2.45 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 550 → 550), starts 2.47 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 550 → 549), starts 2.48 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 549 → 549), starts 2.50 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 549 → 549), starts 2.52 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 549 → 548), starts 2.53 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 548 → 548), starts 2.55 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 548 → 548), starts 2.57 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 548 → 547), starts 2.58 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 547 → 547), starts 2.60 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 547 → 547), starts 2.62 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 547 → 547), starts 2.63 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 547 → 547), starts 2.65 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 547 → 547), starts 2.67 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 547 → 546), starts 2.68 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 546 → 546), starts 2.70 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 546 → 546), starts 2.72 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 546 → 546), starts 2.73 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 546 → 546), starts 2.75 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 546 → 546), starts 2.77 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 546 → 546), starts 2.78 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 546 → 546), starts 2.80 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 546 → 546), starts 2.82 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 546 → 546), starts 2.83 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 546 → 546), starts 2.85 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 546 → 546), starts 2.87 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 546 → 546), starts 2.88 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 546 → 546), starts 2.90 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 546 → 546), starts 2.92 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: rises 0 px (y 546 → 546), starts 2.93 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 0 px (y 546 → 546), starts 2.95 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 0 px (y 546 → 546), starts 2.97 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 0 px (y 546 → 546), starts 2.98 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 0 px (y 546 → 546), starts 3.00 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 0 px (y 546 → 546), starts 3.02 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 0 px (y 546 → 546), starts 3.03 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 0 px (y 546 → 547), starts 3.05 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 0 px (y 547 → 547), starts 3.07 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 0 px (y 547 → 547), starts 3.08 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 1 px (y 547 → 548), starts 3.10 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 1 px (y 548 → 549), starts 3.12 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 1 px (y 549 → 550), starts 3.13 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 1 px (y 550 → 550), starts 3.15 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball**: drops 1 px (y 550 → 552), starts 3.17 s, takes 0.02 s, linear (constant speed)
- **Ball_01**: squash on landing: 0.7121 wide × 0.6717 tall at 1.65 s (reached over 0.02 s, linear); 
- **Chapter 3 Ball Spin**: turns 0° → -0°, starts 0.00 s, takes 3.08 s, linear (constant speed)
- **Chapter 3 Ball Spin**: turns -0° → -0°, starts 3.08 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball Spin**: turns -0° → -0°, starts 3.10 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball Spin**: turns -0° → -0°, starts 3.12 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball Spin**: turns -0° → -1°, starts 3.13 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball Spin**: turns -1° → -1°, starts 3.15 s, takes 0.02 s, linear (constant speed)
- **Chapter 3 Ball Spin**: turns -1° → -1°, starts 3.17 s, takes 0.02 s, linear (constant speed)
- Highlight and shape ease into the landing pose, 0.00 s to 3.18 s.

### Ball · loop

- **Move 1**: 0.00 s to 1.70 s (1.70 s): 91 px right and 3 px up, rising 45 px above its start/finish height
- **Move 2**: 1.80 s to 4.42 s (2.62 s): 343 px right and 181 px down, rising 152 px above its start/finish height
- **Move 3**: 5.68 s to 5.70 s (0.02 s): 434 px left and 148 px up
- **Move 4**: 5.78 s to 6.33 s (0.55 s): 33 px up
- **Move 5**: 6.78 s to 6.93 s (0.15 s): 6 px down
- Waits: 1.70–1.80 s, 4.42–5.68 s, 5.70–5.78 s, 6.33–6.78 s

## Chapter 4 (the shared stack) · scene `chapter-4`

`chapter-4-top-game` shares Chapter 4's room.

`chapter-4-editor-video` shares Chapter 4's room.

**Loop:** 7.00 s (420 frames at 60/s), repeats. First and last frames are the same pose.

### Intro · exactly 3.2 s

- **Floor and front slide in** (Chapter 4 Floor Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)

### Ball · intro


### Ball · loop

- The ball stays put.

## End · scene `end`

`share` shares End's room.

**Loop:** 5.00 s (300 frames at 60/s), repeats. First and last frames are the same pose.

### Intro · exactly 3.2 s

- **Floor and front slide in** (End Floor Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)
- **Floor and front slide in** (End Front Plane): moves left 1600 px (x 1600 → 0), starts 0.05 s, takes 1.50 s, power2.inOut (slow, fast, slow)

### Ball · intro

- **End Ball**: moves right 9 px (x 167 → 176), starts 0.05 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 9 px (x 176 → 185), starts 0.07 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 9 px (x 185 → 193), starts 0.08 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 9 px (x 193 → 202), starts 0.10 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 9 px (x 202 → 211), starts 0.12 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 9 px (x 211 → 219), starts 0.13 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 8 px (x 219 → 228), starts 0.15 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 8 px (x 228 → 236), starts 0.17 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 8 px (x 236 → 244), starts 0.18 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 8 px (x 244 → 252), starts 0.20 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 8 px (x 252 → 261), starts 0.22 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 8 px (x 261 → 269), starts 0.23 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 8 px (x 269 → 277), starts 0.25 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 8 px (x 277 → 284), starts 0.27 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 8 px (x 284 → 292), starts 0.28 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 8 px (x 292 → 300), starts 0.30 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 8 px (x 300 → 307), starts 0.32 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 7 px (x 307 → 315), starts 0.33 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 7 px (x 315 → 322), starts 0.35 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 7 px (x 322 → 330), starts 0.37 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 7 px (x 330 → 337), starts 0.38 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 7 px (x 337 → 344), starts 0.40 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 7 px (x 344 → 351), starts 0.42 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 7 px (x 351 → 358), starts 0.43 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 7 px (x 358 → 365), starts 0.45 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 7 px (x 365 → 372), starts 0.47 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 7 px (x 372 → 378), starts 0.48 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 7 px (x 378 → 385), starts 0.50 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 7 px (x 385 → 392), starts 0.52 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 6 px (x 392 → 398), starts 0.53 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 6 px (x 398 → 404), starts 0.55 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 6 px (x 404 → 411), starts 0.57 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 6 px (x 411 → 417), starts 0.58 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 6 px (x 417 → 423), starts 0.60 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 6 px (x 423 → 429), starts 0.62 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 6 px (x 429 → 435), starts 0.63 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 6 px (x 435 → 441), starts 0.65 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 6 px (x 441 → 447), starts 0.67 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 6 px (x 447 → 452), starts 0.68 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 6 px (x 452 → 458), starts 0.70 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 6 px (x 458 → 463), starts 0.72 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 5 px (x 463 → 469), starts 0.73 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 5 px (x 469 → 474), starts 0.75 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 5 px (x 474 → 480), starts 0.77 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 5 px (x 480 → 485), starts 0.78 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 5 px (x 485 → 490), starts 0.80 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 5 px (x 490 → 495), starts 0.82 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 5 px (x 495 → 500), starts 0.83 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 5 px (x 500 → 505), starts 0.85 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 5 px (x 505 → 509), starts 0.87 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 5 px (x 509 → 514), starts 0.88 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 5 px (x 514 → 518), starts 0.90 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 4 px (x 518 → 523), starts 0.92 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 4 px (x 523 → 527), starts 0.93 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 4 px (x 527 → 532), starts 0.95 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 4 px (x 532 → 536), starts 0.97 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 4 px (x 536 → 540), starts 0.98 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 4 px (x 540 → 544), starts 1.00 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 4 px (x 544 → 548), starts 1.02 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 4 px (x 548 → 552), starts 1.03 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 4 px (x 552 → 556), starts 1.05 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 4 px (x 556 → 559), starts 1.07 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 4 px (x 559 → 563), starts 1.08 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 4 px (x 563 → 567), starts 1.10 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 3 px (x 567 → 570), starts 1.12 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 3 px (x 570 → 573), starts 1.13 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 3 px (x 573 → 577), starts 1.15 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 3 px (x 577 → 580), starts 1.17 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 3 px (x 580 → 583), starts 1.18 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 3 px (x 583 → 586), starts 1.20 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 3 px (x 586 → 589), starts 1.22 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 3 px (x 589 → 592), starts 1.23 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 3 px (x 592 → 595), starts 1.25 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 3 px (x 595 → 597), starts 1.27 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 3 px (x 597 → 600), starts 1.28 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 3 px (x 600 → 602), starts 1.30 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 2 px (x 602 → 605), starts 1.32 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 2 px (x 605 → 607), starts 1.33 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 2 px (x 607 → 609), starts 1.35 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 2 px (x 609 → 612), starts 1.37 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 2 px (x 612 → 614), starts 1.38 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 2 px (x 614 → 616), starts 1.40 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 2 px (x 616 → 617), starts 1.42 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 2 px (x 617 → 619), starts 1.43 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 2 px (x 619 → 621), starts 1.45 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 2 px (x 621 → 623), starts 1.47 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 2 px (x 623 → 624), starts 1.48 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 1 px (x 624 → 626), starts 1.50 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 1 px (x 626 → 627), starts 1.52 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 1 px (x 627 → 628), starts 1.53 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 1 px (x 628 → 630), starts 1.55 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 1 px (x 630 → 631), starts 1.57 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 1 px (x 631 → 632), starts 1.58 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 1 px (x 632 → 633), starts 1.60 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 1 px (x 633 → 633), starts 1.62 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 0 px (x 633 → 634), starts 1.63 s, takes 0.02 s, linear (constant speed)
- **End Ball**: moves right 0 px (x 634 → 634), starts 1.65 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 0° → 32°, starts 0.05 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 32° → 64°, starts 0.07 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 64° → 96°, starts 0.08 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 96° → 127°, starts 0.10 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 127° → 158°, starts 0.12 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 158° → 189°, starts 0.13 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 189° → 219°, starts 0.15 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 219° → 249°, starts 0.17 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 249° → 279°, starts 0.18 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 279° → 309°, starts 0.20 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 309° → 338°, starts 0.22 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 338° → 367°, starts 0.23 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 367° → 395°, starts 0.25 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 395° → 423°, starts 0.27 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 423° → 451°, starts 0.28 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 451° → 479°, starts 0.30 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 479° → 506°, starts 0.32 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 506° → 533°, starts 0.33 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 533° → 560°, starts 0.35 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 560° → 586°, starts 0.37 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 586° → 612°, starts 0.38 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 612° → 638°, starts 0.40 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 638° → 664°, starts 0.42 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 664° → 689°, starts 0.43 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 689° → 713°, starts 0.45 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 713° → 738°, starts 0.47 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 738° → 762°, starts 0.48 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 762° → 786°, starts 0.50 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 786° → 810°, starts 0.52 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 810° → 833°, starts 0.53 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 833° → 856°, starts 0.55 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 856° → 879°, starts 0.57 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 879° → 901°, starts 0.58 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 901° → 923°, starts 0.60 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 923° → 945°, starts 0.62 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 945° → 966°, starts 0.63 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 966° → 987°, starts 0.65 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 987° → 1008°, starts 0.67 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1008° → 1028°, starts 0.68 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1028° → 1049°, starts 0.70 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1049° → 1068°, starts 0.72 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1068° → 1088°, starts 0.73 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1088° → 1107°, starts 0.75 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1107° → 1126°, starts 0.77 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1126° → 1145°, starts 0.78 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1145° → 1163°, starts 0.80 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1163° → 1181°, starts 0.82 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1181° → 1199°, starts 0.83 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1199° → 1216°, starts 0.85 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1216° → 1233°, starts 0.87 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1233° → 1250°, starts 0.88 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1250° → 1267°, starts 0.90 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1267° → 1283°, starts 0.92 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1283° → 1299°, starts 0.93 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1299° → 1314°, starts 0.95 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1314° → 1329°, starts 0.97 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1329° → 1344°, starts 0.98 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1344° → 1359°, starts 1.00 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1359° → 1373°, starts 1.02 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1373° → 1387°, starts 1.03 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1387° → 1401°, starts 1.05 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1401° → 1414°, starts 1.07 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1414° → 1427°, starts 1.08 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1427° → 1440°, starts 1.10 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1440° → 1452°, starts 1.12 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1452° → 1464°, starts 1.13 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1464° → 1476°, starts 1.15 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1476° → 1488°, starts 1.17 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1488° → 1499°, starts 1.18 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1499° → 1510°, starts 1.20 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1510° → 1520°, starts 1.22 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1520° → 1531°, starts 1.23 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1531° → 1541°, starts 1.25 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1541° → 1550°, starts 1.27 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1550° → 1560°, starts 1.28 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1560° → 1569°, starts 1.30 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1569° → 1577°, starts 1.32 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1577° → 1586°, starts 1.33 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1586° → 1594°, starts 1.35 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1594° → 1602°, starts 1.37 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1602° → 1609°, starts 1.38 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1609° → 1616°, starts 1.40 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1616° → 1623°, starts 1.42 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1623° → 1630°, starts 1.43 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1630° → 1636°, starts 1.45 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1636° → 1642°, starts 1.47 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1642° → 1647°, starts 1.48 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1647° → 1653°, starts 1.50 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1653° → 1658°, starts 1.52 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1658° → 1662°, starts 1.53 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1662° → 1667°, starts 1.55 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1667° → 1671°, starts 1.57 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1671° → 1675°, starts 1.58 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1675° → 1678°, starts 1.60 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1678° → 1680°, starts 1.62 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1680° → 1681°, starts 1.63 s, takes 0.02 s, linear (constant speed)
- **End Ball Spin**: turns 1681° → 1682°, starts 1.65 s, takes 0.02 s, linear (constant speed)
- Highlight and shape ease into the landing pose, 0.00 s to 3.18 s.

### Ball · loop

- The ball stays put.
