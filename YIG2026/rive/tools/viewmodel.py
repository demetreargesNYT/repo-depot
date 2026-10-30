"""The Backdrop view model and its enums, written from a chapter's manifest (chapter.json).

Every file's view model is named `Backdrop`. The property and enum-value ids are fixed, the same in every file, so a
layer copied from one file points at the right property in another, and the Direction values are the same everywhere:

    scene      1:2713   enum Scene       (values 1:9100 + place in the manifest's scenes)
    direction  1:2855   enum Direction   (forward 1:9200, back 1:9201)
    lockup     1:3260   boolean          (only in files with game lockups)
    topGame    1:3300   enum TopGame     (values 1:9300 + place in the property's values)
    through    1:3301   boolean          (only our integration sets it)
"""

PROPERTY_ID = {"scene": "1:2713", "direction": "1:2855", "lockup": "1:3260", "topGame": "1:3300", "through": "1:3301", "reveal": "1:3310"}
INSTANCE_ID = {"scene": "1:2816", "direction": "1:2856", "lockup": "1:3261", "topGame": "1:3302", "through": "1:3303", "reveal": "1:3311"}
ENUM_ID = {"Scene": "1:9001", "Direction": "1:9002", "TopGame": "1:9003"}
VALUE_BASE = {"Scene": 9100, "Direction": 9200, "TopGame": 9300}
SCENE_ID, DIRECTION_ID, LOCKUP_ID = PROPERTY_ID["scene"], PROPERTY_ID["direction"], PROPERTY_ID["lockup"]


def value_id(base, index):
    return f"1:{base + index}"


def enum_values(manifest, enum):
    """The names in an enum, in the order Rive stores them."""
    if enum == "Scene":
        return [s["name"] for s in manifest["scenes"]]
    prop = next(p for p in manifest["properties"].values() if p.get("enum") == enum)
    return prop["values"]


def enum_xml(manifest, enum):
    rows = "\n".join(f'        <DataEnumValue key="{v}" value="{v}" id="{value_id(VALUE_BASE[enum], i)}"/>'
                     for i, v in enumerate(enum_values(manifest, enum)))
    return f'    <DataEnumCustom name="{enum}" id="{ENUM_ID[enum]}">\n{rows}\n    </DataEnumCustom>\n'


def enums_xml(manifest):
    names = [p["enum"] for p in manifest["properties"].values() if p["type"] == "enum"]
    return "".join(enum_xml(manifest, e) for e in names)


def view_model_xml(manifest):
    props, rows, insts = manifest["properties"], [], []
    for name, p in props.items():
        pid = PROPERTY_ID[name]
        if p["type"] == "enum":
            values = enum_values(manifest, p["enum"])
            rows.append(f'        <ViewModelPropertyEnumCustom enumId="{ENUM_ID[p["enum"]]}" name="{name}" id="{pid}"/>')
            insts.append(f'            <ViewModelInstanceEnum propertyValue="{value_id(VALUE_BASE[p["enum"]], values.index(p["default"]))}" '
                         f'viewModelPropertyId="{pid}" id="{INSTANCE_ID[name]}"/>')
        else:
            rows.append(f'        <ViewModelPropertyBoolean name="{name}" id="{pid}"/>')
            insts.append(f'            <ViewModelInstanceBoolean propertyValue="{str(p["default"]).lower()}" viewModelPropertyId="{pid}" id="{INSTANCE_ID[name]}"/>')
    return (f'    <ViewModel defaultInstanceId="1:15" name="{manifest["viewModel"]}" id="1:14">\n' + "\n".join(rows) + "\n"
            '        <ViewModelInstance exports="true" name="Default" id="1:15">\n' + "\n".join(insts) + "\n"
            '        </ViewModelInstance>\n    </ViewModel>\n')
