"""Deterministic, rule-based formation optimizer (spec sections 10-17).

Algorithm (greedy, not a global MILP solver -- see README "Known
Limitations"):

1. Convert the requested ratio + capacity into integer per-type
   targets (largest-remainder rounding, see optimizer.ratio).
2. Score every (player, troop_type) combination the player has
   actually registered, using the configured Attack/Defence weights.
3. Walk all candidates in descending score order. For each one,
   assign as many troops as the remaining per-type target, the
   player's remaining march limit, and (for Helios troops) the
   remaining Helios quantity will allow.
4. Because a single player's remaining march limit is shared state
   across every troop type they contribute, this naturally enforces
   "no player exceeds their march limit" and "a player is only used
   once" (spec rules 8, 9, 17) even when the confirmed mechanic
   allows splitting one player's march across multiple troop types.

This is intentionally simple and fully deterministic: same inputs
always produce the same output, and nothing here is LLM-driven (spec
rule 10).
"""
from __future__ import annotations

import math

from bot.database.models.player import TroopType
from bot.recommendations.hero_data import HERO_BUFF_DESCRIPTIONS
from bot.optimizer.ranking import score_contribution
from bot.optimizer.ratio import compute_actual_ratio, compute_deviation, compute_targets
from bot.optimizer.types import (
    Allocation,
    FormationRequest,
    FormationResult,
    FormationType,
    JoinerRecommendation,
    Mode,
    OptimizerPlayer,
    PlayerAllocationSummary,
    Status,
)
from bot.rules.configuration import RankingConfig


def _build_candidates(
    players: list[OptimizerPlayer], request: FormationRequest, config: RankingConfig
) -> list[Allocation]:
    candidates: list[Allocation] = []
    for player in players:
        for troop_type, availability in player.troop_types.items():
            score = score_contribution(
                troop_type, availability, request.mode, request.formation_type, config
            )
            candidates.append(
                Allocation(
                    player_id=player.player_id,
                    player_name=player.name,
                    troop_type=troop_type,
                    amount=0,
                    score=score,
                )
            )
    # Deterministic ordering: highest score first; ties broken by
    # player_id then troop_type so re-running with identical input
    # always yields an identical result.
    candidates.sort(key=lambda c: (-c.score, c.player_id, c.troop_type.value))
    return candidates


def optimize(
    players: list[OptimizerPlayer],
    request: FormationRequest,
    config: RankingConfig,
) -> FormationResult:
    if request.formation_type == FormationType.GARRISON:
        effective_target_capacity = int(round(request.capacity * 1.67))
    else:
        effective_target_capacity = request.capacity

    targets = compute_targets(request.ratio, effective_target_capacity)
    remaining_target = dict(targets)
    remaining_march = {p.player_id: p.march_limit for p in players}
    players_by_id = {p.player_id: p for p in players}
    summaries: dict[int, PlayerAllocationSummary] = {}

    # --- 1. CAPTAIN PRE-ALLOCATION ---
    if getattr(request, 'captain_id', None) and request.captain_id in players_by_id:
        cap_id = request.captain_id
        cap_limit = players_by_id[cap_id].march_limit
        cap_targets = compute_targets(request.ratio, cap_limit) # Exact ratio applied
        
        cap_summary = summaries.setdefault(cap_id, PlayerAllocationSummary(player_id=cap_id, player_name=players_by_id[cap_id].name))
        
        for t_type, amt in cap_targets.items():
            cap_summary.contributions[t_type] = amt
            remaining_target[t_type] -= amt
            
        remaining_march[cap_id] -= sum(cap_targets.values())

    # --- 2. GREEDY ALLOCATION FOR JOINERS ---
    candidates = _build_candidates(players, request, config)

    for candidate in candidates:
        troop_type = candidate.troop_type
        player_id = candidate.player_id

        if remaining_target[troop_type] <= 0 or remaining_march.get(player_id, 0) <= 0:
            continue

        availability = players_by_id[player_id].troop_types[troop_type]
        quantity_cap = (
            availability.available_quantity
            if availability.available_quantity is not None
            else math.inf
        )

        amount = min(remaining_target[troop_type], remaining_march[player_id], quantity_cap)
        if amount <= 0:
            continue
            
        amount = int(amount)
        remaining_target[troop_type] -= amount
        remaining_march[player_id] -= amount

        summary = summaries.setdefault(
            player_id,
            PlayerAllocationSummary(player_id=player_id, player_name=candidate.player_name),
        )
        summary.contributions[troop_type] = summary.contributions.get(troop_type, 0) + amount

    final = {t: targets[t] - remaining_target[t] for t in TroopType}
    actual_ratio = compute_actual_ratio(final)
    deviation = compute_deviation(request.ratio, actual_ratio)
    status = Status.EXACT if all(remaining_target[t] <= 0 for t in TroopType) else Status.BEST_EFFORT

    cap_id = getattr(request, 'captain_id', None)
    if cap_id and cap_id in summaries:
        cap_summary = summaries[cap_id]
        other_players = sorted([s for s in summaries.values() if s.player_id != cap_id], key=lambda s: s.total, reverse=True)
        selected_players = [cap_summary] + other_players
    else:
        selected_players = sorted(summaries.values(), key=lambda s: s.total, reverse=True)

    # Compute average FC level across selected players
    fc_levels = []
    for s in selected_players:
        p_obj = players_by_id.get(s.player_id)
        if p_obj and p_obj.troop_types:
            levels = [avail.level for avail in p_obj.troop_types.values() if avail.level is not None]
            if levels:
                fc_levels.append(sum(levels) / len(levels))
    avg_fc = round(sum(fc_levels) / len(fc_levels), 3) if fc_levels else None

    # Exclude the captain from being recommended as a joiner
    joiner_pool = [s for s in selected_players if s.player_id != cap_id]
    joiners = _select_top_joiners(joiner_pool, players_by_id, request)

    return FormationResult(
        request=request,
        target=targets,
        selected_players=selected_players,
        final=final,
        actual_ratio=actual_ratio,
        deviation=deviation,
        status=status,
        base_capacity=request.capacity,
        target_capacity=effective_target_capacity,
        joiners=joiners,
        avg_fc_level=avg_fc,
    )


HERO_BUFF_DESCRIPTIONS: dict[str, str] = {
    "jessie": "+25% Damage Dealt (Skill 5)",
    "jasser": "+25% Damage Dealt (Skill 5)",
    "seoyoon": "+25% Attack (Skill 5)",
    "patrick": "+25% HP (Skill 5)",
    "sergey": "+20% Defense (Skill 5)",
    "ling_xue": "+20% Defense (Skill 5)",
    "ling xue": "+20% Defense (Skill 5)",
    "ahmose": "Frontline Shield & Counter-strike",
    "norah": "Enemy Damage Reduction & Attack boost",
    "edith": "Frontline Defensive Aegis & Shielding",
    "hendrik": "Lethality boost & Ranged Amplification",
    "blanchette": "Marksman Vulnerability & Critical Stun",
    "alonso": "AoE Burst & Backline Disruption",
    "renee": "Lancer Cavalry Penetration",
    "philly": "Continuous Rally Health Regeneration",
    "jeronimo": "+15% Rally Attack & Stun",
    "natalia": "+15% Rally Defense & Stun",
    "molly": "+15% Skill Damage & Stun",
    "zinman": "Defense & Rally March Speed",
    "flint": "+20% Infantry Defense & Burn",
    "mia": "+20% Lancer Damage & Strike",
    "greg": "+20% Marksman Attack",
    "lynn": "Marksman Critical Boost",
    "hector": "+20% Infantry HP & Shield",
    "gordon": "Lancer Charge & Armor Vulnerability",
    "sonya": "Lancer Defense & Armor Reinforcement",
    "teresa": "Marksman Lethality Amplification",
    "wayne": "+25% Rally Attack & Shield",
    "bradley": "Infantry Block & Counter-blow",
    "magnus": "Ironclad Defense & Sustain",
    "gatot": "Lancer Breaker & Momentum",
    "fred": "Lancer Critical Surge",
    "wu ming": "Infantry Absolute Shield",
}


def _select_top_joiners(
    selected_summaries: list[PlayerAllocationSummary],
    players_by_id: dict[int, OptimizerPlayer],
    request: FormationRequest,
) -> list[JoinerRecommendation]:
    if not selected_summaries:
        return []

    if request.target_joiners:
        target_heroes = list(request.target_joiners)[:4]
    elif request.mode == Mode.ATTACK:
        target_heroes = ["Jessie", "Jasser", "Seoyoon", "Norah"]
    else:
        target_heroes = ["Patrick", "Sergey", "Ling Xue", "Ahmose"]

    recommendations: list[JoinerRecommendation] = []
    used_player_ids: set[int] = set()

    for slot_idx, target_hero in enumerate(target_heroes, start=1):
        norm_target = target_hero.lower().strip()
        candidates = []
        for summary in selected_summaries:
            pid = summary.player_id
            if pid in used_player_ids:
                continue
            player = players_by_id.get(pid)
            if not player:
                continue

            hero_info = player.heroes.get(norm_target)
            if hero_info:
                stars, skill_lvl = hero_info
                score = skill_lvl * 10 + stars
                candidates.append((score, stars, skill_lvl, target_hero, player))

        if candidates:
            candidates.sort(key=lambda c: (-c[0], -c[4].march_limit))
            best_score, best_stars, best_skill, h_name, best_player = candidates[0]
            used_player_ids.add(best_player.player_id)
            desc = HERO_BUFF_DESCRIPTIONS.get(h_name.lower(), "Expedition Skill Buff")
            recommendations.append(
                JoinerRecommendation(
                    slot=slot_idx,
                    player_id=best_player.player_id,
                    player_name=best_player.name,
                    hero_name=h_name.capitalize(),
                    stars=best_stars,
                    skill_level=best_skill,
                    buff_description=desc,
                )
            )
        else:
            available_players = [
                (summary, players_by_id[summary.player_id])
                for summary in selected_summaries
                if summary.player_id not in used_player_ids and summary.player_id in players_by_id
            ]
            if available_players:
                best_match = None
                for summary, player in available_players:
                    for h_name, (stars, skill_lvl) in player.heroes.items():
                        score = skill_lvl * 10 + stars
                        if best_match is None or score > best_match[0]:
                            best_match = (score, stars, skill_lvl, h_name, player)

                if best_match:
                    score, stars, skill_lvl, h_name, player = best_match
                    used_player_ids.add(player.player_id)
                    desc = HERO_BUFF_DESCRIPTIONS.get(h_name.lower(), "Expedition Skill Buff")
                    recommendations.append(
                        JoinerRecommendation(
                            slot=slot_idx,
                            player_id=player.player_id,
                            player_name=player.name,
                            hero_name=h_name.capitalize(),
                            stars=stars,
                            skill_level=skill_lvl,
                            buff_description=desc,
                        )
                    )
                else:
                    top_summary, top_player = available_players[0]
                    used_player_ids.add(top_player.player_id)
                    recommendations.append(
                        JoinerRecommendation(
                            slot=slot_idx,
                            player_id=top_player.player_id,
                            player_name=top_player.name,
                            hero_name=target_hero.capitalize(),
                            stars=5,
                            skill_level=5,
                            buff_description=HERO_BUFF_DESCRIPTIONS.get(target_hero.lower(), "Expedition Skill Buff"),
                        )
                    )

    return recommendations

