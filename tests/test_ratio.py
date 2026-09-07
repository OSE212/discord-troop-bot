import pytest

from bot.database.models.player import TroopType
from bot.optimizer.ratio import (
    InvalidCapacityError,
    InvalidRatioError,
    compute_actual_ratio,
    compute_deviation,
    compute_targets,
    validate_capacity,
    validate_ratio,
)


def make_ratio(infantry, lancers, marksman):
    return {
        TroopType.INFANTRY: infantry,
        TroopType.LANCERS: lancers,
        TroopType.MARKSMAN: marksman,
    }


def test_valid_ratio_passes():
    validate_ratio(make_ratio(49, 2, 49))


def test_ratio_must_total_100():
    with pytest.raises(InvalidRatioError):
        validate_ratio(make_ratio(50, 10, 50))


def test_ratio_rejects_negative_values():
    with pytest.raises(InvalidRatioError):
        validate_ratio(make_ratio(-5, 55, 50))


def test_capacity_must_be_positive():
    with pytest.raises(InvalidCapacityError):
        validate_capacity(0)
    with pytest.raises(InvalidCapacityError):
        validate_capacity(-100)


def test_compute_targets_matches_spec_example():
    targets = compute_targets(make_ratio(49, 2, 49), 2_000_000)
    assert targets[TroopType.INFANTRY] == 980_000
    assert targets[TroopType.LANCERS] == 40_000
    assert targets[TroopType.MARKSMAN] == 980_000
    assert sum(targets.values()) == 2_000_000


def test_compute_targets_rounding_sums_exactly():
    # A ratio that doesn't divide evenly must still sum to capacity.
    targets = compute_targets(make_ratio(33, 33, 34), 1000)
    assert sum(targets.values()) == 1000


def test_actual_ratio_and_deviation():
    final = {TroopType.INFANTRY: 900_000, TroopType.LANCERS: 40_000, TroopType.MARKSMAN: 980_000}
    actual = compute_actual_ratio(final)
    total = sum(final.values())
    assert actual[TroopType.INFANTRY] == pytest.approx(900_000 / total * 100)

    deviation = compute_deviation(make_ratio(49, 2, 49), actual)
    assert deviation[TroopType.INFANTRY] < 0  # under target
    assert deviation[TroopType.MARKSMAN] > 0  # over target relatively
