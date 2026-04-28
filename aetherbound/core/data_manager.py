import json
import os
import numpy as np # Used for vectorized math and random generation

class DataManager:
    """Handles persistence and data generation for the AetherBound engine.
    This class bridges the gap between static JSON data and the live simulation state.

    Args:

    Returns:

    """
    
    @staticmethod
    def load_initial_state(filepath="data/initial_state.json"):
        """Parses the starting conditions for all celestial bodies from a JSON file.

        Args:
          filepath(str, optional): Path to the initial state JSON. (Default value = "data/initial_state.json")

        Returns:
          dict: The decoded JSON content containing 'celestial_bodies', 'spaceship', etc.
          References:
          dict: The decoded JSON content containing 'celestial_bodies', 'spaceship', etc.
          References:
          - standard 'json' library for parsing.
          dict: The decoded JSON content containing 'celestial_bodies', 'spaceship', etc.
          References:
          - standard 'json' library for parsing.
          - standard 'os' library for path validation.

        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Initial state file not found: {filepath}")
        
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        return data

    @staticmethod
    def load_config(filepath="data/game_config.json"):
        """Loads engine-level tunables like simulation speed, weapon damage, and G.

        Args:
          filepath(str, optional): Path to the configuration JSON. (Default value = "data/game_config.json")

        Returns:
          dict: The decoded JSON content.

        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Config file not found: {filepath}")
        
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        return data
        
    @staticmethod
    def generate_asteroids(config):
        """Procedurally generates a ring of asteroids around the sun.
        
        Math:
            - Position: Polar to Cartesian conversion.
              x = r * cos(theta), z = r * sin(theta)
            - Orbital Speed: v = sqrt(G*M / r)
              Uses G*M = 1,000,000.0 to match the Sun's mass.
            - Velocity Vector: Perpendicular to the position vector.
              v_x = -v * sin(theta), v_z = v * cos(theta)

        Args:
          config(dict): Asteroid belt constraints (count, radius range, variances).

        Returns:
          list: A list of dictionaries, each representing one asteroid's physical state.
          References:
          list: A list of dictionaries, each representing one asteroid's physical state.
          References:
          - numpy (np.random, np.sin, np.cos, np.sqrt)

        """
        np.random.seed(config.get("seed", 42))
        count = config.get("count", 500)
        radius_min = config.get("radius_min", 200.0)
        radius_max = config.get("radius_max", 300.0)
        y_var = config.get("y_variance", 6.0)
        vy_var = config.get("vy_variance", 0.6)
        mass_min = config.get("mass_min", 0.5)
        mass_max = config.get("mass_max", 4.0)
        
        asteroids = []
        for i in range(count):
            radius = np.random.uniform(radius_min, radius_max)
            angle = np.random.uniform(0, 2 * np.pi)
            
            # Position Calculation (Polar to Cartesian)
            pos_x = radius * np.cos(angle)
            pos_z = radius * np.sin(angle)
            pos_y = np.random.uniform(-y_var, y_var)
            
            # Orbital Mechanics Formula: v = sqrt(G*M/r) 
            # We use 1,000,000.0 as the central mass constant (G*M)
            speed = np.sqrt(1000000.0 / radius)
            
            # Velocity Calculation (Perpendicular tangent vector)
            vel_x = -speed * np.sin(angle)
            vel_z = speed * np.cos(angle)
            vel_y = np.random.uniform(-vy_var, vy_var)
            
            mass = np.random.uniform(mass_min, mass_max)
            
            asteroids.append({
                "name": f"Asteroid_{i}",
                "type": "asteroid",
                "mass": mass,
                "position": [pos_x, pos_y, pos_z],
                "velocity": [vel_x, vel_y, vel_z]
            })
        return asteroids
