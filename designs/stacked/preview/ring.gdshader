shader_type spatial;
render_mode cull_disabled;
varying vec3 world_position;
#include "res://ring_surface.gdshaderinc"
void vertex() { world_position=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz; }
void fragment() {
    ALBEDO=vec3(0.72,0.82,0.54);
    ROUGHNESS=0.82;
    EMISSION=surface_light(world_position);
}
