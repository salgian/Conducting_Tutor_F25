# Midpoint processing for conducting analysis
# Manages reference and live midpoint calculations with stability tracking

class MidpointProcessor:
    """Handles midpoint calculations, reference point management, and stability tracking."""
    
    def __init__(self):
        """Initialize midpoint processor with tracking variables."""
        # Reference midpoint tracking
        self.reference_midpoint = None
        self.live_midpoint = None
        self.last_midpoint_checked = None
        
        # Stability tracking for large movements
        self.midpoint_stable_count = 0
        
        # Update interval (seconds)
        self.update_interval = 3.0
    
    # -------- Accessor Methods --------
    
    def get_reference_midpoint(self):
        """Get the current reference midpoint."""
        return self.reference_midpoint
    
    def get_live_midpoint(self):
        """Get the current live midpoint."""
        return self.live_midpoint
    
    # -------- Midpoint Management --------
    
    def update_current_midpoint(self, pose_landmarks):
        """Update the live midpoint from current pose data."""
        if pose_landmarks.left_shoulder_12 and pose_landmarks.right_shoulder_11:
            left_x = pose_landmarks.left_shoulder_12[0]
            right_x = pose_landmarks.right_shoulder_11[0]
            if left_x is not None and right_x is not None:
                self.live_midpoint = (left_x + right_x) / 2
            else:
                self.live_midpoint = None
    
    def should_update_midpoint(self, current_time):
        """Check if enough time has passed to update the midpoint."""
        return (current_time - self.last_midpoint_checked) >= self.update_interval
    
    def update_midpoint_check(self, pose_landmarks, clock_manager):
        """Check and update reference midpoint if needed."""
        current_time = clock_manager.get_current_timestamp()
        
        # Check if it's time to update (every 3 seconds)
        if not self.should_update_midpoint(current_time):
            return False  # Not time to check yet

        # 3 seconds have passed update reference midpoint; require a valid live midpoint
        if self.live_midpoint is None:
            self.last_midpoint_checked = current_time
            return False

        # Delegate the evaluation logic to a dedicated method
        updated = self.evaluate_reference_update(current_time)
        self.last_midpoint_checked = current_time
        return updated

    def evaluate_reference_update(self, current_time):
        """Evaluate whether to update reference midpoint based on movement."""
        midpoint_difference = abs(self.live_midpoint - self.reference_midpoint)

        # Micro-adjust when close to reference (smooth small drift)
        if midpoint_difference <= 0.02:
            self.reference_midpoint = self.live_midpoint
            self.midpoint_stable_count = 0
            print("Reference midpoint micro-adjusted")
            return True

        # Large movement: require stability across 2 checks (6s total) before updating
        if midpoint_difference > 0.05:
            self.midpoint_stable_count += 1
            if self.midpoint_stable_count >= 2:
                self.reference_midpoint = self.live_midpoint
                self.midpoint_stable_count = 0
                print("Reference midpoint updated (stable large move)")
                return True
        else:
            # Small-to-medium movement: do not update reference; reset stability counter
            self.midpoint_stable_count = 0
        return False
    
    def initialize_reference_midpoint(self, pose_landmarks, clock_manager):
        """Initialize the reference midpoint on first frame."""
        self.update_current_midpoint(pose_landmarks)
        if self.live_midpoint is not None:
            self.reference_midpoint = self.live_midpoint
            self.last_midpoint_checked = clock_manager.get_current_timestamp()
