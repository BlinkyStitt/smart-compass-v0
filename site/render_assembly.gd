extends SceneTree

# Reuse the demo's complete explosion and reassembly motion with current CAD.
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
	assembly._set_presentation(2)
	assembly._set_ring_material(0)
	assembly._reset_glow(0.35, 0.20)
	assembly._set_finish(0)
	assembly.pattern = 0
	assembly.environment.background_mode = Environment.BG_COLOR
	assembly.environment.background_color = Color("#404040")
	RenderingServer.render_loop_enabled = false
	RenderingServer.viewport_set_update_mode(root.get_viewport_rid(), RenderingServer.VIEWPORT_UPDATE_ALWAYS)
	for frame in range(576):
		assembly._exploded_pose(frame / 576.0)
		assembly._update_colours()
		await assembly._settle()
		var error = root.get_texture().get_image().save_png(frames.path_join("assembly-%04d.png" % frame))
		if error != OK:
			push_error("Cannot save assembly frame: " + str(error))
			quit(1)
			return
		if frame % 96 == 0: print("Assembly frame ", frame, "/576")
	print("SITE ASSEMBLY CAPTURE PASS")
	quit()
