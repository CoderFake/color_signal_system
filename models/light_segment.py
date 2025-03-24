from typing import List, Any, Union
import numpy as np
import sys
sys.path.append('..')
from utils.color_utils import interpolate_colors

class LightSegment:
    """
    A class representing a segment of light with color, position, and movement properties.
    Each LightSegment can move, change color, and apply dimming effects.
    """
    
    def __init__(self, segment_ID: int, color: List[int], transparency: List[float], 
                 length: List[int], move_speed: float, move_range: List[int], 
                 initial_position: int, is_edge_reflect: bool, dimmer_time: List[int]):
        """
        Initialize a LightSegment with the specified parameters.
        
        Args:
            segment_ID: Unique identifier for this segment
            color: List of color indices (4 elements: edge_left, inner_left, inner_right, edge_right)
            transparency: Transparency values for each color point (0.0-1.0)
            length: Length of segment sections (3 elements)
            move_speed: Number of LED positions to move per second (positive: right, negative: left)
            move_range: Range of movement [left_edge, right_edge]
            initial_position: Initial position of the segment
            is_edge_reflect: Whether to reflect at the edges or wrap around
            dimmer_time: Controls fading [fade_in_start, fade_in_end, fade_out_start, fade_out_end, cycle_length]
        """
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
        self.rgb_color = self.calculate_rgb()
        self.total_length = sum(self.length)
        

        self.interval = 10
        

        self.gradient_enabled = False
        self.gradient_colors = [-1, -1]  
        

        self.span_width = 100
        self.span_range = [50, 150]
        self.span_speed = 100
        self.span_interval = 10
        self.fade_enabled = False
        self.span_gradient_enabled = False
        self.span_gradient_colors = [-1, -1, -1, -1, -1, -1]  
        
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
    
    def calculate_rgb(self) -> List[List[int]]:
        """
        Calculate RGB color values from the color indices.
        In a real implementation, this would look up colors from a palette.
        
        Returns:
            List of RGB color values [[r0, g0, b0], ..., [r3, g3, b3]]
        """


        color_map = {
            0: [0, 0, 0],        # Black
            1: [255, 0, 0],      # Red
            2: [0, 255, 0],      # Green
            3: [0, 0, 255],      # Blue
            4: [255, 255, 0],    # Yellow
            5: [0, 255, 255],    # Cyan
            6: [255, 0, 255],    # Magenta
            7: [255, 255, 255]   # White
        }
        
        rgb_values = []
        for color_idx in self.color:
            if color_idx >= 0 and color_idx in color_map: 
                rgb_values.append(color_map[color_idx])
            else:
                rgb_values.append([0, 0, 0])
                
        return rgb_values
    
    def apply_dimming(self) -> float:
        """
        Calculate the brightness factor based on dimmer_time settings.
        
        Returns:
            Brightness factor (0.0-1.0)
        """
        if not self.dimmer_time or self.dimmer_time[4] == 0:
            return 1.0 
            

        cycle_time = self.dimmer_time[4]
        current_time = (self.time * 1000) % cycle_time
        
        fade_in_start = self.dimmer_time[0]
        fade_in_end = self.dimmer_time[1]
        fade_out_start = self.dimmer_time[2]
        fade_out_end = self.dimmer_time[3]
        

        if current_time <= fade_in_start:
            return 0.0
        elif current_time <= fade_in_end:
            return (current_time - fade_in_start) / (fade_in_end - fade_in_start)
        elif current_time <= fade_out_start:
            return 1.0
        elif current_time <= fade_out_end:
            return 1.0 - (current_time - fade_out_start) / (fade_out_end - fade_out_start)
        else:
            return 0.0
    
    def get_light_data(self) -> dict:
        """
        Get the light data (colors, positions, transparency) for this segment.
        
        Returns:
            Dictionary containing the light data for the LED strip
        """
        brightness = self.apply_dimming()
        segment_start = int(self.current_position - self.total_length / 2)
        

        positions = [
            segment_start,
            segment_start + self.length[0],
            segment_start + self.length[0] + self.length[1],
            segment_start + self.total_length
        ]
        

        colors = self.rgb_color
        if self.gradient_enabled and hasattr(self, 'gradient_colors') and len(self.gradient_colors) >= 2:
            if self.gradient_colors[0] >= 0 and self.gradient_colors[1] >= 0:
                pass  

        light_data = {
            'segment_id': self.segment_ID,
            'brightness': brightness,
            'positions': positions,
            'colors': colors,
            'transparency': self.transparency,
            'gradient_enabled': getattr(self, 'gradient_enabled', False),
            'gradient_colors': getattr(self, 'gradient_colors', [-1, -1]),
            'span_width': getattr(self, 'span_width', 100),
            'span_range': getattr(self, 'span_range', [50, 150]),
            'span_speed': getattr(self, 'span_speed', 100),
            'span_interval': getattr(self, 'span_interval', 10),
            'fade_enabled': getattr(self, 'fade_enabled', False),
            'span_gradient_enabled': getattr(self, 'span_gradient_enabled', False),
            'span_gradient_colors': getattr(self, 'span_gradient_colors', [-1, -1, -1, -1, -1, -1])
        }
        
        return light_data