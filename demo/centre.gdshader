shader_type spatial;
// Alpha compositing applies transmission once. Reflectance is the remaining
// PBR layer's colour; R+T<=1 bounds it. Only the outward surface is drawn.
uniform float reflectance=0.04;
uniform float transmission=0.8;
void fragment() {
    ALBEDO=vec3(reflectance/max(1.0-transmission,0.0001));
    METALLIC=1.0;
    ROUGHNESS=0.08;
    ALPHA=1.0-transmission;
}
