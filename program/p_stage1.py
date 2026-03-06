import os
import json
import cv2
import numpy as np
import pygame
import mediapipe as mp

from mp_declaration import mediaPipeDeclaration

# processes a single frame and returns the annotated image and detection results
def process_frame(cap, detector, image):
    if image is None:
        return None, None

    # Add debug print for frame position
    print(f"Current frame position: {int(cap.get(cv2.CAP_PROP_POS_FRAMES))}", end='\r')

    # process image through mediapipe
    frame_timestamp_ms = round(cap.get(cv2.CAP_PROP_POS_MSEC))
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
    detection_result = detector.detect_for_video(mp_image, frame_timestamp_ms)
    
    # convert back to bgr for display
    annotated_image = mediaPipeDeclaration.draw_landmarks_on_image(image_rgb, detection_result)
    annotated_image_bgr = cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR)

    return annotated_image_bgr, detection_result

# processes landmarks for each frame, tracking hand positions and movement
def process_landmarks(detection_result, frame_array, processed_frame_array, processing_active, swaying_detector, mirror_detector, elbow_detector=None):
    pose_landmarks_list = detection_result.pose_landmarks
    if pose_landmarks_list:
        for landmarks in pose_landmarks_list:
            if len(landmarks) > 16:
                # get right hand coordinates
                x16 = landmarks[16].x
                y16 = landmarks[16].y
                
                # store coordinates
                frame_array.append((x16, y16))
                if processing_active:
                    processed_frame_array.append((x16, y16))
                else:
                    processed_frame_array.append((np.nan, np.nan))

                # update movement detectors
                mirror_detector.mirror_calculation(landmarks[15].x, landmarks[15].y, landmarks[16].x, landmarks[16].y)
                swaying_detector.midpoint_calculation(landmarks[12].x, landmarks[11].x)
                
                # Update elbow detector if provided
                if elbow_detector:
                    # Extract landmarks for elbow detection (elbow, shoulder, hip)
                    elbow_pos = (landmarks[14].x, landmarks[14].y)  # Right elbow
                    shoulder_pos = (landmarks[12].x, landmarks[12].y)  # Right shoulder
                    hip_pos = (landmarks[24].x, landmarks[24].y)  # Right hip
                    elbow_detector.elbow_calculation(elbow_pos, shoulder_pos, hip_pos)
                
                # Set the midpoint when processing starts
                if processing_active and not swaying_detector.midpointflag:
                    swaying_detector.set_midpoint()  # This will set the default midpoint only when processing starts
    return

# main video processing loop with predetermined intervals
def process_video(cap, detector, frame_array, processed_frame_array, processing_intervals, swaying_detector, mirror_detector, elbow_detector=None):
    print("\n=== Video Processing Debug Information ===")
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    print(f"Starting video processing...")
    print(f"Expected total frames: {total_frames}")
    print(f"Video FPS: {fps}")
    print(f"Processing intervals: {processing_intervals}")
    
    # initialize frame counter
    frame_number = 0
    frames_read = 0

    # Check if we need to apply cropping
    crop_rect = None
    try:
        with open("interface_config.json", "r") as f:
            config = json.load(f)
            crop_data = config.get("crop_rect", None)
            if crop_data:
                crop_rect = tuple(crop_data)  # [x, y, width, height]
                print(f"Applying crop: {crop_rect}")
    except:
        print("No cropping configuration found.")

    # Track if we're inside a processing interval
    was_processing = False
    is_processing = False
    
    # Determine the range of frames to process based on processing_intervals
    start_process = total_frames
    end_process = 0
    
    # Find the minimum start and maximum end frames from all intervals
    if processing_intervals:
        for start, end in processing_intervals:
            start_process = min(start_process, start)
            end_process = max(end_process, end)
        
        print(f"Processing frame range: {start_process} to {end_process}")
        
        # Set the initial position to the first frame we need to process
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_process)
        frame_number = start_process
    else:
        print("Warning: No processing intervals defined, processing entire video")

    while cap.isOpened() and (not processing_intervals or frame_number <= end_process):
        success, image = cap.read()
        frames_read += 1
        
        if not success:
            print(f"\nTotal frames read: {frames_read}")
            break

        # verify frame is valid
        if image is None:
            continue
            
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

        # Determine if this frame is in a processing interval
        was_processing = is_processing  # Save previous state
        is_processing = False
        
        for start, end in processing_intervals:
            if start <= frame_number <= end:
                is_processing = True
                break
        
        # Handle state changes
        if is_processing and not was_processing:
            # Start of processing interval
            swaying_detector.set_midpoint_flag_true()
            swaying_detector.set_midpoint()
            print(f"Started processing at frame: {frame_number}")
            
        elif was_processing and not is_processing:
            # End of processing interval
            swaying_detector.set_midpoint_flag_false()
            print(f"Ended processing at frame: {frame_number}")
        
        # process current frame with MediaPipe
        annotated_image_bgr, detection_result = process_frame(cap, detector, image)
        
        if annotated_image_bgr is not None:
            # Process landmarks and save annotated frame
            process_landmarks(detection_result, frame_array, processed_frame_array, 
                             is_processing, swaying_detector, mirror_detector, elbow_detector)
        # increment frame counter
        frame_number += 1
        
    # cleanup resources
    cap.release()
    cv2.destroyAllWindows()

    print(f"Actual processed frames: {frame_number - start_process}")
    print(f"Number of processing intervals: {len(processing_intervals)}")
    print("=====================================\n")

    return frame_array, processed_frame_array, processing_intervals