// Qualitative cell diffusion, not measured scattering or photometry.
// The original stencil and flat aperture geometry define each cell boundary.
float centre_profile(vec2 sample_delta, float scatter_amount) {
    float radius=length(sample_delta);
    float direct=exp(-dot(sample_delta,sample_delta)/(0.0007*0.0007));
    float cell_fill=1.0-smoothstep(0.0075,0.008,radius);
    return mix(direct,cell_fill,smoothstep(0.0,0.65,scatter_amount));
}
