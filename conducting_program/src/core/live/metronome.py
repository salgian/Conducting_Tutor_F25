import threading
import time

class MetronomeManager:
    """
    Independent beat manager that handles timing and coordinates with sound/visual components.
    Runs in dedicated thread and coordinates with external sound/visual managers.
    """
    
    def __init__(self):
        # -------------------- Configuration --------------------
        self.bpm = None
        self.time_signature = None
        self.beats_per_measure = None
        
        # -------------------- Beat Timing --------------------
        self.beat_interval = None
        self.is_running = False
        self.bpm_thread = None
        
        # -------------------- Beat Tracking --------------------
        self.current_beat = 0
        self.measure_count = 0
        
        # -------------------- External Components --------------------
        self.sound_manager = None
        self.visual_manager = None
        self.beat_manager = None  # BeatManager for visual coordination
        
    # -------------------- Initialization --------------------
    
    def initialize(self, settings, sound_manager, visual_manager, beat_manager):
        """Initialize the metronome manager with settings and external components."""
        self.bpm = settings.get_beats_per_minute()
        self.time_signature = settings.get_time_signature()
        self.sound_manager = sound_manager
        self.visual_manager = visual_manager
        self.beat_manager = beat_manager
        self.beat_interval = 60 / self.bpm
        self.beats_per_measure = int(self.time_signature.split('/')[0])
        print(f"MetronomeManager initialized: {self.bpm} BPM, {self.time_signature} time signature")
    
    # -------------------- Thread Management --------------------
    
    def start(self):
        """Start the independent beat timing thread."""
        if not self.is_running:
            self.is_running = True
            self.bpm_thread = threading.Thread(target=self._beat_worker, daemon=True)
            self.bpm_thread.start()
            print("MetronomeManager started")
    
    def stop(self):
        """Stop the beat timing thread and wait for it to finish."""
        if not self.is_running:
            return
        self.is_running = False
        if self.bpm_thread and self.bpm_thread.is_alive():
            self.bpm_thread.join(timeout=1.0)
        print("MetronomeManager stopped")

    # -------------------- Beat Processing --------------------
    
    def _beat_worker(self):
        """Main beat timing thread - runs continuously while active."""
        while self.is_running:
            self._trigger_beat(time.time())
            time.sleep(self.beat_interval) # Sleep for exactly one beat interval
        # Thread exits when is_running becomes False

    def _increment_beat(self):
        """Increment the current beat and check if the measure count should be incremented."""
        self.current_beat += 1
        if self.current_beat >= self.beats_per_measure:
            self.current_beat = 0
            self.measure_count += 1
        
    def _trigger_beat(self, beat_time):
        """Trigger beat: spawn daemon threads for sound and coordinate visual display."""
        self._increment_beat()

        # Play sound and show visual for all beats (audio already warmed up during setup)
        # Spawn daemon thread for sound (non-blocking)
        threading.Thread(target=self.sound_manager.play_metronome_sound, daemon=True).start()

        # Trigger visual display via BeatManager (visual timing managed there)
        if self.beat_manager:
            self.beat_manager.trigger_beat_visual(beat_time)
    
    # -------------------- Accessor Methods --------------------
    
    def get_current_beat(self):
        """Get the current beat number (1-based for display)."""
        return self.current_beat + 1
    
    def get_measure_count(self):
        """Get the current measure number."""
        return self.measure_count
    
    def reset_count(self):
        """Reset beat and measure count to start from beginning."""
        self.current_beat = 0
        self.measure_count = 0
        print("Beat and measure count reset")
