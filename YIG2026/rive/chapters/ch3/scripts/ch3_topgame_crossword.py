"""File 3's topGame value "daily" is called "crossword" (Demetre, 2026-11-05), matching the scene and the game's name.

    python3 chapters/ch3/scripts/ch3_topgame_crossword.py --write      once

Names only: the TopGame enum value keeps its id (1:9306), so every condition follows. No other enum in File 3 has a "daily" value
(Scene and Direction have none). The fireworks pose animation "Chapter 4 Fireworks daily" is renamed "Chapter 4 Fireworks crossword",
because the structure checks name those poses after the topGame values. The manifest's topGame values, the Crossword pose condition and
the fireworks table follow.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
from rml_read import chapter_dir


def main():
    folder = chapter_dir("ch3")
    scene = folder / "scene.rml"
    text = scene.read_text()
    pairs = [('<DataEnumValue key="daily" value="daily" id="1:9306"/>', '<DataEnumValue key="crossword" value="crossword" id="1:9306"/>'),
             ('name="Chapter 4 Fireworks daily"', 'name="Chapter 4 Fireworks crossword"')]
    for old, new in pairs:
        assert text.count(old) == 1, old
        text = text.replace(old, new)
    scene.write_text(text)
    path = folder / "chapter.json"
    m = json.loads(path.read_text())
    m["properties"]["topGame"]["values"] = ["crossword" if v == "daily" else v for v in m["properties"]["topGame"]["values"]]
    for pose in m["poses"]:
        if pose.get("when", {}).get("topGame") == "daily":
            pose["when"]["topGame"] = "crossword"
    fw = m["fireworks"]
    m["fireworks"] = {("crossword" if k == "daily" else k): ["crossword" if g == "daily" else g for g in v] for k, v in fw.items()}
    path.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n")
    print("renamed topGame daily to crossword in", scene.name, "and", path.name)


if __name__ == "__main__":
    if "--write" not in sys.argv:
        raise SystemExit(__doc__)
    main()
