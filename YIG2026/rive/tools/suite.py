"""Run the tests in short pieces, one at a time.

    npm run suite       every test, once, before a Rive push or an engineering handoff
    npm run smoke       the short set to run after a meaningful change
    python3 tools/suite.py --list [--smoke]     print the pieces and stop
    python3 tools/suite.py --from 19            start at piece 19 (resume a run that stopped there)

Both npm scripts run under `caffeinate -i`, so the Mac cannot sleep mid-run. Each piece runs alone with a 15 minute limit;
the browser tests also fail on their own, with a message, when Chrome closes or stops answering for 60 seconds. Before every
piece, the headless Chrome windows and the package web server that this suite started are killed (your own Chrome is never
touched: ours all run with a profile folder named yig-*). The run stops at the first failing piece and says which piece, why,
and where its log is. Logs are in test-logs/ (git-ignored) and are overwritten by each run.
"""
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LOGS = REPO / "test-logs"
LIMIT = 15 * 60                      # seconds per piece
HARNESS = "http://127.0.0.1:8765"    # the review server (harness/serve.mjs); the suite starts it if it isn't running and leaves it running
PACKAGE_PORT = 8900                  # the suite's own port for the unzipped-package demo, so it never touches a server of yours
PACKAGE_DIR = REPO / "deliver" / "yig-engineering-package"
PACKAGE = f"http://127.0.0.1:{PACKAGE_PORT}"

PLAYERS = ["wordle-only", "midi-only", "connections-only", "several-games", "all-seven", "none"]


def piece(name, cmd, tier="full", needs=None):
    """tier: "full" (only in npm run suite), "smoke" (only in npm run smoke) or "both"."""
    return {"name": name, "cmd": cmd, "tier": tier, "needs": needs}


def experience(url, path, flow, size, player):
    cmd = ["node", "harness/experience-test.mjs", "--flows", flow, "--sizes", size, "--players", player]
    if url:
        cmd += ["--url", url, "--path", path]
    return cmd


def pieces():
    out = []
    for ch in ("ch1", "ch2", "ch3"):
        out.append(piece(f"rule checks {ch}", ["python3", "tools/check.py", ch], tier="both"))
    out.append(piece("unit tests", ["python3", "-m", "unittest", "discover", "-s", "tools/tests"], tier="both"))
    for ch in ("ch1", "ch2", "ch3"):
        out.append(piece(f"loop motion {ch}", ["python3", "tools/loop_motion.py", ch], tier="both"))
    for ch in ("ch1", "ch2", "ch3"):
        out.append(piece(f"tap {ch}", ["python3", "tools/tap_test.py", ch]))
    for ch in ("ch1", "ch2", "ch3"):
        out.append(piece(f"back {ch}", ["python3", "tools/back_test.py", ch]))
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
    """Headless Chrome windows from our tests (their profile folders are yig-*) and our package web server."""
    for pid in sh(["pgrep", "-f", r"headless=new.*user-data-dir=[^ ]*yig-"]).split():
        if int(pid) != os.getpid():
            try:
                os.kill(int(pid), signal.SIGKILL)
            except ProcessLookupError:
                pass
    for pid in sh(["pgrep", "-f", f"http.server {PACKAGE_PORT}"]).split():
        try:
            os.kill(int(pid), signal.SIGKILL)
        except ProcessLookupError:
            pass
    for pid in sh(["pgrep", "-f", r"vite.*YIG2026/rive"]).split():     # a Vite dev server started from this repo
        try:
            os.kill(int(pid), signal.SIGKILL)
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
    subprocess.Popen([sys.executable, "-m", "http.server", str(PACKAGE_PORT), "--bind", "127.0.0.1"], cwd=PACKAGE_DIR,
                     stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
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
    with open(log_path, "w") as log:
        proc = subprocess.Popen(p["cmd"], cwd=REPO, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            rc = proc.wait(timeout=LIMIT)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
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


def main():
    smoke = "--smoke" in sys.argv
    chosen = [p for p in pieces() if p["tier"] in ("both", "smoke" if smoke else "full")]
    first = int(sys.argv[sys.argv.index("--from") + 1]) if "--from" in sys.argv else 1     # resume a run that stopped: the pieces before it are skipped
    if "--list" in sys.argv:
        for i, p in enumerate(chosen, 1):
            print(f"{i:2}. {p['name']}   {' '.join(p['cmd'])}")
        return
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
        kill_leftovers()
        log_path = LOGS / f"{n:02d}-{re.sub(r'[^a-z0-9]+', '-', p['name'].lower()).strip('-')}.log"
        print(f"[{n}/{len(chosen)}] {p['name']} ...", end=" ", flush=True)
        t0 = time.time()
        ok, why = run_piece(p, log_path)
        dt = time.time() - t0
        kill_leftovers()
        done.append((p["name"], ok, dt))
        print(("pass" if ok else "FAIL") + f"  ({fmt(dt)})", flush=True)
        if not ok:
            print(f"\nSTOPPED at piece {n} of {len(chosen)}: {p['name']}\n  why:  {why}\n  log:  {log_path.relative_to(REPO)}\n  last lines:\n{tail_of(log_path)}\n")
            break
    print("\nSummary")
    for name, ok, dt in done:
        print(f"  {'pass' if ok else 'FAIL'}  {fmt(dt):>10}  {name}")
    for p in chosen[first - 1 + len(done):]:
        print(f"  not run             {p['name']}")
    print(f"\n{label}: {'all ' + str(len(done)) + ' pieces passed' if all(ok for _, ok, _ in done) and first - 1 + len(done) == len(chosen) else 'FAILED'} in {fmt(time.time() - started)}")
    sys.exit(0 if all(ok for _, ok, _ in done) and first - 1 + len(done) == len(chosen) else 1)


if __name__ == "__main__":
    main()
