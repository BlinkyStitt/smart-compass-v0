shader_type spatial;
render_mode cull_disabled;

// CAD metres. Trace a view ray between finite parallel mirror planes.
uniform sampler2D colours : filter_nearest, repeat_disable;
uniform float front_z = 0.0367;
uniform float rear_z = 0.0255;
uniform float halo_radius = 0.08901;
uniform float inner_radius = 0.10824;
uniform float strip_z = 0.0311;
uniform float reflectance = 0.65;
uniform float transmission = 0.25;
uniform float rear_reflectance = 0.94;
uniform float diffuser_transmission = 0.4;
uniform float diffusion = 0.65;
uniform float brightness = 2.0;
uniform vec3 pitch_radii;
uniform float seam_gap = 0.003;
uniform float pitch = 0.008333333;
varying vec3 world_position;

void vertex() { world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }

#include "res://cavity_trace.gdshaderinc"

vec3 ring_light(vec3 p, int group, float radius) {
    float angle = mod(atan(p.x, p.y)+6.28318530718, 6.28318530718);
    float coord = (angle*radius-seam_gap*0.5)/pitch-0.5;
    int count = group == 1 ? 64 : 84;
    if (coord < -0.5 || coord > float(count)-0.5) { return vec3(0.0); }
    int index = int(clamp(floor(coord+0.5), 0.0, float(count-1)));
    vec3 direct = texelFetch(colours, ivec2(index, group), 0).rgb;
    // Gaussian surface spread is an explicit unmeasured diffuser assumption.
    vec3 blur = vec3(0.0);
    float total = 0.0;
    for (int j=-2; j<=2; j++) {
        int k = index+j;
        if (k>=0 && k<count) {
            float w = exp(-pow((coord-float(k))/mix(0.25,1.6,diffusion),2.0));
            blur += texelFetch(colours, ivec2(k,group),0).rgb*w;
            total += w;
        }
    }
    float dz = abs(p.z-strip_z);
    float vertical = exp(-pow(max(0.0,dz-0.0025)/mix(0.00015,0.0035,diffusion),2.0));
    return mix(direct*step(abs(coord-float(index)),0.30),blur/max(total,0.0001),diffusion)*vertical;
}

void fragment() {
    vec3 eye = INV_VIEW_MATRIX[3].xyz;
    vec3 direction = normalize(world_position-eye);
    vec3 point = world_position;
    vec3 light = vec3(0.0);
    // Back and edge faces never show a false infinity tunnel.
    if (direction.z < -0.00001 && eye.z > front_z) {
        point += direction*((front_z-point.z)/direction.z);
        vec3 hit;
        vec3 traced=trace_cavity(point,direction,hit);
        if (traced.z>0.0) {
            int group=int(traced.z);
            light=traced.x*diffuser_transmission*ring_light(hit,group,group==1?pitch_radii.x:pitch_radii.y);
        }
    }
    ALBEDO = vec3(reflectance);
    METALLIC = 1.0;
    ROUGHNESS = 0.08;
    SPECULAR = reflectance;
    // Environment reflection is PBR; the cavity does not use SSR.
    EMISSION = light*brightness;
}
