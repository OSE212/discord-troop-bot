"""Configurable scoring weights for the optimizer.

IMPORTANT: every numeric value in DEFAULT_CONFIG below is a
placeholder that only encodes the *relative ordering* described in
the spec (section 12-14) -- e.g. "Infantry is most important for
Defence" or "Marksman is very strong for Attack". None of these
numbers are real game statistics, and none should ever be presented
to a player as if they were. The project owner will supply real
values later; until then these are just enough for the optimizer to
produce deterministic, sensibly-ordered results.

Admins can override these at runtime by editing the JSON file at
RULES_CONFIG_PATH (default: config/rules.json) -- no code changes or
redeploys required. This is the hook spec section 8 refers to as
"Eventually configure optimizer rules."
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

from bot.database.models.player import TroopType


@dataclass
class ModeWeights:
    """Per-troop-type base weight for one mode (Attack or Defence),
    plus the shared Helios/FC modifiers used in that mode.
    """

    infantry_weight: float
    lancer_weight: float
    marksman_weight: float
    helios_weight: float
    fc_weight: float

    def base_weight(self, troop_type: TroopType) -> float:
        return {
            TroopType.INFANTRY: self.infantry_weight,
            TroopType.LANCERS: self.lancer_weight,
            TroopType.MARKSMAN: self.marksman_weight,
        }[troop_type]


@dataclass
class RankingConfig:
    attack: ModeWeights
    defence: ModeWeights
    # Optional flat modifier applied per formation_type. Spec section
    # 14 flags this as "if needed" -- default to no differentiation
    # until real data says otherwise.
    rally_modifier: float = 1.0
    garrison_modifier: float = 1.0

    def modifier_for(self, formation_type) -> float:
        from bot.optimizer.types import FormationType

        return (
            self.rally_modifier
            if formation_type == FormationType.RALLY
            else self.garrison_modifier
        )

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "RankingConfig":
        return cls(
            attack=ModeWeights(**data["attack"]),
            defence=ModeWeights(**data["defence"]),
            rally_modifier=data.get("rally_modifier", 1.0),
            garrison_modifier=data.get("garrison_modifier", 1.0),
        )


def default_config() -> RankingConfig:
    return RankingConfig(
        # Attack: Marksman + Infantry both "very strong", Lancers is
        # "balance" (kept lower). See spec section 12.
        attack=ModeWeights(
            infantry_weight=3.0,
            lancer_weight=1.5,
            marksman_weight=3.0,
            helios_weight=2.0,
            fc_weight=1.0,
        ),
        # Defence: Infantry "most important", Marksman "very bad
        # compared with Infantry", Lancers "balance". See spec
        # section 13.
        defence=ModeWeights(
            infantry_weight=3.5,
            lancer_weight=1.5,
            marksman_weight=0.5,
            helios_weight=2.0,
            fc_weight=1.0,
        ),
    )


def load_config(path: Optional[Path] = None) -> RankingConfig:
    """Load ranking weights from disk, falling back to (and writing)
    the placeholder defaults if the file doesn't exist yet.
    """
    if path is None:
        from bot.settings import settings

        path = settings.rules_config_path

    if not path.exists():
        config = default_config()
        save_config(config, path)
        return config

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return RankingConfig.from_dict(data)


def save_config(config: RankingConfig, path: Optional[Path] = None) -> None:
    if path is None:
        from bot.settings import settings

        path = settings.rules_config_path
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(config.to_dict(), f, indent=2)
