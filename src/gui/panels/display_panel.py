import customtkinter as ctk
import tkinter as tk
import re
import time
from src.gui.styles import C, FONT_FAMILY, draw_hex_indicator


class DisplayPanel(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C["bg_panel"], corner_radius=0)
        self.app = app
        self._ref_word_positions = []
        self._current_ref_idx = -1
        self._shadowing_idx = -1
        self._shadowed_words = {}    # {index: "green"|"yellow"|"red"}
        self._sample_idx = -1         # blue pacing cursor index
        self._last_sample_idx = -1
        self._sample_start_time = None  # when the independent timer started
        self._last_partial = ""
        self._build()

    def _build(self):
        top_bar = tk.Canvas(
            self, height=2, bg=C["bg_panel"], highlightthickness=0,
        )
        top_bar.pack(fill=tk.X)
        top_bar.create_line(0, 0, 9999, 0, fill=C["cyan_dim"], width=1)

        # ── MAIN: reference text (full height) ──
        ref_container = tk.Frame(self, bg=C["bg_panel"])
        ref_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=(10, 0))

        header = tk.Frame(ref_container, bg=C["bg_panel"])
        header.pack(fill=tk.X)

        cvs = tk.Canvas(header, width=16, height=16, bg=C["bg_panel"], highlightthickness=0)
        cvs.pack(side=tk.LEFT)
        draw_hex_indicator(cvs, 8, 8, size=5, color=C["cyan"])

        tk.Label(
            header, text="REFERENCE  ·  参考文本",
            font=(FONT_FAMILY, 10, "bold"),
            bg=C["bg_panel"], fg=C["fg_primary"],
        ).pack(side=tk.LEFT, padx=(2, 0))

        # Score display in header
        self.score_label = tk.Label(
            header, text="",
            font=(FONT_FAMILY, 9, "bold"),
            bg=C["bg_panel"], fg=C["fg_dim"],
        )
        self.score_label.pack(side=tk.RIGHT, padx=(0, 4))

        self.ref_display = ctk.CTkTextbox(
            ref_container, font=("Consolas", 16),
            fg_color=C["bg_input"], text_color=C["fg_secondary"],
            border_width=1, border_color=C["cyan_dim"],
            corner_radius=2,
            wrap="word", state="normal",
        )
        self.ref_display.pack(fill=tk.BOTH, expand=True, pady=(6, 0))
        # Tags for audio cursor (which word is being PLAYED)
        self.ref_display.tag_config("past", foreground="#555572")
        self.ref_display.tag_config("audio_cur", foreground=C["cyan"],
                                     background="#004466")
        self.ref_display.tag_config("future", foreground="#666680")
        # Tags for shadowing cursor (which word the USER is on)
        self.ref_display.tag_config("shadow_match", foreground=C["green"])
        self.ref_display.tag_config("shadow_medium", foreground=C["yellow"])
        self.ref_display.tag_config("shadow_miss", foreground=C["red"])
        self.ref_display.tag_config("sample_cur", foreground="#ffffff",
                                      background="#aa8800")
        self.ref_display.tag_config("shadow_cur", foreground="#ffffff",
                                      background="#0066aa")

        # ── BOTTOM: partial sentence + speed ──
        bottom = tk.Frame(self, bg=C["bg_panel"])
        bottom.pack(fill=tk.X, padx=12, pady=(6, 10))

        self.partial_label = tk.Label(
            bottom,
            font=("Consolas", 13, "italic"),
            bg=C["bg_input"], fg=C["cyan"],
            anchor="w", justify=tk.LEFT,
            height=2,
            relief=tk.FLAT,
            borderwidth=1,
            highlightbackground=C["cyan_dim"],
            highlightcolor=C["cyan_dim"],
            highlightthickness=1,
        )
        self.partial_label.pack(fill=tk.X, pady=(0, 4))

        # ── Legend: colour / cursor meanings ──
        legend = tk.Frame(bottom, bg=C["bg_panel"])
        legend.pack(fill=tk.X, pady=(0, 6))

        # Row 1: colour dots
        d1 = tk.Frame(legend, bg=C["bg_panel"])
        d1.pack(fill=tk.X)

        self._make_dot(d1, C["green"], "精准", "匹配距光标 ≤1词")
        self._make_dot(d1, C["yellow"], "稍偏", "匹配距光标 ≤3词")
        self._make_dot(d1, C["red"], "偏差", "匹配距光标 ≤5词")

        sep1 = tk.Label(d1, text="│", font=(FONT_FAMILY, 13),
                        bg=C["bg_panel"], fg=C["fg_dim"])
        sep1.pack(side=tk.LEFT, padx=(6, 2))

        self._make_dot(d1, "#aa8800", "跟读光标", "黄底=应跟读到的参考词", bg=True)
        self._make_dot(d1, "#004466", "音频光标", "蓝底=音频当前播放词", bg=True)

        # Row 2: short guide
        d2 = tk.Frame(legend, bg=C["bg_panel"])
        d2.pack(fill=tk.X, pady=(2, 0))
        tk.Label(
            d2, text="跟读指南：跟随黄色光标朗读，优先匹配离光标近的参考词，保持与音频播放节奏一致",
            font=(FONT_FAMILY, 15),
            bg=C["bg_panel"], fg=C["fg_dim"],
            anchor="w",
        ).pack(side=tk.LEFT)

        status_row = tk.Frame(bottom, bg=C["bg_panel"])
        status_row.pack(fill=tk.X)

        self.speed_indicator = tk.Label(
            status_row, text="",
            font=(FONT_FAMILY, 9, "bold"),
            bg=C["bg_panel"], fg=C["fg_dim"],
        )
        self.speed_indicator.pack(side=tk.LEFT)

        self.detail_text = ctk.CTkLabel(
            status_row, text="",
            font=(FONT_FAMILY, 9),
            text_color=C["fg_dim"],
        )
        self.detail_text.pack(side=tk.RIGHT)

    # ──────────────────────────────────────────────
    #  Public API
    # ──────────────────────────────────────────────

    @staticmethod
    def _make_dot(parent, color, label, tooltip, bg=False):
        """Add a coloured indicator dot + label to *parent*."""
        size = 14
        cvs = tk.Canvas(parent, width=size, height=size,
                        bg=C["bg_panel"], highlightthickness=0)
        cvs.pack(side=tk.LEFT, padx=(6, 1))
        if bg:
            cvs.create_rectangle(0, 0, size, size, fill=color, outline="")
        else:
            cvs.create_oval(2, 2, size-2, size-2, fill=color, outline="")
        tk.Label(parent, text=f"{label}",
                 font=(FONT_FAMILY, 13),
                 bg=C["bg_panel"], fg=color).pack(side=tk.LEFT)
        tk.Label(parent, text=f"({tooltip})",
                 font=(FONT_FAMILY, 13),
                 bg=C["bg_panel"], fg=C["fg_dim"]).pack(side=tk.LEFT, padx=(0, 4))

    def init_ref_display(self, reference_words: list):
        """Call once when shadowing starts."""
        self.ref_display.delete("1.0", tk.END)
        self._ref_word_positions = []
        self._current_ref_idx = -1
        self._shadowing_idx = -1
        self._shadowed_words = {}
        self._sample_idx = -1
        self._last_sample_idx = -1
        self._sample_start_time = None
        self._last_partial = ""

        for word in reference_words:
            start = len(self.ref_display.get("1.0", "end-1c"))
            self.ref_display.insert(tk.END, word + " ", "future")
            end = len(self.ref_display.get("1.0", "end-1c"))
            self._ref_word_positions.append((start, end))

        print(f"[Display] init with {len(reference_words)} words")
        self.partial_label.configure(text="")
        self.score_label.configure(text="")
        self.speed_indicator.configure(text="")
        self.detail_text.configure(text="")

    def update_ref_highlight(self):
        """Move the audio playback cursor (called every 100ms)."""
        if not self.app.comparator or not self.app._is_running:
            return

        ref_elapsed = self.app.audio_player.position
        current_idx = self.app.comparator.get_current_ref_word_index(ref_elapsed)

        if current_idx == self._current_ref_idx:
            return
        if current_idx >= len(self._ref_word_positions):
            print(f"[Display] ref highlight OOB: idx={current_idx} >= {len(self._ref_word_positions)}")
            current_idx = len(self._ref_word_positions) - 1

        print(f"[Display] ref highlight: pos={ref_elapsed:.2f}s idx={current_idx}")

        for i, (start, end) in enumerate(self._ref_word_positions):
            if i in self._shadowed_words:
                continue
            tag = "past" if i < current_idx else ("audio_cur" if i == current_idx else "future")
            for t in ("past", "audio_cur", "future"):
                self.ref_display.tag_remove(t, f"1.0+{start}c", f"1.0+{end}c")
            self.ref_display.tag_add(tag, f"1.0+{start}c", f"1.0+{end}c")

        self._current_ref_idx = current_idx
        if current_idx < len(self._ref_word_positions):
            start, _ = self._ref_word_positions[current_idx]
            self.ref_display.see(f"1.0+{start}c")

    def update_sample_cursor(self, audio_position: float) -> bool:
        """Move the blue pacing cursor on its own independent timer.

        The sample cursor starts at time=0 (first word) and advances at
        real-time speed.  Audio playback is NOT used; this is a separate
        clock.  Returns True when the cursor reaches the last word.
        """
        if not self.app.comparator or not self._ref_word_positions:
            return False

        # Lazy‑init the independent timer on the first call
        if self._sample_start_time is None:
            self._sample_start_time = time.time()

        threshold = 3.0
        try:
            from src.utils.config import get_config
            cfg = get_config().get("training", {})
            threshold = cfg.get("shadowing_lag", cfg.get("shadowing_timeout", 3.0))
        except Exception:
            pass

        elapsed = time.time() - self._sample_start_time
        sample_pos = max(0, elapsed - threshold)

        self._sample_idx = self.app.comparator.get_current_ref_word_index(sample_pos)

        # Guard OOB
        if self._sample_idx >= len(self._ref_word_positions):
            self._sample_idx = len(self._ref_word_positions) - 1

        # Check if sample cursor has reached the end
        finished = (self._sample_idx >= len(self._ref_word_positions) - 1 and
                    elapsed > threshold + 0.5)  # small grace period

        if self._sample_idx == self._last_sample_idx:
            return finished

        # Remove old tag
        if self._last_sample_idx >= 0 and self._last_sample_idx < len(self._ref_word_positions):
            s_start, s_end = self._ref_word_positions[self._last_sample_idx]
            self.ref_display.tag_remove("sample_cur", f"1.0+{s_start}c", f"1.0+{s_end}c")

        # Add new tag (unless word already shadowed)
        if self._sample_idx not in self._shadowed_words:
            s_start, s_end = self._ref_word_positions[self._sample_idx]
            self.ref_display.tag_add("sample_cur", f"1.0+{s_start}c", f"1.0+{s_end}c")

        self._last_sample_idx = self._sample_idx
        return finished

    def update_shadowing(self, partial_text: str, audio_position: float):
        """Match spoken words against reference text around the yellow sample cursor.

        For each new spoken word, search within ±match_red_distance around
        the sample cursor.  The closest matching reference word wins.
        Colour is determined by distance:
          ≤ match_green_distance  → green  (shadow_match)
          ≤ match_yellow_distance → yellow (shadow_medium)
          ≤ match_red_distance    → red    (shadow_miss)
        """
        if not partial_text or not partial_text.strip():
            self.partial_label.configure(text="")
            self._last_partial = ""
            return

        self.partial_label.configure(text=f"▎ {partial_text}")

        partial_words = re.findall(r"[a-zA-Z']+", partial_text.strip().lower())
        if not partial_words:
            return

        prev_words = re.findall(r"[a-zA-Z']+", self._last_partial.strip().lower()) if self._last_partial else []
        new_words = partial_words[len(prev_words):] if len(partial_words) > len(prev_words) else (
            partial_words if partial_words != prev_words else []
        )
        self._last_partial = partial_text
        if not new_words:
            return

        if not hasattr(self.app, "comparator") or not self.app.comparator:
            return
        ref_words = self.app.comparator.reference_words
        if not ref_words:
            return

        green_dist = 1
        yellow_dist = 3
        red_dist = 5
        try:
            from src.utils.config import get_config
            cfg = get_config().get("training", {})
            green_dist = int(cfg.get("match_green_distance", 1))
            yellow_dist = int(cfg.get("match_yellow_distance", 3))
            red_dist = int(cfg.get("match_red_distance", 5))
        except Exception:
            pass

        cursor = max(0, self._sample_idx)
        search_radius = max(green_dist, yellow_dist, red_dist)
        lo = max(0, cursor - search_radius)
        hi = min(len(ref_words), cursor + search_radius + 1)

        changed = False
        for new_w in new_words:
            candidates = []
            for i in range(lo, hi):
                if i in self._shadowed_words:
                    continue
                if ref_words[i].lower() == new_w:
                    dist = abs(i - cursor)
                    candidates.append((dist, i))
            if not candidates:
                continue
            candidates.sort(key=lambda x: x[0])
            dist, match_idx = candidates[0]

            if dist <= green_dist:
                color = "green"
                tag = "shadow_match"
            elif dist <= yellow_dist:
                color = "yellow"
                tag = "shadow_medium"
            elif dist <= red_dist:
                color = "red"
                tag = "shadow_miss"
            else:
                continue

            self._shadowed_words[match_idx] = color
            if match_idx > self._shadowing_idx:
                self._shadowing_idx = match_idx

            if match_idx < len(self._ref_word_positions):
                start, end = self._ref_word_positions[match_idx]
                for t in ("past", "audio_cur", "future", "sample_cur"):
                    self.ref_display.tag_remove(t, f"1.0+{start}c", f"1.0+{end}c")
                self.ref_display.tag_add(tag, f"1.0+{start}c", f"1.0+{end}c")

            changed = True

        if changed:
            self._update_score()

    def _update_score(self):
        green = sum(1 for v in self._shadowed_words.values() if v == "green")
        yellow = sum(1 for v in self._shadowed_words.values() if v == "yellow")
        red = sum(1 for v in self._shadowed_words.values() if v == "red")
        total = green + yellow + red
        pct = (green / total * 100) if total > 0 else 0
        self.score_label.configure(
            text=f"G:{green}  Y:{yellow}  R:{red}  {pct:.0f}%"
        )

    def update_speed_info(self, speed_result: dict):
        msg = speed_result.get("message", "")
        color = speed_result.get("color", "")
        if color == "green":
            self.speed_indicator.configure(text=f"● {msg}", fg=C["green"])
        elif color == "yellow":
            self.speed_indicator.configure(text=f"● {msg}", fg=C["yellow"])
        elif color == "red":
            self.speed_indicator.configure(text=f"● {msg}", fg=C["red"])
        else:
            self.speed_indicator.configure(text="", fg=C["fg_dim"])

    def get_shadowing_score(self) -> dict:
        green = sum(1 for v in self._shadowed_words.values() if v == "green")
        yellow = sum(1 for v in self._shadowed_words.values() if v == "yellow")
        red = sum(1 for v in self._shadowed_words.values() if v == "red")
        return {"green": green, "yellow": yellow, "red": red, "total": green + yellow + red}
