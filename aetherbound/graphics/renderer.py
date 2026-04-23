import OpenGL.GL as gl
import OpenGL.GL.shaders
import glm
import numpy as np

from graphics.shaders import STANDARD_VERTEX, STANDARD_FRAGMENT, INSTANCED_VERTEX
from graphics.models.glb_loader import GLBLoader
from graphics.primitives.sphere import create_sphere_mesh, load_texture

class MultiMeshRenderer:
    def __init__(self, model_path, initial_scale=1.0):
        self.scale = initial_scale
        self.meshes = GLBLoader.load(model_path)
        
        vs = gl.shaders.compileShader(STANDARD_VERTEX, gl.GL_VERTEX_SHADER)
        fs = gl.shaders.compileShader(STANDARD_FRAGMENT, gl.GL_FRAGMENT_SHADER)
        self.shader = gl.shaders.compileProgram(vs, fs)

        self.model_loc = gl.glGetUniformLocation(self.shader, "model")
        self.view_loc = gl.glGetUniformLocation(self.shader, "view")
        self.proj_loc = gl.glGetUniformLocation(self.shader, "projection")
        self.use_tex_loc = gl.glGetUniformLocation(self.shader, "use_texture")
        self.impact_pos_loc = gl.glGetUniformLocation(self.shader, "impact_pos")
        self.impact_force_loc = gl.glGetUniformLocation(self.shader, "impact_force")

    def draw(self, position, view_matrix, projection_matrix, yaw=0.0, pitch=0.0, impact_pos=[0,0,0], impact_force=0.0):
        gl.glUseProgram(self.shader)

        model = glm.mat4(1.0)
        model = glm.translate(model, glm.vec3(*position))
        
        # Camera orbit slaving (so ship looks where camera looks)
        model = glm.rotate(model, yaw, glm.vec3(0.0, 1.0, 0.0))
        # Important: Reverse pitch so ship nose points opposite to camera's downward tilt
        model = glm.rotate(model, -pitch, glm.vec3(1.0, 0.0, 0.0))
        
        # Align Orville's native X-forward axis to OpenGL's -Z forward axis
        model = glm.rotate(model, glm.radians(-90.0), glm.vec3(0.0, 1.0, 0.0))
        model = glm.rotate(model, glm.radians(-90.0), glm.vec3(1.0, 0.0, 0.0))
        model = glm.rotate(model, glm.radians(20.0), glm.vec3(0.0, 1.0, 0.0))
        
        model = glm.scale(model, glm.vec3(self.scale))

        gl.glUniformMatrix4fv(self.model_loc, 1, gl.GL_FALSE, glm.value_ptr(model))
        gl.glUniformMatrix4fv(self.view_loc, 1, gl.GL_FALSE, glm.value_ptr(view_matrix))
        gl.glUniformMatrix4fv(self.proj_loc, 1, gl.GL_FALSE, glm.value_ptr(projection_matrix))
        
        gl.glUniform3f(self.impact_pos_loc, *impact_pos)
        gl.glUniform1f(self.impact_force_loc, impact_force)

        for mesh in self.meshes:
            gl.glUniform1i(self.use_tex_loc, int(mesh.has_texture))
            if mesh.has_texture:
                gl.glActiveTexture(gl.GL_TEXTURE0)
                gl.glBindTexture(gl.GL_TEXTURE_2D, mesh.texture_id)

            gl.glBindVertexArray(mesh.vao)
            gl.glDrawElements(gl.GL_TRIANGLES, mesh.index_count, gl.GL_UNSIGNED_INT, None)
            
        gl.glBindVertexArray(0)

class SphereRenderer:
    def __init__(self, texture_path=None, radius=1.0, is_skybox=False):
        self.texture_id = load_texture(texture_path) if texture_path else None
        self.mesh = create_sphere_mesh(radius=radius, sectors=64, stacks=32, texture_id=self.texture_id)
        self.is_skybox = is_skybox

        vs = gl.shaders.compileShader(STANDARD_VERTEX, gl.GL_VERTEX_SHADER)
        fs = gl.shaders.compileShader(STANDARD_FRAGMENT, gl.GL_FRAGMENT_SHADER)
        self.shader = gl.shaders.compileProgram(vs, fs)

        self.model_loc = gl.glGetUniformLocation(self.shader, "model")
        self.view_loc = gl.glGetUniformLocation(self.shader, "view")
        self.proj_loc = gl.glGetUniformLocation(self.shader, "projection")
        self.use_tex_loc = gl.glGetUniformLocation(self.shader, "use_texture")
        self.impact_pos_loc = gl.glGetUniformLocation(self.shader, "impact_pos")
        self.impact_force_loc = gl.glGetUniformLocation(self.shader, "impact_force")

    def draw(self, position, view_matrix, projection_matrix, scale=1.0, rotation=0.0, impact_pos=[0,0,0], impact_force=0.0):
        if self.is_skybox:
            gl.glDepthMask(gl.GL_FALSE)
            view_mat_no_translate = glm.mat4(glm.mat3(view_matrix))
            view_to_use = view_mat_no_translate
        else:
            view_to_use = view_matrix

        gl.glUseProgram(self.shader)

        model = glm.mat4(1.0)
        model = glm.translate(model, glm.vec3(*position))
        
        model = glm.rotate(model, rotation, glm.vec3(0.0, 1.0, 0.0))
        model = glm.scale(model, glm.vec3(scale))

        gl.glUniformMatrix4fv(self.model_loc, 1, gl.GL_FALSE, glm.value_ptr(model))
        gl.glUniformMatrix4fv(self.view_loc, 1, gl.GL_FALSE, glm.value_ptr(view_to_use))
        gl.glUniformMatrix4fv(self.proj_loc, 1, gl.GL_FALSE, glm.value_ptr(projection_matrix))
        
        gl.glUniform3f(self.impact_pos_loc, *impact_pos)
        gl.glUniform1f(self.impact_force_loc, impact_force)
        
        gl.glUniform1i(self.use_tex_loc, int(self.mesh.has_texture))
        if self.mesh.has_texture:
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.mesh.texture_id)

        gl.glBindVertexArray(self.mesh.vao)
        gl.glDrawElements(gl.GL_TRIANGLES, self.mesh.index_count, gl.GL_UNSIGNED_INT, None)
        gl.glBindVertexArray(0)
        
        if self.is_skybox:
            gl.glDepthMask(gl.GL_TRUE)

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

    def draw_instanced(self, view_matrix, projection_matrix, offsets_scales_array):
        count = len(offsets_scales_array)
        if count == 0:
            return
            
        gl.glUseProgram(self.shader)
        gl.glUniformMatrix4fv(self.view_loc, 1, gl.GL_FALSE, glm.value_ptr(view_matrix))
        gl.glUniformMatrix4fv(self.proj_loc, 1, gl.GL_FALSE, glm.value_ptr(projection_matrix))
        
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
