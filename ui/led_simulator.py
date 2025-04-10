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
from models.light_segment import LightSegment
from models.light_scene import LightScene
from config import (
    UI_WIDTH, UI_HEIGHT, UI_BACKGROUND_COLOR, DEFAULT_COLOR_PALETTES,
    DEFAULT_FPS, DEFAULT_LED_COUNT
)

class LEDSimulator:
    """
    GUI simulator for LED tape light visualization.
    Provides interactive controls for manipulating LightSegment, LightEffect, and LightScene properties.
    """
    
    def __init__(self, scene: LightScene):
        """
        Initialize the LED simulator.
        
        Args:
            scene: The active LightScene to visualize
        """
        pygame.init()
        
        self.scene = scene
        self.active_scene_id = scene.scene_ID
        self.active_effect_id = scene.current_effect_ID if scene.current_effect_ID else min(scene.effects.keys()) if scene.effects else 1
        self.active_segment_id = 1
        
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
            'two_row_threshold': 1400,
            'scale_factor': 1.0
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
        
        # Calculate initial scale factor based on display resolution
        display_info = pygame.display.Info()
        base_resolution = (1920, 1080)
        self.ui_state['scale_factor'] = min(display_info.current_w / base_resolution[0], 
                                           display_info.current_h / base_resolution[1])
        self._apply_scale_factor()

    def _get_active_segment(self) -> Optional[LightSegment]:
        """
        Get the currently active segment.
        
        Returns:
            The active LightSegment or None if not found
        """
        if self.active_effect_id not in self.scene.effects:
            return None
            
        effect = self.scene.effects[self.active_effect_id]
        
        if self.active_segment_id not in effect.segments:
            if effect.segments:
                self.active_segment_id = min(effect.segments.keys())
            else:
                return None
                
        return effect.segments[self.active_segment_id]

    def _apply_scale_factor(self):
        """Apply the current scale factor to UI elements"""
        scale = self.ui_state['scale_factor']
        self.led_state['size'] = int(8 * scale)
        self.led_state['spacing'] = max(1, int(1 * scale))
        
        # Recalculate layout with new scale
        self.rects = self._calculate_layout()
        self.ui_dirty = True

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
        """Save the detailed state of the current segment."""
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
        """Restore the saved state for the current segment."""
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
        """Build the complete UI, clearing any existing elements."""
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
                segment.current_position = temp_state['current_position']
                segment.move_speed = temp_state['move_speed']
                segment.move_range = temp_state['move_range'].copy()
                segment.is_edge_reflect = temp_state['is_edge_reflect']
                
                if 'gradient' in temp_state and hasattr(segment, 'gradient'):
                    segment.gradient = temp_state['gradient']
                if 'fade' in temp_state and hasattr(segment, 'fade'):
                    segment.fade = temp_state['fade']
                
                self._update_ui_controls(segment)

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
    
    def _update_ui_controls(self, segment):
        """Update UI controls to reflect current segment state"""
        try:
            if 'speed_slider' in self.ui_elements:
                try:
                    self.ui_elements['speed_slider'].set_current_value(segment.move_speed)
                except Exception:
                    pass
            
            if 'position_slider' in self.ui_elements:
                try:
                    self.ui_elements['position_slider'].set_current_value(segment.current_position)
                except Exception:
                    pass
            
            if 'range_min' in self.ui_elements:
                try:
                    self.ui_elements['range_min'].set_current_value(segment.move_range[0])
                except Exception:
                    pass
            
            if 'range_max' in self.ui_elements:
                try:
                    self.ui_elements['range_max'].set_current_value(segment.move_range[1])
                except Exception:
                    pass
            
            if 'reflect_toggle' in self.ui_elements:
                try:
                    self.ui_elements['reflect_toggle'].set_text('ON' if segment.is_edge_reflect else 'OFF')
                except Exception:
                    pass
            
            if hasattr(segment, 'gradient') and 'gradient_toggle' in self.ui_elements:
                try:
                    self.ui_elements['gradient_toggle'].set_text('ON' if segment.gradient else 'OFF')
                except Exception:
                    pass
            
            if hasattr(segment, 'fade') and 'fade_toggle' in self.ui_elements:
                try:
                    self.ui_elements['fade_toggle'].set_text('ON' if segment.fade else 'OFF')
                except Exception:
                    pass
        except Exception:
            pass

    def _add_panel_toggles(self):
        """Add toggle buttons for expanding/collapsing panels."""
        toggle_size = int(50 * self.ui_state['scale_factor'])
        
        self.ui_elements['top_toggle'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                self.ui_state['width']//2 - toggle_size//2, 
                self.rects['top'].height - int(15 * self.ui_state['scale_factor']),
                toggle_size + int(10 * self.ui_state['scale_factor']), 
                int(35 * self.ui_state['scale_factor'])
            ),
            text='▲' if self.ui_state['top_panel_expanded'] else '▼',
            manager=self.manager,
            tool_tip_text="Toggle Top Panel"
        )

        self.ui_elements['control_toggle'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                self.rects['control'].x - int(30 * self.ui_state['scale_factor']),
                self.ui_state['height']//2 - toggle_size//2,
                int(35 * self.ui_state['scale_factor']), 
                toggle_size
            ),
            text='▶' if self.ui_state['control_panel_expanded'] else '◀',
            manager=self.manager,
            tool_tip_text="Toggle Control Panel"
        )
        
    def _build_top_panel_two_rows(self):
        """Build top panel with controls in two rows (for narrower windows)."""
        scale = self.ui_state['scale_factor']
        row1_y = int(10 * scale)
        button_height = int(30 * scale)
        slider_height = int(20 * scale)
        
        self.ui_elements['play_button'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(int(10 * scale), row1_y, int(80 * scale), button_height),
            text='Pause' if self.is_playing else 'Play',
            manager=self.manager,
            tool_tip_text="Play/Pause Animation"
        )
        
        self.ui_elements['fps_label'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(int(100 * scale), row1_y, int(50 * scale), button_height),
            text='FPS:',
            manager=self.manager
        )
        
        self.ui_elements['fps_slider'] = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(int(150 * scale), row1_y + int(5 * scale), int(150 * scale), slider_height),
            start_value=self.fps,
            value_range=(1, 120),
            manager=self.manager
        )
        
        self.ui_elements['fps_value'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(int(310 * scale), row1_y, int(50 * scale), button_height),
            text=str(self.fps),
            manager=self.manager
        )
        
        self.ui_elements['scene_label'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(int(370 * scale), row1_y, int(80 * scale), button_height),
            text='Scene ID:',
            manager=self.manager
        )
        
        self.ui_elements['scene_buttons'] = []
        scene_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(int(460 * scale), row1_y, int(40 * scale), button_height),
            text=str(self.scene.scene_ID),
            manager=self.manager,
            tool_tip_text=f"Scene {self.scene.scene_ID}"
        )
        self.ui_elements['scene_buttons'].append((scene_button, self.scene.scene_ID))
        
        row2_y = int(45 * scale)
        
        self.ui_elements['effect_label'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(int(10 * scale), row2_y, int(80 * scale), button_height),
            text='Effect ID:',
            manager=self.manager
        )
        
        self.ui_elements['effect_buttons'] = []
        button_x = int(100 * scale)
        button_width = int(45 * scale)
        for i, effect_id in enumerate(sorted(self.scene.effects.keys())):
            x_pos = button_x + i * button_width
            button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(x_pos, row2_y, int(40 * scale), button_height),
                text=str(effect_id),
                manager=self.manager,
                tool_tip_text=f"Select Effect {effect_id}"
            )
            self.ui_elements['effect_buttons'].append((button, effect_id))
        
        self.ui_elements['zoom_in'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(int(370 * scale), row2_y, int(40 * scale), button_height),
            text='+',
            manager=self.manager,
            tool_tip_text="Zoom In"
        )
        
        self.ui_elements['zoom_out'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(int(415 * scale), row2_y, int(40 * scale), button_height),
            text='-',
            manager=self.manager,
            tool_tip_text="Zoom Out"
        )
        
        self.ui_elements['zoom_reset'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(int(460 * scale), row2_y, int(70 * scale), button_height),
            text='Reset',
            manager=self.manager,
            tool_tip_text="Reset Zoom and Pan"
        )
        
        self.ui_elements['center_view'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(int(535 * scale), row2_y, int(70 * scale), button_height),
            text='Center',
            manager=self.manager,
            tool_tip_text="Center View on Segments"
        )

    def _build_top_panel_one_row(self):
        """Build top panel with controls in one row (for wider windows)."""
        scale = self.ui_state['scale_factor']
        row_y = int(10 * scale)
        button_height = int(30 * scale)
        slider_height = int(20 * scale)
        
        self.ui_elements['play_button'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(int(10 * scale), row_y, int(80 * scale), button_height),
            text='Pause' if self.is_playing else 'Play',
            manager=self.manager,
            tool_tip_text="Play/Pause Animation"
        )
        
        self.ui_elements['fps_label'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(int(100 * scale), row_y, int(50 * scale), button_height),
            text='FPS:',
            manager=self.manager
        )
        
        self.ui_elements['fps_slider'] = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(int(150 * scale), row_y + int(5 * scale), int(150 * scale), slider_height),
            start_value=self.fps,
            value_range=(1, 120),
            manager=self.manager
        )
        
        self.ui_elements['fps_value'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(int(310 * scale), row_y, int(50 * scale), button_height),
            text=str(self.fps),
            manager=self.manager
        )
        
        self.ui_elements['scene_label'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(int(370 * scale), row_y, int(80 * scale), button_height),
            text='Scene ID:',
            manager=self.manager
        )
        
        self.ui_elements['scene_buttons'] = []
        scene_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(int(460 * scale), row_y, int(40 * scale), button_height),
            text=str(self.scene.scene_ID),
            manager=self.manager,
            tool_tip_text=f"Scene {self.scene.scene_ID}"
        )
        self.ui_elements['scene_buttons'].append((scene_button, self.scene.scene_ID))
        
        self.ui_elements['effect_label'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(int(510 * scale), row_y, int(80 * scale), button_height),
            text='Effect ID:',
            manager=self.manager
        )
        
        self.ui_elements['effect_buttons'] = []
        button_x = int(600 * scale)
        button_width = int(45 * scale)
        max_buttons = min(8, len(self.scene.effects) if self.scene.effects else 0)
        
        for i, effect_id in enumerate(sorted(self.scene.effects.keys())[:max_buttons]):
            x_pos = button_x + i * button_width
            button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(x_pos, row_y, int(40 * scale), button_height),
                text=str(effect_id),
                manager=self.manager,
                tool_tip_text=f"Select Effect {effect_id}"
            )
            self.ui_elements['effect_buttons'].append((button, effect_id))
        
        zoom_x = button_x + max_buttons * button_width + int(10 * scale)
        
        remaining_width = self.ui_state['width'] - zoom_x - int(20 * scale)
        zoom_controls_width = min(int(400 * scale), remaining_width)
        
        if zoom_controls_width >= int(280 * scale):
            self.ui_elements['zoom_in'] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(zoom_x, row_y, int(40 * scale), button_height),
                text='+',
                manager=self.manager,
                tool_tip_text="Zoom In"
            )
            
            self.ui_elements['zoom_out'] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(zoom_x + int(45 * scale), row_y, int(40 * scale), button_height),
                text='-',
                manager=self.manager,
                tool_tip_text="Zoom Out"
            )
            
            self.ui_elements['zoom_reset'] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(zoom_x + int(90 * scale), row_y, int(70 * scale), button_height),
                text='Reset',
                manager=self.manager,
                tool_tip_text="Reset Zoom and Pan"
            )
            
            self.ui_elements['center_view'] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(zoom_x + int(165 * scale), row_y, int(70 * scale), button_height),
                text='Center',
                manager=self.manager,
                tool_tip_text="Center View on Segments"
            )
    
    def _build_control_panel(self):
        """Build the right side control panel with color and segment controls."""
        scale = self.ui_state['scale_factor']
        panel_y = int(10 * scale)
        panel_width = self.rects['control'].width
        
        label_width = int(120 * scale)
        self.ui_elements['palette_label'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                self.rects['control'].x + (panel_width - label_width) // 2, 
                panel_y, 
                label_width, int(20 * scale)
            ),
            text='Color Palette:',
            manager=self.manager
        )
        
        panel_y += int(25 * scale)
        
        self.ui_elements['palette_buttons'] = []
        button_width = int(40 * scale)
        palette_width = len(self.scene.palettes.keys()) * button_width
        start_x = self.rects['control'].x + (panel_width - palette_width) // 2
        
        for i, palette_id in enumerate(sorted(self.scene.palettes.keys())):
            x_pos = start_x + i * button_width
            button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(x_pos, panel_y, button_width, int(30 * scale)),
                text=palette_id,
                manager=self.manager,
                tool_tip_text=f"Select Palette {palette_id}"
            )
            self.ui_elements['palette_buttons'].append((button, palette_id))
        
        panel_y += int(40 * scale)
        
        self.ui_elements['palette_rect'] = pygame.Rect(
            self.rects['control'].x + int(10 * scale), panel_y, 
            panel_width - int(20 * scale), int(40 * scale)
        )
        
        panel_y += int(50 * scale)
        
        self.ui_elements['segment_label'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                self.rects['control'].x + (self.rects['control'].width - int(100 * scale)) // 2, 
                panel_y, 
                int(100 * scale), 
                int(20 * scale)
            ),
            text='Segment ID:',
            manager=self.manager
        )

        panel_y += int(30 * scale)
        
        segments = []
        if self.active_effect_id in self.scene.effects:
            segments = sorted(self.scene.effects[self.active_effect_id].segments.keys())
        else:
            segments = [1]
        
        segment_buttons_width = min(panel_width - int(100 * scale), len(segments) * int(35 * scale))
        button_width = int(10 * scale) + segment_buttons_width / len(segments)
        
        start_x = (self.rects['control'].x + (panel_width - segment_buttons_width) // 2 ) - int(15 * scale)
        
        self.ui_elements['segment_buttons'] = []
        for i, segment_id in enumerate(segments):
            x_pos = start_x + i * button_width
            button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(x_pos, panel_y, max(int(20 * scale), button_width - int(5 * scale)), int(30 * scale)),
                text=str(segment_id),
                manager=self.manager,
                tool_tip_text=f"Select Segment {segment_id}"
            )
            self.ui_elements['segment_buttons'].append((button, segment_id))
        
        panel_y += int(40 * scale)
        
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
        scale = self.ui_state['scale_factor']
        panel_x = self.rects['control'].x
        panel_width = self.rects['control'].width
        
        effect_id = self.active_effect_id
        segment_id = self.active_segment_id
        saved_state = None
        
        if (effect_id in self.segment_states and 
            segment_id in self.segment_states[effect_id]):
            saved_state = self.segment_states[effect_id][segment_id]

        remaining_height = self.ui_state['height'] - panel_y - int(20 * scale)
        elements_per_section = min(5, remaining_height // int(100 * scale))
        compact_mode = remaining_height < int(500 * scale)

        # Speed & Position section
        self.ui_elements['speed_heading'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(panel_x + int(10 * scale), panel_y, panel_width - int(20 * scale), int(20 * scale)),
            text='Speed & Position',
            manager=self.manager
        )
        panel_y += int(25 * scale)

        if elements_per_section >= 1:
            self.ui_elements['speed_label'] = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(panel_x + int(10 * scale), panel_y, int(100 * scale), int(20 * scale)),
                text='Move Speed:',
                manager=self.manager
            )
            
            panel_y += int(20 * scale) if compact_mode else int(25 * scale)

            current_speed = saved_state['move_speed'] if saved_state else segment.move_speed
            
            self.ui_elements['speed_slider'] = pygame_gui.elements.UIHorizontalSlider(
                relative_rect=pygame.Rect(panel_x + int(10 * scale), panel_y, panel_width - int(20 * scale), int(20 * scale)),
                start_value=current_speed,
                value_range=(-128, 127),
                manager=self.manager
            )
            
            panel_y += int(25 * scale) if compact_mode else int(30 * scale)

        if elements_per_section >= 2:
            self.ui_elements['position_label'] = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(panel_x + int(10 * scale), panel_y, int(100 * scale), int(20 * scale)),
                text='Position:',
                manager=self.manager
            )
            
            panel_y += int(20 * scale) if compact_mode else int(25 * scale)

            current_position = saved_state['current_position'] if saved_state else segment.current_position
            move_range = saved_state['move_range'] if saved_state else segment.move_range

            position = max(move_range[0], min(move_range[1], current_position))
            
            self.ui_elements['position_slider'] = pygame_gui.
