import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import time
import os
import tempfile

from src.services.audio_player import AudioPlayer
from src.services.audio_recorder import AudioRecorder
from src.services.speech_recognizer import SpeechRecognizer
from src.services.comparator import ShadowComparator
from src.services.tts import create_tts_engine
from src.services.asr import create_asr_engine
from src.gui.styles import C, FONT_FAMILY, draw_hex_indicator, draw_panel_border
from src.gui.panels.device_panel import DevicePanel
from src.gui.panels.input_panel import InputPanel
from src.gui.panels.feedback_panel import FeedbackPanel
from src.gui.panels.display_panel import DisplayPanel
from src.gui.panels.material_panel import MaterialPanel
from src.models.material import init_db, record_practice

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ShadowingApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("R.I. Shadowing Practice")
        self.root.geometry("1140x820")
        self.root.minsize(960, 680)
        self.root.configure(fg_color=C["bg_dark"])

        self.audio_player = AudioPlayer()
        self.audio_recorder = AudioRecorder(sample_rate=16000, block_size=4000)
        self.speech_recognizer = SpeechRecognizer(sample_rate=16000)

        self.comparator = None
        self._stt_thread = None
        self._is_running = False
        self._practice_start_time = 0.0
        self._ref_audio_path = None
        self._selected_input_device = None
        self._selected_output_device = None
        self._asr_words = []
        self._current_material_id = None
        self._mode = "generate"
        self._awaiting_return = False

        init_db()

        self._build_title_bar()
        self._build_setup_screen()
        self._build_training_screen()
        self._check_speech_model()
        self.device_panel.scan_devices()

        self._show_setup()

        print("=" * 54)
        print("  R.I. Shadowing Practice v1.2 — Arknights UI")
        print("=" * 54)

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_title_bar(self):
        title_bar = tk.Frame(
            self.root, bg=C["bg_dark"], height=48,
            highlightthickness=0,
        )
        title_bar.pack(fill=tk.X, padx=0, pady=0)
        title_bar.pack_propagate(False)

        border_canvas = tk.Canvas(
            title_bar, height=48, bg=C["bg_dark"],
            highlightthickness=0,
        )
        border_canvas.pack(fill=tk.BOTH)

        border_canvas.create_line(
            0, 46, 9999, 46, fill=C["orange_dim"], width=1
        )
        border_canvas.create_line(
            0, 47, 9999, 47, fill=C["cyan_dim"], width=1
        )

        draw_hex_indicator(border_canvas, 24, 24, size=10, color=C["cyan"])
        draw_hex_indicator(border_canvas, 24, 24, size=5, color=C["cyan"])

        border_canvas.create_text(
            46, 22, anchor=tk.W,
            text="R.I. SHADOWING PRACTICE",
            font=(FONT_FAMILY, 15, "bold"),
            fill=C["fg_primary"],
        )
        border_canvas.create_text(
            46, 36, anchor=tk.W,
            text="听原音 · 跟读 · 实时反馈  |  RHODES ISLAND COMMAND SYSTEM v1.2",
            font=(FONT_FAMILY, 8),
            fill=C["fg_secondary"],
        )

    def _build_setup_screen(self):
        self.setup_screen = ctk.CTkFrame(self.root, fg_color="transparent")

        main = ctk.CTkFrame(self.setup_screen, fg_color="transparent")
        main.pack(fill=tk.BOTH, expand=True, padx=14, pady=(6, 0))

        self.device_panel = DevicePanel(main, self)
        self.device_panel.pack(fill=tk.X, pady=(0, 8))

        self.input_panel = InputPanel(main, self)
        self.input_panel.pack(fill=tk.X, pady=(0, 8))

        self.material_panel = MaterialPanel(main, self)
        self.material_panel.pack(fill=tk.X, pady=(0, 8))

        bottom = ctk.CTkFrame(self.setup_screen, fg_color=C["bg_panel"])
        bottom.pack(fill=tk.X, side=tk.BOTTOM, padx=14, pady=(0, 10))

        top_line = tk.Canvas(
            bottom, height=2, bg=C["bg_panel"], highlightthickness=0,
        )
        top_line.pack(fill=tk.X)
        top_line.create_line(0, 0, 9999, 0, fill=C["orange_dim"], width=1)

        btn_frame = ctk.CTkFrame(bottom, fg_color="transparent")
        btn_frame.pack(pady=(12, 6))

        self.btn_generate = ctk.CTkButton(
            btn_frame,
            text="GENERATE AUDIO",
            font=(FONT_FAMILY, 12, "bold"),
            fg_color=C["button_primary"],
            hover_color=C["button_hover"],
            text_color=C["button_text"],
            border_width=1,
            border_color=C["orange_dim"],
            corner_radius=2,
            width=240,
            height=42,
            command=self._generate_and_prepare,
        )
        self.btn_generate.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_start_shadowing = ctk.CTkButton(
            btn_frame,
            text="START SHADOWING",
            font=(FONT_FAMILY, 12, "bold"),
            fg_color=C["cyan_dim"],
            hover_color=C["cyan"],
            text_color=C["fg_primary"],
            border_width=1,
            border_color=C["cyan_dim"],
            corner_radius=2,
            width=240,
            height=42,
            command=self._start_shadowing,
            state=tk.DISABLED,
        )
        self.btn_start_shadowing.pack(side=tk.LEFT)

        status_frame = ctk.CTkFrame(bottom, fg_color="transparent")
        status_frame.pack(fill=tk.X, padx=12, pady=(0, 10))

        hex_cvs = tk.Canvas(
            status_frame, width=16, height=16,
            bg=C["bg_panel"], highlightthickness=0,
        )
        hex_cvs.pack(side=tk.LEFT)
        draw_hex_indicator(hex_cvs, 8, 8, size=4, color=C["cyan"], filled=False)

        self.setup_status = ctk.CTkLabel(
            status_frame,
            text="STANDBY — INPUT TEXT AND CLICK [GENERATE AUDIO]",
            font=(FONT_FAMILY, 9),
            text_color=C["fg_secondary"],
        )
        self.setup_status.pack(side=tk.LEFT, padx=(4, 0))

        self.btn_download_model = ctk.CTkButton(
            status_frame, text="DOWNLOAD MODEL",
            font=(FONT_FAMILY, 8, "bold"),
            fg_color="transparent",
            hover_color=C["bg_hover"],
            text_color=C["fg_dim"],
            border_width=1,
            border_color=C["fg_dim"],
            corner_radius=2,
            width=120, height=22,
            command=self._prompt_model_download,
        )
        self.btn_download_model.pack(side=tk.RIGHT)

    def _build_training_screen(self):
        self.training_screen = ctk.CTkFrame(self.root, fg_color="transparent")

        main = ctk.CTkFrame(self.training_screen, fg_color="transparent")
        main.pack(fill=tk.BOTH, expand=True, padx=14, pady=(6, 0))

        self.feedback_panel = FeedbackPanel(main, self)
        self.feedback_panel.pack(fill=tk.X, pady=(0, 8))

        self.display_panel = DisplayPanel(main, self)
        self.display_panel.pack(fill=tk.BOTH, expand=True)

        self.countdown_overlay = tk.Label(
            main, text="",
            font=(FONT_FAMILY, 72, "bold"),
            fg=C["cyan"],
            bg=C["bg_dark"],
        )

        bottom = ctk.CTkFrame(self.training_screen, fg_color=C["bg_panel"])
        bottom.pack(fill=tk.X, side=tk.BOTTOM, padx=14, pady=(0, 10))

        top_line = tk.Canvas(
            bottom, height=2, bg=C["bg_panel"], highlightthickness=0,
        )
        top_line.pack(fill=tk.X)
        top_line.create_line(0, 0, 9999, 0, fill=C["red_dim"], width=1)

        btn_frame = ctk.CTkFrame(bottom, fg_color="transparent")
        btn_frame.pack(pady=(12, 6))

        self.btn_terminate = ctk.CTkButton(
            btn_frame,
            text="TERMINATE",
            font=(FONT_FAMILY, 12, "bold"),
            fg_color=C["button_stop"],
            hover_color=C["button_stop_hover"],
            text_color=C["fg_primary"],
            border_width=1,
            border_color=C["red_dim"],
            corner_radius=2,
            width=260,
            height=42,
            command=self._on_training_action,
        )
        self.btn_terminate.pack()

        status_frame = ctk.CTkFrame(bottom, fg_color="transparent")
        status_frame.pack(fill=tk.X, padx=12, pady=(0, 10))

        hex_cvs = tk.Canvas(
            status_frame, width=16, height=16,
            bg=C["bg_panel"], highlightthickness=0,
        )
        hex_cvs.pack(side=tk.LEFT)
        draw_hex_indicator(hex_cvs, 8, 8, size=4, color=C["red"], filled=False)

        self.training_status = ctk.CTkLabel(
            status_frame,
            text="",
            font=(FONT_FAMILY, 9),
            text_color=C["fg_secondary"],
        )
        self.training_status.pack(side=tk.LEFT, padx=(4, 0))

    def _show_setup(self):
        self.training_screen.pack_forget()
        self.setup_screen.pack(fill=tk.BOTH, expand=True)

    def _show_training(self):
        self.setup_screen.pack_forget()
        self.training_screen.pack(fill=tk.BOTH, expand=True)

    def set_status(self, text):
        self.setup_status.configure(text=text)

    def set_training_status(self, text):
        self.training_status.configure(text=text)

    def _check_speech_model(self):
        self._model_ready = self.speech_recognizer.initialize()
        if self._model_ready:
            model_path = self.speech_recognizer._model_path
            model_name = os.path.basename(model_path) if model_path else "en-us"
            self.set_status(f"SPEECH MODEL READY — {model_name}")
            print(f"[App] Vosk model ready: {model_path}")
        else:
            self.set_status(
                "WARNING: Vosk model not found — click [DOWNLOAD MODEL] to auto-download"
            )
            print("[App] Vosk model NOT found")
            self.root.after(500, self._prompt_model_download)

    def _prompt_model_download(self):
        from src.gui.panels.download_dialog import ModelDownloadDialog
        dialog = ModelDownloadDialog(
            self.root,
            extract_dir=os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            ),
        )
        self.wait_window(dialog)
        if dialog.result:
            self.set_status("MODEL DOWNLOADED — LOADING...")
            self.root.update()
            self.speech_recognizer = SpeechRecognizer(sample_rate=16000)
            self._model_ready = self.speech_recognizer.initialize()
            if self._model_ready:
                model_path = self.speech_recognizer._model_path
                model_name = os.path.basename(model_path) if model_path else "en-us"
                self.set_status(f"SPEECH MODEL READY — {model_name}")
                print(f"[App] Vosk model loaded after download: {model_path}")
            else:
                self.set_status("ERROR: Model downloaded but failed to load. Check console.")
                print("[App] Model download completed but init failed")

    def _on_text_changed(self):
        self._ref_audio_path = None
        self._asr_words = []
        self._mode = "generate"
        self.btn_generate.configure(
            text="GENERATE AUDIO",
            fg_color=C["button_primary"],
            hover_color=C["button_hover"],
            border_color=C["orange_dim"],
            text_color=C["button_text"],
            state=tk.NORMAL,
        )
        self.btn_generate.unbind("<Enter>")
        self.btn_generate.unbind("<Leave>")
        self.btn_start_shadowing.configure(state=tk.DISABLED)
        self.set_status("TEXT MODIFIED — CLICK [GENERATE AUDIO]")
        self.input_panel.show_lamp_red()

    def _on_audio_loaded(self, audio_path: str):
        self._asr_words = []
        self._transcribe_with_vosk(audio_path)

    def _transcribe_with_vosk(self, audio_path: str):
        try:
            self.set_status("TRANSCRIBING VIA VOSK...")
            self.root.update()
            engine = create_asr_engine("vosk")
            result = engine.transcribe(audio_path)
            text = result.get("text", "")
            words = result.get("words", [])
            if text:
                self.input_panel.set_text(text)
                self._asr_words = words
                self.set_status(
                    f"VOSK TRANSCRIPTION COMPLETE — {len(words)} WORDS"
                )
                self.input_panel.show_lamp_green()
                print(f"[App] Vosk transcription: {len(words)} words")
            else:
                self.set_status(
                    "WARNING: No speech detected — please enter reference text manually"
                )
        except Exception as e:
            print(f"[App] Vosk transcription error: {e}")
            self.set_status("WARNING: Offline transcription failed")

    def _transcribe_with_whisper(self):
        if not self._ref_audio_path:
            return
        try:
            self.set_status("WHISPER API TRANSCRIBING...")
            self.root.update()
            from src.utils.config import get_env
            env = get_env()
            api_key = env.get("WHISPER_API_KEY")
            if not api_key:
                messagebox.showwarning(
                    "CONFIG REQUIRED",
                    "Set WHISPER_API_KEY in .env file"
                )
                return
            engine = create_asr_engine("whisper", api_key=api_key)
            result = engine.transcribe(self._ref_audio_path)
            text = result.get("text", "")
            words = result.get("words", [])
            if text:
                self.input_panel.set_text(text)
                self._asr_words = words
                self.set_status(
                    f"WHISPER TRANSCRIPTION COMPLETE — {len(words)} WORDS WITH TIMESTAMPS"
                )
                print(f"[App] Whisper transcription: {len(words)} words with timestamps")
        except Exception as e:
            messagebox.showerror("WHISPER TRANSCRIPTION FAILED", str(e))

    def _generate_tts_audio(self, text: str) -> str:
        engine_key = self.input_panel.get_selected_tts_engine()
        self.set_status(f"SYNTHESIZING VIA {engine_key.upper()}...")
        self.root.update()

        try:
            engine = create_tts_engine(engine_key)
            tmp_path = os.path.join(tempfile.gettempdir(), "shadow_ref.wav")
            engine.synthesize(text, tmp_path)
            return tmp_path
        except Exception as e:
            messagebox.showerror("TTS ERROR", f"Speech synthesis failed:\n{e}")
            return None

    def _generate_and_prepare(self):
        ref_text = self.input_panel.get_text()
        if not ref_text:
            messagebox.showwarning("INPUT REQUIRED", "Please enter reference text")
            return

        if not self._model_ready:
            messagebox.showwarning(
                "SPEECH MODEL NOT READY",
                "Download Vosk speech recognition model:\n"
                "https://alphacephei.com/vosk/models\n\n"
                "Recommended: vosk-model-small-en-us-0.15 (~40MB)",
            )
            return

        self.btn_generate.configure(state=tk.DISABLED, text="PROCESSING...")
        self.btn_start_shadowing.configure(state=tk.DISABLED)
        self._ref_audio_path = None
        self._asr_words = []
        self.input_panel.show_lamp_yellow_blinking()

        import threading
        thread = threading.Thread(
            target=self._run_tts_and_finalize, args=(ref_text,), daemon=True
        )
        thread.start()

    def _run_tts_and_finalize(self, ref_text: str):
        audio_path = self._generate_tts_audio(ref_text)
        self.root.after(0, lambda: self._on_tts_complete(audio_path))

    def _on_tts_complete(self, audio_path):
        if not audio_path:
            self.btn_generate.configure(
                state=tk.NORMAL, text="GENERATE AUDIO",
                fg_color=C["button_primary"], hover_color=C["button_hover"],
                border_color=C["orange_dim"], text_color=C["button_text"],
            )
            self.input_panel.show_lamp_red()
            return

        self._ref_audio_path = audio_path

        try:
            self.audio_player.load_file(audio_path)
        except Exception as e:
            messagebox.showerror("AUDIO LOAD FAILED", str(e))
            self.btn_generate.configure(
                state=tk.NORMAL, text="GENERATE AUDIO",
                fg_color=C["button_primary"], hover_color=C["button_hover"],
                border_color=C["orange_dim"], text_color=C["button_text"],
            )
            self.input_panel.show_lamp_red()
            return

        self.set_status("ANALYZING AUDIO TIMELINE...")
        self.root.update()
        try:
            engine = create_asr_engine("vosk")
            result = engine.transcribe(audio_path)
            self._asr_words = result.get("words", [])
            if self._asr_words:
                print(f"[App] TTS audio analyzed: {len(self._asr_words)} word timestamps")
        except Exception as e:
            print(f"[App] TTS timestamp analysis failed, using estimates: {e}")

        self._mode = "shadowing"
        self._set_btn_accomplished()
        self.btn_start_shadowing.configure(state=tk.NORMAL)
        self.set_status(
            f"AUDIO READY — DURATION: {self.audio_player.duration:.1f}s | CLICK [START SHADOWING]"
        )
        self.input_panel.show_lamp_green()

    def _set_btn_accomplished(self):
        self.btn_generate.configure(
            text="GENERATION ACCOMPLISHED!",
            fg_color=C["green"],
            hover_color=C["green"],
            border_color=C["green_dim"],
            text_color=C["button_text"],
            state=tk.NORMAL,
        )
        self.btn_generate.unbind("<Enter>")
        self.btn_generate.unbind("<Leave>")
        self.btn_generate.bind("<Enter>", self._on_btn_generate_enter)
        self.btn_generate.bind("<Leave>", self._on_btn_generate_leave)

    def _on_btn_generate_enter(self, event=None):
        if self._ref_audio_path and os.path.exists(self._ref_audio_path):
            self.btn_generate.configure(
                text="REGENERATE?",
                fg_color=C["button_primary"],
                hover_color=C["button_hover"],
                border_color=C["orange_dim"],
                text_color=C["button_text"],
            )

    def _on_btn_generate_leave(self, event=None):
        self.btn_generate.configure(
            text="GENERATION ACCOMPLISHED!",
            fg_color=C["green"],
            hover_color=C["green"],
            border_color=C["green_dim"],
            text_color=C["button_text"],
        )

    def _start_shadowing(self):
        ref_text = self.input_panel.get_text()
        if not ref_text:
            messagebox.showwarning("INPUT REQUIRED", "Please enter reference text")
            return

        if not self._ref_audio_path:
            self.set_status("WARNING: Click [GENERATE AUDIO] first")
            return

        try:
            self.audio_player.load_file(self._ref_audio_path)
        except Exception as e:
            messagebox.showerror("AUDIO LOAD FAILED", str(e))
            return

        self.audio_player._device = self._selected_output_device
        print(f"[App] output device set to: {self._selected_output_device}")

        self.comparator = ShadowComparator(ref_text)
        if self._asr_words:
            self.comparator.set_word_timings(self._asr_words)
        else:
            self.comparator.set_estimated_timings(self.audio_player.duration)
            self.set_training_status(
                "WARNING: Using estimated word timestamps — accuracy may be reduced"
            )

        self.display_panel.init_ref_display(self.comparator.reference_words)

        self.speech_recognizer.stop()
        self.speech_recognizer = SpeechRecognizer(sample_rate=16000)
        ok = self.speech_recognizer.initialize()
        print(f"[App] SpeechRecognizer init: {'OK' if ok else 'FAILED'}")

        self.audio_recorder = AudioRecorder(
            sample_rate=16000, block_size=4000,
            device=self._selected_input_device,
        )

        self._show_training()
        self.set_training_status("READY — CLICK [START] TO BEGIN")
        self._awaiting_return = False
        self.btn_terminate.configure(
            text="START",
            fg_color=C["green"],
            hover_color=C["green"],
            border_color=C["green_dim"],
            state=tk.NORMAL,
        )
        self._training_state = "ready"
        print(f"[App] _start_shadowing: training screen ready, btn=START, state=ready")

    def _on_training_action(self):
        print(f"[App] _on_training_action: state={self._training_state}, awaiting={self._awaiting_return}")
        if self._training_state == "ready":
            self._begin_countdown()
        elif self._awaiting_return:
            self._finish_transition(self._final_status)
        else:
            self._stop_shadowing()

    def _begin_countdown(self):
        from src.utils.config import get_config
        config = get_config()
        total = config.get("training", {}).get("countdown_seconds", 3.0)
        total = max(0.5, min(total, 10.0))
        print(f"[App] _begin_countdown: total={total}")

        self._training_state = "countdown"
        self._countdown_remaining = total
        self.btn_terminate.configure(
            text="...", state=tk.DISABLED,
            fg_color=C["button_dim"],
            border_color=C["fg_dim"],
        )
        self.countdown_overlay.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.set_training_status(f"GET READY... {self._countdown_remaining:.2f}s")
        self.root.after(50, self._countdown_tick)

    def _countdown_tick(self):
        self._countdown_remaining -= 0.05
        self.countdown_overlay.configure(
            text=f"{max(0, self._countdown_remaining):.2f}"
        )
        if self._countdown_remaining <= 0:
            self.countdown_overlay.place_forget()
            self.set_training_status("TRAINING IN PROGRESS — FOLLOW THE AUDIO...")
            print("[App] countdown finished, starting playback")
            self._start_playback()
        else:
            self.set_training_status(
                f"GET READY... {self._countdown_remaining:.2f}s"
            )
            self.root.after(50, self._countdown_tick)

    def _start_playback(self):
        print("[App] _start_playback: starting recorder and player")
        self.audio_recorder.start()
        print(f"[App] AudioRecorder started, device={self._selected_input_device}")

        self._stt_thread = self.speech_recognizer.start(self.audio_recorder.audio_queue)
        print(f"[App] STT thread started: {self._stt_thread is not None}")

        self._is_running = True
        self._practice_start_time = time.time()
        self._training_state = "running"

        self.btn_terminate.configure(
            text="TERMINATE",
            fg_color=C["button_stop"],
            hover_color=C["button_stop_hover"],
            border_color=C["red_dim"],
            state=tk.NORMAL,
        )

        def on_audio_finished():
            self.root.after(0, self._on_practice_finished)

        self.audio_player.play(on_finished=on_audio_finished)
        print(f"[App] audio_player.play() called, duration={self.audio_player.duration:.1f}s")
        self.root.after(50, self._update_loop)

    def _stop_shadowing(self):
        print("[App] _stop_shadowing called")
        self._is_running = False
        self._training_state = "stopped"
        try:
            self.audio_player.stop()
            print("[App] audio_player stopped")
        except Exception as e:
            print(f"[App] audio_player.stop error: {e}")
        try:
            self.audio_recorder.stop()
            print("[App] audio_recorder stopped")
        except Exception as e:
            print(f"[App] audio_recorder.stop error: {e}")
        try:
            self.speech_recognizer.stop()
            print("[App] speech_recognizer stopped")
        except Exception as e:
            print(f"[App] speech_recognizer.stop error: {e}")
        self.root.after(200, self._show_results)

    def _show_results(self):
        try:
            if self.comparator is None:
                self._finish_transition("TERMINATED")
                return

            recognized_words = self.speech_recognizer.get_latest_words()
            ref_elapsed = self.audio_player.duration
            if ref_elapsed <= 0:
                ref_elapsed = 1.0
            accuracy_result = self.comparator.compare_accuracy(recognized_words, ref_elapsed)
            score = accuracy_result.get("score", 0.0)

            print(f"[App] practice finished. recognized words: {len(recognized_words)}, accuracy: {score:.0%}")
            for w in recognized_words[:5]:
                print(f"  [{w['word']}] conf={w['conf']:.2f}")

            review_words = [w for w in recognized_words if w.get("conf", 1.0) < 0.7]
            if review_words:
                review_list = "  ".join(w["word"] for w in review_words[:8])
                print(f"[App] review suggestions: {review_list}")
                try:
                    self.display_panel.detail_text.configure(state="normal")
                    self.display_panel.detail_text.insert(
                        tk.END,
                        f"\nREVIEW: {review_list}\n"
                        f"(Underlined words have low confidence — practice recommended)",
                    )
                    self.display_panel.detail_text.configure(state="disabled")
                except Exception:
                    pass

            self._final_status = (
                f"TRAINING COMPLETE! ACCURACY: {score:.0%} | "
                f"G:{accuracy_result.get('green_count', 0)} "
                f"Y:{accuracy_result.get('yellow_count', 0)} "
                f"R:{accuracy_result.get('red_count', 0)}"
            )
            self.set_training_status(self._final_status)
            self._awaiting_return = True
            self.btn_terminate.configure(
                text="RETURN",
                fg_color=C["cyan_dim"],
                hover_color=C["cyan"],
                border_color=C["cyan_dim"],
                state=tk.NORMAL,
            )

            mid = self.material_panel.get_current_material_id()
            if mid:
                try:
                    record_practice(
                        mid, score,
                        accuracy_result.get("green_count", 0),
                        accuracy_result.get("yellow_count", 0),
                        accuracy_result.get("red_count", 0),
                        self.audio_player.duration,
                    )
                    self.material_panel._refresh()
                    print(f"[App] recorded practice for material id={mid}")
                except Exception as e:
                    print(f"[App] record practice error: {e}")
        except Exception as e:
            print(f"[App] _show_results error: {e}")
            import traceback
            traceback.print_exc()
            self._finish_transition("TERMINATED")

    def _update_loop(self):
        if not self._is_running:
            return

        if not self.audio_player.is_playing:
            self._on_practice_finished()
            return

        if self.comparator and self._is_running:
            recognized_words = self.speech_recognizer.get_latest_words()
            ref_elapsed = self.audio_player.position

            speed_result = self.comparator.compare_speed(recognized_words, ref_elapsed)
            self.feedback_panel.update_speed(speed_result)

            accuracy_result = self.comparator.compare_accuracy(recognized_words, ref_elapsed)
            self.feedback_panel.update_accuracy(accuracy_result)
            self.display_panel.update_word_accuracy_bars(accuracy_result)
            self.display_panel.update_user_display(recognized_words, accuracy_result)
            self.display_panel.update_detail(recognized_words, accuracy_result)

        self.display_panel.update_ref_highlight()
        self.root.after(100, self._update_loop)

    def _on_practice_finished(self):
        if not self._is_running:
            return
        self._is_running = False
        self.audio_recorder.stop()
        self.speech_recognizer.stop()
        self._show_results()

    def _finish_transition(self, status_text):
        self._show_setup()
        self.root.update_idletasks()

        if self._ref_audio_path and os.path.exists(self._ref_audio_path):
            self._set_btn_accomplished()
            self.btn_start_shadowing.configure(state=tk.NORMAL)
            self.input_panel.show_lamp_green()
        else:
            self.btn_generate.configure(
                text="GENERATE AUDIO",
                fg_color=C["button_primary"],
                hover_color=C["button_hover"],
                border_color=C["orange_dim"],
                text_color=C["button_text"],
                state=tk.NORMAL,
            )
            self.btn_generate.unbind("<Enter>")
            self.btn_generate.unbind("<Leave>")
            self.btn_start_shadowing.configure(state=tk.DISABLED)
            self.input_panel.show_lamp_red()

        self.set_status(status_text)

    def _on_close(self):
        self._is_running = False
        self.audio_player.stop()
        self.audio_recorder.stop()
        self.speech_recognizer.stop()
        self.root.destroy()

    def run(self):
        self.root.mainloop()
