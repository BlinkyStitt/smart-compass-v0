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
varying vec3 pos;
void vertex() { pos = (MODEL_MATRIX * vec4(VERTEX,1.0)).xyz; }
void fragment() {
    float angle = mod(atan(pos.x,pos.y)+6.28318530718,6.28318530718);
    float coord = (angle*pitch_radius-seam_gap*0.5)/pitch-0.5;
    int index = int(clamp(floor(coord+0.5),0.0,float(count-1)));
    vec3 light = vec3(0.0);
    float total = 0.0;
    for (int j=-2;j<=2;j++) {
        int k=index+j;
        if (k>=0 && k<count) {
            float w=exp(-pow((coord-float(k))/mix(0.22,1.6,diffusion),2.0));
            light+=texelFetch(colours,ivec2(k,group),0).rgb*w;
            total+=w;
        }
    }
    float vertical=exp(-pow(max(0.0,abs(pos.z-led_z)-0.0025)/mix(0.00015,0.008,diffusion),2.0));
    ALBEDO=vec3(0.018);
    ROUGHNESS=0.45;
    EMISSION=light/max(total,0.0001)*vertical*transmission*brightness;
    if (coord < -0.5 || coord > float(count)-0.5) { EMISSION=vec3(0.0); }
}
