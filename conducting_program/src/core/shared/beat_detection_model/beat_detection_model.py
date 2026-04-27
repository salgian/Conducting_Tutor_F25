import os
import sys
import collections
import tensorflow as tf
from tensorflow import keras
from .normalizer import Normalizer

def _resolve_model_path():
    """Resolve model path for both source runs and PyInstaller bundles."""
    source_path = os.path.join(os.path.dirname(__file__), "beat_detector_xy.keras")
    if os.path.exists(source_path):
        return source_path

    bundle_base = getattr(sys, "_MEIPASS", None)
    if bundle_base:
        bundled_path = os.path.join(
            bundle_base,
            "src",
            "core",
            "shared",
            "beat_detection_model",
            "beat_detector_xy.keras",
        )
        if os.path.exists(bundled_path):
            return bundled_path

    return source_path


DEFAULT_MODEL_PATH = _resolve_model_path()

@tf.function(reduce_retracing=True)
def _predict_tf(model, X):
    """Compiled TF graph for single-batch model inference."""
    return model(X, training=False)

class BeatDetectionModel:
    """
    LSTM beat detector for real-time conducting analysis.
    
    Feed it raw MediaPipe wrist (x, y) each frame.
    Internally normalizes via bounding-box, maintains sliding window,
    and runs model inference.
    """
    
    def __init__(self, model_path=None, seq_len=11, threshold=0.80, min_beat_gap=10):
        # Allow overriding the path, otherwise use the co-located model file
        actual_path = model_path if model_path else DEFAULT_MODEL_PATH
        if not os.path.exists(actual_path):
            raise FileNotFoundError(
                f"Beat detection model file not found at: {actual_path}. "
                "Copy beat_detector_xy.keras into src/core/shared/beat_detection_model/."
            )
        print(f"Loading BeatDetectionModel from {actual_path}")
        self.model = keras.models.load_model(actual_path)
        
        self.seq_len = seq_len
        self.threshold = threshold
        self.min_beat_gap = min_beat_gap
        
        # State tracking
        self.normalizer = Normalizer()
        self.window = collections.deque(maxlen=seq_len)
        self.frames_since_last_beat = 999  # Start past the gap so we're ready immediately
        self.frame_count = 0

    def feed_frame(self, x: float, y: float) -> bool:
        """
        Feed one frame's RAW wrist coordinates (MediaPipe 0-1 range).
        Internally applies bounding-box normalization before model inference.
        Returns True if a beat was detected this frame.
        """
        # 1. Normalize via bounding box (replicates training pipeline)
        result = self.normalizer.process(x, y)
        if result is None:
            return False
            
        # 2. Append [x_norm, y_norm] to sliding window
        self.window.append([result['x_norm'], result['y_norm']])
        self.frames_since_last_beat += 1
        self.frame_count += 1
        
        # 3. Run inference when window is full + cooldown satisfied
        if len(self.window) == self.seq_len and self.frames_since_last_beat >= self.min_beat_gap:
            X_input = tf.constant([list(self.window)], dtype=tf.float32)
            prob = float(_predict_tf(self.model, X_input)[0, 0])
            
            if prob >= self.threshold:
                self.frames_since_last_beat = 0
                return True
                
        return False

    def reset(self):
        """Reset state for a new session (e.g. entering PROCESSING state)."""
        self.normalizer = Normalizer()
        self.window.clear()
        self.frames_since_last_beat = 999
        self.frame_count = 0
