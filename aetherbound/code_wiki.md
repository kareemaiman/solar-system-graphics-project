# AetherBound 3D Space Explorer - Code Wiki

## Overview
AetherBound is a high-performance 3D space exploration simulation built with Modern OpenGL, Python, and PyGLM. The architectural focus is on Data-Oriented Design (DOD) to minimize Python's interpreter overhead in favor of bulk NumPy processing.

## Architecture Guidelines
1. **Data-Oriented Physics (Master State Matrix)**: 
   - All physics entities exist in a single global `N x 10` NumPy array (`dtype=float32`).
   - Columns: `[x, y, z, v_x, v_y, v_z, mass, yaw, pitch, active_flag]`
2. **Graphics Engine**: 
   - Strictly Modern OpenGL (VAOs, VBOs). No legacy `glBegin`/`glEnd`.
   - Uses `trimesh` along with PIL (`Image`) to dynamically parse embedded `.glb` model textures and send them to the renderer as `GL_TEXTURE_2D`.
3. **Camera System**:
   - 3rd-Person Orbit Camera.
   - Smooth trailing using a "Spring Arm" interpolation.
4. **Graphical User Interface (GUI)**:
   - Utilizes `imgui` (Dear PyGui) overlaid on top of the GLFW OpenGL context.
   - Tied to `core/settings.py` for dynamic global variables (e.g., `MOUSE_SENSITIVITY`).

## File Structure
- `main.py`: Entry point, windowing (GLFW), GUI logic (`imgui`), and game loop.
- `core/settings.py`: Global configuration state memory.
- `physics/state.py`: Global Master State Matrix and raw vectorized operations.
- `graphics/camera.py`: View Matrix generation and 3rd-person controls.
- `graphics/renderer.py`: OpenGL state, VAO/VBO creation, draw calls, texture mapping, and GLSL shaders.
