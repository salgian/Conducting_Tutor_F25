# DO NOT IMPORT THIS FILE
import cv2
import matplotlib.pyplot as plt
import mediapipe as mp
from scipy.signal import find_peaks
import numpy as np
from mediapipe.framework.formats import landmark_pb2

# Initialize MediaPipe Pose
BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path='pose_landmarker_lite.task'),
    running_mode=VisionRunningMode.VIDEO
)
detector = PoseLandmarker.create_from_options(options)

# Arrays to store coordinates
frame_array = []  # Stores coordinates for the entire video
processed_frame_array = []  # Stores coordinates only during active processing intervals
processing_intervals = []  # List to store multiple processing intervals

frame_number = 0
#processing_active = False
#current_start_frame = None

# For video input
cap = cv2.VideoCapture('4-4stacatto(3).mp4')
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = int(cap.get(cv2.CAP_PROP_FPS))
size = (frame_width, frame_height)
out = cv2.VideoWriter('annotated_output.avi', cv2.VideoWriter_fourcc(*'MJPG'), fps, size)

# Text properties for beat display
font = cv2.FONT_HERSHEY_SIMPLEX
font_scale = 2
font_thickness = 2
font_color = (255, 255, 255)
text_display_duration = 3  # Number of frames to display "Beat!" text
text_display_counter = 0

# Initialize variables for beat detection and BPM calculation
bpm_window = 30  # Time window in seconds for BPM calculation
fps = int(cap.get(cv2.CAP_PROP_FPS))
frames_per_window = bpm_window * fps
beats = []  # List to store frames where beats occur


def draw_landmarks_on_image(rgb_image, detection_result):
    """ Draw landmarks on the image. """
    pose_landmarks_list = detection_result.pose_landmarks
    annotated_image = np.copy(rgb_image)

    for idx in range(len(pose_landmarks_list)):
        pose_landmarks = pose_landmarks_list[idx]
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

while cap.isOpened():
    success, image = cap.read()
    if not success:
        #if processing_active:
        #    processing_intervals.append((current_start_frame, frame_number - 1))
        break

    # Crop and resize ROI
    roi = image[450:900, 600:1500] if image.shape[0] >= 900 and image.shape[1] >= 1500 else image
    roi_resized = cv2.resize(roi, (frame_width, frame_height))
    image_rgb = cv2.cvtColor(roi_resized, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
    frame_timestamp_ms = round(cap.get(cv2.CAP_PROP_POS_MSEC))

    # Run pose detection and display
    detection_result = detector.detect_for_video(mp_image, frame_timestamp_ms)
    annotated_image = draw_landmarks_on_image(image_rgb, detection_result)
    annotated_image_bgr = cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR)

    # Display annotated frame in the first loop
    cv2.imshow('Video Feed - Selection Mode', annotated_image_bgr)

    # Extract landmark 16's x and y coordinates for every frame
    pose_landmarks_list = detection_result.pose_landmarks
    if pose_landmarks_list:
        for landmarks in pose_landmarks_list:
            if len(landmarks) > 16:
                x16 = landmarks[16].x
                y16 = landmarks[16].y
                frame_array.append((x16, y16))  # Add to main array for all frames
                #Filter out inactive frames with nan so that it will be ignored by find_peaks
                #processed_frame_array.append((np.nan, np.nan))
    #if processing_active:
    #    pose_landmarks_list = detection_result.pose_landmarks
    #    if pose_landmarks_list:
    #        for landmarks in pose_landmarks_list:
    #            if len(landmarks) > 16:
    #                x16 = landmarks[16].x
    #                y16 = landmarks[16].y
    #                processed_frame_array[frame_number] = (x16, y16)  # Add to array only during active processing

    # Check for user input to start/stop processing
    key = cv2.waitKey(5) & 0xFF
    #if key == ord('s'):  # Press 's' to start a new segment
    #    if not processing_active:
    #        current_start_frame = frame_number
    #        processing_active = True
    #        print(f"Processing started at frame {current_start_frame}")
    #elif key == ord('e'):  # Press 'e' to stop the current segment
    #    if processing_active:
    #        processing_intervals.append((current_start_frame, frame_number))
    #        processing_active = False
    #        print(f"Processing stopped at frame {frame_number}")
    #elif key == 27:  # Press 'ESC' to exit
    #    if processing_active:
    #        processing_intervals.append((current_start_frame, frame_number))
    #    break

    frame_number += 1
    # Press 'q' to quit
    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

print("Processing intervals:", processing_intervals)

# Re-open the video for final processing with beat annotation and video writing
cap = cv2.VideoCapture('4-4stacatto(3).mp4')
frame_index = 0
last_frame_timestamp = 0

# Process x and y coordinates with peak detection for the entire video
x = np.array([coord[0] for coord in frame_array])
y = np.array([coord[1] for coord in frame_array])
#x_peaks, _ = find_peaks(x, prominence=0.005)
#x_valleys, _ = find_peaks(-x, prominence=0.005)
y_peaks, _ = find_peaks(y, prominence=0.005, distance = 5)
y_valleys, _ = find_peaks(-y, prominence=0.005, distance = 5)

# Convert x_proc and y_proc to numpy arrays for proper arithmetic operations
#x_proc = np.array([coord[0] for coord in processed_frame_array])
#y_proc = np.array([coord[1] for coord in processed_frame_array])

# Directly apply find_peaks to x_proc and y_proc as numpy arrays
#x_peaks_proc, _ = find_peaks(x_proc)
#x_valleys_proc, _ = find_peaks(-x_proc)  # Now valid with numpy arrays
#y_peaks_proc, _ = find_peaks(y_proc)
#y_valleys_proc, _ = find_peaks(-y_proc)

# Filter peaks based on a frame threshold
# def filter_significant_points(points, threshold):
#    if len(points) == 0:
#        return []
#    filtered_points = [points[0]]
#    for i in range(1, len(points)):
#        if points[i] - filtered_points[-1] > threshold:
#            filtered_points.append(points[i])
#    return filtered_points

# Filter peaks based on a frame threshold for significant points
threshold = 10
#filtered_x_peaks_proc = filter_significant_points(x_peaks_proc, threshold)
#filtered_x_valleys_proc = filter_significant_points(x_valleys_proc, threshold)
#filtered_y_peaks_proc = filter_significant_points(y_peaks_proc, threshold)
#filtered_y_valleys_proc = filter_significant_points(y_valleys_proc, threshold)

filtered_significant_beats = list(y_peaks) + list(y_valleys)

options = PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path='pose_landmarker_lite.task'),
    running_mode=VisionRunningMode.VIDEO
)
detector = PoseLandmarker.create_from_options(options)

#def is_within_intervals(frame_idx, intervals):
#    return any(start <= frame_idx <= end for start, end in intervals)

# Function to calculate BPM based on beats within the last time window
def calculate_bpm(current_frame, beats, fps, window_duration):
    # Filter out beats that fall outside the time window
    beats_in_window = [beat for beat in beats if current_frame - beat <= window_duration * fps]
    bpm = len(beats_in_window) * (60 / window_duration)
    return bpm

# Video writing loop with beat annotation
while cap.isOpened():
    success, image = cap.read()
    if not success:
        break

    roi = image[450:900, 600:1500] if image.shape[0] >= 900 and image.shape[1] >= 1500 else image
    roi_resized = cv2.resize(roi, (frame_width, frame_height))
    image_rgb = cv2.cvtColor(roi_resized, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
    frame_timestamp_ms = round(cap.get(cv2.CAP_PROP_POS_MSEC))

    # Detect landmarks and annotate the frame only within processing intervals
    detection_result = detector.detect_for_video(mp_image, frame_timestamp_ms)
# Check if the current frame is within the processing intervals
    #if is_within_intervals(frame_index, processing_intervals):
    # Display "Beat!" text and calculate BPM if frame is a beat
    if frame_index in filtered_significant_beats:  # Assuming filtered_significant_beats is predefined
            text = "Beat!"
            text_size = cv2.getTextSize(text, font, font_scale, font_thickness)[0]
            text_x = (image_rgb.shape[1] - text_size[0]) // 2
            text_y = (image_rgb.shape[0] + text_size[1]) // 2
            cv2.putText(annotated_image_bgr, text, (text_x, text_y), font, font_scale, font_color, font_thickness)
            
            # Add the current beat to the list
            beats.append(frame_index)

            # Calculate BPM based on beats within the last time window
            bpm = calculate_bpm(frame_index, beats, fps, bpm_window)

            # Save BPM information to file
            bpm_info = f'Beats per minute (BPM) at frame {frame_index}: {bpm}\n'
            output_file = '4-4stacatto(2).mp4_auto_BPM.txt'
            with open(output_file, 'a') as file:
                print(bpm_info, end='')
                file.write(bpm_info)
                
                # Set display counter for beat text duration
                text_display_counter = text_display_duration

    # Display the beat text for the set duration
    if text_display_counter > 0:
        cv2.putText(annotated_image_bgr, text, (text_x, text_y), font, font_scale, font_color, font_thickness)
        text_display_counter -= 1

    # Add frame number to the annotated frame and write to output
    cv2.putText(annotated_image_bgr, f'Frame: {frame_index}', (10, 50), font, 1, font_color, 2)
    out.write(annotated_image_bgr)
    cv2.imshow('Output Video', annotated_image_bgr)

    # Check for ESC key to exit
    if cv2.waitKey(5) & 0xFF == 27:
        break

    frame_index += 1

cap.release()
out.release()
cv2.destroyAllWindows()

# Plotting x and y coordinates with uniform beat markers within processing intervals
plt.figure(figsize=(12, 6))
plt.plot(range(len(x)), x, label='X Coordinates', color='b', alpha=0.7)
plt.plot(range(len(y)), y, label='Y Coordinates', color='g', alpha=0.7)

# Highlight each processing interval individually on the plot
if processing_intervals:  # Ensure there are intervals to process
    for start, end in processing_intervals:
        plt.axvspan(start, end, color='yellow', alpha=0.3, label="Processed Range" if start == processing_intervals[0][0] else None)

# Plot uniform beat markers for all filtered peaks and valleys
all_beats = list(y_peaks) + list(y_valleys)
all_beat_values = [x[i] if i < len(x) else y[i - len(x)] for i in all_beats]
# Plot vertical lines for all filtered peaks and valleys
for beat in all_beats:
    plt.axvline(x=beat, color='purple', linestyle='--', label="Beats" if beat == all_beats[0] else None)
#plt.plot(x_peaks, [x[i] for i in x_peaks], "x", label="X Peaks")
#plt.plot(x_valleys, [x[i] for i in x_valleys], "x", label="X Valleys")
plt.plot(y_peaks, [y[i] for i in y_peaks], "o", label="Y Peaks")
plt.plot(y_valleys, [y[i] for i in y_valleys], "o", label="Y Valleys")
plt.title('X and Y Coordinates Over Frame Number')
plt.xlabel('Frame Number')
plt.ylabel('Coordinate Value')
plt.legend()
plt.grid(True)
plt.savefig('coordinates_plot.png')
plt.show()