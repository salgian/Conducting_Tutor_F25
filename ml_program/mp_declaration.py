import mediapipe as mp
import cv2

class mediaPipeDeclaration:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

    def initialize_pose_detection(self):
        """Initialize MediaPipe Pose detection"""
        return self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

    def process_pose_detection(self, pose, rgb_frame):
        """Process pose detection on a frame"""
        return pose.process(rgb_frame)

    def draw_pose_landmarks(self, frame, results):
        """Draw pose landmarks on the frame"""
        if results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                frame,
                results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                self.mp_drawing_styles.get_default_pose_landmarks_style()
            )
        return frame
