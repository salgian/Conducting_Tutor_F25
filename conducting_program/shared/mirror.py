
# Mirror detection for conducting analysis
# Detects when both hands are positioned symmetrically around the midpoint

class MirrorDetection: 
    """Detects when both hands are positioned symmetrically around the midpoint."""
    
    def __init__(self):
        """Initialize mirror detection with position thresholds."""
        self.hands = {
            'left': {'x': None, 'y': None},
            'right': {'x': None, 'y': None}
        }

        self.y_threshold = 0.075  # Vertical position threshold for mirroring
        self.x_threshold = 0.05   # Horizontal position threshold for mirroring

        self.before_starting = None
        self.before_ending = None
        self.mirroring_flag = False

    # -------- Accessor Methods --------

    def get_mirroring_flag(self):
        """Returns whether hands are currently in mirroring position."""
        return self.mirroring_flag

    # -------- Detection Logic --------

    def _check_hands_available(self):
        """Check if both hands have valid positions."""
        return (self.hands['left']['x'] is not None and self.hands['left']['y'] is not None and
                self.hands['right']['x'] is not None and self.hands['right']['y'] is not None)

    def mirror_on_y(self):
        """Check if hands are at similar vertical positions."""
        if not self._check_hands_available():
            return False
        return abs(self.hands['left']['y'] - self.hands['right']['y']) < self.y_threshold

    def mirror_on_x(self, current_midpoint):
        """Check if hands are symmetrically positioned around the midpoint."""
        if not self._check_hands_available():
            return False
        left_distance = abs(self.hands['left']['x'] - current_midpoint)
        right_distance = abs(self.hands['right']['x'] - current_midpoint)
        return abs(left_distance - right_distance) < self.x_threshold

    def buffer_start_time(self, current_time, interval_seconds=0.5):
        """Check if enough time has passed to confirm mirroring start."""
        if self.before_starting is None:
            self.before_starting = current_time
            return False  # Need to wait the full interval

        return (current_time - self.before_starting) >= interval_seconds

    def buffer_end_time(self, current_time, interval_seconds=0.5):
        """Check if enough time has passed to confirm mirroring end."""
        if self.before_ending is None:
            self.before_ending = current_time
            return False  # Need to wait the full interval

        return (current_time - self.before_ending) >= interval_seconds

    def main(self, pose_landmarks, clock_manager, current_midpoint):
        """Main detection loop - analyzes hand positions for mirroring."""
        # Update hand positions
        left_hand = pose_landmarks.get_pose_landmark_16()  # Left wrist
        right_hand = pose_landmarks.get_pose_landmark_15()  # Right wrist
        
        if left_hand and right_hand:
            self.hands['left']['x'], self.hands['left']['y'] = left_hand
            self.hands['right']['x'], self.hands['right']['y'] = right_hand
        else:
            # Reset hand positions if not available
            self.hands['left'] = {'x': None, 'y': None}
            self.hands['right'] = {'x': None, 'y': None}
            return
        
        current_time = clock_manager.get_current_timestamp()

        # Check if currently mirroring
        is_mirroring = self.mirror_on_y() and self.mirror_on_x(current_midpoint)

        if is_mirroring:
            if not self.mirroring_flag:
                # Start buffering for mirroring
                if self.buffer_start_time(current_time, 0.5):
                    self.mirroring_flag = True
                    print("Mirroring")
            else:
                # Already confirmed mirroring - keep printing
                print("Mirroring")
                # Reset end buffer since we're still mirroring
                self.before_ending = None
        else:
            # Not mirroring
            if self.mirroring_flag:
                # Start buffering for end of mirroring
                if self.buffer_end_time(current_time, 0.5):
                    self.mirroring_flag = False
                    # Reset buffers for next cycle
                    self.before_starting = None
                    self.before_ending = None
                else:
                    # Still in end buffer - keep printing
                    print("Mirroring")
            else:
                # Not mirroring and not flagged - reset start buffer
                self.before_starting = None