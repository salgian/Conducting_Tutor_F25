# Visual management for the conducting tutor - handles all visual elements and display functions

import cv2

class VisualManager:
    """Comprehensive visual management for the conducting tutor system."""
    
    def __init__(self, time_signature):
        """Initialize the visual manager with the specified time signature."""
        self.time_signature = time_signature
        self.beat_duration = 0.1  # Duration to show each beat circle
        self.beat_manager = None  # Will be set by external system
    
    def set_beat_manager(self, beat_manager):
        """Set the beat manager for position data and hit detection."""
        self.beat_manager = beat_manager

    # -------- Frame Management --------
    
    def show_frame(self, annotated_frame):
        """Display the annotated frame and handle user input for quitting."""
        cv2.imshow('Live Pose Detection', annotated_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            return True  # Signal to exit
        return False  # Continue

    def setup_frame(self, camera_manager, media_pipe_declaration, pose):
        """Capture a frame from camera and process it for pose detection."""
        success, frame = camera_manager.capture_frame()
        if not success:
           return None, None
        
        frame = cv2.flip(frame, 1)  # Flip the frame horizontally
        rgb_frame = camera_manager.convert_to_rgb(frame)  # Convert BGR to RGB
        results = media_pipe_declaration.process_pose_detection(pose, rgb_frame)
        annotated_frame = media_pipe_declaration.draw_pose_landmarks(frame, results)
        
        return annotated_frame, results
    
    # -------- Timing Display --------
    
    def display_timing_info(self, annotated_frame, camera_manager, clock_manager):
        """Display FPS and timing information on the frame."""
        fps = camera_manager.calculate_fps()
        program_time = clock_manager.get_program_elapsed_time()
        session_time = clock_manager.get_session_elapsed_time()
        
        cv2.putText(annotated_frame, 'FPS: {}'.format(fps), (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(annotated_frame, 'Program: {}'.format(clock_manager.format_time(program_time)), (10, 70), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        cv2.putText(annotated_frame, 'Session: {}'.format(clock_manager.format_time(session_time)), (10, 110), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

    # -------- Beat Visualization --------
    
    def display_all_beats(self, frame, current_beat):
        """Display all beat indicators on the frame with current beat highlighted."""
        self.draw_beat_circles(frame, current_beat)
    
    def display_single_beat(self, frame, beat_number):
        """Display beat indicators with the specified beat number highlighted."""
        self.draw_beat_circles(frame, beat_number)
    
    def draw_beat_circles(self, frame, current_beat):
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
                cv2.circle(frame, pos, 30, (0, 0, 255), -1)  # Current beat - bright red
            else:
                cv2.circle(frame, pos, 25, (0, 0, 150), -1)  # Other beats - dim red
    
    def draw_setup_circles(self, frame):
        """Draw all beat circles for setup state (no highlighting)."""
        if self.beat_manager is None:
            return
            
        # Get circle positions from beat manager
        positions = self.beat_manager.get_circle_positions()
        if not positions:
            return
        
        # Draw all circles with same color (no highlighting)
        for pos in positions:
            cv2.circle(frame, pos, 25, (0, 0, 150), -1)  # All circles - dim red
    
    def draw_processing_circles(self, frame, current_beat):
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
            cv2.circle(frame, pos, 30, (0, 0, 255), -1)  # Current beat only - bright red
    
    # -------- Midpoint Visualization --------
    
    def draw_midpoint_live_line(self, pose_landmarks, annotated_frame):
        """Draw the current live midpoint line on the frame."""
        midpoint = pose_landmarks.get_midpoint()
        if midpoint is not None:
            frame_height = annotated_frame.shape[0]
            frame_width = annotated_frame.shape[1]
            midpoint_normalized = int(midpoint * frame_width)
            cv2.line(annotated_frame, (midpoint_normalized, 0), (midpoint_normalized, frame_height), (225, 255, 255), 2)
            cv2.putText(annotated_frame, f'Live Midpoint: {midpoint:.3f}', (10, 150), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        else:
            left_shoulder = pose_landmarks.left_shoulder_12
            right_shoulder = pose_landmarks.right_shoulder_11
            cv2.putText(annotated_frame, f'L:{left_shoulder is not None} R:{right_shoulder is not None}', (10, 150), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

    def draw_midpoint_threshold_lines(self, sway_detection, midpoint_processor, annotated_frame):
        """Draw sway threshold lines on the frame to show acceptable movement boundaries."""
        # Get reference midpoint and sway threshold
        reference_midpoint = midpoint_processor.get_reference_midpoint()
        sway_threshold = sway_detection.get_threshold()
        if reference_midpoint is None or sway_threshold is None:
            return
        
        frame_height = annotated_frame.shape[0]
        frame_width = annotated_frame.shape[1]
        # Calculate positive and negative thresholds from reference midpoint
        positive_threshold = reference_midpoint + sway_threshold
        negative_threshold = reference_midpoint - sway_threshold
        # Convert normalized coordinates to pixel coordinates
        positive_normalized = int(positive_threshold * frame_width)
        negative_normalized = int(negative_threshold * frame_width)
        cv2.line(annotated_frame, (positive_normalized, 0), (positive_normalized, frame_height), (0, 0, 255), 2)
        cv2.line(annotated_frame, (negative_normalized, 0), (negative_normalized, frame_height), (0, 0, 255), 2)

    def draw_midpoint_line(self, midpoint_processor, annotated_frame):
        """Draw the reference midpoint line on the frame."""
        reference_midpoint = midpoint_processor.get_reference_midpoint()
        if reference_midpoint is None:
            return
        frame_height = annotated_frame.shape[0]
        frame_width = annotated_frame.shape[1]
        reference_normalized = int(reference_midpoint * frame_width)
        cv2.line(annotated_frame, (reference_normalized, 0), (reference_normalized, frame_height), (255, 255, 0), 2)
        cv2.putText(annotated_frame, f'Ref Midpoint: {reference_midpoint:.3f}', (10, 170), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    # -------- State Visuals --------
    
    def display_setup_visuals(self, annotated_frame):
        """Display visuals for the setup state."""
        cv2.putText(annotated_frame, "SETUP", (annotated_frame.shape[1] - 10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(annotated_frame, "Bring band to attention", (annotated_frame.shape[1] - 10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Display all circles based on time signature (no highlighting)
        self.draw_setup_circles(annotated_frame)
    
    def display_countdown_visuals(self, annotated_frame, beat_manager):
        """Display visuals for the countdown state."""
        cv2.putText(annotated_frame, "COUNTDOWN", (annotated_frame.shape[1] - 10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
        
        if beat_manager.get_measure_count() == 0:
            cv2.putText(annotated_frame, "Silent Measure", (annotated_frame.shape[1] - 10, 60), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            # Show all circles during silent measure
            self.draw_setup_circles(annotated_frame)
        else:
            # Always show all circles with rotating highlight during countdown (no blinking)
            self.draw_beat_circles(annotated_frame, beat_manager.get_current_beat())
            cv2.putText(annotated_frame, f"Measure {beat_manager.get_measure_count()}", (annotated_frame.shape[1] - 10, 60), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    
    def display_processing_visuals(self, annotated_frame, beat_manager, sway_detection, mirror_detection, 
                                   elbow_detection, pose_landmarks, midpoint_processor):
        """Display visuals for the processing state."""
        cv2.putText(annotated_frame, "PROCESSING", (annotated_frame.shape[1] - 10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # Show beat circle briefly around beat timing for natural feel
        if beat_manager.get_show_visual():
            # Show blinking effect - only current beat circle
            self.draw_processing_circles(annotated_frame, beat_manager.get_current_beat())
            
            # Check for hand hits and display feedback
            self.check_and_display_hits(annotated_frame, pose_landmarks, beat_manager)
        
        # Display detection feedback
        if sway_detection.get_sway_flag():
            cv2.putText(annotated_frame, "Swaying", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2)
        if mirror_detection.get_mirroring_flag():
            cv2.putText(annotated_frame, "Mirroring", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2)
        if elbow_detection.get_watch_left_elbow():
            cv2.putText(annotated_frame, "Watch Left Elbow", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2)
        if elbow_detection.get_watch_right_elbow():
            cv2.putText(annotated_frame, "Watch Right Elbow", (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2)
        
        # Display midpoint visualizations
        self.draw_midpoint_live_line(pose_landmarks, annotated_frame)
        self.draw_midpoint_threshold_lines(sway_detection, midpoint_processor, annotated_frame)
        self.draw_midpoint_line(midpoint_processor, annotated_frame)
        
        # TODO: Add tracking to hands to see if we make it into the circles in time
    
    def display_ending_visuals(self, annotated_frame):
        """Display visuals for the ending state."""
        cv2.putText(annotated_frame, "ENDING", (annotated_frame.shape[1] - 10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(annotated_frame, "Session Complete", (50, 300), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Display final hit percentage if beat manager is available
        if self.beat_manager:
            hit_percentage = self.beat_manager.get_hit_percentage()
            cv2.putText(annotated_frame, f"Hit Rate: {hit_percentage:.1f}%", (50, 350), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    # -------- Hit/Miss Display --------
    
    def display_hit_miss_feedback(self, annotated_frame):
        """Display hit feedback in the middle of the screen."""
        if self.beat_manager is None:
            return
        
        hit_status = self.beat_manager.get_current_hit_status()
        
        # Show HIT if we hit the beat
        if hit_status == "hit":
            frame_height = annotated_frame.shape[0]
            frame_width = annotated_frame.shape[1]
            text_x = frame_width // 2 - 50
            text_y = frame_height // 2
            cv2.putText(annotated_frame, "HIT!", (text_x, text_y), 
                        cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 255, 0), 5)
    
    def check_and_display_hits(self, annotated_frame, pose_landmarks, metronome_manager):
        """Check for hand hits and display feedback."""
        if self.beat_manager is None:
            return
        
        # Get right hand landmarks from MediaPipe
        right_hand_centroid = self.get_right_hand_centroid(pose_landmarks, annotated_frame)
        
        # Check if hand is in circle
        if right_hand_centroid:
            self.beat_manager.check_hand_in_circle(right_hand_centroid, metronome_manager.get_current_beat())
        
        # Display hit/miss feedback
        self.display_hit_miss_feedback(annotated_frame)
    
    def get_right_hand_centroid(self, pose_landmarks, annotated_frame):
        """Get the centroid of the right hand landmarks."""
        # Get right hand landmarks (MediaPipe hand detection)
        # This would need to be implemented with MediaPipe hand detection
        # For now, using right wrist as fallback
        right_hand = pose_landmarks.get_pose_landmark_15()  # Right wrist
        
        if right_hand:
            right_x, right_y = right_hand
            # Convert normalized coordinates to pixel coordinates
            frame_height = annotated_frame.shape[0]
            frame_width = annotated_frame.shape[1]
            return (int(right_x * frame_width), int(right_y * frame_height))
        
        return None