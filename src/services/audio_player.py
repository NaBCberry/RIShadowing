import threading
import time
import sounddevice as sd
import soundfile as sf
import numpy as np


class AudioPlayer:
    def __init__(self, device=None):
        self._audio_data = None
        self._sample_rate = None
        self._is_playing = False
        self._position = 0.0
        self._last_update_time = 0.0
        self._lock = threading.Lock()
        self._stream = None
        self._device = device

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
        return self._is_playing

    @property
    def position(self) -> float:
        with self._lock:
            if not self._is_playing:
                return self._position
            return self._position + (time.time() - self._last_update_time)

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

        self._is_playing = True
        self._position = 0.0
        self._last_update_time = time.time()

        def _play_thread():
            try:
                stream_kwargs = {
                    "samplerate": self._sample_rate,
                    "channels": self._audio_data.shape[1],
                    "dtype": 'float32',
                }
                if self._device is not None:
                    stream_kwargs["device"] = self._device

                stream = sd.OutputStream(**stream_kwargs)
                self._stream = stream
                stream.start()

                chunk_size = 1024
                total_frames = len(self._audio_data)
                pos = 0

                while pos < total_frames and self._is_playing:
                    end = min(pos + chunk_size, total_frames)
                    stream.write(self._audio_data[pos:end])
                    pos = end
                    with self._lock:
                        self._position = pos / self._sample_rate
                        self._last_update_time = time.time()

                if self._stream is stream:
                    self._stream = None
                    stream.stop()
                    stream.close()
            except Exception as e:
                print(f"[AudioPlayer] error: {e}")
            finally:
                self._is_playing = False
                if on_finished:
                    on_finished()

        thread = threading.Thread(target=_play_thread, daemon=True)
        thread.start()
        print(f"[AudioPlayer] playing (device={self._device})")

    def stop(self):
        self._is_playing = False
        stream = self._stream
        self._stream = None
        if stream:
            try:
                stream.abort()
            except Exception:
                pass
            try:
                stream.close()
            except Exception:
                pass
