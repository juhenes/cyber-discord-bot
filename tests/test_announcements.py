from datetime import datetime, timezone

from bot.announcements import format_ctfs
from bot.ctfs import CTF


def test_format_includes_weight_and_utc_plus_8_time_range() -> None:
    event = CTF(
        id=1,
        title="Spring CTF",
        start=datetime(2026, 9, 14, 12, tzinfo=timezone.utc),
        finish=datetime(2026, 9, 14, 16, tzinfo=timezone.utc),
        weight=42.5,
        url="https://example.test/ctf",
        format="Jeopardy",
        onsite=False,
    )

    message = format_ctfs([event])

    assert "Spring CTF" in message
    assert "Weight: **42.5**" in message
    assert "Mon Sep 14, 2026 20:00 - Tue Sep 15, 2026 00:00 (UTC+8)" in message


def test_format_handles_empty_schedule() -> None:
    assert format_ctfs([]) == "No online CTFs are listed for the coming week."