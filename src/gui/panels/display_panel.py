import customtkinter as ctk
import tkinter as tk
from src.gui.styles import C, FONT_FAMILY, draw_hex_indicator


class DisplayPanel(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C["bg_panel"], corner_radius=0)
        self.app = app
        self._ref_word_positions = []
        self._current_ref_idx = -1
        self._build()

    def _build(self):
        top_bar = tk.Canvas(
            self, height=2, bg=C["bg_panel"], highlightthickness=0,
        )
        top_bar.pack(fill=tk.X)
        top_bar.create_line(0, 0, 9999, 0, fill=C["cyan_dim"], width=1)

        left_frame = tk.Frame(self, bg=C["bg_panel"])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(12, 6), pady=10)

        left_header = tk.Frame(left_frame, bg=C["bg_panel"])
        left_header.pack(fill=tk.X)

        cvs1 = tk.Canvas(
            left_header, width=16, height=16,
            bg=C["bg_panel"], highlightthickness=0,
        )
        cvs1.pack(side=tk.LEFT)
        draw_hex_indicator(cvs1, 8, 8, size=5, color=C["cyan"])

        tk.Label(
            left_header, text="REFERENCE  ·  参考文本",
            font=(FONT_FAMILY, 10, "bold"),
            bg=C["bg_panel"], fg=C["fg_primary"],
        ).pack(side=tk.LEFT, padx=(2, 0))

        self.ref_display = ctk.CTkTextbox(
            left_frame, font=("Consolas", 12),
            fg_color=C["bg_input"], text_color=C["fg_secondary"],
            border_width=1, border_color=C["cyan_dim"],
            corner_radius=2,
            wrap="word", state="normal",
        )
        self.ref_display.pack(fill=tk.BOTH, expand=True, pady=(6, 0))
        self.ref_display.tag_config("past", foreground="#555572")
        self.ref_display.tag_config("current", foreground=C["cyan"],
                                     background="#004466")
        self.ref_display.tag_config("future", foreground="#666680")

        self.word_accuracy_frame = tk.Frame(left_frame, bg=C["bg_panel"])
        self.word_accuracy_frame.pack(fill=tk.X, pady=(8, 0))
        self.word_accuracy_canvas = tk.Canvas(
            self.word_accuracy_frame, height=28,
            bg=C["bg_panel"], highlightthickness=0,
        )
        self.word_accuracy_canvas.pack(fill=tk.X)
        self._accuracy_bar_ids = []
        self._total_word_count = 0

        legend = tk.Frame(left_frame, bg=C["bg_panel"])
        legend.pack(fill=tk.X, pady=(4, 0))

        for color, label in [(C["green"], "GOOD"), (C["yellow"], "FAIR"), (C["red"], "ERROR")]:
            dot = tk.Canvas(
                legend, width=10, height=10,
                bg=C["bg_panel"], highlightthickness=0,
            )
            dot.pack(side=tk.RIGHT, padx=(0, 2))
            draw_hex_indicator(dot, 5, 5, size=4, color=color)
            tk.Label(
                legend, text=label,
                font=(FONT_FAMILY, 8),
                bg=C["bg_panel"], fg=C["fg_dim"],
            ).pack(side=tk.RIGHT, padx=(0, 6))

        right_frame = tk.Frame(self, bg=C["bg_panel"])
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(6, 12), pady=10)

        right_header = tk.Frame(right_frame, bg=C["bg_panel"])
        right_header.pack(fill=tk.X)

        cvs2 = tk.Canvas(
            right_header, width=16, height=16,
            bg=C["bg_panel"], highlightthickness=0,
        )
        cvs2.pack(side=tk.LEFT)
        draw_hex_indicator(cvs2, 8, 8, size=5, color=C["orange"])

        tk.Label(
            right_header, text="YOUR SPEECH  ·  你的跟读",
            font=(FONT_FAMILY, 10, "bold"),
            bg=C["bg_panel"], fg=C["fg_primary"],
        ).pack(side=tk.LEFT, padx=(2, 0))

        self.user_display = ctk.CTkTextbox(
            right_frame, font=("Consolas", 12),
            fg_color=C["bg_input"], text_color=C["cyan"],
            border_width=1, border_color=C["orange_dim"],
            corner_radius=2,
            wrap="word", state="normal",
        )
        self.user_display.pack(fill=tk.BOTH, expand=True, pady=(6, 0))
        self.user_display.tag_config("green_word", foreground=C["green"])
        self.user_display.tag_config("yellow_word", foreground=C["yellow"])
        self.user_display.tag_config("red_word", foreground=C["red"])
        self.user_display.tag_config("current", foreground=C["cyan"],
                                      background="#004466")
        self.user_display.tag_config("low_conf", foreground=C["red"],
                                      underline=True)

        detail_frame = tk.Frame(right_frame, bg=C["bg_panel"])
        detail_frame.pack(fill=tk.X, pady=(8, 0))

        self.detail_text = ctk.CTkTextbox(
            detail_frame, font=("Consolas", 10),
            fg_color=C["bg_card"],
            text_color=C["fg_secondary"],
            border_width=1, border_color=C["fg_dim"],
            corner_radius=2,
            wrap="word", state="normal", height=65,
        )
        self.detail_text.pack(fill=tk.BOTH)

    def init_ref_display(self, reference_words: list):
        self.ref_display.delete("1.0", tk.END)
        self._ref_word_positions = []
        self._current_ref_idx = -1

        for word in reference_words:
            start = len(self.ref_display.get("1.0", tk.END)) - 1
            self.ref_display.insert(tk.END, word + " ", "future")
            end = len(self.ref_display.get("1.0", tk.END)) - 1
            self._ref_word_positions.append((start, end))

        mask = self.app.comparator._word_mask if self.app.comparator else []
        word_count = sum(mask) if mask else len(reference_words)
        print(f"[DisplayPanel] init_ref_display: tokens={len(reference_words)}, mask_sum={sum(mask) if mask else 'N/A'}, bars={word_count}")
        self._init_accuracy_bars(word_count)

    def _init_accuracy_bars(self, total: int):
        self.word_accuracy_canvas.delete("all")
        self._accuracy_bar_ids = []
        self._total_word_count = total

        canvas_w = self.word_accuracy_canvas.winfo_width()
        if canvas_w < 50:
            canvas_w = 400
        h = 22
        n = max(total, 1)
        bar_w = max(canvas_w // n, 2)

        print(f"[DisplayPanel] _init_accuracy_bars: total={total}, canvas_w={canvas_w}, bar_w={bar_w}")

        for i in range(total):
            x0 = i * bar_w
            x1 = x0 + bar_w - 2
            rid = self.word_accuracy_canvas.create_rectangle(
                x0, 3, x1, h,
                fill=C["fg_dim"], outline="",
            )
            self._accuracy_bar_ids.append(rid)

    def update_ref_highlight(self):
        if not self.app.comparator or not self.app._is_running:
            return

        ref_elapsed = self.app.audio_player.position
        current_idx = self.app.comparator.get_current_ref_word_index(ref_elapsed)

        if current_idx == self._current_ref_idx or current_idx >= len(self._ref_word_positions):
            return

        for i, (start, end) in enumerate(self._ref_word_positions):
            tag = "past" if i < current_idx else ("current" if i == current_idx else "future")
            self.ref_display.tag_remove("past", f"1.0+{start}c", f"1.0+{end}c")
            self.ref_display.tag_remove("current", f"1.0+{start}c", f"1.0+{end}c")
            self.ref_display.tag_remove("future", f"1.0+{start}c", f"1.0+{end}c")
            self.ref_display.tag_add(tag, f"1.0+{start}c", f"1.0+{end}c")

        self._current_ref_idx = current_idx

        if current_idx < len(self._ref_word_positions):
            start, _ = self._ref_word_positions[current_idx]
            self.ref_display.see(f"1.0+{start}c")

    def update_user_display(self, recognized_words, accuracy_result):
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

        self.user_display.see(tk.END)

    def update_detail(self, recognized_words, accuracy_result):
        self.detail_text.delete("1.0", tk.END)

        total = len(recognized_words)
        low_conf = sum(1 for w in recognized_words if w.get("conf", 1.0) < 0.7) if total > 0 else 0
        avg_conf = sum(w.get("conf", 0) for w in recognized_words) / max(total, 1)

        self.detail_text.insert(
            tk.END,
            f"PROGRESS: {self.app.audio_player.position:.1f}s / {self.app.audio_player.duration:.1f}s\n"
            f"WORDS DETECTED: {total}  |  REF POS: #{accuracy_result.get('ref_index', 0)}\n"
            f"CONFIDENCE: {avg_conf:.0%}  |  LOW-CONF WORDS: {low_conf}{' WARNING' if low_conf > 0 else ''}\n",
        )

    def update_word_accuracy_bars(self, result: dict):
        breakdown = result.get("breakdown", [])
        color_map = {
            "green": C["green"],
            "yellow": C["yellow"],
            "red": C["red"],
        }
        for i, item in enumerate(breakdown):
            if i >= len(self._accuracy_bar_ids):
                break
            fill = color_map.get(item.get("color", ""), C["fg_dim"])
            self.word_accuracy_canvas.itemconfig(
                self._accuracy_bar_ids[i], fill=fill
            )
