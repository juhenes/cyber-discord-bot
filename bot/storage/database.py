from contextlib import contextmanager
from pathlib import Path
import sqlite3
from typing import Any, Generator

from .models import Certification


@contextmanager
def connect_db(path: Path) -> Generator[sqlite3.Connection, None, None]:
    """Context manager for SQLite connections that commits on exit and closes cleanly."""
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


class SQLiteCrudStore:
    """Reusable SQLite CRUD store for single-table operations."""

    def __init__(self, path: Path, table: str, columns: dict[str, str]) -> None:
        self.path = path
        self.table = table
        self.columns = columns
        definitions = ", ".join(f"{name} {definition}" for name, definition in columns.items())
        with self._connect() as connection:
            connection.execute(
                f"CREATE TABLE IF NOT EXISTS {self.table} "
                f"(id INTEGER PRIMARY KEY AUTOINCREMENT, {definitions})"
            )

    def _connect(self) -> Generator[sqlite3.Connection, None, None]:
        return connect_db(self.path)

    def create(self, values: dict[str, Any]) -> int:
        names = list(values)
        placeholders = ", ".join("?" for _ in names)
        with self._connect() as connection:
            cursor = connection.execute(
                f"INSERT INTO {self.table} ({', '.join(names)}) VALUES ({placeholders})",
                [values[name] for name in names],
            )
            return int(cursor.lastrowid)

    def list(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT id, {', '.join(self.columns)} FROM {self.table} ORDER BY id"
            ).fetchall()
        return [dict(row) for row in rows]

    def get(self, record_id: int) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                f"SELECT id, {', '.join(self.columns)} FROM {self.table} WHERE id = ?",
                (record_id,),
            ).fetchone()
        return dict(row) if row else None

    def update(self, record_id: int, values: dict[str, Any]) -> bool:
        if not values:
            return False
        assignments = ", ".join(f"{name} = ?" for name in values)
        with self._connect() as connection:
            cursor = connection.execute(
                f"UPDATE {self.table} SET {assignments} WHERE id = ?",
                [*values.values(), record_id],
            )
        return cursor.rowcount == 1

    def delete(self, record_id: int) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                f"DELETE FROM {self.table} WHERE id = ?", (record_id,)
            )
        return cursor.rowcount == 1


class AnnouncementStore:
    """Tracks weekly CTF announcements to avoid duplicate broadcasts."""

    def __init__(self, path: Path) -> None:
        self.path = path
        with connect_db(self.path) as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS announcements "
                "(channel_id INTEGER PRIMARY KEY, week TEXT NOT NULL)"
            )

    def was_sent(self, channel_id: int, week: str) -> bool:
        with connect_db(self.path) as connection:
            row = connection.execute(
                "SELECT 1 FROM announcements WHERE channel_id = ? AND week = ?",
                (channel_id, week),
            ).fetchone()
        return row is not None

    def mark_sent(self, channel_id: int, week: str) -> None:
        with connect_db(self.path) as connection:
            connection.execute(
                "INSERT INTO announcements(channel_id, week) VALUES (?, ?) "
                "ON CONFLICT(channel_id) DO UPDATE SET week = excluded.week",
                (channel_id, week),
            )


class CertificationStore(SQLiteCrudStore):
    """Store for managing certifications with CRUD operations."""

    VALID_FIELDS = {"name", "provider", "url", "is_free", "hands_on"}

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
        # Handle schema migration for older databases
        with self._connect() as connection:
            columns = {
                row["name"]
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
                "name": name.strip(),
                "provider": provider.strip(),
                "url": url.strip(),
                "is_free": int(bool(is_free)),
                "hands_on": int(bool(hands_on)),
            }
        )

    def all(self) -> list[Certification]:
        return [self._to_certification(record) for record in self.list()]

    def find(self, certification_id: int) -> Certification | None:
        record = self.get(certification_id)
        return self._to_certification(record) if record else None

    @staticmethod
    def _to_certification(record: dict[str, Any]) -> Certification:
        return Certification(
            id=int(record["id"]),
            name=str(record["name"]),
            provider=str(record["provider"]),
            url=str(record["url"]),
            is_free=bool(record["is_free"]),
            hands_on=bool(record["hands_on"]),
        )

    def edit(self, certification_id: int, **values: Any) -> bool:
        filtered: dict[str, Any] = {}
        for key, value in values.items():
            if key not in self.VALID_FIELDS or value is None:
                continue
            if key in ("is_free", "hands_on"):
                filtered[key] = int(bool(value))
            elif isinstance(value, str):
                filtered[key] = value.strip()
            else:
                filtered[key] = value
        if not filtered:
            return False
        return self.update(certification_id, filtered)

    def remove(self, certification_id: int) -> bool:
        return self.delete(certification_id)
