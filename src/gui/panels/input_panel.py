import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
from src.gui.styles import C, FONT_FAMILY
from src.services.tts import list_available_engines


class InputPanel(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C["bg_panel"], corner_radius=8)
        self.app = app
        self._tts_engines = []
        self._build()

    def _build(self):
        row1 = ctk.CTkFrame(self, fg_color="transparent")
        row1.pack(fill=tk.X, padx=10, pady=(8, 4))

        ctk.CTkLabel(
            row1, text="📝 参考文本 (Reference Text):",
            font=(FONT_FAMILY, 10), text_color=C["fg_primary"],
        ).pack(side=tk.LEFT)

        ctk.CTkButton(
            row1, text="📂 加载文本",
            font=(FONT_FAMILY, 11, "bold"),
            fg_color=C["button_bg"], hover_color=C["accent"],
            text_color=C["button_fg"], width=100,
            command=self._load_text_file,
        ).pack(side=tk.RIGHT, padx=(4, 0))

        ctk.CTkButton(
            row1, text="🎵 加载音频",
            font=(FONT_FAMILY, 11, "bold"),
            fg_color=C["button_bg"], hover_color=C["accent"],
            text_color=C["button_fg"], width=100,
            command=self._load_audio_file,
        ).pack(side=tk.RIGHT, padx=(4, 0))

        self.ref_text_widget = ctk.CTkTextbox(
            self, height=90,
            font=("Consolas", 11),
            fg_color=C["bg_input"],
            text_color=C["fg_primary"],
            wrap="word",
        )
        self.ref_text_widget.pack(fill=tk.X, padx=10, pady=(0, 4))
        self.ref_text_widget.insert(
            "1.0",
            "The quick brown fox jumps over the lazy dog. "
            "She sells seashells by the seashore. "
            "Practice makes perfect every single day.",
        )

        tts_row = ctk.CTkFrame(self, fg_color="transparent")
        tts_row.pack(fill=tk.X, padx=10, pady=(0, 8))

        ctk.CTkLabel(
            tts_row, text="🗣 TTS引擎:",
            font=(FONT_FAMILY, 10), text_color=C["fg_primary"],
        ).pack(side=tk.LEFT)

        self._tts_engines = list_available_engines()
        tts_names = [name for _, name in self._tts_engines]
        if not tts_names:
            tts_names = ["无可用引擎"]

        self.tts_menu = ctk.CTkOptionMenu(
            tts_row,
            values=tts_names,
            font=(FONT_FAMILY, 10),
            fg_color=C["bg_input"],
            button_color=C["button_bg"],
            button_hover_color=C["accent"],
            text_color=C["fg_primary"],
            width=160,
            command=self._on_tts_change,
        )
        self.tts_menu.pack(side=tk.LEFT, padx=(6, 0))

        ctk.CTkLabel(
            tts_row, text="(未加载音频时自动生成参考语音)",
            font=(FONT_FAMILY, 8),
            text_color=C["fg_secondary"],
        ).pack(side=tk.LEFT, padx=(10, 0))

        ctk.CTkButton(
            tts_row, text="🎯 精准转写",
            font=(FONT_FAMILY, 9, "bold"),
            fg_color=C["button_bg"], hover_color=C["accent2"],
            text_color=C["button_fg"], width=90, height=26,
            command=self.app._transcribe_with_whisper,
        ).pack(side=tk.RIGHT, padx=(0, 0))

    def get_text(self):
        return self.ref_text_widget.get("1.0", tk.END).strip()

    def set_text(self, text):
        self.ref_text_widget.delete("1.0", tk.END)
        self.ref_text_widget.insert("1.0", text)

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
            title="选择文本文件",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if path:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.set_text(content)

    def _load_audio_file(self):
        path = filedialog.askopenfilename(
            title="选择参考音频 (WAV/MP3)",
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
                    f"✅ 已加载参考音频 — 时长: {dur:.1f}秒"
                )
                self.app._on_audio_loaded(path)
            except Exception as e:
                tk.messagebox.showerror("加载失败", f"无法加载音频文件:\n{e}")
