import OpenGL.GL as gl # Standard OpenGL bindings
import OpenGL.GL.shaders # Shader compilation
import glm # OpenGL Mathematics
import numpy as np # Used for coordinate manipulation
from graphics.shaders import STANDARD_VERTEX, STANDARD_FRAGMENT
from graphics.models.glb_loader import GLBLoader

class MultiMeshRenderer:
    """General-purpose renderer for complex 3D models (GLB format).
    Handles hierarchical mesh structures and specialized orientation logic
    for ships and missiles.

    Args:

    Returns:

    """
    def __init__(self, model_path, initial_scale=1.0, is_ship=False, is_missile=False):
        """
        Loads 3D model data from a GLB file.
        
        Args:
            model_path (str): File path to the .glb asset.
            initial_scale (float): Base scaling factor.
            is_ship, is_missile (bool): Boolean flags for special alignment rotations.
        """
        self.scale = initial_scale
        self.meshes = GLBLoader.load(model_path)
        self.is_ship = is_ship
        self.is_missile = is_missile
        
        vs = gl.shaders.compileShader(STANDARD_VERTEX, gl.GL_VERTEX_SHADER)
        fs = gl.shaders.compileShader(STANDARD_FRAGMENT, gl.GL_FRAGMENT_SHADER)
        self.shader = gl.shaders.compileProgram(vs, fs)

        self.model_loc = gl.glGetUniformLocation(self.shader, "model")
        self.view_loc = gl.glGetUniformLocation(self.shader, "view")
        self.proj_loc = gl.glGetUniformLocation(self.shader, "projection")
        self.use_tex_loc = gl.glGetUniformLocation(self.shader, "use_texture")
        self.impact_pos_loc = [gl.glGetUniformLocation(self.shader, f"impact_pos[{i}]") for i in range(32)]
        self.impact_force_loc = [gl.glGetUniformLocation(self.shader, f"impact_force[{i}]") for i in range(32)]
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
        """Updates global lighting uniforms.

        Args:
          lights_data: List of active light sources.

        Returns:

        """
        gl.glUseProgram(self.shader)
        num = min(len(lights_data), 8)
        gl.glUniform1i(self.num_lights_loc, num)
        for i in range(num):
            gl.glUniform3f(self.light_pos_loc[i], *lights_data[i]['pos'])
            gl.glUniform3f(self.light_color_loc[i], *lights_data[i]['color'])
            gl.glUniform1f(self.light_intensity_loc[i], lights_data[i]['intensity'])

    def draw(self, position, view_matrix, projection_matrix, yaw=0.0, pitch=0.0, impacts=[], self_luminosity=0.0, camera_pos=[0,0,0], config=None):
        """Renders all meshes in the model hierarchy.
        
        Math (Orientation):
            1. Translation: Move to relative position.
            2. Rotation (Yaw): Orbit orientation.
            3. Rotation (Pitch): Tilt orientation.
            4. Model-Specific Corrections: Compensates for model files whose
               internal 'forward' axis doesn't match the engine convention (+Z).
            5. Scale: Normalizes mesh size.

        Args:
          yaw(float, optional): Rotation around Y axis in radians. (Default value = 0.0)
          pitch(float, optional): Rotation around X axis in radians.
        References: (Default value = 0.0)
          pitch(float, optional): Rotation around X axis in radians.
        References:
        - graphics.models.glb_loader.GLBLoader (Default value = 0.0)
          position: 
          view_matrix: 
          projection_matrix: 
          impacts:  (Default value = [])
          self_luminosity:  (Default value = 0.0)
          camera_pos:  (Default value = [0)
          0: 
          0]: 
          config:  (Default value = None)

        Returns:

        """
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
        
        # Camera orbit slaving
        model = glm.rotate(model, yaw, glm.vec3(0.0, 1.0, 0.0))
        model = glm.rotate(model, -pitch, glm.vec3(1.0, 0.0, 0.0))
        
        if self.is_ship:
            # Model Alignment Correction:
            # Adjusts the 'Orville' model to face forward along the trajectory.
            model = glm.rotate(model, glm.radians(-90.0), glm.vec3(0.0, 1.0, 0.0))
            model = glm.rotate(model, glm.radians(-90.0), glm.vec3(1.0, 0.0, 0.0))
            model = glm.rotate(model, glm.radians(20.0), glm.vec3(0.0, 1.0, 0.0))
        elif self.is_missile:
            # Model Alignment Correction:
            # Standardizes missile orientation.
            model = glm.rotate(model, glm.radians(0.0), glm.vec3(0.0, 1.0, 0.0))
        
        model = glm.scale(model, glm.vec3(self.scale))

        gl.glUniformMatrix4fv(self.model_loc, 1, gl.GL_FALSE, glm.value_ptr(model))
        gl.glUniformMatrix4fv(self.view_loc, 1, gl.GL_FALSE, glm.value_ptr(view_matrix))
        gl.glUniformMatrix4fv(self.proj_loc, 1, gl.GL_FALSE, glm.value_ptr(projection_matrix))
        
        num_c = min(len(impacts), 32)
        gl.glUniform1i(self.num_impacts_loc, num_c)
        for i in range(num_c):
            gl.glUniform3f(self.impact_pos_loc[i], *impacts[i][0])
            gl.glUniform1f(self.impact_force_loc[i], impacts[i][1])
            
        gl.glUniform1f(self.self_lum_loc, self_luminosity)
        
        # Default base color (Matte White for missiles if no texture)
        if self.is_missile:
            gl.glUniform3f(self.base_color_loc, 1.0, 1.0, 1.0)
        else:
            gl.glUniform3f(self.base_color_loc, 0.6, 0.6, 0.7)

        # Render Loop for Multi-Mesh assets
        for mesh in self.meshes:
            gl.glUniform1i(self.use_tex_loc, int(mesh.has_texture))
            if mesh.has_texture:
                gl.glActiveTexture(gl.GL_TEXTURE0)
                gl.glBindTexture(gl.GL_TEXTURE_2D, mesh.texture_id)

            gl.glBindVertexArray(mesh.vao)
            gl.glDrawElements(gl.GL_TRIANGLES, mesh.index_count, gl.GL_UNSIGNED_INT, None)
            
        gl.glBindVertexArray(0)
