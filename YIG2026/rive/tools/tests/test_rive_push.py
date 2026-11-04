"""Tests for tools/rive_push.py, with a fake Rive CLI (nothing is pushed). Run: python3 -m unittest discover -s tools/tests"""
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import rive_push as P


class RivePush(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.lock = self.dir / "rive-push.lock"
        self.log = self.dir / "calls.txt"

    def tearDown(self):
        self.tmp.cleanup()

    def fake_rive(self, body):
        """A stand-in for the Rive CLI: records its arguments, checks the lock is held while it runs, then runs body."""
        path = self.dir / "rive"
        path.write_text(f'#!/bin/sh\necho "$@" >> "{self.log}"\n[ -f "{self.lock}" ] && echo "lock held during push" >> "{self.log}"\n{body}\n')
        path.chmod(0o755)
        return str(path)

    def test_push_runs_with_name_holds_lock_and_prints_revision(self):
        rive = self.fake_rive('echo "pushed 3 created, 2 updated"; echo "file 2692475 updated, revision 49500001"')
        code, message = P.push("ch1", "Chapter 1 checkpoint", rive=rive, lock=self.lock)
        self.assertEqual(code, 0)
        self.assertIn("revision 49500001", message)
        calls = self.log.read_text()
        self.assertIn("push", calls)
        self.assertIn("--yes", calls)
        self.assertIn("--name=Chapter 1 checkpoint", calls)
        self.assertIn("chapters/ch1", calls)
        self.assertIn("lock held during push", calls)
        self.assertFalse(self.lock.exists())

    def test_failed_push_still_releases_the_lock(self):
        code, message = P.push("ch2", "x", rive=self.fake_rive('echo "push aborted: build failed"; exit 1'), lock=self.lock)
        self.assertEqual(code, 1)
        self.assertIn("FAILED", message)
        self.assertFalse(self.lock.exists())

    def test_missing_cli_still_releases_the_lock(self):
        code, _ = P.push("ch2", "x", rive=str(self.dir / "no-such-rive"), lock=self.lock)
        self.assertEqual(code, 1)
        self.assertFalse(self.lock.exists())

    def test_up_to_date_has_no_revision(self):
        code, message = P.push("ch3", "x", rive=self.fake_rive('echo "already up to date"'), lock=self.lock)
        self.assertEqual(code, 0)
        self.assertIn("already up to date", message)

    def test_refuses_when_another_session_holds_the_lock(self):
        P.take_lock(self.lock, "ch3", "Chapter 3 checkpoint")
        before = self.lock.read_text()
        code, message = P.push("ch1", "x", rive=self.fake_rive("echo should not run"), lock=self.lock)
        self.assertEqual(code, 2)
        self.assertIn("ch3", message)
        self.assertIn("Chapter 3 checkpoint", message)
        self.assertFalse(self.log.exists())                 # the CLI never ran
        self.assertEqual(self.lock.read_text(), before)     # the other session's lock is untouched

    def test_take_lock_is_exclusive(self):
        P.take_lock(self.lock, "ch1", "a")
        with self.assertRaises(P.LockHeld):
            P.take_lock(self.lock, "ch2", "b")

    def test_release_removes_only_its_own_lock(self):
        mine = P.take_lock(self.lock, "ch1", "a")
        self.assertFalse(P.release_lock(self.lock, "someone-else"))
        self.assertTrue(self.lock.exists())
        self.assertTrue(P.release_lock(self.lock, mine))
        self.assertFalse(self.lock.exists())

    def test_old_lock_is_reported_stale_and_kept(self):
        self.lock.write_text(json.dumps({"chapter": "ch2", "name": "old", "time": "earlier", "since": time.time() - 20 * 60}))
        code, message = P.push("ch1", "x", rive=self.fake_rive("echo should not run"), lock=self.lock)
        self.assertEqual(code, 2)
        self.assertIn("stale", message)
        self.assertTrue(self.lock.exists())

    def test_hand_made_lock_is_respected(self):
        self.lock.write_text("ch2 2026-11-04 13:00\n")      # the old by-hand format
        os.utime(self.lock)
        code, message = P.push("ch1", "x", rive=self.fake_rive("echo should not run"), lock=self.lock)
        self.assertEqual(code, 2)
        self.assertIn("ch2 2026-11-04 13:00", message)
        self.assertNotIn("stale", message)


if __name__ == "__main__":
    unittest.main()
