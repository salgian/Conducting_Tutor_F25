import cv2
import time

class BPMVisualizer:
    """Displays BPM info as a temporary overlay in the top-right corner."""
    
    def __init__(self, display_duration=1.0):
        self.display_duration = display_duration
        self.current_bpm = None
        self.beat_count = 0
        self.display_start_time = None
    
    def trigger_display(self, bpm: float, beat_count: int, current_time: float):
        """Show BPM overlay for display_duration seconds."""
        self.current_bpm = bpm
        self.beat_count = beat_count
        self.display_start_time = current_time
    
    def draw_bpm_overlay(self, frame, current_time: float):
        """Draw the BPM text in top-right if within display window."""
        if self.display_start_time is None:
            return
            
        if current_time - self.display_start_time > self.display_duration:
            # Display period is over
            self.display_start_time = None
            return
            
        if self.current_bpm is None:
            return
            
        # Draw top-right overlay
        frame_width = frame.shape[1]
        padding = 40
        y_pos = 60
        
        # Format text
        text = f"{self.current_bpm:.1f} BPM"
        subtext = f"({self.beat_count} beats)"
        
        # Calculate text sizes for right-alignment
        font_scale_main = 1.0
        font_scale_sub = 0.6
        font_thickness = 2
        
        (main_w, main_h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale_main, font_thickness)
        (sub_w, sub_h), _ = cv2.getTextSize(subtext, cv2.FONT_HERSHEY_SIMPLEX, font_scale_sub, 1)
        
        # Draw background box for readability
        box_width = max(main_w, sub_w) + 40
        box_height = main_h + sub_h + 30
        x_start = frame_width - padding - box_width
        y_start = y_pos - main_h - 10
        
        # Semi-transparent black background
        overlay = frame.copy()
        cv2.rectangle(overlay, (x_start, y_start), (x_start + box_width, y_start + box_height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        # Draw text
        # Primary BPM text (Yellow)
        text_x = frame_width - padding - main_w - 20
        cv2.putText(frame, text, (text_x, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 
                    font_scale_main, (0, 255, 255), font_thickness)
                    
        # Secondary info (White)
        subtext_x = frame_width - padding - sub_w - 20
        cv2.putText(frame, subtext, (subtext_x, y_pos + sub_h + 10), cv2.FONT_HERSHEY_SIMPLEX, 
                    font_scale_sub, (255, 255, 255), 1)
