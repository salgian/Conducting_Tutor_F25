import cv2

class BeatVisualizer:
    """Handles all beat circle and number visualization plus HIT feedback."""
    
    def __init__(self, beat_manager):
        self.beat_manager = beat_manager
    
    def draw_beat_circles(self, frame, current_beat, mode):
        """Unified method - draws beat circles with behavior based on state mode.
        
        Args:
            frame: Current frame to draw on
            current_beat: Current beat number (1-based)
            mode: 'setup' | 'countdown' | 'processing'
                - setup: All circles dim red, all numbers visible
                - countdown: All circles, current highlighted bright red, all numbers
                - processing: Current flashes bright red, next semi-transparent
        """
        positions = self._get_circle_positions()
        if not positions:
            return
        
        match mode:
            case 'setup':
                self._draw_setup_mode(frame, positions)
            case 'countdown':
                self._draw_countdown_mode(frame, positions, current_beat)
            case 'processing':
                self._draw_processing_mode(frame, positions, current_beat)
    
    def _draw_setup_mode(self, frame, positions):
        """All circles dim, all numbers visible."""
        for i, pos in enumerate(positions):
            cv2.circle(frame, pos, 25, (0, 0, 150), -1)
        self._draw_all_numbers(frame, positions)
    
    def _draw_countdown_mode(self, frame, positions, current_beat):
        """All circles visible, current beat highlighted."""
        for i, pos in enumerate(positions):
            beat_num = i + 1
            if beat_num == current_beat:
                cv2.circle(frame, pos, 30, (0, 0, 255), -1)
            else:
                cv2.circle(frame, pos, 25, (0, 0, 150), -1)
        self._draw_all_numbers(frame, positions)
    
    def _draw_processing_mode(self, frame, positions, current_beat):
        """Draw current beat solid red (flashes)."""
        # Draw current beat (solid red)
        current_pos = positions[current_beat - 1]
        cv2.circle(frame, current_pos, 30, (0, 0, 255), -1)
        self._draw_single_number(frame, current_pos, current_beat)
    
    def draw_next_beat_preview(self, frame, current_beat):
        """Draw next beat circle (semi-transparent) - stays visible continuously."""
        positions = self._get_circle_positions()
        if not positions:
            return
        
        # Calculate next beat
        next_beat = (current_beat % len(positions)) + 1
        
        # Draw next beat (semi-transparent)
        next_pos = positions[next_beat - 1]
        overlay = frame.copy()
        cv2.circle(overlay, next_pos, 30, (0, 0, 255), -1)
        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
        self._draw_single_number(frame, next_pos, next_beat)
    
    def draw_hit_feedback(self, frame):
        """Display HIT! message when beat circle is hit by hand centroid."""
        if self.beat_manager is None:
            return
        
        hit_status = self.beat_manager.get_current_hit_status()
        if hit_status == "hit":
            frame_height, frame_width = frame.shape[:2]
            text_x = frame_width // 2 - 50
            text_y = frame_height // 2
            cv2.putText(frame, "HIT!", (text_x, text_y), 
                        cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 255, 0), 5)
    
    def _draw_all_numbers(self, frame, positions):
        """Draw numbers on all beat circles."""
        for i, pos in enumerate(positions):
            self._draw_single_number(frame, pos, i + 1)
    
    def _draw_single_number(self, frame, position, beat_num):
        """Draw a single beat number centered on position."""
        text = str(beat_num)
        (text_width, text_height), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
        text_x = position[0] - text_width // 2
        text_y = position[1] + text_height // 2
        cv2.putText(frame, text, (text_x, text_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    def _get_circle_positions(self):
        """Get circle positions from beat manager with validation."""
        if self.beat_manager is None:
            return []
        positions = self.beat_manager.get_circle_positions()
        return positions if positions else []

