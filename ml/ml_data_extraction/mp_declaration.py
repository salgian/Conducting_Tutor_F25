import mediapipe as mp


class mediaPipeDeclaration:
    """
    Thin wrapper around the MediaPipe Pose solution.

    Keeps all MediaPipe imports and configuration in one place so the
    rest of the codebase never has to import mediapipe directly.
    """

    # Confidence thresholds — adjust here to tune detection quality
    MIN_DETECTION_CONFIDENCE = 0.5
    MIN_TRACKING_CONFIDENCE  = 0.5

    def __init__(self):
        self.mp_pose           = mp.solutions.pose
        self.mp_drawing        = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

    # ── Pose detection ───────────────────────────────

    def initialize_pose_detection(self):
        """Create and return a MediaPipe Pose instance."""
        return self.mp_pose.Pose(
            min_detection_confidence=self.MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=self.MIN_TRACKING_CONFIDENCE,
        )

    def process_pose_detection(self, pose, rgb_frame):
        """
        Run pose estimation on a single RGB frame.
        Returns the raw MediaPipe result object.
        """
        return pose.process(rgb_frame)

    # ── Visualisation ────────────────────────────────

    def draw_pose_landmarks(self, frame, results):
        """
        Overlay pose landmarks on a BGR frame (optional visualisation).
        Returns the annotated frame.
        """
        if results and results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                frame,
                results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                self.mp_drawing_styles.get_default_pose_landmarks_style(),
            )
        return frame
