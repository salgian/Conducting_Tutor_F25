import cv2


class CameraManager:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = None
        
    def initialize_camera(self):
        """Initialize camera with standard resolution."""
        # Try DirectShow first for Windows performance
        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                print("Error: Could not open camera")
                return False
        
        # Set a reasonable resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        return True
    
    def capture_frame(self):
        """Capture a frame from the camera."""
        if self.cap is None:
            return False, None
        return self.cap.read()
    
    def convert_to_rgb(self, frame):
        # MediaPipe expects RGB
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    def cleanup(self):
        if self.cap is not None:
            self.cap.release()

    