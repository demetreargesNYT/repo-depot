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
        sheet = R.Sheet(None)
        pos = [(0, 0)] * 10 + [(i * 5, -abs(30 - i * 10)) for i in range(1, 7)] + [(30, 0)] * 10
        moves = sheet.moves(pos, 60)
        self.assertEqual(len(moves), 1)
        a, b, dx, dy, lift = moves[0]
        self.assertGreater(dx, 20)
        self.assertEqual(round(dy), 0)


class Sheet(unittest.TestCase):
    def test_the_committed_sheet_matches_the_rooms(self):
        # the same rule `npm run check` enforces: rooms.md is regenerated whenever a room changes
        self.assertEqual(R.main(["ch2", "--check"]), 0)


if __name__ == "__main__":
    unittest.main()
