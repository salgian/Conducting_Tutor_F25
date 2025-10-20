# Main live program - carries the logic for the live version of the program

import cv2
from live.mp_declaration import mediaPipeDeclaration
from live.camera import CameraManager
from live.settings import Settings
from live.system_state import SystemState
from live.pose_landmarks import PoseLandmarks
from live.clock import ClockManager
from live.visual import VisualManager
from live.sound import SoundManager
from live.beat import BeatManager
from shared.sway import SwayDetection
from shared.mirror import MirrorDetection
from shared.elbow import ElbowDetection
from shared.midpoint import MidpointProcessor

def live_main():
    """Initialize and start the live conducting tutor system."""
    settings = Settings()
    bpm_input = input("enter bpm as a whole number: ")
    settings.set_beats_per_minute(int(bpm_input))
    time_signature_input = input("enter time signature as (4/4 or 3/4) : ")
    settings.set_time_signature(time_signature_input)
    print("BPM set to:", settings.get_beats_per_minute())
    print("Time signature set to:", settings.get_time_signature())
    
    # Initialize core components
    pose = mediaPipeDeclaration.initialize_pose_detection()
    media_pipe_declaration = mediaPipeDeclaration()
    camera_manager = CameraManager()
    pose_landmarks = PoseLandmarks() 
    clock_manager = ClockManager()
    visual_manager = VisualManager(settings.get_time_signature())
    sound_manager = SoundManager()
    beat_manager = BeatManager()
    
    # Initialize detection components
    sway_detection = SwayDetection()
    mirror_detection = MirrorDetection()
    elbow_detection = ElbowDetection()
    midpoint_processor = MidpointProcessor()
    
    beat_manager.initialize(settings, sound_manager, visual_manager)
    
    # Create system state with all components
    components = {
        'beat_manager': beat_manager,
        'midpoint_processor': midpoint_processor,
        'sway_detection': sway_detection,
        'mirror_detection': mirror_detection,
        'elbow_detection': elbow_detection,
        'visual_manager': visual_manager
    }
    system_state = SystemState(components)
    
    processing_loop(camera_manager, media_pipe_declaration, pose, system_state, pose_landmarks, clock_manager, visual_manager, beat_manager, sway_detection, mirror_detection, elbow_detection, midpoint_processor, settings)

def processing_loop(camera_manager, media_pipe_declaration, pose, system_state, pose_landmarks, clock_manager, visual_manager, beat_manager, sway_detection, mirror_detection, elbow_detection, midpoint_processor, settings):
    """Main processing loop for live pose detection."""
    if not camera_manager.initialize_camera():
        return  # Error handling, handled in camera_manager
    
    clock_manager.start_program_clock()
    print("Starting live pose detection...")
    print("Press 'q' to quit")
    
    try:
        while True:
            annotated_frame, detection_result = visual_manager.setup_frame(camera_manager, media_pipe_declaration, pose)
            if annotated_frame is None:
                  break
            
            # Display timing information
            visual_manager.display_timing_info(annotated_frame, camera_manager, clock_manager)
            
            pose_landmarks.update_landmarks(detection_result)
            
            # Update detection components
            midpoint_processor.update_current_midpoint(pose_landmarks)
            if midpoint_processor.get_reference_midpoint() is not None:
                sway_detection.main(midpoint_processor.get_reference_midpoint(), midpoint_processor.get_live_midpoint())
                mirror_detection.main(pose_landmarks, clock_manager, midpoint_processor.get_live_midpoint())
            elbow_detection.main(pose_landmarks)

            # Handle state management and transitions
            current_state = system_state.get_current_state()
            state_name = current_state.get_state_name()
            next_state = current_state.main(pose_landmarks, clock_manager, annotated_frame)           

            if next_state != state_name:
                system_state.change_state(next_state)
                if next_state == "countdown":  # Start beat manager when transitioning to countdown
                    beat_manager.start()

            if visual_manager.show_frame(annotated_frame):
                break
                    
    except KeyboardInterrupt:
        print("\nStopping pose detection...")
    finally:
        camera_manager.cleanup()
        media_pipe_declaration.close_pose_detection(pose)
        print("Pose detection closed")
