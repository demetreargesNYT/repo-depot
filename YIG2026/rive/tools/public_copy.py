"""Every public page, in the repo-root docs/ folder that GitHub Pages serves (docs/YIG2026/rive/docs/ there, so the URLs are
https://<user>.github.io/repo-depot/YIG2026/rive/docs/marketing/ and .../reference/timing-demo.html and .../text-motion.html).

    python3 tools/public_copy.py                refresh everything; the three .riv files come from each chapter's newest push tag (rive/<ch>-*)
    python3 tools/public_copy.py --working ch2  the same, with one chapter's .riv from chapters/<ch> as it is now (what a push just uploaded)
    python3 tools/public_copy.py --check        write nothing; stop if a public copy differs from its source or holds something internal
    npm run public                              the same as the first line

marketing/  the marketing team's screen-recording page:
  index.html          hand-written controls (Flow, Player, Top game, Screen, Jump to, Rive only) around the stage; never overwritten here
  stage.html          harness/experience-stage.html with its paths made relative, its comments removed and the Rive only pill hidden
  yig-integration.js, yig-text-motion.css, yig-framing.css   the engineering files the stage uses, comments removed
  *.riv               the three built Rive files, the same build the engineering package makes (working artboards taken out)
  fonts/, assets/, icons/   the fonts, the lockup art and the game icons
reference/ and core/  the two engineering reference pages, laid out like the engineering package so their relative links work:
  reference/timing-demo.html, reference/text-motion.html   engineering/ is the only source: copied by package_engineering.copy_reference_pages
                      (the step the package build uses), with one note line added after <body>; a copy that differs from its source
                      in anything else stops the build
  core/yig-text-motion.css, reference/example/yig-framing.css, reference/example/assets/icons/   what those pages link
Every text file in the public folder is checked for anything internal (names, design-file ids, PR numbers, local paths and
local-server routes), and nothing may sit in the root docs/ except these pages.

tools/rive_push.py calls publish() after every successful Rive push: it refreshes everything above (the pushed chapter's .riv from
chapters/<ch>, exactly what was uploaded), commits only the root docs/ folder, and pushes main. Tag the push as usual afterwards:
a manual refresh reads the newest tag, so an untagged push would be rolled back by it.
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import package_engineering as pe  # noqa: E402
import scratch  # noqa: E402

REPO = pe.REPO
# Pages serves only the repo root's docs/, so the page sits at docs/YIG2026/rive/docs/marketing/ there and its URL is
# https://<user>.github.io/repo-depot/YIG2026/rive/docs/marketing/. Nothing else may be under that root docs/ (it is public).
PUBLIC = REPO.parent.parent / "docs"
SITE = PUBLIC / "YIG2026" / "rive" / "docs"
MARKETING = SITE / "marketing"
REFERENCE = SITE / "reference"
CORE = SITE / "core"
RIVS = pe.RIVS
# the one line added to each reference page, right after <body>; everything else in a copy must equal engineering/'s page
REFERENCE_NOTE = ('<p style="margin:0;padding:6px 12px;background:#1F1F1F;color:#FFF;font:500 12px/1.3 -apple-system, \'Helvetica Neue\', Arial, sans-serif">'
                  'Reference page for the Year in Games 2026 build. Not the live experience.</p>\n')
# nothing that names a person, a design file, a pull request, a local path or a local server may be published
INTERNAL = re.compile(
    r"demetre|figma|games-phoenix|nytimes/|\bPR #|handoff|rive-plan|finesse|illustrator|claude|/Users/|127\.0\.0\.1|localhost|"
    r"\.cache|scratch|/builds|room-timing|room-pieces|finesse-notes|review\.js|send to|\bgit\b", re.I)
TEXT = {".html", ".js", ".css", ".svg", ".json", ".md"}


# ---- what goes in the page -------------------------------------------------------------------------------------------

def strip_css(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    return re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+\n", "\n", css)).strip() + "\n"


def strip_trailing(line):
    """Cut a trailing // comment, unless the // is inside a string (quotes tracked on this line only)."""
    quote, i = None, 0
    while i < len(line):
        ch = line[i]
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch in "'\"`":
            quote = ch
        elif line.startswith("//", i):
            return line[:i].rstrip()
        i += 1
    return line


def strip_js(js):
    lines = [strip_trailing(l) for l in js.split("\n") if not l.lstrip().startswith("//")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip() + "\n"


def stage_page():
    """harness/experience-stage.html, ready for a plain static host."""
    s = (REPO / "harness" / "experience-stage.html").read_text()
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    s = re.sub(r"(<style>)(.*?)(</style>)", lambda m: m.group(1) + strip_css(m.group(2)) + m.group(3), s, flags=re.S)
    s = re.sub(r'(<script type="module">)(.*?)(</script>)', lambda m: m.group(1) + strip_js(m.group(2)) + m.group(3), s, flags=re.S)
    s = s.replace("/assets/", "assets/").replace("/art/global/", "icons/")
    s = s.replace("<title>Year in Games 2026 · the full experience (stage)</title>", "<title>Year in Games 2026 · preview</title>")
    s = s.replace('<link rel="stylesheet" href="yig-framing.css">',
                  '<link rel="stylesheet" href="fonts/fonts.css">\n<link rel="stylesheet" href="yig-framing.css">')
    # the page's own pill would show in a recording; the Rive only button in index.html and the H key do the same job
    s = s.replace("</style>\n</head>", ".rive-only-pill { display: none !important; }\n</style>\n</head>", 1)
    return s


def fonts_css():
    css = strip_css((REPO / "harness" / "fonts" / "fonts.css").read_text())
    return css.replace("url(/fonts/", "url(")


def write_static():
    MARKETING.mkdir(parents=True, exist_ok=True)
    (MARKETING / "stage.html").write_text(stage_page())
    (MARKETING / "yig-integration.js").write_text(strip_js((REPO / "engineering" / "yig-integration.js").read_text()))
    (MARKETING / "yig-text-motion.css").write_text(strip_css((REPO / "engineering" / "yig-text-motion.css").read_text()))
    (MARKETING / "yig-framing.css").write_text(strip_css((REPO / "harness" / "yig-framing.css").read_text()))
    for sub, src, pattern in (("fonts", REPO / "harness" / "fonts", "*.woff2"), ("assets", REPO / "harness" / "assets", "*.svg"),
                              ("icons", REPO / "art" / "global", "*.svg")):
        (MARKETING / sub).mkdir(exist_ok=True)
        for f in sorted(src.glob(pattern)):
            shutil.copyfile(f, MARKETING / sub / f.name)
    (MARKETING / "fonts" / "fonts.css").write_text(fonts_css())
    write_reference()


def write_reference():
    """The two engineering reference pages, with the files they link, in the package's layout."""
    (REFERENCE / "example" / "assets" / "icons").mkdir(parents=True, exist_ok=True)
    CORE.mkdir(parents=True, exist_ok=True)
    pe.copy_reference_pages(REFERENCE)                                       # the package build's own copy step
    for name in pe.REFERENCE_PAGES:
        page = REFERENCE / name
        text = page.read_text()
        if text.count("<body>\n") != 1:
            raise SystemExit(f"engineering/{name} has no single '<body>' line to put the note after")
        page.write_text(text.replace("<body>\n", "<body>\n" + REFERENCE_NOTE, 1))
    shutil.copyfile(REPO / "engineering" / "yig-text-motion.css", CORE / "yig-text-motion.css")
    (REFERENCE / "example" / "yig-framing.css").write_text(strip_css((REPO / "harness" / "yig-framing.css").read_text()))
    for f in sorted((REPO / "art" / "global").glob("*.svg")):
        shutil.copyfile(f, REFERENCE / "example" / "assets" / "icons" / f.name)


def reference_problems():
    """Each public reference page must equal its engineering/ source once the note line is taken out."""
    problems = []
    for name in pe.REFERENCE_PAGES:
        page = REFERENCE / name
        if not page.exists():
            problems.append(f"reference/{name} is missing")
            continue
        text = page.read_text()
        if text.count(REFERENCE_NOTE) != 1 or text.replace(REFERENCE_NOTE, "", 1) != (REPO / "engineering" / name).read_text():
            problems.append(f"reference/{name} differs from engineering/{name} in more than the note line (or the note is missing)")
    return problems


# ---- the Rive files --------------------------------------------------------------------------------------------------

def newest_tag(ch):
    tags = subprocess.run(["git", "tag", "-l", f"rive/{ch}-*", "--sort=-creatordate"], cwd=REPO, capture_output=True, text=True).stdout.split()
    if not tags:
        raise SystemExit(f"no rive/{ch}-* tag: tag the push first")
    return tags[0]


def export_tag(ch, tag, dest):
    """The files a build needs, as they were at the tag (nothing is checked out)."""
    dest.mkdir(parents=True, exist_ok=True)
    for name in ("scene.rml", "chapter.json", "rive.yaml", "chapter-2-rive-import.svg"):
        r = subprocess.run(["git", "show", f"{tag}:./chapters/{ch}/{name}"], cwd=REPO, capture_output=True)
        if r.returncode == 0:
            (dest / name).write_bytes(r.stdout)
    if not (dest / "scene.rml").exists():
        raise SystemExit(f"{tag} has no chapters/{ch}/scene.rml")


def refresh_riv(ch, working=False):
    """Build one chapter and write its .riv into the marketing page's folder. Returns what it was built from."""
    scratch.SCRATCH.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="marketing-", dir=scratch.SCRATCH) as tmp:
        tmp = Path(tmp)
        if working:
            origin, src = "chapters/" + ch, None
        else:
            origin = newest_tag(ch)
            src = tmp / "tag" / ch
            export_tag(ch, origin, src)
        data = pe.build(ch, tmp / "build", src=src)
    MARKETING.mkdir(parents=True, exist_ok=True)
    (MARKETING / pe.RIVS[ch]).write_bytes(data)
    return origin


# ---- the check -------------------------------------------------------------------------------------------------------

def public_files():
    return [p for p in sorted(PUBLIC.rglob("*")) if p.is_file()] if PUBLIC.exists() else []


def internal_hits():
    hits = []
    for path in public_files():
        if path.suffix in TEXT:
            for n, line in enumerate(path.read_text().splitlines(), 1):
                m = INTERNAL.search(line)
                if m:
                    hits.append(f"{path.relative_to(PUBLIC)}:{n}: {m.group(0)!r} in {line.strip()[:90]}")
    return hits


def absolute_paths():
    """URLs that would break under a repo subpath: src/href/url() starting with a single slash."""
    bad = []
    for path in public_files():
        if path.suffix in {".html", ".css", ".js"}:
            for n, line in enumerate(path.read_text().splitlines(), 1):
                if re.search(r"""(?:src|href)=["']/(?!/)|url\(\s*["']?/(?!/)|fetch\(\s*["'`]/(?!/)|from\s+["']/""", line):
                    bad.append(f"{path.relative_to(PUBLIC)}:{n}: {line.strip()[:90]}")
    return bad


def verify():
    problems = internal_hits() + absolute_paths() + reference_problems()
    # the root docs/ is the only public folder: it holds these pages and nothing else
    problems += [f"{p.relative_to(PUBLIC)}: not part of the public copy, but under the public docs/"
                 for p in public_files() if not any(d in p.parents for d in (MARKETING, REFERENCE, CORE))]
    required = [MARKETING / "index.html", MARKETING / "stage.html", CORE / "yig-text-motion.css", REFERENCE / "example" / "yig-framing.css"]
    required += [MARKETING / n for n in RIVS.values()]
    problems += [f"{p.relative_to(PUBLIC)} is missing" for p in required if not p.exists()]
    if problems:
        print("\n".join(problems))
        raise SystemExit("STOPPED  the public folder has something internal, an absolute path, a stray file or a reference page that differs from its source (above)")


def refresh(chapters, working=False):
    write_static()
    for ch in chapters:
        origin = refresh_riv(ch, working)
        print(f"   {pe.RIVS[ch]} built from {origin}")
    verify()


# ---- after a Rive push -----------------------------------------------------------------------------------------------

def git(*args):
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True)


def publish(ch, revision=None):
    """Refresh every public page (the pushed chapter's .riv from chapters/<ch>), commit only the root docs/ folder, push main.
    Returns (ok, message)."""
    try:
        refresh([ch], working=True)
    except SystemExit as e:
        return False, f"the public pages were NOT refreshed: {e}"
    except Exception as e:                                   # a failed build must not hide that the Rive push worked
        return False, f"the public pages were NOT refreshed: {e}"
    git("add", "--", str(PUBLIC))
    if git("diff", "--cached", "--quiet", "--", str(PUBLIC)).returncode == 0:
        return True, "the public pages were already current; nothing to commit"
    rev = f" (Rive revision {revision})" if revision else ""
    message = f"YIG2026 rive: public pages refreshed after the {ch} Rive push{rev}"
    c = git("commit", "-m", message, "--", str(PUBLIC))
    if c.returncode != 0:
        return False, f"the public pages were refreshed but not committed: {(c.stdout + c.stderr).strip()[-300:]}"
    p = git("push", "origin", "main")
    if p.returncode != 0:
        return False, f"the public pages are committed but not pushed to GitHub: {(p.stdout + p.stderr).strip()[-300:]}"
    return True, "the public pages refreshed, committed and pushed to GitHub"


def main(argv):
    if argv == ["--check"]:
        verify()
    elif argv[:1] == ["--working"]:
        chapters = [a if a.startswith("ch") else f"ch{a}" for a in argv[1:]] or sys.exit(__doc__)
        refresh(chapters, working=True)
    elif argv:
        sys.exit(__doc__)
    else:
        refresh(list(RIVS))
    print(f"the public pages are up to date ({len(public_files())} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
