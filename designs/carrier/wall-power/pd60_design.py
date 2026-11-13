"""Pin maps for the 60 W USB-C head and LED power selector."""

GND = "GND"
RPW = "WallPower:Texas_RPW_VQFN-10_2x2mm"
R = "Resistor_SMD:R_0603_1608Metric"
C = "Capacitor_SMD:C_0603_1608Metric"
C8 = "Capacitor_SMD:C_0805_2012Metric"
C12 = "Capacitor_SMD:C_1206_3216Metric"
WIRE = "WallPower:Lead_22AWG"
HEAVY = "WallPower:Lead_18AWG"
HOLE = "MountingHole:MountingHole_2.2mm_M2"
TP = "TestPoint:TestPoint_Pad_D1.0mm"

# Top side. The Pololu regulator fits next to this board in the rear cover.
HEAD = {
    "J1": ("USB4736-GF-A", "WallPower:USB4736-GF-A", (14, 31, 0),
           {"A5": "CC1", "B5": "CC2", "A9": "RAW", "B9": "RAW",
            "A12": GND, "B12": GND, "SH": GND}),
    "U1": ("STUSB4500QTR", "Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm",
           (8.4, 17.7, 90), ["CC1", "CC1", "-", "CC2", "CC2", "RESET", "SCL",
           "SDA", "DISCH", GND, "-", GND, GND, "-", "-", "-", "-", "SENSE", "-",
           "PDO2_N", "V1V2", "PROG_3V3", "V2V7", "RAW", GND]),
    "U2": ("TPS259470ARPWR", RPW, (20, 20, 0),
           ["PD_UVLO", "PDO2_N", "-", "-", "RAW", "PD_20V", "PD_SLEW", GND, "PD_ILIM", "-"]),
    "U3": ("TPS259470LRPWR", RPW, (20, 10, 0),
           ["OUT_UVLO", "OUT_OVLO", "-", "-", "BUCK_5V", "WALL_5V", "OUT_SLEW", GND,
            "OUT_ILIM", "-"]),
    "D1": ("ESDA25W", "Package_TO_SOT_SMD:SOT-323_SC-70", (6.6, 22.2, 0),
           ["CC1", "CC2", GND]),
    "D2": ("ESDA25P35-1U1M", "WallPower:ST_QFN-2L_1.6x1mm", (23.0, 24.8, 180),
           ["RAW", GND]),
    "C1": ("4.7uF 50V X7R", C12, (2.9, 24.6, 90), ["RAW", GND]),
    "C2": ("1uF 16V X7R", C, (3.5, 18.45, 180), ["V2V7", GND]),
    "C3": ("1uF 16V X7R", C, (3.5, 15.45, 180), ["V1V2", GND]),
    "C4": ("1uF 50V X7R", C8, (25.7, 17.8, 0), ["PD_20V", GND]),
    "C5": ("10nF 50V X7R", C, (24.5, 21.5, 0), ["PD_SLEW", GND]),
    "C6": ("1uF 50V X7R", C8, (16, 11.75, 0), ["BUCK_5V", GND]),
    "C7": ("10uF 16V X7R", C8, (24.6, 6.8, 0), ["WALL_5V", GND]),
    "C8": ("10nF 16V X7R", C, (24.4, 9.35, 0), ["OUT_SLEW", GND]),
    "R1": ("1k", R, (12.6, 20.8, 180), ["RAW", "SENSE"]),
    "R2": ("1k", R, (12.7, 16.0, 0), ["DISCH", "PD_20V"]),
    "R3": ("100k 1%", R, (16.65, 17.7, 0), ["RAW", "PDO2_N"]),
    "R4": ("22k 1%", R, (16, 16, 0), ["PDO2_N", GND]),
    "R5": ("140k 1%", R, (15.9, 22, 0), ["RAW", "PD_UVLO"]),
    "R6": ("10k 1%", R, (13.2, 19.2, 0), ["PD_UVLO", GND]),
    "R7": ("1.24k 1%", R, (23.9, 19.775, 0), ["PD_ILIM", GND]),
    "R8": ("27.4k 1%", R, (15.5, 9.2, 0), ["BUCK_5V", "OUT_UVLO"]),
    "R9": ("10k 1%", R, (15.5, 7.2, 0), ["OUT_UVLO", GND]),
    "R10": ("35.7k 1%", R, (20, 13.7, 180), ["BUCK_5V", "OUT_OVLO"]),
    "R11": ("10k 1%", R, (19.4, 16.05, 0), ["OUT_OVLO", GND]),
    "R12": ("549R 1%", R, (24.4, 11.6, 0), ["OUT_ILIM", GND]),
    "R13": ("4.7k", R, (7.4, 11.6, 0), ["PROG_3V3", "SCL"]),
    "R14": ("4.7k", R, (8.25, 9.8, 0), ["PROG_3V3", "SDA"]),
    "R15": ("100k", R, (4.0, 12.65, 0), ["RESET", GND]),
    "W1": ("20V TO BUCK", WIRE, (22.05, 16.15, 0), ["PD_20V"]),
    "W2": ("BUCK IN GND", WIRE, (25.6, 15.25, 0), [GND]),
    "W3": ("5V FROM BUCK", HEAVY, (10.25, 6, 0), ["BUCK_5V"]),
    "W4": ("BUCK OUT GND", HEAVY, (13.6, 4.0, 0), [GND]),
    "W5": ("WALL 5V", HEAVY, (20.8, 2.1, 0), ["WALL_5V"]),
    "W6": ("WALL GND", HEAVY, (24.0, 2.1, 0), [GND]),
    "TP1": ("PROG 3V3", TP, (3.8, 7.9, 0), ["PROG_3V3"]),
    "TP2": ("SDA", TP, (6.2, 7.9, 0), ["SDA"]),
    "TP3": ("SCL", TP, (3.8, 5.3, 0), ["SCL"]),
    "TP4": ("GND", TP, (6.2, 5.3, 0), [GND]),
    "H1": ("M2", HOLE, (2, 2, 0), []),
    "H2": ("M2", HOLE, (25.8, 28.8, 0), []),
}

# J7.1 gets LED_5V. The Sparkle clamp's original 5 V lead becomes BAT_5V.
# The display enable comes from J6.1, downstream of the latch and S1.
SELECTOR = {
    "U1": ("TPS259470ARPWR", RPW, (9.6, 13.5, 0),
           ["RUN", "OV_WALL", "WALL_ACTIVE", "-", "WALL_5V", "LED_5V", "SLEW_WALL", GND,
            "LIMIT_WALL", "-"]),
    "U2": ("TPS259470ARPWR", RPW, (19.7, 13.5, 180),
           ["EN_BAT", "WALL_ACTIVE", "-", "-", "BAT_5V", "LED_5V", "SLEW_BAT", GND,
            "LIMIT_BAT", "-"]),
    "Q1": ("MMBT3904LT1G", "Package_TO_SOT_SMD:SOT-23", (9.25, 20.4, 0),
           ["MODE_BASE", GND, "WALL_N"]),
    "C1": ("1uF 16V X7R", C8, (6.3, 10.4, 0), ["WALL_5V", GND]),
    "C2": ("10nF 16V X7R", C, (13.1, 10.7, 0), ["SLEW_WALL", GND]),
    "C3": ("10uF 16V X7R", C8, (13.9, 8.7, 0), ["LED_5V", GND]),
    "C4": ("1uF 16V X7R", C8, (23.5, 16.3, 180), ["BAT_5V", GND]),
    "C5": ("10nF 16V X7R", C, (16.3, 15.4, 180), ["SLEW_BAT", GND]),
    "R1": ("15k 1%", R, (5.2, 13.65, 0), ["LOGIC_5V", "RUN"]),
    "R2": ("10k 1%", R, (5.2, 15.7, 0), ["RUN", GND]),
    "R3": ("35.7k 1%", R, (5.1, 18.35, 0), ["WALL_5V", "OV_WALL"]),
    "R4": ("10k 1%", R, (5.1, 20.25, 0), ["OV_WALL", GND]),
    "R5": ("1.18k 1%", R, (13.2, 13.275, 0), ["LIMIT_WALL", GND]),
    "R6": ("10k", R, (13.3, 16.75, 0), ["WALL_5V", "WALL_ACTIVE"]),
    "R7": ("56k", R, (15.6, 18.4, 0), ["WALL_ACTIVE", GND]),
    "R8": ("47k", R, (11.8, 19, 180), ["WALL_ACTIVE", "MODE_BASE"]),
    "R9": ("27.4k 1%", R, (23.2, 11.2, 180), ["BAT_5V", "EN_BAT"]),
    "R10": ("10k 1%", R, (23.2, 9.2, 180), ["EN_BAT", GND]),
    "R11": ("3.32k 1%", R, (16.2, 12, 180), ["LIMIT_BAT", GND]),
    "W1": ("WALL 5V", HEAVY, (3.7, 7, 0), ["WALL_5V"]),
    "W2": ("WALL GND", HEAVY, (3.7, 3.4, 0), [GND]),
    "W3": ("CHARGE 5V", WIRE, (7.6, 6.5, 0), ["WALL_5V"]),
    "W4": ("CHARGE GND", WIRE, (7.6, 3.4, 0), [GND]),
    "W5": ("BAT 5V", WIRE, (25.2, 20.45, 0), ["BAT_5V"]),
    "W6": ("LED 5V", WIRE, (15.2, 4.5, 0), ["LED_5V"]),
    "W7": ("LED GND", WIRE, (18.5, 4.5, 0), [GND]),
    "W8": ("LOGIC 5V", WIRE, (4.9, 22.8, 0), ["LOGIC_5V"]),
    "W9": ("WALL_N", WIRE, (10.5, 23.7, 0), ["WALL_N"]),
    "H1": ("M2", HOLE, (2, 25.6, 0), []),
    "H2": ("M2", HOLE, (26, 2, 0), []),
}

BOARDS = {"usb-pd60": (HEAD, 28, 31, 1.2), "led-power": (SELECTOR, 28, 28, 1.6)}

PIN_NAMES = {
    "usb-pd60": {
        "U1": ["CC1DB", "CC1", "NC", "CC2", "CC2DB", "RESET", "SCL", "SDA",
               "DISCH", "GND", "ATTACH", "ADDR0", "ADDR1", "POWER_OK3", "GPIO",
               "VBUS_EN_SNK", "A_B_SIDE", "VBUS_VS_DISCH", "ALERT", "POWER_OK2",
               "VREG_1V2", "VSYS", "VREG_2V7", "VDD", "EP"],
        "D1": ["K1", "K2", "A"],
        "D2": ["K", "A"],
    },
    "led-power": {"Q1": ["B", "E", "C"]},
}
for board, refs in (("usb-pd60", ("U2", "U3")), ("led-power", ("U1", "U2"))):
    for ref in refs:
        PIN_NAMES[board][ref] = ["EN", "OVLO", "AUXOFF", "FLT", "IN", "OUT", "DVDT",
                                 "GND", "ILM", "ITIMER"]

LAYOUT = {
    "usb-pd60": [
        ("U1",), ("J1", "D1", "D2", "C1", "C2", "C3"),
        ("U2", "C4", "C5", "R1", "R2", "R3", "R4", "R5", "R6", "R7"),
        ("U3", "C6", "C7", "C8", "R8", "R9", "R10", "R11", "R12"),
        ("W1", "W2", "W3", "W4", "W5", "W6", "H1", "H2"),
        ("R13", "R14", "R15", "TP1", "TP2", "TP3", "TP4"),
    ],
    "led-power": [
        ("U1", "U2"), ("Q1", "C1", "C2", "C3", "C4", "C5"),
        ("R1", "R2", "R3", "R4", "R5", "R6"),
        ("R7", "R8", "R9", "R10", "R11"),
        ("W1", "W2", "W3", "W4", "W5", "W6"),
        ("W7", "W8", "W9", "H1", "H2"),
    ],
}
