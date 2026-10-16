shader_type spatial;
render_mode cull_disabled;

// CAD metres. Trace a view ray between finite parallel mirror planes.
uniform sampler2D colours : filter_nearest, repeat_disable;
uniform sampler2D charges : filter_nearest, repeat_disable;
uniform bool cavity_closed = true;
uniform float front_z = 0.0367;
uniform float rear_z = 0.0255;
uniform float halo_radius = 0.08901;
uniform float inner_radius = 0.10824;
uniform float strip_z = 0.0311;
uniform float reflectance = 0.70;
uniform float transmission = 0.09;
uniform float external_reflectance = 0.10;
uniform float rear_reflectance = 0.70;
uniform float diffuser_transmission = 0.4;
uniform float diffusion = 0.65;
uniform float brightness = 2.0;
uniform vec3 pitch_radii;
uniform vec3 ring_wall_mm;
uniform float seam_gap = 0.003;
uniform float pitch = 0.008333333;
varying vec3 world_position;

void vertex() { world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }

#include "res://cavity_trace.gdshaderinc"

#include "res://ring_diffusion.gdshaderinc"

void fragment() {
    vec3 eye = INV_VIEW_MATRIX[3].xyz;
    vec3 direction = normalize(world_position-eye);
    vec3 point = world_position;
    vec3 light = vec3(0.0);
    // Back and edge faces never show a false infinity tunnel.
    if (cavity_closed && direction.z < -0.00001 && eye.z > front_z) {
        point += direction*((front_z-point.z)/direction.z);
        vec3 hit;
        vec3 traced=trace_cavity(point,direction,hit);
        if (traced.z>0.0) {
            int group=int(traced.z);
            light=traced.x*ring_light(hit,group,group==1?64:84,group==1?pitch_radii.x:pitch_radii.y,strip_z,group==1?ring_wall_mm.x:ring_wall_mm.y,brightness,diffuser_transmission);
        }
    }
    // Complete coated-black-sheet coefficients include substrate absorption.
    ALBEDO = vec3(external_reflectance);
    METALLIC = 1.0;
    ROUGHNESS = 0.3;
    SPECULAR = reflectance;
    // Environment reflection is PBR; transmitted cavity light is traced above.
    EMISSION = light;
}
