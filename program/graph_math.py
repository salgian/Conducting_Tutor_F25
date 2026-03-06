import numpy as np
from matplotlib import pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap
from scipy.signal import find_peaks

# Function to process hand path data
def process_hand_path_data(x_proc, y_proc):
  
    # Filter out NaN values
    valid_mask = ~(np.isnan(x_proc) | np.isnan(y_proc))
    x_valid = x_proc[valid_mask]
    
    # IMPORTANT: We invert the y-coordinates here for visualization
    # This is to match physical conducting space where up is positive,
    # but in image coordinates, up is negative (y increases downward)
    y_valid = -y_proc[valid_mask]
    
    return x_valid, y_valid

# Function to create color gradient segments
def create_color_gradient_segments(x_valid, y_valid):
    points = np.array([x_valid, y_valid]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    colors = ['blue', 'red']
    n_bins = len(x_valid)
    custom_cmap = LinearSegmentedColormap.from_list("custom", colors, N=n_bins)
    return segments, custom_cmap

# Function to normalize data and detect peaks and valleys
def normalize_and_detect_peaks(y):
    y_array = np.array(y)
    
    if len(y_array) == 0:
        return np.array([]), np.array([]), np.array([])
    
    # Handling NaN values
    valid_mask = ~np.isnan(y_array)
    y_valid = y_array[valid_mask]
    
    if len(y_valid) == 0:
        return np.array([]), np.array([]), np.array([])
    
    # Normalize the data to range 0-1
    if np.max(y_valid) != np.min(y_valid):
        y_normalized = (y_valid - np.min(y_valid)) / (np.max(y_valid) - np.min(y_valid))
    else:
        y_normalized = np.zeros_like(y_valid)
    
    # Create a full array with original dimensions for visualization
    y_norm_full = np.full_like(y_array, np.nan)
    y_norm_full[valid_mask] = y_normalized
    
    # Calculate adaptive parameters for peak detection
    # Base prominence on the data variance
    data_range = np.max(y_valid) - np.min(y_valid)
    base_prominence = max(0.02, data_range * 0.005)  # At least 2% of range
    
    # Auto-adjust distance based on data length
    min_distance = max(3, len(y_valid) // 200)  # At least 3 frames apart
    
    # Find valleys (highest points in physical space)
    y_maxima, _ = find_peaks(-y_array, prominence=base_prominence, distance=min_distance)
    
    # Find peaks (lowest points in physical space)
    y_minima, _ = find_peaks(y_array, prominence=base_prominence, distance=min_distance)
    
    # Debug information
    print(f"Peak detection settings: prominence={base_prominence}, distance={min_distance}")
    print(f"Found {len(y_maxima)} maxima (high points) and {len(y_minima)} minima (low points)")
    
    return y_norm_full, y_maxima, y_minima

# Function to estimate time signature from peaks and valleys
def estimate_time_signature(y_maxima, y_minima, y_normalized):
    if len(y_maxima) == 0 or len(y_minima) == 0:
        print("Not enough maxima or minima to determine time signature.")
        return None
    
    # Get heights of maxima (negative values, since these are the highest points)
    maxima_heights = []
    for i in y_maxima:
        if i < len(y_normalized) and not np.isnan(y_normalized[i]):
            maxima_heights.append(-y_normalized[i])
    
    if not maxima_heights or len(maxima_heights) < 2:
        return None
    
    # Adaptive threshold to identify significant maxima (large upward waves)
    # Use statistical analysis to determine threshold
    heights_array = np.array(maxima_heights)
    
    # Using percentile helps with varying maxima heights
    # Higher percentile means we only select the most prominent maxima
    significant_wave_threshold = max(
        np.percentile(heights_array, 75),  # 75th percentile
        np.mean(heights_array) + 0.5 * np.std(heights_array)  # Mean + 0.5 std dev
    )
    
    print(f"Significant wave threshold: {significant_wave_threshold}")
    
    # Identify significant maxima (large upward waves)
    significant_maxima = []
    for i, height in enumerate(maxima_heights):
        if i < len(y_maxima) and height > significant_wave_threshold:
            significant_maxima.append(y_maxima[i])
    
    if not significant_maxima:
        # Try a lower threshold if no significant maxima found
        significant_wave_threshold = np.percentile(heights_array, 60)
        for i, height in enumerate(maxima_heights):
            if i < len(y_maxima) and height > significant_wave_threshold:
                significant_maxima.append(y_maxima[i])
    
    if not significant_maxima:
        print("No significant maxima found to determine time signature.")
        return None
    
    # Sort significant maxima in ascending order
    significant_maxima.sort()
    
    # Find downbeats (minima) that follow each significant maximum
    # Downbeats are when the conductor hits the lowest point after a high point
    downbeat_indices = []
    for peak in significant_maxima:
        # Find minima that come after this maximum
        minima_after_peak = [v for v in y_minima if v > peak]
        if minima_after_peak:
            # Find the closest minimum that follows this maximum (should be the downbeat)
            closest_minimum = min(minima_after_peak, key=lambda v: v - peak)
            # Only consider if it's within a reasonable window
            max_distance = min(30, len(y_normalized) // 20)  # Adaptive window size
            if 0 < closest_minimum - peak < max_distance:
                downbeat_indices.append(closest_minimum)
    
    if len(downbeat_indices) < 2:
        print(f"Not enough downbeats found ({len(downbeat_indices)}) to determine time signature.")
        return None
    
    # Sort the downbeat indices
    downbeat_indices.sort()
    
    # Calculate the number of beats in each measure
    time_signatures = []
    for i in range(1, len(downbeat_indices)):
        start_idx = downbeat_indices[i-1]
        end_idx = downbeat_indices[i]
        
        # Find all minima between consecutive downbeats
        # These represent individual beats in the measure
        intermediate_minima = [v for v in y_minima 
                              if start_idx < v < end_idx]
        
        # The time signature is the total number of beats in the measure
        # which is the number of intermediate minima + 1 (for the downbeat)
        measure_beat_count = len(intermediate_minima) + 1
        
        # Only keep reasonable time signatures (most common are 2, 3, 4, 6)
        if 2 <= measure_beat_count <= 7:
            time_signatures.append(measure_beat_count)
            print(f"Measure from frames {start_idx}-{end_idx}: {measure_beat_count} beats")
    
    if not time_signatures:
        return None
    
    # Find the most common time signature
    from collections import Counter
    counter = Counter(time_signatures)
    most_common = counter.most_common(1)[0]
    most_common_ts = most_common[0]
    count = most_common[1]
    
    # Only return a result if we have enough consistent measures
    if count >= max(2, len(time_signatures) // 3):
        print(f"Detected time signature: {most_common_ts}/4 (found in {count} measures)")
        return most_common_ts
    else:
        print(f"Inconsistent time signatures detected, most common: {most_common_ts}/4 ({count} occurrences)")
        # Still return most common if we have at least 2 measures with that signature
        if count >= 2:
            return most_common_ts
        return None

# Function to identify beat positions in a conducting pattern
def identify_beat_positions(beat_frames, y, time_signature=4):
    if not beat_frames or len(beat_frames) == 0:
        return []
    
    # Get normalized data and detect maxima/minima
    y_normalized, y_maxima, y_minima = normalize_and_detect_peaks(y)
    
    # Try to detect time signature from the data if possible
    detected_ts = estimate_time_signature(y_maxima, y_minima, y_normalized)
    if detected_ts is not None and detected_ts > 0:
        time_signature = detected_ts
        print(f"Using detected time signature: {time_signature}/4")
    else:
        print(f"Using default time signature: {time_signature}/4")
    
    # Calculate maxima heights to identify significant maxima
    maxima_heights = []
    for i in y_maxima:
        if i < len(y_normalized) and not np.isnan(y_normalized[i]):
            maxima_heights.append(-y_normalized[i])
    
    if not maxima_heights:
        print("No valid maxima heights found, using simple sequential assignment")
        return [i % time_signature for i in range(len(beat_frames))]
    
    # Adaptive threshold for significant maxima
    heights_array = np.array(maxima_heights)
    significant_wave_threshold = max(
        np.percentile(heights_array, 70),
        np.mean(heights_array) + 0.5 * np.std(heights_array)
    )
    
    # Find significant maxima (large upward waves before downbeats)
    significant_maxima = []
    for i, height in enumerate(maxima_heights):
        maxima_idx = y_maxima[i] if i < len(y_maxima) else -1
        if maxima_idx >= 0 and height > significant_wave_threshold:
            significant_maxima.append(maxima_idx)
    
    if not significant_maxima:
        print("No significant maxima found, trying lower threshold")
        # Try with lower threshold
        significant_wave_threshold = np.percentile(heights_array, 60)
        for i, height in enumerate(maxima_heights):
            maxima_idx = y_maxima[i] if i < len(y_maxima) else -1
            if maxima_idx >= 0 and height > significant_wave_threshold:
                significant_maxima.append(maxima_idx)
    
    # If still no significant maxima found, fall back to simple assignment
    if not significant_maxima:
        print("No significant maxima found even with lower threshold")
        return [i % time_signature for i in range(len(beat_frames))]
    
    # Sort significant maxima
    significant_maxima.sort()
    
    # Find downbeats - minima following significant maxima
    downbeat_frames = []
    for peak in significant_maxima:
        minima_after_peak = [v for v in y_minima if v > peak]
        if minima_after_peak:
            closest_minimum = min(minima_after_peak, key=lambda v: v - peak)
            max_distance = min(30, len(y_normalized) // 20)
            if 0 < closest_minimum - peak < max_distance:
                downbeat_frames.append(closest_minimum)
    
    if not downbeat_frames:
        print("No downbeat frames identified")
        return [i % time_signature for i in range(len(beat_frames))]
    
    # Match downbeat frames to beat frames
    downbeat_indices = []
    for downbeat in downbeat_frames:
        # Find closest beat frame to this downbeat
        if beat_frames:
            closest_idx = min(range(len(beat_frames)), 
                            key=lambda i: abs(beat_frames[i] - downbeat))
            # Only include if it's reasonably close
            if abs(beat_frames[closest_idx] - downbeat) < 15:
                downbeat_indices.append(closest_idx)
    
    # If we have identified downbeats, use them to determine beat positions
    if downbeat_indices:
        # Sort to ensure proper ordering
        downbeat_indices.sort()
        
        # Initialize positions array
        beat_positions = []
        
        for i in range(len(beat_frames)):
            if i in downbeat_indices:
                # This is a downbeat (first beat)
                beat_positions.append(0)
            elif i < min(downbeat_indices) if downbeat_indices else float('inf'):
                # This is before the first identified downbeat
                # Calculate based on distance to first downbeat
                beats_to_first_downbeat = min(downbeat_indices) - i
                # This handles "pickup" measures (partial measures at start)
                position = time_signature - beats_to_first_downbeat
                # Ensure it's within valid range
                beat_positions.append(position if 0 <= position < time_signature else i % time_signature)
            else:
                # Find the most recent downbeat before this beat
                prev_downbeat = max([d for d in downbeat_indices if d < i], default=-1)
                if prev_downbeat == -1:
                    # Fallback if no previous downbeat found
                    beat_positions.append(i % time_signature)
                else:
                    # Calculate position based on distance from previous downbeat
                    position = (i - prev_downbeat) % time_signature
                    beat_positions.append(position)
        
        return beat_positions
    
    # Fallback to simple sequential assignment if no downbeats identified
    return [i % time_signature for i in range(len(beat_frames))] 