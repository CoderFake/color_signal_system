from typing import Dict, List, Any, Tuple, Optional
from .light_segment import LightSegment

class LightEffect:
    def __init__(self, effect_ID: int, led_count: int, fps: int):
        self.effect_ID = effect_ID
        self.segments = {}
        self.led_count = led_count
        self.fps = fps
        self.time_step = 1.0 / fps
    
    def add_segment(self, segment_ID: int, segment: LightSegment):
        self.segments[segment_ID] = segment
    
    def remove_segment(self, segment_ID: int) -> bool:
        if segment_ID in self.segments:
            del self.segments[segment_ID]
            return True
        return False
    
    def update_segment_param(self, segment_ID: int, param_name: str, value: Any):
        if segment_ID in self.segments:
            self.segments[segment_ID].update_param(param_name, value)
    
    def update_all(self):
        for segment in self.segments.values():
            segment.update_position(self.fps)
    
    def get_led_output(self) -> List[List[int]]:
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
        return list(self.segments.keys())
    
    def get_segment(self, segment_ID: int) -> Optional[LightSegment]:
        return self.segments.get(segment_ID)
    
    def clear(self):
        self.segments.clear()