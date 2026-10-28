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

SCENE_ID, DIRECTION_ID, LOCKUP_ID = "1:2713", "1:2855", "1:3260"      # the existing property ids; kept so no path changes
SCENE_ENUM_ID, DIRECTION_ENUM_ID = "1:9001", "1:9002"
SCENE_VALUE_BASE, DIRECTION_VALUE_BASE = 9100, 9200                   # a value's id is 1:<base + its index>; comparators and defaults point at it
OLD_DIRECTION = {"1": "forward", "-1": "back"}                          # direction was 1 for Next and -1 for Back

CONDITION = re.compile(r"<TransitionViewModelCondition\b.*?</TransitionViewModelCondition>", re.S)


def value_id(base, index):
    return f"1:{base + index}"


def enum_xml(manifest, enum_id, name, values, base):
    rows = "\n".join(f'        <DataEnumValue key="{v}" value="{v}" id="{value_id(base, i)}"/>' for i, v in enumerate(values))
    return f'    <DataEnumCustom name="{name}" id="{enum_id}">\n{rows}\n    </DataEnumCustom>\n'


def view_model_xml(manifest):
    scenes = [s["name"] for s in manifest["scenes"]]
    props = manifest["properties"]
    s_default = scenes.index(props["scene"]["default"])
    d_default = props["direction"]["values"].index(props["direction"]["default"])
    l_default = str(props["lockup"]["default"]).lower()
    return (
        f'    <ViewModel defaultInstanceId="1:15" name="{manifest["viewModel"]}" id="1:14">\n'
        f'        <ViewModelPropertyEnumCustom enumId="{SCENE_ENUM_ID}" name="scene" id="{SCENE_ID}"/>\n'
        f'        <ViewModelPropertyEnumCustom enumId="{DIRECTION_ENUM_ID}" name="direction" id="{DIRECTION_ID}"/>\n'
        f'        <ViewModelPropertyBoolean name="lockup" id="{LOCKUP_ID}"/>\n'
        f'        <ViewModelInstance exports="true" name="Default" id="1:15">\n'
        f'            <ViewModelInstanceEnum propertyValue="{value_id(SCENE_VALUE_BASE, s_default)}" viewModelPropertyId="{SCENE_ID}" id="1:2816"/>\n'
        f'            <ViewModelInstanceEnum propertyValue="{value_id(DIRECTION_VALUE_BASE, d_default)}" viewModelPropertyId="{DIRECTION_ID}" id="1:2856"/>\n'
        f'            <ViewModelInstanceBoolean propertyValue="{l_default}" viewModelPropertyId="{LOCKUP_ID}" id="1:3261"/>\n'
        f'        </ViewModelInstance>\n'
        f'    </ViewModel>\n'
    )


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
    new_vm = enum_xml(manifest, SCENE_ENUM_ID, "Scene", [s["name"] for s in manifest["scenes"]], SCENE_VALUE_BASE) \
        + enum_xml(manifest, DIRECTION_ENUM_ID, "Direction", d_values, DIRECTION_VALUE_BASE) + view_model_xml(manifest)
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
