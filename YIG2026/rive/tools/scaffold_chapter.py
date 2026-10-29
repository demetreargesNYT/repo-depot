"""Write the empty skeleton of a new Rive file from its manifest (chapters/<ch>/chapter.json).

    python3 tools/scaffold_chapter.py ch1        writes chapters/ch1/scene.rml, rive.yaml, .gitignore, AGENTS.md, CLAUDE.md
                                                 (refuses if scene.rml already exists)

The skeleton is what every file shares and nothing else: the 1495 x 1067 artboard, the stage with the Top Marker (draw
order) and the shared Background (wall, floor, floor line at 712, no strokes on its edges), an empty `Backdrop` state
machine, and the `Backdrop` view model with its enums from viewmodel.py. Rooms come in afterwards with import_room.py.
The ids are the same in every file (the artboard 1:2, the state machine 1:7, the view model 1:14), so a layer copied
from another file points at the right property.

There is no `push:` link in rive.yaml: the first `rive push` creates the Rive file and records it.
"""
import json
import shutil
import sys

from rml_read import REPO, chapter_dir_for_new
from viewmodel import enums_xml, view_model_xml

TOP_MARKER = """            <Shape x="-40" y="-40" name="Top Marker" id="1:2857">
                <Rectangle width="1" height="1" name="Top Marker Rect" id="1:2858"/>
                <Fill name="Top Marker Fill" id="1:2859">
                    <SolidColor colorValue="00000000" name="Top Marker Colour" id="1:2860"/>
                </Fill>
            </Shape>"""

# the shared backdrop, as Chapter 2 draws it: the floor line is at 712, nothing has a stroke on its edges
BACKGROUND = """            <Node x="747.5" y="533.5" name="Background" id="1:2285">
                <Shape y="178.5" name="Floor-Line" id="1:2286">
                    <PointsPath id="1:2287">
                        <StraightVertex x="-747.5" id="1:2288"/>
                        <StraightVertex x="747.5" id="1:2289"/>
                    </PointsPath>
                    <Stroke thickness="2" id="1:2618">
                        <SolidColor colorValue="FF1F1F1F" id="1:2290"/>
                    </Stroke>
                </Shape>
                <Shape y="356" name="Floor" id="1:2291">
                    <PointsPath isClosed="true" id="1:2292">
                        <StraightVertex x="-747.5" y="-177.5" id="1:2293"/>
                        <StraightVertex x="747.5" y="-177.5" id="1:2294"/>
                        <StraightVertex x="747.5" y="177.5" id="1:2295"/>
                        <StraightVertex x="-747.5" y="177.5" id="1:2296"/>
                    </PointsPath>
                    <Fill id="1:2619">
                        <SolidColor colorValue="{floor}" id="1:2297"/>
                    </Fill>
                </Shape>
                <Shape name="Wall" id="1:2298">
                    <PointsPath isClosed="true" id="1:2299">
                        <StraightVertex x="-747.5" y="-533.5" id="1:2300"/>
                        <StraightVertex x="747.5" y="-533.5" id="1:2301"/>
                        <StraightVertex x="747.5" y="533.5" id="1:2302"/>
                        <StraightVertex x="-747.5" y="533.5" id="1:2303"/>
                    </PointsPath>
                    <Fill id="1:2620">
                        <SolidColor colorValue="{wall}" id="1:2304"/>
                    </Fill>
                </Shape>
            </Node>"""


def scene_text(m):
    colors = m.get("colors", {"wall": "FFF1ECC0", "floor": "FFFF811E"})
    return f"""<Rive version="1" kind="fragment">
    <Artboard defaultStateMachineId="1:7" viewModelId="1:14" viewModelInstanceId="1:15" clip="true" width="1495" height="1067" styleId="1:5" name="{m["artboard"]}" id="1:2">
        <Node name="{m["artboard"]} Stage" id="1:17">
{TOP_MARKER}
{BACKGROUND.format(**colors)}
        </Node>
        <Fill fillRule="clockwise" id="1:3"/>
        <LayoutComponentStyle id="1:5"/>
        <StateMachine name="{m["stateMachine"]}" id="1:7">
        </StateMachine>
    </Artboard>
{enums_xml(m)}{view_model_xml(m)}</Rive>
"""


def main(argv):
    if not argv:
        raise SystemExit(__doc__)
    d = chapter_dir_for_new(argv[0])
    m = json.loads((d / "chapter.json").read_text())
    if (d / "scene.rml").exists():
        raise SystemExit(f"{d / 'scene.rml'} already exists; this tool only starts a new file")
    (d / "scene.rml").write_text(scene_text(m))
    (d / "rive.yaml").write_text(f'name: yig-{argv[0]}\nlogs:\n  file: build/rive.log\n  problems: build/problems.log\nmain: "{m["artboard"]}"\n')
    ch2 = REPO / "chapters" / "ch2"
    for f in (".gitignore", "AGENTS.md", "CLAUDE.md"):
        if not (d / f).exists():
            shutil.copy2(ch2 / f, d / f)
    print(f"wrote {d / 'scene.rml'}; push it once to create the Rive file (rive push), then import rooms")


if __name__ == "__main__":
    main(sys.argv[1:])
