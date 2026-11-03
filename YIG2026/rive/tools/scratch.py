"""The one place for scratch output: .cache/scratch.nosync/ (git-ignored, inside the repo so it is easy to find and to clear;
the .nosync ending keeps iCloud from syncing it, since the repo sits in the iCloud-synced Desktop).

Tools and tests put their throwaway copies, renders and screenshots here, never in /tmp or the repo root:

    from scratch import SCRATCH, mkdtemp, fresh
    work = mkdtemp("loop-motion-")     # a new folder each run; the caller removes it when done
    out = fresh("frames-ch1")          # a fixed folder, emptied first, for output you want to look at afterwards

Sessions run in parallel, so each has its own subfolder, .cache/scratch.nosync/<ch1|ch2|ch3|shared>/, and SCRATCH is the caller's:
YIG_SESSION if it is set to one of those, else the chapter the tool was run on (its first ch1, ch2 or ch3 argument), else shared.
Every helper here creates and deletes only inside that subfolder. ROOT is the top folder (the finesse notes live in ROOT/finesse-notes).
"""
import os
import re
import shutil
import sys
import time
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / ".cache" / "scratch.nosync"
SESSIONS = ("ch1", "ch2", "ch3", "shared")


def session(argv=None):
    if os.environ.get("YIG_SESSION") in SESSIONS:
        return os.environ["YIG_SESSION"]
    for a in (sys.argv[1:] if argv is None else argv):
        m = re.fullmatch(r"(?:.*/)?(ch[123])/?", a)
        if m:
            return m.group(1)
    return "shared"


SCRATCH = ROOT / session()


def mkdtemp(prefix="yig-"):
    """A new, empty folder in the caller's scratch subfolder (like tempfile.mkdtemp). The callers remove their folders when done,
    but a removal can leave a few empty folders behind; so this subfolder's folders with the same prefix older than an hour (no run
    of ours takes that long, so none is still in use) are cleared first."""
    SCRATCH.mkdir(parents=True, exist_ok=True)
    cutoff = time.time() - 3600
    for old in SCRATCH.glob(f"{prefix}*"):
        try:
            if old.is_dir() and old.stat().st_mtime < cutoff:
                shutil.rmtree(old, ignore_errors=True)
        except OSError:
            pass
    return Path(tempfile.mkdtemp(prefix=prefix, dir=SCRATCH))


def fresh(name):
    """<the caller's subfolder>/<name>, emptied, for output that stays until the next run of the same tool."""
    path = (SCRATCH / name).resolve()
    if SCRATCH.resolve() not in path.parents:
        raise ValueError(f"{name!r} is not a folder inside {SCRATCH}")
    shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True)
    return path
