import sqlite3
from pathlib import Path


class AnnouncementStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS announcements (channel_id INTEGER PRIMARY KEY, week TEXT NOT NULL)"
            )

    def was_sent(self, channel_id: int, week: str) -> bool:
        with sqlite3.connect(self.path) as connection:
            row = connection.execute(
                "SELECT 1 FROM announcements WHERE channel_id = ? AND week = ?",
                (channel_id, week),
            ).fetchone()
        return row is not None

    def mark_sent(self, channel_id: int, week: str) -> None:
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "INSERT INTO announcements(channel_id, week) VALUES (?, ?) "
                "ON CONFLICT(channel_id) DO UPDATE SET week = excluded.week",
                (channel_id, week),
            )