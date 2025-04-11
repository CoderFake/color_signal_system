import pygame
import pygame_gui
import sys
import os
import json
import tkinter as tk
from tkinter import filedialog
from typing import Dict, List, Tuple, Optional
import time
import math
import threading
import copy
sys.path.append('..')

from models.light_effect import LightEffect
from models.light_segment import LightSegment
from models.light_scene import LightScene
from models.scene_manager import SceneManager
from config import (
    UI_WIDTH, UI_HEIGHT, UI_BACKGROUND_COLOR, DEFAULT_COLOR_PALETTES,
    DEFAULT_FPS, DEFAULT_LED_COUNT
)


class LEDSimulator:    
    def __init__(self, scene_manager: SceneManager = None, scene: LightScene = None):
        """
        Khởi tạo LED simulator.
        
        Args:
            scene_manager: SceneManager instance để quản lý nhiều scene (ưu tiên)
            scene: LightScene instance để hiển thị (sử dụng khi không có scene_manager)
        """
        pygame.init()
        pygame.font.init()
        
        if hasattr(pygame, 'freetype'):
            pygame.freetype.init()

        self.root = tk.Tk()
        self.root.withdraw()
        self.scene_manager = scene_manager
        self.scene = None
        self.japanese_font_path = None
        self.japanese_fonts = {}
        
        if scene_manager:
            scene_id = scene_manager.current_scene if scene_manager.current_scene is not None else min(scene_manager.scenes.keys()) if scene_manager.scenes else None
            self.scene = scene_manager.scenes.get(scene_id) if scene_id is not None else scene
        elif scene:
            self.scene = scene
            
        if not self.scene:
            sys.exit(1)

            
        self.active_scene_id = self.scene.scene_ID
        self.active_effect_id = self.scene.current_effect_ID if self.scene.current_effect_ID else min(self.scene.effects.keys()) if self.scene.effects else 1
        self.active_segment_id = 1
        
        self.is_playing = True
        self.fps = DEFAULT_FPS
        self.last_segment_state = None
        self.segment_states = {}
        self.previous_layout_mode = None
        self.ui_dirty = True
        self.ui_rebuilding = False
        self.screen = pygame.display.set_mode((UI_WIDTH, UI_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("LEDテープライトシミュレーター")
        
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
            'scale_factor': 1.0,
            'dark_mode': True
        }
        
        self.led_state = {
            'size': 8,
            'spacing': 1,
            'zoom': 1.0,
            'pan': 0,
            'dragging': False,
            'last_mouse': (0, 0),
            'show_segment_indicators': True,
            'segment_indicator_opacity': 128
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
        

        self._save_segment_state()
        

        display_info = pygame.display.Info()
        base_resolution = (1920, 1080)
        self.ui_state['scale_factor'] = min(display_info.current_w / base_resolution[0], 
                                           display_info.current_h / base_resolution[1])
        self._apply_scale_factor()
        

        self.fade_visualizer = {
            'show': False,
            'position': 0,
            'width': 200,
            'height': 40
        }
        

        self.last_update_time = time.time()
        self.update_interval = 0.1
        

        self.notifications = []

        self._load_fonts()
    
    def _load_fonts(self):
        if hasattr(self, 'japanese_font_path') and self.japanese_font_path and os.path.exists(self.japanese_font_path):
            font_sizes = [12, 14, 16, 18, 24, 30]
            for size in font_sizes:
                scaled_size = int(size * self.ui_state['scale_factor'])
                self.japanese_fonts[size] = pygame.font.Font(self.japanese_font_path, scaled_size)
        else:
            available_fonts = pygame.font.get_fonts()
            japanese_system_fonts = [f for f in available_fonts if f in ['meiryo', 'msgothic', 'yugothic', 'hiragino']]
            
            if japanese_system_fonts:
                for size in [12, 14, 16, 18, 24, 30]:
                    scaled_size = int(size * self.ui_state['scale_factor'])
                    self.japanese_fonts[size] = pygame.font.SysFont(japanese_system_fonts[0], scaled_size)
    
    def _render_text(self, text, size=14, color=(255, 255, 255)):
        if hasattr(self, 'japanese_fonts') and size in self.japanese_fonts:
            return self.japanese_fonts[size].render(text, True, color)
        else:
            font = pygame.font.SysFont('Arial', int(size * self.ui_state['scale_factor']))
            return font.render(text, True, color)
        
    def _get_active_segment(self) -> Optional[LightSegment]:
        """
        Lấy segment đang được chọn.
        
        Returns:
            LightSegment đang chọn hoặc None nếu không tìm thấy
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
        """Áp dụng hệ số tỷ lệ hiện tại cho các phần tử UI"""
        scale = self.ui_state['scale_factor']
        self.led_state['size'] = int(8 * scale)
        self.led_state['spacing'] = max(1, int(1 * scale))
        

        self.rects = self._calculate_layout()
        self.ui_dirty = True

    def _calculate_layout(self) -> Dict[str, pygame.Rect]:
        """
        Tính toán bố cục cho các thành phần UI.
        
        Returns:
            Dictionary của các Pygame Rect cho mỗi vùng UI
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
            ),
            'status_bar': pygame.Rect(
                0, self.ui_state['height'] - 20,
                self.ui_state['width'], 20
            )
        }
    
    def _save_segment_state(self):
        """Lưu trạng thái chi tiết của segment hiện tại."""
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
                'dimmer_time': segment.dimmer_time.copy() if hasattr(segment.dimmer_time, 'copy') else segment.dimmer_time,
                'transparency': segment.transparency.copy() if hasattr(segment.transparency, 'copy') else segment.transparency,
                'color': segment.color.copy() if hasattr(segment.color, 'copy') else segment.color,
                'length': segment.length.copy() if hasattr(segment.length, 'copy') else segment.length,
            }
    
    def _restore_segment_state(self):
        """Khôi phục trạng thái đã lưu cho segment hiện tại."""
        segment = self._get_active_segment()
        effect_id = self.active_effect_id
        segment_id = self.active_segment_id
        
        if (segment and effect_id in self.segment_states and 
            segment_id in self.segment_states[effect_id]):
            
            state = self.segment_states[effect_id][segment_id]
            
            for key, value in state.items():
                if hasattr(segment, key):
                    if hasattr(value, 'copy'):
                        setattr(segment, key, value.copy())
                    else:
                        setattr(segment, key, value)

    def _build_ui(self):
        """Xây dựng toàn bộ UI, xóa tất cả các phần tử hiện có."""
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
                for key, value in temp_state.items():
                    if hasattr(segment, key):
                        if hasattr(value, 'copy'):
                            setattr(segment, key, value.copy())
                        else:
                            setattr(segment, key, value)
                
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
        """
        Cập nhật các điều khiển UI để phản ánh trạng thái hiện tại của segment
        
        Args:
            segment: LightSegment để lấy giá trị từ đó
        """
        try:
            controls_to_update = {
                'speed_slider': segment.move_speed,
                'position_slider': segment.current_position,
                'range_min': segment.move_range[0] if len(segment.move_range) > 0 else 0,
                'range_max': segment.move_range[1] if len(segment.move_range) > 1 else 0,
                'reflect_toggle': 'ON' if segment.is_edge_reflect else 'OFF',
                'gradient_toggle': 'ON' if hasattr(segment, 'gradient') and segment.gradient else 'OFF',
                'fade_toggle': 'ON' if hasattr(segment, 'fade') and segment.fade else 'OFF',
            }
            

            if hasattr(segment, 'dimmer_time') and len(segment.dimmer_time) >= 5:
                for i, name in enumerate(['fade_in_start', 'fade_in_end', 'fade_out_start', 'fade_out_end', 'cycle_time']):
                    if f'{name}_slider' in self.ui_elements:
                        try:
                            self.ui_elements[f'{name}_slider'].set_current_value(segment.dimmer_time[i])
                        except Exception:
                            pass
            

            if hasattr(segment, 'transparency') and len(segment.transparency) >= 4:
                for i in range(4):
                    if f'transparency_{i}_slider' in self.ui_elements:
                        try:
                            self.ui_elements[f'transparency_{i}_slider'].set_current_value(segment.transparency[i])
                        except Exception:
                            pass
            

            for name, value in controls_to_update.items():
                if name in self.ui_elements:
                    try:
                        if isinstance(self.ui_elements[name], pygame_gui.elements.UIButton):
                            self.ui_elements[name].set_text(value)
                        else:
                            self.ui_elements[name].set_current_value(value)
                    except Exception:
                        pass
                        

            if hasattr(segment, 'color') and len(segment.color) >= 4:
                for i in range(4):
                    if f'color_{i}_dropdown' in self.ui_elements:
                        try:
                            color_idx = segment.color[i]
                            if isinstance(color_idx, int) and color_idx >= 0:
                                self.ui_elements[f'color_{i}_dropdown'].selected_option = str(color_idx)
                        except Exception:
                            pass
        except Exception as e:
            print(f"Lỗi khi cập nhật UI: {e}")

    def _add_panel_toggles(self):
        """Thêm nút để mở/đóng các panel."""
        scale = self.ui_state['scale_factor']
        toggle_size = int(40 * scale)
        
        self.ui_elements['top_toggle'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                self.ui_state['width']//2 - toggle_size//2, 
                self.rects['top'].height - int(12 * scale),
                toggle_size, 
                int(18 * scale)
            ),
            text='▲' if self.ui_state['top_panel_expanded'] else '▼',
            manager=self.manager,
            tool_tip_text="Hiện/Ẩn Panel Trên"
        )

        self.ui_elements['control_toggle'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                self.rects['control'].x - int(18 * scale),
                self.ui_state['height']//2 - toggle_size//2,
                int(18 * scale), 
                toggle_size
            ),
            text='►' if self.ui_state['control_panel_expanded'] else '◄',
            manager=self.manager,
            tool_tip_text="Hiện/Ẩn Panel Điều Khiển"
        )
        
    def _build_top_panel_two_rows(self):
        scale = self.ui_state['scale_factor']
        row1_y = int(10 * scale)
        row2_y = int(40 * scale)
        button_height = int(25 * scale)
        slider_height = int(20 * scale)
        button_spacing = int(5 * scale)

        label_width = int(80 * scale)
        dropdown_width = int(80 * scale)
        button_width = int(80 * scale)

        current_x = int(10 * scale)

        self.ui_elements['play_button'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(current_x, row1_y, int(60 * scale), button_height),
            text='Dừng' if self.is_playing else 'Phát',
            manager=self.manager,
            tool_tip_text="Phát/Dừng Animation"
        )
        current_x += int(65 * scale)

        self.ui_elements['fps_label'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(current_x, row1_y, int(40 * scale), button_height),
            text='FPS:',
            manager=self.manager
        )
        current_x += int(45 * scale)
        
        self.ui_elements['fps_slider'] = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(current_x, row1_y + int(2 * scale), int(100 * scale), slider_height),
            start_value=self.fps,
            value_range=(1, 120),
            manager=self.manager
        )
        current_x += int(105 * scale)
        
        self.ui_elements['fps_value'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(current_x, row1_y, int(30 * scale), button_height),
            text=str(self.fps),
            manager=self.manager
        )
        current_x += int(40 * scale)

        self.ui_elements['scene_label'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(current_x, row1_y, label_width, button_height),
            text='Scene:',
            manager=self.manager
        )
        current_x += int(85 * scale)
        
        scenes = [self.scene.scene_ID]
        if self.scene_manager:
            scenes = sorted(self.scene_manager.scenes.keys())
            
        self.ui_elements['scene_dropdown'] = pygame_gui.elements.UIDropDownMenu(
            options_list=[str(scene_id) for scene_id in scenes],
            starting_option=str(self.active_scene_id),
            relative_rect=pygame.Rect(current_x, row1_y, dropdown_width, button_height),
            manager=self.manager
        )
        current_x += int(90 * scale)
    
        current_x = int(10 * scale)

        self.ui_elements['save_button'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(current_x, row2_y, button_width, button_height),
            text='JSONを保存',
            manager=self.manager,
            tool_tip_text="Save JSON"
        )
        current_x += button_width + button_spacing

        self.ui_elements['load_button'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(current_x, row2_y, button_width, button_height),
            text='JSONを読込',
            manager=self.manager,
            tool_tip_text="Load JSON"
        )
        current_x += button_width + button_spacing

        self.ui_elements['effect_label'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(current_x, row2_y, label_width, button_height),
            text='エフェクト:',
            manager=self.manager
        )
        current_x += int(85 * scale)
        
        effects = []
        if self.active_effect_id in self.scene.effects:
            effects = sorted(self.scene.effects.keys())
            
        self.ui_elements['effect_dropdown'] = pygame_gui.elements.UIDropDownMenu(
            options_list=[str(effect_id) for effect_id in effects],
            starting_option=str(self.active_effect_id),
            relative_rect=pygame.Rect(current_x, row2_y, dropdown_width, button_height),
            manager=self.manager
        )
        current_x += int(90 * scale)

        self.ui_elements['palette_label'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(current_x, row2_y, label_width, button_height),
            text='パレット:',
            manager=self.manager
        )
        current_x += int(85 * scale)
        
        palettes = sorted(self.scene.palettes.keys())
        self.ui_elements['palette_dropdown'] = pygame_gui.elements.UIDropDownMenu(
            options_list=palettes,
            starting_option=self.scene.current_palette,
            relative_rect=pygame.Rect(current_x, row2_y, dropdown_width, button_height),
            manager=self.manager
        )
        current_x += int(90 * scale)
        

        self.ui_elements['zoom_in'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(current_x, row2_y, int(30 * scale), button_height),
            text='+',
            manager=self.manager,
            tool_tip_text="Phóng to"
        )
        current_x += int(35 * scale)
        
        self.ui_elements['zoom_out'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(current_x, row2_y, int(30 * scale), button_height),
            text='-',
            manager=self.manager,
            tool_tip_text="Thu nhỏ"
        )
        current_x += int(35 * scale)
        
        self.ui_elements['zoom_reset'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(current_x, row2_y, int(60 * scale), button_height),
            text='Reset',
            manager=self.manager,
            tool_tip_text="Đặt lại Zoom và Pan"
        )
        current_x += int(65 * scale)
        
        self.ui_elements['center_view'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(current_x, row2_y, int(60 * scale), button_height),
            text='Giữa',
            manager=self.manager,
            tool_tip_text="Căn giữa màn hình"
        )
        current_x += int(65 * scale)
        

        self.ui_elements['show_indicators'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(current_x, row2_y, int(100 * scale), button_height),
            text='Chỉ dẫn: ON' if self.led_state['show_segment_indicators'] else 'Chỉ dẫn: OFF',
            manager=self.manager,
            tool_tip_text="Hiện/Ẩn chỉ dẫn segment"
        )

    def _build_control_panel(self):
        if not self.ui_state['control_panel_expanded']:
            return

        scale = self.ui_state['scale_factor']
        panel_rect = self.rects['control']
        

        control_panel = pygame_gui.elements.UIPanel(
            relative_rect=panel_rect,
            manager=self.manager
        )
        
        current_y = int(10 * scale)

        label_height = int(25 * scale)  
        label_width = int(100 * scale)  
        
        segments = []
        if self.active_effect_id in self.scene.effects:
            effect = self.scene.effects[self.active_effect_id]
            segments = sorted(effect.segments.keys())
        
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(int(10 * scale), current_y, label_width, label_height),
            text='Segment:',
            manager=self.manager,
            container=control_panel
        )
        
        self.ui_elements['segment_dropdown'] = pygame_gui.elements.UIDropDownMenu(
            options_list=[str(seg_id) for seg_id in segments],
            starting_option=str(self.active_segment_id),
            relative_rect=pygame.Rect(int(120 * scale), current_y, int(60 * scale), label_height),
            manager=self.manager,
            container=control_panel
        )
        
        current_y += int(35 * scale)
        

        button_width = int(120 * scale)
        self.ui_elements['add_segment'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(int(10 * scale), current_y, button_width, label_height),
            text='セグメント追加',
            manager=self.manager,
            container=control_panel
        )
        
        current_y += int(35 * scale)
        
        self.ui_elements['remove_segment'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(int(10 * scale), current_y, button_width, label_height),
            text='セグメント削除',
            manager=self.manager,
            container=control_panel
        )
        
        current_y += int(45 * scale)
        

        segment = self._get_active_segment()
        if segment:

            pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(int(10 * scale), current_y, label_width, label_height),
                text='位置:',
                manager=self.manager,
                container=control_panel
            )
            
            self.ui_elements['position_slider'] = pygame_gui.elements.UIHorizontalSlider(
                relative_rect=pygame.Rect(int(120 * scale), current_y, int(150 * scale), label_height),
                start_value=segment.current_position,
                value_range=(0, DEFAULT_LED_COUNT),
                manager=self.manager,
                container=control_panel
            )
            
            current_y += int(35 * scale)
            

            pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(int(10 * scale), current_y, label_width, label_height),
                text='速度:',
                manager=self.manager,
                container=control_panel
            )
            
            self.ui_elements['speed_slider'] = pygame_gui.elements.UIHorizontalSlider(
                relative_rect=pygame.Rect(int(120 * scale), current_y, int(150 * scale), label_height),
                start_value=segment.move_speed,
                value_range=(-50, 50),
                manager=self.manager,
                container=control_panel
            )
            
            current_y += int(35 * scale)
            

            pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(int(10 * scale), current_y, label_width, label_height),
                text='範囲:',
                manager=self.manager,
                container=control_panel
            )
            
            range_min = segment.move_range[0] if len(segment.move_range) > 0 else 0
            range_max = segment.move_range[1] if len(segment.move_range) > 1 else DEFAULT_LED_COUNT
            
            self.ui_elements['range_min'] = pygame_gui.elements.UIHorizontalSlider(
                relative_rect=pygame.Rect(int(120 * scale), current_y, int(70 * scale), label_height),
                start_value=range_min,
                value_range=(0, DEFAULT_LED_COUNT),
                manager=self.manager,
                container=control_panel
            )
            
            self.ui_elements['range_max'] = pygame_gui.elements.UIHorizontalSlider(
                relative_rect=pygame.Rect(int(200 * scale), current_y, int(70 * scale), label_height),
                start_value=range_max,
                value_range=(0, DEFAULT_LED_COUNT),
                manager=self.manager,
                container=control_panel
            )
            
            current_y += int(35 * scale)
            

            button_width = int(80 * scale)
            self.ui_elements['reflect_toggle'] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(int(10 * scale), current_y, button_width, label_height),
                text='オン' if segment.is_edge_reflect else 'オフ',
                manager=self.manager,
                container=control_panel
            )
            
            pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(int(100 * scale), current_y, int(170 * scale), label_height),
                text='エッジ反射',
                manager=self.manager,
                container=control_panel
            )
            
            current_y += int(35 * scale)
            
            self.ui_elements['gradient_toggle'] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(int(10 * scale), current_y, button_width, label_height),
                text='オン' if hasattr(segment, 'gradient') and segment.gradient else 'オフ',
                manager=self.manager,
                container=control_panel
            )
            
            pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(int(100 * scale), current_y, int(170 * scale), label_height),
                text='グラデーション',
                manager=self.manager,
                container=control_panel
            )
            
            current_y += int(35 * scale)
            
            self.ui_elements['fade_toggle'] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(int(10 * scale), current_y, button_width, label_height),
                text='ON' if hasattr(segment, 'fade') and segment.fade else 'OFF',
                manager=self.manager,
                container=control_panel
            )
            
            pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(int(100 * scale), current_y, int(170 * scale), label_height),
                text='Fade',
                manager=self.manager,
                container=control_panel
            )

    def _build_top_panel_one_row(self):
        scale = self.ui_state['scale_factor']
        row_y = int(10 * scale)

        button_height = int(30 * scale)  
        slider_height = int(25 * scale)  
        button_spacing = int(8 * scale) 
        
        label_width = int(80 * scale) 
        dropdown_width = int(80 * scale)

        current_x = int(10 * scale)
        

        self.ui_elements['play_button'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(current_x, row_y, int(70 * scale), button_height),
            text='Dừng' if self.is_playing else 'Phát',
            manager=self.manager,
            tool_tip_text="再生/停止"
        )
        current_x += int(80 * scale)
        

        self.ui_elements['fps_label'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(current_x, row_y, int(50 * scale), button_height),
            text='FPS:',
            manager=self.manager
        )
        current_x += int(55 * scale)
        
        self.ui_elements['fps_slider'] = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(current_x, row_y + int(2 * scale), int(100 * scale), slider_height),
            start_value=self.fps,
            value_range=(1, 120),
            manager=self.manager
        )
        current_x += int(110 * scale)
        
        self.ui_elements['fps_value'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(current_x, row_y, int(40 * scale), button_height),
            text=str(self.fps),
            manager=self.manager
        )
        current_x += int(50 * scale)


        self.ui_elements['scene_label'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(current_x, row_y, label_width, button_height),
            text='シーン:',
            manager=self.manager
        )
        current_x += int(85 * scale)
        
        scenes = [self.scene.scene_ID]
        if self.scene_manager:
            scenes = sorted(self.scene_manager.scenes.keys())
            
        self.ui_elements['scene_dropdown'] = pygame_gui.elements.UIDropDownMenu(
            options_list=[str(scene_id) for scene_id in scenes],
            starting_option=str(self.active_scene_id),
            relative_rect=pygame.Rect(current_x, row_y, dropdown_width, button_height),
            manager=self.manager
        )
        current_x += int(90 * scale)


        self.ui_elements['effect_label'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(current_x, row_y, label_width, button_height),
            text='エフェクト:',
            manager=self.manager
        )
        current_x += int(85 * scale)
        
        effects = []
        if self.active_effect_id in self.scene.effects:
            effects = sorted(self.scene.effects.keys())
            
        self.ui_elements['effect_dropdown'] = pygame_gui.elements.UIDropDownMenu(
            options_list=[str(effect_id) for effect_id in effects],
            starting_option=str(self.active_effect_id),
            relative_rect=pygame.Rect(current_x, row_y, dropdown_width, button_height),
            manager=self.manager
        )
        current_x += int(90 * scale)


        self.ui_elements['palette_label'] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(current_x, row_y, label_width, button_height),
            text='パレット:',
            manager=self.manager
        )
        current_x += int(85 * scale)
        
        palettes = sorted(self.scene.palettes.keys())
        self.ui_elements['palette_dropdown'] = pygame_gui.elements.UIDropDownMenu(
            options_list=palettes,
            starting_option=self.scene.current_palette,
            relative_rect=pygame.Rect(current_x, row_y, dropdown_width, button_height),
            manager=self.manager
        )
        current_x += int(90 * scale)


        button_width = int(90 * scale)
        
        self.ui_elements['save_button'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(current_x, row_y, button_width, button_height),
            text='JSONを保存',
            manager=self.manager,
            tool_tip_text="Save JSON"
        )
        current_x += button_width + button_spacing
        
        self.ui_elements['load_button'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(current_x, row_y, button_width, button_height),
            text='JSONを読込',
            manager=self.manager,
            tool_tip_text="Load JSON"
        )
        current_x += button_width + button_spacing


        remaining_width = self.ui_state['width'] - current_x - int(20 * scale)
        if remaining_width >= int(280 * scale):
            self.ui_elements['zoom_in'] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(current_x, row_y, int(35 * scale), button_height),
                text='+',
                manager=self.manager,
                tool_tip_text="拡大"
            )
            current_x += int(40 * scale)
            
            self.ui_elements['zoom_out'] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(current_x, row_y, int(35 * scale), button_height),
                text='-',
                manager=self.manager,
                tool_tip_text="縮小"
            )
            current_x += int(40 * scale)
            
            self.ui_elements['zoom_reset'] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(current_x, row_y, int(70 * scale), button_height),
                text='リセット',
                manager=self.manager,
                tool_tip_text="ズームとパンをリセット"
            )
            current_x += int(75 * scale)
            
            self.ui_elements['center_view'] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(current_x, row_y, int(70 * scale), button_height),
                text='中心',
                manager=self.manager,
                tool_tip_text="画面の中央に配置"
            )
            current_x += int(75 * scale)
            
            self.ui_elements['show_indicators'] = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(current_x, row_y, int(110 * scale), button_height),
                text='表示: オン' if self.led_state['show_segment_indicators'] else '表示: オフ',
                manager=self.manager,
                tool_tip_text="セグメント表示の切替"
            )

    def _center_view(self):
        """Căn giữa view hiệu ứng LED."""

        min_pos = DEFAULT_LED_COUNT
        max_pos = 0
        
        for effect in self.scene.effects.values():
            for segment in effect.segments.values():
                total_length = sum(segment.length) if hasattr(segment, 'length') else 0
                segment_start = segment.current_position - total_length // 2
                segment_end = segment.current_position + total_length // 2
                
                min_pos = min(min_pos, segment_start)
                max_pos = max(max_pos, segment_end)
        
        if min_pos >= DEFAULT_LED_COUNT or max_pos <= 0:
            min_pos = 0
            max_pos = DEFAULT_LED_COUNT - 1
        

        padding = (max_pos - min_pos) * 0.1
        min_pos = max(0, min_pos - padding)
        max_pos = min(DEFAULT_LED_COUNT - 1, max_pos + padding)
        

        display_width = self.rects['display'].width
        led_size = self.led_state['size'] + self.led_state['spacing']
        required_width = (max_pos - min_pos + 1) * led_size
        
        self.led_state['zoom'] = min(2.0, max(0.2, display_width / required_width))
        center_led = (min_pos + max_pos) / 2
        self.led_state['pan'] = center_led - DEFAULT_LED_COUNT / 2
        
    def _handle_ui_event(self, event):
        """
        Xử lý sự kiện từ UI.
        
        Args:
            event: Sự kiện pygame_gui
        """
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            self._handle_button_press(event)
        elif event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
            self._handle_slider_moved(event)
        elif event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            self._handle_dropdown_changed(event)
    
    def _handle_button_press(self, event):
        """
        Xử lý sự kiện nhấn nút.
        
        Args:
            event: Sự kiện pygame_gui
        """

        if event.ui_element == self.ui_elements.get('top_toggle'):
            self.ui_state['top_panel_expanded'] = not self.ui_state['top_panel_expanded']
            self.ui_dirty = True
        
        elif event.ui_element == self.ui_elements.get('control_toggle'):
            self.ui_state['control_panel_expanded'] = not self.ui_state['control_panel_expanded']
            self.ui_dirty = True
        

        elif event.ui_element == self.ui_elements.get('play_button'):
            self.is_playing = not self.is_playing
            event.ui_element.set_text('停止' if self.is_playing else '再生')
        

        elif event.ui_element == self.ui_elements.get('zoom_in'):
            self.led_state['zoom'] = min(10.0, self.led_state['zoom'] * 1.2)
        
        elif event.ui_element == self.ui_elements.get('zoom_out'):
            self.led_state['zoom'] = max(0.1, self.led_state['zoom'] / 1.2)
        
        elif event.ui_element == self.ui_elements.get('zoom_reset'):
            self.led_state['zoom'] = 1.0
            self.led_state['pan'] = 0
        
        elif event.ui_element == self.ui_elements.get('center_view'):
            self._center_view()
        

        elif event.ui_element == self.ui_elements.get('show_indicators'):
            self.led_state['show_segment_indicators'] = not self.led_state['show_segment_indicators']
            event.ui_element.set_text(f"Chỉ dẫn: {'ON' if self.led_state['show_segment_indicators'] else 'OFF'}")
        

        elif event.ui_element in [self.ui_elements.get('fade_toggle'), self.ui_elements.get('fade_toggle_2')]:
            segment = self._get_active_segment()
            if segment:
                if hasattr(segment, 'fade'):
                    segment.fade = not segment.fade
                else:
                    segment.fade = True
                
                text = 'ON' if segment.fade else 'OFF'
                if self.ui_elements.get('fade_toggle'):
                    self.ui_elements['fade_toggle'].set_text(text)
                if self.ui_elements.get('fade_toggle_2'):
                    self.ui_elements['fade_toggle_2'].set_text(text)
        
        elif event.ui_element == self.ui_elements.get('gradient_toggle'):
            segment = self._get_active_segment()
            if segment:
                if hasattr(segment, 'gradient'):
                    segment.gradient = not segment.gradient
                else:
                    segment.gradient = True
                    
                if segment.gradient and (not hasattr(segment, 'gradient_colors') or segment.gradient_colors[0] == 0):
                    segment.gradient_colors = [1, 0, 1] 
                
                event.ui_element.set_text('オン' if segment.gradient else 'オフ')
        

        elif event.ui_element == self.ui_elements.get('reflect_toggle'):
            segment = self._get_active_segment()
            if segment:
                segment.is_edge_reflect = not segment.is_edge_reflect
                event.ui_element.set_text('オン' if segment.is_edge_reflect else 'オフ')
        

        elif event.ui_element == self.ui_elements.get('show_fade_viz'):
            self.fade_visualizer['show'] = not self.fade_visualizer['show']
            event.ui_element.set_text('フェード画像を非表示' if self.fade_visualizer['show'] else 'フェード画像を表示')
        

        elif event.ui_element == self.ui_elements.get('add_segment'):
            if self.active_effect_id in self.scene.effects:
                effect = self.scene.effects[self.active_effect_id]
                

                new_id = 1
                while new_id in effect.segments:
                    new_id += 1
                

                from models.light_segment import LightSegment
                from config import DEFAULT_TRANSPARENCY, DEFAULT_LENGTH, DEFAULT_MOVE_SPEED, DEFAULT_MOVE_RANGE, DEFAULT_INITIAL_POSITION, DEFAULT_IS_EDGE_REFLECT, DEFAULT_DIMMER_TIME
                
                new_segment = LightSegment(
                    segment_ID=new_id,
                    color=[0, 1, 2, 3],
                    transparency=DEFAULT_TRANSPARENCY,
                    length=DEFAULT_LENGTH,
                    move_speed=DEFAULT_MOVE_SPEED,
                    move_range=DEFAULT_MOVE_RANGE,
                    initial_position=DEFAULT_INITIAL_POSITION,
                    is_edge_reflect=DEFAULT_IS_EDGE_REFLECT,
                    dimmer_time=DEFAULT_DIMMER_TIME
                )
                
                effect.add_segment(new_id, new_segment)
                self.active_segment_id = new_id
                self.ui_dirty = True
                
                self._add_notification(f"セグメントが追加されました {new_id}")
        
        elif event.ui_element == self.ui_elements.get('remove_segment'):
            if self.active_effect_id in self.scene.effects:
                effect = self.scene.effects[self.active_effect_id]
                
                if self.active_segment_id in effect.segments:
                    effect.remove_segment(self.active_segment_id)
                    

                    if effect.segments:
                        self.active_segment_id = min(effect.segments.keys())
                    else:
                        self.active_segment_id = None
                    
                    self.ui_dirty = True
                    self._add_notification(f"セグメントが削除されました {self.active_segment_id}")
        

        elif event.ui_element == self.ui_elements.get('save_button'):
            self._save_json_config()
        
        elif event.ui_element == self.ui_elements.get('load_button'):
            self._load_json_config()
    
    def _handle_slider_moved(self, event):
        """
        Xử lý sự kiện di chuyển thanh trượt.
        
        Args:
            event: Sự kiện pygame_gui
        """
        segment = self._get_active_segment()
        if not segment:
            return
            

        if event.ui_element == self.ui_elements.get('fps_slider'):
            self.fps = int(event.value)
            if self.ui_elements.get('fps_value'):
                self.ui_elements['fps_value'].set_text(str(self.fps))
        

        elif event.ui_element == self.ui_elements.get('speed_slider'):
            segment.move_speed = event.value
        
        elif event.ui_element == self.ui_elements.get('position_slider'):
            segment.current_position = event.value
        
        elif event.ui_element == self.ui_elements.get('initial_position_slider'):
            segment.initial_position = int(event.value)
        

        elif event.ui_element == self.ui_elements.get('range_min'):

            new_min = min(int(event.value), segment.move_range[1])
            segment.move_range[0] = new_min
            if self.ui_elements.get('range_min'):
                self.ui_elements['range_min'].set_current_value(new_min)
        
        elif event.ui_element == self.ui_elements.get('range_max'):

            new_max = max(int(event.value), segment.move_range[0])
            segment.move_range[1] = new_max
            if self.ui_elements.get('range_max'):
                self.ui_elements['range_max'].set_current_value(new_max)
        

        for i in range(4):  # 4 vị trí độ trong suốt
            if event.ui_element == self.ui_elements.get(f'transparency_{i}_slider'):
                if i < len(segment.transparency):
                    segment.transparency[i] = event.value
                

        for i in range(5):  # 5 tham số dimmer_time
            if event.ui_element == self.ui_elements.get(f'dimmer_time_{i}_slider'):
                if hasattr(segment, 'dimmer_time') and i < len(segment.dimmer_time):
                    segment.dimmer_time[i] = int(event.value)
        

        for i in range(3):  # 3 phần chiều dài
            if event.ui_element == self.ui_elements.get(f'length_{i}_slider'):
                if i < len(segment.length):
                    segment.length[i] = int(event.value)
                    

                    if self.ui_elements.get('total_length_label'):
                        total_length = sum(segment.length)
                        self.ui_elements['total_length_label'].set_text(str(total_length))
    
    def _handle_dropdown_changed(self, event):
        """
        Xử lý sự kiện thay đổi dropdown.
        
        Args:
            event: Sự kiện pygame_gui
        """

        if event.ui_element == self.ui_elements.get('scene_dropdown'):
            scene_id = int(event.text)
            if self.scene_manager and scene_id in self.scene_manager.scenes:
                self.scene_manager.switch_scene(scene_id)
                self.scene = self.scene_manager.scenes[scene_id]
                self.active_scene_id = scene_id
                

                if self.scene.effects:
                    self.active_effect_id = self.scene.current_effect_ID or min(self.scene.effects.keys())
                    effect = self.scene.effects.get(self.active_effect_id)
                    if effect and effect.segments:
                        self.active_segment_id = min(effect.segments.keys())
                self.ui_dirty = True
        

        elif event.ui_element == self.ui_elements.get('effect_dropdown'):
            effect_id = int(event.text)
            if effect_id in self.scene.effects:
                self.scene.switch_effect(effect_id)
                self.active_effect_id = effect_id
                

                effect = self.scene.effects[effect_id]
                if effect.segments:
                    self.active_segment_id = min(effect.segments.keys())
                self.ui_dirty = True
        

        elif event.ui_element == self.ui_elements.get('palette_dropdown'):
            palette_id = event.text
            if palette_id in self.scene.palettes:
                self.scene.set_palette(palette_id)
        

        elif event.ui_element == self.ui_elements.get('segment_dropdown'):
            segment_id = int(event.text)
            if self.active_effect_id in self.scene.effects:
                effect = self.scene.effects[self.active_effect_id]
                if segment_id in effect.segments:
                    self.active_segment_id = segment_id
                    self.ui_dirty = True
        

        segment = self._get_active_segment()
        if segment:
            for i in range(4):  # 4 vị trí màu
                if event.ui_element == self.ui_elements.get(f'color_{i}_dropdown'):
                    color_idx = int(event.text)
                    if i < len(segment.color):
                        segment.color[i] = color_idx

                        if hasattr(segment, 'calculate_rgb'):
                            segment.rgb_color = segment.calculate_rgb(self.scene.current_palette)
    
    def _save_json_config(self):
        """Lưu cấu hình hiện tại vào file JSON."""
        try:
            filename = filedialog.asksaveasfilename(
                title="Lưu cấu hình",
                defaultextension=".json",
                filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
            )
            
            if filename:
                if self.scene_manager:
                    if self.active_scene_id in self.scene_manager.scenes:
                        self.scene_manager.scenes[self.active_scene_id].save_to_json(filename)
                    else:
                        self.scene_manager.save_scenes_to_json(filename)
                else:
                    self.scene.save_to_json(filename)
                
                self._add_notification(f"設定を保存しました {filename}")
        except Exception as e:
            self._add_notification(f"保存エラー： {str(e)}")
    
    def _load_json_config(self):
        try:
            filename = filedialog.askopenfilename(
                title="ロード構成",
                defaultextension=".json",
                filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
            )
            
            if filename:
                if self.scene_manager:
                    try:
                        self.scene_manager.load_scenes_from_json(filename)
                        scene_id = self.scene_manager.current_scene or min(self.scene_manager.scenes.keys())
                        self.scene = self.scene_manager.scenes[scene_id]
                        self.active_scene_id = scene_id
                    except:

                        from models.light_scene import LightScene
                        new_scene = LightScene.load_from_json(filename)
                        self.scene_manager.scenes[new_scene.scene_ID] = new_scene
                        self.scene_manager.current_scene = new_scene.scene_ID
                        self.scene = new_scene
                        self.active_scene_id = new_scene.scene_ID
                else:
                    from models.light_scene import LightScene
                    self.scene = LightScene.load_from_json(filename)
                    self.active_scene_id = self.scene.scene_ID
                

                if self.scene.effects:
                    self.active_effect_id = self.scene.current_effect_ID or min(self.scene.effects.keys())
                    effect = self.scene.effects.get(self.active_effect_id)
                    if effect and effect.segments:
                        self.active_segment_id = min(effect.segments.keys())
                
                self.ui_dirty = True
                self._add_notification(f"設定を読み込みました {filename}")
        except Exception as e:
            self._add_notification(f"読込エラー： {str(e)}")
    
    def _add_notification(self, message, duration=3.0):
        """
        Thêm thông báo vào hàng đợi.
        
        Args:
            message: Nội dung thông báo
            duration: Thời gian hiển thị (giây)
        """
        self.notifications.append({
            'message': message,
            'time': time.time(),
            'duration': duration
        })
    
    def _update_notifications(self):
        """Cập nhật và xóa các thông báo đã hết hạn."""
        current_time = time.time()
        self.notifications = [n for n in self.notifications 
                             if current_time - n['time'] < n['duration']]
    
    def _render_notifications(self):
        if not self.notifications:
            return
        
        notification_height = int(30 * self.ui_state['scale_factor'])
        padding = int(10 * self.ui_state['scale_factor'])
        
        for i, notification in enumerate(self.notifications):
            elapsed = time.time() - notification['time']
            remaining = notification['duration'] - elapsed
            alpha = min(255, max(0, int(255 * remaining / min(1.0, notification['duration'] / 3))))
            
            text_surface = self._render_text(notification['message'], 14, (255, 255, 255))
            text_width = text_surface.get_width() + padding * 2
            
            bg_surface = pygame.Surface((text_width, notification_height), pygame.SRCALPHA)
            bg_surface.fill((40, 40, 40, alpha))
            
            bg_surface.blit(text_surface, (padding, (notification_height - text_surface.get_height()) // 2))
            
            x = self.ui_state['width'] - text_width - padding
            y = self.ui_state['height'] - notification_height - padding - i * (notification_height + padding)
            
            self.screen.blit(bg_surface, (x, y))

    def _draw_led_visualizer(self, display_rect):
        segment = self._get_active_segment()
        if not segment or not hasattr(segment, 'dimmer_time') or len(segment.dimmer_time) < 5:
            return
            
        fade_in_start = segment.dimmer_time[0]
        fade_in_end = segment.dimmer_time[1]
        fade_out_start = segment.dimmer_time[2]
        fade_out_end = segment.dimmer_time[3]
        cycle_time = segment.dimmer_time[4]
        
        if cycle_time <= 0:
            return
            
        width = int(min(400, display_rect.width - 40) * self.ui_state['scale_factor'])
        height = int(40 * self.ui_state['scale_factor'])
        x = display_rect.x + (display_rect.width - width) // 2
        y = display_rect.y + int(20 * self.ui_state['scale_factor'])
        
        fade_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        fade_surface.fill((0, 0, 0, 180))
        
        def time_to_pos(t):
            return int(t / cycle_time * width)
        
        in_start_pos = time_to_pos(fade_in_start)
        in_end_pos = time_to_pos(fade_in_end)
        out_start_pos = time_to_pos(fade_out_start)
        out_end_pos = time_to_pos(fade_out_end)
        
        pygame.draw.rect(fade_surface, (50, 50, 50, 200), (0, 0, width, height), 1)
        
        pygame.draw.rect(fade_surface, (100, 255, 100, 100), 
                        (in_start_pos, 0, in_end_pos - in_start_pos, height))
        
        pygame.draw.rect(fade_surface, (255, 255, 100, 100), 
                        (in_end_pos, 0, out_start_pos - in_end_pos, height))
        
        pygame.draw.rect(fade_surface, (255, 100, 100, 100), 
                        (out_start_pos, 0, out_end_pos - out_start_pos, height))
        
        current_time = int((segment.time * 1000) % cycle_time)
        current_pos = time_to_pos(current_time)
        pygame.draw.line(fade_surface, (255, 255, 255, 200), 
                        (current_pos, 0), (current_pos, height), 2)
        
        for i, t in enumerate([fade_in_start, fade_in_end, fade_out_start, fade_out_end]):
            pos = time_to_pos(t)
            label = ['In Start', 'In End', 'Out Start', 'Out End'][i]
            text_surface = self._render_text(f"{label}: {t}ms", 10, (255, 255, 255))
            y_offset = i % 2 * int(12 * self.ui_state['scale_factor'])
            fade_surface.blit(text_surface, (pos - text_surface.get_width() // 2, y_offset))
        
        text_current = self._render_text(f"Time: {current_time}ms", 10, (255, 255, 255))
        fade_surface.blit(text_current, (current_pos + 5, height - text_current.get_height()))
        
        brightness = segment.apply_dimming() if hasattr(segment, 'apply_dimming') else 1.0
        brightness_text = self._render_text(f"Brightness: {brightness:.2f}", 10, (255, 255, 255))
        fade_surface.blit(brightness_text, (5, height - brightness_text.get_height()))
        
        self.screen.blit(fade_surface, (x, y))
    
    def _draw_color_palette(self):
        """Vẽ bảng màu hiện tại."""
        if 'color_slots' not in self.ui_elements:
            return
            
        for rect, color in self.ui_elements['color_slots']:
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, (200, 200, 200), rect, 1)
    
    def _draw_status_bar(self):
        status_rect = self.rects['status_bar']
        pygame.draw.rect(self.screen, (30, 30, 30), status_rect)
        
        segment = self._get_active_segment()
        
        if segment:
            status_text = f"Scene: {self.active_scene_id} | Effect: {self.active_effect_id} | Segment: {self.active_segment_id}"
            status_text += f" | Pos: {int(segment.current_position)} | Speed: {segment.move_speed:.1f}"
            status_text += f" | FPS: {self.fps}"
            
            text_surface = self._render_text(status_text, 12, (200, 200, 200))
            self.screen.blit(text_surface, (status_rect.x + 10, status_rect.y + (status_rect.height - text_surface.get_height()) // 2))
    
    def _handle_event(self, event):
        """
        Xử lý sự kiện Pygame.
        
        Args:
            event: Sự kiện Pygame
        """

        self.activity['last_time'] = time.time()
        

        if event.type == pygame.QUIT:
            return False
        

        elif event.type == pygame.VIDEORESIZE:
            self.ui_state['width'] = event.w
            self.ui_state['height'] = event.h
            self.ui_state['resizing'] = True
            self.ui_state['resize_time'] = time.time()
            self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            self.ui_dirty = True
        

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Chuột trái
                self._handle_left_click(event)
            elif event.button in (4, 5):  # Cuộn chuột
                self._handle_mouse_wheel(event)
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # Chuột trái
                self.led_state['dragging'] = False
        
        elif event.type == pygame.MOUSEMOTION:
            self._handle_mouse_motion(event)
        

        elif event.type == pygame.KEYDOWN:
            self._handle_key_press(event)
        

        self.manager.process_events(event)
        if event.type in (pygame_gui.UI_BUTTON_PRESSED, pygame_gui.UI_HORIZONTAL_SLIDER_MOVED, pygame_gui.UI_DROP_DOWN_MENU_CHANGED):
            self._handle_ui_event(event)
        
        return True
    
    def _handle_left_click(self, event):
        """
        Xử lý sự kiện nhấn chuột trái.
        
        Args:
            event: Sự kiện Pygame
        """

        if self.rects['display'].collidepoint(event.pos):
            self.led_state['dragging'] = True
            self.led_state['last_mouse'] = event.pos
    
    def _handle_mouse_wheel(self, event):
        """
        Xử lý sự kiện cuộn chuột.
        
        Args:
            event: Sự kiện Pygame
        """

        if self.rects['display'].collidepoint(event.pos):
            if event.button == 4:  # Cuộn lên
                self.led_state['zoom'] = min(10.0, self.led_state['zoom'] * 1.1)
            else:  # Cuộn xuống
                self.led_state['zoom'] = max(0.1, self.led_state['zoom'] / 1.1)
    
    def _handle_mouse_motion(self, event):
        """
        Xử lý sự kiện di chuyển chuột.
        
        Args:
            event: Sự kiện Pygame
        """

        if self.led_state['dragging'] and hasattr(event, 'rel'):
            dx = event.rel[0]
            led_size = (self.led_state['size'] + self.led_state['spacing']) * self.led_state['zoom']
            self.led_state['pan'] -= dx / led_size
            self.led_state['last_mouse'] = event.pos
    
    def _handle_key_press(self, event):
        """
        Xử lý sự kiện nhấn phím.
        
        Args:
            event: Sự kiện Pygame
        """

        if event.key == pygame.K_SPACE:
            self.is_playing = not self.is_playing
            if 'play_button' in self.ui_elements:
                self.ui_elements['play_button'].set_text('Dừng' if self.is_playing else 'Phát')
        

        elif event.key == pygame.K_LEFT:
            self.led_state['pan'] -= 10 / self.led_state['zoom']
        elif event.key == pygame.K_RIGHT:
            self.led_state['pan'] += 10 / self.led_state['zoom']
        

        elif event.key in (pygame.K_PLUS, pygame.K_EQUALS):
            self.led_state['zoom'] = min(10.0, self.led_state['zoom'] * 1.2)
        elif event.key == pygame.K_MINUS:
            self.led_state['zoom'] = max(0.1, self.led_state['zoom'] / 1.2)
        

        elif event.key == pygame.K_0:
            self.led_state['zoom'] = 1.0
            self.led_state['pan'] = 0
        

        elif event.key == pygame.K_c:
            self._center_view()
        

        elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
            self._save_json_config()
        

        elif event.key in (pygame.K_l, pygame.K_o) and pygame.key.get_mods() & pygame.KMOD_CTRL:
            self._load_json_config()
        

        elif event.key == pygame.K_f:
            self.fade_visualizer['show'] = not self.fade_visualizer['show']
        

        elif event.key == pygame.K_i:
            self.led_state['show_segment_indicators'] = not self.led_state['show_segment_indicators']
            if 'show_indicators' in self.ui_elements:
                self.ui_elements['show_indicators'].set_text(f"Chỉ dẫn: {'ON' if self.led_state['show_segment_indicators'] else 'OFF'}")
        

        elif event.key == pygame.K_TAB:
            if self.active_effect_id in self.scene.effects:
                effect = self.scene.effects[self.active_effect_id]
                if effect.segments:
                    segments = sorted(effect.segments.keys())
                    idx = segments.index(self.active_segment_id) if self.active_segment_id in segments else -1
                    self.active_segment_id = segments[(idx + 1) % len(segments)]
                    self.ui_dirty = True
    
    def _update_auto_hide(self):
        """Cập nhật trạng thái tự động ẩn UI nếu không có hoạt động."""
        if not self.ui_state['auto_hide_enabled']:
            return
            
        current_time = time.time()
        if current_time - self.activity['last_time'] > self.activity['timeout']:
            if self.ui_state['top_panel_expanded'] or self.ui_state['control_panel_expanded']:
                self.ui_state['top_panel_expanded'] = False
                self.ui_state['control_panel_expanded'] = False
                self.ui_dirty = True
        else:
            if not self.ui_state['top_panel_expanded'] or not self.ui_state['control_panel_expanded']:
                self.ui_state['top_panel_expanded'] = True
                self.ui_state['control_panel_expanded'] = True
                self.ui_dirty = True
    
    def _update_real_time(self):
        """Cập nhật liên tục các điều khiển theo thời gian thực."""
        current_time = time.time()
        

        if current_time - self.last_update_time < self.update_interval:
            return
            
        self.last_update_time = current_time
        
        segment = self._get_active_segment()
        if segment and not self.ui_rebuilding:

            self._update_ui_controls(segment)
    
    def _check_resizing_complete(self):
        """Kiểm tra nếu việc thay đổi kích thước đã hoàn tất."""
        if self.ui_state['resizing'] and time.time() - self.ui_state['resize_time'] > 0.2:
            self.ui_state['resizing'] = False
            self.ui_dirty = True
    
    def run(self):
        running = True
        
        while running:
            time_delta = self.clock.tick(self.fps) / 1000.0
            

            self._check_resizing_complete()
            

            self._update_auto_hide()
            

            self._update_real_time()
            

            self._update_notifications()
            

            for event in pygame.event.get():
                if not self._handle_event(event):
                    running = False
                    break
            

            self.manager.update(time_delta)
            

            if self.ui_dirty and not self.ui_rebuilding:
                self._build_ui()
            

            if self.is_playing:
                if self.scene_manager:
                    self.scene_manager.update()
                else:
                    self.scene.update()
            

            self.screen.fill(UI_BACKGROUND_COLOR)
            

            self._draw_led_visualizer()
            

            self._draw_color_palette()
            

            self._draw_status_bar()
            

            self.manager.draw_ui(self.screen)
            

            self._render_notifications()
            

            pygame.display.update()
        

        pygame.quit()