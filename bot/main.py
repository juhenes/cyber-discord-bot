import discord
from discord import app_commands

from .announcements import format_ctfs
from .config import Settings
from .ctfs import CTFtimeProvider
from .health import HealthCommand
from .scheduler import WeeklyCTFAnnouncer
from .storage import AnnouncementStore


class CTFBot(discord.Client):
    def __init__(self, settings: Settings) -> None:
        super().__init__(intents=discord.Intents.default())
        self.settings = settings
        self.commands = app_commands.CommandTree(self)
        self.provider = CTFtimeProvider(settings.ctftime_api_url)
        self.store = AnnouncementStore(settings.database_path)
        self.announcer = WeeklyCTFAnnouncer(
            self, self.provider, self.store, settings.announcement_channel_id,
            settings.announcement_weekday, settings.announcement_hour_utc,
        )

    async def setup_hook(self) -> None:
        self.commands.add_command(HealthCommand())

        @self.commands.command(name="ctfs", description="Show online CTFs in the coming week")
        async def ctfs(interaction: discord.Interaction) -> None:
            events = await self.provider.upcoming_online()
            await interaction.response.send_message(format_ctfs(events))

        await self.commands.sync()

    async def on_ready(self) -> None:
        self.announcer.start()
        print(f"Logged in as {self.user}")

    async def close(self) -> None:
        await self.announcer.stop()
        await super().close()


def run() -> None:
    settings = Settings.from_env()
    CTFBot(settings).run(settings.discord_token)


if __name__ == "__main__":
    run()