"""The one command to run after every finesse change:  npm run finesse 1 "chapter-1-card-4"

    npm run finesse <ch> "<room>" [--open]

<ch> is 1, 2, 3 or ch1, ch2, ch3; <room> is the scene's name (chapter-1-card-4, wordle) or the room's (Chapter 1 Card 4, The Mini).
It does three things and nothing else (no frame renders, no smoke):
  1. the rule checks for that chapter only (npm run check <ch>)
  2. the ball's physics and jitter check for that room (tools/ball_speed.py <ch> "<room>" --contacts); flags accepted on purpose
     (tools/ball_speed_accepted.json) are shown but don't fail
  3. the /experience address that opens on that room with the Finesse panel on, so Replay room is one click away. The review
     server is started if it isn't running; --open also opens the address in the browser.
Each step has a time limit and prints as it goes. Exit code 1 if a step fails.
"""
import json
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HARNESS = "http://127.0.0.1:8765"
LIMITS = {"check": 300, "ball": 120}      # seconds per step

# what each scene needs from the review page (the same choices as the Jump to menu in harness/experience.html)
NEEDS = {
    "2:to-chapter-3": {"flow": "anon"},
    "2:bridge": {"flow": "sub", "player": "wordle-only"},
    "3:ad": {"flow": "sub", "player": "wordle-only"},
}


def chapter_of(arg):
    ch = arg if arg.startswith("ch") else f"ch{arg}"
    if not (REPO / "chapters" / ch / "chapter.json").exists():
        sys.exit(f"no chapter {arg!r}: use 1, 2, 3 (or ch1, ch2, ch3)")
    return ch


def scene_of(ch, arg):
    """(scene name, room name or None) for a scene or room name, matched without regard to case."""
    scenes = json.loads((REPO / "chapters" / ch / "chapter.json").read_text())["scenes"]
    for s in scenes:
        if arg.lower() in (s["name"].lower(), (s.get("room") or "").lower()):
            return s["name"], s.get("room")
    names = ", ".join(s["name"] for s in scenes)
    sys.exit(f"no scene or room {arg!r} in {ch}; its scenes are: {names}")


def step(label, cmd, limit):
    """Runs one step, streaming its output; returns (ok, seconds)."""
    print(f"\n== {label}   ({' '.join(cmd)}; limit {limit} s)", flush=True)
    t0 = time.time()
    proc = subprocess.Popen(cmd, cwd=REPO)
    try:
        rc = proc.wait(timeout=limit)
    except subprocess.TimeoutExpired:
        proc.kill()
        print(f"FAIL  {label}: hit the {limit} s limit", flush=True)
        return False, time.time() - t0
    return rc == 0, time.time() - t0


def up():
    try:
        urllib.request.urlopen(HARNESS + "/", timeout=2)
        return True
    except Exception:
        return False


def ensure_server():
    if up():
        return "the review server is running"
    log = REPO / ".cache" / "scratch.nosync" / "harness-server.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    subprocess.Popen(["node", "serve.mjs"], cwd=REPO / "harness", stdout=open(log, "w"), stderr=subprocess.STDOUT, start_new_session=True)
    for _ in range(50):
        if up():
            return "started the review server (it stays running)"
        time.sleep(0.2)
    return f"could not start the review server; see {log.relative_to(REPO)}"


def address(ch, scene):
    goto = f"{ch[2:]}:{scene}"
    q = {"flow": "sub", "player": "all-seven", "size": "window"}       # all-seven qualifies for every Chapter 2 game
    q.update(NEEDS.get(goto, {}))
    q.update({"finesse": "1", "goto": goto})
    return f"{HARNESS}/experience?{urllib.parse.urlencode(q, safe=':')}"


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 2:
        sys.exit(__doc__)
    t0 = time.time()
    ch = chapter_of(args[0])
    scene, room = scene_of(ch, args[1])
    print(f"finesse: {ch}, scene {scene}" + (f" (room {room!r})" if room else " (an empty room)"), flush=True)
    results = []
    ok, dt = step(f"rule checks for {ch}", [sys.executable, "tools/check.py", ch], LIMITS["check"])
    results.append((f"rule checks {ch}", ok, dt))
    if room is None:
        print(f"\n== the ball's check: skipped ({scene} is an empty room, with no ball)")
    else:
        ok, dt = step(f"the ball's physics and jitter in {room}", [sys.executable, "tools/ball_speed.py", ch, room, "--contacts"], LIMITS["ball"])
        results.append((f"ball check {room}", ok, dt))
    print(f"\n== review\n{ensure_server()}")
    url = address(ch, scene)
    print(f"open: {url}\n(the Finesse panel is on; Replay room plays the intro again)")
    if "--open" in argv:
        subprocess.run(["open", url])
    print("\nSummary")
    for name, ok, dt in results:
        print(f"  {'pass' if ok else 'FAIL'}  {dt:5.1f} s  {name}")
    failed = [n for n, ok, _ in results if not ok]
    print(f"\nfinesse: {'all passed' if not failed else 'FAILED: ' + ', '.join(failed)} in {time.time() - t0:.1f} s")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
