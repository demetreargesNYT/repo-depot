"""Chapter 3's disco ball, saved so it can be checked and restored exactly (Demetre, 2026-11-03).

    python3 chapters/ch3/scripts/ch3_disco.py save       saves the disco ball's pieces and timelines from chapters/ch3/scene.rml
    python3 chapters/ch3/scripts/ch3_disco.py check      says whether the scene's disco ball is still exactly the saved one
    python3 chapters/ch3/scripts/ch3_disco.py restore    puts the saved disco ball back

The disco ball is the "Chapter 3 Disco Ball" group and everything inside it (the hanging group, the Line, the facets, Burst_01 and
the sparkle copies), every animation's keys on any of those elements (the drop, the facet spin, the sparkles, the swing), and the
length of each animation that keys it. The text of each piece is kept exactly as it is in the file.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
import json
import re
import sys

from rml_edit import Doc
from rml_read import chapter_dir

SCENE = chapter_dir("ch3") / "scene.rml"
SAVED = chapter_dir("ch3") / "disco-saved.json"
DISCO = "9:689"
ALIAS = {"Chapter 3 Disco Loop": "Chapter 3 Loop"}      # 2026-11-05: the loop moved to its own layer; the keys and the length are the same


def extract(doc):
    i = doc.idx(DISCO)
    j = doc.end(i)
    piece = doc.lines[i:j + 1]
    ids = set(re.findall(r'\bid="([^"]+)"', "\n".join(piece)))
    anims = {}
    for a, l in enumerate(doc.lines):
        m = re.match(r'\s*<LinearAnimation\b.*\bname="([^"]+)"', l)
        if not m:
            continue
        if "</LinearAnimation>" in l:                 # a one-line pose (the colour poses): it must not key the disco ball
            assert not set(re.findall(r'objectId="([^"]+)"', l)) & ids, m.group(1)
            continue
        b = doc.end(a)
        blocks = []
        k = a + 1
        while k < b:
            mo = re.match(r'\s*<KeyedObject\b[^>]*\bobjectId="([^"]+)"', doc.lines[k])
            if mo:
                e = doc.end(k)
                if mo.group(1) in ids:
                    blocks.append(doc.lines[k:e + 1])
                k = e + 1
            else:
                k += 1
        if blocks:
            dur = re.search(r'duration="(\d+)"', l)
            anims[ALIAS.get(m.group(1), m.group(1))] = {"duration": dur.group(1) if dur else None, "blocks": blocks}
    return {"piece": piece, "anims": anims}


def main(cmd):
    doc = Doc(SCENE)
    if cmd == "save":
        SAVED.parent.mkdir(parents=True, exist_ok=True)
        SAVED.write_text(json.dumps(extract(doc)))
        d = extract(doc)
        print(f"saved the disco ball: {len(d['piece'])} lines of pieces, keys in {len(d['anims'])} animations "
              f"({sum(len(v['blocks']) for v in d['anims'].values())} keyed objects) to {SAVED}")
        return 0
    saved = json.loads(SAVED.read_text())
    now = extract(doc)
    if cmd == "check":
        diffs = []
        if now["piece"] != saved["piece"]:
            diffs.append("its pieces")
        for name in sorted(set(saved["anims"]) | set(now["anims"])):
            a, b = saved["anims"].get(name), now["anims"].get(name)
            if a is None or b is None or a["blocks"] != b["blocks"]:
                diffs.append(f"its keys in {name}")
            elif a["duration"] != b["duration"]:
                diffs.append(f"the length of {name} ({a['duration']} frames saved, {b['duration']} now)")
        print("the disco ball is exactly as saved" if not diffs else "the disco ball differs from the saved one: " + "; ".join(diffs))
        return 1 if diffs else 0
    if cmd == "restore":
        i = doc.idx(DISCO)
        doc.lines[i:doc.end(i) + 1] = saved["piece"]
        for name, v in saved["anims"].items():
            if name == "Chapter 3 Loop" and any('name="Chapter 3 Disco Loop"' in l for l in doc.lines):
                name = "Chapter 3 Disco Loop"
            a, b = doc.anim(name)
            ids = {re.search(r'objectId="([^"]+)"', blk[0]).group(1) for blk in v["blocks"]}
            for oid in ids:
                doc.drop_object(name, oid)
            a, b = doc.anim(name)
            doc.lines[b:b] = [l for blk in v["blocks"] for l in blk]
            if v["duration"]:
                doc.set_duration(name, int(v["duration"]))
        doc.save()
        print("restored the disco ball")
        return 0
    raise SystemExit(__doc__)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else ""))
