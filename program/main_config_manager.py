"""
config_manager.py

This module handles loading and setting configuration options for the application.
"""

import os
import json

# Define CONDUCTING_MODULES_AVAILABLE
try:
    import mediapipe as mp
    CONDUCTING_MODULES_AVAILABLE = True
except ImportError:
    CONDUCTING_MODULES_AVAILABLE = False
    print("Note: Conducting analysis modules not found, will run in movement detection mode only.")

# Define DEFAULT_CONFIG
DEFAULT_CONFIG = {
    "video_path": "",
    "export_path": "output",
    "crop_rect": [200, 150, 400, 300],
    "process_markers": [],
    "processing_options": {
        "conducting_analysis": CONDUCTING_MODULES_AVAILABLE,
        "graph_options": {
            "generate_beat_plot": True,
            "generate_hand_path": True,
            "generate_cluster_graph": True,
            "generate_overtime_graph": True,
            "generate_swaying_graph": True,
            "generate_mirror_x_graph": True,
            "generate_mirror_y_graph": True
        }
    }
}

def load_config():
    """Load configuration from interface_config.json"""
    if os.path.exists("interface_config.json"):
        try:
            with open("interface_config.json", "r") as f:
                config = json.load(f)
                
                # Ensure processing_options contains conducting_analysis setting
                if "processing_options" in config:
                    if "conducting_analysis" not in config["processing_options"]:
                        config["processing_options"]["conducting_analysis"] = CONDUCTING_MODULES_AVAILABLE
                
                return config
        except Exception as e:
            print(f"Error loading configuration: {e}")
    
    return DEFAULT_CONFIG


def get_export_path():
    """Get export path from config file"""
    try:
        with open("interface_config.json", "r") as f:
            config = json.load(f)
            return config.get("export_path", "output")
    except:
        return "output"


def set_export_path(path):
    """Create export directory if it doesn't exist"""
    if not os.path.exists(path):
        os.makedirs(path) 