from abc import ABC, abstractmethod
import os


class BaseTTSEngine(ABC):
    @abstractmethod
    def engine_name(self) -> str:
        ...

    @abstractmethod
    def synthesize(self, text: str, output_path: str) -> str:
        ...

    @staticmethod
    def is_available() -> bool:
        return True


def create_tts_engine(engine: str, **kwargs) -> BaseTTSEngine:
    if engine == "edge":
        from src.services.tts.edge_tts import EdgeTTSEngine
        return EdgeTTSEngine(**kwargs)
    elif engine == "piper":
        from src.services.tts.piper_tts import PiperTTSEngine
        return PiperTTSEngine(**kwargs)
    elif engine == "pyttsx3":
        from src.services.tts.pyttsx3_tts import Pyttsx3Engine
        return Pyttsx3Engine(**kwargs)
    else:
        raise ValueError(f"Unknown TTS engine: {engine}")


def list_available_engines():
    engines = []
    from src.services.tts.edge_tts import EdgeTTSEngine
    from src.services.tts.piper_tts import PiperTTSEngine
    from src.services.tts.pyttsx3_tts import Pyttsx3Engine

    if EdgeTTSEngine.is_available():
        engines.append(("edge", EdgeTTSEngine.engine_name()))
    if PiperTTSEngine.is_available():
        engines.append(("piper", PiperTTSEngine.engine_name()))
    if Pyttsx3Engine.is_available():
        engines.append(("pyttsx3", Pyttsx3Engine.engine_name()))
    return engines
