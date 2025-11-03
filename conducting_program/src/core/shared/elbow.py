# Monitors elbow angles to detect raised arm positions

import math

class ElbowDetection: 
    """Detects when elbows are raised above threshold angle during conducting."""
    
    def __init__(self):
        """Initialize elbow detection with angle threshold."""
        self.angle_threshold = 32  # Degrees - angle above which elbow is considered raised
        self.watch_left_elbow = False
        self.watch_right_elbow = False
        self.left_angle = None
        self.right_angle = None

    # -------- Accessor Methods --------
    
    def get_watch_left_elbow(self):
        """Returns whether left elbow is currently raised."""
        return self.watch_left_elbow
    
    def get_watch_right_elbow(self):
        """Returns whether right elbow is currently raised."""
        return self.watch_right_elbow

    def get_left_angle(self):
        """Returns the current left elbow angle."""
        return self.left_angle
    
    def get_right_angle(self):
        """Returns the current right elbow angle."""
        return self.right_angle

    # -------- Angle Calculations --------

    def calculate_angle(self, pose_landmarks, side):
        """
        Calculate the armpit angle (arm to torso) for the specified side.
        
        Args:
            pose_landmarks: PoseLandmarks object containing landmark data
            side: 'left' or 'right' to specify which side to calculate
        
        Returns:
            angle in degrees, or None if insufficient data
        """
        if side == 'left':
            shoulder = pose_landmarks.left_shoulder_12
            elbow = pose_landmarks.left_elbow_14
            hip = pose_landmarks.left_hip_24
        elif side == 'right':
            shoulder = pose_landmarks.right_shoulder_11
            elbow = pose_landmarks.right_elbow_13
            hip = pose_landmarks.right_hip_23
        else:
            return None
        
        # # Check if all landmarks are available
        # if (shoulder[0] is None or elbow[0] is None or hip[0] is None):
        #     return None
        
        # Get landmark coordinates
        shoulder_x, shoulder_y = shoulder
        elbow_x, elbow_y = elbow
        hip_x, hip_y = hip
        
        # Create vectors from shoulder point (the vertex of the angle)
        # Vector 1: shoulder -> elbow (arm direction)
        arm_x = elbow_x - shoulder_x
        arm_y = elbow_y - shoulder_y
        
        # Vector 2: shoulder -> hip (torso direction)
        torso_x = hip_x - shoulder_x
        torso_y = hip_y - shoulder_y
        
        # Calculate angle between arm and torso vectors
        angle_degrees = self._calculate_vector_angle(arm_x, arm_y, torso_x, torso_y)
        
        if angle_degrees is not None:
            return int(angle_degrees)
        else:
            return None

    def calculate_angles(self, pose_landmarks):
        """Calculate both left and right angles independently."""
        # Calculate left angle if landmarks are available
        if (pose_landmarks.left_shoulder_12[0] is not None and 
            pose_landmarks.left_elbow_14[0] is not None and 
            pose_landmarks.left_hip_24[0] is not None):
            self.left_angle = self.calculate_angle(pose_landmarks, 'left')
        else:
            self.left_angle = None
            
        # Calculate right angle if landmarks are available
        if (pose_landmarks.right_shoulder_11[0] is not None and 
            pose_landmarks.right_elbow_13[0] is not None and 
            pose_landmarks.right_hip_23[0] is not None):
            self.right_angle = self.calculate_angle(pose_landmarks, 'right')
        else:
            self.right_angle = None

    def _calculate_vector_angle(self, v1_x, v1_y, v2_x, v2_y):
        """Calculate angle between two vectors in degrees."""
        # Calculate vector magnitudes
        magnitude_1 = math.hypot(v1_x, v1_y)
        magnitude_2 = math.hypot(v2_x, v2_y)
        
        # Avoid division by zero
        if magnitude_1 == 0 or magnitude_2 == 0:
            return None
        
        # Calculate dot product
        dot_product = v1_x * v2_x + v1_y * v2_y
        
        # Calculate cosine of angle 
        cos_angle = dot_product / (magnitude_1 * magnitude_2)
        cos_angle = max(-1.0, min(1.0, cos_angle))
        
        # Convert to degrees
        angle_radians = math.acos(cos_angle)
        return math.degrees(angle_radians)

    # -------- Detection Logic --------

    def _check_left_elbow(self):
        """Check if left elbow angle exceeds threshold."""
        if self.left_angle is not None and self.left_angle > self.angle_threshold:
            if not self.watch_left_elbow:
                self.watch_left_elbow = True
        else:
            if self.watch_left_elbow:
                self.watch_left_elbow = False
        
    def _check_right_elbow(self):
        """Check if right elbow angle exceeds threshold."""
        if self.right_angle is not None and self.right_angle > self.angle_threshold:
            if not self.watch_right_elbow:
                self.watch_right_elbow = True
        else:
            if self.watch_right_elbow:
                self.watch_right_elbow = False

    def main(self, pose_landmarks):
        """Main detection loop - calculates angles and checks for raised elbows."""
        # Calculate both angles independently
        self.calculate_angles(pose_landmarks)

        # Check each elbow independently
        self._check_left_elbow()
        self._check_right_elbow()
