shader_type spatial;
render_mode cull_disabled;
varying vec3 world_position;
varying vec3 world_normal;
#include "res://trace.gdshaderinc"
void vertex() {
    world_position=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz;
    world_normal=normalize((MODEL_NORMAL_MATRIX*NORMAL));
}
void fragment() {
    bool coated_face=world_normal.z>0.5;
    ALBEDO=vec3(coated_face?rear_r:rear_external_reflectance);
    METALLIC=1.0;
    ROUGHNESS=0.3;
    // Draw transmitted cell light explicitly, without a second alpha/filter loss.
    EMISSION=coated_face?rear_t*source_light(world_position):vec3(0.0);
}
