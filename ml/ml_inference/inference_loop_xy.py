"""
inference_loop_xy.py
--------------------
Core frame-by-frame inference loop (XY-only / 2-feature variant).
Reads video frames, runs pose detection, extracts raw wrist XY,
feeds sliding windows to the model, and triggers beat detections.

Optimised for real-time playback:
  - Downscales frames before MediaPipe to reduce pose-estimation cost.
  - Wraps the model call in @tf.function for compiled graph execution.
  - Syncs display to the source video's native FPS.
"""

import sys
import os
import time
import collections

import cv2
import numpy as np
import tensorflow as tf

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
POSE_MAX_WIDTH      = 640    # downscale frames to this width for MediaPipe


# ── Component initialisation ─────────────────────────────────────────────────

def init_video(video_path=None):
    """Open a video source. Returns (CameraManager, fps) or (None, 0)."""
    camera = CameraManager()
    source = video_path if video_path else camera.camera_index
    if not camera.initialize_camera(source):
        print("  ERROR: Could not open video.")
        return None, 0

    fps = camera.cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30.0  # sensible default
    return camera, fps


def init_pose():
    """Create MediaPipe handler + pose detector + landmark extractor."""
    mp_handler = mediaPipeDeclaration()
    pose       = mp_handler.initialize_pose_detection()
    landmarks  = PoseLandmarks()
    return mp_handler, pose, landmarks


# ── Per-frame processing ─────────────────────────────────────────────────────

def _downscale_for_pose(frame, max_width=POSE_MAX_WIDTH):
    """
    Resize the frame so that its width is at most max_width.
    Returns the resized frame. If already small enough, returns as-is.
    """
    h, w = frame.shape[:2]
    if w <= max_width:
        return frame
    scale = max_width / w
    new_w = max_width
    new_h = int(h * scale)
    return cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)


def extract_wrist_features(frame, mp_handler, pose, landmarks, normalizer):
    """
    Detect wrist in one frame, return the 2-element feature list [wx, wy].
    Returns (features_list, wrist_x, wrist_y).
    features_list is None if the wrist was not detected.
    """
    small = _downscale_for_pose(frame)
    rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
    results = mp_handler.process_pose_detection(pose, rgb)
    landmarks.update_landmarks(results)
    wx, wy = landmarks.get_wrist()
    if wx is None or wy is None:
        return None, wx, wy
    feat = [wx, wy]
    return feat, wx, wy


# ── Model wrapper ────────────────────────────────────────────────────────────

@tf.function(reduce_retracing=True)
def _predict_tf(model, X):
    """Compiled TF graph for single-batch model inference."""
    return model(X, training=False)


def predict_beat(model, window, threshold=BEAT_THRESHOLD):
    """
    Run model on a single window.
    Returns True if the model predicts a beat above the threshold.
    """
    X = tf.constant([list(window)], dtype=tf.float32)
    prob = _predict_tf(model, X)[0, 0]
    return float(prob) >= threshold


# ── Main loop ────────────────────────────────────────────────────────────────

def run_inference(model, video_path=None, threshold=BEAT_THRESHOLD):
    """
    Play a video through the model with real-time pacing.

    Returns:
        beat_frame_indices: list of frame numbers where beats were detected
        total_frames: number of frames processed
    """
    camera, fps = init_video(video_path)
    if camera is None:
        return [], 0

    target_dt = 1.0 / fps          # seconds per frame for real-time pacing

    mp_handler, pose, landmarks = init_pose()
    normalizer = Normalizer()

    window              = collections.deque(maxlen=SEQ_LEN)
    beat_frame_indices   = []
    total_frames         = 0
    beat_display_timer   = 0
    frames_since_last    = 999

    print(f"  Playing video at {fps:.1f} FPS -- press 'q' to quit early.\n")

    while True:
        frame_start = time.perf_counter()

        success, frame = camera.capture_frame()
        if not success:
            break

        frame = cv2.flip(frame, 1)

        # Pose + features (downscaled internally)
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

        # ── FPS-synced wait ──────────────────────────
        elapsed = time.perf_counter() - frame_start
        remaining_ms = max(1, int((target_dt - elapsed) * 1000))
        if cv2.waitKey(remaining_ms) & 0xFF == ord("q"):
            break

        total_frames += 1

    # Cleanup
    camera.cleanup()
    pose.close()
    cv2.destroyAllWindows()

    return beat_frame_indices, total_frames
