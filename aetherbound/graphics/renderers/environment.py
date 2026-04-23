import OpenGL.GL as gl
import OpenGL.GL.shaders
import glm
import numpy as np
from graphics.shaders import DUST_VERTEX, DUST_FRAGMENT
from graphics.primitives.sphere import load_texture

class SpaceDustRenderer:
    def __init__(self, num_particles=1000, spread=200.0):
        self.num_particles = num_particles
        np.random.seed(42)
        positions = (np.random.rand(num_particles, 3) * spread - (spread / 2.0)).astype(np.float32)
        
        self.vao = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(self.vao)
        
        self.vbo = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, positions.nbytes, positions, gl.GL_STATIC_DRAW)
        
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 12, gl.ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(0)
        
        gl.glBindVertexArray(0)
        
        vs = gl.shaders.compileShader(DUST_VERTEX, gl.GL_VERTEX_SHADER)
        fs = gl.shaders.compileShader(DUST_FRAGMENT, gl.GL_FRAGMENT_SHADER)
        self.shader = gl.shaders.compileProgram(vs, fs)
        
        self.view_loc = gl.glGetUniformLocation(self.shader, "view")
        self.proj_loc = gl.glGetUniformLocation(self.shader, "projection")
        self.cam_pos_loc = gl.glGetUniformLocation(self.shader, "camera_pos")

    def draw(self, view_matrix, projection_matrix, camera_pos_f64):
        gl.glUseProgram(self.shader)
        gl.glUniformMatrix4fv(self.view_loc, 1, gl.GL_FALSE, glm.value_ptr(view_matrix))
        gl.glUniformMatrix4fv(self.proj_loc, 1, gl.GL_FALSE, glm.value_ptr(projection_matrix))
        gl.glUniform3f(self.cam_pos_loc, camera_pos_f64[0], camera_pos_f64[1], camera_pos_f64[2])
        
        gl.glEnable(gl.GL_PROGRAM_POINT_SIZE)
        gl.glBindVertexArray(self.vao)
        gl.glDrawArrays(gl.GL_POINTS, 0, self.num_particles)
        gl.glBindVertexArray(0)
        gl.glDisable(gl.GL_PROGRAM_POINT_SIZE)

class BackgroundRenderer:
    def __init__(self, texture_path):
        self.texture_id = load_texture(texture_path)
        vertices = np.array([
            -1, -1, 0,  0, 0,
             1, -1, 0,  1, 0,
             1,  1, 0,  1, 1,
            -1,  1, 0,  0, 1
        ], dtype=np.float32)
        indices = np.array([0, 1, 2, 2, 3, 0], dtype=np.uint32)
        
        self.vao = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(self.vao)
        self.vbo = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW)
        self.ebo = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, gl.GL_STATIC_DRAW)
        
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 20, gl.ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(2, 2, gl.GL_FLOAT, gl.GL_FALSE, 20, gl.ctypes.c_void_p(12))
        gl.glEnableVertexAttribArray(2)
        gl.glBindVertexArray(0)
        
        vs_src = """
        #version 330 core
        layout(location = 0) in vec3 pos;
        layout(location = 2) in vec2 uv;
        out vec2 frag_uv;
        void main() {
            gl_Position = vec4(pos, 1.0);
            frag_uv = uv;
        }
        """
        fs_src = """
        #version 330 core
        in vec2 frag_uv;
        out vec4 color;
        uniform sampler2D tex;
        void main() {
            color = texture(tex, frag_uv);
        }
        """
        vs = gl.shaders.compileShader(vs_src, gl.GL_VERTEX_SHADER)
        fs = gl.shaders.compileShader(fs_src, gl.GL_FRAGMENT_SHADER)
        self.shader = gl.shaders.compileProgram(vs, fs)

    def draw(self):
        gl.glDisable(gl.GL_DEPTH_TEST)
        gl.glUseProgram(self.shader)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture_id)
        gl.glBindVertexArray(self.vao)
        gl.glDrawElements(gl.GL_TRIANGLES, 6, gl.GL_UNSIGNED_INT, None)
        gl.glBindVertexArray(0)
        gl.glEnable(gl.GL_DEPTH_TEST)
