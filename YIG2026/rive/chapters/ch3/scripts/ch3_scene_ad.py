"""File 3's scene ad-3 is called ad again (Demetre, 2026-11-05): every file's ad scene is just "ad" (File 1 uses it for both Ad 1 and Ad 2).

    python3 chapters/ch3/scripts/ch3_scene_ad.py --write      once, after ch3_scene_names.py

Only the enum value's name changes (id 1:9100, so every condition follows by itself), and the manifest's uses of "ad-3": the scene
entry, the two defaults, the poses' scene lists, the badge scenes' sameRoomAs and the tests' flow.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
from rml_read import chapter_dir

OLD, NEW = "ad-3", "ad"


def main():
    folder = chapter_dir("ch3")
    scene = folder / "scene.rml"
    text = scene.read_text()
    line = f'<DataEnumValue key="{OLD}" value="{OLD}" id="1:9100"/>'
    assert text.count(line) == 1, "the ad-3 enum value was not found once"
    scene.write_text(text.replace(line, f'<DataEnumValue key="{NEW}" value="{NEW}" id="1:9100"/>'))
    path = folder / "chapter.json"
    m = json.loads(path.read_text())
    m["properties"]["scene"]["default"] = NEW
    m["properties"]["startScene"]["default"] = NEW
    for s in m["scenes"]:
        if s["name"] == OLD:
            s["name"] = NEW
        if s.get("sameRoomAs") == OLD:
            s["sameRoomAs"] = NEW
    for pose in m["poses"]:
        pose["scenes"] = [NEW if n == OLD else n for n in pose["scenes"]]
    m["tests"]["flow"] = [NEW if n == OLD else n for n in m["tests"]["flow"]]
    path.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n")
    print("renamed ad-3 to ad in", scene.name, "and", path.name)


if __name__ == "__main__":
    if "--write" not in sys.argv:
        raise SystemExit(__doc__)
    main()
