"""Ratio validation and target-count math (spec sections 9, 16)."""
from __future__ import annotations

from bot.database.models.player import TroopType

_RATIO_TOLERANCE = 1e-6


class InvalidRatioError(ValueError):
    pass


class InvalidCapacityError(ValueError):
    pass


def validate_ratio(ratio: dict[TroopType, float]) -> None:
    if set(ratio.keys()) != set(TroopType):
        raise InvalidRatioError(
            "Ratio must specify a percentage for every troop type "
            "(infantry, lancers, marksman)."
        )
    for troop_type, pct in ratio.items():
        if pct < 0:
            raise InvalidRatioError(
                f"{troop_type.value} percentage cannot be negative."
            )
    total = sum(ratio.values())
    if abs(total - 100.0) > _RATIO_TOLERANCE:
        raise InvalidRatioError(
            f"Ratio must total 100%, got {total:.4f}%."
        )


def validate_capacity(capacity: int) -> None:
    if capacity <= 0:
        raise InvalidCapacityError("Capacity must be a positive number.")


def compute_targets(
    ratio: dict[TroopType, float], capacity: int
) -> dict[TroopType, int]:
    """Convert percentages into integer troop targets that always sum
    exactly to `capacity`, using the largest-remainder method so
    rounding never silently drops or adds units.
    """
    validate_ratio(ratio)
    validate_capacity(capacity)

    raw = {t: capacity * (pct / 100.0) for t, pct in ratio.items()}
    floored = {t: int(v) for t, v in raw.items()}
    remainder = capacity - sum(floored.values())

    # Distribute leftover units to the troop types with the largest
    # fractional remainder first, for a deterministic, fair rounding.
    remainders_sorted = sorted(
        raw.keys(), key=lambda t: (raw[t] - floored[t]), reverse=True
    )
    for troop_type in remainders_sorted[:remainder]:
        floored[troop_type] += 1

    return floored


def compute_actual_ratio(final: dict[TroopType, int]) -> dict[TroopType, float]:
    total = sum(final.values())
    if total == 0:
        return {t: 0.0 for t in TroopType}
    return {t: (count / total) * 100.0 for t, count in final.items()}


def compute_deviation(
    requested_ratio: dict[TroopType, float],
    actual_ratio: dict[TroopType, float],
) -> dict[TroopType, float]:
    return {
        t: actual_ratio[t] - requested_ratio[t] for t in TroopType
    }
