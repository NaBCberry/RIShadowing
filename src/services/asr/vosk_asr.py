import os
import json
from typing import Dict
from src.services.asr.base import BaseASREngine
from src.services.speech_recognizer import _find_vosk_model


class VoskASREngine(BaseASREngine):

    def __init__(self, model_path: str = None):
        self._model_path = model_path or _find_vosk_model()

    @staticmethod
    def engine_name() -> str:
        return "Vosk (离线-快速)"

    @staticmethod
    def is_available() -> bool:
        try:
            import vosk
            return _find_vosk_model() is not None
        except Exception:
            return False

    def transcribe(self, audio_path: str) -> Dict:
        import vosk
        import soundfile as sf
        import numpy as np

        if not self._model_path:
            return {"text": "", "words": [], "duration": 0.0}

        audio, sr = sf.read(audio_path, dtype='int16')
        if audio.ndim > 1:
            audio = audio.mean(axis=1).astype(np.int16)
        duration = len(audio) / sr

        if sr != 16000:
            print(f"[VoskASR] resampling {sr}Hz -> 16000Hz...")
            try:
                import samplerate
                ratio = 16000 / sr
                audio = samplerate.resample(audio.astype(np.float32), ratio, 'sinc_best')
                audio = (audio * 32767).astype(np.int16)
            except ImportError:
                ratio = 16000 / sr
                new_len = int(len(audio) * ratio)
                indices = np.linspace(0, len(audio) - 1, new_len)
                audio = np.interp(indices, np.arange(len(audio)), audio.astype(np.float32))
                audio = audio.astype(np.int16)
            sr = 16000

        model = vosk.Model(self._model_path)
        rec = vosk.KaldiRecognizer(model, sr)
        rec.SetWords(True)

        chunk_size = 4000
        results = []
        for i in range(0, len(audio), chunk_size):
            chunk = audio[i:i + chunk_size]
            rec.AcceptWaveform(chunk.tobytes())

        final = json.loads(rec.FinalResult())
        raw_words = final.get("result", [])
        words = [
            {
                "word": w.get("word", ""),
                "start": w.get("start", 0.0),
                "end": w.get("end", 0.0),
                "conf": w.get("conf", 0.0),
            }
            for w in raw_words
        ]
        text = " ".join(w["word"] for w in words)

        print(f"[VoskASR] transcribed {len(words)} words from {audio_path}")
        return {"text": text, "words": words, "duration": duration}
