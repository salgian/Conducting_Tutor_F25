import cv2

class StateVisualizer:
    """Handles state-specific text overlays and labels."""
    
    def draw_setup_label(self, frame):
        """Draw 'SETUP' state label and instruction text in bottom-left."""
        frame_height = frame.shape[0]
        cv2.putText(frame, "SETUP", (10, frame_height - 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, "Bring band to attention", (10, frame_height - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    def draw_countdown_label(self, frame):
        """Draw 'COUNTDOWN' state label in bottom-left."""
        frame_height = frame.shape[0]
        cv2.putText(frame, "COUNTDOWN", (10, frame_height - 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
    
    def draw_processing_label(self, frame):
        """Draw 'PROCESSING' state label in bottom-left."""
        frame_height = frame.shape[0]
        cv2.putText(frame, "PROCESSING", (10, frame_height - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    
    def draw_ending_label(self, frame):
        """Draw 'ENDING' state label in bottom-left."""
        frame_height = frame.shape[0]
        cv2.putText(frame, "ENDING", (10, frame_height - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    
    def draw_session_complete_message(self, frame, hit_percentage=None):
        """Draw centered 'Session Complete' message with optional hit rate."""
        frame_width, frame_height = frame.shape[1], frame.shape[0]
        center_x, center_y = frame_width // 2, frame_height // 2
        
        text = "Session Complete"
        (text_width, _), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)
        cv2.putText(frame, text, (center_x - text_width // 2, center_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        if hit_percentage is not None:
            text2 = f"Hit Rate: {hit_percentage:.1f}%"
            (text_width2, _), _ = cv2.getTextSize(text2, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)
            cv2.putText(frame, text2, (center_x - text_width2 // 2, center_y + 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

