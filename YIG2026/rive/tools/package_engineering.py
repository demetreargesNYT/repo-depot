"""Build the one engineering package for all three Rive files, and zip it.

    python3 tools/package_engineering.py

Writes deliver/yig-engineering-package/ and deliver/yig-engineering-package.zip (deliver/ is not in git). Nothing is sent
anywhere. In order:
  1. the quick rule check must pass for ch1, ch2 and ch3
  2. each file is built from a scratch copy of its project; File 2's working artboard, Bridge Art, is taken out of the
     scratch copy first, so the delivered .riv has only the main artboard. The built files are checked: the artboard,
     the state machine and the view model are there by name, and no working artboard is
  3. the package is assembled: the three .riv files, the engineering guide, the React example, our integration file as a
     working reference, the text CSS, and a standalone page that plays the whole experience
  4. the README says how to run it; it carries no internal version numbers and no git references (checked)
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
from xml_fragments import parse, ser  # noqa: E402

RIVE = os.path.expanduser("~/.rive/bin/rive")
OUT = REPO / "deliver" / "yig-engineering-package"
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
    page = page.replace('from "./yig-integration.js"', 'from "../reference/yig-integration.js"')
    page = page.replace('href="yig-text-motion.css"', 'href="../yig-text-motion.css"')
    page = re.sub(r"<!--\n  The whole experience, Loading through End.*?-->", """<!--
  The whole experience, Loading through End, on one stage, playing the three Rive files back to back with the example
  player data below. Serve the package folder with any static server and open /example/ (see the README). Query:
  flow (subscriber is the default, or anon), player (wordle-only | midi-only | several-games | all-seven), top (a game),
  goto (file:scene, for example 3:chapter-4), jump (a card index). All copy is placeholder.
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
    # the example page lives in example/, so the files are one folder up
    for name in RIVS.values():
        js = js.replace(f'src: "{name}"', f'src: "../riv/{name}"')
    js = js.replace("// The three files, in order,", "// The three files, in order (paths are relative to the example page, example/index.html),")
    return js


def readme():
    return f"""# Year in Games 2026: Rive files and examples for engineering

This package has the three Rive files, a guide that says how to drive them from your own React code, a small React example
that follows the guide, and a page that plays the whole experience so you can see what the files do.

## What is here

| Path | What it is |
|---|---|
| `engineering-guide.md` | Start here. Every rule: the state machine and view model, the properties and the order to set them in, every scene of every file, the card logic, when each card's copy may appear, Back during a move, switching between the files, the text CSS. |
| `riv/start-chapter-1.riv` | File 1: Loading, Start, Ad 1, Chapter 1, Ad 2 |
| `riv/chapter-2.riv` | File 2: Chapter 2, ending on the empty Chapter 3 room |
| `riv/chapters-3-4-end.riv` | File 3: Ad 3, Chapter 3, Chapter 4, End |
| `react/` | A small React 18 + TypeScript example (`@rive-app/react-canvas` 4.20.1, CSS Modules) that does what the guide says |
| `reference/yig-integration.js` | The same rules as plain JavaScript: a working reference |
| `yig-text-motion.css` | The text motion for the copy (see the guide, section 11) |
| `example/` | A standalone page that plays the whole experience |

The state machine and the view model are named `Backdrop` in all three files. Start every file with the plural option
`stateMachines: 'Backdrop'`; the Rive runtime in your page ({RUNTIME}) ignores the singular.

## Run the example page

Any static server will do; opening `example/index.html` straight from disk will not load the `.riv` files. From this folder:

```
python3 -m http.server 8000
```

Then open <http://localhost:8000/example/>. It needs an internet connection, because the page loads the Rive runtime
({RUNTIME}) from a CDN. Tap or click the right side to go forward and the left side to go back; at a desktop width use the
arrow buttons, or the arrow keys. All copy on the page is placeholder.

Things to try (add them to the address):

- `?flow=anon` plays the anonymous flow.
- `?player=midi-only`, `several-games` or `all-seven` changes the subscriber's games (the default is `wordle-only`).
- `?goto=3:chapter-4` jumps to the first card on a scene (`file:scene`), and `?jump=12` jumps to a card by number.

## Read the React example

The `react/` folder is source to read and copy from, not an app with its own bundler. `src/useYigStage.ts` is the whole
rule set in one hook, `src/cards.ts` builds the card list for a player, and `src/YigStage.tsx` draws the stage, the copy
and the controls. Put the three `.riv` files where your app can fetch them (the example expects `/yig/<file>.riv`; change
`src/files.ts`), and import `yig-text-motion.css` once. To check it compiles on its own:

```
cd react
npm install
npx tsc --noEmit
```

## Coming later

- `how-to-mobile.riv`: the short tutorial overlay for mobile ("tap right for Next, tap left for Back"). It is not in this
  package; it will come on its own. Desktop has no tutorial file; the arrow buttons explain themselves.
- Final art for Chapter 4's Mini and Midi, and some placeholder pieces named in the guide.
"""


def assemble(files):
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "riv").mkdir(parents=True)
    for chapter, data in files.items():
        (OUT / "riv" / RIVS[chapter]).write_bytes(data)
    shutil.copy(REPO / "docs" / "engineering-guide.md", OUT / "engineering-guide.md")
    shutil.copy(REPO / "engineering" / "yig-text-motion.css", OUT / "yig-text-motion.css")
    (OUT / "reference").mkdir()
    (OUT / "reference" / "yig-integration.js").write_text(reference_integration())
    shutil.copytree(REPO / "engineering" / "react", OUT / "react", ignore=shutil.ignore_patterns("node_modules", "dist"))
    ex = OUT / "example"
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
    problems = []
    for path in OUT.rglob("*"):
        if path.is_file() and path.suffix in {".md", ".js", ".ts", ".tsx", ".css", ".html", ".json"}:
            for n, line in enumerate(path.read_text().splitlines(), 1):
                if bad.search(line):
                    problems.append(f"{path.relative_to(OUT)}:{n}: {line.strip()[:100]}")
    return problems


def main():
    for chapter in RIVS:
        out = check_chapter.run(chapter)
        failed = [t for ok, t in out if not ok]
        if failed:
            fail(f"{chapter} fails its rule check: {failed[0]}")
    print(f"rule checks pass for {', '.join(RIVS)}")
    with tempfile.TemporaryDirectory(prefix="yig-package-") as tmp:
        files = {c: build(c, Path(tmp)) for c in RIVS}
    assemble(files)
    problems = scrub()
    if problems:
        print("\n".join(problems))
        fail("the package mentions internal versions, git or names (above)")
    if ZIP.exists():
        ZIP.unlink()
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for path in sorted(OUT.rglob("*")):
            if path.is_file() and path.name != ".DS_Store":
                z.write(path, Path("yig-engineering-package") / path.relative_to(OUT))
    print(f"\npackage: {OUT}\nzip:     {ZIP} ({ZIP.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
