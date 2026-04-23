import OpenGL.GL as gl
import OpenGL.GL.shaders
import glm
import numpy as np
from graphics.shaders import INSTANCED_VERTEX, STANDARD_FRAGMENT
from graphics.models.glb_loader import GLBLoader
from graphics.primitives.sphere import create_sphere_mesh, load_texture

class InstancedRenderer:
    def __init__(self, model_path_or_texture=None, is_glb=False, base_radius=1.0):
        if is_glb:
            self.mesh = GLBLoader.load(model_path_or_texture)[0]
        else:
            self.texture_id = load_texture(model_path_or_texture) if model_path_or_texture else None
            self.mesh = create_sphere_mesh(radius=base_radius, sectors=16, stacks=8, texture_id=self.texture_id)

        vs = gl.shaders.compileShader(INSTANCED_VERTEX, gl.GL_VERTEX_SHADER)
        fs = gl.shaders.compileShader(STANDARD_FRAGMENT, gl.GL_FRAGMENT_SHADER)
        self.shader = gl.shaders.compileProgram(vs, fs)

        self.view_loc = gl.glGetUniformLocation(self.shader, "view")
        self.proj_loc = gl.glGetUniformLocation(self.shader, "projection")
        self.use_tex_loc = gl.glGetUniformLocation(self.shader, "use_texture")
        
        self.instance_vbo = gl.glGenBuffers(1)

        self.light_pos_loc = [gl.glGetUniformLocation(self.shader, f"light_pos[{i}]") for i in range(4)]
        self.light_color_loc = [gl.glGetUniformLocation(self.shader, f"light_color[{i}]") for i in range(4)]
        self.light_intensity_loc = [gl.glGetUniformLocation(self.shader, f"light_intensity[{i}]") for i in range(4)]
        self.num_lights_loc = gl.glGetUniformLocation(self.shader, "num_lights")
        
        self.impact_pos_loc = gl.glGetUniformLocation(self.shader, "impact_pos")
        self.impact_force_loc = gl.glGetUniformLocation(self.shader, "impact_force")
        self.crater_radius_mult_loc = gl.glGetUniformLocation(self.shader, "crater_radius_mult")
        self.crater_perturbation_loc = gl.glGetUniformLocation(self.shader, "crater_perturbation")
        self.crater_darken_loc = gl.glGetUniformLocation(self.shader, "crater_darken_factor")
        self.self_lum_loc = gl.glGetUniformLocation(self.shader, "self_luminosity")
        self.base_color_loc = gl.glGetUniformLocation(self.shader, "base_color")
        self.cam_pos_loc = gl.glGetUniformLocation(self.shader, "camera_view_pos")

    def set_lights(self, lights_data):
        gl.glUseProgram(self.shader)
        num = min(len(lights_data), 4)
        gl.glUniform1i(self.num_lights_loc, num)
        for i in range(num):
            gl.glUniform3f(self.light_pos_loc[i], *lights_data[i]['pos'])
            gl.glUniform3f(self.light_color_loc[i], *lights_data[i]['color'])
            gl.glUniform1f(self.light_intensity_loc[i], lights_data[i]['intensity'])

    def draw_instanced(self, view_matrix, projection_matrix, offsets_scales_array, self_luminosity=0.0, camera_pos=[0,0,0], config=None):
        count = len(offsets_scales_array)
        if count == 0:
            return
            
        gl.glUseProgram(self.shader)
        gl.glUniform3f(self.cam_pos_loc, *camera_pos)
        gl.glUniformMatrix4fv(self.view_loc, 1, gl.GL_FALSE, glm.value_ptr(view_matrix))
        gl.glUniformMatrix4fv(self.proj_loc, 1, gl.GL_FALSE, glm.value_ptr(projection_matrix))
        
        gl.glUniform1f(self.self_lum_loc, self_luminosity)
        gl.glUniform3f(self.impact_pos_loc, 0, 0, 0)
        gl.glUniform1f(self.impact_force_loc, 0.0)
        gl.glUniform3f(self.base_color_loc, 0.5, 0.5, 0.5)
        
        if config and "craters" in config:
            gl.glUniform1f(self.crater_radius_mult_loc, config["craters"]["radius_mult"])
            gl.glUniform1f(self.crater_perturbation_loc, config["craters"]["perturbation"])
            gl.glUniform1f(self.crater_darken_loc, config["craters"]["darken_factor"])
        else:
            gl.glUniform1f(self.crater_radius_mult_loc, 2.5)
            gl.glUniform1f(self.crater_perturbation_loc, 0.7)
            gl.glUniform1f(self.crater_darken_loc, 0.4)
        
        gl.glUniform1i(self.use_tex_loc, int(self.mesh.has_texture))
        if self.mesh.has_texture:
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.mesh.texture_id)

        gl.glBindVertexArray(self.mesh.vao)
        
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.instance_vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, offsets_scales_array.nbytes, offsets_scales_array, gl.GL_DYNAMIC_DRAW)
        
        stride = 4 * 4 
        
        gl.glVertexAttribPointer(3, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, gl.ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(3)
        gl.glVertexAttribDivisor(3, 1)
        
        gl.glVertexAttribPointer(4, 1, gl.GL_FLOAT, gl.GL_FALSE, stride, gl.ctypes.c_void_p(12))
        gl.glEnableVertexAttribArray(4)
        gl.glVertexAttribDivisor(4, 1)

        gl.glDrawElementsInstanced(gl.GL_TRIANGLES, self.mesh.index_count, gl.GL_UNSIGNED_INT, None, count)
        gl.glBindVertexArray(0)
