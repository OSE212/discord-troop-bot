from __future__ import annotations

import discord

from bot.database.base import Database
from bot.database.models.player import Player, TroopType
from bot.database.repositories.player_repository import PlayerRepository
from bot.discord.interactions.registration_flow import parse_int, parse_level, summarize_player
from bot.discord.views.components import TROOP_TYPE_LABELS
from bot.services.player_service import PlayerService, ValidationError


class UpdateFieldSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Game Player ID / Name", value="identity"),
            discord.SelectOption(label="March Limit", value="march_limit"),
        ] + [
            discord.SelectOption(label=f"{label} (Helios / FC level / quantity)", value=t.value)
            for t, label in TROOP_TYPE_LABELS.items()
        ]
        super().__init__(placeholder="What do you want to update?", options=options)

    async def callback(self, interaction: discord.Interaction):
        view: UpdateFieldView = self.view  # type: ignore[assignment]
        await view.on_field_chosen(interaction, self.values[0])


class UpdateFieldView(discord.ui.View):
    def __init__(self, db: Database, player: Player | int, *, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.db = db
        self.player_id = player.id if hasattr(player, "id") else int(player)
        self.add_item(UpdateFieldSelect())

    async def on_field_chosen(self, interaction: discord.Interaction, field: str):
        if field == "identity":
            await interaction.response.send_modal(IdentityUpdateModal(self.db, self.player_id))
        elif field == "march_limit":
            await interaction.response.send_modal(MarchLimitUpdateModal(self.db, self.player_id))
        else:
            troop_type = TroopType(field)
            await interaction.response.send_modal(
                TroopTypeUpdateModal(self.db, self.player_id, troop_type)
            )


class IdentityUpdateModal(discord.ui.Modal, title="Update Identity"):
    game_player_id = discord.ui.TextInput(label="Game Player ID", required=False, max_length=64)
    name = discord.ui.TextInput(label="Player Name", required=False, max_length=128)

    def __init__(self, db: Database, player_id: int):
        super().__init__()
        self.db = db
        self.player_id = player_id

    async def on_submit(self, interaction: discord.Interaction):
        with self.db.session() as session:
            repository = PlayerRepository(session)
            service = PlayerService(repository)
            player = repository.get_by_id(self.player_id)
            try:
                service.update_identity(
                    player,
                    game_player_id=str(self.game_player_id.value).strip() or None,
                    name=str(self.name.value).strip() or None,
                )
                summary = summarize_player(player)
            except ValidationError as exc:
                await interaction.response.send_message(str(exc), ephemeral=True)
                return
        await interaction.response.send_message(
            f"Updated!\n{summary}", ephemeral=True
        )


class MarchLimitUpdateModal(discord.ui.Modal, title="Update March Limit"):
    march_limit = discord.ui.TextInput(label="New March Limit", required=True, max_length=16)

    def __init__(self, db: Database, player_id: int):
        super().__init__()
        self.db = db
        self.player_id = player_id

    async def on_submit(self, interaction: discord.Interaction):
        try:
            value = parse_int(str(self.march_limit.value), "March limit")
        except ValidationError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        with self.db.session() as session:
            repository = PlayerRepository(session)
            service = PlayerService(repository)
            player = repository.get_by_id(self.player_id)
            try:
                service.update_identity(player, march_limit=value)
                summary = summarize_player(player)
            except ValidationError as exc:
                await interaction.response.send_message(str(exc), ephemeral=True)
                return
        await interaction.response.send_message(f"Updated!\n{summary}", ephemeral=True)


class TroopTypeUpdateModal(discord.ui.Modal):
    """One modal covering Helios (yes/no), FC level, and (if Helios =
    yes) the Helios quantity for a single troop type. Typing "yes"/"no"
    in a text field is simpler and more reliable across Discord clients
    than chaining an extra select step for a single boolean.
    """

    helios = discord.ui.TextInput(
        label="Helios? (yes/no)", required=True, max_length=3
    )
    level = discord.ui.TextInput(label="FC / Level", required=True, max_length=8)
    helios_quantity = discord.ui.TextInput(
        label="Helios Quantity (leave blank if Helios=no)",
        required=False,
        max_length=16,
    )

    def __init__(self, db: Database, player_id: int, troop_type: TroopType):
        super().__init__(title=f"Update {TROOP_TYPE_LABELS[troop_type]}")
        self.db = db
        self.player_id = player_id
        self.troop_type = troop_type

    async def on_submit(self, interaction: discord.Interaction):
        helios_raw = str(self.helios.value).strip().lower()
        if helios_raw not in ("yes", "no", "y", "n"):
            await interaction.response.send_message(
                'Helios must be "yes" or "no".', ephemeral=True
            )
            return
        helios = helios_raw in ("yes", "y")

        try:
            level = parse_level(str(self.level.value), "FC/Level")
        except ValidationError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return

        quantity = None
        if helios:
            raw_qty = str(self.helios_quantity.value).strip()
            if not raw_qty:
                await interaction.response.send_message(
                    "Helios quantity is required when Helios = yes.", ephemeral=True
                )
                return
            try:
                quantity = parse_int(raw_qty, "Helios quantity")
            except ValidationError as exc:
                await interaction.response.send_message(str(exc), ephemeral=True)
                return

        with self.db.session() as session:
            repository = PlayerRepository(session)
            service = PlayerService(repository)
            player = repository.get_by_id(self.player_id)
            service.update_troop_type(
                player,
                self.troop_type,
                helios=helios,
                level=level,
                helios_quantity=quantity,
            )
            summary = summarize_player(player)

        await interaction.response.send_message(f"Updated!\n{summary}", ephemeral=True)
