from src.services.tts.base import BaseTTSEngine


class Pyttsx3Engine(BaseTTSEngine):

    @staticmethod
    def engine_name() -> str:
        return "pyttsx3 (离线-系统)"

    @staticmethod
    def is_available() -> bool:
        try:
            import pyttsx3
            return True
        except ImportError:
            return False

    def synthesize(self, text: str, output_path: str) -> str:
        import pyttsx3
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        for v in voices:
            if hasattr(v, "languages") and v.languages:
                if any(l.startswith("en") for l in v.languages):
                    engine.setProperty("voice", v.id)
                    break
        engine.setProperty("rate", 155)
        engine.save_to_file(text, output_path)
        engine.runAndWait()
        print(f"[Pyttsx3] synthesized to {output_path}")
        return output_path
