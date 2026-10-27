import customtkinter as ctk
from typing import Callable, Optional, Any
import cv2
import numpy as np
from PIL import Image

from src.core.shared.settings import Settings
from src.core.shared.ui_bridge import UIBridge

widget_background = '#463F3A'
widget_font_color = '#FFFFFF'
widget_title_font = ("Poppins", 48, "bold")
menu_hover_color = "#E0AFA0"
camera_placeholder_color = '#8A817C'


class ActiveView(ctk.CTkFrame):
    """Active conducting view with full-width camera and live metrics."""

    def __init__(
        self,
        master: Any | None = None,
        on_end: Optional[Callable[[], None]] = None,
        ui_bridge: Optional[UIBridge] = None,
    ) -> None:
        super().__init__(master=master, fg_color=widget_background)
        self._on_end = on_end
        self.ui_bridge = ui_bridge
        self.settings = Settings()  # Get singleton instance
        self.camera_label = None
        self.current_photo = None  # Keep reference to prevent garbage collection
        self.frame_update_id = None
        self.metrics_update_id = None

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=0)

        # Header (matching live view structure for consistent positioning)
        header = ctk.CTkFrame(self, fg_color=widget_background, height=100)
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 0))
        header.columnconfigure(0, weight=1)
        header.columnconfigure(1, weight=1)
        
        # Spacer to match back button space in live view
        spacer = ctk.CTkFrame(header, fg_color=widget_background, width=1, height=1)
        spacer.grid(row=0, column=0, sticky="w")
        spacer.grid_propagate(False)

        title = ctk.CTkLabel(header, text="Live", fg_color=widget_background, text_color=widget_font_color, font=widget_title_font, anchor="e")
        title.grid(row=0, column=1, sticky="e")

        # Camera area (full width with padding)
        camera_frame = ctk.CTkFrame(self, fg_color=camera_placeholder_color)
        camera_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(12, 12))
        camera_frame.rowconfigure(0, weight=1)
        camera_frame.columnconfigure(0, weight=1)

        # Camera display label
        self.camera_label = ctk.CTkLabel(
            camera_frame,
            text="No Camera",
            fg_color=camera_placeholder_color,
            text_color=widget_background,
            font=("Poppins", 20, "bold"),
        )
        self.camera_label.grid(row=0, column=0)

        # Footer with metrics and end button
        footer = ctk.CTkFrame(self, fg_color=widget_background)
        footer.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 8))
        footer.rowconfigure(0, minsize=20)  # Match footer height with live view
        footer.columnconfigure(0, weight=1)
        footer.columnconfigure(1, weight=0)

        # Metrics on the left
        metrics_frame = ctk.CTkFrame(footer, fg_color=widget_background)
        metrics_frame.grid(row=0, column=0, sticky="w")

        self.time_label = ctk.CTkLabel(
            metrics_frame,
            text="Time: 00:00",
            fg_color=widget_background,
            text_color=widget_font_color,
            font=("Poppins", 12, "bold"),
        )
        self.time_label.pack(side="left", padx=(0, 20))

        self.bpm_label = ctk.CTkLabel(
            metrics_frame,
            text="Average BPM 000",
            fg_color=widget_background,
            text_color=widget_font_color,
            font=("Poppins", 12, "bold"),
        )
        self.bpm_label.pack(side="left", padx=(0, 20))

        self.ts_label = ctk.CTkLabel(
            metrics_frame,
            text="Time Sig 4/4",
            fg_color=widget_background,
            text_color=widget_font_color,
            font=("Poppins", 12, "bold"),
        )
        self.ts_label.pack(side="left")

        # End button on the right
        end_frame = ctk.CTkFrame(
            footer,
            fg_color=widget_background,
            #highlightthickness=2,
            #highlightbackground=widget_font_color,
            #highlightcolor=widget_font_color,
            border_width=0,
            #padx=12,
            #pady=2,
            cursor="hand2",
        )
        end_frame.grid(row=0, column=1, sticky="e")
        end_label = ctk.CTkLabel(end_frame, text="End", fg_color=widget_background, text_color=widget_font_color, font=("Poppins", 16, "bold"))
        end_label.pack()

        def on_enter(_e: Any) -> None:
            end_frame.configure(fg_color=menu_hover_color)
            end_label.configure(fg_color=menu_hover_color, text="End")

        def on_leave(_e: Any) -> None:
            end_frame.configure(fg_color=widget_background)
            end_label.configure(fg_color=widget_background, text="End")

        end_frame.bind("<Enter>", on_enter)
        end_frame.bind("<Leave>", on_leave)
        end_label.bind("<Enter>", on_enter)
        end_label.bind("<Leave>", on_leave)
        end_frame.bind("<Button-1>", lambda _e: self._fire(self._on_end))
        end_label.bind("<Button-1>", lambda _e: self._fire(self._on_end))
        
        # Initialize display with current settings
        self.update_time_signature(self.settings.get_time_signature())
        self.update_bpm(self.settings.get_beats_per_minute())

       
    def start_metrics_updates(self) -> None:
        """Start periodic frame and metrics updates."""
        self._start_frame_updates()
        self._start_metrics_updates()
    
    def stop_metrics_updates(self) -> None:
        """Stop periodic updates."""
        if self.frame_update_id:
            self.after_cancel(self.frame_update_id)
            self.frame_update_id = None
        if self.metrics_update_id:
            self.after_cancel(self.metrics_update_id)
            self.metrics_update_id = None
    
    def _start_frame_updates(self) -> None:
        """Start periodic frame updates from backend."""
        if self.ui_bridge is None:
            return
        
        frame = self.ui_bridge.get_current_frame()
        if frame is not None:
            self._update_camera_display(frame)
        
        # Schedule next update (~30fps)
        self.frame_update_id = self.after(33, self._start_frame_updates)
    
    def _start_metrics_updates(self) -> None:
        """Start periodic metrics updates."""
        if self.ui_bridge is None:
            return
        
        # Update time
        session_time = self.ui_bridge.get_session_time()
        minutes = int(session_time // 60)
        seconds = int(session_time % 60)
        self.update_time(f"{minutes:02d}:{seconds:02d}")
        
        # Update BPM (use selected BPM for now)
        bpm = self.ui_bridge.get_current_bpm()
        self.update_bpm(bpm)
        
        # Update time signature
        ts = self.ui_bridge.get_time_signature()
        self.update_time_signature(ts)
        
        # Schedule next update (1 second)
        self.metrics_update_id = self.after(1000, self._start_metrics_updates)
    
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
            self.current_photo = ctk.CTkImage(light_image=image, size = image.size)
            
            # Update label
            self.camera_label.configure(image=self.current_photo, text="")
        except Exception as e:
            print(f"Error updating camera display: {e}")

    def update_time(self, time_str: str) -> None:
        """Update the time display."""
        self.time_label.configure(text=f"Time: {time_str}")

    def update_bpm(self, bpm: int) -> None:
        """Update the average BPM display."""
        self.bpm_label.configure(text=f"Average BPM {bpm:03d}")

    def update_time_signature(self, ts: str) -> None:
        """Update the time signature display."""
        self.ts_label.configure(text=f"Time Sig {ts}")

    @staticmethod
    def _fire(cb: Optional[Callable[[], None]]) -> None:
        if callable(cb):
            try:
                cb()
            except Exception:
                pass

    
def main() -> None:
    root = ctk.CTk()
    root.configure(fg_color=widget_background)
    view = ActiveView(root)
    view.pack(fill="both", expand=True)
    root.mainloop()


if __name__ == "__main__":
    main()

