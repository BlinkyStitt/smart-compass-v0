shader_type spatial;
render_mode cull_disabled;
uniform int group=2;
uniform int count=66;
uniform float led_z=0.030;
uniform float wall_mm=2.0;
uniform float diffusion=0.65;
uniform float brightness=2.0;
uniform float transmission=0.4;
uniform float seam_gap=0.003;
uniform float pitch=0.00833333333;
uniform float pitch_radius=0.08801;
uniform sampler2D colours : filter_nearest, repeat_disable;
uniform sampler2D charges : filter_nearest, repeat_disable;
varying vec3 world_position;
#include "res://ring_diffusion.gdshaderinc"
void vertex() { world_position=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz; }
void fragment() {
    ALBEDO=vec3(0.72,0.82,0.54);
    ROUGHNESS=0.82;
    EMISSION=ring_light(world_position,group,count,pitch_radius,led_z,wall_mm,brightness,transmission);
}
