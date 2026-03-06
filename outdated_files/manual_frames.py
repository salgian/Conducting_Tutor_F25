import cv2
import mediapipe as mp
import keyboard

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_pose = mp.solutions.pose

# For video input:
cap = cv2.VideoCapture('3-4stacatto(2).mp4')

# Boolean flag to keep track of key press state
key_pressed = False

# Function to handle key press events
def key_press(event, frame):
    global key_pressed
    if event.event_type == 'down' and event.name == 'r' and not key_pressed:
        message = f"Beat on frame: {frame_index}"
        print(message)
        with open('3-4stacatto(2)_manual.txt', 'a') as f:
            f.write(message + '\n')
        key_pressed = True
    elif event.event_type == 'up' and event.name == 'r':
        key_pressed = False

# Wrapper function to capture frame number
def key_press_wrapper(frame):
    def wrapper(e):
        key_press(e, frame)
    return wrapper

# 2D array to store coordinates
frame_array = []
frame_rate = 24
frame_index = 0

with mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5) as pose:

    while cap.isOpened():
        success, image = cap.read()
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

        frame_landmarks = []

        if results.pose_landmarks:
            # Goes through all pose landmarks (32 total) and adds them to columns in array
            for j in range(33):
                # Fill array with all landmark coordinates for each frame
                frame_landmarks.append(results.pose_landmarks.landmark[j])

            # Insert landmark into 2D array with frames as rows and landmarks as columns
            frame_array.append(frame_landmarks)

        # Check for keyboard events
        keyboard.hook(key_press_wrapper(frame_index))

        if cv2.waitKey(5) & 0xFF == 27:
            break

        frame_index += 1

    cap.release()
