import numpy as np

def update_physics(matrix, active_mask, dt, G=1.0, fixed_indices=None, immune_indices=None):
    """Performs a single step of N-Body gravitational simulation using vectorized NumPy operations.
    Modifies the velocity and position columns in the Physics State Matrix in-place.
    
    Mathematical Formula:
        Acceleration (a) of body 'i' is the sum of forces from all other bodies 'j':
        a_i = sum over j ( (G * M_j / |r_ij|^3) * r_vector_ij )
        where r_vector_ij = P_j - P_i
    
    Optimization:
        Uses broadcasting to compute the displacement matrix (N x N x 3) and distance
        matrix (N x N) in a single pass, avoiding slow Python loops.

    Args:
      matrix(np.ndarray): The N x 10 state matrix.
      active_mask(np.ndarray): Boolean mask of which bodies are active.
      dt(float): The time step for integration.
      G(float, optional): The Universal Gravitational Constant. (Default value = 1.0)
      fixed_indices(list, optional): Indices of bodies that should not move (e.g., the Sun). (Default value = None)
      immune_indices(list, optional): Indices of bodies that should not receive acceleration (e.g., the player ship). (Default value = None)

    Returns:

    """
    if not np.any(active_mask):
        return

    # Extract positions and masses for active bodies
    positions = matrix[active_mask, 0:3]
    masses = matrix[active_mask, 6]
    
    N = positions.shape[0]
    
    # Integration step for single-body systems (no gravity possible)
    # If there's only 1 body or less, no gravity to calculate, just apply velocity
    if N < 2:
        matrix[active_mask, 0:3] += matrix[active_mask, 3:6] * dt
        return

    # diff[i, j] is the vector pointing from body i TO body j (P_j - P_i)
    # Broadcasting positions from (N, 3) to (1, N, 3) and (N, 1, 3) creates the (N, N, 3) difference matrix.
    diff = positions[np.newaxis, :, :] - positions[:, np.newaxis, :]
    
    # Compute pairwise Euclidean distances: |r_ij| = sqrt(dx^2 + dy^2 + dz^2)
    r = np.linalg.norm(diff, axis=2)
    r = np.maximum(r, 0.001) # Softening factor to prevent division by zero/infinity at close range
    np.fill_diagonal(r, 1.0) # Avoid self-to-self force calculation artifacts
    
    # Newton's Law of Gravitation (Vector form): F = G * M1 * M2 * r_vec / |r|^3
    # We compute accel_magnitude = G * M_j / |r_ij|^3
    accel_magnitude = (G * masses[np.newaxis, :]) / (r**3)
    np.fill_diagonal(accel_magnitude, 0.0)
    
    # Multiply the magnitude by the direction vector (r_vec_ij)
    accel_vecs = accel_magnitude[..., np.newaxis] * diff
    
    # Sum accelerations from all bodies 'j' acting on each body 'i'
    total_accel = np.sum(accel_vecs, axis=1)
    
    # Store properties for fixed indices (anchors like the Sun)
    if fixed_indices is not None and len(fixed_indices) > 0:
        fixed_pos = matrix[fixed_indices, 0:3].copy()
        fixed_vel = matrix[fixed_indices, 3:6].copy()
        
    # Apply immunity (bodies like the ship that follow user input instead of gravity)
    if immune_indices is not None and len(immune_indices) > 0:
        active_idx = np.where(active_mask)[0]
        for idx in immune_indices:
            try:
                local_idx = np.where(active_idx == idx)[0][0]
                total_accel[local_idx] = 0.0
            except IndexError:
                pass
        
    # Semi-Implicit Euler Integration:
    # 1. Update Velocity: v_new = v_old + a * dt
    matrix[active_mask, 3:6] += total_accel * dt
    # 2. Update Position: p_new = p_old + v_new * dt
    matrix[active_mask, 0:3] += matrix[active_mask, 3:6] * dt

    # Revert fixed bodies (Ensures anchors stay perfectly still regardless of force)
    if fixed_indices is not None and len(fixed_indices) > 0:
        matrix[fixed_indices, 0:3] = fixed_pos
        matrix[fixed_indices, 3:6] = fixed_vel
