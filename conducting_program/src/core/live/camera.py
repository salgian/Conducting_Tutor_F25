import cv2
import time

class CameraManager:

    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = None
        self.prev_frame_time = 0
        self.new_frame_time = 0
        self.target_fps = 30
        self.target_frame_duration = 1.0 / self.target_fps
        self.next_frame_deadline = 0.0

    def set_camera_index(self, camera_index):
        self.camera_index = camera_index
        self.initialize_camera()
    
    def get_camera_index(self):
        return self.camera_index
    
    def initialize_camera(self):
        """Initialize camera with best available resolution."""
        # Initialize with DirectShow backend for better control
        print("test1")
        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            # Fallback to default backend
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                print("Error: Could not open camera")
                return False
        
        # Try to set high resolution, fall back to default if needed
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        
        # Get actual resolution
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"Camera resolution: {width}x{height}")
        
        return True
    
    def capture_frame(self):
        """Capture a frame from the camera."""
        if self.cap is None:
            return False, None
            
        ret, frame = self.cap.read()
        if not ret:
            return False, None
            
        return True, frame
    
    def get_camera_resolution(self):
        """Get the current camera resolution."""
        if self.cap is None:
            return None, None
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return width, height
    
    def convert_to_rgb(self, frame):
        # Convert BGR frame to RGB (MediaPipe expects RGB)
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    def calculate_fps(self):
        # Calculate current FPS based on frame timing
        self.new_frame_time = time.time()
        time_diff = self.new_frame_time - self.prev_frame_time
        if self.prev_frame_time > 0 and time_diff > 0:
            fps = 1 / time_diff
        else:
            fps = 0
        self.prev_frame_time = self.new_frame_time
        return min(int(fps), self.target_fps)

    def enforce_fps_cap(self):
        """Throttle loop rate to target FPS."""
        now = time.perf_counter()
        if self.next_frame_deadline == 0.0:
            self.next_frame_deadline = now + self.target_frame_duration
            return

        sleep_time = self.next_frame_deadline - now
        if sleep_time > 0:
            time.sleep(sleep_time)

        # Keep fixed cadence; if behind, reset schedule from now.
        self.next_frame_deadline += self.target_frame_duration
        now_after_sleep = time.perf_counter()
        if self.next_frame_deadline < now_after_sleep:
            self.next_frame_deadline = now_after_sleep + self.target_frame_duration
    
    def cleanup(self):
        # Clean up camera resources
        if self.cap is not None:
            self.cap.release()
        cv2.destroyAllWindows()
    