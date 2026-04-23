import numpy as np
import glm

class Frustum:
    def __init__(self):
        self.planes = np.zeros((6, 4))
        
    def update(self, projection_matrix, view_matrix):
        vp = projection_matrix * view_matrix
        
        # VP matrix is column-major in PyGLM. Transposing gives us the rows.
        mat = np.array(vp.to_list()).T
        
        # Calculate planes
        self.planes[0] = mat[3] + mat[0] # Left
        self.planes[1] = mat[3] - mat[0] # Right
        self.planes[2] = mat[3] + mat[1] # Bottom
        self.planes[3] = mat[3] - mat[1] # Top
        self.planes[4] = mat[3] + mat[2] # Near
        self.planes[5] = mat[3] - mat[2] # Far
        
        # Normalize planes
        for i in range(6):
            length = np.linalg.norm(self.planes[i, :3])
            if length > 0.0001:
                self.planes[i] /= length

    def is_sphere_visible(self, center, radius):
        """Returns True if the sphere is inside or intersecting the frustum."""
        for i in range(6):
            distance = np.dot(self.planes[i, :3], center) + self.planes[i, 3]
            if distance < -radius:
                return False
        return True
