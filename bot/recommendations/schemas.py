"""Data types for the multi-rally assignment engine."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class EventScope(str, Enum):
    ALLIANCE = "alliance"
    STATE = "state"


class RallyRole(str, Enum):
    MAIN_STRIKE = "main_strike"
    GARRISON_DEFENSE = "garrison_defense"
    SUICIDE_BREAKER = "suicide_breaker"


ROLE_LABELS = {
    RallyRole.MAIN_STRIKE: "⚔️ Main Strike",
    RallyRole.GARRISON_DEFENSE: "🛡️ Garrison Defense",
    RallyRole.SUICIDE_BREAKER: "💥 Breaker / Suicide",
}

ROLE_COLORS = {
    RallyRole.MAIN_STRIKE: 0xF59E0B,       # amber
    RallyRole.GARRISON_DEFENSE: 0x3B82F6,  # blue
    RallyRole.SUICIDE_BREAKER: 0xEF4444,   # red
}


@dataclass
class PlayerAssignmentRow:
    player_name: str
    march_limit: int
    infantry_count: int
    lancer_count: int
    marksman_count: int
    recommended_captain: str = ""
    recommended_joiners: List[str] = field(default_factory=list)
    tactical_note: Optional[str] = None
    helios: bool = False
    fc_level: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "player_name": self.player_name,
            "march_limit": self.march_limit,
            "infantry_count": self.infantry_count,
            "lancer_count": self.lancer_count,
            "marksman_count": self.marksman_count,
            "recommended_captain": self.recommended_captain,
            "recommended_joiners": self.recommended_joiners,
            "tactical_note": self.tactical_note,
            "helios": self.helios,
            "fc_level": self.fc_level,
        }


@dataclass
class RallyGroup:
    rally_index: int          # 1-based
    role: RallyRole
    label: str
    ratio: dict               # {infantry, lancer, marksman} percentages
    players: List[PlayerAssignmentRow] = field(default_factory=list)
    avg_fc_level: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "rally_index": self.rally_index,
            "role": self.role.value,
            "label": self.label,
            "ratio": self.ratio,
            "players": [p.to_dict() for p in self.players],
            "avg_fc_level": self.avg_fc_level,
        }
