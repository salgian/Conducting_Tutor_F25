import os
import threading
from pydub import AudioSegment
from pydub.playback import play

# Simple sound file paths
SOUNDS_PATH = "assets/sounds/"

class SoundManager:
    """
    Manages sound playback for the conducting tutor.
    Note: Beat timing is now handled centrally in system_state.py
    """
    
    def __init__(self):
        """Initialize the sound manager."""
        self.metronome_sound = None
        self.load_metronome_sound()
    
    def load_metronome_sound(self):
        """Load the metronome sound file."""
        sound_file_path = os.path.abspath(os.path.join(SOUNDS_PATH, "metro_sound.mp3"))
        if os.path.exists(sound_file_path):
            self.metronome_sound = AudioSegment.from_mp3(sound_file_path)
        else:
            print(f"Metronome sound not found: {sound_file_path}")
            self.metronome_sound = None

    def play_metronome_sound(self):
        """Play a single metronome beat (non-blocking)."""
        if self.metronome_sound is not None:
            threading.Thread(target=self._play_sound_non_blocking, args=(self.metronome_sound,)).start()
        else:
            print("Metronome sound not loaded, cannot play.")
    
    def _play_sound_non_blocking(self, sound):
        """Helper to play sound in a separate thread."""
        if sound:
            play(sound)
    
    def warmup_audio_system(self):
        """Pre-initialize the audio system to prevent first-play delays."""
        try:
            # Create a very short silent audio segment to initialize pydub's audio system
            silent_sound = AudioSegment.silent(duration=1)  # 1ms silent audio
            # This initializes the audio system without making any sound
            play(silent_sound)
        except Exception as e:
            print(f"Audio system warmup failed: {e}")

