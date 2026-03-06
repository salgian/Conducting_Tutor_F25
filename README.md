# Conducting_Tutor

# Project Overview (program)

This project processes video data to detect conducting movements and generate visualizations. Below is a brief description of each file in the project:

## Core Files

- **main.py**: The main execution point of the program, handling video processing and orchestrating the analysis workflow.

- **main_conducting_analysis.py**: Manages the conducting analysis process, including pattern detection, beat identification, and visualization generation.

- **main_cycle_processor.py**: Handles the processing of conducting cycles, identifying patterns across multiple frames.

- **main_segment_processor.py**: Processes video segments for isolated analysis of specific conducting sections.

- **main_config_manager.py**: Manages configuration settings for the application.

- **main_graph_options.py**: Controls options for graph generation and visualization preferences.

- **p_stage1.py**: Handles the first stage of video processing, including frame processing and landmark detection.

- **p_stage2.py**: Manages the second stage of video processing, displaying annotated frames with detected beats and generating BPM data.

## Graph Generation and Analysis

- **graphs.py**: Responsible for generating various analysis graphs from the processed data, including plots for beat detection, hand movements, and swaying detection.

- **graph_math.py**: Contains mathematical functions for analyzing conducting patterns, including peak detection, time signature estimation, and beat position identification.

- **graph_config.py**: Manages configuration settings for graph generation, including file paths and naming conventions.

## Detection Components

- **beat_filter.py**: Contains functions for filtering significant points (beats) from the detected peaks and valleys in the movement data.

- **new_beats.py**: Implements improved algorithms for beat detection using advanced signal processing techniques.

- **mirror.py**: Implements the `mirrorDetection` class, which tracks the coordinates of the left and right hands for analyzing mirror movements.

- **sway.py**: Implements the `swayingDetection` class, which detects swaying movements based on the calculated midpoints of the hands.

- **elbow.py**: Analyzes elbow position and movement during conducting patterns.

- **cueing.py**: Detects cueing gestures in conducting movements.

## Interface Components

- **interface.py**: Manages the user interface for the application.

- **sanrio_interface.py**: Provides an alternative themed interface for the application.

## Utility Components

- **mp_declaration.py**: Contains the `mediaPipeDeclaration` class, which sets up and manages the Mediapipe pose landmark detection.

- **names.py**: Provides utility functions for generating names for video files, output files, and plots based on the input video file.

## Configuration Files

- **interface_config.json**: Stores configuration settings for the interface and application behavior.

## Directory Structure

- **output/**: Directory where generated graphs and analysis results are stored.

- **pose_landmarks/**: Contains data related to pose landmark detection.

- **theme_assets/**: Stores assets for the themed interfaces.

