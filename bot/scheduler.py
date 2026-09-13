"""Backward-compatible facade for bot.services.scheduler."""

from .services.scheduler import WeeklyCTFAnnouncer

__all__ = ["WeeklyCTFAnnouncer"]