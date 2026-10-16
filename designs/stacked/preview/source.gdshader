shader_type spatial;
render_mode cull_disabled;
varying vec3 world_position;
#include "res://trace.gdshaderinc"
void vertex() { world_position=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz; }
void fragment() {
    ALBEDO=vec3(0.08);
    ROUGHNESS=0.65;
    EMISSION=source_light(world_position);
}
