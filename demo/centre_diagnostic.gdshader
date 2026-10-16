shader_type spatial;
render_mode unshaded, cull_disabled;
uniform vec2 offset=vec2(0.0);
uniform float sheet_transmission=0.29;
uniform float sheet_reflectance=0.038725;
#include "res://centre_diffusion.gdshaderinc"
void fragment() {
    ALBEDO=vec3(sheet_transmission,sheet_reflectance,centre_profile(offset,0.65));
}
