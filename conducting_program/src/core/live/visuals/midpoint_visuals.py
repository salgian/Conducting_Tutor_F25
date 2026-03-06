import cv2

class MidpointVisualizer:
    """Handles midpoint line visualization for sway detection."""
    
    def draw_live_midpoint_line(self, frame, midpoint, frame_width, frame_height):
        """Draw the current live midpoint line (cyan)."""
        midpoint_normalized = int(midpoint * frame_width)
        cv2.line(frame, (midpoint_normalized, 0), (midpoint_normalized, frame_height), (225, 255, 255), 2)
    
    def draw_reference_midpoint_line(self, frame, reference_midpoint, frame_width, frame_height):
        """Draw the reference midpoint line (yellow)."""
        reference_normalized = int(reference_midpoint * frame_width)
        cv2.line(frame, (reference_normalized, 0), (reference_normalized, frame_height), (255, 255, 0), 2)
    
    def draw_sway_threshold_lines(self, frame, reference_midpoint, sway_threshold, frame_width, frame_height):
        """Draw sway threshold boundary lines (red)."""
        positive_threshold = reference_midpoint + sway_threshold
        negative_threshold = reference_midpoint - sway_threshold
        positive_normalized = int(positive_threshold * frame_width)
        negative_normalized = int(negative_threshold * frame_width)
        cv2.line(frame, (positive_normalized, 0), (positive_normalized, frame_height), (0, 0, 255), 2)
        cv2.line(frame, (negative_normalized, 0), (negative_normalized, frame_height), (0, 0, 255), 2)

