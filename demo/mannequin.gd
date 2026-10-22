extends Node3D
# Display-only metre-scale mannequin. The pendant stays in its CAD coordinates.
# Pose and straps illustrate wearing context, not fit or suspension acceptance.
var surfaces: Array[MeshInstance3D] = []

func _material(colour: Color, roughness: float = 0.7):
	var material = StandardMaterial3D.new()
	material.albedo_color = colour
	material.roughness = roughness
	return material

func _mesh(label: String, mesh: Mesh, material: Material, centre: Vector3):
	var instance = MeshInstance3D.new()
	instance.name = label
	instance.mesh = mesh
	instance.material_override = material
	instance.position = centre
	add_child(instance)
	surfaces.append(instance)
	return instance

func _oval(label: String, centre: Vector3, dimensions: Vector3, material: Material):
	var sphere = SphereMesh.new()
	sphere.radius = 0.5
	sphere.height = 1.0
	sphere.radial_segments = 32
	sphere.rings = 16
	var instance = _mesh(label,sphere,material,centre)
	instance.scale = dimensions
	return instance

func _limb(label: String, start: Vector3, end: Vector3, radius: float, material: Material):
	var capsule = CapsuleMesh.new()
	capsule.radius = radius
	capsule.height = start.distance_to(end)+radius*2.0
	capsule.radial_segments = 24
	capsule.rings = 8
	var instance = _mesh(label,capsule,material,(start+end)*0.5)
	instance.quaternion = Quaternion(Vector3.UP,(end-start).normalized())
	return instance

func _webbing(label: String, points: Array, material: Material):
	for i in range(points.size()-1):
		var strip = BoxMesh.new()
		strip.size = Vector3(0.010,points[i].distance_to(points[i+1])+0.002,0.0015)
		var instance = _mesh(label+str(i),strip,material,(points[i]+points[i+1])*0.5)
		instance.quaternion = Quaternion(Vector3.UP,(points[i+1]-points[i]).normalized())

func _spot(label: String, colour: Color, position_m: Vector3, energy: float):
	var light = SpotLight3D.new()
	light.name = label
	light.position = position_m
	light.light_color = colour
	light.light_energy = energy
	light.spot_range = 5.0
	light.spot_angle = 50.0
	light.shadow_enabled = true
	add_child(light)
	light.look_at(Vector3(0,0.1,-0.1),Vector3.UP)

# Closed elliptical gold sections in head-local coordinates, including inner walls.
func _crown_section(label: String, bottom: float, top: float, pointed: bool, material: Material, head: MeshInstance3D):
	var tool = SurfaceTool.new()
	tool.begin(Mesh.PRIMITIVE_TRIANGLES)
	var segments = 16 if pointed else 64
	for i in range(segments):
		var edges = []
		for j in range(2):
			var index = i+j
			var angle = TAU*index/segments
			var height = top if not pointed or index%2==0 else bottom
			var outer = Vector3(0.086*sin(angle),0,0.096*cos(angle))
			var inner = Vector3(0.078*sin(angle),0,0.088*cos(angle))
			edges.append([outer+Vector3.UP*bottom,outer+Vector3.UP*height,
				inner+Vector3.UP*height,inner+Vector3.UP*bottom])
		for side in range(4):
			var next = (side+1)%4
			for vertex in [edges[0][side],edges[1][side],edges[1][next],
				edges[0][side],edges[1][next],edges[0][next]]:
				tool.add_vertex(vertex)
	tool.generate_normals()
	var section = _mesh(label,tool.commit(),material,head.position)
	section.rotation = head.rotation

func check_crown():
	for label in ["CrownBand","CrownPoints"]:
		var section = get_node_or_null(label) as MeshInstance3D
		assert(section != null and section.visible and section.mesh != null,"Missing crown: "+label)
		assert(surfaces.has(section),"Crown must participate in full-body framing")
		assert(section.transform.is_equal_approx(Transform3D(Basis.from_euler($Head.rotation),$Head.position)),"Crown must follow the head tilt")
	assert(not has_node("Cap") and not has_node("CapBrim"),"Crown replaces the backward cap")

func build():
	var body = _material(Color(0.39,0.41,0.44),0.76)
	var joint = _material(Color(0.22,0.24,0.27),0.65)
	var black = _material(Color(0.025,0.027,0.033),0.92)
	var chest = _oval("Chest",Vector3(0,0.14,-0.195),Vector3(0.43,0.48,0.27),body)
	chest.rotation.x = deg_to_rad(-12)
	_oval("ShoulderYoke",Vector3(0,0.31,-0.23),Vector3(0.47,0.14,0.21),body)
	_oval("Waist",Vector3(0,-0.16,-0.125),Vector3(0.28,0.23,0.21),body)
	var pelvis = _oval("Pelvis",Vector3(0,-0.31,-0.08),Vector3(0.35,0.23,0.25),body)
	pelvis.rotation.z = deg_to_rad(-7)
	_limb("Neck",Vector3(0,0.36,-0.235),Vector3(-0.015,0.47,-0.25),0.05,body)
	var head = _oval("Head",Vector3(-0.03,0.60,-0.265),Vector3(0.18,0.25,0.20),body)
	head.rotation_degrees = Vector3(-12,12,12)
	# Broad gold band and eight tall points, following the head without its oval scale.
	var gold = _material(Color(0.95,0.64,0.16),0.28)
	gold.metallic = 0.65
	gold.cull_mode = BaseMaterial3D.CULL_DISABLED
	_crown_section("CrownBand",0.060,0.105,false,gold,head)
	_crown_section("CrownPoints",0.105,0.185,true,gold,head)
	# Raised arm and open hand: a celebratory pose with the clock on display.
	var shoulder = Vector3(-0.215,0.32,-0.215)
	var elbow = Vector3(-0.44,0.53,-0.14)
	var wrist = Vector3(-0.36,0.74,-0.035)
	_oval("RaisedShoulder",shoulder,Vector3.ONE*0.115,joint)
	_limb("RaisedUpperArm",shoulder,elbow,0.052,body)
	_oval("RaisedElbow",elbow,Vector3.ONE*0.087,joint)
	_limb("RaisedForearm",elbow,wrist,0.040,body)
	var palm = _oval("RaisedPalm",Vector3(-0.36,0.79,-0.025),Vector3(0.075,0.105,0.035),body)
	palm.rotation_degrees.z = -12
	for i in range(4):
		var x = -0.388+i*0.019
		_limb("RaisedFinger"+str(i),Vector3(x,0.824,-0.018),Vector3(x-0.012,0.884-absf(i-1.5)*0.009,-0.015),0.008,body)
	_limb("RaisedThumb",Vector3(-0.397,0.785,-0.02),Vector3(-0.435,0.814,-0.015),0.010,body)
	# Other hand points toward the pendant without crossing its lit face.
	shoulder = Vector3(0.215,0.32,-0.215)
	elbow = Vector3(0.44,0.045,-0.07)
	wrist = Vector3(0.245,0.065,0.105)
	_oval("PointingShoulder",shoulder,Vector3.ONE*0.115,joint)
	_limb("PointingUpperArm",shoulder,elbow,0.052,body)
	_oval("PointingElbow",elbow,Vector3.ONE*0.087,joint)
	_limb("PointingForearm",elbow,wrist,0.040,body)
	_oval("PointingPalm",Vector3(0.211,0.067,0.113),Vector3(0.085,0.060,0.037),body)
	_limb("PointingIndex",Vector3(0.18,0.086,0.12),Vector3(0.129,0.076,0.12),0.009,body)
	for i in range(3):
		_oval("CurledFinger"+str(i),Vector3(0.18,0.065-i*0.012,0.13),Vector3(0.031,0.014,0.026),body)
	_limb("PointingThumb",Vector3(0.215,0.09,0.115),Vector3(0.186,0.112,0.12),0.010,body)
	# Bent knees and wide stance support the backward torso lean.
	for side in [-1.0,1.0]:
		var hip = Vector3(side*0.115,-0.34,-0.08)
		var knee = Vector3(side*0.22,-0.68,0.07)
		var ankle = Vector3(side*0.32,-1.025,0.005)
		_limb("Thigh"+str(side),hip,knee,0.073,body)
		_oval("Knee"+str(side),knee,Vector3.ONE*0.11,joint)
		_limb("Calf"+str(side),knee,ankle,0.052,body)
		_oval("Foot"+str(side),Vector3(side*0.32,-1.08,0.085),Vector3(0.13,0.095,0.25),black)
		_webbing("Necklace"+str(side),[
			Vector3(side*0.053,0.43,-0.195),Vector3(side*0.13,0.29,-0.025),
			Vector3(side*0.12,0.15,-0.020),Vector3(side*0.084,0.064,-0.012)],black)
	var neck_loop = []
	for i in range(17):
		var angle = TAU*i/16.0
		neck_loop.append(Vector3(0.075*sin(angle),0.43,-0.245+0.07*cos(angle)))
	_webbing("NeckLoop",neck_loop,black)
	# Assumed distant camp lighting; this is not a calibrated lux environment.
	_spot("AmberCampLight",Color(1.0,0.48,0.20),Vector3(-1.6,0.9,-0.8),0.2)
	_spot("BlueCampRim",Color(0.24,0.48,1.0),Vector3(1.1,0.8,-0.7),0.25)
