"""
inference_loop.py
-----------------
Core frame-by-frame inference loop.
Reads video frames, runs pose detection, normalises features,
feeds sliding windows to the model, and triggers beat detections.
"""

import sys
import os
import collections

import cv2
import numpy as np

# Import local modules BEFORE modifying sys.path
# (ml_data_extraction also has a drawing.py, so order matters)
from drawing import draw_beat_overlay, draw_wrist_dot

# Add ml_data_extraction to the path so we can import shared modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ml_data_extraction"))

from camera import CameraManager
from mp_declaration import mediaPipeDeclaration
from pose_landmarks import PoseLandmarks
from data_processor import Normalizer

# ── Configuration ────────────────────────────────────────────────────────────

SEQ_LEN             = 11
BEAT_THRESHOLD      = 0.5
BEAT_DISPLAY_FRAMES = 3      # quick flash duration
MIN_BEAT_GAP        = 10     # minimum frames between consecutive detections


# ── Component initialisation ─────────────────────────────────────────────────

def init_video(video_path=None):
    """Open a video source. Returns the CameraManager or None on failure."""
    camera = CameraManager()
    source = video_path if video_path else camera.camera_index
    if not camera.initialize_camera(source):
        print("  ERROR: Could not open video.")
        return None
    return camera


def init_pose():
    """Create MediaPipe handler + pose detector + landmark extractor."""
    mp_handler = mediaPipeDeclaration()
    pose       = mp_handler.initialize_pose_detection()
    landmarks  = PoseLandmarks()
    return mp_handler, pose, landmarks


# ── Per-frame processing ─────────────────────────────────────────────────────

def extract_wrist_features(frame, mp_handler, pose, landmarks, normalizer):
    """
    Detect wrist in one frame, return the 6-element feature list.
    Returns (features_list, wrist_x, wrist_y).
    features_list is None if the wrist was not detected.
    """
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = mp_handler.process_pose_detection(pose, rgb)
    landmarks.update_landmarks(results)
    wx, wy = landmarks.get_wrist()
    feat = normalizer.process_as_list(wx, wy)
    return feat, wx, wy


def predict_beat(model, window, threshold=BEAT_THRESHOLD):
    """
    Run model on a single window.
    Returns True if the model predicts a beat above the threshold.
    """
    X = np.array([list(window)], dtype=np.float32)
    prob = model.predict(X, verbose=0)[0, 0]
    return prob >= threshold


# ── Main loop ────────────────────────────────────────────────────────────────

def run_inference(model, video_path=None, threshold=BEAT_THRESHOLD):
    """
    Play a video through the model.

    Returns:
        beat_frame_indices: list of frame numbers where beats were detected
        total_frames: number of frames processed
    """
    camera = init_video(video_path)
    if camera is None:
        return [], 0

    mp_handler, pose, landmarks = init_pose()
    normalizer = Normalizer()

    window              = collections.deque(maxlen=SEQ_LEN)
    beat_frame_indices   = []
    total_frames         = 0
    beat_display_timer   = 0
    frames_since_last    = 999

    print("  Playing video -- press 'q' to quit early.\n")

    while True:
        success, frame = camera.capture_frame()
        if not success:
            break

        frame = cv2.flip(frame, 1)

        # Pose + features
        feat, wx, wy = extract_wrist_features(
            frame, mp_handler, pose, landmarks, normalizer
        )
        if feat is not None:
            window.append(feat)

        # Model prediction
        if len(window) == SEQ_LEN and feat is not None:
            if predict_beat(model, window, threshold) and frames_since_last >= MIN_BEAT_GAP:
                beat_display_timer = BEAT_DISPLAY_FRAMES
                beat_frame_indices.append(total_frames)
                frames_since_last = 0

        frames_since_last += 1

        # Draw overlays
        draw_wrist_dot(frame, wx, wy)
        if beat_display_timer > 0:
            draw_beat_overlay(frame)
            beat_display_timer -= 1

        cv2.imshow("Beat Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        total_frames += 1

    # Cleanup
    camera.cleanup()
    pose.close()
    cv2.destroyAllWindows()

    return beat_frame_indices, total_frames
