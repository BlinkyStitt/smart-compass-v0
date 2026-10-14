extends RefCounted

# Illustration only. Two populations of phosphor traps give a bright initial
# glow and a weaker tail. These rates are not fitted to a printed sample.
const COUNTS = [256, 64, 84, 90]
const CHARGE_SECONDS = Vector2(6.0, 60.0)
const DECAY_SECONDS = Vector2(45.0, 900.0)
var image = Image.create(256, 4, false, Image.FORMAT_RGBAF)

func reset(fast: float = 0.0, slow: float = 0.0):
	image.fill(Color(fast, slow, 0.0, 1.0))

func advance(seconds: float, source: Image, brightness: float, ambient_drive: float):
	if seconds <= 0.0: return
	for group in range(1, 4):
		for index in range(COUNTS[group]):
			var led = source.get_pixel(index, group)
			# Shorter wavelengths excite the pigment more effectively. The RGB
			# weights and relative ambient intensity are unmeasured assumptions.
			var drive = maxf(0.0, brightness*(0.03*led.r+0.12*led.g+led.b)+ambient_drive)
			var charge = image.get_pixel(index, group)
			var rates = Vector2.ONE*drive/CHARGE_SECONDS+Vector2.ONE/DECAY_SECONDS
			var target = (Vector2.ONE*drive/CHARGE_SECONDS)/rates
			# Exact constant-input integration makes capture and live playback
			# independent of the frame rate.
			charge.r = target.x+(charge.r-target.x)*exp(-rates.x*seconds)
			charge.g = target.y+(charge.g-target.y)*exp(-rates.y*seconds)
			image.set_pixel(index, group, charge)
