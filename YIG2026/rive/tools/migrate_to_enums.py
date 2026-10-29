"""One-time migration of Chapter 2 to the names engineering asked for. Like import_room.py, it is history once it has run:

    python3 tools/migrate_to_enums.py ch2          rewrite chapters/ch2/scene.rml in place (refuses a second run)

It changes only the language the file speaks, not what it does:
  * the state machine and the view model are both named after the manifest (Backdrop);
  * `scene` and `direction` become custom enums (DataEnumCustom) instead of numbers, with the values and order in
    chapter.json (the index in the list is the number the file used before, so every condition keeps its meaning;
    the CLI wants each comparator and default to point at the value's own id, so every DataEnumValue gets one);
  * `community` becomes `lockup` and its meaning flips: true shows the lockup. Its default is true.
Every transition condition keeps its place; only the comparator type and literal change.
"""
import json
import re
import sys

from rml_read import chapter_dir

from viewmodel import DIRECTION_ID, ENUM_ID, LOCKUP_ID, SCENE_ID, VALUE_BASE, enum_xml, value_id, view_model_xml

SCENE_ENUM_ID, DIRECTION_ENUM_ID = ENUM_ID["Scene"], ENUM_ID["Direction"]
SCENE_VALUE_BASE, DIRECTION_VALUE_BASE = VALUE_BASE["Scene"], VALUE_BASE["Direction"]
OLD_DIRECTION = {"1": "forward", "-1": "back"}                          # direction was 1 for Next and -1 for Back

CONDITION = re.compile(r"<TransitionViewModelCondition\b.*?</TransitionViewModelCondition>", re.S)


def convert_condition(block, direction_values):
    if f'sourcePathIds="1:14-{SCENE_ID}"' in block:
        old = re.search(r'<TransitionValueNumberComparator value="(-?\d+)"', block).group(1)
        block = re.sub(r"BindablePropertyNumber", "BindablePropertyEnum", block).replace('propertyKey="636"', 'propertyKey="637"')
        return re.sub(r'<TransitionValueNumberComparator value="-?\d+"', f'<TransitionValueEnumComparator value="{value_id(SCENE_VALUE_BASE, int(old))}"', block)
    if f'sourcePathIds="1:14-{DIRECTION_ID}"' in block:
        old = re.search(r'<TransitionValueNumberComparator value="(-?\d+)"', block).group(1)
        index = direction_values.index(OLD_DIRECTION[old])
        block = re.sub(r"BindablePropertyNumber", "BindablePropertyEnum", block).replace('propertyKey="636"', 'propertyKey="637"')
        return re.sub(r'<TransitionValueNumberComparator value="-?\d+"', f'<TransitionValueEnumComparator value="{value_id(DIRECTION_VALUE_BASE, index)}"', block)
    if f'sourcePathIds="1:14-{LOCKUP_ID}"' in block:        # community true hid the lockup; lockup true shows it
        flip = {"true": "false", "false": "true"}
        return re.sub(r'(<TransitionValueBooleanComparator value=")(true|false)"', lambda m: f'{m.group(1)}{flip[m.group(2)]}"', block)
    return block


def migrate(text, manifest):
    if "<DataEnumCustom" in text:
        raise SystemExit("this file already has enums; nothing to do")
    d_values = manifest["properties"]["direction"]["values"]
    text = CONDITION.sub(lambda m: convert_condition(m.group(0), d_values), text)
    text, n = re.subn(r'<StateMachine name="[^"]*"', f'<StateMachine name="{manifest["stateMachine"]}"', text, count=1)
    assert n == 1, "no state machine to rename"
    new_vm = enum_xml(manifest, "Scene") + enum_xml(manifest, "Direction") + view_model_xml(manifest)
    text, n = re.subn(r"    <ViewModel defaultInstanceId.*?</ViewModel>\n", lambda m: new_vm, text, count=1, flags=re.S)
    assert n == 1, "no view model to replace"
    return text


def main(argv):
    d = chapter_dir(argv[0] if argv else "ch2")
    manifest = json.loads((d / "chapter.json").read_text())
    path = d / "scene.rml"
    path.write_text(migrate(path.read_text(), manifest))
    print(f"migrated {path}")


if __name__ == "__main__":
    main(sys.argv[1:])
