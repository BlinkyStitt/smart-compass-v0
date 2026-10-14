shader_type spatial;
render_mode unshaded, cull_disabled, fog_disabled;
uniform sampler2D colours : filter_nearest, repeat_disable;
uniform sampler2D charges : filter_nearest, repeat_disable;
uniform float diffusion=0.65;
uniform float pitch;
uniform float seam_gap;
uniform int group;
uniform int count;
uniform float radius;
uniform float led_z;
uniform vec3 sample_point;
uniform float brightness=2.0;
uniform float transmission=0.4;
uniform float wall_mm=1.0;
#include "res://ring_diffusion.gdshaderinc"
void fragment() {
    ALBEDO=glow_ring_light(sample_point,group,count,radius,led_z,wall_mm,brightness,transmission);
}
