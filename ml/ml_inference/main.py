"""
main.py
-------
Entry point for running beat detection inference on a video.

Usage:
    python main.py --video "path/to/video.mp4"
    python main.py --video "path/to/video.mp4" --threshold 0.6
"""

import os
import argparse

import numpy as np
from tensorflow import keras

from inference_loop import run_inference
from time_signature import estimate_time_signature

# ── Configuration ────────────────────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(SCRIPT_DIR, "..", "ml_training", "models", "beat_detector.keras")


# ── CLI ──────────────────────────────────────────────────────────────────────

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run beat detection on a video.")
    parser.add_argument("--video", type=str, default=None,
                        help="Path to video file. Uses default in CameraManager if omitted.")
    parser.add_argument("--threshold", type=float, default=0.5,
                        help="Beat probability threshold (default 0.5)")
    return parser.parse_args()


# ── Results ──────────────────────────────────────────────────────────────────

def print_results(beat_frame_indices, total_frames):
    """Print detection summary and estimated time signature."""
    print("\n" + "=" * 50)
    print("  RESULTS")
    print("=" * 50)
    print(f"  Total frames processed : {total_frames}")
    print(f"  Beats detected         : {len(beat_frame_indices)}")

    if len(beat_frame_indices) >= 2:
        intervals = np.diff(beat_frame_indices)
        avg_gap   = np.mean(intervals)
        print(f"  Average beat interval  : {avg_gap:.1f} frames")

        ts = estimate_time_signature(intervals.tolist())
        print(f"\n  >> Estimated time signature:  {ts}")
    else:
        print("\n  Not enough beats detected to estimate time signature.")

    print()


# ── Entry point ──────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    print("\n=== Beat Detection Inference ===\n")
    print("  Loading model...")
    model = keras.models.load_model(MODEL_PATH)
    print(f"  Model loaded from {MODEL_PATH}")

    beat_frame_indices, total_frames = run_inference(
        model, video_path=args.video, threshold=args.threshold
    )

    print_results(beat_frame_indices, total_frames)


if __name__ == "__main__":
    main()
