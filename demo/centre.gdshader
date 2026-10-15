shader_type spatial;
// Only the outward black-sheet surface is drawn. Alpha passes outgoing light
// once; the cavity-side film's external reflection crosses the substrate twice.
uniform float film_reflectance=0.0;
uniform float film_transmission=1.0;
uniform float substrate_transmission=0.29;
uniform float surface_reflectance=0.04;
#include "res://centre_diffusion.gdshaderinc"
void fragment() {
    float transmission=black_sheet_exit(film_transmission,substrate_transmission);
    float reflectance=black_sheet_reflection(film_reflectance,substrate_transmission,surface_reflectance);
    ALBEDO=vec3(reflectance/max(1.0-transmission,0.0001));
    METALLIC=1.0;
    ROUGHNESS=0.3;
    ALPHA=1.0-transmission;
}
