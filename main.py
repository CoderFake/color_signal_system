import sys
import time
import os
from typing import Dict, List, Any
import argparse


current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)


from config import (
    DEFAULT_FPS, DEFAULT_LED_COUNT, DEFAULT_OSC_PORT, DEFAULT_OSC_IP,
    DEFAULT_TRANSPARENCY, DEFAULT_LENGTH, DEFAULT_MOVE_SPEED,
    DEFAULT_MOVE_RANGE, DEFAULT_INITIAL_POSITION, DEFAULT_IS_EDGE_REFLECT,
    DEFAULT_DIMMER_TIME, DEFAULT_COLOR_PALETTES
)
from models.light_segment import LightSegment
from models.light_effect import LightEffect
from controllers.osc_handler import OSCHandler
from ui.led_simulator import LEDSimulator

def create_default_segments(effect: LightEffect, count: int = 3):
    """
    Create default light segments for an effect.
    
    Args:
        effect: LightEffect instance to add segments to
        count: Number of segments to create
    """
    center_position = effect.led_count // 2 

    for i in range(1, count + 1):

        segment = LightSegment(
            segment_ID=i,
            color=[i % 6, (i + 1) % 6, (i + 2) % 6, (i + 3) % 6], 
            transparency=DEFAULT_TRANSPARENCY,
            length=DEFAULT_LENGTH,
            move_speed=DEFAULT_MOVE_SPEED * (1 if i % 2 == 0 else -1),  
            move_range=[0, effect.led_count - 1], 
            initial_position=center_position - 30 + i * 30,
            is_edge_reflect=DEFAULT_IS_EDGE_REFLECT,
            dimmer_time=DEFAULT_DIMMER_TIME
        )
        

        segment.gradient = False
        segment.fade = False
        segment.gradient_colors = [0, -1, -1]

        effect.add_segment(i, segment)

def parse_arguments():
    """Parse command line arguments for the application."""
    parser = argparse.ArgumentParser(description='LED Color Signal Generator')
    parser.add_argument('--fps', type=int, default=DEFAULT_FPS, help=f'Frames per second (default: {DEFAULT_FPS})')
    parser.add_argument('--led-count', type=int, default=DEFAULT_LED_COUNT, help=f'Number of LEDs (default: {DEFAULT_LED_COUNT})')
    parser.add_argument('--osc-ip', type=str, default=DEFAULT_OSC_IP, help=f'OSC IP address (default: {DEFAULT_OSC_IP})')
    parser.add_argument('--osc-port', type=int, default=DEFAULT_OSC_PORT, help=f'OSC port (default: {DEFAULT_OSC_PORT})')
    return parser.parse_args()

def main():
    """
    Main function to initialize and run the Color Signal Generation System.
    """

    args = parse_arguments()
    
    print("Initializing Color Signal Generation System...")
    print(f"FPS: {args.fps}, LED Count: {args.led_count}, OSC: {args.osc_ip}:{args.osc_port}")
    

    light_effects: Dict[int, LightEffect] = {}
    

    for effect_id in range(1, 9): 
        effect = LightEffect(effect_ID=effect_id, led_count=args.led_count, fps=args.fps)
        create_default_segments(effect, count=3)
        light_effects[effect_id] = effect
    

    osc_handler = OSCHandler(light_effects, ip=args.osc_ip, port=args.osc_port)
    osc_handler.start_server()
    
    try:

        print("Starting LED Simulator...")
        simulator = LEDSimulator(light_effects)
        

        osc_handler.set_simulator(simulator)
        

        simulator.run()
    except KeyboardInterrupt:
        print("\nUser interrupted. Shutting down...")
    except Exception as e:
        print(f"Error in simulator: {e}")
        import traceback
        traceback.print_exc()
    finally:

        osc_handler.stop_server()
        print("System shutdown complete.")

if __name__ == "__main__":
    main()