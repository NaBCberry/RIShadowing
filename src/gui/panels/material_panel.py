import customtkinter as ctk
import tkinter as tk
import os
from tkinter import messagebox, filedialog
from typing import Optional
from src.gui.styles import C, FONT_FAMILY
from src.models.material import (
    Material, init_db, list_materials, add_material,
    update_material, delete_material, get_material, get_all_topics,
)


class MaterialPanel(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C["bg_panel"], corner_radius=8)
        self.app = app
        self._materials = []
        self._current_material = None
        self._build()
        self._refresh()

    def _build(self):
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill=tk.X, padx=10, pady=(8, 4))

        ctk.CTkLabel(
            toolbar, text="📚 材料库",
            font=(FONT_FAMILY, 12, "bold"),
            text_color=C["fg_primary"],
        ).pack(side=tk.LEFT)

        ctk.CTkButton(
            toolbar, text="➕ 添加",
            font=(FONT_FAMILY, 9),
            fg_color=C["button_bg"], hover_color=C["accent"],
            text_color=C["button_fg"], width=60, height=26,
            command=self._add_material,
        ).pack(side=tk.RIGHT, padx=(4, 0))

        ctk.CTkButton(
            toolbar, text="🗑 删除",
            font=(FONT_FAMILY, 9),
            fg_color=C["button_stop"], hover_color="#ee4545",
            text_color="#1e1e2e", width=60, height=26,
            command=self._delete_material,
        ).pack(side=tk.RIGHT, padx=(4, 0))

        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *a: self._refresh())

        search_entry = ctk.CTkEntry(
            toolbar,
            textvariable=self.search_var,
            placeholder_text="搜索标题/内容...",
            font=(FONT_FAMILY, 9),
            fg_color=C["bg_input"],
            text_color=C["fg_primary"],
            width=140, height=26,
        )
        search_entry.pack(side=tk.RIGHT, padx=(10, 0))

        self.list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=C["bg_input"],
            height=140,
        )
        self.list_frame.pack(fill=tk.X, padx=10, pady=(4, 6))

        self._refresh()

    def _refresh(self, event=None):
        for w in self.list_frame.winfo_children():
            w.destroy()

        search = self.search_var.get().strip() or None
        self._materials = list_materials(search=search)
        topics = get_all_topics()

        if not self._materials:
            ctk.CTkLabel(
                self.list_frame,
                text="暂无材料，点击「➕ 添加」导入文本或音频文件",
                font=(FONT_FAMILY, 9),
                text_color=C["fg_secondary"],
            ).pack(pady=10)
            return

        for m in self._materials:
            row = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            row.pack(fill=tk.X, pady=1)

            label_text = f"  {m.title[:40]}"
            if m.topic:
                label_text += f"  [{m.topic}]"
            if m.difficulty:
                label_text += f"  ({m.difficulty})"
            if m.duration > 0:
                label_text += f"  {m.duration:.1f}s"
            label_text += f"  | 练习{m.practice_count}次"
            if m.best_score > 0:
                label_text += f"  | 最佳{m.best_score:.0%}"

            btn = ctk.CTkButton(
                row, text=label_text,
                font=(FONT_FAMILY, 9),
                fg_color=C["bg_panel"],
                hover_color=C["button_bg"],
                text_color=C["fg_primary"],
                anchor="w",
                command=lambda mid=m.id: self._select_material(mid),
            )
            btn.pack(fill=tk.X)

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
                self.app.control_panel.set_status(
                    f"✅ 已加载: {material.title} — 时长: {material.duration:.1f}秒"
                )
                self.app._on_audio_loaded(material.audio_path)
            except Exception as e:
                print(f"[MaterialPanel] load audio error: {e}")
        else:
            self.app._ref_audio_path = None
            self.app.control_panel.set_status(
                f"✅ 已选择: {material.title}（未关联音频，将用TTS生成）"
            )
        print(f"[MaterialPanel] selected: {material.title}")

    def _add_material(self):
        dialog = MaterialDialog(self, title="添加材料")
        self.wait_window(dialog)
        if dialog.result:
            try:
                mid = add_material(dialog.result)
                print(f"[MaterialPanel] added material id={mid}")
                self._refresh()
            except Exception as e:
                messagebox.showerror("添加失败", str(e))

    def _delete_material(self):
        if not self._current_material:
            messagebox.showinfo("提示", "请先选择要删除的材料")
            return
        if messagebox.askyesno("确认", f'删除材料 "{self._current_material.title}"？'):
            delete_material(self._current_material.id)
            self._current_material = None
            self._refresh()
            print("[MaterialPanel] material deleted")

    def get_current_material_id(self) -> Optional[int]:
        return self._current_material.id if self._current_material else None


class MaterialDialog(ctk.CTkToplevel):
    def __init__(self, parent, title="编辑材料"):
        super().__init__(parent)
        self.title(title)
        self.geometry("450x380")
        self.resizable(False, False)
        self.result = None
        self.configure(fg_color=C["bg_dark"])

        self._build()
        self.grab_set()

    def _build(self):
        fields = [
            ("标题:", "title"),
            ("话题:", "topic"),
            ("难度:", "difficulty"),
        ]
        self._entries = {}
        for label, key in fields:
            row = ctk.CTkFrame(self, fg_color="transparent")
            row.pack(fill=tk.X, padx=16, pady=(8, 0))
            ctk.CTkLabel(
                row, text=label,
                font=(FONT_FAMILY, 10),
                text_color=C["fg_primary"],
                width=60,
            ).pack(side=tk.LEFT)
            entry = ctk.CTkEntry(
                row,
                font=(FONT_FAMILY, 10),
                fg_color=C["bg_input"],
                text_color=C["fg_primary"],
            )
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self._entries[key] = entry

        text_label = ctk.CTkFrame(self, fg_color="transparent")
        text_label.pack(fill=tk.X, padx=16, pady=(8, 0))
        ctk.CTkLabel(
            text_label, text="参考文本:",
            font=(FONT_FAMILY, 10),
            text_color=C["fg_primary"],
        ).pack(side=tk.LEFT)

        self._entries["text"] = ctk.CTkTextbox(
            self, height=80,
            font=("Consolas", 10),
            fg_color=C["bg_input"],
            text_color=C["fg_primary"],
        )
        self._entries["text"].pack(fill=tk.X, padx=16, pady=(4, 0))

        audio_row = ctk.CTkFrame(self, fg_color="transparent")
        audio_row.pack(fill=tk.X, padx=16, pady=(8, 0))
        self._audio_path = tk.StringVar()
        ctk.CTkButton(
            audio_row, text="🎵 关联音频(可选)",
            font=(FONT_FAMILY, 9),
            fg_color=C["button_bg"], hover_color=C["accent"],
            text_color=C["button_fg"], width=100, height=26,
            command=self._pick_audio,
        ).pack(side=tk.LEFT)
        ctk.CTkLabel(
            audio_row,
            textvariable=self._audio_path,
            font=(FONT_FAMILY, 8),
            text_color=C["fg_secondary"],
        ).pack(side=tk.LEFT, padx=(8, 0))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill=tk.X, padx=16, pady=(12, 0))
        ctk.CTkButton(
            btn_row, text="保存",
            font=(FONT_FAMILY, 10, "bold"),
            fg_color=C["button_bg"], hover_color=C["accent"],
            text_color=C["button_fg"], width=80, height=30,
            command=self._save,
        ).pack(side=tk.RIGHT, padx=(4, 0))
        ctk.CTkButton(
            btn_row, text="取消",
            font=(FONT_FAMILY, 10),
            fg_color=C["gray"], hover_color=C["fg_secondary"],
            text_color=C["button_fg"], width=80, height=30,
            command=self.destroy,
        ).pack(side=tk.RIGHT)

    def _pick_audio(self):
        path = filedialog.askopenfilename(
            title="选择音频文件",
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
            messagebox.showwarning("缺少信息", "请输入标题")
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
