shader_type spatial;
render_mode cull_disabled;
uniform sampler2D colours : filter_nearest, repeat_disable;
uniform int index = 0;
uniform float brightness = 2.0;
uniform float transmission = 0.8;
uniform float diffusion = 0.65;
uniform vec3 led_position;
varying vec3 pos;
void vertex() { pos=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz; }
#include "res://centre_diffusion.gdshaderinc"
void fragment() {
    float weight=centre_profile(pos.xy-led_position.xy,diffusion);
    ALBEDO=vec3(0.012);
    ROUGHNESS=0.65;
    EMISSION=texelFetch(colours,ivec2(index,0),0).rgb*brightness*transmission*weight;
}
