shader_type spatial;
render_mode unshaded,cull_disabled,fog_disabled;
uniform vec3 sample_point;
#include "res://side_surface.gdshaderinc"
void fragment() { ALBEDO=surface_light(sample_point); }
