# Beat position management and hit detection for the conducting tutor

import math
import threading
import time

class BeatManager:
    """Manages beat positions, hit detection, and visual coordination."""
    
    def __init__(self, time_signature):
        """Initialize the beat manager with time signature."""
        # -------------------- Configuration --------------------
        self.time_signature = time_signature
        self.circle_radius = 60
        self.hit_threshold = 25
        
        # -------------------- Hit Detection --------------------
        self.current_hit_status = None
        self.beat_hit_status = None
        self.current_beat = None
        
        # -------------------- Visual Timing --------------------
        self.show_visual = False
        self.visual_lock = threading.Lock()
        self.visual_duration = 0.4  # Duration to show visual (in seconds)
        self.visual_start_time = None
        
    # -------------------- Position Management --------------------
    
    def get_circle_positions(self):
        """Get circle positions based on time signature."""
        match self.time_signature:
            case "4/4":
                return [(1200, 600), (1050, 500), (1350, 500), (1250, 550)]
            case "3/4":
                return [(400, 200), (300, 300), (500, 300)]
            case _:
                return []
    
    # -------------------- Hit Detection --------------------
    
    def main(self, pose_landmarks, metronome_manager, visual_manager):
        """Main entry point for beat detection logic - centralized controller.
        
        Handles:
        - Running detection logic (check if hand hit beat)
        - Coordinating visual updates (display hit feedback)
        
        Args:
            pose_landmarks: PoseLandmarks object
            metronome_manager: MetronomeManager for current beat info
            visual_manager: VisualManager for displaying results
        """
        # Run detection logic
        current_beat = metronome_manager.get_current_beat()
        self.check_hand_hit(pose_landmarks, current_beat, visual_manager)
        
        # Update visuals if showing beat circle (visual timing managed internally)
        if self.get_show_visual():
            visual_manager.display_hit_feedback()
    
    def get_hand_centroid_pixels(self, pose_landmarks, frame_width, frame_height):
        """Get right hand centroid in pixel coordinates.
        
        Args:
            pose_landmarks: PoseLandmarks object with normalized coordinates
            frame_width: Width of the frame in pixels
            frame_height: Height of the frame in pixels
            
        Returns:
            Tuple (x, y) in pixel coordinates, or None if hand not detected
        """
        # Get right hand landmarks (MediaPipe hand detection)
        # For now, using right wrist as fallback
        right_hand = pose_landmarks.get_pose_landmark_15()  # Right wrist
        
        if right_hand:
            right_x, right_y = right_hand
            # Convert normalized coordinates to pixel coordinates
            return (int(right_x * frame_width), int(right_y * frame_height))
        
        return None
    
    def check_hand_hit(self, pose_landmarks, current_beat, visual_manager):
        """Check if hand position hits the current beat circle.
        
        Args:
            pose_landmarks: PoseLandmarks object
            current_beat: Current beat number (1-indexed)
            visual_manager: VisualManager to get frame dimensions from
            
        Returns:
            bool: True if hand is in circle, False otherwise
        """
        # Get frame dimensions directly from visual manager
        frame_height, frame_width = visual_manager.get_frame_dimensions()
        
        # Get hand position in pixels
        hand_position = self.get_hand_centroid_pixels(pose_landmarks, frame_width, frame_height)
        
        # Check if in circle
        return self.check_hand_in_circle(hand_position, current_beat)
    
    def check_hand_in_circle(self, hand_position, current_beat):
        """Check if hand position is inside the current beat circle.
        
        Args:
            hand_position: Tuple (x, y) in pixel coordinates
            current_beat: Current beat number (1-indexed)
            
        Returns:
            bool: True if hand is in circle, False otherwise
        """
        if hand_position is None or current_beat is None:
            return False
        
        if self.current_beat != current_beat:
            self.current_beat = current_beat
            self.beat_hit_status = None
        
        positions = self.get_circle_positions()
        if not positions or current_beat < 1 or current_beat > len(positions):
            return False
        
        target_pos = positions[current_beat - 1]
        hand_x, hand_y = hand_position
        circle_x, circle_y = target_pos
        
        distance = math.sqrt((hand_x - circle_x)**2 + (hand_y - circle_y)**2)
        is_hit = distance <= (self.circle_radius + self.hit_threshold)
        
        if is_hit:
            self.beat_hit_status = "hit"
        
        return is_hit
    
    
    # -------------------- Visual Timing Management --------------------
    
    def trigger_beat_visual(self, beat_time):
        """Trigger visual display for a beat.
        Called by MetronomeManager when a beat occurs.
        
        Args:
            beat_time: Timestamp when the beat was triggered
        """
        with self.visual_lock:
            self.show_visual = True
            self.visual_start_time = beat_time
    
    def get_show_visual(self):
        """Get whether visual should be shown (with duration timeout).
        
        Returns:
            bool: True if visual should be displayed, False otherwise
        """
        with self.visual_lock:
            if self.show_visual and self.visual_start_time is not None:
                # Check if visual duration has expired
                if time.time() - self.visual_start_time > self.visual_duration:
                    self.show_visual = False
                    self.visual_start_time = None
            return self.show_visual
    
    # -------------------- Accessor Methods --------------------
    
    def get_current_hit_status(self):
        """Get the current hit/miss status for this beat."""
        return self.beat_hit_status
