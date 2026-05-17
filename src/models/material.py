import os
from typing import List, Optional
from src.models.db import Database


class Material:
    def __init__(self, row=None, **kwargs):
        if row:
            self.id = row["id"]
            self.title = row["title"]
            self.topic = row["topic"]
            self.difficulty = row["difficulty"]
            self.duration = row["duration"]
            self.text = row["text"]
            self.audio_path = row["audio_path"]
            self.created_at = row["created_at"]
            self.practice_count = row["practice_count"]
            self.best_score = row["best_score"]
        else:
            self.id = kwargs.get("id")
            self.title = kwargs.get("title", "")
            self.topic = kwargs.get("topic", "")
            self.difficulty = kwargs.get("difficulty", "")
            self.duration = kwargs.get("duration", 0.0)
            self.text = kwargs.get("text", "")
            self.audio_path = kwargs.get("audio_path", "")
            self.created_at = kwargs.get("created_at", "")
            self.practice_count = kwargs.get("practice_count", 0)
            self.best_score = kwargs.get("best_score", 0.0)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "topic": self.topic,
            "difficulty": self.difficulty,
            "duration": self.duration,
            "text": self.text,
            "audio_path": self.audio_path,
            "created_at": self.created_at,
            "practice_count": self.practice_count,
            "best_score": self.best_score,
        }


def init_db():
    db = Database.get_instance()
    db.conn.execute("""
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            topic TEXT DEFAULT '',
            difficulty TEXT DEFAULT '',
            duration REAL DEFAULT 0.0,
            text TEXT DEFAULT '',
            audio_path TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            practice_count INTEGER DEFAULT 0,
            best_score REAL DEFAULT 0.0
        )
    """)
    db.conn.execute("""
        CREATE TABLE IF NOT EXISTS practice_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_id INTEGER NOT NULL,
            score REAL DEFAULT 0.0,
            green_count INTEGER DEFAULT 0,
            yellow_count INTEGER DEFAULT 0,
            red_count INTEGER DEFAULT 0,
            duration REAL DEFAULT 0.0,
            practiced_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (material_id) REFERENCES materials(id) ON DELETE CASCADE
        )
    """)
    db.conn.commit()


def add_material(material: Material) -> int:
    db = Database.get_instance()
    cursor = db.conn.execute(
        """INSERT INTO materials (title, topic, difficulty, duration, text, audio_path)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (material.title, material.topic, material.difficulty,
         material.duration, material.text, material.audio_path),
    )
    db.conn.commit()
    return cursor.lastrowid


def update_material(material: Material):
    db = Database.get_instance()
    db.conn.execute(
        """UPDATE materials SET title=?, topic=?, difficulty=?, duration=?,
           text=?, audio_path=? WHERE id=?""",
        (material.title, material.topic, material.difficulty,
         material.duration, material.text, material.audio_path,
         material.id),
    )
    db.conn.commit()


def delete_material(material_id: int):
    db = Database.get_instance()
    db.conn.execute("DELETE FROM materials WHERE id=?", (material_id,))
    db.conn.commit()


def get_material(material_id: int) -> Optional[Material]:
    db = Database.get_instance()
    row = db.conn.execute(
        "SELECT * FROM materials WHERE id=?", (material_id,)
    ).fetchone()
    return Material(row) if row else None


def list_materials(topic: str = None, difficulty: str = None,
                   search: str = None) -> List[Material]:
    db = Database.get_instance()
    query = "SELECT * FROM materials WHERE 1=1"
    params = []
    if topic:
        query += " AND topic=?"
        params.append(topic)
    if difficulty:
        query += " AND difficulty=?"
        params.append(difficulty)
    if search:
        query += " AND (title LIKE ? OR text LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    query += " ORDER BY created_at DESC"
    rows = db.conn.execute(query, params).fetchall()
    return [Material(row) for row in rows]


def get_all_topics() -> List[str]:
    db = Database.get_instance()
    rows = db.conn.execute(
        "SELECT DISTINCT topic FROM materials WHERE topic!='' ORDER BY topic"
    ).fetchall()
    return [r["topic"] for r in rows]


def record_practice(material_id: int, score: float, green: int,
                    yellow: int, red: int, duration: float):
    db = Database.get_instance()
    db.conn.execute(
        """INSERT INTO practice_records (material_id, score, green_count,
           yellow_count, red_count, duration)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (material_id, score, green, yellow, red, duration),
    )
    db.conn.execute(
        """UPDATE materials SET practice_count = practice_count + 1,
           best_score = MAX(best_score, ?) WHERE id=?""",
        (score, material_id),
    )
    db.conn.commit()
