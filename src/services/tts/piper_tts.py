import os
import subprocess
from src.services.tts.base import BaseTTSEngine


class PiperTTSEngine(BaseTTSEngine):

    def __init__(self, model_path: str = None, piper_path: str = None):
        self._model_path = model_path
        self._piper_path = piper_path or self._find_piper()

    @staticmethod
    def engine_name() -> str:
        return "Piper TTS (离线)"

    @staticmethod
    def is_available() -> bool:
        path = PiperTTSEngine._find_piper()
        return path is not None

    @staticmethod
    def _find_piper() -> str:
        candidates = [
            os.path.join(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )), "piper", "piper.exe"),
            "piper", "piper.exe",
        ]
        for c in candidates:
            if os.path.isfile(c):
                return os.path.abspath(c)
        result = subprocess.run(["where", "piper"], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split("\n")[0].strip()
        return None

    def synthesize(self, text: str, output_path: str) -> str:
        if not self._piper_path:
            raise RuntimeError("piper executable not found")
        if not self._model_path:
            raise RuntimeError("piper model not configured")

        proc = subprocess.run(
            [self._piper_path, "--model", self._model_path,
             "--output_file", output_path],
            input=text, text=True, capture_output=True,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"piper error: {proc.stderr}")
        print(f"[PiperTTS] synthesized to {output_path}")
        return output_path
