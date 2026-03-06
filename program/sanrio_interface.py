import pygame
import os
import sys
import cv2
import numpy as np
import json
import time
import tkinter as tk
import platform
import threading
from tkinter import filedialog

# Add these at the beginning of the file, after the imports but before class definitions:

# Global variables for external functions
pygame_initialized = False
pygame_screen = None
pygame_window_size = (800, 600)

# Initialize pygame if needed
def ensure_pygame_initialized():
    """Initialize pygame if not already initialized and return the screen and window size"""
    global pygame_initialized, pygame_screen, pygame_window_size
    if not pygame_initialized:
        # Check if pygame is initialized first
        if not pygame.get_init():
            pygame.init()
        
        # Set pygame_initialized to True after initialization
        pygame_initialized = True
        
        # Check if a window already exists
        existing_surface = pygame.display.get_surface()
        if existing_surface is not None:
            pygame_screen = existing_surface
            pygame_window_size = pygame_screen.get_size()
        else:
            # Get display info for fullscreen mode
            info = pygame.display.Info()
            pygame_window_size = (info.current_w, info.current_h)  # Full screen dimensions
            
            # Try to create a new window with FULLSCREEN flag
            try:
                pygame_screen = pygame.display.set_mode(pygame_window_size, pygame.FULLSCREEN)
                pygame.display.set_caption("Conducting Movement Analysis - Sanrio Edition")
            except pygame.error as e:
                print(f"Error setting fullscreen mode: {e}")
                # Fallback to a resizable window
                try:
                    pygame_window_size = (min(1024, info.current_w), min(768, info.current_h))
                    pygame_screen = pygame.display.set_mode(pygame_window_size, pygame.RESIZABLE)
                    pygame.display.set_caption("Conducting Movement Analysis - Sanrio Edition")
                except pygame.error as e:
                    print(f"Error setting resizable mode: {e}")
                    # Final fallback to a simpler display mode
                    try:
                        pygame_screen = pygame.display.set_mode(pygame_window_size)
                        pygame.display.set_caption("Conducting Movement Analysis - Sanrio Edition")
                    except pygame.error as e:
                        print(f"Critical error: Could not create Pygame display: {e}")
                        return None, pygame_window_size
    
    # Verify that the screen is valid
    if pygame_screen is None or not pygame.display.get_init():
        # Try to reinitialize
        try:
            pygame.init()
            pygame_screen = pygame.display.set_mode(pygame_window_size, pygame.FULLSCREEN)  # Try fullscreen first
            if pygame_screen is None:  # If still None, try regular mode
                pygame_screen = pygame.display.set_mode(pygame_window_size)
        except pygame.error:
            print("Error: Could not reinitialize Pygame display")
    
    return pygame_screen, pygame_window_size
# External API functions for other modules
def get_screen():
    """Returns the pygame screen object for external modules"""
    global pygame_screen
    screen, _ = ensure_pygame_initialized()
    return screen

def get_window_size():
    """Returns the current window size for external modules"""
    global pygame_window_size
    _, window_size = ensure_pygame_initialized()
    return window_size

def display_frame(frame):
    """Display a frame for external modules"""
    global pygame_screen
    
    # Ensure pygame is initialized
    screen, _ = ensure_pygame_initialized()
    
    if frame is None or screen is None:
        print("Warning: Could not display frame in PyGame window: frame or screen is None")
        return False
    
    try:
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
            
            # Verify that display is still valid before updating
            if pygame.display.get_init():
                pygame.display.flip()
                return True
            else:
                print("Warning: Could not update PyGame display: Display not initialized")
                return False
    except (pygame.error, TypeError, ValueError) as e:
        print(f"Error displaying frame: {e}")
        return False
    
    return False


# Define a utility function to scale assets
def scale_asset_to_fit(asset, target_width, target_height):
    """Scale an asset to fit within the target dimensions while maintaining aspect ratio."""
    asset_w, asset_h = asset.get_size()
    scale_w = target_width / asset_w
    scale_h = target_height / asset_h
    scale = min(scale_w, scale_h)
    return pygame.transform.scale(asset, (int(asset_w * scale), int(asset_h * scale)))

# Define a theme manager to handle the Sanrio theme assets
class ThemeManager:
    def __init__(self, base_path="theme_assets/moe-mode"):
        self.base_path = base_path
        self.assets = {}
        self.fonts = {}
        self.colors = {
            "bg_color": (255, 230, 245),  # Light pink background
            "text_color": (218, 93, 157), #Pink text
            "highlight_color": (255, 100, 150),  # Bright pink highlight
            "button_color": (255, 200, 220),  # Light pink buttons
            "border_color": (255, 170, 200),  # Medium pink border
            "panel_color": (255, 240, 250, 220)  # Semi-transparent panel
        }
        
        # Load necessary assets
        self.load_assets()
        self.load_fonts()
    
    def load_assets(self):
        """Load all theme assets from the asset directory"""
        try:
            # Main UI elements
            self.assets["background"] = self.load_image("Background_Picture.png")
            self.assets["title"] = self.load_image("Conducting_analysis.png")
            self.assets["next_button"] = self.load_image("Next_Button.png")
            self.assets["settings_button"] = self.load_image("Settings_button.png")
            
            # Button assets
            self.assets["upload_button"] = self.load_image("Upload_button.png")
            self.assets["record_button"] = self.load_image("Record_button.png")
            self.assets["browse_button"] = self.load_image("Browse_button.png")
            self.assets["finish_button"] = self.load_image("Finish_button.png")
            self.assets["stop_button"] = self.load_image("Stop_button.png")
            self.assets["play_button"] = self.load_image("Play_button.png")
            self.assets["crop_button"] = self.load_image("Crop_button.png")
            self.assets["select_video"] = self.load_image("Select_Video_button.png")
            self.assets["back_arrow"] = self.load_image("back_arrow.png", with_alpha=True)
            self.assets["timeline_instructions"] = self.load_image("Instructions_panel.png", with_alpha=True)
            
            # Frame and UI decoration elements
            self.assets["frame_border"] = self.load_image("Processing_Video_Border.png", with_alpha=True)
            self.assets["crop_frame_border"] = self.load_image("Crop_Video_Border.png", with_alpha=True)    
            self.assets["crop_selector"] = self.load_image("Crop_selector.png", with_alpha=True)
            self.assets["instructions_panel"] = self.load_image("Instructions_panel.png", with_alpha=True)
            self.assets["settings_menu_bg"] = self.load_image("Settings_menu_BG.png", with_alpha=True)
            self.assets["rec_frame"] = self.load_image("recording_border.png", with_alpha=True)

            
            # Special UI elements
            self.assets["flag_icon"] = self.load_image("flag_icon.png", with_alpha=True)
            self.assets["x_icon"] = self.load_image("x_icon.png", with_alpha=True)
            self.assets["melody_icon"] = self.load_image("Icon-w-segments-text.png", with_alpha=True)
            self.assets["recording_text"] = self.load_image("recording_text.png", with_alpha=True)
            
            # Progress elements
            self.assets["heart_slider"] = self.load_image("Playback_scrubber.png", with_alpha=True)
            
            # Headers and text elements
            self.assets["graph_options"] = self.load_image("graph_options.png", with_alpha=True)
            self.assets["export_location_text"] = self.load_image("select_export_location.png", with_alpha=True)
            self.assets["save_close"] = self.load_image("Save_Close_button.png", with_alpha=True)
            self.assets["folder_icon"] = self.load_image("folder_icon.png", with_alpha=True) if os.path.exists(os.path.join(self.base_path, "folder_icon.png")) else None
        except Exception as e:
            print(f"Error loading assets: {e}")
        
    def load_image(self, filename, with_alpha=False):
        """Load an image from the theme directory"""
        path = os.path.join(self.base_path, filename)
        try:
            if with_alpha:
                return pygame.image.load(path).convert_alpha()
            else:
                image = pygame.image.load(path)
                return image.convert() if image.get_alpha() is None else image.convert_alpha()
        except (pygame.error, FileNotFoundError) as e:
            print(f"Error loading image {filename}: {e}")
            # Create a placeholder surface
            placeholder = pygame.Surface((200, 50))
            placeholder.fill((255, 100, 150))
            return placeholder
    
    def load_fonts(self):
        """Load custom fonts for the Sanrio theme"""
        try:
            # Check if the Believer font is available in the system
            available_fonts = os.path.join(self.base_path, "fonts", "Believer-DEMO.otf")

            
            # Default font sizes based on your image
            title_size = 48
            main_size = 32
            small_size = 24
            
            loker_path = os.path.join(self.base_path, "fonts", "Loker.otf")
            self.fonts["title"] = pygame.font.Font(loker_path, title_size)
            self.fonts["main_secondary"] = pygame.font.Font(loker_path, small_size)
            if "believer" in available_fonts:
                # Use Believer font if it's available in the system
                self.fonts["title_secondary"] = pygame.font.Font("believer", title_size)
                self.fonts["main"] = pygame.font.SysFont("believer", main_size)
                self.fonts["small"] = pygame.font.SysFont("believer", small_size)
            else:
                # Try to load Believer from a font file
                try:
                    believer_path = os.path.join(self.base_path, "fonts", "Believer-DEMO.otf")
                    if os.path.exists(believer_path):
                        self.fonts["title_secondary"] = pygame.font.Font(believer_path, title_size)
                        self.fonts["main"] = pygame.font.Font(believer_path, main_size)
                        self.fonts["small"] = pygame.font.Font(believer_path, small_size)
                    else:
                        # Fallback to system fonts with similar appearance
                        self.fonts["title"] = pygame.font.SysFont("arial", title_size, bold=True)
                        self.fonts["main"] = pygame.font.SysFont("arial", main_size)
                        self.fonts["small"] = pygame.font.SysFont("arial", small_size)
                except Exception as e:
                    print(f"Error loading Believer font: {e}")
                    # Fallback to system fonts
                    self.fonts["title"] = pygame.font.SysFont("arial", title_size, bold=True)
                    self.fonts["main"] = pygame.font.SysFont("arial", main_size)
                    self.fonts["small"] = pygame.font.SysFont("arial", small_size)
        except Exception as e:
            print(f"Error loading fonts: {e}")
            # Ultimate fallback
            self.fonts["title"] = pygame.font.SysFont(None, title_size)
            self.fonts["main"] = pygame.font.SysFont(None, main_size)
            self.fonts["small"] = pygame.font.SysFont(None, small_size)

    def create_text_surface(self, text, font_name="main", color=None):
        """Create a text surface with the theme's font and colors"""
        if color is None:
            color = self.colors["text_color"]
        font = self.fonts.get(font_name, self.fonts["main"])
        return font.render(text, True, color)
    
    def draw_theme_button(self, screen, button_asset, x, y, scale=1.0, hover=False, hover_padding=20):
        """Draw a themed button with the specified asset and consistent hover behavior"""
        asset = self.assets.get(button_asset)
        if asset is None:
            # Fallback if asset not found
            rect = pygame.Rect(x, y, 150 * scale, 50 * scale)
            pygame.draw.rect(screen, self.colors["button_color"], rect, border_radius=10)
            if hover:
                pygame.draw.rect(screen, self.colors["highlight_color"], rect, width=3, border_radius=10)
            return rect
        
        # Scale the asset if needed
        if scale != 1.0:
            width, height = asset.get_size()
            asset = pygame.transform.scale(asset, (int(width * scale), int(height * scale)))
        
        # Get button dimensions
        button_width, button_height = asset.get_size()
        
        # Draw the button
        screen.blit(asset, (x, y))
        rect = pygame.Rect(x, y, button_width, button_height)
        
        # Add hover effect if needed
        if hover:
            pygame.draw.rect(screen, self.colors["highlight_color"], rect, width=3, border_radius=10)
        
        # Return the expanded hover rect instead of just the button rect
        hover_rect = pygame.Rect(
            x - hover_padding,
            y - hover_padding,
            button_width + 2 * hover_padding,
            button_height + 2 * hover_padding
        )
        
        return hover_rect
        # Fix the record page functionality - camera display and stop button:
    
# Enhanced Interface class that incorporates the Sanrio theme
class SanrioInterface:
    def __init__(self):
        # Initialize pygame and create window
        if not pygame.get_init():
            pygame.init()
        
        # Get display info for window sizing
        info = pygame.display.Info()
        self.window_size = (info.current_w, info.current_h)  # Use full screen dimensions
        try:
            # Initialize in fullscreen mode
            self.screen = pygame.display.set_mode(self.window_size, pygame.FULLSCREEN)
            pygame.display.set_caption("Conducting Movement Analysis - Moe Mode")
        except pygame.error as e:
            print(f"Error creating fullscreen display: {e}")
            # Try a fallback display mode - still try to get as big as possible
            try:
                self.screen = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
                pygame.display.set_caption("Conducting Movement Analysis - Moe Mode")
            except pygame.error as e:
                print(f"Error creating resizable display: {e}")
                # Last fallback option
                self.window_size = (min(1024, info.current_w), min(768, info.current_h))
                self.screen = pygame.display.set_mode(self.window_size)
                pygame.display.set_caption("Conducting Movement Analysis - Moe Mode")
        
        # Set up theme manager
        self.theme = ThemeManager()
        
        # State variables (similar to your original interface.py)
        self.state = "title"  # title, upload, recording, crop, timeline, export
        self.video_path = ""
        self.export_path = "output"
        self.cap = None
        self.current_frame = 0
        self.total_frames = 0
        self.frame_image = None
        self.process_markers = []
        self.is_playing = False
        self.last_frame_time = 0
        self.frame_display_time = 1/30
        self.is_recording = False
        self.record_device = None
        self.recording_frames = []
        self.recording_start_time = 0
        
        # New UI state variables for segment selection
        self.cursor_mode = "normal"  # normal, flag, x
        self.selected_segment = None
        self.crop_rect = pygame.Rect(200, 150, 400, 300)
        
        # Flag for completion
        self.completed = False
        
        # Processing options
        self.processing_options = {
            "generate_beat_plot": True,
            "generate_hand_path": True,
            "generate_cluster_graph": True,
            "generate_overtime_graph": True,
            "generate_swaying_graph": True,
            "generate_mirror_x_graph": True,
            "generate_mirror_y_graph": True,
            "export_beat_detection": True,
            # "export_pattern_analysis": True, // removed   
            "detect_motion": True
        }
        
        # Configuration dictionary
        self.config = {
            "video_path": "",
            "export_path": "output",
            "crop_rect": [200, 150, 400, 300],
            "process_markers": [],
            "processing_options": self.processing_options
        }
        
        # Flag for showing settings menu
        self.show_menu = False
        
        # Initialize UI state variables for crop handling
        self.creating_crop = False
        self.crop_start_pos = None
        self.resize_edge = None
        self.dragging = False
        self.drag_start = None
        self.resizing = False
    
    def run(self):
        """Main application loop"""
        clock = pygame.time.Clock()
        running = True
        
        while running:
            # Check if pygame is still running
            if not pygame.display.get_init():
                print("Warning: PyGame display not initialized, attempting to reinitialize")
                try:
                    pygame.init()
                    # Reinitialize in fullscreen mode
                    info = pygame.display.Info()
                    self.window_size = (info.current_w, info.current_h)
                    self.screen = pygame.display.set_mode(self.window_size, pygame.FULLSCREEN)
                except pygame.error:
                    print("Error: Could not reinitialize PyGame display")
                    break
            
            # Handle events
            mouse_pos = pygame.mouse.get_pos()
            events = pygame.event.get()
            
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    # Only handle resize events if not in fullscreen mode
                    if not (pygame.display.get_surface().get_flags() & pygame.FULLSCREEN):
                        self.window_size = (event.w, event.h)
                        self.screen = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
                else:
                    # Process other events based on current state
                    running = self.handle_events(event, mouse_pos)
            
            # Update playback if needed
            if self.is_playing and self.cap and self.state == "timeline":
                current_time = time.time()
                if current_time - self.last_frame_time >= self.frame_display_time:
                    self.current_frame += 1
                    if self.current_frame >= self.total_frames:
                        self.current_frame = 0
                        self.is_playing = False
                    self.display_specific_frame(self.current_frame)
                    self.last_frame_time = current_time
            
            # Draw UI based on current state
            try:
                self.draw_state()
                pygame.display.flip()
            except pygame.error as e:
                print(f"Error drawing UI: {e}")
                # Try to recover by reinitializing the display
                try:
                    # Reinitialize in fullscreen mode
                    info = pygame.display.Info()
                    self.window_size = (info.current_w, info.current_h)
                    self.screen = pygame.display.set_mode(self.window_size, pygame.FULLSCREEN)
                except:
                    print("Critical error: Could not recover display")
                    break
            
            clock.tick(60)
        
        # Clean up resources
        if self.cap:
            self.cap.release()
        
        pygame.quit()
        return self.completed
    def is_button_hovered(self, button_asset, x, y, hover_padding=20):
        """Check if mouse is hovering over a button with padding"""
        asset = self.theme.assets.get(button_asset)
        if asset is None:
            # Default size for fallback
            button_width, button_height = 150, 50
        else:
            button_width, button_height = asset.get_size()
        
        hover_rect = pygame.Rect(
            x - hover_padding,
            y - hover_padding,
            button_width + 2 * hover_padding,
            button_height + 2 * hover_padding
        )
        
        return hover_rect.collidepoint(pygame.mouse.get_pos())

    def handle_events(self, event, mouse_pos):
        """Handle events based on current state"""
        # Add ESC key handling for fullscreen mode
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # If ESC is pressed, toggle between fullscreen and windowed mode
                if pygame.display.get_surface().get_flags() & pygame.FULLSCREEN:
                    # Currently in fullscreen, switch to windowed
                    self.screen = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
                else:
                    # Currently in windowed, switch to fullscreen
                    info = pygame.display.Info()
                    self.window_size = (info.current_w, info.current_h)
                    self.screen = pygame.display.set_mode(self.window_size, pygame.FULLSCREEN)
                return True
        
        if self.show_menu:
            return self.handle_menu_events(event, mouse_pos)
        
        if self.state == "title":
            return self.handle_title_events(event, mouse_pos)
        elif self.state == "upload":
            return self.handle_upload_events(event, mouse_pos)
        elif self.state == "recording":
            return self.handle_recording_events(event, mouse_pos)
        elif self.state == "crop":
            return self.handle_crop_events(event, mouse_pos)
        elif self.state == "timeline":
            return self.handle_timeline_events(event, mouse_pos)
        elif self.state == "export":
            return self.handle_export_events(event, mouse_pos)
        
        return True
    
    def handle_menu_events(self, event, mouse_pos):
        """Handle events when the settings menu is shown"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check if clicked save & close button
            if hasattr(self, "close_btn_rect") and self.close_btn_rect.collidepoint(mouse_pos):
                self.show_menu = False
                return True
            
            # Handle checkbox toggles
            checkboxes = self.get_checkboxes()
            for option, rect in checkboxes.items():
                if rect.collidepoint(mouse_pos):
                    self.processing_options[option] = not self.processing_options[option]
                    return True
        
        return True
    
    def handle_title_events(self, event, mouse_pos):
        """Handle events on the title screen"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Upload button
            if hasattr(self, "upload_btn_rect") and self.upload_btn_rect.collidepoint(mouse_pos):
                self.state = "upload"
                return True
            
            # Record button
            if hasattr(self, "record_btn_rect") and self.record_btn_rect.collidepoint(mouse_pos):
                if self.start_recording():
                    self.state = "recording"
                return True
        
        return True
    
    def handle_upload_events(self, event, mouse_pos):
        """Handle events on the upload screen"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Select video button
            if hasattr(self, "select_btn_rect") and self.select_btn_rect.collidepoint(mouse_pos):
                if self.select_video():
                    self.display_specific_frame(0)
                return True
            
            # Next button (only if video is selected)
            if self.video_path:
                if hasattr(self, "next_btn_rect") and self.next_btn_rect.collidepoint(mouse_pos):
                    self.state = "crop"
                    return True
            
            # Settings button
            if hasattr(self, "settings_btn_rect") and self.settings_btn_rect.collidepoint(mouse_pos):
                self.show_menu = True
                return True
        
        return True
    
    def handle_recording_events(self, event, mouse_pos):
        """Handle events on the recording screen"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Stop recording button
            if hasattr(self, "stop_btn_rect") and self.stop_btn_rect.collidepoint(mouse_pos):
                if self.stop_recording():
                    self.state = "crop"
                return True
        
        return True
    
    def handle_crop_events(self, event, mouse_pos):
        """Handle events on the crop screen"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Confirm crop button
            if hasattr(self, "next_btn_rect") and self.next_btn_rect.collidepoint(mouse_pos):
                self.state = "timeline"
                return True
            
            # Settings button
            if hasattr(self, "settings_btn_rect") and self.settings_btn_rect.collidepoint(mouse_pos):
                self.show_menu = True
                return True
            
            # Handle crop rectangle interaction
            if self.frame_image is not None:
                # Get frame rect
                h, w = self.frame_image.shape[:2]
                scale = min(self.window_size[0] / w, (self.window_size[1] - 200) / h)
                new_w, new_h = int(w * scale), int(h * scale)
                x = (self.window_size[0] - new_w) // 2
                y = (self.window_size[1] - new_h - 150) // 2
                frame_rect = (x, y, new_w, new_h)
                
                # Check if clicking inside the frame
                x, y, w, h = frame_rect
                if x <= mouse_pos[0] <= x + w and y <= mouse_pos[1] <= y + h:
                    # Handle crop rectangle creation/adjustment
                    self.handle_crop_creation(event, frame_rect)
                    return True
        
        elif event.type == pygame.MOUSEMOTION and event.buttons[0]:
            # Handle drag operations for crop rectangle only if mouse button is down
            if self.frame_image is not None and (self.creating_crop or self.dragging or self.resizing):
                # Get frame rect
                h, w = self.frame_image.shape[:2]
                scale = min(self.window_size[0] / w, (self.window_size[1] - 200) / h)
                new_w, new_h = int(w * scale), int(h * scale)
                x = (self.window_size[0] - new_w) // 2
                y = (self.window_size[1] - new_h - 150) // 2
                frame_rect = (x, y, new_w, new_h)
                
                # Update crop rectangle
                self.handle_crop_motion(event, frame_rect)
                return True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            # Reset dragging/resizing state
            self.dragging = False
            self.resizing = False
            self.creating_crop = False
            self.resize_edge = None
            print("Reset drag/resize states")  # Debug
        
        return True
    def handle_timeline_events(self, event, mouse_pos):
        """Handle events on the timeline screen with new segment selection UI"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Mode selection buttons - check these first to ensure they work reliably
            if hasattr(self, "flag_btn_rect") and self.flag_btn_rect.collidepoint(mouse_pos):
                # Toggle flag mode
                if self.cursor_mode == "flag":
                    self.cursor_mode = "normal"
                    print("Flag mode turned OFF")  # Debug print
                else:
                    self.cursor_mode = "flag"
                    print("Flag mode turned ON")  # Debug print
                return True
                
            # NEW - Back arrow button to undo last segment
            if hasattr(self, "back_arrow_rect") and self.back_arrow_rect.collidepoint(mouse_pos):
                if len(self.process_markers) > 0:
                    # Remove the last segment from the list
                    removed_segment = self.process_markers.pop()
                    print(f"Removed segment: {removed_segment[0]} - {removed_segment[1]}")  # Debug print
                return True
                    
            if hasattr(self, "x_btn_rect") and self.x_btn_rect.collidepoint(mouse_pos):
                # Clear all processing markers when X button is clicked
                self.process_markers = []
                self.selected_segment = None  # Also clear any in-progress segment
                self.cursor_mode = "normal"  # Reset cursor mode
                print("All markers cleared")  # Debug print
                return True
            
            # Play/pause button
            if hasattr(self, "play_btn_rect") and self.play_btn_rect.collidepoint(mouse_pos):
                self.is_playing = not self.is_playing
                self.last_frame_time = time.time()
                return True
            
            # Timeline slider interactions
            if hasattr(self, "slider_rect") and self.slider_rect.collidepoint(mouse_pos):
                rel_x = (mouse_pos[0] - 100) / (self.window_size[0] - 200)
                new_frame = int(rel_x * self.total_frames)
                self.current_frame = max(0, min(new_frame, self.total_frames - 1))
                self.display_specific_frame(self.current_frame)
                            
            # Crop button
            if hasattr(self, "crop_btn_rect") and self.crop_btn_rect.collidepoint(mouse_pos):
                self.state = "crop"
                self.cursor_mode = "normal"  # Reset cursor mode when changing screens
                return True
            
            # Next button
            if hasattr(self, "next_btn_rect") and self.next_btn_rect.collidepoint(mouse_pos):
                self.state = "export"
                self.cursor_mode = "normal"  # Reset cursor mode when changing screens
                return True
            
            # Settings button
            if hasattr(self, "settings_btn_rect") and self.settings_btn_rect.collidepoint(mouse_pos):
                self.show_menu = True
                self.cursor_mode = "normal"  # Reset cursor mode when opening menu
                return True
            
            # Check for flag mode actions when clicking anywhere else
            if self.cursor_mode == "flag" and self.frame_image is not None:
                # Handle segment creation when in flag mode
                if self.selected_segment is None:
                    # Starting a new segment
                    self.selected_segment = (self.current_frame, self.current_frame)
                    print(f"Started segment at frame {self.current_frame}")  # Debug print
                else:
                    # Completing a segment
                    start, _ = self.selected_segment
                    end = self.current_frame
                    # Ensure start < end
                    if start > end:
                        start, end = end, start
                    self.process_markers.append((start, end))
                    self.selected_segment = None
                    print(f"Completed segment from {start} to {end}")  # Debug print
                return True
        
        elif event.type == pygame.MOUSEMOTION and event.buttons[0]:
            # Handle timeline slider dragging
            if hasattr(self, "slider_rect") and self.slider_rect.collidepoint(mouse_pos):
                rel_x = (mouse_pos[0] - 100) / (self.window_size[0] - 200)
                new_frame = int(rel_x * self.total_frames)
                self.current_frame = max(0, min(new_frame, self.total_frames - 1))
                self.display_specific_frame(self.current_frame)
                return True
        
        return True
    
    def handle_export_events(self, event, mouse_pos):
        """Handle events on the export screen"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Browse button
            if hasattr(self, "browse_btn_rect") and self.browse_btn_rect.collidepoint(mouse_pos):
                self.select_export_path()
                return True
            
            # Finish button
            if hasattr(self, "finish_btn_rect") and self.finish_btn_rect.collidepoint(mouse_pos):
                self.save_config()
                self.completed = True  # Set completion flag
                return False  # Exit the application
            
            # Settings button
            if hasattr(self, "settings_btn_rect") and self.settings_btn_rect.collidepoint(mouse_pos): 
                self.show_menu = True
                return True
        
        return True
    
    def draw_state(self):
        """Draw UI based on current state"""
        # Clear screen and draw background
        self.screen.fill(self.theme.colors["bg_color"])
        
        # Draw appropriate UI elements based on current state
        if self.state == "title":
            self.draw_title_screen()
        elif self.state == "upload":
            self.draw_upload_screen()
        elif self.state == "recording":
            self.draw_recording_screen()
        elif self.state == "crop":
            self.draw_crop_screen()
        elif self.state == "timeline":
            self.draw_timeline_screen()
        elif self.state == "export":
            self.draw_export_screen()
        
        # Draw settings menu if active
        if self.show_menu:
            self.draw_settings_menu()
    
    def draw_title_screen(self):
        """Draw the title screen with Sanrio theme and enhanced hover effects"""
        # Draw background with pattern
        if "background" in self.theme.assets:
            # Scale and tile the background pattern
            bg = self.theme.assets["background"]
            bg_w, bg_h = bg.get_size()
            for y in range(0, self.window_size[1], bg_h):
                for x in range(0, self.window_size[0], bg_w):
                    self.screen.blit(bg, (x, y))
        
        # Draw title
        if "title" in self.theme.assets:
            title = self.theme.assets["title"]
            title_x = self.window_size[0]//2 - title.get_width()//2
            self.screen.blit(title, (title_x, self.window_size[1]//4))
        else:
            title_text = self.theme.create_text_surface("Conducting Analysis", "title")
            self.screen.blit(title_text, (self.window_size[0]//2 - title_text.get_width()//2, self.window_size[1]//4))
        
        # Upload button
        upload_button_x = self.window_size[0]//2 - 150
        upload_button_y = self.window_size[1]//2 - 30
        
        # Check if mouse is hovering over upload button
        is_upload_hovered = self.is_button_hovered("upload_button", upload_button_x, upload_button_y)
        
        # Draw the upload button with hover effect
        self.upload_btn_rect = self.theme.draw_theme_button(
            self.screen, "upload_button", 
            upload_button_x, upload_button_y,
            hover=is_upload_hovered
        )
        
        # Record button
        record_button_x = self.window_size[0]//2 - 150
        record_button_y = self.window_size[1]//2 + 150
        
        # Check if mouse is hovering over record button
        is_record_hovered = self.is_button_hovered("record_button", record_button_x, record_button_y)
        
        # Draw the record button with hover effect
        self.record_btn_rect = self.theme.draw_theme_button(
            self.screen, "record_button", 
            record_button_x, record_button_y,
            hover=is_record_hovered
        )

    def draw_upload_screen(self):
        """Draw the upload screen with Sanrio theme and enhanced hover effects"""
        # Draw background pattern
        if "background" in self.theme.assets:
            bg = self.theme.assets["background"]
            bg_w, bg_h = bg.get_size()
            for y in range(0, self.window_size[1], bg_h):
                for x in range(0, self.window_size[0], bg_w):
                    self.screen.blit(bg, (x, y))
        
        # Select video button
        select_video_x = self.window_size[0]//2 - 150
        select_video_y = self.window_size[1]//3
        
        # Check if mouse is hovering over select video button
        is_select_video_hovered = self.is_button_hovered("select_video", select_video_x, select_video_y)
        
        # Draw the select video button with hover effect
        self.select_btn_rect = self.theme.draw_theme_button(
            self.screen, "select_video", 
            select_video_x, select_video_y,
            hover=is_select_video_hovered
        )
        
        # If video is selected, show info and next button
        if self.video_path:
            # Draw selected video info
            text = f"Selected video: {os.path.basename(self.video_path)}"
            text_surf = self.theme.create_text_surface(text, "main")
            #MADE AN EDIT HERE TO MOVE THIS TEXT, MOVE MORE TO THE RIGHT
            text_rect = text_surf.get_rect(center=(self.window_size[0]//2 + 80, self.window_size[1]//2 + 200))
            
            # Create a panel behind the text
            panel_rect = pygame.Rect(text_rect.left - 20, text_rect.top - 10, text_rect.width + 40, text_rect.height + 20)
            panel = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
            panel.fill((255, 255, 255, 180))  # Semi-transparent white
            self.screen.blit(panel, panel_rect)
            self.screen.blit(text_surf, text_rect)
            
            # Next button MADE AN EDIT HERE TO PUT THE TEXT NEAR THE BOTTOM OF THE SCREEN !!!
            next_button_x = self.window_size[0]//2 - 80
            next_button_y = self.window_size[1]//2 + 250
            
            # Check if mouse is hovering over next button
            is_next_hovered = self.is_button_hovered("next_button", next_button_x, next_button_y)
            
            # Draw the next button with hover effect
            self.next_btn_rect = self.theme.draw_theme_button(
                self.screen, "next_button", 
                next_button_x, next_button_y,
                hover=is_next_hovered
            )
        
        # Settings button
        #MADE AN EDIT HERE TO MOVE THIS TEXT, needs farther left
        settings_button_x = self.window_size[0] - 250
        settings_button_y = 20
        
        # Check if mouse is hovering over settings button
        is_settings_hovered = self.is_button_hovered("settings_button", settings_button_x, settings_button_y)
        
        # Draw the settings button with hover effect
        self.settings_btn_rect = self.theme.draw_theme_button(
            self.screen, "settings_button", 
            settings_button_x, settings_button_y,
            hover=is_settings_hovered
        )
        
    def draw_recording_screen(self):
        """Draw the recording screen with Sanrio theme and enhanced hover effects"""
        # Draw background pattern
        if "background" in self.theme.assets:
            bg = self.theme.assets["background"]
            bg_w, bg_h = bg.get_size()
            for y in range(0, self.window_size[1], bg_h):
                for x in range(0, self.window_size[0], bg_w):
                    self.screen.blit(bg, (x, y))
        
        # Draw "Recording Video" text at the top
        if "recording_text" in self.theme.assets:
            rec_text = self.theme.assets["recording_text"]
            text_x = self.window_size[0]//2 - rec_text.get_width()//2
            text_y = 20  # Position at top
            self.screen.blit(rec_text, (text_x, text_y))
            
            # Draw recording indicator (flashing red dot) ON TOP of the recording text
            elapsed = time.time() - self.recording_start_time
            if int(elapsed) % 2 == 0:
                # Position the red dot on top of the recording text, in a visible area
                dot_x = text_x // 2 + rec_text.get_width() - 25  # Position near right side of text
                dot_y = text_y + 90 # Position near top of text
                pygame.draw.circle(self.screen, (255, 0, 0), (dot_x, dot_y), 8)
        else:
            # Fallback if asset not found
            rec_text = self.theme.create_text_surface("Recording Video...", "main", (255, 50, 100))
            text_x = self.window_size[0]//2 - rec_text.get_width()//2
            text_y = 20
            self.screen.blit(rec_text, (text_x, text_y))
            
            # Draw recording indicator with fallback positioning
            elapsed = time.time() - self.recording_start_time
            if int(elapsed) % 2 == 0:
                pygame.draw.circle(self.screen, (255, 0, 0), (text_x + rec_text.get_width() - 20, text_y + 15), 8)
        
        # Draw elapsed time
        time_text = self.theme.create_text_surface(f"Time: {int(elapsed)}s", "main")
        self.screen.blit(time_text, (self.window_size[0]//2 - time_text.get_width()//2 - 20, 100))
        
        # Capture and process camera frame if recording is active
        camera_frame = None
        if self.is_recording and self.record_device is not None:
            ret, frame = self.record_device.read()
            if ret:
                # Convert to RGB for pygame display
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                camera_frame = frame_rgb
        
        # Display the camera frame (or placeholder) with border
        if camera_frame is not None:
            # Get frame dimensions and scale to fit screen
            h, w = camera_frame.shape[:2]
            scale = min((self.window_size[0] - 200) / w, (self.window_size[1] - 300) / h)
            new_w, new_h = int(w * scale), int(h * scale)
            
            # Center the frame
            x = (self.window_size[0] - new_w) // 2
            y = (self.window_size[1] - new_h - 150) // 2 + 120  # Adjusted for better vertical positioning
            
            # Create surface from numpy array
            scaled_frame = cv2.resize(camera_frame, (new_w - 100, new_h - 100))
            surface = pygame.surfarray.make_surface(scaled_frame.transpose(1, 0, 2))
            self.screen.blit(surface, (x, y))

            
            # Draw themed frame border using the rec_frame asset
            if "rec_frame" in self.theme.assets:
                rec_border = self.theme.assets["rec_frame"]
                new_w -= 100
                new_h -= 100

                # Calculate the desired padding based on a percentage of video dimensions
                # Using a percentage ensures it scales with different video sizes
                padding_percent = 0.3345  # 20% of video dimensions
                h_padding = int(new_w * padding_percent)
                v_padding = int(new_h * padding_percent)
                
                # Calculate the border dimensions based on the video frame plus padding
                border_width = new_w + (h_padding * 2)
                border_height = new_h + (v_padding * 2)
                
                # Scale the border to these dimensions
                scaled_border = pygame.transform.scale(
                    rec_border, 
                    (border_width, border_height)
                )
                
                # Position the border centered around the video frame
                border_x = x - h_padding
                border_y = y - v_padding
                
                # Draw the border
                self.screen.blit(scaled_border, (border_x, border_y))
        else:
            # Draw a placeholder frame with border when no camera feed
            frame_width = 640  # Default width
            frame_height = 480  # Default height
            
            # Center the placeholder frame
            x = (self.window_size[0] - frame_width) // 2
            y = (self.window_size[1] - frame_height - 150) // 2 + 50
            
            # Draw gray placeholder
            pygame.draw.rect(self.screen, (200, 200, 200), (x, y, frame_width, frame_height))
            
            # Add themed border
            if "rec_frame" in self.theme.assets:
                rec_border = self.theme.assets["rec_frame"]
                
                # Calculate the desired padding based on a percentage of video dimensions
                # Using a percentage ensures it scales with different video sizes
                padding_percent = 0.339  # 5% of video dimensions
                h_padding = int(frame_width * padding_percent)
                v_padding = int(frame_height * padding_percent)
                
                # Calculate the border dimensions based on the video frame plus padding
                border_width = frame_width + (h_padding * 2)
                border_height = frame_height + (v_padding * 2)
                
                # Scale the border to these dimensions
                scaled_border = pygame.transform.scale(
                    rec_border, 
                    (border_width, border_height)
                )
                
                # Position the border centered around the video frame
                border_x = x - h_padding
                border_y = y - v_padding
                
                # Draw the border
                self.screen.blit(scaled_border, (border_x, border_y))
            
            # Add camera inactive message
            camera_text = self.theme.create_text_surface("Camera starting...", "main", (100, 100, 100))
            text_x = x + (frame_width - camera_text.get_width()) // 2
            text_y = y + (frame_height - camera_text.get_height()) // 2
            self.screen.blit(camera_text, (text_x, text_y))
            
            # Add camera inactive message
            camera_text = self.theme.create_text_surface("Camera starting...", "main", (100, 100, 100))
            text_x = x + (frame_width - camera_text.get_width()) // 2
            text_y = y + (frame_height - camera_text.get_height()) // 2
            self.screen.blit(camera_text, (text_x, text_y))
        
        # Draw stop button at the bottom (moved down further)
        stop_btn_width = 150
        stop_btn_height = 50
        
        if "stop_button" in self.theme.assets:
            stop_button = self.theme.assets["stop_button"]
            stop_btn_width = stop_button.get_width()
            stop_btn_height = stop_button.get_height()
        
        # Position the stop button lower, closer to the bottom of the window
        stop_button_x = self.window_size[0]//2 - stop_btn_width//2
        stop_button_y = self.window_size[1] - stop_btn_height - 10  # Moved down even further
        
        # Check if mouse is hovering over stop button
        is_stop_hovered = self.is_button_hovered("stop_button", stop_button_x, stop_button_y)
        
        # Draw the stop button with hover effect
        self.stop_btn_rect = self.theme.draw_theme_button(
            self.screen, "stop_button", 
            stop_button_x, stop_button_y,
            hover=is_stop_hovered
        )
    
    def draw_crop_screen(self):
        """Draw the crop screen with Sanrio theme and enhanced hover effects"""
        # Draw Bg pattern
        if "background" in self.theme.assets:
            bg = self.theme.assets["background"]
            bg_w, bg_h = bg.get_size()
            for y in range(0, self.window_size[1], bg_h):
                for x in range(0, self.window_size[0], bg_w):
                    self.screen.blit(bg, (x, y))
        
        # If we have a frame to display
        if self.frame_image is not None:
            # Use fixed dimensions for the video frame display
            fixed_w = 854  # Fixed width
            fixed_h = 480  # Fixed height
            
            # Center the frame
            x = (self.window_size[0] - fixed_w) // 2
            y = (self.window_size[1] - fixed_h - 150) // 2
            
            # Create surface from numpy array, resized to our fixed dimensions
            scaled_frame = cv2.resize(self.frame_image, (fixed_w, fixed_h))
            surface = pygame.surfarray.make_surface(scaled_frame.transpose(1, 0, 2))
            
            # Draw themed frame border using the crop_frame_border asset
            if "crop_frame_border" in self.theme.assets:
                # Get the border asset
                frame_border = self.theme.assets["crop_frame_border"]
                
                # Calculate padding (e.g., 5% of the fixed dimensions)
                padding_percent = 0.022
                h_padding = int(fixed_w * padding_percent)
                v_padding = int(fixed_h * padding_percent)
                
                # Calculate the border dimensions
                border_width = fixed_w + (h_padding * 2)
                border_height = fixed_h + (v_padding * 2) + 57
                
                # Scale the border to these dimensions
                scaled_border = pygame.transform.scale(
                    frame_border, 
                    (border_width, border_height)
                )
                
                # Position the border precisely around the video frame
                border_x = x - h_padding
                border_y = y - v_padding                
            else:
                # Fallback if asset not available
                frame_border = pygame.Rect(x-10, y-10, fixed_w+20, fixed_h+20)
                pygame.draw.rect(self.screen, self.theme.colors["border_color"], frame_border, border_radius=10)
            
            # Blit the frame
            self.screen.blit(surface, (x, y))
            self.screen.blit(scaled_border, (border_x, border_y))
            
            # Draw the crop rectangle
            rel_x = self.crop_rect.x / self.frame_image.shape[1]
            rel_y = self.crop_rect.y / self.frame_image.shape[0]
            rel_w = self.crop_rect.width / self.frame_image.shape[1]
            rel_h = self.crop_rect.height / self.frame_image.shape[0]
            
            screen_crop = pygame.Rect(
                x + rel_x * fixed_w,
                y + rel_y * fixed_h,
                rel_w * fixed_w,
                rel_h * fixed_h
            )
            
            # Draw the crop rectangle with a white border
            pygame.draw.rect(self.screen, (255, 255, 255), screen_crop, 3)
            
            # Draw candy decorations at the corners
            if "crop_selector" in self.theme.assets:
                candy = self.theme.assets["crop_selector"]
                # Make the corner decorations larger - using fixed size
                candy_size = 100  # Fixed size for candy decorations
                small_candy = pygame.transform.scale(candy, (candy_size, candy_size))
                
                # Store the corner positions to check for mouse hover
                self.crop_corners = []
                
                # Draw at the corners of the crop rectangle
                candy_positions = [
                    (screen_crop.left - candy_size//2, screen_crop.top - candy_size//2),  # topleft
                    (screen_crop.right - candy_size//2, screen_crop.top - candy_size//2),  # topright
                    (screen_crop.left - candy_size//2, screen_crop.bottom - candy_size//2),  # bottomleft
                    (screen_crop.right - candy_size//2, screen_crop.bottom - candy_size//2)  # bottomright
                ]
                
                corner_names = ["topleft", "topright", "bottomleft", "bottomright"]
                
                # Check if any corner is being resized (self.resize_edge) and highlight it
                for i, pos in enumerate(candy_positions):
                    corner_rect = small_candy.get_rect(topleft=pos)
                    self.crop_corners.append((corner_names[i], corner_rect))
                    
                    # Draw with potential highlight for active resize corner
                    if self.resizing and self.resize_edge == corner_names[i]:
                        # Draw a highlight effect behind the candy
                        highlight_surface = pygame.Surface((candy_size, candy_size), pygame.SRCALPHA)
                        highlight_surface.fill((255, 150, 200, 150))  # Semi-transparent pink
                        self.screen.blit(highlight_surface, pos)
                    
                    # Draw the candy decoration
                    self.screen.blit(small_candy, pos)
                    
                    # Draw a small label near each corner for better UX
                    if self.resizing and self.resize_edge == corner_names[i]:
                        # Show "Resizing" label when actively resizing
                        resize_text = self.theme.create_text_surface("Resizing", "small", (255, 50, 150))
                        text_x = pos[0] + candy_size//2 - resize_text.get_width()//2
                        text_y = pos[1] + candy_size + 5
                        self.screen.blit(resize_text, (text_x, text_y))
            
            # Draw instruction panel using the themed asset if available
            if "instructions_panel" in self.theme.assets:
                instruction_panel = self.theme.assets["instructions_panel"]
                panel_x = 20
                panel_y = 20
                self.screen.blit(instruction_panel, (panel_x, panel_y))
                
                # Get panel dimensions to better position text
                panel_width = instruction_panel.get_width()
                panel_height = instruction_panel.get_height()
                
                instructions_bg = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
                instructions_bg.fill((255, 255, 255, 180))  # Semi-transparent white
                self.screen.blit(instructions_bg, (panel_x, panel_y))
                # Add text to the panel - adjust font sizes and positions to fill the panel
                instruct_text = [
                    "Region Selection",
                    "Click and drag to select area",
                    "Drag top left corner to resize",
                    "Drag center to move"
                ]
                
                # Calculate better text positioning
                vertical_padding = panel_height * 0.1
                text_area_height = panel_height * 0.8
                line_height = text_area_height / len(instruct_text)
                
                for i, text in enumerate(instruct_text):
                    if i == 0:
                        # Title text in bright pink - larger font
                        text_surf = self.theme.create_text_surface(text, "title", self.theme.colors["highlight_color"])
                    else:
                        # Instruction text in regular pink - appropriate size
                        text_surf = self.theme.create_text_surface(text, "main_secondary", self.theme.colors["highlight_color"])
                    # Center the text horizontally and distribute vertically
                    text_x = panel_x + (panel_width - text_surf.get_width()) / 2
                    text_y = panel_y + vertical_padding + i * line_height
                    
                    # Blit the text at the calculated position
                    self.screen.blit(text_surf, (text_x, text_y))
                    
                # Add 'Next' button (matching image)
                next_button_x = self.window_size[0]//2 - 80
                next_button_y = self.window_size[1]//2 + 250
                
                # Check if mouse is hovering over next button
                is_next_hovered = self.is_button_hovered("next_button", next_button_x, next_button_y)
                
                # Draw the next button with hover effect
                self.next_btn_rect = self.theme.draw_theme_button(
                    self.screen, "next_button", 
                    next_button_x, next_button_y,
                    hover=is_next_hovered
                )
            else:
                # If no frame to display, show error message
                error_text = self.theme.create_text_surface("No video frame available", "main", (255, 50, 50))
                self.screen.blit(error_text, (self.window_size[0]//2 - error_text.get_width()//2, self.window_size[1]//2))
            
            # Settings button in top right (matching mockup)
            settings_button_x = self.window_size[0] - 250
            settings_button_y = 20
            
            # Check if mouse is hovering over settings button
            is_settings_hovered = self.is_button_hovered("settings_button", settings_button_x, settings_button_y)
            
            # Draw the settings button with hover effect
            self.settings_btn_rect = self.theme.draw_theme_button(
                self.screen, "settings_button", 
                settings_button_x, settings_button_y,
                hover=is_settings_hovered
            )

    def handle_crop_creation(self, event, frame_rect):
        """Handle crop rectangle creation"""
        # Get mouse position
        mouse_pos = event.pos
        
        # Convert frame_rect position to video coordinates
        x, y, w, h = frame_rect
        rel_mouse_x = (mouse_pos[0] - x) / w
        rel_mouse_y = (mouse_pos[1] - y) / h
        
        # Clamp to frame boundaries
        rel_mouse_x = max(0, min(1, rel_mouse_x))
        rel_mouse_y = max(0, min(1, rel_mouse_y))
        
        # Convert to video coordinates
        video_x = int(rel_mouse_x * self.frame_image.shape[1])
        video_y = int(rel_mouse_y * self.frame_image.shape[0])
        
        if not self.creating_crop:
            # Calculate screen coordinates of the crop rectangle for hit detection
            rel_x = self.crop_rect.x / self.frame_image.shape[1]
            rel_y = self.crop_rect.y / self.frame_image.shape[0]
            rel_w = self.crop_rect.width / self.frame_image.shape[1]
            rel_h = self.crop_rect.height / self.frame_image.shape[0]
            
            screen_crop = pygame.Rect(
                x + rel_x * w,
                y + rel_y * h,
                rel_w * w,
                rel_h * h
            )
            
            # Calculate candy corner positions for resize handles
            candy_size = 50  # Half the size of the candy decorations
            corners = {
                "topleft": pygame.Rect(screen_crop.left - candy_size, screen_crop.top - candy_size, 
                                    candy_size * 2, candy_size * 2),
                "topright": pygame.Rect(screen_crop.right - candy_size, screen_crop.top - candy_size, 
                                    candy_size * 2, candy_size * 2),
                "bottomleft": pygame.Rect(screen_crop.left - candy_size, screen_crop.bottom - candy_size, 
                                    candy_size * 2, candy_size * 2),
                "bottomright": pygame.Rect(screen_crop.right - candy_size, screen_crop.bottom - candy_size, 
                                        candy_size * 2, candy_size * 2)
            }
            
            # Check if clicking on a candy corner for resizing
            self.resize_edge = None
            for corner, rect in corners.items():
                if rect.collidepoint(mouse_pos):
                    self.resize_edge = corner
                    self.resizing = True
                    print(f"Starting resize on {corner}")  # Debug
                    return
            
            # If not clicking on a corner, check if clicking inside the crop rectangle for dragging
            if screen_crop.collidepoint(mouse_pos):
                self.dragging = True
                self.drag_start = (video_x, video_y)
                print(f"Starting drag at {self.drag_start}")  # Debug
                return
            
            # If not on corners or inside, create a new rectangle
            self.creating_crop = True
            self.crop_start_pos = (video_x, video_y)
            self.crop_rect = pygame.Rect(video_x, video_y, 1, 1)
            print(f"Starting new rectangle at {self.crop_start_pos}")  # Debug
        else:
            # Update during drag (handled in handle_crop_motion)
            pass

    def handle_crop_motion(self, event, frame_rect):
        """Handle crop rectangle mouse motion events"""
        # Implementation similar to your existing interface update_crop_rect
        if not frame_rect or self.frame_image is None:
            return
        
        if not (self.creating_crop or self.dragging or self.resizing):
            return
        
        x, y, w, h = frame_rect
        
        # Convert mouse position to video coordinates
        rel_mouse_x = (event.pos[0] - x) / w
        rel_mouse_y = (event.pos[1] - y) / h
        
        # Clamp to video dimensions
        rel_mouse_x = max(0, min(1, rel_mouse_x))
        rel_mouse_y = max(0, min(1, rel_mouse_y))
        
        # Calculate mouse position in original video dimensions
        mouse_x = int(rel_mouse_x * self.frame_image.shape[1])
        mouse_y = int(rel_mouse_y * self.frame_image.shape[0])
        
        # Update crop rectangle based on interaction type
        if self.creating_crop:
            # Update crop size during creation
            if hasattr(self, 'crop_start_pos'):
                # Update crop rectangle size
                width = mouse_x - self.crop_start_pos[0]
                height = mouse_y - self.crop_start_pos[1]
                
                # Handle negative dimensions (dragging up/left)
                if width < 0:
                    self.crop_rect.x = mouse_x
                    self.crop_rect.width = abs(width)
                else:
                    self.crop_rect.x = self.crop_start_pos[0]
                    self.crop_rect.width = width
                    
                if height < 0:
                    self.crop_rect.y = mouse_y
                    self.crop_rect.height = abs(height)
                else:
                    self.crop_rect.y = self.crop_start_pos[1]
                    self.crop_rect.height = height
        
        elif self.dragging and self.drag_start:
            # Move the entire crop rectangle
            dx = mouse_x - self.drag_start[0]
            dy = mouse_y - self.drag_start[1]
            
            new_x = max(0, min(self.frame_image.shape[1] - self.crop_rect.width, self.crop_rect.x + dx))
            new_y = max(0, min(self.frame_image.shape[0] - self.crop_rect.height, self.crop_rect.y + dy))
            
            self.crop_rect.x = new_x
            self.crop_rect.y = new_y
            self.drag_start = (mouse_x, mouse_y)  # Update drag start
        
        elif self.resizing and self.resize_edge:
            # Resize the crop rectangle from the corners
            min_size = 50  # Minimum size in pixels
            
            # Handle each corner resize differently
            if self.resize_edge == "topleft":
                # Adjust x, y, width, and height
                dx = mouse_x - self.crop_rect.x
                dy = mouse_y - self.crop_rect.y
                new_w = self.crop_rect.width - dx
                new_h = self.crop_rect.height - dy
                
                if new_w >= min_size:
                    self.crop_rect.x = mouse_x
                    self.crop_rect.width = new_w
                
                if new_h >= min_size:
                    self.crop_rect.y = mouse_y
                    self.crop_rect.height = new_h
                    
            elif self.resize_edge == "topright":
                # Adjust y, width, and height
                new_w = mouse_x - self.crop_rect.x
                dy = mouse_y - self.crop_rect.y
                new_h = self.crop_rect.height - dy
                
                if new_w >= min_size:
                    self.crop_rect.width = new_w
                
                if new_h >= min_size:
                    self.crop_rect.y = mouse_y
                    self.crop_rect.height = new_h
                    
            elif self.resize_edge == "bottomleft":
                # Adjust x, width, and height
                dx = mouse_x - self.crop_rect.x
                new_w = self.crop_rect.width - dx
                new_h = mouse_y - self.crop_rect.y
                
                if new_w >= min_size:
                    self.crop_rect.x = mouse_x
                    self.crop_rect.width = new_w
                
                if new_h >= min_size:
                    self.crop_rect.height = new_h
                    
            elif self.resize_edge == "bottomright":
                # Adjust width and height
                new_w = mouse_x - self.crop_rect.x
                new_h = mouse_y - self.crop_rect.y
                
                if new_w >= min_size:
                    self.crop_rect.width = new_w
                
                if new_h >= min_size:
                    self.crop_rect.height = new_h
        
        # Ensure crop rect is within video bounds
        self.crop_rect.x = max(0, min(self.frame_image.shape[1] - 50, self.crop_rect.x))
        self.crop_rect.y = max(0, min(self.frame_image.shape[0] - 50, self.crop_rect.y))
        self.crop_rect.width = max(50, min(self.frame_image.shape[1] - self.crop_rect.x, self.crop_rect.width))
        self.crop_rect.height = max(50, min(self.frame_image.shape[0] - self.crop_rect.y, self.crop_rect.height))

    def select_video(self):
        """Open file dialog to select input video without exiting fullscreen"""
        # Create a tkinter root window
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        # Store current pygame display mode and flags
        current_display_info = pygame.display.get_surface()
        current_flags = current_display_info.get_flags()
        is_fullscreen = bool(current_flags & pygame.FULLSCREEN)
        
        # Handle different operating systems
        if platform.system() == "Windows":
            # On Windows, we need to temporarily switch out of fullscreen
            # But we'll make the transition less jarring
            
            # Save screen position to restore later
            if hasattr(self, 'screen_pos'):
                screen_pos = self.screen_pos
            else:
                screen_pos = (0, 0)
            
            # Create a screenshot of the current screen
            screenshot = pygame.Surface((self.window_size[0], self.window_size[1]))
            screenshot.blit(current_display_info, (0, 0))
            
            # Minimize pygame window slightly to ensure dialog appears on top
            if is_fullscreen:
                temp_size = (self.window_size[0] - 10, self.window_size[1] - 10)
                self.screen = pygame.display.set_mode(temp_size, pygame.NOFRAME)
                self.screen.blit(screenshot, (0, 0))
                pygame.display.flip()
        
        # Make root window appear on top of other windows
        root.attributes('-topmost', True)
        
        # Show file dialog
        video_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video files", "*.mp4;*.avi;*.mov")],
            parent=root
        )
        
        # Clean up tkinter
        root.destroy()
        
        # Restore fullscreen mode if it was active
        if is_fullscreen:
            self.screen = pygame.display.set_mode(self.window_size, pygame.FULLSCREEN)
        
        if not video_path:
            return False
        
        self.video_path = video_path
        self.config["video_path"] = video_path
        
        # Open video file
        self.cap = cv2.VideoCapture(video_path)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Get FPS for playback timing
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        if fps > 0:
            self.frame_display_time = 1/fps
        else:
            self.frame_display_time = 1/30  # Default to 30fps
        
        return True
    
    def select_export_path(self):
        """Open directory dialog to select export folder without exiting fullscreen"""
        # Create a tkinter root window
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        # Store current pygame display mode and flags
        current_display_info = pygame.display.get_surface()
        current_flags = current_display_info.get_flags()
        is_fullscreen = bool(current_flags & pygame.FULLSCREEN)
        
        # Handle different operating systems
        if platform.system() == "Windows":
            # On Windows, we need to temporarily switch out of fullscreen
            # But we'll make the transition less jarring
            
            # Save screen position to restore later
            if hasattr(self, 'screen_pos'):
                screen_pos = self.screen_pos
            else:
                screen_pos = (0, 0)
            
            # Create a screenshot of the current screen
            screenshot = pygame.Surface((self.window_size[0], self.window_size[1]))
            screenshot.blit(current_display_info, (0, 0))
            
            # Minimize pygame window slightly to ensure dialog appears on top
            if is_fullscreen:
                temp_size = (self.window_size[0] - 10, self.window_size[1] - 10)
                self.screen = pygame.display.set_mode(temp_size, pygame.NOFRAME)
                self.screen.blit(screenshot, (0, 0))
                pygame.display.flip()
        
        # Make root window appear on top of other windows
        root.attributes('-topmost', True)
        
        # Show directory dialog
        path = filedialog.askdirectory(
            title="Select Export Folder",
            parent=root
        )
        
        # Clean up tkinter
        root.destroy()
        
        # Restore fullscreen mode if it was active
        if is_fullscreen:
            self.screen = pygame.display.set_mode(self.window_size, pygame.FULLSCREEN)
        
        if path:
            self.export_path = path
            self.config["export_path"] = path
            return True
        
        return False

    def display_specific_frame(self, frame_number):
        """Display a specific frame from the video"""
        if self.cap and self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = self.cap.read()
            if ret:
                self.frame_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                return True
        return False

    # Improve start_recording method to handle camera issues better:
    def start_recording(self):
        """Start recording from webcam"""
        # Try to open the default camera
        self.record_device = cv2.VideoCapture(0)
        if not self.record_device.isOpened():
            print("Could not open camera")
            # Try alternative camera index
            self.record_device = cv2.VideoCapture(1)
            if not self.record_device.isOpened():
                print("Could not open any camera")
                return False
        
        # Set camera properties for better quality
        self.record_device.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.record_device.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.record_device.set(cv2.CAP_PROP_FPS, 30)
        
        self.is_recording = True
        self.recording_frames = []
        self.recording_start_time = time.time()
        
        # Start recording thread
        recording_thread = threading.Thread(target=self.record_video_thread)
        recording_thread.daemon = True
        recording_thread.start()
        
        return True

    # Fix the record_video_thread method to update the frame_image:
    def record_video_thread(self):
        """Background thread to record video frames"""
        while self.is_recording and self.record_device is not None:
            ret, frame = self.record_device.read()
            if ret:
                # Add frame to recorded frames
                self.recording_frames.append(frame)
                # Also update the current frame to show in UI
                self.frame_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            time.sleep(0.03)  # Aim for about 30fps

    # Improve stop_recording method with better file handling:
    def stop_recording(self):
        """Stop recording and save video"""
        if not self.is_recording or self.record_device is None:
            return False
        
        self.is_recording = False
        
        # Allow time for thread to complete
        time.sleep(0.1)
        
        # Release camera
        self.record_device.release()
        self.record_device = None
        
        if len(self.recording_frames) == 0:
            print("No frames were recorded")
            return False
        
        # Get frame dimensions from the first frame
        height, width = self.recording_frames[0].shape[:2]
        
        # Create directory for output if it doesn't exist
        os.makedirs("recordings", exist_ok=True)
        
        # Save recorded video with timestamp to avoid overwriting
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        output_path = f"recordings/recorded_video_{timestamp}.mp4"
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, 30.0, (width, height))
        
        for frame in self.recording_frames:
            out.write(frame)
        
        out.release()
        print(f"Video saved to {output_path}")
        
        # Set the recorded video as the current video
        self.video_path = output_path
        self.config["video_path"] = output_path
        
        self.cap = cv2.VideoCapture(output_path)
        self.total_frames = len(self.recording_frames)
        self.frame_display_time = 1/30.0  # 30fps for recorded video
        
        # Set first frame
        self.current_frame = 0
        self.frame_image = cv2.cvtColor(self.recording_frames[0], cv2.COLOR_BGR2RGB)
        
        return True

    def save_config(self):
            """Save configuration for processing"""
            # Update config with current values
            self.config["video_path"] = self.video_path
            self.config["export_path"] = self.export_path
            self.config["crop_rect"] = [self.crop_rect.x, self.crop_rect.y, self.crop_rect.width, self.crop_rect.height]
            
            # Format process markers
            formatted_markers = []
            for marker in self.process_markers:
                if len(marker) == 2:  # Just start and end frames
                    formatted_marker = {
                        "start_frame": marker[0],
                        "end_frame": marker[1],
                        "crop": [self.crop_rect.x, self.crop_rect.y, self.crop_rect.width, self.crop_rect.height]
                    }
                    formatted_markers.append(formatted_marker)
            
            self.config["process_markers"] = self.process_markers
            self.config["processing_options"] = self.processing_options
            
            # Save to JSON file with absolute path
            with open("interface_config.json", "w") as f:
                json.dump(self.config, f, indent=2)
            
            # Convert to absolute path if not already
            abs_video_path = os.path.abspath(self.video_path)
            abs_export_path = os.path.abspath(self.export_path)
            
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
                                existing_content += f'VIDEO_PATH = r"{abs_video_path}"\n'
                                video_path_found = True
                            elif line.strip().startswith("EXPORT_PATH ="):
                                # Replace EXPORT_PATH line
                                existing_content += f'EXPORT_PATH = r"{abs_export_path}"\n'
                                export_path_found = True
                            else:
                                # Keep other lines unchanged
                                existing_content += line
                except FileNotFoundError:
                    # File doesn't exist yet
                    pass
                
                # Add variables if they weren't found
                if not video_path_found:
                    existing_content += f'\nVIDEO_PATH = r"{abs_video_path}"\n'
                if not export_path_found:
                    existing_content += f'EXPORT_PATH = r"{abs_export_path}"\n'
                
                # Write updated content
                with open("names.py", "w") as f:
                    f.write(existing_content)
                    
                print(f"Saved configuration: Video={abs_video_path}, Export={abs_export_path}")
                
            except Exception as e:
                print(f"Error updating names.py: {e}")
                # Fallback to simple update if something goes wrong
                try:
                    with open("names.py", "w") as f:
                        f.write(f'VIDEO_PATH = r"{abs_video_path}"\n')
                        f.write(f'EXPORT_PATH = r"{abs_export_path}"\n')
                    print(f"Created new names.py with absolute paths")
                except Exception as e2:
                    print(f"Failed to create names.py: {e2}")

# Function to run the Sanrio interface
def run_sanrio_interface():
        """Entry point function to run the Sanrio-themed interface"""
        interface = SanrioInterface()
        result = interface.run()
        return result

# Main entry point when run directly
if __name__ == "__main__":
    run_sanrio_interface()