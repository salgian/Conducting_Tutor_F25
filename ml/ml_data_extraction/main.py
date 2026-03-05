"""
main.py
-------
Entry point for training data collection.

Wires up the camera, MediaPipe, and data processor, then runs the
record -> review -> save workflow.

Usage:
    python main.py
    python main.py --video path/to/video.mp4 --time_sig 4/4
"""

import cv2
import argparse
import os
from datetime import datetime

from camera import CameraManager
from mp_declaration import mediaPipeDeclaration
from pose_landmarks import PoseLandmarks
from data_processor import DataProcessor
from recording import record_session
from review import review_session


# ── CLI helpers ──────────────────────────────────────────────────────────────

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract conducting data from video or webcam."
    )
    parser.add_argument("--video", type=str,
                        help="Path to video file. Omit to use webcam.")
    parser.add_argument("--output", type=str,
                        help="Output CSV file path. Auto-generated if omitted.")
    parser.add_argument("--time_sig", type=str, choices=["2/4", "3/4", "4/4"],
                        help="Time signature of the recording.")
    return parser.parse_args()


def prompt_time_signature():
    """Ask the user to select a time signature interactively."""
    print("\n--- Training Data Collection ---")
    print("Select Time Signature:")
    print("  2: 2/4")
    print("  3: 3/4")
    print("  4: 4/4")
    choice = input("Choice: ").strip()
    return f"{choice}/4"


def generate_output_path(time_sig):
    """Auto-generate a unique output CSV path inside training_data/."""
    os.makedirs("training_data", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ts_clean = time_sig.replace("/", "_")
    return f"training_data/conducting_{ts_clean}_{timestamp}.csv"


def print_controls():
    """Print the recording controls to the console."""
    print("\nCONTROLS:")
    print("  SPACE  -- Mark a beat")
    print("  q      -- Stop recording and start review")


# ── Entry point ──────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    if not args.time_sig:
        args.time_sig = prompt_time_signature()

    if not args.output:
        args.output = generate_output_path(args.time_sig)

    print(f"\nRecording  {args.time_sig}  ->  {args.output}")
    print_controls()

    # Initialise components
    mp_handler     = mediaPipeDeclaration()
    pose           = mp_handler.initialize_pose_detection()
    camera_manager = CameraManager()
    pose_landmarks = PoseLandmarks()
    data_processor = DataProcessor(
        output_file=args.output, time_signature=args.time_sig
    )

    camera_manager.initialize_camera(args.video)

    # Record -> Review -> Save
    frame_buffer = record_session(
        camera_manager, mp_handler, pose, pose_landmarks, data_processor
    )

    if frame_buffer:
        review_session(frame_buffer, data_processor, args.output)

    # Cleanup
    camera_manager.cleanup()
    pose.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()