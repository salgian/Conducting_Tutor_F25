# This file will house the settings for the live detection program, such as:
# Do we want visuals, to ender the feedback
# save the video, etc...
# As well as constants that are set by the user.

# Settings for live conducting program
class Settings:
    def __init__(self):
        self.beats_per_minute = 60  # Default BPM
        self.time_signature = "4/4"  # Default time signature

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
