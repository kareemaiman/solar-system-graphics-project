import numpy as np
import math

def generate_uv_sphere(radius=1.0, sectors=36, stacks=18):
    """
    Procedurally constructs a 3D unit sphere returning explicit arrays mapping
    vertices, normals, UV wraps, and face indices.
    """
    vertices = []
    normals = []
    uvs = []
    
    length_inv = 1.0 / radius
    
    for i in range(stacks + 1):
        stack_angle = math.pi / 2 - i * math.pi / stacks
        xy = radius * math.cos(stack_angle)
        y = radius * math.sin(stack_angle)
        
        # Add (sectors+1) vertices per stack to avoid UV seam artifacts
        for j in range(sectors + 1):
            sector_angle = j * 2 * math.pi / sectors
            
            x = xy * math.cos(sector_angle)
            z = xy * math.sin(sector_angle)
            
            vertices.extend([x, y, z])
            
            nx = x * length_inv
            ny = y * length_inv
            nz = z * length_inv
            normals.extend([nx, ny, nz])
            
            # Inverted T avoids upside-down textures
            s = float(j) / sectors
            t = 1.0 - float(i) / stacks
            uvs.extend([s, t])
            
    indices = []
    for i in range(stacks):
        k1 = i * (sectors + 1)
        k2 = k1 + sectors + 1
        
        for j in range(sectors):
            # Exclude degenerate top triangles
            if i != 0:
                indices.extend([k1, k2, k1 + 1])
                
            # Exclude degenerate bottom triangles
            if i != (stacks - 1):
                indices.extend([k1 + 1, k2, k2 + 1])
                
            k1 += 1
            k2 += 1
            
    return (
        np.array(vertices, dtype=np.float32), 
        np.array(normals, dtype=np.float32), 
        np.array(uvs, dtype=np.float32), 
        np.array(indices, dtype=np.uint32)
    )
