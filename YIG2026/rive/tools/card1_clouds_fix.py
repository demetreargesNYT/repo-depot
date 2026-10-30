"""One time (2026-10-30, history like card1_refine.py): one set of clouds across Chapter 1 card 1's whole window.

card1_refine.py gave every pane the old file's cloud positions as they stand in the old pane's own coordinates, so each
pane showed the same two clouds (nine copies). In the old YIG Test file the positions are in the window's coordinates:
Cloud Big at (-39.4, 40) and Cloud Small at (47.5, -5) from the window's centre, in every pane, each pane clipping its
own slice. So here too: a pane's cloud sits at its window position minus the pane's centre, and every cloud of one kind
shares one drift. The set crosses the window once per loop (130 px at 0.17 px a frame, about twice the old file's speed,
to fit the 762-frame loop with no jump), starting from the old file's places.

    python3 tools/card1_clouds_fix.py            dry run
    python3 tools/card1_clouds_fix.py --write
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from card1_story import fmt, key  # noqa: E402
from card1_refine import Ids  # noqa: E402
from rml_read import chapter_dir  # noqa: E402
from xml_fragments import block_range, parse, ser  # noqa: E402

ROOM = "Chapter 1 Card 1"
EDGE = 65                   # a cloud is out of sight past this from the window's centre (half the grid, 55, plus a cloud's half width)
SPAN = 2 * EDGE
WINDOW_AT = {"Cloud Big": (-39.4, 40.0), "Cloud Small": (47.5, -5.0)}
PANE_CENTRE = 55.5          # in the panes' own group, where the middle pane sits


def track(x0, loop_len):
    """x keys for one cloud: from x0 to the right edge, round to the left edge in one frame, on to x0 by the loop's end."""
    v = SPAN / loop_len
    t1 = round((EDGE - x0) / v)
    return [(0, x0), (t1, EDGE), (t1 + 1, -EDGE), (loop_len, x0)]


def main():
    write = "--write" in sys.argv
    path = chapter_dir("ch1") / "scene.rml"
    lines = path.read_text().split("\n")
    ids = Ids("\n".join(lines))
    wa, wb = block_range(lines, rf'name="{ROOM} Window" id=', 20)
    window = parse("\n".join(lines[wa:wb + 1]))
    solo_of = {s.get("name"): s for s in window.iter("Solo")}
    loop_len = int(parse("\n".join(lines[slice(*[i for i in (block_range(lines, rf'<LinearAnimation .*name="{ROOM} Small Loop"')[0], block_range(lines, rf'<LinearAnimation .*name="{ROOM} Small Loop"')[1] + 1)])])).get("duration"))
    new_x = {}                                           # cloud node id -> its x keys
    for cont in window.iter("Node"):
        if not (cont.get("name") or "").startswith(f"{ROOM} Clouds R"):
            continue
        r, c = int(cont.get("name")[-3]), int(cont.get("name")[-1])
        solo = solo_of[f"Pane_{r + 1}{'abc'[c]}"]
        px, py = float(solo.get("x")) - PANE_CENTRE, float(solo.get("y")) - PANE_CENTRE
        for cloud in cont.iter("Node"):
            if cloud.get("name") in WINDOW_AT:
                wx, wy = WINDOW_AT[cloud.get("name")]
                cloud.set("y", fmt(wy - py))
                keys = [(f, v - px) for f, v in track(wx, loop_len)]
                cloud.set("x", fmt(keys[0][1]))
                new_x[cloud.get("id")] = keys
    assert len(new_x) == 18, len(new_x)

    def retime(name):
        i0, i1 = block_range(lines, rf'<LinearAnimation .*name="{ROOM} {name}"')
        anim = parse("\n".join(lines[i0:i1 + 1]))
        for ko in anim:
            if ko.tag == "KeyedObject" and ko.get("objectId") in new_x:
                kp = ko.find("KeyedProperty")
                for k in list(kp):
                    kp.remove(k)
                keys = new_x[ko.get("objectId")]
                if name == "Small Loop":
                    for i, (f, v) in enumerate(keys):          # linear all the way; the jump from edge to edge takes one frame, out of sight
                        kp.append(key(ids, f, v, "linear" if i < len(keys) - 1 else None))
                else:
                    kp.append(key(ids, 0, keys[0][1]))
        return i0, i1, anim
    edits = [(wa, wb, ser(window, 5))] + [(*retime(n)[:2], ser(retime(n)[2], 2)) for n in ("Small Loop", "Small Waiting", "Small Hold")]
    print("18 clouds placed in window space; track", track(WINDOW_AT["Cloud Big"][0], loop_len))
    if not write:
        return
    for s, e, new in sorted(edits, key=lambda t: -t[0]):
        lines[s:e + 1] = new.rstrip("\n").split("\n")
    path.write_text("\n".join(lines))
    print("wrote", path)


if __name__ == "__main__":
    main()
