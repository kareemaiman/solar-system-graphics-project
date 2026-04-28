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
| **ESC** | Open Pause Menu / Settings (Resets on Game Restart) |

### Functionalities & Features
- **Homing Missiles:** The targeting system automatically acquires the object closest to the center of your screen. Fired missiles inherit the ship's velocity and smoothly track the target.
- **Headlights:** Toggleable dynamic headlights (G key) help you see in the dark side of planets or deep space.
- **Dynamic Craters & Explosions:** Impacts leave dark craters on celestial bodies. The engine supports up to 32 persistent craters per body. The shader handles coordinate transformation so craters stick to the rotating planet. Total destruction triggers a procedural, noise-based explosion effect.
- **Robust Restart:** You can restart the simulation directly from the game-over screen or pause menu. The engine uses a persistent iterative loop in `main.py` to cleanly recreate the physics and graphics contexts, ensuring a fresh state on every restart without memory leaks or recursion.
- **Weapon & Scanner Tuning:** Missiles have a configurable active limit to prevent spam, and the scanner uses real-time seconds for its wave animation and proximity query.
- **Orbital Stability:** The physics engine is balanced around a gravitational constant where $G \cdot M_{sun} = 1,000,000$. The Sun's mass is fixed at $1,000,000.0$ in `initial_state.json` to ensure stable Keplerian orbits for the planets and the ISS.

## Data Flow
The core data flow in AetherBound follows a Data-Oriented Design. Data is loaded from `game_config.json` and `initial_state.json` via `data_manager.py`. It is stored in flat arrays within `PhysicsState` for vectorized processing by `gravity.py` and `collision.py`. In the main loop (`engine.py`), inputs are read via `input.py`, physics vectors are updated, and then the graphics components (`renderer.py` and `ui.py`) consume the state arrays to draw the frame.

## Detailed Function & Class Reference

### main.py
- **Function `main`**: The persistent Application Loop.

### run.py
- **Function `install_requirements`**: Ensures all third-party libraries are installed before the engine starts.

### core/audio.py
- **Class `AudioManager`**: Singleton manager for the game's audio subsystem.
  - **Method `init`**: Initializes the Pygame mixer and pre-loads all sound assets.
  - **Method `_load_assets`**: Scans the assets directory and binds audio files to internal keys.
  - **Method `play`**: Triggers a sound effect.
  - **Method `stop_all`**: No docstring provided.

### core/data_manager.py
- **Class `DataManager`**: Handles persistence and data generation for the AetherBound engine.
  - **Method `load_initial_state`**: Parses the starting conditions for all celestial bodies from a JSON file.
  - **Method `load_config`**: Loads engine-level tunables like simulation speed, weapon damage, and G.
  - **Method `generate_asteroids`**: Procedurally generates a ring of asteroids around the sun.

### core/input.py
- **Class `InputHandler`**: Bridges GLFW input events to engine systems (Camera, Spaceship).
  - **Method `__init__`**: Binds input listeners to the GLFW window.
  - **Method `key_callback`**: Handles discrete key presses (e.g., ESC for pause).
  - **Method `mouse_callback`**: Handles continuous mouse movement for camera orbiting.
  - **Method `scroll_callback`**: Args:
  - **Method `process_ship_input`**: Translates WASD/Space/Ctrl into physical velocity in the simulation.

### core/logger.py
- **Function `setup_logger`**: Configures a dual-output logger for the engine.

### core/metadata.py
- **Class `EntityMetadata`**: A container for non-physical properties of a game object.
  - **Method `__init__`**: Initializes metadata for a celestial body or projectile.
- **Class `MetadataManager`**: Registry that maps Physics IDs (matrix indices) to EntityMetadata objects.
  - **Method `__init__`**: No docstring provided.
  - **Method `add_entity`**: Registers a new metadata entry.
  - **Method `get_entity`**: Retrieves metadata by ID.
  - **Method `remove_entity`**: Cleans up metadata when an entity is destroyed.
  - **Method `clear`**: No docstring provided.

### gameplay/engine.py
- **Class `Engine`**: The central coordinator of the AetherBound simulation.
  - **Method `__init__`**: No docstring provided.
  - **Method `init_window`**: Initializes the GLFW window and OpenGL context.
  - **Method `run`**: The Main Game Loop.

### gameplay/scanner.py
- **Class `ScannerSystem`**: Handles proximity scanning of entities.
  - **Method `__init__`**: Initializes the scanner with configurable range and duration.
  - **Method `trigger`**: Starts a scan sequence.
  - **Method `update`**: Manages the scan timer.
  - **Method `_perform_query`**: Vectorized-ish search for entities within range.
  - **Method `get_wave_params`**: Calculates parameters for the GPU shader to draw the expanding sphere.

### gameplay/ui.py
- **Class `UIManager`**: Orchestrates the 2D interface using Dear ImGui.
  - **Method `__init__`**: No docstring provided.
  - **Method `draw_loading_screen`**: Displays a splash screen with a progress bar.
  - **Method `draw_game_over`**: Renders the failure screen with restart/exit options.
  - **Method `draw_welcome_screen`**: Renders the initial splash/tutorial screen.
  - **Method `draw_pause_menu`**: Renders the configuration and pause menu.
  - **Method `draw_hud`**: Renders the main gameplay overlay (telemetry and crosshair).
  - **Method `draw_target_info`**: Displays details about the currently locked target.
  - **Method `draw_scanner_results`**: Renders a scrollable list of entities detected by the scanner.

### gameplay/weapons.py
- **Class `MissileSystem`**: Manages the lifecycle of projectiles.
  - **Method `__init__`**: Initializes the weapon system.
  - **Method `fire`**: Spawns a new missile body in the physics simulation.
  - **Method `_lerp_angle`**: Linear interpolation between two angles, accounting for 2*PI wrap-around.
  - **Method `update`**: Updates missile positions for homing logic.
  - **Method `remove_missile`**: Deactivates a missile and cleans up its data.
  - **Method `get_missile_data`**: Args:

### graphics/camera.py
- **Class `ThirdPersonCamera`**: 3rd-Person Orbit Camera with 'Spring Arm' following effect.
  - **Method `__init__`**: Initializes the camera state.
  - **Method `_update_actual_position`**: Calculates the camera's Cartesian world coordinates based on the target position
  - **Method `process_mouse_movement`**: Updates the orbit angles based on raw mouse delta input.
  - **Method `process_scroll`**: Increases or decreases the orbit radius (Distance).
  - **Method `update`**: Updates the camera's anchor point to match a moving entity (the spaceship).
  - **Method `get_view_matrix`**: Generates the 4x4 View Matrix required by shaders.

### graphics/frustum.py
- **Class `Frustum`**: Implements View-Frustum Culling to skip rendering objects outside the camera view.
  - **Method `__init__`**: No docstring provided.
  - **Method `update`**: Extracts the 6 frustum planes (Left, Right, Bottom, Top, Near, Far)
  - **Method `is_sphere_visible`**: Checks if a bounding sphere is within the visible volume.

### graphics/shapes.py
- **Function `generate_uv_sphere`**: Procedurally constructs a 3D unit sphere returning explicit arrays mapping

### graphics/models/glb_loader.py
- **Class `GLBLoader`**: No docstring provided.
  - **Method `load`**: Loads a GLB and returns a list of Mesh objects to support multi-mesh GLBs.

### graphics/models/mesh.py
- **Class `Mesh`**: No docstring provided.
  - **Method `__init__`**: No docstring provided.
  - **Method `_build_vbo`**: No docstring provided.
  - **Method `draw`**: No docstring provided.

### graphics/primitives/ring.py
- **Function `create_ring_mesh`**: Generates a flat disc mesh for planetary rings.

### graphics/primitives/sphere.py
- **Function `create_sphere_mesh`**: Generates a UV-mapped sphere mesh.
- **Function `load_texture`**: Loads an image file into an OpenGL texture handle using PIL.

### graphics/renderers/celestial.py
- **Class `SphereRenderer`**: Specialized renderer for planets, stars, and skyboxes.
  - **Method `__init__`**: Initializes the sphere mesh and compiles the standard celestial shader.
  - **Method `set_lights`**: Uploads lighting information to the GPU.
  - **Method `draw`**: Performs the OpenGL draw call for the celestial body.
- **Class `RingRenderer`**: Renders planetary rings (like Saturn's) using a flattened disk primitive.
  - **Method `__init__`**: No docstring provided.
  - **Method `set_lights`**: Args:
  - **Method `draw`**: Renders the ring disk.

### graphics/renderers/effects.py
- **Class `EffectRenderer`**: Renders specialized procedural effects like the Scanner Wave and Explosions.
  - **Method `__init__`**: Initializes shaders and pre-loads a sphere mesh shared by all effects.
  - **Method `draw_scanner`**: Renders the holographic radar wave.
  - **Method `trigger_explosion`**: Adds a new explosion instance to the simulation.
  - **Method `update_explosions`**: Updates the radius of all active explosions.
  - **Method `draw_explosions`**: Batch-renders all active explosions.

### graphics/renderers/environment.py
- **Class `SpaceDustRenderer`**: Renders floating 'space dust' particles around the camera.
  - **Method `__init__`**: Generates a cloud of random points.
  - **Method `draw`**: Renders particles as OpenGL Points.
- **Class `BackgroundRenderer`**: Renders a static 2D image covering the entire screen (Loading screen background).
  - **Method `__init__`**: No docstring provided.
  - **Method `draw`**: Renders a screen-space quad.

### graphics/renderers/instanced.py
- **Class `InstancedRenderer`**: High-performance renderer for drawing thousands of similar objects (Asteroids).
  - **Method `__init__`**: Initializes the geometry and sets up the instance VBO.
  - **Method `set_lights`**: Args:
  - **Method `draw_instanced`**: Executes the instanced draw call.

### graphics/renderers/mesh.py
- **Class `MultiMeshRenderer`**: General-purpose renderer for complex 3D models (GLB format).
  - **Method `__init__`**: Loads 3D model data from a GLB file.
  - **Method `set_lights`**: Updates global lighting uniforms.
  - **Method `draw`**: Renders all meshes in the model hierarchy.

### physics/collision.py
- **Function `detect_collisions`**: Vectorized sphere-to-sphere collision detection.

### physics/gravity.py
- **Function `update_physics`**: Performs a single step of N-Body gravitational simulation using vectorized NumPy operations.

### physics/state.py
- **Class `PhysicsState`**: Master Registry for all physical entities in the simulation.
  - **Method `__init__`**: Allocates the contiguous memory block for the simulation state.
  - **Method `add_body`**: Spawns a new entity by finding the first available slot in the matrix.
  - **Method `delete_body`**: Logically removes an entity from the simulation.
  - **Method `get_active_mask`**: Generates a boolean mask array of all entities where ACTIVE == 1.0.
  - **Method `get_active_bodies`**: Returns an N x 10 view of only the currently active bodies.
  - **Method `apply_gravity`**: Delegate method that calls the optimized gravity solver.