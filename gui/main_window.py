import tkinter as tk
from tkinter import ttk, colorchooser, messagebox, filedialog
import customtkinter as ctk
from PIL import Image, ImageTk
import os
import json
import threading
import time
from typing import Dict, List, Any, Optional, Tuple
import pygame
from pythonosc import udp_client

from ..core.light_effect import LightEffect
from ..core.light_segment import LightSegment
from .led_simulator import LEDSimulator
from ..communication.osc_handler import OSCHandler
from ..communication.device_scanner import DeviceScanner

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class MainWindow:
    """
    Main application window for LED control system
    """
    
    def __init__(self, title: str = "LED Tape Light Control System"):
        """
        Initialize the main window
        
        Args:
            title: Window title
        """
        self.root = ctk.CTk()
        self.root.title(title)
        self.root.geometry("1280x720")
        self.root.minsize(1024, 600)
        

        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
        if os.path.exists(icon_path):
            icon = tk.PhotoImage(file=icon_path)
            self.root.iconphoto(True, icon)
        

        self.effects: Dict[int, LightEffect] = {}
        self.current_effect_id = 1
        self.current_segment_id = 1
        self.osc_client = None
        self.osc_handler = None
        self.device_scanner = DeviceScanner()
        self.led_simulator = None
        self.preset_effects = self.load_preset_effects()
        

        self.create_default_effect()
        

        self.load_assets()
        

        self.create_menu()
        self.create_main_frame()
        

        self.start_simulator()
        

        self.start_osc_handler()
        

        self.schedule_updates()
        

        self.auto_cycle_timer = None
        self.current_preset_index = 0
    
    def load_assets(self):
        """
        Load application assets
        """
        self.icons = {}
        assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        

        if not os.path.exists(assets_dir):
            os.makedirs(assets_dir)
        

        icon_files = {
            "add": "add.png",
            "delete": "delete.png",
            "settings": "settings.png",
            "play": "play.png",
            "stop": "stop.png",
            "scan": "scan.png",
            "connect": "connect.png",
            "save": "save.png",
            "load": "load.png",
            "color": "color.png",
            "preset": "preset.png",
        }
        
        for name, filename in icon_files.items():
            icon_path = os.path.join(assets_dir, filename)
            if os.path.exists(icon_path):
                img = Image.open(icon_path)
                img = img.resize((20, 20), Image.LANCZOS)
                self.icons[name] = ImageTk.PhotoImage(img)
            else:

                img = Image.new('RGBA', (20, 20), color=(100, 100, 100, 255))
                self.icons[name] = ImageTk.PhotoImage(img)
    
    def start_simulator(self):
        """
        Start the LED simulator
        """
        if self.current_effect_id in self.effects:
            self.led_simulator = LEDSimulator(self.effects[self.current_effect_id])
            self.led_simulator.start()
            self.status_var.set("Simulator running")
    
    def start_osc_handler(self):
        """
        Start the OSC handler
        """
        self.osc_handler = OSCHandler(self.effects, ip="0.0.0.0", port=7700)
        self.osc_handler.start_server()
        self.status_var.set("OSC server started on port 7700")
    
    def schedule_updates(self):
        """
        Schedule periodic UI updates
        """
        self.update_ui()
        self.root.after(100, self.schedule_updates)
    
    def update_ui(self):
        """
        Update UI elements
        """

        effect_ids = [str(eid) for eid in self.effects.keys()]
        self.effect_id_combo.configure(values=effect_ids)
        

        if self.current_effect_id in self.effects:
            current_effect = self.effects[self.current_effect_id]
            segment_ids = [str(sid) for sid in current_effect.segments.keys()]
            if segment_ids:
                self.segment_id_combo.configure(values=segment_ids)
                

                try:
                    current_segment_id = int(self.segment_id_var.get())
                    if current_segment_id in current_effect.segments:
                        self.update_segment_ui(current_effect.segments[current_segment_id])
                except (ValueError, KeyError):
                    pass
    
    def update_segment_ui(self, segment):
        """
        Update UI with segment parameters
        
        Args:
            segment: LightSegment instance
        """

        self.pos_var.set(str(segment.initial_position))
        self.range_min_var.set(str(segment.move_range[0]))
        self.range_max_var.set(str(segment.move_range[1]))
        self.speed_var.set(str(segment.move_speed))
        self.reflect_var.set("1" if segment.is_edge_reflect else "0")
        
        for i, length in enumerate(segment.length):
            if i < len(self.length_vars):
                self.length_vars[i].set(str(length))
        

        for i, color_id in enumerate(segment.color):
            if i < len(self.color_vars):
                self.color_vars[i].set(str(color_id))
                if i < len(self.color_buttons):
                    self.color_buttons[i].configure(fg_color=self.get_color_preview(color_id))
        

        for i, trans in enumerate(segment.transparency):
            if i < len(self.transparency_vars):
                self.transparency_vars[i].set(str(trans))
        

        for i, time_val in enumerate(segment.dimmer_time):
            if i < len(self.dimmer_vars):
                self.dimmer_vars[i].set(str(time_val))
    
    def get_color_preview(self, color_id):
        """
        Get RGB hex color for preview
        
        Args:
            color_id: Color ID
            
        Returns:
            Hex color string
        """
        color_map = {
            0: "#000000",  # Black
            1: "#FF0000",  # Red
            2: "#00FF00",  # Green
            3: "#0000FF",  # Blue
            4: "#FFFF00",  # Yellow
            5: "#FF00FF",  # Magenta
            6: "#00FFFF",  # Cyan
            7: "#FFFFFF",  # White
            8: "#FF7F00",  # Orange
            9: "#7F00FF",  # Purple
            10: "#007FFF", # Light blue
        }
        
        try:
            color_id = int(color_id)
            return color_map.get(color_id, "#888888")
        except (ValueError, TypeError):
            return "#888888"
    
    def on_effect_selected(self, value):
        """
        Handle effect selection
        
        Args:
            value: Selected effect ID
        """
        try:
            effect_id = int(value)
            if effect_id in self.effects:
                self.current_effect_id = effect_id
                

                if self.led_simulator:
                    self.led_simulator.stop()
                    self.led_simulator = LEDSimulator(self.effects[effect_id])
                    self.led_simulator.start()
                

                self.led_count_var.set(str(self.effects[effect_id].led_count))
                self.fps_var.set(str(self.effects[effect_id].fps))
                

                segment_ids = [str(sid) for sid in self.effects[effect_id].segments.keys()]
                self.segment_id_combo.configure(values=segment_ids)
                
                if segment_ids:
                    self.segment_id_var.set(segment_ids[0])
                    self.current_segment_id = int(segment_ids[0])
                    self.update_segment_ui(self.effects[effect_id].segments[self.current_segment_id])
        except ValueError:
            pass
    
    def on_segment_selected(self, value):
        """
        Handle segment selection
        
        Args:
            value: Selected segment ID
        """
        try:
            segment_id = int(value)
            self.current_segment_id = segment_id
            
            if self.current_effect_id in self.effects:
                effect = self.effects[self.current_effect_id]
                if segment_id in effect.segments:
                    self.update_segment_ui(effect.segments[segment_id])
        except ValueError:
            pass
    
    def on_new_effect(self):
        """
        Create a new effect
        """

        next_id = 1
        while next_id in self.effects:
            next_id += 1
        

        dialog = ctk.CTkInputDialog(
            text="Enter LED count and FPS (comma separated):",
            title="New Effect"
        )
        result = dialog.get_input()
        
        if result:
            try:
                parts = result.split(',')
                led_count = int(parts[0].strip())
                fps = int(parts[1].strip()) if len(parts) > 1 else 30
                

                effect = LightEffect(next_id, led_count, fps)
                self.effects[next_id] = effect
                

                self.effect_id_var.set(str(next_id))
                self.on_effect_selected(str(next_id))
                
                self.status_var.set(f"Created new effect with ID {next_id}")
            except (ValueError, IndexError):
                messagebox.showerror("Error", "Invalid input. Please enter valid numbers.")
    
    def on_add_effect(self):
        """
        Add a new effect
        """
        self.on_new_effect()
    
    def on_delete_effect(self):
        """
        Delete the current effect
        """
        if len(self.effects) <= 1:
            messagebox.showwarning("Warning", "Cannot delete the last effect.")
            return
        
        if messagebox.askyesno("Confirm", f"Delete effect with ID {self.current_effect_id}?"):

            if self.led_simulator and self.current_effect_id in self.effects:
                self.led_simulator.stop()
                self.led_simulator = None
            

            del self.effects[self.current_effect_id]
            

            next_id = list(self.effects.keys())[0]
            self.effect_id_var.set(str(next_id))
            self.on_effect_selected(str(next_id))
            

            if self.led_simulator is None:
                self.start_simulator()
            
            self.status_var.set(f"Deleted effect with ID {self.current_effect_id}")
    
    def on_update_led_count(self):
        """
        Update LED count for current effect
        """
        try:
            led_count = int(self.led_count_var.get())
            if led_count < 1:
                raise ValueError("LED count must be positive")
            
            if self.current_effect_id in self.effects:

                self.effects[self.current_effect_id].led_count = led_count
                

                if self.led_simulator:
                    self.led_simulator.stop()
                    self.led_simulator = LEDSimulator(self.effects[self.current_effect_id])
                    self.led_simulator.start()
                
                self.status_var.set(f"Updated LED count to {led_count}")
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid LED count: {str(e)}")
    
    def on_update_fps(self):
        """
        Update FPS for current effect
        """
        try:
            fps = int(self.fps_var.get())
            if fps < 1:
                raise ValueError("FPS must be positive")
            
            if self.current_effect_id in self.effects:

                self.effects[self.current_effect_id].fps = fps
                

                if self.led_simulator:
                    self.led_simulator.stop()
                    self.led_simulator = LEDSimulator(self.effects[self.current_effect_id])
                    self.led_simulator.start()
                
                self.status_var.set(f"Updated FPS to {fps}")
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid FPS: {str(e)}")
    
    def on_add_segment(self):
        """
        Add a new segment to the current effect
        """
        if self.current_effect_id not in self.effects:
            return
        
        effect = self.effects[self.current_effect_id]
        

        next_id = 1
        while next_id in effect.segments:
            next_id += 1
        

        segment = LightSegment(
            segment_ID=next_id,
            color=[1, 3, 4, 2],  # Red, Blue, Yellow, Green
            transparency=[0.0, 0.0, 0.0, 0.0],
            length=[30, 30, 30],
            move_speed=20,
            move_range=[0, effect.led_count - 1],
            initial_position=0,
            is_edge_reflect=False,
            dimmer_time=[0, 500, 4500, 5000, 5000]
        )
        

        effect.add_segment(next_id, segment)
        

        self.segment_id_var.set(str(next_id))
        self.current_segment_id = next_id
        self.update_segment_ui(segment)
        

        segment_ids = [str(sid) for sid in effect.segments.keys()]
        self.segment_id_combo.configure(values=segment_ids)
        
        self.status_var.set(f"Added new segment with ID {next_id}")
    
    def on_delete_segment(self):
        """
        Delete the current segment
        """
        if self.current_effect_id not in self.effects:
            return
            
        effect = self.effects[self.current_effect_id]
        
        if len(effect.segments) <= 1:
            messagebox.showwarning("Warning", "Cannot delete the last segment.")
            return
        
        if messagebox.askyesno("Confirm", f"Delete segment with ID {self.current_segment_id}?"):

            if effect.remove_segment(self.current_segment_id):

                segment_ids = [str(sid) for sid in effect.segments.keys()]
                self.segment_id_combo.configure(values=segment_ids)
                
                if segment_ids:
                    self.segment_id_var.set(segment_ids[0])
                    self.current_segment_id = int(segment_ids[0])
                    self.update_segment_ui(effect.segments[self.current_segment_id])
                
                self.status_var.set(f"Deleted segment with ID {self.current_segment_id}")
    
    def on_apply_preset(self):
        """
        Apply selected preset to current segment
        """
        preset_name = self.preset_var.get()
        if not preset_name or preset_name not in self.preset_effects:
            return
            
        if self.current_effect_id not in self.effects:
            return
            
        effect = self.effects[self.current_effect_id]
        if self.current_segment_id not in effect.segments:
            return
            
        segment = effect.segments[self.current_segment_id]
        preset = self.preset_effects[preset_name]
        

        for param, value in preset.items():
            segment.update_param(param, value)
        

        self.update_segment_ui(segment)
        

        if self.osc_client:
            for param, value in preset.items():
                address = f"/effect/{self.current_effect_id}/segment/{self.current_segment_id}/{param}"
                self.osc_handler.send_osc(self.osc_client, address, value)
        
        self.status_var.set(f"Applied preset '{preset_name}' to segment {self.current_segment_id}")
    
    def on_toggle_auto_cycle(self):
        """
        Toggle auto-cycling of presets
        """
        if self.auto_cycle_var.get() == "1":

            self.start_auto_cycle()
        else:

            self.stop_auto_cycle()
    
    def start_auto_cycle(self):
        """
        Start auto-cycling presets
        """
        if self.auto_cycle_timer:
            self.root.after_cancel(self.auto_cycle_timer)
        
        try:
            interval = float(self.cycle_interval_var.get()) * 1000  # Convert to milliseconds
            if interval < 1000:  # Minimum 1 second
                interval = 1000
                self.cycle_interval_var.set("1")
            
            self.current_preset_index = 0
            self.apply_next_preset()
            
            self.status_var.set("Auto-cycling presets started")
        except ValueError:
            messagebox.showerror("Error", "Invalid cycle interval")
            self.auto_cycle_var.set("0")
    
    def stop_auto_cycle(self):
        """
        Stop auto-cycling presets
        """
        if self.auto_cycle_timer:
            self.root.after_cancel(self.auto_cycle_timer)
            self.auto_cycle_timer = None
            
        self.status_var.set("Auto-cycling presets stopped")
    
    def apply_next_preset(self):
        """
        Apply the next preset in sequence
        """
        preset_names = list(self.preset_effects.keys())
        if not preset_names:
            return
            

        preset_name = preset_names[self.current_preset_index]
        self.preset_var.set(preset_name)
        self.on_apply_preset()
        

        self.current_preset_index = (self.current_preset_index + 1) % len(preset_names)
        

        try:
            interval = float(self.cycle_interval_var.get()) * 1000  # Convert to milliseconds
            self.auto_cycle_timer = self.root.after(int(interval), self.apply_next_preset)
        except ValueError:
            pass
    
    def on_update_basic_params(self):
        """
        Update basic parameters for current segment
        """
        if self.current_effect_id not in self.effects:
            return
            
        effect = self.effects[self.current_effect_id]
        if self.current_segment_id not in effect.segments:
            return
            
        segment = effect.segments[self.current_segment_id]
        
        try:

            initial_position = int(self.pos_var.get())
            move_range = [int(self.range_min_var.get()), int(self.range_max_var.get())]
            move_speed = float(self.speed_var.get())
            is_edge_reflect = self.reflect_var.get() == "1"
            length = [int(var.get()) for var in self.length_vars]
            

            if move_range[0] >= move_range[1]:
                raise ValueError("Move range minimum must be less than maximum")
                
            if any(l <= 0 for l in length):
                raise ValueError("Segment lengths must be positive")
            

            segment.update_param("initial_position", initial_position)
            segment.update_param("move_range", move_range)
            segment.update_param("move_speed", move_speed)
            segment.update_param("is_edge_reflect", is_edge_reflect)
            segment.update_param("length", length)
            

            if self.osc_client:
                base_address = f"/effect/{self.current_effect_id}/segment/{self.current_segment_id}"
                self.osc_handler.send_osc(self.osc_client, f"{base_address}/initial_position", initial_position)
                self.osc_handler.send_osc(self.osc_client, f"{base_address}/move_range", move_range)
                self.osc_handler.send_osc(self.osc_client, f"{base_address}/move_speed", move_speed)
                self.osc_handler.send_osc(self.osc_client, f"{base_address}/is_edge_reflect", is_edge_reflect)
                self.osc_handler.send_osc(self.osc_client, f"{base_address}/length", length)
            
            self.status_var.set("Updated basic parameters")
        except ValueError as e:
            messagebox.showerror("Error", str(e))
    
    def on_update_colors(self):
        """
        Update color parameters for current segment
        """
        if self.current_effect_id not in self.effects:
            return
            
        effect = self.effects[self.current_effect_id]
        if self.current_segment_id not in effect.segments:
            return
            
        segment = effect.segments[self.current_segment_id]
        
        try:

            color = [int(var.get()) for var in self.color_vars]
            transparency = [float(var.get()) for var in self.transparency_vars]
            

            if any(c < 0 or c > 10 for c in color):
                raise ValueError("Color values must be between 0 and 10")
                
            if any(t < 0.0 or t > 1.0 for t in transparency):
                raise ValueError("Transparency values must be between 0.0 and 1.0")
            

            segment.update_param("color", color)
            segment.update_param("transparency", transparency)
            

            if self.osc_client:
                base_address = f"/effect/{self.current_effect_id}/segment/{self.current_segment_id}"
                self.osc_handler.send_osc(self.osc_client, f"{base_address}/color", color)
                self.osc_handler.send_osc(self.osc_client, f"{base_address}/transparency", transparency)
            
            self.status_var.set("Updated color parameters")
        except ValueError as e:
            messagebox.showerror("Error", str(e))
    
    def on_update_timing(self):
        """
        Update timing parameters for current segment
        """
        if self.current_effect_id not in self.effects:
            return
            
        effect = self.effects[self.current_effect_id]
        if self.current_segment_id not in effect.segments:
            return
            
        segment = effect.segments[self.current_segment_id]
        
        try:

            dimmer_time = [int(var.get()) for var in self.dimmer_vars]
            

            if any(t < 0 for t in dimmer_time):
                raise ValueError("Timing values must be non-negative")
                
            if dimmer_time[0] >= dimmer_time[1]:
                raise ValueError("Fade In Start must be less than Fade In End")
                
            if dimmer_time[2] >= dimmer_time[3]:
                raise ValueError("Fade Out Start must be less than Fade Out End")
                
            if dimmer_time[4] <= 0:
                raise ValueError("Cycle Time must be positive")
            

            segment.update_param("dimmer_time", dimmer_time)
            

            if self.osc_client:
                address = f"/effect/{self.current_effect_id}/segment/{self.current_segment_id}/dimmer_time"
                self.osc_handler.send_osc(self.osc_client, address, dimmer_time)
            
            self.status_var.set("Updated timing parameters")
        except ValueError as e:
            messagebox.showerror("Error", str(e))
    
    def on_color_selected(self, index):
        """
        Handle color selection from dropdown
        
        Args:
            index: Color index (0-3)
        """
        try:
            color_id = int(self.color_vars[index].get())
            self.color_buttons[index].configure(fg_color=self.get_color_preview(color_id))
        except (ValueError, IndexError):
            pass
    
    def on_custom_color(self, index):
        """
        Handle custom color selection
        
        Args:
            index: Color index (0-3)
        """


        messagebox.showinfo("Custom Colors", "Custom color selection is not available in this version.")
    
    def on_scan_network(self):
        """
        Scan the network for LED controller devices
        """
        self.status_var.set("Scanning network...")
        
        def on_device_found(device_info):
            self.conn_status_var.set(f"Found: {device_info['ip']}:{device_info['port']}")
        
        def on_scan_complete():
            devices = self.device_scanner.get_discovered_devices()
            if devices:
                device_list = "\n".join([f"{d['ip']}:{d['port']} ({d['type']})" for d in devices.values()])
                messagebox.showinfo("Scan Results", f"Found {len(devices)} devices:\n\n{device_list}")
                self.status_var.set(f"Found {len(devices)} devices")
            else:
                messagebox.showinfo("Scan Results", "No LED controller devices found.")
                self.status_var.set("No devices found")
        

        scan_thread = self.device_scanner.scan_network(callback=on_device_found)
        

        def check_scan():
            if self.device_scanner.scanning:
                self.root.after(500, check_scan)
            else:
                on_scan_complete()
        
        self.root.after(500, check_scan)
    
    def on_connect_device(self):
        """
        Connect to a device
        """
        devices = self.device_scanner.get_discovered_devices()
        
        if not devices:
            result = messagebox.askyesno("No Devices", "No devices found. Do you want to scan now?")
            if result:
                self.on_scan_network()
            return
        

        connect_window = ctk.CTkToplevel(self.root)
        connect_window.title("Connect to Device")
        connect_window.geometry("400x300")
        connect_window.transient(self.root)
        connect_window.grab_set()
        

        frame = ctk.CTkFrame(connect_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        label = ctk.CTkLabel(frame, text="Select a device to connect:")
        label.pack(pady=10)
        
        device_list = tk.Listbox(frame, height=10)
        device_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        

        device_map = {}
        for i, (device_id, device) in enumerate(devices.items()):
            display = f"{device['ip']}:{device['port']} ({device['type']})"
            device_list.insert(tk.END, display)
            device_map[i] = device
        

        def on_connect():
            selected = device_list.curselection()
            if selected:
                device = device_map[selected[0]]
                self.connect_to_device(device['ip'], device['port'])
                connect_window.destroy()
        
        connect_button = ctk.CTkButton(frame, text="Connect", command=on_connect)
        connect_button.pack(pady=10)
        

        cancel_button = ctk.CTkButton(frame, text="Cancel", command=connect_window.destroy)
        cancel_button.pack(pady=10)
    
    def connect_to_device(self, ip, port):
        """
        Connect to a device
        
        Args:
            ip: Device IP address
            port: Device port
        """
        try:
            self.osc_client = udp_client.SimpleUDPClient(ip, port)
            self.conn_status_var.set(f"Connected: {ip}:{port}")
            self.status_var.set(f"Connected to {ip}:{port}")
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))
            self.conn_status_var.set("Not Connected")
    
    def on_osc_settings(self):
        """
        Show OSC settings dialog
        """

        settings_window = ctk.CTkToplevel(self.root)
        settings_window.title("OSC Settings")
        settings_window.geometry("400x200")
        settings_window.transient(self.root)
        settings_window.grab_set()
        

        frame = ctk.CTkFrame(settings_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        

        port_frame = ctk.CTkFrame(frame)
        port_frame.pack(fill=tk.X, pady=10)
        
        port_label = ctk.CTkLabel(port_frame, text="Listen Port:")
        port_label.pack(side=tk.LEFT, padx=10)
        
        port_var = tk.StringVar(value="7700")
        port_entry = ctk.CTkEntry(port_frame, textvariable=port_var)
        port_entry.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        

        def on_apply():
            try:
                port = int(port_var.get())
                if port < 1024 or port > 65535:
                    raise ValueError("Port must be between 1024 and 65535")
                

                if self.osc_handler:
                    self.osc_handler.stop_server()
                
                self.osc_handler = OSCHandler(self.effects, ip="0.0.0.0", port=port)
                self.osc_handler.start_server()
                
                self.status_var.set(f"OSC server restarted on port {port}")
                settings_window.destroy()
            except ValueError as e:
                messagebox.showerror("Error", str(e))
        
        apply_button = ctk.CTkButton(frame, text="Apply", command=on_apply)
        apply_button.pack(pady=10)
        

        cancel_button = ctk.CTkButton(frame, text="Cancel", command=settings_window.destroy)
        cancel_button.pack(pady=10)
    
    def on_save_config(self):
        """
        Save current configuration to file
        """
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Configuration"
        )
        
        if not file_path:
            return
        
        try:
            config = {
                "effects": {}
            }
            

            for effect_id, effect in self.effects.items():
                segments = {}
                for segment_id, segment in effect.segments.items():
                    segments[segment_id] = {
                        "segment_ID": segment.segment_ID,
                        "color": segment.color,
                        "transparency": segment.transparency,
                        "length": segment.length,
                        "move_speed": segment.move_speed,
                        "move_range": segment.move_range,
                        "initial_position": segment.initial_position,
                        "is_edge_reflect": segment.is_edge_reflect,
                        "dimmer_time": segment.dimmer_time
                    }
                
                config["effects"][effect_id] = {
                    "effect_ID": effect.effect_ID,
                    "led_count": effect.led_count,
                    "fps": effect.fps,
                    "segments": segments
                }
            
            with open(file_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.status_var.set(f"Configuration saved to {file_path}")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))
    
    def on_load_config(self):
        """
        Load configuration from file
        """
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Configuration"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r') as f:
                config = json.load(f)
            

            if self.led_simulator:
                self.led_simulator.stop()
                self.led_simulator = None
            

            self.effects.clear()
            

            for effect_id_str, effect_data in config["effects"].items():
                effect_id = int(effect_id_str)
                effect = LightEffect(
                    effect_id,
                    effect_data["led_count"],
                    effect_data["fps"]
                )
                

                for segment_id_str, segment_data in effect_data["segments"].items():
                    segment_id = int(segment_id_str)
                    segment = LightSegment(
                        segment_ID=segment_id,
                        color=segment_data["color"],
                        transparency=segment_data["transparency"],
                        length=segment_data["length"],
                        move_speed=segment_data["move_speed"],
                        move_range=segment_data["move_range"],
                        initial_position=segment_data["initial_position"],
                        is_edge_reflect=segment_data["is_edge_reflect"],
                        dimmer_time=segment_data["dimmer_time"]
                    )
                    effect.add_segment(segment_id, segment)
                
                self.effects[effect_id] = effect
            

            if self.effects:
                self.current_effect_id = list(self.effects.keys())[0]
                self.effect_id_var.set(str(self.current_effect_id))
                

                effect = self.effects[self.current_effect_id]
                if effect.segments:
                    self.current_segment_id = list(effect.segments.keys())[0]
                    self.segment_id_var.set(str(self.current_segment_id))
                

                self.update_ui()
                

                self.start_simulator()
            
            self.status_var.set(f"Configuration loaded from {file_path}")
        except Exception as e:
            messagebox.showerror("Load Error", str(e))
            

            if not self.effects:
                self.create_default_effect()
                self.start_simulator()
    
    def on_simulator_settings(self):
        """
        Show simulator settings dialog
        """

        settings_window = ctk.CTkToplevel(self.root)
        settings_window.title("Simulator Settings")
        settings_window.geometry("400x300")
        settings_window.transient(self.root)
        settings_window.grab_set()
        

        frame = ctk.CTkFrame(settings_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        

        size_frame = ctk.CTkFrame(frame)
        size_frame.pack(fill=tk.X, pady=10)
        
        size_label = ctk.CTkLabel(size_frame, text="LED Size:")
        size_label.pack(side=tk.LEFT, padx=10)
        
        size_var = tk.StringVar(value="20")
        size_slider = ctk.CTkSlider(
            size_frame,
            from_=5,
            to=40,
            number_of_steps=35,
            variable=size_var
        )
        size_slider.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        size_value = ctk.CTkLabel(size_frame, textvariable=size_var, width=40)
        size_value.pack(side=tk.LEFT, padx=10)
        

        spacing_frame = ctk.CTkFrame(frame)
        spacing_frame.pack(fill=tk.X, pady=10)
        
        spacing_label = ctk.CTkLabel(spacing_frame, text="LED Spacing:")
        spacing_label.pack(side=tk.LEFT, padx=10)
        
        spacing_var = tk.StringVar(value="5")
        spacing_slider = ctk.CTkSlider(
            spacing_frame,
            from_=0,
            to=20,
            number_of_steps=20,
            variable=spacing_var
        )
        spacing_slider.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        spacing_value = ctk.CTkLabel(spacing_frame, textvariable=spacing_var, width=40)
        spacing_value.pack(side=tk.LEFT, padx=10)
        

        bg_frame = ctk.CTkFrame(frame)
        bg_frame.pack(fill=tk.X, pady=10)
        
        bg_label = ctk.CTkLabel(bg_frame, text="Background:")
        bg_label.pack(side=tk.LEFT, padx=10)
        
        bg_choices = ["Dark Blue", "Dark Gray", "Black", "Navy"]
        bg_var = tk.StringVar(value=bg_choices[0])
        bg_combo = ctk.CTkComboBox(
            bg_frame,
            values=bg_choices,
            variable=bg_var
        )
        bg_combo.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        

        def on_apply():
            try:
                led_size = int(float(size_var.get()))
                led_spacing = int(float(spacing_var.get()))
                

                bg_map = {
                    "Dark Blue": (10, 10, 15),
                    "Dark Gray": (20, 20, 20),
                    "Black": (0, 0, 0),
                    "Navy": (0, 0, 20)
                }
                bg_color = bg_map.get(bg_var.get(), (10, 10, 15))
                

                if self.led_simulator:
                    self.led_simulator.stop()
                    

                    if self.current_effect_id in self.effects:
                        self.led_simulator = LEDSimulator(
                            self.effects[self.current_effect_id],
                            led_size=led_size,
                            led_spacing=led_spacing,
                            bg_color=bg_color
                        )
                        self.led_simulator.start()
                
                self.status_var.set("Simulator settings updated")
                settings_window.destroy()
            except ValueError as e:
                messagebox.showerror("Error", str(e))
        
        apply_button = ctk.CTkButton(frame, text="Apply", command=on_apply)
        apply_button.pack(pady=10)
        

        cancel_button = ctk.CTkButton(frame, text="Cancel", command=settings_window.destroy)
        cancel_button.pack(pady=10)
    
    def on_documentation(self):
        """
        Show documentation
        """
        doc_window = ctk.CTkToplevel(self.root)
        doc_window.title("Documentation")
        doc_window.geometry("600x500")
        

        doc_frame = ctk.CTkScrollableFrame(doc_window)
        doc_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        

        title_label = ctk.CTkLabel(
            doc_frame, 
            text="LED Tape Light Control System",
            font=("Helvetica", 20, "bold")
        )
        title_label.pack(pady=10)
        

        doc_text = """
        This application allows you to create and control LED tape light effects. 
        
        Key Features:
        - Create multiple effects with different LED counts and frame rates
        - Add multiple segments to each effect with customizable properties
        - Apply preset effects or create your own
        - Send control commands via OSC protocol
        - Visualize LED animations in real-time
        
        Usage:
        1. Effect Controls: Manage LED count and FPS settings for each effect
        2. Segment Controls: Customize color, timing, and movement parameters
        3. Presets: Apply predefined effects to segments
        4. Connection: Connect to physical LED controllers over the network
        
        OSC Protocol:
        Send commands using the format: /effect/{effect_ID}/segment/{segment_ID}/{param_name} {value}
        
        For more information, refer to the technical documentation.
        """
        
        doc_label = ctk.CTkLabel(
            doc_frame, 
            text=doc_text,
            anchor="w",
            justify="left",
            wraplength=550
        )
        doc_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        

        close_button = ctk.CTkButton(
            doc_window,
            text="Close",
            command=doc_window.destroy
        )
        close_button.pack(pady=10)
    
    def on_about(self):
        """
        Show about dialog
        """
        messagebox.showinfo(
            "About",
            "LED Tape Light Control System\n\n"
            "Version 1.0\n\n"
            "A Python application for creating and controlling LED tape light effects"
        )
    
    def run(self):
        """
        Run the application
        """
        self.root.mainloop()
        
        if self.led_simulator:
            self.led_simulator.stop()
        
        if self.osc_handler:
            self.osc_handler.stop_server()

    def load_preset_effects(self):
        """
        Load preset effects
        
        Returns:
            Dictionary of preset effects
        """
        
        return {
            "Rainbow Flow": {
                "color": [1, 3, 4, 2],
                "transparency": [0.0, 0.0, 0.0, 0.0],
                "length": [30, 30, 30],
                "move_speed": 20,
                "is_edge_reflect": False,
                "dimmer_time": [0, 500, 4500, 5000, 5000]
            },
            "Breathing": {
                "color": [7, 7, 7, 7],
                "transparency": [0.0, 0.0, 0.0, 0.0],
                "length": [1, 1, 1],
                "move_speed": 0,
                "is_edge_reflect": False,
                "dimmer_time": [0, 2000, 2000, 4000, 4000]
            },
            "Police Lights": {
                "color": [1, 3, 1, 3],
                "transparency": [0.0, 0.0, 0.0, 0.0],
                "length": [20, 20, 20],
                "move_speed": 100,
                "is_edge_reflect": False,
                "dimmer_time": [0, 100, 100, 200, 200]
            },
            "Color Wipe": {
                "color": [0, 5, 0, 5],
                "transparency": [0.0, 0.0, 0.0, 0.0],
                "length": [50, 50, 50],
                "move_speed": 50,
                "is_edge_reflect": False,
                "dimmer_time": [0, 0, 0, 0, 1000]
            },
            "Pulse": {
                "color": [8, 8, 8, 8],
                "transparency": [0.0, 0.0, 0.0, 0.0],
                "length": [10, 10, 10],
                "move_speed": 0,
                "is_edge_reflect": False,
                "dimmer_time": [0, 500, 500, 1000, 1000]
            }
        }
    
    def create_menu(self):
        """
        Create application menu
        """
        self.menu = tk.Menu(self.root)
        self.root.config(menu=self.menu)
        

        file_menu = tk.Menu(self.menu, tearoff=0)
        file_menu.add_command(label="New Effect", command=self.on_new_effect)
        file_menu.add_command(label="Save Configuration", command=self.on_save_config)
        file_menu.add_command(label="Load Configuration", command=self.on_load_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        self.menu.add_cascade(label="File", menu=file_menu)
        

        connection_menu = tk.Menu(self.menu, tearoff=0)
        connection_menu.add_command(label="Scan Network", command=self.on_scan_network)
        connection_menu.add_command(label="Connect to Device", command=self.on_connect_device)
        connection_menu.add_separator()
        connection_menu.add_command(label="OSC Settings", command=self.on_osc_settings)
        self.menu.add_cascade(label="Connection", menu=connection_menu)
        

        view_menu = tk.Menu(self.menu, tearoff=0)
        view_menu.add_command(label="LED Simulator Settings", command=self.on_simulator_settings)
        self.menu.add_cascade(label="View", menu=view_menu)
        

        help_menu = tk.Menu(self.menu, tearoff=0)
        help_menu.add_command(label="Documentation", command=self.on_documentation)
        help_menu.add_command(label="About", command=self.on_about)
        self.menu.add_cascade(label="Help", menu=help_menu)
    
    def create_main_frame(self):
        """
        Create the main application frame with all controls
        """

        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        

        self.left_panel = ctk.CTkFrame(self.main_frame, width=350)
        self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)
        

        self.right_panel = ctk.CTkFrame(self.main_frame)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        

        self.create_effect_panel()
        

        self.create_segment_panel()
        

        self.create_visualizer_panel()
        

        self.create_status_bar()
    
    def create_effect_panel(self):
        """
        Create the effect control panel
        """

        self.effect_frame = ctk.CTkFrame(self.left_panel)
        self.effect_frame.pack(fill=tk.X, padx=5, pady=5)
        

        effect_header = ctk.CTkFrame(self.effect_frame)
        effect_header.pack(fill=tk.X, padx=5, pady=5)
        
        effect_label = ctk.CTkLabel(effect_header, text="Effect Controls", font=("Helvetica", 16, "bold"))
        effect_label.pack(side=tk.LEFT, padx=5)
        

        effect_id_frame = ctk.CTkFrame(self.effect_frame)
        effect_id_frame.pack(fill=tk.X, padx=5, pady=5)
        
        effect_id_label = ctk.CTkLabel(effect_id_frame, text="Effect ID:")
        effect_id_label.pack(side=tk.LEFT, padx=5)
        
        self.effect_id_var = tk.StringVar(value=str(self.current_effect_id))
        effect_ids = [str(eid) for eid in self.effects.keys()]
        self.effect_id_combo = ctk.CTkComboBox(
            effect_id_frame, 
            values=effect_ids,
            variable=self.effect_id_var,
            command=self.on_effect_selected
        )
        self.effect_id_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        add_effect_btn = ctk.CTkButton(
            effect_id_frame, 
            text="", 
            image=self.icons.get("add"),
            width=30,
            command=self.on_add_effect
        )
        add_effect_btn.pack(side=tk.LEFT, padx=5)
        
        delete_effect_btn = ctk.CTkButton(
            effect_id_frame, 
            text="", 
            image=self.icons.get("delete"),
            width=30,
            command=self.on_delete_effect
        )
        delete_effect_btn.pack(side=tk.LEFT, padx=5)
        

        led_count_frame = ctk.CTkFrame(self.effect_frame)
        led_count_frame.pack(fill=tk.X, padx=5, pady=5)
        
        led_count_label = ctk.CTkLabel(led_count_frame, text="LED Count:")
        led_count_label.pack(side=tk.LEFT, padx=5)
        
        self.led_count_var = tk.StringVar(value=str(self.effects[self.current_effect_id].led_count))
        led_count_entry = ctk.CTkEntry(led_count_frame, textvariable=self.led_count_var)
        led_count_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        update_led_count_btn = ctk.CTkButton(
            led_count_frame, 
            text="Update", 
            command=self.on_update_led_count
        )
        update_led_count_btn.pack(side=tk.LEFT, padx=5)
        

        fps_frame = ctk.CTkFrame(self.effect_frame)
        fps_frame.pack(fill=tk.X, padx=5, pady=5)
        
        fps_label = ctk.CTkLabel(fps_frame, text="FPS:")
        fps_label.pack(side=tk.LEFT, padx=5)
        
        self.fps_var = tk.StringVar(value=str(self.effects[self.current_effect_id].fps))
        fps_entry = ctk.CTkEntry(fps_frame, textvariable=self.fps_var)
        fps_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        update_fps_btn = ctk.CTkButton(
            fps_frame, 
            text="Update", 
            command=self.on_update_fps
        )
        update_fps_btn.pack(side=tk.LEFT, padx=5)
    
    def create_segment_panel(self):
        """
        Create the segment control panel
        """

        self.segment_frame = ctk.CTkFrame(self.left_panel)
        self.segment_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        

        segment_header = ctk.CTkFrame(self.segment_frame)
        segment_header.pack(fill=tk.X, padx=5, pady=5)
        
        segment_label = ctk.CTkLabel(segment_header, text="Segment Controls", font=("Helvetica", 16, "bold"))
        segment_label.pack(side=tk.LEFT, padx=5)
        

        segment_id_frame = ctk.CTkFrame(self.segment_frame)
        segment_id_frame.pack(fill=tk.X, padx=5, pady=5)
        
        segment_id_label = ctk.CTkLabel(segment_id_frame, text="Segment ID:")
        segment_id_label.pack(side=tk.LEFT, padx=5)
        
        current_effect = self.effects[self.current_effect_id]
        segment_ids = [str(sid) for sid in current_effect.segments.keys()]
        
        self.segment_id_var = tk.StringVar(value=str(self.current_segment_id) if segment_ids else "1")
        self.segment_id_combo = ctk.CTkComboBox(
            segment_id_frame, 
            values=segment_ids if segment_ids else ["1"],
            variable=self.segment_id_var,
            command=self.on_segment_selected
        )
        self.segment_id_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        add_segment_btn = ctk.CTkButton(
            segment_id_frame, 
            text="", 
            image=self.icons.get("add"),
            width=30,
            command=self.on_add_segment
        )
        add_segment_btn.pack(side=tk.LEFT, padx=5)
        
        delete_segment_btn = ctk.CTkButton(
            segment_id_frame, 
            text="", 
            image=self.icons.get("delete"),
            width=30,
            command=self.on_delete_segment
        )
        delete_segment_btn.pack(side=tk.LEFT, padx=5)
        

        preset_frame = ctk.CTkFrame(self.segment_frame)
        preset_frame.pack(fill=tk.X, padx=5, pady=5)
        
        preset_label = ctk.CTkLabel(preset_frame, text="Preset:")
        preset_label.pack(side=tk.LEFT, padx=5)
        
        preset_values = list(self.preset_effects.keys())
        self.preset_var = tk.StringVar(value=preset_values[0] if preset_values else "")
        self.preset_combo = ctk.CTkComboBox(
            preset_frame,
            values=preset_values,
            variable=self.preset_var
        )
        self.preset_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        apply_preset_btn = ctk.CTkButton(
            preset_frame,
            text="Apply",
            command=self.on_apply_preset
        )
        apply_preset_btn.pack(side=tk.LEFT, padx=5)
        

        self.segment_notebook = ttk.Notebook(self.segment_frame)
        self.segment_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        

        self.basic_tab = ctk.CTkFrame(self.segment_notebook)
        self.segment_notebook.add(self.basic_tab, text="Basic")
        

        self.colors_tab = ctk.CTkFrame(self.segment_notebook)
        self.segment_notebook.add(self.colors_tab, text="Colors")
        

        self.timing_tab = ctk.CTkFrame(self.segment_notebook)
        self.segment_notebook.add(self.timing_tab, text="Timing")
        

        self.create_basic_tab()
        self.create_colors_tab()
        self.create_timing_tab()
    
    def create_basic_tab(self):
        """
        Create controls in the basic parameters tab
        """

        pos_frame = ctk.CTkFrame(self.basic_tab)
        pos_frame.pack(fill=tk.X, padx=5, pady=5)
        
        pos_label = ctk.CTkLabel(pos_frame, text="Initial Position:")
        pos_label.pack(side=tk.LEFT, padx=5)
        
        self.pos_var = tk.StringVar(value="0")
        pos_entry = ctk.CTkEntry(pos_frame, textvariable=self.pos_var)
        pos_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        

        range_frame = ctk.CTkFrame(self.basic_tab)
        range_frame.pack(fill=tk.X, padx=5, pady=5)
        
        range_label = ctk.CTkLabel(range_frame, text="Move Range:")
        range_label.pack(side=tk.LEFT, padx=5)
        
        self.range_min_var = tk.StringVar(value="0")
        range_min_entry = ctk.CTkEntry(range_frame, textvariable=self.range_min_var, width=60)
        range_min_entry.pack(side=tk.LEFT, padx=5)
        
        range_to_label = ctk.CTkLabel(range_frame, text="to")
        range_to_label.pack(side=tk.LEFT)
        
        self.range_max_var = tk.StringVar(value="100")
        range_max_entry = ctk.CTkEntry(range_frame, textvariable=self.range_max_var, width=60)
        range_max_entry.pack(side=tk.LEFT, padx=5)
        

        speed_frame = ctk.CTkFrame(self.basic_tab)
        speed_frame.pack(fill=tk.X, padx=5, pady=5)
        
        speed_label = ctk.CTkLabel(speed_frame, text="Move Speed:")
        speed_label.pack(side=tk.LEFT, padx=5)
        
        self.speed_var = tk.StringVar(value="10")
        speed_scale = ctk.CTkSlider(
            speed_frame,
            from_=-100,
            to=100,
            variable=self.speed_var,
            number_of_steps=200
        )
        speed_scale.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        speed_value = ctk.CTkLabel(speed_frame, textvariable=self.speed_var, width=40)
        speed_value.pack(side=tk.LEFT, padx=5)
        

        reflect_frame = ctk.CTkFrame(self.basic_tab)
        reflect_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.reflect_var = tk.StringVar(value="0")
        reflect_check = ctk.CTkCheckBox(
            reflect_frame,
            text="Edge Reflection",
            variable=self.reflect_var,
            onvalue="1",
            offvalue="0"
        )
        reflect_check.pack(side=tk.LEFT, padx=5)
        

        length_frame = ctk.CTkFrame(self.basic_tab)
        length_frame.pack(fill=tk.X, padx=5, pady=5)
        
        length_label = ctk.CTkLabel(length_frame, text="Segment Length:")
        length_label.pack(side=tk.LEFT, padx=5)
        

        self.length_vars = [tk.StringVar(value="10") for _ in range(3)]
        for i, var in enumerate(self.length_vars):
            if i > 0:
                separator = ctk.CTkLabel(length_frame, text=",")
                separator.pack(side=tk.LEFT)
            
            length_entry = ctk.CTkEntry(length_frame, textvariable=var, width=40)
            length_entry.pack(side=tk.LEFT, padx=2)
        

        update_frame = ctk.CTkFrame(self.basic_tab)
        update_frame.pack(fill=tk.X, padx=5, pady=5)
        
        update_button = ctk.CTkButton(
            update_frame,
            text="Update Parameters",
            command=self.on_update_basic_params
        )
        update_button.pack(fill=tk.X, padx=5, pady=10)
    
    def create_colors_tab(self):
        """
        Create controls in the colors tab
        """

        self.color_frames = []
        self.color_buttons = []
        self.color_vars = [tk.StringVar(value="0") for _ in range(4)]
        
        color_labels = ["Color 1 (Start)", "Color 2", "Color 3", "Color 4 (End)"]
        
        for i in range(4):
            color_frame = ctk.CTkFrame(self.colors_tab)
            color_frame.pack(fill=tk.X, padx=5, pady=5)
            self.color_frames.append(color_frame)
            
            color_label = ctk.CTkLabel(color_frame, text=color_labels[i])
            color_label.pack(side=tk.LEFT, padx=5)
            

            color_combo = ctk.CTkComboBox(
                color_frame,
                values=["0: Black", "1: Red", "2: Green", "3: Blue", "4: Yellow", 
                       "5: Magenta", "6: Cyan", "7: White", "8: Orange", "9: Purple", "10: Light Blue"],
                variable=self.color_vars[i],
                command=lambda idx=i: self.on_color_selected(idx)
            )
            color_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            

            color_button = ctk.CTkButton(
                color_frame,
                text="",
                width=30,
                height=30,
                fg_color=self.get_color_preview(0),
                command=lambda idx=i: self.on_custom_color(idx)
            )
            color_button.pack(side=tk.LEFT, padx=5)
            self.color_buttons.append(color_button)
        

        self.transparency_frames = []
        self.transparency_vars = [tk.StringVar(value="0.0") for _ in range(4)]
        
        for i in range(4):
            trans_frame = ctk.CTkFrame(self.colors_tab)
            trans_frame.pack(fill=tk.X, padx=5, pady=5)
            self.transparency_frames.append(trans_frame)
            
            trans_label = ctk.CTkLabel(trans_frame, text=f"Transparency {i+1}:")
            trans_label.pack(side=tk.LEFT, padx=5)
            
            trans_slider = ctk.CTkSlider(
                trans_frame,
                from_=0.0,
                to=1.0,
                variable=self.transparency_vars[i],
                number_of_steps=100
            )
            trans_slider.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            
            trans_value = ctk.CTkLabel(trans_frame, textvariable=self.transparency_vars[i], width=40)
            trans_value.pack(side=tk.LEFT, padx=5)
        

        update_frame = ctk.CTkFrame(self.colors_tab)
        update_frame.pack(fill=tk.X, padx=5, pady=5)
        
        update_button = ctk.CTkButton(
            update_frame,
            text="Update Colors",
            command=self.on_update_colors
        )
        update_button.pack(fill=tk.X, padx=5, pady=10)
    
    def create_timing_tab(self):
        """
        Create controls in the timing tab
        """

        self.dimmer_labels = ["Fade In Start", "Fade In End", "Fade Out Start", "Fade Out End", "Cycle Time"]
        self.dimmer_vars = [tk.StringVar(value="0") for _ in range(5)]
        
        for i in range(5):
            dimmer_frame = ctk.CTkFrame(self.timing_tab)
            dimmer_frame.pack(fill=tk.X, padx=5, pady=5)
            
            dimmer_label = ctk.CTkLabel(dimmer_frame, text=f"{self.dimmer_labels[i]} (ms):")
            dimmer_label.pack(side=tk.LEFT, padx=5)
            
            dimmer_entry = ctk.CTkEntry(dimmer_frame, textvariable=self.dimmer_vars[i])
            dimmer_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        

        update_frame = ctk.CTkFrame(self.timing_tab)
        update_frame.pack(fill=tk.X, padx=5, pady=5)
        
        update_button = ctk.CTkButton(
            update_frame,
            text="Update Timing",
            command=self.on_update_timing
        )
        update_button.pack(fill=tk.X, padx=5, pady=10)
    
    def create_visualizer_panel(self):
        """
        Create the visualizer panel
        """

        self.visualizer_frame = ctk.CTkFrame(self.right_panel)
        self.visualizer_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        

        self.placeholder_label = ctk.CTkLabel(
            self.visualizer_frame, 
            text="LED Simulator Initializing...",
            font=("Helvetica", 20)
        )
        self.placeholder_label.pack(fill=tk.BOTH, expand=True)
        

        self.control_frame = ctk.CTkFrame(self.right_panel)
        self.control_frame.pack(fill=tk.X, padx=5, pady=5)
        

        self.auto_cycle_var = tk.StringVar(value="0")
        auto_cycle_check = ctk.CTkCheckBox(
            self.control_frame,
            text="Auto-cycle Presets",
            variable=self.auto_cycle_var,
            onvalue="1",
            offvalue="0",
            command=self.on_toggle_auto_cycle
        )
        auto_cycle_check.pack(side=tk.LEFT, padx=10)
        

        cycle_label = ctk.CTkLabel(self.control_frame, text="Interval (sec):")
        cycle_label.pack(side=tk.LEFT, padx=5)
        
        self.cycle_interval_var = tk.StringVar(value="5")
        cycle_entry = ctk.CTkEntry(self.control_frame, textvariable=self.cycle_interval_var, width=50)
        cycle_entry.pack(side=tk.LEFT, padx=5)
        

        spacer = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        spacer.pack(side=tk.LEFT, fill=tk.X, expand=True)
        

        self.conn_status_var = tk.StringVar(value="Not Connected")
        conn_status = ctk.CTkLabel(self.control_frame, textvariable=self.conn_status_var)
        conn_status.pack(side=tk.RIGHT, padx=10)
        
        conn_label = ctk.CTkLabel(self.control_frame, text="Status:")
        conn_label.pack(side=tk.RIGHT)
    
    def create_status_bar(self):
        """
        Create the status bar
        """
        self.status_bar = ctk.CTkFrame(self.root, height=25)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_var = tk.StringVar(value="Ready")
        status_label = ctk.CTkLabel(self.status_bar, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT, padx=10)
    
    def create_default_effect(self):
        """
        Create a default effect
        """
        effect = LightEffect(self.current_effect_id, 100, 30)
        self.effects[self.current_effect_id] = effect
        

        segment = LightSegment(
            segment_ID=self.current_segment_id,
            color=[1, 3, 4, 2],  # Red, Blue, Yellow, Green
            transparency=[0.0, 0.0, 0.0, 0.0],
            length=[30, 30, 30],
            move_speed=20,
            move_range=[0, 99],
            initial_position=0,
            is_edge_reflect=False,
            dimmer_time=[0, 500, 4500, 5000, 5000]
        )
        effect.add_segment(self.current_segment_id, segment)