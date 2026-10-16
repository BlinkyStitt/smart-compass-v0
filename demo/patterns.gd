extends RefCounted

# Both designs use the same spatial rainbow and eight-second colour cycle.
static func rainbow(position: Vector2, fibonacci: bool, seconds: float) -> Color:
	var angle=fposmod(atan2(position.x,position.y)/TAU,1.0)
	var radius=position.length()/0.0795 if fibonacci else 1.0
	return Color.from_hsv(fposmod(angle+2.0*radius-seconds/8.0,1.0),1.0,1.0)
