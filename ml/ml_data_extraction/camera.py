import cv2


class CameraManager:
    """
    Manages video capture from either a webcam or a video file.

    Usage:
        cam = CameraManager()
        cam.initialize_camera()                        # webcam
        cam.initialize_camera("path/to/video.mp4")    # video file
    """

    DEFAULT_WIDTH  = 1280
    DEFAULT_HEIGHT = 720

    def __init__(self, camera_index="C:\\Users\\Jeffrey Ernest\\Desktop\\ml_videos\\Marchingband(2).mp4"):
        self.camera_index = camera_index
        self.cap = None

    # ── Initialisation ──────────────────────────────

    def initialize_camera(self, video_path=None):
        """
        Open a video source.
        - If video_path is given, open that file.
        - Otherwise, open the webcam (tries DirectShow first on Windows).
        Returns True on success, False on failure.
        """
        if video_path:
            return self._open_file(video_path)
        return self._open_webcam()

    def _open_file(self, path):
        """Open a video file for reading."""
        self.cap = cv2.VideoCapture(path)
        if not self.cap.isOpened():
            print(f"Error: Could not open video file '{path}'")
            return False
        return True

    def _open_webcam(self):
        """Open the default webcam, falling back to a plain index if DirectShow fails."""
        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            print("Error: Could not open webcam.")
            return False

        self._set_resolution(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)
        return True

    def _set_resolution(self, width, height):
        """Set the capture resolution (webcam only)."""
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    # ── Frame access ────────────────────────────────

    def capture_frame(self):
        """Read one frame. Returns (success, frame)."""
        if self.cap is None:
            return False, None
        return self.cap.read()

    def convert_to_rgb(self, frame):
        """Convert a BGR frame to RGB (required by MediaPipe)."""
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # ── Cleanup ─────────────────────────────────────

    def cleanup(self):
        """Release the video capture resource."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None