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
from src.gui.styles import C, FONT_FAMILY
from src.gui.panels.device_panel import DevicePanel
from src.gui.panels.input_panel import InputPanel
from src.gui.panels.control_panel import ControlPanel
from src.gui.panels.feedback_panel import FeedbackPanel
from src.gui.panels.display_panel import DisplayPanel

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ShadowingApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("影子跟读训练 Shadowing Practice")
        self.root.geometry("1100x800")
        self.root.minsize(900, 650)
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

        self._build_ui()
        self._check_speech_model()
        self.device_panel.scan_devices()

        print("=" * 50)
        print(" 影子跟读训练 Shadowing Practice v1.2")
        print("=" * 50)

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        main = ctk.CTkFrame(self.root, fg_color="transparent")
        main.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        header = ctk.CTkFrame(main, fg_color="transparent")
        header.pack(fill=tk.X, pady=(0, 6))

        ctk.CTkLabel(
            header, text="🎤 影子跟读训练",
            font=(FONT_FAMILY, 16, "bold"),
            text_color=C["accent"],
        ).pack(side=tk.LEFT)

        ctk.CTkLabel(
            header, text="Shadowing Practice — 听原音 · 跟读 · 实时反馈",
            font=(FONT_FAMILY, 9),
            text_color=C["fg_secondary"],
        ).pack(side=tk.LEFT, padx=(16, 0))

        self.device_panel = DevicePanel(main, self)
        self.device_panel.pack(fill=tk.X, pady=(0, 6))

        self.input_panel = InputPanel(main, self)
        self.input_panel.pack(fill=tk.X, pady=(0, 6))

        self.control_panel = ControlPanel(main, self)
        self.control_panel.pack(fill=tk.X, pady=(0, 6))

        self.feedback_panel = FeedbackPanel(main, self)
        self.feedback_panel.pack(fill=tk.X, pady=(0, 6))

        self.display_panel = DisplayPanel(main, self)
        self.display_panel.pack(fill=tk.BOTH, expand=True)

    def _check_speech_model(self):
        self._model_ready = self.speech_recognizer.initialize()
        if self._model_ready:
            model_path = self.speech_recognizer._model_path
            model_name = os.path.basename(model_path) if model_path else "en-us"
            self.control_panel.set_status(f"✅ 语音模型已就绪 — {model_name}")
            print(f"[App] Vosk model ready: {model_path}")
        else:
            self.control_panel.set_status(
                "⚠ 未找到Vosk语音模型 — 请下载模型并解压到项目根目录\n"
                "下载地址: https://alphacephei.com/vosk/models"
            )
            print("[App] Vosk model NOT found")

    def _generate_tts_audio(self, text: str) -> str:
        engine_key = self.input_panel.get_selected_tts_engine()
        self.control_panel.set_status(f"⏳ 正在用 {engine_key} 合成参考语音...")
        self.root.update()

        try:
            engine = create_tts_engine(engine_key)
            tmp_path = os.path.join(tempfile.gettempdir(), "shadow_ref.wav")
            engine.synthesize(text, tmp_path)
            return tmp_path
        except Exception as e:
            messagebox.showerror("TTS错误", f"语音合成失败:\n{e}")
            return None

    def _start_shadowing(self):
        ref_text = self.input_panel.get_text()
        if not ref_text:
            messagebox.showwarning("缺少输入", "请输入参考文本")
            return

        if not self._model_ready:
            messagebox.showwarning(
                "语音模型未就绪",
                "请先下载Vosk语音识别模型:\n"
                "https://alphacephei.com/vosk/models\n\n"
                "推荐: vosk-model-small-en-us-0.15 (~40MB)",
            )
            return

        if not self._ref_audio_path:
            self.control_panel.set_status("⏳ 正在合成参考语音...")
            self.root.update()
            audio_path = self._generate_tts_audio(ref_text)
            if not audio_path:
                return
            self._ref_audio_path = audio_path

        try:
            self.audio_player.load_file(self._ref_audio_path)
        except Exception as e:
            messagebox.showerror("音频加载失败", str(e))
            return

        self.audio_player._device = self._selected_output_device
        print(f"[App] output device set to: {self._selected_output_device}")

        self.comparator = ShadowComparator(ref_text)
        self.comparator.set_estimated_timings(self.audio_player.duration)

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

        self.control_panel.set_status("🔴 训练中 — 请跟随音频大声跟读...")
        self.root.after(300, self._update_loop)

    def _stop_shadowing(self):
        self._is_running = False
        self.audio_player.stop()
        self.audio_recorder.stop()
        self.speech_recognizer.stop()
        self.control_panel.set_button_states(False)
        self.device_panel.set_state(True)
        self.control_panel.set_status("⏹ 已停止")
        print("[App] shadowing stopped by user")

    def _update_loop(self):
        if not self._is_running:
            return

        if not self.audio_player.is_playing:
            self._on_practice_finished()
            return

        self.device_panel.update_level_meter()

        self.display_panel.update_ref_display()

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
            f"✅ 训练完成! 整体准确度: {score:.0%} | "
            f"🟢{accuracy_result.get('green_count', 0)} "
            f"🟡{accuracy_result.get('yellow_count', 0)} "
            f"🔴{accuracy_result.get('red_count', 0)}"
        )

    def _on_close(self):
        self._is_running = False
        self.audio_player.stop()
        self.audio_recorder.stop()
        self.speech_recognizer.stop()
        self.root.destroy()

    def run(self):
        self.root.mainloop()
