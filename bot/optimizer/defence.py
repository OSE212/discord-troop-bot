"""Defence-mode specific helpers.

Mirrors bot.optimizer.attack -- kept separate so defence-specific
rules (e.g. a future Infantry-priority override) can be added without
touching the attack profile or the core optimizer.
"""
from __future__ import annotations

from bot.rules.configuration import ModeWeights, RankingConfig


def get_weights(config: RankingConfig) -> ModeWeights:
    return config.defence
