import pygame
import pygame_gui
import sys
import os
from typing import Dict, List, Tuple, Optional
import time
import math
import threading

sys.path.append('..')
from models.light_effect import LightEffect
from config import (
    UI_WIDTH, UI_HEIGHT, UI_BACKGROUND_COLOR, DEFAULT_COLOR_PALETTES,
    DEFAULT_FPS, DEFAULT_LED_COUNT
)

class LEDSimulator:
    """
    A completely redesigned LED tape light simulator with a focus on separation of concerns
    and robust state management to prevent UI/interaction bugs.
    """
    def __init__(self, light_effects: Dict[int, LightEffect]):
        """
        Initialize the simulator with the provided light effects.
        
        Args:
            light_effects: Dictionary of LightEffect instances keyed by effect_ID
        """
        pygame.init()
        
        self.effects = light_effects
        self.active_effect_id = min(light_effects.keys()) if light_effects else 1
        self.active_segment_id = 1
        self.current_palette = "A"
        self.palettes = DEFAULT_COLOR_PALETTES.copy()
        
        self.is_playing = True
        self.fps = DEFAULT_FPS
        
        self.screen = pygame.display.set_mode((UI_WIDTH, UI_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("LED Tape Light Simulator")
        
        self.ui_state = {
            'width': UI_WIDTH,
            'height': UI_HEIGHT,
            'top_panel_height': 80,
            'control_panel_width': 300,
            'top_panel_expanded': True, 
            'control_panel_expanded': True, 
            'auto_hide_enabled': False, 
            'resizing': False,
            'resize_time': 0
        }
        
        self.led_state = {
            'size': 8,
            'spacing': 1,
            'zoom': 1.0,
            'pan': 0,
            'dragging': False,
            'last_mouse': (0, 0)
        }
        
        self.activity = {
            'last_time': time.time(),
            'timeout': 60.0
        }
        
        theme_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'theme.json')
        self.manager = pygame_gui.UIManager((self.ui_state['width'], self.ui_state['height']), 
                                            theme_path if os.path.exists(theme_path) else None)

        self.rects = self._calculate_layout()
        
        self.ui_lock = threading.Lock()
        
        self.ui_elements = {}
        self._build_ui()
        self._center_view()
        

        self.clock = pygame.time.Clock()

    def _calculate_layout(self) -> Dict[str, pygame.Rect]:
        """
        Calculate layout rectangles based on current UI state.
        
        Returns:
            Dictionary of named rectangles for different UI areas
        """
        top_height = self.ui_state['top_panel_height'] if self.ui_state['top_panel_expanded'] else 20
        ctrl_width = self.ui_state['control_panel_width'] if self.ui_state['control_panel_expanded'] else 20
        
        return {
            'top': pygame.Rect(0, 0, self.ui_state['width'], top_height),
            'control': pygame.Rect(
                self.ui_state['width'] - ctrl_width, top_height,
                ctrl_width, self.ui_state['height'] - top_height
            ),
            'display': pygame.Rect(
                0, top_height,
                self.ui_state['width'] - ctrl_width, self.ui_state['height'] - top_height
            )
        }
    
    def _build_ui(self):
        """
        Build all UI elements. This separates UI construction from the initialization.
        """
        self.manager.clear_and_reset()
        self.ui_elements = {}

        self._add_panel_toggles()
        
        if self.ui_state['top_panel_expanded']:
            self._build_top_panel()

        if self.ui_state['control_panel_expanded']:
            self._build_control_panel()

    def _add_panel_toggles(self):
        """Add toggle buttons for expanding/collapsing panels."""
        # Top panel toggle (centered at bottom of top panel)
        toggle_size = 30
        self.ui_elements['top_toggle'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                self.ui_state['width']//2 - toggle_size//2, 
                self.rects['top'].height - 15,
                toggle_size, 15
            ),
            text='▼' if self.ui_state['top_panel_expanded'] else '▲',
            manager=self.manager,
            tool_tip_text="Toggle Top Panel"
        )
        
        # Right panel toggle (centered on left edge of control panel)
        self.ui_elements['control_toggle'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                self.rects['control'].x - 15,
                self.ui_state['height']//2 - toggle_size//2,
                15, toggle_size
            ),
            text='▶' if self.ui_state['control_panel_expanded'] else '◀',
            manager=self.manager,
            tool_tip_text="Toggle Control Panel"
        )

        button_size = 40

        self.ui_elements['show_top_panel'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                self.ui_state['width'] - button_size - 10, 
                10,
                button_size, button_size
            ),
            text='▼' if self.ui_state['top_panel_expanded'] else '▲',
            manager=self.manager,
            tool_tip_text="Show/Hide Top Panel"
        )

        self.ui_elements['show_control_panel'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                self.ui_state['width'] - button_size*2 - 20, 
                10,
                button_size, button_size
            ),
            text='◀' if self.ui_state['control_panel_expanded'] else '▶',
            manager=self.manager,
            tool_tip_text="Show/Hide Control Panel"
        )

    def _build_top_panel(self):
        """Build the top panel UI elements."""

        use_two_rows = self.ui_state['width'] < 1400
        print(f"Window width: {self.ui_state['width']}, Using two rows: {use_two_rows}")
        
        if use_two_rows:
            self._build_top_panel_two_rows()
        else:
            self._build_top_panel_one_row()
    
    def _build_top_panel_two_rows(self):
        """Build top panel UI with a two-row layout."""

        row1_y = 10
        

        self.ui_elements['play_button'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10, row1_y, 80, 30),
            text='Pause' if self.is_playing else 'Play',
            manager=self.manager,
            tool_tip_text="Play/Pause Animation"
        )
        

        self.ui_elements['fps_label'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(100, row1_y, 50, 30),
            text='FPS:',
            manager=self.manager
        )
        
        self.ui_elements['fps_slider'] = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(150, row1_y + 5, 150, 20),
            start_value=self.fps,
            value_range=(1, 120),
            manager=self.manager
        )
        
        self.ui_elements['fps_value'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(310, row1_y, 50, 30),
            text=str(self.fps),
            manager=self.manager
        )
        

        self.ui_elements['effect_label'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(370, row1_y, 80, 30),
            text='Effect ID:',
            manager=self.manager
        )
        

        self.ui_elements['effect_buttons'] = []
        button_x = 460
        button_width = 45
        for i, effect_id in enumerate(sorted(self.effects.keys())):
            x_pos = button_x + i * button_width
            button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(x_pos, row1_y, 40, 30),
                text=str(effect_id),
                manager=self.manager,
                tool_tip_text=f"Select Effect {effect_id}"
            )
            self.ui_elements['effect_buttons'].append((button, effect_id))
        

        row2_y = 45
        

        self.ui_elements['zoom_label'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, row2_y, 60, 30),
            text='Zoom:',
            manager=self.manager
        )
        
        self.ui_elements['zoom_in'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(70, row2_y, 40, 30),
            text='+',
            manager=self.manager,
            tool_tip_text="Zoom In"
        )
        
        self.ui_elements['zoom_out'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(115, row2_y, 40, 30),
            text='-',
            manager=self.manager,
            tool_tip_text="Zoom Out"
        )
        
        self.ui_elements['zoom_reset'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(165, row2_y, 120, 30),
            text='Reset View',
            manager=self.manager,
            tool_tip_text="Reset Zoom and Pan"
        )
        
        self.ui_elements['center_view'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(295, row2_y, 120, 30),
            text='Center View',
            manager=self.manager,
            tool_tip_text="Center View on Segments"
        )
    
    def _build_top_panel_one_row(self):
        """Build top panel UI with a single-row layout."""
        row_y = 10
        

        self.ui_elements['play_button'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10, row_y, 80, 30),
            text='Pause' if self.is_playing else 'Play',
            manager=self.manager,
            tool_tip_text="Play/Pause Animation"
        )
        

        self.ui_elements['fps_label'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(100, row_y, 50, 30),
            text='FPS:',
            manager=self.manager
        )
        
        self.ui_elements['fps_slider'] = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(150, row_y + 5, 150, 20),
            start_value=self.fps,
            value_range=(1, 120),
            manager=self.manager
        )
        
        self.ui_elements['fps_value'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(310, row_y, 50, 30),
            text=str(self.fps),
            manager=self.manager
        )
        

        self.ui_elements['effect_label'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(370, row_y, 80, 30),
            text='Effect ID:',
            manager=self.manager
        )
        

        self.ui_elements['effect_buttons'] = []
        button_x = 460
        button_width = 45
        for i, effect_id in enumerate(sorted(self.effects.keys())):
            x_pos = button_x + i * button_width
            button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(x_pos, row_y, 40, 30),
                text=str(effect_id),
                manager=self.manager,
                tool_tip_text=f"Select Effect {effect_id}"
            )
            self.ui_elements['effect_buttons'].append((button, effect_id))
        

        zoom_x = x_pos + 50  # Position after the last effect button
        

        self.ui_elements['zoom_label'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(zoom_x, row_y, 60, 30),
            text='Zoom:',
            manager=self.manager
        )
        
        self.ui_elements['zoom_in'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(zoom_x + 60, row_y, 40, 30),
            text='+',
            manager=self.manager,
            tool_tip_text="Zoom In"
        )
        
        self.ui_elements['zoom_out'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(zoom_x + 105, row_y, 40, 30),
            text='-',
            manager=self.manager,
            tool_tip_text="Zoom Out"
        )
        
        self.ui_elements['zoom_reset'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(zoom_x + 150, row_y, 120, 30),
            text='Reset View',
            manager=self.manager,
            tool_tip_text="Reset Zoom and Pan"
        )
        
        self.ui_elements['center_view'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(zoom_x + 275, row_y, 120, 30),
            text='Center View',
            manager=self.manager,
            tool_tip_text="Center View on Segments"
        )
    
    def _build_control_panel(self):
        """Build the right control panel UI elements."""
        panel_y = 10
        panel_width = self.rects['control'].width
        

        label_width = 120
        self.ui_elements['palette_label'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                self.rects['control'].x + (panel_width - label_width) // 2, 
                panel_y, 
                label_width, 20
            ),
            text='Color Palette:',
            manager=self.manager
        )
        
        panel_y += 25
        

        self.ui_elements['palette_buttons'] = []
        button_width = 35
        palette_width = len(self.palettes.keys()) * button_width
        start_x = self.rects['control'].x + (panel_width - palette_width) // 2
        
        for i, palette_id in enumerate(sorted(self.palettes.keys())):
            x_pos = start_x + i * button_width
            button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(x_pos, panel_y, 30, 30),
                text=palette_id,
                manager=self.manager,
                tool_tip_text=f"Select Palette {palette_id}"
            )
            self.ui_elements['palette_buttons'].append((button, palette_id))
        
        panel_y += 40
        

        self.ui_elements['palette_rect'] = pygame.Rect(
            self.rects['control'].x + 10, panel_y, 
            panel_width - 20, 40
        )
        
        panel_y += 50
        

        self.ui_elements['segment_label'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(self.rects['control'].x + 10, panel_y, 100, 20),
            text='Segment ID:',
            manager=self.manager
        )
        

        segments = []
        if self.active_effect_id in self.effects:
            segments = sorted(self.effects[self.active_effect_id].segments.keys())
        else:
            segments = [1]
        

        self.ui_elements['segment_buttons'] = []
        for i, segment_id in enumerate(segments):
            x_pos = self.rects['control'].x + 120 + i * 35
            button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(x_pos, panel_y, 30, 30),
                text=str(segment_id),
                manager=self.manager,
                tool_tip_text=f"Select Segment {segment_id}"
            )
            self.ui_elements['segment_buttons'].append((button, segment_id))
        
        panel_y += 40
        

        segment = self._get_active_segment()
        if segment:

            self._build_segment_controls(segment, panel_y)
    
    def _build_segment_controls(self, segment, panel_y):
        """
        Build UI controls for the given segment.
        
        Args:
            segment: The segment to build controls for
            panel_y: Starting Y position for controls
        """
        panel_x = self.rects['control'].x
        panel_width = self.rects['control'].width
        

        self.ui_elements['speed_heading'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(panel_x + 10, panel_y, panel_width - 20, 20),
            text='Speed & Position',
            manager=self.manager
        )
        panel_y += 30
        

        self.ui_elements['speed_label'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(panel_x + 10, panel_y, 100, 20),
            text='Move Speed:',
            manager=self.manager
        )
        
        panel_y += 25
        
        self.ui_elements['speed_slider'] = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(panel_x + 10, panel_y, panel_width - 20, 20),
            start_value=segment.move_speed,
            value_range=(-128, 127),
            manager=self.manager
        )
        
        panel_y += 30
        

        self.ui_elements['position_label'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(panel_x + 10, panel_y, 100, 20),
            text='Position:',
            manager=self.manager
        )
        
        panel_y += 25
        

        position = max(segment.move_range[0], min(segment.move_range[1], segment.current_position))
        
        self.ui_elements['position_slider'] = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(panel_x + 10, panel_y, panel_width - 20, 20),
            start_value=position,
            value_range=(segment.move_range[0], max(segment.move_range[0] + 1, segment.move_range[1])),
            manager=self.manager
        )
        
        panel_y += 30
        

        self.ui_elements['range_label'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(panel_x + 10, panel_y, 100, 20),
            text='Move Range:',
            manager=self.manager
        )
        
        panel_y += 25
        
        range_width = (panel_width - 30) / 2
        
        self.ui_elements['range_min'] = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(panel_x + 10, panel_y, range_width, 20),
            start_value=segment.move_range[0],
            value_range=(0, DEFAULT_LED_COUNT - 1),
            manager=self.manager
        )
        
        self.ui_elements['range_max'] = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(panel_x + 10 + range_width + 10, panel_y, range_width, 20),
            start_value=segment.move_range[1],
            value_range=(0, DEFAULT_LED_COUNT - 1),
            manager=self.manager
        )
        
        panel_y += 30
        

        self.ui_elements['reflect_label'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(panel_x + 10, panel_y, 150, 20),
            text='Edge Reflection:',
            manager=self.manager
        )
        
        self.ui_elements['reflect_toggle'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(panel_x + 170, panel_y, panel_width - 180, 20),
            text='ON' if segment.is_edge_reflect else 'OFF',
            manager=self.manager
        )
        
        panel_y += 40
        

        self._build_color_settings(segment, panel_y)
    
    def _build_color_settings(self, segment, panel_y):
        """
        Build color settings controls for the given segment.
        
        Args:
            segment: The segment to build controls for
            panel_y: Starting Y position for controls
        """
        panel_x = self.rects['control'].x
        panel_width = self.rects['control'].width
        

        self.ui_elements['color_heading'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(panel_x + 10, panel_y, panel_width - 20, 20),
            text='Color Settings',
            manager=self.manager
        )
        panel_y += 30
        

        self.ui_elements['color_buttons'] = []
        button_size = 50
        button_spacing = 10
        color_per_row = max(1, min(4, (panel_width - 20) // (button_size + button_spacing)))
        
        for i, color_idx in enumerate(segment.color):
            row = i // color_per_row
            col = i % color_per_row
            
            x = panel_x + 10 + col * (button_size + button_spacing)
            y = panel_y + row * (button_size + button_spacing)
            

            label = str(color_idx) if color_idx >= 0 else "-"
            
            button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(x, y, button_size, button_size),
                text=label,
                manager=self.manager,
                tool_tip_text=f"Color {i+1}"
            )
            
            self.ui_elements['color_buttons'].append((button, i))
        
        panel_y += (((len(segment.color) - 1) // color_per_row) + 1) * (button_size + button_spacing) + 10
        

        self.ui_elements['gradient_label'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(panel_x + 10, panel_y, 150, 20),
            text='Gradient:',
            manager=self.manager
        )
        

        gradient_enabled = hasattr(segment, 'gradient') and segment.gradient
        
        self.ui_elements['gradient_toggle'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(panel_x + 170, panel_y, panel_width - 180, 20),
            text='ON' if gradient_enabled else 'OFF',
            manager=self.manager
        )
        
        panel_y += 30
        

        if gradient_enabled:
            self.ui_elements['gradient_color_label'] = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(panel_x + 10, panel_y, 150, 20),
                text='Gradient Colors:',
                manager=self.manager
            )
            panel_y += 25
            
            self.ui_elements['gradient_buttons'] = []
            button_size = 40
            button_spacing = 10
            

            left_button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(panel_x + 10, panel_y, button_size, button_size),
                text=str(segment.gradient_colors[1]) if segment.gradient_colors[1] >= 0 else "-",
                manager=self.manager,
                tool_tip_text="Left Gradient Color"
            )
            self.ui_elements['gradient_buttons'].append((left_button, 1))
            

            right_button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(panel_x + 10 + button_size + button_spacing, 
                                         panel_y, button_size, button_size),
                text=str(segment.gradient_colors[2]) if segment.gradient_colors[2] >= 0 else "-",
                manager=self.manager,
                tool_tip_text="Right Gradient Color"
            )
            self.ui_elements['gradient_buttons'].append((right_button, 2))
            
            panel_y += button_size + button_spacing
        

        self.ui_elements['fade_label'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(panel_x + 10, panel_y, 150, 20),
            text='Fade Effect:',
            manager=self.manager
        )
        

        fade_enabled = hasattr(segment, 'fade') and segment.fade
        
        self.ui_elements['fade_toggle'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(panel_x + 170, panel_y, panel_width - 180, 20),
            text='ON' if fade_enabled else 'OFF',
            manager=self.manager
        )
        
        panel_y += 40
        

        self._build_dimmer_settings(segment, panel_y)
    
    def _build_dimmer_settings(self, segment, panel_y):
        """
        Build dimmer settings controls for the given segment.
        
        Args:
            segment: The segment to build controls for
            panel_y: Starting Y position for controls
        """
        panel_x = self.rects['control'].x
        panel_width = self.rects['control'].width
        

        self.ui_elements['dimmer_heading'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(panel_x + 10, panel_y, panel_width - 20, 20),
            text='Dimmer Settings (Fade)',
            manager=self.manager
        )
        panel_y += 30
        

        self.ui_elements['dimmer_sliders'] = []
        labels = ["Fade In Start", "Fade In End", "Fade Out Start", "Fade Out End", "Cycle Length"]
        
        for i, label in enumerate(labels):
            if i >= len(segment.dimmer_time):
                break
                
            label_element = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(panel_x + 10, panel_y, panel_width - 20, 20),
                text=label,
                manager=self.manager
            )
            
            panel_y += 20
            
            slider = pygame_gui.elements.UIHorizontalSlider(
                relative_rect=pygame.Rect(panel_x + 10, panel_y, panel_width - 20, 20),
                start_value=segment.dimmer_time[i],
                value_range=(0, 1000),
                manager=self.manager
            )
            
            self.ui_elements['dimmer_sliders'].append((slider, i, label_element))
            panel_y += 30
    
    def _get_active_segment(self):
        """
        Get the currently active segment.
        
        Returns:
            The active segment, or None if not found
        """
        if (self.active_effect_id in self.effects and 
            self.active_segment_id in self.effects[self.active_effect_id].segments):
            return self.effects[self.active_effect_id].segments[self.active_segment_id]
        return None
    
    def _center_view(self):
        """Center the view on the active segments."""
        if self.active_effect_id in self.effects:
            effect = self.effects[self.active_effect_id]
            

            positions = []
            for segment in effect.segments.values():
                positions.append(segment.current_position)
            
            if positions:

                center_pos = sum(positions) / len(positions)
                view_center = self.rects['display'].width / 2
                led_width = (self.led_state['size'] + self.led_state['spacing']) * self.led_state['zoom']
                

                self.led_state['pan'] = view_center - center_pos * led_width
    
    def handle_events(self):
        """
        Process pygame events and update UI state.
        
        Returns:
            bool: False if application should quit, True otherwise
        """

        mouse_pos = pygame.mouse.get_pos()
        

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                return False
            

            elif event.type == pygame.VIDEORESIZE:
                self._handle_resize(event)
            

            elif event.type == pygame.MOUSEWHEEL:
                if self.rects['display'].collidepoint(mouse_pos):
                    self._handle_mouse_wheel_zoom(event, mouse_pos)
                    self.activity['last_time'] = time.time()
            

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and self.rects['display'].collidepoint(mouse_pos): 
                    self.led_state['dragging'] = True
                    self.led_state['last_mouse'] = mouse_pos
                    self.activity['last_time'] = time.time()
            

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.led_state['dragging'] = False
                    self.activity['last_time'] = time.time()
            

            elif event.type == pygame.MOUSEMOTION:
                self._handle_mouse_motion(mouse_pos)
            

            elif event.type == pygame.USEREVENT:
                if hasattr(event, 'user_type'):

                    if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                        self._handle_button_press(event.ui_element)
                        self.activity['last_time'] = time.time()
                    

                    elif event.user_type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
                        self._handle_slider_movement(event.ui_element, event.value)
                        self.activity['last_time'] = time.time()
            

            self.manager.process_events(event)
        

        if self.ui_state['resizing'] and time.time() - self.ui_state['resize_time'] > 0.2:
            self._complete_resize()
        

        if time.time() - self.activity['last_time'] > self.activity['timeout']:
            if self.ui_state['top_panel_expanded'] or self.ui_state['control_panel_expanded']:
                with self.ui_lock:
                    self.ui_state['top_panel_expanded'] = False
                    self.ui_state['control_panel_expanded'] = False
                    self.rects = self._calculate_layout()
                    self._build_ui()
                    
        return True
    
    def _handle_resize(self, event):
        """
        Handle window resize event.
        
        Args:
            event: The pygame resize event
        """
        self.ui_state['resizing'] = True
        self.ui_state['resize_time'] = time.time()
        

        self.ui_state['width'] = max(event.size[0], UI_WIDTH) 
        self.ui_state['height'] = max(event.size[1], UI_HEIGHT)
        

        self.screen = pygame.display.set_mode(
            (self.ui_state['width'], self.ui_state['height']), 
            pygame.RESIZABLE
        )
        

        self.rects = self._calculate_layout()
        

        self.activity['last_time'] = time.time()
    
    def _handle_mouse_wheel_zoom(self, event, mouse_pos):
        """
        Handle mouse wheel zoom.
        
        Args:
            event: The pygame mouse wheel event
            mouse_pos: Current mouse position
        """

        old_zoom = self.led_state['zoom']
        

        self.led_state['zoom'] = max(0.1, min(5.0, self.led_state['zoom'] + event.y * 0.1))
        

        if old_zoom != self.led_state['zoom']:
            zoom_factor = self.led_state['zoom'] / old_zoom
            mouse_x_rel = mouse_pos[0] - self.rects['display'].x - self.led_state['pan']
            new_pan = self.led_state['pan'] - mouse_x_rel * (zoom_factor - 1)
            self.led_state['pan'] = new_pan
    
    def _handle_mouse_motion(self, mouse_pos):
        """
        Handle mouse motion events.
        
        Args:
            mouse_pos: Current mouse position
        """

        if self.led_state['dragging'] and self.rects['display'].collidepoint(mouse_pos):
            dx = mouse_pos[0] - self.led_state['last_mouse'][0]
            self.led_state['pan'] += dx
            self.led_state['last_mouse'] = mouse_pos
            self.activity['last_time'] = time.time()
        

        if not self.ui_state['top_panel_expanded'] and mouse_pos[1] < 20:
            with self.ui_lock:
                self.ui_state['top_panel_expanded'] = True
                self.rects = self._calculate_layout()
                self._build_ui()
                self.activity['last_time'] = time.time()
        
        if not self.ui_state['control_panel_expanded'] and mouse_pos[0] > self.ui_state['width'] - 20:
            with self.ui_lock:
                self.ui_state['control_panel_expanded'] = True
                self.rects = self._calculate_layout()
                self._build_ui()
                self.activity['last_time'] = time.time()
    
    def _handle_button_press(self, ui_element):
        """
        Handle button press events.
        
        Args:
            ui_element: The UI element that was pressed
        """
        if ui_element == self.ui_elements.get('top_toggle') or ui_element == self.ui_elements.get('show_top_panel'):
            self._toggle_panel('top')
        elif ui_element == self.ui_elements.get('control_toggle') or ui_element == self.ui_elements.get('show_control_panel'):
            self._toggle_panel('control')

        elif ui_element == self.ui_elements.get('play_button'):
            self.is_playing = not self.is_playing
            self.ui_elements['play_button'].set_text('Pause' if self.is_playing else 'Play')
        

        elif ui_element == self.ui_elements.get('zoom_in'):
            self._zoom_in()
        elif ui_element == self.ui_elements.get('zoom_out'):
            self._zoom_out()
        elif ui_element == self.ui_elements.get('zoom_reset'):
            self.led_state['zoom'] = 1.0
            self.led_state['pan'] = 0
        elif ui_element == self.ui_elements.get('center_view'):
            self._center_view()
        

        if 'effect_buttons' in self.ui_elements:
            for button, effect_id in self.ui_elements['effect_buttons']:
                if ui_element == button:
                    self.active_effect_id = effect_id
                    

                    if self.active_effect_id in self.effects:
                        segments = sorted(self.effects[self.active_effect_id].segments.keys())
                        if segments:
                            self.active_segment_id = segments[0]
                    

                    with self.ui_lock:
                        self._build_ui()
                    break
        

        if 'segment_buttons' in self.ui_elements:
            for button, segment_id in self.ui_elements['segment_buttons']:
                if ui_element == button:
                    self.active_segment_id = segment_id
                    

                    with self.ui_lock:
                        self._build_ui()
                    break
        

        if 'palette_buttons' in self.ui_elements:
            for button, palette_id in self.ui_elements['palette_buttons']:
                if ui_element == button:
                    self.current_palette = palette_id
                    

                    for effect in self.effects.values():
                        effect.current_palette = self.current_palette
                    

                    with self.ui_lock:
                        self._build_ui()
                    break
        

        if 'color_buttons' in self.ui_elements:
            for button, color_index in self.ui_elements['color_buttons']:
                if ui_element == button:
                    self._cycle_color(color_index)
                    break
        

        if 'gradient_buttons' in self.ui_elements:
            for button, color_position in self.ui_elements['gradient_buttons']:
                if ui_element == button:
                    self._cycle_gradient_color(color_position)
                    break
        

        segment = self._get_active_segment()
        if segment:

            if ui_element == self.ui_elements.get('reflect_toggle'):
                segment.is_edge_reflect = not segment.is_edge_reflect
                self.ui_elements['reflect_toggle'].set_text('ON' if segment.is_edge_reflect else 'OFF')
            

            elif ui_element == self.ui_elements.get('gradient_toggle'):
                if hasattr(segment, 'gradient'):
                    segment.gradient = not segment.gradient
                    if segment.gradient and hasattr(segment, 'gradient_colors') and segment.gradient_colors[0] == 0:
                        segment.gradient_colors[0] = 1
                    self.ui_elements['gradient_toggle'].set_text('ON' if segment.gradient else 'OFF')
                    

                    with self.ui_lock:
                        self._build_ui()
            

            elif ui_element == self.ui_elements.get('fade_toggle'):
                if hasattr(segment, 'fade'):
                    segment.fade = not segment.fade
                    self.ui_elements['fade_toggle'].set_text('ON' if segment.fade else 'OFF')
    
    def _handle_slider_movement(self, ui_element, value):
        """
        Handle slider movement events.
        
        Args:
            ui_element: The UI element that was moved
            value: The new value of the slider
        """

        if ui_element == self.ui_elements.get('fps_slider'):
            self.fps = int(value)
            if 'fps_value' in self.ui_elements:
                self.ui_elements['fps_value'].set_text(str(self.fps))
            

            for effect in self.effects.values():
                effect.fps = self.fps
        

        segment = self._get_active_segment()
        if segment:

            if ui_element == self.ui_elements.get('speed_slider'):
                segment.move_speed = value
            

            elif ui_element == self.ui_elements.get('position_slider'):
                segment.current_position = float(value)
            

            elif ui_element == self.ui_elements.get('range_min'):

                segment.move_range = [value, max(value + 1, segment.move_range[1])]
                

                if 'position_slider' in self.ui_elements:
                    self.ui_elements['position_slider'].value_range = (
                        segment.move_range[0], 
                        segment.move_range[1]
                    )
                    self.ui_elements['position_slider'].update(0)
            
            elif ui_element == self.ui_elements.get('range_max'):

                segment.move_range = [min(segment.move_range[0], value - 1), value]
                

                if 'position_slider' in self.ui_elements:
                    self.ui_elements['position_slider'].value_range = (
                        segment.move_range[0], 
                        segment.move_range[1]
                    )
                    self.ui_elements['position_slider'].update(0)
            

            if 'dimmer_sliders' in self.ui_elements:
                for slider, dimmer_index, _ in self.ui_elements['dimmer_sliders']:
                    if ui_element == slider:
                        dimmer_time = segment.dimmer_time.copy()
                        dimmer_time[dimmer_index] = int(value)
                        segment.dimmer_time = dimmer_time
                        break
    
    def _toggle_panel(self, panel):
        """
        Toggle panel expansion state.
        
        Args:
            panel: Which panel to toggle ('top' or 'control')
        """
        with self.ui_lock:
            if panel == 'top':
                self.ui_state['top_panel_expanded'] = not self.ui_state['top_panel_expanded']
            elif panel == 'control':
                self.ui_state['control_panel_expanded'] = not self.ui_state['control_panel_expanded']
            

            self.rects = self._calculate_layout()
            self._build_ui()
    
    def _complete_resize(self):
        """Complete the resize operation by updating UI manager and rebuilding UI."""
        self.ui_state['resizing'] = False
        
        with self.ui_lock:

            self.manager.set_window_resolution((self.ui_state['width'], self.ui_state['height']))
            

            self._build_ui()
    
    def _zoom_in(self):
        """Zoom in on the LED display."""
        old_zoom = self.led_state['zoom']
        self.led_state['zoom'] = min(5.0, self.led_state['zoom'] * 1.2)
        

        if old_zoom != self.led_state['zoom']:
            center = self.rects['display'].width / 2
            center_led = (center - self.led_state['pan']) / (old_zoom * (self.led_state['size'] + self.led_state['spacing']))
            self.led_state['pan'] = center - center_led * self.led_state['zoom'] * (self.led_state['size'] + self.led_state['spacing'])
    
    def _zoom_out(self):
        """Zoom out on the LED display."""
        old_zoom = self.led_state['zoom']
        self.led_state['zoom'] = max(0.1, self.led_state['zoom'] / 1.2)
        

        if old_zoom != self.led_state['zoom']:
            center = self.rects['display'].width / 2
            center_led = (center - self.led_state['pan']) / (old_zoom * (self.led_state['size'] + self.led_state['spacing']))
            self.led_state['pan'] = center - center_led * self.led_state['zoom'] * (self.led_state['size'] + self.led_state['spacing'])
    
    def _cycle_color(self, color_index):
        """
        Cycle through available colors for a color button.
        
        Args:
            color_index: Index of the color to cycle
        """
        segment = self._get_active_segment()
        if segment and color_index < len(segment.color):

            current_idx = segment.color[color_index]
            next_idx = (current_idx + 1) % len(self.palettes[self.current_palette]) if current_idx >= 0 else 0
            

            new_colors = segment.color.copy()
            new_colors[color_index] = next_idx
            segment.color = new_colors
            

            segment.rgb_color = segment.calculate_rgb(self.current_palette)
            

            with self.ui_lock:
                self._build_ui()
    
    def _cycle_gradient_color(self, color_position):
        """
        Cycle through available colors for a gradient color button.
        
        Args:
            color_position: Position index in gradient_colors (1=left, 2=right)
        """
        segment = self._get_active_segment()
        if segment and hasattr(segment, 'gradient_colors'):

            current_idx = segment.gradient_colors[color_position]
            next_idx = (current_idx + 1) % len(self.palettes[self.current_palette]) if current_idx >= 0 else 0
            

            gradient_colors = segment.gradient_colors.copy()
            gradient_colors[color_position] = next_idx
            segment.update_param('gradient_colors', gradient_colors)
            

            with self.ui_lock:
                self._build_ui()
    
    def update(self):
        """Update LED simulation state."""
        if self.is_playing:
            for effect in self.effects.values():
                effect.update_all()
    
    def draw(self):
        """Draw the simulator UI and LED visualization."""

        self.screen.fill(UI_BACKGROUND_COLOR)
        

        if self.ui_state['resizing']:
            font = pygame.font.SysFont('Arial', 24)
            text = font.render("Đang thay đổi kích thước...", True, (220, 220, 220))
            text_rect = text.get_rect(center=(self.ui_state['width']//2, self.ui_state['height']//2))
            self.screen.blit(text, text_rect)
            return
        

        self._draw_led_visualization()
        

        if self.ui_state['control_panel_expanded'] and 'palette_rect' in self.ui_elements:
            self._draw_color_palette()
        

        self._draw_info_text()
        

        self.manager.draw_ui(self.screen)
    
    def _draw_led_visualization(self):
        """Draw the LED visualization in the display area."""

        if self.active_effect_id not in self.effects:
            return
        
        effect = self.effects[self.active_effect_id]
        

        led_colors = effect.get_led_output()
        

        led_size = max(1, int(self.led_state['size'] * self.led_state['zoom']))
        led_spacing = max(0, int(self.led_state['spacing'] * self.led_state['zoom']))
        led_total_width = led_size + led_spacing
        

        first_visible = max(0, int((-self.led_state['pan']) / led_total_width))
        last_visible = min(
            len(led_colors) - 1, 
            first_visible + int(self.rects['display'].width / led_total_width) + 1
        )
        

        center_y = self.rects['display'].y + self.rects['display'].height // 2
        

        for i in range(first_visible, last_visible + 1):
            if i >= len(led_colors):
                break
            

            x = self.rects['display'].x + i * led_total_width + self.led_state['pan']
            y = center_y - led_size // 2
            

            color = led_colors[i]
            if not isinstance(color, (list, tuple)) or len(color) < 3:
                color = (255, 0, 0)  # Default to red if invalid
            else:
                color = tuple(max(0, min(255, c)) for c in color[:3])
            
            try:

                pygame.draw.rect(self.screen, color, (x, y, led_size, led_size))
                border_color = tuple(min(c + 30, 255) for c in color)
                pygame.draw.rect(self.screen, border_color, (x, y, led_size, led_size), 1)
            except Exception as e:
                print(f"Error drawing LED {i}: {e}")
    
    def _draw_color_palette(self):
        """Draw the color palette display."""
        palette_rect = self.ui_elements['palette_rect']
        palette = self.palettes[self.current_palette]
        color_width = palette_rect.width / len(palette)
        
        for i, color in enumerate(palette):

            if isinstance(color, list):
                color = tuple(color)
            

            rect = pygame.Rect(
                palette_rect.x + i * color_width,
                palette_rect.y,
                color_width,
                palette_rect.height
            )
            

            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, (100, 100, 100), rect, 1)
            

            font = pygame.font.SysFont('Arial', 14)
            text_color = (0, 0, 0) if sum(color) > 380 else (255, 255, 255)
            text = font.render(str(i), True, text_color)
            text_rect = text.get_rect(center=(rect.x + rect.width/2, rect.y + rect.height/2))
            self.screen.blit(text, text_rect)
    
    def _draw_info_text(self):
        """Draw information text (FPS, segment info, etc.)."""
        font = pygame.font.SysFont('Arial', 14)
        

        fps_text = f"FPS: {int(self.clock.get_fps())}"
        fps_surf = font.render(fps_text, True, (220, 220, 220))
        self.screen.blit(fps_surf, (10, self.ui_state['height'] - 20))
        

        segment = self._get_active_segment()
        if segment:
            info_text = f"Effect {self.active_effect_id}, Segment {self.active_segment_id} - Position: {int(segment.current_position)}, Speed: {int(segment.move_speed)}"
            info_surf = font.render(info_text, True, (220, 220, 220))
            self.screen.blit(info_surf, (self.rects['display'].x + 10, self.rects['display'].y + 10))
    
    def run(self):
        """Run the main simulation loop."""
        running = True
        
        while running:

            time_delta = self.clock.tick(self.fps) / 1000.0
            

            running = self.handle_events()
            

            self.update()
            

            self.draw()
            

            pygame.display.flip()
        
        pygame.quit()
    
    def set_active_effect(self, effect_id):
        """
        Set the active effect.
        
        Args:
            effect_id: ID of the effect to activate
        """
        if effect_id in self.effects:
            self.active_effect_id = effect_id
            

            segments = sorted(self.effects[self.active_effect_id].segments.keys())
            if segments:
                self.active_segment_id = segments[0]
            

            with self.ui_lock:
                self._build_ui()