"""Check mass accounting boundaries and the stated energy calculation."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from estimates import estimate_masses, runtime_hours
from inventory import totals

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

    def test_antenna_envelope_does_not_add_mass(self):
        changed = deepcopy(self.narrow)
        next(p for p in changed["parts"] if p["name"] == "RadioAntenna")["volume_cm3"] += 100
        self.assertEqual(
            estimate_masses(self.wide, changed, self.parameters, self.material),
            estimate_masses(self.wide, self.narrow, self.parameters, self.material),
        )

    def test_antenna_inventory_allowance_is_counted_once(self):
        before = estimate_masses(self.wide, self.narrow, self.parameters, self.material)["narrow"]
        changed = deepcopy(self.wide)
        antenna = next(row for row in changed["components"] if row["id"] == "rf_antenna")
        antenna["mass_g_per_unit"] += 10
        antenna["mass_range_g_per_unit"] = [mass + 10 for mass in antenna["mass_range_g_per_unit"]]
        after = estimate_masses(changed, self.narrow, self.parameters, self.material)["narrow"]
        for assembly in ("complete_pendant", "total_worn"):
            self.assertAlmostEqual(after[assembly]["nominal_g"] - before[assembly]["nominal_g"], 10, places=1)
            for low_high in (0, 1):
                self.assertAlmostEqual(
                    after[assembly]["range_g"][low_high] - before[assembly]["range_g"][low_high], 10, places=1,
                )
        self.assertEqual(after["necklace"], before["necklace"])

    def test_battery_is_in_pendant_and_worn_totals_once(self):
        # Change the supplier mass without changing the CAD envelope. Both
        # headline assemblies must gain exactly that mass, not zero or twice it.
        before = estimate_masses(self.wide, self.narrow, self.parameters, self.material)
        changed = deepcopy(self.wide)
        changed["parameters_for_inventory"]["battery_mass_g"] += 50
        pack = next(row for row in changed["components"] if row["id"] == "battery")
        pack["installed_mass_g"] += 50
        changed["mass_estimate"] = totals(changed["components"])
        after = estimate_masses(changed, self.narrow, self.parameters, self.material)
        for design in ("wide", "narrow"):
            for assembly in ("complete_pendant", "total_worn"):
                self.assertAlmostEqual(after[design][assembly]["nominal_g"] - before[design][assembly]["nominal_g"], 50, places=1)
            self.assertEqual(after[design]["necklace"], before[design]["necklace"])

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
        for name in ("NewBracket", "RadioAntennaClip"):
            with self.subTest(name=name):
                changed = deepcopy(self.narrow)
                changed["parts"].append({"name": name, "role": "solid", "volume_cm3": 10})
                with self.assertRaisesRegex(ValueError, "^Unclassified narrow solid: " + name + "$"):
                    self.mass(changed)
