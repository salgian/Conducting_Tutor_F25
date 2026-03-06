# This file has the logic or detecting if a person is raising or lowering their hand
# meaning that the band should print Decrescendo or crescendo
import cv2


class cueingDetection:
    def __init__(self):
        self.previous_left_hand_y = None  # Y-coordinate from 5 frames ago
        self.non_mirroring_frame_count = 0  # Counter for non-mirroring frames (used for waiting a certain amount of frames before processing)

    def print_cueing(self, annotated_image_bgr, mirror_detector, left_hand_y, inverted_y, frame_index):
        # Use the frame index to get the corresponding inverted y-coordinate
        left_hand_y_inverted = inverted_y[frame_index] if frame_index < len(inverted_y) else 0

        # Define a threshold for significant movement
        significant_movement_threshold = .005  

        # Check if mirroring is not detected
        if not mirror_detector.is_mirroring:
            self.non_mirroring_frame_count += 1  # Increment the counter

            # Check if we have a previous Y-coordinate to compare
            if self.previous_left_hand_y is not None and self.non_mirroring_frame_count >= 5:  # 10 is the number of frames we wait
                # Calculate the distance moved
                distance_moved = left_hand_y_inverted - self.previous_left_hand_y

                # Only detect movement if it exceeds the significant movement threshold
                if distance_moved > significant_movement_threshold:  # Hand is moving up
                    cv2.putText(annotated_image_bgr, "Decrescendo", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2)
                elif distance_moved < -significant_movement_threshold:  # Hand is moving down
                    cv2.putText(annotated_image_bgr, "Crescendo", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 2)

            # Update the previous Y-coordinate every frame
            if self.non_mirroring_frame_count >= 5:
                self.previous_left_hand_y = left_hand_y_inverted  # Store the current Y-coordinate for future comparison

        else:
            # Reset the counter and previous Y-coordinate if mirroring is detected
            self.non_mirroring_frame_count = 0
            self.previous_left_hand_y = None  # Reset previous Y-coordinate

