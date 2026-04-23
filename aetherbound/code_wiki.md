# AetherBound - Technical Documentation

## Overview
AetherBound is a 3D space simulation built with Python and Modern OpenGL. It uses a data-driven architecture and a vectorized N-body physics engine.

## File Structure
- **main.py**: Entry point. Manages the high-level restart loop.
- **core/**
    - **settings.py**: Global configuration and runtime flags.
    - **input.py**: [NEW] Centralized GLFW input handling and ship controls.
    - **data_manager.py**: Handles loading/saving JSON configurations.
    - **logger.py**: Centralized logging system.
- **gameplay/**
    - **engine.py**: [NEW] The core simulation loop and state manager.
    - **ui.py**: [NEW] ImGui-based HUD, menus, and overlays.
    - **weapons.py**: Missile logic and targeting systems.
    - **scanner.py**: Proximity detection and result tracking.
- **graphics/**
    - **camera.py**: 3rd-person spring-arm orbit camera.
    - **renderer.py**: Proxy file re-exporting specific renderers.
    - **renderers/** [NEW]
        - **mesh.py**: Multi-mesh GLB rendering.
        - **celestial.py**: Sphere and Ring rendering with culling fixes.
        - **instanced.py**: Fast rendering for many asteroids.
        - **effects.py**: Procedural scanner waves and noise-based explosions.
        - **environment.py**: Space dust and loading screen backgrounds.
    - **shaders.py**: GLSL shader source strings.
- **physics/**
    - **state.py**: Large NumPy matrix holding all body positions and velocities.
    - **engine.py**: Re-exports gravity and collision logic.
    - **gravity.py**: [NEW] Modularized N-body gravity calculations.
    - **collision.py**: [NEW] Modularized collision detection logic.

## Key Features & Fixes
- **Missile Fix**: Resolved `TypeError` during missile rendering and implemented velocity inheritance.
- **Explosion & Crater Shaders**: Fully data-driven via `game_config.json`. Supports configurable core/edge colors, expansion speed, and crater perturbation.
- **UI Improvements**: Added "Quit Game" button to the ESC pause menu.
- **Dynamic Zoom**: Camera distance can be adjusted via scroll wheel (min: 1.0, max: 200.0).
- **Indestructible Planets**: Celestial bodies have extremely high durability (1M) to prevent accidental destruction by missiles.
- **Inside-Sphere Rendering**: Culling is disabled for planets so they remain visible even if the camera enters the geometry.
- **Robust Restart**: ImGui and GLFW are properly shutdown and re-initialized between sessions to avoid assertion errors.

## Controls
- **WASD / Shift / Space**: Ship Movement.
- **Mouse Left Click**: Fire Homing Missile.
- **Mouse Right Click**: Trigger Scanner.
- **ESC**: Pause Menu / Settings.
- **Restart**: Handled via `gameplay/engine.py` with clean state reset.
