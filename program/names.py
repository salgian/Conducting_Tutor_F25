import os

VIDEO_PATH = "C:/Users/Jeffrey Ernest/Desktop/videos/Marchingband(2).mp4"
EXPORT_PATH = "output\Marchingband(2)_analysis_20250422_190948\conducting_analysis"

# returns the name of the video file being processed
def initialize_video():
    # Return just the basename without extension
    return os.path.splitext(os.path.basename(VIDEO_PATH))[0]

# returns name for the final output video
def video_out_name():
    videoFileName = initialize_video()
    outNames = videoFileName + "_analyzed"
    return outNames

# returns name for the main coordinates plot
def video_plot_name():
    videoFileName = initialize_video()
    plotName = videoFileName + '_coordinates_plot'
    return plotName

# returns name for the sway analysis plot
def video_sway_plot_Name():
    videoFileName = initialize_video()
    swayPlotName = videoFileName + '_sway_plot'
    return swayPlotName

# returns name for the x-axis hand movement plot
def video_hands_plot_x_name():
    videoFileName = initialize_video()
    handsPlotName_X = videoFileName + '_hands_plot_x'
    return handsPlotName_X

# returns name for the y-axis hand movement plot
def video_hands_plot_y_name():
    videoFileName = initialize_video()
    handsPlotName_Y = videoFileName + '_hands_plot_y'
    return handsPlotName_Y

# returns name for the beat detection plot
def video_beat_plot_name():
    videoFileName = initialize_video()
    beatPlotName = videoFileName + '_beat_plot'
    return beatPlotName

# returns name for the conducting path visualization
def video_conduct_path_name():
    videoFileName = initialize_video()
    conductPath = videoFileName + '_conduct_path'
    return conductPath

# returns name for the bpm text file
def video_bpm_output_name():
    videoFileName = initialize_video()
    bpmOutputName = videoFileName + '_auto_BPM.txt'
    return bpmOutputName

# returns name for the cluster plot
def video_cluster_plot_name():
    videoFileName = initialize_video()
    clusterPlotName = videoFileName + '_cluster_plot'
    return clusterPlotName

# returns name for the overtime plot
def video_overtime_plot_name():
    videoFileName = initialize_video()
    overtimePlotName = videoFileName + '_overtime_plot'
    return overtimePlotName

# Helper function to join export path with filename
def get_full_path(filename):
    return os.path.join(EXPORT_PATH, filename)
