import discord
from discord import app_commands


class HelpCommand(app_commands.Command):
    """Slash command to display available bot commands and their usage."""

    def __init__(self) -> None:
        super().__init__(
            callback=self.help,
            name="help",
            description="Show available bot commands",
        )

    async def help(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title="Cybersecurity Bot Help",
            description="Available commands and usage:",
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="/ctfs",
            value="Show online CTFs happening in the coming week.",
            inline=False,
        )
        embed.add_field(
            name="/health",
            value="Show Raspberry Pi temperature, memory, storage, and uptime.",
            inline=False,
        )
        embed.add_field(
            name="/certifications",
            value=(
                "Leave `action` empty to show certifications. "
                "Use `create`, `update`, or `delete` for management."
            ),
            inline=False,
        )
        await interaction.response.send_message(embed=embed)
