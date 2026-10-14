shader_type spatial;
render_mode cull_disabled;
uniform sampler2D colours : filter_nearest, repeat_disable;
uniform sampler2D charges : filter_nearest, repeat_disable;
uniform float wall_mm = 1.0;
uniform int group = 3;
uniform int count = 90;
uniform float pitch_radius = 0.11984367;
uniform float seam_gap = 0.003;
uniform float pitch = 0.00833333;
uniform float led_z = 0.0201;
uniform float brightness = 2.0;
uniform float transmission = 0.4;
uniform float diffusion = 0.65;
uniform vec3 assembly_offset = vec3(0.0);
varying vec3 pos;
void vertex() { pos = (MODEL_MATRIX * vec4(VERTEX,1.0)).xyz - assembly_offset; }
#include "res://ring_diffusion.gdshaderinc"
void fragment() {
    // Powder-filled PETG: pale, matte and slightly granular. Fade print layers
    // when the 0.2 mm pitch is smaller than a pixel to avoid moving moire.
    float layer_coord=pos.z/0.0002;
    float resolved=1.0-smoothstep(0.15,0.7,fwidth(layer_coord));
    float layer=cos(6.28318530718*layer_coord)*resolved;
    float grain=sin(pos.x*37000.0)*sin(pos.y*41000.0)*sin(pos.z*29000.0);
    float grain_fade=1.0-smoothstep(0.4,1.0,length(fwidth(pos*6500.0)));
    ALBEDO=vec3(0.80,0.84,0.66)*(1.0+0.018*layer+0.012*grain*grain_fade);
    ROUGHNESS=0.78+0.035*layer;
    EMISSION=glow_ring_light(pos,group,count,pitch_radius,led_z,wall_mm,brightness,transmission);
}
