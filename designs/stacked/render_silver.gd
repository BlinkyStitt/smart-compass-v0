extends SceneTree

func _initialize():
	_render.call_deferred()

func _render():
	var args = OS.get_cmdline_user_args()
	var frames = args[args.find("--frames") + 1]
	var material_scene = JSON.parse_string(FileAccess.get_file_as_string(args[args.find("--material-scene") + 1]))
	var silver = material_scene.ring_materials.silver.render
	var assembly = load("res://main.tscn").instantiate()
	root.add_child(assembly)
	create_timer(600).timeout.connect(func(): push_error("Silver capture timed out"); quit(1))
	assembly.automated = true
	assembly.paused = true
	assembly.panel.visible = false
	assembly._set_presentation(1)
	assembly.pattern = 0
	assembly.caption.text = "Silver PETG | Rainbow | worn night preview | unmeasured optics"
	var absorption = Vector3(silver.absorption_per_mm[0], silver.absorption_per_mm[1], silver.absorption_per_mm[2])
	for part in assembly.metadata.parts:
		if part.role not in ["mirror", "rear_mirror", "side", "inner"]: continue
		var material = assembly.meshes[part.name].material_override
		material.set_shader_parameter("ring_absorption", absorption)
		material.set_shader_parameter("ring_prompt_green", float(silver.prompt_green))
		material.set_shader_parameter("ring_stored_emission", float(silver.stored_emission))
		material.set_shader_parameter("diffusion", float(silver.diffusion))
		if part.role in ["side", "inner"]:
			material.set_shader_parameter("ring_albedo", Vector3(silver.albedo[0], silver.albedo[1], silver.albedo[2]))
			material.set_shader_parameter("ring_roughness", float(silver.roughness))
			material.set_shader_parameter("ring_metallic", float(silver.metallic))
			material.set_shader_parameter("transmission", float(silver.transmission))
		else:
			material.set_shader_parameter("diffuser_transmission", float(silver.transmission))
		assert(material.get_shader_parameter("ring_absorption") == absorption)
		assert(is_zero_approx(material.get_shader_parameter("ring_prompt_green")))
		assert(is_zero_approx(material.get_shader_parameter("ring_stored_emission")))
	RenderingServer.render_loop_enabled = false
	RenderingServer.viewport_set_update_mode(root.get_viewport_rid(), RenderingServer.VIEWPORT_UPDATE_ALWAYS)
	for frame in range(assembly.CaptureView.FRAMES):
		assembly._night_pose(frame)
		assembly.pattern_time = frame / assembly.CaptureView.FPS
		assembly._update_colours()
		await assembly._settle()
		var error = root.get_texture().get_image().save_png(frames.path_join("silver-%04d.png" % frame))
		if error != OK:
			push_error("Cannot save silver frame: " + str(error))
			quit(1)
			return
		if frame % 96 == 0: print("Silver frame ", frame, "/384")
	print("SITE SILVER CAPTURE PASS")
	quit()
