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
void fragment() {
    float spread=mix(0.0025,0.014,diffusion);
    float weight=exp(-dot(pos.xy-led_position.xy,pos.xy-led_position.xy)/(spread*spread));
    ALBEDO=vec3(0.12);
    ROUGHNESS=0.65;
    EMISSION=texelFetch(colours,ivec2(index,0),0).rgb*brightness*transmission*weight;
}
