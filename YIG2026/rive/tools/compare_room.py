"""Compare a room's loop with the illustrator's, frame by frame, and build a side-by-side viewer.

    python3 tools/compare_room.py tools/rooms/strands.json          renders every loop frame of both, writes deliver/compare/strands/
    python3 tools/compare_room.py tools/rooms/strands.json --workers 8

The illustrator's artboard plays its loop from frame 0; our room plays it 192 frames (3.2 s) after the scene is set,
when its intro ends. Frame N of one is rendered next to frame N + 192 of the other. Pixels that differ by more than
THRESHOLD are counted, ignoring what our shared backdrop draws differently on purpose: the 30 px border (the source
artboard has rounded corners) and the floor line. Output (deliver/ is not in git):

    deliver/compare/<room>/index.html   a player: illustrator | ours | where they differ, with a scrubber
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

import import_room
from rml_read import REPO, Scene, chapter_dir

import xml.etree.ElementTree as ET

RIVE = os.path.expanduser("~/.rive/bin/rive")
INTRO_FRAMES = 192
THRESHOLD = 12
BORDER = 30
FLOOR_ROWS = (709, 715)
CROP = (330, 250, 1170, 860)
SCALE = 0.6
CACHE = REPO / ".cache" / "view"


def slug(room):
    return re.sub(r"[^a-z0-9]+", "-", room.lower()).strip("-")


def mute(project, artboard, animations=(), hide=()):
    """In a throwaway copy: empty the named animations of `artboard` (they still play, but key nothing) and hide the named
    nodes. Used to compare only what a room copied: a source's one-off ball journey, and the stand-in ball we put in its
    place, are taken out of both sides."""
    if not animations and not hide:
        return
    path = Path(project) / "scene.rml"
    tree = ET.parse(path)
    for ab in tree.getroot().findall("Artboard"):
        if artboard and ab.get("name") != artboard:
            continue
        for a in ab.iter("LinearAnimation"):
            if a.get("name") in animations:
                for ko in a.findall("KeyedObject"):
                    a.remove(ko)
        for n in ab.iter():
            if n.get("name") in hide:
                n.set("hidden", "true")
    tree.write(path, encoding="utf-8")


def source_project(artboard):
    """A throwaway copy of the illustrator's pull whose main artboard is `artboard` (the pull itself is never edited)."""
    scene = import_room.ensure_illustrator()
    d = CACHE / artboard
    if not d.exists():
        d.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["cp", "-Rc", str(scene.parent), str(d)], check=True)
    (d / "scene.rml").unlink(missing_ok=True)
    shutil.copyfile(scene, d / "scene.rml")             # always the pull as it is, never a leftover edit
    (d / "rive.yaml").write_text(f'name: view\nmain: "{artboard}"\n')
    return d


def our_project(chapter):
    """A copy of the chapter to render from, so parallel renders do not share a build folder."""
    d = CACHE / f"ours-{chapter}"
    if d.exists():
        shutil.rmtree(d)
    shutil.copytree(chapter_dir(chapter), d, ignore=shutil.ignore_patterns("build"))
    # a room the file opens on (Loading) starts looping at once, so with the scene set from outside it would show under
    # every frame; the comparison is of one room at a time
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


def render(project, out, frames, scene=None, data=()):
    args = [RIVE, str(project), f"--screenshot={out}", f"--advance={frames}"]
    if scene is not None:
        args.insert(2, f"--data=scene={scene}")
    args[2:2] = [f"--data={d}" for d in data]
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


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config")
    ap.add_argument("--chapter", default="ch2")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--compare", help="one of the config's named comparisons (cfg compares), e.g. a Chapter 4 fireworks set")
    args = ap.parse_args(argv)
    cfg = json.loads(Path(args.config).read_text())
    ill = ET.parse(import_room.ensure_illustrator()).getroot()
    src_ab = next(a for a in ill.findall("Artboard") if a.get("name") == cfg["artboard"])
    if cfg.get("loops"):                       # merged loops: the loop is as long as the config says
        n = cfg["loop_frames"]
    else:
        loop = next(a for a in src_ab.findall("LinearAnimation") if a.get("name") == cfg["loop"])
        n = int(loop.get("duration", 60))
        if loop.get("enableWorkArea") == "true":   # the source plays only its work area
            n = int(loop.get("workEnd", n))
    w2, h2 = int((CROP[2] - CROP[0]) * SCALE), int((CROP[3] - CROP[1]) * SCALE)
    # what to take out of both sides, and view model values to set on ours: the config's "compare", or one of its "compares"
    ap_cmp = dict(cfg["compares"][args.compare], label=args.compare) if args.compare else cfg.get("compare", {})
    artboard = ap_cmp.get("artboard", cfg["artboard"])
    src, ours = source_project(artboard), our_project(args.chapter)
    mute(src, artboard, ap_cmp.get("mute_source", []), ap_cmp.get("hide_source", []))
    mute(ours, None, (), ap_cmp.get("hide_ours", []))
    scene = cfg["scene"]            # a scene name, or (in the older configs) its place in the Scene enum
    if isinstance(scene, int):
        scene = Scene(chapter_dir(args.chapter) / "scene.rml").scene_names()[scene]
    label = cfg["room"] + (f" {ap_cmp['label']}" if ap_cmp.get("label") else "")
    out = REPO / "deliver" / "compare" / slug(label)
    work = CACHE / f"frames-{slug(label)}"
    for d in (out, work):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)

    def one(frame):
        a = render(src, work / f"s{frame}.png", frame)
        b = render(ours, work / f"o{frame}.png", frame + INTRO_FRAMES, scene, ap_cmp.get("data", []))
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
        sheet.save(out / f"f{frame:03d}.jpg", quality=84)
        for f in (work / f"s{frame}.png", work / f"o{frame}.png"):
            f.unlink()
        return frame, count, d.getbbox()

    print(f"{cfg['room']}: rendering frames 1..{n - 1} of both ({args.workers} at a time) ...", flush=True)
    with ThreadPoolExecutor(args.workers) as pool:
        rows = sorted(pool.map(one, range(1, n)))
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
    summary = {"room": cfg["room"], "artboard": cfg["artboard"], "frames": n - 1, "differing_frames": len(bad),
               "worst_pixels": max((c for _, c, _ in bad), default=0), "differing_runs": runs,
               "counts": {str(f): c for f, c, _ in rows}}
    (out / "summary.json").write_text(json.dumps(summary))
    (out / "index.html").write_text(player(cfg["room"], n - 1, summary["counts"], (w2 * 3 + 8, h2), (w2 + 4)))
    index(out.parent)
    print(f"{cfg['room']}: {len(bad)} of {n - 1} frames differ (worst {summary['worst_pixels']} px); runs {runs or 'none'}")
    print(f"viewer: {out / 'index.html'}")
    return 0


def player(room, last, counts, size, col):
    return f"""<!doctype html><meta charset="utf-8"><title>{room}: illustrator vs ours</title>
<style>body{{font:14px system-ui;margin:20px;background:#f4f4f2}}h1{{font-size:18px;margin:0 0 4px}}.row{{display:flex;gap:10px;align-items:center;margin:10px 0}}
img{{display:block;max-width:100%;border:1px solid #ccc;background:#fff}}.cap{{display:flex;width:{size[0]}px;font-weight:600}}.cap div{{width:{col}px}}
input[type=range]{{width:520px}}button{{padding:4px 12px}}a{{color:#06c}}</style>
<h1>{room}: the illustrator's loop (left), our room (middle), where they differ (right, red)</h1>
<div><a href="../index.html">all rooms</a> &nbsp; Loop frame <b id=fr>1</b> of {last} &nbsp; differing pixels: <b id=cnt>0</b>
&nbsp;<small>(the floor line and the 30 px border are masked: our shared backdrop draws those)</small></div>
<div class=row><button id=play>Play</button><input id=sl type=range min=1 max={last} value=1><label><input type=checkbox id=slow> quarter speed</label></div>
<div class=cap><div>Illustrator</div><div>Ours</div><div>Difference</div></div>
<img id=im width={size[0]}>
<script>
const counts={json.dumps(counts)};let f=1,playing=false,last=0;const im=document.getElementById('im'),sl=document.getElementById('sl');
function show(n){{f=n;im.src='f'+String(n).padStart(3,'0')+'.jpg';fr.textContent=n;cnt.textContent=counts[n];sl.value=n}}
sl.oninput=()=>show(+sl.value);play.onclick=()=>{{playing=!playing;play.textContent=playing?'Pause':'Play'}};
function tick(t){{if(playing){{const step=1000/(slow.checked?15:60);if(t-last>=step){{last=t;show(f>=LASTFRAME?1:f+1)}}}}requestAnimationFrame(tick)}}
show(1);requestAnimationFrame(tick);
</script>""".replace("LASTFRAME", str(last))


def index(folder):
    rows = []
    for d in sorted(p for p in folder.iterdir() if (p / "summary.json").exists()):
        s = json.loads((d / "summary.json").read_text())
        runs = ", ".join(f"{a}-{b}" if a != b else str(a) for a, b in s["differing_runs"]) or "none"
        rows.append(f'<tr><td><a href="{d.name}/index.html">{s["room"]}</a></td><td>{s["frames"]}</td><td>{s["differing_frames"]}</td>'
                    f'<td>{s["worst_pixels"]}</td><td>{runs}</td></tr>')
    (folder / "index.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>Loop comparisons</title><style>body{font:14px system-ui;margin:20px}td,th{padding:4px 12px;text-align:left}</style>'
        "<h1>Rooms compared with the illustrator's loop</h1><table><tr><th>Room</th><th>Frames</th><th>Differing</th><th>Worst (px)</th><th>Differing frames</th></tr>"
        + "".join(rows) + "</table>")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
