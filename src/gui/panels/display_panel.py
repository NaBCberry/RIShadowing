import customtkinter as ctk
import tkinter as tk
import re
from src.gui.styles import C, FONT_FAMILY, draw_hex_indicator


class DisplayPanel(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C["bg_panel"], corner_radius=0)
        self.app = app
        self._ref_word_positions = []
        self._current_ref_idx = -1
        self._shadowing_idx = -1
        self._shadowed_words = {}    # {index: "green"|"red"}
        self._sample_idx = -1         # blue pacing cursor index
        self._last_sample_idx = -1
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
        self.ref_display.tag_config("shadow_miss", foreground=C["red"])
        self.ref_display.tag_config("sample_cur", foreground="#ffffff",
                                     background="#004488")
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
        self.partial_label.pack(fill=tk.X, pady=(0, 6))

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

    def init_ref_display(self, reference_words: list):
        """Call once when shadowing starts."""
        self.ref_display.delete("1.0", tk.END)
        self._ref_word_positions = []
        self._current_ref_idx = -1
        self._shadowing_idx = -1
        self._shadowed_words = {}
        self._sample_idx = -1
        self._last_sample_idx = -1
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

    def update_sample_cursor(self, audio_position: float):
        """Move the blue pacing cursor (lagging behind audio by timeout seconds)."""
        if not self.app.comparator:
            return

        threshold = 3.0
        try:
            from src.utils.config import get_config
            threshold = get_config().get("training", {}).get("shadowing_timeout", 3.0)
        except Exception:
            pass

        sample_pos = max(0, audio_position - threshold)
        self._sample_idx = self.app.comparator.get_current_ref_word_index(sample_pos)

        if self._sample_idx == self._last_sample_idx:
            return
        if self._sample_idx >= len(self._ref_word_positions):
            return

        # Remove old sample tag
        if self._last_sample_idx >= 0 and self._last_sample_idx < len(self._ref_word_positions):
            s_start, s_end = self._ref_word_positions[self._last_sample_idx]
            self.ref_display.tag_remove("sample_cur", f"1.0+{s_start}c", f"1.0+{s_end}c")

        # Add new sample tag (unless that word is already shadowed)
        if self._sample_idx not in self._shadowed_words:
            s_start, s_end = self._ref_word_positions[self._sample_idx]
            self.ref_display.tag_add("sample_cur", f"1.0+{s_start}c", f"1.0+{s_end}c")

        self._last_sample_idx = self._sample_idx

    def update_shadowing(self, partial_text: str, audio_position: float):
        """Process new partial text & advance shadowing cursor.

        Called every 100ms from the update loop.
        """
        if not partial_text or not partial_text.strip():
            self.partial_label.configure(text="")
            self._last_partial = ""
            return

        self.partial_label.configure(text=f"▎ {partial_text}")

        # Tokenize the partial text to get words
        partial_words = re.findall(r"[a-zA-Z']+", partial_text.strip().lower())

        # Check if we have a NEW word compared to last partial
        if not partial_words:
            return

        latest = partial_words[-1]
        prev_words = re.findall(r"[a-zA-Z']+", self._last_partial.strip().lower()) if self._last_partial else []
        is_new = (not prev_words) or (len(partial_words) > len(prev_words)) or (
            latest != (prev_words[-1] if prev_words else "")
        )

        if not is_new:
            self._last_partial = partial_text
            return

        self._last_partial = partial_text

        # Look for the new word in reference text, starting from shadowing_idx + 1
        if not hasattr(self.app, "comparator") or not self.app.comparator:
            return

        ref_words = self.app.comparator.reference_words
        if not ref_words:
            return

        start_search = max(0, self._shadowing_idx + 1)
        end_search = min(len(ref_words), start_search + 3)  # look at 3 words ahead (current + 2)

        match_idx = -1
        for i in range(start_search, end_search):
            if i < len(ref_words) and ref_words[i].lower() == latest:
                match_idx = i
                break

        if match_idx < 0:
            return

        # Move shadowing cursor
        self._shadowing_idx = match_idx

        # Check timing against reference audio timestamp
        threshold = 3.0
        try:
            from src.utils.config import get_config
            cfg = get_config()
            threshold = cfg.get("training", {}).get("shadowing_timeout", 3.0)
        except Exception:
            pass

        # Get the word timestamp from comparator
        timing = self.app.comparator._word_timings
        word_time = 0.0
        if timing and match_idx < len(timing):
            word_time = timing[match_idx].get("start", 0.0)

        diff = abs(word_time - audio_position)
        is_green = diff <= threshold

        # Highlight the matched word
        self._shadowed_words[match_idx] = "green" if is_green else "red"

        if match_idx < len(self._ref_word_positions):
            start, end = self._ref_word_positions[match_idx]
            # Remove audio cursor / future / past tags from this word
            self.ref_display.tag_remove("past", f"1.0+{start}c", f"1.0+{end}c")
            self.ref_display.tag_remove("audio_cur", f"1.0+{start}c", f"1.0+{end}c")
            self.ref_display.tag_remove("future", f"1.0+{start}c", f"1.0+{end}c")
            # Apply shadowing color
            tag = "shadow_match" if is_green else "shadow_miss"
            self.ref_display.tag_add(tag, f"1.0+{start}c", f"1.0+{end}c")

        # Update score display
        self._update_score()

    def _update_score(self):
        green = sum(1 for v in self._shadowed_words.values() if v == "green")
        red = sum(1 for v in self._shadowed_words.values() if v == "red")
        total = green + red
        pct = (green / total * 100) if total > 0 else 0
        self.score_label.configure(
            text=f"G:{green}  R:{red}  {pct:.0f}%"
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
        red = sum(1 for v in self._shadowed_words.values() if v == "red")
        return {"green": green, "red": red, "total": green + red}
