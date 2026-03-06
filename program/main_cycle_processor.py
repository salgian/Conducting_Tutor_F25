"""
cycle_processor.py

This module contains the CycleOne and CycleTwo classes for handling different stages of video processing and analysis.
"""

import cv2
import os
import numpy as np
from mp_declaration import mediaPipeDeclaration
from sway import swayingDetection
from mirror import mirrorDetection
from cueing import cueingDetection
from elbow import elbowDetection
from beat_filter import filter_beats
from p_stage1 import process_video
from p_stage2 import output_process_video
from graphs import generate_all_graphs

# Ensure CONDUCTING_MODULES_AVAILABLE is defined
try:
    import mediapipe as mp
    CONDUCTING_MODULES_AVAILABLE = True
except ImportError:
    CONDUCTING_MODULES_AVAILABLE = False
    print("Note: Conducting analysis modules not found, will run in movement detection mode only.")

def log_debug_info(message):
    """Helper function for debug output with a timestamp"""
    from datetime import datetime
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[DEBUG {timestamp}] {message}")

class CycleOne:
    # initializes the first cycle, setting up video capture and processing parameters
    def __init__(self, config):
        if not CONDUCTING_MODULES_AVAILABLE:
            print("Error: Conducting analysis modules not available")
            return
            
        # get mediapipe detector
        self.detector = mediaPipeDeclaration.get_pose_landmarker()
        self.videoFileName = config["video_path"]
        
        # initialize video capture
        self.cap = cv2.VideoCapture(self.videoFileName)
        if not self.cap.isOpened():
            print("Error: Could not open video file.")
            exit()

        # initialize tracking arrays
        self.frame_array = []
        self.processed_frame_array = []
        
        # Get processing intervals from the configuration
        self.processing_intervals = config.get("process_markers", [])

        # initialize movement detectors
        self.swaying_detector = swayingDetection()
        self.mirror_detector = mirrorDetection()
        self.cueing_detector = cueingDetection()
        self.elbow_detector = elbowDetection()

        # setup video writer
        export_path = config["export_path"]
        os.makedirs(export_path, exist_ok=True)
        
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        
        # Get crop settings if available
        crop_data = config.get("crop_rect", None)
        if crop_data:
            self.frame_width = crop_data[2]
            self.frame_height = crop_data[3]

        # Add debugging info after video capture initialization
        print("\n=== Cycle One Debug Information ===")
        print(f"Video File: {self.videoFileName}")
        print(f"Frame Width: {self.frame_width}")
        print(f"Frame Height: {self.frame_height}")
        print(f"FPS: {self.fps}")
        total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"Total Frames: {total_frames}")
        print(f"Video Duration: {total_frames/self.fps:.2f} seconds")
        print(f"Processing Intervals: {self.processing_intervals}")
        print("================================\n")

        # process video and detect beats
        process_video(self.cap, self.detector, self.frame_array, self.processed_frame_array, 
                     self.processing_intervals, self.swaying_detector, self.mirror_detector, self.elbow_detector)
        
        # analyze detected movements for beats
        # Handle all 7 return values from filter_beats
        # The structure is: filtered_significant_beats, beat_coordinates, y_peaks, y_valleys, y_inverted, y, x
        results = filter_beats(self.frame_array, self.processed_frame_array)
        self.filtered_significant_beats = results[0]
        self.beat_coordinates = results[1]
        self.y_peaks = results[2]
        self.y_valleys = results[3]
        self.y_inverted = results[4]  # This is now explicitly captured
        self.y = results[5]
        self.x = results[6]
        
        # IMPORTANT: Add debug info to understand coordinate system and peak/valley relationship
        log_debug_info(f"PEAK/VALLEY INVESTIGATION: y_peaks count: {len(self.y_peaks)}, y_valleys count: {len(self.y_valleys)}")
        
        # Sample some peak and valley values to understand the relationship
        if len(self.y_peaks) > 0 and len(self.y_valleys) > 0 and len(self.y) > 0:
            for i in range(min(3, len(self.y_peaks))):
                idx = self.y_peaks[i]
                if idx < len(self.y):
                    log_debug_info(f"Peak {i+1} at index {idx}: y-value = {self.y[idx]}")
            
            for i in range(min(3, len(self.y_valleys))):
                idx = self.y_valleys[i]
                if idx < len(self.y):
                    log_debug_info(f"Valley {i+1} at index {idx}: y-value = {self.y[idx]}")
                    
            # Direct comparison of y_peaks from different sources/methods
            # From beat_filter.py (direct find_peaks call)
            log_debug_info("COMPARE PEAKS/VALLEYS: Check if direct vs. normalized peaks match")
            # Also add information about how normalize_and_detect_peaks processes the data 
            from graph_math import normalize_and_detect_peaks
            y_norm, peaks_norm, valleys_norm = normalize_and_detect_peaks(self.y)
            log_debug_info(f"Normalized peaks count: {len(peaks_norm)}, valleys count: {len(valleys_norm)}")
            
            # Compare the first few indices to see if they're similar
            direct_indices = self.y_peaks[:3] if len(self.y_peaks) >= 3 else self.y_peaks
            norm_indices = peaks_norm[:3] if len(peaks_norm) >= 3 else peaks_norm
            log_debug_info(f"Direct y_peaks indices (first 3): {direct_indices}")
            log_debug_info(f"Normalized y_peaks indices (first 3): {norm_indices}")

        # After beat detection, add more debug info
        print("\n=== Beat Detection Results ===")
        print(f"Total frames processed: {len(self.frame_array)}")
        print(f"Number of beats detected: {len(self.filtered_significant_beats)}")
        print(f"Processing intervals: {self.processing_intervals}")
        print("============================\n")


class CycleTwo:
    # initializes the second cycle, using data from cycle one to create visualizations
    def __init__(self, cycle_one_instance, config):
        if not CONDUCTING_MODULES_AVAILABLE:
            print("Error: Conducting analysis modules not available")
            return
            
        # get mediapipe detector
        self.detector = mediaPipeDeclaration.get_pose_landmarker()
        self.videoFileName = config["video_path"]
        self.cap = cv2.VideoCapture(self.videoFileName)
        
        # reuse swaying detector from cycle one
        self.swaying_detector = cycle_one_instance.swaying_detector
        self.mirror_detector = cycle_one_instance.mirror_detector
        self.cueing_detector = cycle_one_instance.cueing_detector
        self.elbow_detector = cycle_one_instance.elbow_detector
        # self.pattern_detector = patternDetection() // removed 
        
        # setup video writer
        export_path = config["export_path"]
        os.makedirs(export_path, exist_ok=True)
        
        # Get the frame dimensions from config
        self.frame_width = 268  # Default to cropped width from logs
        self.frame_height = 496  # Default to cropped height from logs
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        
        # Get crop settings if available to confirm dimensions
        crop_data = config.get("crop_rect", None)
        if crop_data:
            x, y, w, h = crop_data
            self.frame_width = w
            self.frame_height = h
            print(f"Using crop dimensions: {self.frame_width}x{self.frame_height}")
            
        # Add debugging info
        print("\n=== Cycle Two Initialization ===")
        print(f"Video File: {self.videoFileName}")
        print(f"Frame Width: {self.frame_width}")
        print(f"Frame Height: {self.frame_height}")
        print(f"FPS: {self.fps}")
        print("================================\n")

                # Detect patterns and write to files
        # patterns = self.pattern_detector.pattern_detection(cycle_one_instance.beat_coordinates)
        # pattern_file = os.path.join(export_path, os.path.basename(self.videoFileName) + "_video_pattern.txt")
        # with open(pattern_file, "w") as f:
        #     for pattern in patterns:
        #         f.write(pattern + "\n")
        
        # Process video with detected beats
        output_process_video(self.cap, self.detector, 
                           cycle_one_instance.filtered_significant_beats,
                           cycle_one_instance.processing_intervals, 
                           self.swaying_detector, 
                           self.mirror_detector,
                           self.cueing_detector,
                           self.elbow_detector,
                           cycle_one_instance.y_inverted)
        
        
        graph_options = config.get("processing_options", {}).get("graph_options", None)
        # Generate analysis graphs
        generate_all_graphs(cycle_one_instance, graph_options)
        
        # Make sure to release resources
        self.cap.release()
        cv2.destroyAllWindows() 