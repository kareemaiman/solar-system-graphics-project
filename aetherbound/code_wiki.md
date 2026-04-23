# AetherBound 3D Space Explorer - Code Wiki

## Overview
AetherBound is a high-performance 3D space exploration simulation built with Modern OpenGL, Python, and PyGLM. The architectural focus is on Data-Oriented Design (DOD) to minimize Python's interpreter overhead in favor of bulk NumPy processing.

## Architecture Guidelines
1. **Data-Oriented Physics (Master State Matrix)**: 
   - All physics entities exist in a single global `N x 10` NumPy array (`dtype=float32`).
   - Columns: `[x, y, z, v_x, v_y, v_z, mass, yaw, pitch, active_flag]`
2. **Metadata Entity System**:
   - Every physical entity is mapped to an extensive metadata dictionary containing 14+ attributes (density, name, abundant element, angular momentum, friction, durability, etc.).
3. **Graphics Engine**: 
   - Strictly Modern OpenGL (VAOs, VBOs).
   - Distributed rendering system with separate modules for GLB meshes, procedural primitives (spheres), and custom shaders.
   - Dynamic Frustum Culling and Render Distance limits.
   - Procedural shader-based crater systems for collision deformation.
4. **Camera System**:
   - 3rd-Person Orbit Camera strictly locked to ship orientation.
5. **Gameplay Systems**:
   - Weaponry (Missiles) using physical projectile entities.
   - Scanning system utilizing world-space wave animations and metadata retrieval.
   - Multi-layered audio system via `pygame`.

## File Structure
- `main.py`: Entry point, decoupled physics/render loops, and state management.
- `core/settings.py`: Global configuration state memory.
- `core/metadata.py`: Management of the 14-attribute entity metadata.
- `core/audio.py`: Pygame-based sound trigger engine.
- `physics/engine.py`: Vectorized N-Body gravity and collision math.
- `physics/state.py`: Global Master State Matrix management.
- `graphics/renderer.py`: Master rendering coordinator.
- `graphics/models/`: GLB loading and multi-mesh rendering (Ship, ISS, Rock, Missile).
- `graphics/primitives/`: Procedural sphere generation for celestial bodies.
- `graphics/shaders.py`: GLSL shader programs (including procedural craters).
- `graphics/frustum.py`: Mathematical culling logic.
- `gameplay/`: Modules for weapons and scanning logic.
- `assets/`: Organized structure (models, sounds, textures, icons).
