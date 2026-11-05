"""The marketing copy of the experience (docs/YIG2026/rive/docs/marketing/ at the repo root), a static page the marketing team can screen-record from a URL.

    python3 tools/marketing_copy.py                refresh all three .riv files from each chapter's newest push tag (rive/<ch>-*)
    python3 tools/marketing_copy.py --working ch2  refresh one chapter from chapters/<ch> as it is now (what a push just uploaded)
    npm run marketing                              the same as the first line

What it writes, all inside the marketing folder with relative paths only (it works under any URL subpath, with no server code):
  index.html          hand-written controls (Flow, Player, Top game, Screen, Jump to, Rive only) around the stage; never overwritten here
  stage.html          harness/experience-stage.html with its paths made relative, its comments removed and the Rive only pill hidden
  yig-integration.js, yig-text-motion.css, yig-framing.css   the engineering files the stage uses, comments removed
  *.riv               the three built Rive files, the same build the engineering package makes (working artboards taken out)
  fonts/, assets/, icons/   the fonts, the lockup art and the game icons
Then it checks every text file for anything internal (names, Figma ids, PR numbers, local-server paths) and stops if it finds any.

tools/rive_push.py calls publish() after every successful Rive push: it refreshes the pushed chapter's .riv from chapters/<ch>
(exactly what was uploaded), commits only the marketing folder, and pushes main. Tag the push as usual afterwards: a manual refresh
reads the newest tag, so an untagged push would be rolled back by it.

To publish from another folder (a root-level docs/ for GitHub Pages, say), change MARKETING in this file.
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
MARKETING = PUBLIC / "YIG2026" / "rive" / "docs" / "marketing"
RIVS = pe.RIVS
NOTE = "Preview for screen recording. Animations are the current versions and may still change."
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
    """Build one chapter and write its .riv into the marketing folder. Returns what it was built from."""
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

def internal_hits():
    hits = []
    for path in sorted(MARKETING.rglob("*")):
        if path.is_file() and path.suffix in TEXT:
            for n, line in enumerate(path.read_text().splitlines(), 1):
                m = INTERNAL.search(line)
                if m:
                    hits.append(f"{path.relative_to(MARKETING)}:{n}: {m.group(0)!r} in {line.strip()[:90]}")
    return hits


def absolute_paths():
    """URLs that would break under a repo subpath: src/href/url() starting with a single slash."""
    bad = []
    for path in sorted(MARKETING.rglob("*")):
        if path.is_file() and path.suffix in {".html", ".css", ".js"}:
            for n, line in enumerate(path.read_text().splitlines(), 1):
                if re.search(r"""(?:src|href)=["']/(?!/)|url\(\s*["']?/(?!/)|fetch\(\s*["'`]/(?!/)|from\s+["']/""", line):
                    bad.append(f"{path.relative_to(MARKETING)}:{n}: {line.strip()[:90]}")
    return bad


def verify():
    problems = internal_hits() + absolute_paths()
    if PUBLIC.exists():                                      # the root docs/ is the only public folder: it holds this page and nothing else
        problems += [f"{p.relative_to(PUBLIC)}: not part of the marketing copy, but under the public docs/"
                     for p in sorted(PUBLIC.rglob("*")) if p.is_file() and MARKETING not in p.parents]
    if not (MARKETING / "index.html").exists():
        problems.append("index.html is missing")
    for name in RIVS.values():
        if not (MARKETING / name).exists():
            problems.append(f"{name} is missing")
    if problems:
        print("\n".join(problems))
        raise SystemExit("STOPPED  the marketing folder has something internal or an absolute path (above)")


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
    """Refresh the pushed chapter's copy, commit only the marketing folder, push main. Returns (ok, message)."""
    try:
        refresh([ch], working=True)
    except SystemExit as e:
        return False, f"the marketing copy was NOT refreshed: {e}"
    except Exception as e:                                   # a failed build must not hide that the Rive push worked
        return False, f"the marketing copy was NOT refreshed: {e}"
    git("add", "--", str(MARKETING))
    if git("diff", "--cached", "--quiet", "--", str(MARKETING)).returncode == 0:
        return True, "the marketing folder was already current; nothing to commit"
    rev = f" (Rive revision {revision})" if revision else ""
    message = f"YIG2026 rive: marketing copy refreshed after the {ch} Rive push{rev}"
    c = git("commit", "-m", message, "--", str(MARKETING))
    if c.returncode != 0:
        return False, f"the marketing copy was refreshed but not committed: {(c.stdout + c.stderr).strip()[-300:]}"
    p = git("push", "origin", "main")
    if p.returncode != 0:
        return False, f"the marketing copy is committed but not pushed to GitHub: {(p.stdout + p.stderr).strip()[-300:]}"
    return True, "the marketing folder refreshed, committed and pushed to GitHub"


def main(argv):
    if argv[:1] == ["--working"]:
        chapters = [a if a.startswith("ch") else f"ch{a}" for a in argv[1:]] or sys.exit(__doc__)
        refresh(chapters, working=True)
    elif argv:
        sys.exit(__doc__)
    else:
        refresh(list(RIVS))
    print(f"the marketing folder is up to date ({len(list(MARKETING.rglob('*')))} entries)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
