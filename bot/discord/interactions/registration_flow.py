"""Guided /register-troops and /update-troops flows (spec section 5).

Registration never touches the database until every required field
has been collected -- state is accumulated in an in-memory
RegistrationDraft as the player moves through modals/selects, and
PlayerService.register_player() is only called on the final step.
"""
from __future__ import annotations

import discord

import re
from bot.database.base import Database
from bot.database.models.player import TroopType
from bot.database.repositories.player_repository import PlayerRepository
from bot.discord.views.components import TROOP_TYPE_LABELS, HeliosSelectView
from bot.services.player_service import (
    PlayerService,
    RegistrationDraft,
    TroopTypeInput,
    ValidationError,
)


def parse_int(raw: str, field_name: str) -> int:
    s = str(raw).replace(",", "").replace(" ", "").strip()
    if s.lower().endswith("k"):
        try:
            return int(float(s[:-1]) * 1_000)
        except (TypeError, ValueError):
            pass
    elif s.lower().endswith("m"):
        try:
            return int(float(s[:-1]) * 1_000_000)
        except (TypeError, ValueError):
            pass

    if any(k in field_name.lower() for k in ("level", "fc")):
        s = re.sub(r"^(?:fc|level|lvl|t)[\s\-_]*", "", s, flags=re.IGNORECASE).strip()

    try:
        value = int(s)
    except (TypeError, ValueError):
        raise ValidationError(f"{field_name} must be a whole number.")
    return value


def parse_level(raw: str, field_name: str = "FC/Level") -> int:
    s = str(raw).strip()
    s_clean = re.sub(r"^(?:fc|level|lvl|t)[\s\-_]*", "", s, flags=re.IGNORECASE).strip()
    s_clean = s_clean.replace(",", "").replace(" ", "")
    try:
        value = int(s_clean)
        if value <= 0:
            raise ValueError()
        return value
    except (TypeError, ValueError):
        raise ValidationError(f"{field_name} must be a valid number (e.g. 7 or FC7).")


# Backwards-compatible private alias used elsewhere in this module.
_parse_int = parse_int


class IdentityModal(discord.ui.Modal, title="Register Troops - Step 1/4"):
    game_player_id = discord.ui.TextInput(
        label="Game Player ID", required=True, max_length=64
    )
    name = discord.ui.TextInput(label="Player Name", required=True, max_length=128)
    march_limit = discord.ui.TextInput(
        label="March Limit (max troops per march)", required=True, max_length=16
    )

    def __init__(
        self,
        db: Database,
        *,
        on_done=None,
        target_discord_id: str | None = None,
        default_name: str | None = None,
    ):
        super().__init__()
        self.db = db
        self.on_done = on_done
        self.target_discord_id = target_discord_id
        if default_name:
            self.name.default = default_name

    async def on_submit(self, interaction: discord.Interaction):
        try:
            march_limit = _parse_int(str(self.march_limit.value), "March limit")
            if march_limit <= 0:
                raise ValidationError("March limit must be positive.")
        except ValidationError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return

        target_id = self.target_discord_id or str(interaction.user.id)
        game_id = str(self.game_player_id.value).strip()
        if target_id == "manual":
            target_id = f"manual_{game_id}"[:32]

        with self.db.session() as session:
            existing = PlayerRepository(session).get_by_discord_id(target_id)
            if existing is not None:
                await interaction.response.send_message(
                    f"A player with ID '{target_id}' is already registered.",
                    ephemeral=True,
                )
                return

        draft = RegistrationDraft(discord_user_id=target_id)
        draft.game_player_id = game_id
        draft.name = str(self.name.value).strip()
        draft.march_limit = march_limit

        view = HeliosSelectView(
            on_continue=lambda i, chosen: self._on_helios_chosen(i, draft, chosen)
        )
        await interaction.response.send_message(
            "Step 2/4 - Which troop types have Helios?", view=view, ephemeral=True
        )

    async def _on_helios_chosen(
        self, interaction: discord.Interaction, draft: RegistrationDraft, chosen
    ):
        for troop_type in TroopType:
            draft.troop_types[troop_type].helios = troop_type in chosen
        modal = LevelsModal(self.db, draft=draft, on_done=self.on_done)
        await interaction.response.send_modal(modal)


class LevelsModal(discord.ui.Modal, title="Register Troops - Step 3/4"):
    infantry_level = discord.ui.TextInput(
        label="Infantry FC/Level", required=True, max_length=8
    )
    lancers_level = discord.ui.TextInput(
        label="Lancers FC/Level", required=True, max_length=8
    )
    marksman_level = discord.ui.TextInput(
        label="Marksman FC/Level", required=True, max_length=8
    )

    def __init__(self, db: Database, *, draft: RegistrationDraft, on_done):
        super().__init__()
        self.db = db
        self.draft = draft
        self.on_done = on_done

    async def on_submit(self, interaction: discord.Interaction):
        try:
            self.draft.troop_types[TroopType.INFANTRY].level = parse_level(
                str(self.infantry_level.value), "Infantry FC/Level"
            )
            self.draft.troop_types[TroopType.LANCERS].level = parse_level(
                str(self.lancers_level.value), "Lancers FC/Level"
            )
            self.draft.troop_types[TroopType.MARKSMAN].level = parse_level(
                str(self.marksman_level.value), "Marksman FC/Level"
            )
        except ValidationError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return

        helios_types = [
            t for t in TroopType if self.draft.troop_types[t].helios
        ]
        if not helios_types:
            await _finalize_registration(interaction, self.db, self.draft, self.on_done)
            return

        modal = HeliosQuantityModal(
            self.db, draft=self.draft, troop_types=helios_types, on_done=self.on_done
        )
        await interaction.response.send_modal(modal)


class HeliosQuantityModal(discord.ui.Modal, title="Register Troops - Step 4/4"):
    """Fields are built dynamically: only troop types marked Helios
    need a quantity (spec section 5, Step 5)."""

    def __init__(
        self,
        db: Database,
        *,
        draft: RegistrationDraft,
        troop_types: list[TroopType],
        on_done,
    ):
        super().__init__()
        self.db = db
        self.draft = draft
        self.on_done = on_done
        self.troop_types = troop_types
        self.inputs: dict[TroopType, discord.ui.TextInput] = {}
        for troop_type in troop_types:
            text_input = discord.ui.TextInput(
                label=f"{TROOP_TYPE_LABELS[troop_type]} Helios Quantity",
                required=True,
                max_length=16,
            )
            self.inputs[troop_type] = text_input
            self.add_item(text_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            for troop_type, text_input in self.inputs.items():
                qty = _parse_int(
                    str(text_input.value),
                    f"{TROOP_TYPE_LABELS[troop_type]} Helios quantity",
                )
                if qty < 0:
                    raise ValidationError("Helios quantity cannot be negative.")
                self.draft.troop_types[troop_type].helios_quantity = qty
        except ValidationError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return

        await _finalize_registration(interaction, self.db, self.draft, self.on_done)


async def _finalize_registration(
    interaction: discord.Interaction, db: Database, draft: RegistrationDraft, on_done
):
    try:
        draft.guild_id = str(interaction.guild_id) if interaction.guild_id else None
        with db.session() as session:
            repository = PlayerRepository(session)
            service = PlayerService(repository)
            player = service.register_player(draft)
            summary = _summarize(player)

    except ValidationError as exc:
        await interaction.response.send_message(str(exc), ephemeral=True)
        return

    await interaction.response.send_message(
        f"Registration complete!\n{summary}", ephemeral=True
    )
    if on_done:
        await on_done(interaction)


def summarize_player(player) -> str:
    return _summarize(player)


def _summarize(player) -> str:
    lines = [
        f"Name: {player.name}",
        f"Game Player ID: {player.game_player_id}",
        f"March Limit: {player.march_limit:,}",
    ]
    for troop_type in TroopType:
        profile = player.profile_for(troop_type)
        helios = "Helios" if profile.helios else "No Helios"
        qty = (
            f", Qty: {profile.helios_quantity:,}"
            if profile.helios and profile.helios_quantity is not None
            else ""
        )
        lines.append(
            f"{TROOP_TYPE_LABELS[troop_type]}: {helios}, FC{profile.level}{qty}"
        )
    return "\n".join(lines)
