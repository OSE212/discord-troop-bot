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
    """Compute strength score prioritizing the highest troops (highest FC level & Helios).

    Weights:
      - Max FC Level * 1000 (FC8 > FC7 > FC6 > ...)
      - Helios: +500 per Helios troop type (fire tier priority)
      - Avg FC Level * 50
      - March limit / 10000
    """
    troops = player.get("troops", {})
    levels = [t_data.get("level") for t_data in troops.values() if t_data.get("level") is not None]
    max_level = max(levels) if levels else 0
    avg_level = (sum(levels) / len(levels)) if levels else 0
    helios_count = sum(1 for t_data in troops.values() if t_data.get("helios", False))
    march = player.get("march_limit", 0) or 0

    return (max_level * 1000.0) + (helios_count * 500.0) + (avg_level * 50.0) + (march / 10000.0)


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
        rally_captains: Optional[List[Dict[str, Any]]] = None,
    ) -> List[RallyGroup]:
        """
        Compute rally assignments.
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

        groups: List[List[Dict]] = [[] for _ in range(n_rallies)]
        custom_captains_map: Dict[int, Dict[str, Any]] = {} # rally_idx -> captain dict

        # Pre-assign designated captains
        if rally_captains and isinstance(rally_captains, list):
            for r_idx, cap_info in enumerate(rally_captains[:n_rallies]):
                if not cap_info or not isinstance(cap_info, dict):
                    continue
                cap_id = cap_info.get("captain_id")
                if cap_id:
                    # Find player in pool
                    cap_player = next((p for p in pool if p["id"] == cap_id), None)
                    if cap_player:
                        groups[r_idx].append(cap_player)
                        custom_captains_map[r_idx] = {
                            "player": cap_player,
                            "heroes": cap_info.get("captain_heroes") or []
                        }
                        pool.remove(cap_player)

        # Distribute remaining players round-robin across rallies
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

            # Support custom ratio override per rally if specified in rally_captains
            cap_info = rally_captains[idx] if (rally_captains and idx < len(rally_captains) and isinstance(rally_captains[idx], dict)) else {}
            custom_ratio = cap_info.get("ratio")
            if custom_ratio and isinstance(custom_ratio, dict):
                inf = float(custom_ratio.get("infantry", 0))
                lan = float(custom_ratio.get("lancers", custom_ratio.get("lancer", 0)))
                mrk = float(custom_ratio.get("marksman", 0))
                if (inf + lan + mrk) > 0:
                    ratio = {"infantry": inf, "lancers": lan, "marksman": mrk}
            else:
                lan_val = float(ratio.get("lancers", ratio.get("lancer", 20)))
                ratio = {
                    "infantry": float(ratio.get("infantry", 50)),
                    "lancers": lan_val,
                    "marksman": float(ratio.get("marksman", 30)),
                }

            # Support custom capacity per rally if specified (leader limit)
            target_capacity = 2000000
            if cap_info and isinstance(cap_info, dict):
                raw_cap = cap_info.get("capacity")
                if raw_cap:
                    try:
                        target_capacity = int(raw_cap)
                    except (ValueError, TypeError):
                        pass

            # Support custom joiners override per rally if specified in rally_captains
            custom_joiners = [j for j in cap_info.get("target_joiners", []) if j] if cap_info else []
            joiner_list = custom_joiners if custom_joiners else heroes["joiners"]

            cap_heroes = custom_captains_map.get(idx, {}).get("heroes", [])
            primary_cap = cap_heroes[0] if cap_heroes else heroes["primary_captain"]

            rows: List[PlayerAssignmentRow] = []
            assigned_capacity = 0
            for rank, p in enumerate(group_players):
                march = p.get("march_limit", 160000)

                # Captain (rank == 0) is always assigned.
                # For subsequent joiners, check if rally capacity is reached.
                if rank > 0 and target_capacity > 0 and assigned_capacity >= target_capacity:
                    continue

                effective_march = march
                if rank > 0 and target_capacity > 0 and (assigned_capacity + march) > target_capacity:
                    effective_march = max(0, target_capacity - assigned_capacity)
                    if effective_march <= 0:
                        continue

                typed_ratio = _ratio_to_troop_type(ratio)
                counts = compute_targets(typed_ratio, effective_march)

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
                    march_limit=effective_march,
                    infantry_count=counts.get(TroopType.INFANTRY, 0),
                    lancer_count=counts.get(TroopType.LANCERS, 0),
                    marksman_count=counts.get(TroopType.MARKSMAN, 0),
                    recommended_captain=primary_cap,
                    recommended_joiners=joiner_list,
                    tactical_note=tactical_note,
                    helios=has_helios,
                    fc_level=avg_level,
                ))
                assigned_capacity += effective_march

            # Compute avg_fc_level for this rally's players
            fc_vals = [r.fc_level for r in rows if r.fc_level is not None]
            avg_fc = round(sum(fc_vals) / len(fc_vals), 3) if fc_vals else None

            result.append(RallyGroup(
                rally_index=idx + 1,
                role=role,
                label=label,
                ratio=ratio,
                players=rows,
                avg_fc_level=avg_fc,
                max_capacity=target_capacity,
                total_assigned=assigned_capacity,
            ))

        return result
