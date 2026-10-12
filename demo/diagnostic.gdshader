shader_type spatial;
render_mode unshaded, cull_disabled, fog_disabled;
uniform float front_z;
uniform float rear_z;
uniform float halo_radius;
uniform float inner_radius;
uniform float reflectance;
uniform float transmission;
uniform float rear_reflectance=0.94;
uniform float seam_gap=0.003;
uniform vec3 pitch_radii;
uniform vec3 ray_point;
uniform vec3 ray_direction;
#include "res://cavity_trace.gdshaderinc"
void fragment() {
    vec3 hit;
    vec3 traced=trace_cavity(ray_point,normalize(ray_direction),hit);
    ALBEDO=vec3(traced.x,traced.y/32.0,traced.z/2.0);
}
