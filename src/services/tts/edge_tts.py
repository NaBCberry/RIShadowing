import os
import asyncio
import edge_tts
from src.services.tts.base import BaseTTSEngine


class EdgeTTSEngine(BaseTTSEngine):

    def __init__(self, voice: str = "en-US-JennyNeural"):
        self._voice = voice

    @staticmethod
    def engine_name() -> str:
        return "Edge-TTS (在线)"

    @staticmethod
    def is_available() -> bool:
        return True

    def synthesize(self, text: str, output_path: str) -> str:
        if not text.strip():
            return output_path
        asyncio.run(self._synthesize_async(text, output_path))
        return output_path

    async def _synthesize_async(self, text: str, output_path: str):
        communicate = edge_tts.Communicate(text, self._voice)
        await communicate.save(output_path)
        print(f"[EdgeTTS] synthesized to {output_path}")

    @staticmethod
    def list_voices():
        async def _list():
            voices = await edge_tts.VoicesManager.create()
            result = []
            for v in voices.voices:
                result.append({
                    "name": v["ShortName"],
                    "locale": v["Locale"],
                    "gender": v.get("Gender", ""),
                })
            return result
        return asyncio.run(_list())
