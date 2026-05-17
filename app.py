import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import time
import os
import math
import tempfile

from audio_player import AudioPlayer
from audio_recorder import AudioRecorder
from speech_recognizer import SpeechRecognizer
from comparator import ShadowComparator


class ShadowingApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("影子跟读训练 Shadowing Practice")
        self.root.geometry("1100x800")
        self.root.configure(bg="#1e1e2e")
        self.root.minsize(900, 650)

        self.audio_player = AudioPlayer()
        self.audio_recorder = AudioRecorder(sample_rate=16000, block_size=4000)
        self.speech_recognizer = SpeechRecognizer(sample_rate=16000)
        self.comparator = None

        self._stt_thread = None
        self._is_running = False
        self._practice_start_time = 0.0
        self._ref_audio_path = None

        self._input_devices = []
        self._output_devices = []
        self._selected_input_device = None
        self._selected_output_device = None
        self._input_device_var = tk.StringVar(value="默认设备")
        self._output_device_var = tk.StringVar(value="默认设备")
        self._device_menu_open = False

        self.COLORS = {
            "bg_dark": "#1e1e2e",
            "bg_panel": "#2a2a3e",
            "bg_input": "#363650",
            "fg_primary": "#e0e0f0",
            "fg_secondary": "#b0b0c0",
            "green": "#50fa7b",
            "yellow": "#f1fa8c",
            "red": "#ff5555",
            "gray": "#6272a4",
            "accent": "#8be9fd",
            "accent2": "#bd93f9",
            "button_bg": "#4444aa",
            "button_fg": "#ffffff",
            "button_stop": "#aa4444",
        }

        self._setup_styles()
        self._build_ui()
        self._check_speech_model()

        print("=" * 50)
        print(" 影子跟读训练 Shadowing Practice v1.1")
        print("=" * 50)

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=self.COLORS["bg_dark"])
        style.configure("Panel.TFrame", background=self.COLORS["bg_panel"])
        style.configure(
            "TLabel",
            background=self.COLORS["bg_dark"],
            foreground=self.COLORS["fg_primary"],
            font=("Microsoft YaHei", 10),
        )
        style.configure(
            "Panel.TLabel",
            background=self.COLORS["bg_panel"],
            foreground=self.COLORS["fg_primary"],
            font=("Microsoft YaHei", 10),
        )
        style.configure(
            "Title.TLabel",
            background=self.COLORS["bg_dark"],
            foreground=self.COLORS["accent"],
            font=("Microsoft YaHei", 16, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background=self.COLORS["bg_dark"],
            foreground=self.COLORS["fg_secondary"],
            font=("Microsoft YaHei", 9),
        )
        style.configure(
            "Primary.TButton",
            background=self.COLORS["button_bg"],
            foreground=self.COLORS["button_fg"],
            font=("Microsoft YaHei", 11, "bold"),
            padding=8,
        )
        style.configure(
            "Stop.TButton",
            background=self.COLORS["button_stop"],
            foreground=self.COLORS["button_fg"],
            font=("Microsoft YaHei", 11, "bold"),
            padding=8,
        )
        style.configure("TEntry", fieldbackground=self.COLORS["bg_input"])

    def _build_ui(self):
        main_container = ttk.Frame(self.root, style="TFrame")
        main_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        self._build_header(main_container)
        self._build_device_section(main_container)
        self._build_input_section(main_container)
        self._build_control_section(main_container)
        self._build_feedback_section(main_container)
        self._build_display_section(main_container)

    def _build_header(self, parent):
        header = ttk.Frame(parent, style="TFrame")
        header.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(
            header, text="🎤 影子跟读训练", style="Title.TLabel"
        ).pack(side=tk.LEFT)

        ttk.Label(
            header,
            text="Shadowing Practice — 听原音 · 跟读 · 实时反馈",
            style="Subtitle.TLabel",
        ).pack(side=tk.LEFT, padx=(16, 0))

    def _build_device_section(self, parent):
        panel = ttk.Frame(parent, style="Panel.TFrame")
        panel.pack(fill=tk.X, pady=(0, 6))

        row = ttk.Frame(panel, style="Panel.TFrame")
        row.pack(fill=tk.X, padx=10, pady=(6, 4))

        ttk.Label(
            row, text="🎤 麦克风 (Input):", style="Panel.TLabel"
        ).pack(side=tk.LEFT)

        self.input_device_menu = ttk.Combobox(
            row,
            textvariable=self._input_device_var,
            values=["默认设备"],
            state="readonly",
            width=36,
        )
        self.input_device_menu.pack(side=tk.LEFT, padx=(6, 20))
        self.input_device_menu.bind("<<ComboboxSelected>>", self._on_input_device_change)

        ttk.Label(
            row, text="🔊 扬声器 (Output):", style="Panel.TLabel"
        ).pack(side=tk.LEFT)

        self.output_device_menu = ttk.Combobox(
            row,
            textvariable=self._output_device_var,
            values=["默认设备"],
            state="readonly",
            width=36,
        )
        self.output_device_menu.pack(side=tk.LEFT, padx=(6, 0))
        self.output_device_menu.bind("<<ComboboxSelected>>", self._on_output_device_change)

        level_row = ttk.Frame(panel, style="Panel.TFrame")
        level_row.pack(fill=tk.X, padx=10, pady=(2, 6))

        ttk.Label(
            level_row, text="📶 录音电平:", style="Panel.TLabel"
        ).pack(side=tk.LEFT)

        self.level_canvas = tk.Canvas(
            level_row,
            height=18,
            bg=self.COLORS["bg_input"],
            highlightthickness=0,
        )
        self.level_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))
        self._level_bar = self.level_canvas.create_rectangle(
            0, 0, 0, 18, fill=self.COLORS["green"], outline=""
        )
        self._level_peak = self.level_canvas.create_rectangle(
            0, 0, 0, 18, fill=self.COLORS["red"], outline=""
        )

        self._scan_devices()

    def _scan_devices(self):
        try:
            self._input_devices = AudioRecorder.list_devices()
            self._output_devices = AudioPlayer.list_devices()

            input_names = ["默认设备"] + [
                f"{d['name'][:50]} (ch:{d['channels']})" for d in self._input_devices
            ]
            output_names = ["默认设备"] + [
                f"{d['name'][:50]} (ch:{d['channels']})" for d in self._output_devices
            ]

            self.input_device_menu["values"] = input_names
            self.output_device_menu["values"] = output_names

            print(f"[Devices] Found {len(self._input_devices)} input, {len(self._output_devices)} output devices")
        except Exception as e:
            print(f"[Devices] scan error: {e}")

    def _on_input_device_change(self, event=None):
        idx = self.input_device_menu.current()
        if idx <= 0:
            self._selected_input_device = None
            print("[Devices] input: default")
        else:
            self._selected_input_device = self._input_devices[idx - 1]["index"]
            name = self._input_devices[idx - 1]["name"]
            print(f"[Devices] input: {name} (index={self._selected_input_device})")

    def _on_output_device_change(self, event=None):
        idx = self.output_device_menu.current()
        if idx <= 0:
            self._selected_output_device = None
            print("[Devices] output: default")
        else:
            self._selected_output_device = self._output_devices[idx - 1]["index"]
            name = self._output_devices[idx - 1]["name"]
            print(f"[Devices] output: {name} (index={self._selected_output_device})")

    def _update_level_meter(self):
        if not self._is_running:
            self.level_canvas.coords(self._level_bar, 0, 0, 0, 18)
            self.level_canvas.coords(self._level_peak, 0, 0, 0, 18)
            return

        level = self.audio_recorder.current_level
        w = self.level_canvas.winfo_width()
        if w < 10:
            w = 200

        bar_w = int(level * w * 2)
        bar_w = min(bar_w, w)

        if level > 0.85:
            color = self.COLORS["red"]
        elif level > 0.5:
            color = self.COLORS["yellow"]
        else:
            color = self.COLORS["green"]

        self.level_canvas.itemconfig(self._level_bar, fill=color)
        self.level_canvas.coords(self._level_bar, 0, 0, bar_w, 18)

    def _build_input_section(self, parent):
        panel = ttk.Frame(parent, style="Panel.TFrame")
        panel.pack(fill=tk.X, pady=(0, 6))

        row1 = ttk.Frame(panel, style="Panel.TFrame")
        row1.pack(fill=tk.X, padx=10, pady=(8, 4))

        ttk.Label(
            row1, text="📝 参考文本 (Reference Text):", style="Panel.TLabel"
        ).pack(side=tk.LEFT)

        ttk.Button(
            row1,
            text="📂 加载文本",
            style="Primary.TButton",
            command=self._load_text_file,
        ).pack(side=tk.RIGHT, padx=(4, 0))

        ttk.Button(
            row1,
            text="🎵 加载音频",
            style="Primary.TButton",
            command=self._load_audio_file,
        ).pack(side=tk.RIGHT, padx=(4, 0))

        self.ref_text_widget = scrolledtext.ScrolledText(
            panel,
            height=5,
            font=("Consolas", 11),
            bg=self.COLORS["bg_input"],
            fg=self.COLORS["fg_primary"],
            insertbackground=self.COLORS["fg_primary"],
            relief=tk.FLAT,
            wrap=tk.WORD,
        )
        self.ref_text_widget.pack(fill=tk.X, padx=10, pady=(0, 8))
        self.ref_text_widget.insert(
            tk.END,
            "The quick brown fox jumps over the lazy dog. "
            "She sells seashells by the seashore. "
            "Practice makes perfect every single day.",
        )

    def _build_control_section(self, parent):
        panel = ttk.Frame(parent, style="Panel.TFrame")
        panel.pack(fill=tk.X, pady=(0, 6))

        btn_frame = ttk.Frame(panel, style="Panel.TFrame")
        btn_frame.pack(pady=10)

        self.btn_start = tk.Button(
            btn_frame,
            text="▶  开始跟读 (Start Shadowing)",
            font=("Microsoft YaHei", 13, "bold"),
            bg="#50fa7b",
            fg="#1e1e2e",
            activebackground="#40ea6b",
            activeforeground="#1e1e2e",
            relief=tk.FLAT,
            padx=24,
            pady=8,
            cursor="hand2",
            command=self._start_shadowing,
        )
        self.btn_start.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_stop = tk.Button(
            btn_frame,
            text="⏹  停止 (Stop)",
            font=("Microsoft YaHei", 13, "bold"),
            bg="#ff5555",
            fg="#1e1e2e",
            activebackground="#ee4545",
            activeforeground="#1e1e2e",
            relief=tk.FLAT,
            padx=24,
            pady=8,
            cursor="hand2",
            command=self._stop_shadowing,
            state=tk.DISABLED,
        )
        self.btn_stop.pack(side=tk.LEFT)

        self.status_label = ttk.Label(
            panel,
            text="就绪 — 点击「开始跟读」启动训练",
            style="Panel.TLabel",
        )
        self.status_label.pack(pady=(0, 8))

    def _build_feedback_section(self, parent):
        panel = ttk.Frame(parent, style="Panel.TFrame")
        panel.pack(fill=tk.X, pady=(0, 6))

        inner = ttk.Frame(panel, style="Panel.TFrame")
        inner.pack(padx=10, pady=8, fill=tk.X)

        speed_frame = tk.Frame(inner, bg=self.COLORS["bg_panel"])
        speed_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        tk.Label(
            speed_frame,
            text="⏱ 速度 (Speed)",
            font=("Microsoft YaHei", 11, "bold"),
            bg=self.COLORS["bg_panel"],
            fg=self.COLORS["fg_primary"],
        ).pack(anchor=tk.W)

        self.speed_canvas = tk.Canvas(
            speed_frame,
            height=48,
            bg=self.COLORS["bg_panel"],
            highlightthickness=0,
        )
        self.speed_canvas.pack(fill=tk.X, pady=(4, 0))
        self._speed_indicator = self.speed_canvas.create_rectangle(
            0, 0, 10, 48, fill=self.COLORS["gray"], outline=""
        )
        self._speed_text = self.speed_canvas.create_text(
            10, 24, anchor=tk.W, text="等待开始...",
            fill=self.COLORS["fg_primary"],
            font=("Microsoft YaHei", 10, "bold"),
        )

        accuracy_frame = tk.Frame(inner, bg=self.COLORS["bg_panel"])
        accuracy_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))

        tk.Label(
            accuracy_frame,
            text="🎯 准确度 (Accuracy)",
            font=("Microsoft YaHei", 11, "bold"),
            bg=self.COLORS["bg_panel"],
            fg=self.COLORS["fg_primary"],
        ).pack(anchor=tk.W)

        self.accuracy_canvas = tk.Canvas(
            accuracy_frame,
            height=48,
            bg=self.COLORS["bg_panel"],
            highlightthickness=0,
        )
        self.accuracy_canvas.pack(fill=tk.X, pady=(4, 0))
        self._accuracy_indicator = self.accuracy_canvas.create_rectangle(
            0, 0, 10, 48, fill=self.COLORS["gray"], outline=""
        )
        self._accuracy_text = self.accuracy_canvas.create_text(
            10, 24, anchor=tk.W, text="等待开始...",
            fill=self.COLORS["fg_primary"],
            font=("Microsoft YaHei", 10, "bold"),
        )

    def _build_display_section(self, parent):
        panel = ttk.Frame(parent, style="Panel.TFrame")
        panel.pack(fill=tk.BOTH, expand=True)

        left_frame = tk.Frame(panel, bg=self.COLORS["bg_panel"])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 4), pady=8)

        tk.Label(
            left_frame,
            text="📖 参考文本 (Reference)",
            font=("Microsoft YaHei", 11, "bold"),
            bg=self.COLORS["bg_panel"],
            fg=self.COLORS["fg_primary"],
        ).pack(anchor=tk.W)

        self.ref_display = tk.Text(
            left_frame,
            font=("Consolas", 12),
            bg=self.COLORS["bg_input"],
            fg=self.COLORS["fg_secondary"],
            relief=tk.FLAT,
            wrap=tk.WORD,
            state=tk.DISABLED,
            height=8,
        )
        self.ref_display.pack(fill=tk.BOTH, expand=True, pady=(4, 0))
        self._setup_text_tags(self.ref_display)

        self.word_accuracy_frame = tk.Frame(
            left_frame, bg=self.COLORS["bg_panel"]
        )
        self.word_accuracy_frame.pack(fill=tk.X, pady=(6, 0))
        self.word_accuracy_canvas = tk.Canvas(
            self.word_accuracy_frame,
            height=30,
            bg=self.COLORS["bg_panel"],
            highlightthickness=0,
        )
        self.word_accuracy_canvas.pack(fill=tk.X)

        tk.Label(
            left_frame,
            text="🟢 准确  🟡 一般  🔴 错误",
            font=("Microsoft YaHei", 9),
            bg=self.COLORS["bg_panel"],
            fg=self.COLORS["fg_secondary"],
        ).pack(anchor=tk.E, pady=(2, 0))

        right_frame = tk.Frame(panel, bg=self.COLORS["bg_panel"])
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(4, 10), pady=8)

        tk.Label(
            right_frame,
            text="🎙 你的跟读 (Your Speech)",
            font=("Microsoft YaHei", 11, "bold"),
            bg=self.COLORS["bg_panel"],
            fg=self.COLORS["fg_primary"],
        ).pack(anchor=tk.W)

        self.user_display = tk.Text(
            right_frame,
            font=("Consolas", 12),
            bg=self.COLORS["bg_input"],
            fg=self.COLORS["accent"],
            relief=tk.FLAT,
            wrap=tk.WORD,
            state=tk.DISABLED,
            height=8,
        )
        self.user_display.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

        tag_frame = tk.Frame(right_frame, bg=self.COLORS["bg_panel"])
        tag_frame.pack(fill=tk.X, pady=(6, 0))

        self.detail_text = tk.Text(
            tag_frame,
            font=("Consolas", 10),
            bg=self.COLORS["bg_input"],
            fg=self.COLORS["fg_secondary"],
            relief=tk.FLAT,
            height=4,
            state=tk.DISABLED,
        )
        self.detail_text.pack(fill=tk.BOTH)

    def _setup_text_tags(self, text_widget: tk.Text):
        text_widget.tag_configure("past", foreground="#6272a4")
        text_widget.tag_configure("current", foreground="#f1fa8c",
                                   background="#44447a",
                                   font=("Consolas", 12, "bold"))
        text_widget.tag_configure("future", foreground="#6a6a8a")
        text_widget.tag_configure("green_word", foreground="#50fa7b")
        text_widget.tag_configure("yellow_word", foreground="#f1fa8c")
        text_widget.tag_configure("red_word", foreground="#ff5555")

    def _check_speech_model(self):
        self._model_ready = self.speech_recognizer.initialize()
        if self._model_ready:
            model_path = self.speech_recognizer._model_path
            model_name = os.path.basename(model_path) if model_path else "en-us"
            self.status_label.config(
                text=f"✅ 语音模型已就绪 — {model_name}"
            )
            print(f"[App] Vosk model ready: {model_path}")
        else:
            self.status_label.config(
                text="⚠ 未找到Vosk语音模型 — 请下载模型并解压到项目根目录\n"
                     "下载地址: https://alphacephei.com/vosk/models"
            )
            print("[App] Vosk model NOT found")

    def _load_text_file(self):
        path = filedialog.askopenfilename(
            title="选择文本文件",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if path:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.ref_text_widget.delete("1.0", tk.END)
            self.ref_text_widget.insert(tk.END, content)

    def _load_audio_file(self):
        path = filedialog.askopenfilename(
            title="选择参考音频 (WAV/MP3)",
            filetypes=[
                ("Audio files", "*.wav *.mp3 *.flac *.ogg"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self._ref_audio_path = path
            try:
                self.audio_player.load_file(path)
                dur = self.audio_player.duration
                self.status_label.config(
                    text=f"✅ 已加载参考音频 — 时长: {dur:.1f}秒"
                )
            except Exception as e:
                messagebox.showerror("加载失败", f"无法加载音频文件:\n{e}")

    def _generate_tts_audio(self, text: str) -> str:
        try:
            import pyttsx3
            engine = pyttsx3.init()
            voices = engine.getProperty("voices")
            for v in voices:
                if hasattr(v, "languages") and v.languages:
                    if any(l.startswith("en") for l in v.languages):
                        engine.setProperty("voice", v.id)
                        break
            engine.setProperty("rate", 155)

            tmp_path = os.path.join(tempfile.gettempdir(), "shadow_ref.wav")
            engine.save_to_file(text, tmp_path)
            engine.runAndWait()
            return tmp_path
        except ImportError:
            messagebox.showwarning(
                "缺少依赖",
                "pyttsx3未安装。请安装后使用TTS功能:\npip install pyttsx3\n\n"
                "你也可以直接加载WAV音频文件。",
            )
            return None
        except Exception as e:
            messagebox.showerror("TTS错误", f"语音合成失败:\n{e}")
            return None

    def _update_ref_display(self):
        if not self.comparator or not self._is_running:
            return

        ref_elapsed = self.audio_player.position
        words_with_status = self.comparator.get_reference_words_for_display(
            ref_elapsed
        )

        self.ref_display.config(state=tk.NORMAL)
        self.ref_display.delete("1.0", tk.END)

        for word, status, idx in words_with_status:
            tag = status
            self.ref_display.insert(tk.END, word + " ", tag)

        self.ref_display.config(state=tk.DISABLED)

        if words_with_status:
            current_idx = self.comparator.get_current_ref_word_index(ref_elapsed)
            line_start = self.ref_display.index("1.0")
            pos = f"1.0+{sum(len(w[0]) + 1 for w in words_with_status[:current_idx])}c"
            self.ref_display.see(pos)

    def _update_feedback(self):
        if not self.comparator or not self._is_running:
            return

        recognized_words = self.speech_recognizer.get_latest_words()
        ref_elapsed = self.audio_player.position

        speed_result = self.comparator.compare_speed(recognized_words, ref_elapsed)
        self._update_speed_indicator(speed_result)

        accuracy_result = self.comparator.compare_accuracy(
            recognized_words, ref_elapsed
        )
        self._update_accuracy_indicator(accuracy_result)
        self._update_word_accuracy_bars(accuracy_result)
        self._update_user_display(recognized_words, accuracy_result)

    def _update_speed_indicator(self, result: dict):
        color = result["color"]
        self.speed_canvas.itemconfig(self._speed_indicator, fill=color)
        gap = abs(result.get("gap", 0))
        if gap <= 1:
            bar_width = 20
        elif gap <= 2:
            bar_width = 55
        else:
            bar_width = 100

        canvas_w = self.speed_canvas.winfo_width()
        if canvas_w < 50:
            canvas_w = 200
        bar_w = int(canvas_w * bar_width / 100)
        self.speed_canvas.coords(self._speed_indicator, 0, 0, bar_w, 48)
        self.speed_canvas.itemconfig(self._speed_text, text=result["message"])

    def _update_accuracy_indicator(self, result: dict):
        color = result["color"]
        self.accuracy_canvas.itemconfig(self._accuracy_indicator, fill=color)
        score = result.get("score", 0.0)
        canvas_w = self.accuracy_canvas.winfo_width()
        if canvas_w < 50:
            canvas_w = 200
        bar_w = int(canvas_w * score)
        self.accuracy_canvas.coords(self._accuracy_indicator, 0, 0, bar_w, 48)
        self.accuracy_canvas.itemconfig(self._accuracy_text, text=result["message"])

    def _update_word_accuracy_bars(self, result: dict):
        self.word_accuracy_canvas.delete("all")
        breakdown = result.get("breakdown", [])
        canvas_w = self.word_accuracy_canvas.winfo_width()
        if canvas_w < 50:
            canvas_w = 400
        h = 24
        n = max(len(breakdown), 1)
        bar_w = max(canvas_w // n, 2)

        for i, item in enumerate(breakdown):
            x0 = i * bar_w
            x1 = x0 + bar_w - 1
            color_map = {
                "green": self.COLORS["green"],
                "yellow": self.COLORS["yellow"],
                "red": self.COLORS["red"],
            }
            fill = color_map.get(item["color"], self.COLORS["gray"])
            self.word_accuracy_canvas.create_rectangle(
                x0, 3, x1, h, fill=fill, outline=""
            )

    def _update_user_display(self, recognized_words, accuracy_result):
        self.user_display.config(state=tk.NORMAL)
        self.user_display.delete("1.0", tk.END)

        breakdown = accuracy_result.get("breakdown", [])
        for i, item in enumerate(breakdown):
            word = item.get("user_word", "")
            if word:
                color_tag = f"{item.get('color', '')}_word"
                self.user_display.insert(tk.END, word + " ", color_tag)

        partial = self.speech_recognizer.partial_text
        if partial:
            if breakdown:
                self.user_display.insert(tk.END, "| ")
            self.user_display.insert(tk.END, partial, "current")

        self.user_display.config(state=tk.DISABLED)
        self.user_display.see(tk.END)

        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert(
            tk.END,
            f"进度: {self.audio_player.position:.1f}s / {self.audio_player.duration:.1f}s\n"
            f"识别词数: {len(recognized_words)}\n"
            f"参考位置: 第{accuracy_result.get('ref_index', 0)}个词\n",
        )
        self.detail_text.config(state=tk.DISABLED)

    def _update_loop(self):
        if not self._is_running:
            return

        if not self.audio_player.is_playing:
            self._on_practice_finished()
            return

        self._update_level_meter()
        self._update_ref_display()
        self._update_feedback()
        self.root.after(200, self._update_loop)

    def _start_shadowing(self):
        ref_text = self.ref_text_widget.get("1.0", tk.END).strip()
        if not ref_text:
            messagebox.showwarning("缺少输入", "请输入参考文本")
            return

        if not self._model_ready:
            messagebox.showwarning(
                "语音模型未就绪",
                "请先下载Vosk语音识别模型:\n"
                "https://alphacephei.com/vosk/models\n\n"
                "推荐: vosk-model-small-en-us-0.15 (~40MB)",
            )
            return

        if not self._ref_audio_path:
            self.status_label.config(text="⏳ 正在合成参考语音...")
            self.root.update()
            audio_path = self._generate_tts_audio(ref_text)
            if not audio_path:
                return
            self._ref_audio_path = audio_path

        try:
            self.audio_player.load_file(self._ref_audio_path)
        except Exception as e:
            messagebox.showerror("音频加载失败", str(e))
            return

        self.audio_player._device = self._selected_output_device
        print(f"[App] output device set to: {self._selected_output_device}")

        self.comparator = ShadowComparator(ref_text)
        self.comparator.set_estimated_timings(self.audio_player.duration)

        self.speech_recognizer.stop()
        self.speech_recognizer = SpeechRecognizer(sample_rate=16000)
        ok = self.speech_recognizer.initialize()
        print(f"[App] SpeechRecognizer init: {'OK' if ok else 'FAILED'}")

        self.audio_recorder = AudioRecorder(
            sample_rate=16000, block_size=4000,
            device=self._selected_input_device,
        )
        self.audio_recorder.start()
        print(f"[App] AudioRecorder started, device={self._selected_input_device}")

        self._stt_thread = self.speech_recognizer.start(
            self.audio_recorder.audio_queue
        )
        print(f"[App] STT thread started: {self._stt_thread is not None}")

        self._is_running = True
        self._practice_start_time = time.time()

        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.input_device_menu.config(state=tk.DISABLED)
        self.output_device_menu.config(state=tk.DISABLED)

        def on_audio_finished():
            self.root.after(0, self._on_practice_finished)

        self.audio_player.play(on_finished=on_audio_finished)

        self.status_label.config(text="🔴 训练中 — 请跟随音频大声跟读...")
        self.root.after(300, self._update_loop)

    def _stop_shadowing(self):
        self._is_running = False
        self.audio_player.stop()
        self.audio_recorder.stop()
        self.speech_recognizer.stop()
        self._update_button_states(False)
        self.status_label.config(text="⏹ 已停止")
        print("[App] shadowing stopped by user")

    def _on_practice_finished(self):
        if not self._is_running:
            return
        self._is_running = False
        self.audio_recorder.stop()
        self.speech_recognizer.stop()
        self._update_button_states(False)

        recognized_words = self.speech_recognizer.get_latest_words()
        ref_elapsed = self.audio_player.duration
        accuracy_result = self.comparator.compare_accuracy(
            recognized_words, ref_elapsed
        )
        score = accuracy_result.get("score", 0.0)

        print(f"[App] practice finished. recognized words: {len(recognized_words)}, accuracy: {score:.0%}")
        for w in recognized_words[:5]:
            print(f"  [{w['word']}] conf={w['conf']:.2f}")

        self.status_label.config(
            text=f"✅ 训练完成! 整体准确度: {score:.0%} | "
                 f"🟢{accuracy_result.get('green_count', 0)} "
                 f"🟡{accuracy_result.get('yellow_count', 0)} "
                 f"🔴{accuracy_result.get('red_count', 0)}"
        )

    def _update_button_states(self, is_running: bool):
        state = tk.DISABLED if is_running else tk.NORMAL
        readstate = "readonly" if not is_running else tk.DISABLED
        if is_running:
            self.btn_start.config(state=tk.DISABLED)
            self.btn_stop.config(state=tk.NORMAL)
        else:
            self.btn_start.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)
        self.input_device_menu.config(state=readstate)
        self.output_device_menu.config(state=readstate)

    def _on_close(self):
        self._is_running = False
        self.audio_player.stop()
        self.audio_recorder.stop()
        self.speech_recognizer.stop()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = ShadowingApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
