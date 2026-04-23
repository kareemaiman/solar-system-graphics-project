import OpenGL.GL as gl
import OpenGL.GL.shaders
import glm
from graphics.shaders import STANDARD_VERTEX, STANDARD_FRAGMENT
from graphics.primitives.sphere import create_sphere_mesh, load_texture
from graphics.primitives.ring import create_ring_mesh

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
        self.impact_pos_loc = [gl.glGetUniformLocation(self.shader, f"impact_pos[{i}]") for i in range(8)]
        self.impact_force_loc = [gl.glGetUniformLocation(self.shader, f"impact_force[{i}]") for i in range(8)]
        self.num_impacts_loc = gl.glGetUniformLocation(self.shader, "num_impacts")
        self.crater_radius_mult_loc = gl.glGetUniformLocation(self.shader, "crater_radius_mult")
        self.crater_perturbation_loc = gl.glGetUniformLocation(self.shader, "crater_perturbation")
        self.crater_darken_loc = gl.glGetUniformLocation(self.shader, "crater_darken_factor")
        self.self_lum_loc = gl.glGetUniformLocation(self.shader, "self_luminosity")
        self.base_color_loc = gl.glGetUniformLocation(self.shader, "base_color")
        
        self.light_pos_loc = [gl.glGetUniformLocation(self.shader, f"light_pos[{i}]") for i in range(8)]
        self.light_color_loc = [gl.glGetUniformLocation(self.shader, f"light_color[{i}]") for i in range(8)]
        self.light_intensity_loc = [gl.glGetUniformLocation(self.shader, f"light_intensity[{i}]") for i in range(8)]
        self.num_lights_loc = gl.glGetUniformLocation(self.shader, "num_lights")
        self.cam_pos_loc = gl.glGetUniformLocation(self.shader, "camera_view_pos")

    def set_lights(self, lights_data):
        gl.glUseProgram(self.shader)
        num = min(len(lights_data), 4)
        gl.glUniform1i(self.num_lights_loc, num)
        for i in range(num):
            gl.glUniform3f(self.light_pos_loc[i], *lights_data[i]['pos'])
            gl.glUniform3f(self.light_color_loc[i], *lights_data[i]['color'])
            gl.glUniform1f(self.light_intensity_loc[i], lights_data[i]['intensity'])

    def draw(self, position, view_matrix, projection_matrix, scale=1.0, rotation=0.0, impacts=[], self_luminosity=0.0, camera_pos=[0,0,0], config=None):
        gl.glDisable(gl.GL_CULL_FACE)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        if self.is_skybox:
            gl.glDepthMask(gl.GL_FALSE)
            view_mat_no_translate = glm.mat4(glm.mat3(view_matrix))
            view_to_use = view_mat_no_translate
        else:
            view_to_use = view_matrix

        gl.glUseProgram(self.shader)
        gl.glUniform3f(self.cam_pos_loc, *camera_pos)
        
        if config and "craters" in config:
            gl.glUniform1f(self.crater_radius_mult_loc, config["craters"]["radius_mult"])
            gl.glUniform1f(self.crater_perturbation_loc, config["craters"]["perturbation"])
            gl.glUniform1f(self.crater_darken_loc, config["craters"]["darken_factor"])
        else:
            gl.glUniform1f(self.crater_radius_mult_loc, 2.5)
            gl.glUniform1f(self.crater_perturbation_loc, 0.7)
            gl.glUniform1f(self.crater_darken_loc, 0.4)

        model = glm.mat4(1.0)
        model = glm.translate(model, glm.vec3(*position))
        model = glm.rotate(model, rotation, glm.vec3(0.0, 1.0, 0.0))
        model = glm.scale(model, glm.vec3(scale))

        gl.glUniformMatrix4fv(self.model_loc, 1, gl.GL_FALSE, glm.value_ptr(model))
        gl.glUniformMatrix4fv(self.view_loc, 1, gl.GL_FALSE, glm.value_ptr(view_to_use))
        gl.glUniformMatrix4fv(self.proj_loc, 1, gl.GL_FALSE, glm.value_ptr(projection_matrix))
        
        num_c = min(len(impacts), 8)
        gl.glUniform1i(self.num_impacts_loc, num_c)
        for i in range(num_c):
            gl.glUniform3f(self.impact_pos_loc[i], *impacts[i][0])
            gl.glUniform1f(self.impact_force_loc[i], impacts[i][1])
            
        gl.glUniform1f(self.self_lum_loc, self_luminosity)
        gl.glUniform3f(self.base_color_loc, 1.0, 1.0, 1.0)
        
        gl.glUniform1i(self.use_tex_loc, int(self.mesh.has_texture))
        if self.mesh.has_texture:
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.mesh.texture_id)

        gl.glBindVertexArray(self.mesh.vao)
        gl.glDrawElements(gl.GL_TRIANGLES, self.mesh.index_count, gl.GL_UNSIGNED_INT, None)
        gl.glBindVertexArray(0)
        gl.glDisable(gl.GL_BLEND)
        
        if self.is_skybox:
            gl.glDepthMask(gl.GL_TRUE)
        gl.glEnable(gl.GL_CULL_FACE)

class RingRenderer:
    def __init__(self, texture_path, inner_radius=1.2, outer_radius=2.4):
        self.texture_id = load_texture(texture_path)
        self.mesh = create_ring_mesh(inner_radius, outer_radius, texture_id=self.texture_id)

        vs = gl.shaders.compileShader(STANDARD_VERTEX, gl.GL_VERTEX_SHADER)
        fs = gl.shaders.compileShader(STANDARD_FRAGMENT, gl.GL_FRAGMENT_SHADER)
        self.shader = gl.shaders.compileProgram(vs, fs)

        self.model_loc = gl.glGetUniformLocation(self.shader, "model")
        self.view_loc = gl.glGetUniformLocation(self.shader, "view")
        self.proj_loc = gl.glGetUniformLocation(self.shader, "projection")
        self.use_tex_loc = gl.glGetUniformLocation(self.shader, "use_texture")
        self.impact_pos_loc = gl.glGetUniformLocation(self.shader, "impact_pos")
        self.impact_force_loc = gl.glGetUniformLocation(self.shader, "impact_force")

        self.light_pos_loc = [gl.glGetUniformLocation(self.shader, f"light_pos[{i}]") for i in range(4)]
        self.light_color_loc = [gl.glGetUniformLocation(self.shader, f"light_color[{i}]") for i in range(4)]
        self.light_intensity_loc = [gl.glGetUniformLocation(self.shader, f"light_intensity[{i}]") for i in range(4)]
        self.num_lights_loc = gl.glGetUniformLocation(self.shader, "num_lights")
        self.self_lum_loc = gl.glGetUniformLocation(self.shader, "self_luminosity")
        self.cam_pos_loc = gl.glGetUniformLocation(self.shader, "camera_view_pos")

    def set_lights(self, lights_data):
        gl.glUseProgram(self.shader)
        num = min(len(lights_data), 4)
        gl.glUniform1i(self.num_lights_loc, num)
        for i in range(num):
            gl.glUniform3f(self.light_pos_loc[i], *lights_data[i]['pos'])
            gl.glUniform3f(self.light_color_loc[i], *lights_data[i]['color'])
            gl.glUniform1f(self.light_intensity_loc[i], lights_data[i]['intensity'])

    def draw(self, position, view_matrix, projection_matrix, scale=1.0, self_luminosity=0.0, camera_pos=[0,0,0]):
        gl.glUseProgram(self.shader)
        gl.glUniform3f(self.cam_pos_loc, *camera_pos)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        
        model = glm.mat4(1.0)
        model = glm.translate(model, glm.vec3(*position))
        # Tilt rings slightly
        model = glm.rotate(model, glm.radians(25.0), glm.vec3(1.0, 0.0, 1.0))
        model = glm.scale(model, glm.vec3(scale))

        gl.glUniformMatrix4fv(self.model_loc, 1, gl.GL_FALSE, glm.value_ptr(model))
        gl.glUniformMatrix4fv(self.view_loc, 1, gl.GL_FALSE, glm.value_ptr(view_matrix))
        gl.glUniformMatrix4fv(self.proj_loc, 1, gl.GL_FALSE, glm.value_ptr(projection_matrix))
        
        gl.glUniform1i(self.use_tex_loc, 1)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture_id)
        
        gl.glUniform1f(self.self_lum_loc, self_luminosity)
        gl.glUniform3f(self.impact_pos_loc, 0,0,0)
        gl.glUniform1f(self.impact_force_loc, 0.0)

        gl.glBindVertexArray(self.mesh.vao)
        gl.glDrawElements(gl.GL_TRIANGLES, self.mesh.index_count, gl.GL_UNSIGNED_INT, None)
        gl.glBindVertexArray(0)
        gl.glDisable(gl.GL_BLEND)
