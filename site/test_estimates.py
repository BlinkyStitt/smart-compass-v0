"""Check mass accounting boundaries and the stated energy calculation."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from estimates import estimate_masses, runtime_hours

ROOT = Path(__file__).resolve().parents[1]


class EstimateTests(unittest.TestCase):
    def setUp(self):
        self.wide = json.loads((ROOT / "hardware/enclosure/exports/parts.json").read_text())
        self.narrow = json.loads((ROOT / "designs/stacked/exports/scene.json").read_text())
        self.parameters = json.loads((ROOT / "designs/stacked/parameters.json").read_text())
        self.material = json.loads((ROOT / "hardware/enclosure/exports/scene.json").read_text())["ring_materials"]["glow"]

    def mass(self, scene):
        return estimate_masses(self.wide, scene, self.parameters, self.material)["narrow"]["complete_pendant"]["nominal_g"]

    def test_battery_envelope_is_not_added_as_printed_plastic(self):
        changed = deepcopy(self.narrow)
        next(p for p in changed["parts"] if p["name"] == "Battery")["volume_cm3"] *= 10
        self.assertEqual(self.mass(changed), self.mass(self.narrow))

    def test_case_material_is_counted_once_at_structural_density(self):
        changed = deepcopy(self.narrow)
        next(p for p in changed["parts"] if p["name"] == "RearCover")["volume_cm3"] += 100
        self.assertAlmostEqual(self.mass(changed) - self.mass(self.narrow), 127, places=1)

    def test_energy_budget_uses_watt_hours_and_total_five_volt_load(self):
        self.assertAlmostEqual(runtime_hours(37, .85, 1.25), 5.032)
        self.assertAlmostEqual(runtime_hours(37, .85, 1.5), 4.193333333)
        with self.assertRaises(ValueError):
            runtime_hours(37, .85, 0)

    def test_unclassified_new_solid_requires_a_mass_decision(self):
        changed = deepcopy(self.narrow)
        changed["parts"].append({"name": "NewBracket", "role": "solid", "volume_cm3": 10})
        with self.assertRaisesRegex(ValueError, "Unclassified"):
            self.mass(changed)
