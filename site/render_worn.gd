extends SceneTree

# Site stills use soft front fill so the wearer's pose and scale stay visible.
func _initialize():
	_render.call_deferred()

func _render():
	var args = OS.get_cmdline_user_args()
	var output = args[args.find("--output") + 1]
	var assembly = load("res://main.tscn").instantiate()
	root.add_child(assembly)
	if assembly.metadata.is_empty():
		quit(1)
		return
	create_timer(60).timeout.connect(func(): push_error("Wearing-scale capture timed out"); quit(1))
	assembly.automated = true
	assembly.paused = true
	assembly.panel.visible = false
	assembly._set_presentation(0)
	assembly.pattern_time = 2.0
	# Light the mannequin without washing out the pendant's mirror or LEDs.
	for surface in assembly.mannequin.surfaces:
		surface.layers = 2
	var fill = OmniLight3D.new()
	fill.position = Vector3(-0.8, 1.0, 2.0)
	fill.light_color = Color(0.85, 0.90, 1.0)
	fill.light_energy = 1.0
	fill.light_cull_mask = 2
	fill.omni_range = 5.0
	fill.shadow_enabled = true
	assembly.add_child(fill)
	RenderingServer.render_loop_enabled = false
	RenderingServer.viewport_set_update_mode(root.get_viewport_rid(), RenderingServer.VIEWPORT_UPDATE_ALWAYS)
	assembly._update_colours()
	await assembly._settle()
	var error = root.get_texture().get_image().save_png(output)
	if error != OK:
		push_error("Cannot save wearing-scale image: " + str(error))
		quit(1)
		return
	print("SITE WEARING SCALE CAPTURE PASS")
	quit()
