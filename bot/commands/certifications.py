from typing import Any

import discord
from discord import app_commands

from ..storage import Certification, CertificationStore
from ..utils.security import verify_password


def format_certification(certification: Certification) -> str:
    """Format a certification entry for Discord markdown display."""
    availability = "Free" if certification.is_free else "Paid"
    format_type = "Hands-on" if certification.hands_on else "Theoretical"
    return (
        f"{certification.id}. {certification.provider}: [{certification.name}]({certification.url}) "
        f"({availability} & {format_type})"
    )


def split_message(message: str, limit: int = 2000) -> list[str]:
    """Split a Discord message without exceeding its content limit."""
    chunks: list[str] = []
    current = ""

    for line in message.splitlines(keepends=True):
        if len(line) > limit:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(line[index : index + limit] for index in range(0, len(line), limit))
        elif len(current) + len(line) > limit:
            chunks.append(current)
            current = line
        else:
            current += line

    if current:
        chunks.append(current)
    return chunks


# Backward compatibility alias
_format_certification = format_certification


class CertificationsCommand(app_commands.Command):
    """Slash command to view and manage cybersecurity certifications."""

    def __init__(self, store: CertificationStore, password_hash: str) -> None:
        self.store = store
        self.password_hash = password_hash
        super().__init__(
            callback=self.handle,
            name="certifications",
            description="Manage certifications",
        )

    @app_commands.choices(
        action=[
            app_commands.Choice(name="create", value="create"),
            app_commands.Choice(name="update", value="update"),
            app_commands.Choice(name="delete", value="delete"),
        ]
    )
    @app_commands.describe(
        action="Choose an operation, or leave empty",
        certification_id="Certification ID for update or delete",
        name="Certification name",
        provider="Issuing organization",
        url="Certification URL",
        free="Whether the certification is free",
        hands_on="Whether the certification includes practical exercises",
        password="Admin password, required for delete",
    )
    async def handle(
        self,
        interaction: discord.Interaction,
        action: str | None = None,
        certification_id: int | None = None,
        name: str | None = None,
        provider: str | None = None,
        url: str | None = None,
        free: bool | None = None,
        hands_on: bool | None = None,
        password: str | None = None,
    ) -> None:
        if action is None:
            await self._handle_list(interaction)
        elif action == "create":
            await self._handle_create(interaction, name, provider, url, free, hands_on)
        elif action == "update":
            await self._handle_update(
                interaction, certification_id, name, provider, url, free, hands_on
            )
        elif action == "delete":
            await self._handle_delete(interaction, certification_id, password)

    async def _handle_list(self, interaction: discord.Interaction) -> None:
        certifications = self.store.all()
        if not certifications:
            await interaction.response.send_message("No certifications have been added.")
            return

        message = "\n".join(format_certification(cert) for cert in certifications)
        chunks = split_message(message)
        await interaction.response.send_message(chunks[0])
        for chunk in chunks[1:]:
            await interaction.followup.send(chunk)

    async def _handle_create(
        self,
        interaction: discord.Interaction,
        name: str | None,
        provider: str | None,
        url: str | None,
        free: bool | None,
        hands_on: bool | None,
    ) -> None:
        if not name or not provider or not url:
            await interaction.response.send_message(
                "Create requires name, provider, and url.", ephemeral=True
            )
            return

        certification_id = self.store.add(
            name=name,
            provider=provider,
            url=url,
            is_free=True if free is None else free,
            hands_on=False if hands_on is None else hands_on,
        )
        await interaction.response.send_message(
            f"Created certification #{certification_id}.", ephemeral=True
        )

    async def _handle_update(
        self,
        interaction: discord.Interaction,
        certification_id: int | None,
        name: str | None,
        provider: str | None,
        url: str | None,
        free: bool | None,
        hands_on: bool | None,
    ) -> None:
        if certification_id is None:
            await interaction.response.send_message(
                "Update requires a certification ID.", ephemeral=True
            )
            return

        updates: dict[str, Any] = {}
        if name is not None:
            updates["name"] = name
        if provider is not None:
            updates["provider"] = provider
        if url is not None:
            updates["url"] = url
        if free is not None:
            updates["is_free"] = free
        if hands_on is not None:
            updates["hands_on"] = hands_on

        if not updates:
            await interaction.response.send_message(
                "Update requires at least one field.", ephemeral=True
            )
            return

        if not self.store.edit(certification_id, **updates):
            await interaction.response.send_message(
                "Certification not found.", ephemeral=True
            )
            return

        await interaction.response.send_message(
            f"Updated certification #{certification_id}.", ephemeral=True
        )

    async def _handle_delete(
        self,
        interaction: discord.Interaction,
        certification_id: int | None,
        password: str | None,
    ) -> None:
        if certification_id is None or password is None:
            await interaction.response.send_message(
                "Delete requires a certification ID and password.", ephemeral=True
            )
            return

        if not verify_password(password, self.password_hash):
            await interaction.response.send_message(
                "Invalid admin password.", ephemeral=True
            )
            return

        if not self.store.remove(certification_id):
            await interaction.response.send_message(
                "Certification not found.", ephemeral=True
            )
            return

        await interaction.response.send_message(
            f"Deleted certification #{certification_id}.", ephemeral=True
        )
