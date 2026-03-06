EXPORT_PATH = "default_output"

def set_export_path(path):
    """Sets the export path for all output files."""
    global EXPORT_PATH
    EXPORT_PATH = path

def get_export_path():
    """Retrieves the current export path."""
    return EXPORT_PATH

# Standard library imports
import numpy as np
from datetime import datetime
import cv2
import json
import matplotlib
from matplotlib import pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap
from scipy.signal import find_peaks
import time
import sys
#PyGame
import pygame
from numpy import mean
import subprocess

# Mediapipe imports
import mediapipe as mp
from mediapipe.framework.formats import landmark_pb2

# Local imports
from names import *
from outdated_files.pattern import *
from mp_declaration import mediaPipeDeclaration
from p_stage1 import process_video
from p_stage2 import output_process_video
from beat_filter import filter_beats
from sway import swayingDetection
from mirror import mirrorDetection
from graphs import *
from interface import *
from sanrio_interface import *