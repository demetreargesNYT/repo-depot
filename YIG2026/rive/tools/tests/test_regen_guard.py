"""Tests for tools/regen_guard.py on the real chapter files (nothing is written). Run: python3 -m unittest discover -s tools/tests"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import regen_guard as G

SCRIPT = Path(__file__)


def last_commit(ch):
    """The newest commit of a chapter's scene.rml, and whether the working file is that commit's (unchanged)."""
    rel = f"chapters/{ch}/scene.rml"
    sha = subprocess.run(["git", "log", "-1", "--format=%h", "--", rel], cwd=G.REPO, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "diff", "--quiet", "--", rel], cwd=G.REPO).returncode != 0
    return sha, dirty


class RegenGuard(unittest.TestCase):
    def setUp(self):
        G._checked.clear()

    def test_refuses_a_real_file_changed_since_the_commit(self):
        first = subprocess.run(["git", "log", "--reverse", "--format=%h", "--", "chapters/ch3/scene.rml"], cwd=G.REPO,
                               capture_output=True, text=True).stdout.split()[0]
        with self.assertRaises(SystemExit) as e:
            G.check(G.REPO / "chapters" / "ch3" / "scene.rml", first, SCRIPT)
        self.assertIn("REFUSED", str(e.exception))

    def test_allows_the_real_file_at_its_commit(self):
        for ch in ("ch1", "ch2", "ch3"):
            sha, dirty = last_commit(ch)
            if not dirty:
                G.check(G.REPO / "chapters" / ch / "scene.rml", sha, SCRIPT)       # no SystemExit
                return
        self.skipTest("every chapter has uncommitted changes")

    def test_never_refuses_a_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "scene.rml"
            p.write_text("<anything/>")
            G.check(p, "0000000", SCRIPT)                                       # not a chapter's real file: no check

    def test_a_commit_without_the_file_is_refused(self):
        with self.assertRaises(SystemExit):
            G.check(G.REPO / "chapters" / "ch3" / "scene.rml", "68f2e11", SCRIPT)


if __name__ == "__main__":
    unittest.main()
