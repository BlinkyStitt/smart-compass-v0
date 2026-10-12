extends Node3D

const PATTERNS = ["Spiral rainbow", "Rotating spokes", "Radial waves", "Solid red", "Solid green", "Solid blue", "White", "Single-pixel chase"]
const FINISHES = ["Current assembly", "One sheet • full mirror", "One sheet • clear centre"]
const LIGHTING = ["Night", "Indoor", "Overcast", "Bright sun"]
const COUNTS = [256, 64, 84, 90]
var metadata: Dictionary
var meshes = {}
var cell_materials = []
var sleeve_materials = []
var cavity_materials = []
var centre_materials = []
var image_data = Image.create(256, 4, false, Image.FORMAT_RGBAF)
var colour_texture: ImageTexture
var camera = Camera3D.new()
var environment = Environment.new()
var sun = DirectionalLight3D.new()
var sky_material = ProceduralSkyMaterial.new()
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
var reflectance = 0.65
var transmission = 0.25
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
	if automated:
		get_tree().create_timer(600).timeout.connect(func(): push_error("Automation timed out"); get_tree().quit(1))
	if not capture_dir.is_empty() or args.has("--gpu-check"):
		# Explicit capture draws also work when macOS hides the window.
		RenderingServer.render_loop_enabled=false
		RenderingServer.viewport_set_update_mode(get_viewport().get_viewport_rid(),RenderingServer.VIEWPORT_UPDATE_ALWAYS)
	colour_texture = ImageTexture.create_from_image(image_data)
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
	_make_materials()
	_make_world()
	_make_controls()
	_set_finish(0)
	_set_lighting(1)
	_update_camera()
	_update_colours()
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

func _shader(path):
	var material = ShaderMaterial.new()
	material.shader = load(path)
	material.set_shader_parameter("colours", colour_texture)
	return material

func _make_materials():
	var optics = metadata.optics
	for part in metadata.parts:
		var mesh = meshes.get(part.name)
		assert(mesh != null, "Missing named GLB mesh " + part.name)
		if part.role == "cell":
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
			mesh.material_override = material
			cavity_materials.append(material)
		elif part.role == "sleeve":
			var group = 3
			if part.name == "HaloDiffuser": group = 1
			if part.name == "InnerDiffuser": group = 2
			var material = _shader("res://sleeve.gdshader")
			material.set_shader_parameter("group", group)
			material.set_shader_parameter("count", COUNTS[group])
			material.set_shader_parameter("pitch_radius", float(optics.ring_pitch_radii[group-1]))
			material.set_shader_parameter("seam_gap", float(optics.ring_seam_gap))
			material.set_shader_parameter("pitch", float(optics.pitch))
			material.set_shader_parameter("led_z", float(optics.edge_z if group == 3 else optics.strip_z))
			mesh.material_override = material
			sleeve_materials.append(material)
		elif part.role == "centre":
			var material = _shader("res://centre.gdshader")
			mesh.material_override = material
			centre_materials.append(material)
		elif part.name == "RearMirror":
			var material = StandardMaterial3D.new()
			material.albedo_color = Color(0.94,0.94,0.94)
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
	_option(box,"Viewing light",LIGHTING,1,_set_lighting)
	ambient_slider = _slider(box,"Ambient intensity",0,3,ambient,func(v): ambient=v; _update_light())
	_slider(box,"Light direction (degrees)",-180,180,light_angle,func(v): light_angle=v; _update_light())
	_slider(box,"Exposure (fixed unless changed)",0.1,4,exposure,func(v): exposure=v; environment.tonemap_exposure=v)
	reflect_slider = _slider(box,"Front reflectance",0,1,reflectance,func(v):
		reflectance=v
		transmission=minf(transmission,1-v)
		_sync_slider(transmit_slider,transmission)
		_update_optics())
	transmit_slider = _slider(box,"Front transmission",0,1,transmission,func(v):
		transmission=v
		reflectance=minf(reflectance,1-v)
		_sync_slider(reflect_slider,reflectance)
		_update_optics())
	_slider(box,"Sleeve transmission (assumed)",0,1,diffuser_transmission,func(v): diffuser_transmission=v; _update_optics())
	_slider(box,"Sleeve diffusion (assumed)",0,1,diffusion,func(v): diffusion=v; _update_optics())
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

func _option(parent,title,items,selected,callback):
	_label(parent,title,12)
	var option = OptionButton.new()
	for item in items: option.add_item(item)
	option.select(selected)
	option.item_selected.connect(callback)
	parent.add_child(option)

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
		meshes[part.name].visible = part.variant == "common" or part.variant == ("current" if finish == 0 else "proposal")
	_update_optics()

func _update_optics():
	for material in cavity_materials:
		for entry in [["reflectance",reflectance],["transmission",transmission],["diffuser_transmission",diffuser_transmission],["diffusion",diffusion],["brightness",brightness]]:
			material.set_shader_parameter(entry[0],entry[1])
	for material in sleeve_materials:
		material.set_shader_parameter("transmission",diffuser_transmission)
		material.set_shader_parameter("diffusion",diffusion)
		material.set_shader_parameter("brightness",brightness)
	for material in cell_materials:
		material.set_shader_parameter("brightness",brightness)
		material.set_shader_parameter("diffusion",central_diffusion)
		material.set_shader_parameter("transmission",1.0)
	for material in centre_materials:
		material.set_shader_parameter("reflectance",reflectance if finish == 1 else 0.04)
		material.set_shader_parameter("transmission",transmission if finish == 1 else 0.8)

func _set_lighting(value):
	lighting = value
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
	distance=0.6
	yaw=0
	pitch_angle=0
	target=Vector3(0,0,float(metadata.optics.front_z))
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
	if status:
		status.text="%.2f m • yaw %.1f° • tilt %.1f°\nt = %.2f s • R + T = %.2f\n%.1f fps • centre diffusion %.2f" % [distance,yaw,pitch_angle,pattern_time,reflectance+transmission,Engine.get_frames_per_second(),central_diffusion]

func _pattern_colour(led,time: float):
	var p = led.position_m
	var angle = fposmod(atan2(p[0],p[1])/TAU,1.0)
	var radius = sqrt(p[0]*p[0]+p[1]*p[1])/0.0795 if int(led.group)==0 else 1.0
	match pattern:
		0: return Color.from_hsv(fposmod(angle+2*radius-time/8,1.0),1,1)
		1: return Color.from_hsv(fposmod(angle-time/8,1.0),1,1)*pow(maxf(0,cos(TAU*(3*angle-3*time/8))),8)
		2: return Color.from_hsv(fposmod(radius-time/8,1.0),1,1)*(0.1+0.9*(1-absf(2*fposmod(2*radius-time/4,1.0)-1)))
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

func _run_checks():
	assert(metadata.leds.size()==494)
	assert(meshes.size()==metadata.parts.size())
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
	_reset()
	var saved_time=pattern_time
	var saved_position=camera.position
	for value in range(3):
		_set_finish(value)
		assert(pattern_time==saved_time and camera.position==saved_position)
		assert(meshes.RearMirror.visible)
		assert(meshes.WoodMask.visible==(value==0))
		assert(meshes.ProposalWood.visible==(value!=0))
		assert(meshes.HaloDiffuser.visible and meshes.InnerDiffuser.visible)
		assert(meshes.CircleBezel.visible==(value==0))
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
	for view in [["front",0,0],["steep",72,-12],["edge",90,0],["rear",180,0]]:
		yaw=view[1]
		pitch_angle=view[2]
		_update_camera()
		for light in range(4):
			_set_lighting(light)
			for on in [true,false]:
				groups=[on,on,on,on]
				_update_colours()
				for version in range(3):
					_set_finish(version)
					caption.text="%s | %s | LEDs %s" % [FINISHES[version],LIGHTING[light],"on" if on else "off"]
					await _settle()
					var filename="%s-light%d-%s-v%d.png" % [view[0],light,"on" if on else "off",version]
					assert(get_viewport().get_texture().get_image().save_png(capture_dir.path_join(filename))==OK)
	# All movie frames come from the same Godot scene and optical shaders.
	_reset()
	groups=[true,true,true,true]
	for frame in range(624):
		if frame<288:
			_set_finish(0)
			_set_lighting(1)
			_sweep(frame/288.0)
			# One complete eight-second rainbow cycle in the 12-second loop.
			pattern_time=8.0*frame/288.0
		elif frame<432:
			var local_frame=frame-288
			_set_finish(local_frame/48)
			_set_lighting(1)
			_sweep(float(local_frame%48)/48.0,60.0)
			pattern_time=8.0*float(local_frame%48)/48.0
		else:
			var local_frame=frame-432
			_set_finish(2)
			_set_lighting(local_frame/48)
			_sweep(float(local_frame%48)/48.0,60.0)
			pattern_time=8.0*float(local_frame%48)/48.0
		caption.text="%s | %s | Godot optical preview" % [FINISHES[finish],LIGHTING[lighting]]
		_update_camera()
		_update_colours()
		await _settle()
		assert(get_viewport().get_texture().get_image().save_png(capture_dir.path_join("movie-%04d.png" % frame))==OK)
	# Eight-second GIF loops. All light and camera states are periodic. The
	# mirror-only loops remove centre glare to expose the repeated ring images.
	_set_finish(0)
	_set_lighting(0)
	distance=0.46
	for style in ["rainbow","pulse","colour"]:
		diffusion=0.65 if style=="rainbow" else 0.30
		for frame in range(192):
			var phase=frame/192.0
			var seconds=frame/24.0
			_sweep(phase,65.0)
			pattern_time=seconds
			var pulse=0.18+0.82*pow(0.5+0.5*cos(TAU*seconds),4)
			if style=="rainbow":
				pattern=0
				groups=[true,true,true,true]
				brightness=2.0*pulse
				caption.text="Rainbow pulse | moving Godot preview"
			else:
				pattern=6 if style=="pulse" else [3,4,5,6][int(seconds/2.0)%4]
				groups=[false,true,true,false]
				# Black intervals separate each colour and join the loop cleanly.
				brightness=6.0*pow(sin(PI*fposmod(seconds,1.0)),4)
				caption.text="Infinity mirror | %s | assumed diffusion 0.30" % ("white pulse" if style=="pulse" else "colour pulse")
			_update_optics()
			_update_colours()
			await _settle()
			assert(get_viewport().get_texture().get_image().save_png(capture_dir.path_join("blink-%s-%04d.png" % [style,frame]))==OK)
	print("DEMO CAPTURE PASS: 96 matched stills, 624 movie frames and 576 blinking loop frames")
	get_tree().quit()

func _benchmark():
	paused=false
	panel.visible=true
	# Warm pipelines first. Measure this scene, 1280x720, default optics.
	for frame in range(120):
		pattern_time+=1.0/60
		await get_tree().process_frame
	var result=[]
	for version in range(3):
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
		await _settle()
		var measured=viewport.get_texture().get_image().get_pixel(8,8).srgb_to_linear()
		var expected=Color(sample.expected[0],sample.expected[1]/32.0,sample.expected[2]/2.0)
		if absf(measured.r-expected.r)>0.009 or absf(measured.g-expected.g)>0.009 or absf(measured.b-expected.b)>0.009:
			push_error("GPU/reference mismatch: "+str(sample)+" measured "+str(measured)+" expected "+str(expected))
			get_tree().quit(1)
			return
	print("DEMO GPU OPTICS PASS: "+str(samples.size())+" independent unfolded-ray cases; spacing, attenuation, obstruction, exits, 0.1 percent cutoff, 32 reflections")
	get_tree().quit()
