import sys
import time
import os
from typing import Dict, List, Any


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
        effect: LightEffect to add segments to
        count: Number of segments to create
    """
    for i in range(1, count + 1):

        segment = LightSegment(
            segment_ID=i,
            color=[i % 7, (i + 1) % 7, (i + 2) % 7, (i + 3) % 7],
            transparency=DEFAULT_TRANSPARENCY,
            length=DEFAULT_LENGTH,
            move_speed=DEFAULT_MOVE_SPEED * (1 if i % 2 == 0 else -1),
            move_range=DEFAULT_MOVE_RANGE,
            initial_position=DEFAULT_INITIAL_POSITION + i * 20,
            is_edge_reflect=DEFAULT_IS_EDGE_REFLECT,
            dimmer_time=DEFAULT_DIMMER_TIME
        )
        

        segment.gradient_enabled = False
        segment.gradient_colors = [0, 1]
        

        segment.span_width = 100
        segment.span_range = [50, 150]
        segment.span_speed = 100
        segment.span_interval = 10
        segment.fade_enabled = False
        segment.span_gradient_enabled = False
        segment.span_gradient_colors = [0, 1, 2, 3, 4, 5] 
        
        effect.add_segment(i, segment)

def main():
    """
    Main function to initialize and run the Color Signal Generation System.
    """
    print("Initializing Color Signal Generation System...")
    

    light_effects: Dict[int, LightEffect] = {}
    

    for effect_id in range(1, 9): 
        effect = LightEffect(effect_ID=effect_id, led_count=DEFAULT_LED_COUNT, fps=DEFAULT_FPS)
        create_default_segments(effect, count=3)
        light_effects[effect_id] = effect
    

    osc_handler = OSCHandler(light_effects, ip=DEFAULT_OSC_IP, port=DEFAULT_OSC_PORT)
    osc_handler.start_server()
    
    try:

        simulator = LEDSimulator(light_effects)
        simulator.run()
    except Exception as e:
        print(f"Error in simulator: {e}")
        import traceback
        traceback.print_exc()
    finally:

        osc_handler.stop_server()
        print("System shutdown complete.")

if __name__ == "__main__":
    main()