"""Deterministic scoring for a (player, troop_type) contribution.

Formula (spec section 14):

    score = (base troop type value
             + FC level value
             + Helios bonus) * rally/garrison modifier

Base troop type value already differs between Attack and Defence
(spec sections 12-13), which is what the spec calls the
"attack/defence modifier". The relative preference between one extra
FC level and a Helios bonus is intentionally left as configurable
weights (spec section 14) rather than hard-coded, since the real
trade-off is not yet confirmed.
"""
from __future__ import annotations

from bot.database.models.player import TroopType
from bot.optimizer.types import FormationType, Mode, TroopAvailability
from bot.rules.configuration import RankingConfig


def score_contribution(
    troop_type: TroopType,
    availability: TroopAvailability,
    mode: Mode,
    formation_type: FormationType,
    config: RankingConfig,
) -> float:
    weights = config.attack if mode == Mode.ATTACK else config.defence

    base = weights.base_weight(troop_type)
    fc_value = weights.fc_weight * availability.level
    helios_bonus = weights.helios_weight if availability.helios else 0.0

    modifier = config.modifier_for(formation_type)

    return (base + fc_value + helios_bonus) * modifier
