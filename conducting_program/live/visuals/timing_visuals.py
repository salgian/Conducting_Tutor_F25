import cv2

class TimingVisualizer:
    """Handles FPS, timing information, and beat/measure counter display."""
    
    def draw_fps_and_timers(self, frame, fps, program_time_str, session_time_str):
        """Draw FPS, program time, and session time in top-left corner."""
        cv2.putText(frame, f'FPS: {fps}', (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f'Program: {program_time_str}', (10, 70), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        cv2.putText(frame, f'Session: {session_time_str}', (10, 110), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    
    def draw_beat_and_measure_info(self, frame, current_beat, measure_count):
        """Draw current beat and measure numbers below timing info."""
        cv2.putText(frame, f'Beat: {current_beat}', (10, 150), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        cv2.putText(frame, f'Measure: {measure_count}', (10, 190), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

