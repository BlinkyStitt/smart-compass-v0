// One continuous surface model for all direct and reflected ring light.
// The Gaussian blend and small LED peaks are unmeasured diffuser assumptions.
vec3 diffused_ring_light(vec3 p, int ring_group, int pixel_count, float ring_radius, float source_z) {
    float angle = mod(atan(p.x,p.y)+6.28318530718,6.28318530718);
    float coord = (angle*ring_radius-seam_gap*0.5)/pitch-0.5;
    if (coord < -0.5 || coord > float(pixel_count)-0.5) { return vec3(0.0); }
    int index = int(clamp(floor(coord+0.5),0.0,float(pixel_count-1)));
    vec3 light = vec3(0.0);
    float total = 0.0;
    for (int j=-2;j<=2;j++) {
        int k=index+j;
        if (k>=0 && k<pixel_count) {
            float w=exp(-pow((coord-float(k))/mix(0.22,1.6,diffusion),2.0));
            light+=texelFetch(colours,ivec2(k,ring_group),0).rgb*w;
            total+=w;
        }
    }
    // A smooth five-percent peak at the default diffusion replaces the
    // rectangular package mask. Neighbouring LEDs still blend their colours.
    float peak=0.5+0.5*cos(6.28318530718*coord);
    float hotspot=mix(1.0-0.15*(1.0-diffusion),1.0,peak);
    float vertical=exp(-pow(max(0.0,abs(p.z-source_z)-0.0025)/mix(0.00015,0.008,diffusion),2.0));
    return light/max(total,0.0001)*hotspot*vertical;
}
