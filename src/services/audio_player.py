import time
import sounddevice as sd
import soundfile as sf
import numpy as np


class AudioPlayer:
    def __init__(self, device=None):
        self._audio_data = None
        self._sample_rate = None
        self._is_playing = False
        self._start_time = 0.0
        self._device = device
        self._on_finished = None

    def load_file(self, file_path: str):
        self._audio_data, self._sample_rate = sf.read(file_path, dtype='float32')
        if self._audio_data.ndim == 1:
            self._audio_data = self._audio_data.reshape(-1, 1)

    def load_array(self, audio_data: np.ndarray, sample_rate: int):
        self._audio_data = audio_data.astype(np.float32)
        if self._audio_data.ndim == 1:
            self._audio_data = self._audio_data.reshape(-1, 1)
        self._sample_rate = sample_rate

    @property
    def duration(self) -> float:
        if self._audio_data is None or self._sample_rate is None:
            return 0.0
        return len(self._audio_data) / self._sample_rate

    @property
    def is_playing(self) -> bool:
        return self._is_playing and (
            self.position < self.duration - 0.01
        )

    @property
    def position(self) -> float:
        if not self._is_playing:
            return 0.0
        elapsed = time.time() - self._start_time
        return min(elapsed, self.duration)

    @staticmethod
    def list_devices():
        devices = sd.query_devices()
        output_devs = []
        for i, d in enumerate(devices):
            if d["max_output_channels"] > 0:
                output_devs.append({
                    "index": i,
                    "name": d["name"],
                    "channels": d["max_output_channels"],
                    "sample_rate": int(d["default_samplerate"]),
                })
        return output_devs

    def play(self, on_finished=None):
        if self._audio_data is None:
            return

        sd.stop()
        self._on_finished = on_finished
        self._is_playing = True
        self._start_time = time.time()

        kwargs = {
            "samplerate": self._sample_rate,
            "blocking": False,
        }
        if self._device is not None:
            kwargs["device"] = self._device

        sd.play(self._audio_data, **kwargs)

        import threading
        def _wait():
            try:
                sd.wait()
            except Exception as e:
                print(f"[AudioPlayer] wait error: {e}")
            self._is_playing = False
            if self._on_finished:
                self._on_finished()

        thread = threading.Thread(target=_wait, daemon=True)
        thread.start()
        print(f"[AudioPlayer] playing (device={self._device})")

    def stop(self):
        self._is_playing = False
        try:
            sd.stop()
        except Exception as e:
            print(f"[AudioPlayer] stop error: {e}")
