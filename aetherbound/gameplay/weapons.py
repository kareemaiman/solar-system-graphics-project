import numpy as np
from core.audio import AudioManager

class MissileSystem:
    """
    Manages the lifecycle of projectiles.
    Projectiles are active bodies in the PhysicsState that expire over time
    or on collision.
    """
    def __init__(self, physics_state, metadata_manager):
        self.physics_state = physics_state
        self.metadata_manager = metadata_manager
        self.active_missiles = {} # missile_id -> expiration_time
        
        self.missile_speed = 150.0
        self.missile_lifetime = 8.0 # increased lifetime
        self.missile_mass = 0.01
        self.missile_radius = 0.2
        self.missile_damage = 25.0
        self.missile_data = {} # missile_id -> {expiry, yaw, pitch, target_id}

    def fire(self, spawn_pos, direction, current_time, yaw=0, pitch=0, target_id=None, ship_velocity=None):
        """
        Spawns a new missile body in the physics simulation.
        """
        velocity = direction * self.missile_speed
        if ship_velocity is not None:
            velocity += ship_velocity
        
        # Offset spawn position in front of the ship
        pos = np.array(spawn_pos) + direction * 10.0
        
        try:
            m_id = self.physics_state.add_body(
                position=pos,
                velocity=velocity,
                mass=self.missile_mass,
                radius=self.missile_radius
            )
            self.active_missiles[m_id] = current_time + self.missile_lifetime
            self.missile_data[m_id] = {"yaw": yaw, "pitch": pitch, "target_id": target_id}
            
            from core.metadata import EntityMetadata
            self.metadata_manager.add_entity(m_id, EntityMetadata("Homing-Missile", "Projectile", self.missile_mass))
            
            AudioManager.play("missile", volume_mult=0.6)
            return m_id
        except MemoryError:
            return None

    def _lerp_angle(self, a, b, t):
        d = b - a
        while d > np.pi: d -= 2 * np.pi
        while d < -np.pi: d += 2 * np.pi
        return a + d * t

    def update(self, current_time, fixed_dt=1.0/60.0):
        """
        Updates missile positions for homing logic.
        """
        expired = [m_id for m_id, expiry in self.active_missiles.items() if current_time > expiry]
        for m_id in expired:
            self.remove_missile(m_id)
            
        # Homing Logic
        for m_id, data in self.missile_data.items():
            t_id = data.get("target_id")
            if t_id is not None and self.physics_state.get_active_mask()[t_id]:
                m_pos = self.physics_state.matrix[m_id, 0:3]
                t_pos = self.physics_state.matrix[t_id, 0:3]
                
                # Steer toward target
                desired_dir = t_pos - m_pos
                dist = np.linalg.norm(desired_dir)
                if dist > 0.1:
                    desired_dir /= dist
                    curr_vel = self.physics_state.matrix[m_id, 3:6]
                    
                    # Steering strength (increased for better homing)
                    steer_strength = 5.0
                    steer = (desired_dir * self.missile_speed - curr_vel) * steer_strength
                    self.physics_state.matrix[m_id, 3:6] += steer * fixed_dt
            
            # Update visual orientation (gradually align with velocity)
            new_vel = self.physics_state.matrix[m_id, 3:6]
            vel_norm = np.linalg.norm(new_vel)
            if vel_norm > 0.001:
                v = new_vel / vel_norm
                # Align with camera convention: front = (-sin yaw, -sin pitch, -cos yaw)
                target_yaw = np.arctan2(-v[0], -v[2])
                target_pitch = np.arcsin(-v[1])
                
                # Smoothly interpolate from spawn orientation to travel orientation
                lerp_factor = 0.08 
                data["yaw"] = self._lerp_angle(data["yaw"], target_yaw, lerp_factor)
                data["pitch"] = self._lerp_angle(data["pitch"], target_pitch, lerp_factor)

    def remove_missile(self, m_id):
        if m_id in self.active_missiles:
            self.physics_state.delete_body(m_id)
            del self.active_missiles[m_id]
            if m_id in self.missile_data:
                del self.missile_data[m_id]

    def get_missile_data(self, m_id):
        return self.missile_data.get(m_id, {"yaw": 0, "pitch": 0, "target_id": None})
