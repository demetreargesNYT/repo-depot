"""Mark finesse notes done, without inline Python.

    python3 tools/note_done.py <ch> "<note title>" "<reply>"
    python3 tools/note_done.py <ch> --note "<title>" --reply "<reply>" [--note "<title>" --reply "<reply>" ...]

<ch> is 1, 2, 3 or ch1, ch2, ch3. It opens .cache/scratch.nosync/finesse-notes/<ch>.md and, in the most recent "## Sent" section
only (each send numbers its notes from 1, so the older sections repeat the titles), finds each note by its title and replaces its
"Status: open" line with "Status: done: <reply>". The title is the start of the note's heading, with or without the "###", e.g.
"Note 5" or "### Note 5 · Spelling Bee"; "Note 1" does not match "Note 10". Nothing is written unless every title is found
and still open. It prints how many notes in that section are still open.
Exit code 0 when done, 1 when a title isn't found or isn't open.
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
NOTES = REPO / ".cache" / "scratch.nosync" / "finesse-notes"
OPEN = "Status: open"


def chapter_of(arg):
    ch = arg if arg.startswith("ch") else f"ch{arg}"
    if not re.fullmatch(r"ch[123]", ch):
        sys.exit(f"no chapter {arg!r}: use 1, 2, 3 (or ch1, ch2, ch3)")
    return ch


def parse_pairs(args):
    """[(title, reply)] from `"<title>" "<reply>"` or from repeated --note/--reply pairs."""
    if "--note" not in args and "--reply" not in args:
        if len(args) != 2:
            sys.exit(__doc__)
        return [(args[0], args[1])]
    pairs, title = [], None
    it = iter(args)
    for a in it:
        value = next(it, None)
        if a not in ("--note", "--reply") or value is None:
            sys.exit(f"expected --note/--reply pairs, got {a!r}\n\n{__doc__}")
        if a == "--note":
            if title is not None:
                sys.exit(f"--note {title!r} has no --reply")
            title = value
        else:
            if title is None:
                sys.exit(f"--reply {value!r} comes before any --note")
            pairs.append((title, value))
            title = None
    if title is not None:
        sys.exit(f"--note {title!r} has no --reply")
    return pairs


def last_section(lines):
    """(start, end) of the lines of the most recent '## Sent' section."""
    starts = [i for i, l in enumerate(lines) if l.startswith("## Sent")]
    if not starts:
        raise ValueError("no '## Sent' section in the notes file")
    return starts[-1], len(lines)


def heading_matcher(title):
    t = re.sub(r"^#+\s*", "", title.strip())
    return re.compile(r"^###\s+" + re.escape(t) + r"(?![\w])")


def mark_done(text, pairs):
    """Return (new text, notes still open in the latest section). Raises ValueError, and changes nothing, on a bad title."""
    lines = text.split("\n")
    start, end = last_section(lines)
    done = set()
    for title, reply in pairs:
        pat = heading_matcher(title)
        heads = [i for i in range(start, end) if pat.match(lines[i])]
        if not heads:
            raise ValueError(f"no note titled {title!r} in the latest '{lines[start]}' section")
        if len(heads) > 1:
            raise ValueError(f"{title!r} matches {len(heads)} notes in the latest section; give more of the title")
        h = heads[0]
        nxt = next((i for i in range(h + 1, end) if lines[i].startswith("#")), end)
        status = next((i for i in range(h + 1, nxt) if lines[i].startswith("Status:")), None)
        if status is None:
            raise ValueError(f"{lines[h]!r} has no Status line")
        if lines[status].strip() != OPEN:
            raise ValueError(f"{lines[h]!r} is not open ({lines[status].strip()[:80]!r})")
        if h in done:
            raise ValueError(f"{title!r} is given twice")
        lines[status] = f"Status: done: {' '.join(reply.split())}"
        done.add(h)
    still_open = sum(1 for i in range(start, end) if lines[i].strip() == OPEN)
    return "\n".join(lines), still_open


def main(argv):
    if len(argv) < 3:
        sys.exit(__doc__)
    ch = chapter_of(argv[0])
    pairs = parse_pairs(argv[1:])
    path = NOTES / f"{ch}.md"
    if not path.exists():
        sys.exit(f"no notes file: {path.relative_to(REPO)}")
    try:
        text, still_open = mark_done(path.read_text(), pairs)
    except ValueError as e:
        print(f"note_done: {e}; nothing was changed")
        return 1
    path.write_text(text)
    print(f"{ch}: marked {len(pairs)} note(s) done; {still_open} still open in the latest send")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
