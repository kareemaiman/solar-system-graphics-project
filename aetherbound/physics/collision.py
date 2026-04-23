import numpy as np

def detect_collisions(matrix, active_mask, radii):
    """
    Detects collisions between all active spheres using vectorized distance logic.
    Returns: list of tuples (id_a, id_b) representing the global matrix indices.
    """
    active_indices = np.where(active_mask)[0]
    if len(active_indices) < 2:
        return []
        
    positions = matrix[active_mask, 0:3]
    active_radii = radii[active_mask]
    
    diff = positions[np.newaxis, :, :] - positions[:, np.newaxis, :]
    r = np.linalg.norm(diff, axis=2)
    thresholds = active_radii[np.newaxis, :] + active_radii[:, np.newaxis]
    
    np.fill_diagonal(r, np.inf)
    collisions = np.argwhere(r < thresholds)
    
    unique_pairs = []
    for c in collisions:
        i, j = c
        if i < j:
            unique_pairs.append((active_indices[i], active_indices[j]))
            
    return unique_pairs
