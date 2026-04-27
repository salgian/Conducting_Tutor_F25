import mediapipe as mp
import numpy as np
import cv2
import os
import sys

class mediaPipeDeclaration:

    BaseOptions = mp.tasks.BaseOptions
    PoseLandmarker = mp.tasks.vision.PoseLandmarker
    PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
    VisionRunningMode = mp.tasks.vision.RunningMode
    _smoothed_wrist_px = None
    _smoothing_alpha = 0.35 # smoothing factor for the wrist landmark

    @staticmethod
    def _resolve_task_model_path() -> str:
        """Resolve task model path for source and bundled execution."""
        source_path = os.path.join(os.path.dirname(__file__), "pose_landmarks", "pose_landmarker_lite.task")
        if os.path.exists(source_path):
            return source_path

        bundle_base = getattr(sys, "_MEIPASS", None)
        if bundle_base:
            bundled_path = os.path.join(
                bundle_base,
                "src",
                "core",
                "live",
                "pose_landmarks",
                "pose_landmarker_lite.task",
            )
            if os.path.exists(bundled_path):
                return bundled_path

        return source_path

    @staticmethod
    def get_pose_landmarker(result_callback=None):
        model_path = mediaPipeDeclaration._resolve_task_model_path()
        options = mediaPipeDeclaration.PoseLandmarkerOptions(
                  base_options=mediaPipeDeclaration.BaseOptions(model_asset_path=model_path),
                  running_mode=mediaPipeDeclaration.VisionRunningMode.LIVE_STREAM,
                  result_callback=result_callback
                )
        return mediaPipeDeclaration.PoseLandmarker.create_from_options(options)

    @staticmethod
    def draw_landmarks_on_image(rgb_image, detection_result):
        # Import lazily to avoid hard dependency on mediapipe.framework layout.
        try:
            from mediapipe.framework.formats import landmark_pb2
        except ModuleNotFoundError:
            return np.copy(rgb_image)

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
        # Initialize MediaPipe pose detection using whichever API is available.
        if hasattr(mp, "solutions"):
            mp_pose = mp.solutions.pose
            return mp_pose.Pose(
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )

        model_path = mediaPipeDeclaration._resolve_task_model_path()
        options = mediaPipeDeclaration.PoseLandmarkerOptions(
            base_options=mediaPipeDeclaration.BaseOptions(model_asset_path=model_path),
            running_mode=mediaPipeDeclaration.VisionRunningMode.IMAGE
        )
        return mediaPipeDeclaration.PoseLandmarker.create_from_options(options)

    @staticmethod
    def process_pose_detection(pose, rgb_frame):
        # Process pose detection on a frame for either solutions or tasks API.
        if hasattr(pose, "process"):
            return pose.process(rgb_frame)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        return pose.detect(mp_image)

    @staticmethod
    def _extract_landmarks(results):
        """Extract first-pose landmarks from either API result shape."""
        if not results or not hasattr(results, "pose_landmarks"):
            return None
        pose_landmarks = results.pose_landmarks
        if hasattr(pose_landmarks, "landmark"):
            return pose_landmarks.landmark
        if isinstance(pose_landmarks, list) and pose_landmarks:
            return pose_landmarks[0]
        return None

    @staticmethod
    def draw_pose_landmarks(frame, results, show_conducting_hand_marker=True):
        # Draw only the conducting-hand marker (right wrist, landmark 15).
        if not show_conducting_hand_marker:
            mediaPipeDeclaration._smoothed_wrist_px = None
            return frame
        landmarks = mediaPipeDeclaration._extract_landmarks(results)
        if landmarks and len(landmarks) > 15:
            wrist = landmarks[15]
            h, w = frame.shape[:2]
            x_px = int(wrist.x * w)
            y_px = int(wrist.y * h)
            current_point = (x_px, y_px)
            prev_point = mediaPipeDeclaration._smoothed_wrist_px

            if prev_point is None:
                smoothed_point = current_point
            else:
                alpha = mediaPipeDeclaration._smoothing_alpha
                smoothed_point = (
                    int(alpha * current_point[0] + (1.0 - alpha) * prev_point[0]),
                    int(alpha * current_point[1] + (1.0 - alpha) * prev_point[1]),
                )

            mediaPipeDeclaration._smoothed_wrist_px = smoothed_point
            cv2.circle(frame, smoothed_point, 7, (0, 255, 0), -1)
        else:
            mediaPipeDeclaration._smoothed_wrist_px = None
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
    if not hasattr(mp, "solutions"):
        return None, None
    mp_hands = mp.solutions.hands
    mp_pose = mp.solutions.pose
    
    # Return the initialized solutions
    return mp_hands, mp_pose