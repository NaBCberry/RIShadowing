import customtkinter as ctk
import tkinter as tk
from src.gui.styles import C, FONT_FAMILY, draw_hex_indicator


class FeedbackPanel(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C["bg_panel"], corner_radius=0)
        self.app = app
        self._build()

    def _build(self):
        top_bar = tk.Canvas(
            self, height=2, bg=C["bg_panel"], highlightthickness=0,
        )
        top_bar.pack(fill=tk.X)
        top_bar.create_line(0, 0, 9999, 0, fill=C["cyan_dim"], width=1)

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(padx=12, pady=10, fill=tk.X)

        speed_frame = tk.Frame(inner, bg=C["bg_panel"])
        speed_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        speed_header = tk.Frame(speed_frame, bg=C["bg_panel"])
        speed_header.pack(fill=tk.X)

        cvs1 = tk.Canvas(
            speed_header, width=16, height=16,
            bg=C["bg_panel"], highlightthickness=0,
        )
        cvs1.pack(side=tk.LEFT)
        draw_hex_indicator(cvs1, 8, 8, size=5, color=C["orange"], filled=False)

        tk.Label(
            speed_header, text="SPEED  ·  语速同步",
            font=(FONT_FAMILY, 10, "bold"),
            bg=C["bg_panel"], fg=C["fg_primary"],
        ).pack(side=tk.LEFT, padx=(2, 0))

        self.speed_canvas = tk.Canvas(
            speed_frame, height=44, bg=C["bg_card"],
            highlightthickness=0,
        )
        self.speed_canvas.pack(fill=tk.X, pady=(6, 0))

        self._speed_bar = self.speed_canvas.create_rectangle(
            0, 0, 10, 44, fill=C["fg_dim"], outline=""
        )
        self._speed_glow = self.speed_canvas.create_rectangle(
            0, 0, 0, 44, fill=C["fg_dim"], outline="", stipple="gray25"
        )
        self._speed_text = self.speed_canvas.create_text(
            14, 22, anchor=tk.W, text="AWAITING INPUT...",
            fill=C["fg_primary"],
            font=(FONT_FAMILY, 10, "bold"),
        )

        accuracy_frame = tk.Frame(inner, bg=C["bg_panel"])
        accuracy_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(8, 0))

        acc_header = tk.Frame(accuracy_frame, bg=C["bg_panel"])
        acc_header.pack(fill=tk.X)

        cvs2 = tk.Canvas(
            acc_header, width=16, height=16,
            bg=C["bg_panel"], highlightthickness=0,
        )
        cvs2.pack(side=tk.LEFT)
        draw_hex_indicator(cvs2, 8, 8, size=5, color=C["cyan"], filled=False)

        tk.Label(
            acc_header, text="ACCURACY  ·  准确度",
            font=(FONT_FAMILY, 10, "bold"),
            bg=C["bg_panel"], fg=C["fg_primary"],
        ).pack(side=tk.LEFT, padx=(2, 0))

        self.accuracy_canvas = tk.Canvas(
            accuracy_frame, height=44, bg=C["bg_card"],
            highlightthickness=0,
        )
        self.accuracy_canvas.pack(fill=tk.X, pady=(6, 0))

        self._accuracy_bar = self.accuracy_canvas.create_rectangle(
            0, 0, 10, 44, fill=C["fg_dim"], outline=""
        )
        self._accuracy_glow = self.accuracy_canvas.create_rectangle(
            0, 0, 0, 44, fill=C["fg_dim"], outline="", stipple="gray25"
        )
        self._accuracy_text = self.accuracy_canvas.create_text(
            14, 22, anchor=tk.W, text="AWAITING INPUT...",
            fill=C["fg_primary"],
            font=(FONT_FAMILY, 10, "bold"),
        )

    def update_speed(self, result: dict):
        color = result.get("color", C["fg_dim"])
        self.speed_canvas.itemconfig(self._speed_bar, fill=color)
        self.speed_canvas.itemconfig(self._speed_glow, fill=color)

        gap = abs(result.get("gap", 0))
        if gap <= 1:
            bar_width = 25
        elif gap <= 2:
            bar_width = 60
        else:
            bar_width = 100

        canvas_w = self.speed_canvas.winfo_width()
        if canvas_w < 50:
            canvas_w = 200
        bar_w = int(canvas_w * bar_width / 100)
        self.speed_canvas.coords(self._speed_bar, 0, 0, bar_w, 44)
        self.speed_canvas.coords(self._speed_glow, 0, 18, min(bar_w + 6, canvas_w), 26)
        self.speed_canvas.itemconfig(self._speed_text, text=result.get("message", ""))

    def update_accuracy(self, result: dict):
        color = result.get("color", C["fg_dim"])
        self.accuracy_canvas.itemconfig(self._accuracy_bar, fill=color)
        self.accuracy_canvas.itemconfig(self._accuracy_glow, fill=color)

        score = result.get("score", 0.0)
        canvas_w = self.accuracy_canvas.winfo_width()
        if canvas_w < 50:
            canvas_w = 200
        bar_w = int(canvas_w * score)
        self.accuracy_canvas.coords(self._accuracy_bar, 0, 0, bar_w, 44)
        self.accuracy_canvas.coords(self._accuracy_glow, 0, 18, min(bar_w + 6, canvas_w), 26)
        self.accuracy_canvas.itemconfig(self._accuracy_text, text=result.get("message", ""))
