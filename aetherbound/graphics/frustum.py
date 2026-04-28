import numpy as np # Used for vectorized plane distance calculations
import glm # OpenGL Mathematics

class Frustum:
    """Implements View-Frustum Culling to skip rendering objects outside the camera view.
    Uses the Gribb-Hartmann method for extracting frustum planes from the VP matrix.

    Args:

    Returns:

    """
    def __init__(self):
        self.planes = np.zeros((6, 4))
        
    def update(self, projection_matrix, view_matrix):
        """Extracts the 6 frustum planes (Left, Right, Bottom, Top, Near, Far)
        from the combined View-Projection matrix.
        
        Math:
            Each plane equation is Ax + By + Cz + D = 0.
            Planes are extracted by adding/subtracting rows of the VP matrix.

        Args:
          projection_matrix: 
          view_matrix: 

        Returns:

        """
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
        
        # Normalize plane normals to ensure distance calculations are accurate
        for i in range(6):
            length = np.linalg.norm(self.planes[i, :3])
            if length > 0.0001:
                self.planes[i] /= length

    def is_sphere_visible(self, center, radius):
        """Checks if a bounding sphere is within the visible volume.
        
        Math:
            The distance from a point to a plane is: d = Normal * Point + D
            If distance < -radius, the sphere is completely behind the plane.

        Args:
          center(np.array): 3D position of the sphere center.
          radius(float): Radius of the sphere.

        Returns:
          bool: True if visible or partially visible.

        """
        for i in range(6):
            distance = np.dot(self.planes[i, :3], center) + self.planes[i, 3]
            if distance < -radius:
                return False
        return True
