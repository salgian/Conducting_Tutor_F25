from enum import Enum

class State(Enum):
    SETUP = "setup"
    COUNTDOWN = "countdown"
    PROCESSING = "processing"
    ENDING = "ending"

class SystemState:
    def __init__(self, components):
        self.current_state = SetupState(components)
        self.components = components
    
    def get_current_state(self):
        return self.current_state
    
    def change_state(self, new_state):
        match new_state:
            case State.SETUP.value:
                self.current_state = SetupState(self.components)
            case State.COUNTDOWN.value:
                self.current_state = CountdownState(self.components)
            case State.PROCESSING.value:
                self.current_state = ProcessingState(self.components)
            case State.ENDING.value:
                self.current_state = EndingState(self.components)
        print(f"State changed to: {new_state}")

class SetupState:
    def __init__(self, components):
        self.state_name = State.SETUP.value
        self.components = components
        self.movement_tracking = False
        self.movement_start_time = None
        self.previous_left_y = None
        self.previous_right_y = None
        self.first_frame = True
        self.movement_hold_duration = 2.0
        self.significant_movement_threshold = 0.1
        print("=== SETUP PHASE ===")
    
    def get_state_name(self):
        return self.state_name
    
    def main(self):
        pose_landmarks = self.components['pose_landmarks']
        clock_manager = self.components['clock_manager']
        visual_manager = self.components['visual_manager']
        
        if not self.first_frame:
            # Normal processing logic
            next_state = self._process_hand_movements(pose_landmarks, clock_manager, visual_manager)
            return next_state
        else:
            # First frame initialization
            self._initialize_first_frame(pose_landmarks)
            self.first_frame = False
            visual_manager.display_setup_visuals()
            return "setup"
    
    def _process_hand_movements(self, pose_landmarks, clock_manager, visual_manager):
        """Process hand movements to detect attention gesture."""
        # Get hand positions
        left_hand, right_hand = self._get_hand_positions(pose_landmarks)
        
        if not self._validate_hand_positions(left_hand, right_hand, visual_manager):
            return "setup"
        
        left_x, left_y = left_hand
        right_x, right_y = right_hand
        
        # Initialize previous positions if needed
        if not self._initialize_previous_positions(left_y, right_y, visual_manager):
            return "setup"
        
        # Check for movement and handle attention tracking
        next_state = self._handle_attention_tracking(left_y, right_y, clock_manager, visual_manager)
        
        # Update previous positions for next frame
        self._update_previous_positions(left_y, right_y)
        
        # Display visuals
        visual_manager.display_setup_visuals()
        
        return next_state
    
    def _get_hand_positions(self, pose_landmarks):
        """Get left and right hand landmark positions."""
        left_hand = pose_landmarks.get_pose_landmark_16()  # Left wrist
        right_hand = pose_landmarks.get_pose_landmark_15()  # Right wrist
        return left_hand, right_hand
    
    def _validate_hand_positions(self, left_hand, right_hand, visual_manager):
        """Validate that both hands are detected."""
        if not left_hand or not right_hand:
            visual_manager.display_setup_visuals()
            return False
        return True
    
    def _initialize_previous_positions(self, left_y, right_y, visual_manager):
        """Initialize previous hand positions if they're None."""
        if self.previous_left_y is None or self.previous_right_y is None:
            self.previous_left_y = left_y
            self.previous_right_y = right_y
            visual_manager.display_setup_visuals()
            return False
        return True
    
    def _check_hands_raised(self, left_y, right_y):
        """Check if both hands moved upward significantly."""
        left_moved_up = left_y is not None and left_y < self.previous_left_y - self.significant_movement_threshold
        right_moved_up = right_y is not None and right_y < self.previous_right_y - self.significant_movement_threshold
        return left_moved_up and right_moved_up
    
    def _check_hands_dropped(self, left_y, right_y):
        """Check if either hand dropped down significantly."""
        left_dropped_down = left_y is not None and left_y > self.previous_left_y + self.significant_movement_threshold
        right_dropped_down = right_y is not None and right_y > self.previous_right_y + self.significant_movement_threshold
        return left_dropped_down or right_dropped_down
    
    def _handle_attention_tracking(self, left_y, right_y, clock_manager, visual_manager):
        """Handle tracking of attention gesture and timing."""
        both_hands_to_attention = self._check_hands_raised(left_y, right_y)
        
        if both_hands_to_attention and not self.movement_tracking:
            # Start tracking when both hands are brought to attention
            self._start_tracking(clock_manager)
            return "setup"
        elif self.movement_tracking:
            # Check if hands are still in attention position
            return self._check_attention_duration(left_y, right_y, clock_manager)
        
        return "setup"
    
    def _start_tracking(self, clock_manager):
        """Start tracking the attention gesture."""
        self.movement_start_time = clock_manager.get_current_timestamp()
        self.movement_tracking = True
    
    def _check_attention_duration(self, left_y, right_y, clock_manager):
        """Check if hands have been held at attention long enough."""
        if self._check_hands_dropped(left_y, right_y):
            self._reset_tracking()
            return "setup"
        
        # Check if held long enough to transition
        elapsed_time = clock_manager.get_current_timestamp() - self.movement_start_time
        if elapsed_time >= self.movement_hold_duration:
            self._reset_tracking()
            return "countdown"
        
        return "setup"
    
    def _update_previous_positions(self, left_y, right_y):
        """Update the previous hand positions."""
        self.previous_left_y = left_y
        self.previous_right_y = right_y
    
    def _initialize_first_frame(self, pose_landmarks):
        left_hand = pose_landmarks.get_pose_landmark_16()
        right_hand = pose_landmarks.get_pose_landmark_15()
        if left_hand and right_hand:
            _, self.previous_left_y = left_hand
            _, self.previous_right_y = right_hand
        else:
            # Set default values to prevent None errors
            self.previous_left_y = 0.0
            self.previous_right_y = 0.0
    
    def _reset_tracking(self):
        self.movement_tracking = False
        self.movement_start_time = None

class CountdownState:
    def __init__(self, components):
        self.state_name = State.COUNTDOWN.value
        self.components = components
        self.first_frame = True
        print("=== COUNTDOWN PHASE ===")
    
    def get_state_name(self):
        return self.state_name
    
    def main(self):
        beat_manager = self.components['beat_manager']
        visual_manager = self.components['visual_manager']
        
        if not self.first_frame:
            # Normal countdown processing (2 measures: 0 and 1)
            if beat_manager.get_measure_count() >= 2:
                return "processing"
            
            # Display countdown visuals
            visual_manager.display_countdown_visuals(beat_manager)
            
            return "countdown"
        else:
            # First frame initialization
            # Stop continuous audio warmup before starting metronome
            # sound_manager = self.components['sound_manager']
            self.components['sound_manager'].stop_continuous_warmup()
            
            beat_manager.start()
            self.first_frame = False
            visual_manager.display_countdown_visuals(beat_manager)
            return "countdown"

class ProcessingState:
    def __init__(self, components):
        self.state_name = State.PROCESSING.value
        self.components = components
        self.first_frame = True
        self.midpoint_initialized = False
        # Reset beat and measure count to start from 1
        components['beat_manager'].reset_count()
        print("=== PROCESSING PHASE ===")
    
    def get_state_name(self):
        return self.state_name
    
    def main(self):
        pose_landmarks = self.components['pose_landmarks']
        clock_manager = self.components['clock_manager']
        midpoint_processor = self.components['midpoint_processor']
        sway_detection = self.components['sway_detection']
        mirror_detection = self.components['mirror_detection']
        elbow_detection = self.components['elbow_detection']
        beat_manager = self.components['beat_position_manager']
        metronome_manager = self.components['beat_manager']
        visual_manager = self.components['visual_manager']
        
        if not self.first_frame:
            # Normal processing logic
            # Update midpoint and run detection components
            midpoint_processor.update_current_midpoint(pose_landmarks)
            midpoint_processor.update_midpoint_check(pose_landmarks, clock_manager)
            
            if midpoint_processor.get_reference_midpoint() is not None:
                sway_detection.main(midpoint_processor.get_reference_midpoint(), midpoint_processor.get_live_midpoint())
                mirror_detection.main(pose_landmarks, clock_manager, midpoint_processor.get_live_midpoint())
            
            elbow_detection.main(pose_landmarks)
            beat_manager.main(pose_landmarks, metronome_manager, visual_manager)
            
            # Display processing visuals
            visual_manager.display_processing_visuals()
            
            return "processing"
        else:
            # First frame initialization
            midpoint_processor.initialize_reference_midpoint(pose_landmarks, clock_manager)
            self.midpoint_initialized = True
            self.first_frame = False
            
            # Pre-display the first processing beat to avoid missing it
            visual_manager.display_processing_visuals()
            return "processing"

class EndingState:
    def __init__(self, components):
        self.state_name = State.ENDING.value
        self.components = components
        self.first_frame = True
        print("=== ENDING PHASE ===")
    
    def get_state_name(self):
        return self.state_name
    
    def main(self):
        beat_manager = self.components['beat_manager']
        visual_manager = self.components['visual_manager']
        
        if not self.first_frame:
            # Normal ending display
            visual_manager.display_ending_visuals()
            return "ending"
        else:
            # First frame initialization
            beat_manager.stop()
            self.first_frame = False
            visual_manager.display_ending_visuals()
            return "ending"