uniform int group=2;
uniform int count=66;
uniform int row_count=3;
uniform float row_pitch=0.010;
uniform float led_z=0.019;
uniform float wall_mm=2.0;
uniform float diffusion=0.65;
uniform float axial_scatter=0.0075;
uniform float brightness=2.0;
uniform float transmission=0.4;
uniform float seam_gap=0.003;
uniform float pitch=0.00833333333;
uniform float pitch_radius=0.08801;
uniform sampler2D colours : filter_nearest, repeat_disable;
uniform sampler2D charges : filter_nearest, repeat_disable;
#include "res://ring_diffusion.gdshaderinc"

vec3 surface_light(vec3 p) {
    // The broad sleeve mixes rows; the cavity's thin diffuser keeps its
    // narrower profile. This RMS scatter scale is an unmeasured material
    // assumption. Include the variance of a 5 mm emitter in the Gaussian.
    float sigma=sqrt(0.005*0.005/12.0+pow(axial_scatter*diffusion,2.0));
    // Preserve each source's original axial integral as its light spreads.
    float area=0.005+sqrt(3.14159265359)*mix(0.00015,0.003,diffusion);
    vec3 incident=vec3(0.0);
    vec2 stored=vec2(0.0);
    float total=0.0;
    for (int row=0;row<row_count;row++) {
        float z=led_z+float(row)*row_pitch;
        float weight=exp(-0.5*pow((p.z-z)/sigma,2.0));
        incident+=ring_field(colours,p,group+row,count,pitch_radius)*weight;
        stored+=ring_field(charges,p,group+row,count,pitch_radius).rg*weight;
        total+=weight;
    }
    float angle=mod(atan(p.x,p.y)+6.28318530718,6.28318530718);
    float coord=(angle*pitch_radius-seam_gap*0.5)/pitch-0.5;
    float peak=0.5+0.5*cos(6.28318530718*coord);
    float hotspot=mix(1.0-0.15*(1.0-diffusion),1.0,peak);
    incident*=area*hotspot/(sqrt(6.28318530718)*sigma);
    vec3 filtered=incident*exp(-ring_absorption*wall_mm)*transmission;
    vec3 green=vec3(0.16,1.0,0.025);
    vec3 prompt=green*incident.b*ring_prompt_green;
    // The phosphor belongs to one sleeve. Interpolate its charge once.
    stored/=max(total,0.000001);
    return (filtered+prompt)*brightness+green*(0.18*stored.r+0.045*stored.g)*ring_stored_emission;
}
