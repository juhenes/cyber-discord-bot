from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx


@dataclass(frozen=True)
class CTF:
    id: int
    title: str
    start: datetime
    finish: datetime
    weight: float | None
    url: str
    format: str
    onsite: bool

    @property
    def duration(self) -> str:
        hours = max(1, round((self.finish - self.start).total_seconds() / 3600))
        return f"{hours} hour{'s' if hours != 1 else ''}"


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _to_ctf(raw: dict[str, Any]) -> CTF:
    weight = raw.get("weight")
    return CTF(
        id=int(raw["id"]),
        title=str(raw["title"]),
        start=_parse_datetime(raw["start"]),
        finish=_parse_datetime(raw["finish"]),
        weight=float(weight) if weight is not None else None,
        url=str(raw.get("ctftime_url") or raw.get("url") or "https://ctftime.org/"),
        format=str(raw.get("format") or "Unknown"),
        onsite=bool(raw.get("onsite", False)),
    )


class CTFtimeProvider:
    """Retrieves public events; Discord-facing code never depends on this API shape."""

    def __init__(self, api_url: str, client: httpx.AsyncClient | None = None) -> None:
        self.api_url = api_url
        self.client = client

    async def upcoming_online(self, now: datetime | None = None) -> list[CTF]:
        now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        finish = now + timedelta(days=7)
        params = {"start": int(now.timestamp()), "finish": int(finish.timestamp()), "limit": 100}
        owns_client = self.client is None
        client = self.client or httpx.AsyncClient(timeout=20)
        try:
            response = await client.get(
                self.api_url,
                params=params,
                headers={"User-Agent": "cybersecurity-bot/1.0 (+Discord weekly CTF announcements)"},
            )
            response.raise_for_status()
            events = [_to_ctf(item) for item in response.json()]
        finally:
            if owns_client:
                await client.aclose()

        return sorted(
            (
                event
                for event in events
                if event.start >= now
                and event.start <= finish
                and not event.onsite
            ),
            key=lambda event: event.start,
        )