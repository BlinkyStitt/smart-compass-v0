shader_type spatial;
render_mode cull_disabled;
uniform bool cavity_closed=true;
varying vec3 world_position;
#include "res://trace.gdshaderinc"
void vertex() { world_position=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz; }
void fragment() {
    vec3 dir=normalize(world_position-INV_VIEW_MATRIX[3].xyz);
    vec3 p=world_position;
    if (abs(dir.z)>0.000001) { p+=dir*((front_z-p.z)/dir.z); }
    EMISSION=cavity_closed?trace_stacked(p,dir,false):vec3(0.0);
    ALBEDO=vec3(front_r);
    METALLIC=1.0;
    ROUGHNESS=0.3;
    SPECULAR=front_r;
}
