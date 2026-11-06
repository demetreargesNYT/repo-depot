"""Tests for the jump profile and the motionless-ball check in tools/ball_speed.py. Run: python3 -m unittest discover -s tools/tests"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import ball_speed as B

# Wordle's jump, loop frames 221 to 250 (vertical steps, down positive), measured from chapters/ch2/scene.rml on 2026-11-06
WORDLE_JUMP = [-20.59, -17.53, -14.76, -12.28, -10.06, -8.07, -6.32, -4.78, -3.46, -2.35, -1.45, -0.76, -0.28, -0.04,
               0.01, 0.09, 0.24, 0.46, 0.74, 1.09, 1.51, 1.99, 2.54, 3.16, 3.85, 4.61, 5.45, 6.37, 7.39, 8.50]


class Jump(unittest.TestCase):
    def test_wordles_jump_follows_the_profile(self):
        self.assertTrue(B.follows_jump(WORDLE_JUMP))

    def test_a_scaled_jump_follows_it_too(self):
        self.assertTrue(B.follows_jump([x * 0.5 for x in WORDLE_JUMP]))

    def test_a_rise_onto_a_higher_surface_and_a_drop_from_a_float(self):
        rise = WORDLE_JUMP[:14] + [0.3, 0.7]
        self.assertTrue(B.follows_jump(rise))
        drop = [-1.7, -1.3, -1.0, -0.7, -0.4, -0.2] + [0.1, 0.2, 0.4, 0.5, 0.5, 0.6, 0.6, 1.0, 1.6, 2.6, 3.9, 5.5, 7.5, 9.8, 12.4, 15.3, 18.6, 22.2]
        self.assertTrue(B.follows_jump(drop))

    def test_a_hold_at_the_peak_is_part_of_the_float(self):
        held = WORDLE_JUMP[:14] + [0.0] * 60 + WORDLE_JUMP[14:]
        self.assertTrue(B.follows_jump(held))

    def test_a_strict_parabola_is_not_the_jump(self):
        self.assertFalse(B.follows_jump([-9 + 0.4 * k for k in range(46)]))          # 0.40 a frame squared: its ends are twice the mean, not three times
        self.assertFalse(B.follows_jump([-20 + 0.4 * k for k in range(100)]))
        self.assertFalse(B.follows_jump([0.4 * k for k in range(30)]))

    def test_a_rise_that_speeds_up_again_is_not_eased(self):
        bad = [-20, -10, -18, -9, -5, -1, -0.5, 0.5, 1, 3, 6]
        self.assertFalse(B.follows_jump(bad))


def track(n, **kw):
    """n frames of (x, y, turn, scaleX, scaleY, seen), still unless a function of the frame is given."""
    f = {"x": lambda i: 100.0, "y": lambda i: 200.0, "r": lambda i: 0.0, "s": lambda i: 1.0, **kw}
    return [(f["x"](i), f["y"](i), f["r"](i), f["s"](i), f["s"](i), True) for i in range(n)]


class Parked(unittest.TestCase):
    t_of = staticmethod(lambda i: 5.0 + i / 60.0)

    def report(self, tracks, rests=()):
        return B.parked_report(tracks, self.t_of, 100.0, 1000.0, list(rests))

    def test_a_still_ball_is_reported(self):
        self.assertEqual(len(self.report(track(80))), 1)

    def test_a_short_stillness_is_not(self):
        self.assertEqual(self.report(track(36)), [])

    def test_a_swaying_dot_and_a_pixel_of_drift_are_still_parked(self):
        import math
        swaying = track(120, r=lambda i: math.sin(i / 8.0), x=lambda i: 100.0 + 0.8 * math.sin(i / 20.0), s=lambda i: 1.7 * (1 - 0.012 * math.sin(i / 10.0) ** 2))
        self.assertEqual(len(self.report(swaying)), 1)

    def test_an_idle_roll_of_a_few_units_is_not(self):
        rolling = track(240, x=lambda i: 100.0 + 5.0 * (i % 60) / 60.0)
        self.assertEqual(self.report(rolling), [])

    def test_a_declared_rest_excuses_it(self):
        a, b = self.t_of(0), self.t_of(100)
        self.assertEqual(self.report(track(100), [(a, b, "in the box")]), [])

    def test_a_ball_that_cannot_be_seen_is_not_counted(self):
        unseen = [(x, y, r, sx, sy, False) for x, y, r, sx, sy, _ in track(100)]
        self.assertEqual(self.report(unseen), [])


if __name__ == "__main__":
    unittest.main()
