import json
import math

G = 1.0
M_sun = 20000.0

bodies = [
    ("Sun", 20000.0, 0.0),
    ("Mercury", 1.0, 23.22),
    ("Venus", 4.0, 43.38),
    ("Earth", 5.0, 60.0),
    ("Mars", 2.0, 91.44),
    ("Jupiter", 30.0, 312.24),
    ("Saturn", 20.0, 574.92),
    ("Uranus", 10.0, 1152.06),
    ("Neptune", 10.0, 1802.82)
]

data = {
    "constants": {
        "G": 1.0,
        "description": "Idealized units to fit float32 limits. 1 AU = 60 units."
    },
    "celestial_bodies": [],
    "spaceship": {
        "name": "The Orville",
        "type": "ship",
        "mass": 1.0,
        "position": [62.0, 0.0, 2.0],
        "velocity": [0.0, 0.0, -18.257]
    },
    "asteroid_belt": {
        "count": 2000,
        "radius_min": 120.0,
        "radius_max": 280.0,
        "y_variance": 5.0,
        "vy_variance": 0.6,
        "mass_min": 0.1,
        "mass_max": 1.5,
        "seed": 42,
        "note": "Between Mars and Jupiter."
    }
}

for name, mass, r in bodies:
    if r == 0.0:
        pos = [0.0, 0.0, 0.0]
        vel = [0.0, 0.0, 0.0]
        typ = "star"
    else:
        v = math.sqrt(G * M_sun / r)
        pos = [r, 0.0, 0.0]
        vel = [0.0, 0.0, -v]
        typ = "planet"
    data["celestial_bodies"].append({
        "name": name,
        "type": typ,
        "mass": mass,
        "position": pos,
        "velocity": vel
    })

with open("data/initial_state.json", "w") as f:
    json.dump(data, f, indent=2)

print("Updated data/initial_state.json")
