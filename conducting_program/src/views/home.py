import tkinter as tk
from tkinter import font as tkfont

widget_background = '#463F3A'
widget_font_color = '#FFFFFF'
widget_title_font = ("Poppins", 60, "bold")
menu_font = ("Poppins", 40, "bold")
menu_hover_color = "#E0AFA0"


class HomeView(tk.Frame):
    """Home page view with centered title, left menu, and Exit button."""

    def __init__(self, master: tk.Misc | None = None, on_settings=None, on_live=None, on_video=None) -> None:
        super().__init__(master=master, bg=widget_background)
        self.on_settings = on_settings or (lambda: None)
        self.on_live = on_live or (lambda: None)
        self.on_video = on_video or (lambda: None)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        # Header title centered
        title = tk.Label(
            self,
            text="Conducting Tutor",
            bg=widget_background,
            fg=widget_font_color,
            font=widget_title_font,
            anchor="center",
        )
        title.grid(row=0, column=0, columnspan=2, sticky="n", padx=12, pady=(12, 0))

        # Footer spacer
        self.rowconfigure(2, weight=1)
        spacer = tk.Frame(self, bg=widget_background)
        spacer.grid(row=2, column=0, columnspan=2, sticky="nsew")

        # Bottom-left menu
        footer_left = tk.Frame(self, bg=widget_background)
        footer_left.grid(row=3, column=0, sticky="sw", padx=12, pady=12)
        self._menu_item(footer_left, "Live", self.on_live)
        self._menu_item(footer_left, "Video", self.on_video)
        self._menu_item(footer_left, "Settings", self.on_settings)

        # Exit bottom-right
        exit_button = tk.Button(
            self,
            text="Exit",
            command=self._exit_app,
            bg=widget_background,
            fg=widget_font_color,
            activeforeground=menu_hover_color,
            activebackground=widget_background,
            relief=tk.FLAT,
            font=("Poppins", 12, "bold"),
            cursor="hand2",
        )
        exit_button.grid(row=3, column=1, sticky="se", padx=12, pady=12)

    def _menu_item(self, parent: tk.Widget, text: str, command) -> None:
        item_frame = tk.Frame(parent, bg=widget_background)
        item_frame.pack(anchor="w", pady=2)
        label_font = tkfont.Font(family=menu_font[0], size=menu_font[1], weight=menu_font[2])
        label = tk.Label(
            item_frame,
            text=text,
            bg=widget_background,
            fg=widget_font_color,
            font=label_font,
            anchor="w",
            cursor="hand2",
        )
        label.pack(anchor="w")

        underline_width = label_font.measure(text)
        underline = tk.Frame(item_frame, bg=widget_background, height=2, width=underline_width)
        underline.pack(anchor="w")

        def on_enter(_e):
            underline.configure(bg=menu_hover_color)

        def on_leave(_e):
            underline.configure(bg=widget_background)

        label.bind("<Enter>", on_enter)
        label.bind("<Leave>", on_leave)
        label.bind("<Button-1>", lambda _e: command())

    def _exit_app(self) -> None:
        # Walk up to the root window and destroy
        root = self.winfo_toplevel()
        try:
            root.destroy()
        except Exception:
            pass


def main() -> None:
    root = tk.Tk()
    HomeView(root).pack(fill="both", expand=True)
    root.mainloop()


if __name__ == "__main__":
    main()
