"""Build the one engineering package for all three Rive files, and zip it.

    python3 tools/package_engineering.py

Builds the unzipped package in .cache/scratch.nosync/yig-engineering-package/ and writes only the zip to deliver/
(deliver/yig-engineering-package.zip; neither is in git). The unzipped folder stays out of the iCloud-synced Desktop, so a rebuild
leaves no "core 2"-style conflict copies; its path is printed at the end, to open the demos from. Nothing is sent anywhere. In order:
  1. the quick rule check must pass for ch1, ch2 and ch3
  2. each file is built from a scratch copy of its project; File 2's working artboard, Bridge Art, is taken out of the
     scratch copy first, so the delivered .riv has only the main artboard. The built files are checked: the artboard,
     the state machine and the view model are there by name, and no working artboard is
  3. the package is assembled in two folders: core/ (the three .riv files, the engineering guide, the text CSS and the desktop arrow art:
     everything engineering needs) and reference/ (optional: the React example, our integration file and a standalone page that plays
     the whole experience), plus a five-line README at the root
  4. the guide and the README carry no internal version numbers, git references or names only we would understand (checked)
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_chapter  # noqa: E402
from rml_read import REPO, Scene, chapter_dir  # noqa: E402
import scratch  # noqa: E402  scratch output goes in .cache/scratch.nosync/, never /tmp
from xml_fragments import parse, ser  # noqa: E402

RIVE = os.path.expanduser("~/.rive/bin/rive")
OUT = scratch.SCRATCH / "yig-engineering-package"     # the unzipped package (out of iCloud); only the zip goes in deliver/
ZIP = REPO / "deliver" / "yig-engineering-package.zip"
RIVS = {"ch1": "start-chapter-1.riv", "ch2": "chapter-2.riv", "ch3": "chapters-3-4-end.riv"}
RUNTIME = "2.27.3"


def fail(msg):
    print("STOPPED  " + msg)
    sys.exit(1)


def build(chapter, work):
    """Build a scratch copy of the chapter (with working artboards taken out) and return the .riv's bytes."""
    src = chapter_dir(chapter)
    dst = work / chapter
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("build"))
    scene = Scene(dst / "scene.rml")
    keep = scene.artboard
    root = parse((dst / "scene.rml").read_text())
    removed = []
    for ab in list(root.findall("Artboard")):
        if ab.get("includeInExport") == "false" or ab.get("name") != keep.get("name"):
            root.remove(ab)
            removed.append(ab.get("name"))
    (dst / "scene.rml").write_text(ser(root))
    r = subprocess.run([RIVE, str(dst), "--once"], capture_output=True, text=True)
    out = sorted((dst / "build").glob("*.riv"), key=lambda p: p.stat().st_mtime)
    if r.returncode or not out:
        fail(f"building {chapter} failed:\n{r.stdout}\n{r.stderr}")
    data = out[-1].read_bytes()
    manifest = scene.manifest
    for name in (manifest["artboard"], manifest["stateMachine"], manifest["viewModel"]):
        if name.encode() not in data:
            fail(f"{chapter}: the built file does not contain {name!r}")
    for gone in removed:
        if gone.encode() in data:
            fail(f"{chapter}: the working artboard {gone!r} is still in the built file")
    print(f"   {chapter}: {RIVS[chapter]} {len(data):,} bytes" + (f" (taken out: {', '.join(removed)})" if removed else ""))
    return data


def example_page():
    """The harness's experience page, made standalone: its paths point at the package's folders."""
    page = (REPO / "harness" / "experience-stage.html").read_text()
    page = page.replace('src="/assets/', 'src="assets/').replace('/art/global/', 'assets/icons/')
    page = page.replace('from "./yig-integration.js"', 'from "../yig-integration.js"')       # reference/yig-integration.js
    page = page.replace('href="yig-text-motion.css"', 'href="../../core/yig-text-motion.css"')
    page = re.sub(r"<!--\n  The whole experience, Loading through End.*?-->", """<!--
  The whole experience, Loading through End, on one stage, playing the three Rive files back to back with the example
  player data below. Serve the package folder with any static server and open /reference/example/ (engineering-guide.md,
  section 9). Query:
  flow (subscriber is the default, or anon), player (wordle-only | midi-only | connections-only | several-games | all-seven | none), top (a game),
  goto (file:scene, for example 3:chapter-4), jump (a card index), rive-only (hide all the HTML; the H key and the pill do the same).
  Ad cards show no HTML. All copy is placeholder.
-->""", page, count=1, flags=re.S)
    page = re.sub(r"<!-- the Rive runtime: engineering's version -->", "<!-- the Rive runtime, pinned -->", page)
    return page


def framing_css():
    css = (REPO / "harness" / "yig-framing.css").read_text()
    css = re.sub(r"^/\*.*?\*/", """/* The framing the example page uses to crop and scale the Rive stage: the artboard (1495 x 1067) fills the window like
   object-fit: cover, zoomed 1.3x in portrait, with the tap zones below the desktop breakpoint (1025 px) and the arrow
   buttons from it up. Replace it with your page's own framing. */""", css, count=1, flags=re.S)
    css = re.sub(r"\(Demetre,\s*\n?\s*2026-10-29; he had first asked for halves\)", "", css)
    css = css.replace("/* The header and the copy position, from design:", "/* The header and the copy position, from the design:")
    css = re.sub(r"Figma \"Year in Games 2026\" \(file [A-Za-z0-9]+\), frames\s*\n?\s*\"Ch1 01 - Intro\" [\d:]+ \(mobile, 375 x 812\) and [\d:]+ \(desktop, 1495 x 1067\), read [\d-]+\.", "the Ch1 intro frames (mobile 375 x 812 and desktop 1495 x 1067).", css)
    return css


def reference_integration():
    js = (REPO / "engineering" / "yig-integration.js").read_text()
    # the example page is reference/example/index.html, and the files are in core/
    for name in RIVS.values():
        js = js.replace(f'src: "{name}"', f'src: "../../core/{name}"')
    js = js.replace("// The three files, in order,", "// The three files, in order (paths are relative to the example page, reference/example/index.html),")
    return js


def readme():
    return """# Year in Games 2026: Rive files and guide for engineering

Start here. You need the four things in `core/`: the three Rive files, the guide, the text CSS and the desktop arrow art.
Read `core/engineering-guide.md` first: "The rules" is a one-page summary, and "What's new in this delivery" lists what changed since the last package.
Everything in `reference/` is optional, a working example of the guide.
`reference/timing-demo.html` is the visual companion to the guide's timing section (section 6): double-click it to see every wait and the Rive calls on each tap.
`reference/text-motion.html` shows how the copy moves on each card, per line (the guide's section 9): double-click it too.
"""


def assemble(files):
    if OUT.exists():
        shutil.rmtree(OUT)
    core, ref = OUT / "core", OUT / "reference"
    core.mkdir(parents=True)
    ref.mkdir()
    for chapter, data in files.items():
        (core / RIVS[chapter]).write_bytes(data)
    shutil.copy(REPO / "docs" / "engineering-guide.md", core / "engineering-guide.md")
    shutil.copy(REPO / "engineering" / "yig-text-motion.css", core / "yig-text-motion.css")
    shutil.copy(REPO / "art" / "global" / "ui-desktop-button.svg", core / "ui-desktop-button.svg")      # the desktop arrow art: engineering needs it, so it is in core/ (the demo page keeps its own copy)
    (core / "ui-desktop-button.svg").chmod(0o644)
    (ref / "yig-integration.js").write_text(reference_integration())
    shutil.copy(REPO / "engineering" / "timing-demo.html", ref / "timing-demo.html")      # opens from a double-click; links ../core/yig-text-motion.css
    shutil.copy(REPO / "engineering" / "text-motion.html", ref / "text-motion.html")      # the same; also links example/yig-framing.css and its icons
    shutil.copytree(REPO / "engineering" / "react", ref / "react", ignore=shutil.ignore_patterns("node_modules", "dist"))
    main = ref / "react" / "src" / "main.tsx"
    main.write_text(main.read_text().replace("'../../yig-text-motion.css'", "'../../../core/yig-text-motion.css'"))
    ex = ref / "example"
    (ex / "assets" / "icons").mkdir(parents=True)
    (ex / "index.html").write_text(example_page())
    (ex / "yig-framing.css").write_text(framing_css())
    for svg in (REPO / "harness" / "assets").glob("*.svg"):
        shutil.copy(svg, ex / "assets" / svg.name)
    for svg in (REPO / "art" / "global").glob("*.svg"):
        shutil.copy(svg, ex / "assets" / "icons" / svg.name)
    (OUT / "README.md").write_text(readme())


def scrub():
    """The package carries no internal version numbers, git references or names."""
    bad = re.compile(r"handoff|hand-off-\d|revision \d|rive/ch\d|\bPR #|games-phoenix|Demetre|git ", re.I)
    ours = re.compile(r"harness|experience-stage|yigExperience|/experience\b|Figma|for review|what changed from|framework for engineering|Bridge Art|rive-plan|illustrator", re.I)
    problems = []
    for path in OUT.rglob("*"):
        if path.is_file() and path.suffix in {".md", ".js", ".ts", ".tsx", ".css", ".html", ".json"}:
            for n, line in enumerate(path.read_text().splitlines(), 1):
                if bad.search(line) or (path.suffix == ".md" and ours.search(line)):
                    problems.append(f"{path.relative_to(OUT)}:{n}: {line.strip()[:100]}")
    return problems


def main():
    for chapter in RIVS:
        out = check_chapter.run(chapter)
        failed = [t for ok, t in out if not ok]
        if failed:
            fail(f"{chapter} fails its rule check: {failed[0]}")
    print(f"rule checks pass for {', '.join(RIVS)}")
    scratch.SCRATCH.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="package-", dir=scratch.SCRATCH) as tmp:
        files = {c: build(c, Path(tmp)) for c in RIVS}
    assemble(files)
    problems = scrub()
    if problems:
        print("\n".join(problems))
        fail("the package mentions internal versions, git or names (above)")
    copies = [p for p in OUT.rglob("*") if re.search(r" \d+(\.[A-Za-z]+)?$", p.name)]
    if copies:
        fail(f"the package has copies with a number in the name (iCloud conflict copies?): {[str(p.relative_to(OUT)) for p in copies]}")
    ZIP.parent.mkdir(parents=True, exist_ok=True)
    if ZIP.exists():
        ZIP.unlink()
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for path in sorted(OUT.rglob("*")):
            if path.is_file() and path.name != ".DS_Store":
                z.write(path, Path("yig-engineering-package") / path.relative_to(OUT))
    print(f"\nzip:     {ZIP} ({ZIP.stat().st_size:,} bytes)\nunzipped (open the demos from here): {OUT}")


if __name__ == "__main__":
    main()
