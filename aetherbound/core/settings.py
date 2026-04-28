class Settings:
    """Global configuration state accessible throughout AetherBound.
     Static repository for runtime configuration state.
     Values here can be modified by the UI and are read by physics/rendering loops.

    Args:

    Returns:

    """
    MOUSE_SENSITIVITY = 0.005 # Factor for turning speed
    IS_PAUSED = False # Gameplay freeze state
    SIMULATION_SPEED = 0.1 # Delta-time multiplier
    # Audio Settings
    AUDIO_ENABLED = True
    MASTER_VOLUME = 0.5
