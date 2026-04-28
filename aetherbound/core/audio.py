import pygame # Used for cross-platform audio mixing and playback
import os # Standard filesystem access
from .settings import Settings # Global audio volume toggles

class AudioManager:
    """Singleton manager for the game's audio subsystem.
    Encapsulates Pygame Mixer to provide layered sound effects (SFX)
    without blocking the main simulation thread.

    Args:

    Returns:

    """
    _sounds = {}
    _initialized = False

    @classmethod
    def init(cls):
        """Initializes the Pygame mixer and pre-loads all sound assets.
        
        References:
            - pygame.mixer.init()

        Args:

        Returns:

        """
        if not Settings.AUDIO_ENABLED:
            return
        
        try:
            pygame.mixer.init()
            cls._initialized = True
            cls._load_assets()
        except Exception as e:
            print(f"Audio Initialization Failed: {e}")
            cls._initialized = False

    @classmethod
    def _load_assets(cls):
        """Scans the assets directory and binds audio files to internal keys.
        
        Math (Volume):
            Initializes sound volume using the MASTER_VOLUME setting.

        Args:

        Returns:

        """
        sound_dir = "assets/sounds"
        if not os.path.exists(sound_dir):
            return

        # Mapping friendly names to filenames
        mapping = {
            "crash": "dragon-studio-car-crash-sound-376882.mp3",
            "explosion": "dragon-studio-nuclear-explosion-386181.mp3",
            "missile": "freesound_community-missile-blast-2-95177.mp3",
            "scan": "futuristic-scanning-device-jeff-kaale-1-00-04.mp3"
        }

        for key, filename in mapping.items():
            path = os.path.join(sound_dir, filename)
            if os.path.exists(path):
                cls._sounds[key] = pygame.mixer.Sound(path)
                cls._sounds[key].set_volume(Settings.MASTER_VOLUME)

    @classmethod
    def play(cls, sound_name, volume_mult=1.0):
        """Triggers a sound effect.
        
        Math:
            Effective Volume = Master Volume * Instance Multiplier.

        Args:
          sound_name(str): The key (e.g., 'explosion') to play.
          volume_mult(float, optional): Temporary volume adjustment for this instance. (Default value = 1.0)

        Returns:

        """
        if not cls._initialized or not Settings.AUDIO_ENABLED:
            return
        
        if sound_name in cls._sounds:
            sound = cls._sounds[sound_name]
            # Create a channel for layering if needed, but simple play works for SFX
            sound.set_volume(Settings.MASTER_VOLUME * volume_mult)
            sound.play()

    @classmethod
    def stop_all(cls):
        """ """
        if cls._initialized:
            pygame.mixer.stop()
