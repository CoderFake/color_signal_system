import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from PIL import Image, ImageTk
import math
import time
import threading
from typing import Dict, List, Any, Tuple, Optional

from ..core.light_effect import LightEffect
from ..core.light_segment import LightSegment
from ..utils.effect_presets import get_preset_names, get_preset_params

class EffectPreviewPanel:
    """
    Panel to preview different effects
    """
    
    def __init__(self, parent, width: int = 600, height: int = 200):
        """
        Initialize the effect preview panel
        
        Args:
            parent: Parent widget
            width: Canvas width
            height: Canvas height
        """
        self.parent = parent
        self.width = width
        self.height = height
        
        self.frame = ctk.CTkFrame(parent)
        
        self.canvas = tk.Canvas(
            self.frame, 
            width=width, 
            height=height, 
            bg='#121212',
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.control_frame = ctk.CTkFrame(self.frame)
        self.control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        preset_label = ctk.CTkLabel(self.control_frame, text="Preview:")
        preset_label.pack(side=tk.LEFT, padx=5)
        
        preset_names = get_preset_names()
        self.preset_var = tk.StringVar(value=preset_names[0] if preset_names else "")
        self.preset_combo = ctk.CTkComboBox(
            self.control_frame,
            values=preset_names,
            variable=self.preset_var,
            command=self.on_preset_selected
        )
        self.preset_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.fps_var = tk.StringVar(value="FPS: 0")
        fps_label = ctk.CTkLabel(self.control_frame, textvariable=self.fps_var)
        fps_label.pack(side=tk.RIGHT, padx=10)
        
        self.led_count = 50
        self.led_size = 12
        self.led_spacing = 3
        self.running = False
        self.thread = None
        self.effect = None
        self.last_frame_time = time.time()
        self.fps = 30
        self.frame_count = 0
        self.last_fps_update = time.time()
        
        self.initialize_effect()
    
        self.start()
    
    def initialize_effect(self):
        """
        Initialize a sample effect
        """
        self.effect = LightEffect(1, self.led_count, self.fps)
        self.create_default_segment()
        self.apply_current_preset()
    
    def create_default_segment(self):
        """
        Create a default segment
        """
        segment = LightSegment(
            segment_ID=1,
            color=[1, 3, 4, 2],
            transparency=[0.0, 0.0, 0.0, 0.0],
            length=[10, 10, 10],
            move_speed=20,
            move_range=[0, self.led_count - 1],
            initial_position=0,
            is_edge_reflect=False,
            dimmer_time=[0, 500, 4500, 5000, 5000]
        )
        
        self.effect.add_segment(1, segment)
    
    def apply_current_preset(self):
        """
        Apply the currently selected preset
        """
        preset_name = self.preset_var.get()
        if not preset_name or not self.effect:
            return
            
        preset_params = get_preset_params(preset_name)
        if not preset_params:
            return
            
        for segment_id, segment in self.effect.segments.items():
            for param, value in preset_params.items():
                segment.update_param(param, value)
    
    def start(self):
        """
        Start the animation
        """
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._animation_thread)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """
        Stop the animation
        """
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None
    
    def _animation_thread(self):
        """
        Thread function for animation
        """
        while self.running:
            if self.effect:
                self.effect.update_all()
            
            self.parent.after(0, self._update_canvas)
            
            current_time = time.time()
            self.frame_count += 1
            
            if current_time - self.last_fps_update > 1.0:
                fps = self.frame_count / (current_time - self.last_fps_update)
                self.fps_var.set(f"FPS: {fps:.1f}")
                self.frame_count = 0
                self.last_fps_update = current_time
            
            sleep_time = 1.0 / self.fps - (time.time() - current_time)
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def _update_canvas(self):
        """
        Update the canvas with current effect state
        """
        if not self.effect:
            return
            
        self.canvas.delete("all")
        
        self._draw_background()
        
        led_colors = self.effect.get_led_output()
        
        led_total_width = self.led_size + self.led_spacing
        
        start_x = (self.width - (led_total_width * self.led_count - self.led_spacing)) // 2
        center_y = self.height // 2
        
        for i in range(min(self.led_count, len(led_colors))):
            x = start_x + i * led_total_width
            y = center_y
            
            color = self._rgb_to_hex(led_colors[i])
            
            wave_offset = math.sin(time.time() * 3 + i * 0.2) * 3
            
            brightness = sum(led_colors[i]) / (255 * 3)
            if brightness > 0.05:
                glow_radius = self.led_size + 5 * brightness
                self.canvas.create_oval(
                    x - glow_radius, y - glow_radius + wave_offset,
                    x + glow_radius, y + glow_radius + wave_offset,
                    fill=self._adjust_brightness(color, 0.7),
                    outline=""
                )
            
            self.canvas.create_oval(
                x - self.led_size/2, y - self.led_size/2 + wave_offset,
                x + self.led_size/2, y + self.led_size/2 + wave_offset,
                fill=color,
                outline="#333333" if brightness > 0.05 else ""
            )
            
            if brightness > 0.5:
                highlight_size = self.led_size * 0.3
                highlight_x = x - self.led_size * 0.2
                highlight_y = y - self.led_size * 0.2 + wave_offset
                self.canvas.create_oval(
                    highlight_x - highlight_size/2, highlight_y - highlight_size/2,
                    highlight_x + highlight_size/2, highlight_y + highlight_size/2,
                    fill="white",
                    outline=""
                )
        
        self.canvas.create_text(
            self.width // 2, 20,
            text=self.preset_var.get(),
            fill="white",
            font=("Helvetica", 14, "bold")
        )
    
    def _draw_background(self):
        """
        Draw background gradient
        """
        for y in range(self.height):
            ratio = y / self.height
            r = int(18 + ratio * 5)
            g = int(18 + ratio * 5)
            b = int(24 + ratio * 10)
            color = f"#{r:02x}{g:02x}{b:02x}"
            
            self.canvas.create_line(0, y, self.width, y, fill=color)
    
    def _rgb_to_hex(self, rgb: List[int]) -> str:
        """
        Convert RGB list to hex color
        
        Args:
            rgb: RGB color list [r, g, b]
            
        Returns:
            Hex color string
        """
        r, g, b = rgb
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _adjust_brightness(self, hex_color: str, factor: float) -> str:
        """
        Adjust brightness of a hex color
        
        Args:
            hex_color: Hex color string
            factor: Brightness factor (0.0-1.0)
            
        Returns:
            Adjusted hex color
        """
        hex_color = hex_color.lstrip('#')
        
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        r = min(255, int(r * factor))
        g = min(255, int(g * factor))
        b = min(255, int(b * factor))
        
        return f"#{r:02x}{g:02x}{b:02x}"