"""
drawing.py
----------
OpenCV drawing helpers for the inference overlay.
"""

import cv2


def draw_beat_overlay(frame):
    """
    Draw the word 'BEAT' in white with a black outline stroke.
    Momentary flash -- no background bar.
    """
    h, w = frame.shape[:2]
    text      = "BEAT"
    font      = cv2.FONT_HERSHEY_SIMPLEX
    scale     = 2.0
    thickness = 4
    x = w // 2 - 80
    y = 60

    # Black outline (stroke)
    cv2.putText(frame, text, (x, y), font, scale, (0, 0, 0), thickness + 4, cv2.LINE_AA)
    # White fill
    cv2.putText(frame, text, (x, y), font, scale, (255, 255, 255), thickness, cv2.LINE_AA)


def draw_wrist_dot(frame, wrist_x, wrist_y):
    """Draw a green dot at the tracked wrist position."""
    if wrist_x is None or wrist_y is None:
        return
    h, w = frame.shape[:2]
    cx, cy = int(wrist_x * w), int(wrist_y * h)
    cv2.circle(frame, (cx, cy), 8, (0, 255, 0), -1)
