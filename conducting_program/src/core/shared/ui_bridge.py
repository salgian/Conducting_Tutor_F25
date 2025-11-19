# UI-Backend bridge for conducting tutor application
# Manages backend components and provides thread-safe interface for UI

import cv2
import threading
import queue
import numpy as np
from src.core.live.mp_declaration import mediaPipeDeclaration
from src.core.live.camera import CameraManager
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


class UIBridge:
    """Bridge between Tkinter UI and backend processing system.
    
    Manages all backend components, runs processing loop in separate thread,
    and provides thread-safe access to frames, metrics, and state changes.
    """
    
    def __init__(self, settings):
        """Initialize UI bridge with settings.
        
        Args:
            settings: Settings singleton instance
        """
        self.settings = settings
        self.components = {}
        self.processing_thread = None
        self.processing_active = False
        self.processing_lock = threading.Lock()
        
        # Frame queue for UI access (maxsize=2 to drop frames if UI is slow)
        self.frame_queue = queue.Queue(maxsize=2)
        self.current_frame = None
        
        # State change queue for UI polling (processing -> UI)
        self.state_change_queue = queue.Queue()
        
        # State request queue for UI requests (UI -> processing)
        self.state_request_queue = queue.Queue(maxsize=1)
        
        # MediaPipe initialization flag (can be pre-initialized)
        self._mediapipe_initialized = False
    
    def initialize_backend(self) -> bool:
        """Initialize all backend components.
        
        Can be called multiple times to reinitialize after stopping.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        # Clean up existing components if reinitializing
        if self.components:
            self._cleanup_components()
        
        # Initialize MediaPipe pose detection (reuse if pre-initialized)
        if not self._mediapipe_initialized:
            pose = mediaPipeDeclaration.initialize_pose_detection()
            self._mediapipe_initialized = True
        else:
            # Reinitialize if needed (MediaPipe may need fresh instance)
            pose = mediaPipeDeclaration.initialize_pose_detection()
        
        media_pipe_declaration = mediaPipeDeclaration()
        
        # Initialize camera manager with settings
        camera_path = self.settings.get_camera_path()
        camera_manager = CameraManager(camera_path)
        
        # Initialize core components
        pose_landmarks = PoseLandmarks()
        clock_manager = ClockManager()
        visual_manager = VisualManager(self.settings.get_time_signature())
        sound_manager = SoundManager()
        metronome_manager = MetronomeManager()
        beat_manager = BeatManager(self.settings.get_time_signature())
        
        # Start continuous audio warmup in background
        sound_manager.start_continuous_warmup()
        
        # Initialize detection components
        sway_detection = SwayDetection()
        mirror_detection = MirrorDetection()
        elbow_detection = ElbowDetection()
        midpoint_processor = MidpointProcessor()
        
        # Initialize metronome and visual manager
        metronome_manager.initialize(self.settings, sound_manager, visual_manager, beat_manager)
        visual_manager.set_beat_manager(beat_manager)
        
        # Create components dictionary
        self.components = {
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
            'settings': self.settings,
            'sound_manager': sound_manager
        }
        
        # Give visual_manager access to all components
        visual_manager.set_components(self.components)
        
        return True
    
    def start_processing_loop(self, camera_callback=None, state_change_callback=None) -> bool:
        """Start the processing loop in a separate thread.
        
        Args:
            camera_callback: Optional callback for camera events (not used currently)
            state_change_callback: Optional callback for state changes (not used, UI polls instead)
            
        Returns:
            bool: True if processing started successfully, False otherwise
        """
        with self.processing_lock:
            if self.processing_active:
                return True  # Already running
            
            # Ensure all previous threads are stopped before starting new ones
            self._stop_all_threads()
            
            # Initialize camera
            camera_manager = self.components.get('camera_manager')
            if not camera_manager:
                return False
            
            try:
                if not camera_manager.initialize_camera():
                    return False
            except Exception as e:
                print(f"Camera initialization error: {e}")
                return False
            
            # Create system state
            system_state = SystemState(self.components)
            self.components['system_state'] = system_state
            
            # Start program clock
            clock_manager = self.components['clock_manager']
            clock_manager.start_program_clock()
            
            # Start processing thread
            self.processing_active = True
            self.processing_thread = threading.Thread(
                target=self._processing_loop,
                args=(system_state,),
                daemon=True
            )
            self.processing_thread.start()
            
            return True
    
    def _processing_loop(self, system_state):
        """Main processing loop - runs in separate thread.
        
        Args:
            system_state: SystemState instance for state management
        """
        camera_manager = self.components['camera_manager']
        media_pipe_declaration = self.components['media_pipe_declaration']
        pose = self.components['pose']
        pose_landmarks = self.components['pose_landmarks']
        clock_manager = self.components['clock_manager']
        visual_manager = self.components['visual_manager']
        metronome_manager = self.components['beat_manager']
        sound_manager = self.components['sound_manager']
        
        # Frame skipping optimization for pose detection
        frame_counter = 0
        last_detection_result = None
        
        while self.processing_active:
            # Process frame or reuse previous detection result
            success, detection_result = self._process_frame_with_skipping(
                camera_manager,
                media_pipe_declaration,
                pose,
                visual_manager,
                frame_counter,
                last_detection_result
            )
            
            if not success:
                # Camera error - break loop
                break
            
            # Cache the detection result for next frame
            last_detection_result = detection_result
            frame_counter += 1
            
            # Update pose landmarks with current or cached detection result
            if detection_result:
                pose_landmarks.update_landmarks(detection_result)
            
            # Update per-frame visuals
            visual_manager.update_frame_visuals(camera_manager, clock_manager)
            
            # Process state transitions
            self._process_state_transitions(system_state, metronome_manager)
            
            # Store frame in queue for UI access
            self._update_frame_queue(visual_manager)
        
        # Cleanup when loop exits
        self._cleanup_processing()
    
    def _process_state_transitions(self, system_state, metronome_manager):
        """Process state transitions - handles UI requests and normal state flow.
        
        Args:
            system_state: SystemState instance
            metronome_manager: MetronomeManager instance
        """
        # Check for UI-requested state transitions
        requested_state = None
        if not self.state_request_queue.empty():
            requested_state = self.state_request_queue.get_nowait()
        
        if requested_state == "ending":
            system_state.change_state("ending")
            current_state = system_state.get_current_state()
            current_state.main()
            self.state_change_queue.put_nowait("ending")
            return
        
        # Normal state management
        current_state = system_state.get_current_state()
        previous_state_name = current_state.get_state_name()
        next_state = current_state.main()
        
        # Handle state transitions
        if next_state != previous_state_name:
            system_state.change_state(next_state)
            self.state_change_queue.put_nowait(next_state)
            
            if next_state == "countdown":
                metronome_manager.start()
    
    def _update_frame_queue(self, visual_manager):
        """Update frame queue with current frame for UI access.
        
        Args:
            visual_manager: VisualManager instance
        """
        self.current_frame = visual_manager.current_frame.copy()
        if not self.frame_queue.full():
            self.frame_queue.put_nowait(self.current_frame)
    
    def _process_frame_with_skipping(self, camera_manager, media_pipe_declaration, pose,
                                  visual_manager, frame_counter, last_detection_result):
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
    
    def _cleanup_components(self):
        """Clean up all component resources and stop all threads."""
        if not self.components:
            return
        
        self._stop_all_threads()
        
        camera_manager = self.components.get('camera_manager')
        media_pipe_declaration = self.components.get('media_pipe_declaration')
        pose = self.components.get('pose')
        
        if camera_manager:
            camera_manager.cleanup()
        if media_pipe_declaration and pose:
            media_pipe_declaration.close_pose_detection(pose)
        
        self.components = {}
    
    def _cleanup_processing(self):
        """Clean up processing resources after threads are stopped."""
        if not self.components:
            while not self.frame_queue.empty():
                self.frame_queue.get_nowait()
            self.current_frame = None
            return
        
        camera_manager = self.components.get('camera_manager')
        media_pipe_declaration = self.components.get('media_pipe_declaration')
        pose = self.components.get('pose')
        
        if camera_manager:
            camera_manager.cleanup()
        if media_pipe_declaration and pose:
            media_pipe_declaration.close_pose_detection(pose)
        
        while not self.frame_queue.empty():
            self.frame_queue.get_nowait()
        
        self.current_frame = None
    
    def request_ending_state(self):
        """Request transition to ending state."""
        if not self.state_request_queue.full():
            self.state_request_queue.put_nowait("ending")
    
    def stop_processing(self):
        """Stop processing loop and cleanup resources.
        
        Stops all threads:
        1. Processing loop thread (main thread)
        2. Metronome beat thread (spawned from processing)
        3. Sound warmup thread (spawned from processing)
        """
        with self.processing_lock:
            if not self.processing_active:
                return
            
            self.processing_active = False
            
            # Stop all threads (metronome, sound, etc.) immediately
            self._stop_all_threads()
            
            # Wait for processing thread to finish
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=3.0)
            
            self._cleanup_processing()
    
    def _stop_all_threads(self):
        """Stop all threads spawned from the processing loop."""
        if not self.components:
            return
        
        metronome_manager = self.components.get('beat_manager')
        sound_manager = self.components.get('sound_manager')
        
        if metronome_manager:
            metronome_manager.stop()
        if sound_manager:
            sound_manager.stop_continuous_warmup()
    
    def get_current_frame(self) -> np.ndarray | None:
        """Get the current frame for UI display.
        
        Returns:
            np.ndarray: Current frame, or None if no frame available
        """
        if not self.frame_queue.empty():
            frame = self.frame_queue.get_nowait()
            self.current_frame = frame
            return frame
        return self.current_frame
    
    def get_session_time(self) -> float:
        """Get elapsed session time in seconds.
        
        Returns:
            float: Session elapsed time, or 0.0 if not started
        """
        clock_manager = self.components['clock_manager']
        return clock_manager.get_session_elapsed_time()
    
    def get_current_bpm(self) -> int:
        """Get current BPM setting.
        
        Returns:
            int: Current BPM, or 60 if not available
        """
        return self.settings.get_beats_per_minute()
    
    def get_time_signature(self) -> str:
        """Get current time signature.
        
        Returns:
            str: Current time signature, or "4/4" if not available
        """
        return self.settings.get_time_signature()
    
    def update_bpm(self, bpm: int):
        """Update BPM setting and propagate to backend.
        
        Args:
            bpm: New BPM value
        """
        self.settings.set_beats_per_minute(bpm)
        
        if 'beat_manager' in self.components:
            metronome_manager = self.components['beat_manager']
            metronome_manager.bpm = bpm
            metronome_manager.beat_interval = 60 / bpm
    
    def update_time_signature(self, ts: str):
        """Update time signature setting and propagate to backend.
        
        Args:
            ts: New time signature ("4/4" or "3/4")
        """
        self.settings.set_time_signature(ts)
        
        if 'beat_manager' in self.components:
            metronome_manager = self.components['beat_manager']
            metronome_manager.time_signature = ts
            metronome_manager.beats_per_measure = int(ts.split('/')[0])
        
        if 'beat_position_manager' in self.components:
            beat_manager = self.components['beat_position_manager']
            beat_manager.time_signature = ts
        
        if 'visual_manager' in self.components:
            visual_manager = self.components['visual_manager']
            visual_manager.time_signature = ts
    
    def check_state_changes(self) -> str | None:
        """Check for state changes (polled by UI).
        
        Returns:
            str: New state name if state changed, None otherwise
        """
        if not self.state_change_queue.empty():
            return self.state_change_queue.get_nowait()
        return None

