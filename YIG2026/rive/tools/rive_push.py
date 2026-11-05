"""Push one chapter to Rive, safely while other sessions run: every Rive push goes through this tool, never by hand.

    python3 tools/rive_push.py <ch> "<name>"       <ch> is 1, 2, 3 or ch1, ch2, ch3; <name> is the revision history label

It takes .cache/rive-push.lock atomically (the file is created exclusively, so only one session can hold it). If another
session holds it, it refuses, says who holds it and since when, and pushes nothing; a lock older than 15 minutes is
reported as stale, for Demetre to clear (this tool never deletes another session's lock). With the lock it runs
`rive push chapters/<ch> --yes --name=<name>`, removes its own lock afterwards (even when the push fails or is
interrupted), and prints the new revision.

Run `python3 tools/rive_compare.py <ch>` and get Demetre's approval first; commit and tag (rive/<ch>-...) after.

A new revision also refreshes the marketing copy in the same step: tools/marketing_copy.py rebuilds the marketing copy (repo-root docs/YIG2026/rive/docs/marketing/) with the
pushed chapter's .riv, commits only that folder and pushes main to GitHub, so the marketing page always matches Rive.
`--no-marketing` skips that (for a push you don't want published yet).
Exit code 0 when pushed (or already up to date), 1 when the push failed, 2 when another session holds the lock, 3 when Rive
took the push but the marketing copy was not refreshed, committed or pushed (the message says which; `npm run marketing` redoes it).
"""
import json
import os
import re
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RIVE = os.path.expanduser("~/.rive/bin/rive")
LOCK = REPO / ".cache" / "rive-push.lock"
PUSH_LIMIT = 600        # seconds
STALE = 15 * 60         # seconds: a lock older than this is reported as stale


class LockHeld(Exception):
    pass


def chapter_of(arg):
    ch = arg if arg.startswith("ch") else f"ch{arg}"
    if not (REPO / "chapters" / ch / "rive.yaml").exists():
        raise SystemExit(f"no chapter {arg!r}: use 1, 2, 3 (or ch1, ch2, ch3)")
    return ch


def take_lock(path, ch, name):
    """Create the lock exclusively and return its token; raise LockHeld (with who holds it) if it exists."""
    token = uuid.uuid4().hex
    info = {"chapter": ch, "name": name, "time": time.strftime("%Y-%m-%d %H:%M:%S"), "since": time.time(),
            "pid": os.getpid(), "token": token}
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    except FileExistsError:
        raise LockHeld(holder(path)) from None
    with os.fdopen(fd, "w") as f:
        json.dump(info, f)
        f.write("\n")
    return token


def holder(path):
    """A plain description of whoever holds the lock."""
    try:
        text = path.read_text()
    except OSError:
        return "another session (the lock went while reading it; try again)"
    try:
        info = json.loads(text)
        who = f"{info.get('chapter', '?')} (pushing {info.get('name', '?')!r}, since {info.get('time', '?')})"
        since = float(info.get("since", 0))
    except (ValueError, TypeError):
        who, since = f"another session ({text.strip()[:120]!r})", 0
    if not since:
        since = path.stat().st_mtime if path.exists() else time.time()
    age = time.time() - since
    stale = f"; it is {age / 60:.0f} minutes old, so it looks stale: tell Demetre, don't delete it" if age > STALE else ""
    return f"{who}{stale}"


def release_lock(path, token):
    """Remove the lock only if it is still ours. Returns True when it removed it."""
    try:
        if json.loads(path.read_text()).get("token") != token:
            return False
    except (OSError, ValueError):
        return False
    path.unlink()
    return True


def revision_of(output):
    m = re.findall(r"revision\s+(\d+)", output)
    return m[-1] if m else None


def push(ch, name, rive=RIVE, lock=LOCK, limit=PUSH_LIMIT):
    """Take the lock, push, release it. Returns (exit code, message)."""
    try:
        token = take_lock(lock, ch, name)
    except LockHeld as held:
        return 2, f"not pushing {ch}: another push holds {lock.relative_to(REPO) if lock.is_relative_to(REPO) else lock}: {held}. Wait for it, then run this again."
    previous = signal.signal(signal.SIGTERM, lambda *_: sys.exit(1))     # a kill still runs the finally below
    try:
        cmd = [rive, "push", str(REPO / "chapters" / ch), "--yes", f"--name={name}"]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=limit)
            code, output = r.returncode, (r.stdout + r.stderr).strip()
        except subprocess.TimeoutExpired:
            code, output = None, f"hit the {limit} s limit"
        except OSError as e:
            code, output = None, f"could not run the Rive CLI ({e})"
    finally:
        release_lock(lock, token)
        signal.signal(signal.SIGTERM, previous)
    if output:
        print(output)
    if code != 0:
        return 1, f"push of {ch} FAILED (exit {code}); the lock is released. Nothing to commit."
    if "already up to date" in output:
        return 0, f"{ch}: Rive was already up to date; no new revision. The lock is released."
    rev = revision_of(output)
    return 0, (f"{ch} pushed as {name!r}: revision {rev}. The lock is released; commit and tag it (rive/{ch}-...)." if rev else
               f"{ch} pushed as {name!r}, but the output named no revision (see above). The lock is released.")


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 2 or not args[1].strip():
        sys.exit(__doc__)
    ch = chapter_of(args[0])
    code, message = push(ch, args[1].strip())
    print(message)
    # a new revision also refreshes the marketing copy (the marketing folder), commits it and pushes GitHub, in this same step
    if code == 0 and "already up to date" not in message and "--no-marketing" not in argv:
        import marketing_copy
        ok, note = marketing_copy.publish(ch, revision_of(message))
        print(("marketing copy: " if ok else "MARKETING COPY: ") + note)
        if not ok:
            return 3        # the Rive push worked; run `npm run marketing` (or fix the cause above) and commit the marketing folder
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
