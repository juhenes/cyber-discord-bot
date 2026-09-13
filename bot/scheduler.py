import asyncio
from datetime import datetime, timezone

import discord

from .announcements import format_ctfs
from .ctfs import CTFtimeProvider
from .storage import AnnouncementStore


class WeeklyCTFAnnouncer:
    def __init__(self, bot: discord.Client, provider: CTFtimeProvider, store: AnnouncementStore,
                 channel_id: int, weekday: int, hour_utc: int) -> None:
        self.bot = bot
        self.provider = provider
        self.store = store
        self.channel_id = channel_id
        self.weekday = weekday
        self.hour_utc = hour_utc
        self.task: asyncio.Task[None] | None = None

    def start(self) -> None:
        if self.task is None:
            self.task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self.task:
            self.task.cancel()
            await asyncio.gather(self.task, return_exceptions=True)

    async def _run(self) -> None:
        while True:
            now = datetime.now(timezone.utc)
            if now.weekday() == self.weekday and now.hour == self.hour_utc:
                week = now.strftime("%G-W%V")
                if not self.store.was_sent(self.channel_id, week):
                    channel = self.bot.get_channel(self.channel_id)
                    if channel is None:
                        channel = await self.bot.fetch_channel(self.channel_id)
                    ctfs = await self.provider.upcoming_online(now)
                    await channel.send(format_ctfs(ctfs, now))
                    self.store.mark_sent(self.channel_id, week)
            await asyncio.sleep(60)