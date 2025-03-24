from typing import Dict, List, Any
import re
import sys
from pythonosc import dispatcher, osc_server, udp_client
import threading

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
        

        self.dispatcher = dispatcher.Dispatcher()
        self.setup_dispatcher()
        

        self.server = None
        self.server_thread = None
    
    def setup_dispatcher(self):
        """
        Set up the OSC message dispatcher with the necessary message handlers.
        """

        self.dispatcher.map("/effect/*/object/*/*", self.osc_callback)
        

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
            
    def osc_callback(self, address, *args):
        """
        Process incoming OSC messages for effect/object updates.
        
        Args:
            address: OSC address pattern
            *args: OSC message arguments
        """


        pattern = r"/effect/(\d+)/object/(\d+)/(.+)"
        match = re.match(pattern, address)
        
        if not match:
            print(f"Invalid address pattern: {address}")
            return
            
        effect_id = int(match.group(1))
        object_id = int(match.group(2))  # object_id thay vì segment_id theo specs
        param_name = match.group(3)
        value = args[0]
        

        if effect_id in self.light_effects:

            self.light_effects[effect_id].update_segment_param(object_id, param_name, value)
            print(f"Updated effect {effect_id}, object {object_id}, param {param_name} = {value}")
        else:
            print(f"Effect {effect_id} not found")
    
    def palette_callback(self, address, *args):
        """
        Process incoming OSC messages for palette updates.
        
        Args:
            address: OSC address pattern
            *args: OSC message arguments
        """

        pattern = r"/palette/([A-E])"
        match = re.match(pattern, address)
        
        if not match:
            print(f"Invalid palette address: {address}")
            return
            
        palette_name = match.group(1)
        colors = args[0]
        

        if len(colors) % 3 != 0:
            print(f"Invalid color data length: {len(colors)}")
            return
            

        rgb_colors = []
        for i in range(0, len(colors), 3):
            rgb = colors[i:i+3]
            rgb_colors.append([int(rgb[0]), int(rgb[1]), int(rgb[2])])
        

        print(f"Updated palette {palette_name} with {len(rgb_colors)} colors")
        


        
    def init_callback(self, address, *args):
        """
        Process initialization request messages.
        Sends back the current state of all effects and segments.
        
        Args:
            address: OSC address pattern
            *args: OSC message arguments
        """
        print("Received initialization request")
        

        client = udp_client.SimpleUDPClient(self.ip, self.port)
        

        for palette_name, colors in DEFAULT_COLOR_PALETTES.items():

            flat_colors = []
            for color in colors:
                flat_colors.extend(color)
            
            client.send_message(f"/palette/{palette_name}", flat_colors)
        

        for effect_id, effect in self.light_effects.items():
            for segment_id, segment in effect.segments.items():

                client.send_message(f"/effect/{effect_id}/object/{segment_id}/color", segment.color)
                client.send_message(f"/effect/{effect_id}/object/{segment_id}/transparency", segment.transparency)
                client.send_message(f"/effect/{effect_id}/object/{segment_id}/length", segment.length)
                client.send_message(f"/effect/{effect_id}/object/{segment_id}/move_speed", segment.move_speed)
                client.send_message(f"/effect/{effect_id}/object/{segment_id}/move_range", segment.move_range)
                client.send_message(f"/effect/{effect_id}/object/{segment_id}/initial_position", segment.initial_position)
                client.send_message(f"/effect/{effect_id}/object/{segment_id}/is_edge_reflect", int(segment.is_edge_reflect))
                client.send_message(f"/effect/{effect_id}/object/{segment_id}/dimmer_time", segment.dimmer_time)
                

                if hasattr(segment, 'gradient_enabled'):
                    client.send_message(f"/effect/{effect_id}/object/{segment_id}/gradient", int(segment.gradient_enabled))
                
                if hasattr(segment, 'gradient_colors'):
                    client.send_message(f"/effect/{effect_id}/object/{segment_id}/gradient_colors", segment.gradient_colors)
                
                if hasattr(segment, 'interval'):
                    client.send_message(f"/effect/{effect_id}/object/{segment_id}/interval", segment.interval)
                

                if hasattr(segment, 'span_width'):
                    client.send_message(f"/effect/{effect_id}/object/{segment_id}/span", segment.span_width)
                
                if hasattr(segment, 'span_range'):
                    client.send_message(f"/effect/{effect_id}/object/{segment_id}/span/range", segment.span_range)
                
                if hasattr(segment, 'span_speed'):
                    client.send_message(f"/effect/{effect_id}/object/{segment_id}/span/speed", segment.span_speed)
                
                if hasattr(segment, 'span_interval'):
                    client.send_message(f"/effect/{effect_id}/object/{segment_id}/span/interval", segment.span_interval)
                
                if hasattr(segment, 'fade_enabled'):
                    client.send_message(f"/effect/{effect_id}/object/{segment_id}/span/fade", int(segment.fade_enabled))
                
                if hasattr(segment, 'span_gradient_enabled'):
                    client.send_message(f"/effect/{effect_id}/object/{segment_id}/span/gradient_colors", 
                                       [int(segment.span_gradient_enabled)] + segment.span_gradient_colors)
                
        print("Sent initialization data")