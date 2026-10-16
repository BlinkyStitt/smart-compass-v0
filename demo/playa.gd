extends Node3D

const RADIUS = 20.0
const ARC_DEGREES = 210.0
const GROUND_Y = -1.13
const HORIZON_V = 0.62
var panorama: MeshInstance3D
var ground: MeshInstance3D

func build():
	var texture=ImageTexture.create_from_image(Image.load_from_file(ProjectSettings.globalize_path("res://assets/playa-night.png")))
	# The image stays in world space on a curved wall around the field.
	# Its ground portion continues across a horizontal plane under the wearer.
	var vertices=PackedVector3Array()
	var uvs=PackedVector2Array()
	var indices=PackedInt32Array()
	for i in range(129):
		var u=i/128.0
		var angle=deg_to_rad((u-0.5)*ARC_DEGREES)
		var x=RADIUS*sin(angle)
		var z=-RADIUS*cos(angle)
		vertices.append(Vector3(x,GROUND_Y,z))
		vertices.append(Vector3(x,GROUND_Y+35.0,z))
		uvs.append(Vector2(u,HORIZON_V))
		uvs.append(Vector2(u,0))
		if i<128:
			var k=i*2
			indices.append_array(PackedInt32Array([k,k+1,k+2,k+1,k+3,k+2]))
	var arrays=[]
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX]=vertices
	arrays[Mesh.ARRAY_TEX_UV]=uvs
	arrays[Mesh.ARRAY_INDEX]=indices
	var mesh=ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
	var material=StandardMaterial3D.new()
	material.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
	material.cull_mode=BaseMaterial3D.CULL_DISABLED
	material.albedo_texture=texture
	panorama=MeshInstance3D.new()
	panorama.name="CurvedPlaya"
	panorama.mesh=mesh
	panorama.material_override=material
	add_child(panorama)
	var floor_mesh=PlaneMesh.new()
	floor_mesh.size=Vector2(200,200)
	var shader=Shader.new()
	shader.code="""shader_type spatial;
render_mode unshaded, cull_disabled;
uniform sampler2D panorama : source_color, filter_linear;
varying vec3 world_position;
void vertex() { world_position=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz; }
void fragment() {
 vec2 uv=vec2(fract(world_position.x*0.035+world_position.z*0.011),0.68+0.31*fract(world_position.z*0.043));
 ALBEDO=texture(panorama,uv).rgb;
}
"""
	var floor_material=ShaderMaterial.new()
	floor_material.shader=shader
	floor_material.set_shader_parameter("panorama",texture)
	ground=MeshInstance3D.new()
	ground.name="PlayaGround"
	ground.mesh=floor_mesh
	ground.position.y=GROUND_Y
	ground.material_override=floor_material
	add_child(ground)
