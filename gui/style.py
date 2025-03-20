import tkinter as tk
from typing import Dict, Any


COLORS = {
    "primary": "#0078d4",
    "primary_dark": "#005a9e",
    "primary_light": "#2694da",
    "secondary": "#ff5722",
    "secondary_dark": "#c41c00",
    "secondary_light": "#ff8a50",

    "black": "#000000",
    "grey_900": "#212121",
    "grey_800": "#424242",
    "grey_700": "#616161",
    "grey_600": "#757575",
    "grey_500": "#9e9e9e",
    "grey_400": "#bdbdbd",
    "grey_300": "#e0e0e0",
    "grey_200": "#eeeeee",
    "grey_100": "#f5f5f5",
    "white": "#ffffff",
    
    "success": "#4caf50",
    "warning": "#ff9800",
    "error": "#f44336",
    "info": "#2196f3",
    
    "background": "#252525",
    "background_light": "#2e2e2e",
    "background_dark": "#1c1c1c",
    "text": "#ffffff",
    "text_secondary": "#b0b0b0",
    "border": "#3e3e3e",
    "hover": "#3a3a3a",
    "active": "#303030",
    
    "led_black": "#000000",
    "led_red": "#FF0000",
    "led_green": "#00FF00",
    "led_blue": "#0000FF",
    "led_yellow": "#FFFF00",
    "led_magenta": "#FF00FF",
    "led_cyan": "#00FFFF",
    "led_white": "#FFFFFF",
    "led_orange": "#FF7F00",
    "led_purple": "#7F00FF",
    "led_light_blue": "#007FFF",
}

FONTS = {
    "title": ("Helvetica", 18, "bold"),
    "subtitle": ("Helvetica", 16, "bold"),
    "header": ("Helvetica", 14, "bold"),
    "text": ("Helvetica", 12),
    "text_small": ("Helvetica", 10),
    "button": ("Helvetica", 12),
    "code": ("Courier", 12),
}

PADDING = {
    "small": 5,
    "medium": 10,
    "large": 15,
    "xlarge": 20,
}

def apply_theme_to_ttk(style: Any):
    """
    Apply custom theme to ttk widgets
    
    Args:
        style: ttk.Style instance
    """
    style.configure(
        "TButton",
        background=COLORS["primary"],
        foreground=COLORS["white"],
        font=FONTS["button"]
    )
    
    style.map(
        "TButton",
        background=[("active", COLORS["primary_dark"])],
        foreground=[("active", COLORS["white"])]
    )
    
    style.configure(
        "TLabel",
        background=COLORS["background"],
        foreground=COLORS["text"],
        font=FONTS["text"]
    )
    
    style.configure(
        "TFrame",
        background=COLORS["background"]
    )

    style.configure(
        "TNotebook",
        background=COLORS["background"],
        borderwidth=0
    )
    
    style.configure(
        "TNotebook.Tab",
        background=COLORS["background_light"],
        foreground=COLORS["text_secondary"],
        font=FONTS["text"],
        padding=[10, 5]
    )
    
    style.map(
        "TNotebook.Tab",
        background=[("selected", COLORS["primary"])],
        foreground=[("selected", COLORS["white"])]
    )

    style.configure(
        "Title.TLabel",
        font=FONTS["title"],
        foreground=COLORS["primary"]
    )
    
    style.configure(
        "Subtitle.TLabel",
        font=FONTS["subtitle"],
        foreground=COLORS["primary_light"]
    )
    
    style.configure(
        "Header.TLabel",
        font=FONTS["header"],
        foreground=COLORS["text"]
    )
    
    style.configure(
        "Success.TButton",
        background=COLORS["success"],
    )
    
    style.map(
        "Success.TButton",
        background=[("active", COLORS["success"])]
    )
    
    style.configure(
        "Warning.TButton",
        background=COLORS["warning"],
    )
    
    style.map(
        "Warning.TButton",
        background=[("active", COLORS["warning"])]
    )
    
    style.configure(
        "Error.TButton",
        background=COLORS["error"],
    )
    
    style.map(
        "Error.TButton",
        background=[("active", COLORS["error"])]
    )

def get_color_by_id(color_id: int) -> str:
    """
    Get color hex string by ID
    
    Args:
        color_id: Color ID (0-10)
        
    Returns:
        Hex color string
    """
    color_map = {
        0: COLORS["led_black"],
        1: COLORS["led_red"],
        2: COLORS["led_green"],
        3: COLORS["led_blue"],
        4: COLORS["led_yellow"],
        5: COLORS["led_magenta"],
        6: COLORS["led_cyan"],
        7: COLORS["led_white"],
        8: COLORS["led_orange"],
        9: COLORS["led_purple"],
        10: COLORS["led_light_blue"],
    }
    
    return color_map.get(color_id, COLORS["grey_500"])