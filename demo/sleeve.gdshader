shader_type spatial;
render_mode cull_disabled;
uniform sampler2D colours : filter_nearest, repeat_disable;
uniform int group = 3;
uniform int count = 90;
uniform float pitch_radius = 0.11984367;
uniform float seam_gap = 0.003;
uniform float pitch = 0.00833333;
uniform float led_z = 0.0201;
uniform float brightness = 2.0;
uniform float transmission = 0.4;
uniform float diffusion = 0.65;
uniform vec3 assembly_offset = vec3(0.0);
varying vec3 pos;
void vertex() { pos = (MODEL_MATRIX * vec4(VERTEX,1.0)).xyz - assembly_offset; }
#include "res://ring_diffusion.gdshaderinc"
void fragment() {
    ALBEDO=vec3(0.018);
    ROUGHNESS=0.45;
    EMISSION=diffused_ring_light(pos,group,count,pitch_radius,led_z)*transmission*brightness;
}
