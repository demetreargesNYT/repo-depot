"""Before asking Demetre to approve a Rive push: pull the file's current revision from Rive and compare it with ours.

    python3 tools/rive_compare.py <ch>          1, 2, 3 or ch1, ch2, ch3; several at once: python3 tools/rive_compare.py 1 2 3

The pull goes into a scratch copy (.cache/scratch/rive-compare/<ch>/), never into chapters/<ch>/, so nothing local is
overwritten. Then the pulled scene.rml is compared, element by element, with two versions of ours:
  1. the scene.rml at this chapter's last push (its newest rive/<ch>-* tag): any difference here is an edit made in the Rive
     Editor since that push, which a push from here would throw away. Pull it in (rive pull, then commit) before pushing.
  2. the local scene.rml, the one the push would upload: this is what the push changes, as the Editor will show it.
It also builds the pulled copy, to check that what is in Rive builds here.

Elements are matched by id (an element without one by its place under the nearest element that has one). Numbers are equal
within float32 rounding. An attribute on one side only whose value is its default (0 or false, or one of DEFAULTS_BY below,
such as an ease's y2 of 1) is a value the pull leaves out, and isn't a difference. The report lists added and removed elements, a changed tag or parent, and changed values, by element name.
Exit code 0 when Rive matches the last push, 1 when it has Editor edits (or the pull failed). Each step has a time limit.
"""
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import scratch

REPO = Path(__file__).resolve().parent.parent
RIVE = os.path.expanduser("~/.rive/bin/rive")
PULL_LIMIT = 300        # seconds
BUILD_LIMIT = 300
DEFAULTS = {"0", "0.0", "false"}  # a value the pull leaves out on any element
# ...and the ones it leaves out on one kind of element only (read from pulls of all three files, 2026-11-03)
DEFAULTS_BY = {("CubicEaseInterpolator", "y2"): "1", ("TransitionViewModelCondition", "opValue"): "equal", ("LinearAnimation", "fps"): "60",
               ("LinearAnimation", "loopValue"): "oneShot", ("LinearAnimation", "duration"): "60", ("DrawTarget", "placementValue"): "before",
               ("Rectangle", "originX"): "0.5", ("Rectangle", "originY"): "0.5", ("Artboard", "spaceId"): "0:0"}


def is_default(tag, attr, value):
    return value in DEFAULTS or DEFAULTS_BY.get((tag, attr)) == value
SHOW = 12               # differences listed per kind (the counts are always complete)


def chapter_of(arg):
    ch = arg if arg.startswith("ch") else f"ch{arg}"
    if not (REPO / "chapters" / ch / "rive.yaml").exists():
        sys.exit(f"no chapter {arg!r}: use 1, 2, 3 (or ch1, ch2, ch3)")
    return ch


def last_push_tag(ch):
    tags = subprocess.run(["git", "tag", "-l", f"rive/{ch}-*", "--sort=-creatordate"], cwd=REPO, capture_output=True, text=True).stdout.split()
    return tags[0] if tags else None


def elements(root):
    """{key: (element, parent key)}: by id, or (nearest id, tag, n) for an element without one."""
    out, seen = {}, {}

    def walk(e, anchor, parent):
        i = e.get("id")
        if i:
            key = ("id", i)
        else:
            n = seen.get((anchor, e.tag), 0)
            seen[(anchor, e.tag)] = n + 1
            key = ("at", anchor, e.tag, n)
        out[key] = (e, parent)
        for c in e:
            walk(c, i or anchor, key)
    walk(root, None, None)
    return out


def same_value(u, v):
    if u == v:
        return True
    try:
        a, b = float(u), float(v)
    except (TypeError, ValueError):
        return False
    return abs(a - b) <= 1e-4 * max(1.0, abs(a))


def labeler(elems):
    """A function that names an element the way the Editor would: a key as '<timeline>: <piece> <property> frame N'."""
    names = {k[1]: e.get("name") for k, (e, _) in elems.items() if k[0] == "id" and e.get("name")}

    def label(key):
        e, parent = elems[key]
        if e.get("name"):
            return f"{e.tag} {e.get('name')!r}"
        chain, k = [], parent
        while k is not None:
            chain.append(elems[k][0])
            k = elems[k][1]
        timeline = next((x.get("name") for x in chain if x.tag in ("LinearAnimation", "StateMachine") and x.get("name")), None)
        keyed = next((x for x in chain if x.tag == "KeyedObject"), None)
        prop = next((x.get("property") for x in [e] + chain if x.tag == "KeyedProperty"), None)
        frame = e.get("frame") if e.tag.startswith("KeyFrame") else next((x.get("frame") for x in chain if x.tag.startswith("KeyFrame")), None)
        if timeline and keyed is not None:
            what = names.get(keyed.get("objectId"), keyed.get("objectId"))
            return f"{timeline}: {what}" + (f" {prop}" if prop else "") + (f" frame {frame or 0}" if e.tag.startswith("KeyFrame") or frame else "") + (f" ({e.tag})" if not e.tag.startswith("KeyFrame") else "")
        owner = next((x.get("name") for x in chain if x.get("name")), None)
        return f"{e.tag} in {owner!r}" if owner else e.tag
    return label


def compare(ours_text, theirs_text):
    """{"added": [...], "removed": [...], "moved": [...], "changed": [...]} from our scene to theirs."""
    a, b = elements(ET.fromstring(ours_text)), elements(ET.fromstring(theirs_text))
    la, lb = labeler(a), labeler(b)
    out = {"added": [], "removed": [], "moved": [], "changed": []}
    for k in b.keys() - a.keys():
        out["added"].append(lb(k))
    for k in a.keys() - b.keys():
        out["removed"].append(la(k))
    for k in a.keys() & b.keys():
        (x, px), (y, py) = a[k], b[k]
        if x.tag != y.tag or px != py:
            out["moved"].append(f"{la(k)}: now {y.tag}" + (f" under {lb(py)}" if py else ""))
            continue
        for attr in sorted(set(x.attrib) | set(y.attrib)):
            u, v = x.get(attr), y.get(attr)
            if same_value(u, v):
                continue
            if (u is None and is_default(x.tag, attr, v)) or (v is None and is_default(x.tag, attr, u)):
                continue                     # a default the pull leaves out (or our file does)
            out["changed"].append(f"{la(k)}: {attr} {u} -> {v}")
    return out


def report(title, diff):
    n = sum(len(v) for v in diff.values())
    print(f"  {title}: " + ("no differences" if not n else f"{n} difference{'s' if n != 1 else ''}"), flush=True)
    for kind in ("added", "removed", "moved", "changed"):
        items = sorted(diff[kind])
        if items:
            print(f"    {kind} ({len(items)}):")
            for line in items[:SHOW]:
                print(f"      {line}")
            if len(items) > SHOW:
                print(f"      ... and {len(items) - SHOW} more")
    return n


def run(cmd, limit, cwd=None):
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=limit)
        return r.returncode, (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return None, f"hit the {limit} s limit"


def one(ch):
    t0 = time.time()
    local = REPO / "chapters" / ch
    work = scratch.fresh(f"rive-compare/{ch}")
    (work / "rive.yaml").write_text((local / "rive.yaml").read_text())      # the link to the Rive file: all a pull needs
    file_id = next((l.split(":", 1)[1].strip() for l in (local / "rive.yaml").read_text().splitlines() if l.strip().startswith("fileId:")), "?")
    print(f"\n== {ch} (Rive file {file_id})", flush=True)
    print(f"  pulling into {work.relative_to(REPO)}/ ... ", end="", flush=True)
    rc, out = run([RIVE, "pull", str(work), "--yes", "--quiet"], PULL_LIMIT)
    if rc != 0 or not (work / "scene.rml").exists():
        print(f"FAILED ({out[-300:] or 'no scene.rml'})")
        return False
    print(f"done ({time.time() - t0:.1f} s)", flush=True)
    pulled = (work / "scene.rml").read_text()
    print("  building the pulled copy ... ", end="", flush=True)
    rc, out = run([RIVE, str(work), "--verify"], BUILD_LIMIT)
    print("builds" if rc == 0 else f"FAILED to build ({out[-200:]})", flush=True)
    tag = last_push_tag(ch)
    edits = 0
    if tag:
        at_push = subprocess.run(["git", "show", f"{tag}:./chapters/{ch}/scene.rml"], cwd=REPO, capture_output=True, text=True)
        if at_push.returncode == 0:
            edits = report(f"Editor edits since the last push ({tag})", compare(at_push.stdout, pulled))
        else:
            print(f"  could not read scene.rml at {tag}: {at_push.stderr.strip()[:200]}")
    else:
        print("  no rive/<ch>-* tag yet, so there is no last push to compare with")
    changes = report("what a push from here would change in Rive", compare(pulled, (local / "scene.rml").read_text()))
    verdict = ("Rive matches the last push: no Editor edits" if not edits else
               "Rive has Editor edits since the last push: pull them in (rive pull, then commit) before pushing")
    print(f"  {'PASS' if not edits else 'FAIL'}  {verdict}; the push would change {changes} element value(s) ({time.time() - t0:.1f} s)", flush=True)
    return not edits


def main(argv):
    chapters = [chapter_of(a) for a in argv if not a.startswith("--")] or sys.exit(__doc__)
    t0 = time.time()
    results = {ch: one(ch) for ch in chapters}
    summary = ", ".join(f"{ch} {'clean' if ok else 'EDITED or failed'}" for ch, ok in results.items())
    print(f"\nrive_compare: {summary} in {time.time() - t0:.1f} s")
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
