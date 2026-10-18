extends RefCounted

const CYCLE_SECONDS = 8.0
const BLACK_WIDTH = 0.36
const EDGE_WIDTH = 0.08
const DARK_NAMES = ["Rainbow • dark sectors", "Rainbow • dark spirals", "Rainbow • dark diagonals"]

# Both designs use the same spatial rainbow and eight-second colour cycle.
static func rainbow(position: Vector2, fibonacci: bool, seconds: float) -> Color:
	var angle=fposmod(atan2(position.x,position.y)/TAU,1.0)
	var radius=position.length()/0.0795 if fibonacci else 1.0
	return Color.from_hsv(fposmod(angle+2.0*radius-seconds/8.0,1.0),1.0,1.0)

# Coordinates are mapped metres, with +Y at the top. Ring mounting transforms
# belong to the geometry, never to these formulas. No LED count or wire index.
static func coordinates(position: Vector2, fibonacci: bool) -> Vector2:
	return position/0.0795 if fibonacci else position.normalized()

# Periodic distance gives a black plateau around each integer phase. The cubic
# smoothstep has zero slope at both ends. Each edge lasts EDGE_WIDTH*8 = 0.64 s.
static func dark_mask(phase: float) -> float:
	var distance=absf(fposmod(phase+0.5,1.0)-0.5)
	return smoothstep(BLACK_WIDTH/2.0,BLACK_WIDTH/2.0+EDGE_WIDTH,distance)

static func _dim(colour: Color, mask: float) -> Color:
	return Color(colour.r*mask,colour.g*mask,colour.b*mask,1.0)

static func dark_sectors(position: Vector2, fibonacci: bool, seconds: float) -> Color:
	var angle=atan2(position.x,position.y)/TAU
	return _dim(rainbow(position,fibonacci,seconds),dark_mask(2.0*angle-seconds/CYCLE_SECONDS))

static func dark_spirals(position: Vector2, fibonacci: bool, seconds: float) -> Color:
	var angle=atan2(position.x,position.y)/TAU
	var radius=coordinates(position,fibonacci).length()
	return _dim(rainbow(position,fibonacci,seconds),dark_mask(3.0*angle-2.0*radius+seconds/CYCLE_SECONDS))

static func dark_diagonals(position: Vector2, fibonacci: bool, seconds: float) -> Color:
	var point=coordinates(position,fibonacci)
	return _dim(rainbow(position,fibonacci,seconds),dark_mask(0.75*(point.x+point.y)-seconds/CYCLE_SECONDS))
