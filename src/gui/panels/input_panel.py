import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
from src.gui.styles import C, FONT_FAMILY, draw_hex_indicator
from src.services.tts import list_available_engines


class InputPanel(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C["bg_panel"], corner_radius=0)
        self.app = app
        self._tts_engines = []
        self._suppress_change = False
        self._build()

    def _build(self):
        top_bar = tk.Canvas(
            self, height=2, bg=C["bg_panel"], highlightthickness=0,
        )
        top_bar.pack(fill=tk.X)
        top_bar.create_line(0, 0, 9999, 0, fill=C["cyan_dim"], width=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill=tk.X, padx=12, pady=(10, 6))

        hex_cvs = tk.Canvas(
            header, width=20, height=20, bg=C["bg_panel"],
            highlightthickness=0,
        )
        hex_cvs.pack(side=tk.LEFT)
        draw_hex_indicator(hex_cvs, 10, 10, size=6, color=C["cyan"])

        ctk.CTkLabel(
            header, text="REFERENCE TEXT  ·  参考文本",
            font=(FONT_FAMILY, 10, "bold"),
            text_color=C["fg_primary"],
        ).pack(side=tk.LEFT, padx=(2, 0))

        ctk.CTkButton(
            header, text="LOAD AUDIO",
            font=(FONT_FAMILY, 9, "bold"),
            fg_color=C["button_secondary"],
            hover_color=C["bg_hover"],
            text_color=C["fg_primary"],
            border_width=1,
            border_color=C["cyan_dim"],
            corner_radius=2,
            width=100, height=24,
            command=self._load_audio_file,
        ).pack(side=tk.RIGHT, padx=(4, 0))

        ctk.CTkButton(
            header, text="LOAD TXT",
            font=(FONT_FAMILY, 9, "bold"),
            fg_color=C["button_secondary"],
            hover_color=C["bg_hover"],
            text_color=C["fg_primary"],
            border_width=1,
            border_color=C["orange_dim"],
            corner_radius=2,
            width=90, height=24,
            command=self._load_text_file,
        ).pack(side=tk.RIGHT, padx=(4, 0))

        self.ref_text_widget = ctk.CTkTextbox(
            self, height=90,
            font=("Consolas", 11),
            fg_color=C["bg_input"],
            text_color=C["fg_primary"],
            border_width=1,
            border_color=C["cyan_dim"],
            corner_radius=2,
            wrap="word",
        )
        self.ref_text_widget.pack(fill=tk.X, padx=12, pady=(0, 6))
        self.ref_text_widget._textbox.bind("<<Modified>>", self._on_text_modified)
        self.ref_text_widget.insert(
            "1.0",
            "The quick brown fox jumps over the lazy dog. "
            "She sells seashells by the seashore. "
            "Practice makes perfect every single day.",
        )

        tts_row = ctk.CTkFrame(self, fg_color="transparent")
        tts_row.pack(fill=tk.X, padx=12, pady=(0, 10))

        ctk.CTkLabel(
            tts_row, text="ENGINE",
            font=(FONT_FAMILY, 9, "bold"),
            text_color=C["fg_secondary"],
        ).pack(side=tk.LEFT)

        self._tts_engines = list_available_engines()
        tts_names = [name for _, name in self._tts_engines]
        if not tts_names:
            tts_names = ["No Engine"]

        self.tts_menu = ctk.CTkOptionMenu(
            tts_row,
            values=tts_names,
            font=(FONT_FAMILY, 9),
            fg_color=C["bg_input"],
            button_color=C["button_secondary"],
            button_hover_color=C["cyan_dim"],
            text_color=C["fg_primary"],
            width=150,
            corner_radius=2,
            dropdown_fg_color=C["bg_card"],
            dropdown_text_color=C["fg_primary"],
            dropdown_hover_color=C["bg_hover"],
            command=self._on_tts_change,
        )
        self.tts_menu.pack(side=tk.LEFT, padx=(8, 0))

        ctk.CTkLabel(
            tts_row, text="TTS will auto-generate reference audio if none loaded",
            font=(FONT_FAMILY, 8),
            text_color=C["fg_dim"],
        ).pack(side=tk.LEFT, padx=(12, 0))

        ctk.CTkButton(
            tts_row, text="WHISPER TRANSCRIBE",
            font=(FONT_FAMILY, 8, "bold"),
            fg_color=C["button_dim"],
            hover_color=C["bg_hover"],
            text_color=C["fg_secondary"],
            border_width=1,
            border_color=C["fg_dim"],
            corner_radius=2,
            width=140, height=24,
            command=self.app._transcribe_with_whisper,
        ).pack(side=tk.RIGHT, padx=(0, 0))

    def get_text(self):
        return self.ref_text_widget.get("1.0", tk.END).strip()

    def set_text(self, text):
        self._suppress_change = True
        self.ref_text_widget.delete("1.0", tk.END)
        self.ref_text_widget.insert("1.0", text)
        self.ref_text_widget._textbox.edit_modified(False)
        self._suppress_change = False

    def _on_text_modified(self, event=None):
        if self._suppress_change:
            return
        self.ref_text_widget._textbox.edit_modified(False)
        self.app._on_text_changed()

    def get_selected_tts_engine(self) -> str:
        current = self.tts_menu.get()
        for key, name in self._tts_engines:
            if name == current:
                return key
        return "edge"

    def _on_tts_change(self, value):
        engine_key = "edge"
        for key, name in self._tts_engines:
            if name == value:
                engine_key = key
                break
        print(f"[InputPanel] TTS engine changed to: {engine_key}")

    def _load_text_file(self):
        path = filedialog.askopenfilename(
            title="Load Text File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if path:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.set_text(content)

    def _load_audio_file(self):
        path = filedialog.askopenfilename(
            title="Load Reference Audio (WAV/MP3)",
            filetypes=[
                ("Audio files", "*.wav *.mp3 *.flac *.ogg"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self.app._ref_audio_path = path
            try:
                self.app.audio_player.load_file(path)
                dur = self.app.audio_player.duration
                self.app.control_panel.set_status(
                    f"REFERENCE AUDIO LOADED — DURATION: {dur:.1f}s"
                )
                self.app.control_panel.set_mode("shadowing")
                self.app._on_audio_loaded(path)
            except Exception as e:
                tk.messagebox.showerror("LOAD FAILED", f"Cannot load audio:\n{e}")
