import logging

import discord
from discord import app_commands

from .commands import CertificationsCommand, CTFsCommand, HealthCommand, HelpCommand
from .config import Settings
from .services import CTFtimeProvider, WeeklyCTFAnnouncer
from .storage import AnnouncementStore, CertificationStore

logger = logging.getLogger("cyber_bot")


class CTFBot(discord.Client):
    """Discord bot client with CTF announcements, health checks, and cert management."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(intents=discord.Intents.default())
        self.settings = settings
        self.commands = app_commands.CommandTree(self)
        self.provider = CTFtimeProvider(settings.ctftime_api_url)
        self.store = AnnouncementStore(settings.database_path)
        self.certifications = CertificationStore(settings.database_path)
        self.announcer = WeeklyCTFAnnouncer(
            bot=self,
            provider=self.provider,
            store=self.store,
            channel_id=settings.announcement_channel_id,
            weekday=settings.announcement_weekday,
            hour_utc=settings.announcement_hour_utc,
        )

    async def setup_hook(self) -> None:
        self.commands.add_command(HelpCommand())
        self.commands.add_command(CTFsCommand(self.provider))
        self.commands.add_command(HealthCommand())
        self.commands.add_command(
            CertificationsCommand(
                self.certifications, self.settings.crud_admin_password_hash
            )
        )
        await self.commands.sync()
        logger.info("Application slash commands registered and synced.")

    async def on_ready(self) -> None:
        self.announcer.start()
        logger.info("Logged in as %s (ID: %s)", self.user, getattr(self.user, "id", "N/A"))

    async def close(self) -> None:
        await self.announcer.stop()
        await super().close()


def run() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    settings = Settings.from_env()
    CTFBot(settings).run(settings.discord_token)


if __name__ == "__main__":
    run()