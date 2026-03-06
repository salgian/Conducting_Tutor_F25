"""
conducting_analysis.py

This module handles the conducting analysis workflow.
"""

import os
import json
import cv2
import traceback
from datetime import datetime
from main_cycle_processor import CycleOne, CycleTwo

# Ensure CONDUCTING_MODULES_AVAILABLE is defined
try:
    import mediapipe as mp
    CONDUCTING_MODULES_AVAILABLE = True
except ImportError:
    CONDUCTING_MODULES_AVAILABLE = False
    print("Note: Conducting analysis modules not found, will run in movement detection mode only.")

# Define the conducting analysis function
def run_conducting_analysis(config):
    """Run the conducting analysis workflow"""
    if not CONDUCTING_MODULES_AVAILABLE:
        print("Conducting analysis modules not available. Skipping conducting analysis.")
        return False
        
    try:
        print("\n=== Starting Conducting Movement Analysis ===")
        # Make sure output directory exists
        export_path = config["export_path"]
        os.makedirs(export_path, exist_ok=True)
        
        print(f"Set export path to: {export_path}")
        
        # Create the content for names.py with explicit line breaks
        names_py_content = "import os\n\n"
        names_py_content += f'VIDEO_PATH = "{config["video_path"]}"\n'
        names_py_content += f'EXPORT_PATH = "{export_path}"\n\n'
        
        # Add all the functions
        names_py_content += "# returns the name of the video file being processed\n"
        names_py_content += "def initialize_video():\n"
        names_py_content += "    # Return just the basename without extension\n"
        names_py_content += "    return os.path.splitext(os.path.basename(VIDEO_PATH))[0]\n\n"
        
        names_py_content += "# returns name for the final output video\n"
        names_py_content += "def video_out_name():\n"
        names_py_content += "    videoFileName = initialize_video()\n"
        names_py_content += "    outNames = videoFileName + \"_analyzed\"\n"
        names_py_content += "    return outNames\n\n"
        
        names_py_content += "# returns name for the main coordinates plot\n"
        names_py_content += "def video_plot_name():\n"
        names_py_content += "    videoFileName = initialize_video()\n"
        names_py_content += "    plotName = videoFileName + '_coordinates_plot'\n"
        names_py_content += "    return plotName\n\n"
        
        names_py_content += "# returns name for the sway analysis plot\n"
        names_py_content += "def video_sway_plot_Name():\n"
        names_py_content += "    videoFileName = initialize_video()\n"
        names_py_content += "    swayPlotName = videoFileName + '_sway_plot'\n"
        names_py_content += "    return swayPlotName\n\n"
        
        names_py_content += "# returns name for the x-axis hand movement plot\n"
        names_py_content += "def video_hands_plot_x_name():\n"
        names_py_content += "    videoFileName = initialize_video()\n"
        names_py_content += "    handsPlotName_X = videoFileName + '_hands_plot_x'\n"
        names_py_content += "    return handsPlotName_X\n\n"
        
        names_py_content += "# returns name for the y-axis hand movement plot\n"
        names_py_content += "def video_hands_plot_y_name():\n"
        names_py_content += "    videoFileName = initialize_video()\n"
        names_py_content += "    handsPlotName_Y = videoFileName + '_hands_plot_y'\n"
        names_py_content += "    return handsPlotName_Y\n\n"
        
        names_py_content += "# returns name for the beat detection plot\n"
        names_py_content += "def video_beat_plot_name():\n"
        names_py_content += "    videoFileName = initialize_video()\n"
        names_py_content += "    beatPlotName = videoFileName + '_beat_plot'\n"
        names_py_content += "    return beatPlotName\n\n"
        
        names_py_content += "# returns name for the conducting path visualization\n"
        names_py_content += "def video_conduct_path_name():\n"
        names_py_content += "    videoFileName = initialize_video()\n"
        names_py_content += "    conductPath = videoFileName + '_conduct_path'\n"
        names_py_content += "    return conductPath\n\n"
        
        names_py_content += "# returns name for the bpm text file\n"
        names_py_content += "def video_bpm_output_name():\n"
        names_py_content += "    videoFileName = initialize_video()\n"
        names_py_content += "    bpmOutputName = videoFileName + '_auto_BPM.txt'\n"
        names_py_content += "    return bpmOutputName\n\n"
        
        names_py_content += "# returns name for the cluster plot\n"
        names_py_content += "def video_cluster_plot_name():\n"
        names_py_content += "    videoFileName = initialize_video()\n"
        names_py_content += "    clusterPlotName = videoFileName + '_cluster_plot'\n"
        names_py_content += "    return clusterPlotName\n\n"
        
        names_py_content += "# returns name for the overtime plot\n"
        names_py_content += "def video_overtime_plot_name():\n"
        names_py_content += "    videoFileName = initialize_video()\n"
        names_py_content += "    overtimePlotName = videoFileName + '_overtime_plot'\n"
        names_py_content += "    return overtimePlotName\n\n"
        
        # Add function to ensure paths are combined correctly
        names_py_content += "# Helper function to join export path with filename\n"
        names_py_content += "def get_full_path(filename):\n"
        names_py_content += "    return os.path.join(EXPORT_PATH, filename)\n"
        
        # Write the content to names.py
        with open("names.py", "w") as f:
            f.write(names_py_content)
            
        # Reload the names module to ensure it picks up changes
        import importlib
        import names
        importlib.reload(names)
            
        # Run the conducting analysis
        print(f"Analyzing video: {config['video_path']}")
        print(f"Saving results to: {export_path}")
        
        cycle_one_instance = CycleOne(config)
        cycle_two_instance = CycleTwo(cycle_one_instance, config)
        
        print("=== Conducting Analysis Complete ===\n")
        return True
    except Exception as e:
        print(f"Error in conducting analysis: {e}")
        traceback.print_exc()
        return False 