from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.database.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TroopType(str, enum.Enum):
    """The three troop types. Str-enum so values serialize cleanly."""

    INFANTRY = "infantry"
    LANCERS = "lancers"
    MARKSMAN = "marksman"


class Player(Base):
    """A registered player.

    Note: `discord_user_id` is the internal identity (captured
    automatically from the interaction) and is distinct from
    `game_player_id`, which the player types in manually. See spec
    section 5, Step 1.
    """

    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    discord_user_id: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, index=True
    )
    game_player_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    march_limit: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )

    troop_profiles: Mapped[list["TroopProfile"]] = relationship(
        "TroopProfile",
        back_populates="player",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    heroes: Mapped[list["PlayerHero"]] = relationship(
        "PlayerHero",
        back_populates="player",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def profile_for(self, troop_type: TroopType) -> Optional["TroopProfile"]:
        for profile in self.troop_profiles:
            if profile.troop_type == troop_type:
                return profile
        return None

    def hero_for(self, hero_name: str) -> Optional["PlayerHero"]:
        norm = hero_name.lower().strip()
        for h in self.heroes:
            if h.hero_name.lower() == norm:
                return h
        return None

    def is_complete(self) -> bool:
        """A player record is only usable by the optimizer once every
        troop type has a level set and Helios types have a quantity.
        """
        if not self.game_player_id or not self.name or not self.march_limit:
            return False
        profiles = {p.troop_type: p for p in self.troop_profiles}
        for troop_type in TroopType:
            profile = profiles.get(troop_type)
            if profile is None or profile.level is None:
                return False
            if profile.helios and profile.helios_quantity is None:
                return False
        return True

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<Player {self.name} ({self.discord_user_id})>"


class TroopProfile(Base):
    """Per-troop-type data for a player: Helios status + FC level.

    `helios_quantity` is required/finite when helios=True and is
    ignored (should be NULL) when helios=False -- non-Helios
    availability is treated as abundant by application logic rather
    than stored as a number (spec sections 3 and 7).
    """

    __tablename__ = "troop_profiles"
    __table_args__ = (
        UniqueConstraint("player_id", "troop_type", name="uq_player_troop_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"), nullable=False
    )
    troop_type: Mapped[TroopType] = mapped_column(
        Enum(
            TroopType,
            native_enum=False,
            length=16,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    helios: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    helios_quantity: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )

    player: Mapped["Player"] = relationship(
        "Player", back_populates="troop_profiles"
    )

    def available_quantity(self) -> Optional[int]:
        """Return the finite quantity available, or None for
        "sufficiently abundant" non-Helios troops. Callers must treat
        None as unlimited (bounded only by the player's march limit).
        """
        if self.helios:
            return self.helios_quantity
        return None

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<TroopProfile {self.troop_type} helios={self.helios} "
            f"level={self.level} qty={self.helios_quantity}>"
        )


class PlayerHero(Base):
    """Stores key hero progression (Stars 1-5★ and Expedition Skill 1 Level 1-5)
    for a player. Used to optimize the First 4 Joiners in Rallies and Garrisons.
    """

    __tablename__ = "player_heroes"
    __table_args__ = (
        UniqueConstraint("player_id", "hero_name", name="uq_player_hero"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"), nullable=False
    )
    hero_name: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    stars: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    skill_level: Mapped[int] = mapped_column(Integer, default=5, nullable=False)

    player: Mapped["Player"] = relationship("Player", back_populates="heroes")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PlayerHero {self.hero_name} {self.stars}★ skill={self.skill_level}>"

