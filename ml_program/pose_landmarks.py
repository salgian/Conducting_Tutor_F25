class PoseLandmarks:
    def __init__(self):
        # We'll store only what we need right now: right wrist(15) and left wrist(16)
        # Note: Camera is flipped, so indices might feel swapped depending on your view
        self.right_wrist = (None, None)

    def update_landmarks(self, results):
        if results and results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            # Mediapipe indices: 15=Right Wrist, 16=Left Wrist
            self.right_wrist = (landmarks[15].x, landmarks[15].y)
        else:
            self.right_wrist = (None, None)

    def get_pose_landmark_15(self):
        return self.right_wrist
