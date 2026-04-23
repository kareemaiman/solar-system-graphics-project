import glfw
from OpenGL.GL import *
import glm
import numpy as np
import sys
import imgui
import math
from imgui.integrations.glfw import GlfwRenderer

from physics.state import PhysicsState
from physics.engine import detect_collisions
from graphics.camera import ThirdPersonCamera
from graphics.renderer import MultiMeshRenderer, SphereRenderer, InstancedRenderer, EffectRenderer, SpaceDustRenderer, RingRenderer, BackgroundRenderer
from graphics.frustum import Frustum
from core.logger import logger
from core.settings import Settings
from core.data_manager import DataManager
from core.metadata import EntityMetadata, MetadataManager
from core.audio import AudioManager
from core.input import InputHandler
from gameplay.weapons import MissileSystem
from gameplay.scanner import ScannerSystem
from gameplay.ui import UIManager

class Engine:
    def __init__(self):
        self.game_config = DataManager.load_config()
        Settings.MOUSE_SENSITIVITY = self.game_config["engine"]["mouse_sensitivity_default"]
        Settings.SIMULATION_SPEED = self.game_config["engine"]["simulation_speed_default"]
        
        self.window = None
        self.impl = None
        self.ui = None
        self.input_handler = None
        
        self.window_width = 1280
        self.window_height = 720
        self.delta_time = 0.0
        self.last_frame_time = 0.0

    def init_window(self):
        if not glfw.init():
            logger.error("Failed to initialize GLFW")
            return False

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

        monitor = glfw.get_primary_monitor()
        mode = glfw.get_video_mode(monitor)
        self.window = glfw.create_window(mode.size.width, mode.size.height, "AetherBound", monitor, None)
        if not self.window:
            glfw.terminate()
            return False

        glfw.make_context_current(self.window)
        self.window_width, self.window_height = mode.size.width, mode.size.height
        glViewport(0, 0, self.window_width, self.window_height)
        
        imgui.create_context()
        self.impl = GlfwRenderer(self.window)
        self.ui = UIManager(self.window_width, self.window_height)
        
        self.cloud_renderer = SphereRenderer("assets/textures/clouds.png", radius=1.0)
        return True

    def run(self):
        if not self.init_window():
            return False
            
        bg_renderer = BackgroundRenderer("assets/backdrop.png")
        
        # --- SIMULATION INITIALIZATION ---
        physics_state = PhysicsState(max_bodies=2000)
        metadata_manager = MetadataManager()
        
        self.ui.draw_loading_screen("Initializing Graphics Subsystems...", 0.1, bg_renderer)
        self.impl.render(imgui.get_draw_data())
        glfw.swap_buffers(self.window)
        
        AudioManager.init()
        missile_system = MissileSystem(physics_state, metadata_manager)
        missile_system.missile_speed = self.game_config["weapons"]["missile_speed"]
        missile_system.missile_lifetime = self.game_config["weapons"]["missile_lifetime"]
        missile_system.missile_damage = self.game_config["weapons"]["missile_damage"]
        missile_system.missile_radius = self.game_config["weapons"]["missile_radius"]
        
        scanner_system = ScannerSystem(physics_state, metadata_manager, config=self.game_config)
        
        init_data = DataManager.load_initial_state()
        gravity_constant = self.game_config["engine"]["gravity_constant"]
            
        spaceship_data = init_data["spaceship"]
        ship_stats = self.game_config["spaceship"]
        spaceship_id = physics_state.add_body(
            position=spaceship_data["position"], 
            velocity=spaceship_data["velocity"], 
            mass=ship_stats["mass"], 
            radius=ship_stats["radius"]
        )
        metadata_manager.add_entity(spaceship_id, EntityMetadata(spaceship_data["name"], spaceship_data["type"], ship_stats["mass"], durability=ship_stats["durability"]))
        physics_state.immune_indices.append(spaceship_id)

        celestial_ids = {} 
        celestial_renderers = {} 
        
        for i, cb in enumerate(init_data["celestial_bodies"]):
            progress = 0.3 + (i / len(init_data["celestial_bodies"])) * 0.4
            self.ui.draw_loading_screen(f"Mapping {cb['name']}...", progress, bg_renderer)
            self.impl.render(imgui.get_draw_data())
            glfw.swap_buffers(self.window)
            
            c_id = physics_state.add_body(cb["position"], cb["velocity"], cb["mass"], cb["radius"])
            metadata_manager.add_entity(c_id, EntityMetadata(
                cb["name"], cb["type"], cb["mass"], 
                durability=cb.get("durability", 100.0), 
                luminosity=cb.get("luminosity", 0.0)
            ))
            celestial_ids[cb["name"]] = c_id
            
            if cb.get("texture", "").endswith(".glb"):
                m_scale = cb.get("model_scale", 1.0)
                renderer = MultiMeshRenderer(cb["texture"], initial_scale=m_scale)
                # Mark as glb renderer
                celestial_renderers[cb["name"]] = (c_id, renderer, cb["radius"], True)
            else:
                renderer = SphereRenderer(cb["texture"], radius=1.0)
                celestial_renderers[cb["name"]] = (c_id, renderer, cb["radius"], False)
            
        sun_id = celestial_ids.get("Sun")
        if sun_id is not None: physics_state.fixed_indices.append(sun_id)
            
        asteroid_list = DataManager.generate_asteroids(init_data["asteroid_belt"])
        AST_START = physics_state.add_body(asteroid_list[0]["position"], asteroid_list[0]["velocity"], asteroid_list[0]["mass"], asteroid_list[0]["mass"] * 0.8)
        metadata_manager.add_entity(AST_START, EntityMetadata(asteroid_list[0]["name"], asteroid_list[0]["type"], asteroid_list[0]["mass"]))
        
        for ast in asteroid_list[1:]:
            rad = ast["mass"] * 0.8
            a_id = physics_state.add_body(ast["position"], ast["velocity"], ast["mass"], rad)
            metadata_manager.add_entity(a_id, EntityMetadata(ast["name"], ast["type"], ast["mass"]))
        AST_END = AST_START + len(asteroid_list)

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        
        ship_renderer = MultiMeshRenderer(ship_stats["model_path"], initial_scale=ship_stats["model_scale"], is_ship=True) 
        missile_renderer = MultiMeshRenderer(self.game_config["weapons"]["missile_model_path"], initial_scale=self.game_config["weapons"]["missile_scale"], is_missile=True)
        skybox_renderer = SphereRenderer("assets/textures/2k_stars_milky_way.jpg", radius=400.0, is_skybox=True)
        saturn_ring_renderer = RingRenderer("assets/textures/2k_saturn_ring_alpha.png")
        asteroid_renderer = InstancedRenderer("assets/models/Rock1.glb", is_glb=True, base_radius=1.0)
        effect_renderer = EffectRenderer()
        effect_renderer.explosion_max_radius = self.game_config["effects"]["explosion_max_radius"]
        effect_renderer.explosion_expansion_speed = self.game_config["effects"]["explosion_expansion_speed"]
        dust_renderer = SpaceDustRenderer(num_particles=2000)
        frustum = Frustum()

        camera = ThirdPersonCamera(target_pos=spaceship_data["position"], distance=ship_stats["camera_distance"])
        cb_state = {'first_mouse': True, 'last_x': self.window_width / 2.0, 'last_y': self.window_height / 2.0}
        self.input_handler = InputHandler(self.window, camera, cb_state)

        accumulator = 0.0
        fixed_dt = self.game_config["engine"]["fixed_dt"]
        last_time = glfw.get_time()
        current_frame = 0 
        game_over = False
        game_started = False 
        impact_registry = {} # {id: [[pos, force], ...]}
        headlights_on = False
        g_pressed_last = False
        last_fire_time = 0.0

        while not glfw.window_should_close(self.window):
            current_time = glfw.get_time()
            self.delta_time = current_time - last_time
            self.delta_time = min(self.delta_time, 0.1)
            last_time = current_time
            
            # Ensure ship_world_pos is always available for rendering
            ship_world_pos = physics_state.matrix[spaceship_id, 0:3]
            ship_current_pos = physics_state.matrix[spaceship_id, 0:3]
            camera.update(ship_current_pos, self.delta_time)
            
            # Camera and Front Vector calculation
            cam_dist = camera.distance
            offset_x = cam_dist * math.cos(camera.pitch) * math.sin(camera.yaw)
            offset_y = cam_dist * math.sin(camera.pitch)
            offset_z = cam_dist * math.cos(camera.pitch) * math.cos(camera.yaw)
            camera_offset = glm.vec3(offset_x, offset_y, offset_z)
            
            front = -np.array([offset_x, offset_y, offset_z], dtype=np.float32)
            front /= (np.linalg.norm(front) + 1e-6)
            
            up_world = np.array([0.0, 1.0, 0.0], dtype=np.float32)
            right = np.cross(front, up_world)
            right_len = np.linalg.norm(right)
            if right_len > 0.001: right /= right_len
            else: right = np.array([1.0, 0.0, 0.0], dtype=np.float32)
            up = np.cross(right, front)

            if game_started and not game_over: current_frame += 1
            accumulator += self.delta_time

            glfw.poll_events()
            self.impl.process_inputs()
            imgui.new_frame()
            
            should_restart = False
            if game_over:
                glfw.set_input_mode(self.window, glfw.CURSOR, glfw.CURSOR_NORMAL)
                restart, exit_btn = self.ui.draw_game_over()
                if restart:
                    logger.info("Restart requested by user.")
                    should_restart = True
                if exit_btn:
                    glfw.set_window_should_close(self.window, True)
            elif not game_started:
                glfw.set_input_mode(self.window, glfw.CURSOR, glfw.CURSOR_NORMAL)
                start, quit_btn = self.ui.draw_welcome_screen()
                if start or glfw.get_key(self.window, glfw.KEY_ENTER) == glfw.PRESS:
                    game_started = True
                    accumulator = 0.0
                    glfw.set_input_mode(self.window, glfw.CURSOR, glfw.CURSOR_DISABLED)
                    logger.info("Game started.")
                if quit_btn: glfw.set_window_should_close(self.window, True)
            elif Settings.IS_PAUSED:
                res = self.ui.draw_pause_menu(self.game_config)
                if res:
                    resume, quit_game = res
                    if resume:
                        Settings.IS_PAUSED = False
                        glfw.set_input_mode(self.window, glfw.CURSOR, glfw.CURSOR_DISABLED)
                        cb_state['first_mouse'] = True
                    if quit_game:
                        glfw.set_window_should_close(self.window, True)
            else:
                # Headlights toggle
                g_key = glfw.get_key(self.window, glfw.KEY_G)
                if g_key == glfw.PRESS and not g_pressed_last:
                    headlights_on = not headlights_on
                    AudioManager.play("scanner", volume_mult=0.5)
                g_pressed_last = (g_key == glfw.PRESS)

                if glfw.get_mouse_button(self.window, glfw.MOUSE_BUTTON_LEFT) == glfw.PRESS:
                    ship_pos = physics_state.matrix[spaceship_id, 0:3]
                    # Target selection logic
                    target_id = None
                    min_score = 1000.0 
                    active_mask = physics_state.get_active_mask()
                    for b_id in range(len(active_mask)):
                        if b_id == spaceship_id or not active_mask[b_id]: continue
                        b_pos = physics_state.matrix[b_id, 0:3]
                        to_b = b_pos - ship_pos
                        dist = np.linalg.norm(to_b)
                        if dist > 0.001:
                            to_b_norm = to_b / dist
                            angle = np.arccos(np.clip(np.dot(to_b_norm, front), -1.0, 1.0))
                            score = angle * (1.0 + dist * 0.01)
                            if score < min_score:
                                min_score = score
                                target_id = b_id
                    if current_time - last_fire_time > 0.2:
                        ship_vel = physics_state.matrix[spaceship_id, 3:6]
                        missile_system.fire(ship_pos, front, current_time, 
                                           yaw=camera.yaw, pitch=camera.pitch, 
                                           target_id=target_id,
                                           ship_velocity=ship_vel)
                        last_fire_time = current_time
                
                if glfw.get_mouse_button(self.window, glfw.MOUSE_BUTTON_RIGHT) == glfw.PRESS:
                    scanner_system.trigger(current_frame)

                while accumulator >= fixed_dt:
                    self.input_handler.process_ship_input(physics_state, spaceship_id, front, right, up, thrust_power=ship_stats["thrust_power"])
                    physics_state.apply_gravity(fixed_dt * Settings.SIMULATION_SPEED, G=gravity_constant)
                    
                    cols = detect_collisions(physics_state.matrix, physics_state.get_active_mask(), physics_state.radii)
                    for a_id, b_id in cols:
                        if spaceship_id == a_id or spaceship_id == b_id:
                            other_id = b_id if spaceship_id == a_id else a_id
                            if other_id not in missile_system.active_missiles:
                                game_over = True
                                logger.info(f"Game Over! Collision between ship and body {other_id}")
                                AudioManager.play("crash")
                                break
                        
                        m_id, obj_id = None, None
                        if a_id in missile_system.active_missiles: m_id, obj_id = a_id, b_id
                        elif b_id in missile_system.active_missiles: m_id, obj_id = b_id, a_id
                        
                        if m_id is not None:
                            obj_meta = metadata_manager.get_entity(obj_id)
                            missile_system.remove_missile(m_id)
                            if obj_meta:
                                obj_meta.durability -= missile_system.missile_damage
                                impact_pos_world = physics_state.matrix[m_id, 0:3].copy()
                                if obj_meta.durability <= 0:
                                    # Destroyed: 30x the planet's radius
                                    radius = physics_state.radii[obj_id]
                                    exp_max = self.game_config["effects"]["explosion_max_radius"]
                                    scale_m = (30.0 * radius) / exp_max
                                    effect_renderer.trigger_explosion(impact_pos_world, current_frame, self.game_config, scale_mult=scale_m)
                                    
                                    physics_state.delete_body(obj_id)
                                    metadata_manager.remove_entity(obj_id)
                                    # Prevent ID reuse from respawning the planet
                                    if obj_meta.name in celestial_renderers:
                                        del celestial_renderers[obj_meta.name]
                                    if obj_id in impact_registry:
                                        del impact_registry[obj_id]
                                    AudioManager.play("explosion", volume_mult=1.0)
                                    logger.info(f"Entity {obj_id} ({obj_meta.name}) destroyed.")
                                else:
                                    # Not destroyed: 0.25x the planet's radius
                                    radius = physics_state.radii[obj_id]
                                    exp_max = self.game_config["effects"]["explosion_max_radius"]
                                    scale_m = (0.25 * radius) / exp_max
                                    effect_renderer.trigger_explosion(impact_pos_world, current_frame, self.game_config, scale_mult=scale_m)
                                    
                                    # Calculate Local Impact Vector for sticky craters
                                    impact_world_vec = impact_pos_world - physics_state.matrix[obj_id, 0:3]
                                    angle = current_frame * 0.001 # Current planet rotation
                                    c, s = np.cos(-angle), np.sin(-angle)
                                    # Inverse Y-rotation to move world impact to local space
                                    lx = impact_world_vec[0] * c + impact_world_vec[2] * s
                                    lz = -impact_world_vec[0] * s + impact_world_vec[2] * c
                                    impact_local = np.array([lx, impact_world_vec[1], lz])
                                    
                                    impact_local = impact_local / radius
                                    
                                    impacts = impact_registry.get(obj_id, [])
                                    impacts.append([impact_local, 1.5])
                                    if len(impacts) > 8:
                                        impacts.pop(0)
                                    impact_registry[obj_id] = impacts
                                    
                                    AudioManager.play("explosion", volume_mult=0.4)
                    
                    ship_world_pos = physics_state.matrix[spaceship_id, 0:3]
                    for m_id in list(missile_system.active_missiles.keys()):
                        if np.linalg.norm(physics_state.matrix[m_id, 0:3] - ship_world_pos) > 2000.0:
                            missile_system.remove_missile(m_id)

                    missile_system.update(current_time, fixed_dt)
                    effect_renderer.update_explosions(current_frame)
                    scanner_system.update(current_frame, ship_world_pos)
                    accumulator -= fixed_dt
                
            # Rendering
            curr_w, curr_h = glfw.get_framebuffer_size(self.window)
            if curr_h > 0:
                glViewport(0, 0, curr_w, curr_h)
                projection_matrix = glm.perspective(glm.radians(45.0), curr_w / curr_h, 1.0, 1e14)
                self.window_width, self.window_height = curr_w, curr_h
                self.ui.window_width, self.ui.window_height = curr_w, curr_h
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            view_matrix = glm.lookAt(camera_offset, glm.vec3(0.0), glm.vec3(0.0, 1.0, 0.0))
            cam_pos_f = [float(camera_offset.x), float(camera_offset.y), float(camera_offset.z)]
            
            frustum.update(projection_matrix, view_matrix)
            skybox_renderer.draw([0,0,0], view_matrix, projection_matrix, rotation=current_frame*0.0005, camera_pos=cam_pos_f, config=self.game_config)
            camera_world_pos = ship_world_pos + np.array([offset_x, offset_y, offset_z])
            dust_renderer.draw(view_matrix, projection_matrix, camera_world_pos)

            # Lighting
            lights = []
            for e_id, meta in metadata_manager.metadata_map.items():
                if meta.luminosity > 0 and physics_state.get_active_mask()[e_id]:
                    lights.append({
                        'pos': (physics_state.matrix[e_id, 0:3] - ship_world_pos).astype(np.float32),
                        'color': [1.0, 1.0, 1.0],
                        'intensity': float(meta.luminosity)
                    })
            
            # Headlights logic
            if headlights_on:
                # Calculate forward vector from ship orientation
                # In our engine, forward is +Z or -Z depending on alignment
                # Let's use the camera's forward vector for the lights
                cam_fwd = glm.vec3(*front)
                cam_right = glm.vec3(*right)
                
                # Left headlight (relative to ship at 0,0,0)
                lights.append({
                    'pos': (cam_fwd * 2.0) - (cam_right * 1.5),
                    'color': [1.0, 1.0, 0.9],
                    'intensity': 5.0
                })
                # Right headlight
                lights.append({
                    'pos': (cam_fwd * 2.0) + (cam_right * 1.5),
                    'color': [1.0, 1.0, 0.9],
                    'intensity': 5.0
                })
            # lights.append({'pos': np.array([200, 200, 200], dtype=np.float32), 'color': [0.4, 0.5, 0.7], 'intensity': 10.0})
            
            for r in [ship_renderer, missile_renderer, asteroid_renderer, saturn_ring_renderer]:
                if hasattr(r, 'set_lights'): r.set_lights(lights)
            for _, renderer, _, _ in celestial_renderers.values():
                if hasattr(renderer, 'set_lights'): renderer.set_lights(lights)

            # Draw Celeastial Bodies
            for name, data in celestial_renderers.items():
                b_id, renderer, scale, is_glb = data
                if b_id is not None and physics_state.get_active_mask()[b_id]:
                    pos = physics_state.matrix[b_id, 0:3]
                    rel = (pos - ship_world_pos).astype(np.float32)
                    if frustum.is_sphere_visible(rel, scale):
                        impact = impact_registry.get(b_id, [np.array([0,0,0]), 0.0])
                        rel_impact = impact[0] # This is now passed as LOCAL coordinates
                        
                        meta = metadata_manager.get_entity(b_id)
                        lum = float(meta.luminosity if meta else 0)
                        
                        if is_glb:
                            # MultiMeshRenderer expects yaw/pitch
                            renderer.draw(rel, view_matrix, projection_matrix, yaw=current_frame*0.01, camera_pos=cam_pos_f)
                        else:
                            impacts = impact_registry.get(b_id, [])
                            renderer.draw(rel, view_matrix, projection_matrix, scale=scale, rotation=current_frame*0.001, impacts=impacts, self_luminosity=lum, camera_pos=cam_pos_f, config=self.game_config)
                            if name == "Earth":
                                # Draw Atmospheric Clouds - Add self_luminosity to keep them from going black
                                self.cloud_renderer.draw(rel, view_matrix, projection_matrix, scale=scale*1.02, rotation=current_frame*0.0012, self_luminosity=0.2, camera_pos=cam_pos_f, config=self.game_config)
                            if name == "Saturn": 
                                saturn_ring_renderer.draw(rel, view_matrix, projection_matrix, scale=scale*2.2, camera_pos=cam_pos_f)

            # Draw Missiles, Asteroids, Ship, ISS
            if "ISS" in celestial_ids:
                iss_id = celestial_ids["ISS"]
                iss_rel = (physics_state.matrix[iss_id, 0:3] - ship_world_pos).astype(np.float32)
                # The ISS renderer is stored in celestial_renderers, but we draw it here or in the loop
                pass 
            
            for m_id, m_data in missile_system.missile_data.items():
                m_rel = (physics_state.matrix[m_id, 0:3] - ship_world_pos).astype(np.float32)
                missile_renderer.draw(m_rel, view_matrix, projection_matrix, yaw=m_data["yaw"], pitch=m_data["pitch"], camera_pos=cam_pos_f, config=self.game_config)

            if 'AST_START' in locals():
                mask = physics_state.get_active_mask()[AST_START:AST_END]
                indices = np.where(mask)[0] + AST_START
                if len(indices) > 0:
                    inst_data = np.hstack([(physics_state.matrix[indices, 0:3] - ship_world_pos).astype(np.float32), physics_state.radii[indices].reshape(-1, 1).astype(np.float32)])
                    asteroid_renderer.draw_instanced(view_matrix, projection_matrix, inst_data, camera_pos=cam_pos_f, config=self.game_config)

            ship_renderer.draw([0,0,0], view_matrix, projection_matrix, yaw=camera.yaw, pitch=camera.pitch, camera_pos=cam_pos_f, config=self.game_config)
            if scanner_system.is_active:
                wave_rad, _ = scanner_system.get_wave_params(current_frame)
                effect_renderer.draw_scanner([0,0,0], wave_rad, view_matrix, projection_matrix)
            effect_renderer.draw_explosions(view_matrix, projection_matrix, ship_world_pos, current_frame)

            # UI Overlay
            self.ui.draw_hud(ship_world_pos, np.linalg.norm(physics_state.matrix[spaceship_id, 3:6]))
            ui_target_id = None
            ui_min_score = 10.0
            for b_id in range(len(physics_state.get_active_mask())):
                if b_id == spaceship_id or not physics_state.get_active_mask()[b_id]: continue
                to_b = physics_state.matrix[b_id, 0:3] - ship_world_pos
                dist = np.linalg.norm(to_b)
                if dist > 0.001:
                    score = np.arccos(np.clip(np.dot(to_b/dist, front), -1.0, 1.0)) * (1.0 + dist * 0.01)
                    if score < ui_min_score: ui_min_score = score; ui_target_id = b_id
            if ui_target_id is not None:
                target_meta = metadata_manager.get_entity(ui_target_id)
                if target_meta: self.ui.draw_target_info(target_meta)
            if scanner_system.last_results: self.ui.draw_scanner_results(scanner_system.last_results)

            if should_restart:
                imgui.render()
                self.impl.render(imgui.get_draw_data())
                self.impl.shutdown()
                glfw.terminate()
                return True

            imgui.render()
            self.impl.render(imgui.get_draw_data())
            glfw.swap_buffers(self.window)
            
        self.impl.shutdown()
        glfw.terminate()
        return False
