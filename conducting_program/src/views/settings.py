import tkinter as tk
import tkinter.ttk as ttk
from typing import Callable, Optional

from src.core.shared.settings import Settings


widget_background = '#463F3A'
widget_font_color = '#FFFFFF'
widget_title_font = ("Poppins", 48, "bold")
menu_hover_color = "#E0AFA0"  # pinky color used elsewhere
camera_placeholder_color = '#8A817C'  # lighter grey for container


class SettingsView(tk.Frame):
    """Settings view embedded as a Frame for in-window navigation.

    Owns its header (Back on the left with hover; title on the right) and
    the settings content area below.
    """

    def __init__(self, master: tk.Misc | None = None, on_back: Optional[Callable[[], None]] = None) -> None:
        super().__init__(master=master, bg=widget_background)
        self._on_back = on_back
        self.settings = Settings()  # Get singleton instance
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        # Header row with Back (left) and Settings title (right)
        header = tk.Frame(self, bg=widget_background)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(12, 0), padx=12)
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
        back_label = tk.Label(
            back_frame,
            text="Back",
            bg=widget_background,
            fg=widget_font_color,
            font=("Poppins", 16, "bold"),
        )
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
        back_frame.bind("<Button-1>", lambda _e: self._fire_back())
        back_label.bind("<Button-1>", lambda _e: self._fire_back())

        title = tk.Label(
            header,
            text="Settings",
            bg=widget_background,
            fg=widget_font_color,
            font=widget_title_font,
            anchor="e",
        )
        title.grid(row=0, column=1, sticky="e")

        # The header (title and back) is managed by MainWindow. This view
        # contains only the content area below the header row.

        # Container with grey background for consistency with live page
        container = tk.Frame(self, bg=camera_placeholder_color)
        container.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=20, pady=20)
        container.columnconfigure(0, weight=1)
        
        # Content area inside container
        content = tk.Frame(container, bg=camera_placeholder_color)
        content.grid(row=0, column=0, sticky="nw", padx=20, pady=20)

        # Labels and entries
        bpm_label = tk.Label(
            content, text="Default BPM", bg=camera_placeholder_color, fg=widget_background, font=("Poppins", 14, "bold")
        )
        bpm_label.grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.bpm_var = tk.StringVar()
        bpm_entry = ttk.Entry(content, width=24, textvariable=self.bpm_var)
        bpm_entry.grid(row=1, column=0, sticky="w", pady=(0, 14))
        bpm_entry.bind("<FocusOut>", lambda _e: self._save_bpm())
        bpm_entry.bind("<Return>", lambda _e: self._save_bpm())

        ts_label = tk.Label(
            content, text="Default Time Signature", bg=camera_placeholder_color, fg=widget_background, font=("Poppins", 14, "bold")
        )
        ts_label.grid(row=2, column=0, sticky="w", pady=(0, 6))
        self.ts_var = tk.StringVar()
        ts_entry = ttk.Entry(content, width=24, textvariable=self.ts_var)
        ts_entry.grid(row=3, column=0, sticky="w", pady=(0, 14))
        ts_entry.bind("<FocusOut>", lambda _e: self._save_ts())
        ts_entry.bind("<Return>", lambda _e: self._save_ts())

        camera_label = tk.Label(
            content, text="Camera Path", bg=camera_placeholder_color, fg=widget_background, font=("Poppins", 14, "bold")
        )
        camera_label.grid(row=4, column=0, sticky="w", pady=(0, 6))
        self.camera_var = tk.StringVar()
        camera_entry = ttk.Entry(content, width=24, textvariable=self.camera_var)
        camera_entry.grid(row=5, column=0, sticky="w")
        camera_entry.bind("<FocusOut>", lambda _e: self._save_camera())
        camera_entry.bind("<Return>", lambda _e: self._save_camera())
        
        # Load current settings
        self._load_settings()

        # Match ttk widgets with dark theme background where possible
        try:
            style = ttk.Style(self)
            style.theme_use(style.theme_use())
            style.configure("TEntry", fieldbackground="#D9D9D9")
        except tk.TclError:
            pass

    def _load_settings(self) -> None:
        """Load current settings values into UI."""
        self.bpm_var.set(str(self.settings.get_beats_per_minute()))
        self.ts_var.set(self.settings.get_time_signature())
        camera_path = self.settings.get_camera_path()
        self.camera_var.set(str(camera_path) if camera_path is not None else "0")
    
    def _save_bpm(self) -> None:
        """Save BPM setting."""
        try:
            bpm = int(self.bpm_var.get())
            if bpm > 0:
                self.settings.set_beats_per_minute(bpm)
        except (ValueError, TypeError):
            # Reset to current setting if invalid
            self.bpm_var.set(str(self.settings.get_beats_per_minute()))
    
    def _save_ts(self) -> None:
        """Save time signature setting."""
        ts = self.ts_var.get().strip()
        if ts in ["4/4", "3/4"]:
            self.settings.set_time_signature(ts)
        else:
            # Reset to current setting if invalid
            self.ts_var.set(self.settings.get_time_signature())
    
    def _save_camera(self) -> None:
        """Save camera path setting."""
        try:
            camera_path = self.camera_var.get().strip()
            # Try to convert to int if it's a number, otherwise keep as string
            try:
                camera_path = int(camera_path)
            except ValueError:
                pass  # Keep as string for file paths
            self.settings.set_camera_path(camera_path)
        except Exception:
            # Reset to current setting if invalid
            camera_path = self.settings.get_camera_path()
            self.camera_var.set(str(camera_path) if camera_path is not None else "0")
    
    def refresh_settings(self) -> None:
        """Refresh UI with current settings (called when settings change elsewhere)."""
        self._load_settings()
    
    def _fire_back(self) -> None:
        if callable(self._on_back):
            try:
                self._on_back()
            except Exception:
                pass


def main() -> None:
    root = tk.Tk()
    root.configure(bg=widget_background)
    view = SettingsView(root)
    view.pack(fill="both", expand=True)
    root.mainloop()


if __name__ == "__main__":
    main()