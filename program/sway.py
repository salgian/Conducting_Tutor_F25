

import cv2


class swayingDetection:
    def __init__(self):
        self.default_midpoint_x = 0
        self.sway_threshold = 0.025  # Threshold for swaying detection
        self.midpoints_x = []  # Current midpoints
        self.midpointflag = False

        # For storing default midpoint history
        self.default_midpoint_history = []  # Track default midpoint changes
        self.frame_counter = 0  # Add frame counter
        self.update_interval = 100  # Update every 100 frames

    def midpoint_calculation(self, x12, x11):
        # Calculate and store current midpoint
        self.midpoint_x = abs(x12 - x11) * 0.5 + x12
        self.midpoints_x.append(self.midpoint_x)
        
        # Update frame counter and check if we should update default_midpoint_x
        if self.midpointflag:  # Only update if processing is active
            self.frame_counter += 1
            if self.frame_counter >= self.update_interval:
                self.default_midpoint_x = self.midpoint_x  # Update default to current
                self.frame_counter = 0  # Reset counter
            
        # Store current default midpoint for graphing
        self.default_midpoint_history.append(self.default_midpoint_x)

    def set_midpoint(self):
        # This method can be called to explicitly set the midpoint when processing starts
        self.midpointflag = True  # Set the flag to indicate midpoint is set
        self.default_midpoint_x = self.midpoints_x  # Set to current midpoint when called

    def set_midpoint_flag_true(self):
        self.midpointflag = True

    def set_midpoint_flag_false(self):
        self.midpointflag = False

    def swaying_print(self, frame_index, annotated_image_bgr):
        if frame_index < len(self.midpoints_x):
            midpoint_x = self.midpoints_x[frame_index]
            if midpoint_x > self.default_midpoint_x + self.sway_threshold or midpoint_x < self.default_midpoint_x - self.sway_threshold:
                cv2.putText(annotated_image_bgr, "Swaying", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2)
        return