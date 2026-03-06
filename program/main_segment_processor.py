"""
segment_processor.py

This module handles the processing of video segments for conducting analysis.
"""

import os

def process_segment(config, segment_index, segment_interval):
    """Process a single segment of the video using the same approach as full video analysis"""
    try:
        # Extract segment information
        start_frame, end_frame = segment_interval
        
        print(f"\n=== Processing Segment {segment_index+1}: Frames {start_frame}-{end_frame} ===")
        
        # Create a segment-specific configuration
        segment_config = config.copy()
        
        # Important: Set process_markers to the segment interval
        segment_config["process_markers"] = [segment_interval]
        
        # Create segment-specific output directory
        video_name = os.path.splitext(os.path.basename(config["video_path"]))[0]
        segment_dir = os.path.join(config["export_path"], f"{video_name}_segment_{segment_index+1}")
        os.makedirs(segment_dir, exist_ok=True)
        segment_config["export_path"] = segment_dir
        
        # Set export path for this segment
        try:
            # from imports import set_export_path
            print(f"Export path set to: {segment_dir}")
        except Exception as e:
            print(f"Warning: Could not set export path for segment: {e}")
        
        # Run conducting analysis directly for this segment
        # This mirrors the approach used in run_conducting_analysis but for a specific segment
        try:
            print(f"Running analysis for segment {segment_index+1}...")
            
            # Set up names.py for this segment
            names_py_content = "import os\n\n"
            names_py_content += f'VIDEO_PATH = "{segment_config["video_path"]}"\n'
            names_py_content += f'EXPORT_PATH = "{segment_dir}"\n\n'
            
            # Add all the standard functions from names.py
            # Helper functions to generate filenames
            names_py_content += """
# returns the name of the video file being processed
def initialize_video():
    # Return just the basename without extension
    return os.path.splitext(os.path.basename(VIDEO_PATH))[0]

# returns name for the final output video
def video_out_name():
    videoFileName = initialize_video()
    outNames = videoFileName + "_analyzed"
    return outNames

# returns name for the main coordinates plot
def video_plot_name():
    videoFileName = initialize_video()
    plotName = videoFileName + '_coordinates_plot'
    return plotName

# returns name for the sway analysis plot
def video_sway_plot_Name():
    videoFileName = initialize_video()
    swayPlotName = videoFileName + '_sway_plot'
    return swayPlotName

# returns name for the x-axis hand movement plot
def video_hands_plot_x_name():
    videoFileName = initialize_video()
    handsPlotName_X = videoFileName + '_hands_plot_x'
    return handsPlotName_X

# returns name for the y-axis hand movement plot
def video_hands_plot_y_name():
    videoFileName = initialize_video()
    handsPlotName_Y = videoFileName + '_hands_plot_y'
    return handsPlotName_Y
"""
        except Exception as e:
            print(f"Error running analysis for segment {segment_index+1}: {e}")
    except Exception as e:
        print(f"Error processing segment {segment_index+1}: {e}") 