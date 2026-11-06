"""Scripts that regenerate a whole room (or a whole file) refuse to overwrite a chapter's scene.rml that has changed since the commit
they were written against (CLAUDE.md, "Build rules": a room's current state is the file; scripts are history).

    import regen_guard
    WRITTEN_AGAINST = "c72d210"                       # the commit whose scene.rml this script takes as its input
    ...
    regen_guard.save(doc, WRITTEN_AGAINST, __file__)  # in place of doc.save()
    regen_guard.check(path, WRITTEN_AGAINST, __file__) # or check first, before writing the file some other way

The check looks only at a chapter's real file (chapters/ch1, ch2 or ch3 scene.rml); a copy in scratch is never refused, so a helper
can rebuild a room in its own copy. The real file may be written when it is byte for byte the scene.rml at WRITTEN_AGAINST, or what
this same script wrote last time (a script that rebuilds the file on every run, like chapters/ch2/scripts/build.py, calls stamp()
after writing; the stamps are in .cache/regen-stamps.json, on this machine only). Anything else (an Editor pull, a hand edit, a
finesse script, another session's work) stops it with the reason. To run a script on purpose against a newer file, read what has
changed, fold it into the script, and move its WRITTEN_AGAINST to the commit that holds that file: a decision, never a flag.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
STAMPS = REPO / ".cache" / "regen-stamps.json"
_checked = set()


def _real(path):
    """The chapter (ch1, ch2, ch3) when path is a chapter's real scene.rml, else None."""
    p = Path(path).resolve()
    for ch in ("ch1", "ch2", "ch3"):
        if p == (REPO / "chapters" / ch / "scene.rml").resolve():
            return ch
    return None


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _stamps():
    try:
        return json.loads(STAMPS.read_text())
    except (OSError, ValueError):
        return {}


def _key(script, ch):
    return f"{Path(script).resolve().relative_to(REPO)}:{ch}"


def check(path, written_against, script):
    """Stop (SystemExit) if path is a chapter's real scene.rml that is neither the file at written_against nor this script's last output."""
    ch = _real(path)
    if ch is None or Path(path).resolve() in _checked:
        return
    rel = f"chapters/{ch}/scene.rml"
    now = Path(path).read_bytes()
    r = subprocess.run(["git", "show", f"{written_against}:./{rel}"], cwd=REPO, capture_output=True)
    if r.returncode != 0:
        sys.exit(f"REFUSED  {Path(script).name}: it was written against commit {written_against}, which has no {rel} "
                 f"({r.stderr.decode(errors='replace').strip()[:160]})")
    if now != r.stdout and _stamps().get(_key(script, ch)) != _sha(now):
        sys.exit(f"REFUSED  {Path(script).name} regenerates a whole room, and {rel} has changed since commit {written_against}, the file it "
                 f"was written against (and since this script last wrote it). The file is the room's current state: running this would "
                 f"overwrite those changes. Work on a copy (--scene/--out), or fold the changes into the script and move its WRITTEN_AGAINST "
                 f"to the commit that holds them.")
    _checked.add(Path(path).resolve())


def stamp(path, script):
    """Record that this script wrote path (for scripts that rebuild the file on every run)."""
    ch = _real(path)
    if ch is None:
        return
    s = _stamps()
    s[_key(script, ch)] = _sha(Path(path).read_bytes())
    STAMPS.parent.mkdir(parents=True, exist_ok=True)
    STAMPS.write_text(json.dumps(s, indent=1, sort_keys=True) + "\n")


def save(doc, written_against, script):
    """doc.save(), refused when the real file has changed since written_against (checked once per run, before the first write)."""
    check(doc.path, written_against, script)
    doc.save()
