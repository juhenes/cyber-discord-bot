"""Backward-compatible facade for bot.commands.certifications."""

from .commands.certifications import (
    CertificationsCommand,
    _format_certification,
    format_certification,
)

__all__ = [
    "CertificationsCommand",
    "format_certification",
    "_format_certification",
]