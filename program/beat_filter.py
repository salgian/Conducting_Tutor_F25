import numpy as np
from scipy.signal import find_peaks

# filters points based on minimum distance threshold
def filter_significant_points(points, threshold):
    if len(points) == 0:
        return []
        
    filtered_points = [points[0]]
    for i in range(1, len(points)):
        if points[i] - filtered_points[-1] > threshold:
            filtered_points.append(points[i])
            
    return filtered_points

# analyzes movement data to detect conducting beats
def filter_beats(frame_array, processed_frame_array):
    print("\n=== Beat Filter Debug Information ===")
    print(f"Input frame array length: {len(frame_array)}")
    print(f"Processed frame array length: {len(processed_frame_array)}")

    # extract x and y coordinates from frame arrays
    x = [coord[0] for coord in frame_array]
    y = [coord[1] for coord in frame_array]
    
    # convert to numpy arrays for processing
    x = np.array(x).flatten()
    y = np.array(y).flatten()
    
    # Print min and max y values to understand the data range
    if len(y) > 0:
        print(f"Y-coordinate range: min={min(y)}, max={max(y)}")

    # Add debug points to explain the coordinate system
    print("\n=== Coordinate System Explanation ===")
    print("In the coordinate space, y increases DOWNWARD in the image (standard computer vision)")
    print("In physical conducting space, higher hand positions have LOWER y values")
    print("Therefore:")
    print("  - Peaks in y (higher y values) = LOWER physical positions")
    print("  - Valleys in y (lower y values) = HIGHER physical positions")
    print("=============================================")

    # find peaks (maxima) and valleys (minima) in raw coordinates
    # Note: y_peaks are the MINIMA of the conducting gesture (lowest points)
    # Prominence and distance parameters control how peaks are detected
    y_peaks, _ = find_peaks(y, prominence=0.005, distance = 5)
    y_valleys, _ = find_peaks(-y, prominence=0.005, distance = 5)
    
    # Print the actual y-values at peaks and valleys for comparison
    if len(y_peaks) > 0 and len(y_valleys) > 0:
        print("\nValues at peaks (MINIMA) and valleys (MAXIMA):")
        for i in range(min(3, len(y_peaks))):
            print(f"  Peak {i+1}: frame={y_peaks[i]}, y-value={y[y_peaks[i]]} (LOWER physical position)")
        for i in range(min(3, len(y_valleys))):
            print(f"  Valley {i+1}: frame={y_valleys[i]}, y-value={y[y_valleys[i]]} (HIGHER physical position)")

    # process user-selected coordinates
    #x_proc = np.array([coord[0] for coord in processed_frame_array]).flatten()
    y_proc = np.array([coord[1] for coord in processed_frame_array]).flatten()

    # find peaks and valleys in processed coordinates
    y_peaks_proc, _ = find_peaks(y_proc, prominence=0.005)
    y_valleys_proc, _ = find_peaks(-y_proc, prominence=0.005)

    # convert peak/valley indices to lists
    y_peaks_proc = list(y_peaks_proc)
    y_valleys_proc = list(y_valleys_proc)

    # We use y_peaks (which are LOWER physically) for beat detection 
    # This means we're detecting the LOWEST points of conducting gestures as beats (peaks of y)
    
    # Use y_peaks (MAXIMA) for beat detection - these are the lowest points of conducting gestures
    filtered_significant_beats = list(y_peaks)
    
    # Get the x,y coordinates for each beat at the MAXIMA (peaks)
    beat_coordinates = [(x[i], y[i]) for i in filtered_significant_beats]

    # Print peak and valley y-values for verification
    if len(y_peaks) > 0 and len(y_valleys) > 0:
        print(f"\nSample peak y-value (min): {y[y_peaks[0]]} (LOWER physical position)")
        print(f"Sample valley y-value (max): {y[y_valleys[0]]} (HIGHER physical position)")
        print(f"UPDATED IMPLEMENTATION: Using PEAKS (maxima) for beat coordinates = LOWER physical positions")
        
        # Print a few sample beat coordinates for inspection
        if len(beat_coordinates) > 0:
            print(f"\nSample beat coordinates (using PEAKS = LOWER physical positions):")
            for i in range(min(3, len(beat_coordinates))):
                print(f"  Beat {i+1}: x={beat_coordinates[i][0]:.2f}, y={beat_coordinates[i][1]:.2f}")
                
        # Visual representation of peaks vs valleys
        print("\nVisual comparison - Values at peaks vs valleys:")
        peak_markers = ['P' if i in y_peaks else ' ' for i in range(min(80, len(y)))]
        valley_markers = ['V' if i in y_valleys else ' ' for i in range(min(80, len(y)))]
        print(''.join(peak_markers))
        print(''.join(valley_markers))

    # Before return, add debug info
    print(f"Number of y peaks: {len(y_peaks)}")
    print(f"Number of y valleys: {len(y_valleys)}")
    print(f"Number of filtered beats: {len(filtered_significant_beats)}")
    print("==================================\n")

    # Create y_inverted (this is used by some functions)
    y_inverted = y

    # Return values exactly matching the expected signature in main.py (7 values)
    return filtered_significant_beats, beat_coordinates, y_peaks, y_valleys, y_inverted, y, x