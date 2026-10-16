uniform int inner_count=70;
uniform float front_z=0.0692;
uniform float rear_z=0.0492;
uniform float source_plane_z=0.0492;
uniform float wall_radius=0.08386;
uniform float ring_z=0.0592;
uniform float front_r=0.70;
uniform float front_t=0.30;
uniform float rear_r=0.70;
uniform float rear_t=0.09;
uniform float diffusion=0.65;
uniform float brightness=2.0;
// Complete coated-black-sheet coefficients already include substrate loss.
uniform float rear_external_reflectance=0.10;
uniform float diffuser_transmission=0.4;
uniform float seam_gap=0.003;
uniform float pitch=0.00833333333;
uniform float pitch_radius=0.08801;
uniform sampler2D colours : filter_nearest, repeat_disable;
uniform sampler2D charges : filter_nearest, repeat_disable;
uniform sampler2D positions : filter_nearest, repeat_disable;
uniform sampler2D cell_map : filter_nearest, repeat_disable;
#include "res://ring_diffusion.gdshaderinc"
#include "res://centre_diffusion.gdshaderinc"

vec3 source_light(vec3 p) {
    vec2 uv=vec2(p.x/0.166+0.5,0.5-p.y/0.166);
    if (any(lessThan(uv,vec2(0.0))) || any(greaterThan(uv,vec2(1.0)))) { return vec3(0.0); }
    vec2 cell=texture(cell_map,uv).rg;
    if (cell.g<0.5) { return vec3(0.0); }
    int index=int(round(cell.r*255.0));
    vec2 delta=p.xy-texelFetch(positions,ivec2(index,0),0).rg;
    float profile=centre_profile(delta,diffusion);
    return texelFetch(colours,ivec2(index,0),0).rgb*brightness*profile;
}

// Unfolded reference tests exercise this same transport, without source textures.
vec3 trace_stacked(vec3 p, vec3 dir, bool diagnostic) {
    vec3 light=vec3(0.0);
    vec3 stats=vec3(0.0);
    if (dir.z>=-0.00000001 || length(p.xy)>=wall_radius) { return light; }
    float weight=front_t;
    for (int bounce=0;bounce<32;bounce++) {
        if (weight<0.001) { break; }
        float plane=dir.z<0.0?rear_z:front_z;
        float plane_t=(plane-p.z)/dir.z;
        float a=dot(dir.xy,dir.xy);
        float b=dot(p.xy,dir.xy);
        float c=dot(p.xy,p.xy)-wall_radius*wall_radius;
        float wall_t=1e10;
        if (a>1e-14) { wall_t=(-b+sqrt(max(0.0,b*b-a*c)))/a; }
        if (wall_t<plane_t) {
            vec3 hit=p+dir*wall_t;
            float spread=mix(0.00015,0.003,diffusion);
            float axial=exp(-pow(max(0.0,abs(hit.z-ring_z)-0.0025)/spread,2.0));
            stats.g=weight*axial;
            if (!diagnostic) { light+=weight*ring_light(hit,1,inner_count,pitch_radius,ring_z,1.0,brightness,diffuser_transmission); }
            break;
        }
        p+=dir*plane_t;
        if (dir.z<0.0) {
            stats.r+=weight*rear_t;
            if (!diagnostic) {
                vec3 source=p+dir*((source_plane_z-p.z)/dir.z);
                light+=weight*rear_t*source_light(source);
            }
            weight*=rear_r;
        } else { weight*=front_r; }
        stats.b+=1.0;
        dir.z=-dir.z;
    }
    return diagnostic?stats:light;
}
