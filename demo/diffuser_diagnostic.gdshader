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
#include "res://ring_diffusion.gdshaderinc"
void fragment() {
    ALBEDO=diffused_ring_light(sample_point,group,count,radius,led_z);
}
