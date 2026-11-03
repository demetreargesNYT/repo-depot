"""The one place for scratch output: .cache/scratch/ (git-ignored, inside the repo so it is easy to find and to clear).

Tools and tests put their throwaway copies, renders and screenshots here, never in /tmp or the repo root:

    from scratch import SCRATCH, mkdtemp, fresh
    work = mkdtemp("loop-motion-")     # a new folder each run; the caller removes it when done
    out = fresh("frames-ch1")          # a fixed folder, emptied first, for output you want to look at afterwards
"""
import shutil
import tempfile
from pathlib import Path

SCRATCH = Path(__file__).resolve().parent.parent / ".cache" / "scratch"


def mkdtemp(prefix="yig-"):
    """A new, empty folder under .cache/scratch/ (like tempfile.mkdtemp, but in the scratch folder)."""
    SCRATCH.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=prefix, dir=SCRATCH))


def fresh(name):
    """.cache/scratch/<name>, emptied, for output that stays until the next run of the same tool."""
    path = (SCRATCH / name).resolve()
    if SCRATCH.resolve() not in path.parents:
        raise ValueError(f"{name!r} is not a folder inside {SCRATCH}")
    shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True)
    return path
