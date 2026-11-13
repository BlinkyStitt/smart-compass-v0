import itertools
import json
from pathlib import Path
import unittest

from power_policy import BATTERY_BUDGET, WALL_BUDGET

HERE = Path(__file__).resolve().parent


def wall_enabled(pdo2_ready, vbus, current):
    """Model a completed, qualified STUSB4500 fixed PDO and U2 UVLO."""
    return pdo2_ready and 19 <= vbus <= 21 and current >= 3


def steady_state(usb_ready, switch_on, started, cell_present, sensor_ok):
    sys_available = usb_ready or (switch_on and cell_present)
    display = sys_available and switch_on and started
    source = ("wall" if usb_ready else "battery") if display else None
    charging = usb_ready and switch_on and cell_present and sensor_ok
    return source, charging


class WallPowerTests(unittest.TestCase):
    def test_requires_completed_20v_3a_contract(self):
        for ready, voltage, amps in itertools.product(
            (False, True), (0, 5, 9, 12, 15, 19, 20, 21), (0.5, 1.5, 2.99, 3, 5)
        ):
            with self.subTest(ready=ready, voltage=voltage, amps=amps):
                self.assertEqual(
                    wall_enabled(ready, voltage, amps),
                    ready and voltage >= 19 and amps >= 3,
                )

    def test_batteryless_start_charge_and_disconnect(self):
        self.assertEqual(steady_state(True, True, False, False, False), (None, False))
        self.assertEqual(steady_state(True, True, True, False, False), ("wall", False))
        self.assertEqual(steady_state(True, True, True, True, True), ("wall", True))
        self.assertEqual(steady_state(True, True, True, True, False), ("wall", False))
        self.assertEqual(steady_state(False, True, True, True, True), ("battery", False))
        self.assertEqual(steady_state(False, True, True, False, False), (None, False))
        self.assertEqual(steady_state(True, False, True, True, True), (None, False))

    def test_contract_regulator_connector_and_charger_budget(self):
        # 1% resistor tolerance and the eFuse's specified 10% limit tolerance.
        input_limit_low = 3334 / (1240 * 1.01) * 0.9
        input_limit_high = 3334 / (1240 * 0.99) * 1.1
        charger_input_max = 2.46
        wall_current = WALL_BUDGET / 1000 + charger_input_max
        self.assertLess(wall_current, 5.0)
        self.assertLess(WALL_BUDGET / 1000, 3.0)  # J7 supply and return
        self.assertLess(BATTERY_BUDGET / 1000, 0.850 / 1.01)
        self.assertLess(5.2 * wall_current / (0.8 * 18.0), input_limit_low)
        self.assertLess(input_limit_high, 3.0)

        # Include both conductors and conservative eFuse and connector losses.
        cable_loop = 2 * 0.25 * 7.15 / 304.8
        cable_drop = wall_current * cable_loop
        fuse_drop = wall_current * 0.045
        self.assertGreater(4.8 - cable_drop - fuse_drop - 0.07, 4.4)

    def test_bq25616_cell_and_sensor_pin_order(self):
        carrier = json.loads((HERE.parents[1] / "routed-components.json").read_text())
        self.assertEqual(carrier["connectors"]["J1"][3], ["CELL_SW", "GND", "SYS", "THERM"])
        self.assertEqual(carrier["connectors"]["J7"][3],
                         ["LED_DISTRIBUTION", "GND", "LED_DATA1", "LED_DATA2", "LED_DATA3"])
