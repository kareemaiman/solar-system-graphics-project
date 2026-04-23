STANDARD_VERTEX = """
#version 330 core
layout(location = 0) in vec3 in_position;
layout(location = 1) in vec3 in_normal;
layout(location = 2) in vec2 in_uv;

out vec3 frag_normal;
out vec2 frag_uv;
out vec3 world_pos;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

// Crater uniforms
uniform vec3 impact_pos;
uniform float impact_force;

void main() {
    world_pos = vec3(model * vec4(in_position, 1.0));
    
    // Procedural Crater Deformation
    float dist = distance(world_pos, impact_pos);
    float crater_radius = impact_force * 2.0; 
    
    vec3 perturbed_pos = in_position;
    vec3 updated_normal = in_normal;
    
    if (dist < crater_radius && impact_force > 0.0) {
        // Simple dent: push vertices inwards along the normal
        float depth = (crater_radius - dist) * 0.5;
        perturbed_pos -= in_normal * depth;
        // In a more advanced shader we'd recompute normals based on heightmap derivative, 
        // but simple normal tilt towards impact works for a dent:
        vec3 to_impact = normalize(impact_pos - world_pos);
        updated_normal = normalize(in_normal - to_impact * 0.5);
    }
    
    gl_Position = projection * view * model * vec4(perturbed_pos, 1.0);
    frag_normal = mat3(transpose(inverse(model))) * updated_normal;
    frag_uv = in_uv;
}
"""

STANDARD_FRAGMENT = """
#version 330 core
in vec3 frag_normal;
in vec2 frag_uv;
in vec3 world_pos;

out vec4 out_color;

uniform sampler2D texture_sampler;
uniform bool use_texture;

void main() {
    if (use_texture) {
        out_color = texture(texture_sampler, frag_uv);
    } else {
        vec3 n = normalize(frag_normal);
        out_color = vec4(n * 0.5 + 0.5, 1.0);
    }
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

uniform mat4 view;
uniform mat4 projection;

void main() {
    world_pos = (in_position * instance_scale) + instance_offset;
    gl_Position = projection * view * vec4(world_pos, 1.0);
    
    frag_normal = in_normal; 
    frag_uv = in_uv;
}
"""
