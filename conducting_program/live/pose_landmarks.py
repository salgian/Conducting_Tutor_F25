import math

# Landmarks are written in reverse order, so the right side is the left side
# and the left side is the right side (this is because the camera is flipped)
class PoseLandmarks:
    def __init__(self):
        self.right_wrist_15 = (None, None)
        self.left_wrist_16 = (None, None)

        self.right_shoulder_11 = (None, None)
        self.left_shoulder_12 = (None, None)

        self.right_elbow_13 = (None, None)
        self.left_elbow_14 = (None, None)

        self.right_hip_23 = (None, None)
        self.left_hip_24 = (None, None)

        self.midpoint_x_axis = 0

    def update_landmarks(self, detection_result):
        if detection_result and detection_result.pose_landmarks:
            landmarks = detection_result.pose_landmarks.landmark
            if len(landmarks) > 16:
                # Hands
                self.right_wrist_15 = (landmarks[15].x, landmarks[15].y)
                self.left_wrist_16 = (landmarks[16].x, landmarks[16].y)
                # Shoulders
                self.right_shoulder_11 = (landmarks[11].x, landmarks[11].y)
                self.left_shoulder_12 = (landmarks[12].x, landmarks[12].y)
                # Elbows 
                self.right_elbow_13 = (landmarks[13].x, landmarks[13].y)
                self.left_elbow_14 = (landmarks[14].x, landmarks[14].y)
                # Hips
                self.right_hip_23 = (landmarks[23].x, landmarks[23].y)
                self.left_hip_24 = (landmarks[24].x, landmarks[24].y)
        else:
            # Reset landmarks when no detection
            self.right_wrist_15 = (None, None)
            self.left_wrist_16 = (None, None)
            self.right_shoulder_11 = (None, None)
            self.left_shoulder_12 = (None, None)
            self.right_elbow_13 = (None, None)
            self.left_elbow_14 = (None, None)
            self.right_hip_23 = (None, None)
            self.left_hip_24 = (None, None)

    def get_pose_landmark_15(self):
        return self.right_wrist_15
    
    def get_pose_landmark_16(self):
        return self.left_wrist_16
    
    def get_pose_landmark_14(self):
        return self.left_elbow_14
    
    def get_pose_landmark_13(self):
        return self.right_elbow_13
    
    def get_pose_landmark_24(self):
        return self.left_hip_24
    
    def get_pose_landmark_23(self):
        return self.right_hip_23

    def calculate_midpoint(self):
        if (self.left_shoulder_12[0] is not None and self.right_shoulder_11[0] is not None):
            self.midpoint_x_axis = abs(self.right_shoulder_11[0] - self.left_shoulder_12[0]) * 0.5 + self.left_shoulder_12[0]
    
    def get_midpoint(self):
        return self.midpoint_x_axis
