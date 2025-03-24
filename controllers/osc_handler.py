from typing import Dict, List, Any
import re
import sys
import threading
from pythonosc import dispatcher, osc_server, udp_client

sys.path.append('..')
from models.light_effect import LightEffect
from config import DEFAULT_COLOR_PALETTES

class OSCHandler:
    """
    Handler for OSC (Open Sound Control) messages.
    Processes incoming OSC messages and updates LightEffect and LightSegment instances.
    """
    
    def __init__(self, light_effects: Dict[int, LightEffect], ip: str = "127.0.0.1", port: int = 5005):
        """
        Initialize the OSC handler.
        
        Args:
            light_effects: Dictionary mapping effect_ID to LightEffect instances
            ip: IP address to listen on
            port: Port to listen on
        """
        self.light_effects = light_effects
        self.ip = ip
        self.port = port
        self.color_palettes = DEFAULT_COLOR_PALETTES.copy()
        

        self.dispatcher = dispatcher.Dispatcher()
        self.setup_dispatcher()
        

        self.server = None
        self.server_thread = None
        

        self.client = udp_client.SimpleUDPClient(ip, port)
    
    def setup_dispatcher(self):
        """
        Set up the OSC message dispatcher with the necessary message handlers.
        """


        self.dispatcher.map("/effect/*/segment/*/*", self.effect_segment_callback)
        


        self.dispatcher.map("/palette/*", self.palette_callback)
        


        self.dispatcher.map("/request/init", self.init_callback)
    
    def start_server(self):
        """
        Start the OSC server in a separate thread.
        """
        try:
            self.server = osc_server.ThreadingOSCUDPServer((self.ip, self.port), self.dispatcher)
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            print(f"OSC server started on {self.ip}:{self.port}")
        except Exception as e:
            print(f"Error starting OSC server: {e}")
            
    def stop_server(self):
        """
        Stop the OSC server.
        """
        if self.server:
            self.server.shutdown()
            print("OSC server stopped")
            
    def effect_segment_callback(self, address, *args):
        """
        Process messages for effect/segment updates.
        
        Args:
            address: OSC address pattern
            *args: OSC message arguments
        """

        pattern = r"/effect/(\d+)/segment/(\d+)/(.+)"
        match = re.match(pattern, address)
        
        if not match:
            print(f"Invalid address pattern: {address}")
            return
            
        effect_id = int(match.group(1))
        segment_id = int(match.group(2))
        param_name = match.group(3)
        value = args[0]
        


        if param_name == "color" and isinstance(value, list):

            if effect_id in self.light_effects and segment_id in self.light_effects[effect_id].segments:
                self.light_effects[effect_id].update_segment_param(segment_id, "color", value)
                print(f"Updated effect {effect_id}, segment {segment_id}, colors = {value}")
        

        elif param_name == "position":
            if isinstance(value, dict) and "initial_position" in value:
                if effect_id in self.light_effects and segment_id in self.light_effects[effect_id].segments:
                    self.light_effects[effect_id].update_segment_param(segment_id, "initial_position", value["initial_position"])
                    self.light_effects[effect_id].update_segment_param(segment_id, "current_position", value["initial_position"])
                    print(f"Updated effect {effect_id}, segment {segment_id}, initial_position = {value['initial_position']}")
            
            if isinstance(value, dict) and "speed" in value:
                if effect_id in self.light_effects and segment_id in self.light_effects[effect_id].segments:
                    self.light_effects[effect_id].update_segment_param(segment_id, "move_speed", value["speed"])
                    print(f"Updated effect {effect_id}, segment {segment_id}, move_speed = {value['speed']}")
                    
            if isinstance(value, dict) and "range" in value and isinstance(value["range"], list) and len(value["range"]) == 2:
                if effect_id in self.light_effects and segment_id in self.light_effects[effect_id].segments:
                    self.light_effects[effect_id].update_segment_param(segment_id, "move_range", value["range"])
                    print(f"Updated effect {effect_id}, segment {segment_id}, move_range = {value['range']}")
        

        else:
            if effect_id in self.light_effects and segment_id in self.light_effects[effect_id].segments:
                self.light_effects[effect_id].update_segment_param(segment_id, param_name, value)
                print(f"Updated effect {effect_id}, segment {segment_id}, {param_name} = {value}")
    
    def palette_callback(self, address, *args):
        """
        Process messages for palette updates.
        
        Args:
            address: OSC address pattern (e.g. "/palette/A")
            *args: OSC message arguments (array of color values)
        """

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
    
    def init_callback(self, address, *args):
        """
        Process initialization request messages.
        Sends the current state of all effects and segments.
        
        Args:
            address: OSC address pattern
            *args: OSC message arguments
        """
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
                        "gradient": 0  # Default to no gradient
                    }
                )
                

                self.client.send_message(
                    f"/effect/{effect_id}/segment/{segment_id}/position",
                    {
                        "initial_position": segment.initial_position,
                        "speed": segment.move_speed,
                        "range": segment.move_range,
                        "interval": 10  # Default interval
                    }
                )
                

                self.client.send_message(
                    f"/effect/{effect_id}/segment/{segment_id}/transparency", 
                    segment.transparency
                )
                
        print("Sent initialization data")