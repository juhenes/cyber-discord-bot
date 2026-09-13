from datetime import datetime, timedelta, timezone

from .ctfs import CTF

UTC_PLUS_8 = timezone(timedelta(hours=8))


def format_ctfs(ctfs: list[CTF], now: datetime | None = None) -> str:
    if not ctfs:
        return "No online CTFs are listed for the coming week."

    lines = ["**Upcoming online CTFs this week**"]
    for ctf in ctfs:
        start = ctf.start.astimezone(UTC_PLUS_8)
        finish = ctf.finish.astimezone(UTC_PLUS_8)
        time_range = (
            f"{start.strftime('%a %b %-d, %Y %H:%M')} - "
            f"{finish.strftime('%a %b %-d, %Y %H:%M')} (UTC+8)"
        )
        weight = f"{ctf.weight:g}" if ctf.weight is not None else "not listed"
        lines.append(
            f"- **[{ctf.title}]({ctf.url})**\n"
            f"  {time_range} | {ctf.duration} | "
            f"Weight: **{weight}** | Format: {ctf.format}"
        )
    return "\n".join(lines)