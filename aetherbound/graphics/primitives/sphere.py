import OpenGL.GL as gl
from graphics.shapes import generate_uv_sphere
from graphics.models.mesh import Mesh

def create_sphere_mesh(radius=1.0, sectors=64, stacks=32, texture_id=None):
    v, n, u, i = generate_uv_sphere(radius=radius, sectors=sectors, stacks=stacks)
    return Mesh(v, n, u, i, texture_id=texture_id)

def load_texture(image_path):
    from PIL import Image
    import numpy as np
    try:
        img = Image.open(image_path).convert("RGBA").transpose(Image.FLIP_TOP_BOTTOM)
        img_data = np.array(list(img.getdata()), np.uint8)
        
        texture_id = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, texture_id)
        
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_REPEAT)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_REPEAT)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, img.width, img.height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, img_data)
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        return texture_id
    except Exception as e:
        print(f"Failed to load external texture {image_path}: {e}")
        return None
