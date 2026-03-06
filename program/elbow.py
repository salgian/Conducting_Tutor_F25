# This Files includes the logic for dectecting
# the movement of the elbow and printing "watch elbow"

import cv2
import math

class elbowDetection:

    def __init__(self):
        self.elbow_coords = []
        self.shoulder_coords = []
        self.hip_coords = []
        self.debug = False  

    def elbow_calculation(self, elbow, shoulder, hip):
        self.elbow_coords.append(elbow)
        self.shoulder_coords.append(shoulder)
        self.hip_coords.append(hip)
    
    def elbow_print(self, frame_index, annotated_image_bgr, inverted_y):
        angle = self.calculate_angle(frame_index, inverted_y) 
        
        if self.debug:
            print(f"Elbow angle at frame {frame_index}: {angle}")
        
        # Reasonable threshold based on expected elbow angles during conducting
        angle_threshold = 32  # Reset to a reasonable value
        
        # Only print if the angle is significant and exceeds the threshold
        if angle is not None and angle > angle_threshold:
            cv2.putText(annotated_image_bgr, "Watch Elbow", (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2)
        return
    
    def calculate_angle(self, frame_index, inverted_y):
        # Check if frame_index is within the valid range
        if frame_index < 0 or frame_index >= len(self.shoulder_coords):
            if self.debug:
                print(f"Frame index {frame_index} is out of range. Returning None.")
            return None

        # Check if we have valid data for this frame
        if inverted_y is None or frame_index >= len(inverted_y):
            if self.debug:
                print(f"No inverted_y data for frame {frame_index}. Returning None.")
            return None

        # Get the original coordinates
        A = self.shoulder_coords[frame_index]   # Shoulder coordinates
        B = self.elbow_coords[frame_index]      # Elbow coordinates
        C = self.hip_coords[frame_index]        # Hip coordinates

        # Use the actual y-coordinates from the landmarks, not the same inverted_y value
        # This preserves the natural positioning of the joints
        A_y = A[1]  # Original shoulder y
        B_y = B[1]  # Original elbow y
        C_y = C[1]  # Original hip y

        # Create the vectors with original x and y positions
        AB = (B[0] - A[0], B_y - A_y)  # Vector from shoulder to elbow
        AC = (C[0] - A[0], C_y - A_y)  # Vector from shoulder to hip
        
        if self.debug:
            print(f"Original coords - A: {A}, B: {B}, C: {C}")
            print(f"Y-values - A_y: {A_y}, B_y: {B_y}, C_y: {C_y}")
        
        # Calculate dot product of AB and AC
        dot_product = AB[0] * AC[0] + AB[1] * AC[1]
        
        # Calculate magnitudes of AB and AC
        magnitude_AB = math.sqrt(AB[0]**2 + AB[1]**2)
        magnitude_AC = math.sqrt(AC[0]**2 + AC[1]**2)
        
        # Avoid division by zero
        if magnitude_AB < 0.001 or magnitude_AC < 0.001:
            if self.debug:
                print(f"Near-zero magnitude vector detected. Returning None.")
            return None
        
        # Cosine of the angle
        cos_theta = dot_product / (magnitude_AB * magnitude_AC)
        
        # Ensure the cosine value is within the valid range for acos due to floating point precision
        cos_theta = max(-1, min(1, cos_theta))
        
        # Calculate the angle in radians
        angle_radians = math.acos(cos_theta)
        
        # Convert the angle to degrees
        angle_degrees = math.degrees(angle_radians)
        
        if self.debug:
            print(f"Vectors - AB: {AB}, AC: {AC}")
            print(f"Magnitudes - AB: {magnitude_AB}, AC: {magnitude_AC}")
            print(f"Dot product: {dot_product}, Cosine: {cos_theta}")
            print(f"Calculated angle: {angle_degrees}")
        
        return angle_degrees