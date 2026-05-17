import customtkinter as ctk
import tkinter as tk
from src.gui.styles import C, FONT_FAMILY


class FeedbackPanel(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C["bg_panel"], corner_radius=8)
        self.app = app
        self._build()

    def _build(self):
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(padx=10, pady=10, fill=tk.X)

        speed_frame = tk.Frame(inner, bg=C["bg_panel"])
        speed_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        tk.Label(
            speed_frame, text="⏱ 速度 (Speed)",
            font=(FONT_FAMILY, 11, "bold"),
            bg=C["bg_panel"], fg=C["fg_primary"],
        ).pack(anchor=tk.W)

        self.speed_canvas = tk.Canvas(
            speed_frame, height=48, bg=C["bg_panel"],
            highlightthickness=0,
        )
        self.speed_canvas.pack(fill=tk.X, pady=(4, 0))
        self._speed_bar = self.speed_canvas.create_rectangle(
            0, 0, 10, 48, fill=C["gray"], outline=""
        )
        self._speed_text = self.speed_canvas.create_text(
            10, 24, anchor=tk.W, text="等待开始...",
            fill=C["fg_primary"],
            font=(FONT_FAMILY, 10, "bold"),
        )

        accuracy_frame = tk.Frame(inner, bg=C["bg_panel"])
        accuracy_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))

        tk.Label(
            accuracy_frame, text="🎯 准确度 (Accuracy)",
            font=(FONT_FAMILY, 11, "bold"),
            bg=C["bg_panel"], fg=C["fg_primary"],
        ).pack(anchor=tk.W)

        self.accuracy_canvas = tk.Canvas(
            accuracy_frame, height=48, bg=C["bg_panel"],
            highlightthickness=0,
        )
        self.accuracy_canvas.pack(fill=tk.X, pady=(4, 0))
        self._accuracy_bar = self.accuracy_canvas.create_rectangle(
            0, 0, 10, 48, fill=C["gray"], outline=""
        )
        self._accuracy_text = self.accuracy_canvas.create_text(
            10, 24, anchor=tk.W, text="等待开始...",
            fill=C["fg_primary"],
            font=(FONT_FAMILY, 10, "bold"),
        )

    def update_speed(self, result: dict):
        color = result.get("color", C["gray"])
        self.speed_canvas.itemconfig(self._speed_bar, fill=color)
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
        self.speed_canvas.coords(self._speed_bar, 0, 0, bar_w, 48)
        self.speed_canvas.itemconfig(self._speed_text, text=result.get("message", ""))

    def update_accuracy(self, result: dict):
        color = result.get("color", C["gray"])
        self.accuracy_canvas.itemconfig(self._accuracy_bar, fill=color)
        score = result.get("score", 0.0)
        canvas_w = self.accuracy_canvas.winfo_width()
        if canvas_w < 50:
            canvas_w = 200
        bar_w = int(canvas_w * score)
        self.accuracy_canvas.coords(self._accuracy_bar, 0, 0, bar_w, 48)
        self.accuracy_canvas.itemconfig(self._accuracy_text, text=result.get("message", ""))
