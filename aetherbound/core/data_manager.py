import json
import os
import numpy as np

class DataManager:
    @staticmethod
    def load_initial_state(filepath="data/initial_state.json"):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Initial state file not found: {filepath}")
        
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        return data
        
    @staticmethod
    def generate_asteroids(config):
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
            
            pos_x = radius * np.cos(angle)
            pos_z = radius * np.sin(angle)
            pos_y = np.random.uniform(-y_var, y_var)
            
            # calculate perfect circular orbital speed v = sqrt(G*M/r) where G*M = 20000.0
            speed = np.sqrt(20000.0 / radius)
            
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
