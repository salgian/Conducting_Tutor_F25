import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
from typing import Callable, Optional
import sys
from pathlib import Path

# Path manager functionality removed - not needed for now

widget_background = '#463F3A'
widget_font_color = '#FFFFFF'
widget_title_font = ("Poppins", 48, "bold")
menu_hover_color = "#E0AFA0"
camera_placeholder_color = '#8A817C'  # lighter grey for camera area
disabled_color = '#6B6560'  # Greyed out color


class EditView(tk.Frame):
    """Edit path page layout with camera area and a right-side settings panel."""

    def __init__(
        self,
        master: tk.Misc | None = None,
        on_back: Optional[Callable[[], None]] = None,
        on_start: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(master=master, bg=widget_background)
        self._on_back = on_back
        self._on_start = on_start
        self._has_unsaved_changes = False
        self._initial_state = {}

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.rowconfigure(1, weight=1)

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
        back_frame.bind("<Button-1>", lambda _e: self._handle_back())
        back_label.bind("<Button-1>", lambda _e: self._handle_back())

        title = tk.Label(header, text="Edit Path", bg=widget_background, fg=widget_font_color, font=widget_title_font, anchor="e")
        title.grid(row=0, column=1, sticky="e")

        # Main content: camera area (left) and settings panel (right)
        camera_frame = tk.Frame(self, bg=camera_placeholder_color)
        camera_frame.grid(row=1, column=0, sticky="nsew", padx=(12, 6), pady=12)
        camera_frame.rowconfigure(0, weight=1)
        camera_frame.columnconfigure(0, weight=1)

        placeholder = tk.Label(
            camera_frame,
            text="No Camera",
            bg=camera_placeholder_color,
            fg=widget_background,
            font=("Poppins", 20, "bold"),
        )
        placeholder.grid(row=0, column=0)

        # Settings panel
        panel_container = tk.Frame(self, bg=camera_placeholder_color)
        panel_container.grid(row=1, column=1, sticky="ns", padx=(6, 12), pady=12)
        panel_container.columnconfigure(0, minsize=300)  # Set minimum width
        
        panel = tk.Frame(panel_container, bg=camera_placeholder_color)
        panel.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        panel_container.rowconfigure(0, weight=1)
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(10, weight=1)

        # Control variables
        self.preset_var = tk.StringVar(value="Edit Path")
        self.show_kinesis_var = tk.BooleanVar(value=False)
        self.center_kinesis_var = tk.BooleanVar(value=False)
        self.beats_var = tk.StringVar()
        self.path_name_var = tk.StringVar()
        self.is_editing = tk.BooleanVar(value=True)
        
        # Preset dropdown
        preset_label = tk.Label(panel, text="Preset", bg=camera_placeholder_color, fg=widget_background, font=("Poppins", 14, "bold"))
        preset_label.grid(row=0, column=0, sticky="w", pady=(0, 6))
        
        preset_frame = tk.Frame(panel, bg=camera_placeholder_color)
        preset_frame.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        preset_frame.columnconfigure(0, weight=1)
        
        preset_dropdown = ttk.Combobox(
            preset_frame,
            textvariable=self.preset_var,
            values=["4/4", "3/4", "Edit Path"],
            state="readonly",
            width=15,
        )
        preset_dropdown.grid(row=0, column=0, sticky="w")
        
        # Edit button (shown when preset is selected)
        self.edit_button_frame = tk.Frame(
            preset_frame,
            bg="#FFFFFF",
            highlightthickness=2,
            highlightbackground=widget_background,
            highlightcolor=widget_background,
            bd=0,
            padx=8,
            pady=4,
            cursor="hand2",
        )
        self.edit_button_label = tk.Label(
            self.edit_button_frame,
            text="Edit",
            bg="#FFFFFF",
            fg=widget_background,
            font=("Poppins", 12, "bold"),
        )
        self.edit_button_label.pack()
        self.edit_button_frame.grid(row=0, column=1, sticky="e", padx=(6, 0))
        
        def on_edit_enter(_e: tk.Event) -> None:
            self.edit_button_frame.configure(bg=menu_hover_color, highlightbackground=widget_background, highlightcolor=widget_background)
            self.edit_button_label.configure(bg=menu_hover_color)
        
        def on_edit_leave(_e: tk.Event) -> None:
            self.edit_button_frame.configure(bg="#FFFFFF", highlightbackground=widget_background, highlightcolor=widget_background)
            self.edit_button_label.configure(bg="#FFFFFF")
        
        self.edit_button_frame.bind("<Enter>", on_edit_enter)
        self.edit_button_frame.bind("<Leave>", on_edit_leave)
        self.edit_button_label.bind("<Enter>", on_edit_enter)
        self.edit_button_label.bind("<Leave>", on_edit_leave)
        self.edit_button_frame.bind("<Button-1>", lambda _e: self._on_edit_click())
        self.edit_button_label.bind("<Button-1>", lambda _e: self._on_edit_click())
        
        # Path name entry
        self.path_name_label = tk.Label(panel, text="Path Name", bg=camera_placeholder_color, fg=widget_background, font=("Poppins", 12, "bold"))
        self.path_name_label.grid(row=2, column=0, sticky="w", pady=(6, 4))
        self.path_name_frame = tk.Frame(
            panel,
            bg=widget_background,
            highlightthickness=2,
            highlightbackground=widget_background,
            highlightcolor=widget_background,
            bd=0,
        )
        self.path_name_frame.grid(row=3, column=0, sticky="w", pady=(0, 10))
        self.path_name_entry = ttk.Entry(self.path_name_frame, width=18, textvariable=self.path_name_var)
        self.path_name_entry.insert(0, "Enter Path Name")
        self.path_name_entry.pack(padx=2, pady=2)
        
        # Control widget references for enabling/disabling
        self.control_widgets = []
        
        # Kinesis Sphere controls
        kinesis_label = tk.Label(panel, text="Kinesis Sphere", bg=camera_placeholder_color, fg=widget_background, font=("Poppins", 14, "bold"))
        kinesis_label.grid(row=4, column=0, sticky="w", pady=(0, 6))
        self.control_widgets.append(kinesis_label)

        checkbox1 = self._create_checkbox(panel, "Show Kinesis Sphere", self.show_kinesis_var, row=5)
        self.control_widgets.append(checkbox1)

        checkbox2 = self._create_checkbox(panel, "Add Center of Kinesis Sphere", self.center_kinesis_var, row=6)
        self.control_widgets.append(checkbox2)

        # Beat Regions controls
        beats_label = tk.Label(panel, text="Beat Regions", bg=camera_placeholder_color, fg=widget_background, font=("Poppins", 14, "bold"))
        beats_label.grid(row=7, column=0, sticky="w", pady=(12, 4))
        self.control_widgets.append(beats_label)

        beats_entry_label = tk.Label(panel, text="Amount of Beats", bg=camera_placeholder_color, fg=widget_background, font=("Poppins", 12, "bold"))
        beats_entry_label.grid(row=8, column=0, sticky="w", pady=(0, 4))
        self.control_widgets.append(beats_entry_label)
        
        beats_entry_frame = tk.Frame(
            panel,
            bg=widget_background,
            highlightthickness=2,
            highlightbackground=widget_background,
            highlightcolor=widget_background,
            bd=0,
        )
        beats_entry_frame.grid(row=9, column=0, sticky="w", pady=(0, 10))
        self.beats_entry = ttk.Entry(beats_entry_frame, width=18, textvariable=self.beats_var)
        self.beats_entry.insert(0, "Enter Beats")
        self.beats_entry.pack(padx=2, pady=2)
        self.control_widgets.append(beats_entry_frame)
        self.control_widgets.append(self.beats_entry)

        self.save_button = self._create_styled_button(panel, "Save", self._on_save_click, row=10, sticky="sew")
        self.control_widgets.append(self.save_button)
        
        # Setup change tracking and preset handling
        self.preset_var.trace_add("write", lambda *args: self._on_preset_change())
        self._on_preset_change()
        self._track_changes()

        footer = tk.Label(self, text="edit paths", bg=widget_background, fg=widget_font_color, font=("Poppins", 12, "bold"))
        footer.grid(row=2, column=0, columnspan=2, sticky="w", padx=12, pady=(0, 8))

        # Style ttk controls
        try:
            style = ttk.Style(self)
            style.theme_use(style.theme_use())
            style.configure("TEntry", fieldbackground="#D9D9D9")
        except tk.TclError:
            pass
    
    def _track_changes(self) -> None:
        """Track changes to detect unsaved modifications."""
        self._initial_state = {
            "preset": self.preset_var.get(),
            "show_kinesis": self.show_kinesis_var.get(),
            "center_kinesis": self.center_kinesis_var.get(),
            "beats": self.beats_var.get(),
            "path_name": self.path_name_var.get(),
        }
        
        # Track variable changes
        self.show_kinesis_var.trace_add("write", lambda *args: self._mark_changed())
        self.center_kinesis_var.trace_add("write", lambda *args: self._mark_changed())
        self.beats_var.trace_add("write", lambda *args: self._mark_changed())
        self.path_name_var.trace_add("write", lambda *args: self._mark_changed())
        self.preset_var.trace_add("write", lambda *args: self._mark_changed())
    
    def _mark_changed(self) -> None:
        """Mark that unsaved changes exist."""
        current_state = {
            "preset": self.preset_var.get(),
            "show_kinesis": self.show_kinesis_var.get(),
            "center_kinesis": self.center_kinesis_var.get(),
            "beats": self.beats_var.get(),
            "path_name": self.path_name_var.get(),
        }
        self._has_unsaved_changes = current_state != self._initial_state
    
    def _handle_back(self) -> None:
        """Handle back button click, prompting to save if there are unsaved changes."""
        if self._has_unsaved_changes:
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before leaving?",
                icon="question"
            )
            if response is None:  # Cancel
                return
            elif response:  # Yes - save
                self._on_save_click()
                # After saving, mark as saved
                self._has_unsaved_changes = False
                self._initial_state = {
                    "preset": self.preset_var.get(),
                    "show_kinesis": self.show_kinesis_var.get(),
                    "center_kinesis": self.center_kinesis_var.get(),
                    "beats": self.beats_var.get(),
                    "path_name": self.path_name_var.get(),
                }
        
        # Navigate back
        self._fire(self._on_back)
    
    def _on_preset_change(self) -> None:
        """Handle preset dropdown change."""
        preset = self.preset_var.get()
        
        if preset == "Edit Path":
            self.is_editing.set(True)
            self.edit_button_frame.grid_remove()
            self.path_name_label.grid()
            self.path_name_frame.grid()
            self._enable_controls(True)
        else:
            self.is_editing.set(False)
            self.edit_button_frame.grid()
            self.path_name_label.grid_remove()
            self.path_name_frame.grid_remove()
            self._enable_controls(False)
            if preset == "4/4":
                self.beats_var.set("4")
            elif preset == "3/4":
                self.beats_var.set("3")
    
    def _on_edit_click(self) -> None:
        """Enable controls when edit button is clicked."""
        self.is_editing.set(True)
        self._enable_controls(True)
    
    def _enable_controls(self, enabled: bool) -> None:
        """Enable or disable all form controls."""
        state = "normal" if enabled else "disabled"
        color = widget_background if enabled else disabled_color
        checkbox_frames = []
        
        for widget in self.control_widgets:
            if isinstance(widget, tk.Label):
                widget.configure(fg=color)
            elif isinstance(widget, tk.Frame):
                if hasattr(widget, 'checkbox_canvas'):
                    checkbox_frames.append(widget)
                    widget.label.configure(fg=color, cursor="hand2" if enabled else "arrow")
                else:
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Entry):
                            child.configure(state=state)
            elif isinstance(widget, ttk.Entry):
                widget.configure(state=state)
        
        # Handle checkboxes
        for widget in checkbox_frames:
            canvas = widget.checkbox_canvas
            label = widget.label
            var = widget.variable
            
            if not enabled:
                canvas.configure(bg=disabled_color)
                for item in canvas.find_all():
                    canvas.itemconfig(item, fill=disabled_color, outline=disabled_color)
                canvas.unbind("<Button-1>")
                label.unbind("<Button-1>")
            else:
                if var.get():
                    canvas.configure(bg=menu_hover_color)
                    canvas.delete("checkmark")
                    canvas.create_rectangle(1, 1, 19, 19, outline=widget_background, width=2, fill=menu_hover_color, tags="checkmark")
                    canvas.create_text(10, 10, text="✓", fill=widget_background, font=("Poppins", 10, "bold"), tags="checkmark")
                else:
                    canvas.configure(bg="#FFFFFF")
                    canvas.delete("checkmark")
                    canvas.create_rectangle(1, 1, 19, 19, outline=widget_background, width=2, fill="#FFFFFF", tags="checkmark")
                
                def toggle_checkbox(_e: tk.Event = None) -> None:
                    var.set(not var.get())
                    canvas.delete("checkmark")
                    if var.get():
                        canvas.configure(bg=menu_hover_color)
                        canvas.create_rectangle(1, 1, 19, 19, outline=widget_background, width=2, fill=menu_hover_color, tags="checkmark")
                        canvas.create_text(10, 10, text="✓", fill=widget_background, font=("Poppins", 10, "bold"), tags="checkmark")
                    else:
                        canvas.configure(bg="#FFFFFF")
                        canvas.create_rectangle(1, 1, 19, 19, outline=widget_background, width=2, fill="#FFFFFF", tags="checkmark")
                
                canvas.bind("<Button-1>", toggle_checkbox)
                label.bind("<Button-1>", toggle_checkbox)
    
    def _on_save_click(self) -> None:
        """Handle save button click."""
        preset = self.preset_var.get()
        
        if preset == "Edit Path":
            path_name = self.path_name_var.get().strip()
            if not path_name or path_name == "Enter Path Name":
                return
            
            # Path saving functionality removed - not needed for now
            # Just mark as saved
            pass
        
        # Mark as saved
        self._has_unsaved_changes = False
        self._initial_state = {
            "preset": self.preset_var.get(),
            "show_kinesis": self.show_kinesis_var.get(),
            "center_kinesis": self.center_kinesis_var.get(),
            "beats": self.beats_var.get(),
            "path_name": self.path_name_var.get(),
        }
        
        self._fire(self._on_start)

    def _create_checkbox(self, parent: tk.Widget, text: str, variable: tk.BooleanVar, row: int) -> tk.Frame:
        """Create a styled checkbox with a clickable box that turns accent pink.
        
        Returns:
            The checkbox frame widget for enabling/disabling.
        """
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
        
        checkbox_frame.checkbox_canvas = checkbox_canvas
        checkbox_frame.label = label
        checkbox_frame.variable = variable
        
        return checkbox_frame

    def _create_styled_button(self, parent: tk.Widget, text: str, command: Callable[[], None], row: int, sticky: str = "ew") -> None:
        """Create a styled button with accent pink hover effect."""
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
        
        def on_enter(_e: tk.Event) -> None:
            button_frame.configure(bg=menu_hover_color, highlightbackground=widget_background, highlightcolor=widget_background)
            button_label.configure(bg=menu_hover_color)
        
        def on_leave(_e: tk.Event) -> None:
            button_frame.configure(bg="#FFFFFF", highlightbackground=widget_background, highlightcolor=widget_background)
            button_label.configure(bg="#FFFFFF")
        
        def on_click(_e: tk.Event) -> None:
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

    @staticmethod
    def _fire(cb: Optional[Callable[[], None]]) -> None:
        if callable(cb):
            try:
                cb()
            except Exception:
                pass


def main() -> None:
    root = tk.Tk()
    root.configure(bg=widget_background)
    view = EditView(root)
    view.pack(fill="both", expand=True)
    root.mainloop()


if __name__ == "__main__":
    main()

