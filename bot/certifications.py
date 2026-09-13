import discord
from discord import app_commands

from .security import verify_password
from .storage import CertificationStore, FreeCertification


def _format_certification(certification: FreeCertification) -> str:
    availability = "Free" if certification.is_free else "Paid"
    format_type = "Hands-on" if certification.hands_on else "Theoretical"
    return (
        f"{certification.id}. {certification.provider}: [{certification.name}]({certification.url}) "
        f"({availability} & {format_type})"
    )


class CertificationsCommand(app_commands.Command):
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
            await self._list(interaction)
        elif action == "create":
            await self._create(interaction, name, provider, url, free, hands_on)
        elif action == "update":
            await self._update(
                interaction, certification_id, name, provider, url, free, hands_on
            )
        elif action == "delete":
            await self._delete(interaction, certification_id, password)

    async def _list(self, interaction: discord.Interaction) -> None:
        message = "\n".join(
            _format_certification(certification) for certification in self.store.all()
        )
        await interaction.response.send_message(
            message or "No certifications have been added."
        )

    async def _create(
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
            name.strip(),
            provider.strip(),
            url.strip(),
            True if free is None else free,
            False if hands_on is None else hands_on,
        )
        await interaction.response.send_message(
            f"Created certification #{certification_id}.", ephemeral=True
        )

    async def _update(
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
        values = {
            key: value.strip() if isinstance(value, str) else value
            for key, value in {
                "name": name,
                "provider": provider,
                "url": url,
                "is_free": free,
                "hands_on": hands_on,
            }.items()
            if value is not None
        }
        if not values:
            await interaction.response.send_message(
                "Update requires at least one field.", ephemeral=True
            )
            return
        if not self.store.edit(certification_id, **values):
            await interaction.response.send_message(
                "Certification not found.", ephemeral=True
            )
            return
        await interaction.response.send_message(
            f"Updated certification #{certification_id}.", ephemeral=True
        )

    async def _delete(
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