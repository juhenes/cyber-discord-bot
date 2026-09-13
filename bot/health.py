from datetime import datetime
import subprocess

import discord
from discord import app_commands


def _read(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as file:
            return file.read().strip()
    except OSError:
        return "Unavailable"


def get_temperature() -> str:
    try:
        value = int(_read("/host/sys/class/thermal/thermal_zone0/temp")) / 1000
    except ValueError:
        return "Unavailable"

    if value >= 80:
        status = "Very hot"
    elif value >= 70:
        status = "Warm"
    else:
        status = "Normal"

    return f"{value:.1f}°C - {status}"


def get_memory() -> str:
    values = {}
    for line in _read("/host/proc/meminfo").splitlines():
        name, _, value = line.partition(":")
        if name in {"MemTotal", "MemAvailable"}:
            values[name] = int(value.strip().split()[0])

    if "MemTotal" not in values or "MemAvailable" not in values:
        return "Unavailable"

    used = values["MemTotal"] - values["MemAvailable"]
    return f"{used / 1024 / 1024:.1f} GB / {values['MemTotal'] / 1024 / 1024:.1f} GB ({used / values['MemTotal']:.0%})"


def get_storage() -> str:
    try:
        result = subprocess.check_output(
            ["df", "-h", "/"], text=True, stderr=subprocess.DEVNULL
        ).splitlines()[1].split()
        return f"{result[2]} / {result[1]} ({result[4]})"
    except (OSError, IndexError, subprocess.CalledProcessError):
        return "Unavailable"


def get_uptime() -> str:
    try:
        seconds = float(_read("/host/proc/uptime").split()[0])
    except (ValueError, IndexError):
        return "Unavailable"

    days, remainder = divmod(int(seconds), 86400)
    hours, minutes = divmod(remainder, 3600)
    minutes //= 60
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes or not parts:
        parts.append(f"{minutes}m")
    return "up " + " ".join(parts)


class HealthCommand(app_commands.Command):
    def __init__(self) -> None:
        super().__init__(
            callback=self.health,
            name="health",
            description="Show the Raspberry Pi health status",
        )

    async def health(self, interaction: discord.Interaction) -> None:
        temperature = get_temperature()
        memory = get_memory()
        storage = get_storage()
        uptime = get_uptime()

        if "Very hot" in temperature:
            overall = "Attention needed"
            color = discord.Color.red()
        elif "Warm" in temperature:
            overall = "Check recommended"
            color = discord.Color.gold()
        else:
            overall = "Healthy"
            color = discord.Color.green()

        embed = discord.Embed(
            title="Raspberry Pi Health",
            description=f"**{overall}**",
            color=color,
        )
        embed.add_field(name="Temperature", value=temperature, inline=False)
        embed.add_field(name="Storage", value=storage, inline=True)
        embed.add_field(name="Memory", value=f"{memory}", inline=True)
        embed.add_field(name="Uptime", value=uptime, inline=False)
        embed.set_footer(text=f"Last checked - {datetime.now():%Y-%m-%d %H:%M:%S}")

        await interaction.response.send_message(embed=embed)