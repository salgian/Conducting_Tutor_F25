class BPMTracker:
    """Tracks beat timestamps and computes rolling BPM averages."""
    
    def __init__(self, report_interval_seconds=5.0):
        self.beat_timestamps = []
        self.report_interval = report_interval_seconds
        self.last_report_time = None
        self.beat_count = 0
    
    def record_beat(self, timestamp: float):
        """Record a beat occurrence timestamp."""
        self.beat_timestamps.append(timestamp)
        self.beat_count += 1
    
    def get_average_bpm(self, window_seconds: float = None) -> float:
        """
        Compute average BPM. 
        If window_seconds is provided, averages over that recent window.
        Otherwise averages over all recorded beats.
        Returns None if fewer than 2 beats recorded.
        """
        if len(self.beat_timestamps) < 2:
            return None
            
        timestamps = self.beat_timestamps
        if window_seconds is not None:
            cutoff = timestamps[-1] - window_seconds
            timestamps = [t for t in timestamps if t >= cutoff]
            if len(timestamps) < 2:
                return None
                
        # Time difference between last and first beat in the window
        duration = timestamps[-1] - timestamps[0]
        if duration <= 0:
            return None
            
        # Number of intervals is n-1
        intervals = len(timestamps) - 1
        beats_per_second = intervals / duration
        return beats_per_second * 60.0
    
    def should_report(self, current_time: float) -> bool:
        """True if report_interval has elapsed since last report."""
        if self.last_report_time is None:
            return True
        return (current_time - self.last_report_time) >= self.report_interval
    
    def mark_reported(self, current_time: float):
        """Update last report time."""
        self.last_report_time = current_time
    
    def reset(self):
        """Clear all data for a new session."""
        self.beat_timestamps = []
        self.last_report_time = None
        self.beat_count = 0
