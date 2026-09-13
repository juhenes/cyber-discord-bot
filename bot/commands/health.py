from datetime import datetime

import discord
from discord import app_commands

from ..services.system import (
    get_memory,
    get_power,
    get_storage,
    get_temperature,
    get_uptime,
)


class HealthCommand(app_commands.Command):
    """Slash command to display Raspberry Pi system health metrics."""

    def __init__(self) -> None:
        super().__init__(
            callback=self.health,
            name="health",
            description="Show the Raspberry Pi health status",
        )

    async def health(self, interaction: discord.Interaction) -> None:
        temperature = get_temperature()
        power = get_power()
        memory = get_memory()
        storage = get_storage()
        uptime = get_uptime()

        has_critical_power = any(w in power for w in ("Under-voltage detected", "Currently throttled"))
        if "Very hot" in temperature or has_critical_power:
            overall = "Attention needed"
            color = discord.Color.red()
        elif "Warm" in temperature or (power not in ("Normal", "Unavailable")):
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
        embed.add_field(name="Power", value=power, inline=True)
        embed.add_field(name="Memory", value=memory, inline=True)
        embed.add_field(name="Storage", value=storage, inline=True)
        embed.add_field(name="Uptime", value=uptime, inline=False)
        embed.set_footer(text=f"Last checked - {datetime.now():%Y-%m-%d %H:%M:%S}")

        await interaction.response.send_message(embed=embed)
