from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Optional

from bot.database.models.player import TroopType


class Mode(str, enum.Enum):
    ATTACK = "attack"
    DEFENCE = "defence"


class FormationType(str, enum.Enum):
    RALLY = "rally"
    GARRISON = "garrison"


class Status(str, enum.Enum):
    EXACT = "exact"
    BEST_EFFORT = "best_effort"


@dataclass(frozen=True)
class TroopAvailability:
    """A single player's data for one troop type, as seen by the
    optimizer. `available_quantity=None` means non-Helios /
    "sufficiently abundant" -- bounded only by march limit.
    """

    helios: bool
    level: int
    available_quantity: Optional[int]


@dataclass(frozen=True)
class OptimizerPlayer:
    """A candidate player, as seen by the optimizer. This is a plain
    dataclass (not the ORM model) so the optimizer stays decoupled
    from SQLAlchemy and is trivial to unit test.
    """

    player_id: int
    name: str
    march_limit: int
    troop_types: dict[TroopType, TroopAvailability]
    heroes: dict[str, tuple[int, int]] = field(default_factory=dict)


@dataclass(frozen=True)
class FormationRequest:
    mode: Mode
    formation_type: FormationType
    ratio: dict[TroopType, float]  # percentages, must sum to 100
    capacity: int
    captain_id: int | None = None
    captain_heroes: tuple[str, ...] = ()
    target_joiners: tuple[str, ...] = ()


@dataclass
class Allocation:
    player_id: int
    player_name: str
    troop_type: TroopType
    amount: int
    score: float


@dataclass
class PlayerAllocationSummary:
    """Groups a player's (possibly multiple) allocations together for
    display, since spec rule 17 says a player is used only once even
    if their march is split across troop types.
    """

    player_id: int
    player_name: str
    contributions: dict[TroopType, int] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return sum(self.contributions.values())


@dataclass
class JoinerRecommendation:
    slot: int               # 1, 2, 3, 4
    player_id: int
    player_name: str
    hero_name: str
    stars: int
    skill_level: int
    buff_description: str


@dataclass
class FormationResult:
    request: FormationRequest
    target: dict[TroopType, int]
    selected_players: list[PlayerAllocationSummary]
    final: dict[TroopType, int]
    actual_ratio: dict[TroopType, float]
    deviation: dict[TroopType, float]
    status: Status
    base_capacity: int = 0
    target_capacity: int = 0
    joiners: list[JoinerRecommendation] = field(default_factory=list)
    avg_fc_level: float | None = None
