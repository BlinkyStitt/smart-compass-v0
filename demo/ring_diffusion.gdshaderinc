// Material coefficients come from the selected scene material option.
uniform vec3 ring_absorption = vec3(0.40,0.08,0.65);
uniform float ring_prompt_green = 0.06;
uniform float ring_stored_emission = 1.0;
// One continuous surface model for all direct and reflected ring light.
// The Gaussian blend and small LED peaks are unmeasured diffuser assumptions.
vec3 ring_field(sampler2D field, vec3 p, int ring_group, int pixel_count, float ring_radius) {
    float angle = mod(atan(p.x,p.y)+6.28318530718,6.28318530718);
    float coord = (angle*ring_radius-seam_gap*0.5)/pitch-0.5;
    int index = int(floor(coord+0.5));
    float period = 6.28318530718*ring_radius/pitch;
    vec3 light = vec3(0.0);
    float total = 0.0;
    for (int j=-2;j<=2;j++) {
        int raw=index+j;
        int k=(raw%pixel_count+pixel_count)%pixel_count;
        float location=float(k)+(raw<0?-period:raw>=pixel_count?period:0.0);
        float w=exp(-pow((coord-location)/mix(0.22,1.6,diffusion),2.0));
        light+=texelFetch(field,ivec2(k,ring_group),0).rgb*w;
        total+=w;
    }
    return light/max(total,0.0001);
}

vec3 diffused_ring_light(vec3 p, int ring_group, int pixel_count, float ring_radius, float source_z) {
    float angle = mod(atan(p.x,p.y)+6.28318530718,6.28318530718);
    float coord = (angle*ring_radius-seam_gap*0.5)/pitch-0.5;
    // A smooth five-percent peak at the default diffusion replaces the
    // rectangular package mask. Neighbouring LEDs still blend their colours.
    float peak=0.5+0.5*cos(6.28318530718*coord);
    float hotspot=mix(1.0-0.15*(1.0-diffusion),1.0,peak);
    // Keep a soft 5 mm LED band. An assumed 3 mm maximum axial scatter
    // scale leaves visible valleys between mirror copies at the real gap.
    // The previous 8 mm scale blended those copies into one broad wall.
    float vertical=exp(-pow(max(0.0,abs(p.z-source_z)-0.0025)/mix(0.00015,0.003,diffusion),2.0));
    return ring_field(colours,p,ring_group,pixel_count,ring_radius)*hotspot*vertical;
}

// The same material response supplies direct rings and every reflected copy.
// Absorption, fluorescence and stored emission are illustrative, not measured.
vec3 ring_light(vec3 p, int ring_group, int pixel_count, float ring_radius, float source_z, float thickness_mm, float led_brightness, float led_transmission) {
    vec3 incident = diffused_ring_light(p,ring_group,pixel_count,ring_radius,source_z);
    vec3 filtered = incident*exp(-ring_absorption*thickness_mm)*led_transmission;
    vec3 green = vec3(0.16,1.0,0.025);
    vec3 prompt = green*incident.b*ring_prompt_green;
    vec2 stored = ring_field(charges,p,ring_group,pixel_count,ring_radius).rg;
    return (filtered+prompt)*led_brightness+green*(0.18*stored.r+0.045*stored.g)*ring_stored_emission;
}
