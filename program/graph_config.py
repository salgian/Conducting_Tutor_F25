import os
import json

# Get export path from configuration
def get_export_path():
    try:
        with open("interface_config.json", "r") as f:
            config = json.load(f)
            export_path = config.get("export_path", "output")
            # Ensure directory exists
            os.makedirs(export_path, exist_ok=True)
            return export_path
    except:
        # Fallback to default
        default_path = "output"
        os.makedirs(default_path, exist_ok=True)
        return default_path

# Helper function to get video name from configuration
def get_video_name():
    try:
        with open("interface_config.json", "r") as f:
            config = json.load(f)
            video_path = config.get("video_path", "unknown_video")
            return os.path.basename(video_path).split('.')[0]
    except:
        return "unknown_video"

# Video name generation functions
def video_beat_plot_name():
    return f"{get_video_name()}_beat_plot"

def video_conduct_path_name():
    return f"{get_video_name()}_conduct_path"

def video_cluster_plot_name():
    return f"{get_video_name()}_cluster_plot"

def video_time_signature_plot_name():
    return f"{get_video_name()}_time_signature_plot"

def video_sway_plot_Name():
    return f"{get_video_name()}_sway_plot"

def video_hands_plot_x_name():
    return f"{get_video_name()}_hands_x_plot"

def video_hands_plot_y_name():
    return f"{get_video_name()}_hands_y_plot"

def video_out_name():
    return f"{get_video_name()}_analyzed"

# Keep this for backward compatibility
def video_overtime_plot_name():
    return video_time_signature_plot_name() 