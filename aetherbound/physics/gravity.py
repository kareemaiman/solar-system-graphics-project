import numpy as np

def update_physics(matrix, active_mask, dt, G=1.0, fixed_indices=None, immune_indices=None):
    """
    Vectorized N-Body Gravity calculation.
    Modifies the velocity and position columns in the Physics State Matrix in-place.
    """
    if not np.any(active_mask):
        return

    # Extract positions and masses for active bodies
    positions = matrix[active_mask, 0:3]
    masses = matrix[active_mask, 6]
    
    N = positions.shape[0]
    
    # If there's only 1 body or less, no gravity to calculate, just apply velocity
    if N < 2:
        matrix[active_mask, 0:3] += matrix[active_mask, 3:6] * dt
        return

    # diff[i, j] is the vector pointing from body i TO body j (P_j - P_i)
    diff = positions[np.newaxis, :, :] - positions[:, np.newaxis, :]
    
    # Pairwise distances
    r = np.linalg.norm(diff, axis=2)
    r = np.maximum(r, 0.001)
    np.fill_diagonal(r, 1.0)
    
    # Compute: G * M_j / r^3 (Shape: N, N)
    accel_magnitude = (G * masses[np.newaxis, :]) / (r**3)
    np.fill_diagonal(accel_magnitude, 0.0)
    
    # Net acceleration vectors
    accel_vecs = accel_magnitude[..., np.newaxis] * diff
    total_accel = np.sum(accel_vecs, axis=1)
    
    # Store properties for fixed indices
    if fixed_indices is not None and len(fixed_indices) > 0:
        fixed_pos = matrix[fixed_indices, 0:3].copy()
        fixed_vel = matrix[fixed_indices, 3:6].copy()
        
    # Apply immunity
    if immune_indices is not None and len(immune_indices) > 0:
        active_idx = np.where(active_mask)[0]
        for idx in immune_indices:
            try:
                local_idx = np.where(active_idx == idx)[0][0]
                total_accel[local_idx] = 0.0
            except IndexError:
                pass
        
    # Integration
    matrix[active_mask, 3:6] += total_accel * dt
    matrix[active_mask, 0:3] += matrix[active_mask, 3:6] * dt

    # Revert fixed bodies
    if fixed_indices is not None and len(fixed_indices) > 0:
        matrix[fixed_indices, 0:3] = fixed_pos
        matrix[fixed_indices, 3:6] = fixed_vel
