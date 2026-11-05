# The crossword rooms: the cube world

Brief for Chapter 2's three crossword rooms: The Mini, The Midi and The Crossword (Demetre, 2026-11-04). The Mini is built first to test the 3D cube method; The Midi and The Crossword wait until he has approved it.

## Shared across all three

- **3D cube motion is the signature.** Hinged lids, cubes turning to show another face, cubes sliding and locking, faces flipping black to white. All of it is built with the 3D cube method (`chapters/ch2/scripts/cube3d.py`), never the old 2D squeeze.
- **Scale is the metaphor.** The Mini has the largest, fewest cubes, The Midi medium ones, The Crossword the smallest and densest, matching each puzzle's size. Never rescale a room's cubes.
- **Each cube is one square of the grid.** The crossword pattern comes from how the cubes are arranged (some light, some black, grouped into bars and stacks, as in the illustration), never from textures drawn on a cube's faces. The Midi's floor bar should read as a row of light and black squares, like the art's cells, rather than one big black block.
- **The cubes are the stars.** The ball is the thread through the world, for continuity, colour and surprise.
- **Design for the phone crop first** (375 × 812, artboard x 560 to 935). Every important beat happens inside it.
- **Loops of about 15 s.**

## The three rooms

- **The Mini, "the trick".** Fast, staccato sleight of hand. The ball is a magician's ball, hiding in boxes and bursting out of the one you didn't expect. Hinged lids, fake-outs, a "nothing up my sleeve" spin, a reveal.
- **The Midi, "the path".** Measured and mechanical. The ball rolls off the floating bar's end trusting the puzzle, and cubes slide in just in time to build steps under it. It rolls along the floor bar, whose top tiles flip black to white like a word being filled in, and a cube rises like a lift to carry it back up. The steps slide back and the tiles flip back while it rolls home. The floor bar reads as a row of light and black squares (its cubes, not a texture), so it isn't an ominous black box.
- **The Crossword, "the chain reaction".** Rippling and cascading; the cubes are the star. The ball stays fairly local, making a few small hops. Each landing sets off a ripple of black and white flips: one wave across the row (Across) and one up the stacks (Down), meeting at one shared square that flips last.

## The 3D cube method

- Each moving cube or lid is modelled in 3D, moved (rotated about a vertical axis, swung about a hinge edge, or slid), and every corner is projected back onto the drawing each frame.
- The projection is the room art's own angled projection, so a moving cube matches the still ones beside it, plus a light touch of perspective (near edges slightly taller than far ones), one tunable setting, starting gentle.
- A turning cube is honestly wider corner-on (about 40% at 45°). Let it widen; give it room.
- Hinged lids: the hinge edge stays fixed, each free corner travels its own arc, the lid becomes a slanted parallelogram as it opens, and the dark opening is revealed gradually behind it.
- Everything drawn on a face (squares, lines) is projected with the face and deforms with it.
- Faces facing away are hidden; faces facing the viewer draw in depth order.
- Line weight stays constant through every move.
