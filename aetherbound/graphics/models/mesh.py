import OpenGL.GL as gl
import numpy as np

class Mesh:
    def __init__(self, vertices, normals, uvs, indices, texture_id=None):
        self.vertices = vertices
        self.normals = normals
        self.uvs = uvs
        self.indices = indices
        
        self.texture_id = texture_id
        self.has_texture = texture_id is not None
        
        self.vao, self.index_count = self._build_vbo()
        
    def _build_vbo(self):
        vertex_data = np.hstack([self.vertices.reshape(-1, 3), 
                                 self.normals.reshape(-1, 3), 
                                 self.uvs.reshape(-1, 2)]).flatten()
        
        vao = gl.glGenVertexArrays(1)
        vbo = gl.glGenBuffers(1)
        ebo = gl.glGenBuffers(1)

        gl.glBindVertexArray(vao)

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertex_data.nbytes, vertex_data, gl.GL_STATIC_DRAW)

        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, ebo)
        gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices.flatten(), gl.GL_STATIC_DRAW)

        stride = 8 * 4 
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, gl.ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(0)
        
        gl.glVertexAttribPointer(1, 3, gl.GL_FLOAT, gl.GL_FALSE, stride, gl.ctypes.c_void_p(12))
        gl.glEnableVertexAttribArray(1)
        
        gl.glVertexAttribPointer(2, 2, gl.GL_FLOAT, gl.GL_FALSE, stride, gl.ctypes.c_void_p(24))
        gl.glEnableVertexAttribArray(2)
        
        gl.glBindVertexArray(0)
        return vao, len(self.indices.flatten())
