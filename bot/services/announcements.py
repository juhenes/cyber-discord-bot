from datetime import datetime, timedelta, timezone

from .ctfs import CTF

UTC_PLUS_8 = timezone(timedelta(hours=8))


def _format_datetime(dt: datetime) -> str:
    """Format datetime as 'Mon Sep 14, 2026 20:00' portably across platforms."""
    return f"{dt.strftime('%a %b')} {dt.day}, {dt.strftime('%Y %H:%M')}"


def format_ctfs(ctfs: list[CTF], now: datetime | None = None) -> str:
    """Format a list of CTF events into a Discord markdown announcement."""
    if not ctfs:
        return "No online CTFs are listed for the coming week."

    lines = ["**Upcoming online CTFs this week**"]
    for ctf in ctfs:
        start = ctf.start.astimezone(UTC_PLUS_8)
        finish = ctf.finish.astimezone(UTC_PLUS_8)
        time_range = f"{_format_datetime(start)} - {_format_datetime(finish)} (UTC+8)"
        weight = f"{ctf.weight:g}" if ctf.weight is not None else "not listed"
        lines.append(
            f"- **[{ctf.title}]({ctf.url})**\n"
            f"  {time_range} | {ctf.duration} | "
            f"Weight: **{weight}** | Format: {ctf.format}"
        )
    return "\n".join(lines)
