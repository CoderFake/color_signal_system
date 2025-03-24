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
    UI_ACCENT_COLOR, UI_BUTTON_COLOR, UI_PANEL_COLOR, 
    DEFAULT_COLOR_PALETTES
)

class LEDSimulator: 
    def __init__(self, 
                 light_effects: Dict[int, LightEffect], 
                 width: int = UI_WIDTH, 
                 height: int = UI_HEIGHT):
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
        

        self.led_size = 10
        self.led_spacing = 2
        self.led_display_height = 50
        

        self.is_playing = True
        self.fps = 60
        self.zoom_level = 1.0
        self.pan_offset = 0
        self.dragging = False
        self.last_mouse_pos = (0, 0)
        

        self.current_palette = "A"
        self.palettes = DEFAULT_COLOR_PALETTES
        

        self.top_panel_expanded = True
        self.control_panel_expanded = True
        self.panel_animation = {
            'top': {'target': 1.0, 'current': 1.0},
            'right': {'target': 1.0, 'current': 1.0}
        }
        self.animation_speed = 5.0  
        

        self.dock_animation = {
            'enabled': True,
            'magnification': 1.5,  
            'range': 100,
            'active': False,  
            'position': 0,
            'last_update': 0 
        }
        

        self.panel_sections = {
            'colors': {'expanded': True, 'height': 180},
            'position': {'expanded': True, 'height': 150},
            'dimmer': {'expanded': True, 'height': 160}
        }
        

        self.hover_timers = {
            'top': 0,
            'right': 0
        }
        self.hover_threshold = 0.3
        

        self.auto_hide = {
            'enabled': True,
            'timeout': 3.0,
            'last_activity': time.time()
        }
        

        self.setup_ui()
        
    def setup_ui(self):
        """
        Set up the user interface elements.
        """

        self.calculate_panel_dimensions()
        

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
            
            effect_ids = sorted(self.light_effects.keys())
            self.effect_dropdown = pygame_gui.elements.UIDropDownMenu(
                options=[str(eid) for eid in effect_ids],
                starting_option=str(self.active_effect_id),
                relative_rect=pygame.Rect(450, 15, 80, 20),
                manager=self.manager
            )
            

            self.zoom_label = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(540, 10, 60, 30),
                text='Zoom:',
                manager=self.manager
            )
            
            self.zoom_in_button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(600, 10, 30, 30),
                text='+',
                manager=self.manager,
                tool_tip_text="Zoom In"
            )
            
            self.zoom_out_button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(640, 10, 30, 30),
                text='-',
                manager=self.manager,
                tool_tip_text="Zoom Out"
            )
            
            self.zoom_reset_button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(680, 10, 80, 30),
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
            
            self.palette_dropdown = pygame_gui.elements.UIDropDownMenu(
                options=list(self.palettes.keys()),
                starting_option=self.current_palette,
                relative_rect=pygame.Rect(self.control_panel_rect.x + 120, panel_y, 60, 20),
                manager=self.manager
            )
            
            panel_y += 30
            

            self.palette_rect = pygame.Rect(
                self.control_panel_rect.x + 10, panel_y, 
                self.control_panel_rect.width - 20, 40
            )
            panel_y += 50
            

            self.segment_label = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(self.control_panel_rect.x + 10, panel_y, 100, 20),
                text='Object ID:',
                manager=self.manager
            )
            
            self.active_object_id = 1
            self.segment_dropdown = pygame_gui.elements.UIDropDownMenu(
                options=[str(i) for i in range(1, 9)],
                starting_option=str(self.active_object_id),
                relative_rect=pygame.Rect(self.control_panel_rect.x + 120, panel_y, 60, 20),
                manager=self.manager
            )
            
            panel_y += 40
            

            self.create_collapsible_section('colors', 'Colors and Gradients', panel_y)
            panel_y += 30
            

            if self.panel_sections['colors']['expanded']:

                self.color_buttons = []
                button_size = 40
                button_spacing = 10
                for i in range(4):
                    x = self.control_panel_rect.x + 10 + i * (button_size + button_spacing)
                    color_button = pygame_gui.elements.UIButton(
                        relative_rect=pygame.Rect(x, panel_y, button_size, button_size),
                        text='',
                        manager=self.manager,
                        tool_tip_text=f"Color {i+1}"
                    )
                    self.color_buttons.append(color_button)
                
                panel_y += button_size + 20
                

                self.speed_label = pygame_gui.elements.UILabel(
                    relative_rect=pygame.Rect(self.control_panel_rect.x + 10, panel_y, 100, 20),
                    text='Move Speed:',
                    manager=self.manager
                )
                
                panel_y += 25
                
                self.speed_slider = pygame_gui.elements.UIHorizontalSlider(
                    relative_rect=pygame.Rect(self.control_panel_rect.x + 10, panel_y, 
                                            self.control_panel_rect.width - 20, 20),
                    start_value=0,  
                    value_range=(-128, 127),
                    manager=self.manager
                )
                
                panel_y += 50
            else:
                panel_y += 5
            

            self.create_collapsible_section('position', 'Position and Range', panel_y)
            panel_y += 30
            
            if self.panel_sections['position']['expanded']:

                self.position_label = pygame_gui.elements.UILabel(
                    relative_rect=pygame.Rect(self.control_panel_rect.x + 10, panel_y, 280, 20),
                    text='Position:',
                    manager=self.manager
                )
                
                panel_y += 25
                
                self.position_slider = pygame_gui.elements.UIHorizontalSlider(
                    relative_rect=pygame.Rect(self.control_panel_rect.x + 10, panel_y, 
                                             self.control_panel_rect.width - 20, 20),
                    start_value=0, 
                    value_range=(0, 225),
                    manager=self.manager
                )
                
                panel_y += 30
                

                self.interval_label = pygame_gui.elements.UILabel(
                    relative_rect=pygame.Rect(self.control_panel_rect.x + 10, panel_y, 100, 20),
                    text='Interval:',
                    manager=self.manager
                )
                
                panel_y += 25

                self.interval_slider = pygame_gui.elements.UIHorizontalSlider(
                    relative_rect=pygame.Rect(self.control_panel_rect.x + 10, panel_y, 
                                            self.control_panel_rect.width - 20, 20),
                    start_value=10, 
                    value_range=(-128, 127),
                    manager=self.manager,
                    tool_tip_text="Time interval for position updates"
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
                    start_value=0,
                    value_range=(0, 255),
                    manager=self.manager
                )
                
                self.range_max_slider = pygame_gui.elements.UIHorizontalSlider(
                    relative_rect=pygame.Rect(self.control_panel_rect.x + 10 + range_width + 10, 
                                             panel_y, range_width, 20),
                    start_value=255,
                    value_range=(0, 255),
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
                    text='ON',
                    manager=self.manager
                )
                
                panel_y += 30
            else:
                panel_y += 5
            
            self.create_collapsible_section('span', 'Span Settings', panel_y)
            panel_y += 30

            if self.panel_sections['span']['expanded']:
                self.span_width_label = pygame_gui.elements.UILabel(
                    relative_rect=pygame.Rect(self.control_panel_rect.x + 10, panel_y, 100, 20),
                    text='Width:',
                    manager=self.manager
                )
                
                panel_y += 25
                self.span_width_slider = pygame_gui.elements.UIHorizontalSlider(
                    relative_rect=pygame.Rect(self.control_panel_rect.x + 10, panel_y, 
                                            self.control_panel_rect.width - 20, 20),
                    start_value=100,
                    value_range=(0, 255),
                    manager=self.manager
                )
                
                panel_y += 30
                
                self.span_range_label = pygame_gui.elements.UILabel(
                    relative_rect=pygame.Rect(self.control_panel_rect.x + 10, panel_y, 100, 20),
                    text='Range:',
                    manager=self.manager
                )
                
                panel_y += 25
                
                range_width = (self.control_panel_rect.width - 30) / 2
                
                self.span_range_min_slider = pygame_gui.elements.UIHorizontalSlider(
                    relative_rect=pygame.Rect(self.control_panel_rect.x + 10, panel_y, 
                                            range_width, 20),
                    start_value=50,
                    value_range=(0, 255),
                    manager=self.manager
                )
                
                self.span_range_max_slider = pygame_gui.elements.UIHorizontalSlider(
                    relative_rect=pygame.Rect(self.control_panel_rect.x + 10 + range_width + 10, 
                                            panel_y, range_width, 20),
                    start_value=150,
                    value_range=(0, 255),
                    manager=self.manager
                )
                
                panel_y += 30
                
                self.span_speed_label = pygame_gui.elements.UILabel(
                    relative_rect=pygame.Rect(self.control_panel_rect.x + 10, panel_y, 100, 20),
                    text='Speed:',
                    manager=self.manager
                )
                
                panel_y += 25
                self.span_speed_slider = pygame_gui.elements.UIHorizontalSlider(
                    relative_rect=pygame.Rect(self.control_panel_rect.x + 10, panel_y, 
                                            self.control_panel_rect.width - 20, 20),
                    start_value=100,
                    value_range=(0, 255),
                    manager=self.manager
                )
                
                panel_y += 30
                
                self.span_interval_label = pygame_gui.elements.UILabel(
                    relative_rect=pygame.Rect(self.control_panel_rect.x + 10, panel_y, 100, 20),
                    text='Interval:',
                    manager=self.manager
                )
                
                panel_y += 25
                self.span_interval_slider = pygame_gui.elements.UIHorizontalSlider(
                    relative_rect=pygame.Rect(self.control_panel_rect.x + 10, panel_y, 
                                            self.control_panel_rect.width - 20, 20),
                    start_value=10,
                    value_range=(0, 255),
                    manager=self.manager
                )
                
                panel_y += 30
                
                self.fade_label = pygame_gui.elements.UILabel(
                    relative_rect=pygame.Rect(self.control_panel_rect.x + 10, panel_y, 100, 20),
                    text='Fade:',
                    manager=self.manager
                )
                
                self.fade_toggle = pygame_gui.elements.UIButton(
                    relative_rect=pygame.Rect(self.control_panel_rect.x + 120, panel_y, 
                                            self.control_panel_rect.width - 130, 20),
                    text='ON',
                    manager=self.manager,
                    tool_tip_text="Toggle fade effect"
                )
                
                panel_y += 30
                
                self.span_gradient_label = pygame_gui.elements.UILabel(
                    relative_rect=pygame.Rect(self.control_panel_rect.x + 10, panel_y, 100, 20),
                    text='Gradient Colors:',
                    manager=self.manager
                )
                
                self.span_gradient_toggle = pygame_gui.elements.UIButton(
                    relative_rect=pygame.Rect(self.control_panel_rect.x + 120, panel_y, 
                                            self.control_panel_rect.width - 130, 20),
                    text='OFF',
                    manager=self.manager,
                    tool_tip_text="Toggle gradient effect for span"
                )
                
                panel_y += 30
                
                self.span_gradient_colors = []
                button_size = 30
                buttons_per_row = 3
                button_spacing = 10
                
                for i in range(6):
                    row = i // buttons_per_row
                    col = i % buttons_per_row
                    
                    x = self.control_panel_rect.x + 10 + col * (button_size + button_spacing)
                    y = panel_y + row * (button_size + button_spacing)
                    
                    color_button = pygame_gui.elements.UIButton(
                        relative_rect=pygame.Rect(x, y, button_size, button_size),
                        text='',
                        manager=self.manager,
                        tool_tip_text=f"Span Gradient Color {i+1}"
                    )
                    self.span_gradient_colors.append(color_button)
                
                panel_y += 2 * (button_size + button_spacing) + 10

            else:
                panel_y += 5

            self.create_collapsible_section('dimmer', 'Dimmer Settings (Fade)', panel_y)
            panel_y += 30
            
            if self.panel_sections['dimmer']['expanded']:

                self.dimmer_sliders = []
                slider_labels = ['In Start', 'In End', 'Out Start', 'Out End', 'Cycle']
                
                for i in range(5):
                    y = panel_y + i * 25
                    label = pygame_gui.elements.UILabel(
                        relative_rect=pygame.Rect(self.control_panel_rect.x + 10, y, 80, 20),
                        text=slider_labels[i] + ':',
                        manager=self.manager
                    )
                    
                    slider = pygame_gui.elements.UIHorizontalSlider(
                        relative_rect=pygame.Rect(self.control_panel_rect.x + 100, y, 
                                                 self.control_panel_rect.width - 110, 20),
                        start_value=0 if i < 4 else 1000,
                        value_range=(0, 1000),
                        manager=self.manager
                    )
                    
                    self.dimmer_sliders.append(slider)
                
                panel_y += 130
            else:
                panel_y += 5
            
            panel_y += 20
            
            button_width = (self.control_panel_rect.width - 30) / 2
            
            self.add_segment_button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(self.control_panel_rect.x + 10, panel_y, 
                                         button_width, 30),
                text='Add Object',
                manager=self.manager,
                tool_tip_text="Add a new segment to the effect"
            )
            
            self.remove_segment_button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(self.control_panel_rect.x + 10 + button_width + 10, 
                                         panel_y, button_width, 30),
                text='Remove Object',
                manager=self.manager,
                tool_tip_text="Remove the current object"
            )
        
            panel_y += button_size + 10


            self.gradient_label = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(self.control_panel_rect.x + 10, panel_y, 100, 20),
                text='Gradient:',
                manager=self.manager
            )

            self.gradient_toggle = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(self.control_panel_rect.x + 120, panel_y, 
                                        self.control_panel_rect.width - 130, 20),
                text='ON', 
                manager=self.manager,
                tool_tip_text="Toggle gradient effect"
            )

            panel_y += 30

            self.gradient_colors = []
            button_size = 30
            button_spacing = 10
            for i in range(2): 
                x = self.control_panel_rect.x + 10 + i * (button_size + button_spacing)
                color_button = pygame_gui.elements.UIButton(
                    relative_rect=pygame.Rect(x, panel_y, button_size, button_size),
                    text='',
                    manager=self.manager,
                    tool_tip_text=f"Gradient Color {i+1}"
                )
                self.gradient_colors.append(color_button)

            panel_y += button_size + 10

        self.update_ui_from_object()
        
    def create_collapsible_section(self, section_id, title, y_pos):
        """
        Create a collapsible section header with toggle button.
        
        Args:
            section_id: ID of the section
            title: Title text to display
            y_pos: Y position of the section header
        """

        header_rect = pygame.Rect(
            self.control_panel_rect.x + 10, y_pos, 
            self.control_panel_rect.width - 50, 20
        )
        
        label = pygame_gui.elements.UILabel(
            relative_rect=header_rect,
            text=title,
            manager=self.manager
        )
        

        toggle_rect = pygame.Rect(
            self.control_panel_rect.x + self.control_panel_rect.width - 30, y_pos,
            20, 20
        )
        
        toggle_button = pygame_gui.elements.UIButton(
            relative_rect=toggle_rect,
            text='▼' if self.panel_sections[section_id]['expanded'] else '▲',
            manager=self.manager,
            tool_tip_text=f"Toggle {title} Panel"
        )
        

        self.panel_sections[section_id]['label'] = label
        self.panel_sections[section_id]['toggle'] = toggle_button
    
    def calculate_panel_dimensions(self):
        """
        Calculate the dimensions and positions of the panels based on their expansion state.
        """

        top_panel_height = int(60 * self.panel_animation['top']['current'])
        

        control_panel_width = int(300 * self.panel_animation['right']['current'])
        

        self.top_panel_rect = pygame.Rect(0, 0, self.width, top_panel_height)
        

        self.control_panel_rect = pygame.Rect(
            self.width - control_panel_width, top_panel_height, 
            control_panel_width, self.height - top_panel_height
        )
        

        self.led_display_rect = pygame.Rect(
            0, top_panel_height, 
            self.width - (control_panel_width if control_panel_width > 15 else 15), 
            self.height - top_panel_height
        )
    
    def toggle_panel(self, panel_name):
        """
        Toggle the expansion state of a panel.
        
        Args:
            panel_name: Name of the panel to toggle ('top' or 'right')
        """
        if panel_name == 'top':
            self.top_panel_expanded = not self.top_panel_expanded
            self.panel_animation['top']['target'] = 1.0 if self.top_panel_expanded else 0.1
            
        elif panel_name == 'right':
            self.control_panel_expanded = not self.control_panel_expanded
            self.panel_animation['right']['target'] = 1.0 if self.control_panel_expanded else 0.05
        

        if hasattr(self, 'top_panel_toggle'):
            self.top_panel_toggle.set_text('▼' if self.top_panel_expanded else '▲')
            
        if hasattr(self, 'right_panel_toggle'):
            self.right_panel_toggle.set_text('▶' if self.control_panel_expanded else '◀')
    
    def toggle_section(self, section_id):
        """
        Toggle the expansion state of a control panel section.
        
        Args:
            section_id: ID of the section to toggle
        """
        if section_id in self.panel_sections:
            self.panel_sections[section_id]['expanded'] = not self.panel_sections[section_id]['expanded']
            

            if 'toggle' in self.panel_sections[section_id]:
                self.panel_sections[section_id]['toggle'].set_text(
                    '▼' if self.panel_sections[section_id]['expanded'] else '▲'
                )
            

            self.rebuild_ui()
    
    def rebuild_ui(self):
        """
        Rebuild the UI elements to reflect changes in panel states.
        """

        self.manager.clear_and_reset()
        

        self.calculate_panel_dimensions()
        

        self.setup_ui()
    
    def update_panel_animations(self, time_delta):
        """
        Update panel animation states.
        
        Args:
            time_delta: Time elapsed since last frame
        """
        panels_updated = False
        

        current = self.panel_animation['top']['current']
        target = self.panel_animation['top']['target']
        
        if abs(current - target) > 0.01:
            direction = 1 if target > current else -1
            self.panel_animation['top']['current'] += direction * self.animation_speed * time_delta
            self.panel_animation['top']['current'] = max(0.1, min(1.0, self.panel_animation['top']['current']))
            panels_updated = True
            

        current = self.panel_animation['right']['current']
        target = self.panel_animation['right']['target']
        
        if abs(current - target) > 0.01:
            direction = 1 if target > current else -1
            self.panel_animation['right']['current'] += direction * self.animation_speed * time_delta
            self.panel_animation['right']['current'] = max(0.05, min(1.0, self.panel_animation['right']['current']))
            panels_updated = True
        

        if panels_updated:
            self.calculate_panel_dimensions()
            

            if hasattr(self, 'top_panel_toggle'):
                self.top_panel_toggle.set_relative_position(
                    (self.width // 2 - 15, self.top_panel_rect.height - 15)
                )
                
            if hasattr(self, 'right_panel_toggle'):
                self.right_panel_toggle.set_relative_position(
                    (self.control_panel_rect.x - 15, self.height // 2 - 15)
                )
    
    def check_panel_hover(self, mouse_pos, time_delta):
        """
        Check if mouse is hovering over panel edges to auto-expand.
        
        Args:
            mouse_pos: Current mouse position
            time_delta: Time elapsed since last frame
        """

        top_hover_area = pygame.Rect(0, 0, self.width, 20)
        if top_hover_area.collidepoint(mouse_pos) and not self.top_panel_expanded:
            self.hover_timers['top'] += time_delta
            if self.hover_timers['top'] >= self.hover_threshold:
                self.panel_animation['top']['target'] = 1.0
                self.top_panel_expanded = True
                self.top_panel_toggle.set_text('▼')
        else:
            self.hover_timers['top'] = 0
            

        right_hover_area = pygame.Rect(self.width - 20, 0, 20, self.height)
        if right_hover_area.collidepoint(mouse_pos) and not self.control_panel_expanded:
            self.hover_timers['right'] += time_delta
            if self.hover_timers['right'] >= self.hover_threshold:
                self.panel_animation['right']['target'] = 1.0
                self.control_panel_expanded = True
                self.right_panel_toggle.set_text('▶')
        else:
            self.hover_timers['right'] = 0
    
    def update_ui_from_object(self):
        """
        Update UI element states based on the currently selected segment.
        """
        if not hasattr(self, 'color_buttons'):
            return
            
        if self.active_effect_id not in self.light_effects:
            return
            
        effect = self.light_effects[self.active_effect_id]
        
        if self.active_object_id not in effect.segments:
            return
            
        segment = effect.segments[self.active_object_id]
        

        for i, button in enumerate(self.color_buttons):
            if i < len(segment.color):
                color_id = segment.color[i]
                if color_id >= 0 and color_id < len(self.palettes[self.current_palette]):
                    color = self.palettes[self.current_palette][color_id]
                    button.colours['normal_bg'] = pygame.Color(color[0], color[1], color[2])
                    button.colours['hovered_bg'] = pygame.Color(min(255, color[0] + 20), 
                                                            min(255, color[1] + 20), 
                                                            min(255, color[2] + 20))
                    button.colours['active_bg'] = pygame.Color(min(255, color[0] + 40), 
                                                            min(255, color[1] + 40), 
                                                            min(255, color[2] + 40))
                    button.rebuild()
                else:

                    button.colours['normal_bg'] = pygame.Color(80, 80, 80)
                    button.colours['hovered_bg'] = pygame.Color(100, 100, 100)
                    button.colours['active_bg'] = pygame.Color(120, 120, 120)
                    button.rebuild()
        

        if hasattr(self, 'gradient_toggle'):
            self.gradient_toggle.set_text('ON' if getattr(segment, 'gradient_enabled', False) else 'OFF')
        
        if hasattr(self, 'gradient_colors') and hasattr(segment, 'gradient_colors'):
            for i, button in enumerate(self.gradient_colors):
                if i < len(segment.gradient_colors):
                    color_id = segment.gradient_colors[i]
                    if color_id >= 0 and color_id < len(self.palettes[self.current_palette]):

                        color = self.palettes[self.current_palette][color_id]
                        button.colours['normal_bg'] = pygame.Color(color[0], color[1], color[2])
                        button.colours['hovered_bg'] = pygame.Color(min(255, color[0] + 20), 
                                                                min(255, color[1] + 20), 
                                                                min(255, color[2] + 20))
                        button.colours['active_bg'] = pygame.Color(min(255, color[0] + 40), 
                                                                min(255, color[1] + 40), 
                                                                min(255, color[2] + 40))
                        button.rebuild()
                    else:

                        button.colours['normal_bg'] = pygame.Color(80, 80, 80)
                        button.colours['hovered_bg'] = pygame.Color(100, 100, 100)
                        button.colours['active_bg'] = pygame.Color(120, 120, 120)
                        button.rebuild()
        

        if hasattr(self, 'speed_slider'):
            self.speed_slider.set_current_value(segment.move_speed)
        
        if hasattr(self, 'position_slider'):
            self.position_slider.set_current_value(segment.current_position)
        
        if hasattr(self, 'range_min_slider') and hasattr(self, 'range_max_slider'):
            self.range_min_slider.set_current_value(segment.move_range[0])
            self.range_max_slider.set_current_value(segment.move_range[1])
        

        if hasattr(self, 'interval_slider') and hasattr(segment, 'interval'):
            self.interval_slider.set_current_value(segment.interval)
        

        if hasattr(self, 'reflect_toggle'):
            self.reflect_toggle.set_text('ON' if segment.is_edge_reflect else 'OFF')
        

        if hasattr(self, 'dimmer_sliders'):
            for i, slider in enumerate(self.dimmer_sliders):
                if i < len(segment.dimmer_time):
                    slider.set_current_value(segment.dimmer_time[i])
        

        if hasattr(self, 'span_width_slider') and hasattr(segment, 'span_width'):
            self.span_width_slider.set_current_value(segment.span_width)
        
        if hasattr(self, 'span_range_min_slider') and hasattr(self, 'span_range_max_slider') and hasattr(segment, 'span_range'):
            self.span_range_min_slider.set_current_value(segment.span_range[0])
            self.span_range_max_slider.set_current_value(segment.span_range[1])
        
        if hasattr(self, 'span_speed_slider') and hasattr(segment, 'span_speed'):
            self.span_speed_slider.set_current_value(segment.span_speed)
        
        if hasattr(self, 'span_interval_slider') and hasattr(segment, 'span_interval'):
            self.span_interval_slider.set_current_value(segment.span_interval)
        

        if hasattr(self, 'fade_toggle'):
            self.fade_toggle.set_text('ON' if getattr(segment, 'fade_enabled', False) else 'OFF')
        

        if hasattr(self, 'span_gradient_toggle'):
            self.span_gradient_toggle.set_text('ON' if getattr(segment, 'span_gradient_enabled', False) else 'OFF')
        

        if hasattr(self, 'span_gradient_colors') and hasattr(segment, 'span_gradient_colors'):
            for i, button in enumerate(self.span_gradient_colors):
                if i < len(segment.span_gradient_colors):
                    color_id = segment.span_gradient_colors[i]
                    if color_id >= 0 and color_id < len(self.palettes[self.current_palette]):

                        color = self.palettes[self.current_palette][color_id]
                        button.colours['normal_bg'] = pygame.Color(color[0], color[1], color[2])
                        button.colours['hovered_bg'] = pygame.Color(min(255, color[0] + 20), 
                                                                min(255, color[1] + 20), 
                                                                min(255, color[2] + 20))
                        button.colours['active_bg'] = pygame.Color(min(255, color[0] + 40), 
                                                                min(255, color[1] + 40), 
                                                                min(255, color[2] + 40))
                        button.rebuild()
                    else:

                        button.colours['normal_bg'] = pygame.Color(80, 80, 80)
                        button.colours['hovered_bg'] = pygame.Color(100, 100, 100)
                        button.colours['active_bg'] = pygame.Color(120, 120, 120)
                        button.rebuild()
        

        if hasattr(self, 'speed_value_label'):
            self.speed_value_label.set_text(str(int(segment.move_speed)))
        
        if hasattr(self, 'position_value_label'):
            self.position_value_label.set_text(str(int(segment.current_position)))
        
        if hasattr(self, 'interval_value_label') and hasattr(segment, 'interval'):
            self.interval_value_label.set_text(str(segment.interval))
        
        if hasattr(self, 'span_width_value_label') and hasattr(segment, 'span_width'):
            self.span_width_value_label.set_text(str(segment.span_width))
        
        if hasattr(self, 'span_speed_value_label') and hasattr(segment, 'span_speed'):
            self.span_speed_value_label.set_text(str(segment.span_speed))
        
        if hasattr(self, 'span_interval_value_label') and hasattr(segment, 'span_interval'):
            self.span_interval_value_label.set_text(str(segment.span_interval))

    def check_auto_hide(self, time_delta):
        """
        Check if panels should be auto-hidden due to inactivity.
        
        Args:
            time_delta: Time elapsed since last frame
        """
        if not self.auto_hide['enabled']:
            return
            
        if time.time() - self.auto_hide['last_activity'] > self.auto_hide['timeout']:
            if self.top_panel_expanded:
                self.panel_animation['top']['target'] = 0.1
                self.top_panel_expanded = False
                if hasattr(self, 'top_panel_toggle'):
                    self.top_panel_toggle.set_text('▲')
                    
            if self.control_panel_expanded:
                self.panel_animation['right']['target'] = 0.05
                self.control_panel_expanded = False
                if hasattr(self, 'right_panel_toggle'):
                    self.right_panel_toggle.set_text('◀')

    def handle_double_click(self, element, time_threshold=0.3):
        """
        Handle double-click detection for UI elements.
        
        Args:
            element: The UI element that was clicked
            time_threshold: Maximum time between clicks to count as double-click
        
        Returns:
            True if detected double-click, False otherwise
        """
        current_time = time.time()
        
        if not hasattr(self, 'last_click_data'):
            self.last_click_data = {}

        element_id = id(element)

        if element_id in self.last_click_data:
            last_time = self.last_click_data[element_id]['time']
            

            if current_time - last_time < time_threshold:

                del self.last_click_data[element_id]
                return True
        

        self.last_click_data[element_id] = {
            'time': current_time
        }
        
        for key in list(self.last_click_data.keys()):
            if current_time - self.last_click_data[key]['time'] > time_threshold:
                del self.last_click_data[key]
        
        return False

    def select_color(self, color_index):
        """
        Handle color selection or reset via double-click.
        
        Args:
            color_index: Index of the color button that was clicked
        """

        if hasattr(self, 'color_buttons') and self.handle_double_click(self.color_buttons[color_index]):
            if len(segment.color) > color_index:
                segment.color[color_index] = -1
                segment.rgb_color = segment.calculate_rgb()
                self.update_ui_from_segment()
            return
    
        if self.active_effect_id not in self.light_effects:
            return
            
        effect = self.light_effects[self.active_effect_id]
        
        if self.active_object_id not in effect.segments:
            return
            
        segment = effect.segments[self.active_object_id]
        
        if hasattr(self, 'color_buttons') and self.handle_double_click(self.color_buttons[color_index]):
            if len(segment.color) > color_index:
                segment.color[color_index] = -1
                segment.rgb_color = segment.calculate_rgb()
                self.update_ui_from_object()
            return

    def select_span_gradient_color(self, color_index):
        """
        Handle span gradient color selection or reset via double-click.
        
        Args:
            color_index: Index of the color button that was clicked
        """
        if self.active_effect_id not in self.light_effects:
            return
            
        effect = self.light_effects[self.active_effect_id]
        
        if self.active_object_id not in effect.segments:
            return
            
        segment = effect.segments[self.active_object_id]
        
        if hasattr(self, 'span_gradient_colors') and self.handle_double_click(self.span_gradient_colors[color_index]):
            if hasattr(segment, 'span_gradient_colors') and len(segment.span_gradient_colors) > color_index:
                segment.span_gradient_colors[color_index] = -1
                self.update_ui_from_object()
            return

        if self.current_palette not in self.palettes:
            return
            
        palette = self.palettes[self.current_palette]
        
    def select_gradient_color(self, color_index):
        """
        Open a color selection popup for gradient colors.
        
        Args:
            color_index: Index of the gradient color button that was clicked
        """
        if self.active_effect_id not in self.light_effects:
            return
            
        effect = self.light_effects[self.active_effect_id]
        
        if self.active_object_id not in effect.segments:
            return
            
        segment = effect.segments[self.active_object_id]

        if hasattr(self, 'gradient_colors') and self.handle_double_click(self.gradient_colors[color_index]):
            if not hasattr(segment, 'gradient_colors'):
                segment.gradient_colors = [-1, -1]
            
            segment.gradient_colors[color_index] = -1
            self.update_ui_from_object()
            return

        if self.current_palette not in self.palettes:
            return
            
        palette = self.palettes[self.current_palette]
        
        popup_width = min(300, self.width - 40)
        popup_height = min(240, self.height - 40)
        popup_rect = pygame.Rect(
            (self.width - popup_width) // 2,
            (self.height - popup_height) // 2,
            popup_width,
            popup_height
        )

        colors_per_row = 3
        color_size = min(60, (popup_width - 40) // colors_per_row)
        color_spacing = 10

        popup_window = pygame_gui.elements.UIWindow(
            rect=popup_rect,
            manager=self.manager,
            window_display_title=f"Select Gradient Color {color_index + 1}"
        )

        title_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, popup_width - 40, 20),
            text=f"Select a color from palette {self.current_palette}:",
            manager=self.manager,
            container=popup_window
        )

        color_buttons = []
        for i, color in enumerate(palette):
            row = i // colors_per_row
            col = i % colors_per_row
            
            x = col * (color_size + color_spacing) + color_spacing
            y = row * (color_size + color_spacing) + 40 
            
            button_rect = pygame.Rect(x, y, color_size, color_size)
            
            color_button = pygame_gui.elements.UIButton(
                relative_rect=button_rect,
                text='',
                manager=self.manager,
                container=popup_window,
                object_id=f"gradient_color_{i}"
            )
            
            color_button.colours['normal_bg'] = pygame.Color(color[0], color[1], color[2])
            color_button.colours['hovered_bg'] = pygame.Color(min(255, color[0] + 20), 
                                                        min(255, color[1] + 20), 
                                                        min(255, color[2] + 20))
            color_button.colours['active_bg'] = pygame.Color(min(255, color[0] + 40), 
                                                        min(255, color[1] + 40), 
                                                        min(255, color[2] + 40))
            color_button.rebuild()
            
            color_buttons.append((color_button, i))
            
            index_label = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(x, y + color_size + 2, color_size, 15),
                text=f"Color {i}",
                manager=self.manager,
                container=popup_window
            )

        cancel_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(popup_width - 100, popup_height - 40, 80, 30),
            text='Cancel',
            manager=self.manager,
            container=popup_window
        )

        self.gradient_selection_data = {
            'popup': popup_window,
            'color_index': color_index,
            'buttons': color_buttons,
            'cancel_button': cancel_button
        }


    def handle_osc_message(self, address, *args):
        pattern = r"/effect/(\d+)/object/(\d+)/(.+)"
        match = re.match(pattern, address)
        
        if match:
            effect_id = int(match.group(1))
            object_id = int(match.group(2))
            param_name = match.group(3)
            value = args[0]

            if effect_id == self.active_effect_id and object_id == self.active_object_id:
                self.update_ui_from_segment()
    

    def run(self):
        """
        Run the main simulation loop.
        """
        running = True
        last_time = time.time()
        
        while running:
            time_delta = time.time() - last_time
            last_time = time.time()

            mouse_pos = pygame.mouse.get_pos()

            self.update_panel_animations(time_delta)

            self.check_panel_hover(mouse_pos, time_delta)

            self.check_auto_hide(time_delta)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.VIDEORESIZE:
                    self.width, self.height = event.size
                    self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                    self.manager.set_window_resolution((self.width, self.height))
                    self.rebuild_ui()        

                elif event.type == pygame.MOUSEWHEEL:
                    if self.led_display_rect.collidepoint(pygame.mouse.get_pos()):

                        self.zoom_level = max(0.1, min(5.0, self.zoom_level + event.y * 0.1))

                        self.auto_hide['last_activity'] = time.time()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if self.led_display_rect.collidepoint(event.pos):
                            self.dragging = True
                            self.last_mouse_pos = event.pos

                            self.auto_hide['last_activity'] = time.time()
                
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.dragging = False

                        self.auto_hide['last_activity'] = time.time()
                
                elif event.type == pygame.MOUSEMOTION:
                    self.auto_hide['last_activity'] = time.time()

                    if self.dock_animation['enabled'] and self.led_display_rect.collidepoint(event.pos):
                        self.dock_animation['active'] = True
                        self.dock_animation['position'] = event.pos[0]
                        self.dock_animation['last_update'] = time.time()
                    else:

                        if self.dock_animation['active'] and time.time() - self.dock_animation['last_update'] > 0.2:
                            self.dock_animation['active'] = False
                    
                    if self.dragging:

                        dx = event.pos[0] - self.last_mouse_pos[0]
                        self.pan_offset += dx
                        self.last_mouse_pos = event.pos

                elif event.type == pygame.USEREVENT:
                    if event.user_type == pygame_gui.UI_BUTTON_PRESSED:

                        self.auto_hide['last_activity'] = time.time()
                        
                        if hasattr(self, 'top_panel_toggle') and event.ui_element == self.top_panel_toggle:
                            self.toggle_panel('top')
                        elif hasattr(self, 'right_panel_toggle') and event.ui_element == self.right_panel_toggle:
                            self.toggle_panel('right')

                        for section_id, section_data in self.panel_sections.items():
                            if 'toggle' in section_data and event.ui_element == section_data['toggle']:
                                self.toggle_section(section_id)
                        
                        if hasattr(self, 'play_button') and event.ui_element == self.play_button:
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
                            if self.active_effect_id in self.light_effects and \
                            self.active_object_id in self.light_effects[self.active_effect_id].segments:
                                segment = self.light_effects[self.active_effect_id].segments[self.active_object_id]
                                segment.is_edge_reflect = not segment.is_edge_reflect
                                self.reflect_toggle.set_text('ON' if segment.is_edge_reflect else 'OFF')
                        
                        elif hasattr(self, 'add_segment_button') and event.ui_element == self.add_segment_button:
                            self.add_new_object()
                        
                        elif hasattr(self, 'remove_segment_button') and event.ui_element == self.remove_segment_button:
                            self.remove_current_object()

                        elif hasattr(self, 'color_buttons') and event.ui_element in self.color_buttons:
                            self.select_color(self.color_buttons.index(event.ui_element))

                        elif hasattr(self, 'gradient_toggle') and event.ui_element == self.gradient_toggle:
                            if self.active_effect_id in self.light_effects and \
                            self.active_object_id in self.light_effects[self.active_effect_id].segments:
                                segment = self.light_effects[self.active_effect_id].segments[self.active_object_id]
                                segment.gradient_enabled = not segment.gradient_enabled
                                self.gradient_toggle.set_text('ON' if segment.gradient_enabled else 'OFF')

                        elif hasattr(self, 'gradient_colors') and event.ui_element in self.gradient_colors:
                            idx = self.gradient_colors.index(event.ui_element)
                            self.select_gradient_color(idx)

                        elif hasattr(self, 'fade_toggle') and event.ui_element == self.fade_toggle:
                            if self.active_effect_id in self.light_effects and \
                            self.active_object_id in self.light_effects[self.active_effect_id].segments:
                                segment = self.light_effects[self.active_effect_id].segments[self.active_object_id]
                                segment.fade_enabled = not segment.fade_enabled
                                self.fade_toggle.set_text('ON' if segment.fade_enabled else 'OFF')

                        elif hasattr(self, 'span_gradient_toggle') and event.ui_element == self.span_gradient_toggle:
                            if self.active_effect_id in self.light_effects and \
                            self.active_object_id in self.light_effects[self.active_effect_id].segments:
                                segment = self.light_effects[self.active_effect_id].segments[self.active_object_id]
                                segment.span_gradient_enabled = not segment.span_gradient_enabled
                                self.span_gradient_toggle.set_text('ON' if segment.span_gradient_enabled else 'OFF')

                        elif hasattr(self, 'span_gradient_colors') and event.ui_element in self.span_gradient_colors:
                            idx = self.span_gradient_colors.index(event.ui_element)
                            self.select_span_gradient_color(idx)

                        if hasattr(self, 'gradient_selection_data'):
                            if event.ui_element == self.gradient_selection_data['cancel_button']:
                                self.gradient_selection_data['popup'].kill()
                                delattr(self, 'gradient_selection_data')
                            else:
                                for button, palette_idx in self.gradient_selection_data['buttons']:
                                    if event.ui_element == button:

                                        if self.active_effect_id in self.light_effects and \
                                        self.active_object_id in self.light_effects[self.active_effect_id].segments:
                                            segment = self.light_effects[self.active_effect_id].segments[self.active_object_id]
                                            gradient_idx = self.gradient_selection_data['color_index']
                                            
                                            if not hasattr(segment, 'gradient_colors'):
                                                segment.gradient_colors = [-1, -1]
                                            
                                            while len(segment.gradient_colors) <= gradient_idx:
                                                segment.gradient_colors.append(-1)
                                            
                                            segment.gradient_colors[gradient_idx] = palette_idx
                                            self.update_ui_from_object()
                                        

                                        self.gradient_selection_data['popup'].kill()
                                        delattr(self, 'gradient_selection_data')
                                        break

                        if hasattr(self, 'span_gradient_selection_data'):
                            if event.ui_element == self.span_gradient_selection_data['cancel_button']:
                                self.span_gradient_selection_data['popup'].kill()
                                delattr(self, 'span_gradient_selection_data')
                            else:
                                for button, palette_idx in self.span_gradient_selection_data['buttons']:
                                    if event.ui_element == button:

                                        if self.active_effect_id in self.light_effects and \
                                        self.active_object_id in self.light_effects[self.active_effect_id].segments:
                                            segment = self.light_effects[self.active_effect_id].segments[self.active_object_id]
                                            gradient_idx = self.span_gradient_selection_data['color_index']
                                            
                                            if not hasattr(segment, 'span_gradient_colors'):
                                                segment.span_gradient_colors = [-1, -1, -1, -1, -1, -1]
                                            
                                            while len(segment.span_gradient_colors) <= gradient_idx:
                                                segment.span_gradient_colors.append(-1)
                                            
                                            segment.span_gradient_colors[gradient_idx] = palette_idx
                                            self.update_ui_from_object()

                                        self.span_gradient_selection_data['popup'].kill()
                                        delattr(self, 'span_gradient_selection_data')
                                        break

                    elif event.user_type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:

                        self.auto_hide['last_activity'] = time.time()
                        

                        if hasattr(self, 'fps_slider') and event.ui_element == self.fps_slider:
                            self.fps = int(event.value)
                            if hasattr(self, 'fps_value_label'):
                                self.fps_value_label.set_text(str(self.fps))
                            

                            for effect in self.light_effects.values():
                                effect.fps = self.fps

                        elif self.active_effect_id in self.light_effects and \
                            self.active_object_id in self.light_effects[self.active_effect_id].segments:
                            segment = self.light_effects[self.active_effect_id].segments[self.active_object_id]
                            
                            if hasattr(self, 'speed_slider') and event.ui_element == self.speed_slider:
                                segment.update_param('move_speed', event.value)

                            elif hasattr(self, 'position_slider') and event.ui_element == self.position_slider:
                                segment.update_param('current_position', event.value)
                            

                            elif hasattr(self, 'range_min_slider') and event.ui_element == self.range_min_slider:
                                segment.update_param('move_range', [event.value, segment.move_range[1]])
                            elif hasattr(self, 'range_max_slider') and event.ui_element == self.range_max_slider:
                                segment.update_param('move_range', [segment.move_range[0], event.value])
                            
                            elif hasattr(self, 'dimmer_sliders') and event.ui_element in self.dimmer_sliders:
                                idx = self.dimmer_sliders.index(event.ui_element)
                                if idx < len(segment.dimmer_time):
                                    new_dimmer_time = segment.dimmer_time.copy()
                                    new_dimmer_time[idx] = int(event.value)
                                    segment.update_param('dimmer_time', new_dimmer_time)
                            
                            elif hasattr(self, 'interval_slider') and event.ui_element == self.interval_slider:
                                segment.update_param('interval', int(event.value))
                            
                            elif hasattr(self, 'span_width_slider') and event.ui_element == self.span_width_slider:
                                segment.update_param('span_width', int(event.value))
                            
                            elif hasattr(self, 'span_range_min_slider') and event.ui_element == self.span_range_min_slider:
                                segment.update_param('span_range', [int(event.value), segment.span_range[1]])
                            elif hasattr(self, 'span_range_max_slider') and event.ui_element == self.span_range_max_slider:
                                segment.update_param('span_range', [segment.span_range[0], int(event.value)])
                            
                            elif hasattr(self, 'span_speed_slider') and event.ui_element == self.span_speed_slider:
                                segment.update_param('span_speed', int(event.value))

                            elif hasattr(self, 'span_interval_slider') and event.ui_element == self.span_interval_slider:
                                segment.update_param('span_interval', int(event.value))
                    
                    elif event.user_type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:

                        self.auto_hide['last_activity'] = time.time()
                        
                        if hasattr(self, 'effect_dropdown') and event.ui_element == self.effect_dropdown:
                            self.active_effect_id = int(event.text)
                            self.update_ui_from_object()
                        
                        elif hasattr(self, 'segment_dropdown') and event.ui_element == self.segment_dropdown:
                            self.active_object_id = int(event.text)
                            self.update_ui_from_object()
                        
                        elif hasattr(self, 'palette_dropdown') and event.ui_element == self.palette_dropdown:
                            self.current_palette = event.text
                            self.update_ui_from_object()
                
                self.manager.process_events(event)

            self.manager.update(time_delta)
        
            if self.is_playing:
                for effect in self.light_effects.values():
                    effect.update_all()

            self.draw()

            pygame.display.flip()

            self.clock.tick(self.fps)
        
        pygame.quit()