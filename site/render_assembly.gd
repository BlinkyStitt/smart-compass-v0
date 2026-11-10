extends SceneTree

# Keep the CAD unchanged; spread its optical layers three times farther for display.
const EXPLODE_SCALE = 3.0

func _check_framing(assembly, amount: float) -> bool:
	var viewport = root.get_visible_rect().grow(-16)
	for part in assembly.metadata.parts:
		var bounds = part.bounds_m
		for corner in range(8):
			var point = Vector3(bounds[corner & 1][0], bounds[(corner >> 1) & 1][1], bounds[(corner >> 2) & 1][2])
			point.z += float(part.explosion_offset_m) * EXPLODE_SCALE * amount
			if assembly.camera.is_position_behind(point) or not viewport.has_point(assembly.camera.unproject_position(point)):
				push_error("Assembly framing clips " + str(part.name))
				return false
	return true
func _initialize():
	_render.call_deferred()

func _render():
	var args = OS.get_cmdline_user_args()
	var frames = args[args.find("--frames") + 1]
	var assembly = load("res://main.tscn").instantiate()
	root.add_child(assembly)
	if assembly.metadata.is_empty():
		quit(1)
		return
	create_timer(600).timeout.connect(func(): push_error("Assembly capture timed out"); quit(1))
	assembly.automated = true
	assembly.paused = true
	assembly.panel.visible = false
	assembly.caption.visible = false
	assembly._set_presentation(2)
	assembly.pattern = 0
	assembly.environment.background_mode = Environment.BG_COLOR
	assembly.environment.background_color = Color("#404040")
	RenderingServer.render_loop_enabled = false
	RenderingServer.viewport_set_update_mode(root.get_viewport_rid(), RenderingServer.VIEWPORT_UPDATE_ALWAYS)
	for frame in range(576):
		var phase = frame / 576.0
		var amount = smoothstep(0.08, 0.38, phase) * (1.0 - smoothstep(0.62, 0.92, phase))
		assembly._explode(amount)
		for part in assembly.metadata.parts:
			assembly.meshes[part.name].position.z += float(part.explosion_offset_m) * (EXPLODE_SCALE - 1.0) * amount
		assembly.distance = 0.60 + 0.30 * amount
		assembly.target = Vector3(0, 0, 0.0367 + 0.15 * amount)
		assembly.yaw = 35.0 + 30.0 * amount
		assembly.pitch_angle = -16.0
		assembly.pattern_time = 2.0
		assembly._update_camera()
		assembly._update_colours()
		if (frame % 96 == 0 or frame == 575) and not _check_framing(assembly, amount):
			quit(1)
			return
		await assembly._settle()
		var error = root.get_texture().get_image().save_png(frames.path_join("assembly-%04d.png" % frame))
		if error != OK:
			push_error("Cannot save assembly frame: " + str(error))
			quit(1)
			return
		if frame % 96 == 0: print("Assembly frame ", frame, "/576")
	print("SITE ASSEMBLY CAPTURE PASS")
	quit()
