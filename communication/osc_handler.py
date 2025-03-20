from typing import Dict, Any, List, Union, Callable
import json
import re
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer, ThreadingOSCUDPServer
import threading
from ..core.light_effect import LightEffect

class OSCHandler:
    """
    Class to handle OSC messages for controlling light effects
    """
    
    def __init__(self, light_effects: Dict[int, LightEffect], ip: str = "0.0.0.0", port: int = 7700):
        """
        Initialize the OSC handler
        
        Args:
            light_effects: Dictionary of LightEffect instances with effect_ID as key
            ip: IP address to bind the OSC server to
            port: Port to listen on
        """
        self.light_effects = light_effects
        self.ip = ip
        self.port = port
        self.server = None
        self.server_thread = None
        self.running = False
        self.callbacks = {}
        
        self.address_pattern = re.compile(r'^/effect/(\d+)/segment/(\d+)/(\w+)$')
    
    def start_server(self, threading: bool = True):
        """
        Start the OSC server
        
        Args:
            threading: If True, uses ThreadingOSCUDPServer, otherwise BlockingOSCUDPServer
        """
        if self.running:
            return
        
        dispatcher = Dispatcher()
        dispatcher.set_default_handler(self.osc_callback)
        
        if threading:
            self.server = ThreadingOSCUDPServer((self.ip, self.port), dispatcher)
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
        else:
            self.server = BlockingOSCUDPServer((self.ip, self.port), dispatcher)
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
        
        self.running = True
    
    def stop_server(self):
        """
        Stop the OSC server
        """
        if self.server and self.running:
            self.server.shutdown()
            if self.server_thread:
                self.server_thread.join(timeout=1.0)
            self.running = False
    
    def osc_callback(self, address: str, *args):
        """
        Process incoming OSC messages
        
        Args:
            address: OSC address path
            *args: Arguments from the OSC message
        """
        match = self.address_pattern.match(address)
        if match:
            effect_id = int(match.group(1))
            segment_id = int(match.group(2))
            param_name = match.group(3)
            
            value = self._convert_value(args[0]) if args else None
            
            if effect_id in self.light_effects:
                self.light_effects[effect_id].update_segment_param(segment_id, param_name, value)

                callback_key = f"{effect_id}/{segment_id}/{param_name}"
                if callback_key in self.callbacks:
                    for callback in self.callbacks[callback_key]:
                        callback(value)
        else:
            parts = address.split("/")
            if len(parts) > 1 and parts[1] == "effect":
                self._handle_custom_command(address, args)
    
    def _convert_value(self, value: Any) -> Any:
        """
        Convert OSC arguments to appropriate Python types
        
        Args:
            value: Value to convert
            
        Returns:
            Converted value
        """
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                return value
        return value
    
    def _handle_custom_command(self, address: str, args: List[Any]):
        """
        Handle custom OSC commands
        
        Args:
            address: OSC address path
            args: Arguments from the OSC message
        """
        parts = address.split("/")

        if len(parts) >= 3 and parts[1] == "effect" and parts[2] == "create":
            if len(args) >= 3:
                effect_id = int(args[0])
                led_count = int(args[1])
                fps = int(args[2])
                

                if effect_id not in self.light_effects:
                    self.light_effects[effect_id] = LightEffect(effect_id, led_count, fps)
        
        elif len(parts) >= 4 and parts[1] == "effect" and parts[3] == "clear":
            try:
                effect_id = int(parts[2])
                if effect_id in self.light_effects:
                    self.light_effects[effect_id].clear()
            except ValueError:
                pass
    
    def register_callback(self, effect_id: int, segment_id: int, param_name: str, callback: Callable[[Any], None]):
        """
        Register a callback for parameter changes
        
        Args:
            effect_id: Effect ID
            segment_id: Segment ID
            param_name: Parameter name
            callback: Function to call when parameter changes
        """
        key = f"{effect_id}/{segment_id}/{param_name}"
        if key not in self.callbacks:
            self.callbacks[key] = []
        self.callbacks[key].append(callback)
    
    def send_osc(self, client, address: str, value: Any):
        """
        Send an OSC message
        
        Args:
            client: OSC client to use
            address: OSC address path
            value: Value to send
        """
        if isinstance(value, (list, dict)):
            client.send_message(address, json.dumps(value))
        else:
            client.send_message(address, value)