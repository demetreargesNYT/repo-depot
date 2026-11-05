"""Delete a scratch folder, safely: this replaces `rm -rf`.

    python3 tools/scratch_clean.py <path> [<path> ...]

A path is deleted only if it resolves (symlinks and `..` followed) to somewhere strictly inside .cache/scratch.nosync/; the
scratch folder itself and anything else is refused, and nothing is deleted if any path is refused. A path that doesn't exist is
fine (nothing to do). Exit code 0 when done, 1 when a path was refused.
"""
import shutil
import sys
from pathlib import Path

ROOT = (Path(__file__).resolve().parent.parent / ".cache" / "scratch.nosync").resolve()


def inside_scratch(path):
    """The resolved path if it is strictly inside the scratch folder, else None."""
    p = Path(path).expanduser().resolve()
    return p if ROOT in p.parents else None


def clean(paths):
    """Returns (deleted, refused) lists of what was given."""
    checked = [(a, inside_scratch(a)) for a in paths]
    refused = [a for a, p in checked if p is None]
    if refused:
        return [], refused
    deleted = []
    for a, p in checked:
        if p.is_dir() and not p.is_symlink():
            shutil.rmtree(p)
            deleted.append(a)
        elif p.exists() or p.is_symlink():
            p.unlink()
            deleted.append(a)
    return deleted, []


def main(argv):
    if not argv or any(a.startswith("--") for a in argv):
        sys.exit(__doc__)
    deleted, refused = clean(argv)
    if refused:
        for a in refused:
            print(f"scratch_clean: refusing {a!r}: it is not inside {ROOT}")
        print("scratch_clean: nothing was deleted")
        return 1
    print(f"scratch_clean: deleted {len(deleted)} of {len(argv)} (the rest did not exist)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
