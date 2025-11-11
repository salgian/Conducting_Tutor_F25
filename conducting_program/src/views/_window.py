import tkinter as tk
import tkinter.ttk as ttk
from .home import HomeView
from .settings import SettingsView
from .live import LiveView
from .edit import EditView
from .active import ActiveView
from .live_stats import LiveStatsView

from src.core.shared.settings import Settings
from src.core.shared.ui_bridge import UIBridge

widget_background = '#463F3A' # shared background color
widget_font_color = '#FFFFFF' # shared font color
widget_title_font = ("Poppins", 60, "bold")
menu_hover_color = "#E0AFA0"  # shared accent color

class MainWindow:
    """Main window that manages UI initialization and navigation between views."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.settings = Settings()  # Get singleton instance
        self.ui_bridge = UIBridge(self.settings)  # Create UI bridge
        self._configure_root()
        self._build_layout()
        # Pre-initialize MediaPipe in background to avoid freeze
        self._preinitialize_backend()
        self.show_home()
    
    def _preinitialize_backend(self) -> None:
        """Pre-initialize MediaPipe in background thread to avoid UI freeze."""
        import threading
        
        def init_mediapipe():
            from src.core.live.mp_declaration import mediaPipeDeclaration
            mediaPipeDeclaration.initialize_pose_detection()
            self.ui_bridge._mediapipe_initialized = True
        
        thread = threading.Thread(target=init_mediapipe, daemon=True)
        thread.start()

    def _configure_root(self) -> None:
        self.root.title("Conducting Tutor")
        self.root.configure(bg=widget_background)
        # Make the window reasonably sized and resizable; also set a stable initial size
        self.root.geometry("900x600")
        self.root.minsize(720, 480)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

    def _build_layout(self) -> None:
        container = tk.Frame(self.root, bg=widget_background)
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)
        self.container = container

        # View frames (lazy initialization)
        self.home_frame: tk.Frame | None = None
        self.settings_frame: tk.Frame | None = None
        self.live_frame: tk.Frame | None = None
        self.edit_frame: tk.Frame | None = None
        self.active_frame: tk.Frame | None = None
        self.stats_frame: tk.Frame | None = None
        
        # Navigation tracking
        self.nav_history: list[str] = []
        self.current_view: str = "home"

    def _go_back(self) -> None:
        """Navigate to the previous view in history."""
        if self.nav_history:
            prev_view = self.nav_history.pop()
            if prev_view == "home":
                self.show_home()
            elif prev_view == "live":
                self.show_live()
            elif prev_view == "settings":
                self.show_settings()
            elif prev_view == "edit":
                self.show_edit()
            elif prev_view == "active":
                self.show_active()
            elif prev_view == "stats":
                self.show_stats()
        else:
            self.show_home()
    
    def _push_nav_history(self, current_view: str) -> None:
        """Add current view to navigation history."""
        if not self.nav_history or self.nav_history[-1] != current_view:
            self.nav_history.append(current_view)

    def on_live(self) -> None:
        self._push_nav_history("home")
        if self.live_frame is None:
            self.live_frame = LiveView(
                self.container,
                on_back=self._go_back,
                on_open_settings=self.on_settings,
                on_edit_path=self.on_edit_path,
                on_start=self.on_start,
                ui_bridge=self.ui_bridge,
                on_state_change=self._on_state_change,
            )
            self.live_frame.grid(row=0, column=0, sticky="nsew")
        # Initialize backend when showing live view
        if self.live_frame:
            self.live_frame.initialize_backend()
        self.show_live()
    
    def _on_state_change(self, new_state: str) -> None:
        """Handle state changes from backend - navigate to active view when countdown starts."""
        if new_state == "countdown":
            # Automatically transition to active view
            self.on_start()

    def on_video(self) -> None:
        """Navigate to video view (not implemented)."""
        pass
        
    def show_settings(self) -> None:
        if self.settings_frame is None:
            return
        if self.home_frame is not None:
            self.home_frame.lower()
        if self.live_frame is not None:
            self.live_frame.lower()
        if self.edit_frame is not None:
            self.edit_frame.lower()
        if self.active_frame is not None:
            self.active_frame.lower()
        if self.stats_frame is not None:
            self.stats_frame.lower()
        self.settings_frame.tkraise()
        self.current_view = "settings"

    def show_live(self) -> None:
        if self.live_frame is None:
            return
        if self.home_frame is not None:
            self.home_frame.lower()
        if self.settings_frame is not None:
            self.settings_frame.lower()
        if self.edit_frame is not None:
            self.edit_frame.lower()
        if self.active_frame is not None:
            self.active_frame.lower()
            # Stop metrics updates when leaving active view
            if self.active_frame:
                self.active_frame.stop_metrics_updates()
        if self.stats_frame is not None:
            self.stats_frame.lower()
        self.live_frame.tkraise()
        self.current_view = "live"
    
    def show_edit(self) -> None:
        if self.edit_frame is None:
            return
        if self.home_frame is not None:
            self.home_frame.lower()
        if self.settings_frame is not None:
            self.settings_frame.lower()
        if self.live_frame is not None:
            self.live_frame.lower()
        if self.active_frame is not None:
            self.active_frame.lower()
        if self.stats_frame is not None:
            self.stats_frame.lower()
        self.edit_frame.tkraise()
        self.current_view = "edit"

    def on_settings(self) -> None:
        """Navigate to settings view."""
        self._push_nav_history(self.current_view)

        if self.settings_frame is None:
            self.settings_frame = SettingsView(self.container, on_back=self._go_back)
            self.settings_frame.grid(row=0, column=0, sticky="nsew")
        else:
            # Refresh settings view with current values
            self.settings_frame.refresh_settings()

        self.show_settings()

    def on_edit_path(self) -> None:
        """Navigate to edit path view."""
        self._push_nav_history("live")
        if self.edit_frame is None:
            self.edit_frame = EditView(
                self.container,
                on_back=self._go_back,
                on_start=lambda: None,
            )
            self.edit_frame.grid(row=0, column=0, sticky="nsew")
        self.show_edit()

    def on_start(self) -> None:
        """Navigate to active conducting view - triggered by Start button or movement detection."""
        # Wait for camera to be ready before showing active view
        self._wait_for_camera_then_show_active()
    
    def _wait_for_camera_then_show_active(self) -> None:
        """Wait for camera to be ready, then show active view."""
        if not self.ui_bridge or not self.ui_bridge.components:
            # Backend not initialized, show active view anyway
            self._show_active_view()
            return
        
        camera_manager = self.ui_bridge.components.get('camera_manager')
        if not camera_manager or not camera_manager.cap:
            # Camera not ready, show active view anyway
            self._show_active_view()
            return
        
        # Check if camera can capture a frame
        def check_camera():
            success, frame = camera_manager.capture_frame()
            if success and frame is not None:
                # Camera is ready, show active view
                self.root.after(0, self._show_active_view)
            else:
                # Try again in 100ms
                self.root.after(100, check_camera)
        
        # Start checking
        check_camera()
    
    def _show_active_view(self) -> None:
        """Show the active view and start processing."""
        self._push_nav_history("live")
        if self.active_frame is None:
            self.active_frame = ActiveView(
                self.container,
                on_end=self.on_end_active,
                ui_bridge=self.ui_bridge,
            )
            self.active_frame.grid(row=0, column=0, sticky="nsew")
        # Start metrics updates
        if self.active_frame:
            self.active_frame.start_metrics_updates()
        self.show_active()
        
        # Force backend to transition to countdown state if not already
        if self.ui_bridge and self.ui_bridge.components:
            system_state = self.ui_bridge.components.get('system_state')
            if system_state:
                current_state = system_state.get_current_state()
                if current_state.get_state_name() == "setup":
                    # Force transition to countdown
                    system_state.change_state("countdown")
                    metronome_manager = self.ui_bridge.components.get('beat_manager')
                    if metronome_manager:
                        metronome_manager.start()

    def show_active(self) -> None:
        """Show the active conducting view."""
        if self.active_frame is None:
            return
        if self.home_frame is not None:
            self.home_frame.lower()
        if self.settings_frame is not None:
            self.settings_frame.lower()
        if self.live_frame is not None:
            self.live_frame.lower()
        if self.edit_frame is not None:
            self.edit_frame.lower()
        if self.stats_frame is not None:
            self.stats_frame.lower()
        self.active_frame.tkraise()
        self.current_view = "active"

    def on_end_active(self) -> None:
        """Handle end button click in active view - transition to ending state, then navigate to stats."""
        self.ui_bridge.request_ending_state()
        self._stop_view_updates()
        self.root.after(300, self._stop_backend_and_navigate)
    
    def _stop_view_updates(self) -> None:
        """Stop frame and metrics updates in active and live views."""
        self.active_frame.stop_metrics_updates()
        self.live_frame.stop_backend()
    
    def _stop_backend_and_navigate(self) -> None:
        """Stop backend processing and navigate to stats view."""
        self.ui_bridge.stop_processing()
        self._navigate_to_stats()
    
    def _navigate_to_stats(self) -> None:
        """Navigate to stats view."""
        self._push_nav_history("active")
        if self.stats_frame is None:
            self.stats_frame = LiveStatsView(
                self.container,
                on_home=self.show_home,
            )
            self.stats_frame.grid(row=0, column=0, sticky="nsew")
        self.show_stats()

    def show_stats(self) -> None:
        """Show the live stats view."""
        if self.stats_frame is None:
            return
        if self.home_frame is not None:
            self.home_frame.lower()
        if self.settings_frame is not None:
            self.settings_frame.lower()
        if self.live_frame is not None:
            self.live_frame.lower()
        if self.edit_frame is not None:
            self.edit_frame.lower()
        if self.active_frame is not None:
            self.active_frame.lower()
        self.stats_frame.tkraise()
        self.current_view = "stats"

    def show_home(self) -> None:
        if self.home_frame is None:
            self.home_frame = HomeView(self.container, on_settings=self.on_settings, on_live=self.on_live, on_video=self.on_video)
            self.home_frame.grid(row=0, column=0, sticky="nsew")

        # Stop any active processing when returning to home
        if self.active_frame:
            self.active_frame.stop_metrics_updates()
        if self.live_frame:
            self.live_frame.stop_backend()
        if self.ui_bridge:
            try:
                self.ui_bridge.stop_processing()
            except Exception as e:
                print(f"Error stopping backend: {e}")
        
        # Reset frames so they can be reinitialized on next use
        self.live_frame = None
        self.active_frame = None

        if self.settings_frame is not None:
            self.settings_frame.lower()
        if self.live_frame is not None:
            self.live_frame.lower()
        if self.edit_frame is not None:
            self.edit_frame.lower()
        if self.active_frame is not None:
            self.active_frame.lower()
        if self.stats_frame is not None:
            self.stats_frame.lower()
        self.home_frame.tkraise()
        self.current_view = "home"

def main() -> None:
    root = tk.Tk()
    MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
