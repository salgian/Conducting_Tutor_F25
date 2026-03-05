"""
recording.py
------------
Frame-by-frame recording loop and pose processing for data collection.
"""

import cv2

from drawing import draw_beat_indicator, draw_wrist_dot


def process_single_frame(frame, mp_handler, pose, pose_landmarks,
                         data_processor, frame_counter, is_beat_manual):
    """
    Run pose detection on one frame, update landmarks, process data.
    Returns the processed data dict, or None if no pose was found.
    """
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    detection_result = mp_handler.process_pose_detection(pose, rgb_frame)

    if detection_result:
        pose_landmarks.update_landmarks(detection_result)
        wrist_x, wrist_y = pose_landmarks.get_wrist()
        return data_processor.process_frame(
            frame_counter, wrist_x, wrist_y, is_beat=is_beat_manual
        )

    return None


def record_session(camera_manager, mp_handler, pose, pose_landmarks,
                   data_processor):
    """
    Main recording loop. Captures frames, processes pose data, and
    lets the user mark beats with SPACE. Returns the list of display frames.
    """
    print("\nRECORDING... Press 'q' to stop and review.")
    frame_buffer = []
    frame_counter = 0

    try:
        while True:
            success, frame = camera_manager.capture_frame()
            if not success:
                break

            frame = cv2.flip(frame, 1)
            display_frame = frame.copy()

            key = cv2.waitKey(1) & 0xFF
            is_beat_manual = 1 if key == ord(' ') else 0

            data = process_single_frame(
                frame, mp_handler, pose, pose_landmarks,
                data_processor, frame_counter, is_beat_manual
            )

            if data:
                wrist_x, wrist_y = pose_landmarks.get_wrist()
                draw_wrist_dot(display_frame, wrist_x, wrist_y)

                if data['is_beat']:
                    draw_beat_indicator(display_frame)

            frame_buffer.append(display_frame)
            frame_counter += 1

            cv2.imshow("Conducting Recorder", display_frame)
            if key == ord('q'):
                break

    except KeyboardInterrupt:
        pass

    return frame_buffer
