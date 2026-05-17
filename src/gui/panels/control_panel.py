import customtkinter as ctk
import tkinter as tk
from src.gui.styles import C, FONT_FAMILY


class ControlPanel(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C["bg_panel"], corner_radius=8)
        self.app = app
        self._mode = "generate"
        self._build()

    def _build(self):
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=10)

        self.btn_start = ctk.CTkButton(
            btn_frame,
            text="🎙 生成语音",
            font=(FONT_FAMILY, 13, "bold"),
            fg_color=C["green"],
            hover_color="#40ea6b",
            text_color="#1e1e2e",
            width=260,
            height=40,
            command=self._on_start_click,
        )
        self.btn_start.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_stop = ctk.CTkButton(
            btn_frame,
            text="⏹  停止 (Stop)",
            font=(FONT_FAMILY, 13, "bold"),
            fg_color=C["button_stop"],
            hover_color="#ee4545",
            text_color="#1e1e2e",
            width=180,
            height=40,
            command=self.app._stop_shadowing,
            state=tk.DISABLED,
        )
        self.btn_stop.pack(side=tk.LEFT)

        self.status_label = ctk.CTkLabel(
            self,
            text="就绪 — 输入文本后点击「生成语音」",
            font=(FONT_FAMILY, 10),
            text_color=C["fg_primary"],
        )
        self.status_label.pack(pady=(0, 8))

    def set_mode(self, mode: str):
        self._mode = mode
        if mode == "generate":
            self.btn_start.configure(
                text="🎙 生成语音",
                fg_color=C["green"],
            )
        elif mode == "shadowing":
            self.btn_start.configure(
                text="▶  开始跟读 (Start Shadowing)",
                fg_color=C["accent"],
            )
        elif mode == "loading":
            self.btn_start.configure(state=tk.DISABLED)

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
