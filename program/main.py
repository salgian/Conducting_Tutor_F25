"""
main.py

This is the main entry point for the Movement Detection and Conducting Analysis application.
It initializes the configuration, processes video segments, and runs the user interface.
"""
import os
import sys
import json
import cv2
import numpy as np
import time
import traceback
from datetime import datetime
import subprocess

# Import interface module
from interface import run_interface
from mp_declaration import mediaPipeDeclaration
from names import initialize_video
from beat_filter import filter_beats
from graph_config import video_out_name
from mirror import mirrorDetection
from p_stage1 import process_video
from p_stage2 import output_process_video
from cueing import cueingDetection
from elbow import elbowDetection
from sway import swayingDetection
from sanrio_interface import run_sanrio_interface

# Import helper modules
from main_config_manager import load_config, get_export_path, set_export_path
from main_graph_options import select_graph_options
from main_segment_processor import process_segment
from main_conducting_analysis import run_conducting_analysis
from main_cycle_processor import CycleOne, CycleTwo
from graphs import generate_all_graphs, video_beat_plot_name

# handles the first pass through the video, detecting conducting movements and beats
class cycleOne: 

    # initializes the first cycle, setting up video capture and processing parameters
    def __init__(self):

        # get mediapipe detector
        self.detector = mediaPipeDeclaration.get_pose_landmarker()
        self.videoFileName = initialize_video()
        
        # initialize video capture
        self.cap = cv2.VideoCapture(self.videoFileName)
        if not self.cap.isOpened():
            print("Error: Could not open video file.")
            exit()

        # initialize tracking arrays
        self.frame_array = []
        self.processed_frame_array = []
        self.processing_intervals = []

        # initialize movement detectors
        self.swaying_detector = swayingDetection()
        self.mirror_detector = mirrorDetection()
        self.cueing_detector = cueingDetection() 
        self.elbow_detector = elbowDetection()
        # self.start_end_detector = startEndDetection()

        # setup video writer
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.out = cv2.VideoWriter(video_beat_plot_name() + '.avi', cv2.VideoWriter_fourcc(*'MJPG'), self.fps, (self.frame_width, self.frame_height))

        # Add debugging info after video capture initialization
        print("\n=== Cycle One Debug Information ===")
        print(f"Video File: {self.videoFileName}")
        print(f"Frame Width: {self.frame_width}")
        print(f"Frame Height: {self.frame_height}")
        print(f"FPS: {self.fps}")
        total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"Total Frames: {total_frames}")
        print(f"Video Duration: {total_frames/self.fps:.2f} seconds")
        print("================================\n")

        # process video and detect beats
        process_video(self.cap, self.out, self.detector, self.frame_array, self.processed_frame_array, self.processing_intervals, self.swaying_detector, self.mirror_detector, self.elbow_detector, self.start_end_detector)
        
        # analyze detected movements for beats
        (self.filtered_significant_beats, self.beat_coordinates, self.y_peaks, self.y_valleys, self.y_inverted, self.y, self.x) = filter_beats(self.frame_array, self.processed_frame_array)

        # After beat detection, add more debug info
        print("\n=== Beat Detection Results ===")
        print(f"Total frames processed: {len(self.frame_array)}")
        print(f"Number of beats detected: {len(self.filtered_significant_beats)}")
        print(f"Processing intervals: {self.processing_intervals}")
        print("============================\n")


# handles the second pass through the video, visualizing detected beats and generating analysis
class cycleTwo: 

    # initializes the second cycle, using data from cycle one to create visualizations
    def __init__(self, cycle_one_instance):

        # get mediapipe detector
        self.detector = mediaPipeDeclaration.get_pose_landmarker()
        self.videoFileName = initialize_video()
        self.cap = cv2.VideoCapture(self.videoFileName)

        # reuse swaying detector from cycle one
        self.swaying_detector = cycle_one_instance.swaying_detector
        self.mirror_detector = cycle_one_instance.mirror_detector
        self.cueing_detector = cycle_one_instance.cueing_detector
        self.elbow_detector = cycle_one_instance.elbow_detector

        # setup video writer
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))    
        self.out = cv2.VideoWriter(video_out_name() + '.mp4', cv2.VideoWriter_fourcc(*'mp4v'), self.fps, (self.frame_width, self.frame_height))

        # process video with detected beats
        self.processing_intervals = cycle_one_instance.processing_intervals
        
        # Note: output_process_video only takes 5 parameters:
        # cap, detector, filtered_significant_beats, processing_intervals, swaying_detector
        output_process_video(self.cap, self.detector, cycle_one_instance.filtered_significant_beats, 
                            self.processing_intervals, self.swaying_detector)

        # generate analysis graphs
        generate_all_graphs(cycle_one_instance)
        
        cv2.destroyAllWindows()
    
def process_with_visualization(video_path, start_frame, end_frame, crop_rect, options, output_dir):
    """Process a segment of the video with progress visualization"""
    # Simple command-line progress display instead of using pygame
    # This avoids display surface issues
    
    if not os.path.exists(video_path):
        print(f"Error: Video file not found: {video_path}")
        return False
    
    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video: {video_path}")
        return False
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Unpack crop rectangle
    crop_x, crop_y, crop_w, crop_h = crop_rect
    
    # Ensure crop rectangle is within video bounds
    crop_x = max(0, min(width - 10, crop_x))
    crop_y = max(0, min(height - 10, crop_y))
    crop_w = max(10, min(width - crop_x, crop_w))
    crop_h = max(10, min(height - crop_y, crop_h))
    
    # Background subtractor
    bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=100, varThreshold=50, detectShadows=True)
    
    # Process frames
    try:
        # Skip to start frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        frame_count = 0
        total_frames = end_frame - start_frame
        
        prev_gray = None

        print(f"Processed segment {start_frame}-{end_frame}: 100% complete")
        print(f"Segment processing complete. Output saved to: {output_dir}")
        return True
        
    except Exception as e:
        print(f"Error processing video segment: {e}")
        traceback.print_exc()
        return False 

# main execution point of the program
if __name__ == "__main__":
    print("=== Movement Detection and Conducting Analysis Application ===")
    
    # Check if we should use the Sanrio theme
    use_sanrio_mode = "--sanrio-mode" in sys.argv
    
    # Run interface to get user input
    interface_result = False
    if use_sanrio_mode:
        interface_result = run_sanrio_interface()
    else:
        interface_result = run_interface()
    
    if interface_result:
        # Load configuration from interface
        config = load_config()
        
        # Extract process markers
        process_markers = config.get("process_markers", [])
        
        # Create output directory with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_name = os.path.splitext(os.path.basename(config["video_path"]))[0]
        output_dir = os.path.join(config["export_path"], f"{video_name}_analysis_{timestamp}")
        os.makedirs(output_dir, exist_ok=True)
        
        # Save configuration copy
        with open(os.path.join(output_dir, "config.json"), "w") as f:
            json.dump(config, f, indent=2)
        
        # Check if conducting analysis should run
        if config["processing_options"].get("conducting_analysis", False):
            print("\nRunning conducting analysis...")
            # Make a copy of config for conducting analysis
            conducting_config = config.copy()
            conducting_config["export_path"] = os.path.join(output_dir, "conducting_analysis")
            os.makedirs(conducting_config["export_path"], exist_ok=True)
            
            # Run conducting analysis
            run_conducting_analysis(conducting_config)
        
        # Run standard movement detection
        if config["processing_options"].get("detect_motion", True):
            print("\nBeginning movement detection processing...")
            
            # Process each segment
            for i, marker in enumerate(config["process_markers"]):
                print(f"\nProcessing segment {i+1} of {len(config['process_markers'])}...")
                
                # Extract the start_frame, end_frame, and crop values based on marker type
                if isinstance(marker, dict):
                    # New format with dictionary
                    start_frame = marker["start_frame"]
                    end_frame = marker["end_frame"] 
                    crop = marker.get("crop", config["crop_rect"])
                elif isinstance(marker, (list, tuple)) and len(marker) >= 2:
                    # Old format with tuple/list [start_frame, end_frame]
                    start_frame = marker[0]
                    end_frame = marker[1]
                    # Use crop from marker if available, otherwise use default
                    crop = marker[2] if len(marker) > 2 else config["crop_rect"]
                else:
                    print(f"Warning: Invalid marker format: {marker}. Skipping.")
                    continue
                
                # Use the visualization-enabled processing function
                process_with_visualization(
                    config["video_path"],
                    start_frame,
                    end_frame,
                    crop,
                    config["processing_options"],
                    output_dir
                )
        
        print("\nAll processing complete!")
        print(f"Results saved to: {os.path.abspath(output_dir)}")
        
        # Open output folder if on Windows
        if os.name == 'nt':
            os.startfile(output_dir)
    else:
        print("Interface closed without configuration. Exiting.")