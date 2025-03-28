from typing import Dict, List, Any
import re
import sys
import threading
from pythonosc import dispatcher, osc_server, udp_client

sys.path.append('..')
from models.light_effect import LightEffect
from config import DEFAULT_COLOR_PALETTES

class OSCHandler:
    def __init__(self, light_effects: Dict[int, LightEffect], ip: str = "127.0.0.1", port: int = 5005):
        self.light_effects = light_effects
        self.ip = ip
        self.port = port
        self.color_palettes = DEFAULT_COLOR_PALETTES.copy()
        
        self.dispatcher = dispatcher.Dispatcher()
        self.setup_dispatcher()
        
        self.server = None
        self.server_thread = None
        
        self.client = udp_client.SimpleUDPClient(ip, port)
        
        self.simulator = None
    
    def setup_dispatcher(self):
        self.dispatcher.map("/effect/*/segment/*/*", self.effect_segment_callback)
        self.dispatcher.map("/effect/*/object/*/*", self.effect_object_callback)
        self.dispatcher.map("/palette/*", self.palette_callback)
        self.dispatcher.map("/request/init", self.init_callback)
    
    def start_server(self):
        try:
            self.server = osc_server.ThreadingOSCUDPServer((self.ip, self.port), self.dispatcher)
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            print(f"OSC server started on {self.ip}:{self.port}")
        except Exception as e:
            print(f"Error starting OSC server: {e}")
            
    def stop_server(self):
        if self.server:
            self.server.shutdown()
            print("OSC server stopped")

    def set_simulator(self, simulator):
        self.simulator = simulator

    def effect_segment_callback(self, address, *args):
        pattern = r"/effect/(\d+)/segment/(\d+)/(.+)"
        match = re.match(pattern, address)
        
        if not match:
            print(f"Invalid address pattern: {address}")
            return
            
        effect_id = int(match.group(1))
        segment_id = int(match.group(2))
        param_name = match.group(3)
        value = args[0]
        
        if effect_id not in self.light_effects or segment_id not in self.light_effects[effect_id].segments:
            print(f"Effect {effect_id} or segment {segment_id} not found")
            return
        
        segment = self.light_effects[effect_id].segments[segment_id]
        ui_updated = False

        if param_name == "color":
            if isinstance(value, dict):
                if "colors" in value:
                    segment.update_param("color", value["colors"])
                    print(f"Updated colors: {value['colors']}")
                    ui_updated = True
                    
                if "speed" in value:
                    segment.update_param("move_speed", value["speed"])
                    print(f"Updated speed: {value['speed']}")
                    ui_updated = True
                    
                if "gradient" in value:
                    segment.update_param("gradient", value["gradient"] == 1)
                    print(f"Updated gradient: {value['gradient']}")
                    ui_updated = True
                    
            elif isinstance(value, list) and len(value) >= 1:
                segment.update_param("color", value)
                print(f"Updated colors directly: {value}")
                ui_updated = True

        elif param_name == "position":
            if isinstance(value, dict):
                if "initial_position" in value:
                    segment.update_param("initial_position", value["initial_position"])
                    segment.update_param("current_position", float(value["initial_position"]))
                    print(f"Updated position: {value['initial_position']}")
                    ui_updated = True
                    
                if "speed" in value:
                    segment.update_param("move_speed", value["speed"])
                    print(f"Updated speed: {value['speed']}")
                    ui_updated = True
                    
                if "range" in value and isinstance(value["range"], list) and len(value["range"]) == 2:
                    segment.update_param("move_range", value["range"])
                    print(f"Updated range: {value['range']}")
                    ui_updated = True
                    
                if "interval" in value:
                    segment.update_param("position_interval", value["interval"])
                    print(f"Updated interval: {value['interval']}")
                    ui_updated = True

        elif param_name == "span":
            if isinstance(value, dict):
                if "span" in value:
                    new_length = [value["span"]//3, value["span"]//3, value["span"]//3]
                    segment.update_param("length", new_length)
                    print(f"Updated span length: {new_length}")
                    ui_updated = True
                    
                if "range" in value and isinstance(value["range"], list) and len(value["range"]) == 2:
                    segment.update_param("span_range", value["range"])
                    print(f"Updated span range: {value['range']}")
                    ui_updated = True
                    
                if "speed" in value:
                    segment.update_param("span_speed", value["speed"])
                    print(f"Updated span speed: {value['speed']}")
                    ui_updated = True
                    
                if "interval" in value:
                    segment.update_param("span_interval", value["interval"])
                    print(f"Updated span interval: {value['interval']}")
                    ui_updated = True
                    
                if "gradient_colors" in value and isinstance(value["gradient_colors"], list):
                    segment.update_param("gradient_colors", value["gradient_colors"])
                    print(f"Updated gradient colors: {value['gradient_colors']}")
                    ui_updated = True
                    
                if "fade" in value:
                    segment.update_param("fade", value["fade"] == 1)
                    print(f"Updated fade: {value['fade']}")
                    ui_updated = True

        else:
            segment.update_param(param_name, value)
            print(f"Updated {param_name}: {value}")
            ui_updated = True
            
        if ui_updated and self.simulator:
            if hasattr(self.simulator, 'active_effect_id'):
                self.simulator.active_effect_id = effect_id
            if hasattr(self.simulator, 'active_segment_id'):
                self.simulator.active_segment_id = segment_id
            if hasattr(self.simulator, 'ui_dirty'):
                self.simulator.ui_dirty = True

    def effect_object_callback(self, address, *args):
        # iOS app may use 'object' instead of 'segment'
        pattern = r"/effect/(\d+)/object/(\d+)/(.+)"
        match = re.match(pattern, address)
        
        if not match:
            print(f"Invalid address pattern: {address}")
            return
            
        effect_id = int(match.group(1))
        segment_id = int(match.group(2))  # Treat object_ID as segment_ID
        param_name = match.group(3)
        value = args[0]
        
        if effect_id not in self.light_effects:
            print(f"Effect {effect_id} not found, creating it")
            from config import DEFAULT_LED_COUNT, DEFAULT_FPS
            self.light_effects[effect_id] = LightEffect(effect_ID=effect_id, led_count=DEFAULT_LED_COUNT, fps=DEFAULT_FPS)
            
        if segment_id not in self.light_effects[effect_id].segments:
            print(f"Segment {segment_id} not found, creating it")
            from config import (
                DEFAULT_TRANSPARENCY, DEFAULT_LENGTH, DEFAULT_MOVE_SPEED,
                DEFAULT_MOVE_RANGE, DEFAULT_INITIAL_POSITION, DEFAULT_IS_EDGE_REFLECT,
                DEFAULT_DIMMER_TIME
            )
            new_segment = LightSegment(
                segment_ID=segment_id,
                color=[0, 1, 2, 3],  # Default colors
                transparency=DEFAULT_TRANSPARENCY,
                length=DEFAULT_LENGTH,
                move_speed=DEFAULT_MOVE_SPEED,
                move_range=DEFAULT_MOVE_RANGE,
                initial_position=DEFAULT_INITIAL_POSITION,
                is_edge_reflect=DEFAULT_IS_EDGE_REFLECT,
                dimmer_time=DEFAULT_DIMMER_TIME
            )
            self.light_effects[effect_id].add_segment(segment_id, new_segment)
        
        segment = self.light_effects[effect_id].segments[segment_id]
        ui_updated = False

        if param_name == "color":
            if isinstance(value, dict):
                if "colors" in value:
                    segment.update_param("color", value["colors"])
                    print(f"Updated colors: {value['colors']}")
                    ui_updated = True
                    
                if "speed" in value:
                    segment.update_param("move_speed", value["speed"])
                    print(f"Updated speed: {value['speed']}")
                    ui_updated = True
                    
                if "gradient" in value:
                    segment.update_param("gradient", value["gradient"] == 1)
                    print(f"Updated gradient: {value['gradient']}")
                    ui_updated = True
            
            elif isinstance(value, list) and len(value) >= 1:
                segment.update_param("color", value)
                print(f"Updated colors directly: {value}")
                ui_updated = True

        elif param_name == "position":
            if isinstance(value, dict):
                if "initial_position" in value:
                    segment.update_param("initial_position", value["initial_position"])
                    segment.update_param("current_position", float(value["initial_position"]))
                    print(f"Updated position: {value['initial_position']}")
                    ui_updated = True
                    
                if "speed" in value:
                    segment.update_param("move_speed", value["speed"])
                    print(f"Updated speed: {value['speed']}")
                    ui_updated = True
                    
                if "range" in value and isinstance(value["range"], list) and len(value["range"]) == 2:
                    segment.update_param("move_range", value["range"])
                    print(f"Updated range: {value['range']}")
                    ui_updated = True
                    
                if "interval" in value:
                    segment.update_param("position_interval", value["interval"])
                    print(f"Updated interval: {value['interval']}")
                    ui_updated = True

        elif param_name == "span":
            if isinstance(value, dict):
                if "span" in value:
                    new_length = [value["span"]//3, value["span"]//3, value["span"]//3]
                    segment.update_param("length", new_length)
                    print(f"Updated span length: {new_length}")
                    ui_updated = True
                    
                if "range" in value and isinstance(value["range"], list) and len(value["range"]) == 2:
                    segment.update_param("span_range", value["range"])
                    print(f"Updated span range: {value['range']}")
                    ui_updated = True
                    
                if "speed" in value:
                    segment.update_param("span_speed", value["speed"])
                    print(f"Updated span speed: {value['speed']}")
                    ui_updated = True
                    
                if "interval" in value:
                    segment.update_param("span_interval", value["interval"])
                    print(f"Updated span interval: {value['interval']}")
                    ui_updated = True
                    
                if "gradient_colors" in value and isinstance(value["gradient_colors"], list):
                    segment.update_param("gradient_colors", value["gradient_colors"])
                    print(f"Updated gradient colors: {value['gradient_colors']}")
                    ui_updated = True
                    
                if "fade" in value:
                    segment.update_param("fade", value["fade"] == 1)
                    print(f"Updated fade: {value['fade']}")
                    ui_updated = True

        else:
            segment.update_param(param_name, value)
            print(f"Updated {param_name}: {value}")
            ui_updated = True
            
        if ui_updated and self.simulator:
            if hasattr(self.simulator, 'active_effect_id'):
                self.simulator.active_effect_id = effect_id
            if hasattr(self.simulator, 'active_segment_id'):
                self.simulator.active_segment_id = segment_id
            if hasattr(self.simulator, 'ui_dirty'):
                self.simulator.ui_dirty = True

    def palette_callback(self, address, *args):
        pattern = r"/palette/([A-E])"
        match = re.match(pattern, address)
        
        if not match:
            print(f"Invalid palette address: {address}")
            return
            
        palette_id = match.group(1)
        colors_flat = args[0]
        
        if not isinstance(colors_flat, list) or len(colors_flat) % 3 != 0:
            print(f"Invalid color data for palette {palette_id}: {colors_flat}")
            return
        
        colors = []
        for i in range(0, len(colors_flat), 3):
            r = max(0, min(255, int(colors_flat[i])))
            g = max(0, min(255, int(colors_flat[i+1])))
            b = max(0, min(255, int(colors_flat[i+2])))
            colors.append([r, g, b])
        
        self.color_palettes[palette_id] = colors
        
        for effect in self.light_effects.values():
            effect.current_palette = palette_id
            
        print(f"Updated palette {palette_id} with {len(colors)} colors")
        
        if self.simulator:
            if hasattr(self.simulator, 'current_palette'):
                self.simulator.current_palette = palette_id
            if hasattr(self.simulator, 'palettes'):
                self.simulator.palettes[palette_id] = colors
            
            if hasattr(self.simulator, '_build_ui'):
                self.simulator._build_ui()
            elif hasattr(self.simulator, 'ui_dirty'):
                self.simulator.ui_dirty = True
    
    def init_callback(self, address, *args):
        if address != "/request/init" or args[0] != 1:
            return
            
        print("Received initialization request")
        
        for palette_id, colors in self.color_palettes.items():
            flat_colors = []
            for color in colors:
                flat_colors.extend(color)
            self.client.send_message(f"/palette/{palette_id}", flat_colors)
        
        for effect_id, effect in self.light_effects.items():
            for segment_id, segment in effect.segments.items():
                self.client.send_message(
                    f"/effect/{effect_id}/segment/{segment_id}/color", 
                    {
                        "colors": segment.color,
                        "speed": segment.move_speed,
                        "gradient": 1 if segment.gradient else 0
                    }
                )
                
                self.client.send_message(
                    f"/effect/{effect_id}/segment/{segment_id}/position",
                    {
                        "initial_position": segment.initial_position,
                        "speed": segment.move_speed,
                        "range": segment.move_range,
                        "interval": getattr(segment, 'position_interval', 10)
                    }
                )
                
                self.client.send_message(
                    f"/effect/{effect_id}/segment/{segment_id}/span",
                    {
                        "span": sum(segment.length),
                        "range": getattr(segment, 'span_range', segment.move_range), 
                        "speed": getattr(segment, 'span_speed', segment.move_speed),
                        "interval": getattr(segment, 'span_interval', 10),
                        "gradient_colors": segment.gradient_colors if hasattr(segment, "gradient_colors") else [0, -1, -1],
                        "fade": 1 if segment.fade else 0
                    }
                )
                
                self.client.send_message(
                    f"/effect/{effect_id}/segment/{segment_id}/transparency", 
                    segment.transparency
                )

                self.client.send_message(
                    f"/effect/{effect_id}/object/{segment_id}/color", 
                    {
                        "colors": segment.color,
                        "speed": segment.move_speed,
                        "gradient": 1 if segment.gradient else 0
                    }
                )
                
                self.client.send_message(
                    f"/effect/{effect_id}/object/{segment_id}/position",
                    {
                        "initial_position": segment.initial_position,
                        "speed": segment.move_speed,
                        "range": segment.move_range,
                        "interval": getattr(segment, 'position_interval', 10)
                    }
                )
                
                self.client.send_message(
                    f"/effect/{effect_id}/object/{segment_id}/span",
                    {
                        "span": sum(segment.length),
                        "range": getattr(segment, 'span_range', segment.move_range), 
                        "speed": getattr(segment, 'span_speed', segment.move_speed),
                        "interval": getattr(segment, 'span_interval', 10),
                        "gradient_colors": segment.gradient_colors if hasattr(segment, "gradient_colors") else [0, -1, -1],
                        "fade": 1 if segment.fade else 0
                    }
                )
                
        print("Sent initialization data")