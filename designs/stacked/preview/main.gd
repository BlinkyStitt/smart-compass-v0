extends Node3D

const Mannequin = preload("res://mannequin.gd")
const PATTERNS = ["Spiral rainbow", "Ocean gradient", "Sunset gradient", "White", "Single pixel"]
# Match design one's camera world coordinates; keep actual pendant dimensions.
const COMPARISON_FRONT_Z = 0.0367
var metadata: Dictionary
var assets = ""
var camera = Camera3D.new()
var environment = Environment.new()
var sky_material = ProceduralSkyMaterial.new()
var sun = DirectionalLight3D.new()
var backdrop = CanvasLayer.new()
var mannequin = Mannequin.new()
var meshes = {}
var transforms = {}
var mirror_material: ShaderMaterial
var materials: Array[ShaderMaterial] = []
var colour_image: Image
var colours: ImageTexture
var charges: ImageTexture
var positions: ImageTexture
var cell_map: ImageTexture
var panel: Control
var caption: Label
var pattern = 0
var pattern_time = 0.0
var brightness = 2.0
var front_r = 0.70
var front_t = 0.30
var rear_r = 0.70
var rear_t = 0.30
var enabled: Array[bool] = []
var toggles: Array[CheckButton] = []
var paused = false
var automated = false
var distance = 3.5
var yaw = 0.0
var pitch_angle = -3.0
var target = Vector3(0,-0.1,COMPARISON_FRONT_Z)
var capture_dir = ""

func _ready():
	var args = OS.get_cmdline_user_args()
	assets = args[args.find("--assets")+1]
	metadata = JSON.parse_string(FileAccess.get_file_as_string(assets.path_join("scene.json")))
	brightness=float(metadata.comparison.brightness)
	front_r=float(metadata.comparison.front_reflectance)
	front_t=float(metadata.comparison.front_transmission)
	rear_r=float(metadata.comparison.rear_reflectance)
	rear_t=float(metadata.comparison.rear_transmission)
	automated = args.has("--check") or args.has("--gpu-check") or args.has("--capture")
	if args.has("--capture"): capture_dir = args[args.find("--capture")+1]
	get_tree().create_timer(1800).timeout.connect(func(): push_error("Compact preview timed out"); get_tree().quit(1))
	colour_image = Image.create(256,metadata.counts.size(),false,Image.FORMAT_RGBAF)
	enabled.resize(metadata.counts.size())
	enabled.fill(true)
	colour_image.fill(Color.BLACK)
	colours = ImageTexture.create_from_image(colour_image)
	var charge_image = Image.create(256,metadata.counts.size(),false,Image.FORMAT_RGBAF)
	charge_image.fill(Color(0.35,0.20,0,1))
	charges = ImageTexture.create_from_image(charge_image)
	var position_image = Image.create(256,1,false,Image.FORMAT_RGBAF)
	for i in range(256):
		var p = metadata.centres_m[i]
		position_image.set_pixel(i,0,Color(p[0],p[1],0,1))
	positions = ImageTexture.create_from_image(position_image)
	cell_map = ImageTexture.create_from_image(Image.load_from_file(assets.path_join("cell-map.png")))
	var document = GLTFDocument.new()
	var state = GLTFState.new()
	assert(document.append_from_file(assets.path_join("amulet.glb"),state)==OK)
	var model = document.generate_scene(state)
	add_child(model)
	for node in model.find_children("*","MeshInstance3D",true,false):
		meshes[node.name]=node
		transforms[node.name]=node.transform
	for part in metadata.parts:
		assert(meshes.has(part.name),"Missing CAD mesh "+str(part.name))
		var mesh = meshes[part.name]
		if part.role in ["mirror","rear_mirror","side","inner","packages"]:
			var path = {"mirror":"mirror", "rear_mirror":"source", "side":"side", "inner":"ring", "packages":"package"}[part.role]
			var material = ShaderMaterial.new()
			material.shader=load("res://"+path+".gdshader")
			material.set_shader_parameter("colours",colours)
			if part.role != "packages":
				material.set_shader_parameter("charges",charges)
			if part.role in ["mirror","rear_mirror"]:
				material.set_shader_parameter("positions",positions)
				material.set_shader_parameter("cell_map",cell_map)
				material.set_shader_parameter("source_plane_z",float(metadata.optics.source_z))
				material.set_shader_parameter("inner_count",int(metadata.counts[1]))
				for key in ["front_z","rear_z","wall_radius","ring_z","pitch_radius","rear_external_reflectance"]:
					material.set_shader_parameter(key,float(metadata.optics[key]))
			if part.role in ["side","inner"]:
				var is_inner = part.role=="inner"
				material.set_shader_parameter("group",1 if is_inner else 2)
				material.set_shader_parameter("count",int(metadata.counts[1 if is_inner else 2]))
				material.set_shader_parameter("pitch_radius",float(metadata.optics.pitch_radius if is_inner else metadata.optics.side_radius))
				material.set_shader_parameter("led_z",float(metadata.optics.ring_z) if is_inner else float(metadata.optics.side_first_z))
				material.set_shader_parameter("wall_mm",1.0 if is_inner else 2.0)
				if not is_inner:
					material.set_shader_parameter("row_count",int(metadata.optics.side_rows))
					material.set_shader_parameter("row_pitch",float(metadata.optics.side_pitch))
					material.set_shader_parameter("axial_scatter",float(metadata.optics.side_axial_scatter))
			mesh.material_override=material
			materials.append(material)
			if part.role=="mirror": mirror_material=material
	_make_world()
	add_child(camera)
	camera.fov=38.0
	camera.near=0.005
	camera.far=30.0
	camera.current=true
	_make_controls()
	_set_presentation(0)
	_update_colours()
	_update_materials()
	if args.has("--gpu-check"): _gpu_check.call_deferred(args[args.find("--reference")+1])
	elif args.has("--check"): _check.call_deferred()
	elif not capture_dir.is_empty(): _capture.call_deferred()

func _make_world():
	var world=WorldEnvironment.new()
	world.environment=environment
	add_child(world)
	var sky=Sky.new()
	sky.sky_material=sky_material
	environment.sky=sky
	environment.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color=Color(0.75,0.82,1.0)
	environment.reflected_light_source=Environment.REFLECTION_SOURCE_SKY
	environment.tonemap_mode=Environment.TONE_MAPPER_FILMIC
	environment.tonemap_exposure=float(metadata.comparison.exposure)
	environment.glow_enabled=true
	environment.glow_intensity=0.45
	backdrop.layer=-1
	add_child(backdrop)
	var image=TextureRect.new()
	image.texture=ImageTexture.create_from_image(Image.load_from_file(ProjectSettings.globalize_path("res://assets/playa-night.png")))
	image.expand_mode=TextureRect.EXPAND_IGNORE_SIZE
	image.stretch_mode=TextureRect.STRETCH_KEEP_ASPECT_COVERED
	image.mouse_filter=Control.MOUSE_FILTER_IGNORE
	backdrop.add_child(image)
	image.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	environment.background_canvas_max_layer=-1
	add_child(sun)
	sun.shadow_enabled=true
	add_child(mannequin)
	mannequin.build()
	# Change only the final webbing segments to meet the new rear anchors.
	for side in [-1.0,1.0]:
		var node: MeshInstance3D
		for surface in mannequin.surfaces:
			if surface.position.is_equal_approx(Vector3(side*0.102,0.107,-0.016)): node=surface
		assert(node != null,"Missing final webbing segment")
		var start=Vector3(side*0.12,0.15,-0.020)
		var end=Vector3(side*0.055,0.073,0.004)
		node.mesh.size=Vector3(0.010,start.distance_to(end)+0.002,0.0015)
		node.position=(start+end)*0.5
		node.quaternion=Quaternion(Vector3.UP,(end-start).normalized())

func _lighting(night: bool):
	backdrop.visible=night
	environment.background_mode=Environment.BG_CANVAS if night else Environment.BG_SKY
	environment.ambient_light_energy=0.015 if night else 0.35
	environment.background_energy_multiplier=0.06 if night else 0.7
	sun.light_energy=0.03 if night else 0.8
	sun.rotation_degrees=Vector3(-35,35,0)
	sky_material.sky_top_color=Color(0.003,0.005,0.015) if night else Color(0.11,0.14,0.20)
	sky_material.sky_horizon_color=Color(0.012,0.015,0.02) if night else Color(0.30,0.28,0.25)
	sky_material.ground_bottom_color=Color(0.018,0.020,0.024)
	sky_material.ground_horizon_color=sky_material.sky_horizon_color

func _set_presentation(value):
	mannequin.visible=value<2
	_lighting(value<2)
	distance=3.5 if value==0 else (0.46 if value==1 else 0.6)
	yaw=0
	pitch_angle=-3.0 if value==0 else 0.0
	target=Vector3(0,-0.1 if value==0 else 0.0,COMPARISON_FRONT_Z)
	_update_camera()

func _update_camera():
	var az=deg_to_rad(yaw)
	var el=deg_to_rad(pitch_angle)
	camera.position=target+distance*Vector3(sin(az)*cos(el),sin(el),cos(az)*cos(el))
	camera.look_at(target,Vector3.UP)

func _pattern_colour(led,time):
	var p=led.position_m
	var angle=fposmod(atan2(p[0],p[1])/TAU,1.0)
	var radius=sqrt(p[0]*p[0]+p[1]*p[1])/0.0795 if int(led.group)==0 else 1.0
	match pattern:
		0: return Color.from_hsv(fposmod(angle+2*radius-time/8,1.0),1,1)
		1: return Color.from_hsv(0.55+0.12*sin(TAU*(angle+2*radius-time/8)),1,1)
		2: return Color.from_hsv(fposmod(0.98+0.14*(0.5+0.5*sin(TAU*(angle+2*radius-time/8))),1),1,1)
		3: return Color.WHITE
		4:
			var offset=0
			for g in range(int(led.group)): offset+=int(metadata.counts[g])
			return Color.WHITE if int(time*20)%metadata.leds.size()==offset+int(led.index) else Color.BLACK
	return Color.BLACK

func _update_colours():
	colour_image.fill(Color.BLACK)
	for led in metadata.leds:
		colour_image.set_pixel(int(led.index),int(led.group),_pattern_colour(led,pattern_time) if enabled[int(led.group)] else Color.BLACK)
	colours.update(colour_image)

func _update_materials():
	for material in materials:
		material.set_shader_parameter("brightness",brightness)
		material.set_shader_parameter("diffusion",float(metadata.comparison.diffusion))
		material.set_shader_parameter("transmission",float(metadata.comparison.ring_transmission))
		material.set_shader_parameter("diffuser_transmission",float(metadata.comparison.ring_transmission))
		material.set_shader_parameter("front_r",front_r)
		material.set_shader_parameter("front_t",front_t)
		material.set_shader_parameter("rear_r",rear_r)
		material.set_shader_parameter("rear_t",rear_t)

func _make_controls():
	var layer=CanvasLayer.new()
	add_child(layer)
	panel=PanelContainer.new()
	panel.position=Vector2(12,12)
	layer.add_child(panel)
	var box=VBoxContainer.new()
	box.custom_minimum_size.x=260
	panel.add_child(box)
	var title=Label.new()
	title.text="COMPACT / STACKED MIRROR\n%.1f mm × %.1f mm\nOptics and hardware fit unmeasured" % [1000*float(metadata.dimensions_m.diameter),1000*float(metadata.dimensions_m.body_depth)]
	box.add_child(title)
	var presentation=OptionButton.new()
	for text in ["Night • full pose","Night • close-up","Design inspection"]: presentation.add_item(text)
	presentation.item_selected.connect(_set_presentation)
	box.add_child(presentation)
	var patterns=OptionButton.new()
	for text in PATTERNS: patterns.add_item(text)
	patterns.item_selected.connect(func(v): pattern=v)
	box.add_child(patterns)
	for group in range(3):
		var switch=CheckButton.new()
		switch.text=["Fibonacci cells","Inner mirror ring","Side band"][group]
		switch.button_pressed=true
		switch.toggled.connect(func(v): _set_group(group,v))
		box.add_child(switch)
		toggles.append(switch)
	var pause=CheckButton.new()
	pause.text="Pause pattern"
	pause.toggled.connect(func(v): paused=v)
	box.add_child(pause)
	_slider(box,"Brightness",0,8,2,func(v): brightness=v; _update_materials())
	_slider(box,"Front reflection",0,1,front_r,func(v): front_r=minf(v,1-front_t); _update_materials(); return front_r)
	_slider(box,"Front transmission",0,1,front_t,func(v): front_t=minf(v,1-front_r); _update_materials(); return front_t)
	_slider(box,"Rear reflection",0,1,rear_r,func(v): rear_r=minf(v,1-rear_t); _update_materials(); return rear_r)
	_slider(box,"Rear transmission",0,1,rear_t,func(v): rear_t=minf(v,1-rear_r); _update_materials(); return rear_t)
	_slider(box,"Explode",0,1,0,_explode)
	caption=Label.new()
	caption.position=Vector2(24,24)
	caption.add_theme_font_size_override("font_size",28)
	caption.add_theme_color_override("font_outline_color",Color.BLACK)
	caption.add_theme_constant_override("outline_size",5)
	caption.add_theme_color_override("font_color",Color(0.9,0.9,0.9))
	layer.add_child(caption)

func _set_group(group: int, value: bool):
	if group < 2: enabled[group]=value
	else:
		for row in range(2,enabled.size()): enabled[row]=value

func _slider(box,text,low,high,value,callback):
	var label=Label.new()
	label.text=text
	box.add_child(label)
	var slider=HSlider.new()
	slider.min_value=low
	slider.max_value=high
	slider.step=0.01
	slider.value=value
	slider.value_changed.connect(func(v):
		var accepted=callback.call(v)
		if accepted != null: slider.set_value_no_signal(accepted))
	box.add_child(slider)

func _explode(amount):
	for part in metadata.parts:
		var mesh=meshes[part.name]
		mesh.transform=transforms[part.name]
		mesh.position.z+=float(part.explosion_offset_m)*amount
		if part.role in ["mirror","rear_mirror"]: mesh.transparency=0.65*amount
	mirror_material.set_shader_parameter("cavity_closed",amount<0.0001)

func _process(delta):
	if metadata.is_empty(): return
	if not paused and not automated: pattern_time+=delta
	_update_colours()

func _unhandled_input(event):
	if event is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
		yaw-=event.relative.x*0.35
		pitch_angle=clampf(pitch_angle+event.relative.y*0.35,-85,85)
		_update_camera()
	if event is InputEventMouseButton and event.pressed:
		if event.button_index==MOUSE_BUTTON_WHEEL_UP: distance=maxf(0.20,distance*0.9)
		if event.button_index==MOUSE_BUTTON_WHEEL_DOWN: distance=minf(5.0,distance*1.1)
		_update_camera()

func _settle():
	for frame in range(4):
		await get_tree().process_frame
		RenderingServer.force_draw(false)

func _save(name):
	await _settle()
	assert(get_viewport().get_texture().get_image().save_png(capture_dir.path_join(name))==OK)

func _capture():
	panel.visible=false
	paused=true
	DirAccess.make_dir_recursive_absolute(capture_dir)
	_set_presentation(0)
	pattern_time=16.0*95.0/96.0
	caption.text="Worn night preview | full pose | unmeasured optics"
	await _save("night-mannequin.png")
	_set_presentation(1)
	pattern_time=2
	caption.text="Compact Fibonacci | worn night preview | unmeasured optics"
	for view in [["night-front.png",0,0],["night-angled.png",45,-12],["night-side.png",90,0]]:
		yaw=view[1]
		pitch_angle=view[2]
		_update_camera()
		await _save(view[0])
	yaw=45
	pitch_angle=-12
	_update_camera()
	enabled[1]=false
	await _save("night-inner-off.png")
	enabled.fill(false)
	await _save("night-leds-off.png")
	enabled.fill(true)
	for style in range(3):
		pattern=style
		var name=["rainbow","ocean","sunset"][style]
		caption.text="Glow PETG | "+name.capitalize()+" | worn night preview | unmeasured optics"
		for frame in range(384):
			yaw=65.0*cos(TAU*frame/384.0)
			pitch_angle=-12
			pattern_time=frame/24.0
			_update_camera()
			await _save("gradient-%s-%04d.png" % [name,frame])
			if frame%96==0: print("STACKED CAPTURE: "+name+" "+str(frame)+"/384",true)
	_set_presentation(2)
	pattern=0
	pattern_time=2
	_explode(1)
	distance=0.85
	yaw=65
	pitch_angle=-16
	_update_camera()
	caption.text="Compact concept | exploded optical stack | unmeasured fit"
	await _save("exploded.png")
	print("STACKED CAPTURE PASS: matched 24 fps, 16 second sweeps and separate stills")
	get_tree().quit()

func _check():
	assert(metadata.leds.size()==520)
	assert(metadata.counts.size()==5 and int(metadata.counts[0])==256)
	for i in range(1,5): assert(int(metadata.counts[i])==66)
	var band=meshes.SideDiffuser.get_aabb()
	assert(is_equal_approx(band.size.z,0.030))
	for led in metadata.leds:
		if int(led.group)>=2:
			assert(is_equal_approx(float(led.position_m[2]),float(metadata.optics.side_first_z)+(int(led.group)-2)*float(metadata.optics.side_pitch)))
	assert(meshes.size()==metadata.parts.size())
	var mask=cell_map.get_image()
	for i in range(256):
		var p=metadata.centres_m[i]
		var pixel=mask.get_pixel(int(1024*(0.5+p[0]/0.166)),int(1024*(0.5-p[1]/0.166)))
		assert(pixel.g>0.5 and int(round(pixel.r*255))==i,"Cell map loses manufacturer index "+str(i))
	assert(is_equal_approx(float(metadata.dimensions_m.diameter),0.190))
	assert(is_equal_approx(float(metadata.optics.front_z)-float(metadata.optics.rear_z),0.020))
	assert(mannequin.visible and backdrop.visible)
	_set_presentation(1)
	assert(is_equal_approx(distance,0.46))
	assert(is_equal_approx(camera.fov,38.0))
	assert(is_equal_approx(camera.near,0.005) and is_equal_approx(camera.far,30.0))
	assert(is_equal_approx(brightness,float(metadata.comparison.brightness)))
	assert(is_equal_approx(target.z,COMPARISON_FRONT_Z))
	for selection in range(3):
		pattern=selection
		var moving=0
		for led in metadata.leds:
			assert(_pattern_colour(led,0).is_equal_approx(_pattern_colour(led,16)))
			var changes=false
			for t in [0.5,1.0,2.0,4.0]:
				assert(is_equal_approx(_pattern_colour(led,t).v,1.0))
				if not _pattern_colour(led,0).is_equal_approx(_pattern_colour(led,t)): changes=true
			if changes: moving+=1
		assert(moving==metadata.leds.size())
	pattern=4
	pattern_time=0
	_update_colours()
	var whites=0
	for led in metadata.leds:
		if colour_image.get_pixel(int(led.index),int(led.group))==Color.WHITE: whites+=1
	assert(whites==1)
	pattern=0
	toggles[1].button_pressed=false
	assert(not enabled[1] and enabled[0] and enabled[2])
	_update_colours()
	assert(colour_image.get_pixel(0,1)==Color.BLACK)
	assert(colour_image.get_pixel(0,0)!=Color.BLACK)
	toggles[2].button_pressed=false
	_update_colours()
	for row in range(2,enabled.size()):
		assert(not enabled[row] and colour_image.get_pixel(0,row)==Color.BLACK)
	assert(enabled[0] and not enabled[1])
	toggles[2].button_pressed=true
	for row in range(2,enabled.size()): assert(enabled[row])
	_explode(1)
	assert(meshes.FrontMirror.position.z>transforms.FrontMirror.origin.z)
	_explode(0)
	assert(meshes.FrontMirror.transform==transforms.FrontMirror)
	print("STACKED SCENE PASS: CAD meshes, 520 LEDs, three side rows, controls, pose, world cameras and loops")
	get_tree().quit()

func _gpu_check(reference_path):
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
	for key in ["front_z","rear_z","wall_radius","ring_z","pitch_radius","rear_external_reflectance"]:
		material.set_shader_parameter(key,float(metadata.optics[key]))
	material.set_shader_parameter("diffusion",float(metadata.comparison.diffusion))
	plane.material_override=material
	viewport.add_child(plane)
	for sample in samples.cavity:
		material.set_shader_parameter("ray_point",Vector3(sample.point[0],sample.point[1],sample.point[2]))
		material.set_shader_parameter("ray_direction",Vector3(sample.direction[0],sample.direction[1],sample.direction[2]))
		for i in range(4): material.set_shader_parameter(["front_r","front_t","rear_r","rear_t"][i],float(sample.coefficients[i]))
		await _settle()
		var measured=viewport.get_texture().get_image().get_pixel(8,8).srgb_to_linear()
		var expected=Color(sample.expected[0],sample.expected[1],sample.expected[2]/32.0)
		if absf(measured.r-expected.r)>0.009 or absf(measured.g-expected.g)>0.009 or absf(measured.b-expected.b)>0.009:
			push_error("Stacked GPU mismatch: "+str(sample)+" measured "+str(measured)+" expected "+str(expected))
			get_tree().quit(1)
			return
	material=ShaderMaterial.new()
	material.shader=load("res://side_diagnostic.gdshader")
	material.set_shader_parameter("group",2)
	material.set_shader_parameter("count",66)
	material.set_shader_parameter("led_z",float(metadata.optics.side_first_z))
	material.set_shader_parameter("row_pitch",float(metadata.optics.side_pitch))
	material.set_shader_parameter("axial_scatter",float(metadata.optics.side_axial_scatter))
	material.set_shader_parameter("pitch_radius",float(metadata.optics.side_radius))
	material.set_shader_parameter("diffusion",float(metadata.comparison.diffusion))
	material.set_shader_parameter("brightness",0.25)
	material.set_shader_parameter("transmission",1.0)
	material.set_shader_parameter("ring_absorption",Vector3.ZERO)
	material.set_shader_parameter("ring_prompt_green",0.0)
	var field=Image.create(256,metadata.counts.size(),false,Image.FORMAT_RGBAF)
	var charge_field=Image.create(256,metadata.counts.size(),false,Image.FORMAT_RGBAF)
	var field_texture=ImageTexture.create_from_image(field)
	var charge_texture=ImageTexture.create_from_image(charge_field)
	material.set_shader_parameter("colours",field_texture)
	material.set_shader_parameter("charges",charge_texture)
	plane.material_override=material
	for sample in samples.side:
		field.fill(Color.BLACK)
		for row in range(int(sample.rows)):
			var rgb=sample.row_colours[row]
			for pixel in range(66): field.set_pixel(pixel,2+row,Color(rgb[0],rgb[1],rgb[2],1))
		charge_field.fill(Color(0,0,0,1) if sample.lit else Color(0.35,0.20,0,1))
		field_texture.update(field)
		charge_texture.update(charge_field)
		material.set_shader_parameter("row_count",int(sample.rows))
		material.set_shader_parameter("sample_point",Vector3(sample.point[0],sample.point[1],sample.point[2]))
		await _settle()
		var measured=viewport.get_texture().get_image().get_pixel(8,8).srgb_to_linear()
		var expected=Color(sample.expected[0],sample.expected[1],sample.expected[2])
		if absf(measured.r-expected.r)>0.009 or absf(measured.g-expected.g)>0.009 or absf(measured.b-expected.b)>0.009:
			push_error("Side-row GPU mismatch: "+str(sample)+" measured "+str(measured)+" expected "+str(expected))
			get_tree().quit(1)
			return
	print("STACKED GPU OPTICS PASS: %d cavity and %d side-row cases" % [samples.cavity.size(),samples.side.size()])
	get_tree().quit()
