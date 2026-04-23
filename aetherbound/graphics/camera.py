import glm
import math

class ThirdPersonCamera:
    """
    3rd-Person Orbit Camera with 'Spring Arm' following effect.
    Uses spherical coordinates (radius, yaw, pitch) around a target position.
    """
    def __init__(self, target_pos=(0.0, 0.0, 0.0), distance=10.0):
        import numpy as np
        self.target_pos_f64 = np.array(target_pos, dtype=np.float64)
        self.actual_pos_f64 = np.array(target_pos, dtype=np.float64)
        
        # Camera orbit settings
        self.distance = distance
        self.yaw = 0.0     # Horizontal angle in radians
        self.pitch = 0.0   # Vertical angle in radians
        
        # Constraints
        self.min_pitch = -math.pi / 2.0 + 0.01  # Prevent gimbal lock by clamping slightly before 90 deg
        self.max_pitch = math.pi / 2.0 - 0.01
        
        # Spring arm smoothing factor
        # Higher value = faster, tighter follow; Lower value = slower, spongier follow
        self.follow_speed = 5.0  

        self._update_actual_position()

    def _update_actual_position(self):
        """Calculates exact spherical position based on target and angles."""
        import numpy as np
        # Spherical to Cartesian coordinates relative to the target
        offset_x = self.distance * math.cos(self.pitch) * math.sin(self.yaw)
        offset_y = self.distance * math.sin(self.pitch)
        offset_z = self.distance * math.cos(self.pitch) * math.cos(self.yaw)

        self.actual_pos_f64 = self.target_pos_f64 + np.array([offset_x, offset_y, offset_z], dtype=np.float64)

    def process_mouse_movement(self, xoffset, yoffset, sensitivity=0.005):
        """Updates yaw and pitch based on mouse input."""
        self.yaw -= xoffset * sensitivity
        self.pitch += yoffset * sensitivity
        
        # Clamp pitch to prevent over-the-top flipping
        self.pitch = max(self.min_pitch, min(self.max_pitch, self.pitch))

    def process_scroll(self, yoffset, zoom_speed=1.0):
        """Updates the distance (spring arm length) based on scroll wheel."""
        self.distance -= yoffset * zoom_speed
        self.distance = max(1.0, min(200.0, self.distance)) # Clamp zoom range

    def update(self, new_target_pos, dt):
        """
        Locks the camera's target position instantly to the actual entity's position
        """
        import numpy as np
        self.target_pos_f64 = np.array(new_target_pos, dtype=np.float64)
        self._update_actual_position()

    def get_view_matrix(self):
        """Returns the Camera-Centric View Matrix (no world translation) via glm.lookAt."""
        # The camera is conceptually at (0,0,0). It looks towards the target which is at -offset.
        up_vector = glm.vec3(0.0, 1.0, 0.0)
        
        offset_x = self.distance * math.cos(self.pitch) * math.sin(self.yaw)
        offset_y = self.distance * math.sin(self.pitch)
        offset_z = self.distance * math.cos(self.pitch) * math.cos(self.yaw)
        
        target_relative = glm.vec3(-offset_x, -offset_y, -offset_z)
        
        return glm.lookAt(glm.vec3(0.0, 0.0, 0.0), target_relative, up_vector)
