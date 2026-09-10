"""Bridges registered players (DB) and the /calculate command to the
deterministic optimizer, and formats results per spec section 19.

Calculation never writes to player registration data (spec section
9) -- this service only reads players and produces an in-memory
FormationResult.
"""
from __future__ import annotations

from bot.optimizer.optimizer import HERO_BUFF_DESCRIPTIONS

from bot.database.models.player import Player, TroopType
from bot.database.repositories.player_repository import PlayerRepository
from bot.optimizer.optimizer import optimize
from bot.optimizer.types import (
    FormationRequest,
    FormationResult,
    FormationType,
    Mode,
    OptimizerPlayer,
    Status,
    TroopAvailability,
)
from bot.rules.configuration import RankingConfig


def _to_optimizer_player(player: Player) -> OptimizerPlayer | None:
    """Convert a DB player into optimizer input. Returns None for
    players whose registration isn't complete yet -- incomplete
    players are silently excluded from calculations rather than
    crashing the optimizer (spec: registration/calculation are
    separate, and an incomplete registration simply isn't usable
    yet).
    """
    if not player.is_complete():
        return None

    troop_types: dict[TroopType, TroopAvailability] = {}
    for troop_type in TroopType:
        profile = player.profile_for(troop_type)
        if profile is None or profile.level is None:
            continue
        troop_types[troop_type] = TroopAvailability(
            helios=profile.helios,
            level=profile.level,
            available_quantity=profile.available_quantity(),
        )

    heroes = {h.hero_name.lower(): (h.stars, h.skill_level) for h in player.heroes}
    return OptimizerPlayer(
        player_id=player.id,
        name=player.name,
        march_limit=player.march_limit,
        troop_types=troop_types,
        heroes=heroes,
    )


class FormationService:
    def __init__(self, repository: PlayerRepository, config: RankingConfig):
        self.repository = repository
        self.config = config

    def calculate(
        self,
        *,
        mode: Mode,
        formation_type: FormationType,
        ratio: dict[TroopType, float],
        capacity: int,
        captain_id: Optional[int] = None,
        captain_heroes: Optional[list[str]] = None,
        target_joiners: Optional[list[str]] = None,
        guild_id: Optional[str] = None,
        alliance_tag: Optional[str] = None,
    ) -> FormationResult:
        request = FormationRequest(
            mode=mode,
            formation_type=formation_type,
            ratio=ratio,
            capacity=capacity,
            captain_id=captain_id,
            captain_heroes=tuple(captain_heroes or ()),
            target_joiners=tuple(target_joiners or ()),
        )
        all_players = self.repository.list_all(guild_id=guild_id, alliance_tag=alliance_tag)

        candidates = [
            p for p in (_to_optimizer_player(pl) for pl in all_players) if p is not None
        ]
        return optimize(candidates, request, self.config)



def format_result(result: FormationResult) -> str:
    """Render a FormationResult as the plain-text layout from spec
    section 19. Kept separate from Discord embed code so it's easy to
    unit test and easy to swap for a richer embed later.
    """
    req = result.request
    lines: list[str] = []
    lines.append("FORMATION")
    lines.append(f"Mode: {req.mode.value.capitalize()}")
    lines.append(f"Type: {req.formation_type.value.capitalize()}")
    if req.formation_type == FormationType.GARRISON and result.target_capacity > req.capacity:
        lines.append(f"Base Capacity: {req.capacity:,}")
        lines.append(f"Buffered Capacity (1.67x): {result.target_capacity:,}")
    else:
        lines.append(f"Capacity: {req.capacity:,}")
    ratio_str = " / ".join(f"{req.ratio[t]:g}" for t in TroopType)
    lines.append(f"Target Ratio: {ratio_str}")
    lines.append("")
    lines.append("TARGET")
    for t in TroopType:
        lines.append(f"{t.value.capitalize()}: {result.target[t]:,}")
    lines.append("")
    # Insert this inside format_result(result) before "TARGET" or "SELECTED PLAYERS"
    if getattr(req, 'captain_id', None):
        lines.append("COMMAND TEAM (EXACT RATIO)")
        cap_summary = next((s for s in result.selected_players if s.player_id == req.captain_id), None)
        if cap_summary:
            lines.append(f"Captain: {cap_summary.player_name}")
        if getattr(req, 'captain_heroes', None):
            # Import HERO_BUFF_DESCRIPTIONS from optimizer.py
            heroes_str = "\n".join(f"  • {h}: {HERO_BUFF_DESCRIPTIONS.get(h.lower(), 'Expedition Skill')}" for h in req.captain_heroes)
            lines.append(heroes_str)
    lines.append("")
    lines.append("SELECTED PLAYERS")
    for i, summary in enumerate(result.selected_players, start=1):
        lines.append(f"{i}. {summary.player_name}")
        for t, amount in summary.contributions.items():
            lines.append(f"   {t.value.capitalize()}: {amount:,}")

    if result.joiners:
        lines.append("")
        lines.append("TOP 4 JOINERS (MARCH FIRST FOR HERO BUFFS)")
        for j in result.joiners:
            lines.append(
                f"Slot {j.slot}: {j.player_name} [{j.hero_name} {j.stars}★ / Skill {j.skill_level}] - {j.buff_description}"
            )

    lines.append("")
    lines.append("FINAL")
    for t in TroopType:
        lines.append(f"{t.value.capitalize()}: {result.final[t]:,}")
    lines.append("")
    actual_str = " / ".join(f"{result.actual_ratio[t]:.1f}%" for t in TroopType)
    lines.append(f"Actual Ratio: {actual_str}")
    deviation_str = " / ".join(f"{result.deviation[t]:+.1f}%" for t in TroopType)
    lines.append(f"Deviation: {deviation_str}")
    lines.append("")
    status_label = "Exact" if result.status == Status.EXACT else "Best Effort"
    lines.append(f"Status: {status_label}")
    if req.formation_type == FormationType.GARRISON:
        total_final = sum(result.final.values())
        if result.target_capacity > total_final:
            gap = result.target_capacity - total_final
            lines.append(f"Garrison Gap: +{gap:,} troops needed from incoming solos/reinforcements")
    if result.status == Status.BEST_EFFORT:
        lines.append(
            "Note: the exact requested ratio was not achievable with "
            "currently registered players/quantities."
        )
    return "\n".join(lines)
