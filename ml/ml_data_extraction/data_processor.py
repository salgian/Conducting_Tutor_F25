"""
data_processor.py
-----------------
Processes per-frame wrist coordinate data for the conducting trainer.

Contains:
  - Normalizer: Shared bounding-box normalisation + velocity/accel math.
                Used by both data collection AND inference.
  - DataProcessor: Wraps Normalizer with CSV buffering + commit logic.
"""

import csv
import os


# ── Normalizer (shared between data collection and inference) ────────────────

class Normalizer:
    """
    Bounding-box normalization + velocity/acceleration computation.

    Pipeline per frame:
        1. Track the bounding box of the conductor's motion.
        2. Normalise X and Y coordinates to [0, 1] within that bounding box.
        3. Derive normalised velocity and acceleration.
    """

    def __init__(self):
        self.min_x =  float('inf')
        self.max_x = -float('inf')
        self.min_y =  float('inf')
        self.max_y = -float('inf')

        self.last_x  = None
        self.last_y  = None
        self.last_vx = 0.0
        self.last_vy = 0.0

    def _update_bounds(self, x, y):
        """Expand the bounding box to include this frame's coordinate."""
        self.min_x = min(self.min_x, x)
        self.max_x = max(self.max_x, x)
        self.min_y = min(self.min_y, y)
        self.max_y = max(self.max_y, y)

    def _normalize(self, val, min_v, max_v):
        """Map val into [0, 1] relative to [min_v, max_v]. Returns 0.5 if range is zero."""
        if max_v == min_v:
            return 0.5
        return (val - min_v) / (max_v - min_v)

    def _normalize_coords(self, x, y):
        """Return (x_norm, y_norm) within the current bounding box."""
        return (
            self._normalize(x, self.min_x, self.max_x),
            self._normalize(y, self.min_y, self.max_y),
        )

    def _compute_velocity(self, x_norm, y_norm):
        """
        Compute normalised velocity as position delta from the previous frame.
        Returns (vx, vy) = (0, 0) on the very first frame.
        """
        if self.last_x is None:
            return 0.0, 0.0
        last_x_norm, last_y_norm = self._normalize_coords(self.last_x, self.last_y)
        return x_norm - last_x_norm, y_norm - last_y_norm

    def _compute_acceleration(self, vx, vy):
        """Compute normalised acceleration as velocity delta from the previous frame."""
        return vx - self.last_vx, vy - self.last_vy

    def process(self, x, y):
        """
        Compute a 6-element feature vector from raw wrist coordinates.

        Returns:
            dict with keys: x_norm, y_norm, vx_norm, vy_norm, ax_norm, ay_norm
            or None if coordinates are unavailable.
        """
        if x is None or y is None:
            return None

        self._update_bounds(x, y)
        x_norm, y_norm = self._normalize_coords(x, y)
        vx_norm, vy_norm = self._compute_velocity(x_norm, y_norm)
        ax_norm, ay_norm = self._compute_acceleration(vx_norm, vy_norm)

        # Advance physics state
        self.last_x, self.last_y = x, y
        self.last_vx, self.last_vy = vx_norm, vy_norm

        return {
            "x_norm": x_norm, "y_norm": y_norm,
            "vx_norm": vx_norm, "vy_norm": vy_norm,
            "ax_norm": ax_norm, "ay_norm": ay_norm,
        }

    def process_as_list(self, x, y):
        """
        Same as process() but returns a flat list [x, y, vx, vy, ax, ay].
        Convenient for feeding directly into the model.
        """
        result = self.process(x, y)
        if result is None:
            return None
        return [
            result["x_norm"], result["y_norm"],
            result["vx_norm"], result["vy_norm"],
            result["ax_norm"], result["ay_norm"],
        ]


# ── DataProcessor (CSV buffering on top of Normalizer) ──────────────────────

class DataProcessor:
    """
    Wraps Normalizer with CSV row buffering and file commit logic.
    Used only by the data collection pipeline.
    """

    HEADERS = [
        "frame", "time_sig",
        "x_norm", "y_norm",
        "vx_norm", "vy_norm",
        "ax_norm", "ay_norm",
        "beat"
    ]

    def __init__(self, output_file="data.csv", time_signature=None):
        self.output_file    = output_file
        self.time_signature = time_signature
        self.normalizer     = Normalizer()
        self.buffer         = []

    def process_frame(self, frame_count, x, y, is_beat=0):
        """
        Process one frame of wrist data and add it to the in-memory buffer.

        Args:
            frame_count: Integer frame index.
            x, y:        Raw wrist coordinates from MediaPipe (in [0, 1]).
            is_beat:     1 if the user pressed SPACE this frame, else 0.

        Returns:
            Dict of computed values, or None if coordinates are unavailable.
        """
        result = self.normalizer.process(x, y)
        if result is None:
            return None

        # Buffer row
        self.buffer.append([
            frame_count, self.time_signature,
            result["x_norm"], result["y_norm"],
            result["vx_norm"], result["vy_norm"],
            result["ax_norm"], result["ay_norm"],
            is_beat
        ])

        result["is_beat"] = is_beat
        return result

    def commit(self):
        """
        Finalise the buffer and write it to disk.
        Creates the CSV with a header row if the file does not yet exist.
        Returns the number of frames written.
        """
        file_exists = os.path.isfile(self.output_file)
        with open(self.output_file, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(self.HEADERS)
            writer.writerows(self.buffer)

        count = len(self.buffer)
        self.buffer.clear()
        return count
