import threading
import time
from typing import List, Dict, Any, Callable, Optional

class AutoEffectCycler:
    """
    Class to automatically cycle through different effects/presets
    """
    
    def __init__(self, preset_names: List[str], apply_callback: Callable[[str], None], 
                 interval_sec: float = 5.0):
        """
        Initialize the auto cycler
        
        Args:
            preset_names: List of preset names to cycle through
            apply_callback: Function to call when applying a preset (takes preset name)
            interval_sec: Interval between effect changes in seconds
        """
        self.preset_names = preset_names
        self.apply_callback = apply_callback
        self.interval_sec = interval_sec
        self.running = False
        self.current_index = 0
        self.thread = None
    
    def start(self):
        """
        Start cycling effects
        """
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._cycle_thread)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """
        Stop cycling effects
        """
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None
    
    def set_interval(self, interval_sec: float):
        """
        Set the cycling interval
        
        Args:
            interval_sec: New interval in seconds
        """
        self.interval_sec = max(0.5, interval_sec)  
    
    def get_current_preset(self) -> Optional[str]:
        """
        Get the current preset name
        
        Returns:
            Current preset name or None if no presets
        """
        if not self.preset_names:
            return None
        return self.preset_names[self.current_index]
    
    def skip_to_next(self):
        """
        Skip to the next preset immediately
        """
        if not self.preset_names:
            return
            
        self.current_index = (self.current_index + 1) % len(self.preset_names)
        self.apply_callback(self.preset_names[self.current_index])
    
    def _cycle_thread(self):
        """
        Thread function to cycle through effects
        """
        while self.running and self.preset_names:
            self.apply_callback(self.preset_names[self.current_index])
            
            sleep_time = 0
            while sleep_time < self.interval_sec and self.running:
                time.sleep(0.1)
                sleep_time += 0.1

            if self.running:
                self.current_index = (self.current_index + 1) % len(self.preset_names)
        
        self.running = False