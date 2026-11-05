"""Build the one engineering package for all three Rive files, and zip it.

    python3 tools/package_engineering.py --working     (the working tree's chapters; `npm run package` uses tools/package_from_tags.py)

Builds the unzipped package in .cache/scratch.nosync/shared/yig-engineering-package/ and writes only the zip to deliver/
(deliver/yig-engineering-package.zip; neither is in git). The unzipped folder stays out of the iCloud-synced Desktop, so a rebuild
leaves no "core 2"-style conflict copies; its path is printed at the end, to open the demos from. Nothing is sent anywhere. In order:
  1. the quick rule check must pass for ch1, ch2 and ch3
  2. each file is built from a scratch copy of its project; File 2's working artboard, Bridge Art, is taken out of the
     scratch copy first, so the delivered .riv has only the main artboard. The built files are checked: the artboard,
     the state machine and the view model are there by name, and no working artboard is
  3. the package is assembled in two folders: core/ (the three .riv files, the engineering guide, the text CSS and the desktop arrow art:
     everything engineering needs; core/card-flow.md is the card-by-card spec) and reference/ (optional: the React example, our integration file and a standalone page that plays
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
OUT = scratch.ROOT / "shared" / "yig-engineering-package"     # the unzipped package (out of iCloud; the shared-files session's); only the zip goes in deliver/
ZIP = REPO / "deliver" / "yig-engineering-package.zip"
RIVS = {"ch1": "start-chapter-1.riv", "ch2": "chapter-2.riv", "ch3": "chapters-3-4-end.riv"}
RUNTIME = "2.27.3"


def fail(msg):
    print("STOPPED  " + msg)
    sys.exit(1)


def build(chapter, work, src=None):
    """Build a scratch copy of the chapter (with working artboards taken out) and return the .riv's bytes.
    `src` is the folder to build from; it defaults to chapters/<chapter> (tools/public_copy.py passes a pushed tag's files)."""
    src = Path(src) if src else chapter_dir(chapter)
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
  player data below. Serve the package folder with any static server and open /reference/example/ (see the README). Query:
  flow (subscriber is the default, or anon), player (wordle-only | midi-only | connections-only | several-games | all-seven | none), top (a game),
  goto (file:scene, for example 3:chapter-4-top-game), jump (a card's place in the list), rive-only (hide all the HTML; the H key and the pill do the same).
  Ad cards show no HTML. All copy is sample copy.
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
    return """# Year in Games 2026: Rive files for engineering

Read `core/engineering-guide.md` first. It has everything you need to build with these files. `core/card-flow.md` lists every card in order for both flows.

This replaces the Nov 3 package. Scene names have changed; use the names in the guide.

## What you need: `core/`

| File | What it is |
|---|---|
| `start-chapter-1.riv`, `chapter-2.riv`, `chapters-3-4-end.riv` | The three Rive files |
| `engineering-guide.md` | The guide |
| `card-flow.md` | Every card in order, for both flows: scene, settings, copy wait and when it is skipped |
| `yig-text-motion.css` | The copy motion and waits |
| `ui-desktop-button.svg` | The desktop arrow button |

## Working examples: `reference/` (optional)

| Path | What it is |
|---|---|
| `timing-demo.html` | Every wait and the Rive calls on each tap. Double-click to open. |
| `text-motion.html` | How the copy moves on each card. Double-click to open. |
| `example/` | The whole experience with the real files. |
| `react/` | A React 18 and TypeScript example. `src/useYigStage.ts` has the rules; `src/cards.ts` builds the card list. |
| `yig-integration.js` | The same rules in plain JavaScript. |

To run `example/`, serve the package folder with any static server (`python3 -m http.server 8000`) and open
`http://localhost:8000/reference/example/`. Options: `?flow=anon`, `?player=connections-only` (or `several-games`,
`midi-only`, `all-seven`, `none`), `?goto=3:chapter-4-top-game` (a file and a scene), `?jump=12` (a card's place in the
list, Loading is 0), and `?rive-only` or the H key to hide the HTML.
"""


REFERENCE_PAGES = ("timing-demo.html", "text-motion.html")


def copy_reference_pages(ref):
    """Copy the two reference pages from engineering/ into `ref`, unchanged. They open from a double-click and link
    ../core/yig-text-motion.css; text-motion.html also links example/yig-framing.css and example/assets/icons/.
    The engineering package and tools/public_copy.py (the public pages) both use this, so engineering/ stays the only source."""
    for name in REFERENCE_PAGES:
        shutil.copy(REPO / "engineering" / name, Path(ref) / name)


def assemble(files):
    if OUT.exists():
        shutil.rmtree(OUT)
    core, ref = OUT / "core", OUT / "reference"
    core.mkdir(parents=True)
    ref.mkdir()
    for chapter, data in files.items():
        (core / RIVS[chapter]).write_bytes(data)
    shutil.copy(REPO / "docs" / "engineering-guide.md", core / "engineering-guide.md")
    shutil.copy(REPO / "docs" / "card-flow.md", core / "card-flow.md")
    shutil.copy(REPO / "engineering" / "yig-text-motion.css", core / "yig-text-motion.css")
    shutil.copy(REPO / "art" / "global" / "ui-desktop-button.svg", core / "ui-desktop-button.svg")      # the desktop arrow art: engineering needs it, so it is in core/ (the demo page keeps its own copy)
    (core / "ui-desktop-button.svg").chmod(0o644)
    (ref / "yig-integration.js").write_text(reference_integration())
    copy_reference_pages(ref)
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
    # card-flow.md also gets the public pages' check (no person, design file, pull request, local path or server) and the old-name
    # check: none of the Nov 3 scene names, which are fine only in the guide's last section. Its frame names (such as chapter-1--intro)
    # are the design files' names, so the word "intro" is checked in the Scene column instead (a scene that isn't in the enum fails the harness test).
    import public_copy      # here, not at the top: public_copy imports this file
    flow = OUT / "core" / "card-flow.md"
    old = re.compile(r"chapter-1-card-\d|chapter-3-bird|\bad-3\b|\bdaily\b|\bbridge\b|`intro`", re.I)
    for n, line in enumerate(flow.read_text().splitlines(), 1):
        hit = public_copy.INTERNAL.search(line) or old.search(line)
        if hit:
            problems.append(f"core/card-flow.md:{n}: {hit.group(0)!r} in {line.strip()[:100]}")
    return problems


def main(src_for=None):
    """`src_for(chapter)` gives the folder to build a chapter from (tools/package_from_tags.py passes each tag's files);
    without it the build reads chapters/<chapter>, the working tree."""
    for chapter in RIVS:
        out = check_chapter.run(chapter)
        failed = [t for ok, t in out if not ok]
        if failed:
            fail(f"{chapter} fails its rule check: {failed[0]}")
    print(f"rule checks pass for {', '.join(RIVS)}")
    scratch.SCRATCH.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="package-", dir=scratch.SCRATCH) as tmp:
        files = {c: build(c, Path(tmp), src=src_for(c) if src_for else None) for c in RIVS}
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
    if "--working" not in sys.argv:
        sys.exit("This builds from chapters/, which can hold art that isn't in Rive. Use `npm run package` (tools/package_from_tags.py), "
                 "or pass --working to build from the working tree on purpose.")
    main()
