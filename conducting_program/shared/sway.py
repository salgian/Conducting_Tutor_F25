
# Sway detection for conducting analysis
# Monitors midpoint movement to detect excessive swaying

class SwayDetection:
    """Detects when the conductor's midpoint moves beyond acceptable thresholds."""
    
    def __init__(self):
        """Initialize sway detection with movement threshold."""
        self.sway_threshold = 0.025  # Threshold for swaying detection
        self.sway_flag = False

    # -------- Accessor Methods --------

    def get_threshold(self):
        """Returns the sway threshold value."""
        return self.sway_threshold

    def get_sway_flag(self): 
        """Returns whether swaying is currently detected."""
        return self.sway_flag

    # -------- Detection Logic --------

    def _set_sway_flag(self, reference_midpoint, new_midpoint):
        """Set the sway flag based on current midpoint position."""
        if reference_midpoint is None or new_midpoint is None:
            self.sway_flag = False
            return
        
        left_threshold = reference_midpoint + self.sway_threshold
        right_threshold = reference_midpoint - self.sway_threshold
        self.sway_flag = (new_midpoint > left_threshold or new_midpoint < right_threshold)

    def main(self, midpoint, new_midpoint):
        """Main detection loop - checks for swaying."""
        if midpoint is None:
            self.sway_flag = False
            return

        # Check if we are swaying
        self._set_sway_flag(midpoint, new_midpoint)

