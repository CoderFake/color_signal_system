import os
import sys
import traceback
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from gui.main_window import MainWindow
from gui.theme_manager import apply_dark_theme, configure_ttk_style
from gui.main_window_integration import integrate_effects

def setup_environment():
    """
    Set up necessary environment variables and paths
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    
    for dir_name in ["config", "presets", "logs"]:
        dir_path = os.path.join(script_dir, dir_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

def exception_handler(exc_type, exc_value, exc_traceback):
    """
    Global exception handler
    """
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "error.log")
    
    with open(log_file, "a") as f:
        f.write(f"\n--- New Error ---\n{error_msg}\n")
    
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

def setup_theme():
    """
    Set up application theme
    """
    apply_dark_theme()

    style = ttk.Style()
    configure_ttk_style(style)

def main():
    """
    Main function
    """
    sys.excepthook = exception_handler

    setup_environment()
    
    setup_theme()
    
    app = MainWindow("LED Tape Light Control System")

    effects = integrate_effects(app)
    
    app.run()

if __name__ == "__main__":
    main()