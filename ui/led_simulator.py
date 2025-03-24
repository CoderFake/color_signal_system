import pygame
import pygame_gui
import sys
import os
import re
from typing import Dict, List, Any, Tuple, Optional
import time
import math

sys.path.append('..')
from models.light_effect import LightEffect
from config import (
    UI_WIDTH, UI_HEIGHT, UI_BACKGROUND_COLOR, UI_TEXT_COLOR, 
    UI_ACCENT_COLOR, UI_BUTTON_COLOR, DEFAULT_COLOR_PALETTES,
    DEFAULT_FPS, DEFAULT_LED_COUNT
)

class LEDSimulator:
    """
    A class for simulating and visualizing LED lighting effects.
    Provides a GUI to display the LED states and control parameters.
    """
    
    def __init__(self, light_effects: Dict[int, LightEffect], width: int = UI_WIDTH, height: int = UI_HEIGHT):
        """
        Initialize the LED simulator.
        
        Args:
            light_effects: Dictionary mapping effect_ID to LightEffect instances
            width: Width of the window in pixels
            height: Height of the window in pixels
        """
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption("LED Tape Light Simulator")
        

        try:
            icon = pygame.Surface((32, 32))
            icon.fill((60, 120, 240))
            pygame.display.set_icon(icon)
        except:
            pass
        

        theme_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'theme.json')
        if os.path.exists(theme_path):
            self.manager = pygame_gui.UIManager((width, height), theme_path)
        else:
            self.manager = pygame_gui.UIManager((width, height))
            
        self.clock = pygame.time.Clock()
        

        self.light_effects = light_effects
        self.active_effect_id = min(light_effects.keys()) if light_effects else 1
        self.active_segment_id = 1
        

        self.led_size = 8
        self.led_spacing = 1
        self.led_display_height = 40
        

        self.is_playing = True
        self.fps = DEFAULT_FPS
        

        self.zoom_level = 1.0
        self.pan_offset = 0
        self.dragging = False
        self.last_mouse_pos = (0, 0)
        

        self.current_palette = "A"
        self.palettes = DEFAULT_COLOR_PALETTES.copy()
        

        self.top_panel_height = 60
        self.control_panel_width = 300
        self.control_panel_expanded = True
        self.top_panel_expanded = True
        

        self.last_activity_time = time.time()
        self.auto_hide_timeout = 60.0
        

        self.calculate_layout()
        self.setup_ui()
        
    def calculate_layout(self):
        """
        Calculate the positions and sizes of UI elements based on window size.
        """

        top_panel_height = self.top_panel_height if self.top_panel_expanded else 20
        control_panel_width = self.control_panel_width if self.control_panel_expanded else 20
        

        self.top_panel_rect = pygame.Rect(0, 0, self.width, top_panel_height)
        self.control_panel_rect = pygame.Rect(
            self.width - control_panel_width, top_panel_height,
            control_panel_width, self.height - top_panel_height
        )
        self.led_display_rect = pygame.Rect(
            0, top_panel_height,
            self.width - control_panel_width, self.height - top_panel_height
        )
        

        self.led_display_center_y = self.led_display_rect.y + self.led_display_rect.height // 2
        self.effective_led_width = (self.led_size + self.led_spacing) * self.zoom_level
    
    def setup_ui(self):
        """
        Set up the user interface elements.
        """

        self.manager.clear_and_reset()


        toggle_size = 30
        self.top_panel_toggle = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(self.width // 2 - toggle_size // 2, 
                                      self.top_panel_rect.height - 15, 
                                      toggle_size, 15),
            text='▼' if self.top_panel_expanded else '▲',
            manager=self.manager,
            tool_tip_text="Toggle Top Panel"
        )
        
        self.right_panel_toggle = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(self.control_panel_rect.x - 15, 
                                      self.height // 2 - toggle_size // 2, 
                                      15, toggle_size),
            text='▶' if self.control_panel_expanded else '◀',
            manager=self.manager,
            tool_tip_text="Toggle Control Panel"
        )
        

        if self.top_panel_expanded:

            self.play_button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(10, 10, 80, 30),
                text='Pause' if self.is_playing else 'Play',
                manager=self.manager,
                tool_tip_text="Play/Pause Animation"
            )
            

            self.fps_label = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(100, 10, 50, 30),
                text='FPS:',
                manager=self.manager
            )
            
            self.fps_slider = pygame_gui.elements.UIHorizontalSlider(
                relative_rect=pygame.Rect(150, 15, 150, 20),
                start_value=self.fps,
                value_range=(1, 120),
                manager=self.manager
            )
            
            self.fps_value_label = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(310, 10, 50, 30),
                text=str(self.fps),
                manager=self.manager
            )
            

            self.effect_label = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(370, 10, 80, 30),
                text='Effect ID:',
                manager=self.manager
            )
            

            self.effect_buttons = []
            for i, effect_id in enumerate(sorted(self.light_effects.keys())):
                x_pos = 450 + i * 35
                button = pygame_gui.elements.UIButton(
                    relative_rect=pygame.Rect(x_pos, 10, 30, 30),
                    text=str(effect_id),
                    manager=self.manager,
                    tool_tip_text=f"Select Effect {effect_id}"
                )
                self.effect_buttons.append((button, effect_id))
            

            self.zoom_label = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(740, 10, 60, 30),
                text='Zoom:',
                manager=self.manager
            )
            
            self.zoom_in_button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(800, 10, 30, 30),
                text='+',
                manager=self.manager,
                tool_tip_text="Zoom In"
            )
            
            self.zoom_out_button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(840, 10, 30, 30),
                text='-',
                manager=self.manager,
                tool_tip_text="Zoom Out"
            )
            
            self.zoom_reset_button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(880, 10, 80, 30),
                text='Reset View',
                manager=self.manager,
                tool_tip_text="Reset Zoom and Pan"
            )
        

        if self.control_panel_expanded:
            panel_y = 10
            

            self.palette_label = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(self.control_panel_rect.x + 10, panel_y, 100, 20),
                text='Color Palette:',
                manager=self.manager
            )
            

            self.palette_buttons = []
            for i, palette_id in enumerate(sorted(self.palettes.keys())):
                x_pos = self.control_panel_rect.x + 120 + i * 35
                button = pygame_gui.elements.UIButton(
                    relative_rect=pygame.Rect(x_pos, panel_y, 30, 30),
                    text=palette_id,
                    manager=self.manager,
                    tool_tip_text=f"Select Palette {palette_id}"
                )
                self.palette_buttons.append((button, palette_id))
            
            panel_y += 40
            

            self.palette_rect = pygame.Rect(
                self.control_panel_rect.x + 10, panel_y, 
                self.control_panel_rect.width - 20, 40
            )
            panel_y += 50
            

            self.segment_label = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(self.control_panel_rect.x + 10, panel_y, 100, 20),
                text='Segment ID:',
                manager=self.manager
            )
            

            segments = []
            if self.active_effect_id in self.light_effects:
                segments = sorted(self.light_effects[self.active_effect_id].segments.keys())
            else:
                segments = [1]
                
            self.segment_buttons = []
            for i, segment_id in enumerate(segments):
                x_pos = self.control_panel_rect.x + 120 + i * 35
                button = pygame_gui.elements.UIButton(
                    relative_rect=pygame.Rect(x_pos, panel_y, 30, 30),
                    text=str(segment_id),
                    manager=self.manager,
                    tool_tip_text=f"Select Segment {segment_id}"
                )
                self.segment_buttons.append((button, segment_id))
            
            panel_y += 40
            

            self.speed_heading = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(self.control_panel_rect.x + 10, panel_y, 
                                        self.control_panel_rect.width - 20, 20),
                text='Speed & Position',
                manager=self.manager
            )
            panel_y += 30
            

            segment = None
            if self.active_effect_id in self.light_effects and self.active_segment_id in self.light_effects[self.active_effect_id].segments:
                segment = self.light_effects[self.active_effect_id].segments[self.active_segment_id]
            
            if segment:

                self.speed_label = pygame_gui.elements.UILabel(
                    relative_rect=pygame.Rect(self.control_panel_rect.x + 10, panel_y, 100, 20),
                    text='Move Speed:',
                    manager=self.manager
                )
                
                panel_y += 25
                
                self.speed_slider = pygame_gui.elements.UIHorizontalSlider(
                    relative_rect=pygame.Rect(self.control_panel_rect.x + 10, panel_y, 
                                            self.control_panel_rect.width - 20, 20),
                    start_value=segment.move_speed,
                    value_range=(-128, 127),
                    manager=self.manager
                )
                
                panel_y += 30
                

                self.position_label = pygame_gui.elements.UILabel(
                    relative_rect=pygame.Rect(self.control_panel_rect.x + 10, panel_y, 100, 20),
                    text='Position:',
                    manager=self.manager
                )
                
                panel_y += 25
                
                self.position_slider = pygame_gui.elements.UIHorizontalSlider(
                    relative_rect=pygame.Rect(self.control_panel_rect.x + 10, panel_y, 
                                            self.control_panel_rect.width - 20, 20),
                    start_value=segment.current_position,
                    value_range=(segment.move_range[0], segment.move_range[1]),
                    manager=self.manager
                )
                
                panel_y += 30
                

                self.range_label = pygame_gui.elements.UILabel(
                    relative_rect=pygame.Rect(self.control_panel_rect.x + 10, panel_y, 100, 20),
                    text='Move Range:',
                    manager=self.manager
                )
                
                panel_y += 25
                
                range_width = (self.control_panel_rect.width - 30) / 2
                
                self.range_min_slider = pygame_gui.elements.UIHorizontalSlider(
                    relative_rect=pygame.Rect(self.control_panel_rect.x + 10, panel_y, 
                                            range_width, 20),
                    start_value=segment.move_range[0],
                    value_range=(0, DEFAULT_LED_COUNT - 1),
                    manager=self.manager
                )
                
                self.range_max_slider = pygame_gui.elements.UIHorizontalSlider(
                    relative_rect=pygame.Rect(self.control_panel_rect.x + 10 + range_width + 10, 
                                            panel_y, range_width, 20),
                    start_value=segment.move_range[1],
                    value_range=(0, DEFAULT_LED_COUNT - 1),
                    manager=self.manager
                )
                
                panel_y += 30
                

                self.reflect_label = pygame_gui.elements.UILabel(
                    relative_rect=pygame.Rect(self.control_panel_rect.x + 10, panel_y, 150, 20),
                    text='Edge Reflection:',
                    manager=self.manager
                )
                
                self.reflect_toggle = pygame_gui.elements.UIButton(
                    relative_rect=pygame.Rect(self.control_panel_rect.x + 170, panel_y, 
                                            self.control_panel_rect.width - 180, 20),
                    text='ON' if segment.is_edge_reflect else 'OFF',
                    manager=self.manager
                )
                
                panel_y += 40
                

                self.color_heading = pygame_gui.elements.UILabel(
                    relative_rect=pygame.Rect(self.control_panel_rect.x + 10, panel_y, 
                                            self.control_panel_rect.width - 20, 20),
                    text='Color Settings',
                    manager=self.manager
                )
                panel_y += 30
                

                self.color_buttons = []
                button_size = 40
                button_spacing = 10
                color_per_row = 4
                
                for i, color_idx in enumerate(segment.color):
                    row = i // color_per_row
                    col = i % color_per_row
                    
                    x = self.control_panel_rect.x + 10 + col * (button_size + button_spacing)
                    y = panel_y + row * (button_size + button_spacing)
                    

                    label = str(color_idx) if color_idx >= 0 else "-"
                    
                    button = pygame_gui.elements.UIButton(
                        relative_rect=pygame.Rect(x, y, button_size, button_size),
                        text=label,
                        manager=self.manager,
                        tool_tip_text=f"Color {i+1}"
                    )
                    

                    self.color_buttons.append((button, i))
                
                panel_y += (((len(segment.color) - 1) // color_per_row) + 1) * (button_size + button_spacing) + 10
                

                self.dimmer_heading = pygame_gui.elements.UILabel(
                    relative_rect=pygame.Rect(self.control_panel_rect.x + 10, panel_y, 
                                            self.control_panel_rect.width - 20, 20),
                    text='Dimmer Settings (Fade)',
                    manager=self.manager
                )
                panel_y += 30
                

                self.dimmer_sliders = []
                labels = ["Fade In Start", "Fade In End", "Fade Out Start", "Fade Out End", "Cycle Length"]
                
                for i, label in enumerate(labels):
                    if i >= len(segment.dimmer_time):
                        break
                        
                    label_element = pygame_gui.elements.UILabel(
                        relative_rect=pygame.Rect(self.control_panel_rect.x + 10, panel_y, 
                                                self.control_panel_rect.width - 20, 20),
                        text=label,
                        manager=self.manager
                    )
                    
                    panel_y += 20
                    
                    slider = pygame_gui.elements.UIHorizontalSlider(
                        relative_rect=pygame.Rect(self.control_panel_rect.x + 10, panel_y, 
                                                self.control_panel_rect.width - 20, 20),
                        start_value=segment.dimmer_time[i],
                        value_range=(0, 1000),
                        manager=self.manager
                    )
                    
                    self.dimmer_sliders.append((slider, i, label_element))
                    panel_y += 30
    
    def toggle_panel(self, panel_name):
        """
        Toggle the expansion state of a panel.
        
        Args:
            panel_name: Name of the panel to toggle ('top' or 'right')
        """
        if panel_name == 'top':
            self.top_panel_expanded = not self.top_panel_expanded
        elif panel_name == 'right':
            self.control_panel_expanded = not self.control_panel_expanded
            
        self.calculate_layout()
        self.setup_ui()
    
    def handle_events(self, time_delta):
        """
        Process pygame events and update the UI.
        
        Args:
            time_delta: Time elapsed since last frame
            
        Returns:
            bool: False if the application should quit, True otherwise
        """

        mouse_pos = pygame.mouse.get_pos()
        

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                return False
                

            elif event.type == pygame.VIDEORESIZE:
                self.width, self.height = event.size
                self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                self.manager.set_window_resolution((self.width, self.height))
                self.calculate_layout()
                self.setup_ui()
                

            elif event.type == pygame.MOUSEWHEEL:
                if self.led_display_rect.collidepoint(mouse_pos):
                    self.zoom_level = max(0.1, min(5.0, self.zoom_level + event.y * 0.1))
                    self.last_activity_time = time.time()
                    

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and self.led_display_rect.collidepoint(mouse_pos):  # Left click in LED display
                    self.dragging = True
                    self.last_mouse_pos = mouse_pos
                    self.last_activity_time = time.time()
                    
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left mouse button
                    self.dragging = False
                    self.last_activity_time = time.time()
                    
            elif event.type == pygame.MOUSEMOTION:

                if self.dragging and self.led_display_rect.collidepoint(mouse_pos):
                    dx = mouse_pos[0] - self.last_mouse_pos[0]
                    self.pan_offset += dx
                    self.last_mouse_pos = mouse_pos
                    self.last_activity_time = time.time()
            

            elif event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.top_panel_toggle:
                        self.toggle_panel('top')
                    elif event.ui_element == self.right_panel_toggle:
                        self.toggle_panel('right')
                    elif hasattr(self, 'play_button') and event.ui_element == self.play_button:
                        self.is_playing = not self.is_playing
                        self.play_button.set_text('Pause' if self.is_playing else 'Play')
                    elif hasattr(self, 'zoom_in_button') and event.ui_element == self.zoom_in_button:
                        self.zoom_level = min(5.0, self.zoom_level * 1.2)
                    elif hasattr(self, 'zoom_out_button') and event.ui_element == self.zoom_out_button:
                        self.zoom_level = max(0.1, self.zoom_level / 1.2)
                    elif hasattr(self, 'zoom_reset_button') and event.ui_element == self.zoom_reset_button:
                        self.zoom_level = 1.0
                        self.pan_offset = 0
                    elif hasattr(self, 'reflect_toggle') and event.ui_element == self.reflect_toggle:
                        if self.active_effect_id in self.light_effects and self.active_segment_id in self.light_effects[self.active_effect_id].segments:
                            segment = self.light_effects[self.active_effect_id].segments[self.active_segment_id]
                            segment.is_edge_reflect = not segment.is_edge_reflect
                            self.reflect_toggle.set_text('ON' if segment.is_edge_reflect else 'OFF')
                    

                    if hasattr(self, 'effect_buttons'):
                        for button, effect_id in self.effect_buttons:
                            if event.ui_element == button:
                                self.active_effect_id = effect_id
                                

                                if self.active_effect_id in self.light_effects:
                                    segments = sorted(self.light_effects[self.active_effect_id].segments.keys())
                                    if segments:
                                        self.active_segment_id = segments[0]
                                        
                                self.setup_ui()
                                break
                    

                    if hasattr(self, 'segment_buttons'):
                        for button, segment_id in self.segment_buttons:
                            if event.ui_element == button:
                                self.active_segment_id = segment_id
                                self.setup_ui()
                                break
                                

                    if hasattr(self, 'palette_buttons'):
                        for button, palette_id in self.palette_buttons:
                            if event.ui_element == button:
                                self.current_palette = palette_id

                                for effect in self.light_effects.values():
                                    effect.current_palette = self.current_palette
                                self.setup_ui()
                                break
                                

                    if hasattr(self, 'color_buttons'):
                        for button, color_index in self.color_buttons:
                            if event.ui_element == button:
                                self.cycle_color(color_index)
                                break
                                
                elif event.user_type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
                    if hasattr(self, 'fps_slider') and event.ui_element == self.fps_slider:
                        self.fps = int(event.value)
                        if hasattr(self, 'fps_value_label'):
                            self.fps_value_label.set_text(str(self.fps))
                        for effect in self.light_effects.values():
                            effect.fps = self.fps
                    

                    if self.active_effect_id in self.light_effects and self.active_segment_id in self.light_effects[self.active_effect_id].segments:
                        segment = self.light_effects[self.active_effect_id].segments[self.active_segment_id]
                        
                        if hasattr(self, 'speed_slider') and event.ui_element == self.speed_slider:
                            segment.move_speed = event.value
                        elif hasattr(self, 'position_slider') and event.ui_element == self.position_slider:
                            segment.current_position = event.value
                        elif hasattr(self, 'range_min_slider') and event.ui_element == self.range_min_slider:
                            segment.move_range = [event.value, segment.move_range[1]]
                        elif hasattr(self, 'range_max_slider') and event.ui_element == self.range_max_slider:
                            segment.move_range = [segment.move_range[0], event.value]
                        

                        if hasattr(self, 'dimmer_sliders'):
                            for slider, dimmer_index, _ in self.dimmer_sliders:
                                if event.ui_element == slider:
                                    dimmer_time = segment.dimmer_time.copy()
                                    dimmer_time[dimmer_index] = int(event.value)
                                    segment.dimmer_time = dimmer_time
                                    break
            

            self.manager.process_events(event)
        

        if time.time() - self.last_activity_time > self.auto_hide_timeout:
            if self.top_panel_expanded or self.control_panel_expanded:
                self.top_panel_expanded = False
                self.control_panel_expanded = False
                self.calculate_layout()
                self.setup_ui()
                

        self.manager.update(time_delta)
        
        return True
    
    def cycle_color(self, color_index):
        """
        Cycle through available colors for a specific color button.
        
        Args:
            color_index: Index of the color to change
        """
        if self.active_effect_id in self.light_effects and self.active_segment_id in self.light_effects[self.active_effect_id].segments:
            segment = self.light_effects[self.active_effect_id].segments[self.active_segment_id]
            

            current_idx = segment.color[color_index] if color_index < len(segment.color) else -1
            

            next_idx = (current_idx + 1) % len(self.palettes[self.current_palette]) if current_idx >= 0 else 0
            

            if color_index < len(segment.color):
                new_colors = segment.color.copy()
                new_colors[color_index] = next_idx
                segment.update_param('color', new_colors)
                

            self.setup_ui()
    
    def draw(self):
        """
        Render the UI and LED visualization.
        """

        self.screen.fill(UI_BACKGROUND_COLOR)
        

        if self.active_effect_id in self.light_effects:
            effect = self.light_effects[self.active_effect_id]
            led_colors = effect.get_led_output()
            

            led_width = int(self.led_size * self.zoom_level)
            led_spacing = int(self.led_spacing * self.zoom_level)
            led_total_width = led_width + led_spacing
            

            first_visible_led = max(0, int((-self.pan_offset) / led_total_width))

            last_visible_led = min(len(led_colors) - 1, 
                                  first_visible_led + int(self.led_display_rect.width / led_total_width) + 1)
            

            for i in range(first_visible_led, last_visible_led + 1):
                if i >= len(led_colors):
                    break
                    
                x = self.led_display_rect.x + i * led_total_width + self.pan_offset
                y = self.led_display_center_y - led_width // 2
                

                color = led_colors[i]
                if isinstance(color, list):
                    color = tuple(color)
                
                pygame.draw.rect(self.screen, color, (x, y, led_width, led_width))
                

                border_color = (min(color[0] + 30, 255), min(color[1] + 30, 255), min(color[2] + 30, 255))
                pygame.draw.rect(self.screen, border_color, (x, y, led_width, led_width), 1)
        

        if self.control_panel_expanded and hasattr(self, 'palette_rect'):
            palette = self.palettes[self.current_palette]
            color_width = self.palette_rect.width / len(palette)
            for i, color in enumerate(palette):
                if isinstance(color, list):
                    color = tuple(color)
                    
                rect = pygame.Rect(
                    self.palette_rect.x + i * color_width,
                    self.palette_rect.y,
                    color_width,
                    self.palette_rect.height
                )
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, (100, 100, 100), rect, 1)
                

                font = pygame.font.SysFont('Arial', 14)
                text = font.render(str(i), True, (0, 0, 0) if sum(color) > 380 else (255, 255, 255))
                text_rect = text.get_rect(center=(rect.x + rect.width/2, rect.y + rect.height/2))
                self.screen.blit(text, text_rect)
        

        fps_font = pygame.font.SysFont('Arial', 14)
        fps_text = f"FPS: {int(self.clock.get_fps())}"
        fps_surf = fps_font.render(fps_text, True, (220, 220, 220))
        self.screen.blit(fps_surf, (10, self.height - 20))
        

        if self.active_effect_id in self.light_effects and self.active_segment_id in self.light_effects[self.active_effect_id].segments:
            segment = self.light_effects[self.active_effect_id].segments[self.active_segment_id]
            info_text = f"Effect {self.active_effect_id}, Segment {self.active_segment_id} - Position: {int(segment.current_position)}, Speed: {int(segment.move_speed)}"
            info_surf = fps_font.render(info_text, True, (220, 220, 220))
            self.screen.blit(info_surf, (self.led_display_rect.x + 10, self.led_display_rect.y + 10))
        

        self.manager.draw_ui(self.screen)
    
    def run(self):
        """
        Run the main simulation loop.
        """
        running = True
        
        while running:

            time_delta = self.clock.tick(self.fps) / 1000.0
            

            running = self.handle_events(time_delta)
            

            if self.is_playing:
                for effect in self.light_effects.values():
                    effect.update_all()
            

            self.draw()
            

            pygame.display.flip()
        
        pygame.quit()