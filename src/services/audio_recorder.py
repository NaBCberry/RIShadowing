import threading
import queue
import math
import sounddevice as sd
import numpy as np


class AudioRecorder:
    def __init__(self, sample_rate: int = 16000, channels: int = 1,
                 block_size: int = 4000, device=None):
        self._sample_rate = sample_rate
        self._channels = channels
        self._block_size = block_size
        self._device = device
        self._is_recording = False
        self._stream = None
        self._audio_queue = queue.Queue()
        self._all_frames = []
        self._current_level = 0.0
        self._level_lock = threading.Lock()

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    @property
    def audio_queue(self) -> queue.Queue:
        return self._audio_queue

    @property
    def current_level(self) -> float:
        with self._level_lock:
            return self._current_level

    @staticmethod
    def list_devices():
        devices = sd.query_devices()
        input_devs = []
        for i, d in enumerate(devices):
            if d["max_input_channels"] > 0:
                input_devs.append({
                    "index": i,
                    "name": d["name"],
                    "channels": d["max_input_channels"],
                    "sample_rate": int(d["default_samplerate"]),
                })
        return input_devs

    def start(self):
        if self._is_recording:
            return

        self._is_recording = True
        self._audio_queue = queue.Queue()
        self._all_frames = []
        self._current_level = 0.0

        stream_kwargs = {
            "samplerate": self._sample_rate,
            "channels": self._channels,
            "dtype": 'int16',
            "blocksize": self._block_size,
            "callback": self._audio_callback,
        }
        if self._device is not None:
            stream_kwargs["device"] = self._device

        self._stream = sd.InputStream(**stream_kwargs)
        self._stream.start()
        print(f"[AudioRecorder] started (device={self._device}, rate={self._sample_rate})")

    def stop(self):
        self._is_recording = False
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        print("[AudioRecorder] stopped")

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            print(f"[AudioRecorder] status: {status}")
        if self._is_recording:
            data = indata.copy().flatten()
            self._audio_queue.put(data.tobytes())
            self._all_frames.append(data)
            rms = math.sqrt(np.mean(data.astype(np.float64) ** 2))
            with self._level_lock:
                self._current_level = min(rms / 32768.0, 1.0)

    def get_full_audio(self) -> np.ndarray:
        if self._all_frames:
            return np.concatenate(self._all_frames)
        return np.array([], dtype=np.int16)
