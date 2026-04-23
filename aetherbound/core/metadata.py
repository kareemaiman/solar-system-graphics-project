class EntityMetadata:
    def __init__(self, name, entity_type, mass, volume=1.0, density=1.0, 
                 abundant_element="Unknown", durability=100.0, luminosity=0):
        self.name = name
        self.entity_type = entity_type # planet, star, asteroid, ship, moon
        self.mass = mass
        self.volume = volume
        self.density = density
        self.abundant_element = abundant_element
        self.luminosity = luminosity # 0 = no light, >0 = brightness
        
        # Physical dynamic vectors mapping
        self.acceleration = [0.0, 0.0, 0.0]
        self.velocity = [0.0, 0.0, 0.0]
        self.position = [0.0, 0.0, 0.0]
        
        self.angular_velocity = [0.0, 0.0, 0.0]
        self.angular_acceleration = [0.0, 0.0, 0.0]
        self.angular_momentum = [0.0, 0.0, 0.0]
        
        self.friction_index = 0.0
        self.durability = durability

class MetadataManager:
    def __init__(self):
        self.metadata_map = {}
        
    def add_entity(self, entity_id, metadata: EntityMetadata):
        self.metadata_map[entity_id] = metadata
        
    def get_entity(self, entity_id) -> EntityMetadata:
        return self.metadata_map.get(entity_id)
        
    def remove_entity(self, entity_id):
        if entity_id in self.metadata_map:
            del self.metadata_map[entity_id]

    def clear(self):
        self.metadata_map.clear()
