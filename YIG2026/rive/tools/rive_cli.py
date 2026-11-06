"""Run the Rive CLI from a tool so it can never hang the tool: one place for the push, pull and build calls.

    from rive_cli import run, LIMIT
    code, output = run([RIVE, "pull", folder, "--yes", "--quiet"])     # code is None when it timed out or could not start

Why (Rive CLI 1.9.1, 2026-11-06): a push from tools/rive_push.py ran 26 minutes and a compare 904 s, where both take
seconds. subprocess.run(..., timeout=) is not enough on its own: on a timeout it kills the CLI, then waits for its output
pipes to close, and any helper process the CLI started keeps them open, so the wait has no limit. Here:
  - the CLI runs in its own process group, and on a timeout the whole group is killed;
  - its output goes to a temporary file, not a pipe, so nothing left behind can hold the tool up;
  - stdin is /dev/null, so a prompt fails at once instead of waiting for an answer that never comes;
  - RIVE_NO_TUI=1, so the CLI never opens a browser to ask something (its own documented switch).
"""
import os
import signal
import subprocess
import tempfile
import time

RIVE = os.path.expanduser("~/.rive/bin/rive")
LIMIT = 180          # seconds: every push, pull and build takes a few seconds; three minutes means something is stuck


def run(cmd, limit=LIMIT, cwd=None):
    """(exit code, output). The code is None when the CLI timed out (the message says so) or could not be started."""
    env = dict(os.environ, RIVE_NO_TUI="1")
    t0 = time.time()
    with tempfile.TemporaryFile() as out:
        try:
            p = subprocess.Popen(cmd, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=out, stderr=subprocess.STDOUT,
                                 start_new_session=True)
        except OSError as e:
            return None, f"could not run the Rive CLI ({e})"
        try:
            code = p.wait(timeout=limit)
            timed_out = False
        except subprocess.TimeoutExpired:
            timed_out = True
        finally:
            try:
                os.killpg(p.pid, signal.SIGKILL)       # the CLI and anything it started, finished or not
            except (ProcessLookupError, PermissionError):
                pass
            p.wait()
        out.seek(0)
        text = out.read().decode(errors="replace").strip()
    if timed_out:
        return None, (text + "\n" if text else "") + f"TIMED OUT: the Rive CLI was still running after {limit} s ({time.time() - t0:.0f} s); it was stopped"
    return code, text
