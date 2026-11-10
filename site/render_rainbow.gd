extends SceneTree

const Spiral = preload("res://site_spiral.gd")

func _initialize():
	_render.call_deferred()

func _lights(assembly, seconds: float):
	assembly.colour_image.fill(Color.BLACK)
	for led in assembly.metadata.leds:
		var p = led.position_m
		var colour = Spiral.colour(Vector2(p[0], p[1]), int(led.group) == 0, seconds)
		assert(colour.v >= 0.44999, "Every LED must remain lit")
		assembly.colour_image.set_pixel(int(led.index), int(led.group), colour)
	assembly.colours.update(assembly.colour_image)

func _render():
	var args = OS.get_cmdline_user_args()
	var frames = args[args.find("--frames") + 1]
	var assembly = load("res://main.tscn").instantiate()
	root.add_child(assembly)
	if assembly.metadata.is_empty():
		quit(1)
		return
	create_timer(600).timeout.connect(func(): push_error("Spiral capture timed out"); quit(1))
	assembly.automated = true
	assembly.paused = true
	assembly.set_process(false)
	assembly.panel.visible = false
	assembly.caption.visible = false
	assembly._set_presentation(1)
	RenderingServer.render_loop_enabled = false
	RenderingServer.viewport_set_update_mode(root.get_viewport_rid(), RenderingServer.VIEWPORT_UPDATE_ALWAYS)
	# A fixed-camera witness makes light travel inspectable without camera motion.
	assembly._night_pose(0)
	for seconds in [0.0, 1.0, 4.0]:
		_lights(assembly, seconds)
		await assembly._settle()
		assert(root.get_texture().get_image().save_png(frames.path_join("fixed-%02d.png" % int(seconds))) == OK)
	for frame in range(384):
		assembly._night_pose(frame)
		_lights(assembly, frame / 24.0)
		await assembly._settle()
		assert(root.get_texture().get_image().save_png(frames.path_join("rainbow-%04d.png" % frame)) == OK)
		if frame % 96 == 0: print("Rainbow spiral frame ", frame, "/384")
	print("SITE RAINBOW SPIRAL CAPTURE PASS")
	quit()
