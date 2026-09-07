"""Attack-mode specific helpers.

For V1 this is a thin wrapper around RankingConfig.attack -- kept as
its own module (per the spec's suggested project structure) so
attack-specific tie-breaking or bonuses can be added later without
touching the core optimizer or the defence profile.
"""
from __future__ import annotations

from bot.rules.configuration import ModeWeights, RankingConfig


def get_weights(config: RankingConfig) -> ModeWeights:
    return config.attack
