import discord
from discord import app_commands

from ..services.announcements import format_ctfs
from ..services.ctfs import CTFtimeProvider


class CTFsCommand(app_commands.Command):
    """Slash command to show online CTFs in the coming week."""

    def __init__(self, provider: CTFtimeProvider) -> None:
        self.provider = provider
        super().__init__(
            callback=self.handle,
            name="ctfs",
            description="Show online CTFs in the coming week",
        )

    async def handle(self, interaction: discord.Interaction) -> None:
        events = await self.provider.upcoming_online()
        await interaction.response.send_message(format_ctfs(events))
