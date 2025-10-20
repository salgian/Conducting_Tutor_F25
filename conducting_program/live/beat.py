import threading
import time

class BeatManager:
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
        
        # -------------------- Visual State --------------------
        # Visual state (checked by live_display per frame)
        self.show_visual = False
        self.visual_lock = threading.Lock()
        self.visual_duration = 0.1  # Duration to show visual (in seconds)
        self.visual_start_time = None
        
        # -------------------- External Components --------------------
        self.sound_manager = None
        self.visual_manager = None
        
    # -------------------- Initialization --------------------
    
    def initialize(self, settings, sound_manager, visual_manager):
        """Initialize the beat manager with settings and external components."""
        self.bpm = settings.get_beats_per_minute()
        self.time_signature = settings.get_time_signature()
        self.sound_manager = sound_manager
        self.visual_manager = visual_manager
        self.beat_interval = 60 / self.bpm
        self.beats_per_measure = int(self.time_signature.split('/')[0])
        print(f"BeatManager initialized: {self.bpm} BPM, {self.time_signature} time signature")
    
    # -------------------- Thread Management --------------------
    
    def start(self):
        """Start the independent beat timing thread."""
        if not self.is_running:
            self.is_running = True
            self.bpm_thread = threading.Thread(target=self._beat_worker, daemon=True)
            self.bpm_thread.start()
            print("BeatManager started")
    
    def stop(self):
        """Stop the beat timing thread."""
        self.is_running = False
        if self.bpm_thread:
            self.bpm_thread.join(timeout=0.1)
        print("BeatManager stopped")

    # -------------------- Beat Processing --------------------
    
    def _beat_worker(self):
        """Main beat timing thread - runs continuously while active."""
        while self.is_running:
            self._trigger_beat(time.time())
            time.sleep(self.beat_interval) # Sleep for exactly one beat interval

    def _increment_beat(self):
        """Increment the current beat and check if the measure count should be incremented."""
        self.current_beat += 1
        if self.current_beat >= self.beats_per_measure:
            self.current_beat = 0
            self.measure_count += 1
        
    def _trigger_beat(self, beat_time):
        """Trigger beat: spawn daemon threads for sound and visual."""
        self._increment_beat()

        # Only play sound and show visual after warmup measure (measure 0)
        if self.measure_count >= 1:
            # Spawn daemon thread for sound (non-blocking)
            threading.Thread(target=self.sound_manager.play_metronome_sound, daemon=True).start()

            # Set visual flag with duration (checked by live_display per frame)
            with self.visual_lock:
                self.show_visual = True
                self.visual_start_time = beat_time
                
        elif self.measure_count == 0:
            # Warmup measure: initialize audio system silently
            threading.Thread(target=self._warmup_audio, daemon=True).start()
    
    # -------------------- Visual Management --------------------
    
    def get_show_visual(self):
        """Get the visual state (called by live_display each frame)."""
        with self.visual_lock:
            if self.show_visual and self.visual_start_time is not None:
                # Check if visual duration has expired
                if time.time() - self.visual_start_time > self.visual_duration:
                    self.show_visual = False
                    self.visual_start_time = None
            return self.show_visual
    
    # -------------------- Accessor Methods --------------------
    
    def get_current_beat(self):
        """Get the current beat number."""
        return self.current_beat
    
    def get_measure_count(self):
        """Get the current measure number."""
        return self.measure_count
    
    # -------------------- Audio Management --------------------
    
    def _warmup_audio(self):
        """Warmup the audio system during the warmup measure."""
        # Pre-initialize the audio system by calling the sound manager's warmup
        try:
            self.sound_manager.warmup_audio_system()
            print("Audio system warming up...")
        except Exception as e:
            print(f"Audio warmup failed: {e}")
