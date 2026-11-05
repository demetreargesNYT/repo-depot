"""Spelling Bee, "the fidget toy": the upright block's inner plate turns like a coin (a 2D squeeze, width |cos t|), with a dark hollow
behind it.

The block's own drawing is kept (group 9:506): its inner plate (9:507) goes into a pivot at its centre, which is keyed on scaleX; its
stroke stays 1.5 at every width (transformAffectsStroke off), so the sliver keeps a visible outline. Right under the plate (the next
sibling, drawn below it) a dark hexagon of the same size is the hollow that shows while the plate is turned.
"""
import math

from rml_edit import num

DARK = "FF1F1F1F"
PLATE = "9:507"
PLATE_STROKE = "9:517"
PLATE_AT = (38.209999, 33.191502)          # the plate's position (its centre) in the block's group
PLATE_R = 25.501                            # the plate hexagon's half width (pointy left and right)
PLATE_PTS = [(12.751, -22.0845), (-12.75, -22.0845), (-25.501, 0.0005), (-12.75, 22.0845), (12.751, 22.0845), (25.501, 0.0005)]
BLOCK_C = (754.5 + 38.2105, 553 + 33.1915)  # the block's front hexagon's centre on the artboard
BLOCK_R = 37.4605                           # its circumradius
BLOCK_D = 35.12                             # the block's depth (the back face is the front moved right by this)


def rot(a, p):
    c, s = math.cos(a), math.sin(a)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def block_outline():
    """The block's silhouette on the artboard, as a closed list of corners (front hexagon's left half, the back face's right half)."""
    cx, cy = BLOCK_C
    h = BLOCK_R * math.sin(math.pi / 3)
    return [(cx - BLOCK_R / 2, cy - h), (cx + BLOCK_R / 2 + BLOCK_D, cy - h), (cx + BLOCK_R + BLOCK_D, cy),
            (cx + BLOCK_R / 2 + BLOCK_D, cy + h), (cx - BLOCK_R / 2, cy + h), (cx - BLOCK_R, cy)]


def add_plate_spin(doc, room):
    """Wrap the plate in a pivot at its centre (key its scaleX), keep its line weight, and add the hollow under it. Returns the pivot."""
    i = doc.idx(PLATE_STROKE)
    if "transformAffectsStroke" not in doc.lines[i]:
        doc.lines[i] = doc.lines[i].replace("<Stroke ", '<Stroke transformAffectsStroke="false" ', 1)
    pid, _ = doc.wrap(PLATE, f"{room} Plate Spin", *PLATE_AT)
    j = doc.end(doc.idx(pid))
    pad = " " * (len(doc.lines[j]) - len(doc.lines[j].lstrip()))
    p2 = pad + "    "
    body = [f'{pad}<Shape x="{num(PLATE_AT[0])}" y="{num(PLATE_AT[1])}" name="{room} Plate Hollow" id="{doc.new_id()}">',
            f'{p2}<PointsPath isClosed="true" id="{doc.new_id()}">']
    body += [f'{p2}    <StraightVertex x="{num(x)}" y="{num(y)}" id="{doc.new_id()}"/>' for x, y in PLATE_PTS]
    body += [f"{p2}</PointsPath>",
             f'{p2}<Fill id="{doc.new_id()}">', f'{p2}    <SolidColor colorValue="{DARK}" id="{doc.new_id()}"/>', f"{p2}</Fill>",
             f'{p2}<Stroke thickness="1.5" cap="round" join="round" id="{doc.new_id()}">',
             f'{p2}    <SolidColor colorValue="{DARK}" id="{doc.new_id()}"/>', f"{p2}</Stroke>",
             f"{pad}</Shape>"]
    doc.lines[j + 1:j + 1] = body
    return pid
