"""
review.py
---------
Playback and save/discard review for recorded data collection sessions.
"""

import cv2

from drawing import draw_review_indicator


def playback_session(frame_buffer, data_processor):
    """
    Replay the buffered frames and overlay confirmed beat indicators.
    Returns False if the user exits mid-playback, True on completion.
    """
    for i, frame in enumerate(frame_buffer):
        review_frame = frame.copy()
        is_beat = data_processor.buffer[i][8]  # beat column (index 8)

        if is_beat:
            draw_review_indicator(review_frame)

        cv2.imshow("Conducting Recorder", review_frame)
        if cv2.waitKey(30) & 0xFF == ord('q'):
            return False

    return True


def review_session(frame_buffer, data_processor, output_path):
    """
    Review loop: play back the recording, then ask whether to save or discard.
    Repeats playback until the user makes a decision.
    """
    print("\n--- REVIEW ---")
    print("Replaying with confirmed beats highlighted in green.")
    print("Press 'q' during playback to skip to the prompt.\n")

    while True:
        playback_session(frame_buffer, data_processor)

        save_choice = input("Save this data? (y / n / replay): ").strip().lower()
        if save_choice == 'y':
            count = data_processor.commit()
            print(f"Saved {count} frames to {output_path}")
            break
        elif save_choice == 'n':
            print("Data discarded.")
            break
        else:
            print("Replaying...")
