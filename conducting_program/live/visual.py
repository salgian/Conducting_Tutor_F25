# Visual management for the conducting tutor - handles all visual elements and display functions

import cv2

class VisualManager:
    """Comprehensive visual management for the conducting tutor system."""
    
    def __init__(self, time_signature):
        """Initialize the visual manager with the specified time signature."""
        self.time_signature = time_signature
        self.beat_duration = 0.1  # Duration to show each beat circle
        self.beat_manager = None  # Will be set by external system
        self.current_frame = None  # Stores the current annotated frame
        self.components = None  # Will be set with all components for access
        self.window_name = 'Live Pose Detection'
        self.window_initialized = False
    
    def set_beat_manager(self, beat_manager):
        """Set the beat manager for position data and hit detection."""
        self.beat_manager = beat_manager
    
    def set_components(self, components):
        """Set components dict for accessing all system components."""
        self.components = components

    # -------- Frame Management --------
    
    def get_frame_dimensions(self):
        """Get the current frame height and width."""
        return self.current_frame.shape[0], self.current_frame.shape[1]
    
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
        """Update per-frame visual elements (timing info, etc.)."""
        self.display_timing_info(camera_manager, clock_manager)
    
    def display_timing_info(self, camera_manager, clock_manager):
        """Display FPS and timing information on the frame."""
        fps = camera_manager.calculate_fps()
        program_time = clock_manager.get_program_elapsed_time()
        session_time = clock_manager.get_session_elapsed_time()
        
        cv2.putText(self.current_frame, 'FPS: {}'.format(fps), (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(self.current_frame, 'Program: {}'.format(clock_manager.format_time(program_time)), (10, 70), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        cv2.putText(self.current_frame, 'Session: {}'.format(clock_manager.format_time(session_time)), (10, 110), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

    # -------- Beat Visualization --------
    
    def display_all_beats(self, current_beat):
        """Display all beat indicators on the frame with current beat highlighted."""
        self.draw_beat_circles(current_beat)
    
    def display_single_beat(self, beat_number):
        """Display beat indicators with the specified beat number highlighted."""
        self.draw_beat_circles(beat_number)
    
    def draw_beat_circles(self, current_beat):
        """Draw beat indicator circles based on time signature and highlight current beat."""
        if current_beat is None or self.beat_manager is None:
            return
        
        # Get circle positions from beat manager
        positions = self.beat_manager.get_circle_positions()
        if not positions:
            return
        
        # Draw all circles, highlight the current one
        for i, pos in enumerate(positions):
            if i + 1 == current_beat:
                cv2.circle(self.current_frame, pos, 30, (0, 0, 255), -1)  # Current beat - bright red
            else:
                cv2.circle(self.current_frame, pos, 25, (0, 0, 150), -1)  # Other beats - dim red
    
    def draw_setup_circles(self):
        """Draw all beat circles for setup state (no highlighting)."""
        if self.beat_manager is None:
            return
            
        # Get circle positions from beat manager
        positions = self.beat_manager.get_circle_positions()
        if not positions:
            return
        
        # Draw all circles with same color (no highlighting)
        for pos in positions:
            cv2.circle(self.current_frame, pos, 25, (0, 0, 150), -1)  # All circles - dim red
    
    def draw_processing_circles(self, current_beat):
        """Draw only the current beat circle for processing state (blinking effect)."""
        if current_beat is None or self.beat_manager is None:
            return
        
        # Get circle positions from beat manager
        positions = self.beat_manager.get_circle_positions()
        if not positions:
            return
        
        # Draw only the current beat circle
        if 1 <= current_beat <= len(positions):
            pos = positions[current_beat - 1]
            cv2.circle(self.current_frame, pos, 30, (0, 0, 255), -1)  # Current beat only - bright red
    
    # -------- Midpoint Visualization --------
    
    def draw_midpoint_live_line(self, pose_landmarks):
        """Draw the current live midpoint line on the frame."""
        midpoint = pose_landmarks.get_midpoint()
        if midpoint is not None:
            frame_height, frame_width = self.get_frame_dimensions()
            midpoint_normalized = int(midpoint * frame_width)
            cv2.line(self.current_frame, (midpoint_normalized, 0), (midpoint_normalized, frame_height), (225, 255, 255), 2)
            cv2.putText(self.current_frame, f'Live Midpoint: {midpoint:.3f}', (10, 150), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        else:
            left_shoulder = pose_landmarks.left_shoulder_12
            right_shoulder = pose_landmarks.right_shoulder_11
            cv2.putText(self.current_frame, f'L:{left_shoulder is not None} R:{right_shoulder is not None}', (10, 150), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

    def draw_midpoint_threshold_lines(self, sway_detection, midpoint_processor):
        """Draw sway threshold lines on the frame to show acceptable movement boundaries."""
        # Get reference midpoint and sway threshold
        reference_midpoint = midpoint_processor.get_reference_midpoint()
        sway_threshold = sway_detection.get_threshold()
        if reference_midpoint is None or sway_threshold is None:
            return
        
        frame_height, frame_width = self.get_frame_dimensions()
        # Calculate positive and negative thresholds from reference midpoint
        positive_threshold = reference_midpoint + sway_threshold
        negative_threshold = reference_midpoint - sway_threshold
        # Convert normalized coordinates to pixel coordinates
        positive_normalized = int(positive_threshold * frame_width)
        negative_normalized = int(negative_threshold * frame_width)
        cv2.line(self.current_frame, (positive_normalized, 0), (positive_normalized, frame_height), (0, 0, 255), 2)
        cv2.line(self.current_frame, (negative_normalized, 0), (negative_normalized, frame_height), (0, 0, 255), 2)

    def draw_midpoint_line(self, midpoint_processor):
        """Draw the reference midpoint line on the frame."""
        reference_midpoint = midpoint_processor.get_reference_midpoint()
        if reference_midpoint is None:
            return
        frame_height, frame_width = self.get_frame_dimensions()
        reference_normalized = int(reference_midpoint * frame_width)
        cv2.line(self.current_frame, (reference_normalized, 0), (reference_normalized, frame_height), (255, 255, 0), 2)
        cv2.putText(self.current_frame, f'Ref Midpoint: {reference_midpoint:.3f}', (10, 170), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    # -------- State Visuals --------
    
    def display_setup_visuals(self):
        """Display visuals for the setup state."""
        # State name in bottom left
        frame_height = self.current_frame.shape[0]
        
        # State name
        cv2.putText(self.current_frame, "SETUP", (10, frame_height - 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # Details below state name
        cv2.putText(self.current_frame, "Bring band to attention", (10, frame_height - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Display all circles based on time signature (no highlighting)
        self.draw_setup_circles()
    
    def display_countdown_visuals(self, beat_manager):
        """Display visuals for the countdown state."""
        # State name in bottom left
        frame_height = self.current_frame.shape[0]
        
        # State name
        cv2.putText(self.current_frame, "COUNTDOWN", (10, frame_height - 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
        
        if beat_manager.get_measure_count() == 0:
            # Details below state name
            cv2.putText(self.current_frame, "Silent Measure", (10, frame_height - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            # Show all circles during silent measure
            self.draw_setup_circles()
        else:
            # Always show all circles with rotating highlight during countdown (no blinking)
            self.draw_beat_circles(beat_manager.get_current_beat())
            # Details below state name
            cv2.putText(self.current_frame, f"Measure {beat_manager.get_measure_count()}", (10, frame_height - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    
    def display_processing_visuals(self):
        """Display visuals for the processing state."""
        # Get components we need
        beat_position_manager = self.components['beat_position_manager']
        metronome_manager = self.components['beat_manager']
        sway_detection = self.components['sway_detection']
        mirror_detection = self.components['mirror_detection']
        elbow_detection = self.components['elbow_detection']
        pose_landmarks = self.components['pose_landmarks']
        midpoint_processor = self.components['midpoint_processor']
        
        frame_width = self.current_frame.shape[1]
        frame_height = self.current_frame.shape[0]
        
        # State name in bottom left
        cv2.putText(self.current_frame, "PROCESSING", (10, frame_height - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # Show beat circle briefly around beat timing for natural feel
        if beat_position_manager.get_show_visual():
            # Show blinking effect - only current beat circle (get beat from metronome)
            self.draw_processing_circles(metronome_manager.get_current_beat())
        
        # Display detection feedback - positioned at top center
        center_x = frame_width // 2
        feedback_y_start = 100
        
        feedback_index = 0
        if sway_detection.get_sway_flag():
            y_pos = feedback_y_start + (feedback_index * 60)
            text = "Swaying"
            (text_width, _), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 3)
            cv2.putText(self.current_frame, text, (center_x - text_width // 2, y_pos), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
            feedback_index += 1
            
        if mirror_detection.get_mirroring_flag():
            y_pos = feedback_y_start + (feedback_index * 60)
            text = "Mirroring"
            (text_width, _), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 3)
            cv2.putText(self.current_frame, text, (center_x - text_width // 2, y_pos), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
            feedback_index += 1
            
        if elbow_detection.get_watch_left_elbow():
            y_pos = feedback_y_start + (feedback_index * 60)
            text = "Watch Left Elbow"
            (text_width, _), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 3)
            cv2.putText(self.current_frame, text, (center_x - text_width // 2, y_pos), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
            feedback_index += 1
            
        if elbow_detection.get_watch_right_elbow():
            y_pos = feedback_y_start + (feedback_index * 60)
            text = "Watch Right Elbow"
            (text_width, _), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 3)
            cv2.putText(self.current_frame, text, (center_x - text_width // 2, y_pos), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
        
        # Display midpoint visualizations
        self.draw_midpoint_live_line(pose_landmarks)
        # Only show threshold lines when actively swaying (outside threshold)
        if sway_detection.get_sway_flag():
            self.draw_midpoint_threshold_lines(sway_detection, midpoint_processor)
        self.draw_midpoint_line(midpoint_processor)
        
        # TODO: Add tracking to hands to see if we make it into the circles in time
    
    def display_ending_visuals(self):
        """Display visuals for the ending state."""
        frame_width = self.current_frame.shape[1]
        frame_height = self.current_frame.shape[0]
        
        # State name in bottom left
        cv2.putText(self.current_frame, "ENDING", (10, frame_height - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # Center the session complete message
        center_x = frame_width // 2
        center_y = frame_height // 2
        
        text2 = "Session Complete"
        (text_width2, text_height2), _ = cv2.getTextSize(text2, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)
        cv2.putText(self.current_frame, text2, (center_x - text_width2 // 2, center_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Display final hit percentage if beat manager is available (centered below)
        if self.beat_manager:
            hit_percentage = self.beat_manager.get_hit_percentage()
            text3 = f"Hit Rate: {hit_percentage:.1f}%"
            (text_width3, _), _ = cv2.getTextSize(text3, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)
            cv2.putText(self.current_frame, text3, (center_x - text_width3 // 2, center_y + 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    # -------- Hit Feedback Display --------
    
    def display_hit_feedback(self):
        """Display hit feedback if beat was hit."""
        if self.beat_manager is None:
            return
        
        hit_status = self.beat_manager.get_current_hit_status()
        
        # Show HIT if we hit the beat
        if hit_status == "hit":
            frame_height, frame_width = self.get_frame_dimensions()
            text_x = frame_width // 2 - 50
            text_y = frame_height // 2
            cv2.putText(self.current_frame, "HIT!", (text_x, text_y), 
                        cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 255, 0), 5)