import glfw
from OpenGL.GL import *
import glm
import numpy as np
import sys
import imgui
from imgui.integrations.glfw import GlfwRenderer

from physics.state import PhysicsState
from graphics.camera import ThirdPersonCamera
from graphics.renderer import GLBRenderer, SphereRenderer, InstancedSphereRenderer
from core.settings import Settings

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
    
    thrust_power = 25.0 * delta_time
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
    global delta_time, last_frame
    
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
    
    # 0. Spaceship
    spaceship_pos = [100.0, 0.0, 100.0]
    spaceship_vel = [-15.0, 0.0, 15.0]  
    spaceship_id = physics_state.add_body(position=spaceship_pos, velocity=spaceship_vel, mass=1.0)
    
    # 1. Central massive Sun
    sun_id = physics_state.add_body(position=[0.0, 0.0, 0.0], velocity=[0.0, 0.0, 0.0], mass=20000.0)
    
    # 2. Earth
    v_earth = np.sqrt(20000.0 / 60.0)
    earth_id = physics_state.add_body(position=[60.0, 0.0, 0.0], velocity=[0.0, 0.0, -v_earth], mass=5.0)

    # 3. Jupiter
    v_jupiter = np.sqrt(20000.0 / 150.0)
    jupiter_id = physics_state.add_body(position=[150.0, 0.0, 0.0], velocity=[0.0, 0.0, -v_jupiter], mass=30.0)

    # 4 to 503. Asteroid Belt
    np.random.seed(42)
    AST_START = 4
    AST_END = 504
    for _ in range(500):
        radius = np.random.uniform(200.0, 300.0)
        angle = np.random.uniform(0, 2 * np.pi)
        
        pos_x = radius * np.cos(angle)
        pos_z = radius * np.sin(angle)
        pos_y = np.random.uniform(-6.0, 6.0)
        
        speed = np.sqrt(20000.0 / radius)
        
        vel_x = -speed * np.sin(angle)
        vel_z = speed * np.cos(angle)
        vel_y = np.random.uniform(-0.6, 0.6) 
        
        mass = np.random.uniform(0.5, 4.0)
        physics_state.add_body(position=[pos_x, pos_y, pos_z], velocity=[vel_x, vel_y, vel_z], mass=mass)

    # --- GRAPHICS PIPELINE & TEXTURES ---
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_CULL_FACE)
    
    print("Loading textures and GPU Buffers...")
    ship_renderer = GLBRenderer("assets/the_orville.glb", initial_scale=0.1) # scale tuned down
    skybox_renderer = SphereRenderer("assets/2k_stars_milky_way.jpg", radius=400.0, is_skybox=True)
    sun_renderer = SphereRenderer("assets/2k_sun.jpg", radius=1.0)
    earth_renderer = SphereRenderer("assets/2k_earth_daymap.jpg", radius=1.0)
    jupiter_renderer = SphereRenderer("assets/2k_jupiter.jpg", radius=1.0)
    asteroid_renderer = InstancedSphereRenderer("assets/2k_moon.jpg", base_radius=1.0)

    projection_matrix = glm.perspective(glm.radians(45.0), window_width / window_height, 0.1, 2000.0)

    # --- CAMERA & CALLBACK SETUP ---
    camera = ThirdPersonCamera(target_pos=spaceship_pos, distance=15.0)
    cb_state = {'first_mouse': True, 'last_x': window_width / 2.0, 'last_y': window_height / 2.0}
    
    glfw.set_window_user_pointer(window, (camera, cb_state))
    glfw.set_cursor_pos_callback(window, mouse_callback)
    glfw.set_scroll_callback(window, scroll_callback)
    glfw.set_key_callback(window, key_callback)

    # --- RENDER LOOP ---
    while not glfw.window_should_close(window):
        current_frame = glfw.get_time()
        delta_time = current_frame - last_frame
        last_frame = current_frame

        glfw.poll_events()
        impl.process_inputs()
        imgui.new_frame()
        
        if Settings.IS_PAUSED:
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
            process_input(window, physics_state, camera, spaceship_id)
            # Physics ticked
            physics_state.apply_gravity(delta_time, G=1.0)
            
            # Follow ship
            ship_current_pos = physics_state.matrix[spaceship_id, physics_state.X : physics_state.Z + 1]
            camera.update(ship_current_pos, delta_time)

        # Clear Buffer
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        view_matrix = camera.get_view_matrix()
        
        # 1. Skybox
        skybox_renderer.draw([0,0,0], view_matrix, projection_matrix, scale=1.0, rotation=current_frame*0.01)
        
        # 2. Celestial Spheres
        pos_sun = physics_state.matrix[sun_id, physics_state.X : physics_state.Z + 1]
        sun_renderer.draw(pos_sun, view_matrix, projection_matrix, scale=18.0, rotation=current_frame*0.5)
        
        pos_earth = physics_state.matrix[earth_id, physics_state.X : physics_state.Z + 1]
        earth_renderer.draw(pos_earth, view_matrix, projection_matrix, scale=2.5, rotation=current_frame)
        
        pos_jupiter = physics_state.matrix[jupiter_id, physics_state.X : physics_state.Z + 1]
        jupiter_renderer.draw(pos_jupiter, view_matrix, projection_matrix, scale=8.0, rotation=current_frame*0.2)
        
        # 3. Asteroid Instancing
        asteroid_matrix = physics_state.matrix[AST_START : AST_END]
        if len(asteroid_matrix) > 0:
            # Map X, Y, Z, and visual pseudo-scale (mass*0.8) into N x 4 float array for GPU
            inst_data = np.empty((len(asteroid_matrix), 4), dtype=np.float32)
            inst_data[:, 0:3] = asteroid_matrix[:, 0:3]
            inst_data[:, 3] = asteroid_matrix[:, physics_state.MASS] * 0.8
            asteroid_renderer.draw_instanced(view_matrix, projection_matrix, inst_data)
            
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
