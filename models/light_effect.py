from typing import Dict, List, Any, Tuple
import numpy as np
import sys
sys.path.append('..')
from models.light_segment import LightSegment

class LightEffect:
    """
    A class that manages multiple LightSegment instances to create composite lighting effects.
    Handles the positioning, blending, and timing of multiple light segments.
    """
    
    def __init__(self, effect_ID: int, led_count: int, fps: int):
        """
        Initialize a LightEffect instance.
        
        Args:
            effect_ID: Unique identifier for this effect
            led_count: Total number of LEDs to control
            fps: Frames per second for animation
        """
        self.effect_ID = effect_ID
        self.segments: Dict[int, LightSegment] = {}
        self.led_count = led_count
        self.fps = fps
        self.time_step = 1.0 / fps
        self.current_palette = "A"
        
    def add_segment(self, segment_ID: int, segment: LightSegment):
        """
        Add a LightSegment to this effect.
        
        Args:
            segment_ID: Unique identifier for the segment
            segment: LightSegment instance to add
        """
        self.segments[segment_ID] = segment
        
    def remove_segment(self, segment_ID: int):
        """
        Remove a LightSegment from this effect.
        
        Args:
            segment_ID: ID of the segment to remove
        """
        if segment_ID in self.segments:
            del self.segments[segment_ID]
    
    def update_segment_param(self, segment_ID: int, param_name: str, value: Any):
        """
        Update a parameter of a specific LightSegment.
        
        Args:
            segment_ID: ID of the segment to update
            param_name: Name of the parameter to update
            value: New value for the parameter
        """
        if segment_ID in self.segments:
            self.segments[segment_ID].update_param(param_name, value)
    
    def update_all(self):
        """
        Update all segments, advancing their positions and states.
        """
        for segment in self.segments.values():
            segment.update_position(self.fps)

    def get_led_output(self) -> List[List[int]]:
        """
        Calculate the final color values for all LEDs based on all active segments.
        Xử lý tổng hợp segment_data (xem xét độ mờ)
        """

        led_colors = [[0, 0, 0] for _ in range(self.led_count)]
        led_transparency = [1.0 for _ in range(self.led_count)]

        sorted_segments = sorted(self.segments.items(), key=lambda x: x[0])
        
        for segment_id, segment in sorted_segments:
            segment_data = segment.get_light_data(self.current_palette)

            if segment_data['brightness'] <= 0:
                continue
                
            positions = segment_data['positions']
            colors = segment_data['colors']
            transparency = segment_data['transparency']
            brightness = segment_data['brightness']
            
            start_pos = max(0, int(positions[0]))
            end_pos = min(self.led_count - 1, int(positions[3]))
            
            for led_idx in range(start_pos, end_pos + 1):
                if led_idx < 0 or led_idx >= self.led_count:
                    continue

                if led_idx <= positions[1]:

                    rel_pos = (led_idx - positions[0]) / max(1, positions[1] - positions[0])
                    trans_idx = 0
                    color1 = colors[0]
                    color2 = colors[1]
                    
                elif led_idx <= positions[2]:

                    rel_pos = (led_idx - positions[1]) / max(1, positions[2] - positions[1])
                    trans_idx = 1
                    color1 = colors[1]
                    color2 = colors[2]
                    
                else:

                    rel_pos = (led_idx - positions[2]) / max(1, positions[3] - positions[2])
                    trans_idx = 2
                    color1 = colors[2]
                    color2 = colors[3]

                from utils.color_utils import interpolate_colors
                led_color = interpolate_colors(color1, color2, rel_pos)
                
                from utils.color_utils import apply_brightness
                led_color = apply_brightness(led_color, brightness)
                
                current_transparency = transparency[trans_idx]
                
                if led_colors[led_idx] == [0, 0, 0]:

                    led_colors[led_idx] = led_color
                    led_transparency[led_idx] = current_transparency
                else:

                    from utils.color_utils import blend_colors, apply_transparency

                    weight_current = led_transparency[led_idx]
                    weight_new = current_transparency * (1.0 - led_transparency[led_idx])

                    led_colors[led_idx] = blend_colors(
                        [led_colors[led_idx], led_color],
                        [weight_current, weight_new]
                    )

                    led_transparency[led_idx] = max(0.0, min(1.0, 
                        led_transparency[led_idx] + current_transparency * (1.0 - led_transparency[led_idx])
                    ))
        
        return led_colors

    def _interpolate_color(self, color1: List[int], color2: List[int], factor: float) -> List[int]:
        """
        Interpolate between two colors for gradient effects.
        
        Args:
            color1: First RGB color [r, g, b]
            color2: Second RGB color [r, g, b]
            factor: Interpolation factor (0.0-1.0)
        
        Returns:
            Interpolated RGB color [r, g, b]
        """
        r = int(color1[0] + (color2[0] - color1[0]) * factor)
        g = int(color1[1] + (color2[1] - color1[1]) * factor)
        b = int(color1[2] + (color2[2] - color1[2]) * factor)
        return [max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))]
    
    def _apply_transparency(self, base_color: List[int], overlay_color: List[int], 
                          transparency: float) -> List[int]:
        """
        Apply a transparent overlay color to a base color.
        
        Args:
            base_color: Base color [r, g, b]
            overlay_color: Overlay color [r, g, b]
            transparency: Transparency factor (0.0-1.0)
        
        Returns:
            Resulting color [r, g, b]
        """
        return self._interpolate_color(base_color, overlay_color, transparency)
    
    def _apply_brightness(self, color: List[int], brightness: float) -> List[int]:
        """
        Apply brightness to a color.
        
        Args:
            color: Color [r, g, b]
            brightness: Brightness factor (0.0-1.0)
        
        Returns:
            Adjusted color [r, g, b]
        """
        r = int(color[0] * brightness)
        g = int(color[1] * brightness)
        b = int(color[2] * brightness)
        return [max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))]