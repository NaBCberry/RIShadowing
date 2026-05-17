import customtkinter as ctk
import tkinter as tk
from src.gui.styles import C, FONT_FAMILY


class DevicePanel(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C["bg_panel"], corner_radius=8)
        self.app = app
        self._input_devices = []
        self._output_devices = []
        self._build()

    def _build(self):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill=tk.X, padx=10, pady=(8, 4))

        ctk.CTkLabel(
            row, text="🎤 麦克风 (Input):",
            font=(FONT_FAMILY, 10), text_color=C["fg_primary"],
        ).pack(side=tk.LEFT)

        self.input_menu = ctk.CTkOptionMenu(
            row,
            values=["默认设备"],
            font=(FONT_FAMILY, 10),
            fg_color=C["bg_input"],
            button_color=C["button_bg"],
            button_hover_color=C["accent"],
            text_color=C["fg_primary"],
            width=220,
            command=self._on_input_change,
        )
        self.input_menu.pack(side=tk.LEFT, padx=(6, 20))

        ctk.CTkLabel(
            row, text="🔊 扬声器 (Output):",
            font=(FONT_FAMILY, 10), text_color=C["fg_primary"],
        ).pack(side=tk.LEFT)

        self.output_menu = ctk.CTkOptionMenu(
            row,
            values=["默认设备"],
            font=(FONT_FAMILY, 10),
            fg_color=C["bg_input"],
            button_color=C["button_bg"],
            button_hover_color=C["accent"],
            text_color=C["fg_primary"],
            width=220,
            command=self._on_output_change,
        )
        self.output_menu.pack(side=tk.LEFT, padx=(6, 0))

        level_row = ctk.CTkFrame(self, fg_color="transparent")
        level_row.pack(fill=tk.X, padx=10, pady=(2, 8))

        ctk.CTkLabel(
            level_row, text="📶 录音电平:",
            font=(FONT_FAMILY, 10), text_color=C["fg_primary"],
        ).pack(side=tk.LEFT)

        self.level_canvas = tk.Canvas(
            level_row, height=18, bg=C["bg_input"],
            highlightthickness=0,
        )
        self.level_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))
        self._level_bar = self.level_canvas.create_rectangle(
            0, 0, 0, 18, fill=C["green"], outline=""
        )

    def scan_devices(self):
        try:
            from src.services.audio_recorder import AudioRecorder
            from src.services.audio_player import AudioPlayer
            self._input_devices = AudioRecorder.list_devices()
            self._output_devices = AudioPlayer.list_devices()

            input_names = ["默认设备"] + [
                f"{d['name'][:50]} (ch:{d['channels']})" for d in self._input_devices
            ]
            output_names = ["默认设备"] + [
                f"{d['name'][:50]} (ch:{d['channels']})" for d in self._output_devices
            ]

            self.input_menu.configure(values=input_names)
            self.output_menu.configure(values=output_names)

            print(f"[Devices] Found {len(self._input_devices)} input, {len(self._output_devices)} output devices")
        except Exception as e:
            print(f"[Devices] scan error: {e}")

    def _on_input_change(self, value):
        idx = list(self.input_menu._values).index(value) if value in self.input_menu._values else -1
        if idx <= 0:
            self.app._selected_input_device = None
            print("[Devices] input: default")
        else:
            self.app._selected_input_device = self._input_devices[idx - 1]["index"]
            name = self._input_devices[idx - 1]["name"]
            print(f"[Devices] input: {name} (index={self.app._selected_input_device})")

    def _on_output_change(self, value):
        idx = list(self.output_menu._values).index(value) if value in self.output_menu._values else -1
        if idx <= 0:
            self.app._selected_output_device = None
            print("[Devices] output: default")
        else:
            self.app._selected_output_device = self._output_devices[idx - 1]["index"]
            name = self._output_devices[idx - 1]["name"]
            print(f"[Devices] output: {name} (index={self.app._selected_output_device})")

    def update_level_meter(self):
        if not self.app._is_running:
            self.level_canvas.coords(self._level_bar, 0, 0, 0, 18)
            return

        level = self.app.audio_recorder.current_level
        w = self.level_canvas.winfo_width()
        if w < 10:
            w = 200

        bar_w = int(level * w * 2)
        bar_w = min(bar_w, w)

        if level > 0.85:
            color = C["red"]
        elif level > 0.5:
            color = C["yellow"]
        else:
            color = C["green"]

        self.level_canvas.itemconfig(self._level_bar, fill=color)
        self.level_canvas.coords(self._level_bar, 0, 0, bar_w, 18)

    def set_state(self, enabled: bool):
        state = tk.NORMAL if enabled else tk.DISABLED
        self.input_menu.configure(state=state)
        self.output_menu.configure(state=state)
