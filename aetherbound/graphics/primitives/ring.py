import numpy as np
import OpenGL.GL as gl
from graphics.models.mesh import Mesh

def create_ring_mesh(inner_radius, outer_radius, sectors=64, texture_id=None):
    """Generates a flat disc mesh for planetary rings."""
    vertices = []
    normals = []
    uvs = []
    indices = []

    for i in range(sectors + 1):
        angle = 2.0 * np.pi * i / sectors
        x = np.cos(angle)
        z = np.sin(angle)

        # Outer ring point
        vertices.append([x * outer_radius, 0, z * outer_radius])
        normals.append([0, 1, 0])
        uvs.append([float(i) / sectors, 1.0])

        # Inner ring point
        vertices.append([x * inner_radius, 0, z * inner_radius])
        normals.append([0, 1, 0])
        uvs.append([float(i) / sectors, 0.0])

    for i in range(sectors):
        # Two triangles per segment
        indices.append([2*i, 2*i+1, 2*i+2])
        indices.append([2*i+1, 2*i+3, 2*i+2])

    return Mesh(
        np.array(vertices, dtype=np.float32),
        np.array(normals, dtype=np.float32),
        np.array(uvs, dtype=np.float32),
        np.array(indices, dtype=np.uint32),
        texture_id
    )
