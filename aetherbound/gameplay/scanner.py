import numpy as np
import glfw
from core.audio import AudioManager
from core.metadata import MetadataManager

class ScannerSystem:
    """
    Handles proximity scanning of entities.
    Triggers a visual radar wave and retrieves metadata for nearby bodies.
    """
    def __init__(self, physics_state, metadata_manager, config=None):
        self.physics_state = physics_state
        self.metadata_manager = metadata_manager
        
        self.is_active = False
        self.scan_start_time = 0.0
        
        # Data-driven values
        self.scan_duration = config["scanner"]["duration"] if config else 2.0
        self.max_range = config["scanner"]["range"] if config else 150.0
        
        self.last_results = [] # List of (entity_id, distance, metadata)

    def trigger(self, current_time):
        if self.is_active:
            return
        
        self.is_active = True
        self.scan_start_time = current_time
        AudioManager.play("scan", volume_mult=0.7)

    def update(self, current_time, ship_pos):
        if not self.is_active:
            return
            
        progress = (current_time - self.scan_start_time) / self.scan_duration
        if progress >= 1.0:
            self.is_active = False
            self._perform_query(ship_pos)
            return

    def _perform_query(self, ship_pos):
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
        """Returns (radius, alpha) for the visual wave shader."""
        if not self.is_active:
            return 0.0, 0.0
            
        progress = (current_time - self.scan_start_time) / self.scan_duration
        return progress * self.max_range, 1.0 - progress
