extends Node3D

const PATTERNS = ["Spiral rainbow", "Rotating spokes", "Radial waves", "Solid red", "Solid green", "Solid blue", "White", "Single-pixel chase", "Ocean gradient", "Sunset gradient"]
const FINISHES = ["Selected • black LED centre", "Comparison • full mirror"]
const RING_MATERIALS = ["glow", "silver"]
const LIGHTING = ["Night", "Indoor", "Overcast", "Bright sun"]
const Glow = preload("res://glow.gd")
const Mannequin = preload("res://mannequin.gd")
const Patterns = preload("res://patterns.gd")
const CaptureView = preload("res://capture_view.gd")
const Playa = preload("res://playa.gd")
const PRESENTATIONS = ["Night • worn mannequin", "Night • pendant close-up", "Design inspection"]
const COUNTS = Glow.COUNTS
var glow = Glow.new()
var ring_material = 0
var ring_transmit_slider: HSlider
var ring_diffuse_slider: HSlider
var glow_buttons = []
var charge_texture: ImageTexture
var metadata: Dictionary
var meshes = {}
var assembled_transforms = {}
var explosion_offsets = {}
var cell_materials = []
var package_materials = []
var sleeve_materials = []
var cavity_materials = []
var centre_materials = []
var image_data = Image.create(256, 4, false, Image.FORMAT_RGBAF)
var colour_texture: ImageTexture
var camera = Camera3D.new()
var environment = Environment.new()
var sun = DirectionalLight3D.new()
var sky_material = ProceduralSkyMaterial.new()
var infinity_backdrop = Playa.new()
var mannequin = Mannequin.new()
var presentation = 2
var presentation_option: OptionButton
var lighting_option: OptionButton
var distance = 0.6
var yaw = 0.0
var pitch_angle = 0.0
var target = Vector3(0, 0, 0.0367)
var pattern_time = 0.0
var pattern = 0
var finish = 0
var lighting = 1
var paused = false
var brightness = 2.0
var groups = [true, true, true, true]
var reflectance = 0.70
var transmission = 0.09
var diffuser_transmission = 0.4
var diffusion = 0.65
var central_diffusion = 0.65
var exposure = 1.0
var ambient = 0.35
var light_angle = 35.0
var status: Label
var panel: PanelContainer
var reflect_slider: HSlider
var transmit_slider: HSlider
var ambient_slider: HSlider
var capture_dir = ""
var automated = false
var asset_dir = ""

func _ready():
	asset_dir = ProjectSettings.globalize_path("res://../hardware/enclosure/exports/")
	var args = OS.get_cmdline_user_args()
	for i in range(args.size()):
		if args[i] == "--assets": asset_dir = args[i+1]
		if args[i] == "--capture": capture_dir = args[i+1]
	automated = args.has("--check") or args.has("--benchmark") or args.has("--gpu-check") or not capture_dir.is_empty()
	# The same freshness gate also protects direct editor/game launches.
	if not args.has("--build-validation"):
		var result = []
		var code = OS.execute("python3", [ProjectSettings.globalize_path("res://../hardware/enclosure/cad.py"), "check"], result, true)
		if code != 0:
			push_error("Stale CAD assets. Run just cad. " + str(result))
			get_tree().quit(1)
			return
	var text = FileAccess.get_file_as_string(asset_dir.path_join("scene.json"))
	var parsed = JSON.parse_string(text)
	if not parsed is Dictionary:
		push_error("Missing or invalid scene metadata")
		get_tree().quit(1)
		return
	metadata = parsed
	reflectance=float(metadata.comparison.front_reflectance)
	transmission=float(metadata.comparison.front_transmission)
	if automated:
		get_tree().create_timer(600).timeout.connect(func(): push_error("Automation timed out"); get_tree().quit(1))
	if not capture_dir.is_empty() or args.has("--gpu-check"):
		# Explicit capture draws also work when macOS hides the window.
		RenderingServer.render_loop_enabled=false
		RenderingServer.viewport_set_update_mode(get_viewport().get_viewport_rid(),RenderingServer.VIEWPORT_UPDATE_ALWAYS)
	colour_texture = ImageTexture.create_from_image(image_data)
	glow.reset(0.35,0.20)
	charge_texture = ImageTexture.create_from_image(glow.image)
	var document = GLTFDocument.new()
	var state = GLTFState.new()
	var error = document.append_from_file(asset_dir.path_join("amulet.glb"), state)
	if error != OK:
		push_error("GLB import failed: " + str(error))
		get_tree().quit(1)
		return
	var assembly = document.generate_scene(state)
	add_child(assembly)
	_collect(assembly)
	_prepare_explosion()
	_make_materials()
	_make_world()
	_make_controls()
	_set_finish(0)
	_set_lighting(1)
	_update_camera()
	_update_colours()
	if not automated: _set_presentation(0)
	if args.has("--check"):
		_run_checks()
	elif args.has("--gpu-check"):
		_gpu_checks.call_deferred()
	elif not capture_dir.is_empty():
		_capture.call_deferred()
	elif args.has("--benchmark"):
		_benchmark.call_deferred()

func _collect(node):
	if node is MeshInstance3D: meshes[str(node.name)] = node
	for child in node.get_children(): _collect(child)

# Illustration distances in metres. The stencil lifts separately from the
# populated LED board. Each ring/strip pair stays together.
func _prepare_explosion():
	var layers = {
		0.36: ["FrontCentre", "FrontMirrorCoating", "FrontRim"],
		0.28: ["FibonacciBaffle", "CircleRimFoot0", "CircleRimFoot1", "CircleRimFoot2"],
		0.22: ["CirclePCB", "CircleLEDs"],
		0.19: ["HaloRing", "HaloLightShield", "HaloStripSeam", "HaloLEDs"],
		0.14: ["InnerRing", "InnerLightShield", "InnerStripSeam", "InnerLEDs"],
		0.085: ["RearMirror"],
		0.04: ["OpticalDeck", "EdgeDiffuser", "OuterLightShield", "OuterStripSeam", "OuterLEDs"],
		0.0: ["BarrelFrame"],
		-0.10: ["RearPlate", "BatteryEnvelope0", "SparklePCBWithHoles", "blackpillPCB", "gpsPCB", "imuPCB", "radioPCB", "sensePCB", "powerPCB", "ExternalPowerBlank", "RearButton0", "RearButton1", "RearButton2", "ControlMembrane0", "ControlMembrane1", "ControlMembrane2"],
		-0.13: ["NecklaceLink0", "NecklaceLink1", "HatchGasket", "VentMembrane0", "VentMembrane1", "VentMembrane2", "VentMembrane3"],
		-0.16: ["ServiceCover", "VentGuard0", "VentGuard1", "VentGuard2", "VentGuard3"],
	}
	for offset in layers:
		for name in layers[offset]:
			assert(meshes.has(name), "Unknown exploded part: " + name)
			explosion_offsets[name] = Vector3(0, 0, offset)
	for part in metadata.parts:
		if part.role == "cell": explosion_offsets[part.name] = explosion_offsets.CirclePCB
		if part.role == "hardware": explosion_offsets[part.name] = Vector3(0, 0, part.explosion_offset_m)
		assert(explosion_offsets.has(part.name), "Assign an exploded layer to " + part.name)
		assembled_transforms[part.name] = meshes[part.name].transform

func _set_explosion(amount: float):
	for name in meshes:
		var mesh = meshes[name]
		mesh.transform = assembled_transforms[name]
		mesh.position += explosion_offsets[name]*amount
		if mesh.material_override is ShaderMaterial and mesh.material_override in sleeve_materials:
			# Keep the direct light field attached to the moved sleeve and LED row.
			mesh.material_override.set_shader_parameter("assembly_offset", explosion_offsets[name]*amount)
	for material in cavity_materials:
		# Separated mirrors no longer form the canonical 11.2 mm cavity.
		material.set_shader_parameter("cavity_closed", amount == 0.0)
	# Fade both separated mirrors for the assembly illustration. Geometry
	# transparency returns to zero when the real mirror cavity closes again.
	for name in ["FrontMirrorCoating","RearMirror"]:
		meshes[name].transparency = 0.65*amount
	# These faces approximate light at the assembled diffuser plane. They are
	# not physical pieces of the stencil or LEDs. Reveal the package emitters
	# when the stencil lifts, rather than carrying lit aperture shapes with it.
	for part in metadata.parts:
		if part.role == "cell": meshes[part.name].visible = amount == 0.0

func _exploded_pose(phase: float):
	var amount = smoothstep(0.08, 0.38, phase)*(1.0-smoothstep(0.62, 0.92, phase))
	_set_explosion(amount)
	distance = 0.60+0.25*amount
	target = Vector3(0, 0, 0.0367+0.075*amount)
	yaw = 35.0+30.0*amount+6.0*sin(TAU*phase)
	pitch_angle = -16.0
	pattern_time = 16.0*phase
	_update_camera()

func _shader(path):
	var material = ShaderMaterial.new()
	material.shader = load(path)
	material.set_shader_parameter("colours", colour_texture)
	if path in ["res://sleeve.gdshader","res://optics.gdshader"]:
		material.set_shader_parameter("charges", charge_texture)
	return material

func _make_materials():
	var optics = metadata.optics
	for part in metadata.parts:
		var mesh = meshes.get(part.name)
		assert(mesh != null, "Missing named GLB mesh " + part.name)
		if part.name == "CircleLEDs":
			var material = _shader("res://package.gdshader")
			mesh.material_override = material
			package_materials.append(material)
		elif part.role == "cell":
			var material = _shader("res://cell.gdshader")
			var index = int(part.name.trim_prefix("Cell"))
			material.set_shader_parameter("index", index)
			material.set_shader_parameter("led_position", Vector3(metadata.leds[index].position_m[0], metadata.leds[index].position_m[1], metadata.leds[index].position_m[2]))
			mesh.material_override = material
			cell_materials.append(material)
		elif part.role == "cavity":
			var material = _shader("res://optics.gdshader")
			for key in ["front_z", "rear_z", "halo_radius", "inner_radius", "strip_z", "pitch"]:
				material.set_shader_parameter(key, float(optics[key]))
			material.set_shader_parameter("seam_gap", float(optics.ring_seam_gap))
			material.set_shader_parameter("pitch_radii", Vector3(optics.ring_pitch_radii[0], optics.ring_pitch_radii[1], optics.ring_pitch_radii[2]))
			material.set_shader_parameter("ring_wall_mm", Vector3(optics.ring_wall_mm[0],optics.ring_wall_mm[1],optics.ring_wall_mm[2]))
			mesh.material_override = material
			cavity_materials.append(material)
		elif part.role == "sleeve":
			var group = 3
			if part.name == "HaloRing": group = 1
			if part.name == "InnerRing": group = 2
			var material = _shader("res://sleeve.gdshader")
			material.set_shader_parameter("group", group)
			material.set_shader_parameter("count", COUNTS[group])
			material.set_shader_parameter("pitch_radius", float(optics.ring_pitch_radii[group-1]))
			material.set_shader_parameter("seam_gap", float(optics.ring_seam_gap))
			material.set_shader_parameter("pitch", float(optics.pitch))
			material.set_shader_parameter("led_z", float(optics.edge_z if group == 3 else optics.strip_z))
			material.set_shader_parameter("wall_mm", float(optics.ring_wall_mm[group-1]))
			mesh.material_override = material
			sleeve_materials.append(material)
		elif part.role == "centre":
			var material = _shader("res://centre.gdshader")
			mesh.material_override = material
			centre_materials.append(material)
		elif part.name == "RearMirror":
			var material = StandardMaterial3D.new()
			var r=float(metadata.comparison.rear_reflectance)
			var t=float(metadata.comparison.rear_transmission)
			material.albedo_color = Color(r/(1.0-t),r/(1.0-t),r/(1.0-t),1.0-t)
			material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			material.metallic = 1.0
			material.roughness = 0.06
			mesh.material_override = material
	_update_optics()

func _make_world():
	add_child(camera)
	camera.current = true
	camera.near = 0.005
	camera.far = 30.0
	camera.fov = 38.0
	var world = WorldEnvironment.new()
	world.environment = environment
	add_child(world)
	environment.background_mode = Environment.BG_SKY
	infinity_backdrop.visible=false
	add_child(infinity_backdrop)
	infinity_backdrop.build()
	var sky = Sky.new()
	sky.sky_material = sky_material
	environment.sky = sky
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color(0.75,0.82,1.0)
	environment.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	environment.tonemap_exposure = exposure
	environment.glow_enabled = true
	environment.glow_intensity = 0.45
	add_child(sun)
	sun.shadow_enabled = true
	add_child(mannequin)
	mannequin.build()
	mannequin.visible = false

func _set_infinity_backdrop(enabled):
	infinity_backdrop.visible = enabled
	environment.background_mode = Environment.BG_SKY

func _set_presentation(value):
	presentation = value
	if presentation_option: presentation_option.select(value)
	mannequin.visible = value < 2
	_set_infinity_backdrop(value < 2)
	_set_lighting(0 if value < 2 else 1)
	_reset()

func _night_pose(frame: float):
	distance=CaptureView.DISTANCE
	target=CaptureView.TARGET
	yaw=CaptureView.yaw(frame)
	pitch_angle=CaptureView.pitch(frame)
	_update_camera()

func _make_controls():
	var layer = CanvasLayer.new()
	add_child(layer)
	panel = PanelContainer.new()
	panel.position = Vector2(12,12)
	panel.size = Vector2(292,696)
	layer.add_child(panel)
	var scroll = ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(292,696)
	panel.add_child(scroll)
	var box = VBoxContainer.new()
	box.custom_minimum_size.x = 270
	box.add_theme_constant_override("separation", 7)
	scroll.add_child(box)
	_label(box,"AMULET / OPTICAL PREVIEW",18)
	_label(box,"Assumed optics • no measured brightness",12)
	presentation_option = _option(box,"Presentation",PRESENTATIONS,presentation,_set_presentation)
	_option(box,"Ring material",[metadata.ring_materials.glow.label,metadata.ring_materials.silver.label],0,_set_ring_material)
	_option(box,"Front finish",FINISHES,0,_set_finish)
	_option(box,"Pattern",PATTERNS,0,func(v): pattern=v)
	var pause_button = CheckButton.new()
	pause_button.text = "Pause pattern"
	pause_button.toggled.connect(func(v): paused=v)
	box.add_child(pause_button)
	_slider(box,"LED brightness",0,8,brightness,func(v): brightness=v; _update_optics())
	var switches = HBoxContainer.new()
	box.add_child(switches)
	for i in range(4):
		var button = CheckBox.new()
		button.text = metadata.groups[i]
		button.add_theme_font_size_override("font_size",11)
		button.button_pressed = true
		button.toggled.connect(func(v): groups[i]=v; _update_colours())
		switches.add_child(button)
	lighting_option = _option(box,"Viewing light",LIGHTING,1,_set_lighting)
	ambient_slider = _slider(box,"Ambient intensity",0,3,ambient,func(v): ambient=v; _update_light())
	_slider(box,"Light direction (degrees)",-180,180,light_angle,func(v): light_angle=v; _update_light())
	_slider(box,"Exposure (fixed unless changed)",0.1,4,exposure,func(v): exposure=v; environment.tonemap_exposure=v)
	reflect_slider = _slider(box,"Mirror film reflectance",0,1,reflectance,func(v):
		reflectance=v
		transmission=minf(transmission,1-v)
		_sync_slider(transmit_slider,transmission)
		_update_optics())
	transmit_slider = _slider(box,"Mirror film transmission",0,1,transmission,func(v):
		transmission=v
		reflectance=minf(reflectance,1-v)
		_sync_slider(reflect_slider,reflectance)
		_update_optics())
	ring_transmit_slider = _slider(box,"Ring transmission (assumed)",0,1,diffuser_transmission,func(v): diffuser_transmission=v; _update_optics())
	ring_diffuse_slider = _slider(box,"Ring diffusion (assumed)",0,1,diffusion,func(v): diffusion=v; _update_optics())
	glow_buttons.append(_button(box,"Precharge glow (illustration)",func(): _reset_glow(0.85,0.65)))
	glow_buttons.append(_button(box,"Clear stored glow",func(): _reset_glow()))
	_slider(box,"Centre diffusion (assumed)",0,1,central_diffusion,func(v): central_diffusion=v; _update_optics())
	var views = HBoxContainer.new()
	box.add_child(views)
	for item in [["Front",0,0],["¾",40,-12],["Edge",90,0],["Rear",180,0]]:
		_button(views,item[0],func(): yaw=item[1]; pitch_angle=item[2]; _update_camera())
	var distances = HBoxContainer.new()
	box.add_child(distances)
	for value in [0.3,0.5,1.0,2.0,5.0,10.0]:
		_button(distances,str(value)+" m",func(): distance=value; _update_camera())
	_button(box,"Reset view (R)",_reset)
	status = _label(box,"",12)
	_label(box,"Drag: orbit • Right drag: pan\nWheel: distance • R: reset view\nFinish switches preserve time and view.",12)

func _label(parent,text,size):
	var label = Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size",size)
	parent.add_child(label)
	return label

func _button(parent,text,callback):
	var button = Button.new()
	button.text = text
	button.add_theme_font_size_override("font_size",11)
	button.pressed.connect(callback)
	parent.add_child(button)
	return button

func _option(parent,title,items,selected,callback):
	_label(parent,title,12)
	var option = OptionButton.new()
	for item in items: option.add_item(item)
	option.select(selected)
	option.item_selected.connect(callback)
	parent.add_child(option)
	return option

func _slider(parent,title,low,high,value,callback):
	var row = HBoxContainer.new()
	parent.add_child(row)
	var label = _label(row,title,11)
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var number = _label(row,"%.2f" % value,11)
	var slider = HSlider.new()
	slider.min_value=low
	slider.max_value=high
	slider.step=0.01 if high<=8 else 1.0
	slider.value=value
	slider.value_changed.connect(func(v): callback.call(v); number.text="%.2f" % v)
	slider.set_meta("readout",number)
	parent.add_child(slider)
	return slider

func _sync_slider(slider,value):
	if slider:
		slider.set_value_no_signal(value)
		slider.get_meta("readout").text="%.2f" % value

func _set_finish(value):
	finish = value
	for part in metadata.parts:
		meshes[part.name].visible = true
	_update_optics()

func _apply_ring_response(material, choice):
	var response=choice.render
	material.set_shader_parameter("ring_absorption",Vector3(response.absorption_per_mm[0],response.absorption_per_mm[1],response.absorption_per_mm[2]))
	material.set_shader_parameter("ring_prompt_green",float(response.prompt_green))
	material.set_shader_parameter("ring_stored_emission",float(response.stored_emission))

func _set_ring_material(value):
	ring_material=value
	var response=metadata.ring_materials[RING_MATERIALS[value]].render
	diffuser_transmission=float(response.transmission)
	diffusion=float(response.diffusion)
	_sync_slider(ring_transmit_slider,diffuser_transmission)
	_sync_slider(ring_diffuse_slider,diffusion)
	for button in glow_buttons: button.disabled=RING_MATERIALS[value]!="glow"
	_update_optics()

func _update_optics():
	var choice=metadata.ring_materials[RING_MATERIALS[ring_material]]
	for material in sleeve_materials+cavity_materials: _apply_ring_response(material,choice)
	for material in cavity_materials:
		for entry in [["reflectance",reflectance],["transmission",transmission],["rear_reflectance",metadata.comparison.rear_reflectance],["diffuser_transmission",diffuser_transmission],["diffusion",diffusion],["brightness",brightness],["external_reflectance",metadata.comparison.front_external_reflectance]]:
			material.set_shader_parameter(entry[0],entry[1])
	for material in sleeve_materials:
		material.set_shader_parameter("ring_albedo",Vector3(choice.render.albedo[0],choice.render.albedo[1],choice.render.albedo[2]))
		material.set_shader_parameter("ring_roughness",float(choice.render.roughness))
		material.set_shader_parameter("ring_metallic",float(choice.render.metallic))
		material.set_shader_parameter("transmission",diffuser_transmission)
		material.set_shader_parameter("diffusion",diffusion)
		material.set_shader_parameter("brightness",brightness)
	for material in cell_materials:
		material.set_shader_parameter("brightness",brightness)
		material.set_shader_parameter("diffusion",central_diffusion)
		material.set_shader_parameter("transmission",1.0)
	for material in package_materials:
		material.set_shader_parameter("brightness",brightness)
	for material in centre_materials:
		material.set_shader_parameter("sheet_reflectance",metadata.comparison.front_external_reflectance if finish == 1 else metadata.comparison.black_acrylic_surface_reflectance)
		material.set_shader_parameter("sheet_transmission",transmission if finish == 1 else metadata.comparison.black_acrylic_transmission)

func _set_lighting(value):
	lighting = value
	if lighting_option: lighting_option.select(value)
	ambient = [0.015,0.35,1.2,2.0][value]
	sun.light_energy = [0.03,0.8,0.65,6.0][value]
	sky_material.sky_top_color = [Color(0.003,0.005,0.015),Color(0.11,0.14,0.20),Color(0.52,0.60,0.68),Color(0.14,0.36,0.75)][value]
	sky_material.sky_horizon_color = [Color(0.012,0.015,0.02),Color(0.30,0.28,0.25),Color(0.72,0.75,0.78),Color(0.72,0.80,0.90)][value]
	sky_material.ground_bottom_color = Color(0.018,0.020,0.024)
	sky_material.ground_horizon_color = sky_material.sky_horizon_color
	environment.background_energy_multiplier = [0.06,0.7,1.1,1.8][value]
	_sync_slider(ambient_slider,ambient)
	_update_light()

func _update_light():
	environment.ambient_light_energy = ambient
	sun.rotation_degrees = Vector3(-35,light_angle,0)

func _update_camera():
	var az = deg_to_rad(yaw)
	var el = deg_to_rad(pitch_angle)
	camera.position = target+distance*Vector3(sin(az)*cos(el),sin(el),cos(az)*cos(el))
	camera.look_at(target,Vector3.UP)

func _reset():
	distance=3.5 if presentation==0 else (0.46 if presentation==1 else 0.6)
	yaw=0
	pitch_angle=-3.0 if presentation==0 else 0.0
	target=Vector3(0,-0.10 if presentation==0 else 0.0,float(metadata.optics.front_z))
	_update_camera()

func _unhandled_input(event):
	if automated: return
	if event is InputEventMouseMotion:
		if event.button_mask & MOUSE_BUTTON_MASK_LEFT:
			yaw -= event.relative.x*0.35
			pitch_angle = clampf(pitch_angle+event.relative.y*0.35,-85,85)
		elif event.button_mask & MOUSE_BUTTON_MASK_RIGHT:
			target += (-camera.global_basis.x*event.relative.x+camera.global_basis.y*event.relative.y)*distance*0.001
		_update_camera()
	elif event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_WHEEL_UP: distance=maxf(0.15,distance*0.9)
		if event.button_index == MOUSE_BUTTON_WHEEL_DOWN: distance=minf(15,distance/0.9)
		_update_camera()
	elif event is InputEventKey and event.pressed and event.keycode == KEY_R: _reset()

func _process(delta):
	if metadata.is_empty(): return
	if not paused and not automated: pattern_time+=delta
	_update_colours()
	if not automated: _advance_glow(delta)
	if status:
		status.text="%.2f m • yaw %.1f° • tilt %.1f°\nt = %.2f s • film R + T = %.2f\n%.1f fps • centre diffusion %.2f" % [distance,yaw,pitch_angle,pattern_time,reflectance+transmission,Engine.get_frames_per_second(),central_diffusion]

func _pattern_colour(led,time: float):
	var p = led.position_m
	var angle = fposmod(atan2(p[0],p[1])/TAU,1.0)
	var radius = sqrt(p[0]*p[0]+p[1]*p[1])/0.0795 if int(led.group)==0 else 1.0
	match pattern:
		0: return Patterns.rainbow(Vector2(p[0],p[1]),int(led.group)==0,time)
		1: return Color.from_hsv(fposmod(angle-time/8,1.0),1,1)*pow(maxf(0,cos(TAU*(3*angle-3*time/8))),8)
		2: return Color.from_hsv(fposmod(radius-time/8,1.0),1,1)*(0.1+0.9*(1-absf(2*fposmod(2*radius-time/4,1.0)-1)))
		8: return Color.from_hsv(0.55+0.12*sin(TAU*(angle+2*radius-time/8)),1,1)
		9: return Color.from_hsv(fposmod(0.98+0.14*(0.5+0.5*sin(TAU*(angle+2*radius-time/8))),1),1,1)
		3: return Color.RED
		4: return Color.GREEN
		5: return Color.BLUE
		6: return Color.WHITE
		7:
			var offset = [0,256,320,404][int(led.group)]
			return Color.WHITE if (int(time*20)%494)==offset+int(led.index) else Color.BLACK
	return Color.BLACK

func _update_colours():
	for led in metadata.leds:
		var color = _pattern_colour(led,pattern_time) if groups[int(led.group)] else Color.BLACK
		color.a=1.0
		image_data.set_pixel(int(led.index),int(led.group),color)
	colour_texture.update(image_data)

func _reset_glow(fast: float = 0.0, slow: float = 0.0):
	glow.reset(fast,slow)
	charge_texture.update(glow.image)

func _advance_glow(seconds: float):
	if RING_MATERIALS[ring_material]!="glow": return
	glow.advance(seconds,image_data,brightness,ambient*0.08+sun.light_energy*0.01)
	charge_texture.update(glow.image)

func _check_glow():
	var source=Image.create(256,4,false,Image.FORMAT_RGBAF)
	source.fill(Color.WHITE)
	var charged=Glow.new()
	charged.reset()
	charged.advance(60.0,source,2.0,0.0)
	var lit=charged.image.get_pixel(0,1)
	assert(lit.r>0.8 and lit.g>0.5,"Light must charge both phosphor populations")
	var stepped=Glow.new()
	stepped.reset()
	for frame in range(120): stepped.advance(0.5,source,2.0,0.0)
	assert(stepped.image.get_pixel(0,1).is_equal_approx(lit),"Glow must not depend on frame rate")
	source.fill(Color.BLACK)
	charged.advance(60.0,source,0.0,0.0)
	var dark=charged.image.get_pixel(0,1)
	assert(dark.r>0.0 and dark.r<lit.r and dark.g>0.0 and dark.g<lit.g,"Glow must persist and decay with LEDs off")
	charged.advance(840.0,source,0.0,0.0)
	var later=charged.image.get_pixel(0,1)
	assert(later.r<dark.r and later.g<dark.g and later.g>0.0,"Glow must retain a weak long tail")
	var red=Glow.new()
	red.reset()
	source.fill(Color.RED)
	red.advance(10.0,source,2.0,0.0)
	charged.reset()
	source.fill(Color.BLUE)
	charged.advance(10.0,source,2.0,0.0)
	assert(charged.image.get_pixel(0,1).r>red.image.get_pixel(0,1).r,"Blue light must excite the pigment more than red")
	print("DEMO GLOW STATE PASS: charging, dark decay, long tail, spectral response and frame-rate independence")

func _run_checks():
	_check_glow()
	var material_time=pattern_time
	var material_camera=camera.position
	for value in range(RING_MATERIALS.size()):
		_set_ring_material(value)
		var response=metadata.ring_materials[RING_MATERIALS[value]].render
		for material in sleeve_materials+cavity_materials:
			assert(is_equal_approx(material.get_shader_parameter("ring_stored_emission"),float(response.stored_emission)),"Direct and reflected rings must use the selected material")
		assert(pattern_time==material_time and camera.position==material_camera,"Material selection must preserve pattern and view")
	_set_ring_material(0)
	# Headless Godot starts with a 64-pixel window; test the capture resolution.
	get_window().size = Vector2i(1280,720)
	assert(metadata.leds.size()==494)
	for material in sleeve_materials+cavity_materials:
		assert(material.get_shader_parameter("charges")==charge_texture,"Direct and reflected rings must share stored glow")
	assert(meshes.size()==metadata.parts.size())
	_set_presentation(0)
	assert(mannequin.visible and infinity_backdrop.visible and lighting==0,"Worn presentation must use the night scene")
	for surface in mannequin.surfaces:
		for corner in range(8):
			var point=surface.global_transform*surface.get_aabb().get_endpoint(corner)
			assert(not camera.is_position_behind(point),"Mannequin behind the camera")
			assert(get_viewport().get_visible_rect().grow(-12).has_point(camera.unproject_position(point)),"Full pose clipped: "+str(surface.name))
	_set_presentation(1)
	assert(mannequin.visible and infinity_backdrop.visible,"Night close-up must retain the wearer")
	yaw=65
	pitch_angle=20
	_update_camera()
	assert(CaptureView.hand_overlaps(camera,mannequin,0.125,float(metadata.optics.front_z)),"Clearance check must detect an obstructed hand-side view")
	_night_pose(0)
	var night_start=camera.transform
	var body_start=mannequin.global_transform
	var field_start=infinity_backdrop.global_transform
	for sample in range(CaptureView.FRAMES+1):
		var phase=sample/float(CaptureView.FRAMES)
		_night_pose(phase*CaptureView.FRAMES)
		assert(is_equal_approx(distance,0.46),"Night sweep must hold its detail distance")
		assert(is_equal_approx(yaw,35.0*sin(TAU*phase)-15.0*pow(sin(TAU*phase),2)),"Figure eight must show both sides")
		assert(is_equal_approx(pitch_angle,20*sin(2*TAU*phase)),"Figure eight must cross the centre head on")
		assert(mannequin.global_transform.is_equal_approx(body_start),"Mannequin must remain stationary")
		assert(infinity_backdrop.global_transform.is_equal_approx(field_start),"Field must remain in world space")
		assert(not CaptureView.hand_overlaps(camera,mannequin,0.125,float(metadata.optics.front_z)),"Pointing hand covers the case at frame "+str(sample))
		for name in ["FrontCentre","FrontMirrorCoating","FrontRim","EdgeDiffuser"]:
			var mesh=meshes[name]
			# Check the circular surfaces themselves, not empty AABB corners.
			for surface in range(mesh.mesh.get_surface_count()):
				for vertex in mesh.mesh.surface_get_arrays(surface)[Mesh.ARRAY_VERTEX]:
					var point=mesh.global_transform*vertex
					assert(not camera.is_position_behind(point),"Pendant behind the camera")
					assert(get_viewport().get_visible_rect().grow(-12).has_point(camera.unproject_position(point)),"Night pendant clipped: "+name)

	assert(camera.transform.is_equal_approx(night_start),"Night sweep must close")
	_night_pose(96)
	assert(is_equal_approx(yaw,20.0) and is_equal_approx(pitch_angle,0.0),"Hand-side swing must stop at 20 degrees")
	_night_pose(288)
	assert(is_equal_approx(yaw,-50.0) and is_equal_approx(pitch_angle,0.0),"Clear-side swing must reach 50 degrees")
	_set_presentation(2)
	assert(not mannequin.visible and not infinity_backdrop.visible,"Design inspection must show the isolated CAD assembly")
	print("DEMO MANNEQUIN PASS: full-pose framing, fixed-distance figure eight with stationary wearer and field, night and inspection controls")
	for part in metadata.parts:
		var bounds = meshes[part.name].get_aabb()
		for axis in range(3):
			assert(absf(bounds.position[axis]-part.bounds_m[0][axis])<0.0003,"Imported position differs from CAD")
			assert(absf(bounds.end[axis]-part.bounds_m[1][axis])<0.0003,"Imported size differs from CAD")
	_sweep(0)
	var loop_start=camera.position
	_sweep(0.25)
	assert(absf(yaw)<0.00001, "Sweep must cross the front")
	_sweep(1)
	assert(camera.position.is_equal_approx(loop_start), "Sweep must close its loop")
	_exploded_pose(0)
	var exploded_start=camera.transform
	for phase in [0.125,0.25,0.5,0.75,0.875]:
		_exploded_pose(phase)
		for mesh in meshes.values():
			var bounds=mesh.get_aabb()
			for corner in range(8):
				var point=mesh.global_transform*bounds.get_endpoint(corner)
				assert(not camera.is_position_behind(point), "Exploded part behind camera")
				assert(get_viewport().get_visible_rect().grow(-12).has_point(camera.unproject_position(point)), "Exploded part clipped: %s at %s in %s (phase %s)" % [mesh.name,camera.unproject_position(point),get_viewport().get_visible_rect(),phase])
	_exploded_pose(0.5)
	for name in ["FrontMirrorCoating","RearMirror"]:
		assert(meshes[name].transparency>0.0 and meshes[name].transparency<1.0,"Separated mirror must remain visible and semi-transparent: "+name)
	assert(meshes.FibonacciBaffle.get_aabb().position.z+meshes.FibonacciBaffle.position.z > meshes.CircleLEDs.get_aabb().end.z+meshes.CircleLEDs.position.z+0.05,"Stencil must lift clear of the populated LED board")
	assert(explosion_offsets.CirclePCB==explosion_offsets.CircleLEDs,"Soldered LED packages must stay on their board")
	for part in metadata.parts:
		if part.role == "cell": assert(not meshes[part.name].visible,"Exploded stencil must not carry virtual lit apertures")
	assert(meshes.FrontCentre.position == meshes.FrontRim.position and meshes.FrontCentre.position == meshes.FrontMirrorCoating.position, "Front sheet must stay whole")
	assert(not cavity_materials[0].get_shader_parameter("cavity_closed"), "Separated mirrors must not show a closed cavity")
	assert(meshes.HaloRing.material_override.get_shader_parameter("assembly_offset").is_equal_approx(explosion_offsets.HaloRing))
	assert(explosion_offsets.HaloLightShield.is_equal_approx(explosion_offsets.HaloRing))
	assert(explosion_offsets.InnerLightShield.is_equal_approx(explosion_offsets.InnerRing))
	assert(explosion_offsets.OuterLightShield.is_equal_approx(explosion_offsets.EdgeDiffuser))
	_exploded_pose(1)
	assert(camera.transform.is_equal_approx(exploded_start), "Exploded camera loop must close")
	for name in meshes:
		assert(meshes[name].transform.is_equal_approx(assembled_transforms[name]), "Reassembly must restore " + name)
		assert(meshes[name].visible,"Reassembly must restore the assembled light field")
	assert(cavity_materials[0].get_shader_parameter("cavity_closed"), "Reassembly must restore reflections")
	for name in ["FrontMirrorCoating","RearMirror"]:
		assert(is_zero_approx(meshes[name].transparency),"Reassembly must restore mirror opacity: "+name)
	_reset()
	var saved_time=pattern_time
	var saved_position=camera.position
	for value in range(FINISHES.size()):
		_set_finish(value)
		assert(pattern_time==saved_time and camera.position==saved_position)
		assert(meshes.RearMirror.visible)
		assert(meshes.FibonacciBaffle.visible and meshes.FrontCentre.visible)
		assert(meshes.HaloRing.visible and meshes.InnerRing.visible)
		assert(meshes.OpticalDeck.visible and meshes.BarrelFrame.visible and meshes.RearPlate.visible)
	for value in range(4):
		_set_lighting(value)
		assert(environment.tonemap_exposure==1.0)
	reflect_slider.value=0.95
	assert(reflectance+transmission<=1.000001)
	transmit_slider.value=0.9
	assert(reflectance+transmission<=1.000001)
	assert(absf(reflect_slider.value-reflectance)<0.000001)
	pattern=0
	var top={"group":1,"position_m":[0.0,0.0795,0.03]}
	assert(_pattern_colour(top,0).is_equal_approx(Color.RED))
	assert(_pattern_colour(top,4).is_equal_approx(Color.CYAN))
	for selection in [0,8,9]:
		pattern=selection
		var spatial_change=false
		var moving_count=0
		var first=_pattern_colour(metadata.leds[0],0)
		for led in metadata.leds:
			var colour=_pattern_colour(led,0)
			assert(colour.is_equal_approx(_pattern_colour(led,16)), "Gradient loop must close")
			for t in [0.0,0.5,2.0,4.0,7.5]:
				assert(is_equal_approx(_pattern_colour(led,t).v,1.0), "Gradient must not pulse or go dark")
			if not colour.is_equal_approx(first): spatial_change=true
			if not colour.is_equal_approx(_pattern_colour(led,2)): moving_count+=1
		assert(spatial_change and moving_count>480, "Gradient must move across all LED groups")
	pattern=7
	var white_count=0
	for led in metadata.leds:
		if _pattern_colour(led,0)==Color.WHITE: white_count+=1
	assert(white_count==1)
	groups=[false,false,false,false]
	_update_colours()
	assert(image_data.get_pixel(0,0)==Color.BLACK)
	print("DEMO SCENE PASS: runtime GLB, dimensions, visibility, fixed exposure, shared patterns and 494 LEDs")
	get_tree().quit()

func _settle():
	for frame in range(4):
		await get_tree().process_frame
		RenderingServer.force_draw(false)

func _sweep(phase: float, angle: float = 70.0):
	# Periodic pose and velocity: the loop crosses the front twice.
	yaw=angle*cos(TAU*phase)
	pitch_angle=-12.0
	_update_camera()

func _capture():
	paused=true
	pattern_time=2.0
	DirAccess.make_dir_recursive_absolute(capture_dir)
	panel.visible=false
	var captions=CanvasLayer.new()
	add_child(captions)
	var caption=Label.new()
	caption.position=Vector2(24,24)
	caption.add_theme_font_size_override("font_size",28)
	caption.add_theme_color_override("font_outline_color",Color.BLACK)
	caption.add_theme_constant_override("outline_size",5)
	captions.add_child(caption)
	# All 494 LEDs share a moving spatial gradient at constant brightness.
	# Two colour rotations share the closed figure-eight camera orbit.
	_set_presentation(0)
	caption.text="Worn night preview | full pose | unmeasured optics"
	await _settle()
	assert(get_viewport().get_texture().get_image().save_png(capture_dir.path_join("night-mannequin.png"))==OK)
	_set_presentation(1)
	_set_finish(0)
	_set_lighting(0)
	diffusion=0.65
	brightness=2.0
	groups=[true,true,true,true]
	for material_index in range(RING_MATERIALS.size()):
		_set_ring_material(material_index)
		for style in ["rainbow"]:
			var capture_style=style+("-silver" if material_index==1 else "")
			# A uniform precharged state makes the repeating colour loop continuous.
			_reset_glow(0.35,0.20)
			pattern={"rainbow":0,"ocean":8,"sunset":9}[style]
			caption.text="%s | %s | worn night preview | unmeasured optics" % [metadata.ring_materials[RING_MATERIALS[material_index]].label,style.capitalize()]
			for frame in range(CaptureView.FRAMES):
				_night_pose(frame)
				pattern_time=frame/CaptureView.FPS
				_update_optics()
				_update_colours()
				await _settle()
				assert(get_viewport().get_texture().get_image().save_png(capture_dir.path_join("gradient-%s-%04d.png" % [capture_style,frame]))==OK)
	print("DEMO CAPTURE PASS: two matched rainbow material loops, 384 frames each")
	get_tree().quit()

func _benchmark():
	paused=false
	panel.visible=true
	# Warm pipelines first. Measure this scene, 1280x720, default optics.
	for frame in range(120):
		pattern_time+=1.0/60
		await get_tree().process_frame
	var result=[]
	for version in range(FINISHES.size()):
		_set_finish(version)
		for frame in range(30): await get_tree().process_frame
		var samples=[]
		var previous=Time.get_ticks_usec()
		for frame in range(300):
			pattern_time+=1.0/60
			await RenderingServer.frame_post_draw
			await get_tree().process_frame
			var now=Time.get_ticks_usec()
			samples.append((now-previous)/1000.0)
			previous=now
		samples.sort()
		var total=0.0
		for value in samples: total+=value
		result.append({"finish":FINISHES[version],"mean_ms":total/samples.size(),"p95_ms":samples[int(samples.size()*0.95)],"fps":1000.0/(total/samples.size())})
	print("DEMO BENCHMARK "+JSON.stringify({"size":[1280,720],"renderer":RenderingServer.get_current_rendering_method(),"driver":RenderingServer.get_current_rendering_driver_name(),"gpu":RenderingServer.get_video_adapter_name(),"results":result}))
	get_tree().quit()

func _gpu_checks():
	var args=OS.get_cmdline_user_args()
	var reference_path=args[args.find("--reference")+1]
	var samples=JSON.parse_string(FileAccess.get_file_as_string(reference_path))
	var viewport=SubViewport.new()
	viewport.size=Vector2i(16,16)
	viewport.own_world_3d=true
	viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	add_child(viewport)
	var diagnostic_camera=Camera3D.new()
	diagnostic_camera.position=Vector3(0,0,1)
	viewport.add_child(diagnostic_camera)
	diagnostic_camera.current=true
	var plane=MeshInstance3D.new()
	var quad=QuadMesh.new()
	quad.size=Vector2(2,2)
	plane.mesh=quad
	var material=ShaderMaterial.new()
	material.shader=load("res://diagnostic.gdshader")
	for key in ["front_z","rear_z","halo_radius","inner_radius"]:
		material.set_shader_parameter(key,float(metadata.optics[key]))
	var radii=metadata.optics.ring_pitch_radii
	material.set_shader_parameter("pitch_radii",Vector3(radii[0],radii[1],radii[2]))
	plane.material_override=material
	viewport.add_child(plane)
	for sample in samples:
		material.set_shader_parameter("ray_point",Vector3(sample.point[0],sample.point[1],sample.point[2]))
		material.set_shader_parameter("ray_direction",Vector3(sample.direction[0],sample.direction[1],sample.direction[2]))
		material.set_shader_parameter("reflectance",float(sample.reflectance))
		material.set_shader_parameter("transmission",float(sample.transmission))
		material.set_shader_parameter("rear_reflectance",float(sample.rear_reflectance))
		await _settle()
		var measured=viewport.get_texture().get_image().get_pixel(8,8).srgb_to_linear()
		var expected=Color(sample.expected[0],sample.expected[1]/32.0,sample.expected[2]/2.0)
		if absf(measured.r-expected.r)>0.009 or absf(measured.g-expected.g)>0.009 or absf(measured.b-expected.b)>0.009:
			push_error("GPU/reference mismatch: "+str(sample)+" measured "+str(measured)+" expected "+str(expected))
			get_tree().quit(1)
			return
	# Exercise the shared direct/reflected diffuser on the GPU. Uniform white
	# must stay smooth between LEDs, with a small local peak and no hard edge.
	material=ShaderMaterial.new()
	material.shader=load("res://diffuser_diagnostic.gdshader")
	material.set_shader_parameter("colours",colour_texture)
	material.set_shader_parameter("pitch",float(metadata.optics.pitch))
	material.set_shader_parameter("seam_gap",float(metadata.optics.ring_seam_gap))
	plane.material_override=material
	pattern=6
	groups=[true,true,true,true]
	_update_colours()
	var baseline=[]
	for group in range(1,4):
		var radius=float(radii[group-1])
		var led_z=float(metadata.optics.edge_z if group==3 else metadata.optics.strip_z)
		material.set_shader_parameter("group",group)
		material.set_shader_parameter("count",COUNTS[group])
		material.set_shader_parameter("radius",radius)
		material.set_shader_parameter("led_z",led_z)
		var readings=[]
		for offset in [Vector2(0,0),Vector2(0.299,0),Vector2(0.301,0),Vector2(0.5,0),Vector2(0,0.002499),Vector2(0,0.002501),Vector2(0,0.0035),Vector2(0,0.0055),Vector2(0,-0.0055),Vector2(0,0.0075)]:
			var angle=(float(metadata.optics.ring_seam_gap)*0.5+(5.5+offset.x)*float(metadata.optics.pitch))/radius
			material.set_shader_parameter("sample_point",Vector3(sin(angle)*radius,cos(angle)*radius,led_z+offset.y))
			await _settle()
			readings.append(viewport.get_texture().get_image().get_pixel(8,8).srgb_to_linear().r)
		assert(readings[3]>0.90, "Dark gap between diffused LEDs")
		assert(readings[0]-readings[3]>0.02 and readings[0]-readings[3]<0.10, "LED peaks must be gentle")
		assert(absf(readings[1]-readings[2])<0.009, "Hard package edge in diffuser")
		# The axial band has a smooth package boundary and a soft tail. At the
		# cavity edge it must leave a dark valley between repeated LED rows.
		assert(readings[4]>0.97 and absf(readings[4]-readings[5])<0.009, "Hard axial package edge in diffuser")
		assert(readings[6]>0.5 and readings[6]<0.95, "LED band must have a soft axial shoulder")
		assert(readings[7]>0.05 and readings[7]<0.2, "Axial spill must retain contrast between mirror copies")
		assert(absf(readings[7]-readings[8])<0.009, "Axial diffusion must be symmetric")
		assert(readings[9]<0.01, "Distant LED spill must not fill the reflection valleys")
		if baseline.is_empty(): baseline=readings
		else:
			for index in range(readings.size()):
				assert(absf(readings[index]-baseline[index])<0.009, "Ring diffuser profiles differ")
	print("DEMO GPU DIFFUSER PASS: smooth LED gaps, gentle peaks, continuous edges, axial reflection contrast and matching profiles for all three rings")
	material.shader=load("res://glow_diagnostic.gdshader")
	_apply_ring_response(material,metadata.ring_materials.glow)
	material.set_shader_parameter("colours",colour_texture)
	material.set_shader_parameter("charges",charge_texture)
	material.set_shader_parameter("pitch",float(metadata.optics.pitch))
	material.set_shader_parameter("seam_gap",float(metadata.optics.ring_seam_gap))
	material.set_shader_parameter("group",1)
	material.set_shader_parameter("count",64)
	material.set_shader_parameter("radius",float(radii[0]))
	material.set_shader_parameter("led_z",float(metadata.optics.strip_z))
	var angle=(float(metadata.optics.ring_seam_gap)*0.5+5.5*float(metadata.optics.pitch))/float(radii[0])
	material.set_shader_parameter("sample_point",Vector3(sin(angle)*radii[0],cos(angle)*radii[0],metadata.optics.strip_z))
	material.set_shader_parameter("wall_mm",float(metadata.optics.ring_wall_mm[0]))
	_reset_glow()
	await _settle()
	var thin=viewport.get_texture().get_image().get_pixel(8,8).srgb_to_linear()
	assert(thin.g>thin.r and thin.r>thin.b,"Glow pigment must filter white light toward green")
	material.set_shader_parameter("wall_mm",float(metadata.optics.ring_wall_mm[2]))
	await _settle()
	var thick=viewport.get_texture().get_image().get_pixel(8,8).srgb_to_linear()
	assert(thick.r<thin.r and thick.g<thin.g and thick.b<thin.b,"Thicker PETG must transmit less direct light")
	groups=[false,false,false,false]
	_update_colours()
	_reset_glow(0.85,0.65)
	material.set_shader_parameter("brightness",0.0)
	await _settle()
	var after=viewport.get_texture().get_image().get_pixel(8,8).srgb_to_linear()
	assert(after.g>0.15 and after.g>4.0*after.r and after.g>10.0*after.b,"LED-off emission must retain a green afterglow")
	material.set_shader_parameter("sample_point",Vector3(0.0,radii[0],metadata.optics.strip_z))
	await _settle()
	var joint=viewport.get_texture().get_image().get_pixel(8,8).srgb_to_linear()
	assert(absf(joint.g-after.g)<0.009,"The strip joint must not cut a dark seam in the whole glow ring")
	glow.advance(900.0,image_data,0.0,0.0)
	charge_texture.update(glow.image)
	await _settle()
	var faded=viewport.get_texture().get_image().get_pixel(8,8).srgb_to_linear()
	assert(faded.g>0.005 and faded.g<after.g*0.15,"GPU afterglow must fade to a weaker green tail")
	print("DEMO GPU GLOW PASS: green spectral filtering, wall attenuation, LED-off emission and fading tail")
	_apply_ring_response(material,metadata.ring_materials.silver)
	groups=[true,true,true,true]
	pattern=6
	_update_colours()
	material.set_shader_parameter("brightness",2.0)
	material.set_shader_parameter("wall_mm",float(metadata.optics.ring_wall_mm[0]))
	await _settle()
	var silver_thin=viewport.get_texture().get_image().get_pixel(8,8).srgb_to_linear()
	assert(silver_thin.r>0.1 and absf(silver_thin.r-silver_thin.g)<0.009 and absf(silver_thin.g-silver_thin.b)<0.009,"Silver must retain neutral RGB transmission")
	material.set_shader_parameter("wall_mm",float(metadata.optics.ring_wall_mm[2]))
	await _settle()
	var silver_thick=viewport.get_texture().get_image().get_pixel(8,8).srgb_to_linear()
	assert(silver_thick.r<silver_thin.r,"Silver wall thickness must attenuate light")
	_reset_glow(0.85,0.65)
	material.set_shader_parameter("brightness",0.0)
	await _settle()
	var silver_off=viewport.get_texture().get_image().get_pixel(8,8).srgb_to_linear()
	assert(silver_off.r<0.00001 and silver_off.g<0.00001 and silver_off.b<0.00001,"Silver must not emit stored green afterglow")
	print("DEMO GPU SILVER PASS: neutral colour transmission, wall attenuation and no afterglow")
	# Complete-sheet coefficients must not acquire a second black-substrate loss.
	material.shader=load("res://centre_diagnostic.gdshader")
	material.set_shader_parameter("offset",Vector2.ZERO)
	material.set_shader_parameter("sheet_transmission",float(metadata.comparison.black_acrylic_transmission))
	material.set_shader_parameter("sheet_reflectance",float(metadata.comparison.black_acrylic_surface_reflectance))
	await _settle()
	var centre=viewport.get_texture().get_image().get_pixel(8,8).srgb_to_linear()
	assert(absf(centre.r-0.29)<0.009 and absf(centre.b-1.0)<0.009,"Uncoated black centre must transmit 29% once and retain a local LED peak")
	material.set_shader_parameter("sheet_transmission",float(metadata.comparison.front_transmission))
	material.set_shader_parameter("sheet_reflectance",float(metadata.comparison.front_external_reflectance))
	await _settle()
	var coated=viewport.get_texture().get_image().get_pixel(8,8).srgb_to_linear()
	assert(absf(coated.r-0.09)<0.009 and absf(coated.g-0.10)<0.009,"Coated black sheet uses complete-sheet T9 and external R10 without a second substrate factor")
	material.set_shader_parameter("offset",Vector2(0.0015,0))
	await _settle()
	var plateau=viewport.get_texture().get_image().get_pixel(8,8).srgb_to_linear()
	assert(plateau.b>0.96,"Diffused cells need a flat luminous centre, without a rounded hotspot")
	material.set_shader_parameter("offset",Vector2(0.008,0))
	await _settle()
	var distant=viewport.get_texture().get_image().get_pixel(8,8).srgb_to_linear()
	assert(distant.b<0.009,"Cell diffusion must stay local to its flat aperture")
	print("DEMO GPU CENTRE PASS: flat cell plateau, spatial falloff, uncoated T29 and coated T9/R10")
	print("DEMO GPU OPTICS PASS: "+str(samples.size())+" independent unfolded-ray cases; spacing, attenuation, obstruction, exits, 0.1 percent cutoff, 32 reflections")
	get_tree().quit()
