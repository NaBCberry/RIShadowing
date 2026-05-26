import customtkinter as ctk
import tkinter as tk
from src.gui.styles import C, FONT_FAMILY, draw_hex_indicator


class ControlPanel(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C["bg_panel"], corner_radius=0)
        self.app = app
        self._mode = "generate"
        self._build()

    def _build(self):
        top_bar = tk.Canvas(
            self, height=2, bg=C["bg_panel"], highlightthickness=0,
        )
        top_bar.pack(fill=tk.X)
        top_bar.create_line(0, 0, 9999, 0, fill=C["orange_dim"], width=1)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=(12, 6))

        self.btn_start = ctk.CTkButton(
            btn_frame,
            text="GENERATE AUDIO",
            font=(FONT_FAMILY, 12, "bold"),
            fg_color=C["button_primary"],
            hover_color=C["button_hover"],
            text_color=C["button_text"],
            border_width=1,
            border_color=C["orange_dim"],
            corner_radius=2,
            width=280,
            height=42,
            command=self._on_start_click,
        )
        self.btn_start.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_stop = ctk.CTkButton(
            btn_frame,
            text="TERMINATE",
            font=(FONT_FAMILY, 12, "bold"),
            fg_color=C["button_stop"],
            hover_color=C["button_stop_hover"],
            text_color=C["fg_primary"],
            border_width=1,
            border_color=C["red_dim"],
            corner_radius=2,
            width=190,
            height=42,
            command=self.app._stop_shadowing,
            state=tk.DISABLED,
        )
        self.btn_stop.pack(side=tk.LEFT)

        status_frame = ctk.CTkFrame(self, fg_color="transparent")
        status_frame.pack(fill=tk.X, padx=12, pady=(0, 10))

        hex_cvs = tk.Canvas(
            status_frame, width=16, height=16,
            bg=C["bg_panel"], highlightthickness=0,
        )
        hex_cvs.pack(side=tk.LEFT)
        draw_hex_indicator(hex_cvs, 8, 8, size=4, color=C["cyan"], filled=False)

        self.status_label = ctk.CTkLabel(
            status_frame,
            text="STANDBY — INPUT TEXT AND CLICK [GENERATE AUDIO]",
            font=(FONT_FAMILY, 9),
            text_color=C["fg_secondary"],
        )
        self.status_label.pack(side=tk.LEFT, padx=(4, 0))

    def set_mode(self, mode: str):
        self._mode = mode
        if mode == "generate":
            self.btn_start.configure(
                text="GENERATE AUDIO",
                fg_color=C["button_primary"],
                hover_color=C["button_hover"],
                border_color=C["orange_dim"],
                state=tk.NORMAL,
            )
        elif mode == "shadowing":
            self.btn_start.configure(
                text="START SHADOWING",
                fg_color=C["cyan_dim"],
                hover_color=C["cyan"],
                border_color=C["cyan_dim"],
                text_color=C["fg_primary"],
                state=tk.NORMAL,
            )
        elif mode == "loading":
            self.btn_start.configure(
                text="PROCESSING...",
                state=tk.DISABLED,
            )

    def _on_start_click(self):
        if self._mode == "generate":
            self.app._generate_and_prepare()
        else:
            self.app._start_shadowing()

    def set_status(self, text):
        self.status_label.configure(text=text)

    def set_button_states(self, running: bool):
        if running:
            self.btn_start.configure(state=tk.DISABLED)
            self.btn_stop.configure(state=tk.NORMAL)
        else:
            state = tk.NORMAL if self._mode in ("generate", "shadowing") else tk.DISABLED
            self.btn_start.configure(state=state)
            self.btn_stop.configure(state=tk.DISABLED)
