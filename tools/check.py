"""The fast check, run after every change:  npm run check ch2

  1. rive --verify and rive inspect: the file builds and reports no problems
  2. the rule checks in check_chapter.py: Waiting poses equal their intro's first keys, every intro is exactly
     3.2 s, every loop's first and last frames match (and start on the intro's last frame), the shared
     backdrop and its colour crossfade, outros and draw rules are as the spec says, no intro keys the shelf ball
  3. the opener clears the artboard: with the first game started, the shelf room draws nothing from 1.7 s on
     (two renders; the other rooms are covered by tap_test.py, which needs a pair of games)

It does not re-render, pixel-diff or time anything else. Full passes (tap_test.py, harness/text-test.mjs,
frame-by-frame renders) are for a handoff to engineering, or when asked.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageChops
import check_chapter
from rml_read import chapter_dir

RIVE = os.path.expanduser("~/.rive/bin/rive")


def rive_json(args):
    r = subprocess.run([RIVE, *args, "--format=json"], capture_output=True, text=True)
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return {"success": False, "errors": [r.stdout + r.stderr], "data": {"problems": []}}


def build_checks(project):
    out = []
    v = rive_json([str(project), "--verify"])
    out.append((v.get("success", False) and not v.get("errors"), f"rive --verify: {len(v.get('errors', []))} error(s), {len(v.get('warnings', []))} warning(s)"))
    ins = subprocess.run([RIVE, "inspect", str(project), "--summary"], capture_output=True, text=True)
    try:
        problems = json.loads(ins.stdout)["problems"]
    except (json.JSONDecodeError, KeyError):
        problems = ["inspect output could not be read"]
    out.append((not problems, f"rive inspect: {len(problems)} problem(s)" + ("" if not problems else f" {problems[:2]}")))
    return out


def opener_clears(project):
    """Scene 1 from the start: the opener leaves. At 1.58 s, the outro's last frame (the Gone pose takes over at
    1.6 s and would hide a broken outro), it must draw nothing."""
    tmp = Path(tempfile.mkdtemp())
    try:
        dst = tmp / "p"
        shutil.copytree(project, dst, ignore=shutil.ignore_patterns("build"))
        full_t = tmp / "full.png"
        subprocess.run([RIVE, str(dst), "--data=scene=1", f"--screenshot={full_t}", "--advance=1.58s"], capture_output=True)
        if not full_t.exists():
            return False, "the opener check could not render the scene (the build failed)"
        tree = ET.parse(dst / "scene.rml")
        for n in tree.getroot().iter("Node"):
            if n.get("name") == "Shelf Room":
                n.set("hidden", "true")
        tree.write(dst / "scene.rml", encoding="utf-8")
        bare_t = tmp / "bare.png"
        subprocess.run([RIVE, str(dst), "--data=scene=1", f"--screenshot={bare_t}", "--advance=1.58s"], capture_output=True)
        if not bare_t.exists():
            return False, "the opener check could not render the scene (the build failed)"
        diff = ImageChops.difference(Image.open(full_t).convert("RGB"), Image.open(bare_t).convert("RGB")).convert("L").point(lambda v: 255 if v > 12 else 0)
        px = diff.histogram()[255]
        return px == 0, f"the opener clears the artboard by the outro's last frame (1.58 s): {px} px of the shelf room still drawn"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv):
    chapter = argv[0] if argv else "ch2"
    t0 = time.time()
    project = chapter_dir(chapter)
    results = build_checks(project) + check_chapter.run(chapter) + [opener_clears(project)]
    failed = [t for ok, t in results if not ok]
    for ok, t in results:
        if not ok:
            print("FAIL  " + t)
    print(f"{len(results) - len(failed)} of {len(results)} checks passed in {time.time() - t0:.1f} s" + ("" if not failed else f"; {len(failed)} FAILED"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
