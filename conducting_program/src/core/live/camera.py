import cv2
import time

class CameraManager:

    def __init__(self, camera_index=0):
        self.camera_index = "C:/Users/Jeffrey Ernest/Desktop/old cs stuff/videos/Marchingband(2).mp4"
        self.cap = None
        self.prev_frame_time = 0
        self.new_frame_time = 0
        
    def initialize_camera(self):
        """Initialize camera with best available resolution."""
        # Initialize with DirectShow backend for better control
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
        return int(fps)
    
    def cleanup(self):
        # Clean up camera resources
        if self.cap is not None:
            self.cap.release()
        cv2.destroyAllWindows()
    