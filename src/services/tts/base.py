from abc import ABC, abstractmethod


class BaseTTSEngine(ABC):

    @staticmethod
    @abstractmethod
    def engine_name() -> str:
        ...

    @abstractmethod
    def synthesize(self, text: str, output_path: str) -> str:
        ...

    @staticmethod
    def is_available() -> bool:
        return True
