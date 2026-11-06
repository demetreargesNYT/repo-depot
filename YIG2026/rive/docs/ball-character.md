# The ball: character and beats

Read this before you touch the ball in any room. It adds a vocabulary to CLAUDE.md's rules and does not repeat them: the ball's role, rotation, stillness, squash limits and physics are in CLAUDE.md, "Motion rules" and "Scene loop guideline". Every number below was measured from the scene files on 2026-11-06 (60 frames a second; times are frames and seconds), unless it says *agreed*, which means it comes from the recent rounds and no room has it yet.

## Who the ball is

*(Draft; Demetre will rewrite this paragraph.)* The ball is the one character in every room. It is curious, quick and a little mischievous, and pleased with itself when something works. It looks before it acts: a glance, a lean, a test hop, then the move. It is never a prop: it is never parked, set down or carried like an object; when it is still, it has chosen to be. Where it is right: Chapter 1 card 4 (`tools/ch1_cards_234.py`, `card4`), Wordle (`chapters/ch2/scene.rml`, the room's own keys; `chapters/ch2/scripts/wordle.py` only adds the shadows) and the Start idle (`chapters/ch1/ch1_start_idle.py`). When in doubt, measure those: `python3 tools/ball_speed.py <ch> "<room>"` prints the ball's position and speed on every frame.

## The beats

| Beat | What it looks like | Frames (s) | The dot | Squash | Built with |
|---|---|---|---|---|---|
| **Glance** | The dot turns toward what interests it; the ball doesn't move. Then a hold with a 1 degree sway. | The Mini: 8 to 12 (0.13 to 0.2), to 6 to 19 degrees, eased in and out; hold 5 to 8 with a 1 degree sway every 14 to 16 frames. *Agreed:* 4 to 6. | Turns, eased | None | `mini.py` `Ball.glance_to`, `Ball.hold(sway=)` |
| **Peek** | The top of the ball rises over an edge, holds with a small drift of the dot, dips back a touch. | Chapter 3: up 5, hold 6 (0.1 s), dip 3.5 units over 4; The Mini (R's lid): a 24 frame rise, then looks about for 30. *Agreed:* hold 0.8 to 1.2 s. | Turned toward the edge, drifting | None | `ch3_loop_tracks.py` `peek_rows`; `mini.py` section 5 |
| **Prep hop** | One small hop in place before a jump, a diver testing the board. | Chapter 3: gather 3 (to 3%), hop 10 (5 units high), land 2 (3%, then 1%). | Still | 3% | `ch3_loop_tracks.py` `peek_rows`; `ball_motion.arc` |
| **Settle roll** | On landing, a short roll one way and back, then rest. | Wordle's rest-state rock after a roll: +2 units over 12, -3 over 18, +1 over 12 (0.7 s). The Mini: keeps 30% of its sideways speed and rolls to a stop over 16 (0.27 s). *Agreed:* a few degrees one way and back, about 0.4 s. | Turns with the roll (±10 degrees) | The landing's, 6% within 12 frames | `mini.py` `Ball.land`; `ball_motion.speed_profile` |
| **Idle** | The rest state: small eased rolls with pauses. | Start: a sway of ±5 units over 5 s (dot ±5.6 degrees), slowing to nearly still for 0.4 s at each end. Card 4 on the crossword head: +8 over 18, pause 8, -16 over 24, pause 10, +11 over 16, pause 14. | Turns with the roll | None | `ch1_start_idle.py`; card 4's `smooth_path(balA)` |
| **Count** | Small hops along a row, one per square. | The Mini on T's top: 15 to 18 in the air, 10 to 13 units high, gather 3% over 4. Card 4's streak: 34 frame hops with 5 frame stays. | Still in the air | 3% gather | `mini.py` `beat_hop` |
| **Lean** | A small roll and turn of the dot toward where it's about to go. | The Mini: 22 units over 24 with the dot at -8 degrees, a hold of 7, a look of -16 degrees over 8, then off. | Toward the way out | 3% gather before the roll | `mini.py` section 6 |
| **Startle** | A quick hop back when something moves nearby. | No room has it. *Agreed:* the dot snaps toward the thing in 3 to 4, a hop back of 6 to 8 units over 8 to 10, a 0.3 s hold, then a glance. | Snaps toward it | 3% on the landing | `ball_motion.arc` |
| **Ta-da** | A single bounce after a reveal. | No room has it now (the Mini's went with its 11-05 round). *Agreed:* one bounce, one 6% squash. | Up | One 6% | `ball_physics.simulate`, or `arc` and `pulse` |
| **The entry** | The ball comes out of an object in its room as the loop's first move; the loop's reset happens inside it. | The Mini: F1's lid opens (30), the ball gathers inside (5% over 6), jumps out (28 in the air). | Turns with the travel | 5% gather | `chapters/ch2/scripts/common.py` (`Cycle`, `emit`, `add_hole` for the slot it passes through) |

Also in the reference rooms: Wordle's **dribble** (a landing that bounces twice more, 24 then 12 units high, before it rolls off) and card 4's **balance** (rolls and pauses on a narrow top while the piece tilts under it, 0.06 radians per 8 units).

## Timing laws

- The ball is never motionless more than 0.6 s (36 frames) outside a declared rest.
- A rest always holds a settle roll or an idle.
- A beat of hesitation before every jump: a glance, a gather or a prep hop, not nothing.
- A beat after every landing before the next move (card 4: 5 frames at least; most rooms 8 to 16).
- Snappy hops are 0.35 to 0.45 s in the air (Wordle's are 0.43 and 0.5); the geometry decides when one must be longer (the Mini's hops between cubes are 0.47 to 0.97 s).
- Squash maximums: CLAUDE.md, "Squash and stretch stay subtle".

Where the reference rooms differ from these, as measured: Wordle stays fully still 2.35 s around its loop's seam; no room glances as fast as 4 to 6 frames or peeks as long as 0.8 s. Don't copy those parts; ask Demetre if a room seems to need them.

Beats are chosen to fit the moment, never listed in order. A loop that performs every beat is a routine, not a character.

## Don'ts (from the rounds that failed)

- Never parked: set down and left, as if put away.
- Never a hidden surface under the ball: it rests and rolls only on what is drawn and visible.
- The dot stays up at rest (Chapter 3's rule since 11-05): it turns with every roll and comes back up when the ball stops.
- Never a tumble about a horizontal axis (the Mini's tumbling roll, 11-05): the ball turns only as it rolls.
- Never fully still except for drama, and then short.
- Never more than about 2.5 s out of view.
- Not a dance: the Chapter 3 dance (11-05) was taken out; the ball moves for a reason in the room, not to music.

## Checks

`python3 tools/ball_speed.py <ch> "<room>" --contacts` (part of `npm run finesse`) already flags, per CLAUDE.md "The ball's physics": flights whose gravity isn't 0.40, bounces that keep less than 70% of their speed, launches faster than the arrival, turn-rounds off a near-flat surface, downhill rolls that slow (and uphill ones that speed up), and jitter (hitch, lurch, stall, buzz) on the ball and every moving piece. The flags Demetre accepted are in `tools/ball_speed_accepted.json`.

New (2026-11-06): **PARKED**, a stretch of more than 36 frames outside a declared rest where the ball moves less than 0.3 units, turns less than 0.5 degrees and its squash changes less than 0.005. Frames where the ball can't be seen (faded out, shrunk away or off the artboard) don't count, nor does the wait at the very start while its room arrives. A ball hidden by a clip inside an object can't be told from a visible one: declare that wait as a rest.

**Declaring a rest:** add a named range to `tools/ball_rests.json`: chapter, room, `from` and `to` in Finesse-panel seconds (the intro is 0 to 3.2; a rest across the loop's seam may end after the loop's end), why, and who approved it. It isn't a comment in `scene.rml`, because a `rive pull` rewrites that file and drops comments.

**It fails only for rooms changed after 2026-11-06.** A room fails on PARKED when its own pieces and timelines differ from its chapter's last commit of that day (ids aside); the rooms as they stood then keep reporting their stillness without failing (`PARKED_FAILS`, `PARKED_CUTOFF` in `tools/ball_speed.py`). Declared on 2026-11-06, the ball hidden inside an object or waiting under its room's arrival: Start (under the bird, 1.77 to 3.25 s), Chapter 1 card 1 (behind the clock's door), Spelling Bee (in the mug), The Crossword (in the hollow bar), The Mini (in F1, then in T, while R turns). Still reported, real stillness, for Demetre to rule on the next time each room is touched:

| Room | Visible stillness |
|---|---|
| Wordle | 0.77 s from 3.07 s, after the intro's landing; 2.35 s from 8.68 s, the end of the loop and across the seam |
| Chapter 1 card 5 | 0.70 s from 3.10 s and 0.82 s from 10.75 s on the floor before a try; 1.08 s from 7.93 s on the cube's top beside the bot |
| Community | 2.28 s from 2.13 s and 7.08 s from 5.35 s, the ball with the bird on top between hops |
| End | the whole 5 s loop, the ball in the pile |
