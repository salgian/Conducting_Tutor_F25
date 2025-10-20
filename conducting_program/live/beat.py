# Beat position management and hit detection for the conducting tutor

import math

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
    
    def check_hand_in_circle(self, hand_position, current_beat):
        """Check if hand position is inside the current beat circle."""
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
    
    
    # -------------------- Accessor Methods --------------------
    
    def get_current_hit_status(self):
        """Get the current hit/miss status for this beat."""
        return self.beat_hit_status
