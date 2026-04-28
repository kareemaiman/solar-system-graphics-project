import imgui # Immediate Mode GUI library
import numpy as np # Used for coordinate processing
from core.settings import Settings # Global engine settings

class UIManager:
    """Orchestrates the 2D interface using Dear ImGui.
    Handles the HUD, menus, loading screens, and debug overlays.

    Args:

    Returns:

    """
    def __init__(self, window_width, window_height):
        self.window_width = window_width
        self.window_height = window_height

    def draw_loading_screen(self, text, progress, bg_renderer=None):
        """Displays a splash screen with a progress bar.

        Args:
          text(str): Subtitle describing the current step.
          progress(float): 0.0 to 1.0 value.
          bg_renderer: Optional 3D background to render behind the UI.
        References: (Default value = None)
          bg_renderer: Optional 3D background to render behind the UI.
        References:
        - OpenGL.GL (glClear) (Default value = None)
          bg_renderer: Optional 3D background to render behind the UI.
        References:
        - OpenGL.GL (glClear)
        - imgui.progress_bar (Default value = None)

        Returns:

        """
        from OpenGL.GL import GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, glClear
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        if bg_renderer:
            bg_renderer.draw()
        imgui.new_frame()
        imgui.set_next_window_position(self.window_width/2, self.window_height/2, pivot_x=0.5, pivot_y=0.5)
        imgui.set_next_window_size(400, 150)
        imgui.begin("Loading", flags=imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_MOVE)
        
        text_width = imgui.calc_text_size("AETHERBOUND").x
        imgui.set_cursor_pos_x((400 - text_width) / 2)
        imgui.text_colored("AETHERBOUND", 0.4, 0.7, 1.0, 1.0)
        imgui.separator()
        imgui.spacing()
        
        imgui.text(text)
        imgui.progress_bar(progress, size=(380, 20))
        imgui.end()
        imgui.render()

    def draw_game_over(self):
        """Renders the failure screen with restart/exit options.

        Args:

        Returns:
          tuple: (restart_clicked, exit_clicked)

        """
        center_x, center_y = self.window_width / 2.0, self.window_height / 2.0
        imgui.set_next_window_position(center_x, center_y, imgui.ALWAYS, pivot_x=0.5, pivot_y=0.5)
        imgui.begin("GAME OVER", flags=imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_MOVE)
        
        imgui.push_style_color(imgui.COLOR_TEXT, 1.0, 0.0, 0.0, 1.0)
        imgui.set_window_font_scale(3.0)
        imgui.text("YOU DIED")
        imgui.pop_style_color()
        
        imgui.set_window_font_scale(1.0)
        restart = imgui.button("Restart")
        exit_game = imgui.button("Exit")
        imgui.end()
        return restart, exit_game

    def draw_welcome_screen(self):
        """Renders the initial splash/tutorial screen.

        Args:

        Returns:
          tuple: (start_clicked, quit_clicked)

        """
        imgui.set_next_window_position(self.window_width / 2, self.window_height / 2, pivot_x=0.5, pivot_y=0.5)
        imgui.begin("AetherBound Welcome", flags=imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE)
        imgui.set_window_font_scale(2.5)
        imgui.text("AETHERBOUND")
        imgui.set_window_font_scale(1.0)
        imgui.text("Explore the cosmos. Fire with Left Click. Scan with Right Click.")
        imgui.spacing()
        start = imgui.button("START JOURNEY (ENTER)")
        quit_game = imgui.button("QUIT")
        imgui.end()
        return start, quit_game

    def draw_pause_menu(self, game_config):
        """Renders the configuration and pause menu.
        Allows real-time tweaking of MOUSE_SENSITIVITY and SIMULATION_SPEED.

        Args:
          game_config: Dictionary containing engine max limits.

        Returns:

        """
        imgui.begin("AetherBound Config", True)
        changed, new_sens = imgui.slider_float(
            "Mouse Sensitivity", Settings.MOUSE_SENSITIVITY,
            min_value=0.0001, max_value=0.015, format="%.4f"
        )
        if changed:
            Settings.MOUSE_SENSITIVITY = new_sens
        
        changed_speed, new_speed = imgui.slider_float(
            "Simulation Speed", Settings.SIMULATION_SPEED,
            min_value=0.0, max_value=game_config["engine"]["simulation_speed_max"], format="%.2fx"
        )
        if changed_speed:
            Settings.SIMULATION_SPEED = new_speed
            
        resume = imgui.button("Resume (ESC)")
        restart = imgui.button("Restart Game")
        quit_game = imgui.button("Quit Game")
        imgui.end()
        return resume, restart, quit_game

    def draw_hud(self, ship_world_pos, ship_speed):
        """Renders the main gameplay overlay (telemetry and crosshair).
        
        Math (Crosshair):
            Calculates screen center = (width/2, height/2)
            Draws lines +/- 10 pixels from center.

        Args:
          ship_world_pos: 3D coordinates from PhysicsState.
          ship_speed: Magnitude of velocity vector.

        Returns:

        """
        imgui.set_next_window_position(10, 10, imgui.ONCE)
        imgui.begin("Telemetry", flags=imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_ALWAYS_AUTO_RESIZE | imgui.WINDOW_NO_BACKGROUND)
        imgui.text(f"SHIP COORDS: X={ship_world_pos[0]:.1f} Y={ship_world_pos[1]:.1f} Z={ship_world_pos[2]:.1f}")
        imgui.text(f"SPEED: {ship_speed:.1f}")
        imgui.end()

        # Crosshair Rendering
        # Uses the low-level ImGui draw list to draw primitive lines on top of the scene.
        draw_list = imgui.get_background_draw_list()
        cx, cy = self.window_width / 2, self.window_height / 2
        draw_list.add_line(cx - 10, cy, cx + 10, cy, imgui.get_color_u32_rgba(0, 1, 0, 1), 2)
        draw_list.add_line(cx, cy - 10, cx, cy + 10, imgui.get_color_u32_rgba(0, 1, 0, 1), 2)

    def draw_target_info(self, meta):
        """Displays details about the currently locked target.
        
        Math:
            health_pct = current_durability / max_reference
            Determines the color (Red to Green) of the health bar.

        Args:
          meta: EntityMetadata object.

        Returns:

        """
        imgui.set_next_window_position(self.window_width - 250, 50, imgui.ALWAYS)
        imgui.begin("Target Info", flags=imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_ALWAYS_AUTO_RESIZE)
        imgui.text(f"TARGET: {meta.name.upper()}")
        imgui.text(f"TYPE: {meta.entity_type}")
        
        max_ref = 100.0 # Could be more dynamic
        health_pct = max(0.0, meta.durability / max_ref) if max_ref > 0 else 0
        imgui.text(f"DURABILITY: {int(meta.durability)}")
        imgui.push_style_color(imgui.COLOR_PLOT_HISTOGRAM, 1.0 - health_pct, health_pct, 0.0, 1.0)
        imgui.progress_bar(health_pct, size=(200, 15))
        imgui.pop_style_color()
        imgui.end()

    def draw_scanner_results(self, last_results):
        """Renders a scrollable list of entities detected by the scanner.

        Args:
          last_results(list): List of dictionaries from ScannerSystem.

        Returns:

        """
        imgui.set_next_window_position(self.window_width - 280, 150, imgui.ONCE)
        imgui.begin("Scanner Results", True)
        if not last_results:
            imgui.text("No objects in range.")
        for res in last_results:
            meta = res["meta"]
            imgui.text_colored(f"[{meta.entity_type}] {meta.name}", 0.4, 0.7, 1.0, 1.0)
            imgui.text(f"Dist: {res['dist']:.1f} | Speed: {res['speed']:.1f}")
            imgui.text(f"Mass: {res['mass']:.2e} | HP: {int(meta.durability)}")
            imgui.separator()
        imgui.end()
