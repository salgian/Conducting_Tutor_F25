import mediapipe as mp
import numpy as np
from mediapipe.framework.formats import landmark_pb2

# Import specific functions
from main_segment_processor import process_segment

class mediaPipeDeclaration:

    BaseOptions = mp.tasks.BaseOptions
    PoseLandmarker = mp.tasks.vision.PoseLandmarker
    PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
    VisionRunningMode = mp.tasks.vision.RunningMode

    @staticmethod
    def get_pose_landmarker():
        options = mediaPipeDeclaration.PoseLandmarkerOptions(
                  base_options=mediaPipeDeclaration.BaseOptions(model_asset_path='pose_landmarks/pose_landmarker_full.task'),
                  running_mode=mediaPipeDeclaration.VisionRunningMode.VIDEO
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

# Function to declare mediapipe processing
def declare_mp_processing():
    """Declare mediapipe processing for segments"""
    # Initialize mediapipe solutions
    mp_hands = mp.solutions.hands
    mp_pose = mp.solutions.pose
    
    # Process segment with mediapipe
    def process_with_mediapipe(segment):
        with mp_hands.Hands() as hands, mp_pose.Pose() as pose:
            # Process segment
            processed_segment = process_segment(segment, hands, pose)
            return processed_segment
    
    return process_with_mediapipe