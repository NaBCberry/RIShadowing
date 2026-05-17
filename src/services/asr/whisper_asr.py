import os
from typing import Dict
from src.services.asr.base import BaseASREngine


class WhisperASREngine(BaseASREngine):

    def __init__(self, api_key: str = None, endpoint: str = None):
        self._api_key = api_key or os.environ.get("WHISPER_API_KEY")
        self._endpoint = endpoint or "https://api.openai.com/v1/audio/transcriptions"

    @staticmethod
    def engine_name() -> str:
        return "Whisper API (在线-精准)"

    @staticmethod
    def is_available() -> bool:
        try:
            import openai
            return True
        except ImportError:
            return False

    def transcribe(self, audio_path: str) -> Dict:
        from openai import OpenAI

        if not self._api_key:
            raise RuntimeError("Whisper API 密钥未配置，请在 .env 中填入 WHISPER_API_KEY")

        client = OpenAI(api_key=self._api_key)
        if self._endpoint:
            client.base_url = self._endpoint

        with open(audio_path, "rb") as f:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="verbose_json",
                timestamp_granularities=["word"],
            )

        words = []
        raw_words = getattr(response, "words", []) or []
        for w in raw_words:
            words.append({
                "word": getattr(w, "word", ""),
                "start": getattr(w, "start", 0.0),
                "end": getattr(w, "end", 0.0),
                "conf": getattr(w, "confidence", 0.0) if hasattr(w, "confidence") else 1.0,
            })

        text = " ".join(w["word"] for w in words)
        duration = words[-1]["end"] if words else 0.0

        print(f"[WhisperASR] transcribed {len(words)} words from {audio_path}")
        return {"text": text, "words": words, "duration": duration}
