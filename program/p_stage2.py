import cv2
from names import video_out_name
import pygame
import mediapipe as mp
import json
import numpy as np
import os
from mp_declaration import mediaPipeDeclaration
from graph_config import get_export_path

# Make sure pygame is initialized
if not pygame.get_init():
    pygame.init()

# processes a single frame and returns the annotated image
def process_frame(cap, detector, image):

    if image is None:
        return None

    image_bgr = image
    frame_timestamp_ms = round(cap.get(cv2.CAP_PROP_POS_MSEC))
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
    detection_result = detector.detect_for_video(mp_image, frame_timestamp_ms)
    annotated_image = mediaPipeDeclaration.draw_landmarks_on_image(image_rgb, detection_result)
    annotated_image_bgr = cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR)

    return annotated_image_bgr

# checks if a frame index falls within any of the specified intervals
def is_within_intervals(frame_idx, intervals):
    return any(start <= frame_idx <= end for start, end in intervals)

# calculates bpm based on beats within the specified time window
def calculate_bpm(current_frame, beats, fps, window_duration):
    if len(beats) < 2:
        return 0
    
    # convert frames to seconds
    current_time = current_frame / fps
    beat_times = [beat / fps for beat in beats]
    
    # get recent beats within window
    recent_beats = [time for time in beat_times if current_time - time <= window_duration]
    
    if len(recent_beats) < 2:
        return 0
    
    # calculate time between first and last beat
    total_time = recent_beats[-1] - recent_beats[0]
    num_intervals = len(recent_beats) - 1
    
    # calculate and round bpm
    if total_time > 0:
        bpm = (num_intervals * 60) / total_time
    else:
        bpm = 0
    
    return round(bpm, 1)

# displays beat indicator and records bpm data
def print_beats(frame_index, output_frame, filtered_significant_beats, beats, fps, bpm_window, text_display_counter):
    # Ensure pygame is initialized
    if not pygame.get_init():
        pygame.init()
        
    try:
        window_size = get_window_size()
        screen = get_screen()

        # For pygame display (keep this for the UI)
        font = pygame.font.Font(None, 50)
        text = font.render("Beat!", True, (255, 255, 255))
        text_x = (window_size[0] - text.get_width()) // 2
        text_y = (window_size[1] - text.get_height()) // 2
    except Exception as e:
        print(f"Warning: pygame UI elements could not be initialized: {e}")
        # Continue without pygame display elements
        window_size = None
        screen = None
        font = None
        text = None
        text_x = 0
        text_y = 0

    # For video output - make sure to position text within the visible area
    font_out = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 2
    font_thickness = 2
    font_color = (255, 255, 255)  # White text
    text_out = "Beat!"
    text_size_out = cv2.getTextSize(text_out, font_out, font_scale, font_thickness)[0]
    
    # Position the text properly in the center of the frame
    text_x_out = (output_frame.shape[1] - text_size_out[0]) // 2
    text_y_out = 100  # Fixed position near the top where it's visible

    if frame_index in filtered_significant_beats:
        # Show on pygame display if available
        if screen is not None and font is not None:
            try:
                screen.blit(text, (text_x, text_y))
            except Exception as e:
                print(f"Warning: Could not display on pygame screen: {e}")
        
        # Write to output frame for video
        cv2.putText(output_frame, text_out, (text_x_out, text_y_out), 
                   font_out, font_scale, font_color, font_thickness)

        beats.append(frame_index)
        bpm = calculate_bpm(frame_index, beats, fps, bpm_window)

        # Display BPM info below the Beat! text
        bpm_info = f'BPM: {bpm}'
        cv2.putText(output_frame, bpm_info, 
                   (text_x_out, text_y_out + 60), font_out, 1, font_color, font_thickness)
        
        # Save BPM data to file
        full_bpm_info = f'Beats per minute (BPM) at frame {frame_index}: {bpm}\n'
        print(full_bpm_info)
        output_file = video_out_name()
        with open(output_file + '_auto_BPM.txt', 'a') as file:
            file.write(full_bpm_info)

        # Duration of text display
        text_display_counter = 3
    elif text_display_counter > 0:
        # Show on pygame display if available
        if screen is not None and font is not None:
            try:
                screen.blit(text, (text_x, text_y))
            except Exception as e:
                print(f"Warning: Could not display on pygame screen: {e}")
        
        # Write to output frame for video
        cv2.putText(output_frame, text_out, (text_x_out, text_y_out), 
                   font_out, font_scale, font_color, font_thickness)
        text_display_counter -= 1

    return text_display_counter

# processes video for second pass, displaying beats and generating analysis
# Simplified replacement for output_process_video in p_stage2.py
def output_process_video(cap, detector, filtered_significant_beats, processing_intervals, swaying_detector, mirror_detector, cueing_detector, elbow_detector, inverted_y):
    """
    Process video for second pass, displaying beats and generating analysis with side panel
    - Uses the passed detector to avoid timestamp errors
    - Fixes export directory issues
    - Adds time signature estimation
    """
    # Ensure pygame is initialized
    if not pygame.get_init():
        pygame.init()
        
    print("\n=== Cycle Two Debug Information ===")
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"FPS: {fps}")
    print(f"Total Frames: {total_frames}")
    print(f"Video Duration: {total_frames/fps:.2f} seconds")
    print(f"Number of beats to display: {len(filtered_significant_beats)}")
    print(f"Processing intervals: {processing_intervals}")
    print("================================\n")
    
    # Initialize parameters
    try:
        font = pygame.font.Font(None, 50)
        screen = get_screen()
    except Exception as e:
        print(f"Warning: pygame font initialization failed: {e}")
        # Continue without pygame-specific elements
        font = None
        screen = None
        
    bpm_window = 5
    beats = []
    current_bpm = 0
    beat_count = 0
    
    # Determine the start frame based on processing intervals
    start_frame = 0
    if processing_intervals:
        start_frame = min(start[0] for start in processing_intervals)
    
    # Initialize frame_index to the start frame of processing
    frame_index = start_frame
    
    # Get the original video dimensions
    video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Check if we need to apply cropping
    crop_rect = None
    try:
        with open("interface_config.json", "r") as f:
            config = json.load(f)
            crop_data = config.get("crop_rect", None)
            if crop_data:
                crop_rect = tuple(crop_data)  # [x, y, width, height]
                print(f"Applying crop: {crop_rect}")
                video_width = crop_data[2]  # Use the crop width
                video_height = crop_data[3]  # Use the crop height
    except Exception as e:
        print(f"No cropping configuration found: {str(e)}")
    
    # Calculate dimensions for output with side panel
    panel_width = 250
    output_width = video_width + panel_width
    output_height = video_height
    
    # Get the export path from the configuration
    export_path = get_export_path()
    
    # Create output directory if it doesn't exist
    os.makedirs(export_path, exist_ok=True)
    
    output_filename = os.path.join(export_path, video_out_name() + 'with_panel' + '.mp4')
    
    print(f"Writing output video to: {output_filename}")
    
    # Create VideoWriter for the combined output
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    panel_out = cv2.VideoWriter(output_filename, fourcc, fps, (output_width, output_height))
    
    # If the VideoWriter fails, try with a different codec
    if not panel_out.isOpened():
        print("Warning: Failed to open video writer with mp4v codec. Trying XVID.")
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        panel_out = cv2.VideoWriter(output_filename, fourcc, fps, (output_width, output_height))
        if not panel_out.isOpened():
            print("Error: Failed to create video writer with both mp4v and XVID codecs.")
            return
    
    # Initialize conducting metrics for the side panel
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
        
        # y_pos += 40
        # cv2.putText(panel, f"Pattern: {metrics['pattern_type']}", (10, y_pos), 
        #            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
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
    
    # If we have processing intervals, set the video position to the start frame
    if processing_intervals and len(processing_intervals) > 0:
        start_frame = min(start for start, _ in processing_intervals)
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        frame_index = start_frame
        print(f"Starting video processing at frame {start_frame}")
    
    # Main processing loop
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            break
            
        # Apply cropping if specified
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
        
        # Process the frame with MediaPipe - use the process_frame function
        # which utilizes the passed detector
        annotated_image_bgr = process_frame(cap, detector, image)
        
        # Skip if the frame couldn't be processed
        if annotated_image_bgr is None:
            continue
       
        # Create a copy of the frame for adding text and graphics
        output_frame = annotated_image_bgr.copy()
        
        # Get current interval info for the side panel
        current_interval = (0, total_frames)
        for interval in processing_intervals:
            if interval[0] <= frame_index <= interval[1]:
                current_interval = interval
                break
        
        # Process the frame if it's within the intervals
        if is_within_intervals(frame_index, processing_intervals):
            # For time signature detection, we need to track hand movements
            # We'll do this by collecting coordinates from the processed frames
            try:
                # Extract coordinates from the existing frame_array
                if frame_index in filtered_significant_beats:
                    # Since these are beat frames, likely to have good landmark detection
                    # We'll find corresponding y-coordinate from detected landmarks
                    
                    # This is where we'd normally get coordinates from MediaPipe
                    # But we'll use a simpler approach to avoid duplicate detection
                    # We'll use the y-coordinate from swaying detector if available
                    if hasattr(swaying_detector, 'last_right_hand_y'):
                        y_coords.append(swaying_detector.last_right_hand_y)
                    elif hasattr(swaying_detector, 'midpoint'):
                        # Fallback if right hand coords not available
                        y_coords.append(0.5)  # Use a default value
            except Exception as e:
                # Ignore errors in time signature detection
                pass
                
            # Update time signature periodically
            if frame_index - last_time_signature_update >= time_signature_update_interval and len(y_coords) >= 30:
                new_time_sig = update_time_signature()
                conducting_metrics["suggested_time_signature"] = new_time_sig
                last_time_signature_update = frame_index
                
                # Update pattern type based on time signature
                if new_time_sig == "2/4":
                    conducting_metrics["pattern_confidence"] = 80
                elif new_time_sig == "3/4":
                    conducting_metrics["pattern_confidence"] = 85
                elif new_time_sig == "4/4":
                    conducting_metrics["pattern_confidence"] = 90
                else:
                    conducting_metrics["pattern_type"] = "Compound"
                    conducting_metrics["pattern_confidence"] = 75
            
            # Check if the current frame is a beat frame
            # No need to adjust frame indices - filtered_significant_beats are already in global frame space
            if frame_index in filtered_significant_beats:
                # Keep the original BEAT text as requested
                text = "BEAT!"
                cv2.putText(output_frame, text, 
                           (output_frame.shape[1]//2 - 100, 100), 
                           cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 255), 3)
                               
                # Track beat for BPM calculation
                beats.append(frame_index)
                beat_count += 1
                
                # Calculate BPM
                current_bpm = calculate_bpm(frame_index, beats, fps, bpm_window)
                
                # Update metrics for side panel
                conducting_metrics["current_bpm"] = current_bpm
                conducting_metrics["beat_count"] = beat_count
                
                # Save BPM data to file
                bpm_info = f'Beats per minute (BPM) at frame {frame_index}: {current_bpm}\n'
                print(bpm_info)
                output_file = os.path.join(export_path, video_out_name() + '_auto_BPM.txt')
                with open(output_file, 'a') as file:
                    file.write(bpm_info)
            
            # Always display current BPM in a consistent location (not flashing)
            bpm_text = f"BPM: {conducting_metrics['current_bpm']:.1f}"
            cv2.putText(output_frame, bpm_text, 
                       (output_frame.shape[1]//2 - 80, 150), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            
            # Let swaying detector add its visualization
            try:
                swaying_detector.swaying_print(frame_index, output_frame)
            except Exception as e:
                print(f"Warning: Error in swaying detection: {e}")
            
            # Update sway index for side panel
            if hasattr(swaying_detector, 'swayingIndex'):
                conducting_metrics["sway_index"] = swaying_detector.swayingIndex
            
            # Get the midpoint from swaying detector for mirroring detection
            midpoint_x = swaying_detector.default_midpoint_x if hasattr(swaying_detector, 'default_midpoint_x') else 0.5

            # Use print_mirroring method for mirroring detection
            try:
                mirror_detector.print_mirroring(frame_index, output_frame, midpoint_x)
            except Exception as e:
                print(f"Warning: Error in mirroring detection: {e}")

            # Get the left hand y-coordinate for cueing detection
            left_hand_y = 0
            if frame_index < len(mirror_detector.left_hand_y):
                left_hand_y = mirror_detector.left_hand_y[frame_index]

            # Display cueing information (crescendo/decrescendo)
            try:
                cueing_detector.print_cueing(output_frame, mirror_detector, left_hand_y, inverted_y, frame_index)
            except Exception as e:
                print(f"Warning: Error in cueing detection: {e}")

            # Display elbow position warnings
            try:
                # Only check elbow position if we have valid data for this frame
                if frame_index < len(elbow_detector.elbow_coords) and frame_index < len(inverted_y):
                    elbow_detector.elbow_print(frame_index, output_frame, inverted_y)
            except Exception as e:
                print(f"Warning: Error in elbow detection: {e}")
        
        # Create side panel with current metrics
        side_panel = create_side_panel(
            conducting_metrics, 
            output_frame.shape[0], 
            panel_width, 
            frame_index, 
            current_interval
        )
        
        # Combine frame and side panel
        combined_frame = np.zeros((output_height, output_width, 3), dtype=np.uint8)
        combined_frame[:, :video_width] = output_frame
        combined_frame[:, video_width:] = side_panel
                
        # Write the combined frame to output
        if panel_out.isOpened():
            panel_out.write(combined_frame)
        else:
            print(f"Warning: Could not write frame {frame_index} to output video")
        
        # Check for escape key
        key = cv2.waitKey(5) & 0xFF
        if key == 27:
            break
            
        frame_index += 1
        
        # If we've reached the end of the processing interval, break out of the loop
        if processing_intervals and frame_index > max(end for _, end in processing_intervals):
            print(f"Reached end of processing interval at frame {frame_index}")
            break
    
    # cleanup
    print(f"Processed {frame_index - start_frame} frames")
    print(f"Output video saved to: {output_filename}")
    
    # Close video resources
    cap.release()
    if panel_out.isOpened():
        panel_out.release()
        
    # Don't quit pygame here, as it might be needed by other modules
    # pygame.quit()
    
    # Close all OpenCV windows
    cv2.destroyAllWindows()
    return

def get_window_size():
    from interface import get_window_size as get_size
    return get_size()


def get_screen():
    from interface import get_screen as get_scr
    return get_scr()


def display_frame(frame):
    from interface import display_frame as disp_frame
    return disp_frame(frame)