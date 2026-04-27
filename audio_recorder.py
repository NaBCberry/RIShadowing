import threading
import queue
import sounddevice as sd
import numpy as np


class AudioRecorder:
    def __init__(self, sample_rate: int = 16000, channels: int = 1, block_size: int = 4000):
        self._sample_rate = sample_rate
        self._channels = channels
        self._block_size = block_size
        self._is_recording = False
        self._stream = None
        self._audio_queue = queue.Queue()
        self._all_frames = []

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    @property
    def audio_queue(self) -> queue.Queue:
        return self._audio_queue

    def start(self):
        if self._is_recording:
            return

        self._is_recording = True
        self._audio_queue = queue.Queue()
        self._all_frames = []
        self._stream = sd.InputStream(
            samplerate=self._sample_rate,
            channels=self._channels,
            dtype='int16',
            blocksize=self._block_size,
            callback=self._audio_callback,
        )
        self._stream.start()

    def stop(self):
        self._is_recording = False
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            print(f"AudioRecorder status: {status}")
        if self._is_recording:
            data = indata.copy().flatten()
            self._audio_queue.put(data.tobytes())
            self._all_frames.append(data)

    def get_full_audio(self) -> np.ndarray:
        if self._all_frames:
            return np.concatenate(self._all_frames)
        return np.array([], dtype=np.int16)
