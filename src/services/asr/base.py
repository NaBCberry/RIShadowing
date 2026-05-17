from abc import ABC, abstractmethod
from typing import List, Dict


class BaseASREngine(ABC):

    @staticmethod
    @abstractmethod
    def engine_name() -> str:
        ...

    @abstractmethod
    def transcribe(self, audio_path: str) -> Dict:
        ...

    @staticmethod
    def is_available() -> bool:
        return True
