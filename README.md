# AetherBound - Technical Documentation

## Overview
AetherBound is a 3D space simulation built with Python, Modern OpenGL, and Data-Oriented Design principles. It features a vectorized N-body gravity physics engine, a procedural asteroid belt, homing missiles, dynamic destruction, and a customized graphics pipeline.

---

## Full Detailed File Structure & Functionalities

### Root Directory
- **`run.py`**: The primary launch wrapper. It ensures all dependencies from `requirements.txt` are met (auto-installing/recovering them if necessary) before starting `main.py`.
- **`main.py`**: The main entry point. Manages the high-level application lifecycle and handles the seamless restart loop if the user restarts the game from the UI.
- **`requirements.txt`**: List of Python dependencies (e.g., `glfw`, `PyOpenGL`, `numpy`, `imgui[glfw]`, `PyGLM`).
- **`imgui.ini`**: Auto-generated ImGui layout and window configuration.
- **`scratch_scale.py`**: Prototyping/scratchpad script.

### `core/` - System and Utilities
- **`settings.py`**: Global configuration flags and runtime state variables (e.g., `IS_PAUSED`, `SIMULATION_SPEED`).
- **`input.py`**: Centralized GLFW input handling, converting keyboard/mouse inputs into spaceship control vectors.
- **`data_manager.py`**: Handles loading, saving, and parsing JSON configurations (`game_config.json`, `initial_state.json`) and procedurally generating asteroid data.
- **`logger.py`**: Centralized logging system to output debug and error messages to the console and `logs/` directory.
- **`metadata.py`**: Manages non-physics entity data (e.g., name, type, durability, luminosity) via `MetadataManager`.
- **`audio.py`**: `AudioManager` singleton for loading and playing sound effects using pygame's mixer.

### `gameplay/` - Game Logic and UI
- **`engine.py`**: The core simulation and render loop. It glues together the graphics pipeline, physics engine, user input, and UI. It handles game states (loading, main menu, pause menu, game over).
- **`ui.py`**: Contains `UIManager`, which uses ImGui to draw the HUD, target information, scanner results, menus, and loading screens.
- **`weapons.py`**: Implements the `MissileSystem`, handling homing logic, missile lifecycle, and velocity inheritance.
- **`scanner.py`**: Implements the `ScannerSystem` for proximity detection, revealing entity data within a certain radius.

### `graphics/` - Rendering Pipeline
- **`camera.py`**: Implements a `ThirdPersonCamera` with spring-arm orbit behavior, following the spaceship.
- **`frustum.py`**: View frustum culling logic to avoid rendering objects outside the camera's view.
- **`renderer.py`**: Proxy module that imports and re-exports specific renderers for cleaner imports.
- **`shaders.py`**: Stores all GLSL shader source strings (vertex and fragment shaders) for meshes, spheres, instancing, and effects.
- **`shapes.py`**: Generates base geometry (vertices, normals, UVs) for primitives like spheres and quads.
- **`renderers/`**:
  - **`mesh.py`**: `MultiMeshRenderer` for rendering 3D `.glb` models (spaceship, missiles).
  - **`celestial.py`**: Renderers for spheres and rings. Handles shader-based planets with features like craters, impacts, and self-luminosity.
  - **`instanced.py`**: `InstancedRenderer` for efficiently rendering thousands of asteroids in a single draw call.
  - **`effects.py`**: `EffectRenderer` for procedural visuals like scanner waves and noise-based explosions.
  - **`environment.py`**: Renderers for space dust particles and static background loading screens.

### `physics/` - Physics Engine
- **`state.py`**: `PhysicsState` manages a large, vectorized NumPy matrix holding the position, velocity, and properties of all bodies for data-oriented processing.
- **`engine.py`**: Proxy module re-exporting gravity and collision logic.
- **`gravity.py`**: Vectorized N-body gravity calculations using NumPy for performance.
- **`collision.py`**: Sphere-to-sphere collision detection returning overlapping pairs.

### `data/` - Configuration Files
- **`game_config.json`**: Tuneable parameters for engine speed, weapons, effects, and spaceship stats.
- **`initial_state.json`**: Defines the initial setup: positions, velocities, masses, and textures of celestial bodies and the asteroid belt constraints.

### `assets/` - Media Resources
- Contains subdirectories: **`models/`** (.glb files), **`textures/`** (.png, .jpg), **`sounds/`** (.wav, .ogg), and **`icons/`**. Includes `backdrop.png` for menus.

---

## User Guide

### How to Start
Run the application using the wrapper script from your terminal:
```bash
python run.py
```
This will ensure all required libraries are installed before launching the game window.

### Basic Mechanics
- **Exploration:** You pilot a spaceship in a star system filled with planets, a sun, and an asteroid belt. The physics are governed by N-body gravity, meaning all celestial bodies and asteroids pull on each other and the ship.
- **Combat & Destruction:** You can fire homing missiles at targeted planets or asteroids. Collisions (from ship or missiles) will reduce a celestial body's durability. Minor damage creates visible, persistent craters. If durability drops to zero, the body explodes spectacularly.
- **Crashing:** Colliding your spaceship directly into a planet, asteroid, or the ISS will result in a Game Over.
- **Scanning:** You can trigger a scanner to emit a visible wave. Any celestial body or asteroid hit by the wave will have its data (distance, mass, etc.) displayed on your HUD.

### Controls
| Input | Action |
| --- | --- |
| **W, A, S, D** | Move the spaceship (Forward, Left, Backward, Right relative to camera) |
| **Space / Shift** | Move Up / Down |
| **Mouse Movement** | Rotate camera around the spaceship |
| **Mouse Scroll Wheel** | Zoom camera in and out |
| **Left Mouse Click** | Fire a homing missile at the closest target near the center crosshair |
| **Right Mouse Click** | Trigger the scanner ping |
| **G** | Toggle spaceship headlights |
| **ESC** | Open Pause Menu / Settings |

### Functionalities & Features
- **Homing Missiles:** The targeting system automatically acquires the object closest to the center of your screen. Fired missiles inherit the ship's velocity and smoothly track the target.
- **Headlights:** Toggleable dynamic headlights (G key) help you see in the dark side of planets or deep space.
- **Dynamic Craters & Explosions:** Impacts leave dark craters on celestial bodies. The shader handles coordinate transformation so craters stick to the rotating planet. Total destruction triggers a procedural, noise-based explosion effect.
- **Robust Restart:** You can restart the simulation directly from the game-over screen or pause menu, cleanly resetting the physics state and graphics context.
