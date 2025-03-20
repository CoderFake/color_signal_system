"""
Effects Manager for LED Tape Light
Handles transitions and effect application
"""
from typing import Dict, List, Any, Tuple, Optional
import time
import threading

from core.light_effect import LightEffect
from core.light_segment import LightSegment
from utils.effect_presets import PRESET_EFFECTS, get_preset_names, get_preset_params
from utils.auto_cycler import AutoEffectCycler

class EffectsManager:
    """
    Class to manage effect transitions and application
    """
    
    def __init__(self):
        """
        Initialize the effects manager
        """
        self.effects: Dict[int, LightEffect] = {}
        self.current_effect_id = None
        self.auto_cycler = None
        self.last_update_time = time.time()
        self.transition_time = 1.0  
        self.osc_client = None
        self.osc_handler = None
        
        self.param_ranges = {
            "move_speed": (-100.0, 100.0),
            "transparency": (0.0, 1.0),
            "dimmer_time": (0, 5000),
            "color": (0, 10)
        }
    
    def add_effect(self, effect: LightEffect) -> None:
        """
        Add an effect to the manager
        
        Args:
            effect: LightEffect to add
        """
        self.effects[effect.effect_ID] = effect
        if self.current_effect_id is None:
            self.current_effect_id = effect.effect_ID
    
    def remove_effect(self, effect_id: int) -> bool:
        """
        Remove an effect from the manager
        
        Args:
            effect_id: ID of the effect to remove
            
        Returns:
            True if effect was removed, False otherwise
        """
        if effect_id in self.effects:
            del self.effects[effect_id]
            
            if effect_id == self.current_effect_id:
                if self.effects:
                    self.current_effect_id = list(self.effects.keys())[0]
                else:
                    self.current_effect_id = None
            
            return True
        return False
    
    def get_current_effect(self) -> Optional[LightEffect]:
        """
        Get the current active effect
        
        Returns:
            Current effect or None if no effects
        """
        if self.current_effect_id is None or self.current_effect_id not in self.effects:
            return None
        return self.effects[self.current_effect_id]
    
    def set_current_effect(self, effect_id: int) -> bool:
        """
        Set the current active effect
        
        Args:
            effect_id: ID of the effect to set as current
            
        Returns:
            True if effect was set, False if effect doesn't exist
        """
        if effect_id in self.effects:
            self.current_effect_id = effect_id
            return True
        return False
    
    def create_new_effect(self, effect_id: int, led_count: int, fps: int) -> LightEffect:
        """
        Create a new effect and add it to the manager
        
        Args:
            effect_id: ID for the new effect
            led_count: Number of LEDs in the effect
            fps: Frames per second for the effect
            
        Returns:
            The created effect
        """
        effect = LightEffect(effect_id, led_count, fps)
        self.add_effect(effect)
        return effect
    
    def add_segment_to_effect(self, effect_id: int, segment: LightSegment) -> bool:
        """
        Add a segment to an effect
        
        Args:
            effect_id: ID of the effect to add segment to
            segment: LightSegment to add
            
        Returns:
            True if successful, False otherwise
        """
        if effect_id in self.effects:
            self.effects[effect_id].add_segment(segment.segment_ID, segment)
            return True
        return False
    
    def create_default_segment(self, effect_id: int, segment_id: int) -> Optional[LightSegment]:
        """
        Create a default segment and add it to an effect
        
        Args:
            effect_id: ID of the effect to add segment to
            segment_id: ID for the new segment
            
        Returns:
            Created segment or None if effect doesn't exist
        """
        if effect_id not in self.effects:
            return None
            
        effect = self.effects[effect_id]
        segment = LightSegment(
            segment_ID=segment_id,
            color=[1, 3, 4, 2],
            transparency=[0.0, 0.0, 0.0, 0.0],
            length=[30, 30, 30],
            move_speed=20,
            move_range=[0, effect.led_count - 1],
            initial_position=0,
            is_edge_reflect=False,
            dimmer_time=[0, 500, 4500, 5000, 5000]
        )
        
        effect.add_segment(segment_id, segment)
        
        return segment
    
    def apply_preset(self, effect_id: int, segment_id: int, preset_name: str) -> bool:
        """
        Apply a preset to a segment
        
        Args:
            effect_id: ID of the effect containing the segment
            segment_id: ID of the segment to apply preset to
            preset_name: Name of preset to apply
            
        Returns:
            True if successful, False otherwise
        """
        if effect_id not in self.effects:
            return False
            
        effect = self.effects[effect_id]
        
        segment = None
        for sid, seg in effect.segments.items():
            if sid == segment_id:
                segment = seg
                break
                
        if segment is None:
            return False
            
        preset_params = get_preset_params(preset_name)
        if not preset_params:
            return False
            
        for param, value in preset_params.items():
            segment.update_param(param, value)
        
        if self.osc_client and self.osc_handler:
            for param, value in preset_params.items():
                address = f"/effect/{effect_id}/segment/{segment_id}/{param}"
                self.osc_handler.send_osc(self.osc_client, address, value)
        
        return True
    
    def start_auto_cycle(self, interval_sec: float = 5.0) -> None:
        """
        Start auto-cycling presets for current effect
        
        Args:
            interval_sec: Interval between changes in seconds
        """
        if self.auto_cycler:
            self.auto_cycler.stop()
            
        preset_names = get_preset_names()
        
        def apply_preset_callback(preset_name: str):
            effect = self.get_current_effect()
            if effect and effect.segments:
                segment_id = list(effect.segments.keys())[0]  
                self.apply_preset(self.current_effect_id, segment_id, preset_name)
        
        self.auto_cycler = AutoEffectCycler(preset_names, apply_preset_callback, interval_sec)
        self.auto_cycler.start()
    
    def stop_auto_cycle(self) -> None:
        """
        Stop auto-cycling presets
        """
        if self.auto_cycler:
            self.auto_cycler.stop()
            self.auto_cycler = None
    
    def set_auto_cycle_interval(self, interval_sec: float) -> None:
        """
        Set auto-cycle interval
        
        Args:
            interval_sec: New interval in seconds
        """
        if self.auto_cycler:
            self.auto_cycler.set_interval(interval_sec)
    
    def is_auto_cycling(self) -> bool:
        """
        Check if auto-cycling is active
        
        Returns:
            True if auto-cycling, False otherwise
        """
        return self.auto_cycler is not None and self.auto_cycler.running
    
    def get_available_presets(self) -> List[str]:
        """
        Get list of available preset names
        
        Returns:
            List of preset names
        """
        return get_preset_names()
    
    def update_all_effects(self) -> None:
        """
        Update all effects (usually called in main loop)
        """
        current_time = time.time()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time
        
        for effect in self.effects.values():
            effect.update_all()
    
    def set_transition_time(self, seconds: float) -> None:
        """
        Set transition time between effects
        
        Args:
            seconds: Transition time in seconds
        """
        self.transition_time = max(0.0, seconds)
    
    def get_transition_time(self) -> float:
        """
        Get current transition time
        
        Returns:
            Transition time in seconds
        """
        return self.transition_time
    
    def set_osc_client(self, client: Any) -> None:
        """
        Set OSC client for sending commands
        
        Args:
            client: OSC client instance
        """
        self.osc_client = client
    
    def set_osc_handler(self, handler: Any) -> None:
        """
        Set OSC handler for sending commands
        
        Args:
            handler: OSC handler instance
        """
        self.osc_handler = handler