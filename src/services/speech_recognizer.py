import json
import os
import glob
import queue
import threading

try:
    import vosk
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False


def _find_vosk_model():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    search_dirs = [
        current_dir,
        project_root,
        os.getcwd(),
    ]
    for search_dir in search_dirs:
        for pattern in ["vosk-model*", "vosk-model*/am"]:
            matches = glob.glob(os.path.join(search_dir, pattern))
            for m in matches:
                if m.endswith("am"):
                    m = os.path.dirname(m)
                conf = os.path.join(m, "conf", "model.conf")
                mdl = os.path.join(m, "am", "final.mdl")
                if os.path.isfile(conf) and os.path.isfile(mdl):
                    return m
    return None


class SpeechRecognizer:
    def __init__(self, model_path: str = None, sample_rate: int = 16000):
        self._sample_rate = sample_rate
        self._model = None
        self._recognizer = None
        self._is_running = False
        self._results = []
        self._partial_text = ""
        self._lock = threading.Lock()
        self._model_path = model_path if model_path else _find_vosk_model()

    def initialize(self) -> bool:
        if not VOSK_AVAILABLE:
            print("Vosk not installed. Run: pip install vosk")
            return False
        if not self._model_path:
            print("No Vosk model found. Download from https://alphacephei.com/vosk/models")
            print("Extract to the project root directory.")
            return False
        try:
            self._model = vosk.Model(self._model_path)
            self._recognizer = vosk.KaldiRecognizer(self._model, self._sample_rate)
            print(f"Vosk model loaded: {self._model_path}")
            return True
        except Exception as e:
            print(f"Vosk init error: {e}")
            return False

    @property
    def partial_text(self) -> str:
        with self._lock:
            return self._partial_text

    @property
    def results(self) -> list:
        with self._lock:
            return list(self._results)

    def process_audio(self, audio_queue: queue.Queue):
        self._is_running = True
        chunk_count = 0
        accept_count = 0
        while self._is_running:
            try:
                data = audio_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if data is None:
                break

            chunk_count += 1

            if self._recognizer.AcceptWaveform(data):
                accept_count += 1
                result = json.loads(self._recognizer.Result())
                text = result.get("text", "").strip()
                if text:
                    print(f"[STT] final: '{text}'")
                    with self._lock:
                        self._results.append({
                            "text": text,
                            "result": result.get("result", []),
                        })
            else:
                partial = json.loads(self._recognizer.PartialResult())
                text = partial.get("partial", "").strip()
                if text:
                    print(f"[STT] partial: '{text}'")
                with self._lock:
                    self._partial_text = text

        print(f"[STT] process_audio ended. chunks={chunk_count}, accepted={accept_count}")
        if self._recognizer:
            final = json.loads(self._recognizer.FinalResult())
            text = final.get("text", "").strip()
            if text:
                print(f"[STT] drain final: '{text}'")
                with self._lock:
                    self._results.append({
                        "text": text,
                        "result": final.get("result", []),
                    })

    def start(self, audio_queue: queue.Queue):
        if not self._recognizer:
            return
        self._is_running = True
        self._results = []
        self._partial_text = ""
        thread = threading.Thread(
            target=self.process_audio, args=(audio_queue,), daemon=True
        )
        thread.start()
        return thread

    def stop(self):
        self._is_running = False

    def get_latest_words(self) -> list:
        with self._lock:
            words = []
            for r in self._results:
                for w in r.get("result", []):
                    words.append({
                        "word": w.get("word", ""),
                        "start": w.get("start", 0.0),
                        "end": w.get("end", 0.0),
                        "conf": w.get("conf", 0.0),
                    })
            return words
