from typing import Dict, List, Any, Optional
import json
import sys
sys.path.append('..')
from models.light_effect import LightEffect
from config import DEFAULT_COLOR_PALETTES

class LightScene:
    """
    LightScene manages multiple LightEffect instances and shares color palettes among them.
    It provides functionality for switching between effects and updating palette settings.
    """
    
    def __init__(self, scene_ID: int):
        """
        Initialize a LightScene instance.
        
        Args:
            scene_ID: Unique identifier for this scene
        """
        self.scene_ID = scene_ID
        self.effects: Dict[int, LightEffect] = {}
        self.current_effect_ID = None
        self.palettes = DEFAULT_COLOR_PALETTES.copy()
        self.current_palette = "A"  # Default palette
    
    def add_effect(self, effect_ID: int, effect: LightEffect):
        """
        Add a LightEffect to the scene.
        
        Args:
            effect_ID: Unique identifier for the effect
            effect: LightEffect instance to add
        """
        self.effects[effect_ID] = effect
        effect.current_palette = self.current_palette
        
        if self.current_effect_ID is None:
            self.current_effect_ID = effect_ID
    
    def remove_effect(self, effect_ID: int):
        """
        Remove a LightEffect from the scene.
        
        Args:
            effect_ID: ID of the effect to remove
        """
        if effect_ID in self.effects:
            del self.effects[effect_ID]
            

            if effect_ID == self.current_effect_ID:
                if self.effects:
                    self.current_effect_ID = next(iter(self.effects.keys()))
                else:
                    self.current_effect_ID = None
    
    def set_palette(self, palette_id: str):
        """
        Change the current color palette for all effects.
        
        Args:
            palette_id: ID of the palette to use
        """
        if palette_id in self.palettes:
            self.current_palette = palette_id

            for effect in self.effects.values():
                effect.current_palette = palette_id
    
    def update_palette(self, palette_id: str, colors: List[List[int]]):
        """
        Update a specific palette's colors.
        
        Args:
            palette_id: ID of the palette to update
            colors: New color values
        """
        if palette_id in self.palettes:
            self.palettes[palette_id] = colors

            if palette_id == self.current_palette:
                self.set_palette(palette_id)
    
    def switch_effect(self, effect_ID: int):
        """
        Switch to a different LightEffect.
        
        Args:
            effect_ID: ID of the effect to switch to
        """
        if effect_ID in self.effects:
            self.current_effect_ID = effect_ID
    
    def update(self):
        """
        Update the current LightEffect.
        """
        if self.current_effect_ID is not None and self.current_effect_ID in self.effects:
            self.effects[self.current_effect_ID].update_all()
    
    def get_led_output(self):
        """
        Get the LED output from the current effect.
        
        Returns:
            List of RGB color values for each LED
        """
        if self.current_effect_ID is not None and self.current_effect_ID in self.effects:
            return self.effects[self.current_effect_ID].get_led_output()
        return []
    
    def save_to_json(self, file_path: str):
        """
        Save the complete scene configuration to a JSON file.
        
        Args:
            file_path: Path to save the JSON file
        """
        data = {
            "scene_ID": self.scene_ID,
            "current_effect_ID": self.current_effect_ID,
            "current_palette": self.current_palette,
            "palettes": self.palettes,
            "effects": {}
        }
        
        for effect_id, effect in self.effects.items():
            effect_data = {
                "effect_ID": effect.effect_ID,
                "led_count": effect.led_count,
                "fps": effect.fps,
                "segments": {}
            }
            
            for segment_id, segment in effect.segments.items():
                effect_data["segments"][segment_id] = {
                    "segment_ID": segment.segment_ID,
                    "color": segment.color,
                    "transparency": segment.transparency,
                    "length": segment.length,
                    "move_speed": segment.move_speed,
                    "move_range": segment.move_range,
                    "initial_position": segment.initial_position,
                    "current_position": segment.current_position,
                    "is_edge_reflect": segment.is_edge_reflect,
                    "dimmer_time": segment.dimmer_time
                }
                

                if hasattr(segment, "gradient"):
                    effect_data["segments"][segment_id]["gradient"] = segment.gradient
                if hasattr(segment, "fade"):
                    effect_data["segments"][segment_id]["fade"] = segment.fade
                if hasattr(segment, "gradient_colors"):
                    effect_data["segments"][segment_id]["gradient_colors"] = segment.gradient_colors
            
            data["effects"][effect_id] = effect_data
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
    
    @classmethod
    def load_from_json(cls, file_path: str):
        """
        Load a scene configuration from a JSON file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            A new LightScene instance with the loaded configuration
        """
        from models.light_segment import LightSegment
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        scene = cls(scene_ID=data["scene_ID"])
        scene.current_palette = data.get("current_palette", "A")
        
        if "palettes" in data:
            scene.palettes = data["palettes"]
        
        for effect_id_str, effect_data in data["effects"].items():
            effect_id = int(effect_id_str)
            
            effect = LightEffect(
                effect_ID=effect_data["effect_ID"],
                led_count=effect_data["led_count"],
                fps=effect_data["fps"]
            )
            
            for segment_id_str, segment_data in effect_data["segments"].items():
                segment_id = int(segment_id_str)
                
                segment = LightSegment(
                    segment_ID=segment_data["segment_ID"],
                    color=segment_data["color"],
                    transparency=segment_data["transparency"],
                    length=segment_data["length"],
                    move_speed=segment_data["move_speed"],
                    move_range=segment_data["move_range"],
                    initial_position=segment_data["initial_position"],
                    is_edge_reflect=segment_data["is_edge_reflect"],
                    dimmer_time=segment_data["dimmer_time"]
                )
                

                if "current_position" in segment_data:
                    segment.current_position = segment_data["current_position"]
                

                if "gradient" in segment_data:
                    segment.gradient = segment_data["gradient"]
                if "fade" in segment_data:
                    segment.fade = segment_data["fade"]
                if "gradient_colors" in segment_data:
                    segment.gradient_colors = segment_data["gradient_colors"]
                
                effect.add_segment(segment_id, segment)
            
            scene.add_effect(effect_id, effect)
        

        if "current_effect_ID" in data and data["current_effect_ID"] is not None:
            scene.current_effect_ID = data["current_effect_ID"]
            
        return scene
    
    def save_palettes_to_json(self, file_path: str):
        """
        Save only color palettes to a JSON file.
        
        Args:
            file_path: Path to save the JSON file
        """
        data = {
            "palettes": self.palettes,
            "current_palette": self.current_palette
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
    
    def load_palettes_from_json(self, file_path: str):
        """
        Load color palettes from a JSON file.
        
        Args:
            file_path: Path to the JSON file
        """
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if "palettes" in data:
            self.palettes = data["palettes"]
        
        if "current_palette" in data:
            self.set_palette(data["current_palette"])