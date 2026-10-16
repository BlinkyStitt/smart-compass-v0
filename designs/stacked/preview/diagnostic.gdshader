shader_type spatial;
render_mode unshaded,cull_disabled,fog_disabled;
uniform vec3 ray_point;
uniform vec3 ray_direction;
#include "res://trace.gdshaderinc"
void fragment() {
    vec3 stats=trace_stacked(ray_point,normalize(ray_direction),true);
    ALBEDO=vec3(stats.r,stats.g,stats.b/32.0);
}
