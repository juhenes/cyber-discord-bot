from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    discord_token: str
    announcement_channel_id: int
    ctftime_api_url: str
    announcement_weekday: int
    announcement_hour_utc: int
    database_path: Path

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        token = os.environ.get("DISCORD_TOKEN", "").strip()
        channel_id = os.environ.get("ANNOUNCEMENT_CHANNEL_ID", "").strip()
        if not token:
            raise ValueError("DISCORD_TOKEN is required")
        if not channel_id.isdigit():
            raise ValueError("ANNOUNCEMENT_CHANNEL_ID must be a Discord channel ID")

        weekday = int(os.environ.get("ANNOUNCEMENT_WEEKDAY", "0"))
        hour = int(os.environ.get("ANNOUNCEMENT_HOUR_UTC", "9"))
        if weekday not in range(7) or hour not in range(24):
            raise ValueError("ANNOUNCEMENT_WEEKDAY must be 0-6 and ANNOUNCEMENT_HOUR_UTC must be 0-23")

        return cls(
            discord_token=token,
            announcement_channel_id=int(channel_id),
            ctftime_api_url=os.environ.get(
                "CTFTIME_API_URL", "https://ctftime.org/api/v1/events/"
            ),
            announcement_weekday=weekday,
            announcement_hour_utc=hour,
            database_path=Path(os.environ.get("DATABASE_PATH", "data/bot.sqlite3")),
        )