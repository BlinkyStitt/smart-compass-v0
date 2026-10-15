shader_type spatial;
render_mode unshaded, cull_disabled;
uniform vec2 offset=vec2(0.0);
uniform float film_transmission=1.0;
uniform float film_reflectance=0.0;
uniform float substrate_transmission=0.29;
uniform float surface_reflectance=0.04;
#include "res://centre_diffusion.gdshaderinc"
void fragment() {
    ALBEDO=vec3(black_sheet_exit(film_transmission,substrate_transmission),
        black_sheet_reflection(film_reflectance,substrate_transmission,surface_reflectance),
        centre_profile(offset,0.65));
}
