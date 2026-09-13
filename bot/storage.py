import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class SQLiteCrudStore:
    """Small SQLite CRUD foundation for stores backed by a single table."""

    def __init__(self, path: Path, table: str, columns: dict[str, str]) -> None:
        self.path = path
        self.table = table
        self.columns = columns
        self.path.parent.mkdir(parents=True, exist_ok=True)
        definitions = ", ".join(f"{name} {definition}" for name, definition in columns.items())
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                f"CREATE TABLE IF NOT EXISTS {self.table} "
                f"(id INTEGER PRIMARY KEY AUTOINCREMENT, {definitions})"
            )

    def create(self, values: dict[str, Any]) -> int:
        names = list(values)
        placeholders = ", ".join("?" for _ in names)
        with sqlite3.connect(self.path) as connection:
            cursor = connection.execute(
                f"INSERT INTO {self.table} ({', '.join(names)}) VALUES ({placeholders})",
                [values[name] for name in names],
            )
            return int(cursor.lastrowid)

    def list(self) -> list[dict[str, Any]]:
        with sqlite3.connect(self.path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                f"SELECT id, {', '.join(self.columns)} FROM {self.table} ORDER BY id"
            ).fetchall()
        return [dict(row) for row in rows]

    def get(self, record_id: int) -> dict[str, Any] | None:
        with sqlite3.connect(self.path) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                f"SELECT id, {', '.join(self.columns)} FROM {self.table} WHERE id = ?",
                (record_id,),
            ).fetchone()
        return dict(row) if row else None

    def update(self, record_id: int, values: dict[str, Any]) -> bool:
        assignments = ", ".join(f"{name} = ?" for name in values)
        with sqlite3.connect(self.path) as connection:
            cursor = connection.execute(
                f"UPDATE {self.table} SET {assignments} WHERE id = ?",
                [*values.values(), record_id],
            )
        return cursor.rowcount == 1

    def delete(self, record_id: int) -> bool:
        with sqlite3.connect(self.path) as connection:
            cursor = connection.execute(
                f"DELETE FROM {self.table} WHERE id = ?", (record_id,)
            )
        return cursor.rowcount == 1


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


@dataclass(frozen=True)
class FreeCertification:
    id: int
    name: str
    provider: str
    url: str
    is_free: bool
    hands_on: bool


class CertificationStore(SQLiteCrudStore):
    def __init__(self, path: Path) -> None:
        super().__init__(
            path,
            "free_certifications",
            {
                "name": "TEXT NOT NULL",
                "provider": "TEXT NOT NULL",
                "url": "TEXT NOT NULL",
                "is_free": "INTEGER NOT NULL DEFAULT 1",
                "hands_on": "INTEGER NOT NULL DEFAULT 0",
            },
        )
        with sqlite3.connect(self.path) as connection:
            columns = {
                row[1]
                for row in connection.execute("PRAGMA table_info(free_certifications)")
            }
            if "is_free" not in columns:
                connection.execute(
                    "ALTER TABLE free_certifications "
                    "ADD COLUMN is_free INTEGER NOT NULL DEFAULT 1"
                )
            if "hands_on" not in columns:
                connection.execute(
                    "ALTER TABLE free_certifications "
                    "ADD COLUMN hands_on INTEGER NOT NULL DEFAULT 0"
                )

    def add(
        self,
        name: str,
        provider: str,
        url: str,
        is_free: bool = True,
        hands_on: bool = False,
    ) -> int:
        return self.create(
            {
                "name": name,
                "provider": provider,
                "url": url,
                "is_free": int(is_free),
                "hands_on": int(hands_on),
            }
        )

    def all(self) -> list[FreeCertification]:
        return [self._to_certification(record) for record in self.list()]

    def find(self, certification_id: int) -> FreeCertification | None:
        record = self.get(certification_id)
        return self._to_certification(record) if record else None

    @staticmethod
    def _to_certification(record: dict[str, Any]) -> FreeCertification:
        return FreeCertification(
            **{
                **record,
                "is_free": bool(record["is_free"]),
                "hands_on": bool(record["hands_on"]),
            }
        )

    def edit(self, certification_id: int, **values: str | bool) -> bool:
        for field in ("is_free", "hands_on"):
            if field in values:
                values[field] = int(values[field])
        return self.update(certification_id, values)

    def remove(self, certification_id: int) -> bool:
        return self.delete(certification_id)