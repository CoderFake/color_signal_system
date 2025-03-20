import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from typing import Dict, Any, List, Tuple, Optional

# Define main color scheme
COLORS = {
    # Primary colors
    "primary": "#1E88E5",       # Blue
    "primary_dark": "#1565C0",  # Dark Blue
    "primary_light": "#42A5F5", # Light Blue
    
    # Secondary colors
    "secondary": "#FF5722",     # Orange
    "secondary_dark": "#E64A19",
    "secondary_light": "#FF8A65",
    
    # Background colors
    "bg_dark": "#121212",       # Dark background
    "bg_medium": "#1E1E1E",     # Medium background
    "bg_light": "#2A2A2A",      # Light background
    
    # Text colors
    "text": "#FFFFFF",          # White text
    "text_secondary": "#B0B0B0", # Gray text
    "text_disabled": "#666666",  # Disabled text
    
    # Accent colors
    "accent_green": "#4CAF50",   # Success
    "accent_yellow": "#FFC107",  # Warning
    "accent_red": "#F44336",     # Error
    "accent_purple": "#9C27B0",  # Info
    
    # Other UI colors
    "border": "#333333",
    "divider": "#444444",
    "hover": "#3A3A3A",
    "pressed": "#252525",
    "card": "#2C2C2C",
    
    # LED color map
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

# Font configuration
FONTS = {
    "heading1": ("Helvetica", 24, "bold"),
    "heading2": ("Helvetica", 20, "bold"),
    "heading3": ("Helvetica", 16, "bold"),
    "body": ("Helvetica", 12),
    "body_bold": ("Helvetica", 12, "bold"),
    "small": ("Helvetica", 10),
    "button": ("Helvetica", 12),
    "code": ("Courier", 12),
}

# UI metrics
METRICS = {
    "padding_small": 5,
    "padding_medium": 10,
    "padding_large": 15,
    "border_radius": 8,
    "icon_size": 20,
    "button_height": 32,
}

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

def apply_dark_theme():
    """
    Apply dark theme to customtkinter
    """
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    ctk.ThemeManager.theme["CTkButton"]["fg_color"] = (COLORS["primary"], COLORS["primary"])
    ctk.ThemeManager.theme["CTkButton"]["hover_color"] = (COLORS["primary_dark"], COLORS["primary_dark"])
    ctk.ThemeManager.theme["CTkButton"]["border_color"] = (COLORS["border"], COLORS["border"])
    ctk.ThemeManager.theme["CTkButton"]["text_color"] = (COLORS["text"], COLORS["text"])
    
    ctk.ThemeManager.theme["CTkFrame"]["fg_color"] = (COLORS["bg_medium"], COLORS["bg_medium"])
    ctk.ThemeManager.theme["CTkFrame"]["border_color"] = (COLORS["border"], COLORS["border"])
    
    ctk.ThemeManager.theme["CTkLabel"]["text_color"] = (COLORS["text"], COLORS["text"])
    ctk.ThemeManager.theme["CTkLabel"]["fg_color"] = ("transparent", "transparent")
    
    ctk.ThemeManager.theme["CTkEntry"]["fg_color"] = (COLORS["bg_light"], COLORS["bg_light"])
    ctk.ThemeManager.theme["CTkEntry"]["border_color"] = (COLORS["border"], COLORS["border"])
    ctk.ThemeManager.theme["CTkEntry"]["text_color"] = (COLORS["text"], COLORS["text"])
    
    ctk.ThemeManager.theme["CTkCheckBox"]["fg_color"] = (COLORS["primary"], COLORS["primary"])
    ctk.ThemeManager.theme["CTkCheckBox"]["border_color"] = (COLORS["border"], COLORS["border"])
    ctk.ThemeManager.theme["CTkCheckBox"]["hover_color"] = (COLORS["primary_dark"], COLORS["primary_dark"])
    ctk.ThemeManager.theme["CTkCheckBox"]["text_color"] = (COLORS["text"], COLORS["text"])
    
    ctk.ThemeManager.theme["CTkSwitch"]["fg_color"] = (COLORS["bg_light"], COLORS["bg_light"])
    ctk.ThemeManager.theme["CTkSwitch"]["progress_color"] = (COLORS["primary"], COLORS["primary"])
    ctk.ThemeManager.theme["CTkSwitch"]["button_color"] = (COLORS["text"], COLORS["text"])
    ctk.ThemeManager.theme["CTkSwitch"]["button_hover_color"] = (COLORS["text_secondary"], COLORS["text_secondary"])
    
    ctk.ThemeManager.theme["CTkSlider"]["fg_color"] = (COLORS["bg_light"], COLORS["bg_light"])
    ctk.ThemeManager.theme["CTkSlider"]["progress_color"] = (COLORS["primary"], COLORS["primary"])
    ctk.ThemeManager.theme["CTkSlider"]["button_color"] = (COLORS["primary"], COLORS["primary"])
    ctk.ThemeManager.theme["CTkSlider"]["button_hover_color"] = (COLORS["primary_dark"], COLORS["primary_dark"])
    
    ctk.ThemeManager.theme["CTkComboBox"]["fg_color"] = (COLORS["bg_light"], COLORS["bg_light"])
    ctk.ThemeManager.theme["CTkComboBox"]["border_color"] = (COLORS["border"], COLORS["border"])
    ctk.ThemeManager.theme["CTkComboBox"]["button_color"] = (COLORS["primary"], COLORS["primary"])
    ctk.ThemeManager.theme["CTkComboBox"]["button_hover_color"] = (COLORS["primary_dark"], COLORS["primary_dark"])
    ctk.ThemeManager.theme["CTkComboBox"]["text_color"] = (COLORS["text"], COLORS["text"])
    ctk.ThemeManager.theme["CTkComboBox"]["dropdown_hover"] = (COLORS["hover"], COLORS["hover"])
    
    ctk.ThemeManager.theme["CTkScrollbar"]["fg_color"] = ("transparent", "transparent")
    ctk.ThemeManager.theme["CTkScrollbar"]["button_color"] = (COLORS["bg_light"], COLORS["bg_light"])
    ctk.ThemeManager.theme["CTkScrollbar"]["button_hover_color"] = (COLORS["primary"], COLORS["primary"])

def configure_ttk_style(style: ttk.Style):
    """
    Configure ttk styles for widgets not covered by customtkinter
    
    Args:
        style: ttk.Style instance
    """
    style.configure("TNotebook", background=COLORS["bg_dark"], borderwidth=0)
    style.configure("TNotebook.Tab", background=COLORS["bg_medium"], foreground=COLORS["text_secondary"], padding=[10, 5], font=FONTS["body"])
    style.map("TNotebook.Tab", background=[("selected", COLORS["primary"])], foreground=[("selected", COLORS["text"])])
    
    style.configure("TFrame", background=COLORS["bg_medium"])
    style.configure("TLabel", background=COLORS["bg_medium"], foreground=COLORS["text"], font=FONTS["body"])
    style.configure("TButton", background=COLORS["primary"], foreground=COLORS["text"], font=FONTS["button"])
    style.map("TButton", background=[("active", COLORS["primary_dark"])])
    
    style.configure("Title.TLabel", font=FONTS["heading1"], foreground=COLORS["primary"])
    style.configure("Subtitle.TLabel", font=FONTS["heading2"], foreground=COLORS["primary_light"])
    style.configure("Heading.TLabel", font=FONTS["heading3"], foreground=COLORS["text"])
    
    style.configure("Success.TButton", background=COLORS["accent_green"])
    style.map("Success.TButton", background=[("active", COLORS["accent_green"])])
    
    style.configure("Warning.TButton", background=COLORS["accent_yellow"])
    style.map("Warning.TButton", background=[("active", COLORS["accent_yellow"])])
    
    style.configure("Danger.TButton", background=COLORS["accent_red"])
    style.map("Danger.TButton", background=[("active", COLORS["accent_red"])])

def create_custom_button(parent, text, command=None, bg_color=None, fg_color=None, icon=None, width=None, height=None):
    """
    Create a custom styled button
    
    Args:
        parent: Parent widget
        text: Button text
        command: Button command
        bg_color: Background color (optional)
        fg_color: Foreground color (optional)
        icon: Button icon (optional)
        width: Button width (optional)
        height: Button height (optional)
        
    Returns:
        CTkButton instance
    """
    if fg_color is None:
        fg_color = COLORS["primary"]
        
    button = ctk.CTkButton(
        parent,
        text=text,
        command=command,
        fg_color=fg_color,
        bg_color=bg_color,
        image=icon,
        width=width if width else 100,
        height=height if height else METRICS["button_height"],
        corner_radius=METRICS["border_radius"],
        border_width=0,
        font=FONTS["button"]
    )
    
    return button

def create_section_label(parent, text):
    """
    Create a section label
    
    Args:
        parent: Parent widget
        text: Label text
        
    Returns:
        CTkLabel instance
    """
    label = ctk.CTkLabel(
        parent,
        text=text,
        font=FONTS["heading3"],
        text_color=COLORS["primary"],
        anchor="w"
    )
    
    return label

def create_card_frame(parent):
    """
    Create a card frame with shadow effect
    
    Args:
        parent: Parent widget
        
    Returns:
        CTkFrame instance
    """
    frame = ctk.CTkFrame(
        parent,
        fg_color=COLORS["card"],
        corner_radius=METRICS["border_radius"],
        border_width=1,
        border_color=COLORS["border"]
    )
    
    return frame

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