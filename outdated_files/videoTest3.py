import cv2
import mediapipe as mp
import time
from mediapipe.framework.formats import landmark_pb2
import numpy as np

BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

# draw landmarks
def draw_landmarks_on_image(rgb_image, detection_result):
    pose_landmarks_list = detection_result.pose_landmarks
    annotated_image = np.copy(rgb_image)

    # Loop through the detected poses to visualize.
    for idx in range(len(pose_landmarks_list)):
        pose_landmarks = pose_landmarks_list[idx]

        # Draw the pose landmarks.
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

# Create a PoseLandmarker object
options = PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path='pose_landmarker_lite.task'),
    running_mode=VisionRunningMode.VIDEO
)

detector = PoseLandmarker.create_from_options(options)

# Open the video file
cap = cv2.VideoCapture('4-4legato(3).mp4')

if not cap.isOpened():
    print("Error: Could not open video file")

while cap.isOpened():
    success, image = cap.read()

    if not success:
        print("Ignoring empty camera frame.")
        break

    roi = image[450:900, 600:1500]
    # Resize the ROI to a specific size
    roi_resized = cv2.resize(roi, (1280, 720))
    image = roi_resized

    # frame_timestamp_ms = int(round(time.time() * 1000)) | how we get time
    frame_timestamp_ms = round(cap.get(cv2.CAP_PROP_POS_MSEC))

    # Convert to RGB (MediaPipe works with RGB format)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Convert the image to a MediaPipe format
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)

    # detect pose landmarks from the image
    detection_result = detector.detect_for_video(mp_image, frame_timestamp_ms)

    # Draw landmarks on the image
    annotated_image = draw_landmarks_on_image(image_rgb, detection_result)

    # Convert back to BGR for OpenCV display
    annotated_image_bgr = cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR)
    
    # Display the annotated image
    cv2.imshow('Pose Landmarks', annotated_image_bgr)

    pose_landmarks_list = detection_result.pose_landmarks
    if len(pose_landmarks_list) > 0:
        # getting dimensions of the window
        h, w, _ = image.shape
        #add code for the algortim here.

    # Press 'q' to quit
    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
