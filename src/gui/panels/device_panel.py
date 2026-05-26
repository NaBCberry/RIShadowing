import customtkinter as ctk
import tkinter as tk
from src.gui.styles import C, FONT_FAMILY, draw_hex_indicator


class DevicePanel(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C["bg_panel"], corner_radius=0)
        self.app = app
        self._input_devices = []
        self._output_devices = []
        self._build()

    def _build(self):
        top_bar = tk.Canvas(
            self, height=2, bg=C["bg_panel"], highlightthickness=0,
        )
        top_bar.pack(fill=tk.X)
        top_bar.create_line(0, 0, 9999, 0, fill=C["cyan_dim"], width=1)

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill=tk.X, padx=12, pady=(10, 4))

        draw_hex_indicator(
            tk.Canvas(row, width=20, height=20, bg=C["bg_panel"],
                       highlightthickness=0).master if False else None,
            0, 0, size=0,
        )
        hex_cvs = tk.Canvas(
            row, width=20, height=20, bg=C["bg_panel"],
            highlightthickness=0,
        )
        hex_cvs.pack(side=tk.LEFT)
        draw_hex_indicator(hex_cvs, 10, 10, size=6, color=C["cyan"])

        ctk.CTkLabel(
            row, text="INPUT  ·  音频输入设备",
            font=(FONT_FAMILY, 10, "bold"),
            text_color=C["fg_primary"],
        ).pack(side=tk.LEFT, padx=(2, 0))

        ctk.CTkLabel(
            row, text="OUTPUT",
            font=(FONT_FAMILY, 9, "bold"),
            text_color=C["orange"],
        ).pack(side=tk.RIGHT, padx=(0, 4))

        hex_cvs2 = tk.Canvas(
            row, width=20, height=20, bg=C["bg_panel"],
            highlightthickness=0,
        )
        hex_cvs2.pack(side=tk.RIGHT)
        draw_hex_indicator(hex_cvs2, 10, 10, size=6, color=C["orange"])

        sel_row = ctk.CTkFrame(self, fg_color="transparent")
        sel_row.pack(fill=tk.X, padx=12, pady=(0, 8))

        self.input_menu = ctk.CTkOptionMenu(
            sel_row,
            values=["DEFAULT DEVICE"],
            font=(FONT_FAMILY, 9),
            fg_color=C["bg_input"],
            button_color=C["button_secondary"],
            button_hover_color=C["cyan_dim"],
            text_color=C["fg_primary"],
            width=260,
            corner_radius=2,
            dropdown_fg_color=C["bg_card"],
            dropdown_text_color=C["fg_primary"],
            dropdown_hover_color=C["bg_hover"],
            command=self._on_input_change,
        )
        self.input_menu.pack(side=tk.LEFT, padx=(0, 12))

        self.output_menu = ctk.CTkOptionMenu(
            sel_row,
            values=["DEFAULT DEVICE"],
            font=(FONT_FAMILY, 9),
            fg_color=C["bg_input"],
            button_color=C["button_secondary"],
            button_hover_color=C["orange_dim"],
            text_color=C["fg_primary"],
            width=260,
            corner_radius=2,
            dropdown_fg_color=C["bg_card"],
            dropdown_text_color=C["fg_primary"],
            dropdown_hover_color=C["bg_hover"],
            command=self._on_output_change,
        )
        self.output_menu.pack(side=tk.RIGHT)

        level_frame = ctk.CTkFrame(self, fg_color="transparent")
        level_frame.pack(fill=tk.X, padx=12, pady=(0, 10))

        lvl_label = tk.Frame(level_frame, bg=C["bg_panel"])
        lvl_label.pack(side=tk.LEFT)

        lvl_cvs = tk.Canvas(
            lvl_label, width=16, height=16,
            bg=C["bg_panel"], highlightthickness=0,
        )
        lvl_cvs.pack(side=tk.LEFT)
        draw_hex_indicator(lvl_cvs, 8, 8, size=5, color=C["green"], filled=False)

        ctk.CTkLabel(
            lvl_label, text=" LEVEL",
            font=(FONT_FAMILY, 9, "bold"),
            text_color=C["fg_secondary"],
        ).pack(side=tk.LEFT)

        self.level_canvas = tk.Canvas(
            level_frame, height=20, bg=C["bg_input"],
            highlightthickness=0,
        )
        self.level_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))
        self._level_bar = self.level_canvas.create_rectangle(
            0, 0, 0, 20, fill=C["green"], outline=""
        )
        self._level_glow = self.level_canvas.create_rectangle(
            0, 0, 0, 20, fill=C["green"], outline="", stipple="gray50"
        )

        peak_frame = tk.Frame(level_frame, bg=C["bg_panel"])
        peak_frame.pack(side=tk.LEFT, padx=(8, 0))
        ctk.CTkLabel(
            peak_frame, text="PEAK",
            font=(FONT_FAMILY, 8),
            text_color=C["fg_dim"],
        ).pack()

    def scan_devices(self):
        try:
            from src.services.audio_recorder import AudioRecorder
            from src.services.audio_player import AudioPlayer
            self._input_devices = AudioRecorder.list_devices()
            self._output_devices = AudioPlayer.list_devices()

            input_names = ["DEFAULT DEVICE"] + [
                f"{d['name'][:45]} (ch:{d['channels']})" for d in self._input_devices
            ]
            output_names = ["DEFAULT DEVICE"] + [
                f"{d['name'][:45]} (ch:{d['channels']})" for d in self._output_devices
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
            self.level_canvas.coords(self._level_bar, 0, 0, 0, 20)
            self.level_canvas.coords(self._level_glow, 0, 0, 0, 20)
            return

        level = self.app.audio_recorder.current_level
        w = self.level_canvas.winfo_width()
        if w < 10:
            w = 200

        bar_w = int(level * w * 2.5)
        bar_w = min(bar_w, w)

        if level > 0.85:
            color = C["red"]
        elif level > 0.5:
            color = C["yellow"]
        else:
            color = C["green"]

        self.level_canvas.itemconfig(self._level_bar, fill=color)
        self.level_canvas.coords(self._level_bar, 0, 2, bar_w, 18)

        glow_w = min(bar_w + 4, w)
        self.level_canvas.itemconfig(self._level_glow, fill=color)
        self.level_canvas.coords(self._level_glow, 0, 8, glow_w, 12)

    def set_state(self, enabled: bool):
        state = tk.NORMAL if enabled else tk.DISABLED
        self.input_menu.configure(state=state)
        self.output_menu.configure(state=state)
