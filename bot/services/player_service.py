"""Business logic for registration/update/admin flows (spec sections
5, 6, 8, 24). Keeps validation rules out of the Discord layer so they
can be unit tested without spinning up a bot.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from bot.database.models.player import Player, TroopType
from bot.database.repositories.player_repository import PlayerRepository


class ValidationError(ValueError):
    """Raised for any registration/update input that fails spec
    section 24's required validation rules."""


@dataclass
class TroopTypeInput:
    helios: bool
    level: Optional[int] = None
    helios_quantity: Optional[int] = None


@dataclass
class RegistrationDraft:
    """Accumulates answers from the guided /register-troops flow
    before anything is written to the database. Registration only
    touches the DB once `is_ready()` is true (spec: "Registration
    must be separate from calculation" + guided-form UX).
    """

    discord_user_id: str
    game_player_id: Optional[str] = None
    name: Optional[str] = None
    march_limit: Optional[int] = None
    guild_id: Optional[str] = None
    troop_types: dict[TroopType, TroopTypeInput] = field(
        default_factory=lambda: {t: TroopTypeInput(helios=False) for t in TroopType}
    )


    def is_ready(self) -> bool:
        if not self.game_player_id or not self.name or not self.march_limit:
            return False
        for troop_type in TroopType:
            data = self.troop_types[troop_type]
            if data.level is None:
                return False
            if data.helios and data.helios_quantity is None:
                return False
        return True


def _validate_identity(game_player_id: str, name: str) -> None:
    if not game_player_id or not game_player_id.strip():
        raise ValidationError("Game Player ID is required.")
    if not name or not name.strip():
        raise ValidationError("Player name is required.")


def _validate_march_limit(march_limit: int) -> None:
    if march_limit is None or march_limit <= 0:
        raise ValidationError("March limit is required and must be positive.")


def _validate_level(level: Optional[int]) -> None:
    if level is None or level <= 0:
        raise ValidationError("FC/troop level is required for every troop type.")


def _validate_helios_quantity(helios: bool, quantity: Optional[int]) -> None:
    if helios and (quantity is None or quantity < 0):
        raise ValidationError(
            "Helios troop quantity is required (and must be >= 0) when "
            "Helios = YES."
        )


class PlayerService:
    def __init__(self, repository: PlayerRepository):
        self.repository = repository

    # -- registration -------------------------------------------------

    def register_player(self, draft: RegistrationDraft) -> Player:
        _validate_identity(draft.game_player_id, draft.name)
        _validate_march_limit(draft.march_limit)
        for troop_type in TroopType:
            data = draft.troop_types[troop_type]
            _validate_level(data.level)
            _validate_helios_quantity(data.helios, data.helios_quantity)

        existing = self.repository.get_by_discord_id(draft.discord_user_id)
        if existing is not None:
            raise ValidationError(
                "You are already registered. Use /update-troops instead."
            )

        troop_data = {
            t: {
                "helios": draft.troop_types[t].helios,
                "level": draft.troop_types[t].level,
                "helios_quantity": draft.troop_types[t].helios_quantity,
            }
            for t in TroopType
        }
        return self.repository.create_player(
            discord_user_id=draft.discord_user_id,
            game_player_id=draft.game_player_id,
            name=draft.name,
            march_limit=draft.march_limit,
            troop_data=troop_data,
            guild_id=draft.guild_id,
        )


    # -- updates ---------------------------------------------------------

    def update_identity(
        self,
        player: Player,
        *,
        game_player_id: Optional[str] = None,
        name: Optional[str] = None,
        march_limit: Optional[int] = None,
    ) -> Player:
        if game_player_id is not None or name is not None:
            _validate_identity(
                game_player_id or player.game_player_id, name or player.name
            )
        if march_limit is not None:
            _validate_march_limit(march_limit)
        return self.repository.update_player_fields(
            player,
            game_player_id=game_player_id,
            name=name,
            march_limit=march_limit,
        )

    def update_troop_type(
        self,
        player: Player,
        troop_type: TroopType,
        *,
        helios: Optional[bool] = None,
        level: Optional[int] = None,
        helios_quantity: Optional[int] = None,
    ) -> Player:
        if level is not None:
            _validate_level(level)

        existing_profile = player.profile_for(troop_type)
        effective_helios = (
            helios if helios is not None else (existing_profile.helios if existing_profile else False)
        )
        effective_quantity = (
            helios_quantity
            if helios_quantity is not None
            else (existing_profile.helios_quantity if existing_profile else None)
        )
        # Spec section 6: switching NO -> YES requires a quantity
        # before the record is complete again. We don't hard-fail the
        # update itself (the player may set Helios first, quantity in
        # a follow-up step of the same guided flow) but the record
        # will report incomplete via Player.is_complete() until it's
        # supplied.
        if helios is False:
            effective_quantity = None

        self.repository.update_troop_profile(
            player,
            troop_type,
            helios=helios,
            level=level,
            helios_quantity=helios_quantity if helios is not False else None,
        )
        _ = effective_helios, effective_quantity  # documented intent above
        return player

    # -- admin ----------------------------------------------------------

    def get_player(self, discord_user_id: str) -> Optional[Player]:
        return self.repository.get_by_discord_id(discord_user_id)

    def list_players(self) -> list[Player]:
        return self.repository.list_all()

    def remove_player(self, player: Player) -> None:
        self.repository.delete_player(player)

    def reset_player(self, player: Player) -> None:
        self.repository.reset_player(player)
