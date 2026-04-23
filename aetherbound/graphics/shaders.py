STANDARD_VERTEX = """
#version 330 core
layout(location = 0) in vec3 in_position;
layout(location = 1) in vec3 in_normal;
layout(location = 2) in vec2 in_uv;

out vec3 frag_normal;
out vec2 frag_uv;
out vec3 world_pos;
out vec3 local_pos;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

void main() {
    world_pos = vec3(model * vec4(in_position, 1.0));
    local_pos = in_position;
    gl_Position = projection * view * vec4(world_pos, 1.0);
    
    // Pass transformed normal and uv
    frag_normal = mat3(transpose(inverse(model))) * in_normal;
    frag_uv = in_uv;
}
"""

STANDARD_FRAGMENT = """
#version 330 core
in vec3 frag_normal;
in vec2 frag_uv;
in vec3 world_pos;
in vec3 local_pos;

out vec4 out_color;

uniform sampler2D texture_sampler;
uniform bool use_texture;
uniform vec3 base_color;

uniform vec3 impact_pos[8];
uniform float impact_force[8];
uniform int num_impacts;

uniform float crater_radius_mult;
uniform float crater_perturbation;
uniform float crater_darken_factor;

uniform vec3 light_pos[8];
uniform vec3 light_color[8];
uniform float light_intensity[8];
uniform int num_lights;
uniform float self_luminosity;
uniform vec3 camera_view_pos;

float hash(vec3 p) {
    p = fract(p * 0.3183099 + 0.1);
    p *= 17.0;
    return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
}

float noise(vec3 x) {
    vec3 i = floor(x);
    vec3 f = fract(x);
    f = f*f*(3.0-2.0*f);
    return mix(mix(mix( hash(i+vec3(0,0,0)), hash(i+vec3(1,0,0)),f.x),
                   mix( hash(i+vec3(0,1,0)), hash(i+vec3(1,1,0)),f.x),f.y),
               mix(mix( hash(i+vec3(0,0,1)), hash(i+vec3(1,0,1)),f.x),
                   mix( hash(i+vec3(0,1,1)), hash(i+vec3(1,1,1)),f.x),f.y),f.z);
}

void main() {
    vec3 base_tex;
    if (use_texture) {
        vec4 sampled = texture(texture_sampler, frag_uv);
        base_tex = sampled.rgb; 
    } else {
        base_tex = base_color;
    }

    vec3 normal = normalize(frag_normal);
    
    // Multi-Crater via Normal Perturbation (Local Space)
    for (int i = 0; i < num_impacts; i++) {
        float dist_to_impact = distance(local_pos, impact_pos[i]);
        float crater_radius = impact_force[i] * crater_radius_mult; 
        
        if (dist_to_impact < crater_radius && impact_force[i] > 0.0) {
            float normalized_dist = dist_to_impact / crater_radius;
            vec3 to_impact = normalize(impact_pos[i] - local_pos);
            float noise_val = noise(local_pos * 2.0);
            
            // Dynamic intensity based on config
            float intensity = pow(1.0 - normalized_dist, 2.0) * crater_perturbation;
            normal = normalize(normal + to_impact * intensity);
            
            // Darken the crater and perturb normals
            float darken = mix(crater_darken_factor * 0.5, 1.0, smoothstep(0.0, 1.0, normalized_dist));
            base_tex *= (darken + noise_val * 0.1);
        }
    }

    vec3 view_dir = normalize(camera_view_pos - world_pos);
    vec3 total_lighting = vec3(0.03); // Reset to requested ambient level

    for (int i = 0; i < num_lights; i++) {
        vec3 to_light = light_pos[i] - world_pos;
        float dist_l = length(to_light);
        vec3 light_dir = normalize(to_light);
        
        // Wrap Lighting (Half-Lambert) for softer terminator
        float wrap = max(dot(normal, light_dir), 0.0) * 0.5 + 0.5;
        float diff = pow(wrap, 2.0);
        
        float attenuation = 1.0 / (1.0 + 0.005 * dist_l + 0.0001 * dist_l * dist_l);
        total_lighting += light_color[i] * light_intensity[i] * diff * attenuation;
    }

    // Rim Lighting (Fresnel) - Reduced intensity
    float rim = pow(1.0 - max(dot(view_dir, normal), 0.0), 5.0);
    total_lighting += vec3(rim * 0.1);

    // Combine lighting and emissive - Lowered emissive boost
    vec3 color = base_tex * total_lighting + base_tex * (self_luminosity * 1.0);

    // Reinhard Tone Mapping
    color = color / (color + vec3(1.0));

    // Gamma Correction
    color = pow(color, vec3(1.0/2.2));

    float alpha = use_texture ? texture(texture_sampler, frag_uv).a : 1.0;
    out_color = vec4(color, alpha);
}
"""

INSTANCED_VERTEX = """
#version 330 core
layout(location = 0) in vec3 in_position;
layout(location = 1) in vec3 in_normal;
layout(location = 2) in vec2 in_uv;
layout(location = 3) in vec3 instance_offset;
layout(location = 4) in float instance_scale;

out vec3 frag_normal;
out vec2 frag_uv;
out vec3 world_pos;
out vec3 local_pos;

uniform mat4 view;
uniform mat4 projection;

void main() {
    world_pos = (in_position * instance_scale) + instance_offset;
    local_pos = in_position;
    gl_Position = projection * view * vec4(world_pos, 1.0);
    
    frag_normal = in_normal; 
    frag_uv = in_uv;
}
"""

DUST_VERTEX = """
#version 330 core
layout(location = 0) in vec3 in_position;

uniform mat4 view;
uniform mat4 projection;
uniform vec3 camera_pos; // the real world camera position

out vec3 frag_color;

void main() {
    vec3 wrapped_pos = mod(in_position - camera_pos + 100.0, 200.0) - 100.0;
    
    float dist = length(wrapped_pos);
    float fade = smoothstep(100.0, 0.0, dist); 
    
    frag_color = vec3(1.0, 1.0, 1.0) * fade;
    gl_Position = projection * view * vec4(wrapped_pos, 1.0);
    gl_PointSize = 2.0;
}
"""

DUST_FRAGMENT = """
#version 330 core
in vec3 frag_color;
out vec4 out_color;

void main() {
    out_color = vec4(frag_color, 1.0);
}
"""

SCANNER_FRAGMENT = """
#version 330 core
in vec3 world_pos;
in vec3 frag_normal;
out vec4 out_color;

uniform vec3 center_pos;
uniform float current_radius;
uniform float wave_width;

void main() {
    float dist = distance(world_pos, center_pos);
    float diff = abs(dist - current_radius);
    
    if (diff < wave_width) {
        float edge_fade = 1.0 - (diff / wave_width);
        out_color = vec4(0.0, 1.0, 0.8, edge_fade * 0.4); 
    } else {
        discard;
    }
}
"""

EXPLOSION_FRAGMENT = """
#version 330 core
in vec3 world_pos;
in vec3 frag_normal;
out vec4 out_color;

uniform vec3 center_pos;
uniform float current_radius;
uniform float max_radius;
uniform float time;
uniform vec3 core_color_u;
uniform vec3 edge_color_u;

float hash(vec3 p) {
    p = fract(p * 0.3183099 + 0.1);
    p *= 17.0;
    return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
}

float noise(vec3 x) {
    vec3 i = floor(x);
    vec3 f = fract(x);
    f = f*f*(3.0-2.0*f);
    return mix(mix(mix( hash(i+vec3(0,0,0)), hash(i+vec3(1,0,0)),f.x),
                   mix( hash(i+vec3(0,1,0)), hash(i+vec3(1,1,0)),f.x),f.y),
               mix(mix( hash(i+vec3(0,0,1)), hash(i+vec3(1,0,1)),f.x),
                   mix( hash(i+vec3(0,1,1)), hash(i+vec3(1,1,1)),f.x),f.y),f.z);
}

void main() {
    vec3 dir = world_pos - center_pos;
    float dist = length(dir);
    
    // Normalize life for logic (1.0 at start, 0.0 at end)
    float life = clamp(1.0 - (current_radius / max_radius), 0.0, 1.0);
    
    // Boiling Chaos Jitter
    float chaos = noise(world_pos * 0.2 + time * 2.0);
    float radius_with_noise = current_radius * (0.8 + chaos * 0.4);
    
    // Soft Edge with Smoothstep
    float alpha_edge = 1.0 - smoothstep(radius_with_noise * 0.7, radius_with_noise, dist);
    
    if (dist < radius_with_noise) {
        float n = noise(world_pos * 0.5 - time * 3.0);
        
        float t = dist / radius_with_noise;
        vec3 color = mix(core_color_u, edge_color_u, t * (1.2 - n * 0.4));
        
        // Boost glow and apply life-based fade
        float alpha = alpha_edge * life * (0.6 + n * 0.4);
        vec3 final_color = color * (2.0 + n * 1.5);
        
        // Tone Mapping
        final_color = final_color / (final_color + vec3(1.0));
        
        out_color = vec4(final_color, alpha);
    } else {
        discard;
    }
}
"""
