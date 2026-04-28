import numpy as np # Used for vectorized distance matrix calculations

def detect_collisions(matrix, active_mask, radii):
    """Vectorized sphere-to-sphere collision detection.
    Identifies pairs of entities whose surfaces are overlapping.
    
    Mathematical Formula:
        Two spheres collide if the distance between their centers (d) is less than
        the sum of their radii (R1 + R2).
        Collision condition: |P1 - P2| < (R1 + R2)

    Args:
      matrix(np.ndarray): The global physics state matrix.
      active_mask(np.ndarray): Boolean mask of active entities.
      radii(np.ndarray): Array of radii for all entities.

    Returns:
      list: List of tuples (id_a, id_b) representing global matrix indices of colliding pairs.
      References:
      list: List of tuples (id_a, id_b) representing global matrix indices of colliding pairs.
      References:
      - numpy (np.where, np.linalg.norm, np.argwhere)

    """
    active_indices = np.where(active_mask)[0]
    if len(active_indices) < 2:
        return []
        
    # Extract data for only active bodies to keep the distance matrix small
    positions = matrix[active_mask, 0:3]
    active_radii = radii[active_mask]
    
    # Calculate displacement matrix (N x N x 3) using broadcasting
    diff = positions[np.newaxis, :, :] - positions[:, np.newaxis, :]
    
    # Compute center-to-center distances (N x N)
    r = np.linalg.norm(diff, axis=2)
    
    # Calculate the sum of radii for all pairs (N x N)
    thresholds = active_radii[np.newaxis, :] + active_radii[:, np.newaxis]
    
    # Ignore self-collision by setting diagonal to infinity
    np.fill_diagonal(r, np.inf)
    
    # Find indices where distance < sum of radii
    collisions = np.argwhere(r < thresholds)
    
    unique_pairs = []
    for c in collisions:
        i, j = c
        # Filter to only keep one instance of each pair (avoiding [a,b] and [b,a])
        if i < j:
            unique_pairs.append((active_indices[i], active_indices[j]))
            
    return unique_pairs
