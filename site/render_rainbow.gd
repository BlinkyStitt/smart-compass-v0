extends SceneTree

func _initialize():
	_render.call_deferred()

func _lights(assembly, rows):
	assembly.colour_image.fill(Color.BLACK)
	for led in assembly.metadata.leds:
		var rgb = rows[int(led.group)][int(led.index)]
		var colour = Color(rgb[0], rgb[1], rgb[2])
		assert(colour.v > 0.10, "Every LED must remain lit")
		assembly.colour_image.set_pixel(int(led.index), int(led.group), colour)
	assembly.colours.update(assembly.colour_image)

func _render():
	var args = OS.get_cmdline_user_args()
	var frames = args[args.find("--frames") + 1]
	var light_frames = JSON.parse_string(FileAccess.get_file_as_string(frames.path_join("colours.json")))
	assert(light_frames.size() == 384)
	var assembly = load("res://main.tscn").instantiate()
	root.add_child(assembly)
	if assembly.metadata.is_empty():
		quit(1)
		return
	create_timer(600).timeout.connect(func(): push_error("Pride capture timed out"); quit(1))
	assembly.automated = true
	assembly.paused = true
	assembly.set_process(false)
	assembly.panel.visible = false
	assembly.caption.visible = false
	assembly._set_presentation(1)
	RenderingServer.render_loop_enabled = false
	RenderingServer.viewport_set_update_mode(root.get_viewport_rid(), RenderingServer.VIEWPORT_UPDATE_ALWAYS)
	# Record actual LED motion with a fixed camera before the gallery capture.
	assembly._night_pose(0)
	for frame in range(96):
		_lights(assembly, light_frames[frame])
		await assembly._settle()
		assert(root.get_texture().get_image().save_png(frames.path_join("fixed-%04d.png" % frame)) == OK)
	for frame in range(384):
		assembly._night_pose(frame)
		_lights(assembly, light_frames[frame])
		await assembly._settle()
		assert(root.get_texture().get_image().save_png(frames.path_join("rainbow-%04d.png" % frame)) == OK)
		if frame % 96 == 0: print("Pride frame ", frame, "/384")
	print("SITE RAINBOW SPIRAL CAPTURE PASS")
	quit()
