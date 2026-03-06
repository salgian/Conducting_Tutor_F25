import cv2
import matplotlib.pyplot as plt
import pickle
import mediapipe as mp
from scipy.signal import find_peaks
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_pose = mp.solutions.pose

# 2D array to store coordinates
frame_array = [[]]

# For video input:
cap = cv2.VideoCapture('3-4stacatto(4).mp4')

with mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5) as pose:
  
  while cap.isOpened():
    success, image = cap.read() #save as image, out.write
    if not success:
      print("Ignoring empty camera frame.")
      # If loading a video, use 'break' instead of 'continue'.
      break
    
    # Crop a region of interest (ROI) from the frame [up/down: scale?, left/right: zoom]
    roi = image[450:900, 600:1500]
    # Resize the ROI to a specific size
    roi_resized = cv2.resize(roi, (1280, 720))
    image = roi_resized
    
    # To improve performance, optionally mark the image as not writeable to
    # pass by reference.
    image.flags.writeable = False
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = pose.process(image)
 
    # Draw the pose annotation on the image.
    image.flags.writeable = True
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    mp_drawing.draw_landmarks(
        image,
        results.pose_landmarks,
        mp_pose.POSE_CONNECTIONS,
        landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())
    # Flip the image horizontally for a selfie-view display.
    cv2.imshow('MediaPipe Pose', cv2.flip(image, 1))
    
    i = 0
    j = 0
    frame_landmarks = []
    
    if results.pose_landmarks:
      # Goes through all pose landmarks (32 total) and adds them to columns in array
      while j <= 32:
        # Fill array with all landmark coordinates for each frame
        frame_landmarks.append(results.pose_landmarks.landmark[j])
        j = j + 1
      
      # Insert landmark into 2D array with frames as rows and landmarks as columns
      frame_array.insert(i, frame_landmarks)
      i = i + 1
      j = 0
    
    if cv2.waitKey(5) & 0xFF == 27:
      break

cap.release()

# Store array information into pickle file
coordinates_file = open('conducting_coords.pickle', 'ab')
pickle.dump(frame_array, coordinates_file)
coordinates_file.close()

# Extract high and low peaks for x and y coordinates
x = []
y = []

for frame_landmarks in frame_array:
    if frame_landmarks:
        x.append(frame_landmarks[16].x)
        y.append(frame_landmarks[16].y)

# Find peaks in x and y coordinates
x_peaks, _ = find_peaks(x)
y_peaks, _ = find_peaks(y)
x_valleys, _ = find_peaks([-val for val in x])  # Finding valleys by flipping the sign
y_valleys, _ = find_peaks([-val for val in y])  # Finding valleys by flipping the sign

# Plot x and y coordinates
plt.figure(figsize=(12, 6))
plt.plot(x, label='X Coordinate')
plt.plot(y, label='Y Coordinate')
plt.plot(x_peaks, [x[i] for i in x_peaks], "x", label="X Peaks")
plt.plot(x_valleys, [x[i] for i in x_valleys], "x", label="X Valleys")
plt.plot(y_peaks, [y[i] for i in y_peaks], "o", label="Y Peaks")
plt.plot(y_valleys, [y[i] for i in y_valleys], "o", label="Y Valleys")
plt.xlabel('Frame')
plt.ylabel('Coordinate')
plt.legend()
plt.show()
