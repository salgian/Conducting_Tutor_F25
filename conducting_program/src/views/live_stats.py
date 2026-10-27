import customtkinter as ctk
from typing import Callable, Optional, Any

widget_background = '#463F3A'
widget_font_color = '#FFFFFF'
widget_title_font = ("Poppins", 48, "bold")
menu_hover_color = "#E0AFA0"


class LiveStatsView(ctk.CTkFrame):
    """Live statistics view showing session results."""

    def __init__(
        self,
        master: Any | None = None,
        on_home: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(master=master, fg_color=widget_background)
        self._on_home = on_home

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Main content area
        content = ctk.CTkFrame(self, fg_color=widget_background)
        content.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)

        # Home button
        home_frame = ctk.CTkFrame(
            content,
            fg_color="#FFFFFF",
            #highlightthickness=2,
            #highlightbackground=widget_font_color,
            #highlightcolor=widget_font_color,
            border_width=0,
            #padx=12,
            #pady=6,
            cursor="hand2",
        )
        home_frame.grid(row=0, column=0, sticky="")
        home_label = ctk.CTkLabel(home_frame, text="Home", fg_color="#FFFFFF", text_color=widget_background, font=("Poppins", 16, "bold"))
        home_label.pack()

        def on_enter(_e: Any) -> None:
            home_frame.configure(fg_color=menu_hover_color, highlightbackground=widget_font_color, highlightcolor=widget_font_color)
            home_label.configure(fg_color=menu_hover_color)

        def on_leave(_e: Any) -> None:
            home_frame.configure(fg_color="#FFFFFF", highlightbackground=widget_font_color, highlightcolor=widget_font_color)
            home_label.configure(fg_color="#FFFFFF")

        home_frame.bind("<Enter>", on_enter)
        home_frame.bind("<Leave>", on_leave)
        home_label.bind("<Enter>", on_enter)
        home_label.bind("<Leave>", on_leave)
        home_frame.bind("<Button-1>", lambda _e: self._fire(self._on_home))
        home_label.bind("<Button-1>", lambda _e: self._fire(self._on_home))

    @staticmethod
    def _fire(cb: Optional[Callable[[], None]]) -> None:
        if callable(cb):
                cb()


def main() -> None:
    root = ctk.CTk()
    root.configure(fg_color=widget_background)
    view = LiveStatsView(root)
    view.pack(fill="both", expand=True)
    root.mainloop()


if __name__ == "__main__":
    main()

