import glfw
import numpy as np
from core.settings import Settings

class InputHandler:
    def __init__(self, window, camera, cb_state):
        self.window = window
        self.camera = camera
        self.cb_state = cb_state
        
        glfw.set_window_user_pointer(window, (camera, cb_state))
        glfw.set_key_callback(window, self.key_callback)
        glfw.set_cursor_pos_callback(window, self.mouse_callback)
        glfw.set_scroll_callback(window, self.scroll_callback)

    @staticmethod
    def key_callback(window, key, scancode, action, mods):
        if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
            Settings.IS_PAUSED = not Settings.IS_PAUSED
            if Settings.IS_PAUSED:
                glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_NORMAL)
            else:
                glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)

    @staticmethod
    def mouse_callback(window, xpos, ypos):
        if Settings.IS_PAUSED:
            return
            
        ptr = glfw.get_window_user_pointer(window)
        if not ptr: return
        camera, state = ptr
        
        if state['first_mouse']:
            state['last_x'] = xpos
            state['last_y'] = ypos
            state['first_mouse'] = False

        xoffset = xpos - state['last_x']
        yoffset = state['last_y'] - ypos
        state['last_x'] = xpos
        state['last_y'] = ypos
        
        camera.process_mouse_movement(xoffset, yoffset, sensitivity=Settings.MOUSE_SENSITIVITY)

    @staticmethod
    def scroll_callback(window, xoffset, yoffset):
        if Settings.IS_PAUSED:
            return
        ptr = glfw.get_window_user_pointer(window)
        if not ptr: return
        camera, _ = ptr
        camera.process_scroll(yoffset)

    def process_ship_input(self, physics_state, spaceship_id, front, right, up, thrust_power=200.0):
        thrust_vec = np.zeros(3, dtype=np.float32)
        any_pressed = False
        
        # Speed Boost Modifier
        current_thrust = thrust_power
        if glfw.get_key(self.window, glfw.KEY_LEFT_SHIFT) == glfw.PRESS:
            current_thrust *= 3.0  # 3x boost
        
        if glfw.get_key(self.window, glfw.KEY_W) == glfw.PRESS:
            thrust_vec += front
            any_pressed = True
        if glfw.get_key(self.window, glfw.KEY_S) == glfw.PRESS:
            thrust_vec -= front
            any_pressed = True
        if glfw.get_key(self.window, glfw.KEY_A) == glfw.PRESS:
            thrust_vec += right
            any_pressed = True
        if glfw.get_key(self.window, glfw.KEY_D) == glfw.PRESS:
            thrust_vec -= right
            any_pressed = True
        if glfw.get_key(self.window, glfw.KEY_SPACE) == glfw.PRESS:
            thrust_vec += up
            any_pressed = True
        if glfw.get_key(self.window, glfw.KEY_LEFT_CONTROL) == glfw.PRESS:
            thrust_vec -= up
            any_pressed = True
            
        if not any_pressed:
            physics_state.matrix[spaceship_id, 3:6] = 0.0
        else:
            length = np.linalg.norm(thrust_vec)
            if length > 0:
                thrust_vec = (thrust_vec / length) * current_thrust
            physics_state.matrix[spaceship_id, 3:6] = thrust_vec
