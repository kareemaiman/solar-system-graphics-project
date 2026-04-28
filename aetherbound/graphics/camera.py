import glm
import math

class ThirdPersonCamera:
    """3rd-Person Orbit Camera with 'Spring Arm' following effect.
    Uses spherical coordinates (radius, yaw, pitch) around a target position.

    Args:

    Returns:

    """
    def __init__(self, target_pos=(0.0, 0.0, 0.0), distance=10.0):
        """
        Initializes the camera state.
        
        Args:
            target_pos (tuple): Initial center point to orbit.
            distance (float): Radius of the orbit.
        """
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
        """Calculates the camera's Cartesian world coordinates based on the target position
        and the current orbit angles (Spherical Coordinates).
        
        Math (Spherical to Cartesian):
            x = r * cos(pitch) * sin(yaw)
            y = r * sin(pitch)
            z = r * cos(pitch) * cos(yaw)

        Args:

        Returns:

        """
        import numpy as np
        # Spherical to Cartesian coordinates relative to the target
        offset_x = self.distance * math.cos(self.pitch) * math.sin(self.yaw)
        offset_y = self.distance * math.sin(self.pitch)
        offset_z = self.distance * math.cos(self.pitch) * math.cos(self.yaw)

        self.actual_pos_f64 = self.target_pos_f64 + np.array([offset_x, offset_y, offset_z], dtype=np.float64)

    def process_mouse_movement(self, xoffset, yoffset, sensitivity=0.005):
        """Updates the orbit angles based on raw mouse delta input.
        
        Math:
            New_Angle = Old_Angle + Delta * Sensitivity

        Args:
          xoffset: Mouse move delta on X axis.
          yoffset: Mouse move delta on Y axis.
          sensitivity:  (Default value = 0.005)

        Returns:

        """
        self.yaw -= xoffset * sensitivity
        self.pitch += yoffset * sensitivity
        
        # Clamp pitch to prevent over-the-top flipping
        self.pitch = max(self.min_pitch, min(self.max_pitch, self.pitch))

    def process_scroll(self, yoffset, zoom_speed=1.0):
        """Increases or decreases the orbit radius (Distance).

        Args:
          yoffset: 
          zoom_speed:  (Default value = 1.0)

        Returns:

        """
        self.distance -= yoffset * zoom_speed
        self.distance = max(1.0, min(200.0, self.distance)) # Clamp zoom range

    def update(self, new_target_pos, dt):
        """Updates the camera's anchor point to match a moving entity (the spaceship).

        Args:
          new_target_pos: The latest world position of the ship.
          dt: Delta time (used if smoothing/lerping is enabled).
        Implementation: Currently locks instantly for maximum precision.

        Returns:

        """
        import numpy as np
        self.target_pos_f64 = np.array(new_target_pos, dtype=np.float64)
        self._update_actual_position()

    def get_view_matrix(self):
        """Generates the 4x4 View Matrix required by shaders.
        
        Math:
            Uses the 'LookAt' algorithm:
            1. Computes the Forward vector (from camera to target).
            2. Computes the Right vector (Cross product of Up and Forward).
            3. Computes the Up vector (Cross product of Forward and Right).
            4. Constructs a rotation/translation matrix that transforms
               world space into camera-relative space.

        Args:

        Returns:

        """
        # Implementation note: The renderer handles world translation separately 
        # for large-scale floating point stability.
        up_vector = glm.vec3(0.0, 1.0, 0.0)
        
        offset_x = self.distance * math.cos(self.pitch) * math.sin(self.yaw)
        offset_y = self.distance * math.sin(self.pitch)
        offset_z = self.distance * math.cos(self.pitch) * math.cos(self.yaw)
        
        target_relative = glm.vec3(-offset_x, -offset_y, -offset_z)
        
        return glm.lookAt(glm.vec3(0.0, 0.0, 0.0), target_relative, up_vector)
