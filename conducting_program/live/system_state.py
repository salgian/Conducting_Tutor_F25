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
    
    def main(self, pose_landmarks, clock_manager, annotated_frame):
        if self.first_frame:
            self._initialize_first_frame(pose_landmarks)
            self.first_frame = False
            return "setup"
        
        # Get hand landmarks (note: landmark 15 is right wrist, 16 is left wrist)
        left_hand = pose_landmarks.get_pose_landmark_16()  # Left wrist
        right_hand = pose_landmarks.get_pose_landmark_15()  # Right wrist
        
        if not left_hand or not right_hand:
            return "setup"
        
        left_x, left_y = left_hand
        right_x, right_y = right_hand
        
        
        # Safety check for None values
        if self.previous_left_y is None or self.previous_right_y is None:
            self.previous_left_y = left_y
            self.previous_right_y = right_y
            return "setup"
        
        # Check for significant upward movement (bring to attention)
        left_moved_up = left_y < self.previous_left_y - self.significant_movement_threshold
        right_moved_up = right_y < self.previous_right_y - self.significant_movement_threshold
        
        # Check for significant downward movement (hands dropped from attention)
        left_dropped_down = left_y > self.previous_left_y + self.significant_movement_threshold
        right_dropped_down = right_y > self.previous_right_y + self.significant_movement_threshold
        
        # Check if both hands are brought to attention (significant upward movement)
        both_hands_to_attention = left_moved_up and right_moved_up
        
        if both_hands_to_attention and not self.movement_tracking:
            # Start tracking when both hands are brought to attention
            self.movement_start_time = clock_manager.get_current_timestamp()
            self.movement_tracking = True
        elif self.movement_tracking:
            # While tracking, check if hands are still in attention position
            # Allow small variations but reset if hands drop significantly
            if left_dropped_down or right_dropped_down:
                self._reset_tracking()
            else:
                # Hands are still in attention position, check timing
                elapsed_time = clock_manager.get_current_timestamp() - self.movement_start_time
                if elapsed_time >= self.movement_hold_duration:
                    self._reset_tracking()
                    return "countdown"
        
        # Update previous positions
        self.previous_left_y = left_y
        self.previous_right_y = right_y
        
        # Display setup visuals
        self.components['visual_manager'].display_setup_visuals(annotated_frame)
        
        return "setup"
    
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
    
    def main(self, pose_landmarks, clock_manager, annotated_frame):
        if self.first_frame:
            self.components['beat_manager'].start()
            self.first_frame = False
            return "countdown"
        
        if self.components['beat_manager'].get_measure_count() >= 3:
            return "processing"
        
        # Display countdown visuals
        self.components['visual_manager'].display_countdown_visuals(annotated_frame, self.components['beat_manager'])
        
        return "countdown"

class ProcessingState:
    def __init__(self, components):
        self.state_name = State.PROCESSING.value
        self.components = components
        self.first_frame = True
        self.midpoint_initialized = False
        print("=== PROCESSING PHASE ===")
    
    def get_state_name(self):
        return self.state_name
    
    def main(self, pose_landmarks, clock_manager, annotated_frame):
        if self.first_frame:
            self.components['midpoint_processor'].initialize_reference_midpoint(pose_landmarks, clock_manager)
            self.midpoint_initialized = True
            self.first_frame = False
            return "processing"
        
        self.components['midpoint_processor'].update_midpoint_check(pose_landmarks, clock_manager)
        
        if self.components['midpoint_processor'].get_reference_midpoint() is not None:
            self.components['sway_detection'].main(self.components['midpoint_processor'].get_reference_midpoint(), self.components['midpoint_processor'].get_live_midpoint())
            self.components['mirror_detection'].main(pose_landmarks, clock_manager, self.components['midpoint_processor'].get_live_midpoint())
            self.components['elbow_detection'].main(pose_landmarks)
        
        # Display processing visuals
        self.components['visual_manager'].display_processing_visuals(annotated_frame, 
                                                                    self.components['beat_manager'], 
                                                                    self.components['sway_detection'], 
                                                                    self.components['mirror_detection'], 
                                                                    self.components['elbow_detection'], 
                                                                    pose_landmarks, 
                                                                    self.components['midpoint_processor'])
        
        return "processing"

class EndingState:
    def __init__(self, components):
        self.state_name = State.ENDING.value
        self.components = components
        self.first_frame = True
        print("=== ENDING PHASE ===")
    
    def get_state_name(self):
        return self.state_name
    
    def main(self, pose_landmarks, clock_manager, annotated_frame):
        if self.first_frame:
            self.components['beat_manager'].stop()
            self.first_frame = False
            return "ending"
        
        # Display ending visuals
        self.components['visual_manager'].display_ending_visuals(annotated_frame)
        
        return "ending"