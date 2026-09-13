import asyncio
from datetime import datetime, timezone
import logging

import discord

from ..storage import AnnouncementStore
from .announcements import format_ctfs
from .ctfs import CTFtimeProvider

logger = logging.getLogger(__name__)


class WeeklyCTFAnnouncer:
    """Schedules and publishes weekly CTF announcements to a Discord channel."""

    def __init__(
        self,
        bot: discord.Client,
        provider: CTFtimeProvider,
        store: AnnouncementStore,
        channel_id: int,
        weekday: int,
        hour_utc: int,
    ) -> None:
        self.bot = bot
        self.provider = provider
        self.store = store
        self.channel_id = channel_id
        self.weekday = weekday
        self.hour_utc = hour_utc
        self.task: asyncio.Task[None] | None = None

    def start(self) -> None:
        """Start the background announcement task if not already running."""
        if self.task is None or self.task.done():
            self.task = asyncio.create_task(self._run())
            logger.info("Weekly CTF announcer task started.")

    async def stop(self) -> None:
        """Cancel the background announcement task."""
        if self.task and not self.task.done():
            self.task.cancel()
            await asyncio.gather(self.task, return_exceptions=True)
            logger.info("Weekly CTF announcer task stopped.")

    async def _check_and_announce(self, now: datetime) -> None:
        """Check if announcement is due and send if not already sent this week."""
        if now.weekday() != self.weekday or now.hour != self.hour_utc:
            return

        week = now.strftime("%G-W%V")
        if self.store.was_sent(self.channel_id, week):
            return

        channel = self.bot.get_channel(self.channel_id)
        if channel is None:
            channel = await self.bot.fetch_channel(self.channel_id)

        if not isinstance(channel, discord.abc.Messageable):
            logger.error("Channel %s is not messageable.", self.channel_id)
            return

        logger.info("Fetching upcoming CTFs for week %s announcement...", week)
        ctfs = await self.provider.upcoming_online(now)
        await channel.send(format_ctfs(ctfs, now))
        self.store.mark_sent(self.channel_id, week)
        logger.info("Sent weekly CTF announcement for %s to channel %s.", week, self.channel_id)

    async def _run(self) -> None:
        while True:
            try:
                now = datetime.now(timezone.utc)
                await self._check_and_announce(now)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.exception("Unexpected error in CTF announcer loop: %s", exc)

            await asyncio.sleep(60)
