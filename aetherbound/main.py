import glfw
from OpenGL.GL import *
import glm
import numpy as np
import sys
import imgui
from imgui.integrations.glfw import GlfwRenderer

from physics.state import PhysicsState
from physics.engine import detect_collisions
from graphics.camera import ThirdPersonCamera
from graphics.renderer import MultiMeshRenderer, SphereRenderer, InstancedRenderer
from graphics.frustum import Frustum
from core.settings import Settings
from core.data_manager import DataManager
from core.metadata import EntityMetadata, MetadataManager

window_width = 1280
window_height = 720
delta_time = 0.0
last_frame = 0.0

def key_callback(window, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        Settings.IS_PAUSED = not Settings.IS_PAUSED
        if Settings.IS_PAUSED:
            glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_NORMAL)
        else:
            glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)

def process_input(window, physics_state, camera, spaceship_id):
    # Calculate fully 3D flight directional vector from camera orientation!
    # In Spherical orbiting, the forward look vector is inverse to the camera offset.
    front_x = -np.sin(camera.yaw) * np.cos(camera.pitch)
    front_y = -np.sin(camera.pitch)
    front_z = -np.cos(camera.yaw) * np.cos(camera.pitch)
    
    front = np.array([front_x, front_y, front_z], dtype=np.float32)
    front = front / np.linalg.norm(front) # Ensure unity
    
    up_world = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    right = np.cross(front, up_world)
    right = right / np.linalg.norm(right)
    
    # Real local up vector
    up = np.cross(right, front)
    
    thrust_power = 80.0 * delta_time
    thrust_vec = np.zeros(3, dtype=np.float32)
    
    if glfw.get_key(window, glfw.KEY_W) == glfw.PRESS:
        thrust_vec += front * thrust_power
    if glfw.get_key(window, glfw.KEY_S) == glfw.PRESS:
        thrust_vec -= front * thrust_power
    if glfw.get_key(window, glfw.KEY_A) == glfw.PRESS:
        thrust_vec += right * thrust_power
    if glfw.get_key(window, glfw.KEY_D) == glfw.PRESS:
        thrust_vec -= right * thrust_power
    if glfw.get_key(window, glfw.KEY_SPACE) == glfw.PRESS:
        thrust_vec += up * thrust_power
    if glfw.get_key(window, glfw.KEY_LEFT_SHIFT) == glfw.PRESS:
        thrust_vec -= up * thrust_power
        
    matrix = physics_state.matrix
    matrix[spaceship_id, physics_state.VX : physics_state.VZ + 1] += thrust_vec

def mouse_callback(window, xpos, ypos):
    if Settings.IS_PAUSED:
        return
        
    camera_ptr = glfw.get_window_user_pointer(window)
    if not camera_ptr:
        return
        
    camera, state = camera_ptr
    
    if state['first_mouse']:
        state['last_x'] = xpos
        state['last_y'] = ypos
        state['first_mouse'] = False

    xoffset = xpos - state['last_x']
    yoffset = state['last_y'] - ypos

    state['last_x'] = xpos
    state['last_y'] = ypos
    camera.process_mouse_movement(xoffset, yoffset, sensitivity=Settings.MOUSE_SENSITIVITY)

def scroll_callback(window, xoffset, yoffset):
    if Settings.IS_PAUSED:
        return
    camera_ptr = glfw.get_window_user_pointer(window)
    if not camera_ptr:
        return
    camera, _ = camera_ptr
    camera.process_scroll(yoffset)

def main():
    global delta_time, last_frame, window_width, window_height
    
    if not glfw.init():
        print("Failed to initialize GLFW")
        return

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

    window = glfw.create_window(window_width, window_height, "AetherBound", None, None)
    if not window:
        glfw.terminate()
        return

    glfw.make_context_current(window)
    imgui.create_context()
    impl = GlfwRenderer(window)
    glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)

    # --- SIMULATION INITIALIZATION ---
    physics_state = PhysicsState(max_bodies=2000)
    metadata_manager = MetadataManager()
    
    try:
        init_data = DataManager.load_initial_state()
    except FileNotFoundError as e:
        print(f"Failed to load data: {e}")
        return
        
    spaceship_data = init_data["spaceship"]
    spaceship_pos = spaceship_data["position"]
    spaceship_id = physics_state.add_body(position=spaceship_pos, velocity=spaceship_data["velocity"], mass=spaceship_data["mass"], radius=1.0)
    metadata_manager.add_entity(spaceship_id, EntityMetadata(spaceship_data["name"], spaceship_data["type"], spaceship_data["mass"]))

    celestial_ids = []
    celestial_radii = [18.0, 2.5, 8.0]
    for i, cb in enumerate(init_data["celestial_bodies"]):
        rad = celestial_radii[i] if i < len(celestial_radii) else 2.0
        c_id = physics_state.add_body(position=cb["position"], velocity=cb["velocity"], mass=cb["mass"], radius=rad)
        metadata_manager.add_entity(c_id, EntityMetadata(cb["name"], cb["type"], cb["mass"]))
        
    if len(init_data["celestial_bodies"]) >= 3:
        # Assuming Sun, Earth, Jupiter based on config
        sun_id = 1
        earth_id = 2
        jupiter_id = 3
    else:
        sun_id, earth_id, jupiter_id = 1, 2, 3
        
    physics_state.fixed_indices.append(sun_id)
    """
    AST_START = len(init_data["celestial_bodies"]) + 1 
    asteroid_list = DataManager.generate_asteroids(init_data["asteroid_belt"])
    for ast in asteroid_list:
        rad = ast["mass"] * 0.8
        a_id = physics_state.add_body(position=ast["position"], velocity=ast["velocity"], mass=ast["mass"], radius=rad)
        metadata_manager.add_entity(a_id, EntityMetadata(ast["name"], ast["type"], ast["mass"]))
    AST_END = AST_START + len(asteroid_list)
"""
    # --- GRAPHICS PIPELINE & TEXTURES ---
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_CULL_FACE)
    
    print("Loading textures and GPU Buffers...")
    ship_renderer = MultiMeshRenderer("assets/models/the_orville.glb", initial_scale=0.6) # scale tuned down
    skybox_renderer = SphereRenderer("assets/textures/2k_stars_milky_way.jpg", radius=400.0, is_skybox=True)
    sun_renderer = SphereRenderer("assets/textures/2k_sun.jpg", radius=1.0)
    earth_renderer = SphereRenderer("assets/textures/2k_earth_daymap.jpg", radius=1.0)
    jupiter_renderer = SphereRenderer("assets/textures/2k_jupiter.jpg", radius=1.0)
    asteroid_renderer = InstancedRenderer("assets/models/Rock1.glb", is_glb=True, base_radius=1.0)
    # The rock texture is bound inside the GLB model material, but Asteroid shader defaults to it

    frustum = Frustum()

    # --- CAMERA & CALLBACK SETUP ---
    camera = ThirdPersonCamera(target_pos=spaceship_pos, distance=10.0)
    cb_state = {'first_mouse': True, 'last_x': window_width / 2.0, 'last_y': window_height / 2.0}
    
    glfw.set_window_user_pointer(window, (camera, cb_state))
    glfw.set_cursor_pos_callback(window, mouse_callback)
    glfw.set_scroll_callback(window, scroll_callback)
    glfw.set_key_callback(window, key_callback)

    # --- RENDER LOOP ---
    accumulator = 0.0
    fixed_dt = 1.0 / 60.0
    game_over = False
    
    while not glfw.window_should_close(window):
        current_frame = glfw.get_time()
        delta_time = current_frame - last_frame
        last_frame = current_frame
        
        accumulator += delta_time

        glfw.poll_events()
        impl.process_inputs()
        imgui.new_frame()
        
        if game_over:
            # Render "YOU DIED" Screen
            glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_NORMAL)
            center_x, center_y = window_width / 2.0, window_height / 2.0
            
            imgui.set_next_window_position(center_x, center_y, imgui.ALWAYS, pivot_x=0.5, pivot_y=0.5)
            imgui.begin("GAME OVER", flags=imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_MOVE)
            
            # Use red text
            imgui.push_style_color(imgui.COLOR_TEXT, 1.0, 0.0, 0.0, 1.0)
            imgui.set_window_font_scale(3.0)
            imgui.text("YOU DIED")
            imgui.pop_style_color()
            
            imgui.set_window_font_scale(1.0)
            if imgui.button("Exit"):
                glfw.set_window_should_close(window, True)
                
            imgui.end()

        elif Settings.IS_PAUSED:
            imgui.begin("AetherBound Config", True)
            changed, new_sens = imgui.slider_float(
                "Mouse Sensitivity", Settings.MOUSE_SENSITIVITY,
                min_value=0.0001, max_value=0.015, format="%.4f"
            )
            if changed:
                Settings.MOUSE_SENSITIVITY = new_sens
            if imgui.button("Resume (ESC)"):
                Settings.IS_PAUSED = False
                glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)
                cb_state['first_mouse'] = True
            imgui.end()
        else:
            # Draw Crosshair in ImGui
            draw_list = imgui.get_background_draw_list()
            center_x, center_y = window_width / 2.0, window_height / 2.0
            crosshair_size = 10.0
            draw_list.add_line(center_x - crosshair_size, center_y, center_x + crosshair_size, center_y, imgui.get_color_u32_rgba(1, 1, 1, 0.8), 2.0)
            draw_list.add_line(center_x, center_y - crosshair_size, center_x, center_y + crosshair_size, imgui.get_color_u32_rgba(1, 1, 1, 0.8), 2.0)

            while accumulator >= fixed_dt:
                process_input(window, physics_state, camera, spaceship_id)
                # Physics ticked
                physics_state.apply_gravity(fixed_dt, G=1.0)
                
                # Check collisions
                cols = detect_collisions(physics_state.matrix, physics_state.get_active_mask(), physics_state.radii)
                for c in cols:
                    if spaceship_id in c:
                        game_over = True
                        break
                        
                accumulator -= fixed_dt
                
            # Follow ship
            ship_current_pos = physics_state.matrix[spaceship_id, physics_state.X : physics_state.Z + 1]
            camera.update(ship_current_pos, delta_time)

        # Maintain Aspect Ratio & Viewport
        curr_width, curr_height = glfw.get_framebuffer_size(window)
        if curr_height > 0:
            glViewport(0, 0, curr_width, curr_height)
            projection_matrix = glm.perspective(glm.radians(45.0), curr_width / curr_height, 0.1, 2000.0)
            window_width, window_height = curr_width, curr_height
        else:
            projection_matrix = glm.mat4(1.0)

        # Clear Buffer
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        view_matrix = camera.get_view_matrix()
        
        # Update frustum for culling
        frustum.update(projection_matrix, view_matrix)
        
        # 1. Skybox
        skybox_renderer.draw([0,0,0], view_matrix, projection_matrix, scale=1.0, rotation=current_frame*0.01)
        
        # 2. Celestial Spheres
        pos_sun = physics_state.matrix[sun_id, physics_state.X : physics_state.Z + 1]
        if frustum.is_sphere_visible(pos_sun, 18.0):
            sun_renderer.draw(pos_sun, view_matrix, projection_matrix, scale=18.0, rotation=current_frame*0.5)
        
        pos_earth = physics_state.matrix[earth_id, physics_state.X : physics_state.Z + 1]
        if frustum.is_sphere_visible(pos_earth, 2.5):
            earth_renderer.draw(pos_earth, view_matrix, projection_matrix, scale=2.5, rotation=current_frame)
        
        pos_jupiter = physics_state.matrix[jupiter_id, physics_state.X : physics_state.Z + 1]
        if frustum.is_sphere_visible(pos_jupiter, 8.0):
            jupiter_renderer.draw(pos_jupiter, view_matrix, projection_matrix, scale=8.0, rotation=current_frame*0.2)
        
        # 3. Asteroid Instancing
        """
        asteroid_matrix = physics_state.matrix[AST_START : AST_END]
        if len(asteroid_matrix) > 0:
            visible_asteroids = []
            for ast in asteroid_matrix:
                rad = ast[physics_state.MASS] * 0.8
                if frustum.is_sphere_visible(ast[0:3], rad):
                    visible_asteroids.append([ast[0], ast[1], ast[2], rad])
            
            if visible_asteroids:
                inst_data = np.array(visible_asteroids, dtype=np.float32)
                asteroid_renderer.draw_instanced(view_matrix, projection_matrix, inst_data)
            """
        # 4. Spaceship 
        ship_current_pos = physics_state.matrix[spaceship_id, physics_state.X : physics_state.Z + 1]
        ship_renderer.draw(ship_current_pos, view_matrix, projection_matrix, yaw=camera.yaw, pitch=camera.pitch)

        imgui.render()
        impl.render(imgui.get_draw_data())

        glfw.swap_buffers(window)
        
    impl.shutdown()
    glfw.terminate()

if __name__ == '__main__':
    main()
