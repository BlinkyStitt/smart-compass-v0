// Qualitative local diffusion, not measured scattering or photometry.
float centre_profile(vec2 sample_delta, float scatter_amount) {
    float spread=mix(0.0007,0.004,scatter_amount);
    return exp(-dot(sample_delta,sample_delta)/(spread*spread));
}
