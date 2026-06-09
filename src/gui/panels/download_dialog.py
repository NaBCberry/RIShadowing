import customtkinter as ctk
import tkinter as tk
import threading
from src.gui.styles import C, FONT_FAMILY, draw_hex_indicator
from src.utils.model_downloader import VOSK_MODELS, download_model


class ModelDownloadDialog(ctk.CTkToplevel):
    def __init__(self, parent, extract_dir: str):
        super().__init__(parent)
        self.title("DOWNLOAD SPEECH MODEL")
        self.geometry("460x320")
        self.resizable(False, False)
        self.configure(fg_color=C["bg_dark"])
        self._extract_dir = extract_dir
        self._result = None
        self._cancel = False

        self._build()
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

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
            header_frame, text="SPEECH MODEL DOWNLOAD",
            font=(FONT_FAMILY, 12, "bold"),
            bg=C["bg_dark"], fg=C["fg_primary"],
        ).place(x=28, y=8)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill=tk.BOTH, expand=True, padx=16, pady=(12, 0))

        ctk.CTkLabel(
            body,
            text="Vosk speech recognition model is required.\n"
                 "Select a model to download:",
            font=(FONT_FAMILY, 10),
            text_color=C["fg_secondary"],
            justify="left",
        ).pack(anchor=tk.W)

        self._model_var = tk.StringVar(value="small-en")
        model_frame = ctk.CTkFrame(body, fg_color="transparent")
        model_frame.pack(fill=tk.X, pady=(10, 0))

        for key, info in VOSK_MODELS.items():
            row = ctk.CTkFrame(model_frame, fg_color=C["bg_card"])
            row.pack(fill=tk.X, pady=2)

            rb = ctk.CTkRadioButton(
                row, text="",
                variable=self._model_var, value=key,
                fg_color=C["cyan"],
                border_color=C["fg_dim"],
                hover_color=C["cyan_dim"],
                width=20,
            )
            rb.pack(side=tk.LEFT, padx=(8, 0))

            ctk.CTkLabel(
                row, text=info["description"],
                font=(FONT_FAMILY, 10),
                text_color=C["fg_primary"],
            ).pack(side=tk.LEFT, padx=(4, 0), pady=6)

        self._progress_frame = ctk.CTkFrame(body, fg_color="transparent")

        self._status_label = ctk.CTkLabel(
            self._progress_frame,
            text="",
            font=(FONT_FAMILY, 9),
            text_color=C["fg_secondary"],
        )

        self._progress_bar = ctk.CTkProgressBar(
            self._progress_frame,
            fg_color=C["bg_input"],
            progress_color=C["cyan"],
            height=12,
            corner_radius=2,
        )
        self._progress_bar.set(0)

        btn_frame = ctk.CTkFrame(body, fg_color="transparent")
        btn_frame.pack(fill=tk.X, pady=(14, 0))

        self._btn_download = ctk.CTkButton(
            btn_frame, text="DOWNLOAD",
            font=(FONT_FAMILY, 10, "bold"),
            fg_color=C["cyan_dim"],
            hover_color=C["cyan"],
            text_color=C["fg_primary"],
            border_width=1,
            border_color=C["cyan_dim"],
            corner_radius=2,
            width=110, height=32,
            command=self._start_download,
        )
        self._btn_download.pack(side=tk.RIGHT, padx=(6, 0))

        self._btn_cancel = ctk.CTkButton(
            btn_frame, text="SKIP",
            font=(FONT_FAMILY, 10),
            fg_color=C["button_dim"],
            hover_color=C["bg_hover"],
            text_color=C["fg_primary"],
            border_width=1,
            border_color=C["fg_dim"],
            corner_radius=2,
            width=90, height=32,
            command=self._on_cancel,
        )
        self._btn_cancel.pack(side=tk.RIGHT)

    def _start_download(self):
        self._btn_download.configure(state=tk.DISABLED, text="DOWNLOADING...")
        self._btn_cancel.configure(text="CANCEL")

        self._progress_frame.pack(fill=tk.X, pady=(12, 0))
        self._status_label.pack(fill=tk.X, pady=(0, 6))
        self._progress_bar.pack(fill=tk.X)
        self._progress_bar.set(0)

        model_key = self._model_var.get()
        self._status_label.configure(text=f"Connecting to server...")

        thread = threading.Thread(
            target=self._run_download, args=(model_key,), daemon=True
        )
        thread.start()

    def _run_download(self, model_key: str):
        def callback(stage, pct, result):
            if self._cancel:
                return
            self.after(0, lambda: self._on_progress(stage, pct, result))

        try:
            path = download_model(model_key, self._extract_dir, progress_callback=callback)
            self._result = path
        except Exception as e:
            self.after(0, lambda: self._on_error(str(e)))

    def _on_progress(self, stage, pct, result):
        if stage == "downloading":
            self._status_label.configure(
                text=f"Downloading... {pct}%"
            )
            self._progress_bar.set(pct / 100)
        elif stage == "extracting":
            self._status_label.configure(
                text=f"Extracting files... {pct}%"
            )
            self._progress_bar.set(pct / 100)
        elif stage == "already_downloaded":
            self._status_label.configure(
                text="Model already exists — ready to use"
            )
            self._progress_bar.set(1)
            self._btn_download.configure(text="DONE", state=tk.DISABLED)
            self._btn_cancel.configure(text="CLOSE", command=self._on_finish)
        elif stage == "complete":
            self._status_label.configure(
                text="Download complete!"
            )
            self._progress_bar.set(1)
            self._btn_download.configure(text="DONE", state=tk.DISABLED)
            self._btn_cancel.configure(text="CLOSE", command=self._on_finish)

    def _on_error(self, msg):
        self._status_label.configure(
            text=f"ERROR: {msg[:80]}"
        )
        self._btn_download.configure(
            state=tk.NORMAL, text="RETRY",
            command=self._start_download,
        )
        self._btn_cancel.configure(text="SKIP", command=self._on_cancel)

    def _on_cancel(self):
        self._cancel = True
        self.destroy()

    def _on_finish(self):
        self.destroy()

    @property
    def result(self):
        return self._result
