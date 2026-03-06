"""
Main entry point for the Movement Detection and Conducting Analysis application.
This file loads the interface and handles the processing workflow, combining
movement detection with conducting pattern analysis.
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
from graph_config import video_out_name
from names import video_bpm_output_name
from sanrio_interface import run_sanrio_interface

# Try to import conducting-specific modules, but don't fail if they're not available
try:
    from imports import *
    CONDUCTING_MODULES_AVAILABLE = True
except ImportError:
    CONDUCTING_MODULES_AVAILABLE = False
    print("Note: Conducting analysis modules not found, will run in movement detection mode only.")

# Add these helper functions at the top of main.py after imports
def print_checkbox_menu(options):
    """Display a checkbox menu for options"""
    print("\n=== Graph Selection Menu ===")
    print("Select which graphs to generate:")
    for i, (key, value) in enumerate(options.items(), 1):
        status = "[X]" if value else "[ ]"
        print(f"{i}. {status} {key.replace('generate_', '').replace('_', ' ').title()}")
    print("\nEnter the number to toggle selection, or 'c' to continue: ")

def get_checkbox_input(options):
    """Get user input for checkbox menu"""
    keys = list(options.keys())
    while True:
        choice = input("> ").strip().lower()
        if choice == 'c':
            return options
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(keys):
                key = keys[idx]
                options[key] = not options[key]
                print_checkbox_menu(options)
            else:
                print(f"Please enter a number between 1 and {len(keys)}, or 'c' to continue")
        except ValueError:
            print("Please enter a number or 'c' to continue")

def select_graph_options():
    """Interactive menu for selecting graph options"""
    options = {
        "generate_beat_plot": True,
        "generate_hand_path": True,
        "generate_cluster_graph": True,
        "generate_overtime_graph": True,
        "generate_swaying_graph": True,
        "generate_mirror_x_graph": True,
        "generate_mirror_y_graph": True
    }
    
    print_checkbox_menu(options)
    return get_checkbox_input(options)

# Default configuration
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

# Conducting Analysis Classes
# Here's the complete implementation that should be added to main.py

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
            from imports import set_export_path
            set_export_path(segment_dir)
            print(f"Export path set to: {segment_dir}")
        except Exception as e:
            print(f"Warning: Could not set export path for segment: {e}")
        
        # Run conducting analysis directly for this segment
        # This mirrors the approach used in run_conducting_analysis but for a specific segment
        try:
            print(f"Running analysis for segment {segment_index+1}...")
            
            # Set up names.py for this segment
            names_py_content = "from imports import *\n"
            names_py_content += "import os\n\n"
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

# returns name for the beat detection plot
def video_beat_plot_name():
    videoFileName = initialize_video()
    beatPlotName = videoFileName + '_beat_plot'
    return beatPlotName

# returns name for the conducting path visualization
def video_conduct_path_name():
    videoFileName = initialize_video()
    conductPath = videoFileName + '_conduct_path'
    return conductPath

# returns name for the bpm text file
def video_bpm_output_name():
    videoFileName = initialize_video()
    bpmOutputName = videoFileName + '_auto_BPM.txt'
    return bpmOutputName

# returns name for the cluster plot
def video_cluster_plot_name():
    videoFileName = initialize_video()
    clusterPlotName = videoFileName + '_cluster_plot'
    return clusterPlotName

# returns name for the overtime plot
def video_overtime_plot_name():
    videoFileName = initialize_video()
    overtimePlotName = videoFileName + '_overtime_plot'
    return overtimePlotName

# Helper function to join export path with filename
def get_full_path(filename):
    return os.path.join(EXPORT_PATH, filename)
"""
            
            # Prepare the segment output file names
            segment_suffix = f"_segment_{start_frame}_{end_frame}"
            
            # Write the names.py for this segment
            with open("names.py", "w") as f:
                f.write(names_py_content)
            
            # Reload the names module to ensure it picks up changes
            import importlib
            import names
            importlib.reload(names)
            
            # Process the segment using the approach of cycle one and cycle two
            class SegmentCycleProcessor:
                def __init__(self, config):
                    """Initialize the segment processing, similar to CycleOne"""
                    if not CONDUCTING_MODULES_AVAILABLE:
                        print("Error: Conducting analysis modules not available")
                        return
                    
                    # Store config
                    self.config = config
                    
                    # Get mediapipe detector
                    self.detector = mediaPipeDeclaration.get_pose_landmarker()
                    self.videoFileName = config["video_path"]
                    
                    # Initialize video capture
                    self.cap = cv2.VideoCapture(self.videoFileName)
                    if not self.cap.isOpened():
                        print("Error: Could not open video file.")
                        exit()
                    
                    # Initialize tracking arrays
                    self.frame_array = []
                    self.processed_frame_array = []
                    
                    # Get processing intervals
                    self.processing_intervals = config.get("process_markers", [])
                    
                    # Initialize movement detectors
                    self.swaying_detector = swayingDetection()
                    self.mirror_detector = mirrorDetection()
                    
                    # Set up video writer
                    export_path = config["export_path"]
                    os.makedirs(export_path, exist_ok=True)
                    
                    # Get video properties
                    self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
                    
                    # Apply crop if specified
                    crop_data = config.get("crop_rect", None)
                    if crop_data:
                        self.frame_width = crop_data[2]
                        self.frame_height = crop_data[3]
                    
                    # Print debug info
                    print("\n=== Segment Cycle Debug Information ===")
                    print(f"Video File: {self.videoFileName}")
                    print(f"Processing segment: {start_frame}-{end_frame}")
                    print(f"Frame Width: {self.frame_width}")
                    print(f"Frame Height: {self.frame_height}")
                    print(f"FPS: {self.fps}")
                    total_frames = end_frame - start_frame + 1
                    print(f"Total Frames in segment: {total_frames}")
                    print(f"Segment Duration: {total_frames/self.fps:.2f} seconds")
                    print("================================\n")
                    
                    # Process video and detect beats - just like in CycleOne
                    self.process_segment()
                    
                    # Analyze detected movements for beats - same as CycleOne
                    (self.filtered_significant_beats, self.beat_coordinates, 
                     self.y_peaks, self.y_valleys, self.y, self.x) = filter_beats(self.frame_array, 
                                                                                self.processed_frame_array)
                    
                    # Print beat detection results
                    print("\n=== Beat Filter Debug Information ===")
                    print(f"Input frame array length: {len(self.frame_array)}")
                    print(f"Processed frame array length: {len(self.processed_frame_array)}")
                    print(f"Number of y peaks: {len(self.y_peaks)}")
                    print(f"Number of y valleys: {len(self.y_valleys)}")
                    print(f"Number of filtered beats: {len(self.filtered_significant_beats)}")
                    print("==================================\n")
                    
                    # Create the analyzed video with beat visualization - this is key
                    self.create_analyzed_video(export_path, segment_suffix)
                    
                    # Print beat detection summary
                    print("\n=== Beat Detection Results ===")
                    print(f"Total frames processed: {len(self.frame_array)}")
                    print(f"Number of beats detected: {len(self.filtered_significant_beats)}")
                    print("============================\n")
                
                def process_segment(self):
                    """Process only the frames in this segment - similar to process_video"""
                    if not self.processing_intervals:
                        print("Warning: No processing intervals defined")
                        return
                    
                    # Process each interval (should be just one for a segment)
                    for interval in self.processing_intervals:
                        start_frame, end_frame = interval
                        frame_count = start_frame
                        total_frames = end_frame - start_frame + 1
                        
                        # Set position to start frame
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
                        
                        # Process frames in this interval
                        while self.cap.isOpened() and frame_count <= end_frame:
                            success, image = self.cap.read()
                            if not success:
                                break
                            
                            # Apply cropping if specified
                            crop_rect = self.config.get("crop_rect", None)
                            if crop_rect:
                                x, y, w, h = crop_rect
                                # Ensure crop dimensions are within image bounds
                                height, width = image.shape[:2]
                                x = max(0, min(x, width-1))
                                y = max(0, min(y, height-1))
                                w = min(w, width-x)
                                h = min(h, height-y)
                                
                                if w > 0 and h > 0:
                                    image = image[y:y+h, x:x+w]
                                else:
                                    print("Warning: Invalid crop dimensions, using full frame")
                            
                            # Process the frame with MediaPipe
                            frame_timestamp_ms = round(self.cap.get(cv2.CAP_PROP_POS_MSEC))
                            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
                            detection_result = self.detector.detect_for_video(mp_image, frame_timestamp_ms)
                            
                            # Extract and store landmarks
                            pose_landmarks_list = detection_result.pose_landmarks
                            
                            if pose_landmarks_list:
                                for landmarks in pose_landmarks_list:
                                    if len(landmarks) > 16:
                                        # Get right hand coordinates
                                        x16 = landmarks[16].x
                                        y16 = landmarks[16].y
                                        
                                        # Store coordinates
                                        self.frame_array.append((x16, y16))
                                        self.processed_frame_array.append((x16, y16))
                            
                                        # Update movement detectors
                                        self.mirror_detector.mirror_calculation(landmarks[15].x, landmarks[15].y, landmarks[16].x, landmarks[16].y)
                                        self.swaying_detector.midpoint_calculation(landmarks[12].x, landmarks[11].x)
                                        
                                        # Set the midpoint when processing starts
                                        if not self.swaying_detector.midpointflag:
                                            self.swaying_detector.set_midpoint()
                            else:
                                # No landmarks detected, add NaN values
                                self.frame_array.append((np.nan, np.nan))
                                self.processed_frame_array.append((np.nan, np.nan))
                                                     
                            # Update frame counter
                            frame_count += 1
                            
                            # Display progress
                            if frame_count % 10 == 0:
                                progress = ((frame_count - start_frame) / total_frames) * 100
                                print(f"Processing segment {start_frame}-{end_frame}: {progress:.1f}% complete", end='\r')
                    
                
                def create_analyzed_video(self, export_path, segment_suffix=""):
                    """Create a final analyzed video with beat information and side panel
                    Modified version of create_analyzed_video for SegmentCycleProcessor class
                    """
                    print("\n=== Creating Analyzed Video ===")
                    
                    # Create a fresh detector
                    detector = mediaPipeDeclaration.get_pose_landmarker()
                    
                    # Create a new video capture
                    cap = cv2.VideoCapture(self.videoFileName)
                    
                    # Get video properties and dimensions
                    fps = int(cap.get(cv2.CAP_PROP_FPS))
                    frame_width = self.frame_width
                    frame_height = self.frame_height
                    
                    # Calculate dimensions for output with side panel
                    panel_width = 250
                    output_width = frame_width + panel_width
                    output_height = frame_height
                    
                    # Create output file for the analyzed video
                    analyzed_output_file = os.path.join(export_path, video_out_name() + segment_suffix + '.mp4')
                    
                    # Create VideoWriter with the combined dimensions
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    analyzed_out = cv2.VideoWriter(analyzed_output_file, fourcc, fps, 
                                                (output_width, output_height))
                    
                    # Verify writer is opened
                    if not analyzed_out.isOpened():
                        print("Error: Failed to open video writer")
                        # Try alternative codec
                        fourcc = cv2.VideoWriter_fourcc(*'XVID')
                        analyzed_out = cv2.VideoWriter(analyzed_output_file, fourcc, fps, 
                                                    (output_width, output_height))
                        if not analyzed_out.isOpened():
                            print("Error: Failed to open video writer with alternative codec")
                            cap.release()
                            return
                    
                    # Print video details
                    print(f"Video File: {self.videoFileName}")
                    print(f"Frame Width: {frame_width}")
                    print(f"Frame Height: {frame_height}")
                    print(f"Output Width: {output_width} (with panel)")
                    print(f"FPS: {fps}")
                    print(f"Output File: {analyzed_output_file}")
                    print(f"Processing segment: {self.processing_intervals[0][0]}-{self.processing_intervals[0][1]}")
                    total_frames = self.processing_intervals[0][1] - self.processing_intervals[0][0] + 1
                    print(f"Total frames to process: {total_frames}")
                    print("================================\n")
                    
                    # Initialize metrics for tracking
                    bpm_window = 5  # Window in seconds to calculate BPM
                    beats = []
                    current_bpm = 0
                    beat_count = 0
                    
                    # Initialize conducting metrics for side panel
                    conducting_metrics = {
                        "current_bpm": 0,
                        "beat_count": 0,
                        "suggested_time_signature": "4/4",
                        "sway_index": 0,
                        "pattern_confidence": 0,
                        "pattern_type": "Unknown"
                    }
                    
                    # Store y-coordinates for time signature estimation
                    y_coords = []
                    
                    # Function to create side panel
                    def create_side_panel(metrics, frame_height, panel_width, frame_index, segment_info):
                        """Create a side panel with conducting analysis information"""
                        # Create blank panel
                        panel = np.zeros((frame_height, panel_width, 3), dtype=np.uint8)
                        panel[:, :] = (40, 40, 40)  # Dark gray background
                        
                        # Add title
                        cv2.putText(panel, "Conducting Analysis", (10, 30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                        
                        # Add horizontal line
                        cv2.line(panel, (10, 40), (panel_width-10, 40), (200, 200, 200), 1)
                        
                        # Add metrics
                        y_pos = 80
                        cv2.putText(panel, f"Current BPM: {metrics['current_bpm']:.1f}", (10, y_pos), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                        
                        y_pos += 40
                        cv2.putText(panel, f"Beats detected: {metrics['beat_count']}", (10, y_pos), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                        
                        y_pos += 40
                        cv2.putText(panel, f"Time signature: {metrics['suggested_time_signature']}", (10, y_pos), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                        
                        y_pos += 40
                        cv2.putText(panel, f"Pattern: {metrics['pattern_type']}", (10, y_pos), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                        
                        y_pos += 40
                        cv2.putText(panel, f"Pattern conf: {metrics['pattern_confidence']}%", (10, y_pos), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                        
                        y_pos += 40
                        cv2.putText(panel, f"Sway index: {metrics['sway_index']:.2f}", (10, y_pos), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                        
                        # Add segment info
                        y_pos += 60
                        start_frame, end_frame = segment_info
                        cv2.putText(panel, f"Segment: {start_frame}-{end_frame}", (10, y_pos), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
                        
                        # Add progress bar
                        y_pos += 30
                        total_frames = end_frame - start_frame
                        progress = min(1.0, max(0, (frame_index - start_frame) / total_frames if total_frames > 0 else 0))
                        bar_width = panel_width - 20
                        cv2.rectangle(panel, (10, y_pos), (10 + bar_width, y_pos + 15), (100, 100, 100), -1)
                        cv2.rectangle(panel, (10, y_pos), (10 + int(bar_width * progress), y_pos + 15), (0, 255, 0), -1)
                        
                        # Add percentage text
                        y_pos += 30
                        cv2.putText(panel, f"Progress: {progress*100:.1f}%", (10, y_pos), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
                        
                        # Add frame info at bottom
                        y_pos = frame_height - 30
                        cv2.putText(panel, f"Frame: {frame_index}", (10, y_pos), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
                        
                        return panel
                        
                    # Function to estimate time signature (similar to overtime_graph)
                    def update_time_signature():
                        """Update time signature based on collected y-coordinates"""
                        try:
                            if len(y_coords) < 30:  # Need enough data
                                return "4/4"
                                
                            # Use find_peaks from scipy.signal to detect peaks and valleys
                            from scipy.signal import find_peaks
                            import numpy as np
                            
                            # Normalize data
                            y_array = np.array(y_coords)
                            y_min, y_max = min(y_array), max(y_array)
                            
                            if y_max == y_min:  # Avoid division by zero
                                return "4/4"
                                
                            y_normalized = (y_array - y_min) / (y_max - y_min)
                            
                            # Set parameters for peak detection
                            prominence = 0.1  # Similar to overtime_graph
                            distance = 5
                            
                            # Find peaks and valleys (inverted for peaks)
                            peaks, _ = find_peaks(-y_normalized, prominence=prominence, distance=distance)
                            valleys, _ = find_peaks(y_normalized, prominence=prominence, distance=distance)
                            
                            if len(peaks) < 4:  # Need at least a few peaks
                                return "4/4"
                                
                            # Count peaks and determine pattern
                            peak_heights = [-y_normalized[i] for i in peaks]
                            
                            # Apply logic similar to overtime_graph
                            if len(peak_heights) > 0:
                                # Find larger peaks
                                threshold = np.percentile(peak_heights, 75)
                                large_peaks = [i for i, h in zip(peaks, peak_heights) if h > threshold]
                                
                                if len(large_peaks) >= 2:
                                    # Count smaller peaks between large peaks
                                    all_patterns = []
                                    
                                    for i in range(1, len(large_peaks)):
                                        small_count = sum(1 for p in peaks 
                                                    if large_peaks[i-1] < p < large_peaks[i] 
                                                    and -y_normalized[p] <= threshold)
                                        pattern = small_count + 1
                                        all_patterns.append(pattern)
                                    
                                    # Get most common pattern
                                    if all_patterns:
                                        from collections import Counter
                                        counter = Counter(all_patterns)
                                        most_common = counter.most_common(1)[0][0]
                                        
                                        # Map to time signature
                                        if most_common == 2:
                                            return "2/4"
                                        elif most_common == 3:
                                            return "3/4"
                                        elif most_common == 4:
                                            return "4/4"
                                        elif most_common >= 5:
                                            return f"{most_common}/8"
                            
                            return "4/4"  # Default
                            
                        except Exception as e:
                            print(f"Error in time signature detection: {e}")
                            return "4/4"  # Default on error
                    
                    # Initialize variables for time signature updates
                    last_time_signature_update = 0
                    time_signature_update_interval = 30  # Update every 30 frames
                        
                    # Process each interval
                    for interval in self.processing_intervals:
                        start_frame, end_frame = interval
                        frame_count = start_frame
                        
                        # Set video to start frame
                        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
                        
                        # Process frames
                        while cap.isOpened() and frame_count <= end_frame:
                            ret, frame = cap.read()
                            if not ret:
                                break
                                
                            # Apply crop if available
                            crop_rect = self.config.get("crop_rect", None)
                            if crop_rect:
                                x, y, w, h = crop_rect
                                try:
                                    frame = frame[y:y+h, x:x+w]
                                except Exception as e:
                                    print(f"Error applying crop: {e}")
                                    # Try to continue with full frame if crop fails
                                    pass
                            
                            # Process frame with MediaPipe
                            frame_timestamp_ms = round(cap.get(cv2.CAP_PROP_POS_MSEC))
                            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
                            detection_result = detector.detect_for_video(mp_image, frame_timestamp_ms)
                            
                            # Draw landmarks
                            annotated_image = mediaPipeDeclaration.draw_landmarks_on_image(image_rgb, detection_result)
                            output_frame = cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR)
                            
                            # Calculate relative frame index within segment
                            relative_frame = frame_count - start_frame
                            
                            # For time signature detection, collect y coordinates
                            try:
                                # Extract coordinates from detected landmarks
                                if detection_result.pose_landmarks and len(detection_result.pose_landmarks[0]) > 16:
                                    y_coord = detection_result.pose_landmarks[0][16].y
                                    y_coords.append(y_coord)
                            except Exception as e:
                                # Ignore errors in time signature detection
                                pass
                                
                            # Update time signature periodically
                            if frame_count - last_time_signature_update >= time_signature_update_interval and len(y_coords) >= 30:
                                new_time_sig = update_time_signature()
                                conducting_metrics["suggested_time_signature"] = new_time_sig
                                last_time_signature_update = frame_count
                                
                                # Update pattern type based on time signature
                                if new_time_sig == "2/4":
                                    conducting_metrics["pattern_type"] = "Binary"
                                    conducting_metrics["pattern_confidence"] = 80
                                elif new_time_sig == "3/4":
                                    conducting_metrics["pattern_type"] = "Ternary" 
                                    conducting_metrics["pattern_confidence"] = 85
                                elif new_time_sig == "4/4":
                                    conducting_metrics["pattern_type"] = "Quaternary"
                                    conducting_metrics["pattern_confidence"] = 90
                                else:
                                    conducting_metrics["pattern_type"] = "Compound"
                                    conducting_metrics["pattern_confidence"] = 75
                            
                            # Add frame info
                            cv2.putText(output_frame, f'Frame: {frame_count}', 
                                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                            
                            # Add segment info
                            cv2.putText(output_frame, f'Segment: {start_frame}-{end_frame}', 
                                    (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                            
                            # Check if this relative frame position has a beat
                            is_beat_frame = relative_frame in self.filtered_significant_beats
                            
                            # Handle beat detection and display
                            if is_beat_frame:
                                # Show original BEAT text (preserving original visualization)
                                cv2.putText(output_frame, "BEAT!", 
                                        (output_frame.shape[1]//2 - 100, 100), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 255), 3)
                                
                                # Track beat for BPM calculation
                                beats.append(frame_count)
                                beat_count += 1
                                
                                # Get index of this beat in the filtered beats array
                                beat_index = self.filtered_significant_beats.index(relative_frame)
                                
                                if beat_index > 0:
                                    # Get previous beat (relative to segment start)
                                    prev_beat = self.filtered_significant_beats[beat_index - 1]
                                    
                                    # Calculate time between beats in seconds
                                    time_diff = (relative_frame - prev_beat) / fps
                                    
                                    # Calculate BPM
                                    if time_diff > 0:
                                        current_bpm = 60 / time_diff
                                    else:
                                        current_bpm = 0
                                        
                                    print(f"\nBeats per minute (BPM) at frame {frame_count}: {current_bpm:.1f}\n")
                                    
                                    # Update metrics
                                    conducting_metrics["current_bpm"] = current_bpm
                                    conducting_metrics["beat_count"] = beat_count
                                    
                                    # Save BPM data to file
                                    bpm_info = f'Beats per minute (BPM) at frame {frame_count}: {current_bpm:.1f}\n'
                                    bpm_file = os.path.join(export_path, video_bpm_output_name())
                                    with open(bpm_file, 'a') as file:
                                        file.write(bpm_info)
                            
                            # Always show current BPM (consistent display)
                            cv2.putText(output_frame, f'BPM: {conducting_metrics["current_bpm"]:.1f}', 
                                    (output_frame.shape[1]//2 - 80, 150), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                            
                            # Update sway index from detector
                            if hasattr(self.swaying_detector, 'swayingIndex'):
                                conducting_metrics["sway_index"] = self.swaying_detector.swayingIndex
                                
                            # Let swaying detector add any visual indicators
                            self.swaying_detector.swaying_print(frame_count, output_frame)
                            
                            # Create side panel
                            side_panel = create_side_panel(
                                conducting_metrics, 
                                frame_height=output_frame.shape[0], 
                                panel_width=panel_width, 
                                frame_index=frame_count, 
                                segment_info=(start_frame, end_frame)
                            )
                            
                            # Combine frame and side panel
                            combined_frame = np.zeros((output_height, output_width, 3), dtype=np.uint8)
                            combined_frame[:, :frame_width] = output_frame
                            combined_frame[:, frame_width:] = side_panel
                            
                            # Write the combined frame
                            analyzed_out.write(combined_frame)
                            
                            # Increment frame counter
                            frame_count += 1
                            
                            # Print progress occasionally
                            if frame_count % 100 == 0:
                                progress = ((frame_count - start_frame) / (end_frame - start_frame + 1)) * 100
                                print(f"Processing: {progress:.1f}% complete", end='\r')
                    
                    # Release resources
                    cap.release()
                    analyzed_out.release()
                    print(f"\nAnalyzed video with side panel saved to: {analyzed_output_file}")
            # Create and run the segment processor
            segment_processor = SegmentCycleProcessor(segment_config)
            
            # Generate graphs for this segment - directly using graph functions
            print("\n=== Generating Analysis Graphs for segment ===")
            from graphs import generate_all_graphs
            
            # Use the segment processor to generate graphs
            graph_options = segment_config.get("processing_options", {}).get("graph_options", None)
            generate_all_graphs(segment_processor, graph_options, segment_interval)
            
            print("=== Graph Generation Complete ===\n")
            
            print(f"Segment {segment_index+1} processed successfully")
            return True
            
        except Exception as e:
            print(f"Error processing segment {segment_index+1}: {e}")
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"Error in segment processing setup: {e}")
        traceback.print_exc()
        return False
    
# handles the first pass through the video, detecting conducting movements and beats
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
                     self.processing_intervals, self.swaying_detector, self.mirror_detector)
        
        # analyze detected movements for beats
        (self.filtered_significant_beats, self.beat_coordinates, self.y_peaks, self.y_valleys, self.y, self.x) = filter_beats(self.frame_array, self.processed_frame_array)

        # After beat detection, add more debug info
        print("\n=== Beat Detection Results ===")
        print(f"Total frames processed: {len(self.frame_array)}")
        print(f"Number of beats detected: {len(self.filtered_significant_beats)}")
        print(f"Processing intervals: {self.processing_intervals}")
        print("============================\n")


# handles the second pass through the video, visualizing detected beats and generating analysis
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
        self.pattern_detector = patternDetection()
        
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
        patterns = self.pattern_detector.pattern_detection(cycle_one_instance.beat_coordinates)
        pattern_file = os.path.join(export_path, os.path.basename(self.videoFileName) + "_video_pattern.txt")
        with open(pattern_file, "w") as f:
            for pattern in patterns:
                f.write(pattern + "\n")
        
        # Process video with detected beats
        output_process_video(self.cap, self.detector, 
                           cycle_one_instance.filtered_significant_beats,
                           cycle_one_instance.processing_intervals, 
                           self.swaying_detector)
        
        
        graph_options = config.get("processing_options", {}).get("graph_options", None)
        # Generate analysis graphs
        generate_all_graphs(cycle_one_instance, graph_options)
        
        # Make sure to release resources
        self.cap.release()
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
        
        # Set the export path in imports.py to ensure all graphs are saved to the correct location
        from imports import set_export_path
        set_export_path(export_path)
        
        print(f"Set export path to: {export_path}")
        
        # Create the content for names.py with explicit line breaks
        names_py_content = "from imports import *\n"
        names_py_content += "import os\n\n"
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

def main():
    """Main application entry point"""
    print("=== Movement Detection and Conducting Analysis Application ===")
    
    # Check if we should use the Sanrio theme
    use_sanrio_mode = "--sanrio-mode" in sys.argv
    
    # Run interface to get user input
    interface_result = False
    if use_sanrio_mode:
        from sanrio_interface import run_sanrio_interface
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
        if config["processing_options"].get("conducting_analysis", False) and CONDUCTING_MODULES_AVAILABLE:
            print("\nRunning conducting analysis...")
            # Make a copy of config for conducting analysis
            conducting_config = config.copy()
            conducting_config["export_path"] = os.path.join(output_dir, "conducting_analysis")
            os.makedirs(conducting_config["export_path"], exist_ok=True)
            
            # Explicitly update the export path in imports.py
            try:
                from imports import set_export_path
                set_export_path(conducting_config["export_path"])
                print(f"Updated export path to: {conducting_config['export_path']}")
            except Exception as e:
                print(f"Warning: Could not update export path in imports.py: {e}")
            
            # Check how many segments we have
            if len(process_markers) <= 1:
                # Process full video analysis for single segment or no segments
                print("\n--- Processing full video analysis ---")
                run_conducting_analysis(conducting_config)
            else:
                # Skip the full video analysis and only process individual segments
                print(f"\n--- Processing {len(process_markers)} individual segments ---")
                for i, marker in enumerate(process_markers):
                    # Extract segment interval
                    if isinstance(marker, dict):
                        segment_interval = (marker["start_frame"], marker["end_frame"])
                    elif isinstance(marker, (list, tuple)) and len(marker) >= 2:
                        segment_interval = (marker[0], marker[1])
                    else:
                        print(f"Warning: Invalid marker format: {marker}. Skipping.")
                        continue
                    
                    # Process this segment
                    process_segment(conducting_config, i, segment_interval)
        
        # Reset the path for movement detection
        try:
            from imports import set_export_path
            set_export_path(output_dir)
        except Exception as e:
            print(f"Warning: Could not reset export path for movement detection: {e}")
        
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
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        
        # Keep console open on error if running as executable
        if getattr(sys, 'frozen', False):
            input("\nPress Enter to exit...")