extends SceneTree

var plan: Dictionary
var shown = {}
var heading = Label.new()

func _initialize():
	_render.call_deferred()

func _view(assembly, bounds):
	var u = (bounds[0] + bounds[2]) / 2.0
	var v = (bounds[1] + bounds[3]) / 2.0
	assembly.target = Vector3(plan.right[0], plan.right[1], plan.right[2]) * u + Vector3(plan.up[0], plan.up[1], plan.up[2]) * v
	assembly.camera.size = maxf(bounds[3] - bounds[1], (bounds[2] - bounds[0]) * 720.0 / 1280.0) * 1.16
	assembly._update_camera()

func _blend_bounds(a, b, weight):
	return [lerpf(a[0], b[0], weight), lerpf(a[1], b[1], weight), lerpf(a[2], b[2], weight), lerpf(a[3], b[3], weight)]

func _pose(assembly, seconds):
	var amount = smoothstep(2.0, 7.0, seconds) * (1.0 - smoothstep(40.0, 46.0, seconds))
	for unit in plan.units:
		var offset = Vector3(unit.offset[0], unit.offset[1], unit.offset[2]) * amount
		for name in unit.parts:
			var mesh = assembly.meshes[name]
			mesh.transform = assembly.transforms[name]
			mesh.position += offset
	var bounds = _blend_bounds(plan.closed, plan.overview, amount)
	heading.text = "Assembled" if amount < 0.001 else "All fitted parts"
	var focus = ""
	var focus_weight = 0.0
	if seconds >= 9.0 and seconds < 37.0:
		var index = mini(int((seconds - 9.0) / 3.5), 7)
		var local_time = fmod(seconds - 9.0, 3.5)
		var detail = plan.views[index]
		var weight = smoothstep(0.0, 0.65, local_time) * (1.0 - smoothstep(2.85, 3.5, local_time))
		bounds = _blend_bounds(plan.overview, detail.bounds, weight)
		focus = detail.label
		focus_weight = weight
		if weight > 0.5: heading.text = detail.label
	for unit in plan.units:
		for name in unit.parts:
			assembly.meshes[name].transparency = focus_weight if not focus.is_empty() and unit.category != focus else 0.0
	_view(assembly, bounds)
	return amount

func _check_visible(assembly, unit):
	var screen = root.get_visible_rect().grow(-20)
	var rect = Rect2()
	var first = true
	for name in unit.parts:
		var mesh = assembly.meshes[name]
		assert(mesh.is_visible_in_tree() and mesh.transparency < 0.001, "Hidden fitted part: " + name)
		for corner in range(8):
			var point = mesh.global_transform * mesh.get_aabb().get_endpoint(corner)
			assert(not assembly.camera.is_position_behind(point), "Part behind camera: " + name)
			var pixel = assembly.camera.unproject_position(point)
			assert(screen.has_point(pixel), "Part clipped: " + name)
			rect = Rect2(pixel, Vector2.ZERO) if first else rect.expand(pixel)
			first = false
	return rect

func _render():
	var args = OS.get_cmdline_user_args()
	var frames = args[args.find("--frames") + 1]
	plan = JSON.parse_string(FileAccess.get_file_as_string(frames.path_join("layout.json")))
	var assembly = load("res://main.tscn").instantiate()
	root.add_child(assembly)
	if assembly.metadata.is_empty():
		quit(1)
		return
	create_timer(850).timeout.connect(func(): push_error("Assembly capture timed out"); quit(1))
	assembly.automated = true
	assembly.paused = true
	assembly.set_process(false)
	assembly.panel.visible = false
	assembly.caption.visible = false
	assembly._set_presentation(2)
	assembly.environment.background_mode = Environment.BG_COLOR
	assembly.environment.background_color = Color("#d7dbde")
	assembly.environment.ambient_light_energy = 0.8
	assembly.environment.glow_enabled = false
	assembly.sun.light_energy = 1.0
	assembly.camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	assembly.distance = 4.0
	assembly.yaw = 35.0
	assembly.pitch_angle = -20.0
	# Use the source CAD colours. World-space optical shaders only describe the
	# closed cavity and would paint translated parts incorrectly.
	for part in assembly.metadata.parts:
		var mesh = assembly.meshes[part.name]
		if part.name in plan.references:
			mesh.visible = false
			continue
		var material = mesh.mesh.surface_get_material(0).duplicate()
		material.vertex_color_use_as_albedo = false
		material.cull_mode = BaseMaterial3D.CULL_DISABLED
		if part.role in ["mirror", "rear_mirror"]:
			material.albedo_color = Color(0.55, 0.60, 0.65)
			material.metallic = 0.5
		elif part.role in ["packages", "ring_packages"]:
			material.albedo_color = Color(0.85, 0.85, 0.8)
		mesh.material_override = material
	heading.position = Vector2(32, 24)
	heading.add_theme_font_size_override("font_size", 32)
	heading.add_theme_color_override("font_color", Color("#17231d"))
	root.add_child(heading)
	RenderingServer.render_loop_enabled = false
	RenderingServer.viewport_set_update_mode(root.get_viewport_rid(), RenderingServer.VIEWPORT_UPDATE_ALWAYS)
	var indices = [0, 72, 168, 192, 258, 342, 426, 510, 594, 678, 762, 846, 960, 1056, 1151] if args.has("--preview") else range(1152)
	for frame in indices:
		var seconds = frame / 24.0
		var amount = _pose(assembly, seconds)
		if frame in [258, 342, 426, 510, 594, 678, 762, 846]:
			var label = plan.views[int((seconds - 9.0) / 3.5)].label
			var rectangles = []
			for unit in plan.units:
				if unit.category != label: continue
				var rect = _check_visible(assembly, unit)
				assert(maxf(rect.size.x, rect.size.y) >= 8.0, "Detail too small: " + unit.name)
				for previous in rectangles:
					assert(not rect.intersects(previous), "Components overlap in " + label)
				rectangles.append(rect)
				for name in unit.parts: shown[name] = true
		if frame in [0, 192, 960, 1151]:
			for unit in plan.units: _check_visible(assembly, unit)
		await assembly._settle()
		assert(root.get_texture().get_image().save_png(frames.path_join("assembly-%04d.png" % frame)) == OK)
		if frame % 96 == 0: print("Assembly frame ", frame, "/1152")
	var expected = assembly.metadata.parts.size() - plan.references.size()
	assert(shown.size() == expected, "Not every fitted part was shown")
	print("ALL FITTED PARTS VISIBLE: ", shown.size(), " CAD pieces in ", plan.units.size(), " separate units")
	print("SITE ASSEMBLY CAPTURE PASS")
	quit()
