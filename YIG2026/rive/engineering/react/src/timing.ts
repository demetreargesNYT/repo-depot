// Every number the guide gives for when copy may appear. They are fixed by the Rive files.

// A room's first visit with Next: its copy arrives this long after the scene is set (the 3.2 s intro is still finishing)
export const FIRST_VISIT_COPY_MS = 2000
// ...except a Chapter 2 game's first card with its lockup: the whole intro, so the copy never overlaps the lockup
export const LOCKUP_COPY_MS = 3200
export const PAN_MS = 1650 // a room change: the moves run 1.6 s, plus a few frames
// Chapter 4: the wall fades to the top game's colour (or back to the lighter blue) this long after `reveal` changes; the copy waits for it
export const REVEAL_FADE_MS = 1450
export const CLEAR_MS = 340 // the old copy dissolves within this long; the next copy inside the same room waits for it

// a copy block has finished rising this long after its delay (the 720 ms rise plus the stagger of a few lines)
export const RISE_SETTLED_MS = 1200
