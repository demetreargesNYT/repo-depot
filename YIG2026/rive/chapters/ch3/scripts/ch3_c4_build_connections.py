"""Chapter 4, card 1: the Connections building builds itself, then lives (Demetre, 2026-11-04).

    python3 chapters/ch3/scripts/ch3_c4_build_connections.py --write [--scene PATH]      once, on a scene without the layer

Bottom to top: blue bar (9:4223, its backer 9:4409), purple bar (9:4292, backer 9:4403), yellow-green bar (9:4134, backer 9:4397),
olive-green bar with its end cap (9:4351). The groups and backers are keyed directly (x and opacity); the Connections node is not.
BUILD: each colour group slides in from the side (blue and yellow-green from the left, purple and olive from the right), 28
frames from 66 units out, fading in over its first 6 frames, and locks with one 1.4 px overshoot; starts 96, 112, 128, 144;
the last lock is still at 180 (192 is the end of the build).
LOOP (HERO 2): frames 372 to 462: yellow-green row (with backer) 12 px left, purple row (with backer) 12 px right, hold 0.4 s,
back with one small bump. CALM: 6 px. No tile flips. Everything else flat.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ch3_c4_city import LOOP, BUILD, add_building, scene_path
from rml_edit import Doc

LAYER = "Chapter 4 City Connections"
# (group, backer or None, rest x of each, side it comes from (-1 left, +1 right), start frame)
BARS = [("9:4223", ("9:4409",), -1, 96), ("9:4292", ("9:4403",), +1, 112), ("9:4134", ("9:4397",), -1, 128), ("9:4351", (), +1, 144)]
REST = {"9:4223": 74.5, "9:4409": 52, "9:4292": 68.875, "9:4403": 70.75, "9:4134": 90.75, "9:4397": 98.25, "9:4351": 61.4855}
OUT, SLIDE_F, FADE_F, OVER = 66.0, 28, 6, 1.4
SLIDE = 12.0


def build_opacity(s):
    return [(0, 0, "hold"), (s, 0, "power1.out"), (s + FADE_F, 1, "hold"), (BUILD, 1, "hold")]


def track(rest, beats, end):
    keys = [(0, rest, "hold")] + [b for b in beats if 0 < b[0] < end]
    if keys[-1][0] != end:
        keys.append((end, rest, "hold"))
    return keys


def slide_beats(rest, amount, t0, hold):
    """x of a row: out, a tiny settle, hold, back with one bump (OVER px past rest) and then still."""
    out_end, back = t0 + 26, t0 + 26 + 6 + hold
    return [(t0, rest, "power2.inOut"), (out_end, rest + amount * 1.07, "sine.inOut"), (out_end + 6, rest + amount, "hold"),
            (back, rest + amount, "power2.inOut"), (back + 21, rest - OVER * (1 if amount > 0 else -1), "sine.inOut"),
            (back + 28, rest, "hold")]


def main():
    path = scene_path()
    assert LAYER not in path.read_text(), f"{LAYER} is already in {path}"
    doc = Doc(path)
    build, loop, calm = {}, {}, {}
    for gid, backers, side, s in BARS:
        for oid in (gid, *backers):
            # side -1: comes from the left, so it starts at rest - OUT and overshoots to rest + OVER
            r = REST[oid]
            build[(oid, "x")] = [(0, r - OUT if side < 0 else r + OUT, "hold"), (s, r - OUT if side < 0 else r + OUT, "power3.out"),
                                 (s + SLIDE_F, r + OVER if side < 0 else r - OVER, "sine.inOut"), (s + SLIDE_F + 8, r, "hold"), (BUILD, r, "hold")]
            build[(oid, "opacity")] = build_opacity(s)
    for label, group, amount, hold in (("loop", loop, SLIDE, 24), ("calm", calm, SLIDE / 2, 16)):
        for oid, sign, t0, h in (("9:4134", -1, 372, hold), ("9:4397", -1, 372, hold), ("9:4292", 1, 376, hold - 4), ("9:4403", 1, 376, hold - 4)):
            group[(oid, "x")] = track(REST[oid], slide_beats(REST[oid], sign * amount, t0, h), LOOP)
    add_building(doc, "Connections", {"build": build, "loop": loop, "calm": calm})
    doc.save()
    print(f"wrote {path}")


if __name__ == "__main__":
    if "--write" not in sys.argv:
        raise SystemExit(__doc__)
    main()
