"""Backward-compatible facade for bot.services.system and bot.commands.health."""

from .commands.health import HealthCommand
from .services.system import (
    get_memory,
    get_storage,
    get_temperature,
    get_uptime,
    read_proc_file,
)

# Backward-compatibility alias
_read = read_proc_file

__all__ = [
    "HealthCommand",
    "get_temperature",
    "get_memory",
    "get_storage",
    "get_uptime",
    "read_proc_file",
    "_read",
]