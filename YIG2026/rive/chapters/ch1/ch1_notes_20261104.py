"""One time (2026-11-04): Demetre's pinned notes on Start and Chapter 1 cards 2 and 3 (.cache/scratch.nosync/finesse-notes/ch1.md).

    python3 chapters/ch1/ch1_notes_20261104.py            dry run: prints what would change
    python3 chapters/ch1/ch1_notes_20261104.py --write    rewrite chapters/ch1/scene.rml

It checks each room is as it was before (Start's loop 270 frames, card 3's hop-out rock in place, card 2's stop at x 577.95) and
refuses otherwise, so it can't run twice.

  * Card 2, the stop on the floor (sent 07:38, note 1): the ball brakes. Rolling left it runs a hair past its stop (to x 577.95, where
    it used to stop), rolls back 2.5 px (its turn follows: it over-rotates a little, then turns back), waits, and carries on right,
    joining its old path at loop frame 95. Its stop moves 2.5 px right so the overshoot stays inside the phone frame.
  * Card 3, the mug (sent 07:45, note 1): the mug keeps its wobble when the ball lands in it (loop frames 94 to 120) and no longer
    rocks when the ball hops out (it rocked on intro frames 101 to 136 and loop frames 128 to 163).
  * Start, the bounce (sent 07:45, note 2): one flight at the one gravity (0.40), 32 frames and 51 px high, where it was 47 frames
    and 58 px (falling at 0.28). The bird's hop, the squashes and the bird's blinks go with it in time, and the rest after the landing
    is 3 s longer: the loop goes from 270 frames to 435, and the Small Loop with it.
"""
import math
import sys
from pathlib import Path

RIVE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RIVE_ROOT / "tools"))

from ball_motion import smooth                  # noqa: E402
from rml_edit import Doc, bake                  # noqa: E402
from rml_read import Scene                      # noqa: E402
from rooms_sheet import Sheet                   # noqa: E402

SCENE = RIVE_ROOT / "chapters" / "ch1" / "scene.rml"


def ids_by_name(s):
    return {e.get("name"): e.get("id") for e in s.root.iter() if e.get("name") and e.get("id")}


def hermite(u, p0, p1, m0, m1):
    h00, h10, h01, h11 = 2 * u ** 3 - 3 * u ** 2 + 1, u ** 3 - 2 * u ** 2 + u, -2 * u ** 3 + 3 * u ** 2, u ** 3 - u ** 2
    return h00 * p0 + h10 * m0 + h01 * p1 + h11 * m1


# ---- card 2 -----------------------------------------------------------------------------------------------------------------------------
def card2(s, sh, doc, names, write):
    room = "Chapter 1 Card 2"
    loop = s.animations[f"{room} Loop"]
    n = s.duration(loop)
    keys = sh.anim_keys(loop)
    bx = keys[names[f"{room} Ball"]]["x"]
    spin_id = names[f"{room} Ball Spin"]
    th = keys[spin_id]["rotation"]
    x = {f: bx.at(f) for f in range(n)}
    t = {f: th.at(f) for f in range(n)}
    assert abs(x[60] - 577.95) < 0.05 and abs(x[70] - 577.95) < 0.05, "card 2's stop is not where it was"
    r = (x[50] - x[60]) / (t[50] - t[60])                 # its rolling radius, from the old roll
    F0, F_STOP, F_BACK, F_GO, F1 = 50, 62, 70, 80, 95
    STOP, REST = 577.95, 580.45
    v0 = (x[51] - x[49]) / 2
    v1 = (x[F1 + 1] - x[F1 - 1]) / 2
    new = dict(x)
    for f in range(F0, F1 + 1):
        if f <= F_STOP:
            u = (f - F0) / (F_STOP - F0)
            new[f] = hermite(u, x[F0], STOP, v0 * (F_STOP - F0), 0.0)
        elif f <= F_BACK:
            new[f] = STOP + (REST - STOP) * smooth((f - F_STOP) / (F_BACK - F_STOP))
        elif f <= F_GO:
            new[f] = REST
        else:
            u = (f - F_GO) / (F1 - F_GO)
            new[f] = hermite(u, REST, x[F1], 0.0, v1 * (F1 - F_GO))
    new_t = dict(t)
    for f in range(F0, F1 + 1):
        new_t[f] = t[F0] + (new[f] - x[F0]) / r
    gap = t[F1] - new_t[F1]
    assert abs(gap) < 0.02, (new_t[F1], t[F1])
    for f in range(F_GO, F1 + 1):                         # the turn left over at the join (under a hundredth of a turn) goes into the last roll
        new_t[f] += gap * smooth((f - F_GO) / (F1 - F_GO))
    left_edge = min(new.values()) - 17.7
    print(f"{room}: brakes at loop frames {F0} to {F_STOP} (timecode {3.2 + F0 / 60:.2f} to {3.2 + F_STOP / 60:.2f} s) to x {STOP}, "
          f"rolls back to x {REST} by {3.2 + F_BACK / 60:.2f} s, waits, goes on at {3.2 + F_GO / 60:.2f} s and joins its old path at "
          f"{3.2 + F1 / 60:.2f} s; rolling radius {r:.2f}; its left edge at x {left_edge:.1f}")
    if write:
        doc.set_prop(f"{room} Loop", names[f"{room} Ball"], "x", bake(new, range(n)))
        doc.set_prop(f"{room} Loop", spin_id, "rotation", bake(new_t, range(n)))
        # the turn must close the loop on a whole number of turns: check
        turns = (new_t[n - 1] - new_t[0]) / (2 * math.pi)
        print(f"  {room}: the loop's turn {turns:.4f} turns (was {(t[n - 1] - t[0]) / (2 * math.pi):.4f})")


# ---- card 3 -----------------------------------------------------------------------------------------------------------------------------
def card3(s, sh, doc, names, write):
    room = "Chapter 1 Card 3"
    mug = names[f"{room} Mug"]
    loop, intro = s.animations[f"{room} Loop"], s.animations[f"{room} Intro"]
    n = s.duration(loop)
    r = sh.anim_keys(loop)[mug]["rotation"]
    ri = sh.anim_keys(intro)[mug]["rotation"]
    assert abs(r.at(130) - 0.05) < 0.002 and max(abs(ri.at(f)) for f in range(101, 137)) > 0.01, "card 3's hop-out rock is not where it was"
    vals = {f: (r.at(f) if f <= 120 else 0.0) for f in range(n)}
    print(f"{room}: the mug keeps its catch wobble (loop frames 94 to 120, timecode {3.2 + 94 / 60:.2f} to {3.2 + 120 / 60:.2f} s) and "
          f"stops rocking for the hop out (intro 1.68 to 2.27 s, loop {3.2 + 128 / 60:.2f} to {3.2 + 163 / 60:.2f} s)")
    if write:
        doc.set_prop(f"{room} Loop", mug, "rotation", bake(vals, range(n)))
        doc.set_prop(f"{room} Intro", mug, "rotation", [(0, ri.at(0), "hold"), (191, ri.at(0), "hold")])


# ---- Start ------------------------------------------------------------------------------------------------------------------------------
UP, OLD_LAND, NEW_N = 61, 108, 32                      # the take-off frame, the old landing, the new flight's frames
EXTRA = 180                                            # 3 s more rest after the landing
OLD_END = 270


def start(s, sh, doc, names, write):
    loop = s.animations["Start Loop"]
    small = s.animations["Start Small Loop"]
    assert s.duration(loop) == OLD_END and s.duration(small) == OLD_END, "Start's loop is not 270 frames: already changed?"
    shift = (OLD_LAND - UP) - NEW_N                    # 15 frames saved by the quicker flight
    new_end = OLD_END - shift + EXTRA

    def g(f):
        """The old frame shown at new frame f."""
        if f <= UP:
            return f
        if f <= UP + NEW_N:
            return UP + (f - UP) * (OLD_LAND - UP) / NEW_N
        if f <= OLD_END - shift:
            return f + shift
        return OLD_END

    ball = names["Start Ball"]
    v0 = 0.2 * NEW_N                                   # rise speed for a flight of NEW_N frames at 0.40
    h = 0.2 * (NEW_N / 2) ** 2
    floor = sh.anim_keys(loop)[ball]["y"].at(0)
    print(f"Start: the bounce takes {NEW_N} frames ({NEW_N / 60:.2f} s) and rises {h:.1f} px (was {OLD_LAND - UP} frames and "
          f"{floor - min(sh.anim_keys(loop)[ball]['y'].at(f) for f in range(UP, OLD_LAND)):.1f} px); it lands at loop frame {UP + NEW_N} "
          f"(timecode of a loop pass + {(UP + NEW_N) / 60:.2f} s); the loop {OLD_END} -> {new_end} frames ({new_end / 60:.2f} s), "
          f"the rest between bounces {(OLD_END - OLD_LAND + 48) / 60:.2f} -> {(new_end - (UP + NEW_N) + 48) / 60:.2f} s")
    if not write:
        return
    for anim in (loop, small):
        name = anim.get("name")
        for oid, props in sh.anim_keys(anim).items():
            for prop, k in props.items():
                vals = {f: k.at(g(f)) for f in range(new_end + 1)}
                if anim is loop and oid == ball and prop == "y":
                    for f in range(UP, UP + NEW_N + 1):
                        u = f - UP
                        vals[f] = floor - (v0 * u - 0.2 * u * u)
                doc.set_prop(name, oid, prop, bake(vals, range(new_end + 1)))
        doc.set_duration(name, new_end)


def main(argv):
    write = "--write" in argv
    s = Scene(SCENE)
    sh = Sheet(s)
    names = ids_by_name(s)
    doc = Doc(SCENE)
    card2(s, sh, doc, names, write)
    card3(s, sh, doc, names, write)
    start(s, sh, doc, names, write)
    if write:
        doc.save()
        print("wrote", SCENE)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
