from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from bot.database.models.player import Player, PlayerHero, TroopProfile, TroopType


class PlayerRepository:
    """All persistence access for players goes through this class.

    Keeping this as the single point of contact with SQLAlchemy means
    the optimizer and Discord command layers never need to know
    whether the backing store is SQLite or PostgreSQL.
    """

    def __init__(self, session: Session):
        self.session = session

    # -- lookups ----------------------------------------------------

    def get_by_discord_id(
        self, discord_user_id: str, guild_id: Optional[str] = None
    ) -> Optional[Player]:
        stmt = select(Player).where(Player.discord_user_id == str(discord_user_id))
        if guild_id and guild_id != "*":
            stmt = stmt.where((Player.guild_id == str(guild_id)) | (Player.guild_id.is_(None)))
        return self.session.execute(stmt).scalars().first()

    def get_by_game_player_id(self, game_player_id: str, guild_id: Optional[str] = None) -> Optional[Player]:
        stmt = select(Player).where(Player.game_player_id == str(game_player_id))
        if guild_id and guild_id != "*":
            stmt = stmt.where((Player.guild_id == str(guild_id)) | (Player.guild_id.is_(None)))
        return self.session.execute(stmt).scalars().first()

    def get_by_id(self, player_id: int) -> Optional[Player]:
        return self.session.get(Player, player_id)

    def list_all(
        self, guild_id: Optional[str] = None, alliance_tag: Optional[str] = None
    ) -> list[Player]:
        stmt = select(Player).order_by(Player.name)
        if guild_id and guild_id != "*":
            stmt = stmt.where((Player.guild_id == str(guild_id)) | (Player.guild_id.is_(None)))
        if alliance_tag and alliance_tag != "*":
            tag_clean = alliance_tag.strip().upper().lstrip("[").rstrip("]")
            stmt = stmt.where(Player.alliance_tag.ilike(f"%{tag_clean}%"))
        return list(self.session.execute(stmt).scalars().all())

    def list_distinct_guild_ids(self) -> list[str]:
        stmt = select(Player.guild_id).where(Player.guild_id.isnot(None)).distinct()
        return [str(g) for g in self.session.execute(stmt).scalars().all() if g]

    def list_distinct_alliance_tags(self) -> list[str]:
        stmt = select(Player.alliance_tag).where(Player.alliance_tag.isnot(None)).distinct()
        return [str(t) for t in self.session.execute(stmt).scalars().all() if t]

    # -- writes -------------------------------------------------------

    def create_player(
        self,
        *,
        discord_user_id: str,
        game_player_id: str,
        name: str,
        march_limit: int,
        troop_data: dict[TroopType, dict],
        heroes_data: Optional[dict[str, dict]] = None,
        guild_id: Optional[str] = None,
        alliance_tag: Optional[str] = None,
    ) -> Player:
        """Create a brand new player with all three troop profiles and optional heroes."""
        tag_clean = alliance_tag.strip().upper() if alliance_tag else None
        if tag_clean and not tag_clean.startswith("["):
            tag_clean = f"[{tag_clean}]"

        player = Player(
            guild_id=str(guild_id) if guild_id else None,
            discord_user_id=str(discord_user_id),
            game_player_id=game_player_id,
            name=name,
            alliance_tag=tag_clean,
            march_limit=march_limit,
        )


        for troop_type in TroopType:
            data = troop_data[troop_type]
            player.troop_profiles.append(
                TroopProfile(
                    troop_type=troop_type,
                    helios=data["helios"],
                    level=data["level"],
                    helios_quantity=data.get("helios_quantity")
                    if data["helios"]
                    else None,
                )
            )
        if heroes_data:
            for h_name, h_info in heroes_data.items():
                player.heroes.append(
                    PlayerHero(
                        hero_name=h_name.lower().strip(),
                        stars=max(1, min(5, int(h_info.get("stars", 5)))),
                        skill_level=max(1, min(5, int(h_info.get("skill_level", 5)))),
                    )
                )
        self.session.add(player)
        self.session.flush()
        return player

    def upsert_hero(
        self,
        player: Player,
        hero_name: str,
        *,
        stars: int = 5,
        skill_level: int = 5,
    ) -> PlayerHero:
        norm = hero_name.lower().strip()
        existing = player.hero_for(norm)
        if existing is not None:
            existing.stars = max(1, min(5, int(stars)))
            existing.skill_level = max(1, min(5, int(skill_level)))
            hero = existing
        else:
            hero = PlayerHero(
                hero_name=norm,
                stars=max(1, min(5, int(stars))),
                skill_level=max(1, min(5, int(skill_level))),
            )
            player.heroes.append(hero)
        self.session.flush()
        return hero

    def update_player_fields(
        self,
        player: Player,
        *,
        game_player_id: Optional[str] = None,
        name: Optional[str] = None,
        march_limit: Optional[int] = None,
        alliance_tag: Optional[str] = None,
    ) -> Player:
        if game_player_id is not None:
            player.game_player_id = game_player_id
        if name is not None:
            player.name = name
        if march_limit is not None:
            player.march_limit = march_limit
        if alliance_tag is not None:
            tag_clean = alliance_tag.strip().upper() if alliance_tag else None
            if tag_clean and not tag_clean.startswith("["):
                tag_clean = f"[{tag_clean}]"
            player.alliance_tag = tag_clean
        self.session.flush()
        return player


    def update_troop_profile(
        self,
        player: Player,
        troop_type: TroopType,
        *,
        helios: Optional[bool] = None,
        level: Optional[int] = None,
        helios_quantity: Optional[int] = None,
    ) -> TroopProfile:
        profile = player.profile_for(troop_type)
        if profile is None:
            profile = TroopProfile(troop_type=troop_type, helios=False)
            player.troop_profiles.append(profile)

        if helios is not None:
            profile.helios = helios
            # Spec section 6: toggling Helios OFF invalidates the
            # stored quantity; toggling ON requires a fresh quantity
            # before the record is considered complete again.
            if helios is False:
                profile.helios_quantity = None

        if level is not None:
            profile.level = level

        if helios_quantity is not None:
            profile.helios_quantity = helios_quantity

        self.session.flush()
        return profile

    def delete_player(self, player: Player) -> None:
        self.session.delete(player)
        self.session.flush()

    def delete_all(self, guild_id: Optional[str] = None) -> int:
        """Delete all players matching the guild_id (or all players if guild_id is '*' or None)."""
        players = self.list_all(guild_id=guild_id)
        count = len(players)
        for p in players:
            self.session.delete(p)
        self.session.flush()
        return count

    def reset_player(self, player: Player) -> None:
        """Wipe a player's registered troop data so they must
        re-register, without losing their row (kept distinct from
        `delete_player` for admin audit clarity -- see README).
        """
        for profile in list(player.troop_profiles):
            player.troop_profiles.remove(profile)
            self.session.delete(profile)
        for troop_type in TroopType:
            player.troop_profiles.append(
                TroopProfile(troop_type=troop_type, helios=False, level=None)
            )
        self.session.flush()
