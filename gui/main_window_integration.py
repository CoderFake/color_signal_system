import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import json
import threading
import time
from typing import Dict, List, Any, Optional

from ..core.light_effect import LightEffect
from ..core.light_segment import LightSegment
from ..core.effects_manager import EffectsManager
from ..utils.effect_presets import get_preset_names, get_preset_params
from ..utils.color_utils import get_color_by_id, get_color_hex, get_all_color_options, parse_color_option
from .custom_theme import COLORS, FONTS, METRICS, create_custom_button, create_section_label

class EffectsIntegration:
    """
    Integration for effects in the main window
    """
    
    def __init__(self, main_window):
        """
        Initialize effects integration
        
        Args:
            main_window: Main window instance
        """
        self.main_window = main_window
        self.effects_manager = EffectsManager()
        self.preset_names = get_preset_names()
    
    def initialize(self):
        """
        Initialize effects integration
        """
        self.effects_manager.osc_handler = self.main_window.osc_handler
        
        self._setup_event_handlers()
        
        self._initialize_default_effects()
    
    def _setup_event_handlers(self):
        """
        Set up event handlers for effects
        """
        self.main_window.preset_combo.configure(values=self.preset_names)
        self.main_window.preset_var.set(self.preset_names[0] if self.preset_names else "")
        
        self.main_window.auto_cycle_var.trace_add("write", self._on_auto_cycle_changed)
        self.main_window.cycle_interval_var.trace_add("write", self._on_cycle_interval_changed)
        
        if hasattr(self.main_window, 'set_osc_client'):
            self.main_window.set_osc_client = self._set_osc_client
    
    def _initialize_default_effects(self):
        """
        Initialize default effects
        """
        try:
            effect_id = int(self.main_window.effect_id_var.get())
            led_count = int(self.main_window.led_count_var.get())
            fps = int(self.main_window.fps_var.get())
        except ValueError:
            effect_id = 1
            led_count = 100
            fps = 30
        
        effect = LightEffect(effect_id, led_count, fps)
        self.effects_manager.add_effect(effect)

        segment_id = 1
        segment = LightSegment(
            segment_ID=segment_id,
            color=[1, 3, 4, 2],  
            transparency=[0.0, 0.0, 0.0, 0.0],
            length=[30, 30, 30],
            move_speed=20,
            move_range=[0, led_count - 1],
            initial_position=0,
            is_edge_reflect=False,
            dimmer_time=[0, 500, 4500, 5000, 5000]
        )
        effect.add_segment(segment_id, segment)
        
        if self.preset_names:
            self.apply_preset(effect_id, segment_id, self.preset_names[0])
    
    def _set_osc_client(self, client):
        """
        Set OSC client
        
        Args:
            client: OSC client
        """
        self.effects_manager.set_osc_client(client)
        self.effects_manager.osc_client = client
    
    def _on_auto_cycle_changed(self, *args):
        """
        Handle auto-cycle checkbox change
        """
        if self.main_window.auto_cycle_var.get() == "1":
            try:
                interval = float(self.main_window.cycle_interval_var.get())
                self.effects_manager.start_auto_cycle(interval)
                self.main_window.status_var.set("Auto-cycling presets started")
            except ValueError:
                self.main_window.auto_cycle_var.set("0")
                messagebox.showerror("Error", "Invalid cycle interval")
        else:
            self.effects_manager.stop_auto_cycle()
            self.main_window.status_var.set("Auto-cycling presets stopped")
    
    def _on_cycle_interval_changed(self, *args):
        """
        Handle cycle interval change
        """
        if self.effects_manager.is_auto_cycling():
            try:
                interval = float(self.main_window.cycle_interval_var.get())
                self.effects_manager.set_auto_cycle_interval(interval)
            except ValueError:
                pass
    
    def update_ui_from_segment(self, segment):
        """
        Update UI with segment parameters
        
        Args:
            segment: LightSegment instance
        """
        if hasattr(self.main_window, 'update_segment_ui'):
            self.main_window.update_segment_ui(segment)
    
    def apply_preset(self, effect_id, segment_id, preset_name):
        """
        Apply a preset to a segment
        
        Args:
            effect_id: Effect ID
            segment_id: Segment ID
            preset_name: Preset name
            
        Returns:
            True if successful, False otherwise
        """
        result = self.effects_manager.apply_preset(effect_id, segment_id, preset_name)
        
        if result:
            effect = self.effects_manager.get_current_effect()
            if effect and segment_id in effect.segments:
                self.update_ui_from_segment(effect.segments[segment_id])

            self.main_window.status_var.set(f"Applied preset '{preset_name}' to segment {segment_id}")
            
        return result
    
    def on_apply_preset(self):
        """
        Handle apply preset button click
        """
        preset_name = self.main_window.preset_var.get()
        if not preset_name:
            return
            
        try:
            effect_id = int(self.main_window.effect_id_var.get())
            segment_id = int(self.main_window.segment_id_var.get())
            
            self.apply_preset(effect_id, segment_id, preset_name)
            
        except ValueError:
            messagebox.showerror("Error", "Invalid effect or segment ID")
    
    def update_effects(self):
        """
        Update all effects (called in periodic updates)
        """
        self.effects_manager.update_all_effects()


class MainWindowExtension:
    """
    Extensions for the main window to better support effects
    """
    
    def __init__(self, main_window):
        """
        Initialize main window extensions
        
        Args:
            main_window: Main window instance
        """
        self.main_window = main_window
        self.effects_integration = EffectsIntegration(main_window)
    
    def setup(self):
        """
        Set up main window extensions
        """

        self.effects_integration.initialize()

        self.main_window.original_on_apply_preset = self.main_window.on_apply_preset
        self.main_window.on_apply_preset = self._extended_on_apply_preset

        self.main_window.get_color_preview = self._get_color_preview

        self.main_window.original_update_ui = self.main_window.update_ui
        self.main_window.update_ui = self._extended_update_ui
    
    def _extended_on_apply_preset(self):
        """
        Extended method for applying presets
        """
        self.effects_integration.on_apply_preset()

        if hasattr(self.main_window, 'original_on_apply_preset'):
            self.main_window.original_on_apply_preset()
    
    def _get_color_preview(self, color_id):
        """
        Get color hex for preview
        
        Args:
            color_id: Color ID
            
        Returns:
            Hex color string
        """
        try:
            color_id = int(color_id)
            return get_color_hex(color_id)
        except (ValueError, TypeError):
            return "#888888"
    
    def _extended_update_ui(self):

        self.effects_integration.update_effects()

        if hasattr(self.main_window, 'original_update_ui'):
            self.main_window.original_update_ui()


def integrate_effects(main_window):
    """
    Integrate effects functionality into the main window
    
    Args:
        main_window: Main window instance
    """
    extension = MainWindowExtension(main_window)
    extension.setup()
    return extension