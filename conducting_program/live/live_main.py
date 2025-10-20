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
from live.metronome import MetronomeManager
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
    metronome_manager = MetronomeManager()
    beat_manager = BeatManager(settings.get_time_signature())
    
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
        'settings': settings
    }
    
    # Give visual_manager access to all components
    visual_manager.set_components(components)
    system_state = SystemState(components)
    
    processing_loop(components, system_state)

def processing_loop(components, system_state):
    """Main processing loop for live pose detection."""
    camera_manager = components['camera_manager']
    media_pipe_declaration = components['media_pipe_declaration']
    pose = components['pose']
    pose_landmarks = components['pose_landmarks']
    clock_manager = components['clock_manager']
    visual_manager = components['visual_manager']
    metronome_manager = components['beat_manager']
    
    if not camera_manager.initialize_camera():
        return  # Error handling, handled in camera_manager
    
    clock_manager.start_program_clock()
    print("Starting live pose detection...")
    print("Press 'q' to quit")
    
    try:
        while True:
            # Setup frame (stores in visual_manager)
            success, detection_result = visual_manager.setup_frame(camera_manager, media_pipe_declaration, pose)
            if not success:
                break
            
            # Update per-frame visuals (timing info, etc.)
            visual_manager.update_frame_visuals(camera_manager, clock_manager)
            
            # Update pose landmarks
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
        camera_manager.cleanup()
        media_pipe_declaration.close_pose_detection(pose)
        print("Pose detection closed")
