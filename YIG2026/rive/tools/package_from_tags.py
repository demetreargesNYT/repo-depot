"""Build the engineering package from the three pushed Rive tags, and zip it. This is what `npm run package` runs.

    python3 tools/package_from_tags.py

Each chapter's scene.rml, chapter.json, rive.yaml (and File 2's import SVG) are read from that chapter's newest rive/<ch>-* tag,
which `tools/rive_push.py` creates at every Rive push, so the .riv files in the package are the ones in Rive and the working tree's
unpushed chapter art can never get into the zip. The rule check and the build both read the tag's files. Everything else (the
guide, the card-flow spec, the CSS, the README, reference/) comes from the working tree, as in tools/package_engineering.py
(which builds from chapters/ and needs --working). Writes the unzipped package and deliver/yig-engineering-package.zip.
"""
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_chapter  # noqa: E402
import package_engineering as pe  # noqa: E402
import public_copy  # noqa: E402  newest_tag and export_tag are shared with the public pages
import scratch  # noqa: E402


def main():
    scratch.SCRATCH.mkdir(parents=True, exist_ok=True)
    src_root = scratch.mkdtemp("tag-build-")
    try:
        sources = {}
        for ch in pe.RIVS:
            tag = public_copy.newest_tag(ch)
            commit = subprocess.run(["git", "rev-list", "-n1", tag], cwd=pe.REPO, capture_output=True, text=True).stdout.strip()[:7]
            sources[ch] = Path(src_root) / ch
            public_copy.export_tag(ch, tag, sources[ch])
            print(f"{ch}: built from {tag} ({commit})")
        check_chapter.chapter_dir = lambda name: sources.get(name, Path(name))     # the rule check reads the tag's files too
        pe.main(src_for=lambda ch: sources[ch])
    finally:
        shutil.rmtree(src_root, ignore_errors=True)


if __name__ == "__main__":
    main()
