"""
drawing.py
----------
All OpenCV drawing helpers used during data collection.
"""

import cv2


def draw_beat_indicator(frame, label="BEAT", color=(0, 0, 255)):
    """Draw a colored circle and label on the frame to indicate a beat."""
    cv2.circle(frame, (50, 100), 15, color, -1)
    cv2.putText(frame, label, (75, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)


def draw_wrist_dot(frame, wrist_x, wrist_y):
    """Draw a green dot at the tracked wrist position."""
    if wrist_x is None or wrist_y is None:
        return
    h, w = frame.shape[:2]
    cx, cy = int(wrist_x * w), int(wrist_y * h)
    cv2.circle(frame, (cx, cy), 8, (0, 255, 0), -1)


def draw_review_indicator(frame):
    """Overlay a 'CONFIRMED BEAT' indicator on the review frame."""
    w = frame.shape[1]
    cv2.circle(frame, (w - 100, 100), 30, (0, 255, 0), 5)
    cv2.putText(frame, "CONFIRMED BEAT", (w - 260, 110),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
