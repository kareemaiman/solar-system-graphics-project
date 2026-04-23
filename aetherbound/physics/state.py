import numpy as np

class PhysicsState:
    """
    Data-Oriented Master State Matrix for all physical bodies.
    Manages an N x 10 NumPy array of dtype float64 (f8).
    
    Columns:
        0: x
        1: y
        2: z
        3: v_x
        4: v_y
        5: v_z
        6: mass
        7: yaw
        8: pitch
        9: active_flag (1.0 = Active, 0.0 = Inactive/Deleted)
    """
    
    # Column semantic indices for improved readability
    X, Y, Z = 0, 1, 2
    VX, VY, VZ = 3, 4, 5
    MASS = 6
    YAW, PITCH = 7, 8
    ACTIVE = 9

    def __init__(self, max_bodies=10000):
        # A 2D array of (max_bodies, 10) initialized to zeros with 'f4' constraints
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
        """
        Spawns a new celestial body and returns its index.
        Finds the first inactive row and overwrites it.
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
        """
        Logically deletes a body by clearing its active flag.
        Sets mass to 0, which ignores it in Newtonian equations.
        """
        self.matrix[idx, self.ACTIVE] = 0.0
        self.matrix[idx, self.MASS] = 0.0
        
    def get_active_mask(self):
        """
        Returns a boolean mask of active bodies for vectorized operations.
        """
        return self.matrix[:, self.ACTIVE] == 1.0

    def get_active_bodies(self):
        """
        Returns an N x 10 view of only the currently active bodies.
        """
        mask = self.get_active_mask()
        return self.matrix[mask]
    
    def apply_gravity(self, dt, G=1.0):
        """
        Updates positions and velocities of all active bodies via N-Body gravity.
        """
        from .engine import update_physics
        mask = self.get_active_mask()
        update_physics(self.matrix, mask, dt, G, fixed_indices=self.fixed_indices, immune_indices=self.immune_indices)
