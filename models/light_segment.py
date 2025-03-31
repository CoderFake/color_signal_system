from typing import List, Any, Dict
import sys
import math
sys.path.append('..')
from utils.color_utils import interpolate_colors

class LightSegment:
    """
    LightSegment represents a segment of light with specific properties like color, position, and movement.
    """

    def __init__(self, segment_ID: int, color: List[int], transparency: List[float], 
                length: List[int], move_speed: float, move_range: List[int], 
                initial_position: int, is_edge_reflect: bool, dimmer_time: List[int]):
        """
        Initialize a LightSegment instance.
        
        Args:
            segment_ID: Unique identifier for this segment
            color: List of color indices from the palette
            transparency: Transparency values for each color point
            length: Lengths of each segment section
            move_speed: Speed of movement in LED particles per second
            move_range: Range of movement [left_edge, right_edge]
            initial_position: Initial position of the segment
            is_edge_reflect: Whether to reflect at edges or wrap around
            dimmer_time: Fade timing parameters [fade_in_start, fade_in_end, fade_out_start, fade_out_end, cycle_time]
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
        

        self.gradient = False
        self.fade = False
        self.gradient_colors = [0, -1, -1]  # On/Off flag, left color, right color
        
        self.rgb_color = self.calculate_rgb()
        self.total_length = sum(self.length)

    def update_param(self, param_name: str, value: Any):
        """
        Update a specific parameter of the segment.
        
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
        Update the position of the segment based on move_speed and fps.
        
        Args:
            fps: Frames per second
        """
        dt = 1.0 / fps
        
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
        """
        Calculate RGB color values from color palette indices.
        
        Args:
            palette_name: Name of the palette to use
            
        Returns:
            List of RGB values corresponding to each color index
        """
        from config import DEFAULT_COLOR_PALETTES
        
        palette = DEFAULT_COLOR_PALETTES.get(palette_name, DEFAULT_COLOR_PALETTES["A"])
        
        rgb_values = []
        for i, color_idx in enumerate(self.color):
            try:
                if isinstance(color_idx, int) and 0 <= color_idx < len(palette):
                    rgb_values.append(palette[color_idx])
                else:
                    rgb_values.append([255, 0, 0])  # Default to red for invalid indices
            except Exception as e:
                print(f"Error getting color {color_idx} from palette: {e}")
                rgb_values.append([255, 0, 0])
        

        while len(rgb_values) < 4:
            if rgb_values:
                rgb_values.append(rgb_values[-1])
            else:
                rgb_values.append([255, 0, 0])
        
        return rgb_values

    def apply_dimming(self, current_time: float = 0.0) -> float:
        """
        Apply fade effect based on dimmer_time parameters.
        
        Args:
            current_time: Current time value (in seconds)
            
        Returns:
            Brightness level from 0.0 to 1.0
        """
        if not self.fade or not self.dimmer_time or len(self.dimmer_time) < 5 or self.dimmer_time[4] == 0:
            return 1.0  # Full brightness if fade is disabled
            
        cycle_time = self.dimmer_time[4]

        current_time_ms = int((current_time * 1000) % cycle_time)
        fade_in_start = self.dimmer_time[0]
        fade_in_end = self.dimmer_time[1]
        fade_out_start = self.dimmer_time[2]
        fade_out_end = self.dimmer_time[3]

        if current_time_ms < fade_in_start:
            return 0.0
        elif current_time_ms < fade_in_end:
            progress = (current_time_ms - fade_in_start) / max(1, fade_in_end - fade_in_start)
            return progress * progress  # Use quadratic easing for smoother fade
        elif current_time_ms < fade_out_start:
            return 1.0
        elif current_time_ms < fade_out_end:
            progress = (current_time_ms - fade_out_start) / max(1, fade_out_end - fade_out_start)
            return 1.0 - (progress * progress)  # Quadratic easing for fade out
        else:
            return 0.0

    def get_light_data(self, palette_name: str = "A", current_time: float = 0.0) -> dict:
        """
        Get data for light rendering based on current segment state.
        
        Args:
            palette_name: Name of the palette to use
            current_time: Current time value (in seconds)
            
        Returns:
            Dictionary with segment rendering information
        """
        brightness = self.apply_dimming(current_time) if hasattr(self, 'fade') and self.fade else 1.0
        
        segment_start = int(self.current_position - self.total_length / 2)
        positions = [
            segment_start,                          # Left edge
            segment_start + self.length[0],         # First transition
            segment_start + self.length[0] + self.length[1],  # Second transition
            segment_start + self.total_length       # Right edge
        ]

        colors = self.calculate_rgb(palette_name)
        

        if hasattr(self, 'gradient') and self.gradient and hasattr(self, 'gradient_colors'):
            if self.gradient_colors[0] == 1:  # If gradient is on
                from config import DEFAULT_COLOR_PALETTES
                palette = DEFAULT_COLOR_PALETTES.get(palette_name, DEFAULT_COLOR_PALETTES["A"])
                

                left_idx = self.gradient_colors[1]
                right_idx = self.gradient_colors[2]
                
                if 0 <= left_idx < len(palette) and 0 <= right_idx < len(palette):
                    left_color = palette[left_idx]
                    right_color = palette[right_idx]
                    

                    colors[0] = left_color
                    colors[3] = right_color
                    colors[1] = interpolate_colors(left_color, right_color, 0.33)
                    colors[2] = interpolate_colors(left_color, right_color, 0.67)
        
        light_data = {
            'segment_id': self.segment_ID,
            'brightness': brightness,
            'positions': positions,
            'colors': colors,
            'transparency': self.transparency,
            'gradient': getattr(self, 'gradient', False),
            'fade': getattr(self, 'fade', False)
        }
        
        return light_data
        
    def to_dict(self) -> Dict:
        """
        Convert the segment to a dictionary representation.
        
        Returns:
            Dictionary containing segment properties
        """
        data = {
            "segment_ID": self.segment_ID,
            "color": self.color,
            "transparency": self.transparency,
            "length": self.length,
            "move_speed": self.move_speed,
            "move_range": self.move_range,
            "initial_position": self.initial_position,
            "current_position": self.current_position,
            "is_edge_reflect": self.is_edge_reflect,
            "dimmer_time": self.dimmer_time
        }
        

        if hasattr(self, "gradient"):
            data["gradient"] = self.gradient
        if hasattr(self, "fade"):
            data["fade"] = self.fade
        if hasattr(self, "gradient_colors"):
            data["gradient_colors"] = self.gradient_colors
            
        return data
        
    @classmethod
    def from_dict(cls, data: Dict):
        """
        Create a segment from a dictionary representation.
        
        Args:
            data: Dictionary containing segment properties
            
        Returns:
            A new LightSegment instance
        """
        segment = cls(
            segment_ID=data["segment_ID"],
            color=data["color"],
            transparency=data["transparency"],
            length=data["length"],
            move_speed=data["move_speed"],
            move_range=data["move_range"],
            initial_position=data["initial_position"],
            is_edge_reflect=data["is_edge_reflect"],
            dimmer_time=data["dimmer_time"]
        )
        

        if "current_position" in data:
            segment.current_position = data["current_position"]
            

        if "gradient" in data:
            segment.gradient = data["gradient"]
        if "fade" in data:
            segment.fade = data["fade"]
        if "gradient_colors" in data:
            segment.gradient_colors = data["gradient_colors"]
            
        return segment