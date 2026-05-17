import customtkinter as ctk
import tkinter as tk
from src.gui.styles import C, FONT_FAMILY


class DisplayPanel(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C["bg_panel"], corner_radius=8)
        self.app = app
        self._build()

    def _build(self):
        left_frame = tk.Frame(self, bg=C["bg_panel"])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 4), pady=10)

        tk.Label(
            left_frame, text="📖 参考文本 (Reference)",
            font=(FONT_FAMILY, 11, "bold"),
            bg=C["bg_panel"], fg=C["fg_primary"],
        ).pack(anchor=tk.W)

        self.ref_display = ctk.CTkTextbox(
            left_frame, font=("Consolas", 12),
            fg_color=C["bg_input"], text_color=C["fg_secondary"],
            wrap="word", state=tk.DISABLED,
        )
        self.ref_display.pack(fill=tk.BOTH, expand=True, pady=(4, 0))
        self.ref_display.tag_config("past", foreground="#6272a4")
        self.ref_display.tag_config("current", foreground="#f1fa8c",
                                     background="#44447a")
        self.ref_display.tag_config("future", foreground="#6a6a8a")

        self.word_accuracy_frame = tk.Frame(left_frame, bg=C["bg_panel"])
        self.word_accuracy_frame.pack(fill=tk.X, pady=(6, 0))
        self.word_accuracy_canvas = tk.Canvas(
            self.word_accuracy_frame, height=30,
            bg=C["bg_panel"], highlightthickness=0,
        )
        self.word_accuracy_canvas.pack(fill=tk.X)

        tk.Label(
            left_frame, text="🟢 准确  🟡 一般  🔴 错误",
            font=(FONT_FAMILY, 9),
            bg=C["bg_panel"], fg=C["fg_secondary"],
        ).pack(anchor=tk.E, pady=(2, 0))

        right_frame = tk.Frame(self, bg=C["bg_panel"])
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(4, 10), pady=10)

        tk.Label(
            right_frame, text="🎙 你的跟读 (Your Speech)",
            font=(FONT_FAMILY, 11, "bold"),
            bg=C["bg_panel"], fg=C["fg_primary"],
        ).pack(anchor=tk.W)

        self.user_display = ctk.CTkTextbox(
            right_frame, font=("Consolas", 12),
            fg_color=C["bg_input"], text_color=C["accent"],
            wrap="word", state=tk.DISABLED,
        )
        self.user_display.pack(fill=tk.BOTH, expand=True, pady=(4, 0))
        self.user_display.tag_config("green_word", foreground="#50fa7b")
        self.user_display.tag_config("yellow_word", foreground="#f1fa8c")
        self.user_display.tag_config("red_word", foreground="#ff5555")
        self.user_display.tag_config("current", foreground="#f1fa8c",
                                      background="#44447a")
        self.user_display.tag_config("low_conf", foreground="#ff5555",
                                      underline=True)

        tag_frame = tk.Frame(right_frame, bg=C["bg_panel"])
        tag_frame.pack(fill=tk.X, pady=(6, 0))

        self.detail_text = ctk.CTkTextbox(
            tag_frame, font=("Consolas", 10),
            fg_color=C["bg_input"], text_color=C["fg_secondary"],
            wrap="word", state=tk.DISABLED, height=70,
        )
        self.detail_text.pack(fill=tk.BOTH)


    def update_ref_display(self):
        if not self.app.comparator or not self.app._is_running:
            return

        ref_elapsed = self.app.audio_player.position
        words_with_status = self.app.comparator.get_reference_words_for_display(ref_elapsed)

        self.ref_display.configure(state=tk.NORMAL)
        self.ref_display.delete("1.0", tk.END)

        for word, status, idx in words_with_status:
            tag = status
            self.ref_display.insert(tk.END, word + " ", tag)

        self.ref_display.configure(state=tk.DISABLED)

    def update_user_display(self, recognized_words, accuracy_result):
        self.user_display.configure(state=tk.NORMAL)
        self.user_display.delete("1.0", tk.END)

        breakdown = accuracy_result.get("breakdown", [])
        for i, item in enumerate(breakdown):
            word = item.get("user_word", "")
            if word:
                if i < len(recognized_words) and recognized_words[i].get("conf", 1.0) < 0.7:
                    self.user_display.insert(tk.END, word, "low_conf")
                    self.user_display.insert(tk.END, "* ")
                else:
                    color_tag = f"{item.get('color', '')}_word"
                    self.user_display.insert(tk.END, word + " ", color_tag)

        partial = self.app.speech_recognizer.partial_text
        if partial:
            if breakdown:
                self.user_display.insert(tk.END, "| ")
            self.user_display.insert(tk.END, partial, "current")

        self.user_display.configure(state=tk.DISABLED)
        self.user_display.see(tk.END)

    def update_detail(self, recognized_words, accuracy_result):
        self.detail_text.configure(state=tk.NORMAL)
        self.detail_text.delete("1.0", tk.END)

        total = len(recognized_words)
        low_conf = sum(1 for w in recognized_words if w.get("conf", 1.0) < 0.7) if total > 0 else 0
        avg_conf = sum(w.get("conf", 0) for w in recognized_words) / max(total, 1)

        self.detail_text.insert(
            tk.END,
            f"进度: {self.app.audio_player.position:.1f}s / {self.app.audio_player.duration:.1f}s\n"
            f"识别词数: {total}\n"
            f"参考位置: 第{accuracy_result.get('ref_index', 0)}个词\n"
            f"发音置信度: {avg_conf:.0%}  |  低置信度词: {low_conf}{' 🔴' if low_conf > 0 else ''}\n",
        )
        self.detail_text.configure(state=tk.DISABLED)

    def update_word_accuracy_bars(self, result: dict):
        self.word_accuracy_canvas.delete("all")
        breakdown = result.get("breakdown", [])
        canvas_w = self.word_accuracy_canvas.winfo_width()
        if canvas_w < 50:
            canvas_w = 400
        h = 24
        n = max(len(breakdown), 1)
        bar_w = max(canvas_w // n, 2)

        color_map = {
            "green": C["green"],
            "yellow": C["yellow"],
            "red": C["red"],
        }

        for i, item in enumerate(breakdown):
            x0 = i * bar_w
            x1 = x0 + bar_w - 1
            fill = color_map.get(item.get("color", ""), C["gray"])
            self.word_accuracy_canvas.create_rectangle(
                x0, 3, x1, h, fill=fill, outline=""
            )
