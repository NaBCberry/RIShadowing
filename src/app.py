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
from src.gui.panels.control_panel import ControlPanel
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

        init_db()

        self._build_ui()
        self._check_speech_model()
        self.device_panel.scan_devices()

        print("=" * 54)
        print("  R.I. Shadowing Practice v1.2 — Arknights UI")
        print("=" * 54)

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        self._build_title_bar()

        main = ctk.CTkFrame(self.root, fg_color="transparent")
        main.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 10))

        self.device_panel = DevicePanel(main, self)
        self.device_panel.pack(fill=tk.X, pady=(0, 8))

        self.input_panel = InputPanel(main, self)
        self.input_panel.pack(fill=tk.X, pady=(0, 8))

        self.material_panel = MaterialPanel(main, self)
        self.material_panel.pack(fill=tk.X, pady=(0, 8))

        self.control_panel = ControlPanel(main, self)
        self.control_panel.pack(fill=tk.X, pady=(0, 8))

        self.feedback_panel = FeedbackPanel(main, self)
        self.feedback_panel.pack(fill=tk.X, pady=(0, 8))

        self.display_panel = DisplayPanel(main, self)
        self.display_panel.pack(fill=tk.BOTH, expand=True)

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

        decor_x = 1100
        border_canvas.create_line(
            decor_x, 10, decor_x + 20, 10, fill=C["cyan_dim"], width=1
        )
        border_canvas.create_line(
            decor_x, 36, decor_x + 20, 36, fill=C["orange_dim"], width=1
        )

        corner = 1130
        border_canvas.create_line(
            corner, 14, corner, 6, corner, 6, corner + 14, 6,
            fill=C["cyan_dim"], width=1,
        )
        border_canvas.create_line(
            corner, 34, corner, 42, corner, 42, corner + 14, 42,
            fill=C["orange_dim"], width=1,
        )

    def _check_speech_model(self):
        self._model_ready = self.speech_recognizer.initialize()
        if self._model_ready:
            model_path = self.speech_recognizer._model_path
            model_name = os.path.basename(model_path) if model_path else "en-us"
            self.control_panel.set_status(f"SPEECH MODEL READY — {model_name}")
            print(f"[App] Vosk model ready: {model_path}")
        else:
            self.control_panel.set_status(
                "WARNING: Vosk model not found — download and extract to project root\n"
                "URL: https://alphacephei.com/vosk/models"
            )
            print("[App] Vosk model NOT found")

    def _on_text_changed(self):
        self._ref_audio_path = None
        self._asr_words = []
        self.control_panel.set_mode("generate")
        self.control_panel.set_status("TEXT MODIFIED — CLICK [GENERATE AUDIO]")

    def _on_audio_loaded(self, audio_path: str):
        self._asr_words = []
        self._transcribe_with_vosk(audio_path)

    def _transcribe_with_vosk(self, audio_path: str):
        try:
            self.control_panel.set_status("TRANSCRIBING VIA VOSK...")
            self.root.update()
            engine = create_asr_engine("vosk")
            result = engine.transcribe(audio_path)
            text = result.get("text", "")
            words = result.get("words", [])
            if text:
                self.input_panel.set_text(text)
                self._asr_words = words
                self.control_panel.set_status(
                    f"VOSK TRANSCRIPTION COMPLETE — {len(words)} WORDS"
                )
                print(f"[App] Vosk transcription: {len(words)} words")
            else:
                self.control_panel.set_status(
                    "WARNING: No speech detected — please enter reference text manually"
                )
        except Exception as e:
            print(f"[App] Vosk transcription error: {e}")
            self.control_panel.set_status("WARNING: Offline transcription failed")

    def _transcribe_with_whisper(self):
        if not self._ref_audio_path:
            return
        try:
            self.control_panel.set_status("WHISPER API TRANSCRIBING...")
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
                self.control_panel.set_status(
                    f"WHISPER TRANSCRIPTION COMPLETE — {len(words)} WORDS WITH TIMESTAMPS"
                )
                print(f"[App] Whisper transcription: {len(words)} words with timestamps")
        except Exception as e:
            messagebox.showerror("WHISPER TRANSCRIPTION FAILED", str(e))

    def _generate_tts_audio(self, text: str) -> str:
        engine_key = self.input_panel.get_selected_tts_engine()
        self.control_panel.set_status(f"SYNTHESIZING VIA {engine_key.upper()}...")
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

        self.control_panel.set_mode("loading")
        self._ref_audio_path = None
        self._asr_words = []

        audio_path = self._generate_tts_audio(ref_text)
        if not audio_path:
            self.control_panel.set_mode("generate")
            return

        self._ref_audio_path = audio_path

        try:
            self.audio_player.load_file(audio_path)
        except Exception as e:
            messagebox.showerror("AUDIO LOAD FAILED", str(e))
            self.control_panel.set_mode("generate")
            return

        self.control_panel.set_status("ANALYZING AUDIO TIMELINE...")
        self.root.update()
        try:
            engine = create_asr_engine("vosk")
            result = engine.transcribe(audio_path)
            self._asr_words = result.get("words", [])
            if self._asr_words:
                print(f"[App] TTS audio analyzed: {len(self._asr_words)} word timestamps")
        except Exception as e:
            print(f"[App] TTS timestamp analysis failed, using estimates: {e}")

        self.control_panel.set_mode("shadowing")
        self.control_panel.set_status(
            f"AUDIO READY — DURATION: {self.audio_player.duration:.1f}s | CLICK [START SHADOWING]"
        )

    def _start_shadowing(self):
        ref_text = self.input_panel.get_text()
        if not ref_text:
            messagebox.showwarning("INPUT REQUIRED", "Please enter reference text")
            return

        if not self._ref_audio_path:
            self.control_panel.set_mode("generate")
            self.control_panel.set_status("WARNING: Click [GENERATE AUDIO] first")
            return

        try:
            self.audio_player.load_file(self._ref_audio_path)
        except Exception as e:
            messagebox.showerror("音频加载失败", str(e))
            return

        self.audio_player._device = self._selected_output_device
        print(f"[App] output device set to: {self._selected_output_device}")

        self.comparator = ShadowComparator(ref_text)
        if self._asr_words:
            self.comparator.set_word_timings(self._asr_words)
        else:
            self.comparator.set_estimated_timings(self.audio_player.duration)

        self.display_panel.init_ref_display(self.comparator.reference_words)

        self.speech_recognizer.stop()
        self.speech_recognizer = SpeechRecognizer(sample_rate=16000)
        ok = self.speech_recognizer.initialize()
        print(f"[App] SpeechRecognizer init: {'OK' if ok else 'FAILED'}")

        self.audio_recorder = AudioRecorder(
            sample_rate=16000, block_size=4000,
            device=self._selected_input_device,
        )
        self.audio_recorder.start()
        print(f"[App] AudioRecorder started, device={self._selected_input_device}")

        self._stt_thread = self.speech_recognizer.start(self.audio_recorder.audio_queue)
        print(f"[App] STT thread started: {self._stt_thread is not None}")

        self._is_running = True
        self._practice_start_time = time.time()

        self.control_panel.set_button_states(True)
        self.device_panel.set_state(False)

        def on_audio_finished():
            self.root.after(0, self._on_practice_finished)

        self.audio_player.play(on_finished=on_audio_finished)

        self.control_panel.set_status("TRAINING IN PROGRESS — FOLLOW THE AUDIO...")
        self.root.after(300, self._update_loop)

    def _stop_shadowing(self):
        self._is_running = False
        self.audio_player.stop()
        self.audio_recorder.stop()
        self.speech_recognizer.stop()
        self.control_panel.set_button_states(False)
        self.device_panel.set_state(True)
        self.control_panel.set_status("TERMINATED")
        print("[App] shadowing stopped by user")

    def _update_loop(self):
        if not self._is_running:
            return

        if not self.audio_player.is_playing:
            self._on_practice_finished()
            return

        self.device_panel.update_level_meter()

        self.display_panel.update_ref_highlight()

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

        self.root.after(200, self._update_loop)

    def _on_practice_finished(self):
        if not self._is_running:
            return
        self._is_running = False
        self.audio_recorder.stop()
        self.speech_recognizer.stop()
        self.control_panel.set_button_states(False)
        self.device_panel.set_state(True)

        recognized_words = self.speech_recognizer.get_latest_words()
        ref_elapsed = self.audio_player.duration
        accuracy_result = self.comparator.compare_accuracy(recognized_words, ref_elapsed)
        score = accuracy_result.get("score", 0.0)

        print(f"[App] practice finished. recognized words: {len(recognized_words)}, accuracy: {score:.0%}")
        for w in recognized_words[:5]:
            print(f"  [{w['word']}] conf={w['conf']:.2f}")

        self.control_panel.set_status(
            f"TRAINING COMPLETE! ACCURACY: {score:.0%} | "
            f"G:{accuracy_result.get('green_count', 0)} "
            f"Y:{accuracy_result.get('yellow_count', 0)} "
            f"R:{accuracy_result.get('red_count', 0)}"
        )

        review_words = [w for w in recognized_words if w.get("conf", 1.0) < 0.7]
        if review_words:
            review_list = "  ".join(w["word"] for w in review_words[:8])
            print(f"[App] review suggestions: {review_list}")
            self.display_panel.detail_text.configure(state="normal")
            self.display_panel.detail_text.insert(
                tk.END,
                f"\n📝 建议复习: {review_list}\n"
                f"(带下划线的词为发音置信度较低，可重点练习)",
            )
            self.display_panel.detail_text.configure(state="disabled")

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

    def _on_close(self):
        self._is_running = False
        self.audio_player.stop()
        self.audio_recorder.stop()
        self.speech_recognizer.stop()
        self.root.destroy()

    def run(self):
        self.root.mainloop()
