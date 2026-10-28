"""Tests for the enum and lockup migration and the readers that go with it. Run: python3 -m unittest discover -s tools/tests"""
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import migrate_to_enums as M
from rml_read import REPO, Scene

MANIFEST = {
    "stateMachine": "Backdrop", "viewModel": "Backdrop",
    "properties": {"scene": {"default": "b"}, "direction": {"values": ["forward", "back"], "default": "forward"}, "lockup": {"default": True}},
    "scenes": [{"name": "a"}, {"name": "b"}, {"name": "c"}],
}


def cond(prop_id, key, comparator):
    return (f'<TransitionViewModelCondition opValue="equal" id="9:1"><TransitionPropertyViewModelComparator id="9:2">'
            f'<{key} id="9:3"><DataBindContext sourcePathIds="1:14-{prop_id}" propertyKey="{"636" if "Number" in key else "634"}" id="9:4"/></{key}>'
            f'</TransitionPropertyViewModelComparator>{comparator}</TransitionViewModelCondition>')


OLD = f"""<Rive version="1" kind="fragment">
    <Artboard id="1:1" name="Old"><StateMachine name="Chapter 2" id="1:7"><StateMachineLayer name="L" id="1:8">
{cond("1:2713", "BindablePropertyNumber", '<TransitionValueNumberComparator value="2" id="9:5"/>')}
{cond("1:2855", "BindablePropertyNumber", '<TransitionValueNumberComparator value="-1" id="9:6"/>')}
{cond("1:2855", "BindablePropertyNumber", '<TransitionValueNumberComparator value="1" id="9:7"/>')}
{cond("1:3260", "BindablePropertyBoolean", '<TransitionValueBooleanComparator value="true" id="9:8"/>')}
    </StateMachineLayer></StateMachine></Artboard>
    <ViewModel defaultInstanceId="1:15" name="Chapter 2" id="1:14">
        <ViewModelPropertyNumber name="scene" id="1:2713"/>
        <ViewModelPropertyNumber name="direction" id="1:2855"/>
        <ViewModelPropertyBoolean name="community" id="1:3260"/>
        <ViewModelInstance exports="true" name="Default" id="1:15">
            <ViewModelInstanceNumber propertyValue="9" viewModelPropertyId="1:2713" id="1:2816"/>
        </ViewModelInstance>
    </ViewModel>
</Rive>
"""


class Migration(unittest.TestCase):
    def setUp(self):
        self.out = ET.fromstring(M.migrate(OLD, MANIFEST))
        self.conds = self.out.findall(".//TransitionViewModelCondition")

    def test_enums_hold_the_manifests_values_in_order(self):
        enums = {e.get("name"): [v.get("key") for v in e] for e in self.out.findall("DataEnumCustom")}
        self.assertEqual(enums, {"Scene": ["a", "b", "c"], "Direction": ["forward", "back"]})

    def test_names_come_from_the_manifest(self):
        self.assertEqual(self.out.find(".//StateMachine").get("name"), "Backdrop")
        self.assertEqual(self.out.find("ViewModel").get("name"), "Backdrop")

    def test_scene_condition_points_at_the_value_by_id(self):
        c = self.conds[0].find("TransitionValueEnumComparator")
        self.assertEqual(c.get("value"), M.value_id(M.SCENE_VALUE_BASE, 2))
        self.assertEqual(self.conds[0].find(".//BindablePropertyEnum").find("DataBindContext").get("propertyKey"), "637")

    def test_direction_minus_one_is_back_and_one_is_forward(self):
        back, forward = (c.find("TransitionValueEnumComparator").get("value") for c in self.conds[1:3])
        self.assertEqual((forward, back), (M.value_id(M.DIRECTION_VALUE_BASE, 0), M.value_id(M.DIRECTION_VALUE_BASE, 1)))

    def test_community_true_becomes_lockup_false(self):
        self.assertEqual(self.conds[3].find("TransitionValueBooleanComparator").get("value"), "false")
        names = [p.get("name") for p in self.out.find("ViewModel")]
        self.assertIn("lockup", names)
        self.assertNotIn("community", names)

    def test_defaults(self):
        inst = {v.get("viewModelPropertyId"): v for v in self.out.find("ViewModel/ViewModelInstance")}
        self.assertEqual(inst["1:2713"].get("propertyValue"), M.value_id(M.SCENE_VALUE_BASE, 1))
        self.assertEqual(inst["1:3260"].get("propertyValue"), "true")

    def test_a_second_run_is_refused(self):
        with self.assertRaises(SystemExit):
            M.migrate(M.migrate(OLD, MANIFEST), MANIFEST)


class Readers(unittest.TestCase):
    """The migrated Chapter 2 file, read through rml_read."""

    @classmethod
    def setUpClass(cls):
        cls.s = Scene(REPO / "chapters" / "ch2" / "scene.rml")

    def test_scene_names_match_the_manifest(self):
        self.assertEqual(self.s.scene_names(), [x["name"] for x in self.s.manifest["scenes"]])

    def test_defaults(self):
        ids = {p.get("name"): p.get("id") for p in self.s.view_model}
        self.assertEqual(self.s.property_default(ids["scene"]), "from-chapter-1")
        self.assertEqual(self.s.property_default(ids["direction"]), "forward")
        self.assertEqual(self.s.property_default(ids["lockup"]), "true")

    def test_every_game_room_waits_for_its_manifest_scene(self):
        names, waits = self.s.scene_names(), self.s.scene_numbers()
        for x in self.s.manifest["scenes"]:
            if "room" in x:
                self.assertEqual(names[waits[x["room"]]], x["name"], x["room"])

    def test_view_model_and_state_machine_names(self):
        self.assertEqual(self.s.view_model.get("name"), "Backdrop")
        self.assertEqual(self.s.artboard.find("StateMachine").get("name"), "Backdrop")


if __name__ == "__main__":
    unittest.main()
