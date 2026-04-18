import numpy as np

def update_physics(matrix, active_mask, dt, G=1.0):
    """
    Vectorized N-Body Gravity calculation.
    Modifies the velocity and position columns in the Physics State Matrix in-place.
    
    Uses O(N^2) broadcasting but heavily optimized via NumPy C-backends.
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

    # Calculate pairwise coordinate differences (Shape: N, N, 3)
    # diff[i, j] is the vector pointing from body i TO body j (P_j - P_i)
    # Corrected broadcast mapping so gravity is attractive!
    diff = positions[np.newaxis, :, :] - positions[:, np.newaxis, :]
    
    # Calculate pairwise distances (Shape: N, N)
    r = np.linalg.norm(diff, axis=2)
    
    # Add a small epsilon to the diagonal to prevent division by zero for self-interactions (i == j)
    # We fill it with 1.0 because we'll zero out the force magnitude for the diagonal later anyway.
    np.fill_diagonal(r, 1.0)
    
    # Acceleration logic based on Newton's Law of Universal Gravitation:
    # F_ij = G * M_i * M_j / r^2
    # a_i = F_tot_i / M_i = sum_j (G * M_j * diff_ij / r^3)
    
    # Compute: G * M_j / r^3 (Shape: N, N)
    accel_magnitude = (G * masses[np.newaxis, :]) / (r**3)
    
    # Zero out self-interaction (diagonal) so a body doesn't pull on itself
    np.fill_diagonal(accel_magnitude, 0.0)
    
    # Acceleration vectors directed from i to j (Shape: N, N, 3)
    accel_vecs = accel_magnitude[..., np.newaxis] * diff
    
    # Sum over all j to get net acceleration vector for each i (Shape: N, 3)
    total_accel = np.sum(accel_vecs, axis=1)
    
    # Update velocities: V = V + A * dt
    matrix[active_mask, 3:6] += total_accel * dt
    
    # Update positions: P = P + V * dt
    matrix[active_mask, 0:3] += matrix[active_mask, 3:6] * dt
