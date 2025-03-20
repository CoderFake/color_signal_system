import numpy as np
import time
from typing import List, Dict, Tuple, Any, Optional

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
        self.time = 0
        self.direction = 1 if move_speed >= 0 else -1
        self.rgb_color = self.calculate_rgb()
        self.creation_time = time.time()
        
        self.control_points_offsets = [0]
        for i in range(len(length)):
            self.control_points_offsets.append(self.control_points_offsets[-1] + length[i])
        self.total_length = sum(length)

    def update_param(self, param_name: str, value: Any):
        if param_name == 'color':
            setattr(self, param_name, value)
            self.rgb_color = self.calculate_rgb()
        elif param_name == 'move_speed':
            if (value > 0 and self.move_speed < 0) or (value < 0 and self.move_speed > 0):
                self.direction *= -1
            setattr(self, param_name, value)
        elif param_name == 'length':
            setattr(self, param_name, value)
            self.control_points_offsets = [0]
            for i in range(len(value)):
                self.control_points_offsets.append(self.control_points_offsets[-1] + value[i])
            self.total_length = sum(value)
        else:
            setattr(self, param_name, value)

    def update_position(self, fps: int):
        dt = 1.0 / fps
        self.time += dt
        
        delta = self.move_speed * dt
        new_position = self.current_position + delta
        
        if self.is_edge_reflect:
            if new_position < self.move_range[0]:
                overshoot = self.move_range[0] - new_position
                new_position = self.move_range[0] + overshoot
                self.move_speed = abs(self.move_speed)
                self.direction = 1
            elif new_position > self.move_range[1]:
                overshoot = new_position - self.move_range[1]
                new_position = self.move_range[1] - overshoot
                self.move_speed = -abs(self.move_speed)
                self.direction = -1
        else:
            if new_position < self.move_range[0]:
                new_position = self.move_range[1] - ((self.move_range[0] - new_position) % 
                                                   (self.move_range[1] - self.move_range[0] + 1))
            elif new_position > self.move_range[1]:
                new_position = self.move_range[0] + ((new_position - self.move_range[1]) % 
                                                   (self.move_range[1] - self.move_range[0] + 1))
                
        self.current_position = new_position

    def calculate_rgb(self) -> List[List[int]]:
        COLOR_MAP = {
            0: [0, 0, 0],       # Black
            1: [255, 0, 0],     # Red
            2: [0, 255, 0],     # Green
            3: [0, 0, 255],     # Blue
            4: [255, 255, 0],   # Yellow
            5: [255, 0, 255],   # Magenta
            6: [0, 255, 255],   # Cyan
            7: [255, 255, 255], # White
            8: [255, 127, 0],   # Orange
            9: [127, 0, 255],   # Purple
            10: [0, 127, 255],  # Light blue
        }
        
        return [COLOR_MAP.get(color_id, [0, 0, 0]) for color_id in self.color]

    def apply_dimming(self, elapsed_time: float) -> float:
        if len(self.dimmer_time) != 5:
            return 1.0
            
        start_fade_in, end_fade_in, start_fade_out, end_fade_out, cycle_time = self.dimmer_time
        
        if cycle_time <= 0:
            return 1.0
            
        t = (elapsed_time % (cycle_time / 1000)) * 1000
        
        if t < start_fade_in:
            return 0.0
        elif start_fade_in <= t < end_fade_in:
            return (t - start_fade_in) / (end_fade_in - start_fade_in)
        elif end_fade_in <= t < start_fade_out:
            return 1.0
        elif start_fade_out <= t < end_fade_out:
            return 1.0 - (t - start_fade_out) / (end_fade_out - start_fade_out)
        else:
            return 0.0

    def get_light_data(self) -> Dict[int, Tuple[List[int], float]]:
        elapsed_time = time.time() - self.creation_time
        dimming_factor = self.apply_dimming(elapsed_time)
        
        result = {}
        
        control_positions = []
        for offset in self.control_points_offsets:
            control_positions.append(int(self.current_position + offset * self.direction))
        
        start_pos = min(control_positions)
        end_pos = max(control_positions)
        
        for led_pos in range(start_pos, end_pos + 1):
            if self.move_range[0] <= led_pos <= self.move_range[1]:
                segment_idx = -1
                for i in range(len(control_positions) - 1):
                    if ((control_positions[i] <= led_pos <= control_positions[i+1]) or 
                        (control_positions[i+1] <= led_pos <= control_positions[i])):
                        segment_idx = i
                        break
                
                if segment_idx != -1:
                    start = control_positions[segment_idx]
                    end = control_positions[segment_idx + 1]
                    
                    if start == end:
                        t = 0
                    else:
                        t = abs((led_pos - start) / (end - start))
                    
                    color1 = self.rgb_color[segment_idx]
                    color2 = self.rgb_color[segment_idx + 1]
                    
                    rgb = [
                        int(color1[0] * (1 - t) + color2[0] * t),
                        int(color1[1] * (1 - t) + color2[1] * t),
                        int(color1[2] * (1 - t) + color2[2] * t)
                    ]
                    
                    transparency = self.transparency[segment_idx] * (1 - t) + self.transparency[segment_idx + 1] * t
                    transparency = max(0.0, min(1.0, transparency * dimming_factor))
                    
                    result[led_pos] = (rgb, transparency)
        
        return result