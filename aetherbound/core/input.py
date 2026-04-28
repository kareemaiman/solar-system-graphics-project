import glfw # GLFW bindings for window events and raw input
import numpy as np # Vector math for movement vectors
from core.settings import Settings # Global pause and sensitivity states

class InputHandler:
    """Bridges GLFW input events to engine systems (Camera, Spaceship).
    Manages callbacks for mouse, keyboard, and scroll wheel.

    Args:

    Returns:

    """
    def __init__(self, window, camera, cb_state):
        """
        Binds input listeners to the GLFW window.
        
        Args:
            window: The active GLFW window context.
            camera: Reference to the ThirdPersonCamera.
            cb_state: Mutable dictionary for tracking mouse state.
        """
        self.window = window
        self.camera = camera
        self.cb_state = cb_state
        
        glfw.set_window_user_pointer(window, (camera, cb_state))
        glfw.set_key_callback(window, self.key_callback)
        glfw.set_cursor_pos_callback(window, self.mouse_callback)
        glfw.set_scroll_callback(window, self.scroll_callback)

    @staticmethod
    def key_callback(window, key, scancode, action, mods):
        """Handles discrete key presses (e.g., ESC for pause).
        
        Logic:
            Toggles Settings.IS_PAUSED and switches cursor modes.

        Args:
          window: 
          key: 
          scancode: 
          action: 
          mods: 

        Returns:

        """
        if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
            Settings.IS_PAUSED = not Settings.IS_PAUSED
            if Settings.IS_PAUSED:
                glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_NORMAL)
            else:
                glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)

    @staticmethod
    def mouse_callback(window, xpos, ypos):
        """Handles continuous mouse movement for camera orbiting.
        
        Math:
            delta = current_pos - last_pos

        Args:
          window: 
          xpos: 
          ypos: 

        Returns:

        """
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
        """

        Args:
          window: 
          xoffset: 
          yoffset: 

        Returns:

        """
        if Settings.IS_PAUSED:
            return
        ptr = glfw.get_window_user_pointer(window)
        if not ptr: return
        camera, _ = ptr
        camera.process_scroll(yoffset)

    def process_ship_input(self, physics_state, spaceship_id, front, right, up, thrust_power=200.0):
        """Translates WASD/Space/Ctrl into physical velocity in the simulation.
        
        Math:
            Velocity_Vector = sum(Pressed_Key_Direction_Vectors)
            Normalized_Velocity = Velocity_Vector.normalize() * Thrust_Power

        Args:
          front, right, up: Camera-relative direction vectors.
          thrust_power(float, optional): Units per second speed. (Default value = 200.0)
          physics_state: 
          spaceship_id: 
          front: 
          right: 
          up: 

        Returns:

        """
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
            # Stop instantly if no keys are pressed (Arcade-style physics)
            physics_state.matrix[spaceship_id, 3:6] = 0.0
        else:
            length = np.linalg.norm(thrust_vec)
            if length > 0:
                thrust_vec = (thrust_vec / length) * current_thrust
            physics_state.matrix[spaceship_id, 3:6] = thrust_vec
