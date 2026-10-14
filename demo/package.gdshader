shader_type spatial;
render_mode cull_disabled;
uniform sampler2D colours : filter_nearest, repeat_disable;
uniform float brightness = 2.0;
varying vec3 package_normal;
void vertex() { package_normal = NORMAL; }
void fragment() {
    // COLOR_0.r stores the manufacturer's pixel index divided by 255.
    // Every triangle of a package has one index; only its front face emits.
    int index = int(round(COLOR.r*255.0));
    float front = step(0.99,package_normal.z);
    ALBEDO=mix(vec3(0.12),vec3(0.75,0.74,0.61),front);
    ROUGHNESS=0.6;
    EMISSION=texelFetch(colours,ivec2(index,0),0).rgb*brightness*front;
}
