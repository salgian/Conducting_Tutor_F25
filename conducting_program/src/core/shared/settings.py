# This file will house the settings for the live detection program, such as:
# Do we want visuals, to ender the feedback
# save the video, etc...
# As well as constants that are set by the user.

# Settings for live conducting program
class Settings:
    _instance = None
    
    def __new__(cls):
        """Singleton pattern - ensure only one Settings instance exists."""
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.beats_per_minute = 60  # Default BPM
        self.time_signature = "4/4"  # Default time signature
        self.camera_path = 0  # Default camera index
        self.feature_toggles = {
            "metronome_enabled": True,
            "markers_enabled": True,
            "conducting_hand_marker_enabled": True,
        }

    def set_time_signature(self, time_sig: str):
        match time_sig:
            case "4/4":
                self.time_signature = "4/4"
            case "3/4":
                self.time_signature = "3/4"
            case "4/custom/4":
                self.time_signature = "4/custom/4"
            case _:
                print("Invalid time signature")
    
    def set_beats_per_minute(self, bpm):
        self.beats_per_minute = int(bpm)
    
    def get_beats_per_minute(self):
        return self.beats_per_minute
            
    def get_time_signature(self):
        return self.time_signature
    
    def set_camera_path(self, path):
        """Set camera path (index for default camera, or path string for video file)."""
        self.camera_path = path
    
    def get_camera_path(self):
        """Get camera path."""
        return self.camera_path

    def set_feature_toggle(self, toggle_name: str, enabled: bool):
        """Set a feature toggle by name."""
        if toggle_name in self.feature_toggles:
            self.feature_toggles[toggle_name] = bool(enabled)

    def get_feature_toggle(self, toggle_name: str) -> bool:
        """Get a feature toggle by name."""
        return bool(self.feature_toggles.get(toggle_name, False))

    def set_metronome_enabled(self, enabled: bool):
        self.set_feature_toggle("metronome_enabled", enabled)

    def get_metronome_enabled(self) -> bool:
        return self.get_feature_toggle("metronome_enabled")

    def set_markers_enabled(self, enabled: bool):
        self.set_feature_toggle("markers_enabled", enabled)

    def get_markers_enabled(self) -> bool:
        return self.get_feature_toggle("markers_enabled")

    def set_conducting_hand_marker_enabled(self, enabled: bool):
        self.set_feature_toggle("conducting_hand_marker_enabled", enabled)

    def get_conducting_hand_marker_enabled(self) -> bool:
        return self.get_feature_toggle("conducting_hand_marker_enabled")

