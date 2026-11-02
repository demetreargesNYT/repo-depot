"""Compare a room with an earlier committed version of itself, frame by frame, and build a side-by-side viewer.

    python3 tools/compare_room.py ch2 wordle                     the room's loop now against the last commit (HEAD)
    python3 tools/compare_room.py ch2 wordle --rev 158faed       against any commit, tag or branch
    python3 tools/compare_room.py ch1 start --part intro         the intro (frames 1 to 191) instead of the loop
    python3 tools/compare_room.py ch1 chapter-1-card-1 --frames 190-400    an exact range of scene frames (60 per second)
    python3 tools/compare_room.py ch2 wordle --workers 8

What is in Rive now is the current version of a room, so this answers "what did my change do?", not "does it match a source".
It renders the committed `scene.rml` and the working copy with the scene set from outside, at the same moments, and counts
the pixels that differ by more than THRESHOLD (ignoring the 30 px border and the floor-line rows, which the shared backdrop
draws). Frames are counted from the moment the scene is set: the intro is frames 1 to 191, and the loop starts at frame 192
(3.2 s). Output (deliver/ is not in git):

    deliver/compare/<room>/index.html   a player: before | now | where they differ, with a scrubber
    deliver/compare/<room>/summary.json what the numbers say
    deliver/compare/index.html          links to every room compared so far
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

import room_timing
from rml_read import REPO, Scene, chapter_dir

import xml.etree.ElementTree as ET

RIVE = os.path.expanduser("~/.rive/bin/rive")
INTRO_FRAMES = room_timing.INTRO_FRAMES
THRESHOLD = 12
BORDER = 30
FLOOR_ROWS = (709, 715)
CROP = (330, 250, 1170, 860)
SCALE = 0.6
CACHE = REPO / ".cache" / "view"


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def project(chapter, name, scene_text=None):
    """A copy of the chapter to render from (so parallel renders do not share a build folder), with `scene_text` as its
    scene.rml when given (an earlier version). A room the file opens on (Loading) starts looping at once, so with the scene
    set from outside it would show under every frame; it is hidden, because the comparison is of one room at a time."""
    d = CACHE / f"{name}-{chapter}"
    if d.exists():
        shutil.rmtree(d)
    shutil.copytree(chapter_dir(chapter), d, ignore=shutil.ignore_patterns("build"))
    if scene_text is not None:
        (d / "scene.rml").write_text(scene_text)
    manifest = Scene(d / "scene.rml").manifest
    opening = {x["room"] + " Room" for x in manifest["scenes"] if x.get("kind") == "loading" and "room" in x}
    if any(x.get("kind") == "loading" and "room" not in x for x in manifest["scenes"]):
        opening.add("Start Room")                     # Loading is drawn by the Start room
    if opening:
        tree = ET.parse(d / "scene.rml")
        for n in tree.getroot().iter("Node"):
            if n.get("name") in opening:
                n.set("hidden", "true")
        tree.write(d / "scene.rml", encoding="utf-8")
    return d


def committed_scene(chapter, rev):
    """The chapter's scene.rml as it was at `rev`."""
    path = f"./chapters/{chapter}/scene.rml"
    r = subprocess.run(["git", "show", f"{rev}:{path}"], cwd=REPO, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"could not read {path} at {rev}:\n{r.stderr}")
    return r.stdout


def render(proj, out, frames, scene):
    args = [RIVE, str(proj), f"--data=scene={scene}", f"--screenshot={out}", f"--advance={frames}"]
    for _ in range(4):                                  # a render can fail when the machine is busy: try again
        Path(out).unlink(missing_ok=True)
        subprocess.run(args, capture_output=True)
        if Path(out).exists():
            return Image.open(out).convert("RGB")
    raise SystemExit(f"could not render {out}")


def differing(a, b):
    d = ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v > THRESHOLD else 0)
    dr = ImageDraw.Draw(d)
    w, h = d.size
    for box in ((0, 0, w, BORDER - 1), (0, h - BORDER, w, h), (0, 0, BORDER - 1, h), (w - BORDER, 0, w, h), (0, FLOOR_ROWS[0], w, FLOOR_ROWS[1])):
        dr.rectangle(box, fill=0)
    return d


def frame_range(args, scene_entry, scene):
    """The scene frames to render: --frames, or --part (the loop by default)."""
    if args.frames:
        a, b = (int(x) for x in args.frames.split("-"))
        return a, b
    room = scene_entry.get("room")
    loop = scene.animations.get(f"{room} Loop")
    if args.part == "intro" or loop is None:
        return 1, INTRO_FRAMES - 1
    n = round(room_timing.length(loop) * room_timing.FPS)
    return INTRO_FRAMES + 1, INTRO_FRAMES + n - 1


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("chapter", help="ch1, ch2 or ch3")
    ap.add_argument("scene", help="the scene name, e.g. wordle, start, chapter-1-card-1, chapter-4")
    ap.add_argument("--rev", default="HEAD", help="the version to compare against (a commit, tag or branch; default HEAD)")
    ap.add_argument("--part", choices=("loop", "intro"), default="loop")
    ap.add_argument("--frames", help="an exact range of scene frames, e.g. 190-400")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args(argv)
    now_scene = Scene(chapter_dir(args.chapter) / "scene.rml")
    entry = next((s for s in now_scene.manifest["scenes"] if s["name"] == args.scene), None)
    if entry is None:
        raise SystemExit(f"{args.chapter} has no scene {args.scene!r}: {[s['name'] for s in now_scene.manifest['scenes']]}")
    first, last = frame_range(args, entry, now_scene)
    before, now = project(args.chapter, "before", committed_scene(args.chapter, args.rev)), project(args.chapter, "now")
    title = f"{entry.get('room') or args.scene} ({args.chapter} {args.scene}) vs {args.rev}"
    out = REPO / "deliver" / "compare" / slug(f"{args.chapter} {args.scene} {args.rev}")
    work = CACHE / f"frames-{slug(title)}"
    for d in (out, work):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
    frames = list(range(first, last + 1))

    def one(frame):
        a = render(before, work / f"b{frame}.png", frame, args.scene)
        b = render(now, work / f"n{frame}.png", frame, args.scene)
        d = differing(a, b)
        count = sum(1 for p in d.getdata() if p)
        faded = Image.blend(b, Image.new("RGB", b.size, "white"), 0.6)
        faded.paste(Image.new("RGB", b.size, (230, 0, 0)), mask=d)
        panels = [im.crop(CROP) for im in (a, b, faded)]
        w, h = panels[0].size
        w2, h2 = int(w * SCALE), int(h * SCALE)
        sheet = Image.new("RGB", (w2 * 3 + 8, h2), "white")
        for i, p in enumerate(panels):
            sheet.paste(p.resize((w2, h2), Image.LANCZOS), (i * (w2 + 4), 0))
        sheet.save(out / f"f{frame:04d}.jpg", quality=84)
        for f in (work / f"b{frame}.png", work / f"n{frame}.png"):
            f.unlink()
        return frame, count, d.getbbox()

    print(f"{title}: rendering scene frames {first} to {last} of both ({args.workers} at a time) ...", flush=True)
    with ThreadPoolExecutor(args.workers) as pool:
        rows = sorted(pool.map(one, frames))
    shutil.rmtree(work, ignore_errors=True)
    bad = [(f, c, b) for f, c, b in rows if c]
    runs, start, prev = [], None, None
    for f, c, _ in bad:
        if start is None or f != prev + 1:
            if start is not None:
                runs.append((start, prev))
            start = f
        prev = f
    if start is not None:
        runs.append((start, prev))
    w2, h2 = int((CROP[2] - CROP[0]) * SCALE), int((CROP[3] - CROP[1]) * SCALE)
    summary = {"room": title, "frames": len(frames), "first": first, "last": last, "differing_frames": len(bad),
               "worst_pixels": max((c for _, c, _ in bad), default=0), "differing_runs": runs,
               "counts": {str(f): c for f, c, _ in rows}}
    (out / "summary.json").write_text(json.dumps(summary))
    (out / "index.html").write_text(player(title, first, last, summary["counts"], (w2 * 3 + 8, h2), w2 + 4))
    index(out.parent)
    print(f"{title}: {len(bad)} of {len(frames)} frames differ (worst {summary['worst_pixels']} px); runs {runs or 'none'}")
    print(f"viewer: {out / 'index.html'}")
    return 0


def player(title, first, last, counts, size, col):
    return f"""<!doctype html><meta charset="utf-8"><title>{title}</title>
<style>body{{font:14px system-ui;margin:20px;background:#f4f4f2}}h1{{font-size:18px;margin:0 0 4px}}.row{{display:flex;gap:10px;align-items:center;margin:10px 0}}
img{{display:block;max-width:100%;border:1px solid #ccc;background:#fff}}.cap{{display:flex;width:{size[0]}px;font-weight:600}}.cap div{{width:{col}px}}
input[type=range]{{width:520px}}button{{padding:4px 12px}}a{{color:#06c}}</style>
<h1>{title}: the committed version (left), the room now (middle), where they differ (right, red)</h1>
<div><a href="../index.html">all comparisons</a> &nbsp; Scene frame <b id=fr>{first}</b> (<b id=sec>0</b> s) &nbsp; differing pixels: <b id=cnt>0</b>
&nbsp;<small>(the floor line and the 30 px border are masked: the shared backdrop draws those)</small></div>
<div class=row><button id=play>Play</button><input id=sl type=range min={first} max={last} value={first}><label><input type=checkbox id=slow> quarter speed</label></div>
<div class=cap><div>Before</div><div>Now</div><div>Difference</div></div>
<img id=im width={size[0]}>
<script>
const counts={json.dumps(counts)};let f={first},playing=false,last=0;const im=document.getElementById('im'),sl=document.getElementById('sl');
function show(n){{f=n;im.src='f'+String(n).padStart(4,'0')+'.jpg';fr.textContent=n;sec.textContent=(n/60).toFixed(2);cnt.textContent=counts[n];sl.value=n}}
sl.oninput=()=>show(+sl.value);play.onclick=()=>{{playing=!playing;play.textContent=playing?'Pause':'Play'}};
function tick(t){{if(playing){{const step=1000/(slow.checked?15:60);if(t-last>=step){{last=t;show(f>={last}?{first}:f+1)}}}}requestAnimationFrame(tick)}}
show({first});requestAnimationFrame(tick);
</script>"""


def index(folder):
    rows = []
    for d in sorted(p for p in folder.iterdir() if (p / "summary.json").exists()):
        s = json.loads((d / "summary.json").read_text())
        if "first" not in s:                    # a viewer from the old tool, which compared with the illustrator's file
            continue
        runs = ", ".join(f"{a}-{b}" if a != b else str(a) for a, b in s["differing_runs"]) or "none"
        rows.append(f'<tr><td><a href="{d.name}/index.html">{s["room"]}</a></td><td>{s["first"]}-{s["last"]}</td><td>{s["differing_frames"]}</td>'
                    f'<td>{s["worst_pixels"]}</td><td>{runs}</td></tr>')
    (folder / "index.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>Room comparisons</title><style>body{font:14px system-ui;margin:20px}td,th{padding:4px 12px;text-align:left}</style>'
        "<h1>Rooms compared with an earlier version</h1><table><tr><th>Room</th><th>Scene frames</th><th>Differing</th><th>Worst (px)</th><th>Differing frames</th></tr>"
        + "".join(rows) + "</table>")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
