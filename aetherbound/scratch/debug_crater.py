import numpy as np
import json

def debug_crater_math(ship_pos, planet_pos, impact_world_pos, radius_mult):
    rel = planet_pos - ship_pos
    impact_local = impact_world_pos - planet_pos
    rel_impact = rel + impact_local
    
    print(f"Ship Pos: {ship_pos}")
    print(f"Planet Pos: {planet_pos}")
    print(f"Impact World Pos: {impact_world_pos}")
    print(f"Planet-Ship Vector (rel): {rel}")
    print(f"Impact Local Offset: {impact_local}")
    print(f"Impact-Ship Vector (rel_impact): {rel_impact}")
    
    # Simulate shader
    # world_pos in shader is relative to ship
    # Let's test a point on the planet surface near impact
    test_point_world = impact_world_pos + np.array([0.1, 0, 0])
    test_point_shader = test_point_world - ship_pos
    
    dist_to_impact = np.linalg.norm(test_point_shader - rel_impact)
    print(f"Distance in shader: {dist_to_impact}")
    
    impact_force = 1.5
    crater_radius = impact_force * radius_mult
    print(f"Crater Radius: {crater_radius}")
    
    if dist_to_impact < crater_radius:
        print("Point is INSIDE crater (Working)")
    else:
        print("Point is OUTSIDE crater (Not working as intended if it should be inside)")

if __name__ == "__main__":
    with open("data/game_config.json", "r") as f:
        config = json.load(f)
    
    ship_pos = np.array([0, 0, 0])
    planet_pos = np.array([150, 0, 0])
    impact_world_pos = np.array([147, 0, 0]) # On surface of planet with radius 3
    
    debug_crater_math(ship_pos, planet_pos, impact_world_pos, config["craters"]["radius_mult"])
