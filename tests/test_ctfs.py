from datetime import datetime, timezone

import httpx

from bot.ctfs import CTFtimeProvider


def test_provider_filters_by_ctftime_onsite_flag() -> None:
    now = datetime(2026, 9, 13, 12, tzinfo=timezone.utc)
    payload = [
        {
            "id": 1,
            "title": "Online CTF",
            "start": "2026-09-14T12:00:00+00:00",
            "finish": "2026-09-14T16:00:00+00:00",
            "weight": 10,
            "format": "Jeopardy",
            "onsite": False,
            "ctftime_url": "https://ctftime.org/event/1/",
        },
        {
            "id": 2,
            "title": "Onsite CTF",
            "start": "2026-09-15T12:00:00+00:00",
            "finish": "2026-09-15T16:00:00+00:00",
            "weight": 20,
            "format": "Jeopardy",
            "onsite": True,
            "ctftime_url": "https://ctftime.org/event/2/",
        },
    ]
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=payload))

    import asyncio

    provider = CTFtimeProvider("https://example.test/events", httpx.AsyncClient(transport=transport))
    events = asyncio.run(provider.upcoming_online(now))

    assert [event.title for event in events] == ["Online CTF"]