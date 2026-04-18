import OpenGL.GL as gl
import OpenGL.GL.shaders
import glm
import numpy as np
import trimesh
from PIL import Image
from graphics.shapes import generate_uv_sphere

# --- SHADERS ---

STANDARD_VERTEX = """
#version 330 core
layout(location = 0) in vec3 in_position;
layout(location = 1) in vec3 in_normal;
layout(location = 2) in vec2 in_uv;

out vec3 frag_normal;
out vec2 frag_uv;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

void main() {
    gl_Position = projection * view * model * vec4(in_position, 1.0);
    frag_normal = mat3(transpose(inverse(model))) * in_normal;
    frag_uv = in_uv;
}
"""

STANDARD_FRAGMENT = """
#version 330 core
in vec3 frag_normal;
in vec2 frag_uv;
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

uniform mat4 view;
uniform mat4 projection;

void main() {
    // Local scale -> World Space Translation
    vec3 world_pos = (in_position * instance_scale) + instance_offset;
    gl_Position = projection * view * vec4(world_pos, 1.0);
    
    // Simplification: Asteroids don't rotate independently yet so normal is static
    frag_normal = in_normal; 
    frag_uv = in_uv;
}
"""


# --- SHARED UTILS ---

def load_texture(image_path):
    try:
        img = Image.open(image_path).convert("RGBA").transpose(Image.FLIP_TOP_BOTTOM)
        img_data = np.array(list(img.getdata()), np.uint8)
        
        texture_id = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, texture_id)
        
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_REPEAT)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_REPEAT)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, img.width, img.height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, img_data)
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        return texture_id
    except Exception as e:
        print(f"Failed to load external texture {image_path}: {e}")
        return None

def build_interleaved_vbo(vertices, normals, uvs, indices):
    vertex_data = np.hstack([vertices.reshape(-1, 3), normals.reshape(-1, 3), uvs.reshape(-1, 2)]).flatten()
    
    vao = gl.glGenVertexArrays(1)
    vbo = gl.glGenBuffers(1)
    ebo = gl.glGenBuffers(1)

    gl.glBindVertexArray(vao)

    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
    gl.glBufferData(gl.GL_ARRAY_BUFFER, vertex_data.nbytes, vertex_data, gl.GL_STATIC_DRAW)

    gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, ebo)
    gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices.flatten(), gl.GL_STATIC_DRAW)

    stride = 8 * 4 
    gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, gl.ctypes.c_void_p(0))
    gl.glEnableVertexAttribArray(0)
    
    gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, gl.ctypes.c_void_p(12))
    gl.glEnableVertexAttribArray(1)
    
    gl.glVertexAttribPointer(2, 2, gl.GL_FLOAT, gl.GL_FALSE, stride, gl.ctypes.c_void_p(24))
    gl.glEnableVertexAttribArray(2)
    
    gl.glBindVertexArray(0)
    return vao, len(indices.flatten())


# --- RENDERERS ---

class GLBRenderer:
    """Renderer for the Spaceship GLB."""
    def __init__(self, model_path, initial_scale=1.0):
        self.scale = initial_scale
        self.texture_id = None
        self.has_texture = False
        
        vs = gl.shaders.compileShader(STANDARD_VERTEX, gl.GL_VERTEX_SHADER)
        fs = gl.shaders.compileShader(STANDARD_FRAGMENT, gl.GL_FRAGMENT_SHADER)
        self.shader = gl.shaders.compileProgram(vs, fs)

        self.model_loc = gl.glGetUniformLocation(self.shader, "model")
        self.view_loc = gl.glGetUniformLocation(self.shader, "view")
        self.proj_loc = gl.glGetUniformLocation(self.shader, "projection")
        self.use_tex_loc = gl.glGetUniformLocation(self.shader, "use_texture")

        # Parse GLB
        mesh = trimesh.load(model_path, force='mesh')
        if isinstance(mesh, trimesh.Scene):
            mesh = trimesh.util.concatenate([geom for geom in mesh.geometry.values()])
            
        vertices = mesh.vertices.astype(np.float32)
        if not hasattr(mesh, 'vertex_normals') or mesh.vertex_normals is None or len(mesh.vertex_normals) == 0:
            mesh.fix_normals()
        normals = mesh.vertex_normals.astype(np.float32)
        indices = mesh.faces.astype(np.uint32)
        
        uvs = getattr(mesh.visual, 'uv', None)
        if uvs is None or len(uvs) == 0:
            uvs = np.zeros((len(vertices), 2), dtype=np.float32)
        else:
            uvs = np.array(uvs, dtype=np.float32)
            
        if hasattr(mesh.visual, 'material') and hasattr(mesh.visual.material, 'image') and mesh.visual.material.image:
            img = mesh.visual.material.image.convert("RGBA").transpose(Image.FLIP_TOP_BOTTOM)
            img_data = np.array(list(img.getdata()), np.uint8)
            self.texture_id = gl.glGenTextures(1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture_id)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, img.width, img.height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, img_data)
            gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
            self.has_texture = True

        self.vao, self.index_count = build_interleaved_vbo(vertices, normals, uvs, indices)

    def draw(self, position, view_matrix, projection_matrix, yaw=0.0, pitch=0.0):
        gl.glUseProgram(self.shader)

        model = glm.mat4(1.0)
        model = glm.translate(model, glm.vec3(*position))
        
        model = glm.rotate(model, yaw, glm.vec3(0.0, 1.0, 0.0))
        model = glm.rotate(model, pitch, glm.vec3(1.0, 0.0, 0.0))
        model = glm.rotate(model, glm.radians(-90.0), glm.vec3(0.0, 1.0, 0.0))
        model = glm.scale(model, glm.vec3(self.scale))

        gl.glUniformMatrix4fv(self.model_loc, 1, gl.GL_FALSE, glm.value_ptr(model))
        gl.glUniformMatrix4fv(self.view_loc, 1, gl.GL_FALSE, glm.value_ptr(view_matrix))
        gl.glUniformMatrix4fv(self.proj_loc, 1, gl.GL_FALSE, glm.value_ptr(projection_matrix))
        
        gl.glUniform1i(self.use_tex_loc, int(self.has_texture))
        if self.has_texture:
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture_id)

        gl.glBindVertexArray(self.vao)
        gl.glDrawElements(gl.GL_TRIANGLES, self.index_count, gl.GL_UNSIGNED_INT, None)
        gl.glBindVertexArray(0)


class SphereRenderer:
    """Renders single procedurally generated spheres (Planets, Sun, Skybox)."""
    def __init__(self, texture_path=None, radius=1.0, is_skybox=False):
        self.texture_id = load_texture(texture_path) if texture_path else None
        self.has_texture = self.texture_id is not None
        self.is_skybox = is_skybox

        vs = gl.shaders.compileShader(STANDARD_VERTEX, gl.GL_VERTEX_SHADER)
        fs = gl.shaders.compileShader(STANDARD_FRAGMENT, gl.GL_FRAGMENT_SHADER)
        self.shader = gl.shaders.compileProgram(vs, fs)

        self.model_loc = gl.glGetUniformLocation(self.shader, "model")
        self.view_loc = gl.glGetUniformLocation(self.shader, "view")
        self.proj_loc = gl.glGetUniformLocation(self.shader, "projection")
        self.use_tex_loc = gl.glGetUniformLocation(self.shader, "use_texture")

        v, n, u, i = generate_uv_sphere(radius=radius, sectors=64, stacks=32)
        self.vao, self.index_count = build_interleaved_vbo(v, n, u, i)

    def draw(self, position, view_matrix, projection_matrix, scale=1.0, rotation=0.0):
        if self.is_skybox:
            gl.glDepthMask(gl.GL_FALSE) # Don't write to depth buffer
            # Ignore camera translation for skybox view
            view_mat_no_translate = glm.mat4(glm.mat3(view_matrix))
            view_to_use = view_mat_no_translate
        else:
            view_to_use = view_matrix

        gl.glUseProgram(self.shader)

        model = glm.mat4(1.0)
        model = glm.translate(model, glm.vec3(*position))
        
        # Simple continuous rotation based on time proxy
        model = glm.rotate(model, rotation, glm.vec3(0.0, 1.0, 0.0))
        model = glm.scale(model, glm.vec3(scale))

        gl.glUniformMatrix4fv(self.model_loc, 1, gl.GL_FALSE, glm.value_ptr(model))
        gl.glUniformMatrix4fv(self.view_loc, 1, gl.GL_FALSE, glm.value_ptr(view_to_use))
        gl.glUniformMatrix4fv(self.proj_loc, 1, gl.GL_FALSE, glm.value_ptr(projection_matrix))
        
        gl.glUniform1i(self.use_tex_loc, int(self.has_texture))
        if self.has_texture:
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture_id)

        gl.glBindVertexArray(self.vao)
        gl.glDrawElements(gl.GL_TRIANGLES, self.index_count, gl.GL_UNSIGNED_INT, None)
        gl.glBindVertexArray(0)
        
        if self.is_skybox:
            gl.glDepthMask(gl.GL_TRUE)


class InstancedSphereRenderer:
    """Draws massive chunks of spheres (Asteroids) via GPU Instancing arrays."""
    def __init__(self, texture_path=None, base_radius=1.0):
        self.texture_id = load_texture(texture_path) if texture_path else None
        self.has_texture = self.texture_id is not None

        vs = gl.shaders.compileShader(INSTANCED_VERTEX, gl.GL_VERTEX_SHADER)
        fs = gl.shaders.compileShader(STANDARD_FRAGMENT, gl.GL_FRAGMENT_SHADER)
        self.shader = gl.shaders.compileProgram(vs, fs)

        self.view_loc = gl.glGetUniformLocation(self.shader, "view")
        self.proj_loc = gl.glGetUniformLocation(self.shader, "projection")
        self.use_tex_loc = gl.glGetUniformLocation(self.shader, "use_texture")

        # Procedural base mesh
        v, n, u, i = generate_uv_sphere(radius=base_radius, sectors=16, stacks=8) # Lower geom for instancing
        self.vao, self.index_count = build_interleaved_vbo(v, n, u, i)
        
        # Instance Buffers
        self.instance_vbo = gl.glGenBuffers(1)

    def draw_instanced(self, view_matrix, projection_matrix, offsets_scales_array):
        """
        offsets_scales_array: Nx4 numpy float32 array where columns are [x, y, z, scale].
        """
        count = len(offsets_scales_array)
        if count == 0:
            return
            
        gl.glUseProgram(self.shader)
        gl.glUniformMatrix4fv(self.view_loc, 1, gl.GL_FALSE, glm.value_ptr(view_matrix))
        gl.glUniformMatrix4fv(self.proj_loc, 1, gl.GL_FALSE, glm.value_ptr(projection_matrix))
        
        gl.glUniform1i(self.use_tex_loc, int(self.has_texture))
        if self.has_texture:
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture_id)

        gl.glBindVertexArray(self.vao)
        
        # Bind dynamic instance data
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.instance_vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, offsets_scales_array.nbytes, offsets_scales_array, gl.GL_DYNAMIC_DRAW)
        
        stride = 4 * 4 # 4 floats (x, y, z, scale)
        
        # Location 3: vec3 instance_offset
        gl.glVertexAttribPointer(3, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, gl.ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(3)
        gl.glVertexAttribDivisor(3, 1) # Advance per instance
        
        # Location 4: float instance_scale
        gl.glVertexAttribPointer(4, 1, gl.GL_FLOAT, gl.GL_FALSE, stride, gl.ctypes.c_void_p(12))
        gl.glEnableVertexAttribArray(4)
        gl.glVertexAttribDivisor(4, 1)

        # Draw N instances!
        gl.glDrawElementsInstanced(gl.GL_TRIANGLES, self.index_count, gl.GL_UNSIGNED_INT, None, count)
        
        gl.glBindVertexArray(0)
