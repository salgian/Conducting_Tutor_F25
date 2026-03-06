from imports import * 

class patternDetection:
    def __init__(self):
        self.pattern_list = []

    def pattern_list_output(self):
        return self.pattern_list

    def pattern_detection(self, beat_coordinates):
        # Need at least 2 beats to detect movement
        if len(beat_coordinates) < 2:
            return
                
        threshold = 0.005

        # For each pair of consecutive beats
        for i in range(1, len(beat_coordinates)):
            current_x, current_y = beat_coordinates[i]
            previous_x, previous_y = beat_coordinates[i-1]
            
            # Calculate differences
            x_diff = current_x - previous_x
            y_diff = current_y - previous_y

            # Check for diagonal movement first
            if abs(x_diff) > threshold and abs(y_diff) > threshold:
                if x_diff > 0 and y_diff > 0:
                    self.pattern_list.append("down-right")
                elif x_diff > 0 and y_diff < 0:
                    self.pattern_list.append("up-right")
                elif x_diff < 0 and y_diff > 0:
                    self.pattern_list.append("down-left")
                elif x_diff < 0 and y_diff < 0:
                    self.pattern_list.append("up-left")
            # If not diagonal, check for single direction movement
            elif abs(x_diff) > abs(y_diff):
                if x_diff > threshold:
                    self.pattern_list.append("right")
                elif x_diff < -threshold:
                    self.pattern_list.append("left")
            else:
                if y_diff < -threshold:
                    self.pattern_list.append("up")
                elif y_diff > threshold:
                    self.pattern_list.append("down")
                
        return self.pattern_list