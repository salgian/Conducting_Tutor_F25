import cv2
import matplotlib.pyplot as plt
import pickle
import mediapipe as mp
from scipy.signal import find_peaks
import numpy as np
import time
from mediapipe.framework.formats import landmark_pb2


BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

# 2D array to store coordinates
frame_array = []
frame_rate = 24

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
# Creates / initializing the poselandmarker
detector = PoseLandmarker.create_from_options(options)

# For video input:
cap = cv2.VideoCapture('4-4stacatto(3).mp4')

# Initialize flags and variables
processing_active = False
start_frame = None
end_frame = None
frame_number = 0

# Initialize VideoWriter for output video
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = int(cap.get(cv2.CAP_PROP_FPS))
out = cv2.VideoWriter('annotated_output.avi', cv2.VideoWriter_fourcc(*'MJPG'), fps, (frame_width, frame_height))

# Running to do calculations- the first time
while cap.isOpened():
    success, image = cap.read()
    if not success:
        if processing_active and end_frame is None:
            end_frame = frame_number - 1
            print(f"Processing stopped at the last frame: {end_frame}")
        break

    # Crop a region of interest (ROI) from the frame
    roi = image[450:900, 600:1500]
    roi_resized = cv2.resize(roi, (1280, 720))
    image = roi_resized

    frame_timestamp_ms = round(cap.get(cv2.CAP_PROP_POS_MSEC))
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
    detection_result = detector.detect_for_video(mp_image, frame_timestamp_ms)
    annotated_image = draw_landmarks_on_image(image_rgb, detection_result)
    annotated_image_bgr = cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR)

    # Only process frames between start_frame and end_frame
    pose_landmarks_list = detection_result.pose_landmarks
    if processing_active and start_frame is not None and (end_frame is None or frame_number <= end_frame):
        if pose_landmarks_list:
            for landmarks in pose_landmarks_list:
                if len(landmarks) > 15:
                    x15 = landmarks[15].x
                    y15 = landmarks[15].y
                    frame_array.append((x15, y15))

    # After the loop, prepare the x and y lists from frame_array
    x = [coord[0] for coord in frame_array]  
    y = [coord[1] for coord in frame_array] 

    # Display the current frame number
    cv2.putText(image, f'Frame: {frame_number}', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2)

    # Show the video feed
    cv2.imshow('Video Feed', annotated_image_bgr)

    # Write the annotated frame to the output video
    out.write(annotated_image_bgr)
    # print(f"Frame {frame_number} written to output video.")

    # Check for user input to start/stop processing
    key = cv2.waitKey(5) & 0xFF
    if key == ord('s'):  # Press 's' to mark the start frame
        if not processing_active:
            start_frame = frame_number
            processing_active = True
            print(f"Processing started at frame {start_frame}")
    elif key == ord('e'):  # Press 'e' to mark the end frame
        if processing_active:
            end_frame = frame_number
            processing_active = False
            print(f"Processing stopped at frame {end_frame}")
    elif key == 27:  # Press 'ESC' to exit
        break

    frame_number += 1

cap.release()
out.release()
cv2.destroyAllWindows()

# If the end frame was never set, default to the last frame
if end_frame is None:
    end_frame = frame_number - 1
    print(f"Processing stopped at the last frame: {end_frame}")
    
# Find peaks and valleys in x and y coordinates
x_peaks, _ = find_peaks(x)
x_valleys, _ = find_peaks([-val for val in x])
# Find peaks and valleys in y coordinates
y_peaks, _ = find_peaks(y)
y_valleys, _ = find_peaks([-val for val in y])

# Function to filter peaks and valleys based on a threshold
def filter_significant_points(points, threshold):
    if len(points) == 0:
        return []
    filtered_points = [points[0]]  # Start with the first point
    for i in range(1, len(points)):
        if points[i] - filtered_points[-1] > threshold:
            filtered_points.append(points[i])
    return filtered_points

# Apply filtering to ensure peaks and valleys are not closer than the threshold
threshold = 15  # Define a threshold in number of frames
# Filter x_peaks and x_valleys
filtered_x_peaks = filter_significant_points(x_peaks, threshold)
filtered_x_valleys = filter_significant_points(x_valleys, threshold)
# Filter y_peaks and y_valleys
filtered_y_peaks = filter_significant_points(y_peaks, threshold)
filtered_y_valleys = filter_significant_points(y_valleys, threshold)

# Combine the filtered peaks and valleys
combined_peaks = sorted(set(x_peaks).union(set(y_peaks))) 
combined_valleys = sorted(set(x_valleys).union(set(y_valleys)))  

# Convert combined_peaks and combined_valleys to standard Python integers for safe processing
combined_peaks = [int(p) for p in combined_peaks]
combined_valleys = [int(v) for v in combined_valleys]

filtered_significant_beats = combined_peaks.copy()  

filtered_significant_valleys = combined_valleys.copy()
filtered_significant_beats.extend(filtered_significant_valleys) 

filtered_significant_beats = filter_significant_points(filtered_significant_beats, threshold)

# OpenCV window name for displaying annotated frames
window_name = 'Annotated Frames'
frame_index = 0
frame_skip = 1  # Process every frame

# Initialize for second video capture loop
cap = cv2.VideoCapture('4-4stacatto(3).mp4')
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
size = (frame_width, frame_height)
fps = int(cap.get(cv2.CAP_PROP_FPS))  

# Change codec if necessary
out = cv2.VideoWriter('4-4stacatto(2)_output.avi', cv2.VideoWriter_fourcc(*'MJPG'), fps, size)

# Initialize text properties
font = cv2.FONT_HERSHEY_SIMPLEX
font_scale = 2  
font_thickness = 2
font_color = (255, 255, 255)
text_display_duration = 3  
text_display_counter = 0

# Initialize variables for beat detection
prev_beat = None
prev_bpm = 0
bpm = None  
last_frame_timestamp = 0
frame_index = 0  

# Video frame processing loop
while cap.isOpened():
    success, image = cap.read()
    if not success:
        print("Ending processing.")
        break

    roi = image[450:900, 600:1500] if image.shape[0] >= 900 and image.shape[1] >= 1500 else image
    roi_resized = cv2.resize(roi, (frame_width, frame_height))
    image_bgr = roi_resized

    frame_timestamp_ms = last_frame_timestamp + (1000 / fps)
    last_frame_timestamp = frame_timestamp_ms

    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
    frame_timestamp_microseconds = int(frame_timestamp_ms * 1000)

    detection_result = detector.detect_for_video(mp_image, frame_timestamp_microseconds)
    annotated_image = draw_landmarks_on_image(image_rgb, detection_result)
    annotated_image_bgr = cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR)

    if start_frame <= frame_index <= end_frame:
        if frame_index in filtered_significant_beats:
            text = "Beat!"
            text_size = cv2.getTextSize(text, font, font_scale, font_thickness)[0]
            text_x = (image_rgb.shape[1] - text_size[0]) // 2
            text_y = (image_rgb.shape[0] + text_size[1]) // 2
            cv2.putText(annotated_image_bgr, text, (text_x, text_y), font, font_scale, font_color, font_thickness)
            if prev_beat is not None:
                frames_between_beats = frame_index - prev_beat
                time_between_beats = frames_between_beats / fps
                bpm = 60 / time_between_beats
            else:
                bpm = prev_bpm
            prev_beat = frame_index
            bpm_info = f'Beats per minute (BPM) at frame {frame_index}: {bpm}\n'
            output_file = '4-4stacatto(2).mp4_auto_BPM.txt'
            with open(output_file, 'a') as file:
                print(bpm_info, end='')
                file.write(bpm_info)
            text_display_counter = text_display_duration

    if text_display_counter > 0:
        cv2.putText(annotated_image_bgr, text, (text_x, text_y), font, font_scale, font_color, font_thickness)
        text_display_counter -= 1

    out.write(annotated_image_bgr)
    # print(f"Frame {frame_index} written to output video.")

    cv2.putText(annotated_image_bgr, f'Frame: {frame_index}', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2)
    cv2.imshow('Annotated Frames', annotated_image_bgr)

    key = cv2.waitKey(5) & 0xFF
    if key == 27:
        break

    frame_index += 1

cap.release()
out.release()
cv2.destroyAllWindows()

plt.figure(figsize=(12, 6))
plt.plot(range(len(x)), x, label='X Coordinates', color='b', alpha=0.7)
plt.plot(range(len(y)), y, label='Y Coordinates', color='g', alpha=0.7)
plt.axvspan(start_frame, end_frame, color='yellow', alpha=0.3, label="Processed Range")
plt.plot(filtered_x_peaks, [x[i] for i in filtered_x_peaks], "x", label="X Peaks")
plt.plot(filtered_x_valleys, [x[i] for i in filtered_x_valleys], "x", label="X Valleys")
plt.plot(filtered_y_peaks, [y[i] for i in filtered_y_peaks], "o", label="Y Peaks")
plt.plot(filtered_y_valleys, [y[i] for i in filtered_y_valleys], "o", label="Y Valleys")
plt.title('X and Y Coordinates Over Frame Number')
plt.xlabel('Frame Number')
plt.ylabel('Coordinate Value')
plt.legend()
plt.grid(True)
plt.savefig('coordinates_plot.png')
plt.show()

cv2.destroyAllWindows()
