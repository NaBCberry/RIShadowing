import customtkinter as ctk
import tkinter as tk
import os
from tkinter import messagebox, filedialog
from typing import Optional
from src.gui.styles import C, FONT_FAMILY, draw_hex_indicator
from src.models.material import (
    Material, init_db, list_materials, add_material,
    update_material, delete_material, get_material, get_all_topics,
)


class MaterialPanel(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C["bg_panel"], corner_radius=0)
        self.app = app
        self._materials = []
        self._current_material = None
        self._collapsed = True
        self._build()

    def _build(self):
        top_bar = tk.Canvas(
            self, height=2, bg=C["bg_panel"], highlightthickness=0,
        )
        top_bar.pack(fill=tk.X)
        top_bar.create_line(0, 0, 9999, 0, fill=C["orange_dim"], width=1)

        self._header = ctk.CTkFrame(self, fg_color="transparent")
        self._header.pack(fill=tk.X, padx=12, pady=(10, 4))

        hex_cvs = tk.Canvas(
            self._header, width=18, height=18,
            bg=C["bg_panel"], highlightthickness=0,
        )
        hex_cvs.pack(side=tk.LEFT)
        draw_hex_indicator(hex_cvs, 9, 9, size=6, color=C["gold"], filled=False)

        self._toggle_btn = ctk.CTkButton(
            self._header, text="MATERIAL LIBRARY  ▸",
            font=(FONT_FAMILY, 10, "bold"),
            fg_color="transparent", hover_color=C["bg_hover"],
            text_color=C["fg_secondary"],
            anchor="w",
            command=self._toggle,
        )
        self._toggle_btn.pack(side=tk.LEFT, fill=tk.X, padx=(4, 0))

        self._body = ctk.CTkFrame(self, fg_color="transparent")

    def _toggle(self):
        self._collapsed = not self._collapsed
        if self._collapsed:
            self._body.pack_forget()
            self._toggle_btn.configure(text="MATERIAL LIBRARY  ▸")
        else:
            self._body.pack(fill=tk.X, padx=12, pady=(0, 8),
                            after=self._header)
            self._refresh_body()
            self._toggle_btn.configure(text="MATERIAL LIBRARY  ▾")

    def _refresh_body(self):
        for w in self._body.winfo_children():
            w.destroy()

        toolbar = ctk.CTkFrame(self._body, fg_color="transparent")
        toolbar.pack(fill=tk.X, pady=(0, 6))

        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *a: self._refresh_body())

        ctk.CTkEntry(
            toolbar,
            textvariable=self.search_var,
            placeholder_text="SEARCH...",
            font=(FONT_FAMILY, 9),
            fg_color=C["bg_input"],
            text_color=C["fg_primary"],
            border_width=1,
            border_color=C["fg_dim"],
            corner_radius=2,
            width=130, height=28,
        ).pack(side=tk.LEFT, padx=(0, 6))

        ctk.CTkButton(
            toolbar, text="ADD",
            font=(FONT_FAMILY, 9, "bold"),
            fg_color=C["button_secondary"],
            hover_color=C["bg_hover"],
            text_color=C["fg_primary"],
            border_width=1,
            border_color=C["cyan_dim"],
            corner_radius=2,
            width=60, height=28,
            command=self._add_material,
        ).pack(side=tk.RIGHT, padx=(4, 0))

        ctk.CTkButton(
            toolbar, text="DEL",
            font=(FONT_FAMILY, 9, "bold"),
            fg_color=C["button_stop"],
            hover_color=C["button_stop_hover"],
            text_color=C["fg_primary"],
            border_width=1,
            border_color=C["red_dim"],
            corner_radius=2,
            width=50, height=28,
            command=self._delete_material,
        ).pack(side=tk.RIGHT, padx=(4, 0))

        search = self.search_var.get().strip() or None
        self._materials = list_materials(search=search)

        list_frame = ctk.CTkScrollableFrame(
            self._body,
            fg_color=C["bg_input"],
            height=110,
            corner_radius=2,
        )
        list_frame.pack(fill=tk.X, pady=(0, 2))

        if not self._materials:
            ctk.CTkLabel(
                list_frame,
                text="LIBRARY EMPTY — CLICK [ADD] TO IMPORT MATERIALS",
                font=(FONT_FAMILY, 9),
                text_color=C["fg_dim"],
            ).pack(pady=14)
            return

        for m in self._materials:
            row = ctk.CTkFrame(list_frame, fg_color="transparent")
            row.pack(fill=tk.X, pady=1)

            label_text = f"  {m.title[:35]}"
            if m.topic:
                label_text += f"  [{m.topic}]"
            if m.duration > 0:
                label_text += f"  {m.duration:.0f}s"
            label_text += f"  | {m.practice_count} runs"
            if m.best_score > 0:
                label_text += f"  | BEST {m.best_score:.0%}"

            ctk.CTkButton(
                row, text=label_text,
                font=(FONT_FAMILY, 9),
                fg_color=C["bg_card"],
                hover_color=C["bg_hover"],
                text_color=C["fg_primary"],
                anchor="w",
                corner_radius=2,
                command=lambda mid=m.id: self._select_material(mid),
            ).pack(fill=tk.X)

    def _refresh(self):
        if not self._collapsed:
            self._refresh_body()

    def _select_material(self, material_id: int):
        material = get_material(material_id)
        if not material:
            return
        self._current_material = material
        self.app.input_panel.set_text(material.text)
        if material.audio_path and os.path.exists(material.audio_path):
            self.app._ref_audio_path = material.audio_path
            try:
                self.app.audio_player.load_file(material.audio_path)
                self.app.set_status(
                    f"LOADED: {material.title} — DURATION: {material.duration:.1f}s"
                )
                self.app._mode = "shadowing"
                self.app.btn_start_shadowing.configure(state=tk.NORMAL)
                self.app.btn_generate.configure(state=tk.DISABLED)
                self.app._on_audio_loaded(material.audio_path)
            except Exception as e:
                print(f"[MaterialPanel] load audio error: {e}")
        else:
            self.app._ref_audio_path = None
            self.app.set_status(
                f"SELECTED: {material.title} (NO AUDIO — WILL USE TTS)"
            )
        print(f"[MaterialPanel] selected: {material.title}")

    def _add_material(self):
        dialog = MaterialDialog(self, title="ADD MATERIAL")
        self.wait_window(dialog)
        if dialog.result:
            try:
                mid = add_material(dialog.result)
                print(f"[MaterialPanel] added material id={mid}")
                self._refresh()
            except Exception as e:
                messagebox.showerror("ADD FAILED", str(e))

    def _delete_material(self):
        if not self._current_material:
            messagebox.showinfo("INFO", "SELECT A MATERIAL FIRST")
            return
        if messagebox.askyesno("CONFIRM", f'DELETE "{self._current_material.title}"?'):
            delete_material(self._current_material.id)
            self._current_material = None
            self._refresh()
            print("[MaterialPanel] material deleted")

    def get_current_material_id(self) -> Optional[int]:
        return self._current_material.id if self._current_material else None


class MaterialDialog(ctk.CTkToplevel):
    def __init__(self, parent, title="EDIT MATERIAL"):
        super().__init__(parent)
        self.title(title)
        self.geometry("460x400")
        self.resizable(False, False)
        self.result = None
        self.configure(fg_color=C["bg_dark"])

        self._build()
        self.grab_set()

    def _build(self):
        header_frame = tk.Frame(self, bg=C["bg_dark"], height=36)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        border_cvs = tk.Canvas(
            header_frame, height=36, bg=C["bg_dark"],
            highlightthickness=0,
        )
        border_cvs.pack(fill=tk.BOTH)
        border_cvs.create_line(0, 34, 9999, 34, fill=C["orange_dim"], width=1)

        cvs_h = tk.Canvas(
            header_frame, width=16, height=36,
            bg=C["bg_dark"], highlightthickness=0,
        )
        cvs_h.place(x=10, y=0)
        draw_hex_indicator(cvs_h, 8, 18, size=6, color=C["gold"], filled=False)

        tk.Label(
            header_frame, text="MATERIAL DATA",
            font=(FONT_FAMILY, 11, "bold"),
            bg=C["bg_dark"], fg=C["fg_primary"],
        ).place(x=28, y=8)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill=tk.BOTH, expand=True, padx=16, pady=(8, 0))

        fields = [
            ("TITLE:", "title"),
            ("TOPIC:", "topic"),
            ("DIFFICULTY:", "difficulty"),
        ]
        self._entries = {}
        for label, key in fields:
            row = ctk.CTkFrame(body, fg_color="transparent")
            row.pack(fill=tk.X, pady=(6, 0))
            ctk.CTkLabel(
                row, text=label,
                font=(FONT_FAMILY, 10, "bold"),
                text_color=C["fg_secondary"],
                width=80,
            ).pack(side=tk.LEFT)
            entry = ctk.CTkEntry(
                row,
                font=(FONT_FAMILY, 10),
                fg_color=C["bg_input"],
                text_color=C["fg_primary"],
                border_width=1,
                border_color=C["fg_dim"],
                corner_radius=2,
            )
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self._entries[key] = entry

        text_label = ctk.CTkFrame(body, fg_color="transparent")
        text_label.pack(fill=tk.X, pady=(8, 0))
        ctk.CTkLabel(
            text_label, text="TEXT:",
            font=(FONT_FAMILY, 10, "bold"),
            text_color=C["fg_secondary"],
        ).pack(side=tk.LEFT)

        self._entries["text"] = ctk.CTkTextbox(
            body, height=80,
            font=("Consolas", 10),
            fg_color=C["bg_input"],
            text_color=C["fg_primary"],
            border_width=1,
            border_color=C["fg_dim"],
            corner_radius=2,
        )
        self._entries["text"].pack(fill=tk.X, pady=(4, 0))

        audio_row = ctk.CTkFrame(body, fg_color="transparent")
        audio_row.pack(fill=tk.X, pady=(8, 0))
        self._audio_path = tk.StringVar()
        ctk.CTkButton(
            audio_row, text="LINK AUDIO",
            font=(FONT_FAMILY, 9),
            fg_color=C["button_secondary"],
            hover_color=C["bg_hover"],
            text_color=C["fg_primary"],
            border_width=1,
            border_color=C["cyan_dim"],
            corner_radius=2,
            width=100, height=26,
            command=self._pick_audio,
        ).pack(side=tk.LEFT)
        ctk.CTkLabel(
            audio_row,
            textvariable=self._audio_path,
            font=(FONT_FAMILY, 8),
            text_color=C["fg_dim"],
        ).pack(side=tk.LEFT, padx=(8, 0))

        btn_row = ctk.CTkFrame(body, fg_color="transparent")
        btn_row.pack(fill=tk.X, pady=(14, 0))
        ctk.CTkButton(
            btn_row, text="SAVE",
            font=(FONT_FAMILY, 10, "bold"),
            fg_color=C["button_primary"],
            hover_color=C["button_hover"],
            text_color=C["button_text"],
            border_width=1,
            border_color=C["orange_dim"],
            corner_radius=2,
            width=90, height=30,
            command=self._save,
        ).pack(side=tk.RIGHT, padx=(4, 0))
        ctk.CTkButton(
            btn_row, text="CANCEL",
            font=(FONT_FAMILY, 10),
            fg_color=C["button_dim"],
            hover_color=C["bg_hover"],
            text_color=C["fg_primary"],
            border_width=1,
            border_color=C["fg_dim"],
            corner_radius=2,
            width=90, height=30,
            command=self.destroy,
        ).pack(side=tk.RIGHT)

    def _pick_audio(self):
        path = filedialog.askopenfilename(
            title="SELECT AUDIO FILE",
            filetypes=[
                ("Audio files", "*.wav *.mp3 *.flac *.ogg"),
                ("All files", "*.*"),
            ],
        )
        if path:
            import soundfile as sf
            try:
                info = sf.info(path)
                self._audio_path.set(f"{path[-40:]} ({info.duration:.1f}s)")
                self._audio_full_path = path
            except Exception:
                self._audio_path.set(path[-40:])

    def _save(self):
        title = self._entries["title"].get().strip()
        if not title:
            messagebox.showwarning("REQUIRED", "TITLE IS REQUIRED")
            return
        text = self._entries["text"].get("1.0", tk.END).strip()
        duration = 0.0
        audio_path = getattr(self, "_audio_full_path", "")
        if audio_path:
            import soundfile as sf
            try:
                info = sf.info(audio_path)
                duration = info.duration
            except Exception:
                pass

        self.result = Material(
            title=title,
            topic=self._entries["topic"].get().strip(),
            difficulty=self._entries["difficulty"].get().strip(),
            duration=duration,
            text=text,
            audio_path=audio_path,
        )
        self.destroy()
