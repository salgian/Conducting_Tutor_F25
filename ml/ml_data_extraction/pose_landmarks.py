class PoseLandmarks:
    """
    Extracts and stores wrist landmarks from a MediaPipe pose result.

    MediaPipe landmark indices:
        15 = Left  Wrist  (appears as Right when camera is flipped)
        16 = Right Wrist
    """

    # Named constants so the rest of the code never relies on magic numbers
    WRIST_INDEX = 15

    def __init__(self):
        self.wrist = (None, None)

    def update_landmarks(self, results):
        """Update stored landmarks from the latest MediaPipe detection result."""
        if results and results.pose_landmarks:
            landmark = results.pose_landmarks.landmark[self.WRIST_INDEX]
            self.wrist = (landmark.x, landmark.y)
        else:
            self.wrist = (None, None)

    def get_wrist(self):
        """Return the (x, y) tuple for the tracked wrist. Values are in [0, 1]."""
        return self.wrist

    # Kept for backwards-compatibility with any existing callers
    def get_pose_landmark_15(self):
        return self.get_wrist()
