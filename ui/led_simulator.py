import pygame
import pygame_gui
import sys
import os
from typing import Dict, List, Tuple, Optional
import time
import math
import threading
import copy

sys.path.append('..')
from models.light_effect import LightEffect
from config import (
    UI_WIDTH, UI_HEIGHT, UI_BACKGROUND_COLOR, DEFAULT_COLOR_PALETTES,
    DEFAULT_FPS, DEFAULT_LED_COUNT
)

class LEDSimulator:
    """
    GUI simulator for LED tape light visualization.
    Provides interactive controls for manipulating LightSegment and LightEffect properties.
    """
    
    def __init__(self, light_effects: Dict[int, LightEffect]):
        """
        Initialize the LED simulator.
        
        Args:
            light_effects: Dictionary mapping effect_ID to LightEffect instances
        """
        pygame.init()
        

        self.effects = light_effects
        self.active_effect_id = min(light_effects.keys()) if light_effects else 1
        self.active_segment_id = 1
        self.current_palette = "A"
        self.palettes = DEFAULT_COLOR_PALETTES.copy()
        

        self.is_playing = True
        self.fps = DEFAULT_FPS
        self.last_segment_state = None

        self.segment_states = {}
        self.previous_layout_mode = None  

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
            'resize_time': 0,
            'last_window_size': (UI_WIDTH, UI_HEIGHT), 
            'two_row_threshold': 1400
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
        

        self.ui_lock = threading.RLock()
        

        self.ui_elements = {}
        self._build_ui()
        self._center_view()
        

        self.clock = pygame.time.Clock()
        self.ui_dirty = False
        self.ui_rebuilding = False
        

        self._save_segment_state()

    def _calculate_layout(self) -> Dict[str, pygame.Rect]:
        """
        Calculate layout rectangles for UI components.
        
        Returns:
            Dictionary of Pygame Rect objects for each UI area
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
    
    def _save_segment_state(self):
        """Lưu trạng thái chi tiết của segment hiện tại"""
        segment = self._get_active_segment()
        if segment:
            effect_id = self.active_effect_id
            segment_id = self.active_segment_id
            
            if effect_id not in self.segment_states:
                self.segment_states[effect_id] = {}
            
            self.segment_states[effect_id][segment_id] = {
                'current_position': segment.current_position,
                'move_speed': segment.move_speed,
                'move_range': segment.move_range.copy(),
                'is_edge_reflect': segment.is_edge_reflect,
                'gradient': segment.gradient if hasattr(segment, 'gradient') else False,
                'fade': segment.fade if hasattr(segment, 'fade') else False,
                'dimmer_time': segment.dimmer_time.copy() if hasattr(segment.dimmer_time, 'copy') else segment.dimmer_time
            }
    
    def _restore_segment_state(self):
        """Khôi phục trạng thái đã lưu cho segment hiện tại"""
        segment = self._get_active_segment()
        effect_id = self.active_effect_id
        segment_id = self.active_segment_id
        
        if (segment and effect_id in self.segment_states and 
            segment_id in self.segment_states[effect_id]):
            
            state = self.segment_states[effect_id][segment_id]
            
            segment.current_position = state['current_position']
            segment.move_speed = state['move_speed']
            segment.move_range = state['move_range'].copy()
            segment.is_edge_reflect = state['is_edge_reflect']
            
            if hasattr(segment, 'gradient'):
                segment.gradient = state['gradient']
            if hasattr(segment, 'fade'):
                segment.fade = state['fade']
            if hasattr(segment, 'dimmer_time'):
                segment.dimmer_time = state['dimmer_time'].copy() if hasattr(state['dimmer_time'], 'copy') else state['dimmer_time']

    def _build_ui(self):
        """Build the complete UI, clearing any existing elements"""
        try:
            if not self.ui_lock.acquire(False):
                self.ui_dirty = True
                return
            
            temp_state = None
            if hasattr(self, '_temp_state'):
                temp_state = self._temp_state.copy()
            
            self.ui_rebuilding = True
            self.manager.clear_and_reset()
            self.ui_elements = {}

            current_layout_mode = 'two_rows' if self.ui_state['width'] < self.ui_state['two_row_threshold'] else 'one_row'

            self.rects = self._calculate_layout()
            self.manager.set_window_resolution((self.ui_state['width'], self.ui_state['height']))

            self._add_panel_toggles()
            
            if self.ui_state['top_panel_expanded']:
                if current_layout_mode == 'two_rows':
                    self._build_top_panel_two_rows()
                else:
                    self._build_top_panel_one_row()
            
            if self.ui_state['control_panel_expanded']:
                self._build_control_panel()

            segment = self._get_active_segment()
            if segment and temp_state:
                print(f"Restoring state to segment: {temp_state}")
                segment.current_position = temp_state['current_position']
                segment.move_speed = temp_state['move_speed']
                segment.move_range = temp_state['move_range'].copy()
                segment.is_edge_reflect = temp_state['is_edge_reflect']
                
                if 'gradient' in temp_state and hasattr(segment, 'gradient'):
                    segment.gradient = temp_state['gradient']
                if 'fade' in temp_state and hasattr(segment, 'fade'):
                    segment.fade = temp_state['fade']
                
                if 'speed_slider' in self.ui_elements:
                    try:
                        print(f"Setting speed slider to: {segment.move_speed}")
                        self.ui_elements['speed_slider'].set_current_value(segment.move_speed)
                    except Exception as e:
                        print(f"Failed to update speed slider: {e}")
                
                if 'position_slider' in self.ui_elements:
                    try:
                        print(f"Setting position slider to: {segment.current_position}")
                        self.ui_elements['position_slider'].set_current_value(segment.current_position)
                    except Exception as e:
                        print(f"Failed to update position slider: {e}")
                
                if 'range_min' in self.ui_elements:
                    try:
                        print(f"Setting range_min slider to: {segment.move_range[0]}")
                        self.ui_elements['range_min'].set_current_value(segment.move_range[0])
                    except Exception as e:
                        print(f"Failed to update range_min slider: {e}")
                
                if 'range_max' in self.ui_elements:
                    try:
                        self.ui_elements['range_max'].set_current_value(segment.move_range[1])
                    except Exception as e:
                        print(f"Failed to update range_max slider: {e}")
                
                if 'reflect_toggle' in self.ui_elements:
                    try:
                        self.ui_elements['reflect_toggle'].set_text('ON' if segment.is_edge_reflect else 'OFF')
                    except Exception as e:
                        print(f"Failed to update reflect toggle: {e}")
                
                if hasattr(segment, 'gradient') and 'gradient_toggle' in self.ui_elements:
                    try:
                        self.ui_elements['gradient_toggle'].set_text('ON' if segment.gradient else 'OFF')
                    except Exception as e:
                        print(f"Failed to update gradient toggle: {e}")
                
                if hasattr(segment, 'fade') and 'fade_toggle' in self.ui_elements:
                    try:
                        self.ui_elements['fade_toggle'].set_text('ON' if segment.fade else 'OFF')
                    except Exception as e:
                        print(f"Failed to update fade toggle: {e}")

                if hasattr(self, '_temp_state'):
                    delattr(self, '_temp_state')

            self.ui_dirty = False
            self.ui_rebuilding = False
            self.previous_layout_mode = current_layout_mode
            
        finally:
            try:
                self.ui_lock.release()
            except RuntimeError:
                pass

    def _add_panel_toggles(self):
        """Add toggle buttons for expanding/collapsing panels"""
        toggle_size = 50
        
        self.ui_elements['top_toggle'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                self.ui_state['width']//2 - toggle_size//2, 
                self.rects['top'].height - 15,
                toggle_size + 10, 35
            ),
            text='▲' if self.ui_state['top_panel_expanded'] else '▼',
            manager=self.manager,
            tool_tip_text="Toggle Top Panel"
        )

        self.ui_elements['control_toggle'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                self.rects['control'].x -30,
                self.ui_state['height']//2 - toggle_size//2,
                35, toggle_size
            ),
            text='▶' if self.ui_state['control_panel_expanded'] else '◀',
            manager=self.manager,
            tool_tip_text="Toggle Control Panel"
        )

    def _build_top_panel_two_rows(self):
        """Build top panel with controls in two rows (for narrower windows)"""
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
        """Build top panel with controls in one row (for wider windows)"""
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
        max_buttons = min(8, (self.ui_state['width'] - 700) // button_width)
        
        for i, effect_id in enumerate(sorted(self.effects.keys())[:max_buttons]):
            x_pos = button_x + i * button_width
            button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(x_pos, row_y, 40, 30),
                text=str(effect_id),
                manager=self.manager,
                tool_tip_text=f"Select Effect {effect_id}"
            )
            self.ui_elements['effect_buttons'].append((button, effect_id))
        

        zoom_x = button_x + max_buttons * button_width + 10
        
        remaining_width = self.ui_state['width'] - zoom_x - 20
        zoom_controls_width = min(400, remaining_width)
        
        if zoom_controls_width >= 280:
            self.ui_elements['zoom_label'] = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(zoom_x, row_y, 60, 30),
                text='Zoom:',
                manager=self.manager
            )
            
            button_width = (zoom_controls_width - 60) // 4
            
            self.ui_elements['zoom_in'] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(zoom_x + 60, row_y, button_width, 30),
                text='+',
                manager=self.manager,
                tool_tip_text="Zoom In"
            )
            
            self.ui_elements['zoom_out'] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(zoom_x + 60 + button_width, row_y, button_width, 30),
                text='-',
                manager=self.manager,
                tool_tip_text="Zoom Out"
            )
            
            self.ui_elements['zoom_reset'] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(zoom_x + 60 + button_width*2, row_y, button_width, 30),
                text='Reset',
                manager=self.manager,
                tool_tip_text="Reset Zoom and Pan"
            )
            
            self.ui_elements['center_view'] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(zoom_x + 60 + button_width*3, row_y, button_width, 30),
                text='Center',
                manager=self.manager,
                tool_tip_text="Center View on Segments"
            )
    
    def _build_control_panel(self):
        """Build the right side control panel with color and segment controls"""
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
        button_width = 40
        palette_width = len(self.palettes.keys()) * button_width
        start_x = self.rects['control'].x + (panel_width - palette_width) // 2
        
        for i, palette_id in enumerate(sorted(self.palettes.keys())):
            x_pos = start_x + i * button_width
            button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(x_pos, panel_y, 40, 30),
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
            relative_rect=pygame.Rect(
                self.rects['control'].x + (self.rects['control'].width - 100) // 2, 
                panel_y, 
                100, 
                20
            ),
            text='Segment ID:',
            manager=self.manager
        )

        panel_y += 30
        

        segments = []
        if self.active_effect_id in self.effects:
            segments = sorted(self.effects[self.active_effect_id].segments.keys())
        else:
            segments = [1]
        

        segment_buttons_width = min(panel_width - 100, len(segments) * 35)
        button_width = 10 + segment_buttons_width / len(segments)
        
        start_x = (self.rects['control'].x + (panel_width - segment_buttons_width) // 2 ) - 15
        
        self.ui_elements['segment_buttons'] = []
        for i, segment_id in enumerate(segments):
            x_pos = start_x + i * button_width
            button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(x_pos, panel_y, max(20, button_width - 5), 30),
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
        Build controls specific to the currently selected segment.
        
        Args:
            segment: The active LightSegment instance
            panel_y: Starting Y coordinate for controls
        """
        panel_x = self.rects['control'].x
        panel_width = self.rects['control'].width
        
        effect_id = self.active_effect_id
        segment_id = self.active_segment_id
        saved_state = None
        
        if (effect_id in self.segment_states and 
            segment_id in self.segment_states[effect_id]):
            saved_state = self.segment_states[effect_id][segment_id]

        remaining_height = self.ui_state['height'] - panel_y - 20
        elements_per_section = min(5, remaining_height // 100)
        compact_mode = remaining_height < 500

        self.ui_elements['speed_heading'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(panel_x + 10, panel_y, panel_width - 20, 20),
            text='Speed & Position',
            manager=self.manager
        )
        panel_y += 25

        if elements_per_section >= 1:
            self.ui_elements['speed_label'] = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(panel_x + 10, panel_y, 100, 20),
                text='Move Speed:',
                manager=self.manager
            )
            
            panel_y += 20 if compact_mode else 25

            current_speed = saved_state['move_speed'] if saved_state else segment.move_speed
            
            self.ui_elements['speed_slider'] = pygame_gui.elements.UIHorizontalSlider(
                relative_rect=pygame.Rect(panel_x + 10, panel_y, panel_width - 20, 20),
                start_value=current_speed,
                value_range=(-128, 127),
                manager=self.manager
            )
            
            panel_y += 25 if compact_mode else 30

        if elements_per_section >= 2:
            self.ui_elements['position_label'] = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(panel_x + 10, panel_y, 100, 20),
                text='Position:',
                manager=self.manager
            )
            
            panel_y += 20 if compact_mode else 25

            current_position = saved_state['current_position'] if saved_state else segment.current_position
            move_range = saved_state['move_range'] if saved_state else segment.move_range

            position = max(move_range[0], min(move_range[1], current_position))
            
            self.ui_elements['position_slider'] = pygame_gui.elements.UIHorizontalSlider(
                relative_rect=pygame.Rect(panel_x + 10, panel_y, panel_width - 20, 20),
                start_value=position,
                value_range=(move_range[0], max(move_range[0] + 1, move_range[1])),
                manager=self.manager
            )
            
            panel_y += 25 if compact_mode else 30

        if elements_per_section >= 3:
            self.ui_elements['range_label'] = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(panel_x + 10, panel_y, 100, 20),
                text='Move Range:',
                manager=self.manager
            )
            
            panel_y += 20 if compact_mode else 25
            
            range_width = (panel_width - 30) / 2

            range_min = saved_state['move_range'][0] if saved_state else segment.move_range[0]
            range_max = saved_state['move_range'][1] if saved_state else segment.move_range[1]

            if range_min >= range_max:
                range_max = range_min + 1
            
            self.ui_elements['range_min'] = pygame_gui.elements.UIHorizontalSlider(
                relative_rect=pygame.Rect(panel_x + 10, panel_y, range_width, 20),
                start_value=range_min,
                value_range=(0, DEFAULT_LED_COUNT - 1),
                manager=self.manager
            )
            
            self.ui_elements['range_max'] = pygame_gui.elements.UIHorizontalSlider(
                relative_rect=pygame.Rect(panel_x + 10 + range_width + 10, panel_y, range_width, 20),
                start_value=range_max,
                value_range=(0, DEFAULT_LED_COUNT - 1),
                manager=self.manager
            )
            
            panel_y += 25 if compact_mode else 30

        if elements_per_section >= 4:
            self.ui_elements['reflect_label'] = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(panel_x + 10, panel_y, 150, 20),
                text='Edge Reflection:',
                manager=self.manager
            )

            is_edge_reflect = saved_state['is_edge_reflect'] if saved_state else segment.is_edge_reflect
            
            self.ui_elements['reflect_toggle'] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(panel_x + 170, panel_y, panel_width - 180, 20),
                text='ON' if is_edge_reflect else 'OFF',
                manager=self.manager
            )
            
            panel_y += 30 if compact_mode else 40

        if elements_per_section >= 2:
            self._build_color_settings(segment, panel_y, compact_mode, saved_state)

    def _build_color_settings(self, segment, panel_y, compact_mode=False, saved_state=None):
        """
        Build color control settings for a segment.
        
        Args:
            segment: The active LightSegment instance
            panel_y: Starting Y coordinate for controls
            compact_mode: Whether to use compact layout
            saved_state: Previously saved state to restore values from
        """
        panel_x = self.rects['control'].x
        panel_width = self.rects['control'].width
        
        self.ui_elements['color_heading'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(panel_x + 10, panel_y, panel_width - 20, 20),
            text='Color Settings',
            manager=self.manager
        )
        panel_y += 25
        
        remaining_height = self.ui_state['height'] - panel_y - 100
        max_colors = min(len(segment.color), 6)
        
        button_size = min(50, panel_width // 3 - 10)
        button_spacing = 5
        color_per_row = max(1, min(4, (panel_width - 20) // (button_size + button_spacing)))
        
        if compact_mode:
            button_size = min(button_size, 30)
            button_spacing = 3
            color_per_row = max(2, color_per_row)
        
        self.ui_elements['color_buttons'] = []
        total_width = color_per_row * (button_size + button_spacing) - button_spacing
        start_x = panel_x + (panel_width - total_width) // 2
        
        colors = segment.color
        
        for i, color_idx in enumerate(colors[:max_colors]):
            row = i // color_per_row
            col = i % color_per_row
            
            x = start_x + col * (button_size + button_spacing)
            y = panel_y + row * (button_size + button_spacing)
            
            label = str(color_idx) if color_idx >= 0 else "-"
            
            button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(x, y, button_size, button_size),
                text=label,
                manager=self.manager,
                tool_tip_text=f"Color {i+1}"
            )
            
            self.ui_elements['color_buttons'].append((button, i))
        
        panel_y += (((len(colors[:max_colors]) - 1) // color_per_row) + 1) * (button_size + button_spacing) + 10

        if remaining_height > 80:
            self.ui_elements['gradient_label'] = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(panel_x + 10, panel_y, 150, 20),
                text='Gradient:',
                manager=self.manager
            )

            gradient_enabled = False
            if saved_state and 'gradient' in saved_state:
                gradient_enabled = saved_state['gradient']
            elif hasattr(segment, 'gradient'):
                gradient_enabled = segment.gradient
            
            self.ui_elements['gradient_toggle'] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(panel_x + 170, panel_y, panel_width - 180, 20),
                text='ON' if gradient_enabled else 'OFF',
                manager=self.manager
            )
            
            panel_y += 25
            
            self.ui_elements['fade_label'] = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(panel_x + 10, panel_y, 150, 20),
                text='Fade Effect:',
                manager=self.manager
            )

            fade_enabled = False
            if saved_state and 'fade' in saved_state:
                fade_enabled = saved_state['fade']
            elif hasattr(segment, 'fade'):
                fade_enabled = segment.fade
            
            self.ui_elements['fade_toggle'] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(panel_x + 170, panel_y, panel_width - 180, 20),
                text='ON' if fade_enabled else 'OFF',
                manager=self.manager
            )
            
            panel_y += 30
            
            if remaining_height > 150:
                self._build_dimmer_settings(segment, panel_y, compact_mode, saved_state)

    def _build_dimmer_settings(self, segment, panel_y, compact_mode=False, saved_state=None):
        """
        Build dimmer/fade controls for a segment.
        
        Args:
            segment: The active LightSegment instance
            panel_y: Starting Y coordinate for controls
            compact_mode: Whether to use compact layout
            saved_state: Previously saved state to restore values from
        """
        panel_x = self.rects['control'].x
        panel_width = self.rects['control'].width
        
        self.ui_elements['dimmer_heading'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(panel_x + 10, panel_y, panel_width - 20, 20),
            text='Dimmer Settings (Fade)',
            manager=self.manager
        )
        panel_y += 25
        
        remaining_height = self.ui_state['height'] - panel_y - 20
        max_sliders = min(5, remaining_height // 30)
        
        if max_sliders <= 0:
            return
        
        label_height = 15 if compact_mode else 20
        slider_gap = 5 if compact_mode else 10
        
        dimmer_time = segment.dimmer_time
        if saved_state and 'dimmer_time' in saved_state:
            dimmer_time = saved_state['dimmer_time']
        
        self.ui_elements['dimmer_sliders'] = []
        labels = ["Fade In Start", "Fade In End", "Fade Out Start", "Fade Out End", "Cycle Length"]
        
        for i, label in enumerate(labels[:max_sliders]):
            if i >= len(dimmer_time):
                break
            
            current_value = dimmer_time[i]
                
            label_element = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(panel_x + 10, panel_y, panel_width - 20, label_height),
                text=label,
                manager=self.manager
            )
            
            panel_y += label_height
            
            slider = pygame_gui.elements.UIHorizontalSlider(
                relative_rect=pygame.Rect(panel_x + 10, panel_y, panel_width - 20, 20),
                start_value=current_value,
                value_range=(0, 1000),
                manager=self.manager
            )
            
            self.ui_elements['dimmer_sliders'].append((slider, i, label_element))
            panel_y += 20 + slider_gap

    def _get_active_segment(self):
        """
        Get the currently active segment.
        
        Returns:
            LightSegment instance or None if not found
        """
        if (self.active_effect_id in self.effects and 
            self.active_segment_id in self.effects[self.active_effect_id].segments):
            return self.effects[self.active_effect_id].segments[self.active_segment_id]
        return None
    
    def _center_view(self):
        """Center the view on the active segments"""
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
        Handle pygame events and return whether the application should continue running.
        
        Returns:
            Boolean indicating whether the application should continue running
        """
        mouse_pos = pygame.mouse.get_pos()
        
        try:
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
                
                try:
                    self.manager.process_events(event)
                except Exception as e:
                    print(f"Error processing UI event: {e}")
            

            if self.ui_state['resizing'] and time.time() - self.ui_state['resize_time'] > 0.2:
                self._complete_resize()
            

            if self.ui_state['auto_hide_enabled'] and time.time() - self.activity['last_time'] > self.activity['timeout']:
                if self.ui_state['top_panel_expanded'] or self.ui_state['control_panel_expanded']:
                    self.ui_state['top_panel_expanded'] = False
                    self.ui_state['control_panel_expanded'] = False
                    self.rects = self._calculate_layout()
                    self.ui_dirty = True
            

            if self.ui_dirty:
                self._build_ui()
        except Exception as e:
            print(f"Error in event handling: {e}")
                        
        return True
    def _handle_resize(self, event):
        """Handle window resize events."""
        try:
            segment = self._get_active_segment()
            if segment:
                self._temp_state = {
                    'current_position': segment.current_position,
                    'move_speed': segment.move_speed,
                    'move_range': segment.move_range.copy(),
                    'is_edge_reflect': segment.is_edge_reflect
                }

            old_width = self.ui_state['width']
            new_width = max(event.size[0], 800)
            threshold = self.ui_state['two_row_threshold']
            
            old_layout = 'two_rows' if old_width < threshold else 'one_row'
            new_layout = 'two_rows' if new_width < threshold else 'one_row'
            layout_changed = old_layout != new_layout
            
            self.ui_state['resizing'] = True
            self.ui_state['resize_time'] = time.time()
            
            self.ui_state['width'] = new_width
            self.ui_state['height'] = max(event.size[1], 600)
            
            self.screen = pygame.display.set_mode(
                (self.ui_state['width'], self.ui_state['height']), 
                pygame.RESIZABLE
            )
            
            self.rects = self._calculate_layout()
            
            self.activity['last_time'] = time.time()
            
            if layout_changed:
                self.previous_layout_mode = None 
                self.ui_dirty = True
                self.manager.clear_and_reset()
                self.ui_elements = {}
        except Exception as e:
            print(f"Error handling resize: {e}")

    def _handle_mouse_wheel_zoom(self, event, mouse_pos):
        """
        Handle mouse wheel zoom events.
        
        Args:
            event: Mouse wheel event
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
            self._save_segment_state()  # Save state before changing UI
            self.ui_state['top_panel_expanded'] = True
            self.rects = self._calculate_layout()
            self.ui_dirty = True
            self.activity['last_time'] = time.time()
        

        if not self.ui_state['control_panel_expanded'] and mouse_pos[0] > self.ui_state['width'] - 20:
            self._save_segment_state()  # Save state before changing UI
            self.ui_state['control_panel_expanded'] = True
            self.rects = self._calculate_layout()
            self.ui_dirty = True
            self.activity['last_time'] = time.time()
    
    def _handle_button_press(self, ui_element):
        """
        Handle button press events.
        
        Args:
            ui_element: The pygame_gui element that was pressed
        """
        try:

            if ui_element == self.ui_elements.get('top_toggle') or ui_element == self.ui_elements.get('show_top_panel'):
                self._save_segment_state()  # Save state before toggling
                self._toggle_panel('top')
            elif ui_element == self.ui_elements.get('control_toggle') or ui_element == self.ui_elements.get('show_control_panel'):
                self._save_segment_state()  # Save state before toggling
                self._toggle_panel('control')


            elif ui_element == self.ui_elements.get('play_button'):
                self.is_playing = not self.is_playing
                ui_element.set_text('Pause' if self.is_playing else 'Play')
            

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
                        
                        self.ui_dirty = True
                        break
            

            if 'segment_buttons' in self.ui_elements:
                for button, segment_id in self.ui_elements['segment_buttons']:
                    if ui_element == button:
                        self.active_segment_id = segment_id
                        self.ui_dirty = True
                        break
            

            if 'palette_buttons' in self.ui_elements:
                for button, palette_id in self.ui_elements['palette_buttons']:
                    if ui_element == button:
                        self.current_palette = palette_id
                        
                        for effect in self.effects.values():
                            effect.current_palette = self.current_palette
                        
                        self.ui_dirty = True
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
                    ui_element.set_text('ON' if segment.is_edge_reflect else 'OFF')
                
                elif ui_element == self.ui_elements.get('gradient_toggle'):
                    if hasattr(segment, 'gradient'):
                        segment.gradient = not segment.gradient
                        if segment.gradient and hasattr(segment, 'gradient_colors') and segment.gradient_colors[0] == 0:
                            segment.gradient_colors[0] = 1
                        ui_element.set_text('ON' if segment.gradient else 'OFF')
                        self.ui_dirty = True
                
                elif ui_element == self.ui_elements.get('fade_toggle'):
                    if hasattr(segment, 'fade'):
                        segment.fade = not segment.fade
                        ui_element.set_text('ON' if segment.fade else 'OFF')
        except Exception as e:
            print(f"Error handling button press: {e}")

    def _update_segment_state_value(self, param_name, value):
        effect_id = self.active_effect_id
        segment_id = self.active_segment_id
        
        if effect_id not in self.segment_states:
            self.segment_states[effect_id] = {}
        if segment_id not in self.segment_states[effect_id]:
            self._save_segment_state() 
        else:
            if param_name == 'move_range' and hasattr(value, 'copy'):
                self.segment_states[effect_id][segment_id][param_name] = value.copy()
            elif param_name == 'dimmer_time' and hasattr(value, 'copy'):
                self.segment_states[effect_id][segment_id][param_name] = value.copy()
            else:
                self.segment_states[effect_id][segment_id][param_name] = value      

    def _handle_slider_movement(self, ui_element, value):
        """Handle slider movement events."""
        try:
            if ui_element == self.ui_elements.get('fps_slider'):
                self.fps = int(value)
                if 'fps_value' in self.ui_elements:
                    try:
                        self.ui_elements['fps_value'].set_text(str(self.fps))
                    except:
                        pass
                
                for effect in self.effects.values():
                    effect.fps = self.fps
            
            segment = self._get_active_segment()
            if segment and not self.ui_rebuilding:
                if ui_element == self.ui_elements.get('speed_slider'):
                    old_speed = segment.move_speed
                    segment.move_speed = value
                    self._update_segment_state_value('move_speed', value)
                
                elif ui_element == self.ui_elements.get('position_slider'):
                    old_position = segment.current_position
                    segment.current_position = float(value)
                    self._update_segment_state_value('current_position', float(value))
                
                elif ui_element == self.ui_elements.get('range_min'):
                    old_range = segment.move_range.copy()
                    
                    new_min = float(value)
                    new_max = max(new_min + 1, old_range[1])
                    new_range = [new_min, new_max]
                    
                    segment.move_range = new_range
                    self._update_segment_state_value('move_range', new_range)
                    
                    position_slider = self.ui_elements.get('position_slider')
                    if position_slider:
                        try:
                            position_slider.value_range = (new_min, new_max)
                            
                            if segment.current_position < new_min:
                                segment.current_position = float(new_min)
                                position_slider.set_current_value(new_min)
                            elif segment.current_position > new_max:
                                segment.current_position = float(new_max)
                                position_slider.set_current_value(new_max)
                        except Exception as e:
                            print(f"Error updating position slider: {e}")
                    
                    if old_range[1] != new_max and 'range_max' in self.ui_elements:
                        try:
                            self.ui_elements['range_max'].set_current_value(new_max)
                            print(f"Updated range_max slider to: {new_max}")
                        except Exception as e:
                            print(f"Error updating range_max slider: {e}")
                
                elif ui_element == self.ui_elements.get('range_max'):
                    old_range = segment.move_range.copy()
                    
                    new_max = float(value)
                    new_min = min(old_range[0], new_max - 1)
                    new_range = [new_min, new_max]
                    
                    segment.move_range = new_range
                    self._update_segment_state_value('move_range', new_range)
                    
                    position_slider = self.ui_elements.get('position_slider')
                    if position_slider:
                        try:
                            position_slider.value_range = (new_min, new_max)
                            
                            if segment.current_position < new_min:
                                segment.current_position = float(new_min)
                                position_slider.set_current_value(new_min)
                            elif segment.current_position > new_max:
                                segment.current_position = float(new_max)
                                position_slider.set_current_value(new_max)
                        except Exception as e:
                            print(f"Error updating position slider: {e}")
                    
                    if old_range[0] != new_min and 'range_min' in self.ui_elements:
                        try:
                            self.ui_elements['range_min'].set_current_value(new_min)
                        except Exception as e:
                            print(f"Error updating range_min slider: {e}")
                
                if 'dimmer_sliders' in self.ui_elements:
                    for slider, dimmer_index, _ in self.ui_elements['dimmer_sliders']:
                        if ui_element == slider and dimmer_index < len(segment.dimmer_time):
                            old_value = segment.dimmer_time[dimmer_index]
                            dimmer_time = segment.dimmer_time.copy() if hasattr(segment.dimmer_time, 'copy') else list(segment.dimmer_time)
                            dimmer_time[dimmer_index] = int(value)
                            segment.dimmer_time = dimmer_time
                            
                            self._update_segment_state_value('dimmer_time', dimmer_time)
                            break
        except Exception as e:
            print(f"Error handling slider movement: {e}")

    def _toggle_panel(self, panel):
        """Toggle expansion/collapse of a panel."""
        segment = self._get_active_segment()
        if segment:
            self._temp_state = {
                'current_position': segment.current_position,
                'move_speed': segment.move_speed,
                'move_range': segment.move_range.copy(),
                'is_edge_reflect': segment.is_edge_reflect,
                'gradient': segment.gradient if hasattr(segment, 'gradient') else False,
                'fade': segment.fade if hasattr(segment, 'fade') else False,
            }

        if panel == 'top':
            self.ui_state['top_panel_expanded'] = not self.ui_state['top_panel_expanded']
        elif panel == 'control':
            self.ui_state['control_panel_expanded'] = not self.ui_state['control_panel_expanded']
 
        self.rects = self._calculate_layout()
        self.ui_dirty = True

    def _complete_resize(self):
        """Complete the resize operation and rebuild UI"""
        self.ui_state['resizing'] = False
        self.manager.set_window_resolution((self.ui_state['width'], self.ui_state['height']))
        self.ui_dirty = True
    
    def _zoom_in(self):
        """Zoom in on the LED visualization"""
        old_zoom = self.led_state['zoom']
        self.led_state['zoom'] = min(5.0, self.led_state['zoom'] * 1.2)
        
        if old_zoom != self.led_state['zoom']:
            center = self.rects['display'].width / 2
            center_led = (center - self.led_state['pan']) / (old_zoom * (self.led_state['size'] + self.led_state['spacing']))
            self.led_state['pan'] = center - center_led * self.led_state['zoom'] * (self.led_state['size'] + self.led_state['spacing'])
    
    def _cycle_color(self, color_index):
        """
        Cycle through available colors in the palette for a color index.
        
        Args:
            color_index: Index in the segment's color list to change
        """
        segment = self._get_active_segment()
        if segment and color_index < len(segment.color):
            current_idx = segment.color[color_index]
            next_idx = (current_idx + 1) % len(self.palettes[self.current_palette]) if current_idx >= 0 else 0
            
            new_colors = segment.color.copy()
            new_colors[color_index] = next_idx
            segment.color = new_colors
            
            segment.rgb_color = segment.calculate_rgb(self.current_palette)
            self.ui_dirty = True
    
    def _cycle_gradient_color(self, color_position):
        """
        Cycle through available colors for gradient endpoints.
        
        Args:
            color_position: Position in gradient_colors to change
        """
        segment = self._get_active_segment()
        if segment and hasattr(segment, 'gradient_colors'):
            current_idx = segment.gradient_colors[color_position]
            next_idx = (current_idx + 1) % len(self.palettes[self.current_palette]) if current_idx >= 0 else 0
            
            gradient_colors = segment.gradient_colors.copy()
            gradient_colors[color_position] = next_idx
            segment.update_param('gradient_colors', gradient_colors)
            self.ui_dirty = True
    
    def update(self):
        """Update all light effects if playing"""
        try:
            if self.is_playing:
                for effect in self.effects.values():
                    effect.update_all()
        except Exception as e:
            print(f"Error in update method: {e}")
    
    def draw(self):
        """Draw the UI and LED visualization"""
        try:

            self.screen.fill(UI_BACKGROUND_COLOR)
            

            if self.ui_state['resizing']:
                font = pygame.font.SysFont('Arial', 24)
                text = font.render("Đang thay đổi kích thước...", True, (220, 220, 220))
                text_rect = text.get_rect(center=(self.ui_state['width']//2, self.ui_state['height']//2))
                self.screen.blit(text, text_rect)
                return
                

            try:
                time_delta = self.clock.get_time() / 1000.0
                self.manager.update(time_delta)
            except Exception as e:
                print(f"Error updating UI manager: {e}")
            

            self._draw_led_visualization()


            try:
                self.manager.draw_ui(self.screen)
            except Exception as e:
                print(f"Error drawing UI: {e}")


            if self.ui_state['control_panel_expanded'] and 'palette_rect' in self.ui_elements:
                self._draw_color_palette()
            

            self._draw_info_text()
        except Exception as e:
            print(f"Error in draw method: {e}")
            import traceback
            traceback.print_exc()
    
    def _draw_led_visualization(self):
        """Draw the LED tape visualization in the display area"""
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
        """Draw the current color palette in the control panel"""
        palette_rect = self.ui_elements['palette_rect']
        palette = self.palettes[self.current_palette]
        color_width = palette_rect.width / len(palette)
        

        pygame.draw.rect(self.screen, (50, 50, 50), palette_rect)
        

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
        """Draw information text at the bottom of the screen"""
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
        """Main application loop"""
        running = True
        
        while running:
            try:
                time_delta = self.clock.tick(self.fps) / 1000.0
                
                running = self.handle_events()
                
                self.update()
                
                self.draw()
                
                pygame.display.flip()
            except Exception as e:
                print(f"Exception in main loop: {e}")
                import traceback
                traceback.print_exc()

                time.sleep(0.1)
        
        try:
            pygame.quit()
        except:
            pass
