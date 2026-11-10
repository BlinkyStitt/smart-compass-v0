extends RefCounted

# An always-lit rainbow with one travelling spiral of brighter LEDs.
static func colour(position: Vector2, fibonacci: bool, seconds: float) -> Color:
	var angle = atan2(position.x, position.y) / TAU
	var radius = position.length() / 0.0795 if fibonacci else 1.0
	var spatial = angle + 2.0 * radius
	var crest = 0.5 + 0.5 * cos(TAU * (spatial - seconds / 4.0))
	var level = 0.45 + 0.55 * pow(crest, 3.0)
	return Color.from_hsv(fposmod(spatial - seconds / 8.0, 1.0), 1.0, level)
