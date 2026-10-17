shader_type spatial;
render_mode cull_disabled;
uniform vec3 ring_albedo = vec3(0.72,0.82,0.54);
uniform float ring_roughness = 0.82;
uniform float ring_metallic = 0.0;
varying vec3 world_position;
#include "res://side_surface.gdshaderinc"
void vertex() { world_position=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz; }
void fragment() {
    ALBEDO=ring_albedo;
    ROUGHNESS=ring_roughness;
    METALLIC=ring_metallic;
    EMISSION=surface_light(world_position);
}
