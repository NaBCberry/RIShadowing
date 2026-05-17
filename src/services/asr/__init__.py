from src.services.asr.base import BaseASREngine


def create_asr_engine(engine: str, **kwargs) -> BaseASREngine:
    if engine == "vosk":
        from src.services.asr.vosk_asr import VoskASREngine
        return VoskASREngine(**kwargs)
    elif engine == "whisper":
        from src.services.asr.whisper_asr import WhisperASREngine
        return WhisperASREngine(**kwargs)
    else:
        raise ValueError(f"Unknown ASR engine: {engine}")


def list_available_asr_engines():
    engines = []
    from src.services.asr.vosk_asr import VoskASREngine
    from src.services.asr.whisper_asr import WhisperASREngine

    if VoskASREngine.is_available():
        engines.append(("vosk", VoskASREngine.engine_name()))
    if WhisperASREngine.is_available():
        engines.append(("whisper", WhisperASREngine.engine_name()))
    return engines
