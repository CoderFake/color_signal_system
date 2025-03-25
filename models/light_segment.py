from typing import List, Any, Dict
import numpy as np
import sys
import math
sys.path.append('..')
from config import DEFAULT_COLOR_PALETTES
from utils.color_utils import interpolate_colors

class LightSegment:

    def __init__(self, segment_ID: int, color: List[int], transparency: List[float], 
                length: List[int], move_speed: float, move_range: List[int], 
                initial_position: int, is_edge_reflect: bool, dimmer_time: List[int]):
        self.segment_ID = segment_ID
        self.color = color
        self.transparency = transparency
        self.length = length
        self.move_speed = move_speed
        self.move_range = move_range
        self.initial_position = initial_position
        self.current_position = float(initial_position)
        self.is_edge_reflect = is_edge_reflect
        self.dimmer_time = dimmer_time
        self.time = 0.0
        

        self.gradient = False
        self.fade = False
        self.gradient_colors = [0, -1, -1]

        self.rgb_color = self.calculate_rgb()
        self.total_length = sum(self.length)

    def update_param(self, param_name: str, value: Any):
        """
        Update a specified parameter with a new value.
        
        Args:
            param_name: Name of the parameter to update
            value: New value for the parameter
        """
        if param_name == 'color':
            setattr(self, param_name, value)
            self.rgb_color = self.calculate_rgb()
        else:
            setattr(self, param_name, value)
            

        if param_name == 'move_range':
            if self.current_position < self.move_range[0]:
                self.current_position = self.move_range[0]
            elif self.current_position > self.move_range[1]:
                self.current_position = self.move_range[1]
    
    def update_position(self, fps: int):
        """
        Update the position of the segment based on the frame rate and move_speed.
        
        Args:
            fps: Frames per second
        """
        dt = 1.0 / fps
        self.time += dt
        

        delta = self.move_speed * dt
        self.current_position += delta
        

        if self.is_edge_reflect:
            if self.current_position < self.move_range[0]:

                self.current_position = 2 * self.move_range[0] - self.current_position
                self.move_speed *= -1
            elif self.current_position > self.move_range[1]:

                self.current_position = 2 * self.move_range[1] - self.current_position
                self.move_speed *= -1
        else:

            if self.current_position < self.move_range[0]:
                self.current_position = self.move_range[1] - (self.move_range[0] - self.current_position)
            elif self.current_position > self.move_range[1]:
                self.current_position = self.move_range[0] + (self.current_position - self.move_range[1])
    
    def calculate_rgb(self, palette_name: str = "A") -> List[List[int]]:
        """Calculate RGB color values from the color indices"""
        from config import DEFAULT_COLOR_PALETTES
        
        palette = DEFAULT_COLOR_PALETTES.get(palette_name, DEFAULT_COLOR_PALETTES["A"])
        
        rgb_values = []
        for color_idx in self.color:
            try:
                if isinstance(color_idx, int) and 0 <= color_idx < len(palette):
                    rgb_values.append(palette[color_idx])
                else:
                    rgb_values.append([255, 0, 0]) 
            except Exception as e:
                print(f"Error getting color {color_idx} from palette: {e}")
                rgb_values.append([255, 0, 0])  
        
        return rgb_values

    def apply_dimming(self) -> float:
        """
        Calculate the brightness factor based on dimmer_time settings.
        
        Returns:
            Brightness factor (0.0-1.0)
        """

        if not self.fade or not self.dimmer_time or len(self.dimmer_time) < 5 or self.dimmer_time[4] == 0:
            return 1.0 
            
        cycle_time = self.dimmer_time[4]
        current_time = int((self.time * 1000) % cycle_time)
        
        fade_in_start = self.dimmer_time[0]
        fade_in_end = self.dimmer_time[1]
        fade_out_start = self.dimmer_time[2]
        fade_out_end = self.dimmer_time[3]

        if current_time < fade_in_start:
            return 0.0
        elif current_time < fade_in_end:
            return (current_time - fade_in_start) / max(1, fade_in_end - fade_in_start)
        elif current_time < fade_out_start:
            return 1.0
        elif current_time < fade_out_end:
            return 1.0 - (current_time - fade_out_start) / max(1, fade_out_end - fade_out_start)
        else:
            return 0.0

    def get_light_data(self, palette_name: str = "A") -> dict:
        """Get the light data (colors, positions, transparency) for this segment"""
        brightness = self.apply_dimming() if self.fade else 1.0
        

        segment_start = int(self.current_position - self.total_length / 2)
        positions = [
            segment_start,                          
            segment_start + self.length[0],           
            segment_start + self.length[0] + self.length[1],  
            segment_start + self.total_length        
        ]

        colors = self.calculate_rgb(palette_name)
        
        light_data = {
            'segment_id': self.segment_ID,
            'brightness': brightness,
            'positions': positions,
            'colors': colors,
            'transparency': self.transparency
        }
        
        return light_data