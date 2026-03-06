from graph_config import get_export_path, get_video_name, video_beat_plot_name, video_conduct_path_name, video_cluster_plot_name, video_overtime_plot_name, video_sway_plot_Name, video_hands_plot_x_name, video_hands_plot_y_name, video_out_name, video_time_signature_plot_name
from graph_math import process_hand_path_data, create_color_gradient_segments, normalize_and_detect_peaks, estimate_time_signature, identify_beat_positions
import os
import json
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection

# Get export path from configuration

def get_export_path():
    try:
        with open("interface_config.json", "r") as f:
            config = json.load(f)
            export_path = config.get("export_path", "output")
            # Ensure directory exists
            os.makedirs(export_path, exist_ok=True)
            return export_path
    except:
        # Fallback to default
        default_path = "output"
        os.makedirs(default_path, exist_ok=True)
        return default_path

# Helper function to get video name from configuration

def get_video_name():
    try:
        with open("interface_config.json", "r") as f:
            config = json.load(f)
            video_path = config.get("video_path", "unknown_video")
            return os.path.basename(video_path).split('.')[0]
    except:
        return "unknown_video"

# Video name generation functions

def video_beat_plot_name():
    return f"{get_video_name()}_beat_plot"

def video_conduct_path_name():
    return f"{get_video_name()}_conduct_path"

def video_cluster_plot_name():
    return f"{get_video_name()}_cluster_plot"

def video_overtime_plot_name():
    return f"{get_video_name()}_overtime_plot"

def video_sway_plot_Name():
    return f"{get_video_name()}_sway_plot"

def video_hands_plot_x_name():
    return f"{get_video_name()}_hands_x_plot"

def video_hands_plot_y_name():
    return f"{get_video_name()}_hands_y_plot"

def video_out_name():
    return f"{get_video_name()}_analyzed"

def video_time_signature_plot_name():
    return f"{get_video_name()}_time_signature_plot"

# generates all analysis graphs from the collected data
# Add this updated function to graphs.py

def generate_all_graphs(cycle_one, graph_options=None, segment_info=None):
    
    # Default all options to True if none provided
    if graph_options is None:
        graph_options = {
            "generate_beat_plot": True,
            "generate_hand_path": True,
            "generate_beat_cluster_graph": True,
            "generate_maxima_cluster_graph": True,
            "generate_time_signature_plot": True,
            "generate_swaying_graph": True,
            "generate_mirror_x_graph": True,
            "generate_mirror_y_graph": True
        }
    
    # Create segment suffix for filenames if segment_info is provided
    segment_suffix = ""
    if segment_info and len(segment_info) == 2:
        start_frame, end_frame = segment_info
        segment_suffix = f"_segment_{start_frame}_{end_frame}"
    
    print(f"\n=== Generating Analysis Graphs{' for segment' if segment_suffix else ''} ===")
    
    # Get beat frames if available
    beat_frames = getattr(cycle_one, 'filtered_significant_beats', 
                         getattr(cycle_one, 'significant_beats', None))
    
    # Get maxima and minima - these might be called peaks and valleys in the existing data
    # We maintain backwards compatibility while using our new terminology
    y_maxima = getattr(cycle_one, 'y_maxima', 
                      getattr(cycle_one, 'y_peaks', None))
    y_minima = getattr(cycle_one, 'y_minima', 
                      getattr(cycle_one, 'y_valleys', None))
    
    # First, detect time signature from the data for consistency across graphs
    # Start with the default or stored time signature
    time_signature = getattr(cycle_one, 'time_signature', 4)
    
    # Detect the time signature using normalized_and_detect_peaks, if we have y data
    if hasattr(cycle_one, 'y') and len(cycle_one.y) > 0:
        y_normalized, detected_maxima, detected_minima = normalize_and_detect_peaks(cycle_one.y)
        detected_ts = estimate_time_signature(detected_maxima, detected_minima, y_normalized)
        
        # If we successfully detected a time signature, use it
        if detected_ts is not None and detected_ts > 0:
            time_signature = detected_ts
            print(f"Detected time signature: {time_signature}/4 - using for all graphs")
        else:
            print(f"Using default time signature: {time_signature}/4")
    
    # Now generate all graphs with the consistent time signature
    
    if graph_options.get("generate_time_signature_plot", True):
        print("Generating time signature plot...")
        time_signature_plot(cycle_one.y, segment_suffix, beat_frames, time_signature)
    
    if graph_options.get("generate_beat_plot", True):
        print("Generating beat plot...")
        beat_plot_graph(cycle_one.processing_intervals, cycle_one.filtered_significant_beats, 
                       y_maxima, y_minima, cycle_one.y, segment_suffix)
    
    if graph_options.get("generate_hand_path", True):
        print("Generating hand path graph...")
        hand_path_graph(cycle_one.x, cycle_one.y, segment_suffix)

    if graph_options.get("generate_beat_cluster_graph", True):
        print("Generating beat-based cluster graph...")
        # Pass x and y coordinates and enable show_path for better visualization
        # This plots points at the frames where beats were detected
        cluster_graph(cycle_one.beat_coordinates, segment_suffix, 
                     cycle_one.y, beat_frames, time_signature,
                     show_path=True, x=cycle_one.x)
    
    if graph_options.get("generate_maxima_cluster_graph", True):
        print("Generating maxima-based cluster graph...")
        maxima_cluster_graph(cycle_one.x, cycle_one.y, None,
                            segment_suffix, time_signature, show_path=True)

    if graph_options.get("generate_swaying_graph", True):
        print("Generating swaying graph...")
        swaying_graph(cycle_one.swaying_detector.midpoints_x, 
                     cycle_one.swaying_detector.default_midpoint_history, 
                     cycle_one.swaying_detector.sway_threshold,
                     segment_suffix)
    
    if graph_options.get("generate_mirror_x_graph", True):
        print("Generating mirror X coordinate graph...")
        mirror_x_coordinate_graph(cycle_one.mirror_detector.left_hand_x, 
                                cycle_one.mirror_detector.right_hand_x,
                                segment_suffix)
    
    if graph_options.get("generate_mirror_y_graph", True):
        print("Generating mirror Y coordinate graph...")
        mirror_y_coordinate_graph(cycle_one.mirror_detector.left_hand_y, 
                                cycle_one.mirror_detector.right_hand_y,
                                segment_suffix)
    
    print("=== Graph Generation Complete ===\n")

# Updated beat_plot_graph function for graphs.py

def beat_plot_graph(intervals, beats, y_maxima, y_minima, y, segment_suffix=""):
    export_path = get_export_path()
    plt.figure(figsize=(12, 6))
    
    # plot coordinate data
    plt.plot(range(len(y)), y, label='Y Coordinates', color='g', alpha=0.7)

    # Handle different behavior for segment graphs vs full video graph
    if not segment_suffix:
        # For the full video graph, highlight all processing intervals
        if intervals:
            for start, end in intervals:
                # Make sure intervals are within the data range
                if start < len(y) and end < len(y):
                    plt.axvspan(start, end, color='yellow', alpha=0.3, 
                               label="Processed Range" if start == intervals[0][0] else None)
    else:
        # For segment graphs, highlight the entire range since it's all processed
        plt.axvspan(0, len(y)-1, color='yellow', alpha=0.2, label="Processed Range")

    # plot beat markers if any exist
    if beats:
        all_beats = [b for b in sorted(beats) if b < len(y)]
        if all_beats:
            for beat in all_beats:
                plt.axvline(x=beat, color='purple', linestyle='--', 
                           label="Beats" if beat == all_beats[0] else None)
    
    # Only plot maxima and minima within the data range
    if y_maxima is not None and len(y_maxima) > 0:
        valid_maxima = [m for m in y_maxima if m < len(y)]
        if valid_maxima:
            plt.plot(valid_maxima, [y[i] for i in valid_maxima], "o", label="Maxima (Highest Points)", markersize=6)
    
    if y_minima is not None and len(y_minima) > 0:
        valid_minima = [m for m in y_minima if m < len(y)]
        if valid_minima:
            plt.plot(valid_minima, [y[i] for i in valid_minima], "o", label="Minima (Lowest Points)", markersize=6)
    
    # Set plot title based on whether it's a segment or full video
    if segment_suffix:
        segment_parts = segment_suffix.split("_")
        if len(segment_parts) >= 3:
            segment_start = segment_parts[-2]
            segment_end = segment_parts[-1]
            title = f'Segment Analysis - Frames {segment_start}-{segment_end}'
        else:
            title = f'Segment Analysis{segment_suffix}'
            
        # For segment plots, adjust the x-axis to show frame numbers relative to segment
        plt.xlim(0, len(y)-1)
    else:
        title = 'X and Y Coordinates Over Frame Number - Full Video'
    
    # set plot attributes and save
    plt.title(title)
    plt.xlabel('Frame Number')
    plt.ylabel('Coordinate Value')
    plt.legend()
    plt.grid(True)
    
    # Add segment suffix to filename if provided
    output_file = os.path.join(export_path, video_beat_plot_name() + segment_suffix + '.png')
    plt.savefig(output_file, bbox_inches='tight', dpi=100)
    plt.close()

def hand_path_graph(x_proc, y_proc, segment_suffix=""):
    export_path = get_export_path()
    plt.figure(figsize=(12, 6))
    
    # Use helper function to process hand path data
    x_valid, y_valid = process_hand_path_data(x_proc, y_proc)
    
    # Use helper function to create color gradient segments
    segments, custom_cmap = create_color_gradient_segments(x_valid, y_valid)
    
    # plot path with gradient
    norm = plt.Normalize(0, len(x_valid))
    lc = LineCollection(segments, cmap=custom_cmap, norm=norm)
    lc.set_array(np.arange(len(x_valid)))
    plt.gca().add_collection(lc)
    
    # set plot attributes and save
    plt.xlim(np.nanmin(x_valid), np.nanmax(x_valid))
    plt.ylim(np.nanmin(y_valid), np.nanmax(y_valid))
    cbar = plt.colorbar(lc)
    cbar.set_label('Frame Number')
    plt.xlabel("X-Coords")
    plt.ylabel("Y-Coords")
    plt.title("Conducting Pattern")
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Add segment suffix to filename if provided
    output_file = os.path.join(export_path, video_conduct_path_name() + segment_suffix + '.png')
    plt.savefig(output_file, bbox_inches='tight')
    plt.close()

def cluster_graph(beat_coordinates, segment_suffix="", y=None, beat_frames=None, time_signature=4, show_path=False, x=None):
    export_path = get_export_path()  
    plt.figure(figsize=(12, 6))
    
    # Define colors for the beats
    colors = ['red', 'blue', 'green', 'orange']  # List of colors for beats
    color_labels = ['1st Beat (Downbeat)', '2nd Beat', '3rd Beat', '4th Beat']

    # If show_path is True, plot all frames as a path to see the full conducting pattern
    if show_path and x is not None and y is not None and len(x) == len(y):
        # Process the data to remove NaN values and invert y-coordinates
        valid_mask = ~(np.isnan(x) | np.isnan(y))
        x_valid = x[valid_mask]
        y_valid = -y[valid_mask]  # Invert y-coordinates for proper visualization
        
        # Plot the full conducting path with a light gray color
        plt.plot(x_valid, y_valid, color='lightgray', alpha=0.5, linestyle='-', 
               linewidth=1, label='Conducting Path')

    # Plot the beats on the graph
    if beat_coordinates:  # Check if there are any beat coordinates
        x_beats, y_beats = zip(*beat_coordinates)  # Unzip the beat coordinates
        
        # We need to invert for display to maintain the right orientation
        # In conducting, higher y value = higher physical position
        y_beats_inverted = [-y for y in y_beats]
        
        # Determine beat positions:
        beat_positions = []
        
        # If we have y data and beat frames, use the beat position identification
        if y is not None and beat_frames is not None and len(beat_frames) == len(beat_coordinates):
            # Use our advanced beat position detection
            beat_positions = identify_beat_positions(beat_frames, y, time_signature)
        else:
            # Fallback: Simple sequential assignment based on expected time signature
            beat_positions = [i % time_signature for i in range(len(x_beats))]
        
        # Create a legend handle list
        legend_elements = []
        legend_labels = []
        
        # Add title to clarify we're using minima for beat detection
        plt.title("Beat Positions at Conducting Minima (beats)")
        
        # Plot each beat with color based on its position in the pattern
        for i in range(len(x_beats)):
            position = beat_positions[i] if i < len(beat_positions) else i % time_signature
            color_index = position % len(colors)  # Map position to color
            
            # Plot the beat
            plt.scatter(x_beats[i], y_beats_inverted[i], color=colors[color_index], s=100, alpha=0.7)
            
            # Add position number beside point
            plt.annotate(f"{position+1}", (x_beats[i], y_beats_inverted[i]), 
                        xytext=(5, 5), textcoords='offset points', fontsize=10)
            
            # Add to legend if this position hasn't been seen yet
            if position < len(colors) and color_labels[position] not in legend_labels:
                from matplotlib.lines import Line2D
                legend_elements.append(Line2D([0], [0], marker='o', color='w', 
                                            markerfacecolor=colors[color_index], markersize=10))
                legend_labels.append(color_labels[position])
        
        # Add legend with beat position labels
        if legend_elements:
            plt.legend(legend_elements, legend_labels, loc='upper right')
    
    plt.xlabel("X-Coords")
    plt.ylabel("Y-Coords (Inverted)")
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Add segment suffix to filename if provided
    output_file = os.path.join(export_path, video_cluster_plot_name() + segment_suffix + '.png')
    plt.savefig(output_file, bbox_inches='tight')
    plt.close()

def time_signature_plot(y, segment_suffix="", beat_frames=None, time_signature=4):
    export_path = get_export_path()
    plt.figure(figsize=(12, 6))

    # Plot inverted Y coordinates for visual consistency
    # Inverting the values makes the plot match the physical conducting space
    # (where higher values = higher hand position)
    plt.plot(range(len(y)), [-value for value in y], label="Y-Coords", color='g', alpha=0.7)

    # Use helper function to normalize data and detect maxima and minima
    # Maxima represent highest points in conducting pattern (when inverted)
    # Minima represent lowest points in conducting pattern (when inverted)
    y_normalized, y_maxima, y_minima = normalize_and_detect_peaks(y)

    # Mark minima on the plot (these are the lowest points in conducting)
    for minima in y_minima:
        if minima < len(y_normalized) and not np.isnan(y_normalized[minima]):
            # Invert the y-values for display consistency
            plt.plot(minima, -y_normalized[minima], 'o', color='purple', 
                    label="Minimum" if minima == y_minima[0] else None)
            plt.text(minima, -y_normalized[minima], 'Min', color='purple', fontsize=8, ha='right')
    
    # Calculate maxima heights for coloring (higher values = higher in physical space)
    maxima_heights = []
    for maxima in y_maxima:
        if maxima < len(y_normalized) and not np.isnan(y_normalized[maxima]):
            maxima_heights.append(-y_normalized[maxima])
    
    # Determine threshold for significant maxima if we have enough data
    significant_threshold = None
    if maxima_heights:
        heights_array = np.array(maxima_heights)
        significant_threshold = max(
            np.percentile(heights_array, 75),
            np.mean(heights_array) + 0.5 * np.std(heights_array)
        )
    
    # Mark maxima with different colors based on significance
    for i, maxima in enumerate(y_maxima):
        if maxima < len(y_normalized) and not np.isnan(y_normalized[maxima]):
            # Determine if this is a significant maxima (higher point)
            is_significant = False
            if significant_threshold is not None and i < len(maxima_heights):
                maxima_height = maxima_heights[i] if i < len(maxima_heights) else 0
                is_significant = maxima_height > significant_threshold
            
            # Use different colors/sizes for significant vs regular maxima
            maxima_color = 'red' if is_significant else 'blue'
            maxima_size = 8 if is_significant else 6
            maxima_label = "Significant Maximum" if is_significant and all(p != "Significant Maximum" for p in plt.gca().get_legend_handles_labels()[1]) else \
                        "Maximum" if maxima == y_maxima[0] else None
            
            # Invert the y-values for display consistency
            plt.plot(maxima, -y_normalized[maxima], 'o', color=maxima_color, 
                    markersize=maxima_size, label=maxima_label)
            
            # Add label text
            label_text = "Max" if not is_significant else "Sig.Max"
            plt.text(maxima, -y_normalized[maxima], label_text, color=maxima_color, 
                    fontsize=8, ha='right')

    # Mark beat frames if available with beat position numbers
    if beat_frames:
        # Use the identify_beat_positions function to determine beat positions
        # This classifies beats by their position in the conducting pattern
        beat_positions = identify_beat_positions(beat_frames, y, time_signature)
        colors = ['red', 'blue', 'green', 'orange']  # Colors for different beat positions
        
        for i, frame in enumerate(beat_frames):
            if frame < len(y):
                position = beat_positions[i] if i < len(beat_positions) else i % time_signature
                label = f"Beat {position+1}" if i == 0 else None
                # plt.axvline(x=frame, color=colors[position % len(colors)], linestyle='--', alpha=0.5, label=label)
                
                # Add beat position number (inverted for consistent display)
                plt.text(frame, -y[frame] if frame < len(y) else 0, 
                         f"{position+1}", color=colors[position % len(colors)], 
                         fontsize=10, fontweight='bold', ha='center')

    # Try to detect the time signature based on peaks
    # This uses the logic: large maximum waves followed by minima are downbeats,
    # and counting minima between consecutive downbeats determines the time signature
    detected_ts = estimate_time_signature(y_maxima, y_minima, y_normalized)
    if detected_ts:
        plt.title(f"Time Signature Plot - Detected Time Signature: {detected_ts}/4")
    else:
        plt.title(f"Time Signature Plot")

    # Finalize and show the plot
    plt.xlabel("Frame Number")
    plt.ylabel("Y Value (Inverted)")
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()

    # Save the plot with segment suffix if provided
    output_file = os.path.join(export_path, video_time_signature_plot_name() + segment_suffix + '.png')
    plt.savefig(output_file, bbox_inches='tight')
    plt.close()

def swaying_graph(mid, default_mid, threshold, segment_suffix=""):
    export_path = get_export_path()
    if not mid:
        return
        
    plt.figure(figsize=(12, 6))
    
    # Plot all midpoints
    plt.plot(range(len(mid)), mid, label='Current Midpoint X', color='b', alpha=0.7)
    
    # Ensure default_mid has consistent data types
    default_mid_normalized = []
    for value in default_mid:
        try:
            if isinstance(value, (list, tuple, np.ndarray)):
                # If it's a sequence, take the first element or average
                if len(value) > 0:
                    default_mid_normalized.append(float(value[0]))
                else:
                    default_mid_normalized.append(0.0)
            else:
                default_mid_normalized.append(float(value))
        except (ValueError, TypeError):
            # If conversion fails, use a default value
            default_mid_normalized.append(0.0)
    
    # Plot the default midpoints only if we have normalized values
    if default_mid_normalized:
        plt.plot(range(len(default_mid_normalized)), default_mid_normalized, 
                label='Default Midpoint X', color='r', alpha=0.7)
        
        # Plot threshold lines based on default_mid values
        upper_threshold = [value + threshold for value in default_mid_normalized]
        lower_threshold = [value - threshold for value in default_mid_normalized]
        
        plt.plot(range(len(default_mid_normalized)), upper_threshold, color='r', 
                linestyle='--', label='Upper Threshold X')
        plt.plot(range(len(default_mid_normalized)), lower_threshold, color='r', 
                linestyle='--', label='Lower Threshold X')
    
    # Set plot attributes and save
    plt.title('Swaying Detection Over Frame Number')
    plt.xlabel('Frame Number')
    plt.ylabel('Midpoint X Value')
    plt.legend()
    plt.grid(True)
    
    # Ensure export path exists and create full path for the file
    os.makedirs(export_path, exist_ok=True)
    
    # Add segment suffix to filename if provided
    output_file = os.path.join(export_path, video_sway_plot_Name() + segment_suffix + '.png')
    
    print(f"Saving swaying graph to: {output_file}")
    plt.savefig(output_file)
    plt.close()

def mirror_x_coordinate_graph(left_hand_x, right_hand_x, segment_suffix=""):
    export_path = get_export_path()
    if not left_hand_x or not right_hand_x:
        return
        
    plt.figure(figsize=(12, 6))
    
    # plot normalized hand coordinates
    plt.plot(range(len(left_hand_x)), [x - left_hand_x[0] for x in left_hand_x], 
             label='Left Hand X', color='b', alpha=0.7)
    plt.plot(range(len(right_hand_x)), [x - right_hand_x[0] for x in right_hand_x], 
             label='Right Hand X', color='g', alpha=0.7)
    plt.axhline(y=0, color='k', linestyle='-', label='Default Line')
    
    # set plot attributes and save
    plt.title('Hands X Coordinates Over Frame Number')
    plt.xlabel('Frame Number')
    plt.ylabel('Coordinate Value')
    plt.legend()
    plt.grid(True)
    
    # Add segment suffix to filename if provided
    output_file = os.path.join(export_path, video_hands_plot_x_name() + segment_suffix + '.png')
    plt.savefig(output_file)
    plt.close()

def mirror_y_coordinate_graph(left_hand_y, right_hand_y, segment_suffix=""):
    export_path = get_export_path()
    if not left_hand_y or not right_hand_y:
        return

    y_corrected_left = [-y for y in left_hand_y]
    y_corrected_right = [-y for y in right_hand_y]
        
    plt.figure(figsize=(12, 6))
    
    # plot normalized hand coordinates
    plt.plot(range(len(y_corrected_left)), [y - y_corrected_left[0] for y in y_corrected_left], 
             label='Left Hand Y', color='r', alpha=0.7)
    plt.plot(range(len(y_corrected_right)), [y - y_corrected_right[0] for y in y_corrected_right], 
             label='Right Hand Y', color='m', alpha=0.7)
    plt.axhline(y=0, color='k', linestyle='-', label='Default Line')
    
    # set plot attributes and save
    plt.title('Hands Y Coordinates Over Frame Number')
    plt.xlabel('Frame Number')
    plt.ylabel('Coordinate Value')
    plt.legend()
    plt.grid(True)
    
    # Add segment suffix to filename if provided
    output_file = os.path.join(export_path, video_hands_plot_y_name() + segment_suffix + '.png')
    plt.savefig(output_file)
    plt.close()

def maxima_cluster_graph(x, y, y_peaks, segment_suffix="", time_signature=4, show_path=True):
   
    export_path = get_export_path()  
    plt.figure(figsize=(12, 6))
    
    # Define colors for the maxima
    colors = ['red', 'blue', 'green', 'orange']  # List of colors for maxima
    color_labels = ['1st Max', '2nd Max', '3rd Max', '4th Max']

    # If show_path is True, plot all frames as a path to see the full conducting pattern
    if show_path and len(x) == len(y):
        # Process the data to remove NaN values and invert y-coordinates
        valid_mask = ~(np.isnan(x) | np.isnan(y))
        x_valid = x[valid_mask]
        # Invert y-coordinates for proper visualization
        y_valid = -y[valid_mask]  
        
        # Plot the full conducting path with a light gray color
        plt.plot(x_valid, y_valid, color='lightgray', alpha=0.5, linestyle='-', 
               linewidth=1, label='Conducting Path')

    # Due to the coordinate system inversion, maxima in the data (highest points)
    # correspond to the highest points in the physical conducting gesture
    
    # Get normalized data and find maxima (which are the actual highest points)
    _, y_maxima, _ = normalize_and_detect_peaks(y)
    
    if len(y_maxima) > 0 and len(x) == len(y):
        # Filter maxima that are within the array bounds
        valid_maxima = [m for m in y_maxima if m < len(y)]
        
        if valid_maxima:
            # Get x,y values at the maxima (which are the highest points of gesture)
            x_maxima = [x[m] for m in valid_maxima]
            y_maxima_vals = [y[m] for m in valid_maxima]
            
            # Invert y for display consistency
            y_maxima_inverted = [-y for y in y_maxima_vals]
            
            # Create a legend handle list
            legend_elements = []
            legend_labels = []
            
            # Add title to clarify we're using maxima
            plt.title("Cluster of Conducting Gesture Maxima (Highest Points)")
            
            # Plot each maximum with color based on its position in the pattern
            for i in range(len(x_maxima)):
                # Assign positions based on sequence (mod time_signature)
                position = i % time_signature
                color_index = position
                
                # Plot the maximum
                plt.scatter(x_maxima[i], y_maxima_inverted[i], color=colors[color_index], s=100, alpha=0.7)
                
                # Add position number beside point
                plt.annotate(f"{position+1}", (x_maxima[i], y_maxima_inverted[i]), 
                            xytext=(5, 5), textcoords='offset points', fontsize=10)
                
                # Add to legend if this position hasn't been seen yet
                if position < len(colors) and color_labels[position] not in legend_labels:
                    from matplotlib.lines import Line2D
                    legend_elements.append(Line2D([0], [0], marker='o', color='w', 
                                                markerfacecolor=colors[color_index], markersize=10))
                    legend_labels.append(color_labels[position])
            
            # Add legend with maxima position labels
            if legend_elements:
                plt.legend(legend_elements, legend_labels, loc='upper right')
    
    plt.xlabel("X-Coords")
    plt.ylabel("Y-Coords (Inverted)")
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Add segment suffix to filename if provided
    output_file = os.path.join(export_path, video_cluster_plot_name() + "_maxima" + segment_suffix + '.png')
    plt.savefig(output_file, bbox_inches='tight')
    plt.close()