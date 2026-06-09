import sqlite3
import os
import threading
from src.utils.paths import get_db_path


class Database:
    _instance = None
    _lock = threading.Lock()

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = get_db_path()
        self._db_path = db_path
        self._conn = None

    @classmethod
    def get_instance(cls, db_path: str = None) -> "Database":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(db_path)
        return cls._instance

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
