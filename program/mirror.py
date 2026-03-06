import cv2
import numpy as np
import os

# Check for mediapipe availability
try:
    import mediapipe as mp
    MIRROR_MODULES_AVAILABLE = True
except ImportError:
    MIRROR_MODULES_AVAILABLE = False

# Function to process video for mirror detection
def process_mirror_video(input_path, output_path):
    """Process video to detect mirror movements and save output"""
    cap = cv2.VideoCapture(input_path)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = None
    
    # Ensure the mirrorDetection class is used correctly
    # In the process_mirror_video function, instantiate the mirrorDetection class
    mirror_detector = mirrorDetection()
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Process frame for mirror detection using the mirror_detector instance
        mirror_detector.mirror_calculation(frame)
        processed_frame = frame  # Assuming the frame is processed in place
        
        # Initialize output video writer if not already done
        if out is None:
            height, width = processed_frame.shape[:2]
            out = cv2.VideoWriter(output_path, fourcc, 30.0, (width, height))
        
        # Write processed frame to output
        out.write(processed_frame)
    
    cap.release()
    if out:
        out.release()

# Function to output processed video
def output_mirror_video(input_path, output_path):
    """Output processed video with mirror detection"""
    if not MIRROR_MODULES_AVAILABLE:
        print("Mirror modules not available. Cannot process video.")
        return
    
    process_mirror_video(input_path, output_path)
    print(f"Processed video saved to {output_path}")

class mirrorDetection:

    def __init__(self):
        self.left_hand_x = []
        self.left_hand_y = []
        self.right_hand_x = []
        self.right_hand_y = []
        self.is_mirroring = False
        self.mirroring_history = []
        self.movement_history = []
        self.mirroring_count = 0
        self.last_left_x = None
        self.last_left_y = None
        self.last_right_x = None
        self.last_right_y = None

    def get_coordinates(self):
        return self.left_hand_x, self.left_hand_y, self.right_hand_x, self.right_hand_y

    def mirror_calculation(self, left_x, left_y, right_x, right_y):
        self.left_hand_x.append(left_x)
        self.left_hand_y.append(left_y)
        self.right_hand_x.append(right_x)
        self.right_hand_y.append(right_y)
        self.last_left_x = left_x
        self.last_left_y = left_y
        self.last_right_x = right_x
        self.last_right_y = right_y

    def detect_mirroring(self, left_x, right_x, left_y, right_y, midpoint_x):
        left_distance = abs(left_x - midpoint_x)
        right_distance = abs(right_x - midpoint_x)
        distance_threshold = 0.1
        similar_distance = abs(left_distance - right_distance) < distance_threshold
        y_movement_difference = left_y - right_y
        y_movement_similar = abs(y_movement_difference) < 0.075
        current_mirroring = similar_distance and y_movement_similar
        self.mirroring_history.append(current_mirroring)
        self.movement_history.append(similar_distance and y_movement_similar)
        if len(self.mirroring_history) > 5:
            self.mirroring_history.pop(0)
        if len(self.movement_history) > 10:
            self.movement_history.pop(0)
        if current_mirroring:
            self.mirroring_count += 1
        else:
            self.mirroring_count = 0
        if self.mirroring_count >= 15:
            self.is_mirroring = True
        elif self.is_mirroring and not any(self.mirroring_history[-5:]):
            self.is_mirroring = False
        return self.is_mirroring

    def print_mirroring(self, frame_index, annotated_image_bgr, midpoint_x):
        if frame_index < len(self.left_hand_x) and frame_index < len(self.right_hand_x):
            left_x = self.left_hand_x[frame_index]
            left_y = self.left_hand_y[frame_index]
            right_x = self.right_hand_x[frame_index]
            right_y = self.right_hand_y[frame_index]
            self.is_mirroring = self.detect_mirroring(left_x, right_x, left_y, right_y, midpoint_x)
            if self.is_mirroring:
                cv2.putText(annotated_image_bgr, "Mirroring", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2)
        return

    def get_last_positions(self):
        # Return last positions for movement detection
        return (self.last_left_x, self.last_left_y, 
                self.last_right_x, self.last_right_y)