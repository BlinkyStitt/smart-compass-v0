uniform int group=1;
uniform int count=70;
uniform float led_z=0.0582;
uniform float wall_mm=1.0;
uniform float diffusion=0.65;
uniform float brightness=2.0;
uniform float transmission=0.4;
uniform float seam_gap=0.003;
uniform float pitch=0.00833333333;
uniform float pitch_radius=0.08801;
uniform sampler2D colours : filter_nearest, repeat_disable;
uniform sampler2D charges : filter_nearest, repeat_disable;
#include "res://ring_diffusion.gdshaderinc"

vec3 surface_light(vec3 p) {
    return ring_light(p,group,count,pitch_radius,led_z,wall_mm,brightness,transmission);
}
