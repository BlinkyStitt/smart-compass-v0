"""Current limits for the Rev B Sparkle Motion display.

All current values are in units of 1/255 mA. A full RGB channel costs
20 mA and every powered pixel costs 1 mA with all channels off.
"""

PIXEL_COUNTS = (256, 70, 70, 70)
BATTERY_DRIVE = 5  # 2% electrical duty
WALL_DRIVE = 34  # 13.3% electrical duty
BATTERY_BUDGET = 795  # mA for the whole LED rail
WALL_BUDGET = 2400
WALL_BRANCH_BUDGETS = (1320, 410, 410, 410)


def rainbow_frame(phases, elapsed, wall):
    drive = WALL_DRIVE if wall else BATTERY_DRIVE
    budget = WALL_BUDGET if wall else BATTERY_BUDGET
    output = []
    for phase_group in phases:
        colors = []
        for phase in phase_group:
            hue = ((phase - elapsed / 8) % 1) * 6
            sector = int(hue)
            ramp = int((hue - sector) * drive + 0.5)
            colors.append((
                (drive, ramp, 0), (drive - ramp, drive, 0),
                (0, drive, ramp), (0, drive - ramp, drive),
                (ramp, 0, drive), (drive, 0, drive - ramp),
            )[sector])
        output.append(colors)

    # Scale all channels together so the pattern stays saturated. Use integer
    # floor after scaling so rounding cannot put the frame over its limit.
    channel_sums = [sum(sum(color) for color in colors) for colors in output]
    scale = min(1024, (budget - sum(PIXEL_COUNTS)) * 255 * 1024
                // (20 * sum(channel_sums)))
    if wall:
        for count, limit, channel_sum in zip(PIXEL_COUNTS, WALL_BRANCH_BUDGETS, channel_sums):
            scale = min(scale, (limit - count) * 255 * 1024 // (20 * channel_sum))
    if scale < 1024:
        return [[tuple(channel * scale // 1024 for channel in color)
                 for color in colors] for colors in output]
    return output
