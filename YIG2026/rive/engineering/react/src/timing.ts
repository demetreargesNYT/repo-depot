// Every number the guide gives for when copy may appear. They are fixed by the Rive files.

export const INTRO_MS = 3200 // a room's first visit with Next: every intro is exactly this long
export const PAN_MS = 1650 // a room change: the moves run 1.6 s, plus a few frames
export const CLEAR_MS = 340 // the old copy dissolves within this long; the next copy inside the same room waits for it

// A community card has no lockup, so its copy arrives when the room's pieces have landed
export const COMMUNITY_COPY_MS: Record<string, number> = {
  wordle: 2334,
  connections: 2367,
  strands: 1967,
  'spelling-bee': 2017,
  mini: 2084,
  midi: 1950,
  daily: 1950,
}

// a copy block has finished rising this long after its delay (the 720 ms rise plus the stagger of a few lines)
export const RISE_SETTLED_MS = 1200
