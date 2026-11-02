"""One time (2026-11-02, history like loading_start.py): the ball comes out of the cuckoo clock's door (finesse round, Chapter 1 card 1).

    python3 tools/clock_door_clip.py            dry run
    python3 tools/clock_door_clip.py --write    rewrite chapters/ch1/scene.rml

The clip was a plain rectangle whose left edge (x 654.86) sat on the doorway's left stroke (the door is a gable: left edge
x 655.22, right edge 669.86, roofline from (655.22, 434.17) up to the apex (662.54, 426.85), stroke 1.5), so the 35.4 px ball
covered the stroke and showed over the clock's face above the roof. Now the clip is a polygon:
  * its left edge is x 660.0: 4 px of black doorway, with its stroke, stays visible to the left of the ball
  * over the doorway's width its top follows the roofline, inset 1 px so the stroke stays visible
  * from the apex (x 662.54) the edge climbs to the right at 45 degrees and is open beyond x 700, so the cut fades away and the
    ball has no notch once it is out (a vertical opening at the doorway's right edge left a visible bite in the ball)
Only the clip shape changes.
"""
import sys

from ball_easing import Patcher
from rml_read import chapter_dir

LEFT = 660.0
INSET = 1.41           # 1 px measured across the 45 degree roof, as a vertical drop
# the clip is everything except a slot: the doorway's area to the left of x 660 (y 380 to 500, open to the left edge) and the wedge
# above the roofline up to x 700. Anywhere else on the stage the ball is not clipped at all.
POINTS = [(-1000.0, -1000.0), (3600.0, -1000.0), (3600.0, 2000.0), (-1000.0, 2000.0), (-1000.0, 500.0), (LEFT, 500.0),
          (LEFT, round(434.17 - (LEFT - 655.22) + INSET, 2)), (662.54, round(426.85 + INSET, 2)),
          (700.0, round(426.85 + INSET - (700.0 - 662.54), 2)), (700.0, 380.0), (-1000.0, 380.0)]


def main(argv):
    pt = Patcher(chapter_dir("ch1") / "scene.rml")
    old = ('<Shape x="654.86" y="600" name="Chapter 1 Card 1 Ball Doorway Clip" id="15:3978">\n'
           '                        <Rectangle width="3000" height="2000" originX="0" originY="0.5" name="Path" id="15:3980"/>\n'
           '                    </Shape>')
    import re
    m = re.search(r'<Shape name="Chapter 1 Card 1 Ball Doorway Clip" id="15:3978">.*?</Shape>', pt.text, re.S)
    assert m or old in pt.text
    if m:
        old = m.group(0)
    verts = "\n".join(f'                            <StraightVertex x="{x!r}" y="{y!r}" id="{pt.new_id()}"/>' for x, y in POINTS)
    new = (f'<Shape name="Chapter 1 Card 1 Ball Doorway Clip" id="15:3978">\n'
           f'                        <PointsPath isClosed="true" name="Path" id="15:3980">\n{verts}\n                        </PointsPath>\n'
           f'                    </Shape>')
    print("clip polygon:", POINTS)
    if "--write" in argv:
        pt.path.write_text(pt.text.replace(old, new))
        print("wrote", pt.path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
