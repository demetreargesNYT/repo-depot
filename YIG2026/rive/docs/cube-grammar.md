# Cubes: the grammar

Read this before you touch a cube in any room: The Mini, The Midi, The Crossword, Chapter 4's Crossword tower, and Chapter 1 card 5's cube. It sits beside CLAUDE.md's rules (line weight, loops, the ball's role and physics) and the crossword brief, `chapters/ch2/refs/crossword-family.md`, and doesn't repeat them. The numbers were measured on 2026-11-06 from `chapters/ch2/scripts/mini.py` (the current Mini, "the walkway") and the files it writes, unless they say *agreed*.

## The grid

- The cubes are the grid's squares. Each sits on the floor line or on another cube, and touches its neighbours along shared edges. No gap, no background, ever shows between two cubes. The Mini: cubes 84 square on one lattice, within 0.8 px of every Figma position.
- One viewpoint per room: every cube recedes the same way (the Mini: a back face sits 33.63 left and 39.21 up from its front face, for an 84 cube).
- The pattern comes from which faces are black, never from textures drawn on a face (every Mini face is one solid colour, `LIGHT` DFDBD7 or `DARK` 1F1F1F). `cube3d.Face(pattern=...)` still exists; don't use it.
- Line weight is 1.5 on every face at every scale: faces are plain paths whose corners are keyed, never scaled.

## Named moves

| Move | Mechanics and timing (the Mini) | Ease | Built with |
|---|---|---|---|
| **Quarter turn** | 90 degrees about the vertical axis, left to right unless said otherwise; 34 frames (0.57 s) to 3.5 degrees past, a 10 frame (0.17 s) settle; lands square on a face. Never a partial tip. The lowest bottom corner stays on the floor line at every angle (`cube3d.Cube.world` lifts the turning cube by the amount its nearest corner would dip, and the correction fades out within 6 degrees of a face, so it is exactly nothing at 0 and 90 degrees and the follow-through isn't a second swing). | Cubic in and out, then smooth | `Cube` pose `turn`; `mini.py` `turn_state`, `TURN_N`, `SETTLE_N`, `OVER` |
| **Lid open** | Hinged on the back edge. Lift 20 frames to 96 degrees (4 past open), settle 10: 0.5 s. No press-down: a lid gets its life from the lift's ease, the overshoot and the bump, and the cube never moves. | Smooth then ease-out (`lift_ease`) | pose `lid`; `joint_state` "open", `FULL` |
| **Lid close** | Falls under its own weight, 14 frames (accelerating), one soft bump of 1.5 degrees over 7: 0.35 s. | Gravity (t squared) | `joint_state` "shut" |
| **Half-open peek** | The lid lifts to 38 degrees (1.5 past) in 16, settles 8, drops back in 10 with a 1.2 degree bump over 6. | As the lid | `CRACK` |
| **Side flap** | A side face hinged on its bottom edge falls open until flat: 26 frames, accelerating, one 2.2 degree bump over 10; lifts shut in 20 with a 1.5 degree bump. | Gravity; lift ease to shut | part `flap`; `FLAP` |
| **Walkway** | Two or more open lids lying flat at cube-top height make a road (the Mini's T flap and F1's lid folded right over, 180 degrees: lift 34, settle 12). The ball rolls along it; it folds back at the reset. | As the lid | `FOLD` |
| **Face flip** | A face fades white to black or back: a short fade, never a pop. The wave: flips in sequence along a row or up a stack. *Agreed;* no current room has it (`midi.py` and `daily.py`, old concepts, used a wipe and a dip). | Eased fade | per-face opacity or fill keys |
| **Slide and lock** | A cube slides into a cell and seats. Old Midi: slide in 42 frames, a 1.2 px recoil over 10. | Quick start easing into the seat | pose `slide` |
| **Build** | A cube appears in place. Chapter 4's tower: rows from the base, a row 4 frames after the one below, each square 0 to 6 frames after its row's start, fading in over 6 while dropping 16 to 28 units with one small overshoot (back.out.small, 22 frames). Chapter 4's city: build over the intro (192 frames), then live. | back.out.small | `ch3_c4_build_tower.py`, `ch3_c4_city.add_building` |

## Laws

- Cubes never move, shake or shift, not a pixel, when a lid closes (or at any time, except in a turn, a slide or a build).
- Lids are closed during any turn.
- A turn never happens next to the ball unless the turn is the reveal.
- Every move lands square.
- The ball only ever rests on a drawn, visible surface.
- Moves don't overlap: one lid or one cube at a time, at least 0.3 s between one finishing and the next starting (Demetre's lid note, 11-04).
- The loop ends with every face, lid and cube as it began.

## Scale across the family

The Mini has the largest cubes and fewest (84), The Midi medium ones (its old squares are about 52), The Crossword the smallest and densest, and Chapter 4's tower uses the same grammar (12.5). Never rescale a room's cubes. With scale: more cubes, smaller moves, longer waves. Never with scale: the projection measured from each room's own art, the line weight, the laws.

## The engine

- **`chapters/ch2/scripts/cube3d.py`** models each cube in 3D and projects every corner onto the drawing every frame. `Cube(name, front, depth_px)` takes the front square at rest and how far the art puts the back face; a pose moves it (`turn`, `lid`, `lidl`, `flap`, `door`, `slide`; `tip`, `rot` and `dip` also exist and break the laws above). `Face` writes a face as a plain path with keyed corners; faces facing away are hidden on the frame they go edge-on.
- **The projection is measured from the art:** the front face is the true square and depth moves a point by (dx, dy) per unit, read off one cube's front and back edges in the room's own drawing (the Mini: 33.63, 39.21 per 84). `PERSPECTIVE` (default 0.06) adds a touch of central perspective, so near points are drawn slightly larger. At 0 it is the art exactly; the Mini uses 0. The still cubes are redrawn by the same code at the same setting, so still and moving cubes always agree.
- **The ball among cubes:** `mini.py` models the ball as a sphere in the grid's space and plans each hop (`plan_hop`) against the cubes' walls and lids, checking on every frame that it clears them, that every face over or under it is on the right side in depth, and that it is wholly covered whenever it is meant to be out of sight. (The 11-04 "speed solve" had its own flight planner, `mini_paths.py`; it was unused and was removed on 2026-11-06.)
- **Start from `mini.py`.** `midi.py` and `daily.py` are the old concepts (2D face tricks and dipping stacks) and are not the starting point: The Midi and The Crossword start from `mini.py`'s structure and this grammar.

## Stills before reports

Before reporting a cube room, look at stills from `python3 tools/rive_still.py <ch> <scene> <seconds ...>`: the grid at rest, mid-turn, and lids fully open. Then compare with the last commit, `python3 tools/compare_room.py <ch> <scene>`.
