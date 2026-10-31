extends SceneTree

# Isolated numerical export; no renderer, optical brightness or copied formulas.
const Patterns = preload("res://patterns.gd")

func _initialize():
	var args = OS.get_cmdline_user_args()
	if args.size() != 3:
		push_error("Expected scene.json, output prefix and sample count")
		quit(1)
		return
	var scene = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	var steps = int(args[2])
	assert(steps >= 512 and steps <= 8192)
	var identities = {}
	for led in scene.leds:
		var identity = "%d:%d" % [led.group, led.index]
		assert(not identities.has(identity), "Duplicate group/index identity")
		identities[identity] = true
	var names = ["rainbow", "dark-sectors", "dark-spirals", "dark-diagonals"]
	var methods = [Patterns.rainbow, Patterns.dark_sectors, Patterns.dark_spirals, Patterns.dark_diagonals]
	for style in range(names.size()):
		var samples = PackedFloat32Array()
		samples.resize(steps * scene.leds.size() * 3)
		var offset = 0
		for step in range(steps):
			var seconds = Patterns.CYCLE_SECONDS * step / steps
			for led in scene.leds:
				var point = Vector2(led.position_m[0], led.position_m[1])
				var colour: Color = methods[style].call(point, int(led.group) == 0, seconds)
				for channel in [colour.r, colour.g, colour.b]:
					assert(is_finite(channel) and channel >= 0 and channel <= 1)
					samples[offset] = channel
					offset += 1
		var file = FileAccess.open(args[1] + "-" + names[style] + ".f32", FileAccess.WRITE)
		assert(file != null, "Cannot write pattern samples")
		# PackedFloat32Array.to_byte_array() stores IEEE-754 little-endian values.
		file.store_buffer(samples.to_byte_array())
		file.close()
	print("PATTERN SAMPLE COMPLETE: %d steps, %d LEDs, four shared functions" % [steps, scene.leds.size()])
	quit(0)
