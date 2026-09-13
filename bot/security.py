"""Backward-compatible facade for bot.utils.security module."""

from .utils.security import hash_password, verify_password

__all__ = ["hash_password", "verify_password"]