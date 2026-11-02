"""Tests for tools/rooms_sheet.py. Run: python3 -m unittest discover -s tools/tests"""
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import rooms_sheet as R


class FakeScene:
    def eases_of(self, c):
        return "ease"


def keys(xml):
    return R.Keys(FakeScene(), ET.fromstring(xml))


class KeyValues(unittest.TestCase):
    def test_linear_hold_and_value_curve(self):
        k = keys('<KeyedProperty property="x">'
                 '<KeyFrameDouble value="0" interpolationType="linear" frame="0"/>'
                 '<KeyFrameDouble value="100" interpolationType="hold" frame="10"/>'
                 '<KeyFrameDouble value="100" interpolationType="cubicValue" frame="20">'
                 '<CubicValueInterpolator x1="0" y1="100" x2="1" y2="40"/></KeyFrameDouble>'
                 '<KeyFrameDouble value="40" frame="30"/></KeyedProperty>')
        self.assertEqual(k.at(5), 50)
        self.assertEqual(k.at(15), 100)
        self.assertEqual(k.at(20), 100)         # a value curve starts at its own key's value...
        self.assertEqual(k.at(30), 40)          # ...and ends at the next key's
        self.assertTrue(40 < k.at(25) < 100)

    def test_ease_curve_is_symmetric_for_in_out(self):
        k = keys('<KeyedProperty property="y">'
                 '<KeyFrameDouble value="0" interpolationType="cubic" frame="0">'
                 '<CubicEaseInterpolator x1="0.65" y1="0" x2="0.35" y2="1"/></KeyFrameDouble>'
                 '<KeyFrameDouble value="10" frame="10"/></KeyedProperty>')
        self.assertAlmostEqual(k.at(5), 5, places=3)
        self.assertLess(k.at(2), 2)             # slow at the start


class Moves(unittest.TestCase):
    def test_a_hop_between_two_rests_is_one_move(self):
        # a loop is closed (it ends where it began), so the hop goes out and comes back to its rest: one move
        sheet = R.Sheet(None)
        pos = [(0, 0)] * 10 + [(i * 5, -abs(30 - i * 10)) for i in range(1, 7)] + [(30, 0)] * 10 + [(30 - i * 6, 0) for i in range(1, 6)] + [(0, 0)] * 4
        moves = sheet.moves(pos, 60)
        self.assertEqual(len(moves), 2)          # out, and back
        a, b, dx, dy, lift = moves[0]
        self.assertGreater(dx, 20)
        self.assertEqual(round(dy), 0)

    def test_a_move_into_the_wrap_ends_on_the_last_frame_of_the_loop(self):
        # the ball is still travelling on the last rendered frame and lands on frame 0 of the next pass: the move ends at n,
        # not one frame early (Strands showed 2.98 s for a 3.00 s loop)
        sheet = R.Sheet(None)
        n = 20
        pos = [(0, 0)] * 5 + [(i * 2, 0) for i in range(1, 11)] + [(20 - (i - 10) * 4, 0) for i in range(11, 16)]
        pos = pos[:n - 1] + [(2, 0)]
        moves = sheet.moves(pos, 60)
        self.assertEqual(moves[-1][1], n)


class Sheet(unittest.TestCase):
    def test_the_committed_sheet_matches_the_rooms(self):
        # the same rule `npm run check` enforces: rooms.md is regenerated whenever a room changes
        self.assertEqual(R.main(["ch2", "--check"]), 0)


if __name__ == "__main__":
    unittest.main()
