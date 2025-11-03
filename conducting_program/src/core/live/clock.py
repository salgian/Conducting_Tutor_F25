import time

class ClockManager:  
    def __init__(self):
        self.program_start_time = None
        self.session_start_time = None
        
    def start_program_clock(self): # Start the main program clock
        self.program_start_time = time.time()
        print(f"Program clock started at: {self.program_start_time}")
        
    def start_session_clock(self): # Start a new session (e.g., when processing begins)
        self.session_start_time = time.time()
        print(f"Session clock started at: {self.session_start_time}")
        
    def get_program_elapsed_time(self) -> float: # Get total elapsed time since program started
        if self.program_start_time is None:
            return 0.0
        return time.time() - self.program_start_time
    
    def get_session_elapsed_time(self) -> float: # Get elapsed time since current session started
        if self.session_start_time is None:
            return 0.0
        return time.time() - self.session_start_time
    
    def get_current_timestamp(self) -> float: # Get current system timestamp
        return time.time()
    
    def format_time(self, seconds: float) -> str: # Format seconds into MM:SS.mmm format
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes:02d}:{remaining_seconds:06.3f}"

