import numpy as np
import glfw
from core.audio import AudioManager
from core.metadata import MetadataManager

class ScannerSystem:
    """Handles proximity scanning of entities.
    Triggers a visual radar wave and retrieves metadata for nearby bodies.

    Args:

    Returns:

    """
    def __init__(self, physics_state, metadata_manager, config=None):
        """
        Initializes the scanner with configurable range and duration.
        
        Args:
            physics_state: Reference to the global physics matrix.
            metadata_manager: Registry for entity names and types.
            config: Simulation configuration dictionary.
        """
        self.physics_state = physics_state
        self.metadata_manager = metadata_manager
        
        self.is_active = False
        self.scan_start_time = 0.0
        
        # Data-driven values (tunable in game_config.json)
        self.scan_duration = config["scanner"]["duration"] if config else 2.0
        self.max_range = config["scanner"]["range"] if config else 150.0
        
        self.last_results = [] # List of (entity_id, distance, metadata)

    def trigger(self, current_time):
        """Starts a scan sequence.

        Args:
          current_time(float): The current simulation time in seconds.

        Returns:

        """
        if self.is_active:
            return
        
        self.is_active = True
        self.scan_start_time = current_time
        self.last_results = [] # Clear old results on new scan
        AudioManager.play("scan", volume_mult=0.7)

    def update(self, current_time, ship_pos):
        """Manages the scan timer.
        
        Math:
            Progress = (Now - Start) / Duration
            When Progress reaches 1.0, the actual spatial query is performed.

        Args:
          current_time: 
          ship_pos: 

        Returns:

        """
        if not self.is_active:
            return
            
        progress = (current_time - self.scan_start_time) / self.scan_duration
        if progress >= 1.0:
            self.is_active = False
            self._perform_query(ship_pos)
            return

    def _perform_query(self, ship_pos):
        """Vectorized-ish search for entities within range.
        
        Math:
            dist = sqrt((x1-x2)^2 + (y1-y2)^2 + (z1-z2)^2)
            Filtering condition: dist < max_range

        Args:
          ship_pos(np.array): Origin of the scan.

        Returns:

        """
        self.last_results = []
        mask = self.physics_state.get_active_mask()
        indices = np.where(mask)[0]
        
        for idx in indices:
            pos = self.physics_state.matrix[idx, 0:3]
            dist = np.linalg.norm(pos - ship_pos)
            
            if dist < self.max_range and dist > 1.0: # Ignore self
                meta = self.metadata_manager.get_entity(idx)
                if meta:
                    mass = self.physics_state.matrix[idx, self.physics_state.MASS]
                    vel = self.physics_state.matrix[idx, 3:6]
                    speed = np.linalg.norm(vel)
                    self.last_results.append({
                        "id": idx,
                        "dist": dist,
                        "meta": meta,
                        "mass": mass,
                        "speed": speed
                    })
        
        # Sort by distance
        self.last_results.sort(key=lambda x: x["dist"])

    def get_wave_params(self, current_time):
        """Calculates parameters for the GPU shader to draw the expanding sphere.
        
        Math:
            Radius = Progress * MaxRange
            Alpha (transparency) = 1.0 - Progress (fades out as it expands)

        Args:
          current_time: 

        Returns:
          tuple: (radius, alpha)

        """
        if not self.is_active:
            return 0.0, 0.0
            
        progress = (current_time - self.scan_start_time) / self.scan_duration
        return progress * self.max_range, 1.0 - progress
