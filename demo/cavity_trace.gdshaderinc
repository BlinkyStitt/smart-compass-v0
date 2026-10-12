float cylinder_hit(vec3 p, vec3 d, float radius) {
    float a = dot(d.xy, d.xy);
    float b = dot(p.xy, d.xy);
    float c = dot(p.xy, p.xy) - radius * radius;
    float det = b*b-a*c;
    if (a < 1e-10 || det < 0.0) { return 1e6; }
    float near_t = (-b-sqrt(det))/a;
    float far_t = (-b+sqrt(det))/a;
    return near_t > 1e-7 ? near_t : (far_t > 1e-7 ? far_t : 1e6);
}

// Returns remaining weight, reflection count and wall group.
vec3 trace_cavity(vec3 point, vec3 direction, out vec3 hit) {
    hit=point;
    float radius=length(point.xy);
    if (direction.z>=-0.00001 || radius<=halo_radius || radius>=inner_radius) { return vec3(0.0); }
    float weight=transmission;
    for (int reflection=0; reflection<=32; reflection++) {
        if (weight<0.001) { return vec3(0.0); }
        float plane=direction.z<0.0?rear_z:front_z;
        float plane_t=(plane-point.z)/direction.z;
        float halo_t=cylinder_hit(point,direction,halo_radius);
        float inner_t=cylinder_hit(point,direction,inner_radius);
        float wall_t=min(halo_t,inner_t);
        if (wall_t<plane_t) {
            hit=point+direction*wall_t;
            return vec3(weight,float(reflection),halo_t<inner_t?1.0:2.0);
        }
        point+=direction*plane_t;
        radius=length(point.xy);
        if (radius<=halo_radius || radius>=inner_radius ||
            (plane==rear_z && abs(point.x)<seam_gap*0.5 && point.y>pitch_radii.y-0.003)) { return vec3(0.0); }
        if (reflection==32) { return vec3(0.0); }
        weight*=direction.z<0.0?rear_reflectance:reflectance;
        direction.z=-direction.z;
    }
    return vec3(0.0);
}
