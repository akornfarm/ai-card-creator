from aqt import mw, gui_hooks
from aqt.qt import QAction
from aqt.utils import showWarning
import os
import sys
import traceback

# Add addon directory to path
addon_dir = os.path.dirname(__file__)
if addon_dir not in sys.path:
    sys.path.insert(0, addon_dir)

ai_card_creator = None

def safe_import():
    """Safely import modules with error handling"""
    try:
        from .ui import AICardCreatorWindow
        from .config import AICardCreatorConfig
        return AICardCreatorWindow, AICardCreatorConfig
    except Exception as e:
        print(f"AI Card Creator: Import error: {str(e)}")
        print(traceback.format_exc())
        return None, None

def initialize():
    """Initialize the addon when Anki is ready"""
    global ai_card_creator
    
    try:
        AICardCreatorWindow, AICardCreatorConfig = safe_import()
        
        if not AICardCreatorWindow or not AICardCreatorConfig:
            print("AI Card Creator: Failed to import required modules")
            return
        
        class AICardCreator:
            def __init__(self):
                self.config = None
                self.window = None
                try:
                    self.config = AICardCreatorConfig()
                    self.setup_menu()
                except Exception as e:
                    print(f"AI Card Creator: Init error: {str(e)}")
                    print(traceback.format_exc())
            
            def setup_menu(self):
                try:
                    # Add menu item to open AI Card Creator
                    create_action = QAction("AI Card Creator", mw)
                    create_action.triggered.connect(self.show_window_safe)
                    mw.form.menuTools.addAction(create_action)
                    
                    # Add separator
                    mw.form.menuTools.addSeparator()
                    
                    # Add settings menu item
                    settings_action = QAction("AI Card Creator Settings", mw)
                    settings_action.triggered.connect(self.show_settings_safe)
                    mw.form.menuTools.addAction(settings_action)
                except Exception as e:
                    print(f"AI Card Creator: Menu setup error: {str(e)}")
                    print(traceback.format_exc())
            
            def show_window_safe(self):
                """Safely show window with error handling"""
                try:
                    self.show_window()
                except Exception as e:
                    error_msg = f"Error opening AI Card Creator:\n{str(e)}\n\nCheck console for details."
                    showWarning(error_msg)
                    print(f"AI Card Creator: Window error: {str(e)}")
                    print(traceback.format_exc())
            
            def show_window(self):
                if self.window is None:
                    self.window = AICardCreatorWindow(mw, self.config)
                self.window.show()
                self.window.raise_()
                self.window.activateWindow()
            
            def show_settings_safe(self):
                """Safely show settings with error handling"""
                try:
                    self.show_settings()
                except Exception as e:
                    error_msg = f"Error opening settings:\n{str(e)}\n\nCheck console for details."
                    showWarning(error_msg)
                    print(f"AI Card Creator: Settings error: {str(e)}")
                    print(traceback.format_exc())
            
            def show_settings(self):
                self.config.show_settings_dialog()
                # Refresh the window lists if it's open
                if self.window and hasattr(self.window, 'refresh_lists'):
                    self.window.refresh_lists()
        
        ai_card_creator = AICardCreator()
        print("AI Card Creator: Initialized successfully")
        
    except Exception as e:
        print(f"AI Card Creator: Fatal initialization error: {str(e)}")
        print(traceback.format_exc())

# Register the initialization function to run when profile is loaded
gui_hooks.profile_did_open.append(initialize)