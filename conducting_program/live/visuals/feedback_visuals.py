import cv2

class FeedbackVisualizer:
    """Handles error/warning feedback messages display."""
    
    def draw_feedback_messages(self, frame, feedback_flags):
        """Draw stacked feedback messages centered at top of frame.
        
        Args:
            frame: Current frame to draw on
            feedback_flags: Dict with keys: 'swaying', 'mirroring', 'watch_left_elbow', 'watch_right_elbow'
        """
        frame_width = frame.shape[1]
        center_x = frame_width // 2
        feedback_y_start = 100
        feedback_index = 0
        
        if feedback_flags.get('swaying'):
            self._draw_centered_text(frame, "Swaying", center_x, 
                                      feedback_y_start + (feedback_index * 60), (0, 0, 255))
            feedback_index += 1
        
        if feedback_flags.get('mirroring'):
            self._draw_centered_text(frame, "Mirroring", center_x, 
                                      feedback_y_start + (feedback_index * 60), (255, 255, 255))
            feedback_index += 1
        
        if feedback_flags.get('watch_left_elbow'):
            self._draw_centered_text(frame, "Watch Left Elbow", center_x, 
                                      feedback_y_start + (feedback_index * 60), (255, 255, 255))
            feedback_index += 1
        
        if feedback_flags.get('watch_right_elbow'):
            self._draw_centered_text(frame, "Watch Right Elbow", center_x, 
                                      feedback_y_start + (feedback_index * 60), (255, 255, 255))
    
    def _draw_centered_text(self, frame, text, center_x, y_pos, color, font_scale=1.5):
        """Helper: Draw text centered horizontally at given y position."""
        (text_width, _), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 3)
        cv2.putText(frame, text, (center_x - text_width // 2, y_pos), 
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 3)

