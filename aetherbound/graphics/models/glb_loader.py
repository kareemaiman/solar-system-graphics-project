import trimesh
import numpy as np
import OpenGL.GL as gl
from PIL import Image
from graphics.models.mesh import Mesh

class GLBLoader:
    @staticmethod
    def load(filepath):
        """Loads a GLB and returns a list of Mesh objects to support multi-mesh GLBs."""
        scene_or_mesh = trimesh.load(filepath, force='scene')
        
        meshes = []
        
        # Iterating over all geometry in the scene
        for geom_name, geom in scene_or_mesh.geometry.items():
            vertices = geom.vertices.astype(np.float32)
            
            if not hasattr(geom, 'vertex_normals') or geom.vertex_normals is None or len(geom.vertex_normals) == 0:
                geom.fix_normals()
            normals = geom.vertex_normals.astype(np.float32)
            indices = geom.faces.astype(np.uint32)
            
            uvs = getattr(geom.visual, 'uv', None)
            if uvs is None or len(uvs) == 0:
                uvs = np.zeros((len(vertices), 2), dtype=np.float32)
            else:
                uvs = np.array(uvs, dtype=np.float32)
                
            texture_id = None
            if hasattr(geom.visual, 'material'):
                img = None
                if hasattr(geom.visual.material, 'baseColorTexture') and geom.visual.material.baseColorTexture is not None:
                    img = geom.visual.material.baseColorTexture
                elif hasattr(geom.visual.material, 'image') and geom.visual.material.image is not None:
                    img = geom.visual.material.image
                    
                if img is not None:
                    img = img.convert("RGBA").transpose(Image.FLIP_TOP_BOTTOM)
                    img_data = np.array(list(img.getdata()), np.uint8)
                    texture_id = gl.glGenTextures(1)
                    gl.glBindTexture(gl.GL_TEXTURE_2D, texture_id)
                    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
                    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
                    gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, img.width, img.height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, img_data)
                    gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

            mesh_obj = Mesh(vertices, normals, uvs, indices, texture_id)
            meshes.append(mesh_obj)
            
        return meshes
