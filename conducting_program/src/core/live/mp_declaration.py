import mediapipe as mp
import numpy as np
import cv2
from mediapipe.framework.formats import landmark_pb2

class mediaPipeDeclaration:

    BaseOptions = mp.tasks.BaseOptions
    PoseLandmarker = mp.tasks.vision.PoseLandmarker
    PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
    VisionRunningMode = mp.tasks.vision.RunningMode

    @staticmethod
    def get_pose_landmarker(result_callback=None):
        options = mediaPipeDeclaration.PoseLandmarkerOptions(
                  base_options=mediaPipeDeclaration.BaseOptions(model_asset_path='pose_landmarks/pose_landmarker_lite.task'),
                  running_mode=mediaPipeDeclaration.VisionRunningMode.LIVE_STREAM,
                  result_callback=result_callback
                )
        return mediaPipeDeclaration.PoseLandmarker.create_from_options(options)

    @staticmethod
    def draw_landmarks_on_image(rgb_image, detection_result):
        pose_landmarks_list = detection_result.pose_landmarks
        annotated_image = np.copy(rgb_image)

        for pose_landmarks in pose_landmarks_list:
            pose_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
            pose_landmarks_proto.landmark.extend([
                landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in pose_landmarks
            ])
            mp.solutions.drawing_utils.draw_landmarks(
                annotated_image,
                pose_landmarks_proto,
                mp.solutions.pose.POSE_CONNECTIONS,
                mp.solutions.drawing_styles.get_default_pose_landmarks_style()
            )
        return annotated_image

    @staticmethod
    def initialize_pose_detection():
        #Initialize MediaPipe Pose detection
        mp_pose = mp.solutions.pose
        pose = mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        return pose

    @staticmethod
    def process_pose_detection(pose, rgb_frame):
        # Process pose detection on a frame
        return pose.process(rgb_frame)

    @staticmethod
    def draw_pose_landmarks(frame, results):
        # Draw only the conducting-hand marker (right wrist, landmark 15).
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            if len(landmarks) > 15:
                wrist = landmarks[15]
                h, w = frame.shape[:2]
                x_px = int(wrist.x * w)
                y_px = int(wrist.y * h)
                cv2.circle(frame, (x_px, y_px), 7, (0, 255, 0), -1)
        return frame

    @staticmethod
    def close_pose_detection(pose):
        """Close pose detection"""
        if pose is None:
            return
        try:
            pose.close()
        except ValueError:
            # Pose detection already closed, ignore
            pass

# Function to declare mediapipe processing
def declare_mp_processing():
    """Declare mediapipe processing for segments"""
    # Initialize mediapipe solutions
    mp_hands = mp.solutions.hands
    mp_pose = mp.solutions.pose
    
    # Return the initialized solutions
    return mp_hands, mp_pose