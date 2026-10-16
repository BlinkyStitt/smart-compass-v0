shader_type spatial;
// Complete-sheet transmission passes the already rendered LED source once.
uniform float sheet_reflectance=0.038725;
uniform float sheet_transmission=0.29;
void fragment() {
    ALBEDO=vec3(sheet_reflectance/max(1.0-sheet_transmission,0.0001));
    METALLIC=1.0;
    ROUGHNESS=0.3;
    ALPHA=1.0-sheet_transmission;
}
