import numpy as np # Used for memory-mapped-like state matrix storage

class PhysicsState:
    """Master Registry for all physical entities in the simulation.
    Uses a Data-Oriented Design (DOD) approach by storing all entity properties
    in a contiguous NumPy matrix for cache-friendly vectorized processing.
    
    The N x 10 matrix is structured as follows:
    
    Matrix Columns:
        0-2: Position (X, Y, Z) - World space coordinates.
        3-5: Velocity (VX, VY, VZ) - Units per simulation second.
        6:   Mass - Scalar mass used for gravitational pull calculations.
        7-8: Yaw, Pitch - Visual orientation (rotation around Y and local X).
        9:   Active Flag - 1.0 if the entity exists, 0.0 if it is deleted/available.

    Args:

    Returns:

    """
    
    X, Y, Z = 0, 1, 2
    VX, VY, VZ = 3, 4, 5
    MASS = 6
    YAW, PITCH = 7, 8
    ACTIVE = 9

    def __init__(self, max_bodies=10000):
        """
        Allocates the contiguous memory block for the simulation state.
        
        Args:
            max_bodies (int): The maximum number of physical entities allowed simultaneously.
        """
        self.max_bodies = max_bodies
        self.matrix = np.zeros((self.max_bodies, 10), dtype=np.float64)
        
        # Radii for collision checks
        self.radii = np.zeros(self.max_bodies, dtype=np.float64)
        
        # Anchor specific indices
        self.fixed_indices = []
        
        # Immune indices (unaffected by gravity but can move)
        self.immune_indices = []
        
        # Track how many bodies have been spawned
        self.spawn_count = 0

    def add_body(self, position, velocity, mass, radius=1.0, yaw=0.0, pitch=0.0):
        """Spawns a new entity by finding the first available slot in the matrix.
        
        Math:
            Uses np.where(ACTIVE == 0.0) to find free indices.

        Args:
          position, velocity: Initial 3D vectors.
          mass(float): Mass of the object.
          radius(float, optional): Physical size for collision detection. (Default value = 1.0)
          yaw, pitch: Starting rotation.
          position: 
          velocity: 
          yaw:  (Default value = 0.0)
          pitch:  (Default value = 0.0)

        Returns:
          int: The index (ID) of the entity in the global matrix.

        """
        # Find first inactive slot
        inactive_indices = np.where(self.matrix[:, self.ACTIVE] == 0.0)[0]
        
        if len(inactive_indices) == 0:
            raise MemoryError("PhysicsState matrix is completely full!")
            
        idx = inactive_indices[0]
        
        # Set values
        self.matrix[idx, self.X:self.Z+1] = position
        self.matrix[idx, self.VX:self.VZ+1] = velocity
        self.matrix[idx, self.MASS] = mass
        self.matrix[idx, self.YAW:self.PITCH+1] = [yaw, pitch]
        self.matrix[idx, self.ACTIVE] = 1.0
        
        self.radii[idx] = radius
        return idx
        
    def delete_body(self, idx):
        """Logically removes an entity from the simulation.
        
        Action:
            Sets ACTIVE to 0.0 so renderers and physics loops ignore it.
            Sets MASS to 0.0 so it no longer exerts gravitational pull.

        Args:
          idx(int): The matrix index to clear.

        Returns:

        """
        self.matrix[idx, self.ACTIVE] = 0.0
        self.matrix[idx, self.MASS] = 0.0
        
    def get_active_mask(self):
        """Generates a boolean mask array of all entities where ACTIVE == 1.0.
        This mask is used to perform sub-selections of the matrix without loops.

        Args:

        Returns:
          np.ndarray: Boolean array of shape (max_bodies,).

        """
        return self.matrix[:, self.ACTIVE] == 1.0

    def get_active_bodies(self):
        """Returns an N x 10 view of only the currently active bodies."""
        mask = self.get_active_mask()
        return self.matrix[mask]
    
    def apply_gravity(self, dt, G=1.0):
        """Delegate method that calls the optimized gravity solver.
        
        References:
            - physics.gravity.update_physics

        Args:
          dt(float): Time step.
          G(float, optional): Gravity constant. (Default value = 1.0)

        Returns:

        """
        from .engine import update_physics
        mask = self.get_active_mask()
        update_physics(self.matrix, mask, dt, G, fixed_indices=self.fixed_indices, immune_indices=self.immune_indices)
