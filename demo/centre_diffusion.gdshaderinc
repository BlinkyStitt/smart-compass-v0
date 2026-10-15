// Qualitative local diffusion, not measured scattering or photometry.
float centre_profile(vec2 sample_delta, float scatter_amount) {
    float spread=mix(0.0007,0.004,scatter_amount);
    return exp(-dot(sample_delta,sample_delta)/(spread*spread));
}
float black_sheet_exit(float coat_t, float sheet_t) {
    return coat_t*sheet_t;
}
float black_sheet_reflection(float coat_r, float sheet_t, float skin_r) {
    return skin_r+coat_r*sheet_t*sheet_t;
}
