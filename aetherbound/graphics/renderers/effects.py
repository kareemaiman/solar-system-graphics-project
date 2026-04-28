import OpenGL.GL as gl # Direct access to GPU state and draw calls
import OpenGL.GL.shaders # Utilities for compiling GLSL
import glm # OpenGL Mathematics
import numpy as np # Used for coordinate offsets

class EffectRenderer:
    """Renders specialized procedural effects like the Scanner Wave and Explosions.
    These effects utilize spherical math and alpha blending to simulate
    translucent, expanding volumes.

    Args:

    Returns:

    """
    def __init__(self):
        """
        Initializes shaders and pre-loads a sphere mesh shared by all effects.
        
        References:
            - graphics.shaders (SCANNER_FRAGMENT, EXPLOSION_FRAGMENT)
            - graphics.primitives.sphere (create_sphere_mesh)
        """
        from graphics.shaders import STANDARD_VERTEX, SCANNER_FRAGMENT, EXPLOSION_FRAGMENT
        from graphics.primitives.sphere import create_sphere_mesh
        
        # Scanner Shader
        vs = gl.shaders.compileShader(STANDARD_VERTEX, gl.GL_VERTEX_SHADER)
        fs = gl.shaders.compileShader(SCANNER_FRAGMENT, gl.GL_FRAGMENT_SHADER)
        self.shader = gl.shaders.compileProgram(vs, fs)
        
        self.mesh = create_sphere_mesh(radius=1.0, sectors=64, stacks=32)
        
        # Explosion Shader
        vs_exp = gl.shaders.compileShader(STANDARD_VERTEX, gl.GL_VERTEX_SHADER)
        fs_exp = gl.shaders.compileShader(EXPLOSION_FRAGMENT, gl.GL_FRAGMENT_SHADER)
        self.explosion_prog = gl.shaders.compileProgram(vs_exp, fs_exp)
        
        # Explosion Uniforms
        self.exp_model_loc = gl.glGetUniformLocation(self.explosion_prog, "model")
        self.exp_view_loc = gl.glGetUniformLocation(self.explosion_prog, "view")
        self.exp_proj_loc = gl.glGetUniformLocation(self.explosion_prog, "projection")
        self.exp_center_pos_loc = gl.glGetUniformLocation(self.explosion_prog, "center_pos")
        self.exp_radius_loc = gl.glGetUniformLocation(self.explosion_prog, "current_radius")
        self.exp_max_radius_loc = gl.glGetUniformLocation(self.explosion_prog, "max_radius")
        self.exp_time_loc = gl.glGetUniformLocation(self.explosion_prog, "time")
        self.exp_core_color_loc = gl.glGetUniformLocation(self.explosion_prog, "core_color_u")
        self.exp_edge_color_loc = gl.glGetUniformLocation(self.explosion_prog, "edge_color_u")
        
        # Explosion tracking: list of dicts {pos, radius, start_frame}
        self.active_explosions = []

        self.model_loc = gl.glGetUniformLocation(self.shader, "model")
        self.view_loc = gl.glGetUniformLocation(self.shader, "view")
        self.proj_loc = gl.glGetUniformLocation(self.shader, "projection")
        self.center_pos_loc = gl.glGetUniformLocation(self.shader, "center_pos")
        self.radius_loc = gl.glGetUniformLocation(self.shader, "current_radius")
        self.wave_width_loc = gl.glGetUniformLocation(self.shader, "wave_width")

    def draw_scanner(self, center_pos, radius, view_matrix, projection_matrix):
        """Renders the holographic radar wave.
        
        Math:
            - Model Matrix: Translates to ship center and scales to the current wave radius.
            - Shader: Uses the distance from fragment to center_pos to draw a thin glowing ring.

        Args:
          center_pos(vec3): Origin of the wave.
          radius(float): Current expansion distance.
          view_matrix, projection_matrix: Camera matrices.
          view_matrix: 
          projection_matrix: 

        Returns:

        """
        if radius <= 0:
            return
            
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glDepthMask(gl.GL_FALSE)
        
        gl.glUseProgram(self.shader)
        
        model = glm.mat4(1.0)
        model = glm.translate(model, glm.vec3(*center_pos))
        model = glm.scale(model, glm.vec3(radius + 2.0))
        
        gl.glUniformMatrix4fv(self.model_loc, 1, gl.GL_FALSE, glm.value_ptr(model))
        gl.glUniformMatrix4fv(self.view_loc, 1, gl.GL_FALSE, glm.value_ptr(view_matrix))
        gl.glUniformMatrix4fv(self.proj_loc, 1, gl.GL_FALSE, glm.value_ptr(projection_matrix))
        
        gl.glUniform3f(self.center_pos_loc, *center_pos)
        gl.glUniform1f(self.radius_loc, radius)
        gl.glUniform1f(self.wave_width_loc, 5.0)
        
        self.mesh.draw()
        
        gl.glDepthMask(gl.GL_TRUE)
        gl.glDisable(gl.GL_BLEND)
        gl.glUseProgram(0)

    def trigger_explosion(self, world_pos, current_frame, config, scale_mult=1.0):
        """Adds a new explosion instance to the simulation.

        Args:
          world_pos(vec3): World coordinates of the impact.
          current_frame(int): Frame number for timing.
          config(dict): Visual settings from game_config.json.
          scale_mult(float, optional): Size multiplier based on the target's radius.
        Effect: Appends metadata to self.active_explosions. (Default value = 1.0)

        Returns:

        """
        self.active_explosions.append({
            "world_pos": np.array(world_pos),
            "radius": 0.0,
            "start_frame": current_frame,
            "max_radius": config["effects"]["explosion_max_radius"] * scale_mult,
            "expansion_speed": config["effects"]["explosion_expansion_speed"] * scale_mult,
            "core_color": config["effects"]["explosion_color_core"],
            "edge_color": config["effects"]["explosion_color_edge"]
        })

    def update_explosions(self, current_frame):
        """Updates the radius of all active explosions.
        
        Math:
            Radius = Elapsed_Frames * Expansion_Speed
        
        Cleanup:
            Removes explosions that have exceeded their max_radius.

        Args:
          current_frame: 

        Returns:

        """
        for exp in self.active_explosions[:]:
            elapsed = current_frame - exp["start_frame"]
            exp["radius"] = elapsed * exp["expansion_speed"]
            if exp["radius"] > exp["max_radius"]:
                self.active_explosions.remove(exp)

    def draw_explosions(self, view_matrix, projection_matrix, current_ship_world_pos, time_val):
        """Batch-renders all active explosions.
        
        Graphics Logic:
            - Disables Depth Mask: Explosions are translucent and don't block pixels.
            - Additive Blending: glBlendFunc(SRC_ALPHA, ONE) - makes overlapping explosions brighter.
            - Shader: Procedural noise generates the "fuzzy" fireball look.

        Args:
          current_ship_world_pos: Used to convert world coords to relative view coords.
          time_val: Seed for procedural noise animation.
          view_matrix: 
          projection_matrix: 

        Returns:

        """
        if not self.active_explosions:
            return

        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE)
        gl.glDepthMask(gl.GL_FALSE)
        gl.glUseProgram(self.explosion_prog)

        gl.glUniformMatrix4fv(self.exp_view_loc, 1, gl.GL_FALSE, glm.value_ptr(view_matrix))
        gl.glUniformMatrix4fv(self.exp_proj_loc, 1, gl.GL_FALSE, glm.value_ptr(projection_matrix))
        gl.glUniform1f(self.exp_time_loc, time_val)

        for exp in self.active_explosions:
            rel_pos = (exp["world_pos"] - current_ship_world_pos).astype(np.float32)
            model = glm.mat4(1.0)
            model = glm.translate(model, glm.vec3(*rel_pos))
            model = glm.scale(model, glm.vec3(exp["radius"]))
            
            gl.glUniformMatrix4fv(self.exp_model_loc, 1, gl.GL_FALSE, glm.value_ptr(model))
            gl.glUniform3f(self.exp_center_pos_loc, *rel_pos)
            gl.glUniform1f(self.exp_radius_loc, exp["radius"])
            gl.glUniform1f(self.exp_max_radius_loc, exp["max_radius"])
            gl.glUniform3f(self.exp_core_color_loc, *exp["core_color"])
            gl.glUniform3f(self.exp_edge_color_loc, *exp["edge_color"])
            
            self.mesh.draw()
        
        gl.glDepthMask(gl.GL_TRUE)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glDisable(gl.GL_BLEND)
        gl.glUseProgram(0)
