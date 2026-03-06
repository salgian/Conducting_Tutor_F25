import pygame
import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
import os
import numpy as np
import json
import time
import sys
import threading

# Import additional modules
from main_config_manager import load_config
from main_graph_options import select_graph_options
from main_segment_processor import process_segment
from main_conducting_analysis import run_conducting_analysis
from main_cycle_processor import CycleOne, CycleTwo
from graphs import generate_all_graphs

# Global variables for external functions
should_render_frame = True
pygame_initialized = False
screen = None
window_size = (800, 600)
# Additional state variables
creating_crop = False
crop_start_pos = None
double_click_time = 0
double_click_threshold = 0.5  # seconds
crop_mode = "ready"  # "ready", "creating", "adjusting"

# In interface.py, after your imports
try:
    # Try to import the flag from main
    from main import CONDUCTING_MODULES_AVAILABLE
except (ImportError, ModuleNotFoundError):
    # If main.py hasn't been run yet or can't be imported
    CONDUCTING_MODULES_AVAILABLE = False

# Processing options with default values
processing_options = {
    "generate_beat_plot": True,
    "generate_hand_path": True,
    "generate_cluster_graph": True,
    "generate_overtime_graph": True,
    "generate_swaying_graph": True,
    "generate_mirror_x_graph": True,
    "generate_mirror_y_graph": True,
    
    # Add export options for graphs and videos
    "export_beat_detection": CONDUCTING_MODULES_AVAILABLE,
    # "export_pattern_analysis": CONDUCTING_MODULES_AVAILABLE,
}

# Initialize pygame if needed
def ensure_pygame_initialized():
    global pygame_initialized, screen, window_size
    if not pygame_initialized:
        if not pygame.get_init():
            pygame.init()
        pygame_initialized = True
        
        # Check if a window already exists
        existing_surface = pygame.display.get_surface()
        if existing_surface is not None:
            screen = existing_surface
            window_size = screen.get_size()
        else:
            # Get display info
            info = pygame.display.Info()
            window_size = (min(1024, info.current_w), min(768, info.current_h))
            screen = pygame.display.set_mode(window_size, pygame.RESIZABLE)
            pygame.display.set_caption("Conducting Movement Detection")

# Function to determine if frames should be shown in the current state
def should_show_frame_in_state(current_state):
    """Determine if a frame should be shown based on current state"""
    # Define states where the frame should be shown
    frame_states = ["crop", "timeline"]
    return current_state in frame_states

# Function to update the render state flag
def update_render_state():
    """Update the should_render_frame flag based on current state"""
    global should_render_frame, state, show_menu
    
    # Don't render frames when menu is shown
    if show_menu:
        should_render_frame = False
        return
    
    # Update based on state
    should_render_frame = should_show_frame_in_state(state)

# External API functions (for other modules)
def get_window_size():
    """Returns the current window size for external modules"""
    global window_size, screen
    ensure_pygame_initialized()
    if screen:
        return screen.get_size()
    return window_size

def get_screen():
    """Returns the Pygame screen object for external modules"""
    global screen
    ensure_pygame_initialized()
    return screen

def display_frame(frame):
    """Display a frame for external modules"""
    global screen, should_render_frame
    ensure_pygame_initialized()
    
    if frame is None or not should_render_frame:
        return False
    
    # Handle different frame formats
    if isinstance(frame, np.ndarray):
        # Convert BGR to RGB if needed
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        else:
            frame_rgb = frame
        
        # Create pygame surface
        frame_surface = pygame.surfarray.make_surface(frame_rgb.transpose(1, 0, 2))
        screen.blit(frame_surface, (0, 0))
        pygame.display.flip()
        return True
    return False

# UI Constants
ensure_pygame_initialized()  # Initialize pygame before using it
BG_COLOR = (30, 30, 30)
BUTTON_COLOR = (70, 130, 180)
HIGHLIGHT_COLOR = (100, 180, 240)
TEXT_COLOR = (255, 255, 255)
RED_COLOR = (255, 50, 50)
GREEN_COLOR = (50, 255, 50)
BLUE_COLOR = (50, 50, 255)
CHECKBOX_COLOR = (150, 150, 150)
CHECKBOX_CHECKED_COLOR = (100, 200, 100)
MENU_BG_COLOR = (40, 40, 40)
PANEL_BG_COLOR = (40, 40, 40, 220)  # Semi-transparent background for panels
FONT = pygame.font.Font(None, 30)
SMALL_FONT = pygame.font.Font(None, 24)
TITLE_FONT = pygame.font.Font(None, 36)

# Tkinter root for file dialogs
root = tk.Tk()
root.withdraw()

# UI State management
state = "title"
video_path = ""
export_path = "output"
crop_rect = pygame.Rect(200, 150, 400, 300)
resizing = False
resize_edge = None
dragging = False
drag_start = None
cap = None
current_frame = 0
total_frames = 0
frame_image = None
process_markers = []  # List of tuples (start_frame, end_frame, crop_rect)
is_playing = False
last_frame_time = 0
frame_display_time = 1/30  # Default to 30fps
currently_processing = False
process_start_frame = None
show_menu = False
record_device = None
is_recording = False
recording_frames = []
recording_start_time = 0

# Output configuration
config = {
    "video_path": "",
    "export_path": "output",
    "crop_rect": [200, 150, 400, 300],
    "process_markers": [],
    "processing_options": processing_options
}

def save_config():
    """Save configuration to JSON file for main.py to read"""
    config["video_path"] = video_path
    config["export_path"] = export_path
    config["crop_rect"] = [crop_rect.x, crop_rect.y, crop_rect.width, crop_rect.height]
    
    # Format process markers with crop info
    formatted_markers = []
    for marker in process_markers:
        if len(marker) == 2:  # Old format with just start and end
            formatted_markers.append({
                "start_frame": marker[0],
                "end_frame": marker[1],
                "crop": [crop_rect.x, crop_rect.y, crop_rect.width, crop_rect.height]
            })
        else:  # New format with crop info
            marker_crop = marker[2]
            formatted_markers.append({
                "start_frame": marker[0],
                "end_frame": marker[1],
                #"crop": [marker_crop.x, marker_crop.y, marker_crop.width, marker_crop.height]
            })
    
    config["process_markers"] = process_markers
    
    # Extract graph-related options from processing_options
    graph_options = {}
    for key, value in processing_options.items():
        if key.startswith("generate_"):
            graph_options[key] = value
    
    # Add graph options to the config
    if "processing_options" not in config:
        config["processing_options"] = {}
    
    config["processing_options"]["graph_options"] = graph_options
    
    # Add the remaining processing options
    for key, value in processing_options.items():
        if not key.startswith("generate_"):
            config["processing_options"][key] = value
    
    with open("interface_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    # Preserve existing content of names.py and update only the needed variables
    try:
        # Read existing content
        existing_content = ""
        video_path_found = False
        export_path_found = False
        
        try:
            with open("names.py", "r") as f:
                lines = f.readlines()
                
                for line in lines:
                    if line.strip().startswith("VIDEO_PATH ="):
                        # Replace VIDEO_PATH line
                        existing_content += f'VIDEO_PATH = "{video_path}"\n'
                        video_path_found = True
                    elif line.strip().startswith("EXPORT_PATH ="):
                        # Replace EXPORT_PATH line
                        existing_content += f'EXPORT_PATH = "{export_path}"\n'
                        export_path_found = True
                    else:
                        # Keep other lines unchanged
                        existing_content += line
        except FileNotFoundError:
            # File doesn't exist yet
            pass
        
        # Add variables if they weren't found
        if not video_path_found:
            existing_content += f'\nVIDEO_PATH = "{video_path}"\n'
        if not export_path_found:
            existing_content += f'EXPORT_PATH = "{export_path}"\n'
        
        # Write updated content
        with open("names.py", "w") as f:
            f.write(existing_content)
            
    except Exception as e:
        print(f"Error updating names.py: {e}")
        # Fallback to simple update if something goes wrong
        try:
            with open("names.py", "w") as f:
                f.write(f'VIDEO_PATH = "{video_path}"\n')
                f.write(f'EXPORT_PATH = "{export_path}"\n')
        except:
            pass

def select_video():
    """Open file dialog to select input video"""
    global video_path, cap, total_frames, current_frame, frame_image, frame_display_time
    video_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4;*.avi;*.mov")])
    if video_path:
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        # Get FPS for playback timing
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps > 0:
            frame_display_time = 1/fps
        # Read the first frame
        ret, frame = cap.read()
        if ret:
            frame_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return True
    return False

def select_export_path():
    """Open directory dialog to select export folder"""
    global export_path
    path = filedialog.askdirectory()
    if path:
        export_path = path
        return True
    return False

def start_recording():
    """Start recording from webcam"""
    global record_device, is_recording, recording_frames, recording_start_time
    
    # Try to open the default camera
    record_device = cv2.VideoCapture(0)
    if not record_device.isOpened():
        messagebox.showerror("Error", "Could not open camera")
        return False
    
    is_recording = True
    recording_frames = []
    recording_start_time = time.time()
    
    # Start recording thread
    recording_thread = threading.Thread(target=record_video_thread)
    recording_thread.daemon = True
    recording_thread.start()
    
    return True

def record_video_thread():
    """Background thread to record video frames"""
    global record_device, is_recording, recording_frames
    
    while is_recording and record_device is not None:
        ret, frame = record_device.read()
        if ret:
            recording_frames.append(frame)
        time.sleep(0.03)  # Aim for about 30fps

def stop_recording():
    """Stop recording and save video"""
    global record_device, is_recording, recording_frames, video_path
    global cap, total_frames, current_frame, frame_image, frame_display_time
    
    if not is_recording or record_device is None:
        return False
    
    is_recording = False
    
    # Allow time for thread to complete
    time.sleep(0.1)
    
    # Release camera
    record_device.release()
    record_device = None
    
    if len(recording_frames) == 0:
        messagebox.showerror("Error", "No frames were recorded")
        return False
    
    # Get frame dimensions from the first frame
    height, width = recording_frames[0].shape[:2]
    
    # Save recorded video
    output_path = "recorded_video.mp4"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, 30.0, (width, height))
    
    for frame in recording_frames:
        out.write(frame)
    
    out.release()
    
    # Set the recorded video as the current video
    video_path = output_path
    cap = cv2.VideoCapture(video_path)
    total_frames = len(recording_frames)
    frame_display_time = 1/30.0  # 30fps for recorded video
    
    # Set first frame
    current_frame = 0
    frame_image = cv2.cvtColor(recording_frames[0], cv2.COLOR_BGR2RGB)
    
    messagebox.showinfo("Success", f"Video recorded and saved to {output_path}")
    return True

def get_resize_edge(mouse_pos, frame_rect):
    """Determine which edge of the crop rectangle is being resized"""
    if not frame_rect:
        return None
        
    # Convert crop_rect to screen coordinates
    x, y, w, h = frame_rect
    rel_x = crop_rect.x / frame_image.shape[1]
    rel_y = crop_rect.y / frame_image.shape[0]
    rel_w = crop_rect.width / frame_image.shape[1]
    rel_h = crop_rect.height / frame_image.shape[0]
    
    screen_crop = pygame.Rect(
        x + rel_x * w,
        y + rel_y * h,
        rel_w * w,
        rel_h * h
    )
    
    # Define the edges with a certain thickness
    edge_thickness = 10
    edges = {
        "left": pygame.Rect(screen_crop.left - edge_thickness//2, screen_crop.top, edge_thickness, screen_crop.height),
        "right": pygame.Rect(screen_crop.right - edge_thickness//2, screen_crop.top, edge_thickness, screen_crop.height),
        "top": pygame.Rect(screen_crop.left, screen_crop.top - edge_thickness//2, screen_crop.width, edge_thickness),
        "bottom": pygame.Rect(screen_crop.left, screen_crop.bottom - edge_thickness//2, screen_crop.width, edge_thickness),
        "topleft": pygame.Rect(screen_crop.left - edge_thickness//2, screen_crop.top - edge_thickness//2, edge_thickness, edge_thickness),
        "topright": pygame.Rect(screen_crop.right - edge_thickness//2, screen_crop.top - edge_thickness//2, edge_thickness, edge_thickness),
        "bottomleft": pygame.Rect(screen_crop.left - edge_thickness//2, screen_crop.bottom - edge_thickness//2, edge_thickness, edge_thickness),
        "bottomright": pygame.Rect(screen_crop.right - edge_thickness//2, screen_crop.bottom - edge_thickness//2, edge_thickness, edge_thickness)
    }
    
    # Check if mouse is over any edge
    for edge, rect in edges.items():
        if rect.collidepoint(mouse_pos):
            if mouse_pos[0] > screen_crop.left + edge_thickness and mouse_pos[0] < screen_crop.right - edge_thickness and \
               mouse_pos[1] > screen_crop.top + edge_thickness and mouse_pos[1] < screen_crop.bottom - edge_thickness:
                return "middle"  # Inside the crop rect but not on an edge
            return edge
    
    return None

def draw_button(text, x, y, w, h, color=BUTTON_COLOR, hover=False, active=False):
    """Draw a button with hover and active effects"""
    rect = pygame.Rect(x, y, w, h)
    if active:
        button_color = GREEN_COLOR
    elif hover:
        button_color = HIGHLIGHT_COLOR
    else:
        button_color = color
    
    pygame.draw.rect(screen, button_color, rect, border_radius=5)
    text_surface = FONT.render(text, True, TEXT_COLOR)
    text_rect = text_surface.get_rect(center=rect.center)
    screen.blit(text_surface, text_rect)
    return rect

def draw_checkbox(label, x, y, width, height, checked=False, hover=False):
    """Draw a checkbox with label"""
    # Draw the box
    box_size = height
    box_rect = pygame.Rect(x, y, box_size, box_size)
    
    if hover:
        pygame.draw.rect(screen, HIGHLIGHT_COLOR, box_rect, border_radius=3)
    else:
        pygame.draw.rect(screen, CHECKBOX_COLOR, box_rect, border_radius=3)
    
    # If checked, draw the checkmark
    if checked:
        pygame.draw.rect(screen, CHECKBOX_CHECKED_COLOR, 
                        pygame.Rect(x+3, y+3, box_size-6, box_size-6), 
                        border_radius=2)
    
    # Draw the label
    label_text = SMALL_FONT.render(label, True, TEXT_COLOR)
    screen.blit(label_text, (x + box_size + 10, y + box_size//2 - label_text.get_height()//2))
    
    # Return the entire area for mouse detection
    return pygame.Rect(x, y, width, height)

def draw_menu():
    """Draw settings menu overlay with categorized options"""
    global processing_options
    
    # Draw a full-screen semi-transparent overlay
    overlay = pygame.Surface((window_size[0], window_size[1]), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))  # Dark semi-transparent overlay
    screen.blit(overlay, (0, 0))
    
    # Draw the menu panel
    menu_surface = pygame.Surface((350, window_size[1]), pygame.SRCALPHA)
    menu_surface.fill((40, 40, 40, 230))  # Semi-transparent dark background
    screen.blit(menu_surface, (window_size[0] - 350, 0))
    
    # Draw menu title
    title = TITLE_FONT.render("Processing Settings", True, TEXT_COLOR)
    screen.blit(title, (window_size[0] - 350 + 20, 20))
    
    # Draw divider
    pygame.draw.line(screen, HIGHLIGHT_COLOR, 
                   (window_size[0] - 350 + 20, 60),
                   (window_size[0] - 20, 60), 2)
    
    # Categorize options
    categories = {
        "Graph Options": [
            "generate_beat_plot", 
            "generate_hand_path", 
            "generate_cluster_graph",
            "generate_overtime_graph",
            "generate_swaying_graph",
            "generate_mirror_x_graph",
            "generate_mirror_y_graph"
        ]
    }
    
    if CONDUCTING_MODULES_AVAILABLE:
        categories["Conducting Analysis"] = [
            "export_beat_detection",
            # "export_pattern_analysis" // removed
        ]
    
    # Draw processing options checkboxes
    y_offset = 80
    checkboxes = {}
    
    for category, options in categories.items():
        # Draw category header
        category_text = FONT.render(category, True, HIGHLIGHT_COLOR)
        screen.blit(category_text, (window_size[0] - 330, y_offset))
        y_offset += 35
        
        for option in options:
            # Check if we need to add this option to processing_options
            if option.startswith("generate_") and option not in processing_options:
                processing_options[option] = True
                
            if option in processing_options:
                # Format the label (convert snake_case to Title Case with spaces)
                label = " ".join(word.capitalize() for word in option.split("_"))
                
                # Draw the checkbox
                checkbox_rect = draw_checkbox(
                    label, 
                    window_size[0] - 320, 
                    y_offset, 
                    300, 
                    30, 
                    checked=processing_options[option],
                    hover=pygame.Rect(window_size[0] - 320, y_offset, 300, 30).collidepoint(pygame.mouse.get_pos())
                )
                checkboxes[option] = checkbox_rect
                y_offset += 40
        
        # Add space between categories
        y_offset += 10
        pygame.draw.line(screen, (100, 100, 100), 
                       (window_size[0] - 320, y_offset - 5),
                       (window_size[0] - 50, y_offset - 5), 1)
    
    # Draw close button
    close_btn = draw_button(
        "Save & Close", 
        window_size[0] - 200, 
        window_size[1] - 60, 
        150, 
        40,
        hover=pygame.Rect(window_size[0] - 200, window_size[1] - 60, 150, 40).collidepoint(pygame.mouse.get_pos())
    )
    
    # Return a dictionary containing both checkboxes and close button
    return {'checkboxes': checkboxes, 'close_btn': close_btn}

def draw_recording_interface():
    """Draw recording interface"""
    # Draw a background panel
    panel_rect = pygame.Rect(window_size[0]//2 - 150, 30, 300, 170)
    pygame.draw.rect(screen, MENU_BG_COLOR, panel_rect, border_radius=10)
    pygame.draw.rect(screen, HIGHLIGHT_COLOR, panel_rect, 2, border_radius=10)
    
    recording_text = FONT.render("Recording Video...", True, RED_COLOR)
    screen.blit(recording_text, (window_size[0]//2 - recording_text.get_width()//2, 50))
    
    # Display recording time
    elapsed = time.time() - recording_start_time
    time_text = FONT.render(f"Time: {int(elapsed)}s", True, TEXT_COLOR)
    screen.blit(time_text, (window_size[0]//2 - time_text.get_width()//2, 90))
    
    # Red recording indicator (flashing)
    if int(elapsed) % 2 == 0:
        pygame.draw.circle(screen, RED_COLOR, (window_size[0]//2, 140), 10)
    
    # Stop recording button
    stop_btn = draw_button(
        "Stop Recording", 
        window_size[0]//2 - 100, 
        window_size[1]//2, 
        200, 
        50,
        color=RED_COLOR,
        hover=pygame.Rect(window_size[0]//2 - 100, window_size[1]//2, 200, 50).collidepoint(pygame.mouse.get_pos())
    )
    
    return stop_btn

def draw_slider(x, y, width, height, value, max_value):
    """Draw a slider control"""
    # Draw background
    back_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(screen, (100, 100, 100), back_rect, border_radius=height//2)
    
    # Draw process markers
    for marker in process_markers:
        start, end = marker[0], marker[1]
        start_pos = x + int((start / max_value) * width)
        end_pos = x + int((end / max_value) * width)
        marker_width = max(end_pos - start_pos, 5)
        pygame.draw.rect(screen, GREEN_COLOR, 
                         (start_pos, y, marker_width, height), 
                         border_radius=height//2)
    
    # Draw current processing marker if active
    if currently_processing and process_start_frame is not None:
        start_pos = x + int((process_start_frame / max_value) * width)
        end_pos = x + int((value / max_value) * width)
        marker_width = max(end_pos - start_pos, 5)
        pygame.draw.rect(screen, RED_COLOR, 
                         (start_pos, y, marker_width, height), 
                         border_radius=height//2)
    
    # Draw handle
    handle_pos = x + int((value / max_value) * width)
    pygame.draw.circle(screen, (200, 200, 200), (handle_pos, y + height//2), height)
    
    return back_rect

def display_specific_frame(frame_number):
    """Display a specific frame from the video"""
    global frame_image
    if cap and cap.isOpened():
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        if ret:
            frame_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return True
    return False

def draw_crop_instructions():
    """Draw enhanced instructions for crop mode"""
    # Draw instructions panel
    panel_rect = pygame.Rect(20, 20, 320, 200)
    panel_surface = pygame.Surface((320, 200), pygame.SRCALPHA)
    panel_surface.fill(PANEL_BG_COLOR)
    screen.blit(panel_surface, (20, 20))
    pygame.draw.rect(screen, HIGHLIGHT_COLOR, panel_rect, 2, border_radius=5)
    
    # Title
    instr_title = FONT.render("Region Selection", True, HIGHLIGHT_COLOR)
    screen.blit(instr_title, (panel_rect.x + 10, panel_rect.y + 10))
    
    # Different instructions based on current crop mode
    if crop_mode == "ready":
        instructions = [
            "Click and drag to create a selection",
            "Existing selection can be adjusted",
            "Press ENTER to confirm when done"
        ]
    elif crop_mode == "creating":
        instructions = [
            "Keep dragging to size your selection",
            "Release mouse button when done",
            "Double-click to finalize selection"
        ]
    elif crop_mode == "adjusting":
        instructions = [
            "Drag corners/edges to resize",
            "Drag center to move entire selection",
            "Double-click to finalize selection"
        ]
    
    y_offset = panel_rect.y + 45
    for instr in instructions:
        instr_text = SMALL_FONT.render(instr, True, TEXT_COLOR)
        screen.blit(instr_text, (panel_rect.x + 15, y_offset))
        y_offset += 25
    
    # Status message based on current mode
    status_msg = ""
    if crop_mode == "ready":
        status_msg = "Ready to create selection"
    elif crop_mode == "creating":
        status_msg = "Creating selection..."
    elif crop_mode == "adjusting":
        status_msg = "Adjusting selection..."
    
    status_text = FONT.render(status_msg, True, GREEN_COLOR)
    screen.blit(status_text, (panel_rect.x + 15, y_offset + 10))
    
    # Key commands
    y_offset += 50
    key_text = SMALL_FONT.render("ENTER: Confirm  |  ESC: Cancel", True, (200, 200, 200))
    screen.blit(key_text, (panel_rect.x + 15, y_offset))

def update_crop_rect(mouse_pos, frame_rect, edge, dragging=False):
    """Update crop rectangle based on mouse position and which edge is being resized"""
    if not frame_rect or not edge:
        return
    
    x, y, w, h = frame_rect
    
    # Convert mouse position to video coordinates
    rel_mouse_x = (mouse_pos[0] - x) / w
    rel_mouse_y = (mouse_pos[1] - y) / h
    
    # Clamp to video dimensions
    rel_mouse_x = max(0, min(1, rel_mouse_x))
    rel_mouse_y = max(0, min(1, rel_mouse_y))
    
    # Calculate mouse position in original video dimensions
    mouse_x = int(rel_mouse_x * frame_image.shape[1])
    mouse_y = int(rel_mouse_y * frame_image.shape[0])
    
    min_size = 50  # Minimum size in pixels
    
    if edge == "middle" and dragging:
        # Move the entire rectangle (dragging)
        dx = mouse_x - drag_start[0]
        dy = mouse_y - drag_start[1]
        
        new_x = max(0, min(frame_image.shape[1] - crop_rect.width, crop_rect.x + dx))
        new_y = max(0, min(frame_image.shape[0] - crop_rect.height, crop_rect.y + dy))
        
        crop_rect.x = new_x
        crop_rect.y = new_y
        return (mouse_x, mouse_y)  # Return new drag start
    
    # Handle corner and edge resizing
    if "left" in edge:
        new_width = crop_rect.right - mouse_x
        if new_width >= min_size:
            crop_rect.x = mouse_x
            crop_rect.width = new_width
    
    if "right" in edge:
        new_width = mouse_x - crop_rect.x
        if new_width >= min_size:
            crop_rect.width = new_width
    
    if "top" in edge:
        new_height = crop_rect.bottom - mouse_y
        if new_height >= min_size:
            crop_rect.y = mouse_y
            crop_rect.height = new_height
    
    if "bottom" in edge:
        new_height = mouse_y - crop_rect.y
        if new_height >= min_size:
            crop_rect.height = new_height
    
    # Ensure crop rect is within video bounds
    crop_rect.x = max(0, min(frame_image.shape[1] - min_size, crop_rect.x))
    crop_rect.y = max(0, min(frame_image.shape[0] - min_size, crop_rect.y))
    crop_rect.width = max(min_size, min(frame_image.shape[1] - crop_rect.x, crop_rect.width))
    crop_rect.height = max(min_size, min(frame_image.shape[0] - crop_rect.y, crop_rect.height))
    
    return drag_start  # Keep existing drag start

def handle_crop_creation(event):
    """Handle crop rectangle creation with direct mouse interaction"""
    global crop_rect, creating_crop, crop_start_pos, resizing, drag_start, crop_mode, double_click_time
    
    # Handle double clicks to finalize selection
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        current_time = time.time()
        if current_time - double_click_time < double_click_threshold:
            # Double click detected - finalize selection
            creating_crop = False
            if crop_mode != "ready":
                crop_mode = "adjusting"  # Set to adjusting mode after creation
            return
        double_click_time = current_time
        
        # Start creating a new crop if we're in the ready state
        frame_rect = None
        if should_render_frame:
            # Get frame rect from render_frame or ui_elements
            if 'frame_rect' in event.dict.get('ui_elements', {}):
                frame_rect = event.dict['ui_elements']['frame_rect']
            else:
                h, w = frame_image.shape[:2]
                window_w, window_h = screen.get_size()
                scale = min(window_w / w, (window_h - 200) / h)
                new_w, new_h = int(w * scale), int(h * scale)
                x = (window_w - new_w) // 2
                y = (window_h - new_h - 150) // 2
                frame_rect = (x, y, new_w, new_h)
                
        if frame_rect and crop_mode == "ready":
            # Check if clicking inside the rendered frame
            x, y, w, h = frame_rect
            if x <= event.pos[0] <= x + w and y <= event.pos[1] <= y + h:
                # Convert to video coordinates
                rel_x = (event.pos[0] - x) / w
                rel_y = (event.pos[1] - y) / h
                
                video_x = int(rel_x * frame_image.shape[1])
                video_y = int(rel_y * frame_image.shape[0])
                
                # Start creating new crop rectangle
                creating_crop = True
                crop_start_pos = (video_x, video_y)
                # Initialize with small size
                crop_rect = pygame.Rect(video_x, video_y, 1, 1)
                crop_mode = "creating"
    
    # Update crop rectangle during drag
    elif event.type == pygame.MOUSEMOTION and creating_crop and crop_mode == "creating":
        # Get frame rect from render_frame or ui_elements
        frame_rect = None
        if should_render_frame:
            if hasattr(event, 'dict') and 'ui_elements' in event.dict and 'frame_rect' in event.dict['ui_elements']:
                frame_rect = event.dict['ui_elements']['frame_rect']
            else:
                h, w = frame_image.shape[:2]
                window_w, window_h = screen.get_size()
                scale = min(window_w / w, (window_h - 200) / h)
                new_w, new_h = int(w * scale), int(h * scale)
                x = (window_w - new_w) // 2
                y = (window_h - new_h - 150) // 2
                frame_rect = (x, y, new_w, new_h)
                
        if frame_rect:
            # Convert mouse position to video coordinates
            x, y, w, h = frame_rect
            rel_x = (event.pos[0] - x) / w
            rel_y = (event.pos[1] - y) / h
            
            rel_x = max(0, min(1, rel_x))
            rel_y = max(0, min(1, rel_y))
            
            video_x = int(rel_x * frame_image.shape[1])
            video_y = int(rel_y * frame_image.shape[0])
            
            # Update crop rectangle size
            width = video_x - crop_start_pos[0]
            height = video_y - crop_start_pos[1]
            
            # Handle negative dimensions (dragging up/left)
            if width < 0:
                crop_rect.x = video_x
                crop_rect.width = abs(width)
            else:
                crop_rect.x = crop_start_pos[0]
                crop_rect.width = width
                
            if height < 0:
                crop_rect.y = video_y
                crop_rect.height = abs(height)
            else:
                crop_rect.y = crop_start_pos[1]
                crop_rect.height = height
    
    # Finalize crop rectangle on mouse release
    elif event.type == pygame.MOUSEBUTTONUP and creating_crop and crop_mode == "creating":
        creating_crop = False
        crop_mode = "adjusting"  # Switch to adjustment mode
        
        # Ensure minimum size
        if crop_rect.width < 50:
            crop_rect.width = 50
        if crop_rect.height < 50:
            crop_rect.height = 50

def handle_crop_keyboard_events(event):
    """Handle keyboard events for crop mode"""
    global crop_mode, state
    
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_RETURN:
            # ENTER key confirms and moves to timeline
            state = "timeline"
            should_render_frame = True
        elif event.key == pygame.K_ESCAPE:
            # ESC cancels current operation and resets to ready mode
            crop_mode = "ready"

def run_interface():
    """Run the interface and return when complete"""
    try:
        # Always start fresh
        if os.path.exists("interface_config.json"):
            os.remove("interface_config.json")
        
        main()
        return True
    except Exception as e:
        print(f"Interface error: {e}")
        return False
    
def is_mouse_over_button(button_rect, mouse_pos):
    """Check if mouse is over a button"""
    return button_rect.collidepoint(mouse_pos)

    # Add these functions to your interface.py file, replacing the existing versions

def render_frame():
    """Render the current frame as a background layer"""
    global should_render_frame
    if frame_image is not None and should_render_frame:
        # Get video dimensions
        h, w = frame_image.shape[:2]
        
        # Calculate scaling to fit screen
        window_w, window_h = screen.get_size()
        scale = min(window_w / w, (window_h - 200) / h)
        new_w, new_h = int(w * scale), int(h * scale)
        
        # Center the frame
        x = (window_w - new_w) // 2
        y = (window_h - new_h - 150) // 2
        
        # Create surface from numpy array
        scaled_frame = cv2.resize(frame_image, (new_w, new_h))
        surface = pygame.surfarray.make_surface(scaled_frame.transpose(1, 0, 2))
        
        # Blit directly to screen (as background)
        screen.blit(surface, (x, y))
        
        return (x, y, new_w, new_h)
    return None

def draw_ui_layers():
    """Draw all UI elements as separate layers on top of the video frame"""
    global state, window_size
    mouse_pos = pygame.mouse.get_pos()
    frame_rect = None
    
    if should_render_frame:
        frame_rect = render_frame()
    
    # Now draw UI layers on top based on current state
    if state == "title":
        # Draw semi-transparent overlay for text visibility
        overlay = pygame.Surface((window_size[0], window_size[1]), pygame.SRCALPHA)
        overlay.fill((20, 20, 20, 200))
        screen.blit(overlay, (0, 0))
        
        title_text = TITLE_FONT.render("Conducting Movement Detection", True, TEXT_COLOR)
        screen.blit(title_text, (window_size[0]//2 - title_text.get_width()//2, window_size[1]//4))
        
        start_btn = draw_button("Start", window_size[0]//2 - 100, window_size[1]//2 - 50, 200, 50, 
                              hover=is_mouse_over_button(pygame.Rect(window_size[0]//2 - 100, window_size[1]//2 - 50, 200, 50), mouse_pos))
        
        record_btn = draw_button("Record Video", window_size[0]//2 - 100, window_size[1]//2 + 20, 200, 50, 
                               hover=is_mouse_over_button(pygame.Rect(window_size[0]//2 - 100, window_size[1]//2 + 20, 200, 50), mouse_pos))
        
        return {'start_btn': start_btn, 'record_btn': record_btn}
    
    elif state == "recording":
        overlay = pygame.Surface((window_size[0], window_size[1]), pygame.SRCALPHA)
        overlay.fill((20, 20, 20, 200))
        screen.blit(overlay, (0, 0))
        
        return {'stop_btn': draw_recording_interface()}
    
    elif state == "upload":
        overlay = pygame.Surface((window_size[0], window_size[1]), pygame.SRCALPHA)
        overlay.fill((20, 20, 20, 200))
        screen.blit(overlay, (0, 0))
        
        upload_btn = draw_button("Select Video", window_size[0]//2 - 100, window_size[1]//3, 200, 50,
                              hover=is_mouse_over_button(pygame.Rect(window_size[0]//2 - 100, window_size[1]//3, 200, 50), mouse_pos))
        
        buttons = {'upload_btn': upload_btn}
        
        if video_path:
            # Create a background panel for the text
            path_panel = pygame.Rect(window_size[0]//2 - 250, window_size[1]//3 + 60, 500, 40)
            pygame.draw.rect(screen, (40, 40, 40), path_panel, border_radius=5)
            
            path_text = FONT.render(f"Selected: {os.path.basename(video_path)}", True, TEXT_COLOR)
            screen.blit(path_text, (window_size[0]//2 - path_text.get_width()//2, window_size[1]//3 + 70))
            
            next_btn = draw_button("Next", window_size[0]//2 - 100, window_size[1]//2 + 50, 200, 50,
                                hover=is_mouse_over_button(pygame.Rect(window_size[0]//2 - 100, window_size[1]//2 + 50, 200, 50), mouse_pos))
            buttons['next_btn'] = next_btn
        
        # Add settings button
        settings_btn = draw_button("Settings", window_size[0] - 120, 20, 100, 40,
                               hover=is_mouse_over_button(pygame.Rect(window_size[0] - 120, 20, 100, 40), mouse_pos))
        buttons['settings_btn'] = settings_btn
        
        return buttons
    
    elif state == "crop":
        # Draw crop rectangle (after frame but before UI)
        if frame_rect:
            x, y, w, h = frame_rect
            
            # Calculate crop rect in screen coordinates
            rel_x = crop_rect.x / frame_image.shape[1]
            rel_y = crop_rect.y / frame_image.shape[0]
            rel_w = crop_rect.width / frame_image.shape[1]
            rel_h = crop_rect.height / frame_image.shape[0]
            
            screen_crop = pygame.Rect(
                x + rel_x * w,
                y + rel_y * h,
                rel_w * w,
                rel_h * h
            )
            
            # Draw the crop rectangle
            pygame.draw.rect(screen, (255, 0, 0), screen_crop, 2)
            
            # Draw handles at the corners and edges
            handle_size = 10
            handles = [
                (screen_crop.left, screen_crop.top),                 # top-left
                (screen_crop.left + screen_crop.width//2, screen_crop.top),    # top-center
                (screen_crop.right, screen_crop.top),                # top-right
                (screen_crop.left, screen_crop.top + screen_crop.height//2),   # middle-left
                (screen_crop.right, screen_crop.top + screen_crop.height//2),  # middle-right
                (screen_crop.left, screen_crop.bottom),              # bottom-left
                (screen_crop.left + screen_crop.width//2, screen_crop.bottom), # bottom-center
                (screen_crop.right, screen_crop.bottom)              # bottom-right
            ]
            
            for handle_x, handle_y in handles:
                pygame.draw.rect(screen, (255, 0, 0), 
                              (handle_x - handle_size//2, handle_y - handle_size//2, handle_size, handle_size))
        
        # Draw UI elements
        confirm_btn = draw_button("Confirm Crop", window_size[0]//2 - 100, window_size[1] - 70, 200, 50,
                               hover=is_mouse_over_button(pygame.Rect(window_size[0]//2 - 100, window_size[1] - 70, 200, 50), mouse_pos))
        
        settings_btn = draw_button("Settings", window_size[0] - 120, 20, 100, 40,
                               hover=is_mouse_over_button(pygame.Rect(window_size[0] - 120, 20, 100, 40), mouse_pos))
        
        # Draw instructions with semi-transparent background
        draw_crop_instructions()
        
        return {'confirm_btn': confirm_btn, 'settings_btn': settings_btn, 'frame_rect': frame_rect}
    
    elif state == "timeline":
        # Create a semi-transparent top panel for info
        top_panel = pygame.Surface((window_size[0], 90), pygame.SRCALPHA)
        top_panel.fill((20, 20, 20, 220))
        screen.blit(top_panel, (0, 0))
        
        # Draw instructions
        timeline_text = FONT.render("Select video segments to process", True, TEXT_COLOR)
        screen.blit(timeline_text, (window_size[0]//2 - timeline_text.get_width()//2, 20))
        
        frame_info = FONT.render(f"Frame: {current_frame} / {total_frames}", True, TEXT_COLOR)
        screen.blit(frame_info, (window_size[0]//2 - frame_info.get_width()//2, 50))
        
        # Create a semi-transparent bottom panel for controls
        bottom_panel = pygame.Surface((window_size[0], 150), pygame.SRCALPHA)
        bottom_panel.fill((20, 20, 20, 220))
        screen.blit(bottom_panel, (0, window_size[1] - 150))
        
        # Draw status panel
        status_panel = pygame.Surface((500, 60), pygame.SRCALPHA)
        status_panel.fill((40, 40, 40, 220))
        screen.blit(status_panel, (window_size[0]//2 - 250, window_size[1] - 210))
        
        # Draw marker count and instructions
        process_status = "Currently recording process segment" if currently_processing else "Ready to record process segment"
        status_color = GREEN_COLOR if currently_processing else TEXT_COLOR
        status_text = FONT.render(process_status, True, status_color)
        screen.blit(status_text, (window_size[0]//2 - status_text.get_width()//2, window_size[1] - 200))
        
        count_text = FONT.render(f"Processing segments: {len(process_markers)}", True, TEXT_COLOR)
        screen.blit(count_text, (window_size[0]//2 - count_text.get_width()//2, window_size[1] - 180))
        
        # Draw playback controls
        buttons = {}
        
        control_y = window_size[1] - 140  # Adjusted for better positioning
        play_btn = draw_button("▶ Play" if not is_playing else "⏸ Pause", 
                            window_size[0]//2 - 250, control_y, 120, 40,
                            hover=is_mouse_over_button(pygame.Rect(window_size[0]//2 - 250, control_y, 120, 40), mouse_pos))
        buttons['play_btn'] = play_btn
        
        # Draw process controls
        start_process_btn = draw_button("Start Processing", 
                                      window_size[0]//2 - 60, control_y, 150, 40,
                                      hover=is_mouse_over_button(pygame.Rect(window_size[0]//2 - 60, control_y, 150, 40), mouse_pos),
                                      active=currently_processing)
        buttons['start_process_btn'] = start_process_btn
        
        stop_process_btn = draw_button("Stop Processing", 
                                     window_size[0]//2 + 100, control_y, 150, 40,
                                     hover=is_mouse_over_button(pygame.Rect(window_size[0]//2 + 100, control_y, 150, 40), mouse_pos),
                                     color=RED_COLOR)
        buttons['stop_process_btn'] = stop_process_btn
        
        # Draw slider for timeline navigation
        slider_rect = draw_slider(100, window_size[1] - 100, window_size[0] - 200, 20, current_frame, total_frames)
        buttons['slider_rect'] = slider_rect
        
        # Draw additional controls
        next_btn = draw_button("Next", window_size[0] - 120, window_size[1] - 70, 100, 50,
                            hover=is_mouse_over_button(pygame.Rect(window_size[0] - 120, window_size[1] - 70, 100, 50), mouse_pos))
        buttons['next_btn'] = next_btn
        
        clear_btn = draw_button("Clear Markers", 20, window_size[1] - 70, 150, 50,
                             hover=is_mouse_over_button(pygame.Rect(20, window_size[1] - 70, 150, 50), mouse_pos))
        buttons['clear_btn'] = clear_btn
        
        new_crop_btn = draw_button("New Crop", 180, window_size[1] - 70, 150, 50,
                                hover=is_mouse_over_button(pygame.Rect(180, window_size[1] - 70, 150, 50), mouse_pos))
        buttons['new_crop_btn'] = new_crop_btn
        
        # Add settings button
        settings_btn = draw_button("Settings", window_size[0] - 120, 20, 100, 40,
                               hover=is_mouse_over_button(pygame.Rect(window_size[0] - 120, 20, 100, 40), mouse_pos))
        buttons['settings_btn'] = settings_btn
        
        return buttons
    
    elif state == "export":
        # Draw semi-transparent overlay for text visibility
        overlay = pygame.Surface((window_size[0], window_size[1]), pygame.SRCALPHA)
        overlay.fill((20, 20, 20, 220))
        screen.blit(overlay, (0, 0))
        
        export_text = TITLE_FONT.render("Select export location", True, TEXT_COLOR)
        screen.blit(export_text, (window_size[0]//2 - export_text.get_width()//2, window_size[1]//4))
        
        # Create a background panel for the path info
        path_panel = pygame.Rect(window_size[0]//2 - 350, window_size[1]//3 - 5, 700, 40)
        pygame.draw.rect(screen, (40, 40, 40), path_panel, border_radius=5)
        
        path_info = FONT.render(f"Current: {export_path}", True, TEXT_COLOR)
        screen.blit(path_info, (window_size[0]//2 - path_info.get_width()//2, window_size[1]//3))
        
        # Display summary of processing segments
        summary_text = FONT.render(f"Processing {len(process_markers)} video segment(s)", True, TEXT_COLOR)
        screen.blit(summary_text, (window_size[0]//2 - summary_text.get_width()//2, window_size[1]//3 + 60))
        
        browse_btn = draw_button("Browse", window_size[0]//2 - 100, window_size[1]//2, 200, 50,
                              hover=is_mouse_over_button(pygame.Rect(window_size[0]//2 - 100, window_size[1]//2, 200, 50), mouse_pos))
        
        finish_btn = draw_button("Finish & Process", window_size[0]//2 - 100, window_size[1]//2 + 100, 200, 50,
                              hover=is_mouse_over_button(pygame.Rect(window_size[0]//2 - 100, window_size[1]//2 + 100, 200, 50), mouse_pos))
        
        # Add settings button
        settings_btn = draw_button("Settings", window_size[0] - 120, 20, 100, 40,
                               hover=is_mouse_over_button(pygame.Rect(window_size[0] - 120, 20, 100, 40), mouse_pos))
        
        return {'browse_btn': browse_btn, 'finish_btn': finish_btn, 'settings_btn': settings_btn}
    
    return {}

def main():
    """Main application loop"""
    global state, current_frame, resizing, resize_edge, process_markers, dragging, drag_start
    global is_playing, last_frame_time, currently_processing, process_start_frame
    global video_path, export_path, window_size, show_menu, crop_rect, should_render_frame
    global is_recording
    
    # Reset state to ensure fresh start
    state = "title"
    video_path = ""
    export_path = "output"
    process_markers = []
    
    # Update window size for calculations
    window_size = screen.get_size()
    
    clock = pygame.time.Clock()
    
    # Main loop
    running = True
    while running:
        # Update rendering state at the beginning of each frame
        update_render_state()
        
        # Clear the screen at the beginning of each frame
        screen.fill(BG_COLOR)
        mouse_pos = pygame.mouse.get_pos()
        
        # Handle playback if video is playing
        if is_playing and cap and state == "timeline":
            current_time = time.time()
            if current_time - last_frame_time >= frame_display_time:
                current_frame += 1
                if current_frame >= total_frames:
                    current_frame = 0
                    is_playing = False
                display_specific_frame(current_frame)
                last_frame_time = current_time
        
        # Draw UI layers based on state
        ui_elements = draw_ui_layers()
        
        # Draw menu if active (should be the top-most layer)
        menu_elements = {}
        if show_menu:
            menu_elements = draw_menu()
        
        # Event handling
        for event in pygame.event.get():
            # Add ui_elements to the event for crop handling
            if not hasattr(event, 'dict'):
                event.dict = {}
            event.dict['ui_elements'] = ui_elements
            
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if show_menu:
                    menu_checkboxes = menu_elements.get('checkboxes', {})
                    # Handle menu interactions
                    for option, rect in menu_checkboxes.items():
                        if rect.collidepoint(mouse_pos):
                            processing_options[option] = not processing_options[option]
                    
                    if menu_elements.get('close_btn') and menu_elements['close_btn'].collidepoint(mouse_pos):
                        show_menu = False
                        # Restore frame rendering state based on current state
                        update_render_state()
                    
                    # Skip other button processing when menu is open
                    continue
                
                if state == "title":
                    if 'start_btn' in ui_elements and ui_elements['start_btn'].collidepoint(mouse_pos):
                        state = "upload"
                        should_render_frame = False
                    elif 'record_btn' in ui_elements and ui_elements['record_btn'].collidepoint(mouse_pos):
                        if start_recording():
                            state = "recording"
                            should_render_frame = False
                
                elif state == "recording":
                    if 'stop_btn' in ui_elements and ui_elements['stop_btn'].collidepoint(mouse_pos):
                        if stop_recording():
                            state = "crop"
                            should_render_frame = True
                
                elif state == "upload":
                    if 'upload_btn' in ui_elements and ui_elements['upload_btn'].collidepoint(mouse_pos):
                        if select_video():
                            display_specific_frame(0)  # Show the first frame
                    
                    elif video_path and 'next_btn' in ui_elements and ui_elements['next_btn'].collidepoint(mouse_pos):
                        state = "crop"
                        should_render_frame = True
                        
                    # Handle settings button
                    elif 'settings_btn' in ui_elements and ui_elements['settings_btn'].collidepoint(mouse_pos):
                        show_menu = True
                        should_render_frame = False
                
                elif state == "crop":
                    if 'confirm_btn' in ui_elements and ui_elements['confirm_btn'].collidepoint(mouse_pos):
                        state = "timeline"
                        should_render_frame = True
                    elif 'settings_btn' in ui_elements and ui_elements['settings_btn'].collidepoint(mouse_pos):
                        show_menu = True
                        should_render_frame = False
                    elif 'frame_rect' in ui_elements and ui_elements['frame_rect']:
                        if crop_mode == "adjusting":
                            # Check if attempting to resize or drag crop rectangle
                            resize_edge = get_resize_edge(mouse_pos, ui_elements['frame_rect'])
                            if resize_edge == "middle":
                                # Dragging the crop rectangle
                                dragging = True
                                
                                # Convert mouse pos to video coordinates for drag handling
                                x, y, w, h = ui_elements['frame_rect']
                                rel_mouse_x = (mouse_pos[0] - x) / w
                                rel_mouse_y = (mouse_pos[1] - y) / h
                                rel_mouse_x = max(0, min(1, rel_mouse_x))
                                rel_mouse_y = max(0, min(1, rel_mouse_y))
                                
                                drag_start = (int(rel_mouse_x * frame_image.shape[1]), 
                                            int(rel_mouse_y * frame_image.shape[0]))
                            elif resize_edge:
                                resizing = True
                        # Pass to crop creation handler
                        handle_crop_creation(event)
                
                elif state == "timeline":
                    # Playback controls
                    if 'play_btn' in ui_elements and ui_elements['play_btn'].collidepoint(mouse_pos):
                        is_playing = not is_playing
                        last_frame_time = time.time()
                    
                    # Process control buttons
                    elif 'start_process_btn' in ui_elements and ui_elements['start_process_btn'].collidepoint(mouse_pos) and not currently_processing:
                        currently_processing = True
                        process_start_frame = current_frame
                        
                    elif 'stop_process_btn' in ui_elements and ui_elements['stop_process_btn'].collidepoint(mouse_pos) and currently_processing:
                        currently_processing = False
                        if process_start_frame is not None and current_frame > process_start_frame:
                            # Store current crop rectangle with process marker
                            current_crop = pygame.Rect(crop_rect)
                            process_markers.append((process_start_frame, current_frame))
                            process_start_frame = None
                    
                    # Settings button
                    elif 'settings_btn' in ui_elements and ui_elements['settings_btn'].collidepoint(mouse_pos):
                        show_menu = True
                        should_render_frame = False
                    
                    # New crop button - return to crop state to define a new region
                    elif 'new_crop_btn' in ui_elements and ui_elements['new_crop_btn'].collidepoint(mouse_pos):
                        state = "crop"
                        should_render_frame = True
                    
                    # Navigation buttons
                    elif 'next_btn' in ui_elements and ui_elements['next_btn'].collidepoint(mouse_pos):
                        # Finalize any ongoing processing
                        if currently_processing and process_start_frame is not None:
                            current_crop = pygame.Rect(crop_rect)
                            process_markers.append((process_start_frame, current_frame))
                        state = "export"
                        should_render_frame = False
                    
                    elif 'clear_btn' in ui_elements and ui_elements['clear_btn'].collidepoint(mouse_pos):
                        process_markers = []
                        currently_processing = False
                        process_start_frame = None
                    
                    # Handle timeline slider clicks
                    elif 'slider_rect' in ui_elements and ui_elements['slider_rect'].collidepoint(mouse_pos):
                        rel_x = (mouse_pos[0] - 100) / (window_size[0] - 200)
                        new_frame = int(rel_x * total_frames)
                        current_frame = max(0, min(new_frame, total_frames - 1))
                        display_specific_frame(current_frame)
                
                elif state == "export":
                    if 'browse_btn' in ui_elements and ui_elements['browse_btn'].collidepoint(mouse_pos):
                        select_export_path()
                    
                    elif 'finish_btn' in ui_elements and ui_elements['finish_btn'].collidepoint(mouse_pos):
                        save_config()
                        running = False
                    
                    elif 'settings_btn' in ui_elements and ui_elements['settings_btn'].collidepoint(mouse_pos):
                        show_menu = True
                        should_render_frame = False
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if state == "crop" and creating_crop:
                    handle_crop_creation(event)
                resizing = False
                dragging = False
                drag_start = None 
            elif event.type == pygame.KEYDOWN:
                if state == "crop":
                    handle_crop_keyboard_events(event)
            elif event.type == pygame.MOUSEMOTION:
                # Only perform frame-related operations if we should be showing frames
                if state == "crop" and should_render_frame:
                    # Only handle crop creation if we're actively creating a crop
                    if creating_crop and crop_mode == "creating":
                        handle_crop_creation(event)
                    # Handle crop rectangle resizing or dragging when in adjustment mode
                    elif 'frame_rect' in ui_elements and (resizing or dragging) and crop_mode == "adjusting":
                        if resizing and resize_edge:
                            update_crop_rect(mouse_pos, ui_elements['frame_rect'], resize_edge)
                        elif dragging and drag_start:
                            new_drag_start = update_crop_rect(mouse_pos, ui_elements['frame_rect'], "middle", dragging=True)
                            if new_drag_start:
                                drag_start = new_drag_start
                
                # Handle timeline slider dragging
                elif state == "timeline" and event.buttons[0] and 'slider_rect' in ui_elements and ui_elements['slider_rect'].collidepoint(mouse_pos):
                    rel_x = (mouse_pos[0] - 100) / (window_size[0] - 200)
                    new_frame = int(rel_x * total_frames)
                    current_frame = max(0, min(new_frame, total_frames - 1))
                    display_specific_frame(current_frame)
            
            elif event.type == pygame.VIDEORESIZE:
                # Update window size
                window_size = (event.w, event.h)
        
        pygame.display.flip()
        clock.tick(60)
    
    # Clean up
    if cap:
        cap.release()
    
    # Return without quitting pygame so other modules can use it
    return