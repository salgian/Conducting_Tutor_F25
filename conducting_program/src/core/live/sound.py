import os
import threading
import time
from pydub import AudioSegment
from pydub.playback import play

class SoundManager:
    """
    Manages sound playback for the conducting tutor.
    Note: Beat timing is now handled centrally in system_state.py
    """
    
    def __init__(self):
        """Initialize the sound manager."""
        self.metronome_sound = None
        self.warmup_running = False
        self.warmup_thread = None
        self.audio_lock = threading.Lock()  # Prevent simultaneous audio playback
        self.load_metronome_sound()
    
    def load_metronome_sound(self):
        """Load the metronome sound file (WAV format)."""
        # Get path relative to this file: go up 3 levels to project root, then to assets/sounds
        sound_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "assets", "sounds", "metro_sound.wav"))
        
        # Load WAV file directly
        if os.path.exists(sound_file_path):
            self.metronome_sound = AudioSegment.from_wav(sound_file_path)
        else:
            print(f"Metronome sound not found: {sound_file_path}")
            print("Continuing without metronome sound...")
            self.metronome_sound = None

    def play_metronome_sound(self):
        """Play a single metronome beat (non-blocking)."""
        if self.metronome_sound is not None:
            threading.Thread(target=self._play_sound_non_blocking, args=(self.metronome_sound,), daemon=True).start()
        else:
            print("Metronome sound not loaded, cannot play.")
    
    def _play_sound_non_blocking(self, sound):
        """Helper to play sound in a separate thread with lock to prevent conflicts."""
        if sound:
            with self.audio_lock:
                play(sound)
    
    def warmup_audio_system(self):
        """Pre-initialize the audio system to prevent first-play delays."""
        # Only warmup if sound is available
        if self.metronome_sound is None:
            return
        # Create a very short silent audio segment to initialize pydub's audio system
        silent_sound = AudioSegment.silent(duration=1)  # 1ms silent audio
        # This initializes the audio system without making any sound
        with self.audio_lock:
            play(silent_sound)
    
    def start_continuous_warmup(self):
        """Start continuously warming up the audio system in the background."""
        if not self.warmup_running:
            self.warmup_running = True
            self.warmup_thread = threading.Thread(target=self._warmup_worker, daemon=True)
            self.warmup_thread.start()
            print("Continuous audio warmup started")
    
    def stop_continuous_warmup(self):
        """Stop the continuous warmup thread and wait for it to finish."""
        self.warmup_running = False
        if self.warmup_thread and self.warmup_thread.is_alive():
            self.warmup_thread.join(timeout=1.0)
        print("Continuous audio warmup stopped")
    
    def _warmup_worker(self):
        """Background worker that continuously warms up the audio system."""
        while self.warmup_running:
            if self.warmup_running and self.metronome_sound is not None:
                self.warmup_audio_system()
            time.sleep(1.0)  # Warmup every 1 second (reduced frequency to minimize contention)

