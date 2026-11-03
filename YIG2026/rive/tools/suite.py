"""Run the tests in short pieces, one at a time.

    npm run suite       every test, once: when Demetre asks, or before a delivery that changes Rive files
    npm run smoke       the short set, before a delivery
    npm run smoke -- --all / npm run suite -- --all     run everything, skipping nothing (below)
    python3 tools/suite.py --list [--smoke]     print the pieces and stop
    python3 tools/suite.py --from 19            start at piece 19 (resume a run that stopped there)

What is skipped (both kept in .cache/suite-state.json, written only when a piece or a whole smoke run passes):
  - a chapter's own pieces (its rule checks, loop motion, tap and back) when nothing they read has changed since that piece last
    passed: the chapter's folder (scene.rml, chapter.json, rive.yaml; not build/), its rooms sheet, and the tools in tools/;
  - the whole smoke run when the reference code (engineering/), the harness (harness/, not node_modules), the guide
    (docs/engineering-guide.md) and this runner are all unchanged since the last smoke run that passed. It says why it ran or skipped.

Both npm scripts run under `caffeinate -i`, so the Mac cannot sleep mid-run. Each piece runs alone with a 15 minute limit;
the browser tests also fail on their own, with a message, when Chrome closes or stops answering for 60 seconds. Before and
after every piece, what this run started is killed, and nothing else (other sessions run their own tests alongside): the
piece's own process group, the package web server it started, and the headless Chrome windows whose profile folder is under
this run's own folder (YIG_CHROME_ROOT, which harness/scratch.mjs uses). The review server is never stopped. The run stops at the first failing piece and says which piece, why,
and where its log is. Logs are in test-logs/ (git-ignored) and are overwritten by each run.
"""
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import scratch

REPO = Path(__file__).resolve().parent.parent
LOGS = REPO / "test-logs"
LIMIT = 15 * 60                      # seconds per piece
HARNESS = "http://127.0.0.1:8765"    # the review server (harness/serve.mjs); the suite starts it if it isn't running and leaves it running
PACKAGE_PORT = 8900                  # the suite's own port for the unzipped-package demo, so it never touches a server of yours
PACKAGE_DIR = scratch.ROOT / "shared" / "yig-engineering-package"   # where package_engineering.py builds the unzipped package
PACKAGE = f"http://127.0.0.1:{PACKAGE_PORT}"
CHROME_RUN = scratch.SCRATCH / "chrome" / f"suite-{os.getpid()}"     # this run's Chrome profiles, so its cleanup can tell them apart
started = []                         # the process groups this run started and cleans up (its package web servers)

STATE = REPO / ".cache" / "suite-state.json"   # what passed, and the inputs it passed with (git-ignored)
SHEETS = {"ch1": "docs/rooms-ch1.md", "ch2": "docs/rooms.md", "ch3": "docs/rooms-ch3.md"}
SMOKE_INPUTS = {"the reference code": "engineering", "the harness": "harness", "the guide": "docs/engineering-guide.md", "the test runner": "tools/suite.py"}

PLAYERS = ["wordle-only", "midi-only", "connections-only", "several-games", "all-seven", "none"]


def piece(name, cmd, tier="full", needs=None, chapter=None):
    """tier: "full" (only in npm run suite), "smoke" (only in npm run smoke) or "both". chapter: the piece only reads that
    chapter's file, so it is skipped while the chapter is unchanged since the piece last passed."""
    return {"name": name, "cmd": cmd, "tier": tier, "needs": needs, "chapter": chapter}


def files_hash(paths):
    """One hash over every file under the given paths (relative to the repo), skipping build/, node_modules/ and caches."""
    h = hashlib.sha256()
    for rel in paths:
        root = REPO / rel
        files = [root] if root.is_file() else sorted(f for f in root.rglob("*") if f.is_file()) if root.exists() else []
        for f in files:
            parts = set(f.relative_to(REPO).parts)
            if parts & {"build", "node_modules", "__pycache__", ".DS_Store"} or f.name == ".DS_Store":
                continue
            h.update(str(f.relative_to(REPO)).encode() + b"\0" + f.read_bytes() + b"\0")
    return h.hexdigest()


def chapter_hash(p):
    return files_hash([f"chapters/{p['chapter']}", SHEETS[p["chapter"]], "tools"]) + " " + " ".join(p["cmd"])


def load_state():
    try:
        return json.loads(STATE.read_text())
    except (OSError, ValueError):
        return {}


def save_state(state):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=1, sort_keys=True))


def experience(url, path, flow, size, player):
    cmd = ["node", "harness/experience-test.mjs", "--flows", flow, "--sizes", size, "--players", player]
    if url:
        cmd += ["--url", url, "--path", path]
    return cmd


def pieces():
    out = []
    for ch in ("ch1", "ch2", "ch3"):
        out.append(piece(f"rule checks {ch}", ["python3", "tools/check.py", ch], tier="both", chapter=ch))
    out.append(piece("unit tests", ["python3", "-m", "unittest", "discover", "-s", "tools/tests"], tier="both"))
    for ch in ("ch1", "ch2", "ch3"):
        out.append(piece(f"loop motion {ch}", ["python3", "tools/loop_motion.py", ch], tier="both", chapter=ch))
    for ch in ("ch1", "ch2", "ch3"):
        out.append(piece(f"tap {ch}", ["python3", "tools/tap_test.py", ch], chapter=ch))
    for ch in ("ch1", "ch2", "ch3"):
        out.append(piece(f"back {ch}", ["python3", "tools/back_test.py", ch], chapter=ch))
    # the Chapter 2 page's text timing: the whole test in the full run, the shorter set of tap times in smoke
    out.append(piece("text timing (Chapter 2 page)", ["node", "harness/text-test.mjs"], needs="harness"))
    out.append(piece("text timing, short", ["node", "harness/text-test.mjs", "--quick"], tier="smoke", needs="harness"))
    for flow in ("sub", "anon"):
        for size in ("phone", "desktop"):
            out.append(piece(f"experience harness {flow} {size}", experience(None, None, flow, size, "wordle-only"), needs="harness"))
    out.append(piece("experience harness sub phone", experience(None, None, "sub", "phone", "connections-only"), tier="smoke", needs="harness"))
    out.append(piece("experience harness anon phone", experience(None, None, "anon", "phone", "wordle-only"), tier="smoke", needs="harness"))
    out.append(piece("Finesse panel", ["node", "harness/finesse-test.mjs"], needs="harness"))
    out.append(piece("build the package", ["python3", "tools/package_engineering.py"]))
    for player in PLAYERS:
        out.append(piece(f"package demo sub phone {player}", experience(PACKAGE, "/reference/example/", "sub", "phone", player), needs="package"))
    out.append(piece("package demo sub desktop connections-only", experience(PACKAGE, "/reference/example/", "sub", "desktop", "connections-only"), needs="package"))
    for size in ("phone", "desktop"):
        out.append(piece(f"package demo anon {size}", experience(PACKAGE, "/reference/example/", "anon", size, "wordle-only"), needs="package"))
    return out


def sh(args):
    return subprocess.run(args, capture_output=True, text=True).stdout


def kill_leftovers():
    """Only what this run started: Chrome windows with a profile under CHROME_RUN, and the package web servers in `started`."""
    mark = f"--user-data-dir={CHROME_RUN}{os.sep}"     # a substring test: the profile path has a space in it ("My Stuff")
    for line in sh(["ps", "-axo", "pid=,command="]).splitlines():
        pid, _, cmd = line.strip().partition(" ")
        if mark in cmd and int(pid) != os.getpid():
            try:
                os.kill(int(pid), signal.SIGKILL)
            except ProcessLookupError:
                pass
    while started:
        try:
            os.killpg(started.pop(), signal.SIGKILL)
        except ProcessLookupError:
            pass


def up(url):
    try:
        urllib.request.urlopen(url, timeout=2)
        return True
    except Exception:
        return False


def ensure_harness():
    if up(HARNESS + "/"):
        return None
    log = open(LOGS / "harness-server.log", "w")
    subprocess.Popen(["node", "serve.mjs"], cwd=REPO / "harness", stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    for _ in range(50):
        if up(HARNESS + "/"):
            return "started the review server on 8765 (it stays running)"
        time.sleep(0.2)
    return "could not start the review server on 8765"


def serve_package():
    if not (PACKAGE_DIR / "reference" / "example" / "index.html").exists():
        return "the package folder is missing (the 'build the package' piece makes it)"
    log = open(LOGS / "package-server.log", "w")
    server = subprocess.Popen([sys.executable, "-m", "http.server", str(PACKAGE_PORT), "--bind", "127.0.0.1"], cwd=PACKAGE_DIR,
                              stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    started.append(server.pid)
    for _ in range(50):
        if up(f"{PACKAGE}/reference/example/"):
            return None
        time.sleep(0.2)
    return f"could not start the package web server on {PACKAGE_PORT}"


def run_piece(p, log_path):
    """Returns (ok, why)."""
    if p["needs"] == "harness":
        err = ensure_harness()
        if err and err.startswith("could not"):
            return False, err
    if p["needs"] == "package":
        err = serve_package()
        if err:
            return False, err
    # the pieces write their scratch where this run does, and their Chrome profiles in this run's own folder
    env = {**os.environ, "YIG_SESSION": scratch.SCRATCH.name, "YIG_CHROME_ROOT": str(CHROME_RUN)}
    with open(log_path, "w") as log:
        proc = subprocess.Popen(p["cmd"], cwd=REPO, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            rc = proc.wait(timeout=LIMIT)
        except subprocess.TimeoutExpired:
            rc = None
        try:
            os.killpg(proc.pid, signal.SIGKILL)       # whatever the piece left running in its own process group
        except ProcessLookupError:
            pass
        if rc is None:
            return False, f"hit the {LIMIT // 60} minute limit"
    if rc == 0:
        return True, ""
    text = Path(log_path).read_text(errors="replace")
    browser = re.search(r"^FAIL  browser: (.*)$", text, re.M)
    if browser:
        return False, f"Chrome stopped: {browser.group(1)}"
    return False, f"exit code {rc}"


def tail_of(log_path):
    lines = Path(log_path).read_text(errors="replace").splitlines()
    fails = [l for l in lines if l.startswith("FAIL") or "FAIL " in l[:12]]
    shown = fails[:6] if fails else lines[-6:]
    return "\n".join("    " + l[:240] for l in shown)


def fmt(seconds):
    return f"{int(seconds // 60)} min {int(seconds % 60):02d} s" if seconds >= 60 else f"{seconds:.1f} s"


def smoke_gate(state):
    """(run?, why) for the whole smoke run, from the inputs it covers."""
    now = {label: files_hash([rel]) for label, rel in SMOKE_INPUTS.items()}
    last = state.get("smoke")
    if not last:
        return True, "no smoke run has passed yet", now
    changed = [label for label in SMOKE_INPUTS if last["inputs"].get(label) != now[label]]
    if changed:
        return True, ", ".join(changed) + (" has" if len(changed) == 1 else " have") + " changed since the last smoke pass (" + last["at"] + ")", now
    return False, "the reference code, the harness, the guide and the test runner are unchanged since the last smoke pass (" + last["at"] + ")", now


def main():
    smoke = "--smoke" in sys.argv
    every = "--all" in sys.argv
    state = load_state()
    chosen = [p for p in pieces() if p["tier"] in ("both", "smoke" if smoke else "full")]
    first = int(sys.argv[sys.argv.index("--from") + 1]) if "--from" in sys.argv else 1     # resume a run that stopped: the pieces before it are skipped
    if "--list" in sys.argv:
        for i, p in enumerate(chosen, 1):
            print(f"{i:2}. {p['name']}   {' '.join(p['cmd'])}")
        return
    smoke_inputs = None
    if smoke:
        run, why, smoke_inputs = smoke_gate(state)
        if every:
            print("smoke: running everything (--all)" + ("" if run else "; " + why), flush=True)
        elif not run:
            print(f"smoke: skipped: {why}.\nnpm run smoke -- --all runs it anyway.")
            return
        else:
            print(f"smoke: running because {why}.", flush=True)
    if LOGS.exists():
        shutil.rmtree(LOGS)
    LOGS.mkdir()
    label = "smoke" if smoke else "suite"
    print(f"{label}: {len(chosen)} pieces, one at a time, {LIMIT // 60} minute limit each. Logs: {LOGS.relative_to(REPO)}/\n", flush=True)
    done = []
    started = time.time()
    for n, p in enumerate(chosen, 1):
        if n < first:
            continue
        key = chapter_hash(p) if p["chapter"] else None
        if key and not every and state.get("pieces", {}).get(p["name"]) == key:
            print(f"[{n}/{len(chosen)}] {p['name']} ... skipped ({p['chapter']} and its tools are unchanged since this piece last passed)", flush=True)
            done.append((p["name"], True, 0.0, "skipped"))
            continue
        kill_leftovers()
        log_path = LOGS / f"{n:02d}-{re.sub(r'[^a-z0-9]+', '-', p['name'].lower()).strip('-')}.log"
        print(f"[{n}/{len(chosen)}] {p['name']} ...", end=" ", flush=True)
        t0 = time.time()
        ok, why = run_piece(p, log_path)
        dt = time.time() - t0
        kill_leftovers()
        done.append((p["name"], ok, dt, ""))
        print(("pass" if ok else "FAIL") + f"  ({fmt(dt)})", flush=True)
        if ok and key:
            state.setdefault("pieces", {})[p["name"]] = key
            save_state(state)
        if not ok:
            print(f"\nSTOPPED at piece {n} of {len(chosen)}: {p['name']}\n  why:  {why}\n  log:  {log_path.relative_to(REPO)}\n  last lines:\n{tail_of(log_path)}\n")
            break
    shutil.rmtree(CHROME_RUN, ignore_errors=True)
    print("\nSummary")
    for name, ok, dt, note in done:
        print(f"  {'skip' if note else 'pass' if ok else 'FAIL'}  {'' if note else fmt(dt):>10}  {name}")
    for p in chosen[first - 1 + len(done):]:
        print(f"  not run             {p['name']}")
    passed = all(ok for _, ok, _, _ in done) and first - 1 + len(done) == len(chosen)
    skipped = sum(1 for d in done if d[3])
    if passed and smoke and first == 1:
        state["smoke"] = {"inputs": smoke_inputs, "at": time.strftime("%Y-%m-%d %H:%M")}
        save_state(state)
    print(f"\n{label}: {'all ' + str(len(done)) + ' pieces passed' + (f' ({skipped} skipped, unchanged)' if skipped else '') if passed else 'FAILED'} in {fmt(time.time() - started)}")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
