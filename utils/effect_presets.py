from typing import Dict, Any, List


PRESET_EFFECTS = {
    "Rainbow Flow": {
        "color": [1, 3, 4, 2],  # Red, Blue, Yellow, Green
        "transparency": [0.0, 0.0, 0.0, 0.0],
        "length": [30, 30, 30],
        "move_speed": 20.0,
        "is_edge_reflect": False,
        "dimmer_time": [0, 500, 4500, 5000, 5000]
    },
    "Breathing": {
        "color": [7, 7, 7, 7],  # All White
        "transparency": [0.0, 0.0, 0.0, 0.0],
        "length": [1, 1, 1],
        "move_speed": 0.0,
        "is_edge_reflect": False,
        "dimmer_time": [0, 2000, 2000, 4000, 4000]
    },
    "Police Lights": {
        "color": [1, 3, 1, 3],  # Red, Blue alternating
        "transparency": [0.0, 0.0, 0.0, 0.0],
        "length": [20, 20, 20],
        "move_speed": 100.0,
        "is_edge_reflect": False,
        "dimmer_time": [0, 100, 100, 200, 200]
    },
    "Color Wipe": {
        "color": [0, 5, 0, 5],  # Black, Magenta alternating
        "transparency": [0.0, 0.0, 0.0, 0.0],
        "length": [50, 50, 50],
        "move_speed": 50.0,
        "is_edge_reflect": False,
        "dimmer_time": [0, 0, 0, 0, 1000]
    },
    "Pulse": {
        "color": [8, 8, 8, 8],  # All Orange
        "transparency": [0.0, 0.0, 0.0, 0.0],
        "length": [10, 10, 10],
        "move_speed": 0.0,
        "is_edge_reflect": False,
        "dimmer_time": [0, 500, 500, 1000, 1000]
    },
    "Cylon": {
        "color": [1, 1, 1, 1],  # All Red
        "transparency": [0.5, 0.0, 0.0, 0.5],
        "length": [10, 5, 10],
        "move_speed": 30.0,
        "is_edge_reflect": True,
        "dimmer_time": [0, 0, 0, 0, 1000]
    },
    "Rainbow Cycle": {
        "color": [1, 3, 5, 8],  # Red, Blue, Magenta, Orange
        "transparency": [0.0, 0.0, 0.0, 0.0],
        "length": [33, 33, 33],
        "move_speed": 10.0,
        "is_edge_reflect": False,
        "dimmer_time": [0, 500, 4500, 5000, 5000]
    },
    "Sparkle": {
        "color": [7, 0, 7, 0],  # White and Black
        "transparency": [0.0, 0.5, 0.0, 0.5],
        "length": [1, 10, 1],
        "move_speed": 150.0,
        "is_edge_reflect": False,
        "dimmer_time": [0, 50, 50, 100, 100]
    },
    "Fire": {
        "color": [1, 8, 8, 1],  # Red, Orange
        "transparency": [0.3, 0.0, 0.0, 0.3],
        "length": [20, 20, 20],
        "move_speed": 15.0,
        "is_edge_reflect": False,
        "dimmer_time": [0, 200, 300, 500, 500]
    },
    "Ocean Waves": {
        "color": [3, 6, 3, 6],  # Blue, Cyan
        "transparency": [0.2, 0.0, 0.2, 0.0],
        "length": [40, 40, 40],
        "move_speed": 8.0,
        "is_edge_reflect": False,
        "dimmer_time": [0, 1000, 1000, 2000, 2000]
    }
}

def get_preset_names() -> List[str]:
    """
    Get list of available preset names
    
    Returns:
        List of preset names
    """
    return list(PRESET_EFFECTS.keys())

def get_preset_params(preset_name: str) -> Dict[str, Any]:
    """
    Get parameters for a specific preset
    
    Args:
        preset_name: Name of the preset
        
    Returns:
        Dictionary of preset parameters or empty dict if not found
    """
    return PRESET_EFFECTS.get(preset_name, {})