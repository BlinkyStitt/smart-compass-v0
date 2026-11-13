import itertools
import json
import math
from pathlib import Path
import sys
import unittest

from power_policy import BATTERY_BUDGET, WALL_BUDGET

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from pd60_design import SELECTOR


def resistance(ref):
    value = SELECTOR[ref][0].split()[0]
    return 1000 * float(value.removesuffix("k"))


def limiter_range(ref):
    ohms = resistance(ref)
    return 3334 * .9 / (ohms * 1.01), 3334 * 1.1 / (ohms * .99)


def trip_time(resistance_ohm, capacitance_f, initial, threshold, final):
    return resistance_ohm * capacitance_f * math.log((final - initial) / (final - threshold))


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
        for ref in ("R5", "R14"):
            minimum, maximum = limiter_range(ref)
            self.assertLess(WALL_BUDGET / 1000 + 0.25, minimum)
            self.assertLess(maximum, 3.0)  # J7 supply and return on 22 AWG
        self.assertLess(BATTERY_BUDGET / 1000, 0.850 / 1.01)
        self.assertLess(5.2 * wall_current / (0.8 * 18.0), input_limit_low)
        self.assertLess(input_limit_high, 3.0)

        # Include both conductors and conservative eFuse and connector losses.
        inlet_lead_limit_m = 0.40
        inlet_to_selector_m = ((25.5 + 44) ** 2 + (41.53 - 47) ** 2) ** 0.5 / 1000
        self.assertGreater(inlet_lead_limit_m, inlet_to_selector_m + 0.025)
        cable_loop = 2 * inlet_lead_limit_m * 7.15 / 304.8
        cable_drop = wall_current * cable_loop
        fuse_drop = wall_current * 0.045
        self.assertGreater(4.8 - cable_drop - fuse_drop - 0.07, 4.4)

    def test_led_output_has_one_cutoff_and_a_logic_powered_latch(self):
        pins = {ref: part[3] for ref, part in SELECTOR.items()}
        self.assertEqual(pins["U1"][4:6], ["WALL_5V", "LED_SOURCE"])
        self.assertEqual(pins["U2"][4:6], ["BAT_5V", "LED_SOURCE"])
        self.assertEqual(pins["U3"][4:6], ["LED_SOURCE", "LED_5V"])
        self.assertEqual(pins["W6"], ["LED_5V"])
        self.assertEqual(pins["U3"][0], "EN_LED")
        self.assertEqual(pins["R12"], ["ALLOW_LED", "EN_LED"])
        self.assertEqual(pins["R13"], ["EN_LED", "GND"])

        # /CLR initializes /Q high. Pulling /PRE low then holds /Q low
        # across changes at U1 or U2. Tying CLK low prevents any release
        # edge at the sense inputs from clearing the saved fault.
        self.assertEqual(pins["U4"],
                         ["GND", "GND", "ALLOW_LED", "GND", "-",
                          "RESET_N", "TRIP_N", "LOGIC_5V"])
        self.assertEqual(pins["U5"], ["RESET_N", "GND", "LOGIC_5V", "-",
                                      "LOGIC_5V", "LOGIC_5V"])
        self.assertEqual(pins["U6"][0], "FAULT_N")
        self.assertEqual(pins["U8"][5], "FAULT_N")
        self.assertEqual(pins["U7"], ["FAULT_N", "GND", "FAULT_FILTER", "TRIP_N",
                                      "LOGIC_5V", "FAULT_HIGH"])
        self.assertEqual(pins["R19"], ["FAULT_HIGH", "FAULT_FILTER"])
        self.assertEqual(pins["C12"], ["FAULT_FILTER", "GND"])
        self.assertEqual(pins["D1"], ["FAULT_HIGH", "FAULT_FILTER"])
        self.assertEqual(pins["Q1"], ["MODE_BASE", "MODE_GND", "WALL_N"])
        self.assertEqual(pins["Q2"], ["OK_BASE", "GND", "MODE_GND"])

    def test_led_fault_filter_margin_and_rail_threshold(self):
        # TPS3808G01 0.405 V, ±2%, up to 3% rising hysteresis, 25 nA
        # SENSE leakage. The healthy rail must recover above the upper limit.
        upper, lower = resistance("R16"), resistance("R17")
        rise_max = .405 * 1.02 * 1.03 * (1 + upper * 1.01 / (lower * .99))
        rise_max += 25e-9 * upper * 1.01
        fall_min = .405 * .98 * (1 + upper * .99 / (lower * 1.01))
        fall_min -= 25e-9 * upper * 1.01
        self.assertGreater(fall_min, 3.5)
        self.assertLess(rise_max, 4.1)

        # R19 tolerance and the required effective C12 range in the BOM.
        # SN74LVC2G14 positive threshold range bounds the RC assertion.
        # Use the input leakage limit as a ±0.51 V shift. Use correlated
        # switching thresholds and conservative output levels at the supply
        # endpoints. Allow a 1.1 V initial value for the discharged diode path.
        timing_r = resistance("R19")
        earliest = trip_time(timing_r * .99, 3.3e-6, 1.1, 1.9, 5.5 + .51)
        latest = max(trip_time(timing_r * 1.01, 5.7e-6, 0, threshold, output - .51)
                     for threshold, output in ((3.1, 3.8), (3.7, 4.8)))
        self.assertLess(latest, 2.0)

        # U5 releases reset in at most 28 ms after a valid logic supply.
        # Allocate 20 ms for ordinary rail recovery and 5 ms for the U6
        # release delay. A sustained fault crosses the Schmitt threshold
        # regardless of which source is active.
        self.assertGreater(earliest, .028 + .020 + .005)

    def test_bq25616_cell_and_sensor_pin_order(self):
        carrier = json.loads((HERE.parents[1] / "routed-components.json").read_text())
        self.assertEqual(carrier["connectors"]["J1"][3], ["CELL_SW", "GND", "SYS", "THERM"])
        self.assertEqual(carrier["connectors"]["J7"][3],
                         ["LED_DISTRIBUTION", "GND", "LED_DATA1", "LED_DATA2", "LED_DATA3"])
