"""Print the byte size of a Rive file, without the raw Rive command line.

    python3 tools/rive_size.py <file.riv>             its size on disk
    python3 tools/rive_size.py <project folder>       builds the project (`rive <folder> --publish`, which writes the .riv into
                                                      the folder's build/ as any build does) and prints the size it reports

A folder given as 1, 2 or 3 (or ch1, ch2, ch3) means chapters/<ch>. Nothing is pushed or published. Exit code 0 on success,
1 when the build fails.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RIVE = os.path.expanduser("~/.rive/bin/rive")
LIMIT = 300     # seconds


def project_of(arg):
    if re.fullmatch(r"(ch)?[123]", arg):
        return REPO / "chapters" / (arg if arg.startswith("ch") else f"ch{arg}")
    return Path(arg)


def built_size(output):
    m = re.findall(r"built\s+\S+\s+\((\d+) bytes", output)
    return int(m[-1]) if m else None


def main(argv):
    if len(argv) != 1 or argv[0].startswith("--"):
        sys.exit(__doc__)
    target = project_of(argv[0])
    if target.is_file():
        print(f"{target.name}: {target.stat().st_size} bytes")
        return 0
    if not (target / "rive.yaml").exists():
        print(f"rive_size: {argv[0]!r} is neither a .riv file nor a Rive project folder (no rive.yaml)")
        return 1
    try:
        r = subprocess.run([RIVE, str(target), "--publish"], capture_output=True, text=True, timeout=LIMIT)
    except subprocess.TimeoutExpired:
        print(f"rive_size: the build hit the {LIMIT} s limit")
        return 1
    output = (r.stdout + r.stderr).strip()
    size = built_size(output)
    if r.returncode != 0 or size is None:
        print(output[-600:])
        print(f"rive_size: the build failed (exit {r.returncode})" if r.returncode else "rive_size: the build reported no size")
        return 1
    print(f"{target.name}: {size} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
