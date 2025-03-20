from typing import Dict, List, Any, Tuple
from .light_segment import LightSegment

class LightEffect:
    """
    Class to manage multiple LightSegments to create a complete lighting effect
    """
    
    def __init__(self, effect_ID: int, led_count: int, fps: int):
        """
        Initialize a LightEffect instance
        
        Args:
            effect_ID: Unique ID for the effect
            led_count: Total number of LEDs
            fps: Frame rate for updates
        """
        self.effect_ID = effect_ID
        self.segments = {}
        self.led_count = led_count
        self.fps = fps
        self.time_step = 1.0 / fps
    
    def add_segment(self, segment_ID: int, segment: LightSegment):
        """
        Add a light segment to the effect
        
        Args:
            segment_ID: Unique ID for the segment
            segment: LightSegment instance to add
        """
        self.segments[segment_ID] = segment
    
    def remove_segment(self, segment_ID: int) -> bool:
        """
        Remove a segment from the effect
        
        Args:
            segment_ID: ID of the segment to remove
            
        Returns:
            True if segment was found and removed, False otherwise
        """
        if segment_ID in self.segments:
            del self.segments[segment_ID]
            return True
        return False
    
    def update_segment_param(self, segment_ID: int, param_name: str, value: Any):
        """
        Update a parameter of a specific LightSegment
        
        Args:
            segment_ID: ID of the segment to update
            param_name: Name of the parameter to update
            value: New value for the parameter
        """
        if segment_ID in self.segments:
            self.segments[segment_ID].update_param(param_name, value)
    
    def update_all(self):
        """
        Update all segments for the current frame
        """
        for segment in self.segments.values():
            segment.update_position(self.fps)
    
    def get_led_output(self) -> List[List[int]]:
        """
        Get the final color data for all LEDs after combining all segments
        
        Returns:
            List of RGB values [r, g, b] for each LED
        """
        led_colors = [[0, 0, 0] for _ in range(self.led_count)]
        led_transparency = [1.0 for _ in range(self.led_count)]
        
        for segment in self.segments.values():
            segment_data = segment.get_light_data()
            
            for led_pos, (rgb, transparency) in segment_data.items():
                if 0 <= led_pos < self.led_count:
                    if transparency <= 0.0:
                        continue
                    
                    current_trans = led_transparency[led_pos]
                    
                    if current_trans >= 1.0:
                        led_colors[led_pos] = rgb.copy()
                        led_transparency[led_pos] = transparency
                    else:
                        blend_factor = transparency * (1.0 - current_trans)
                        total_factor = current_trans + blend_factor
                        
                        if total_factor > 0:
                            current_weight = current_trans / total_factor
                            new_weight = blend_factor / total_factor

                            led_colors[led_pos] = [
                                int(led_colors[led_pos][0] * current_weight + rgb[0] * new_weight),
                                int(led_colors[led_pos][1] * current_weight + rgb[1] * new_weight),
                                int(led_colors[led_pos][2] * current_weight + rgb[2] * new_weight)
                            ]
                            
                            led_transparency[led_pos] = 1.0 - (1.0 - current_trans) * (1.0 - transparency)
        
        return led_colors
    
    def get_segment_ids(self) -> List[int]:
        """
        Get list of all segment IDs in this effect
        
        Returns:
            List of segment IDs
        """
        return list(self.segments.keys())
    
    def get_segment(self, segment_ID: int) -> LightSegment:
        """
        Get a specific segment by ID
        
        Args:
            segment_ID: ID of the segment to retrieve
            
        Returns:
            The requested LightSegment or None if not found
        """
        return self.segments.get(segment_ID)
    
    def clear(self):
        """
        Remove all segments from the effect
        """
        self.segments.clear()