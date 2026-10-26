"""Interrupted-tap test: no browser, no wall-clock timing.

    python3 tools/tap_test.py ch2                      both orders, tap 2 at 0.5, 1.5, 2.5 and 3.0 s into the intro
    python3 tools/tap_test.py ch2 --times 0.5 --orders cw --keep /tmp/frames

Scenario: from the opener, tap 1 starts the first game at t = 0. Tap 2 starts the second game T seconds later,
while the first game's intro is still running.

The CLI can set the view model only before the scene runs, so tap 2 is emulated in a throwaway copy of the
project: the two transitions that tap 2 would fire (first game's Shown -> Outro, second game's Waiting -> Intro)
are given an exit time of T seconds instead of their scene condition. Same states, same layers, same moment.

Every frame is rendered three times: as it is, with the first game's room and lockup hidden, and with both games
hidden. The rooms share one backdrop that fades in colour, so there is no wall edge to measure from; instead:
  * the arriving room draws on top: wherever the second game draws (second-only render differs from the bare
    backdrop), the full render must show the second game's pixels, not the first game's;
  * the first game is gone from 1.7 s after tap 2 (the pan is over): the full render equals the second-only one.
"""
import copy
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageChops
from rml_read import chapter_dir

RIVE = os.path.expanduser("~/.rive/bin/rive")
GAMES = {1: "Wordle", 2: "Connections"}
THRESHOLD = 12            # per-channel difference that counts as "drawn"
SETTLED = 1.7             # s after tap 2: the 1.55 s pan is over
DTS = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.5, 3.4]   # s after tap 2


def prepare(src, first, second, T, hide):
    """Copy the project with tap 2 emulated at T seconds. Returns the project dir."""
    dst = Path(tempfile.mkdtemp()) / "p"
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("build"))
    tree = ET.parse(dst / "scene.rml")
    root = tree.getroot()
    ab = root.find("Artboard")
    anims = {a.get("name"): a for a in ab.iter("LinearAnimation")}
    layers = {l.get("name"): l for l in ab.find("StateMachine").findall("StateMachineLayer")}
    frames = str(round(T * 60))
    top = [max(int(e.get("id").split(":")[1]) for e in root.iter() if e.get("id", "").startswith("1:"))]

    def new_id():
        top[0] += 1
        return "1:%d" % top[0]

    def at_exit_time(transition):
        for c in list(transition):
            if c.tag == "TransitionViewModelCondition":
                transition.remove(c)
        transition.set("enableExitTime", "true")
        transition.set("exitTimeIsPercetange", "true")
        transition.set("exitTime", "100")

    # first game's Exit layer: Shown (plays the Home pose) -> Outro fires after T seconds, not on "scene != n"
    shown = next(st for st in layers[f"{first} Exit"].findall("AnimationState")
                 if any(c.get("opValue") == "notEqual" for tr in st.findall("StateTransition") for c in tr.findall("TransitionViewModelCondition")))
    hold = copy.deepcopy(anims[f"{first} Home"])
    for e in hold.iter():                     # ids must be unique, so every copied element gets a new one
        if e.get("id"):
            e.set("id", new_id())
    hold.set("name", f"{first} Hold")
    hold.set("duration", frames)
    ab.append(hold)
    shown.set("animationId", hold.get("id"))
    at_exit_time(shown.find("StateTransition"))

    # second game's layer: Waiting -> Intro fires after T seconds, not on "scene == n"
    waiting = next(st for st in layers[second].findall("AnimationState") if st.find("StateTransition") is not None)
    next(a for a in ab.iter("LinearAnimation") if a.get("id") == waiting.get("animationId")).set("duration", frames)
    at_exit_time(waiting.find("StateTransition"))

    for n in ab.iter("Node"):
        if n.get("name") in {f"{g} {part}" for g in hide for part in ("Room", "Lockup")}:
            n.set("hidden", "true")
    tree.write(dst / "scene.rml", encoding="utf-8")
    return dst


def render(project, scene, seconds, out):
    r = subprocess.run([RIVE, str(project), f"--data=scene={scene}", f"--screenshot={out}", f"--advance={seconds}s"],
                       capture_output=True, text=True)
    if not Path(out).exists():
        raise SystemExit("render failed:\n" + r.stdout + r.stderr)
    return Image.open(out).convert("RGB")


def mask(a, b):
    return ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v > THRESHOLD else 0)


def lit(img):
    return img.histogram()[255]


def run_case(chapter, order, T, keep):
    first, second = (GAMES[1], GAMES[2]) if order == "wc" else (GAMES[2], GAMES[1])
    scene = 1 if order == "wc" else 2
    src = chapter_dir(chapter)
    full, second_only, bare = (prepare(src, first, second, T, h) for h in ((), (first,), (first, second)))
    tmp = Path(tempfile.mkdtemp())
    rows = []
    try:
        for dt in DTS:
            tau = round(T + dt, 3)
            A = render(full, scene, tau, tmp / "a.png")
            B = render(second_only, scene, tau, tmp / "b.png")
            D = render(bare, scene, tau, tmp / "d.png")
            first_drawn = mask(A, B)                     # what the first game adds to the frame
            second_art = mask(B, D)                      # where the second game draws
            over = ImageChops.multiply(first_drawn, second_art)
            rows.append({"dt": dt, "drawn": lit(first_drawn), "bbox": first_drawn.getbbox(), "second": lit(second_art),
                         "over": lit(over), "over_bbox": over.getbbox()})
            if keep:
                Path(keep).mkdir(parents=True, exist_ok=True)
                A.save(Path(keep) / f"{order}-{T}-{dt}.png")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        for d in (full, second_only, bare):
            shutil.rmtree(d.parent, ignore_errors=True)
    return first, second, rows


def main(argv):
    chapter = argv[0] if argv and not argv[0].startswith("--") else "ch2"
    flag = lambda n, d: argv[argv.index(n) + 1] if n in argv else d
    times = [float(t) for t in flag("--times", "0.5,1.5,2.5,3.0").split(",")]
    orders = flag("--orders", "wc,cw").split(",")
    keep = flag("--keep", None)
    failures = 0
    for order in orders:
        for T in times:
            first, second, rows = run_case(chapter, order, T, keep)
            over = [r for r in rows if r["over"]]
            stale = [r for r in rows if r["dt"] >= SETTLED and r["drawn"]]
            ok = not over and not stale
            failures += not ok
            print(f'{"PASS" if ok else "FAIL"}  {first:11s} then {second:11s}  tap 2 at {T:3.1f} s   '
                  f'frames with old art over the new room\'s art: {len(over)} of {len(rows)}   old art still on stage after {SETTLED} s: {len(stale)}')
            for r in over[:3] + stale[:2]:
                print(f'        +{r["dt"]:.2f} s: old art spans {r["bbox"]}; {r["over"]} px of it cover the new room\'s art, within {r["over_bbox"]}')
    print(f"\n{'all cases passed' if not failures else str(failures) + ' case(s) failed'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
