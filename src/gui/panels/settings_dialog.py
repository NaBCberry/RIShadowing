import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from src.gui.styles import C, FONT_FAMILY, draw_hex_indicator
from src.utils.error_diagnosis import ERROR_DATABASE, show_error_dialog


class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("SETTINGS / 设置")
        self.geometry("560x480")
        self.resizable(False, False)
        self.configure(fg_color=C["bg_dark"])

        self._build()
        self.grab_set()

    def _build(self):
        header_frame = tk.Frame(self, bg=C["bg_dark"], height=38)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        border_cvs = tk.Canvas(
            header_frame, height=38, bg=C["bg_dark"],
            highlightthickness=0,
        )
        border_cvs.pack(fill=tk.BOTH)
        border_cvs.create_line(0, 36, 9999, 36, fill=C["cyan_dim"], width=1)

        cvs_h = tk.Canvas(
            header_frame, width=16, height=38,
            bg=C["bg_dark"], highlightthickness=0,
        )
        cvs_h.place(x=10, y=0)
        draw_hex_indicator(cvs_h, 8, 19, size=6, color=C["cyan"])

        tk.Label(
            header_frame, text="SETTINGS  ·  设置",
            font=(FONT_FAMILY, 12, "bold"),
            bg=C["bg_dark"], fg=C["fg_primary"],
        ).place(x=28, y=8)

        body = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
        )
        body.pack(fill=tk.BOTH, expand=True, padx=16, pady=(8, 0))

        self._build_countdown_section(body)
        self._build_dev_section(body)

    def _build_countdown_section(self, body):
        section = ctk.CTkFrame(body, fg_color=C["bg_card"])
        section.pack(fill=tk.X, pady=(0, 8))

        header = tk.Frame(section, bg=C["bg_card"])
        header.pack(fill=tk.X, padx=10, pady=(8, 2))

        cvs = tk.Canvas(header, width=14, height=14, bg=C["bg_card"], highlightthickness=0)
        cvs.pack(side=tk.LEFT)
        draw_hex_indicator(cvs, 7, 7, size=5, color=C["cyan"], filled=False)

        tk.Label(
            header, text="COUNTDOWN  ·  倒计时设置",
            font=(FONT_FAMILY, 11, "bold"),
            bg=C["bg_card"], fg=C["fg_primary"],
        ).pack(side=tk.LEFT, padx=(4, 0))

        row = tk.Frame(section, bg=C["bg_card"])
        row.pack(fill=tk.X, padx=10, pady=(4, 8))

        tk.Label(
            row, text="倒计时秒数 (0.5-10):",
            font=(FONT_FAMILY, 10),
            bg=C["bg_card"], fg=C["fg_secondary"],
        ).pack(side=tk.LEFT)

        from src.utils.config import get_config
        cfg = get_config()
        current = cfg.get("training", {}).get("countdown_seconds", 3.0)

        self._countdown_var = tk.StringVar(value=str(current))
        ctk.CTkEntry(
            row,
            textvariable=self._countdown_var,
            font=(FONT_FAMILY, 10),
            fg_color=C["bg_input"],
            text_color=C["fg_primary"],
            border_width=1,
            border_color=C["fg_dim"],
            corner_radius=2,
            width=80,
        ).pack(side=tk.LEFT, padx=(8, 0))

        ctk.CTkButton(
            row, text="SAVE",
            font=(FONT_FAMILY, 9, "bold"),
            fg_color=C["cyan_dim"],
            hover_color=C["cyan"],
            text_color=C["fg_primary"],
            border_width=1,
            border_color=C["cyan_dim"],
            corner_radius=2,
            width=60, height=26,
            command=self._save_countdown,
        ).pack(side=tk.RIGHT, padx=(8, 0))

    def _save_countdown(self):
        try:
            val = float(self._countdown_var.get())
            val = max(0.5, min(val, 10.0))
            from src.utils.config import get_config
            import json
            from src.utils.paths import get_config_path
            cfg = get_config()
            cfg.setdefault("training", {})["countdown_seconds"] = val

            try:
                with open(get_config_path(), "w", encoding="utf-8") as f:
                    json.dump(cfg, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("SAVED", f"倒计时已设为 {val:.1f} 秒，下次开始跟读时生效")
            except PermissionError:
                messagebox.showwarning("PERMISSION",
                    "无法写入配置文件（安装目录只读）。\n"
                    "倒计时设置将在本次会话中生效，但重启后会恢复默认值。")
        except ValueError:
            messagebox.showwarning("INVALID", "请输入有效数字")

    def _build_dev_section(self, body):
        section = ctk.CTkFrame(body, fg_color=C["bg_card"])
        section.pack(fill=tk.X, pady=(0, 8))

        header = tk.Frame(section, bg=C["bg_card"])
        header.pack(fill=tk.X, padx=10, pady=(8, 2))

        cvs = tk.Canvas(header, width=14, height=14, bg=C["bg_card"], highlightthickness=0)
        cvs.pack(side=tk.LEFT)
        draw_hex_indicator(cvs, 7, 7, size=5, color=C["orange"], filled=False)

        tk.Label(
            header, text="DEV OPTIONS  ·  开发人员选项",
            font=(FONT_FAMILY, 11, "bold"),
            bg=C["bg_card"], fg=C["fg_primary"],
        ).pack(side=tk.LEFT, padx=(4, 0))

        hint = tk.Label(
            section,
            text="点击下方按钮可手动触发错误诊断弹窗，用于测试错误提示界面",
            font=(FONT_FAMILY, 9),
            bg=C["bg_card"], fg=C["fg_dim"],
            justify=tk.LEFT,
        )
        hint.pack(fill=tk.X, padx=10, pady=(2, 4))

        btn_frame = tk.Frame(section, bg=C["bg_card"])
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 8))

        for i, entry in enumerate(ERROR_DATABASE):
            btn = ctk.CTkButton(
                btn_frame,
                text=f"{entry['code']} — {entry['description']}",
                font=(FONT_FAMILY, 9),
                fg_color=C["button_dim"],
                hover_color=C["bg_hover"],
                text_color=C["fg_secondary"],
                border_width=1,
                border_color=C["fg_dim"],
                corner_radius=2,
                anchor="w",
                command=lambda e=entry: self._trigger_error(e),
            )
            btn.pack(fill=tk.X, pady=1)

    def _trigger_error(self, entry):
        dummy = {
            "code": entry["code"],
            "description": entry["description"],
            "solution": entry["solution"],
            "traceback": f"Traceback (模拟):\n  File \"app.py\", line 99\n    raise RuntimeError('{entry['code']}')\nRuntimeError: {entry['description']}",
            "console": (
                f"[App] Starting R.I. Shadowing Practice v1.2\n"
                f"[Config] generated config.json\n"
                f"[App] Vosk model loaded: vosk-model-small-en-us-0.15\n"
                f"[Devices] Found 15 input, 22 output devices\n"
                f"ERROR: {entry['description']}\n"
                f"[System] Process terminated with code 1"
            ),
        }
        show_error_dialog(dummy)
