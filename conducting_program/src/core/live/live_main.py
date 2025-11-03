# Main live program - carries the logic for the live version of the program

import cv2
from src.core.live.mp_declaration import mediaPipeDeclaration
from src.core.live.camera import CameraManager
from src.core.live.settings import Settings
from src.core.live.system_state import SystemState
from src.core.live.pose_landmarks import PoseLandmarks
from src.core.live.clock import ClockManager
from src.core.live.visual import VisualManager
from src.core.live.sound import SoundManager
from src.core.live.metronome import MetronomeManager
from src.core.live.beat import BeatManager
from src.core.shared.sway import SwayDetection
from src.core.shared.mirror import MirrorDetection
from src.core.shared.elbow import ElbowDetection
from src.core.shared.midpoint import MidpointProcessor

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
    metronome_manager = MetronomeManager()
    beat_manager = BeatManager(settings.get_time_signature())
    
    # Start continuous audio warmup in background
    sound_manager.start_continuous_warmup()
    
    # Initialize detection components
    sway_detection = SwayDetection()
    mirror_detection = MirrorDetection()
    elbow_detection = ElbowDetection()
    midpoint_processor = MidpointProcessor()
    
    metronome_manager.initialize(settings, sound_manager, visual_manager, beat_manager)
    visual_manager.set_beat_manager(beat_manager)
    
    # Create system state with all components
    components = {
        'beat_manager': metronome_manager,  
        'beat_position_manager': beat_manager,  
        'midpoint_processor': midpoint_processor,
        'sway_detection': sway_detection,
        'mirror_detection': mirror_detection,
        'elbow_detection': elbow_detection,
        'visual_manager': visual_manager,
        'camera_manager': camera_manager,
        'media_pipe_declaration': media_pipe_declaration,
        'pose': pose,
        'pose_landmarks': pose_landmarks,
        'clock_manager': clock_manager,
        'settings': settings,
        'sound_manager': sound_manager
    }
    
    # Give visual_manager access to all components
    visual_manager.set_components(components)
    system_state = SystemState(components)
    
    processing_loop(components, system_state)

def process_frame_with_skipping(camera_manager, media_pipe_declaration, pose, visual_manager, 
                                frame_counter, last_detection_result):
    """Capture and process frame with pose detection frame skipping optimization.
    
    Args:
        camera_manager: Camera manager instance
        media_pipe_declaration: MediaPipe declaration instance
        pose: MediaPipe pose object
        visual_manager: Visual manager instance
        frame_counter: Current frame counter
        last_detection_result: Previously cached detection result
        
    Returns:
        tuple: (success, detection_result) - success status and current/cached detection result
    """
    # Capture and prepare frame
    success, frame = camera_manager.capture_frame()
    if not success:
        return False, None
    
    frame = cv2.flip(frame, 1)  # Flip the frame horizontally
    rgb_frame = camera_manager.convert_to_rgb(frame)  # Convert BGR to RGB
    
    # Frame skipping optimization: Process pose detection every 2nd frame
    # Reuse previous results on alternate frames
    if frame_counter % 2 == 0:
        # Run full MediaPipe pose detection
        detection_result = media_pipe_declaration.process_pose_detection(pose, rgb_frame)
    else:
        # Reuse previous detection result (skip expensive pose processing)
        detection_result = last_detection_result
    
    # Draw pose landmarks and store in visual manager
    visual_manager.current_frame = media_pipe_declaration.draw_pose_landmarks(frame, detection_result)
    
    return True, detection_result

def processing_loop(components, system_state):
    """Main processing loop for live pose detection."""
    camera_manager = components['camera_manager']
    media_pipe_declaration = components['media_pipe_declaration']
    pose = components['pose']
    pose_landmarks = components['pose_landmarks']
    clock_manager = components['clock_manager']
    visual_manager = components['visual_manager']
    metronome_manager = components['beat_manager']
    sound_manager = components['sound_manager']
    
    if not camera_manager.initialize_camera():
        return  # Error handling, handled in camera_manager
    
    clock_manager.start_program_clock()
    print("Starting live pose detection...")
    print("Press 'q' to quit")
    
    # Frame skipping optimization for pose detection
    frame_counter = 0
    last_detection_result = None
    
    try:
        while True:
            # Process frame or reuse previous detection result
            success, detection_result = process_frame_with_skipping(camera_manager, media_pipe_declaration, pose, visual_manager, frame_counter, last_detection_result)
            if not success:
                break
            
            # Cache the detection result for next frame
            last_detection_result = detection_result
            frame_counter += 1
            
            # Update per-frame visuals (timing info, etc.)
            visual_manager.update_frame_visuals(camera_manager, clock_manager)
            
            # Update pose landmarks with current or cached detection result
            pose_landmarks.update_landmarks(detection_result)
            
            # State management - state handles its own logic
            current_state = system_state.get_current_state()
            next_state = current_state.main()  # No parameters - uses components
            
            # Handle state transitions
            if next_state != current_state.get_state_name():
                system_state.change_state(next_state)
                if next_state == "countdown":
                    metronome_manager.start()
            
            # Display frame
            if visual_manager.show_frame():
                break
                    
    except KeyboardInterrupt:
        print("\nStopping pose detection...")
    finally:
        sound_manager.stop_continuous_warmup()
        camera_manager.cleanup()
        media_pipe_declaration.close_pose_detection(pose)
        print("Pose detection closed")
