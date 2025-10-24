# Visual management for the conducting tutor - orchestrates all visual elements

import cv2
from .visuals.beat_visuals import BeatVisualizer
from .visuals.timing_visuals import TimingVisualizer
from .visuals.midpoint_visuals import MidpointVisualizer
from .visuals.feedback_visuals import FeedbackVisualizer
from .visuals.state_visuals import StateVisualizer

class VisualManager:
    """Orchestrates all visual elements for the conducting tutor."""
    
    def __init__(self, time_signature):
        self.time_signature = time_signature
        self.current_frame = None
        self.window_name = 'Live Pose Detection'
        self.window_initialized = False
        self.beat_manager = None
        self.components = None
        
        # Visualizer instances (initialized when components are set)
        self.beat_visual = None
        self.timing_visual = None
        self.midpoint_visual = None
        self.feedback_visual = None
        self.state_visual = None
    
    def set_beat_manager(self, beat_manager):
        """Set the beat manager for position data and hit detection."""
        self.beat_manager = beat_manager
    
    def set_components(self, components):
        """Set components dict and initialize all visualizers."""
        self.components = components
        self._initialize_visualizers()
    
    def _initialize_visualizers(self):
        """Initialize all specialized visualizer instances during startup."""
        self.beat_visual = BeatVisualizer(self.beat_manager)
        self.timing_visual = TimingVisualizer()
        self.midpoint_visual = MidpointVisualizer()
        self.feedback_visual = FeedbackVisualizer()
        self.state_visual = StateVisualizer()
        print("Visualizers initialized")

    # -------- Frame Management --------
    
    def get_frame_dimensions(self):
        """Get the current frame width and height."""
        return self.current_frame.shape[1], self.current_frame.shape[0]  # Return (width, height)
    
    def _add_letterbox(self, frame, target_width, target_height):
        """Add letterboxing/pillarboxing to maintain aspect ratio.
        
        Args:
            frame: Original frame to display
            target_width: Target window width
            target_height: Target window height
            
        Returns:
            Frame with letterboxing added to maintain aspect ratio
        """
        if frame is None:
            return frame
            
        # Get original frame dimensions
        orig_height, orig_width = frame.shape[:2]
        orig_aspect = orig_width / orig_height
        target_aspect = target_width / target_height
        
        # Calculate scaling to fit within target while maintaining aspect ratio
        if orig_aspect > target_aspect:
            # Frame is wider - fit to width, add letterbox top/bottom
            new_width = target_width
            new_height = int(target_width / orig_aspect)
        else:
            # Frame is taller - fit to height, add pillarbox left/right
            new_height = target_height
            new_width = int(target_height * orig_aspect)
        
        # Resize frame maintaining aspect ratio
        resized_frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
        
        # Create black canvas at target size
        canvas = cv2.copyMakeBorder(
            resized_frame,
            top=(target_height - new_height) // 2,
            bottom=(target_height - new_height + 1) // 2,
            left=(target_width - new_width) // 2,
            right=(target_width - new_width + 1) // 2,
            borderType=cv2.BORDER_CONSTANT,
            value=[0, 0, 0]
        )
        
        return canvas
    
    def show_frame(self):
        """Display the annotated frame and handle user input for quitting."""
        # Initialize resizable window on first call
        if not self.window_initialized:
            # Create resizable window
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
            # Set initial window size to match frame
            if self.current_frame is not None:
                height, width = self.current_frame.shape[:2]
                cv2.resizeWindow(self.window_name, width, height)
            self.window_initialized = True
        
        # Get current window size
        window_rect = cv2.getWindowImageRect(self.window_name)
        window_width, window_height = window_rect[2], window_rect[3]
        
        # Add letterboxing to maintain aspect ratio
        if window_width > 0 and window_height > 0:
            display_frame = self._add_letterbox(self.current_frame, window_width, window_height)
        else:
            display_frame = self.current_frame
        
        cv2.imshow(self.window_name, display_frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            return True  # Signal to exit
        return False  # Continue

    def setup_frame(self, camera_manager, media_pipe_declaration, pose):
        """Capture a frame from camera and process it for pose detection.
        Stores frame internally and returns (success, detection_result)."""
        success, frame = camera_manager.capture_frame()
        if not success:
           return False, None
        
        frame = cv2.flip(frame, 1)  # Flip the frame horizontally
        rgb_frame = camera_manager.convert_to_rgb(frame)  # Convert BGR to RGB
        results = media_pipe_declaration.process_pose_detection(pose, rgb_frame)
        self.current_frame = media_pipe_declaration.draw_pose_landmarks(frame, results)
        
        return True, results
    
    # -------- Timing Display --------
    
    def update_frame_visuals(self, camera_manager, clock_manager):
        """Update per-frame visual elements (timing info)."""
        fps = camera_manager.calculate_fps()
        program_time = clock_manager.format_time(clock_manager.get_program_elapsed_time())
        session_time = clock_manager.format_time(clock_manager.get_session_elapsed_time())
        self.timing_visual.draw_fps_and_timers(self.current_frame, fps, program_time, session_time)
    
    # -------- Public API: State Display Methods --------
    
    def display_setup_visuals(self):
        """Orchestrate setup state visuals."""
        self.state_visual.draw_setup_label(self.current_frame)
        self.beat_visual.draw_beat_circles(self.current_frame, current_beat=1, mode='setup')
    
    def display_countdown_visuals(self, beat_manager):
        """Orchestrate countdown state visuals."""
        self.state_visual.draw_countdown_label(self.current_frame)
        self.beat_visual.draw_beat_circles(self.current_frame, beat_manager.get_current_beat(), mode='countdown')
    
    def display_processing_visuals(self):
        """Orchestrate processing state visuals."""
        # Get components
        beat_position_manager = self.components['beat_position_manager']
        metronome_manager = self.components['beat_manager']
        sway_detection = self.components['sway_detection']
        mirror_detection = self.components['mirror_detection']
        elbow_detection = self.components['elbow_detection']
        pose_landmarks = self.components['pose_landmarks']
        midpoint_processor = self.components['midpoint_processor']
        frame_width, frame_height = self.get_frame_dimensions()
        
        # State label
        self.state_visual.draw_processing_label(self.current_frame)
        
        # Beat and measure counter
        self.timing_visual.draw_beat_and_measure_info(
            self.current_frame, 
            metronome_manager.get_current_beat(), 
            metronome_manager.get_measure_count()
        )
        
        # Next beat preview (semi-transparent) - always visible, doesn't flash
        self.beat_visual.draw_next_beat_preview(self.current_frame, metronome_manager.get_current_beat())
        
        # Current beat (solid red) - only shown when flashing
        if beat_position_manager.get_show_visual():
            self.beat_visual.draw_beat_circles(self.current_frame, metronome_manager.get_current_beat(), mode='processing')
        
        # Midpoint visualization (drawn after beat circles so lines are visible on top)
        midpoint = midpoint_processor.get_live_midpoint()
        if midpoint is not None:
            self.midpoint_visual.draw_live_midpoint_line(self.current_frame, midpoint, frame_width, frame_height)
        
        reference_midpoint = midpoint_processor.get_reference_midpoint()
        if reference_midpoint is not None:
            self.midpoint_visual.draw_reference_midpoint_line(self.current_frame, reference_midpoint, frame_width, frame_height)
            
        if sway_detection.get_sway_flag():
            sway_threshold = sway_detection.get_threshold()
            self.midpoint_visual.draw_sway_threshold_lines(
                self.current_frame, reference_midpoint, sway_threshold, frame_width, frame_height
            )
        
        # Feedback messages (drawn last, on top of everything)
        feedback_flags = {
            'swaying': sway_detection.get_sway_flag(),
            'mirroring': mirror_detection.get_mirroring_flag(),
            'watch_left_elbow': elbow_detection.get_watch_left_elbow(),
            'watch_right_elbow': elbow_detection.get_watch_right_elbow()
        }
        self.feedback_visual.draw_feedback_messages(self.current_frame, feedback_flags)
    
    def display_ending_visuals(self):
        """Orchestrate ending state visuals."""
        self.state_visual.draw_ending_label(self.current_frame)
        hit_percentage = self.beat_manager.get_hit_percentage() if self.beat_manager else None
        self.state_visual.draw_session_complete_message(self.current_frame, hit_percentage)
    
    # -------- Hit Feedback Display --------
    
    def display_hit_feedback(self):
        """Display HIT! message when beat is hit."""
        if self.beat_visual:
            self.beat_visual.draw_hit_feedback(self.current_frame)
    
    # -------- Backward Compatibility Wrappers --------
    
    def display_all_beats(self, current_beat):
        """Wrapper for backward compatibility - draws beats in countdown mode."""
        self.beat_visual.draw_beat_circles(self.current_frame, current_beat, mode='countdown')
    
    def display_single_beat(self, beat_number):
        """Wrapper for backward compatibility - draws beats in countdown mode."""
        self.beat_visual.draw_beat_circles(self.current_frame, beat_number, mode='countdown')
