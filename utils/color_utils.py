from typing import List, Tuple, Dict


COLOR_MAP = {
    0: [0, 0, 0],       # Black
    1: [255, 0, 0],     # Red
    2: [0, 255, 0],     # Green
    3: [0, 0, 255],     # Blue
    4: [255, 255, 0],   # Yellow
    5: [255, 0, 255],   # Magenta
    6: [0, 255, 255],   # Cyan
    7: [255, 255, 255], # White
    8: [255, 127, 0],   # Orange
    9: [127, 0, 255],   # Purple
    10: [0, 127, 255],  # Light blue
}


COLOR_NAMES = {
    0: "Black",
    1: "Red",
    2: "Green",
    3: "Blue",
    4: "Yellow",
    5: "Magenta",
    6: "Cyan",
    7: "White",
    8: "Orange",
    9: "Purple",
    10: "Light Blue",
}

def get_color_by_id(color_id: int) -> List[int]:
    """
    Get RGB color by ID
    
    Args:
        color_id: Color ID (0-10)
        
    Returns:
        RGB color list [r, g, b]
    """
    return COLOR_MAP.get(color_id, [0, 0, 0])

def get_color_hex(color_id: int) -> str:
    """
    Get hex color by ID
    
    Args:
        color_id: Color ID (0-10)
        
    Returns:
        Hex color string
    """
    rgb = get_color_by_id(color_id)
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

def rgb_to_hex(rgb: List[int]) -> str:
    """
    Convert RGB list to hex color
    
    Args:
        rgb: RGB color list [r, g, b]
        
    Returns:
        Hex color string
    """
    r, g, b = rgb
    return f"#{r:02x}{g:02x}{b:02x}"

def hex_to_rgb(hex_color: str) -> List[int]:
    """
    Convert hex color to RGB list
    
    Args:
        hex_color: Hex color string (with or without #)
        
    Returns:
        RGB color list [r, g, b]
    """
    hex_color = hex_color.lstrip('#')
    return [int(hex_color[i:i+2], 16) for i in range(0, 6, 2)]

def blend_colors(color1: List[int], color2: List[int], ratio: float) -> List[int]:
    """
    Blend two colors
    
    Args:
        color1: First RGB color [r, g, b]
        color2: Second RGB color [r, g, b]
        ratio: Blend ratio (0.0 = color1, 1.0 = color2)
        
    Returns:
        Blended RGB color
    """
    r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
    g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
    b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
    return [r, g, b]

def adjust_brightness(color: List[int], factor: float) -> List[int]:
    """
    Adjust color brightness
    
    Args:
        color: RGB color [r, g, b]
        factor: Brightness factor (0.0-1.0)
        
    Returns:
        Adjusted RGB color
    """
    r = min(255, int(color[0] * factor))
    g = min(255, int(color[1] * factor))
    b = min(255, int(color[2] * factor))
    return [r, g, b]

def get_all_color_options() -> List[str]:
    """
    Get formatted color options for dropdown
    
    Returns:
        List of color options in format "ID: Name"
    """
    return [f"{id}: {name}" for id, name in COLOR_NAMES.items()]

def parse_color_option(option: str) -> int:
    """
    Parse color option to get color ID
    
    Args:
        option: Color option string (e.g. "1: Red")
        
    Returns:
        Color ID
    """
    try:
        return int(option.split(':')[0])
    except (ValueError, IndexError):
        return 0