uniform int group=2;
uniform int count=66;
uniform int row_count=1;
uniform float row_pitch=0.010;
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
#include "res://ring_diffusion.gdshaderinc"

vec3 surface_light(vec3 p) {
    vec3 emitted=vec3(0.0);
    vec3 stored=vec3(0.0);
    float total=0.0;
    for (int row=0;row<row_count;row++) {
        float z=led_z+float(row)*row_pitch;
        // Sum the actual sources. Interpolate the local phosphor state once.
        vec3 row_stored=ring_light(p,group+row,count,pitch_radius,z,wall_mm,0.0,transmission);
        emitted+=ring_light(p,group+row,count,pitch_radius,z,wall_mm,brightness,transmission)-row_stored;
        float weight=exp(-pow((p.z-z)/row_pitch,2.0));
        stored+=row_stored*weight;
        total+=weight;
    }
    return emitted+stored/max(total,0.000001);
}
