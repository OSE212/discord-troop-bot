"""
Multi-Rally Assignment Engine.

Accepts a pool of online players, a rally count (1-6), scope, and generation.
Returns a list of RallyGroup objects with per-player troop assignments.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from bot.database.models.player import TroopType
from bot.optimizer.ratio import compute_targets
from bot.recommendations.hero_data import get_hero_recommendations
from bot.recommendations.schemas import (
    EventScope,
    PlayerAssignmentRow,
    RallyGroup,
    RallyRole,
    ROLE_LABELS,
)


def _ratio_to_troop_type(ratio_pct: dict) -> dict:
    """Convert {'infantry': 50, 'lancer': 20, 'marksman': 30} to {TroopType.INFANTRY: 50, ...}"""
    mapping = {
        "infantry": TroopType.INFANTRY,
        "lancer": TroopType.LANCERS,
        "lancers": TroopType.LANCERS,
        "marksman": TroopType.MARKSMAN,
    }
    return {mapping[k]: v for k, v in ratio_pct.items() if k in mapping}


def _power_score(player: Dict[str, Any]) -> float:
    """Compute strength score for sorting: FC level × 10 + 50 per Helios type."""
    score = 0.0
    troops = player.get("troops", {})
    for t_data in troops.values():
        level = t_data.get("level") or 0
        helios = t_data.get("helios", False)
        score += level * 10
        if helios:
            score += 50
    # Also factor in march limit (bigger = better) at a small weight
    score += (player.get("march_limit", 0) / 10000)
    return score


def _assign_role_sequence(rally_count: int) -> List[RallyRole]:
    """Return ordered list of rally roles for 1..6 rallies.

    Pattern:
      1 → Main Strike
      2 → Main Strike, Breaker
      3 → Main Strike, Garrison, Breaker
      4 → Main Strike x2, Garrison, Breaker
      5 → Main Strike x2, Garrison, Breaker x2
      6 → Main Strike x2, Garrison x2, Breaker x2
    """
    patterns = {
        1: [RallyRole.MAIN_STRIKE],
        2: [RallyRole.MAIN_STRIKE, RallyRole.SUICIDE_BREAKER],
        3: [RallyRole.MAIN_STRIKE, RallyRole.GARRISON_DEFENSE, RallyRole.SUICIDE_BREAKER],
        4: [RallyRole.MAIN_STRIKE, RallyRole.MAIN_STRIKE, RallyRole.GARRISON_DEFENSE, RallyRole.SUICIDE_BREAKER],
        5: [RallyRole.MAIN_STRIKE, RallyRole.MAIN_STRIKE, RallyRole.GARRISON_DEFENSE, RallyRole.SUICIDE_BREAKER, RallyRole.SUICIDE_BREAKER],
        6: [RallyRole.MAIN_STRIKE, RallyRole.MAIN_STRIKE, RallyRole.GARRISON_DEFENSE, RallyRole.GARRISON_DEFENSE, RallyRole.SUICIDE_BREAKER, RallyRole.SUICIDE_BREAKER],
    }
    return patterns.get(max(1, min(rally_count, 6)), patterns[3])


class MultiRallyAssignmentEngine:

    @classmethod
    def process_assignments(
        cls,
        players: List[Dict[str, Any]],
        rally_count: int,
        generation: int,
        scope: EventScope = EventScope.STATE,
        alliance_tag: Optional[str] = None,
        online_only: bool = True,
        attendance: Optional[set] = None,
    ) -> List[RallyGroup]:
        """
        Compute rally assignments.

        Args:
            players:      Full serialized player list from the DB.
            rally_count:  Number of rallies (1–6).
            generation:   Server generation (1–7) for hero recommendations.
            scope:        EventScope.ALLIANCE or EventScope.STATE.
            alliance_tag: Filter by alliance tag when scope == ALLIANCE.
            online_only:  Whether to filter by attendance set.
            attendance:   Set of player IDs currently checked in online.

        Returns:
            List of RallyGroup, one per rally slot.
        """
        # 1 — Scope filtering
        pool = list(players)
        if scope == EventScope.ALLIANCE and alliance_tag:
            pool = [p for p in pool if (p.get("alliance_tag") or "").upper() == alliance_tag.upper()]

        # 2 — Attendance filtering
        if online_only and attendance is not None:
            pool = [p for p in pool if p["id"] in attendance]

        # 3 — Sort by power score descending
        pool.sort(key=_power_score, reverse=True)

        if not pool:
            return []

        # 4 — Build role sequence
        role_sequence = _assign_role_sequence(rally_count)
        n_rallies = len(role_sequence)

        # 5 — Distribute players across rallies (round-robin by power rank)
        groups: List[List[Dict]] = [[] for _ in range(n_rallies)]
        for i, player in enumerate(pool):
            groups[i % n_rallies].append(player)

        # 6 — Build RallyGroup objects
        result: List[RallyGroup] = []
        role_counters: Dict[RallyRole, int] = {}

        for idx, (role, group_players) in enumerate(zip(role_sequence, groups)):
            role_counters[role] = role_counters.get(role, 0) + 1
            suffix = f" #{role_counters[role]}" if role_counters[role] > 1 else ""
            label = ROLE_LABELS[role] + suffix

            heroes = get_hero_recommendations(generation, role.value)
            ratio = heroes["ratio"]

            rows: List[PlayerAssignmentRow] = []
            for rank, p in enumerate(group_players):
                march = p.get("march_limit", 160000)
                typed_ratio = _ratio_to_troop_type(ratio)
                counts = compute_targets(typed_ratio, march)

                # Extract aggregated helios/level for display
                troops = p.get("troops", {})
                has_helios = any(t.get("helios") for t in troops.values())
                levels = [t.get("level") for t in troops.values() if t.get("level") is not None]
                avg_level = round(sum(levels) / len(levels)) if levels else None

                tactical_note = None
                if rank == 0:
                    tactical_note = "🥇 Top Whale — Priority Captain"
                elif rank < 3:
                    tactical_note = "⭐ High Power"

                rows.append(PlayerAssignmentRow(
                    player_name=p.get("name", "Unknown"),
                    march_limit=march,
                    infantry_count=counts.get(TroopType.INFANTRY, 0),
                    lancer_count=counts.get(TroopType.LANCERS, 0),
                    marksman_count=counts.get(TroopType.MARKSMAN, 0),
                    recommended_captain=heroes["primary_captain"],
                    recommended_joiners=heroes["joiners"],
                    tactical_note=tactical_note,
                    helios=has_helios,
                    fc_level=avg_level,
                ))

            result.append(RallyGroup(
                rally_index=idx + 1,
                role=role,
                label=label,
                ratio=ratio,
                players=rows,
            ))

        return result
