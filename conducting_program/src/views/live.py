import tkinter as tk
import tkinter.ttk as ttk
from typing import Callable, Optional
import cv2
import numpy as np
from PIL import Image, ImageTk

from src.core.shared.settings import Settings
from src.core.shared.ui_bridge import UIBridge

widget_background = '#463F3A'
widget_font_color = '#FFFFFF'
widget_title_font = ("Poppins", 48, "bold")
menu_hover_color = "#E0AFA0"
camera_placeholder_color = '#8A817C'  # lighter grey for camera area


class LiveView(tk.Frame):
    """Live page layout with camera area and a right-side settings panel."""

    def __init__(
        self,
        master: tk.Misc | None = None,
        on_back: Optional[Callable[[], None]] = None,
        on_open_settings: Optional[Callable[[], None]] = None,
        on_edit_path: Optional[Callable[[], None]] = None,
        on_start: Optional[Callable[[], None]] = None,
        ui_bridge: Optional[UIBridge] = None,
        on_state_change: Optional[Callable[[str], None]] = None,
    ) -> None:
        super().__init__(master=master, bg=widget_background)
        self._on_back = on_back
        self._on_open_settings = on_open_settings
        self._on_edit_path = on_edit_path
        self._on_start = on_start
        self.ui_bridge = ui_bridge
        self._on_state_change = on_state_change
        self.settings = Settings()  # Get singleton instance
        self.camera_label = None
        self.current_photo = None  # Keep reference to prevent garbage collection
        self.frame_update_id = None
        self.state_check_id = None
        self.backend_initialized = False
        self.start_button_frame = None  # Store reference to Start button for enabling/disabling
        self.camera_initialized = False  # Track camera initialization status

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=0)

        # Header
        header = tk.Frame(self, bg=widget_background)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=12, pady=(12, 0))
        header.columnconfigure(0, weight=1)
        header.columnconfigure(1, weight=1)

        back_frame = tk.Frame(
            header,
            bg=widget_background,
            highlightthickness=2,
            highlightbackground=widget_font_color,
            highlightcolor=widget_font_color,
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
        )
        back_frame.grid(row=0, column=0, sticky="w")
        back_label = tk.Label(back_frame, text="Back", bg=widget_background, fg=widget_font_color, font=("Poppins", 16, "bold"))
        back_label.pack()

        def on_enter(_e: tk.Event) -> None:
            back_frame.configure(bg=menu_hover_color)
            back_label.configure(bg=menu_hover_color, text="<- Back")

        def on_leave(_e: tk.Event) -> None:
            back_frame.configure(bg=widget_background)
            back_label.configure(bg=widget_background, text="Back")

        back_frame.bind("<Enter>", on_enter)
        back_frame.bind("<Leave>", on_leave)
        back_label.bind("<Enter>", on_enter)
        back_label.bind("<Leave>", on_leave)
        back_frame.bind("<Button-1>", lambda _e: self._fire(self._on_back))
        back_label.bind("<Button-1>", lambda _e: self._fire(self._on_back))

        title = tk.Label(header, text="Live", bg=widget_background, fg=widget_font_color, font=widget_title_font, anchor="e")
        title.grid(row=0, column=1, sticky="e")

        # Main content:
        # Left: camera display
        camera_frame = tk.Frame(self, bg=camera_placeholder_color)
        camera_frame.grid(row=1, column=0, sticky="nsew", padx=(12, 6), pady=12)
        camera_frame.rowconfigure(0, weight=1)
        camera_frame.columnconfigure(0, weight=1)

        # Camera display label
        self.camera_label = tk.Label(
            camera_frame,
            text="No Camera",
            bg=camera_placeholder_color,
            fg=widget_background,
            font=("Poppins", 20, "bold"),
        )
        self.camera_label.grid(row=0, column=0)

        # Right: settings panel with grey container background
        panel_container = tk.Frame(self, bg=camera_placeholder_color)
        panel_container.grid(row=1, column=1, sticky="ns", padx=(6, 12), pady=12)
        panel_container.columnconfigure(0, minsize=300)  # Set minimum width
        
        panel = tk.Frame(panel_container, bg=camera_placeholder_color)
        panel.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        panel_container.rowconfigure(0, weight=1)
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(9, weight=1)  # Spacer row before button

        # Controls mimic settings options
        self.dynamics_var = tk.BooleanVar(value=False)
        self.swaying_var = tk.BooleanVar(value=False)
        self.mirroring_var = tk.BooleanVar(value=False)
        self.bpm_var = tk.StringVar()
        self.ts_var = tk.StringVar()

        # Checkboxes
        self._create_checkbox(panel, "Dynamics", self.dynamics_var, row=0)
        self._create_checkbox(panel, "Swaying", self.swaying_var, row=1)
        self._create_checkbox(panel, "Mirroring", self.mirroring_var, row=2)

        # BPM label and entry
        bpm_label = tk.Label(panel, text="BPM", bg=camera_placeholder_color, fg=widget_background, font=("Poppins", 12, "bold"))
        bpm_label.grid(row=3, column=0, sticky="w", pady=(6, 4))
        bpm_entry_frame = tk.Frame(
            panel,
            bg=widget_background,
            highlightthickness=2,
            highlightbackground=widget_background,
            highlightcolor=widget_background,
            bd=0,
        )
        bpm_entry_frame.grid(row=4, column=0, sticky="w", pady=(0, 6))
        bpm_entry = ttk.Entry(bpm_entry_frame, width=18, textvariable=self.bpm_var)
        bpm_entry.insert(0, str(self.settings.get_beats_per_minute()))
        bpm_entry.pack(padx=2, pady=2)
        bpm_entry.bind("<Return>", lambda _e: self._on_bpm_enter())

        # Time Signature label and dropdown
        ts_label = tk.Label(panel, text="Time Signature", bg=camera_placeholder_color, fg=widget_background, font=("Poppins", 12, "bold"))
        ts_label.grid(row=5, column=0, sticky="w", pady=(6, 4))
        self.ts_dropdown = ttk.Combobox(
            panel,
            textvariable=self.ts_var,
            values=["4/4", "3/4", "Custom"],
            state="readonly",
            width=16,
        )
        self.ts_dropdown.grid(row=6, column=0, sticky="w", pady=(0, 10))
        self.ts_dropdown.set(self.settings.get_time_signature())  # Set from settings
        self.ts_dropdown.bind("<<ComboboxSelected>>", lambda _e: self._on_ts_change())

        # Buttons
        self._create_styled_button(panel, "Edit Path", lambda: self._fire(self._on_edit_path), row=7)
        self._create_styled_button(panel, "Settings", lambda: self._fire(self._on_open_settings), row=8)
        
        # Start button at the bottom (store reference for enabling/disabling)
        self.start_button_frame = self._create_styled_button(panel, "Start", lambda: self._fire(self._on_start), row=9, sticky="sew", return_frame=True)
        # Initially disable until camera is ready
        self._set_start_button_enabled(False)

        # Footer hint under camera
        footer = tk.Label(self, text="Bring band to attention to start the program", bg=widget_background, fg=widget_font_color, font=("Poppins", 12, "bold"))
        footer.grid(row=2, column=0, columnspan=2, sticky="w", padx=12, pady=(0, 8))

        # Style tweaks for ttk controls to blend with dark theme
        try:
            style = ttk.Style(self)
            style.theme_use(style.theme_use())
            style.configure("TEntry", fieldbackground="#D9D9D9")
        except tk.TclError:
            pass
    
    def initialize_backend(self) -> bool:
        """Initialize backend asynchronously when view is shown to avoid UI freeze."""
        if self.backend_initialized or self.ui_bridge is None:
            return self.backend_initialized
        
        # Show loading message
        if self.camera_label:
            self.camera_label.configure(text="Initializing camera...", fg=widget_background)
        
        # Start async initialization
        import threading
        def init_thread():
            try:
                # Get current settings from UI
                try:
                    bpm = int(self.bpm_var.get()) if self.bpm_var.get() and self.bpm_var.get() != "Enter BPM" else self.settings.get_beats_per_minute()
                    if bpm <= 0:
                        bpm = 60
                except (ValueError, TypeError):
                    bpm = 60
                
                ts = self.ts_var.get()
                if ts == "Custom" or ts == "Edit Path":
                    ts = "4/4"
                if ts not in ["4/4", "3/4"]:
                    ts = "4/4"
                
                # Update settings
                self.settings.set_beats_per_minute(bpm)
                self.settings.set_time_signature(ts)
                
                # Initialize backend
                if not self.ui_bridge.initialize_backend():
                    self.after(0, lambda: self._show_error("Failed to initialize backend components"))
                    return
                
                # Start processing loop
                if not self.ui_bridge.start_processing_loop(
                    camera_callback=None,
                    state_change_callback=self._on_state_change
                ):
                    self.after(0, lambda: self._show_error("Failed to start camera. Please check camera connection."))
                    self.camera_initialized = False
                    return
                
                # Mark as initialized and start updates
                self.backend_initialized = True
                self.camera_initialized = True
                self.after(0, self._start_frame_updates)
                self.after(0, self._start_state_checking)
                # Enable Start button now that camera is ready
                self.after(0, lambda: self._set_start_button_enabled(True))
                
            except Exception as e:
                self.after(0, lambda: self._show_error(f"Error initializing: {str(e)}"))
        
        thread = threading.Thread(target=init_thread, daemon=True)
        thread.start()
        return True
    
    def _show_error(self, message: str) -> None:
        """Show error message to user and disable Start button."""
        if self.camera_label:
            self.camera_label.configure(text=f"Error: {message}", fg="#FF0000")
        # Disable Start button on error
        self._set_start_button_enabled(False)
        self.camera_initialized = False
    
    def _start_frame_updates(self) -> None:
        """Start periodic frame updates from backend."""
        if self.ui_bridge is None:
            return
        
        frame = self.ui_bridge.get_current_frame()
        if frame is not None:
            self._update_camera_display(frame)
            # Camera is working - ensure button is enabled
            if not self.camera_initialized:
                self.camera_initialized = True
                self._set_start_button_enabled(True)
        else:
            # No frame - check if camera disconnected
            if self.camera_initialized and self.ui_bridge.components:
                camera_manager = self.ui_bridge.components.get('camera_manager')
                if camera_manager and (camera_manager.cap is None or not camera_manager.cap.isOpened()):
                    # Camera disconnected
                    self.camera_initialized = False
                    self._set_start_button_enabled(False)
                    if self.camera_label:
                        self.camera_label.configure(text="Camera disconnected", fg="#FF0000")
        
        # Schedule next update (~30fps)
        self.frame_update_id = self.after(33, self._start_frame_updates)
    
    def _start_state_checking(self) -> None:
        """Check for state changes from backend."""
        if self.ui_bridge is None:
            return
        
        new_state = self.ui_bridge.check_state_changes()
        if new_state and self._on_state_change:
            self._fire(self._on_state_change, new_state)
        
        # Check again in 100ms
        self.state_check_id = self.after(100, self._start_state_checking)
    
    def _update_camera_display(self, frame: np.ndarray) -> None:
        """Update camera display with new frame."""
        if self.camera_label is None:
            return
        
        try:
            # Get camera frame dimensions
            camera_frame = self.camera_label.master
            camera_frame.update_idletasks()
            width = camera_frame.winfo_width()
            height = camera_frame.winfo_height()
            
            if width <= 1 or height <= 1:
                # Frame not ready yet, try again later
                return
            
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Resize to fit camera frame while maintaining aspect ratio
            frame_height, frame_width = frame_rgb.shape[:2]
            frame_aspect = frame_width / frame_height
            target_aspect = width / height
            
            if frame_aspect > target_aspect:
                # Frame is wider - fit to width
                new_width = width
                new_height = int(width / frame_aspect)
            else:
                # Frame is taller - fit to height
                new_height = height
                new_width = int(height * frame_aspect)
            
            # Resize frame
            resized = cv2.resize(frame_rgb, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
            
            # Convert to PIL Image then PhotoImage
            image = Image.fromarray(resized)
            self.current_photo = ImageTk.PhotoImage(image=image)
            
            # Update label
            self.camera_label.configure(image=self.current_photo, text="")
        except Exception as e:
            print(f"Error updating camera display: {e}")
    
    def _on_bpm_enter(self) -> None:
        """Handle BPM entry on Enter key."""
        try:
            bpm_str = self.bpm_var.get().strip()
            if not bpm_str or bpm_str == "Enter BPM":
                bpm = self.settings.get_beats_per_minute()
            else:
                bpm = int(bpm_str)
                if bpm <= 0:
                    bpm = 60
        except (ValueError, TypeError):
            bpm = 60
        
        # Update settings and backend
        self.settings.set_beats_per_minute(bpm)
        self.bpm_var.set(str(bpm))
        
        if self.ui_bridge:
            self.ui_bridge.update_bpm(bpm)
        
        # Refresh settings view if open
        self._refresh_settings_view()
    
    def _on_ts_change(self) -> None:
        """Handle time signature dropdown change."""
        ts = self.ts_var.get()
        
        # Handle "Custom" as "4/4"
        if ts == "Custom" or ts == "Edit Path":
            ts = "4/4"
            self.ts_var.set("4/4")
        
        if ts in ["4/4", "3/4"]:
            # Update settings and backend
            self.settings.set_time_signature(ts)
            
            if self.ui_bridge:
                self.ui_bridge.update_time_signature(ts)
            
            # Refresh settings view if open
            self._refresh_settings_view()
    
    def _refresh_settings_view(self) -> None:
        """Refresh settings view if it exists."""
        # This will be called from _window.py if needed
        pass
    
    def stop_backend(self) -> None:
        """Stop backend processing and cleanup."""
        if self.frame_update_id:
            self.after_cancel(self.frame_update_id)
            self.frame_update_id = None
        if self.state_check_id:
            self.after_cancel(self.state_check_id)
            self.state_check_id = None
        
        # Don't stop processing here - just stop frame updates
        # Processing will be stopped by on_end_active
        self.backend_initialized = False
        # Reset camera display
        if self.camera_label:
            self.camera_label.configure(text="No Camera", image="", fg=widget_background)
        
        # Reset camera initialization status
        self.camera_initialized = False
        self._set_start_button_enabled(False)
    
    def _set_start_button_enabled(self, enabled: bool) -> None:
        """Enable or disable the Start button.
        
        Args:
            enabled: True to enable, False to disable
        """
        if self.start_button_frame is None:
            return
        
        self.start_button_frame._enabled = enabled
        
        if enabled:
            # Enable button - normal appearance
            self.start_button_frame.configure(bg="#FFFFFF", cursor="hand2")
            self.start_button_frame._button_label.configure(bg="#FFFFFF", fg=widget_background, cursor="hand2")
        else:
            # Disable button - greyed out appearance
            disabled_color = '#6B6560'
            self.start_button_frame.configure(bg=disabled_color, cursor="")
            self.start_button_frame._button_label.configure(bg=disabled_color, fg="#FFFFFF", cursor="")

    def _create_checkbox(self, parent: tk.Widget, text: str, variable: tk.BooleanVar, row: int) -> None:
        """Create a styled checkbox with a clickable box that turns accent pink."""
        checkbox_frame = tk.Frame(parent, bg=camera_placeholder_color)
        checkbox_frame.grid(row=row, column=0, sticky="w", pady=(0, 6))
        
        checkbox_canvas = tk.Canvas(
            checkbox_frame,
            width=20,
            height=20,
            bg="#FFFFFF",
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        checkbox_canvas.pack(side="left", padx=(0, 8))
        checkbox_canvas.create_rectangle(1, 1, 19, 19, outline=widget_background, width=2, fill="#FFFFFF", tags="border")
        
        label = tk.Label(
            checkbox_frame,
            text=text,
            bg=camera_placeholder_color,
            fg=widget_background,
            font=("Poppins", 12, "bold"),
        )
        label.pack(side="left")
        
        def toggle_checkbox(_e: tk.Event = None) -> None:
            variable.set(not variable.get())
            update_checkbox_appearance()
        
        def update_checkbox_appearance() -> None:
            checkbox_canvas.delete("checkmark")
            if variable.get():
                # Fill with accent pink and draw checkmark
                checkbox_canvas.configure(bg=menu_hover_color)
                checkbox_canvas.create_rectangle(1, 1, 19, 19, outline=widget_background, width=2, fill=menu_hover_color, tags="checkmark")
                # Draw checkmark
                checkbox_canvas.create_text(10, 10, text="✓", fill=widget_background, font=("Poppins", 10, "bold"), tags="checkmark")
            else:
                # White background, no checkmark
                checkbox_canvas.configure(bg="#FFFFFF")
                checkbox_canvas.create_rectangle(1, 1, 19, 19, outline=widget_background, width=2, fill="#FFFFFF", tags="checkmark")
        
        checkbox_canvas.bind("<Button-1>", toggle_checkbox)
        label.bind("<Button-1>", toggle_checkbox)
        label.configure(cursor="hand2")
        variable.trace_add("write", lambda *args: update_checkbox_appearance())
        update_checkbox_appearance()

    def _create_styled_button(self, parent: tk.Widget, text: str, command: Callable[[], None], row: int, sticky: str = "ew", return_frame: bool = False):
        """Create a styled button with accent pink hover effect.
        
        Args:
            parent: Parent widget
            text: Button text
            command: Command to execute on click
            row: Grid row
            sticky: Grid sticky option
            return_frame: If True, return the button frame for enabling/disabling
            
        Returns:
            button_frame if return_frame is True, None otherwise
        """
        button_frame = tk.Frame(
            parent,
            bg="#FFFFFF",
            highlightthickness=2,
            highlightbackground=widget_background,
            highlightcolor=widget_background,
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
        )
        button_frame.grid(row=row, column=0, sticky=sticky, pady=(0, 6))
        parent.columnconfigure(0, weight=1)
        
        button_label = tk.Label(
            button_frame,
            text=text,
            bg="#FFFFFF",
            fg=widget_background,
            font=("Poppins", 16, "bold"),
        )
        button_label.pack()
        
        # Store references for enabling/disabling
        button_frame._button_label = button_label
        button_frame._command = command
        button_frame._enabled = True
        
        def on_enter(_e: tk.Event) -> None:
            if button_frame._enabled:
                button_frame.configure(bg=menu_hover_color, highlightbackground=widget_background, highlightcolor=widget_background)
                button_label.configure(bg=menu_hover_color)
        
        def on_leave(_e: tk.Event) -> None:
            if button_frame._enabled:
                button_frame.configure(bg="#FFFFFF", highlightbackground=widget_background, highlightcolor=widget_background)
                button_label.configure(bg="#FFFFFF")
        
        def on_click(_e: tk.Event) -> None:
            if button_frame._enabled and command:
                command()
                button_frame.configure(bg=menu_hover_color)
                button_label.configure(bg=menu_hover_color)
                button_frame.after(100, lambda: button_frame.configure(bg="#FFFFFF") or button_label.configure(bg="#FFFFFF"))
        
        button_frame.bind("<Enter>", on_enter)
        button_frame.bind("<Leave>", on_leave)
        button_label.bind("<Enter>", on_enter)
        button_label.bind("<Leave>", on_leave)
        button_frame.bind("<Button-1>", on_click)
        button_label.bind("<Button-1>", on_click)
        
        if return_frame:
            return button_frame

    @staticmethod
    def _fire(cb: Optional[Callable], *args) -> None:
        if callable(cb):
            try:
                cb(*args)
            except Exception:
                pass


def main() -> None:
    root = tk.Tk()
    root.configure(bg=widget_background)
    view = LiveView(root)
    view.pack(fill="both", expand=True)
    root.mainloop()


if __name__ == "__main__":
    main()
